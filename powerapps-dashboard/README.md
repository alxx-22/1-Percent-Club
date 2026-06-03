# 1% Club — Crew Dashboard (PowerApps + Power BI, HPE Design System)

Data‑driven **SVG image controls** for a two‑column PowerApps dashboard, fed from
`PowerBIIntegration.Data`. Two views:

* **Right – Crew Leaderboard:** a non‑gallery **podium** for ranks 1‑3 and a **gallery**
  for ranks 4‑10.
* **Left – In‑Crew:** a big **“My Points”** box (your breakdown) above a non‑gallery
  **member grid** (everyone in your crew + their total points).

Layout follows the HPE [two‑column dashboard template](https://design-system.hpe.design/templates/dashboards#two-column-dashboard);
colours are the HPE [semantic / dataVis tokens (light mode)](https://design-system.hpe.design/design-tokens/all-design-tokens?token=semantic%2Fcolor&tokenTypes=docs&mode=light).

![Full page mockup](previews/full-page-mockup.png)

> The PNGs in `previews/` are rendered from the **exact same SVG string fragments** the
> Power Fx formulas concatenate, so what you see is what the app draws.

---

## 1. What you paste where

| # | Control (type) | Property | Formula file |
|---|----------------|----------|--------------|
| 0 | **Screen** | `OnVisible` | [`formulas/Screen_OnVisible.powerfx`](formulas/Screen_OnVisible.powerfx) |
| 1 | `imgPodium` (Image) | `Image` | [`formulas/imgPodium.Image.powerfx`](formulas/imgPodium.Image.powerfx) |
| 2 | `galLeaderboard` (blank vertical Gallery) | `Items` | `colCrewRest` |
| 2b| `imgRow` (Image, inside the gallery) | `Image` | [`formulas/imgRow.Image.powerfx`](formulas/imgRow.Image.powerfx) |
| 3 | `imgMyPoints` (Image) | `Image` | [`formulas/imgMyPoints.Image.powerfx`](formulas/imgMyPoints.Image.powerfx) |
| 4 | `imgCrewGrid` (Image) | `Image` + `Height` | [`formulas/imgCrewGrid.Image.powerfx`](formulas/imgCrewGrid.Image.powerfx) |

Every Image control: set **`ImagePosition = ImagePosition.Fit`**.

---

## 2. Data model & scoring

`PowerBIIntegration.Data` columns (exactly as they arrive from Power BI — note the spaces /
`&` / `?`, so Power Fx wraps them in single quotes, e.g. `'IB & NS Points'`):

**Counted toward the total** (and the member squares):

```
IB & NS Points · Manager Sponsor Points · New CC Logo Points ·
Cap Won Points · Cap Requests · Customer Centricity Points · IP in GL points
```

**Pending** = every column whose name contains *“Pending”*:

```
Cap Won Points Pending · Cap Requests Pending · Customer Centricity Points Pending
```

```
MemberTotal   = sum of the 7 point columns          (excludes pending)
MemberPending = sum of the 3 pending columns
CrewTotal     = sum of MemberTotal   over the crew
CrewPending   = sum of MemberPending over the crew   → the “points pending” label
Rank          = crews sorted by CrewTotal desc (ties → lower crew #)
```

**“My Points” category re‑labels** (left box):

| Box label | Source column(s) |
|-----------|------------------|
| New CC Logo / IB Upsell | `IB & NS Points` **+** `New CC Logo Points` |
| CAP Engagement | `Cap Requests` |
| CAP Orders Booked | `Cap Won Points` |
| Customer Centricity | `Customer Centricity Points` |
| Accreditation Race | `Manager Sponsor Points` |
| IP Push | `IP in GL points` |

### Collections built in `OnVisible`
`colMembers` (per person + `MemberTotal`/`MemberPending`) → `colCrew` (ranked crews) →
`colCrewRest` (ranks 4‑10, the gallery) + `varLeaderMax`; plus `varMe`, `varMyCrew`,
`varMyInitials`, and `colMyCrew` (your crew with a 0‑based `Idx` for the grid).

---

## 3. Layout (control tree & sizes)

Screen `Fill = RGBA(247,247,247,1)` (HPE `background-back #f7f7f7`).

```
scrDashboard  (Fill #f7f7f7)
├─ conHeader            X=0   Y=0    W=Parent.Width  H=64   Fill=White
│   └─ lblTitle "1% Club  ·  Crew Dashboard"
├─ LEFT COLUMN          X=24  Y=100  W=440
│   ├─ imgMyPoints      W=440  H=imgMyPoints.Width*360/440      (≈295)
│   └─ imgCrewGrid      Y=below   W=440
│                       H=imgCrewGrid.Width*(46+RoundUp(CountRows(colMyCrew)/2,0)*102+4)/440
└─ RIGHT COLUMN         X=488 Y=100  W=854   (=Parent.Width-488-24 on a 1366 screen)
    ├─ imgPodium        W=854  H=imgPodium.Width*440/920         (≈408)
    └─ galLeaderboard   Y=below   W=854   TemplateSize=84
        └─ imgRow       X=0 Y=0  W=Parent.TemplateWidth  H=Parent.TemplateHeight
```

Prefer responsive? Drop the two columns into a **Horizontal container** (left `FillPortions=2`,
right `FillPortions=3`) and put each column’s controls in a **Vertical container**.

### Components
| | |
|---|---|
| Podium (ranks 1‑3) | ![podium](previews/podium.png) |
| Gallery rows (4‑10) | ![rows](previews/leaderboard-gallery.png) |
| My Points box | ![my points](previews/my-points.png) |
| Crew member grid | ![grid](previews/crew-grid.png) |

---

## 4. HPE colour tokens used (light mode)

| Token | Hex | Used for |
|-------|-----|----------|
| `background-back` | `#f7f7f7` | screen canvas |
| `background-default` | `#ffffff` | cards |
| `background-contrast` | `#f2f3f4` | rank tiles / track |
| `border-weak` | `#d4d8db` | card borders |
| `text-strong` | `#292d3a` | numbers / names |
| `text-default` | `#3e4550` | body |
| `text-weak` | `#606a70` | labels |
| `decorative-brand` | `#01a982` | HPE green (avatar, bars, “you”) |
| `text-primary` | `#006750` | point totals (dark green) |
| `icon-warning` | `#d36d00` | pending |
| dataVis categorical 10/20/30/50/60/80 | `#0070f8` `#009a71` `#7764fc` `#cc54a4` `#04909d` `#d25f4b` | the 6 category accents |
| medal gold / silver / bronze | `#E0A300` `#8C99A4` `#B5742E` | podium ranks 1/2/3 |

---

## 5. How the dynamic SVG works (and gotchas)

* **Pattern:** `"data:image/svg+xml;utf8," & EncodeUrl( "<svg …>" & values & "</svg>" )`,
  bound to an **Image** control. `EncodeUrl` percent‑encodes the markup; the host decodes it
  back to SVG, so anything it encodes round‑trips safely.
* **Quotes:** every SVG attribute uses **single quotes** so you never have to escape `"`
  inside the Power Fx string.
* **Repeating shapes** (variable rows) are built with **`Concat()`** over a collection
  (`colMyCrew`) or an inline `Table()` (podium slots / the 6 categories) — that is how a
  *non‑gallery* visual draws N members in one image. Tile position is pure maths:
  `Mod(Idx,2)` = column, `Int(Idx/2)` = row.
* **Escaping text:** values that are typed by humans (member names) are passed through
  `Substitute(... "&"→"&amp;", "<"→"&lt;", ">"→"&gt;")` so a stray `&` can’t break the XML.
  Numbers are safe.
* **Font:** formulas use `Segoe UI` (renders natively in PowerApps). To match HPE exactly,
  embed **Metric** and change `font-family` to `'Metric, Segoe UI, Arial, sans-serif'`.
* **`Index(colCrew, n)`** returns the n‑th row; on older Power Fx use
  `Last(FirstN(colCrew, n))` instead (same result).
* **Who am I:** `User().Email` drives `varMe`. In a Power BI custom‑visual context you can
  instead pass the e‑mail in through `PowerBIIntegration` and set `varUserEmail` from it.
  There’s a Crew‑1 fallback so the page still renders while testing with sample data.
* **Blanks:** the sample sheet is sparse — every numeric column is wrapped in
  `Coalesce(x, 0)` so blanks read as 0.
* **Refresh:** the visual recomputes on `OnVisible`; call `Set(varRefresh, Rand())` or
  re‑run the `OnVisible` block from a refresh button if the Power BI data updates in place.

---

## 6. Animations (motion)

Entrance + idle motion is **CSS keyframes embedded in each SVG** (`<style>`), defined
once as `varSvgCss` in `OnVisible` and injected into every image via `& varSvgCss &`.
CSS animation runs in PowerApps' WebView2 image rendering (img‑mode allows declarative
CSS — only scripts are blocked); the hidden start‑states live **only** inside
`@keyframes`, so any static export still shows the settled design.

Tuned to HPE motion — purposeful, smooth, low‑amplitude, ease‑out ~0.5s — and it
**honours `prefers-reduced-motion`** (motion off → content simply appears):

| Component | Entrance | Idle |
|-----------|----------|------|
| **Podium** | cards rise + fade, **winner revealed last** (3rd → 2nd → 1st); medals pop in | gold medal **champion halo** pulses |
| **Leaderboard rows** | slide in from the left, **staggered by rank** `(Rank‑4)·80ms`; progress bar **grows** from 0 | — (kept calm; many rows) |
| **My Points** | box rises, avatar pops, the 6 category cards fade in staggered | avatar **halo**; **pending** chip gently pulses |
| **Crew grid** | tiles **pop** in, staggered by position | your **“YOU”** tile breathes |

Classes: `fu` fade‑up · `fo` fade · `pp` pop · `gx` grow‑bar · `rw` row‑slide ·
`ring` idle halo · `brz` idle pulse. Per‑element timing is `style='animation-delay:<n>ms'`.
To restyle every visual at once, edit the single `varSvgCss` block. Entrances replay
when the screen is re‑shown or the data changes; idle loops run continuously. The
`svg/` files animate when opened in any browser (a PNG can’t show motion).

---

## 7. Regenerate the previews (optional)

```bash
pip install cairosvg openpyxl
python3 _generate_previews.py      # design references (svg/ + previews/)
python3 _verify_powerfx_svg.py     # proves the Power Fx SVG strings are valid markup
```

`svg/` holds standalone reference SVGs with mock data; the live values come from
`PowerBIIntegration.Data` via the formulas above.
