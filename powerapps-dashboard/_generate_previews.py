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
    s.append(eyebrow(4, 16, crew_name.upper() + " · MEMBERS"))
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
        g.append(f"<text x='{cx}' y='{top+76}' font-family='{FONT}' font-size='17' font-weight='700' fill='{C['strong']}' text-anchor='middle'>{esc(crew['name'])}</text>")
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
    g.append(f"<text x='40' y='19' font-family='{FONT}' font-size='13' font-weight='700' fill='{C['greenDark'] if match else C['strong']}'>{esc(r['name'])}</text>")
    if match:
        nx = 40 + len(str(r['name'])) * 7 + 8
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
        s.append(f"<text x='50' y='24' font-family='{FONT}' font-size='16' font-weight='700' fill='{C['strong']}'>{esc(cr['name'])}</text>")
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
TOP3 = [dict(rank=1, num=3, name="Crew 3", pts=580, pending=20),
        dict(rank=2, num=5, name="Crew 5", pts=480, pending=0),
        dict(rank=3, num=7, name="Crew 7", pts=480, pending=0)]
REST = [dict(rank=4, num=10, name="Crew 10", pts=420, pending=0),
        dict(rank=5, num=4, name="Crew 4", pts=410, pending=0),
        dict(rank=6, num=1, name="Crew 1", pts=370, pending=0),
        dict(rank=7, num=2, name="Crew 2", pts=270, pending=0),
        dict(rank=8, num=9, name="Crew 9", pts=160, pending=0),
        dict(rank=9, num=6, name="Crew 6", pts=60, pending=0),
        dict(rank=10, num=8, name="Crew 8", pts=0, pending=0)]
MEMBERS = [dict(name="Alex Jackson", pts=310), dict(name="Rowan Johnson", pts=40),
           dict(name="Quinn White", pts=20), dict(name="Avery Anderson", pts=0),
           dict(name="Alex Brown", pts=0), dict(name="Jordan Brown", pts=0),
           dict(name="Jordan Smith", pts=0), dict(name="Morgan White", pts=0)]
MEMBER_BOX = dict(title="YOUR PERFORMANCE", ini="AJ", name="Alex Jackson", sub="Crew 1 · You",
                  total=310, pending=30, totlbl="TOTAL · EXCL PENDING", vals=[120, 40, 60, 30, 20, 40])
SPONSOR_BOX = dict(title="YOUR CREW", ini="RJ", name="Crew 3", sub="You sponsor · 9 people",
                   total=580, pending=20, totlbl="CREW TOTAL · EXCL PENDING", vals=[120, 60, 80, 60, 40, 220])
# all crews for the spectator tour (rank order)
ALLCREWS = [dict(rank=1, name="Crew 3", total=580, vals=[120, 60, 80, 60, 40, 220]),
            dict(rank=2, name="Crew 5", total=480, vals=[80, 40, 60, 40, 60, 200]),
            dict(rank=3, name="Crew 7", total=480, vals=[60, 80, 40, 80, 20, 200]),
            dict(rank=4, name="Crew 10", total=420, vals=[60, 40, 40, 40, 40, 200]),
            dict(rank=5, name="Crew 4", total=410, vals=[40, 60, 50, 60, 40, 160]),
            dict(rank=6, name="Crew 1", total=370, vals=[120, 40, 60, 30, 20, 100]),
            dict(rank=7, name="Crew 2", total=270, vals=[40, 30, 40, 40, 20, 100]),
            dict(rank=8, name="Crew 9", total=160, vals=[20, 20, 20, 20, 20, 60]),
            dict(rank=9, name="Crew 6", total=60, vals=[10, 10, 10, 10, 10, 10]),
            dict(rank=10, name="Crew 8", total=0, vals=[0, 0, 0, 0, 0, 0])]
RIB = dict(ini="AJ", chip="Alex Jackson · Crew 1")

# standalone component previews
save("ribbon", wrap(*ribbon_inner(RIB)))
save("my-points", wrap(*mypoints_inner(MEMBER_BOX)))
save("crew-summary", wrap(*mypoints_inner(SPONSOR_BOX)))
save("crew-grid", wrap(*grid_inner("Crew 1", MEMBERS, "Alex Jackson")))
save("podium", wrap(*podium_inner(TOP3, my_crew=3, tag="YOU SPONSOR")))
save("ranks-header", wrap(*ranks_header_inner(10)))
save("leaderboard-row", wrap(*row_inner(REST[2], TOP3[0]['pts'], my_crew=1, tag="YOUR CREW")))
save("spectator", wrap(*spectator_inner(ALLCREWS)))
stack = []
for i, r in enumerate(REST):
    _, _, ri = row_inner(r, TOP3[0]['pts'], my_crew=1)
    stack.append(f"<svg x='0' y='{i*ROW_H}' width='{RW}' height='{ROW_H}' viewBox='0 0 {RW} {ROW_H}'>{ri}</svg>")
save("leaderboard-gallery", wrap(RW, ROW_H*len(REST), "".join(stack)))


# ------------------------------ FULL PAGES ------------------------------
def place(x, y, w, h, vw, vh, inner):
    return f"<svg x='{x}' y='{y}' width='{w}' height='{h}' viewBox='0 0 {vw} {vh}'>{inner}</svg>"


def page(role):
    s = [DEFS, f"<rect x='0' y='0' width='{PAGE_W}' height='{PAGE_H}' fill='{C['canvas']}'/>"]
    if role == "member":
        rib = dict(ini="AJ", chip="Alex Jackson · Crew 1"); myc, tag = 1, "YOUR CREW"
    elif role == "sponsor":
        rib = dict(ini="RJ", chip="Rowan Jackson · Sponsor"); myc, tag = 3, "YOU SPONSOR"
    else:
        rib = dict(ini="GV", chip="Guest Viewer · Spectator"); myc, tag = None, ""
    s.append(place(0, 0, PAGE_W, RIB_H, PAGE_W, RIB_H, ribbon_inner(rib)[2]))
    if role == "spectator":
        s.append(place(*SPEC, SPEC[2], SPEC[3], spectator_inner(ALLCREWS)[2]))
    elif role == "sponsor":
        s.append(place(*MP, MP[2], MP[3], mypoints_inner(SPONSOR_BOX)[2]))
        s.append(place(*GR, GR[2], GR[3], grid_inner("Crew 3", MEMBERS, None)[2]))
    else:
        s.append(place(*MP, MP[2], MP[3], mypoints_inner(MEMBER_BOX)[2]))
        s.append(place(*GR, GR[2], GR[3], grid_inner("Crew 1", MEMBERS, "Alex Jackson")[2]))
    s.append(place(*PD, PD[2], PD[3], podium_inner(TOP3, my_crew=myc, tag=tag)[2]))
    s.append(place(*RH, RH[2], RH[3], ranks_header_inner(10)[2]))
    for i, r in enumerate(REST):
        s.append(place(GAL[0], GAL[1] + i*ROW_H, RW, ROW_H, RW, ROW_H, row_inner(r, TOP3[0]['pts'], my_crew=myc, tag=tag)[2]))
    return PAGE_W, PAGE_H, "".join(s)


save("full-page-mockup", wrap(*page("member"), bg=C['canvas']))
save("full-page-sponsor", wrap(*page("sponsor"), bg=C['canvas']))
save("full-page-spectator", wrap(*page("spectator"), bg=C['canvas']))
print("done")
