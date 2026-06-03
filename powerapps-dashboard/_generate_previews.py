#!/usr/bin/env python3
"""
Generates PREVIEW svgs (mock data baked in) + PNG renders for the
1% Club HPE-styled PowerApps dashboard. The PowerApps formula templates
live in README.md; this script is only to design/verify the visuals.
"""
import os, cairosvg

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "Liberation Sans, Arial, Helvetica, sans-serif"  # preview font (PowerApps uses Segoe UI)

# ---- HPE Design System · semantic color tokens (light mode) ----
C = dict(
    canvas="#f7f7f7", card="#ffffff", contrast="#f2f3f4",
    border="#d4d8db", borderStrong="#b1b9be",
    text="#3e4550", strong="#292d3a", weak="#606a70",
    brand="#01a982", green="#05cc93", greenBtn="#068667",
    greenDark="#006750", greenTint="#d1ffee",
    blue="#0070f8", purple="#7764fc", teal="#04909d",
    magenta="#cc54a4", coral="#d25f4b",
    ok="#009a71", warn="#d36d00", crit="#cc1f1a",
)
GOLD, GOLD_T = "#E0A300", "#FBF1D6"
SILVER, SILVER_T = "#8C99A4", "#EDEFF1"
BRONZE, BRONZE_T = "#B5742E", "#F4E9DD"
MEDALS = [(GOLD, GOLD_T, "1st"), (SILVER, SILVER_T, "2nd"), (BRONZE, BRONZE_T, "3rd")]

# personal category accent colors (HPE dataVis categorical)
CATCOL = [C["blue"], C["teal"], C["ok"], C["purple"], C["magenta"], C["coral"]]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def shadow(x, y, w, h, rx, op=0.10):
    return (f"<rect x='{x}' y='{y+4}' width='{w}' height='{h}' rx='{rx}' "
            f"fill='#000000' opacity='{op}' filter='url(#blur)'/>")


def initials(name):
    p = [w for w in name.split() if w]
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper()


DEFS = (
    "<defs><filter id='blur' x='-20%' y='-20%' width='140%' height='140%'>"
    "<feGaussianBlur stdDeviation='5'/></filter></defs>"
)

# HPE-aligned motion: purposeful, smooth, low-amplitude. Hidden states live ONLY
# in @keyframes (never on base attrs) so static renders show the settled design,
# while WebView2/Chromium plays the animation. Honors reduced-motion.
CSS = (
    "<style>"
    ".fu{animation:fu .55s cubic-bezier(.2,.7,.2,1) both}"
    ".fo{animation:fo .5s ease-out both}"
    ".pp{animation:pp .5s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box;transform-origin:center}"
    ".gx{animation:gx .65s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box;transform-origin:left center}"
    ".rw{animation:rw .5s cubic-bezier(.2,.7,.2,1) both}"
    ".ring{transform-box:fill-box;transform-origin:center;animation:ring 2.8s ease-out infinite}"
    ".brz{animation:brz 2.6s ease-in-out infinite}"
    "@keyframes fu{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
    "@keyframes fo{from{opacity:0}to{opacity:1}}"
    "@keyframes pp{from{opacity:0;transform:scale(.5)}to{opacity:1;transform:scale(1)}}"
    "@keyframes gx{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    "@keyframes rw{from{opacity:0;transform:translateX(-18px)}to{opacity:1;transform:none}}"
    "@keyframes ring{0%{opacity:.45;transform:scale(.75)}70%{opacity:0;transform:scale(2)}100%{opacity:0;transform:scale(2)}}"
    "@keyframes brz{0%,100%{opacity:.9}50%{opacity:.45}}"
    "@media(prefers-reduced-motion:reduce){.fu,.fo,.pp,.gx,.rw,.ring,.brz{animation:none}}"
    "</style>"
)

