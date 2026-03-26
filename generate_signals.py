import os
import json
import requests
from datetime import datetime, timezone

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

def fetch_prices():
    print("Fetching prices...")
    ids = "bitcoin,ethereum,ripple,solana,binancecoin,hyperliquid"
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    prices = {
        "BTC":  {"price": data["bitcoin"]["usd"],     "change": data["bitcoin"]["usd_24h_change"]},
        "ETH":  {"price": data["ethereum"]["usd"],    "change": data["ethereum"]["usd_24h_change"]},
        "XRP":  {"price": data["ripple"]["usd"],      "change": data["ripple"]["usd_24h_change"]},
        "SOL":  {"price": data["solana"]["usd"],      "change": data["solana"]["usd_24h_change"]},
        "BNB":  {"price": data["binancecoin"]["usd"], "change": data["binancecoin"]["usd_24h_change"]},
        "HYPE": {"price": data["hyperliquid"]["usd"], "change": data["hyperliquid"]["usd_24h_change"]},
    }
    for k, v in prices.items():
        sign = "+" if v["change"] >= 0 else ""
        print(f"  {k}: ${v['price']:,.2f}  {sign}{v['change']:.1f}%")
    return prices

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
    headers = {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}
    body = {"model": "claude-sonnet-4-5", "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
    resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    raw = resp.json()["content"][0]["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    signals = json.loads(raw.strip())
    print(f"  Theme: {signals.get('session_theme')}")
    return signals

def fetch_subscribers():
    print("Fetching subscribers...")
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/subscribers?select=email,tier,active&active=eq.true", headers=headers, timeout=15)
    resp.raise_for_status()
    subs = resp.json()
    by_tier = {"starter": [], "pro": [], "vip": []}
    for s in subs:
        tier = s.get("tier", "starter").lower()
        if tier == "elite": tier = "vip"
        if tier in by_tier:
            by_tier[tier].append(s["email"])
    for tier, emails in by_tier.items():
        print(f"  {tier.upper()}: {len(emails)}")
    return by_tier

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
        sig = signals.get("signals", {}).get(ticker, {})
        bias = sig.get("bias", "")
        line = sig.get("summary_line", "")
        p = prices.get(ticker, {})
        price_str = f"${p.get('price', 0):,.2f}"
        chg = p.get("change", 0)
        chg_str = f"+{chg:.1f}%" if chg >= 0 else f"{chg:.1f}%"
        chg_col = "#00C896" if chg >= 0 else "#FF3B3B"
        rows += f'<tr><td style="padding:8px 0;border-bottom:1px solid #1E1A35;"><b style="color:#fff;">{ticker}</b> <span style="color:{chg_col};">{price_str} {chg_str}</span> <span style="color:{color};font-weight:bold;">{bias}</span><br><span style="color:#6E688A;font-size:12px;">{line}</span></td></tr>'
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
<p style="color:#6E688A;font-size:12px;margin:20px 0 0 0;">Your signal PDFs are attached. Open for full entry zones, targets and stop losses.</p>
</td></tr>
<tr><td style="padding:16px 24px;border-top:1px solid #2A2240;text-align:center;">
<p style="color:#6E688A;font-size:10px;margin:0;">AI market analysis — educational purposes only. Not financial advice.<br>Vektor Signals — vektorsignals.com</p>
</td></tr></table></body></html>"""

def send_emails(subscribers, signals, prices):
    print("Sending emails...")
    sent = 0; failed = 0
    for tier, emails in subscribers.items():
        if not emails: continue
        config = TIER_CONFIG.get(tier, TIER_CONFIG["starter"])
        html = build_email(tier, prices, signals, config)
        for email in emails:
            payload = {"from": "Vektor Signals <signals@vektorsignals.com>", "to": [email], "subject": config["subject"], "html": html}
            resp = requests.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                sent += 1; print(f"  ✅ {tier} → {email}")
            else:
                failed += 1; print(f"  ❌ {email}: {resp.text}")
    print(f"  Total: {sent} sent, {failed} failed")

def main():
    print("=" * 55)
    print(f"  VEKTOR SIGNALS — {DATE_LABEL}")
    print("=" * 55)
    prices      = fetch_prices()
    signals     = generate_signals(prices)
    subscribers = fetch_subscribers()
    send_emails(subscribers, signals, prices)
    print("\n" + "=" * 55)
    print("  COMPLETE")
    print("=" * 55)

if __name__ == "__main__":
    main()

