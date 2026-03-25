from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
import math

# ── BRAND ──────────────────────────────────────────────────────────────────────
BG         = HexColor("#080612")
CARD_BG    = HexColor("#0F0C1E")
CARD_ALT   = HexColor("#110E20")
BORDER     = HexColor("#7B2FBE")
GOLD       = HexColor("#F5C842")
WHITE      = HexColor("#FFFFFF")
MUTED      = HexColor("#6E688A")
MUTED2     = HexColor("#9A94B8")
ACCENT     = HexColor("#4DC3FF")
GREEN      = HexColor("#00C896")
RED        = HexColor("#FF3B3B")
ORANGE     = HexColor("#FF6B1A")
DIVIDER    = HexColor("#1E1A35")
VIP_GOLD   = HexColor("#FFD700")
VIP_BADGE  = HexColor("#1C1530")

BIAS_COLOURS = {
    "STRONG BUY":   HexColor("#00C896"),
    "BUY":          HexColor("#22C55E"),
    "ACCUMULATE":   HexColor("#4DC3FF"),
    "NEUTRAL":      HexColor("#9A94B8"),
    "CAUTION":      HexColor("#FFB800"),
    "REDUCE":       HexColor("#FF6B1A"),
}

RISK_COLOURS = {
    "LOW":         HexColor("#00C896"),
    "MEDIUM":      HexColor("#4DC3FF"),
    "MEDIUM-HIGH": HexColor("#FFB800"),
    "HIGH":        HexColor("#FF6B1A"),
    "VERY HIGH":   HexColor("#FF3B3B"),
}

