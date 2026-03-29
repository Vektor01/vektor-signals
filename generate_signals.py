import os
import json
import base64
import requests
from datetime import datetime, timezone
from vektor_pdf import generate_pdf

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
COINGECKO_API_KEY = os.environ["COINGECKO_API_KEY"]
SUPABASE_URL      = os.environ["SUPABASE_URL"]
SUPABASE_KEY      = os.environ["SUPABASE_SERVICE_KEY"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]

NOW        = datetime.now(timezone.utc)
DATE_LABEL = NOW.strftime("%A %d %B %Y")
DATE_FILE  = NOW.strftime("%Y%m%d")
TIME_LABEL = NOW.strftime("%H:%M GMT")

TIER_CONFIG = {
    "starter": {
        "subject":  f"📊 Vektor Starter Signals — {DATE_LABEL}",
        "assets":   ["BTC", "ETH", "XRP"],
        "preview":  "Your daily BTC, ETH & XRP signals are ready.",
    },
    "pro": {
        "subject":  f"🚀 Vektor Pro Signals — {DATE_LABEL}",
        "assets":   ["BTC", "ETH", "XRP", "SOL", "BNB", "HYPE"],
        "preview":  "Your full 6-asset daily signals + macro overview are ready.",
    },
    "vip": {
        "subject":  f"⚡ Vektor Elite Signals — {DATE_LABEL}",
        "assets":   ["BTC", "ETH", "XRP", "SOL", "BNB", "HYPE"],
        "preview":  "Your complete Elite daily briefing — all 4 reports attached.",
    },
}

# ── Price fetching ────────────────────────────────────────────────────────────

def fetch_binance_prices():
    """
    Fetch real-time prices from Binance REST API.
    Returns dict of ticker -> {price, change} for all available symbols.
    No API key required.
    """
    symbol_map = {
        "BTCUSDT": "BTC",
        "ETHUSDT": "ETH",
        "XRPUSDT": "XRP",
        "SOLUSDT": "SOL",
        "BNBUSDT": "BNB",
    }
    try:
        resp = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            timeout=15
        )
        resp.raise_for_status()
        all_tickers = {item["symbol"]: item for item in resp.json()}

        prices = {}
        for symbol, ticker in symbol_map.items():
            if symbol in all_tickers:
                data   = all_tickers[symbol]
                price  = float(data["lastPrice"])
                change = float(data["priceChangePercent"])
                prices[ticker] = {"price": price, "change": change}
            else:
                print(f"  ⚠️  {symbol} not found on Binance")

        return prices

    except Exception as e:
        print(f"  ⚠️  Binance fetch failed: {e}")
        return {}


def fetch_hype_price_coingecko(api_key):
    """
    Fetch HYPE price from CoinGecko.
    HYPE trades on its own DEX and OKX/Gate — not on Binance.
    """
    try:
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=hyperliquid&vs_currencies=usd&include_24hr_change=true"
        )
        headers = {"x-cg-demo-api-key": api_key}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "HYPE": {
                "price":  data["hyperliquid"]["usd"],
                "change": data["hyperliquid"]["usd_24h_change"],
            }
        }
    except Exception as e:
        print(f"  ⚠️  CoinGecko HYPE fetch failed: {e}")
        return {}


def fetch_coingecko_fallback(api_key, missing_tickers):
    """
    Full CoinGecko fallback for any tickers that Binance didn't return.
    Used if Binance is down or a symbol is missing.
    """
    cg_ids = {
        "BTC":  "bitcoin",
        "ETH":  "ethereum",
        "XRP":  "ripple",
        "SOL":  "solana",
        "BNB":  "binancecoin",
        "HYPE": "hyperliquid",
    }
    ids_to_fetch = [cg_ids[t] for t in missing_tickers if t in cg_ids]
    if not ids_to_fetch:
        return {}

    try:
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            f"?ids={','.join(ids_to_fetch)}"
            "&vs_currencies=usd&include_24hr_change=true"
        )
        headers = {"x-cg-demo-api-key": api_key}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        id_to_ticker = {v: k for k, v in cg_ids.items()}
        prices = {}
        for cg_id, values in data.items():
            ticker = id_to_ticker.get(cg_id)
            if ticker:
                prices[ticker] = {
                    "price":  values["usd"],
                    "change": values["usd_24h_change"],
                }
        return prices

    except Exception as e:
        print(f"  ⚠️  CoinGecko fallback failed: {e}")
        return {}


