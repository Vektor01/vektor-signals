"""
VEKTOR BLACK SWAN ALERT SYSTEM
Runs every hour via GitHub Actions.
Fires instant email + WhatsApp alert to Elite subscribers
when a major market event is detected.

Triggers:
- BTC drops -8% in 1 hour
- BTC drops -15% in 24 hours  
- Major geopolitical/exchange keywords in crypto news
"""

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
TIME_LABEL = NOW.strftime("%H:%M GMT")

# Keywords that trigger a geopolitical Black Swan alert
BLACK_SWAN_KEYWORDS = [
    "exchange hack", "exchange collapse", "exchange bankrupt",
    "war declared", "nuclear", "strait of hormuz closed",
    "binance hack", "coinbase hack", "tether collapse",
    "sec ban", "crypto banned", "bitcoin banned",
    "major exchange", "rug pull", "protocol exploit",
    "flash crash", "circuit breaker",
]

def fetch_btc_data():
    """Fetch BTC price with 1hr and 24hr change"""
    print("Checking BTC price...")
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_1hr_change=true"
    headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()["bitcoin"]
    price     = data["usd"]
    change_1h = data.get("usd_1h_change", 0)
    change_24h = data.get("usd_24h_change", 0)
    print(f"  BTC: ${price:,.0f} | 1h: {change_1h:.1f}% | 24h: {change_24h:.1f}%")
    return price, change_1h, change_24h

def check_news_triggers():
    """Check latest crypto news for Black Swan keywords"""
    print("Scanning news for Black Swan keywords...")
    try:
        url = "https://api.coingecko.com/api/v3/news"
        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            news = resp.json().get("data", [])
            for item in news[:20]:
                title = item.get("title", "").lower()
                desc  = item.get("description", "").lower()
                for keyword in BLACK_SWAN_KEYWORDS:
                    if keyword in title or keyword in desc:
                        print(f"  BLACK SWAN KEYWORD DETECTED: '{keyword}' in: {item.get('title')}")
                        return True, item.get("title", "Major crypto market event detected"), keyword
    except Exception as e:
        print(f"  News check failed: {e}")
    return False, None, None

def get_elite_subscribers():
    """Fetch only Elite/VIP subscribers"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/subscribers?select=email,tier,active&active=eq.true&tier=eq.vip",
        headers=headers, timeout=15
    )
    resp.raise_for_status()
    subs = resp.json()
    emails = [s["email"] for s in subs]
    print(f"  Elite subscribers: {len(emails)}")
    return emails

def generate_alert_analysis(price, change_1h, change_24h, trigger_type, news_headline=None):
    """Use Claude to generate instant alert analysis"""
    print("Generating alert analysis via Claude...")

    if trigger_type == "1H_CRASH":
        context = f"BTC just crashed {change_1h:.1f}% in the last hour. Current price: ${price:,.0f}. 24hr change: {change_24h:.1f}%."
    elif trigger_type == "24H_CRASH":
        context = f"BTC is down {change_24h:.1f}% in 24 hours. Current price: ${price:,.0f}. Hourly change: {change_1h:.1f}%."
    else:
        context = f"Major crypto news event detected: '{news_headline}'. BTC at ${price:,.0f}, down {change_24h:.1f}% in 24hrs."

    prompt = f"""You are Vektor Signals issuing an emergency Black Swan Alert.

Situation: {context}

