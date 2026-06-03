#!/usr/bin/env python3
"""
Mirrors the EXACT string fragments used in the Power Fx Image formulas and
renders them, to prove the generated SVG is valid markup. If these render,
the Power Fx (which concatenates the identical fragments) will too.
Text(n) -> integer string ; Round/Int/Mod/RoundUp mimic Power Fx.
"""
import math, cairosvg, os
OUT = os.path.dirname(os.path.abspath(__file__))
def T(x):            # PowerFx Text(int)
    return str(int(x))
def Len(s): return len(str(s))

# ---------- PODIUM (mirror of imgPodium.Image) ----------
colCrew = [
    dict(Rank=1, CrewName="Crew 3", CrewTotal=580, CrewPending=20),
    dict(Rank=2, CrewName="Crew 5", CrewTotal=480, CrewPending=0),
    dict(Rank=3, CrewName="Crew 7", CrewTotal=480, CrewPending=0),
]
p1, p2, p3 = colCrew[0], colCrew[1], colCrew[2]
slots = [
    dict(cx=180, top=132, medal="#8C99A4", tint="#EDEFF1", rank=2, nm=p2["CrewName"], pts=p2["CrewTotal"], pend=p2["CrewPending"]),
    dict(cx=460, top=70,  medal="#E0A300", tint="#FBF1D6", rank=1, nm=p1["CrewName"], pts=p1["CrewTotal"], pend=p1["CrewPending"]),
    dict(cx=740, top=162, medal="#B5742E", tint="#F4E9DD", rank=3, nm=p3["CrewName"], pts=p3["CrewTotal"], pend=p3["CrewPending"]),
]
podium = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 920 440' font-family='Liberation Sans, Arial, sans-serif'>"
for s in slots:
    cx, top, medal, tint = s["cx"], s["top"], s["medal"], s["tint"]
    podium += "<rect x='"+T(cx-116)+"' y='"+T(top)+"' width='232' height='"+T(430-top)+"' rx='16' fill='#ffffff' stroke='#d4d8db'/>"
    podium += "<path d='M"+T(cx-115)+","+T(top+15)+" v-1 a14,14 0 0 1 14,-14 h202 a14,14 0 0 1 14,14 v1 z' fill='"+medal+"'/>"
    podium += "<circle cx='"+T(cx)+"' cy='"+T(top+56)+"' r='30' fill='"+tint+"' stroke='"+medal+"' stroke-width='2'/>"
    podium += "<text x='"+T(cx)+"' y='"+T(top+57)+"' font-size='22' font-weight='700' fill='"+medal+"' text-anchor='middle' dominant-baseline='central'>"+T(s["rank"])+"</text>"
    podium += "<text x='"+T(cx)+"' y='"+T(top+114)+"' font-size='22' font-weight='700' fill='#292d3a' text-anchor='middle'>"+s["nm"]+"</text>"
    podium += "<text x='"+T(cx)+"' y='"+T(top+164)+"' font-size='44' font-weight='700' fill='#006750' text-anchor='middle'>"+T(s["pts"])+"</text>"
    podium += "<text x='"+T(cx)+"' y='"+T(top+186)+"' font-size='12' font-weight='600' letter-spacing='1.5' fill='#606a70' text-anchor='middle'>TOTAL POINTS</text>"
    if s["pend"] > 0:
        podium += "<rect x='"+T(cx-58)+"' y='396' width='116' height='24' rx='12' fill='#FBEEDF'/>"
        podium += "<text x='"+T(cx)+"' y='412' font-size='12' font-weight='600' fill='#d36d00' text-anchor='middle'>+"+T(s["pend"])+" pending</text>"
    else:
        podium += "<rect x='"+T(cx-50)+"' y='396' width='100' height='24' rx='12' fill='#f2f3f4'/>"
        podium += "<text x='"+T(cx)+"' y='412' font-size='12' font-weight='600' fill='#606a70' text-anchor='middle'>no pending</text>"