def fetch_prices():
    """
    Master price fetch:
      1. Binance REST  — real-time, free, no key needed (BTC/ETH/XRP/SOL/BNB)
      2. CoinGecko     — for HYPE (not on Binance) and as fallback if Binance fails
    """
    print("Fetching prices...")
    required = ["BTC", "ETH", "XRP", "SOL", "BNB", "HYPE"]

    # Step 1 — Binance for the 5 main assets
    prices = fetch_binance_prices()

    if prices:
        print(f"  ✅ Binance returned {len(prices)} assets")
    else:
        print("  ⚠️  Binance returned nothing — falling back to CoinGecko for all assets")

    # Step 2 — HYPE always from CoinGecko (not on Binance)
    hype = fetch_hype_price_coingecko(COINGECKO_API_KEY)
    prices.update(hype)

    # Step 3 — CoinGecko fallback for anything still missing
    missing = [t for t in required if t not in prices]
    if missing:
        print(f"  ⚠️  Missing from Binance: {missing} — fetching from CoinGecko")
        fallback = fetch_coingecko_fallback(COINGECKO_API_KEY, missing)
        prices.update(fallback)

    # Step 4 — Log final prices
    print("  Final prices:")
    for ticker in required:
        if ticker in prices:
            v    = prices[ticker]
            sign = "+" if v["change"] >= 0 else ""
            print(f"    {ticker}: ${v['price']:,.4f}  {sign}{v['change']:.1f}%")
        else:
            print(f"    {ticker}: ⚠️  NOT AVAILABLE")

    return prices


# ── Signal generation ─────────────────────────────────────────────────────────

def generate_signals(prices):
    print("Generating signals via Claude...")
    price_block = "\n".join([
        f"- {k}: ${v['price']:,.4f} ({'+' if v['change']>=0 else ''}{v['change']:.1f}% 24h)"
        for k, v in prices.items()
    ])
    prompt = f"""You are Vektor Signals, an elite crypto trading signal service.
Today is {DATE_LABEL}. Current prices:
{price_block}

Generate a daily signal for each asset. Respond ONLY in valid JSON:
{{
  "session_theme": "3-5 word theme",
  "macro_summary": "one sentence macro context",
  "signals": {{
    "BTC": {{"bias":"ACCUMULATE","risk":"MEDIUM","entry_zone":"$X-$Y","target_1":"$X (+Y%)","target_2":"$X (+Y%)","stop_loss":"$X (-Y%)","rsi_estimate":"36","structure":"DESCENDING CHANNEL","ta":"2-3 sentence TA","catalyst":"2-3 sentence catalyst","summary_line":"one punchy sentence"}},
    "ETH": {{}},
    "XRP": {{}},
    "SOL": {{}},
    "BNB": {{}},
    "HYPE": {{}}
  }}
}}"""
    headers = {
        "Content-Type":    "application/json",
        "x-api-key":       ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    body = {
        "model":      "claude-sonnet-4-5",
        "max_tokens": 2000,
        "messages":   [{"role": "user", "content": prompt}]
    }
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers, json=body, timeout=60
    )
    resp.raise_for_status()
    raw = resp.json()["content"][0]["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    signals = json.loads(raw.strip())
    print(f"  Theme: {signals.get('session_theme')}")
    return signals


# ── PDF generation ────────────────────────────────────────────────────────────

def build_pdfs(prices, signals):
    """Generate branded PDFs for all tiers. Returns dict of tier -> filepath."""
    print("Generating PDFs...")
    pdfs = {}
    for tier in ["starter", "pro", "vip"]:
        try:
            filepath = generate_pdf(
                prices=prices,
                signals=signals,
                date_label=DATE_LABEL,
                tier=tier,
                output_dir="outputs"
            )
            pdfs[tier] = filepath
        except Exception as e:
            print(f"  ⚠️  PDF failed for {tier}: {e}")
    return pdfs


# ── Subscribers ───────────────────────────────────────────────────────────────

def fetch_subscribers():
    print("Fetching subscribers...")
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json"
    }
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/subscribers?select=email,tier,active&active=eq.true",
        headers=headers, timeout=15
    )
    resp.raise_for_status()
    subs = resp.json()
    by_tier = {"starter": [], "pro": [], "vip": []}
    for s in subs:
        tier = s.get("tier", "starter").lower()
        if tier == "elite":
            tier = "vip"
        if tier in by_tier:
            by_tier[tier].append(s["email"])
    for tier, emails in by_tier.items():
        print(f"  {tier.upper()}: {len(emails)}")
    return by_tier


# ── Email ─────────────────────────────────────────────────────────────────────

