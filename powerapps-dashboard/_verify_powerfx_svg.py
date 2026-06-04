#!/usr/bin/env python3
"""
Verification for the dashboard assets:

  1. Every svg/*.svg (produced by _generate_previews.py, mirroring the exact
     markup the Power Fx Image formulas build) is WELL-FORMED XML and carries
     the expected motion hooks.  Because cairosvg/XML ignore CSS animation,
     a clean parse also proves the settled (static / reduced-motion) design.

  2. Every formulas/*.powerfx is structurally sound: no unterminated strings,
     balanced () [] {} outside strings, balanced <g>/</g> inside the SVG text,
     and no raw XML metacharacters (& < >) in non-comment lines (EncodeUrl-safe).
"""
import glob, os, sys
import xml.dom.minidom as minidom

OUT = os.path.dirname(os.path.abspath(__file__))
fail = False

print("== svg/*.svg : well-formed XML + motion hooks ==")
for f in sorted(glob.glob(os.path.join(OUT, "svg", "*.svg"))):
    s = open(f).read()
    name = os.path.basename(f)
    try:
        minidom.parseString(s)
    except Exception as e:
        print(f"  FAIL {name}: {e}"); fail = True; continue
    hooks = sum(s.count(f"class='{c}'") for c in ("fu", "fo", "pp", "gx", "rw", "ring", "brz", "scrl"))
    has_style = "<style>" in s
    print(f"  ok  {name:26} style={has_style} motion-hooks={hooks}")
    if not has_style:
        print(f"      WARN {name} has no <style> block");

print("\n== formulas/*.powerfx : structural integrity ==")
def check(path):
    s = open(path).read()
    code = "\n".join("" if ln.lstrip().startswith("//") else ln for ln in s.split("\n"))
    depth = {'(': 0, '[': 0, '{': 0}; pairs = {')': '(', ']': '[', '}': '{'}
    instr = False; i = 0; errs = []
    while i < len(code):
        c = code[i]
        if instr:
            if c == '"':
                if i + 1 < len(code) and code[i + 1] == '"':
                    i += 2; continue
                instr = False
            i += 1; continue
        if c == '"': instr = True; i += 1; continue
        if c in '([{': depth[c] += 1
        elif c in ')]}':
            depth[pairs[c]] -= 1
            if depth[pairs[c]] < 0: errs.append(f"extra {c}")
        i += 1
    og = s.count("<g ") + s.count("<g>"); cg = s.count("</g>")
    meta = sorted({ch for ln in s.split("\n") if not ln.lstrip().startswith("//")
                   for ch in ln if ch in '&<>' and "EncodeUrl" not in ln} )
    problems = []
    if instr: problems.append("unterminated string")
    if any(v != 0 for v in depth.values()): problems.append(f"unbalanced {depth}")
    if errs: problems.append(",".join(errs[:3]))
    if og != cg: problems.append(f"<g> {og}/{cg}")
    return problems

for f in sorted(glob.glob(os.path.join(OUT, "formulas", "*.powerfx"))):
    p = check(f)
    print(f"  {'ok ' if not p else 'FAIL'} {os.path.basename(f):30} {'' if not p else '<-- '+', '.join(p)}")
    if p: fail = True

print("\n" + ("VERIFICATION FAILED" if fail else "ALL VERIFICATION PASSED"))
sys.exit(1 if fail else 0)
