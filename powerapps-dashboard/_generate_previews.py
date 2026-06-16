#!/usr/bin/env python3
"""
Generates PREVIEW svgs (mock data) + PNG renders for the 1% Club HPE dashboard,
laid out to fill a LOCKED 1136 x 640 PowerApps screen.

Role-aware:
  member    -> left = personal "My Points" + own crew grid ; own crew flagged in board
  sponsor   -> left = sponsored-crew summary + that crew grid ; sponsored crew flagged
  spectator -> left = slow auto-scrolling tour of every crew's points breakdown
PowerApps formula templates live in formulas/*.powerfx ; this only designs/verifies.
"""
import os, math, cairosvg
OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "Liberation Sans, Arial, Helvetica, sans-serif"   # preview font (PowerApps uses Segoe UI)

C = dict(
    canvas="#f7f7f7", card="#ffffff", contrast="#f2f3f4",
    border="#d4d8db", borderStrong="#b1b9be",
    text="#3e4550", strong="#292d3a", weak="#606a70",
    brand="#01a982", greenDark="#006750", greenTint="#d1ffee",
    blue="#0070f8", purple="#7764fc", teal="#04909d", magenta="#cc54a4", coral="#d25f4b",
    ok="#009a71", warn="#d36d00",
)
GOLD, GOLD_T = "#E0A300", "#FBF1D6"
SILVER, SILVER_T = "#8C99A4", "#EDEFF1"
BRONZE, BRONZE_T = "#B5742E", "#F4E9DD"
MEDALS = [(GOLD, GOLD_T), (SILVER, SILVER_T), (BRONZE, BRONZE_T)]
CATCOL = [C["blue"], C["teal"], C["ok"], C["purple"], C["magenta"], C["coral"]]
CATLBL = ["New CC Logo / IB Upsell", "CAP Engagement", "CAP Orders Booked",
          "Customer Centricity", "Accreditation Race", "IP Push"]

PAGE_W, PAGE_H = 1136, 640
RIB_H = 52
LX, LW = 16, 420
RX, RW = 452, 668
TOP = 68
MP = (LX, TOP, LW, 300)
GR = (LX, 380, LW, 244)
PD = (RX, TOP, RW, 300)
RH = (RX, 380, RW, 28)
GAL = (RX, 412, RW, 212)
ROW_H = 30
SPEC = (LX, TOP, LW, 556)     # spectator fills the whole left column


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def shadow(x, y, w, h, rx, op=0.10):
    return (f"<rect x='{x:.0f}' y='{y+4:.0f}' width='{w:.0f}' height='{h:.0f}' rx='{rx}' "
            f"fill='#000000' opacity='{op}' filter='url(#blur)'/>")


def initials(name):
    p = [w for w in str(name).split() if w]
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper() if p else "?"


def eyebrow(x, y, t, anchor="start", fill=None):
    return (f"<text x='{x}' y='{y}' font-family='{FONT}' font-size='11' font-weight='700' "
            f"letter-spacing='1.2' fill='{fill or C['weak']}' text-anchor='{anchor}'>{esc(t)}</text>")


DEFS = ("<defs><filter id='blur' x='-20%' y='-20%' width='140%' height='140%'>"
        "<feGaussianBlur stdDeviation='5'/></filter></defs>")

CSS = (
    "<style>"
    ".fu{animation:fu .55s cubic-bezier(.2,.7,.2,1) both}"
    ".fo{animation:fo .5s ease-out both}"
    ".pp{animation:pp .5s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box;transform-origin:center}"
    ".gx{animation:gx .65s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box;transform-origin:left center}"
    ".rw{animation:rw .5s cubic-bezier(.2,.7,.2,1) both}"
    ".ring{transform-box:fill-box;transform-origin:center;animation:ring 2.8s ease-out infinite}"
    ".brz{animation:brz 2.6s ease-in-out infinite}"
    ".bob{transform-box:fill-box;transform-origin:center;animation:bob 2.4s ease-in-out infinite}"
    "@keyframes fu{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
    "@keyframes fo{from{opacity:0}to{opacity:1}}"
    "@keyframes pp{from{opacity:0;transform:scale(.5)}to{opacity:1;transform:scale(1)}}"
    "@keyframes gx{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    "@keyframes rw{from{opacity:0;transform:translateX(-18px)}to{opacity:1;transform:none}}"
    "@keyframes ring{0%{opacity:.45;transform:scale(.75)}70%{opacity:0;transform:scale(2)}100%{opacity:0;transform:scale(2)}}"
    "@keyframes brz{0%,100%{opacity:.9}50%{opacity:.45}}"
    "@keyframes bob{0%,100%{transform:translateY(0) rotate(-4deg)}50%{transform:translateY(-2px) rotate(4deg)}}"
    "@media(prefers-reduced-motion:reduce){.fu,.fo,.pp,.gx,.rw,.ring,.brz,.scrl,.bob{animation:none}}"
    "</style>"
)


def flag(cx, top, tag):
    """green 'your crew / you sponsor' tab centred above a podium card."""
    w = 7 * len(tag) + 22
    return (f"<g class='pp'><rect x='{cx-w/2:.0f}' y='{top-19}' width='{w:.0f}' height='18' rx='9' fill='{C['brand']}'/>"
            f"<text x='{cx:.0f}' y='{top-10}' font-family='{FONT}' font-size='10' font-weight='700' "
            f"letter-spacing='.4' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>{esc(tag)}</text></g>")


