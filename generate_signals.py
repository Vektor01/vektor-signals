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

def send_summary_email(prices, signals):
    print("Sending summary email...")
    theme = signals.get("session_theme", "Daily Signals")
    price_rows = "".join([
        f'<tr><td style="padding:6px 0;color:#9A94B8;font-size:13px;border-bottom:1px solid #1E1A35;"><b style="color:#fff;">{k}</b> &nbsp; <span style="color:{"#00C896" if v["change"]>=0 else "#FF3B3B"};">${v["price"]:,.2f} &nbsp; {"+" if v["change"]>=0 else ""}{v["change"]:.1f}%</span> &nbsp; <span style="color:#6E688A;">{signals["signals"].get(k,{}).get("bias","")}</span></td></tr>'
        for k, v in prices.items()
    ])
    html = f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#080612;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#0F0C1E;border:1px solid #2A2240;">
<tr><td style="padding:24px;border-bottom:1px solid #2A2240;">
<span style="font-size:22px;font-weight:bold;color:#F5C842;">VEKTOR</span>
<span style="font-size:22px;font-weight:bold;color:#fff;"> SIGNALS</span>
<p style="color:#6E688A;font-size:12px;margin:8px 0 0 0;">{DATE_LABEL} — Automated Daily Run</p>
</td></tr>
<tr><td style="padding:20px 24px;">
<p style="color:#fff;font-size:15px;font-weight:bold;margin:0 0 4px 0;">"{theme}"</p>
<p style="color:#9A94B8;font-size:13px;margin:0 0 20px 0;">{signals.get("macro_summary","")}</p>
<table width="100%" cellpadding="0" cellspacing="0">{price_rows}</table>
<p style="color:#6E688A;font-size:11px;margin:20px 0 0 0;">Automation running successfully. PDFs generating next.</p>
</td></tr>
<tr><td style="padding:16px 24px;border-top:1px solid #2A2240;text-align:center;">
<p style="color:#6E688A;font-size:10px;margin:0;">AI market analysis — educational purposes only. Not financial advice.<br>Vektor Signals — vektorsignals.com</p>
</td></tr></table></body></html>"""
    payload = {"from": "Vektor Signals <onboarding@resend.dev>", "to": ["markwclohessy@gmail.com"], "subject": f"⚡ Vektor Automation Live — {DATE_LABEL}", "html": html}
    resp = requests.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        print("  Email sent successfully!")
    else:
        print(f"  Email failed: {resp.text}")

def main():
    print("=" * 50)
    print(f"  VEKTOR SIGNALS — {DATE_LABEL}")
    print("=" * 50)
    prices  = fetch_prices()
    signals = generate_signals(prices)
    send_summary_email(prices, signals)
    print("\n" + "=" * 50)
    print("  COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
