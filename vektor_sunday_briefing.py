from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

BG      = HexColor("#080612")
CARD_BG = HexColor("#0F0C1E")
BORDER  = HexColor("#7B2FBE")
GOLD    = HexColor("#F5C842")
WHITE   = HexColor("#FFFFFF")
MUTED   = HexColor("#6E688A")
MUTED2  = HexColor("#9A94B8")
ACCENT  = HexColor("#4DC3FF")
GREEN   = HexColor("#00C896")
RED     = HexColor("#FF3B3B")
ORANGE  = HexColor("#FF6B1A")
DIVIDER = HexColor("#1E1A35")
AMBER   = HexColor("#FFB800")

def rrect(c, x, y, w, h, r, fc=None, sc=None, sw=1):
    if fc: c.setFillColor(fc)
    if sc: c.setStrokeColor(sc); c.setLineWidth(sw)
    else: c.setLineWidth(0)
    c.roundRect(x, y, w, h, r, fill=1 if fc else 0, stroke=1 if sc else 0)

def txt(c, s, x, y, font, size, color, align="left"):
    c.setFont(font, size); c.setFillColor(color)
    if align == "right": c.drawRightString(x, y, s)
    elif align == "center": c.drawCentredString(x, y, s)
    else: c.drawString(x, y, s)

def wrap(c, text, x, y, max_w, font, size, color, lh):
    c.setFont(font, size); c.setFillColor(color)
    words = text.split(); line = ""
    for w2 in words:
        test = line + (" " if line else "") + w2
        if c.stringWidth(test, font, size) <= max_w: line = test
        else:
            if line: c.drawString(x, y, line); y -= lh
            line = w2
    if line: c.drawString(x, y, line); y -= lh
    return y

def section_header(c, title, x, y, card_w, color=GOLD):
    c.setFillColor(color)
    c.roundRect(x, y - 16, 4, 16, 2, fill=1, stroke=0)
    txt(c, title, x + 10, y - 12, "Helvetica-Bold", 9, color)
    c.setStrokeColor(DIVIDER); c.setLineWidth(0.4)
    c.line(x + 10 + c.stringWidth(title, "Helvetica-Bold", 9) + 8, y - 8, x + card_w - 10, y - 8)
    return y - 22

