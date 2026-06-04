# 1% Club — Crew Dashboard (PowerApps + Power BI, HPE Design System)

Data‑driven **SVG image controls** for a **locked 1136 × 640** PowerApps screen, fed from
`PowerBIIntegration.Data`. A top ribbon spans the page; the right column is the **Crew
Leaderboard** (podium for 1‑3, gallery for 4‑10); the left column is **role‑aware**:

| Viewer role | Detected when their email is… | Left column shows | Leaderboard |
|---|---|---|---|
| **Member** | in **`User Email`** | **My Points** (their own breakdown) + their crew grid | their crew flagged **YOUR CREW** |
| **Sponsor** | in **`Manager Sponsor Email`** | **sponsored‑crew summary** + that crew's grid | sponsored crew flagged **YOU SPONSOR** |
| **Spectator** | in neither | **auto‑scrolling tour** of every crew's points breakdown | (no flag) |

Layout follows the HPE [two‑column dashboard](https://design-system.hpe.design/templates/dashboards#two-column-dashboard);
colours are the HPE [semantic / dataVis tokens (light)](https://design-system.hpe.design/design-tokens/all-design-tokens?token=semantic%2Fcolor&tokenTypes=docs&mode=light).

**Member**
![member](previews/full-page-mockup.png)
**Sponsor** &nbsp;·&nbsp; **Spectator**
![sponsor](previews/full-page-sponsor.png)
![spectator](previews/full-page-spectator.png)

---

## 1. Controls & formulas

| Control | Type | Property | Formula |
|---|---|---|---|
| **App** | — | `OnStart` | [`App_OnStart.powerfx`](formulas/App_OnStart.powerfx) |
| `tmrLoad` | **Timer** | `Start` | [`tmrLoad.Start.powerfx`](formulas/tmrLoad.Start.powerfx) — reactive trigger |
| `tmrLoad` | **Timer** | `OnTimerEnd` | [`tmrLoad.OnTimerEnd.powerfx`](formulas/tmrLoad.OnTimerEnd.powerfx) — **builds all data** |
| **Screen** | — | `OnVisible` | [`Screen_OnVisible.powerfx`](formulas/Screen_OnVisible.powerfx) (thin trigger) |
| `imgRibbon` | Image | `Image` | [`imgRibbon.Image.powerfx`](formulas/imgRibbon.Image.powerfx) |
| `imgMyPoints` | Image | `Image` | [`imgMyPoints.Image.powerfx`](formulas/imgMyPoints.Image.powerfx) |
| `imgCrewGrid` | Image | `Image` | [`imgCrewGrid.Image.powerfx`](formulas/imgCrewGrid.Image.powerfx) |
| `imgSpectator` | Image | `Image` | [`imgSpectator.Image.powerfx`](formulas/imgSpectator.Image.powerfx) |
| `imgPodium` | Image | `Image` | [`imgPodium.Image.powerfx`](formulas/imgPodium.Image.powerfx) |
| `imgRanksHeader` | Image | `Image` | [`imgRanksHeader.Image.powerfx`](formulas/imgRanksHeader.Image.powerfx) |
| `galLeaderboard` | Gallery (blank vertical) | `Items` | `colCrewRest` |
| `imgRow` (in gallery) | Image | `Image` | [`imgRow.Image.powerfx`](formulas/imgRow.Image.powerfx) |

Every Image: **`ImagePosition = ImagePosition.Fit`**.

---

## 2. Layout — locked 1136 × 640

Screen `Fill = RGBA(247,247,247,1)` (`background-back #f7f7f7`). Each image's viewBox matches
its rectangle's aspect, so it fills with no letterboxing.

| Control | X | Y | Width | Height | Visible |
|---|---:|---:|---:|---:|---|
| `imgRibbon` | 0 | 0 | 1136 | 52 | `true` |
| `imgMyPoints` | 16 | 68 | 420 | 300 | `varRole <> "spectator"` |
| `imgCrewGrid` | 16 | 380 | 420 | 244 | `varRole <> "spectator"` |
| `imgSpectator` | 16 | 68 | 420 | 556 | `varRole = "spectator"` |
| `imgPodium` | 452 | 68 | 668 | 300 | `true` |
| `imgRanksHeader` | 452 | 380 | 668 | 28 | `true` |
| `galLeaderboard` | 452 | 412 | 668 | 212 | `true` |
| `recLoading` (Rectangle) | 0 | 0 | 1136 | 640 | `!varReady` |
| `lblLoading` (Label, centred "Loading crew data…") | 0 | 0 | 1136 | 640 | `!varReady` |
| `tmrLoad` (Timer) | 1100 | 14 | 24 | 24 | `true` *(place behind `imgRibbon`, or `Fill=Transparent`, so it's hidden)* |

**Gallery** `galLeaderboard`: `Items = colCrewRest`, `TemplateSize = 30`, `TemplatePadding = 0`,
`ShowScrollbar = false`. Inside it, one Image `imgRow`: `X=0 Y=0`,
`Width = Parent.TemplateWidth`, `Height = Parent.TemplateHeight`, `ImagePosition = Fit`.
(7 rows × 30 = 210 ≈ 212 → all of ranks 4‑10 show without scrolling.)

`imgMyPoints`/`imgCrewGrid` (member & sponsor) and `imgSpectator` occupy the **same** left
column and are swapped purely by their `Visible` rule — no screen switching.

### Loads on open — REACTIVE timer (not `OnVisible`)

In a Power BI custom visual, **`PowerBIIntegration.Data` is empty for a moment after the screen
first shows**, so building collections in `Screen.OnVisible` once gives empty visuals on open —
it only "fixed itself" after navigating to another screen and back (which re‑ran `OnVisible`
after the data arrived). Build **reactively** with a Timer whose `Start` watches the row count:

1. **Insert a Timer `tmrLoad`** and set these **exactly** (the usual cause of "still empty" is
   a missing one):
   | Property | Value |
   |---|---|
   | `AutoStart` | `false` |
   | `Start` | `CountRows(PowerBIIntegration.Data) <> varRowCount` |
   | `Duration` | `50` |
   | `Repeat` | `false` |
   | `Reset` | `false` |
   | `Visible` | `true` *(timers pause when hidden — keep true, place it behind `imgRibbon`)* |
   | `OnTimerEnd` | paste [`tmrLoad.OnTimerEnd.powerfx`](formulas/tmrLoad.OnTimerEnd.powerfx) |
   `Start` re‑evaluates whenever the data changes → fires the instant rows arrive (and on slicer
   changes), `OnTimerEnd` builds, then sets `varRowCount` so `Start` goes false again.
2. **`App.OnStart`** → `Set(varRowCount,-1); Set(varReady,false)`.
3. **`Screen.OnVisible`** → `Set(varRowCount,-1)` (forces a rebuild whenever the screen is shown).
4. **Loading state**: a full‑screen `recLoading` rectangle + `lblLoading` ("Loading crew data…")
   with `Visible = !varReady` cover the page until `OnTimerEnd` sets `varReady=true`.

Result: it loads on open with **no navigation**. Collections are app‑global so they persist
across screens.

#### Still blank? Add the one‑line diagnostic
Drop a Label `lblDebug` on the screen with `Text =` the contents of
[`lblDebug.Text.powerfx`](formulas/lblDebug.Text.powerfx). It reads e.g.
`data=86 | ready=true | members=86 | crews=10 | role=member …` and tells you where it stalls:

| What you see | Meaning → fix |
|---|---|
| `data=0` always | Power BI is sending **no rows**. In Power BI, add the fields to the PowerApps visual's data well (Name, Crew, User Email, Manager Sponsor Email, **every points column**). |
| `data>0` but `members=0` | Build failed — almost always a **column‑name mismatch**. Make the names in `tmrLoad` match your fields exactly (e.g. `'IB & NS Points'`). |
| `started=false` forever, `data>0` | Timer never fired — re‑check the `tmrLoad` properties above (especially `Start`, `AutoStart=false`, `Visible=true`). |
| `members>0` but visuals blank | Image controls aren't bound to the latest formulas / `Visible` rules — re‑paste them. |

Delete `lblDebug` once it works.

---

## 3. Roles (built by `tmrLoad`)

```
varUserEmail  = Lower(User().Email)
varMemberRec  = LookUp(colMembers, Lower('User Email')          = varUserEmail)
varSponsorRec = LookUp(colMembers, Lower('Manager Sponsor Email')= varUserEmail)
varRole       = member | sponsor | spectator
varMyCrew     = the crew to feature on the left + flag on the board (Blank for spectator)
varMyCrewTag  = "YOUR CREW" (member) | "YOU SPONSOR" (sponsor)
```

- **Member** → `imgMyPoints` shows their personal 6‑category breakdown; `imgCrewGrid` shows
  their crew with the **YOU** tile highlighted.
- **Sponsor** → `imgMyPoints` becomes a **crew summary** (crew total + the 6 categories summed
  for the crew); `imgCrewGrid` shows that crew (no personal highlight).
- **Spectator** → `imgSpectator` slowly auto‑scrolls a card per crew (rank, total, and a mini
  bar per category) — a hands‑off "kiosk" tour. Speed/scroll length scale with crew count.
- **Crew flag** → on the podium and gallery, the row/card whose `Crew = varMyCrew` gets a green
  outline + a `varMyCrewTag` chip. Spectators see no flag.

> **Test a role** without changing accounts: after `tmrLoad` runs, set
> `Set(varUserEmail, "jordan.smith@example.com")` (member) /
> a `Manager Sponsor Email` value (sponsor) / a non‑existent email (spectator) and re‑run.

---

## 4. Data model & scoring

`PowerBIIntegration.Data` columns arrive as in the sheet — note spaces / `&` / `?`, so Power Fx
wraps them in single quotes, e.g. `'IB & NS Points'`.

**Counted toward totals:** `IB & NS Points` · `Manager Sponsor Points` · `New CC Logo Points` ·
`Cap Won Points` · `Cap Requests` · `Customer Centricity Points` · `IP in GL points`.
**Pending** = the three `*Pending` columns.

```
MemberTotal = sum of the 7 point columns (excl. pending)
CrewTotal   = sum of MemberTotal over the crew      Rank = crews by CrewTotal desc (ties: lower #)
Pending     = sum of the *Pending columns           "points pending" = per-crew Pending
```

**Category re‑labels** (My Points / Crew summary / Spectator):

| Label | Source |
|---|---|
| New CC Logo / IB Upsell | `IB & NS Points` + `New CC Logo Points` |
| CAP Engagement | `Cap Requests` |
| CAP Orders Booked | `Cap Won Points` |
| Customer Centricity | `Customer Centricity Points` |
| Accreditation Race | `Manager Sponsor Points` |
| IP Push | `IP in GL points` |

Collections built by `tmrLoad`: `colMembers` → `colCrew` (ranked) → `colCrewRest` (4‑10),
`colCrewBreak` (per‑crew category sums, for sponsor box + spectator), `colMyCrew` (viewer's crew,
grid), plus the role / box / `varSvgCss` variables.

### Components
| | |
|---|---|
| Ribbon | ![ribbon](previews/ribbon.png) |
| My Points (member) · Crew summary (sponsor) | ![mp](previews/my-points.png) ![cs](previews/crew-summary.png) |
| Crew grid · Podium | ![grid](previews/crew-grid.png) ![podium](previews/podium.png) |
| Gallery rows · Spectator tour | ![rows](previews/leaderboard-gallery.png) ![spec](previews/spectator.png) |

---

## 5. HPE colour tokens (light)

`background-back #f7f7f7` · card `#ffffff` · contrast `#f2f3f4` · border `#d4d8db` ·
text `#292d3a / #3e4550 / #606a70` · brand green `#01a982` · dark green `#006750` ·
green tint `#d1ffee` · warning `#d36d00`. Category accents (dataVis categorical):
`#0070f8 #04909d #009a71 #7764fc #cc54a4 #d25f4b`. Medals gold/silver/bronze
`#E0A300 #8C99A4 #B5742E`.

---

## 6. Animations (motion)

CSS keyframes embedded in each SVG (`<style>`), defined once as `varSvgCss` in `tmrLoad`.
Runs in PowerApps' WebView2 image rendering; hidden start‑states live only in `@keyframes` so
static/`reduced-motion` renders show the settled design. **Honours `prefers-reduced-motion`.**

- **Ribbon / My Points / Crew summary**: fade‑up; avatar pops + idle halo; cards fade in
  staggered; pending chip pulses.
- **Podium**: cards rise (winner last); medals pop; gold champion halo; the flagged card draws
  a green outline + chip.
- **Gallery**: rows slide in staggered by rank; bar grows; the flagged row tints + chip.
- **Crew grid**: tiles pop in staggered; **YOU** tile breathes.
- **Spectator**: continuous slow vertical auto‑scroll (`scrl`) through all crews.

---

## 7. Gotchas

- **Dynamic SVG**: `"data:image/svg+xml;utf8," & EncodeUrl( "<svg…>" & values & "</svg>" )` on an
  Image. Single quotes for all attributes; `EncodeUrl` round‑trips the markup.
- **Repeats** use `Concat()` over a collection / inline `Table()` — that's how non‑gallery
  visuals draw N members / 3 podium slots / 6 categories / 10 spectator cards.
- **Coordinates are integers** (delays in `ms`, `Int()`/`Round()` for sizes) to avoid locale
  decimal separators breaking SVG geometry.
- **Text escaping**: human names pass through `Substitute(… & < >)`. `·` and `–` in labels are
  safe (EncodeUrl‑encoded, not XML metacharacters).
- **Font**: `Segoe UI` (native in PowerApps). Swap to `'Metric, Segoe UI, …'` to match HPE exactly.
- **`Index(colCrew,n)`** → `Last(FirstN(colCrew,n))` on older Power Fx.
- **Who am I**: `User().Email`. In a Power BI custom‑visual context, feed the email via
  `PowerBIIntegration` and set `varUserEmail` from it instead.

---

## 8. Regenerate / verify (optional)

```bash
pip install cairosvg openpyxl
python3 _generate_previews.py    # writes svg/ + previews/ (member, sponsor, spectator)
python3 _verify_powerfx_svg.py   # XML-validates the SVGs + structural-checks the .powerfx
```