def build_email(tier, prices, signals, config):
    theme = signals.get("session_theme", "Daily Signals")
    macro = signals.get("macro_summary", "")
    assets = config["assets"]
    tier_colors = {"starter": "#4DC3FF", "pro": "#7B2FBE", "vip": "#F5C842"}
    tier_labels = {"starter": "Starter", "pro": "Pro", "vip": "Elite"}
    color = tier_colors.get(tier, "#7B2FBE")
    label = tier_labels.get(tier, "")
    rows = ""
    for ticker in assets:
        sig      = signals.get("signals", {}).get(ticker, {})
        bias     = sig.get("bias", "")
        line     = sig.get("summary_line", "")
        p        = prices.get(ticker, {})
        price_str = f"${p.get('price', 0):,.2f}"
        chg      = p.get("change", 0)
        chg_str  = f"+{chg:.1f}%" if chg >= 0 else f"{chg:.1f}%"
        chg_col  = "#00C896" if chg >= 0 else "#FF3B3B"
        rows += (
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #1E1A35;">'
            f'<b style="color:#fff;">{ticker}</b> '
            f'<span style="color:{chg_col};">{price_str} {chg_str}</span> '
            f'<span style="color:{color};font-weight:bold;">{bias}</span>'
            f'<br><span style="color:#6E688A;font-size:12px;">{line}</span>'
            f'</td></tr>'
        )
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#080612;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#0F0C1E;border:1px solid #2A2240;">
<tr><td style="padding:24px;border-bottom:1px solid #2A2240;">
<span style="font-size:24px;font-weight:bold;color:#F5C842;">VEKTOR</span><span style="font-size:24px;font-weight:bold;color:#fff;"> SIGNALS</span>
<span style="background:{color};color:#000;font-size:11px;font-weight:bold;padding:3px 10px;border-radius:12px;margin-left:10px;">{label}</span>
<p style="color:#6E688A;font-size:12px;margin:8px 0 0 0;">{DATE_LABEL}</p>
</td></tr>
<tr><td style="padding:20px 24px;">
<p style="color:#fff;font-size:16px;font-weight:bold;margin:0 0 6px 0;">"{theme}"</p>
<p style="color:#9A94B8;font-size:13px;margin:0 0 20px 0;">{macro}</p>
<table width="100%">{rows}</table>
<p style="color:#6E688A;font-size:12px;margin:20px 0 0 0;">Your signal PDF is attached. Open for full entry zones, targets and stop losses.</p>
</td></tr>
<tr><td style="padding:16px 24px;border-top:1px solid #2A2240;text-align:center;">
<p style="color:#6E688A;font-size:10px;margin:0;">AI market analysis — educational purposes only. Not financial advice.<br>Vektor Signals — vektorsignals.com</p>
</td></tr></table></body></html>"""


def send_emails(subscribers, signals, prices, pdfs):
    print("Sending emails...")
    sent = 0
    failed = 0

    for tier, emails in subscribers.items():
        if not emails:
            continue
        config   = TIER_CONFIG.get(tier, TIER_CONFIG["starter"])
        html     = build_email(tier, prices, signals, config)
        pdf_path = pdfs.get(tier)

        # Build attachment if PDF exists
        attachments = []
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
            pdf_filename = os.path.basename(pdf_path)
            attachments = [{
                "filename": pdf_filename,
                "content":  pdf_b64,
                "type":     "application/pdf"
            }]
            print(f"  📎 Attaching {pdf_filename} for {tier.upper()} tier")
        else:
            print(f"  ⚠️  No PDF for {tier} — sending email only")

        for email in emails:
            payload = {
                "from":    "Vektor Signals <signals@vektorsignals.com>",
                "to":      [email],
                "subject": config["subject"],
                "html":    html,
            }
            if attachments:
                payload["attachments"] = attachments

            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type":  "application/json"
                },
                json=payload,
                timeout=30
            )
            if resp.status_code in (200, 201):
                sent += 1
                print(f"  ✅ {tier} → {email}")
            else:
                failed += 1
                print(f"  ❌ {email}: {resp.text}")

    print(f"  Total: {sent} sent, {failed} failed")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print(f"  VEKTOR SIGNALS — {DATE_LABEL}")
    print("=" * 55)

    prices      = fetch_prices()
    signals     = generate_signals(prices)
    pdfs        = build_pdfs(prices, signals)
    subscribers = fetch_subscribers()
    send_emails(subscribers, signals, prices, pdfs)

    print("\n" + "=" * 55)
    print("  COMPLETE")
    print("=" * 55)

if __name__ == "__main__":
    main()