# ── SIGNAL DATA ────────────────────────────────────────────────────────────────
SIGNALS = [
    {
        "ticker": "BTC",
        "name": "BITCOIN",
        "price": "$70,245",
        "change": "-0.3%",
        "change_pos": False,
        "bias": "ACCUMULATE",
        "risk": "MEDIUM",
        "timeframe": "3D / DAILY",
        "entry": "$68,500 – $71,500",
        "t1": "$76,000  (+8%)",
        "t2": "$82,500  (+17%)",
        "sl": "$64,800  (-8%)",
        "ma50": "$74,200",
        "ma200": "$82,100",
        "rsi": "38",
        "trend": "BEARISH CHANNEL",
        "ta": (
            "BTC confirmed descending channel from $98,769 ATH. Post-FOMC sell-off "
            "brought price to $70,245 — 8 of last 9 FOMC meetings ended in a sell-off. "
            "100-week SMA is holding as structural support. RSI at 38 is approaching "
            "oversold on daily. Watch $68,500 — major liquidation cluster per Binance heatmap."
        ),
        "catalyst": (
            "SEC/CFTC commodity classification (Mar 17) has not fully priced in. "
            "FTX $2.2B creditor payout on Mar 31 — reinvestment flow likely. "
            "BTC dominance at 58.8% — rotation into alts when BTC stabilises. "
            "Strategy adding $76.6M last week signals continued institutional bid."
        ),
    },
    {
        "ticker": "ETH",
        "name": "ETHEREUM",
        "price": "$2,124",
        "change": "-0.9%",
        "change_pos": False,
        "bias": "ACCUMULATE",
        "risk": "MEDIUM-HIGH",
        "timeframe": "DAILY / 4H",
        "entry": "$2,000 – $2,200",
        "t1": "$2,580  (+21%)",
        "t2": "$3,200  (+51%)",
        "sl": "$1,820  (-14%)",
        "ma50": "$2,650",
        "ma200": "$3,100",
        "rsi": "32",
        "trend": "MULTI-YR LOW vs BTC",
        "ta": (
            "ETH/BTC ratio at multi-year low of 0.0302 — historically this precedes "
            "major ETH outperformance rotations. Price holding just above $2,000 psychological "
            "support. RSI 32 — approaching deep oversold. Glamsterdam hard fork is the "
            "biggest ETH upgrade of the 2026 roadmap, targeting H1. BlackRock ETHB ETF "
            "inflows confirm institutional floor building despite macro headwinds."
        ),
        "catalyst": (
            "Glamsterdam hard fork targeting H1 2026 — major validator/staking upgrade. "
            "BlackRock ETHB staking ETF attracting long-term allocators. "
            "ETH/BTC at cycle lows — mean reversion alone justifies accumulation. "
            "$2,000 is the institutional line in the sand. Below it triggers stops; "
            "above it triggers FOMO from the sidelines."
        ),
    },
    {
        "ticker": "XRP",
        "name": "XRP / RIPPLE",
        "price": "$2.05",
        "change": "-0.2%",
        "change_pos": False,
        "bias": "ACCUMULATE",
        "risk": "MEDIUM-HIGH",
        "timeframe": "DAILY / WEEKLY",
        "entry": "$1.90 – $2.15",
        "t1": "$2.55  (+24%)",
        "t2": "$3.40  (+66%)",
        "sl": "$1.62  (-21%)",
        "ma50": "$2.20",
        "ma200": "$2.65",
        "rsi": "38",
        "trend": "RANGE / COILING",
        "ta": (
            "$2.00 is the critical weekly support — it has produced long-tailed "
            "weekly candles on every test, signalling seller exhaustion. "
            "5 & 10-week SMAs declining but flattening. RSI at 38 with positive divergence "
            "forming on the 4H. A close above $2.30 invalidates the bearish lower-high "
            "pattern and signals a bullish revival. XRP ETF flows recovering — "
            "outflows stopped as of this week."
        ),
        "catalyst": (
            "SEC dropped appeal — regulatory clarity fully established. "
            "XRP ETF approvals expanding globally (UK, EU, Asia). "
            "Standard Chartered $8 target for end-2026 still in play. "
            "Treasury/SWIFT integration pipeline building. "
            "Commodity classification Mar 17 removes final institutional blocker."
        ),
    },
    {
        "ticker": "SOL",
        "name": "SOLANA",
        "price": "$87.40",
        "change": "-0.4%",
        "change_pos": False,
        "bias": "ACCUMULATE",
        "risk": "MEDIUM-HIGH",
        "timeframe": "DAILY / 3D",
        "entry": "$82.00 – $92.00",
        "t1": "$105.00  (+20%)",
        "t2": "$130.00  (+49%)",
        "sl": "$74.00  (-15%)",
        "ma50": "$102.00",
        "ma200": "$138.00",
        "rsi": "40",
        "trend": "BASE BUILDING",
        "ta": (
            "SOL holding above critical $80 psychological floor after FOMC sell-off. "
            "Correlation with BTC at 0.84 — SOL needs BTC to reclaim $72K+ for a "
            "meaningful breakout. $92.34 is the short-term resistance; daily close above "
            "this targets $98.65. Firedancer upgrade + $1.66B RWA growth provide "
            "fundamental floor. Alpenglow consensus upgrade imminent — "
            "sub-200ms finality positions SOL ahead of all other L1s."
        ),
        "catalyst": (
            "Alpenglow consensus upgrade — fastest finality in L1 history when live. "
            "Nasdaq tokenised equities deploying on Solana (State Street, Franklin Templeton). "
            "SOL ETF inflows growing — institutional structural demand building. "
            "FTX $2.2B payout Mar 31 — significant SOL treasury holdings may redeploy. "
            "BTC push above $72K drags SOL to $100 based on historical correlation."
        ),
    },
    {
        "ticker": "BNB",
        "name": "BNB CHAIN",
        "price": "$650",
        "change": "+0.5%",
        "change_pos": True,
        "bias": "BUY",
        "risk": "MEDIUM",
        "timeframe": "DAILY / 4H",
        "entry": "$630 – $665",
        "t1": "$780  (+20%)",
        "t2": "$920  (+42%)",
        "sl": "$565  (-13%)",
        "ma50": "$705",
        "ma200": "$720",
        "rsi": "44",
        "trend": "RANGE / RECOVERY",
        "ta": (
            "BNB showing relative strength — green day while majors bled. "
            "Trading inside a basing range $630–$680 for 3 weeks. "
            "Maxwell Upgrade accelerated block times delivering measurable performance gains. "
            "RSI at 44 — room to run without being overbought. "
            "BNB outperforms in sideways/risk-off markets due to exchange utility demand. "
            "20-day EMA beginning to flatten and turn — early reversal signal."
        ),
        "catalyst": (
            "Maxwell Upgrade: faster block times, lower fees — measurable on-chain improvement. "
            "Binance ecosystem DeFi/GameFi TVL recovering strongly. "
            "BNB burn mechanics create continuous supply pressure. "
            "Exchange-native token demand insulated from pure sentiment swings. "
            "Regulatory classification as commodity removes key institutional barrier."
        ),
    },
    {
        "ticker": "HYPE",
        "name": "HYPERLIQUID",
        "price": "$37.30",
        "change": "+2.9%",
        "change_pos": True,
        "bias": "BUY",
        "risk": "HIGH",
        "timeframe": "DAILY / 4H",
        "entry": "$34.00 – $39.00",
        "t1": "$48.00  (+29%)",
        "t2": "$65.00  (+74%)",
        "sl": "$29.50  (-21%)",
        "ma50": "$42.00",
        "ma200": "$58.00",
        "rsi": "46",
        "trend": "RECOVERY / BULLISH",
        "ta": (
            "HYPE showing clear strength — up 2.9% on a red market day. "
            "20-day EMA at $35.50 acting as strong support. Break above 50-day SMA "
            "at $42 sets up a run to the $58–$65 zone. $178B monthly volume, $880M "
            "stablecoin reserves. HIP-4 upgrade live. Arthur Hayes $150 target by "
            "August still structural thesis. RSI at 46 — coiling before breakout."
        ),
        "catalyst": (
            "Grayscale ETF filing targeting Hyperliquid perpetual DEX exposure — "
            "first institutional product in the perp DEX space. "
            "Arthur Hayes $150 price target — $178B monthly volume validates real product. "
            "HIP-4 upgrade expands vault and liquidity provisioning. "
            "Perp DEX sector capturing CEX market share globally. "
            "HYPE decoupling from broader market — own momentum forming."
        ),
    },
]