Generate an urgent but calm alert. Respond ONLY in valid JSON:
{{
  "headline": "5-8 word urgent headline",
  "severity": "CRITICAL or HIGH",
  "what_happened": "2 sentences explaining what triggered this alert",
  "immediate_action": "2 sentences on what subscribers should do RIGHT NOW",
  "key_levels": "2 sentences on key BTC support levels to watch",
  "outlook": "1 sentence on what happens next if support holds vs breaks"
}}"""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    body = {
        "model": "claude-sonnet-4-5",
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}]
    }
    resp = requests.post("https://api.anthropic.com/v1/messages",
                        headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    raw = resp.json()["content"][0]["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    return json.loads(raw.strip())

def send_black_swan_email(emails, price, change_1h, change_24h, analysis):
    """Send urgent Black Swan Alert email"""
    print(f"Sending Black Swan Alert to {len(emails)} Elite subscribers...")
    severity_col = "#FF3B3B" if analysis.get("severity") == "CRITICAL" else "#FF6B1A"

    html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#080612;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#0F0C1E;border:2px solid {severity_col};">

<tr><td style="padding:0;">
  <div style="background:{severity_col};padding:12px 24px;text-align:center;">
    <span style="font-size:18px;font-weight:bold;color:#fff;letter-spacing:2px;">
      ⚠ VEKTOR BLACK SWAN ALERT ⚠
    </span>
  </div>
</td></tr>

<tr><td style="padding:20px 24px;border-bottom:1px solid #2A2240;">
  <span style="font-size:22px;font-weight:bold;color:#F5C842;">VEKTOR</span>
  <span style="font-size:22px;font-weight:bold;color:#fff;"> ELITE</span>
  <span style="background:{severity_col};color:#fff;font-size:11px;font-weight:bold;padding:3px 10px;border-radius:12px;margin-left:10px;">{analysis.get('severity')}</span>
  <p style="color:#6E688A;font-size:12px;margin:6px 0 0 0;">{DATE_LABEL} — {TIME_LABEL}</p>
</td></tr>

<tr><td style="padding:20px 24px;">
  <p style="color:{severity_col};font-size:20px;font-weight:bold;margin:0 0 16px 0;">
    {analysis.get('headline')}
  </p>

  <div style="background:#1A0810;border-left:4px solid {severity_col};padding:12px 16px;margin-bottom:16px;">
    <p style="color:#fff;font-size:13px;margin:0 0 4px 0;font-weight:bold;">PRICE SNAPSHOT</p>
    <p style="color:#9A94B8;font-size:13px;margin:0;">
      BTC: <b style="color:#fff;">${price:,.0f}</b> &nbsp;|&nbsp;
      1hr: <b style="color:{severity_col};">{change_1h:+.1f}%</b> &nbsp;|&nbsp;
      24hr: <b style="color:{severity_col};">{change_24h:+.1f}%</b>
    </p>
  </div>

  <p style="color:#9A94B8;font-size:13px;font-weight:bold;margin:0 0 4px 0;">WHAT HAPPENED</p>
  <p style="color:#fff;font-size:13px;margin:0 0 16px 0;">{analysis.get('what_happened')}</p>

  <p style="color:#F5C842;font-size:13px;font-weight:bold;margin:0 0 4px 0;">⚡ IMMEDIATE ACTION</p>
  <p style="color:#fff;font-size:13px;margin:0 0 16px 0;">{analysis.get('immediate_action')}</p>

  <p style="color:#4DC3FF;font-size:13px;font-weight:bold;margin:0 0 4px 0;">KEY LEVELS</p>
  <p style="color:#fff;font-size:13px;margin:0 0 16px 0;">{analysis.get('key_levels')}</p>

  <p style="color:#6E688A;font-size:13px;font-weight:bold;margin:0 0 4px 0;">OUTLOOK</p>
  <p style="color:#9A94B8;font-size:13px;margin:0;">{analysis.get('outlook')}</p>
</td></tr>

<tr><td style="padding:16px 24px;border-top:1px solid #2A2240;text-align:center;">
  <p style="color:#6E688A;font-size:10px;margin:0;">
    AI market analysis — educational purposes only. Not financial advice.<br>
    Vektor Signals — vektorsignals.com | Elite Black Swan Alert System
  </p>
</td></tr>
</table></body></html>"""

    sent = 0
    for email in emails:
        payload = {
            "from": "Vektor Signals <signals@vektorsignals.com>",
            "to": [email],
            "subject": f"⚠ VEKTOR BLACK SWAN ALERT — {analysis.get('headline')} — {TIME_LABEL}",
            "html": html,
        }
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json=payload, timeout=30
        )
        if resp.status_code in (200, 201):
            sent += 1
            print(f"  ✅ Alert sent to {email}")
        else:
            print(f"  ❌ Failed {email}: {resp.text}")
    print(f"  Black Swan Alert: {sent} sent")

def log_alert_to_supabase(price, change_1h, change_24h, trigger_type, analysis):
    """Log the alert to Supabase for records"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "alert_time": NOW.isoformat(),
        "trigger_type": trigger_type,
        "btc_price": price,
        "change_1h": change_1h,
        "change_24h": change_24h,
        "headline": analysis.get("headline"),
        "severity": analysis.get("severity"),
    }
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/black_swan_alerts",
            headers=headers, json=payload, timeout=10
        )
    except:
        pass  # Don't fail the alert if logging fails

def main():
    print("=" * 55)
    print(f"  VEKTOR BLACK SWAN MONITOR — {TIME_LABEL}")
    print("=" * 55)

    price, change_1h, change_24h = fetch_btc_data()
    trigger_type  = None
    news_headline = None

    # Check hourly crash
    if change_1h <= -8.0:
        print(f"  🚨 HOURLY CRASH DETECTED: {change_1h:.1f}%")
        trigger_type = "1H_CRASH"

    # Check 24hr crash
    elif change_24h <= -15.0:
        print(f"  🚨 24HR CRASH DETECTED: {change_24h:.1f}%")
        trigger_type = "24H_CRASH"

    # Check news
    else:
        news_triggered, news_headline, keyword = check_news_triggers()
        if news_triggered:
            trigger_type = "NEWS_EVENT"

    if trigger_type:
        print(f"\n  *** BLACK SWAN ALERT TRIGGERED: {trigger_type} ***\n")
        analysis = generate_alert_analysis(price, change_1h, change_24h, trigger_type, news_headline)
        print(f"  Headline: {analysis.get('headline')}")
        emails = get_elite_subscribers()
        if emails:
            send_black_swan_email(emails, price, change_1h, change_24h, analysis)
            log_alert_to_supabase(price, change_1h, change_24h, trigger_type, analysis)
        else:
            print("  No Elite subscribers to alert yet.")
    else:
        print("  ✅ No Black Swan conditions detected. Market normal.")

    print("\n" + "=" * 55)
    print("  MONITOR COMPLETE")
    print("=" * 55)

if __name__ == "__main__":
    main()