# =========================================================================
# 1) PODIUM  (top 3 crews) — viewBox 920 x 440
# =========================================================================
def podium_inner(top3):
    W, H = 920, 440
    base = 430
    cols = [  # (cx, top, medalIdx)
        (180, 132, 1),   # 2nd  (left)
        (460, 70,  0),   # 1st  (center)
        (740, 162, 2),   # 3rd  (right)
    ]
    card_delay = {0: 0.34, 1: 0.18, 2: 0.05}   # winner (#1) revealed last
    medal_delay = {0: 0.55, 1: 0.39, 2: 0.26}
    s = [DEFS, CSS]
    for (cx, top, mi), crew in zip(cols, [top3[1], top3[0], top3[2]]):
        medal, tint, ord_ = MEDALS[mi]
        cw = 232
        x = cx - cw / 2
        h = base - top
        my = top + 56
        g = [f"<g class='fu' style='animation-delay:{card_delay[mi]}s'>"]
        g.append(shadow(x, top, cw, h, 16))
        g.append(f"<rect x='{x}' y='{top}' width='{cw}' height='{h}' rx='16' "
                 f"fill='{C['card']}' stroke='{C['border']}'/>")
        g.append(f"<path d='M{x+1},{top+15} v-1 a14,14 0 0 1 14,-14 h{cw-30} "
                 f"a14,14 0 0 1 14,14 v1 z' fill='{medal}'/>")
        # champion idle halo (1st only)
        if mi == 0:
            g.append(f"<circle cx='{cx}' cy='{my}' r='30' fill='none' stroke='{medal}' stroke-width='2' class='ring' opacity='0'/>")
        # medal pops in
        g.append(f"<g class='pp' style='animation-delay:{medal_delay[mi]}s'>")
        g.append(f"<circle cx='{cx}' cy='{my}' r='30' fill='{tint}' stroke='{medal}' stroke-width='2'/>")
        g.append(f"<text x='{cx}' y='{my+1}' font-family='{FONT}' font-size='22' font-weight='700' "
                 f"fill='{medal}' text-anchor='middle' dominant-baseline='central'>{esc(crew['rank'])}</text>")
        g.append("</g>")
        g.append(f"<text x='{cx}' y='{my+58}' font-family='{FONT}' font-size='22' font-weight='700' "
                 f"fill='{C['strong']}' text-anchor='middle'>{esc(crew['name'])}</text>")
        g.append(f"<text x='{cx}' y='{my+108}' font-family='{FONT}' font-size='44' font-weight='700' "
                 f"fill='{C['greenDark']}' text-anchor='middle'>{esc(crew['pts'])}</text>")
        g.append(f"<text x='{cx}' y='{my+130}' font-family='{FONT}' font-size='12' font-weight='600' "
                 f"letter-spacing='1.5' fill='{C['weak']}' text-anchor='middle'>TOTAL POINTS</text>")
        pend = crew['pending']
        py = base - 34
        if pend and int(pend) > 0:
            label, fg, bg = f"+{pend} pending", C['warn'], "#FBEEDF"
        else:
            label, fg, bg = "no pending", C['weak'], C['contrast']
        pw = 8 * len(label) + 26
        g.append(f"<rect x='{cx-pw/2}' y='{py}' width='{pw}' height='24' rx='12' fill='{bg}'/>")
        g.append(f"<text x='{cx}' y='{py+16}' font-family='{FONT}' font-size='12' font-weight='600' "
                 f"fill='{fg}' text-anchor='middle'>{esc(label)}</text>")
        g.append("</g>")
        s.append("".join(g))
    return W, H, "".join(s)


# =========================================================================
# 2) LEADERBOARD ROW  (gallery, ranks 4..10) — viewBox 920 x 84
# =========================================================================
def row_inner(r, leader_pts):
    W, H = 920, 84
    d = max(0.0, (int(r['rank']) - 4) * 0.08)   # stagger rows as the gallery appears
    s = [DEFS, CSS]
    g = [f"<g class='rw' style='animation-delay:{d:.2f}s'>"]
    g.append(shadow(4, 8, W - 8, 64, 12, op=0.07))
    g.append(f"<rect x='4' y='8' width='{W-8}' height='64' rx='12' fill='{C['card']}' stroke='{C['border']}'/>")
    g.append(f"<rect x='22' y='18' width='44' height='44' rx='10' fill='{C['contrast']}'/>")
    g.append(f"<text x='44' y='40' font-family='{FONT}' font-size='20' font-weight='700' "
             f"fill='{C['strong']}' text-anchor='middle' dominant-baseline='central'>{esc(r['rank'])}</text>")
    g.append(f"<text x='86' y='37' font-family='{FONT}' font-size='21' font-weight='700' "
             f"fill='{C['strong']}'>{esc(r['name'])}</text>")
    pct = (float(r['pts']) / leader_pts) if leader_pts else 0
    bx, bw = 86, 460
    g.append(f"<rect x='{bx}' y='50' width='{bw}' height='7' rx='3.5' fill='{C['contrast']}'/>")
    g.append(f"<rect x='{bx}' y='50' width='{max(6,bw*pct):.0f}' height='7' rx='3.5' fill='{C['brand']}' "
             f"class='gx' style='animation-delay:{d+0.25:.2f}s'/>")
    g.append(f"<line x1='735' y1='22' x2='735' y2='58' stroke='{C['border']}'/>")
    g.append(f"<text x='820' y='44' font-family='{FONT}' font-size='30' font-weight='700' "
             f"fill='{C['strong']}' text-anchor='end'>{esc(r['pts'])}</text>")
    g.append(f"<text x='828' y='44' font-family='{FONT}' font-size='13' font-weight='600' "
             f"fill='{C['weak']}'>pts</text>")
    pend = r['pending']
    if pend and int(pend) > 0:
        g.append(f"<text x='890' y='62' font-family='{FONT}' font-size='12.5' font-weight='600' "
                 f"fill='{C['warn']}' text-anchor='end'>+{esc(pend)} pending</text>")
    else:
        g.append(f"<text x='890' y='62' font-family='{FONT}' font-size='12.5' "
                 f"fill='{C['weak']}' text-anchor='end'>no pending</text>")
    g.append("</g>")
    s.append("".join(g))
    return W, H, "".join(s)