# ---------------------------------------------------------------- RIBBON
def ribbon_inner(u):
    W, H = PAGE_W, RIB_H
    s = [DEFS, CSS, "<g class='fu'>"]
    s.append(f"<rect x='0' y='0' width='{W}' height='{H}' fill='{C['card']}'/>")
    s.append(f"<line x1='0' y1='{H-1}' x2='{W}' y2='{H-1}' stroke='{C['border']}'/>")
    s.append(f"<rect x='16' y='13' width='26' height='26' rx='7' fill='{C['brand']}'/>")
    s.append(f"<text x='29' y='27' font-family='{FONT}' font-size='11' font-weight='700' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>1%</text>")
    s.append(f"<text x='54' y='32' font-family='{FONT}' font-size='17' font-weight='700' fill='{C['strong']}'>1% Club <tspan fill='{C['weak']}' font-weight='400'>&#183; Crew Dashboard</tspan></text>")
    cw = 244
    cx = W - 16 - cw
    s.append(f"<rect x='{cx}' y='10' width='{cw}' height='32' rx='16' fill='{C['contrast']}'/>")
    s.append(f"<circle cx='{cx+20}' cy='26' r='12' fill='{C['brand']}'/>")
    s.append(f"<text x='{cx+20}' y='27' font-family='{FONT}' font-size='10' font-weight='700' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>{esc(u['ini'])}</text>")
    s.append(f"<text x='{cx+40}' y='30' font-family='{FONT}' font-size='13' fill='{C['text']}'>{esc(u['chip'])}</text>")
    s.append("</g>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- MY POINTS / CREW SUMMARY
def mypoints_inner(d):
    W, H = MP[2], MP[3]
    s = [DEFS, CSS]
    s.append(eyebrow(4, 16, d['title']))
    s.append("<g class='fu'>")
    s.append(shadow(2, 24, W - 4, H - 28, 14, op=0.07))
    s.append(f"<rect x='2' y='24' width='{W-4}' height='{H-28}' rx='14' fill='{C['card']}' stroke='{C['border']}'/>")
    s.append(f"<circle cx='38' cy='60' r='18' fill='none' stroke='{C['brand']}' stroke-width='2' class='ring' opacity='0'/>")
    s.append("<g class='pp' style='animation-delay:120ms'>")
    s.append(f"<circle cx='38' cy='60' r='18' fill='{C['brand']}'/>")
    s.append(f"<text x='38' y='61' font-family='{FONT}' font-size='14' font-weight='700' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>{esc(d['ini'])}</text>")
    s.append("</g>")
    s.append(f"<text x='64' y='55' font-family='{FONT}' font-size='15' font-weight='700' fill='{C['strong']}'>{esc(d['name'])}</text>")
    s.append(f"<text x='64' y='72' font-family='{FONT}' font-size='11.5' fill='{C['weak']}'>{esc(d['sub'])}</text>")
    s.append(f"<text x='{W-16}' y='56' font-family='{FONT}' font-size='28' font-weight='700' fill='{C['greenDark']}' text-anchor='end'>{esc(d['total'])}</text>")
    s.append(f"<text x='{W-16}' y='71' font-family='{FONT}' font-size='8.5' font-weight='600' letter-spacing='.6' fill='{C['weak']}' text-anchor='end'>{esc(d['totlbl'])}</text>")
    pend = d['pending']
    if pend and int(pend) > 0:
        pw = 7 * len(str(pend)) + 66
        s.append(f"<g class='brz'><rect x='64' y='80' width='{pw}' height='17' rx='8.5' fill='#FBEEDF'/>")
        s.append(f"<text x='{64+pw/2}' y='91' font-family='{FONT}' font-size='10' font-weight='600' fill='{C['warn']}' text-anchor='middle'>+{esc(pend)} pending</text></g>")
    s.append(f"<line x1='18' y1='104' x2='{W-18}' y2='104' stroke='{C['border']}'/>")
    x0, y0, gxx, gyy = 18, 112, 12, 8
    cwid = (W - 2*x0 - gxx) / 2
    chei = (H - 8 - y0 - 2*gyy) / 3
    for i, (label, val) in enumerate(zip(CATLBL, d['vals'])):
        col, rowi = i % 2, i // 2
        x = x0 + col * (cwid + gxx)
        y = y0 + rowi * (chei + gyy)
        acc = CATCOL[i]
        s.append(f"<g class='fo' style='animation-delay:{0.28+i*0.07:.2f}s'>")
        s.append(f"<rect x='{x:.0f}' y='{y:.0f}' width='{cwid:.0f}' height='{chei:.0f}' rx='10' fill='#fbfcfc' stroke='{C['border']}'/>")
        s.append(f"<rect x='{x:.0f}' y='{y:.0f}' width='5' height='{chei:.0f}' rx='2.5' fill='{acc}'/>")
        s.append(f"<circle cx='{x+20:.0f}' cy='{y+19:.0f}' r='3.5' fill='{acc}'/>")
        s.append(f"<text x='{x+30:.0f}' y='{y+22:.0f}' font-family='{FONT}' font-size='10.5' font-weight='600' fill='{C['weak']}'>{esc(label)}</text>")
        s.append(f"<text x='{x+16:.0f}' y='{y+chei-11:.0f}' font-family='{FONT}' font-size='19' font-weight='700' fill='{C['strong']}'>{esc(val)}</text>")
        s.append("</g>")
    s.append("</g>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- CREW GRID
def grid_inner(crew_name, members, current):
    W, H = GR[2], GR[3]
    s = [DEFS, CSS]
    s.append(eyebrow(4, 16, crew_name.upper()[:20] + " · MEMBERS"))
    s.append(f"<text x='{W-4}' y='16' font-family='{FONT}' font-size='11' fill='{C['weak']}' text-anchor='end'>{len(members)} people</text>")
    n = len(members)
    rows = max(1, math.ceil(n / 2))
    x0, y0, gxx, gyy = 2, 26, 8, 8
    tw = (W - 2*x0 - gxx) / 2
    th = (H - y0 - (rows-1)*gyy) / rows
    for i, m in enumerate(members):
        col, rowi = i % 2, i // 2
        x = x0 + col * (tw + gxx)
        y = y0 + rowi * (th + gyy)
        me = (m['name'] == current)
        fill = C['greenTint'] if me else C['card']
        stroke = C['brand'] if me else C['border']
        s.append(f"<g class='pp' style='animation-delay:{0.10+i*0.05:.2f}s'>")
        s.append(f"<rect x='{x:.0f}' y='{y:.0f}' width='{tw:.0f}' height='{th:.0f}' rx='11' fill='{fill}' stroke='{stroke}' stroke-width='{2 if me else 1}'/>")
        if me:
            s.append(f"<rect x='{x:.0f}' y='{y:.0f}' width='{tw:.0f}' height='{th:.0f}' rx='11' fill='none' stroke='{C['brand']}' stroke-width='2' class='brz' opacity='0'/>")
        nm = m['name'] if len(m['name']) <= 22 else m['name'][:21] + "…"
        s.append(f"<text x='{x+14:.0f}' y='{y+22:.0f}' font-family='{FONT}' font-size='12.5' font-weight='600' fill='{C['strong'] if me else C['text']}'>{esc(nm)}</text>")
        if me:
            s.append(f"<text x='{x+tw-12:.0f}' y='{y+21:.0f}' font-family='{FONT}' font-size='9.5' font-weight='700' letter-spacing='.5' fill='{C['greenDark']}' text-anchor='end'>YOU</text>")
        s.append(f"<text x='{x+14:.0f}' y='{y+th-11:.0f}' font-family='{FONT}' font-size='20' font-weight='700' fill='{C['greenDark'] if me else C['strong']}'>{esc(m['pts'])}</text>")
        s.append(f"<text x='{x+14+len(str(m['pts']))*12+5:.0f}' y='{y+th-11:.0f}' font-family='{FONT}' font-size='11' fill='{C['weak']}'>pts</text>")
        s.append("</g>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- PODIUM (+ crew flag)
def podium_inner(top3, my_crew=None, tag="YOUR CREW"):
    W, H = PD[2], PD[3]
    base = 292
    cols = [(148, 120, 1, 0.18, 0.39), (334, 78, 0, 0.34, 0.55), (520, 142, 2, 0.05, 0.26)]
    s = [DEFS, CSS]
    s.append(eyebrow(4, 16, "CREW LEADERBOARD"))
    s.append(f"<text x='{W-4}' y='16' font-family='{FONT}' font-size='11' fill='{C['weak']}' text-anchor='end'>Top 3 crews</text>")
    cw = 180
    for (cx, top, mi, cd, md), crew in zip(cols, [top3[1], top3[0], top3[2]]):
        medal, tint = MEDALS[mi]
        x = cx - cw/2
        h = base - top
        my = top + 36
        match = (my_crew is not None and crew.get('num') == my_crew)
        g = [f"<g class='fu' style='animation-delay:{cd}s'>"]
        g.append(shadow(x, top, cw, h, 14))
        g.append(f"<rect x='{x:.0f}' y='{top}' width='{cw}' height='{h}' rx='14' fill='{C['card']}' stroke='{C['border']}'/>")
        g.append(f"<path d='M{x+1:.0f},{top+14} v-1 a13,13 0 0 1 13,-13 h{cw-28} a13,13 0 0 1 13,13 v1 z' fill='{medal}'/>")
        if mi == 0:
            g.append(f"<circle cx='{cx}' cy='{my}' r='22' fill='none' stroke='{medal}' stroke-width='2' class='ring' opacity='0'/>")
        g.append(f"<g class='pp' style='animation-delay:{md}s'>")
        g.append(f"<circle cx='{cx}' cy='{my}' r='22' fill='{tint}' stroke='{medal}' stroke-width='2'/>")
        g.append(f"<text x='{cx}' y='{my+1}' font-family='{FONT}' font-size='18' font-weight='700' fill='{medal}' text-anchor='middle' dominant-baseline='central'>{esc(crew['rank'])}</text>")
        g.append("</g>")
        g.append(f"<text x='{cx}' y='{top+76}' font-family='{FONT}' font-size='17' font-weight='700' fill='{C['strong']}' text-anchor='middle'>{esc(str(crew['name'])[:16])}</text>")
        g.append(f"<text x='{cx}' y='{top+112}' font-family='{FONT}' font-size='30' font-weight='700' fill='{C['greenDark']}' text-anchor='middle'>{esc(crew['pts'])}</text>")
        g.append(f"<text x='{cx}' y='{top+128}' font-family='{FONT}' font-size='9' font-weight='600' letter-spacing='1' fill='{C['weak']}' text-anchor='middle'>TOTAL POINTS</text>")
        pend = crew['pending']
        py = base - 30
        if pend and int(pend) > 0:
            label, fg, bg = f"+{pend} pending", C['warn'], "#FBEEDF"
        else:
            label, fg, bg = "no pending", C['weak'], C['contrast']
        pw = 7 * len(label) + 24
        g.append(f"<rect x='{cx-pw/2:.0f}' y='{py}' width='{pw}' height='22' rx='11' fill='{bg}'/>")
        g.append(f"<text x='{cx}' y='{py+15}' font-family='{FONT}' font-size='11' font-weight='600' fill='{fg}' text-anchor='middle'>{esc(label)}</text>")
        if match:
            g.append(f"<rect x='{x:.0f}' y='{top}' width='{cw}' height='{h}' rx='14' fill='none' stroke='{C['brand']}' stroke-width='2.5'/>")
            g.append(flag(cx, top, tag))
        g.append("</g>")
        s.append("".join(g))
    return W, H, "".join(s)


# ---------------------------------------------------------------- RANKS HEADER
def ranks_header_inner(total_crews):
    W, H = RH[2], RH[3]
    s = [DEFS, CSS]
    s.append(eyebrow(4, 19, "RANKS 4–10"))
    s.append(f"<text x='{W-4}' y='19' font-family='{FONT}' font-size='11' fill='{C['weak']}' text-anchor='end'>{total_crews} crews total</text>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- ROW (+ crew flag)
def row_inner(r, leader_pts, my_crew=None, tag="YOUR CREW"):
    W, H = RW, ROW_H
    d = max(0.0, (int(r['rank']) - 4) * 0.08)
    match = (my_crew is not None and r.get('num') == my_crew)
    s = [DEFS, CSS]
    g = [f"<g class='rw' style='animation-delay:{d:.2f}s'>"]
    g.append(f"<rect x='2' y='2' width='{W-4}' height='{H-4}' rx='8' fill='{C['greenTint'] if match else C['card']}' stroke='{C['brand'] if match else C['border']}' stroke-width='{2 if match else 1}'/>")
    if match:
        g.append(f"<rect x='2' y='2' width='5' height='{H-4}' rx='2.5' fill='{C['brand']}'/>")
    chipbg = C['brand'] if match else C['contrast']
    chipfg = "#ffffff" if match else C['strong']
    g.append(f"<rect x='10' y='5' width='20' height='20' rx='6' fill='{chipbg}'/>")
    g.append(f"<text x='20' y='15' font-family='{FONT}' font-size='11' font-weight='700' fill='{chipfg}' text-anchor='middle' dominant-baseline='central'>{esc(r['rank'])}</text>")
    nm22 = str(r['name'])[:22]
    g.append(f"<text x='40' y='19' font-family='{FONT}' font-size='13' font-weight='700' fill='{C['greenDark'] if match else C['strong']}'>{esc(nm22)}</text>")
    if match:
        nx = 40 + len(nm22) * 7 + 8
        tw = 7 * len(tag) + 16
        g.append(f"<rect x='{nx:.0f}' y='8' width='{tw}' height='14' rx='7' fill='{C['greenTint']}' stroke='{C['brand']}'/>")
        g.append(f"<text x='{nx+tw/2:.0f}' y='15' font-family='{FONT}' font-size='8.5' font-weight='700' letter-spacing='.3' fill='{C['greenDark']}' text-anchor='middle' dominant-baseline='central'>{esc(tag)}</text>")
    pct = (float(r['pts']) / leader_pts) if leader_pts else 0
    bx, bw = 190, 358
    fw = max(4, bw * pct)
    shipx = bx + fw
    g.append(f"<rect x='{bx}' y='15' width='{bw}' height='7' rx='3.5' fill='#eef1f3'/>")              # sea lane
    g.append(f"<rect x='{bx}' y='15' width='{fw:.0f}' height='7' rx='3.5' fill='{C['brand']}' class='gx' style='animation-delay:{d+0.25:.2f}s'/>")  # water
    g.append(f"<g class='fo' style='animation-delay:{d+0.5:.2f}s' transform='translate({shipx:.0f},15)'>")
    g.append("<path d='M-12,5 q3,-3 6,0 t6,0 t6,0' fill='none' stroke='#ffffff' stroke-width='1.4' opacity='.7'/>")  # bow wave
    g.append("<g class='bob'>")
    g.append("<path d='M-8,-1 L8,-1 L5,4 L-5,4 Z' fill='#292d3a'/>")                                  # hull
    g.append("<line x1='0' y1='-1' x2='0' y2='-12' stroke='#292d3a' stroke-width='1.4'/>")           # mast
    g.append("<path d='M1.5,-11 L7,-2 L1.5,-2 Z' fill='#ffffff' stroke='#b1b9be' stroke-width='.5'/>")  # mainsail
    g.append("<path d='M-1.5,-9 L-5.5,-2 L-1.5,-2 Z' fill='#ffffff' stroke='#b1b9be' stroke-width='.5'/>")  # jib
    g.append(f"<path d='M0,-12 L4,-11 L0,-10 Z' fill='{C['brand']}'/>")                               # pennant
    g.append("</g></g>")
    g.append(f"<text x='{W-70}' y='20' font-family='{FONT}' font-size='16' font-weight='700' fill='{C['strong']}' text-anchor='end'>{esc(r['pts'])}</text>")
    g.append(f"<text x='{W-66}' y='20' font-family='{FONT}' font-size='10' font-weight='600' fill='{C['weak']}'>pts</text>")
    if r['pending'] and int(r['pending']) > 0:
        g.append(f"<text x='{W-10}' y='20' font-family='{FONT}' font-size='10' font-weight='600' fill='{C['warn']}' text-anchor='end'>+{esc(r['pending'])}</text>")
    g.append("</g>")
    s.append("".join(g))
    return W, H, "".join(s)


# ---------------------------------------------------------------- SPECTATOR (auto-scroll tour)
def spectator_inner(crews):
    W, H = SPEC[2], SPEC[3]
    cardH, gap = 150, 10
    n = len(crews)
    contentH = n * cardH + (n-1) * gap
    visT, visB = 36, H - 10
    visH = visB - visT
    dist = max(0, contentH - visH)
    dur = max(24, n * 4)
    s = [DEFS, CSS,
         f"<style>.scrl{{animation:scrl {dur}s linear infinite alternate}}"
         f"@keyframes scrl{{from{{transform:translateY(0)}}to{{transform:translateY(-{dist}px)}}}}"
         f"@media(prefers-reduced-motion:reduce){{.scrl{{animation:none}}}}</style>",
         f"<clipPath id='spec'><rect x='6' y='{visT}' width='{W-12}' height='{visH}' rx='12'/></clipPath>"]
    s.append(eyebrow(4, 16, "ALL CREWS — LIVE TOUR"))
    s.append(f"<circle cx='{W-12}' cy='12' r='4' fill='{C['brand']}' class='brz'/>")
    s.append(f"<text x='{W-22}' y='16' font-family='{FONT}' font-size='10' font-weight='600' fill='{C['weak']}' text-anchor='end'>auto</text>")
    s.append(f"<rect x='4' y='{visT-2}' width='{W-8}' height='{visH+4}' rx='14' fill='{C['card']}' stroke='{C['border']}'/>")
    s.append(f"<g clip-path='url(#spec)'><g class='scrl'>")
    cw = W - 24
    for k, cr in enumerate(crews):
        y = visT + 6 + k * (cardH + gap)
        s.append(f"<g transform='translate(12,{y})'>")
        s.append(f"<rect x='0' y='0' width='{cw}' height='{cardH}' rx='12' fill='#fbfcfc' stroke='{C['border']}'/>")
        # header
        mi = cr['rank'] - 1
        medal = MEDALS[mi][0] if mi < 3 else C['weak']
        s.append(f"<circle cx='26' cy='28' r='15' fill='{MEDALS[mi][1] if mi<3 else C['contrast']}' stroke='{medal}' stroke-width='1.5'/>")
        s.append(f"<text x='26' y='29' font-family='{FONT}' font-size='13' font-weight='700' fill='{medal}' text-anchor='middle' dominant-baseline='central'>{cr['rank']}</text>")
        s.append(f"<text x='50' y='24' font-family='{FONT}' font-size='16' font-weight='700' fill='{C['strong']}'>{esc(str(cr['name'])[:24])}</text>")
        s.append(f"<text x='50' y='40' font-family='{FONT}' font-size='10.5' fill='{C['weak']}'>rank #{cr['rank']}</text>")
        s.append(f"<text x='{cw-14}' y='26' font-family='{FONT}' font-size='24' font-weight='700' fill='{C['greenDark']}' text-anchor='end'>{cr['total']}</text>")
        s.append(f"<text x='{cw-14}' y='40' font-family='{FONT}' font-size='8.5' font-weight='600' letter-spacing='.5' fill='{C['weak']}' text-anchor='end'>TOTAL POINTS</text>")
        # 6 mini category bars
        mx = max([1] + list(cr['vals']))
        by, bh, brow = 54, 13, 15
        for i, (lbl, v) in enumerate(zip(CATLBL, cr['vals'])):
            yy = by + i * brow
            s.append(f"<circle cx='14' cy='{yy+5}' r='3' fill='{CATCOL[i]}'/>")
            s.append(f"<text x='22' y='{yy+8}' font-family='{FONT}' font-size='9.5' fill='{C['text']}'>{esc(lbl)}</text>")
            tx, tw2 = 196, cw - 196 - 44
            s.append(f"<rect x='{tx}' y='{yy+1}' width='{tw2}' height='7' rx='3.5' fill='{C['contrast']}'/>")
            s.append(f"<rect x='{tx}' y='{yy+1}' width='{max(3, tw2*v/mx):.0f}' height='7' rx='3.5' fill='{CATCOL[i]}'/>")
            s.append(f"<text x='{cw-14}' y='{yy+8}' font-family='{FONT}' font-size='9.5' font-weight='700' fill='{C['strong']}' text-anchor='end'>{v}</text>")
        s.append("</g>")
    s.append("</g></g>")
    return W, H, "".join(s)


def wrap(w, h, inner, bg=None):
    b = f"<rect x='0' y='0' width='{w}' height='{h}' fill='{bg}'/>" if bg else ""
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}'>{b}{inner}</svg>"


def save(name, svg):
    open(os.path.join(OUT, "svg", name + ".svg"), "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, "previews", name + ".png"), scale=2)
    print("wrote", name)


# ----------------------------- MOCK DATA -----------------------------
TOP3 = [dict(rank=1, num="Sharks & Minnows", name="Sharks & Minnows", pts=580, pending=20),
        dict(rank=2, num="Apex Predators", name="Apex Predators", pts=480, pending=0),
        dict(rank=3, num="Pipeline Pirates", name="Pipeline Pirates", pts=480, pending=0)]
REST = [dict(rank=4, num="Quota Crushers", name="Quota Crushers", pts=420, pending=0),
        dict(rank=5, num="Deal Hunters", name="Deal Hunters", pts=410, pending=0),
        dict(rank=6, num="Green Machine", name="Green Machine", pts=370, pending=0),
        dict(rank=7, num="The Closers", name="The Closers", pts=270, pending=0),
        dict(rank=8, num="Cloud Surfers", name="Cloud Surfers", pts=160, pending=0),
        dict(rank=9, num="Edge Runners", name="Edge Runners", pts=60, pending=0),
        dict(rank=10, num="Momentum", name="Momentum", pts=0, pending=0)]
MEMBERS = [dict(name="Alex Jackson", pts=310), dict(name="Rowan Johnson", pts=40),
           dict(name="Quinn White", pts=20), dict(name="Avery Anderson", pts=0),
           dict(name="Alex Brown", pts=0), dict(name="Jordan Brown", pts=0),
           dict(name="Jordan Smith", pts=0), dict(name="Morgan White", pts=0)]
MEMBER_BOX = dict(title="YOUR PERFORMANCE", ini="AJ", name="Alex Jackson", sub="Green Machine · You",
                  total=310, pending=30, totlbl="TOTAL · EXCL PENDING", vals=[120, 40, 60, 30, 20, 40])
SPONSOR_BOX = dict(title="YOUR CREW", ini="RJ", name="Sharks & Minnows", sub="You sponsor · 9 people",
                   total=580, pending=20, totlbl="CREW TOTAL · EXCL PENDING", vals=[120, 60, 80, 60, 40, 220])
# all crews for the spectator tour (rank order)
ALLCREWS = [dict(rank=1, name="Sharks & Minnows", total=580, vals=[120, 60, 80, 60, 40, 220]),
            dict(rank=2, name="Apex Predators", total=480, vals=[80, 40, 60, 40, 60, 200]),
            dict(rank=3, name="Pipeline Pirates", total=480, vals=[60, 80, 40, 80, 20, 200]),
            dict(rank=4, name="Quota Crushers", total=420, vals=[60, 40, 40, 40, 40, 200]),
            dict(rank=5, name="Deal Hunters", total=410, vals=[40, 60, 50, 60, 40, 160]),
            dict(rank=6, name="Green Machine", total=370, vals=[120, 40, 60, 30, 20, 100]),
            dict(rank=7, name="The Closers", total=270, vals=[40, 30, 40, 40, 20, 100]),
            dict(rank=8, name="Cloud Surfers", total=160, vals=[20, 20, 20, 20, 20, 60]),
            dict(rank=9, name="Edge Runners", total=60, vals=[10, 10, 10, 10, 10, 10]),
            dict(rank=10, name="Momentum", total=0, vals=[0, 0, 0, 0, 0, 0])]
RIB = dict(ini="AJ", chip="Alex Jackson · Green Machine")

# standalone component previews
save("ribbon", wrap(*ribbon_inner(RIB)))
save("my-points", wrap(*mypoints_inner(MEMBER_BOX)))
save("crew-summary", wrap(*mypoints_inner(SPONSOR_BOX)))
save("crew-grid", wrap(*grid_inner("Green Machine", MEMBERS, "Alex Jackson")))
save("podium", wrap(*podium_inner(TOP3, my_crew="Sharks & Minnows", tag="YOU SPONSOR")))
save("ranks-header", wrap(*ranks_header_inner(10)))
save("leaderboard-row", wrap(*row_inner(REST[2], TOP3[0]['pts'], my_crew="Green Machine", tag="YOUR CREW")))
save("spectator", wrap(*spectator_inner(ALLCREWS)))
stack = []
for i, r in enumerate(REST):
    _, _, ri = row_inner(r, TOP3[0]['pts'], my_crew="Green Machine")
    stack.append(f"<svg x='0' y='{i*ROW_H}' width='{RW}' height='{ROW_H}' viewBox='0 0 {RW} {ROW_H}'>{ri}</svg>")
save("leaderboard-gallery", wrap(RW, ROW_H*len(REST), "".join(stack)))


# ------------------------------ FULL PAGES ------------------------------
def place(x, y, w, h, vw, vh, inner):
    return f"<svg x='{x}' y='{y}' width='{w}' height='{h}' viewBox='0 0 {vw} {vh}'>{inner}</svg>"


def page(role):
    s = [DEFS, f"<rect x='0' y='0' width='{PAGE_W}' height='{PAGE_H}' fill='{C['canvas']}'/>"]
    if role == "member":
        rib = dict(ini="AJ", chip="Alex Jackson · Green Machine"); myc, tag = "Green Machine", "YOUR CREW"
    elif role == "sponsor":
        rib = dict(ini="RJ", chip="Rowan Jackson · Sponsor"); myc, tag = "Sharks & Minnows", "YOU SPONSOR"
    else:
        rib = dict(ini="GV", chip="Guest Viewer · Spectator"); myc, tag = None, ""
    s.append(place(0, 0, PAGE_W, RIB_H, PAGE_W, RIB_H, ribbon_inner(rib)[2]))
    if role == "spectator":
        s.append(place(*SPEC, SPEC[2], SPEC[3], spectator_inner(ALLCREWS)[2]))
    elif role == "sponsor":
        s.append(place(*MP, MP[2], MP[3], mypoints_inner(SPONSOR_BOX)[2]))
        s.append(place(*GR, GR[2], GR[3], grid_inner("Sharks & Minnows", MEMBERS, None)[2]))
    else:
        s.append(place(*MP, MP[2], MP[3], mypoints_inner(MEMBER_BOX)[2]))
        s.append(place(*GR, GR[2], GR[3], grid_inner("Green Machine", MEMBERS, "Alex Jackson")[2]))
    s.append(place(*PD, PD[2], PD[3], podium_inner(TOP3, my_crew=myc, tag=tag)[2]))
    s.append(place(*RH, RH[2], RH[3], ranks_header_inner(10)[2]))
    for i, r in enumerate(REST):
        s.append(place(GAL[0], GAL[1] + i*ROW_H, RW, ROW_H, RW, ROW_H, row_inner(r, TOP3[0]['pts'], my_crew=myc, tag=tag)[2]))
    return PAGE_W, PAGE_H, "".join(s)


save("full-page-mockup", wrap(*page("member"), bg=C['canvas']))
save("full-page-sponsor", wrap(*page("sponsor"), bg=C['canvas']))
save("full-page-spectator", wrap(*page("spectator"), bg=C['canvas']))


# ============================================================================
#  CREW PORTAL  (second page) — locked 1136 x 640
#    ribbon (back to dashboard)         0,0,1136,52
#    crew member cards strip            16,68,1104,150   (current user larger)
#    opp-list header                    16,230,420,30
#    opp list (gallery)                 16,262,420,362   rows 420x64
#    right panel                        452,230,668,394
#       - opp DETAIL   (shown when an opp is selected)
#       - pipeline OVERVIEW (the "underneath" visual, shown when nothing selected)
#    leaf-wipe transition overlay       full screen, plays on entry
# ============================================================================
P_CARDS = (16, 68, 1104, 150)
P_HEAD  = (16, 230, 420, 30)
P_LIST  = (16, 262, 420, 362)
P_RIGHT = (452, 230, 668, 394)
OPPROW_H = 64
FUNNELCOL = {"Upsell": C["blue"], "New Logo": C["ok"], "Renewal": C["teal"],
             "Cross-sell": C["purple"], "Expansion": C["magenta"]}
FCCOL = {"Commit": C["ok"], "Best Case": C["blue"], "Pipeline": C["teal"],
         "Upside": C["purple"], "Omitted": C["weak"]}


def money(v):
    return f"{int(v):,}"


def wrap_text(s, maxchars, maxlines=3):
    words, lines, cur = str(s).split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= maxchars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
            if len(lines) == maxlines - 1:
                break
    if cur and len(lines) < maxlines:
        lines.append(cur)
    if len(lines) == maxlines and len("".join(words)) > maxchars * maxlines:
        lines[-1] = lines[-1][:maxchars - 1].rstrip() + "…"
    return lines


def trunc(s, n):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


def chip(x, y, label, col, fg="#ffffff"):
    w = 7 * len(str(label)) + 20
    return (f"<rect x='{x:.0f}' y='{y:.0f}' width='{w:.0f}' height='20' rx='10' fill='{col}'/>"
            f"<text x='{x+w/2:.0f}' y='{y+10:.0f}' font-family='{FONT}' font-size='10.5' font-weight='700' "
            f"fill='{fg}' text-anchor='middle' dominant-baseline='central'>{esc(label)}</text>"), w


# ---------------------------------------------------------------- PORTAL RIBBON
def portal_button_inner():
    """The 'Crew Portal' ribbon button — an SVG (Image control with its own OnSelect)."""
    W, H = 140, 30
    s = [CSS,
         "<style>.nudge{animation:nudge 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
         "@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(3px)}}"
         "@media(prefers-reduced-motion:reduce){.nudge{animation:none}}</style>",
         "<g class='fu'>"]
    s.append(f"<rect x='1' y='1' width='138' height='28' rx='14' fill='{C['brand']}'/>")
    s.append(f"<rect x='1' y='1' width='138' height='14' rx='13' fill='#ffffff' opacity='.12'/>")
    # leaf glyph (ties into the leaf-wipe transition)
    s.append(f"<g transform='translate(20,15)'><path d='M0,-7 C4,-5 4,3 0,7 C-4,3 -4,-5 0,-7 Z' fill='#ffffff' opacity='.95'/>"
             f"<path d='M0,-6 L0,6' stroke='{C['brand']}' stroke-width='.8' opacity='.5'/></g>")
    s.append(f"<text x='36' y='16' font-family='{FONT}' font-size='13' font-weight='600' fill='#ffffff' dominant-baseline='central'>Crew Portal</text>")
    s.append("<path d='M122,11 l5,4 l-5,4' fill='none' stroke='#ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' class='nudge'/>")
    s.append("</g>")
    return W, H, "".join(s)


def portal_ribbon_inner(u):
    W, H = PAGE_W, RIB_H
    s = [DEFS, CSS, "<g class='fu'>"]
    s.append(f"<rect x='0' y='0' width='{W}' height='{H}' fill='{C['card']}'/>")
    s.append(f"<line x1='0' y1='{H-1}' x2='{W}' y2='{H-1}' stroke='{C['border']}'/>")
    # back pill (a transparent btnBack sits over this in PowerApps)
    s.append(f"<rect x='16' y='11' width='132' height='30' rx='15' fill='{C['contrast']}' stroke='{C['border']}'/>")
    s.append(f"<path d='M34,26 l7,-6 m-7,6 l7,6 m-7,-6 h12' fill='none' stroke='{C['greenDark']}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/>")
    s.append(f"<text x='54' y='27' font-family='{FONT}' font-size='12.5' font-weight='600' fill='{C['greenDark']}' dominant-baseline='central'>Dashboard</text>")
    # title
    s.append(f"<rect x='164' y='13' width='26' height='26' rx='7' fill='{C['brand']}'/>")
    s.append(f"<text x='177' y='27' font-family='{FONT}' font-size='11' font-weight='700' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>1%</text>")
    s.append(f"<text x='202' y='32' font-family='{FONT}' font-size='17' font-weight='700' fill='{C['strong']}'>Crew Portal <tspan fill='{C['weak']}' font-weight='400'>&#183; {esc(u.get('crew',''))}</tspan></text>")
    cw = 244; cx = W - 16 - cw
    s.append(f"<rect x='{cx}' y='10' width='{cw}' height='32' rx='16' fill='{C['contrast']}'/>")
    s.append(f"<circle cx='{cx+20}' cy='26' r='12' fill='{C['brand']}'/>")
    s.append(f"<text x='{cx+20}' y='27' font-family='{FONT}' font-size='10' font-weight='700' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>{esc(u['ini'])}</text>")
    s.append(f"<text x='{cx+40}' y='30' font-family='{FONT}' font-size='13' fill='{C['text']}'>{esc(u['chip'])}</text>")
    s.append("</g>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- CREW CARDS
def crew_cards_inner(members, current):
    W, H = P_CARDS[2], P_CARDS[3]
    n = max(1, len(members)); gap = 12
    small = (W - (n - 1) * gap) / (n + 0.5)
    big = small * 1.5
    s = [DEFS, CSS]
    s.append(eyebrow(4, 15, "CREW ROSTER"))
    s.append(f"<text x='{W-4}' y='15' font-family='{FONT}' font-size='11' fill='{C['weak']}' text-anchor='end'>{n} members</text>")
    ry, ch = 24, H - 26
    x = 0.0
    for i, m in enumerate(members):
        me = (m['name'] == current)
        cwid = big if me else small
        cx = x + cwid / 2
        fill = C['greenTint'] if me else C['card']
        stroke = C['brand'] if me else C['border']
        ar = 20 if me else 18
        acy = ry + (30 if me else 34)
        s.append(f"<g class='fu' style='animation-delay:{0.10+i*0.06:.2f}s'>")
        s.append(shadow(x, ry, cwid, ch, 13, op=0.06))
        s.append(f"<rect x='{x:.0f}' y='{ry}' width='{cwid:.0f}' height='{ch}' rx='13' fill='{fill}' stroke='{stroke}' stroke-width='{2 if me else 1}'/>")
        s.append(f"<rect x='{x:.0f}' y='{ry}' width='{cwid:.0f}' height='4' rx='2' fill='{C['brand'] if me else C['contrast']}'/>")
        if me:
            s.append(f"<circle cx='{cx:.0f}' cy='{acy}' r='{ar+4}' fill='none' stroke='{C['brand']}' stroke-width='2' class='ring' opacity='0'/>")
        s.append(f"<circle cx='{cx:.0f}' cy='{acy}' r='{ar}' fill='{C['brand'] if me else C['contrast']}'/>")
        s.append(f"<text x='{cx:.0f}' y='{acy+1}' font-family='{FONT}' font-size='{14 if me else 12}' font-weight='700' fill='{'#ffffff' if me else C['greenDark']}' text-anchor='middle' dominant-baseline='central'>{esc(initials(m['name']))}</text>")
        nm = trunc(m['name'], int(cwid / 7.5))
        s.append(f"<text x='{cx:.0f}' y='{ry+(66 if me else 68)}' font-family='{FONT}' font-size='{14 if me else 12}' font-weight='700' fill='{C['strong']}' text-anchor='middle'>{esc(nm)}</text>")
        rl = trunc(m['role'], int(cwid / 6.2))
        s.append(f"<text x='{cx:.0f}' y='{ry+(82 if me else 84)}' font-family='{FONT}' font-size='{10.5 if me else 9.5}' fill='{C['weak']}' text-anchor='middle'>{esc(rl)}</text>")
        s.append(f"<text x='{cx:.0f}' y='{ry+ch-(16 if me else 14)}' font-family='{FONT}' font-size='{26 if me else 22}' font-weight='700' fill='{C['greenDark']}' text-anchor='middle'>{esc(m['pts'])}</text>")
        s.append(f"<text x='{cx:.0f}' y='{ry+ch-(4 if me else 3)}' font-family='{FONT}' font-size='8' font-weight='600' letter-spacing='1' fill='{C['weak']}' text-anchor='middle'>POINTS</text>")
        if me:
            s.append(f"<rect x='{x+cwid-44:.0f}' y='{ry+8}' width='36' height='16' rx='8' fill='{C['brand']}'/>")
            s.append(f"<text x='{x+cwid-26:.0f}' y='{ry+16}' font-family='{FONT}' font-size='9' font-weight='700' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>YOU</text>")
        s.append("</g>")
        x += cwid + gap
    return W, H, "".join(s)


# ---------------------------------------------------------------- OPP LIST HEADER
def opp_header_inner(count):
    W, H = P_HEAD[2], P_HEAD[3]
    s = [DEFS, CSS]
    s.append(eyebrow(4, 19, "CREW PIPELINE"))
    s.append(f"<text x='{W-4}' y='19' font-family='{FONT}' font-size='11' fill='{C['weak']}' text-anchor='end'>{count} opportunities</text>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- OPP ROW
def opp_row_inner(o, selected=False, idx=0):
    W, H = P_LIST[2], OPPROW_H
    fc = FCCOL.get(o['forecast'], C['weak'])
    s = [DEFS, CSS]
    s.append(f"<g class='rw' style='animation-delay:{0.06+idx*0.05:.2f}s'>")
    s.append(f"<rect x='2' y='3' width='{W-4}' height='{H-8}' rx='11' fill='{C['greenTint'] if selected else C['card']}' stroke='{C['brand'] if selected else C['border']}' stroke-width='{2 if selected else 1}'/>")
    s.append(f"<rect x='2' y='3' width='5' height='{H-8}' rx='2.5' fill='{fc}'/>")
    s.append(f"<text x='18' y='25' font-family='{FONT}' font-size='13' font-weight='700' fill='{C['strong']}'>{esc(trunc(o['name'], 34))}</text>")
    s.append(f"<text x='18' y='44' font-family='{FONT}' font-size='10.5' fill='{C['weak']}'>{esc(trunc(o['account'], 30))}</text>")
    ftc = FUNNELCOL.get(o['funnel'], C['weak'])
    ch, cw = chip(18, 48, o['funnel'], "#eef2f5", fg=ftc)
    # value, right aligned
    s.append(f"<text x='{W-16}' y='27' font-family='{FONT}' font-size='13' font-weight='700' fill='{C['greenDark']}' text-anchor='end'>{money(o['value'])}</text>")
    fch, fcw = chip(W - 16 - (7 * len(o['forecast']) + 20), 44, o['forecast'], fc)
    s.append(ch); s.append(fch)
    if selected:
        s.append(f"<path d='M{W-14},28 l6,5 l-6,5' fill='none' stroke='{C['brand']}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/>")
    s.append("</g>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- OPP DETAIL
def opp_detail_inner(o):
    W, H = P_RIGHT[2], P_RIGHT[3]
    fc = FCCOL.get(o['forecast'], C['weak'])
    ftc = FUNNELCOL.get(o['funnel'], C['weak'])
    s = [DEFS, CSS, "<g class='fu'>"]
    s.append(shadow(0, 0, W, H, 16, op=0.07))
    s.append(f"<rect x='0' y='0' width='{W}' height='{H}' rx='16' fill='{C['card']}' stroke='{C['border']}'/>")
    s.append(f"<rect x='0' y='0' width='{W}' height='6' rx='3' fill='{fc}'/>")
    s.append(eyebrow(28, 38, "OPPORTUNITY DETAIL"))
    # title (wrap up to 2 lines)
    tl = wrap_text(o['name'], 46, 2)
    for i, ln in enumerate(tl):
        s.append(f"<text x='28' y='{70+i*26}' font-family='{FONT}' font-size='22' font-weight='700' fill='{C['strong']}'>{esc(ln)}</text>")
    ay = 70 + len(tl) * 26
    s.append(f"<text x='28' y='{ay}' font-family='{FONT}' font-size='13' fill='{C['weak']}'>{esc(o['account'])}</text>")
    # chips row
    cy = ay + 14
    fch, fcw = chip(28, cy, o['forecast'], fc)
    s.append(fch)
    uch, ucw = chip(28 + fcw + 8, cy, o['funnel'], "#eef2f5", fg=ftc)
    s.append(uch)
    # stat tiles
    ty = cy + 34
    tiles = [("TOTAL VALUE", money(o['value']), C['greenDark']),
             ("CLOSE DATE", o['close'], C['strong']),
             ("OPP OWNER", trunc(o['owner'], 16), C['strong'])]
    tw = (W - 56 - 2 * 12) / 3
    for i, (lbl, val, col) in enumerate(tiles):
        x = 28 + i * (tw + 12)
        s.append(f"<g class='fo' style='animation-delay:{0.20+i*0.08:.2f}s'>")
        s.append(f"<rect x='{x:.0f}' y='{ty}' width='{tw:.0f}' height='70' rx='12' fill='#fbfcfc' stroke='{C['border']}'/>")
        s.append(f"<text x='{x+16:.0f}' y='{ty+24}' font-family='{FONT}' font-size='9' font-weight='700' letter-spacing='.6' fill='{C['weak']}'>{esc(lbl)}</text>")
        s.append(f"<text x='{x+16:.0f}' y='{ty+52}' font-family='{FONT}' font-size='{22 if i==0 else 17}' font-weight='700' fill='{col}'>{esc(val)}</text>")
        s.append("</g>")
    # latest update panel
    uy = ty + 86
    s.append(f"<g class='fu' style='animation-delay:0.34s'>")
    s.append(f"<rect x='28' y='{uy}' width='{W-56}' height='{H-uy-24}' rx='12' fill='#fbfcfc' stroke='{C['border']}'/>")
    s.append(f"<rect x='28' y='{uy}' width='5' height='{H-uy-24}' rx='2.5' fill='{C['brand']}'/>")
    s.append(f"<text x='46' y='{uy+24}' font-family='{FONT}' font-size='9.5' font-weight='700' letter-spacing='.6' fill='{C['weak']}'>LATEST UPDATE</text>")
    for i, ln in enumerate(wrap_text(o['update'], 64, 4)):
        s.append(f"<text x='46' y='{uy+46+i*18}' font-family='{FONT}' font-size='12' fill='{C['text']}'>{esc(ln)}</text>")
    s.append("</g>")
    s.append("</g>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- PIPELINE OVERVIEW (underneath)
def pipeline_inner(opps):
    W, H = P_RIGHT[2], P_RIGHT[3]
    total = sum(o['value'] for o in opps)
    # group by forecast category, preserve a sensible order
    order = ["Commit", "Best Case", "Pipeline", "Upside", "Omitted"]
    groups = {}
    for o in opps:
        groups.setdefault(o['forecast'], [0, 0])
        groups[o['forecast']][0] += o['value']
        groups[o['forecast']][1] += 1
    cats = sorted(groups.items(), key=lambda kv: (order.index(kv[0]) if kv[0] in order else 99))
    mx = max([1] + [v[0] for v in groups.values()])
    s = [DEFS, CSS, "<g class='fu'>"]
    s.append(shadow(0, 0, W, H, 16, op=0.07))
    s.append(f"<rect x='0' y='0' width='{W}' height='{H}' rx='16' fill='{C['card']}' stroke='{C['border']}'/>")
    s.append(eyebrow(28, 38, "CREW PIPELINE OVERVIEW"))
    s.append(f"<text x='{W-28}' y='38' font-family='{FONT}' font-size='11' fill='{C['weak']}' text-anchor='end'>{len(opps)} open opps</text>")
    # hero
    s.append(f"<text x='28' y='86' font-family='{FONT}' font-size='40' font-weight='700' fill='{C['greenDark']}'>{money(total)}</text>")
    s.append(f"<text x='28' y='106' font-family='{FONT}' font-size='11' font-weight='600' letter-spacing='.6' fill='{C['weak']}'>TOTAL PIPELINE VALUE</text>")
    s.append(f"<line x1='28' y1='124' x2='{W-28}' y2='124' stroke='{C['border']}'/>")
    s.append(f"<text x='28' y='148' font-family='{FONT}' font-size='10' font-weight='700' letter-spacing='.6' fill='{C['weak']}'>BY FORECAST CATEGORY</text>")
    by = 162
    rowh = (H - by - 56) / max(1, len(cats))
    for i, (cat, (val, cnt)) in enumerate(cats):
        y = by + i * rowh
        col = FCCOL.get(cat, C['weak'])
        s.append(f"<g class='fo' style='animation-delay:{0.18+i*0.08:.2f}s'>")
        s.append(f"<circle cx='36' cy='{y+13:.0f}' r='4' fill='{col}'/>")
        s.append(f"<text x='48' y='{y+17:.0f}' font-family='{FONT}' font-size='12.5' font-weight='600' fill='{C['strong']}'>{esc(cat)}</text>")
        s.append(f"<text x='{W-28}' y='{y+17:.0f}' font-family='{FONT}' font-size='12.5' font-weight='700' fill='{C['strong']}' text-anchor='end'>{money(val)} <tspan fill='{C['weak']}' font-weight='400'>&#183; {cnt}</tspan></text>")
        bw = W - 28 - 48
        s.append(f"<rect x='48' y='{y+22:.0f}' width='{bw}' height='8' rx='4' fill='{C['contrast']}'/>")
        s.append(f"<rect x='48' y='{y+22:.0f}' width='{max(6, bw*val/mx):.0f}' height='8' rx='4' fill='{col}' class='gx' style='animation-delay:{0.30+i*0.08:.2f}s'/>")
        s.append("</g>")
    # footer hint
    s.append(f"<rect x='28' y='{H-44}' width='{W-56}' height='24' rx='12' fill='{C['contrast']}'/>")
    s.append(f"<circle cx='48' cy='{H-32}' r='3' fill='{C['brand']}' class='brz'/>")
    s.append(f"<text x='60' y='{H-28}' font-family='{FONT}' font-size='11' font-weight='600' fill='{C['weak']}'>Select an opportunity on the left to see full details</text>")
    s.append("</g>")
    return W, H, "".join(s)


# ---------------------------------------------------------------- LEAF-WIPE TRANSITION
LEAF_PATH = "M0,-15 C9,-11 9,7 0,15 C-9,7 -9,-11 0,-15 Z"


def leafwipe_inner(static=False):
    W, H = PAGE_W, PAGE_H
    css = (
        "<style>"
        ".wipe{" + ("" if static else "animation:wipe 1.05s cubic-bezier(.5,0,.2,1) both") + "}"
        ".lf{transform-box:fill-box;transform-origin:center;" + ("" if static else "animation:lf 1.05s ease-in-out both") + "}"
        "@keyframes wipe{0%{transform:translateX(-112%)}42%{transform:translateX(0)}56%{transform:translateX(0)}100%{transform:translateX(112%)}}"
        "@keyframes lf{0%{transform:rotate(-50deg) scale(.6)}100%{transform:rotate(340deg) scale(1)}}"
        "@media(prefers-reduced-motion:reduce){.wipe{animation:none;transform:translateX(112%)}.lf{animation:none}}"
        "</style>")
    s = [css, "<g class='wipe'>"]
    # leading-edge gradient panel
    s.append(f"<defs><linearGradient id='lg' x1='0' y1='0' x2='1' y2='0'>"
             f"<stop offset='0' stop-color='{C['greenDark']}'/><stop offset='1' stop-color='{C['brand']}'/></linearGradient></defs>")
    s.append(f"<rect x='-40' y='0' width='{W+80}' height='{H}' fill='url(#lg)'/>")
    # diagonal leading edge highlight
    s.append(f"<polygon points='{W-2},0 {W+90},0 {W+50},{H} {W-42},{H}' fill='{C['brand']}' opacity='.55'/>")
    # tumbling leaves scattered across the panel
    leaves = [(140, 150, 1.6, GOLD, .00), (320, 470, 1.2, "#ffffff", .10),
              (520, 120, 2.0, "#bdf5e4", .04), (700, 400, 1.4, GOLD, .14),
              (880, 230, 1.7, "#ffffff", .08), (1030, 520, 1.1, "#bdf5e4", .12),
              (250, 320, 1.0, "#ffffff", .16), (640, 560, 1.3, GOLD, .06),
              (980, 80, 1.5, "#bdf5e4", .02)]
    for (lx, ly, sc, col, dl) in leaves:
        style = "" if static else f" style='animation-delay:{dl}s'"
        s.append(f"<g transform='translate({lx},{ly}) scale({sc})'><g class='lf'{style}>"
                 f"<path d='{LEAF_PATH}' fill='{col}' opacity='.92'/>"
                 f"<path d='M0,-13 L0,13' stroke='{C['greenDark']}' stroke-width='.8' opacity='.35'/>"
                 f"</g></g>")
    # brand mark riding the wipe
    s.append(f"<g transform='translate({W/2:.0f},{H/2:.0f})'>"
             f"<rect x='-30' y='-30' width='60' height='60' rx='16' fill='#ffffff' opacity='.95'/>"
             f"<text x='0' y='2' font-family='{FONT}' font-size='26' font-weight='700' fill='{C['greenDark']}' text-anchor='middle' dominant-baseline='central'>1%</text></g>")
    s.append("</g>")
    return W, H, "".join(s)


# ----------------------------- PORTAL MOCK DATA -----------------------------
P_MEMBERS = [
    dict(name="Alex Jackson", role="Account Executive", pts=310),
    dict(name="Rowan Johnson", role="Solutions Architect", pts=40),
    dict(name="Quinn White", role="Inside Sales Rep", pts=20),
    dict(name="Avery Anderson", role="Customer Success", pts=0),
    dict(name="Alex Brown", role="Sales Engineer", pts=0),
    dict(name="Jordan Brown", role="BDR", pts=0),
]
P_OPPS = [
    dict(name="Cloud Migration – Phase 2", funnel="Upsell", account="Northwind Trading", forecast="Commit",
         close="31 Jul 2026", value=185000, owner="Alex Jackson",
         update="Signed SOW received; legal is reviewing MSA redlines and we expect a countersignature next week. Procurement aligned on budget."),
    dict(name="GreenLake Edge Rollout", funnel="New Logo", account="Helios Manufacturing", forecast="Best Case",
         close="14 Aug 2026", value=240000, owner="Rowan Johnson",
         update="Technical validation passed. Champion presenting business case to CFO Friday; pricing approval pending."),
    dict(name="Storage Refresh", funnel="Renewal", account="Atlas Logistics", forecast="Commit",
         close="30 Jun 2026", value=96000, owner="Quinn White",
         update="Renewal quote accepted verbally, awaiting PO. Low risk."),
    dict(name="Data Platform Expansion", funnel="Expansion", account="Vertex Health", forecast="Pipeline",
         close="22 Sep 2026", value=410000, owner="Alex Jackson",
         update="Discovery workshops scheduled. Multiple stakeholders; needs exec sponsor mapping."),
    dict(name="Security Suite Add-on", funnel="Cross-sell", account="Northwind Trading", forecast="Best Case",
         close="05 Sep 2026", value=72000, owner="Avery Anderson",
         update="POC in flight, positive early feedback from the SecOps team."),
    dict(name="AI Workloads Net-New", funnel="New Logo", account="Lumen Robotics", forecast="Upside",
         close="18 Oct 2026", value=320000, owner="Alex Brown",
         update="Early-stage; intro call booked through partner referral."),
    dict(name="Backup-as-a-Service", funnel="Upsell", account="Atlas Logistics", forecast="Pipeline",
         close="11 Nov 2026", value=58000, owner="Quinn White",
         update="Awaiting current contract end date to time the proposal."),
]
P_RIB = dict(ini="AJ", chip="Alex Jackson · AE", crew="Green Machine")

# standalone portal component previews
save("portal-button", wrap(*portal_button_inner()))
save("portal-ribbon", wrap(*portal_ribbon_inner(P_RIB)))
save("portal-cards", wrap(*crew_cards_inner(P_MEMBERS, "Alex Jackson"), bg=C['canvas']))
save("portal-opp-row", wrap(*opp_row_inner(P_OPPS[0], selected=True)))
save("portal-opp-detail", wrap(*opp_detail_inner(P_OPPS[0])))
save("portal-pipeline", wrap(*pipeline_inner(P_OPPS)))
save("leaf-transition", wrap(*leafwipe_inner(static=True)))


def page_portal(sel=None):
    s = [DEFS, f"<rect x='0' y='0' width='{PAGE_W}' height='{PAGE_H}' fill='{C['canvas']}'/>"]
    s.append(place(0, 0, PAGE_W, RIB_H, PAGE_W, RIB_H, portal_ribbon_inner(P_RIB)[2]))
    s.append(place(*P_CARDS, P_CARDS[2], P_CARDS[3], crew_cards_inner(P_MEMBERS, "Alex Jackson")[2]))
    s.append(place(*P_HEAD, P_HEAD[2], P_HEAD[3], opp_header_inner(len(P_OPPS))[2]))
    for i, o in enumerate(P_OPPS):
        if i * OPPROW_H + OPPROW_H > P_LIST[3]:
            break
        s.append(place(P_LIST[0], P_LIST[1] + i * OPPROW_H, P_LIST[2], OPPROW_H,
                       P_LIST[2], OPPROW_H, opp_row_inner(o, selected=(i == sel), idx=i)[2]))
    if sel is not None:
        s.append(place(*P_RIGHT, P_RIGHT[2], P_RIGHT[3], opp_detail_inner(P_OPPS[sel])[2]))
    else:
        s.append(place(*P_RIGHT, P_RIGHT[2], P_RIGHT[3], pipeline_inner(P_OPPS)[2]))
    return PAGE_W, PAGE_H, "".join(s)


save("full-portal", wrap(*page_portal(sel=0), bg=C['canvas']))
save("full-portal-empty", wrap(*page_portal(sel=None), bg=C['canvas']))
print("done")