podium += "</svg>"

# ---------- CREW GRID (mirror of imgCrewGrid.Image) ----------
varMyCrew = 1
colMyCrew = [
    dict(Idx=0, Name="Alex Jackson", MemberTotal=310, IsMe=True),
    dict(Idx=1, Name="Rowan Johnson", MemberTotal=40, IsMe=False),
    dict(Idx=2, Name="Quinn White", MemberTotal=20, IsMe=False),
    dict(Idx=3, Name="Avery Anderson", MemberTotal=0, IsMe=False),
    dict(Idx=4, Name="Alex Brown", MemberTotal=0, IsMe=False),
    dict(Idx=5, Name="Jordan Brown", MemberTotal=0, IsMe=False),
    dict(Idx=6, Name="Jordan Smith", MemberTotal=0, IsMe=False),
    dict(Idx=7, Name="Morgan White", MemberTotal=0, IsMe=False),
]
vbH = 46 + math.ceil(len(colMyCrew)/2) * 102 + 4
grid = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 440 "+T(vbH)+"' font-family='Liberation Sans, Arial, sans-serif'>"
grid += "<text x='14' y='28' font-size='17' font-weight='700' fill='#292d3a'>Crew "+T(varMyCrew)+" - Members</text>"
grid += "<text x='426' y='28' font-size='13' fill='#606a70' text-anchor='end'>"+T(len(colMyCrew))+" people</text>"
for m in colMyCrew:
    Idx, IsMe, Name, MT = m["Idx"], m["IsMe"], m["Name"], m["MemberTotal"]
    grid += "<g transform='translate("+T(12+(Idx%2)*212)+","+T(46+(Idx//2)*102)+")'>"
    grid += "<rect width='204' height='92' rx='12' fill='"+("#d1ffee" if IsMe else "#ffffff")+"' stroke='"+("#01a982" if IsMe else "#d4d8db")+"' stroke-width='"+("2" if IsMe else "1")+"'/>"
    nm = Name.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")[:20]
    grid += "<text x='16' y='28' font-size='13.5' font-weight='600' fill='"+("#292d3a" if IsMe else "#3e4550")+"'>"+nm+"</text>"
    if IsMe:
        grid += "<text x='190' y='27' font-size='10.5' font-weight='700' fill='#006750' text-anchor='end'>YOU</text>"
    grid += "<text x='16' y='74' font-size='30' font-weight='700' fill='"+("#006750" if IsMe else "#292d3a")+"'>"+T(MT)+"</text>"
    grid += "<text x='"+T(16+Len(T(MT))*18+6)+"' y='74' font-size='12' fill='#606a70'>pts</text>"
    grid += "</g>"
grid += "</svg>"

# ---------- MY POINTS (mirror of imgMyPoints.Image) ----------
varMe = dict(Name="Alex Jackson")
ini, crew, tot, pend = "AJ", "Crew 1", 310, 30
c = [120, 40, 60, 30, 20, 40]
cats = [("New CC Logo / IB Upsell", c[0], "#0070f8"), ("CAP Engagement", c[1], "#04909d"),
        ("CAP Orders Booked", c[2], "#009a71"), ("Customer Centricity", c[3], "#7764fc"),
        ("Accreditation Race", c[4], "#cc54a4"), ("IP Push", c[5], "#d25f4b")]
nm = varMe["Name"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
mp = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 440 360' font-family='Liberation Sans, Arial, sans-serif'>"
mp += "<rect x='2' y='2' width='436' height='354' rx='16' fill='#ffffff' stroke='#d4d8db'/>"
mp += "<circle cx='44' cy='50' r='26' fill='#01a982'/>"
mp += "<text x='44' y='51' font-size='19' font-weight='700' fill='#ffffff' text-anchor='middle' dominant-baseline='central'>"+ini+"</text>"
mp += "<text x='82' y='44' font-size='20' font-weight='700' fill='#292d3a'>"+nm+"</text>"
mp += "<text x='82' y='66' font-size='13' fill='#606a70'>"+crew+" - You</text>"
mp += "<text x='418' y='48' font-size='38' font-weight='700' fill='#006750' text-anchor='end'>"+T(tot)+"</text>"
mp += "<text x='418' y='66' font-size='10.5' font-weight='600' letter-spacing='1' fill='#606a70' text-anchor='end'>TOTAL - EXCL PENDING</text>"
if pend > 0:
    w = 8*Len(T(pend))+78
    mp += "<rect x='82' y='78' width='"+T(w)+"' height='20' rx='10' fill='#FBEEDF'/>"
    mp += "<text x='"+T(82+w/2)+"' y='92' font-size='11.5' font-weight='600' fill='#d36d00' text-anchor='middle'>+"+T(pend)+" pending</text>"
mp += "<line x1='22' y1='110' x2='418' y2='110' stroke='#d4d8db'/>"
for i,(lbl,val,col) in enumerate(cats):
    mp += "<g transform='translate("+T(22+(i%2)*206)+","+T(122+(i//2)*80)+")'>"
    mp += "<rect width='194' height='68' rx='10' fill='#fbfcfc' stroke='#d4d8db'/>"
    mp += "<rect width='6' height='68' rx='3' fill='"+col+"'/>"
    mp += "<circle cx='22' cy='22' r='4' fill='"+col+"'/>"
    mp += "<text x='34' y='26' font-size='11' font-weight='600' fill='#606a70'>"+lbl+"</text>"
    mp += "<text x='18' y='56' font-size='24' font-weight='700' fill='#292d3a'>"+T(val)+"</text>"
    mp += "</g>"
mp += "</svg>"

# ---------- ROW (mirror of imgRow.Image) ----------
varLeaderMax = 580
it = dict(Rank=4, CrewName="Crew 10", CrewTotal=420, CrewPending=0)
row = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 920 84' font-family='Liberation Sans, Arial, sans-serif'>"
row += "<rect x='4' y='8' width='912' height='64' rx='12' fill='#ffffff' stroke='#d4d8db'/>"
row += "<rect x='22' y='18' width='44' height='44' rx='10' fill='#f2f3f4'/>"
row += "<text x='44' y='40' font-size='20' font-weight='700' fill='#292d3a' text-anchor='middle' dominant-baseline='central'>"+T(it["Rank"])+"</text>"
row += "<text x='86' y='37' font-size='21' font-weight='700' fill='#292d3a'>"+it["CrewName"]+"</text>"
row += "<rect x='86' y='50' width='460' height='7' rx='3.5' fill='#f2f3f4'/>"
pw = round(max(6, 460*it["CrewTotal"]/max(varLeaderMax,1)))
row += "<rect x='86' y='50' width='"+T(pw)+"' height='7' rx='3.5' fill='#01a982'/>"
row += "<line x1='735' y1='22' x2='735' y2='58' stroke='#d4d8db'/>"
row += "<text x='820' y='44' font-size='30' font-weight='700' fill='#292d3a' text-anchor='end'>"+T(it["CrewTotal"])+"</text>"
row += "<text x='828' y='44' font-size='13' font-weight='600' fill='#606a70'>pts</text>"
if it["CrewPending"] > 0:
    row += "<text x='890' y='62' font-size='12.5' font-weight='600' fill='#d36d00' text-anchor='end'>+"+T(it["CrewPending"])+" pending</text>"
else:
    row += "<text x='890' y='62' font-size='12.5' fill='#606a70' text-anchor='end'>no pending</text>"
row += "</svg>"

for name, svg in [("vf-podium", podium), ("vf-grid", grid), ("vf-mypoints", mp), ("vf-row", row)]:
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT,"previews",name+".png"), scale=2)
    print("rendered", name, "len", len(svg))
print("OK - all Power Fx-mirrored SVG strings are valid")