# =========================================================================
# 3) CREW MEMBER GRID (non-gallery, whole crew) — viewBox 440 x 600
# =========================================================================
def grid_inner(crew_name, members, current):
    W, H = 440, 600
    s = [DEFS, CSS]
    # heading
    s.append(f"<text x='14' y='28' font-family='{FONT}' font-size='17' font-weight='700' "
             f"fill='{C['strong']}'>{esc(crew_name)} · Members</text>")
    s.append(f"<text x='{W-14}' y='28' font-family='{FONT}' font-size='13' "
             f"fill='{C['weak']}' text-anchor='end'>{len(members)} people</text>")
    tw, th, gx, gy, x0, y0 = 204, 92, 8, 10, 12, 46
    for i, m in enumerate(members):
        col, rowi = i % 2, i // 2
        x = x0 + col * (tw + gx)
        y = y0 + rowi * (th + gy)
        me = (m['name'] == current)
        fill = C['greenTint'] if me else C['card']
        stroke = C['brand'] if me else C['border']
        sw = 2 if me else 1
        g = [f"<g class='pp' style='animation-delay:{0.10 + i*0.05:.2f}s'>"]
        g.append(shadow(x, y, tw, th, 12, op=0.05))
        g.append(f"<rect x='{x}' y='{y}' width='{tw}' height='{th}' rx='12' fill='{fill}' "
                 f"stroke='{stroke}' stroke-width='{sw}'/>")
        if me:  # idle breathing highlight on the viewer's tile
            g.append(f"<rect x='{x}' y='{y}' width='{tw}' height='{th}' rx='12' fill='none' "
                     f"stroke='{C['brand']}' stroke-width='2' class='brz' opacity='0'/>")
        nm = m['name'] if len(m['name']) <= 20 else m['name'][:19] + "…"
        g.append(f"<text x='{x+16}' y='{y+28}' font-family='{FONT}' font-size='13.5' font-weight='600' "
                 f"fill='{C['strong'] if me else C['text']}'>{esc(nm)}</text>")
        if me:
            g.append(f"<text x='{x+tw-14}' y='{y+27}' font-family='{FONT}' font-size='10.5' font-weight='700' "
                     f"letter-spacing='.5' fill='{C['greenDark']}' text-anchor='end'>YOU</text>")
        g.append(f"<text x='{x+16}' y='{y+74}' font-family='{FONT}' font-size='30' font-weight='700' "
                 f"fill='{C['greenDark'] if me else C['strong']}'>{esc(m['pts'])}</text>")
        g.append(f"<text x='{x+16+len(str(m['pts']))*18+6}' y='{y+74}' font-family='{FONT}' font-size='12' "
                 f"fill='{C['weak']}'>pts</text>")
        g.append("</g>")
        s.append("".join(g))
    return W, H, "".join(s)