# ── HELPERS ────────────────────────────────────────────────────────────────────
def rrect(c, x, y, w, h, r, fc=None, sc=None, sw=1):
    if fc: c.setFillColor(fc)
    if sc:
        c.setStrokeColor(sc)
        c.setLineWidth(sw)
    else:
        c.setLineWidth(0)
    c.roundRect(x, y, w, h, r, fill=1 if fc else 0, stroke=1 if sc else 0)

def txt(c, s, x, y, font, size, color, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "right":   c.drawRightString(x, y, s)
    elif align == "center": c.drawCentredString(x, y, s)
    else:                   c.drawString(x, y, s)

def wrap(c, text, x, y, max_w, font, size, color, lh):
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    line = ""
    for w2 in words:
        test = line + (" " if line else "") + w2
        if c.stringWidth(test, font, size) <= max_w:
            line = test
        else:
            if line:
                c.drawString(x, y, line)
                y -= lh
            line = w2
    if line:
        c.drawString(x, y, line)
        y -= lh
    return y

def badge(c, text, cx, cy, bg, fg=None, font="Helvetica-Bold", size=6.5):
    if fg is None: fg = WHITE
    w = c.stringWidth(text, font, size) + 12
    h = 14
    rrect(c, cx - w/2, cy - h/2, w, h, 3, fc=bg)
    txt(c, text, cx, cy - 4.5, font, size, fg, "center")

def page_bg(c, W, H):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

def draw_header(c, W, H, page=1, total_pages=2):
    # Left accent stripe
    c.setFillColor(BORDER)
    c.rect(0, H - 22*mm, 3, 22*mm, fill=1, stroke=0)

    # VEKTOR name
    txt(c, "VEKTOR", 8*mm, H - 11*mm, "Helvetica-Bold", 22, GOLD)
    vw = c.stringWidth("VEKTOR", "Helvetica-Bold", 22)
    txt(c, " VIP", 8*mm + vw, H - 11*mm, "Helvetica-Bold", 22, WHITE)

    # VIP badge
    badge(c, "★ VIP TIER", 8*mm + vw + c.stringWidth(" VIP", "Helvetica-Bold", 22) + 22,
          H - 11*mm + 1, VIP_BADGE, VIP_GOLD, size=7)

    # Right side header
    txt(c, "DAILY SIGNALS — LARGE CAP EDITION", W - 8*mm, H - 8*mm, "Helvetica-Bold", 7, MUTED2, "right")
    txt(c, "Tuesday 24 March 2026  |  07:00 GMT  |  6 ASSETS COVERED", W - 8*mm, H - 14.5*mm, "Helvetica", 6.5, MUTED, "right")
    txt(c, f"Page {page} of {total_pages}", W - 8*mm, H - 20*mm, "Helvetica", 6, MUTED, "right")

    # Divider
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.7)
    c.line(8*mm, H - 23*mm, W - 8*mm, H - 23*mm)