def build_weekly(output, date_label, week_label, data):
    W, H = A4; mm = 2.835
    c = canvas.Canvas(output, pagesize=A4)
    c.setFillColor(BG); c.rect(0, 0, W, H, fill=1, stroke=0)

    # Left accent
    c.setFillColor(BORDER); c.rect(0, 0, 4, H, fill=1, stroke=0)

    # ── HEADER ──
    hdr_y = H - 18*mm
    txt(c, "VEKTOR", 10*mm, hdr_y, "Helvetica-Bold", 28, GOLD)
    vw = c.stringWidth("VEKTOR", "Helvetica-Bold", 28)
    txt(c, " ELITE", 10*mm + vw, hdr_y, "Helvetica-Bold", 28, WHITE)

    bw = c.stringWidth("★ SUNDAY BRIEFING", "Helvetica-Bold", 7.5) + 14
    rrect(c, 10*mm + vw + c.stringWidth(" ELITE", "Helvetica-Bold", 28) + 10,
          hdr_y - 8, bw, 16, 8, fc=HexColor("#1C1530"))
    txt(c, "★ SUNDAY BRIEFING",
        10*mm + vw + c.stringWidth(" ELITE", "Helvetica-Bold", 28) + 10 + bw/2,
        hdr_y - 2, "Helvetica-Bold", 7.5, GOLD, "center")

    txt(c, f"WEEK AHEAD BRIEFING — {week_label}", W - 10*mm, hdr_y, "Helvetica-Bold", 7, MUTED2, "right")
    txt(c, f"{date_label}  |  18:00 GMT  |  ELITE SUBSCRIBERS ONLY", W - 10*mm, hdr_y - 10, "Helvetica", 6.5, MUTED, "right")

    c.setStrokeColor(BORDER); c.setLineWidth(0.8)
    c.line(10*mm, hdr_y - 16, W - 10*mm, hdr_y - 16)

    pad = 10*mm; card_w = W - 20*mm
    cy = hdr_y - 24

    # ── MACRO EVENTS CALENDAR ──
    cal_h = 85
    rrect(c, pad, cy - cal_h, card_w, cal_h, 5, fc=CARD_BG)
    c.setFillColor(ACCENT); c.roundRect(pad, cy - cal_h, 3, cal_h, 2, fill=1, stroke=0)
    inner = pad + 7*mm

    cy2 = section_header(c, "WEEK AHEAD — MACRO EVENTS CALENDAR", inner, cy, card_w, ACCENT)

    events = data.get("events", [])
    col_w = (card_w - 14*mm) / 2
    for i, event in enumerate(events[:6]):
        ex = inner + (i % 2) * col_w
        ey = cy2 - (i // 2) * 18
        dot_col = RED if event.get("impact") == "HIGH" else AMBER if event.get("impact") == "MEDIUM" else GREEN
        c.setFillColor(dot_col); c.circle(ex + 4, ey - 3, 3, fill=1, stroke=0)
        txt(c, event.get("day", ""), ex + 11, ey, "Helvetica-Bold", 7, WHITE)
        dw = c.stringWidth(event.get("day", ""), "Helvetica-Bold", 7)
        txt(c, f"  {event.get('name', '')}", ex + 11 + dw, ey, "Helvetica", 7, MUTED2)
        txt(c, event.get("time", ""), ex + 11, ey - 9, "Helvetica", 6, MUTED)

    cy = cy - cal_h - 6

    # ── BTC/ETH KEY LEVELS ──
    levels_h = 72
    rrect(c, pad, cy - levels_h, card_w, levels_h, 5, fc=CARD_BG)
    c.setFillColor(GOLD); c.roundRect(pad, cy - levels_h, 3, levels_h, 2, fill=1, stroke=0)

    cy2 = section_header(c, "KEY LEVELS TO WATCH — BTC & ETH", inner, cy, card_w, GOLD)

    assets_levels = data.get("key_levels", {})
    half = (card_w - 14*mm) / 2

    for ai, (asset, levels) in enumerate(assets_levels.items()):
        ax = inner + ai * half
        txt(c, asset, ax, cy2, "Helvetica-Bold", 10, WHITE)
        lv_y = cy2 - 12
        for lbl, val, col in levels:
            txt(c, lbl, ax, lv_y, "Helvetica", 6, MUTED)
            txt(c, val, ax + 55, lv_y, "Helvetica-Bold", 7.5, col)
            lv_y -= 11

    cy = cy - levels_h - 6

    # ── TOP 3 NARRATIVES ──
    narr_h = 80
    rrect(c, pad, cy - narr_h, card_w, narr_h, 5, fc=CARD_BG)
    c.setFillColor(HexColor("#22C55E")); c.roundRect(pad, cy - narr_h, 3, narr_h, 2, fill=1, stroke=0)

    cy2 = section_header(c, "TOP 3 NARRATIVES FOR THE WEEK", inner, cy, card_w, HexColor("#22C55E"))

    narratives = data.get("narratives", [])
    for i, narr in enumerate(narratives[:3]):
        ny = cy2 - i * 20
        rrect(c, inner, ny - 15, 16, 15, 3, fc=HexColor("#1A3A2A"))
        txt(c, str(i+1), inner + 8, ny - 5, "Helvetica-Bold", 8, GREEN, "center")
        txt(c, narr.get("title", ""), inner + 22, ny - 4, "Helvetica-Bold", 8, WHITE)
        tw = c.stringWidth(narr.get("title", ""), "Helvetica-Bold", 8)
        txt(c, f" — {narr.get('detail', '')}", inner + 22 + tw, ny - 4, "Helvetica", 7.5, MUTED2)

    cy = cy - narr_h - 6

    # ── PORTFOLIO POSITIONING ──
    pos_h = 75
    rrect(c, pad, cy - pos_h, card_w, pos_h, 5, fc=CARD_BG)
    c.setFillColor(BORDER); c.roundRect(pad, cy - pos_h, 3, pos_h, 2, fill=1, stroke=0)

    cy2 = section_header(c, "PORTFOLIO POSITIONING — WEEK AHEAD", inner, cy, card_w, BORDER)

    positioning = data.get("positioning", [])
    col_w3 = (card_w - 14*mm) / 3
    for i, pos in enumerate(positioning[:3]):
        px = inner + i * col_w3
        bias_col = GREEN if pos.get("bias") == "BUY" else RED if pos.get("bias") == "SELL" else AMBER
        rrect(c, px, cy2 - 14, col_w3 - 6, 14, 3, fc=HexColor("#1A1630"))
        txt(c, pos.get("asset", ""), px + 6, cy2 - 7, "Helvetica-Bold", 8, WHITE)
        aw = c.stringWidth(pos.get("asset", ""), "Helvetica-Bold", 8)
        txt(c, f"  {pos.get('bias', '')}", px + 6 + aw, cy2 - 7, "Helvetica-Bold", 7, bias_col)
        wrap(c, pos.get("note", ""), px + 6, cy2 - 24, col_w3 - 10, "Helvetica", 6.5, MUTED2, 8)

    cy = cy - pos_h - 6

    # ── DEGEN PICKS OF THE WEEK ──
    degen_h = 90
    rrect(c, pad, cy - degen_h, card_w, degen_h, 5, fc=CARD_BG)
    c.setFillColor(RED); c.roundRect(pad, cy - degen_h, 3, degen_h, 2, fill=1, stroke=0)

    cy2 = section_header(c, "DEGEN PICKS — WEEKLY SPECULATIVE WATCHLIST", inner, cy, card_w, RED)

    degen = data.get("degen_picks", [])
    col_w5 = (card_w - 14*mm) / 5
    for i, pick in enumerate(degen[:5]):
        dx = inner + i * col_w5
        rrect(c, dx, cy2 - 52, col_w5 - 4, 52, 4, fc=HexColor("#1A0810"))
        txt(c, pick.get("ticker", ""), dx + (col_w5-4)/2, cy2 - 12, "Helvetica-Bold", 9, WHITE, "center")
        txt(c, pick.get("price", ""), dx + (col_w5-4)/2, cy2 - 24, "Helvetica-Bold", 7.5, MUTED2, "center")
        # Risk badge
        rrect(c, dx + 4, cy2 - 36, col_w5 - 12, 10, 3, fc=RED)
        txt(c, "DEGEN", dx + (col_w5-4)/2, cy2 - 29, "Helvetica-Bold", 5.5, WHITE, "center")
        txt(c, pick.get("target", ""), dx + (col_w5-4)/2, cy2 - 44, "Helvetica-Bold", 7, GREEN, "center")

    cy = cy - degen_h - 6

    # ── FOOTER ──
    c.setStrokeColor(DIVIDER); c.setLineWidth(0.4)
    c.line(10*mm, 16, W - 10*mm, 16)
    txt(c, "AI market analysis — educational purposes only. Not financial advice. | VEKTOR SIGNALS — vektorsignals.com",
        W/2, 9, "Helvetica", 5, MUTED, "center")

    c.save()
    print("Sunday Briefing done.")


# ── SAMPLE DATA — replace with live Claude-generated data on Sundays ──
SAMPLE_DATA = {
    "events": [
        {"day": "MON", "name": "US Consumer Confidence", "time": "15:00 GMT", "impact": "MEDIUM"},
        {"day": "TUE", "name": "Fed Speaker — Powell", "time": "18:00 GMT", "impact": "HIGH"},
        {"day": "WED", "name": "US ADP Employment", "time": "13:15 GMT", "impact": "MEDIUM"},
        {"day": "THU", "name": "US GDP Final Q4", "time": "13:30 GMT", "impact": "HIGH"},
        {"day": "FRI", "name": "PCE Inflation Data", "time": "13:30 GMT", "impact": "HIGH"},
        {"day": "FRI", "name": "BTC Options Expiry", "time": "08:00 GMT", "impact": "HIGH"},
    ],
    "key_levels": {
        "BTC / USD": [
            ("Resistance 2", "$75,000", HexColor("#FF6B1A")),
            ("Resistance 1", "$72,000", HexColor("#FFB800")),
            ("Current",      "$71,400", HexColor("#FFFFFF")),
            ("Support 1",    "$68,500", HexColor("#4DC3FF")),
            ("Support 2",    "$64,800", HexColor("#00C896")),
        ],
        "ETH / USD": [
            ("Resistance 2", "$2,600", HexColor("#FF6B1A")),
            ("Resistance 1", "$2,300", HexColor("#FFB800")),
            ("Current",      "$2,182", HexColor("#FFFFFF")),
            ("Support 1",    "$2,000", HexColor("#4DC3FF")),
            ("Support 2",    "$1,820", HexColor("#00C896")),
        ],
    },
    "narratives": [
        {"title": "Options Expiry + PCE = Volatility Week", "detail": "$14.16B BTC options expire Friday. PCE below 2.8% triggers rally toward $75K"},
        {"title": "SOL Institutional Breakout", "detail": "Mastercard/Western Union SDP launch is the biggest SOL catalyst of Q1 2026"},
        {"title": "Altcoin Season Index Rising", "detail": "Index recovering from extreme lows — selective rotation into quality mid-caps beginning"},
    ],
    "positioning": [
        {"asset": "BTC", "bias": "ACCUMULATE", "note": "Scale into $68-72K range. Options expiry creates upside drift toward $75K this week"},
        {"asset": "ETH", "bias": "BUY", "note": "RSI recovering from 30. ETH/BTC at cycle lows = highest conviction accumulation zone"},
        {"asset": "SOL", "bias": "BUY", "note": "Breaking $92 resistance. SDP launch with Mastercard is a genuine institutional catalyst"},
    ],
    "degen_picks": [
        {"ticker": "HYPE", "price": "$38.50", "target": "T: $50 (+30%)"},
        {"ticker": "AERO", "price": "$0.34",  "target": "T: $0.58 (+71%)"},
        {"ticker": "FARTCOIN", "price": "$0.21", "target": "T: $0.36 (+71%)"},
        {"ticker": "QUBIC", "price": "$0.000051", "target": "T: +80%"},
        {"ticker": "HBAR", "price": "$0.104",  "target": "T: $0.168 (+62%)"},
    ],
}

if __name__ == "__main__":
    from datetime import datetime
    now = datetime.utcnow()
    date_label = now.strftime("%A %d %B %Y")
    # Get next Monday date for week label
    week_label = "31 March – 4 April 2026"
    build_weekly("/mnt/user-data/outputs/vektor_sunday_briefing.pdf",
                 date_label, week_label, SAMPLE_DATA)