# =========================================================================
# 4) MY POINTS box (current user breakdown) — viewBox 440 x 360
# =========================================================================
def mypoints_inner(u):
    W, H = 440, 360
    s = [DEFS, CSS, "<g class='fu'>"]
    s.append(shadow(2, 2, W - 4, H - 6, 16, op=0.08))
    s.append(f"<rect x='2' y='2' width='{W-4}' height='{H-6}' rx='16' fill='{C['card']}' stroke='{C['border']}'/>")
    # avatar: idle halo + pop-in disc
    s.append(f"<circle cx='44' cy='50' r='26' fill='none' stroke='{C['brand']}' stroke-width='2' class='ring' opacity='0'/>")
    s.append("<g class='pp' style='animation-delay:.12s'>")
    s.append(f"<circle cx='44' cy='50' r='26' fill='{C['brand']}'/>")
    s.append(f"<text x='44' y='51' font-family='{FONT}' font-size='19' font-weight='700' fill='#ffffff' "
             f"text-anchor='middle' dominant-baseline='central'>{esc(initials(u['name']))}</text>")
    s.append("</g>")
    s.append(f"<text x='82' y='44' font-family='{FONT}' font-size='20' font-weight='700' fill='{C['strong']}'>{esc(u['name'])}</text>")
    s.append(f"<text x='82' y='66' font-family='{FONT}' font-size='13' fill='{C['weak']}'>{esc(u['crew'])} · You</text>")
    # total (right)
    s.append(f"<text x='{W-22}' y='48' font-family='{FONT}' font-size='38' font-weight='700' "
             f"fill='{C['greenDark']}' text-anchor='end'>{esc(u['total'])}</text>")
    s.append(f"<text x='{W-22}' y='66' font-family='{FONT}' font-size='10.5' font-weight='600' letter-spacing='1' "
             f"fill='{C['weak']}' text-anchor='end'>TOTAL · EXCL PENDING</text>")
    # pending chip (idle pulse to flag action)
    pend = u['pending']
    if pend and int(pend) > 0:
        pw = 8*len(str(pend))+78
        s.append(f"<g class='brz'><rect x='82' y='78' width='{pw}' height='20' rx='10' fill='#FBEEDF'/>")
        s.append(f"<text x='{82+pw/2}' y='92' font-family='{FONT}' font-size='11.5' font-weight='600' "
                 f"fill='{C['warn']}' text-anchor='middle'>+{esc(pend)} pending</text></g>")
    # divider
    s.append(f"<line x1='22' y1='110' x2='{W-22}' y2='110' stroke='{C['border']}'/>")
    # category cards 2x3
    cards = [
        ("New CC Logo / IB Upsell", u['newcc']),
        ("CAP Engagement",          u['capeng']),
        ("CAP Orders Booked",       u['caporders']),
        ("Customer Centricity",     u['cc']),
        ("Accreditation Race",      u['accred']),
        ("IP Push",                 u['ip']),
    ]
    cw, ch, gx, gy, x0, y0 = 194, 68, 12, 12, 22, 122
    for i, (label, val) in enumerate(cards):
        col, rowi = i % 2, i // 2
        x = x0 + col * (cw + gx)
        y = y0 + rowi * (ch + gy)
        acc = CATCOL[i]
        s.append(f"<g class='fo' style='animation-delay:{0.28 + i*0.07:.2f}s'>")
        s.append(f"<rect x='{x}' y='{y}' width='{cw}' height='{ch}' rx='10' fill='#fbfcfc' stroke='{C['border']}'/>")
        s.append(f"<rect x='{x}' y='{y}' width='6' height='{ch}' rx='3' fill='{acc}'/>")
        s.append(f"<circle cx='{x+22}' cy='{y+22}' r='4' fill='{acc}'/>")
        s.append(f"<text x='{x+34}' y='{y+26}' font-family='{FONT}' font-size='11' font-weight='600' "
                 f"fill='{C['weak']}'>{esc(label)}</text>")
        s.append(f"<text x='{x+18}' y='{y+56}' font-family='{FONT}' font-size='24' font-weight='700' "
                 f"fill='{C['strong']}'>{esc(val)}</text>")
        s.append("</g>")
    s.append("</g>")
    return W, H, "".join(s)


def wrap(w, h, inner, bg=None):
    b = f"<rect x='0' y='0' width='{w}' height='{h}' fill='{bg}'/>" if bg else ""
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' "
            f"width='{w}' height='{h}'>{b}{inner}</svg>")