def draw_macro_bar(c, W, start_y):
    bar_h = 20
    rrect(c, 8*mm, start_y - bar_h, W - 16*mm, bar_h, 3,
          fc=HexColor("#0D0A1E"), sc=HexColor("#2A2240"), sw=0.5)
    items = [
        ("BTC DOM", "58.8%", MUTED2),
        ("F&G INDEX", "26  FEAR", RED),
        ("TOTAL MCAP", "$2.52T", MUTED2),
        ("DXY", "100.4  ↑", ORANGE),
        ("WTI CRUDE", "~$108/bbl", ORANGE),
        ("FED RATE", "3.50–3.75%  HOLD", MUTED2),
        ("ALTCOIN IDX", "35/100", MUTED2),
    ]
    col_w = (W - 16*mm) / len(items)
    for i, (label, val, col) in enumerate(items):
        cx = 8*mm + (i + 0.5) * col_w
        txt(c, label, cx, start_y - 8, "Helvetica", 5, MUTED, "center")
        txt(c, val, cx, start_y - 15, "Helvetica-Bold", 6.5, col, "center")

    # vertical dividers
    c.setStrokeColor(HexColor("#1E1A35"))
    c.setLineWidth(0.3)
    for i in range(1, len(items)):
        dx = 8*mm + i * col_w
        c.line(dx, start_y - 18, dx, start_y - 4)

def draw_signal_card(c, sig, x, y, card_w, card_h):
    """Draw a single signal card. Returns bottom y of card."""
    # Card BG
    rrect(c, x, y - card_h, card_w, card_h, 5, fc=CARD_BG)
    # Left colour bar — colour by bias
    bar_col = BIAS_COLOURS.get(sig["bias"], BORDER)
    c.setFillColor(bar_col)
    c.roundRect(x, y - card_h, 3, card_h, 2, fill=1, stroke=0)

    pad = 7*mm
    inner_x = x + pad
    inner_w = card_w - pad - 5*mm

    # ── ROW 1: ticker + name + price + change + badges ──
    r1_y = y - 11
    txt(c, sig["ticker"], inner_x, r1_y, "Helvetica-Bold", 16, WHITE)
    tw = c.stringWidth(sig["ticker"], "Helvetica-Bold", 16)
    txt(c, "  " + sig["name"], inner_x + tw, r1_y, "Helvetica", 8, MUTED2)

    # Price right
    txt(c, sig["price"], x + card_w - 5*mm, r1_y, "Helvetica-Bold", 13, WHITE, "right")
    price_w = c.stringWidth(sig["price"], "Helvetica-Bold", 13)
    chg_col = GREEN if sig["change_pos"] else RED
    txt(c, sig["change"], x + card_w - 5*mm - price_w - 3,
        r1_y, "Helvetica-Bold", 8.5, chg_col, "right")

    # ── ROW 2: badges ──
    r2_y = r1_y - 14
    bias_col = BIAS_COLOURS.get(sig["bias"], BORDER)
    risk_col  = RISK_COLOURS.get(sig["risk"], WHITE)
    badge(c, "● " + sig["bias"], inner_x + 24, r2_y + 4, bias_col, WHITE, size=6.5)
    badge(c, "RISK: " + sig["risk"], inner_x + 85, r2_y + 4, HexColor("#1A1630"), risk_col, size=6.5)
    badge(c, "TF: " + sig["timeframe"], inner_x + 155, r2_y + 4, HexColor("#1A1630"), ACCENT, size=6)

    # Thin divider
    c.setStrokeColor(DIVIDER)
    c.setLineWidth(0.4)
    c.line(x + 4*mm, r2_y - 6, x + card_w - 4*mm, r2_y - 6)

    # ── ROW 3: levels ──
    r3_y = r2_y - 18
    levels = [
        ("ENTRY ZONE", sig["entry"], MUTED2),
        ("TARGET 1",   sig["t1"],    GREEN),
        ("TARGET 2",   sig["t2"],    GREEN),
        ("STOP LOSS",  sig["sl"],    RED),
    ]
    col_w = inner_w / 4
    for i, (lbl, val, col) in enumerate(levels):
        cx = inner_x + i * col_w
        txt(c, lbl, cx, r3_y, "Helvetica", 5, MUTED, "left")
        txt(c, val, cx, r3_y - 10, "Helvetica-Bold", 7, col, "left")

    # ── ROW 4: indicators strip ──
    r4_y = r3_y - 24
    inds = [
        ("50 SMA", sig["ma50"]),
        ("200 SMA", sig["ma200"]),
        ("RSI", sig["rsi"]),
        ("STRUCTURE", sig["trend"]),
    ]
    for i, (lbl, val) in enumerate(inds):
        cx = inner_x + i * (inner_w / 4)
        txt(c, lbl, cx, r4_y, "Helvetica", 4.8, MUTED, "left")
        txt(c, val, cx, r4_y - 9, "Helvetica-Bold", 6.5, MUTED2, "left")

    # Thin divider
    c.setStrokeColor(DIVIDER)
    c.setLineWidth(0.3)
    c.line(x + 4*mm, r4_y - 16, x + card_w - 4*mm, r4_y - 16)

    # ── ROW 5: TA + CATALYST columns ──
    r5_y = r4_y - 24
    half = (inner_w - 4*mm) / 2

    # TA label
    txt(c, "TECHNICAL ANALYSIS", inner_x, r5_y, "Helvetica-Bold", 5.5, GOLD, "left")
    ta_y = wrap(c, sig["ta"], inner_x, r5_y - 9, half,
                "Helvetica", 5.8, MUTED2, 8)

    # CATALYST label
    cat_x = inner_x + half + 4*mm
    txt(c, "CATALYST & THESIS", cat_x, r5_y, "Helvetica-Bold", 5.5, ACCENT, "left")
    wrap(c, sig["catalyst"], cat_x, r5_y - 9, half,
         "Helvetica", 5.8, MUTED2, 8)

    return y - card_h