def save(name, svg):
    p = os.path.join(OUT, "svg", name + ".svg")
    open(p, "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, "previews", name + ".png"), scale=2)
    print("wrote", name)


# ----------------------------- MOCK DATA -----------------------------
TOP3 = [
    dict(rank=1, name="Crew 3", pts=580, pending=20),
    dict(rank=2, name="Crew 5", pts=480, pending=0),
    dict(rank=3, name="Crew 7", pts=480, pending=0),
]
REST = [
    dict(rank=4, name="Crew 10", pts=420, pending=0),
    dict(rank=5, name="Crew 4", pts=410, pending=0),
    dict(rank=6, name="Crew 1", pts=370, pending=0),
    dict(rank=7, name="Crew 2", pts=270, pending=0),
    dict(rank=8, name="Crew 9", pts=160, pending=0),
    dict(rank=9, name="Crew 6", pts=60, pending=0),
    dict(rank=10, name="Crew 8", pts=0, pending=0),
]
MEMBERS = [
    dict(name="Jordan Smith", pts=0), dict(name="Quinn White", pts=20),
    dict(name="Avery Anderson", pts=0), dict(name="Jordan Brown", pts=0),
    dict(name="Rowan Johnson", pts=40), dict(name="Alex Brown", pts=0),
    dict(name="Morgan White", pts=0), dict(name="Alex Jackson", pts=310),
]
USER = dict(name="Alex Jackson", crew="Crew 1", total=310, pending=30,
            newcc=120, capeng=40, caporders=60, cc=30, accred=20, ip=40)

# standalone components
pW, pH, pInner = podium_inner(TOP3)
save("podium", wrap(pW, pH, pInner))
rW, rH, rInner = row_inner(REST[0], TOP3[0]['pts'])
save("leaderboard-row", wrap(rW, rH, rInner))
gW, gH, gInner = grid_inner("Crew 1", MEMBERS, "Alex Jackson")
save("crew-grid", wrap(gW, gH, gInner))
mW, mH, mInner = mypoints_inner(USER)
save("my-points", wrap(mW, mH, mInner))

# gallery preview = several rows stacked
stack = []
for i, r in enumerate(REST[:7]):
    _, _, ri = row_inner(r, TOP3[0]['pts'])
    stack.append(f"<svg x='0' y='{i*84}' width='920' height='84' viewBox='0 0 920 84'>{ri}</svg>")
save("leaderboard-gallery", wrap(920, 84*7, "".join(stack)))

# =========================================================================
# FULL PAGE — HPE two-column dashboard composition (design reference only)
# =========================================================================
def place(x, y, w, h, vw, vh, inner):
    return f"<svg x='{x}' y='{y}' width='{w}' height='{h}' viewBox='0 0 {vw} {vh}'>{inner}</svg>"


def label(x, y, t):
    return (f"<text x='{x}' y='{y}' font-family='{FONT}' font-size='15' font-weight='700' "
            f"letter-spacing='.3' fill='{C['strong']}'>{esc(t)}</text>")


def page():
    W, H = 1366, 1180
    LX, LW = 24, 440
    RX = LX + LW + 24
    RW = W - RX - 24
    s = [DEFS, f"<rect x='0' y='0' width='{W}' height='{H}' fill='{C['canvas']}'/>"]
    # app bar
    s.append(f"<rect x='0' y='0' width='{W}' height='64' fill='{C['card']}'/>")
    s.append(f"<line x1='0' y1='64' x2='{W}' y2='64' stroke='{C['border']}'/>")
    s.append(f"<rect x='24' y='18' width='28' height='28' rx='6' fill='{C['brand']}'/>")
    s.append(f"<text x='62' y='40' font-family='{FONT}' font-size='19' font-weight='700' fill='{C['strong']}'>1% Club <tspan fill='{C['weak']}' font-weight='400'>· Crew Dashboard</tspan></text>")
    s.append(f"<rect x='{W-220}' y='16' width='196' height='32' rx='16' fill='{C['contrast']}'/>")
    s.append(f"<circle cx='{W-196}' cy='32' r='11' fill='{C['brand']}'/>")
    s.append(f"<text x='{W-196}' y='33' font-family='{FONT}' font-size='10' font-weight='700' fill='#fff' text-anchor='middle' dominant-baseline='central'>AJ</text>")
    s.append(f"<text x='{W-176}' y='37' font-family='{FONT}' font-size='13' fill='{C['text']}'>Alex Jackson · Crew 1</text>")
    # LEFT column
    s.append(label(LX, 100, "YOUR PERFORMANCE"))
    s.append(place(LX, 112, LW, 360, 440, 360, mypoints_inner(USER)))
    s.append(place(LX, 496, LW, 600, 440, 600, grid_inner("Crew 1", MEMBERS, "Alex Jackson")))
    # RIGHT column
    s.append(label(RX, 100, "CREW LEADERBOARD"))
    podH = int(RW * 440 / 920)
    s.append(place(RX, 112, RW, podH, 920, 440, podium_inner(TOP3)))
    gy = 112 + podH + 18
    s.append(label(RX, gy, "RANKS 4–10"))
    gy += 12
    rowH = int(RW * 84 / 920)
    for i, r in enumerate(REST):
        _, _, ri = row_inner(r, TOP3[0]['pts'])
        s.append(place(RX, gy + i * rowH, RW, rowH, 920, 84, ri))
    return W, H, "".join(s)


pw, ph, pin = page()
save("full-page-mockup", wrap(pw, ph, pin, bg=C['canvas']))

print("done")