def draw_footer(c, W, pg):
    c.setStrokeColor(DIVIDER)
    c.setLineWidth(0.4)
    c.line(8*mm, 16, W - 8*mm, 16)
    txt(c, "AI market analysis — educational purposes only. Not financial advice. | Prices: CoinGecko/CMC | 24 Mar 2026 07:00 GMT | VEKTOR SIGNALS — vektorsignals.com",
        W/2, 9, "Helvetica", 4.8, MUTED, "center")

# ── BUILD ──────────────────────────────────────────────────────────────────────
def build(output):
    W, H = A4

    c = canvas.Canvas(output, pagesize=A4)

    # ━━━━━━━━━━━━━━ PAGE 1 ━━━━━━━━━━━━━━
    page_bg(c, W, H)
    draw_header(c, W, H, page=1, total_pages=2)
    macro_y = H - 26*mm
    draw_macro_bar(c, W, macro_y)

    card_w = W - 16*mm
    # 3 cards on page 1
    cards_p1 = SIGNALS[:3]
    card_h = [116, 116, 116]
    gap = 5
    cy = macro_y - 26

    for i, sig in enumerate(cards_p1):
        draw_signal_card(c, sig, 8*mm, cy, card_w, card_h[i])
        cy = cy - card_h[i] - gap

    draw_footer(c, W, 1)
    c.showPage()

    # ━━━━━━━━━━━━━━ PAGE 2 ━━━━━━━━━━━━━━
    page_bg(c, W, H)
    draw_header(c, W, H, page=2, total_pages=2)

    cy = H - 28*mm
    cards_p2 = SIGNALS[3:]
    card_h2 = [116, 116, 116]

    for i, sig in enumerate(cards_p2):
        draw_signal_card(c, sig, 8*mm, cy, card_w, card_h2[i])
        cy = cy - card_h2[i] - gap

    # ── Vektor Summary Box ──
    sum_y = cy - 5
    sum_h = 52
    rrect(c, 8*mm, sum_y - sum_h, card_w, sum_h, 5,
          fc=HexColor("#0D0A1E"), sc=BORDER, sw=0.6)

    txt(c, "VEKTOR VIP — DAILY MARKET SUMMARY", 8*mm + 6*mm, sum_y - 10,
        "Helvetica-Bold", 8, GOLD)

    summary_lines = [
        "MACRO: Post-FOMC sell-off digesting. Hawkish hold + 7 officials now pricing zero 2026 cuts. WTI ~$108 keeping Fed hands tied.",
        "BTC: Holding $70K critical support. Commodity classification catalyst unpriced. Watch $68.5K — key liquidation level.",
        "LARGE CAPS: ETH/BTC at multi-year lows = structural accumulation opportunity. XRP $2 defence holding. SOL base building.",
        "STANDOUT: HYPE showing relative strength on a down day — decoupling from BTC. BNB showing resilience. Both worth watching.",
        "POSITIONING: This is an accumulation window, not a chase window. Scale into positions across 2–3 entries. Keep 20–30% dry powder.",
    ]
    sy = sum_y - 20
    for line in summary_lines:
        txt(c, "▸", 8*mm + 5*mm, sy, "Helvetica-Bold", 5.5, BORDER)
        wrap(c, line, 8*mm + 9*mm, sy, card_w - 14*mm, "Helvetica", 5.8, MUTED2, 8)
        sy -= 8

    draw_footer(c, W, 2)
    c.save()
    print("VIP PDF saved.")

build("/mnt/user-data/outputs/vektor_vip_march24.pdf")
