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

There's also a **second page — the [Crew Portal](#8-crew-portal-second-page)** — opened from a
button on the ribbon: crew profile cards along the top, the crew's opportunity pipeline on the
left, and a per‑opportunity detail panel on the right, with a branded **leaf‑wipe** transition
between the two pages.

![crew portal](previews/full-portal.png)

---

## 1. Controls & formulas

| Control | Type | Property | Formula |
|---|---|---|---|
| **App** | — | `OnStart` | [`App_OnStart.powerfx`](formulas/App_OnStart.powerfx) — `varReady` + portal/transition vars |
| `imgLoading` (on **scrLoading**, the 1st screen) | Image | `Image` | [`imgLoading.Image.powerfx`](formulas/imgLoading.Image.powerfx) |
| `tmrGo` (on scrLoading) | Timer | `OnTimerEnd` | [`tmrGo.OnTimerEnd.powerfx`](formulas/tmrGo.OnTimerEnd.powerfx) — auto‑enter when data ready |
| `btnEnter` (on scrLoading) | Button | `OnSelect` | [`btnEnter.OnSelect.powerfx`](formulas/btnEnter.OnSelect.powerfx) — manual fallback |
| **scrDashboard** | Screen | `OnVisible` | [`Screen_OnVisible.powerfx`](formulas/Screen_OnVisible.powerfx) — **builds all data** |
| `imgRibbon` | Image | `Image` | [`imgRibbon.Image.powerfx`](formulas/imgRibbon.Image.powerfx) |
| `imgMyPoints` | Image | `Image` | [`imgMyPoints.Image.powerfx`](formulas/imgMyPoints.Image.powerfx) |
| `imgCrewGrid` | Image | `Image` | [`imgCrewGrid.Image.powerfx`](formulas/imgCrewGrid.Image.powerfx) |
| `imgSpectator` | Image | `Image` | [`imgSpectator.Image.powerfx`](formulas/imgSpectator.Image.powerfx) |
| `imgPodium` | Image | `Image` | [`imgPodium.Image.powerfx`](formulas/imgPodium.Image.powerfx) |
| `imgRanksHeader` | Image | `Image` | [`imgRanksHeader.Image.powerfx`](formulas/imgRanksHeader.Image.powerfx) |
| `galLeaderboard` | Gallery (blank vertical) | `Items` | `colCrewRest` |
| `imgRow` (in gallery) | Image | `Image` | [`imgRow.Image.powerfx`](formulas/imgRow.Image.powerfx) |
| `imgCrewPortalBtn` (on ribbon) | Image | `Image` + `OnSelect` | [`imgCrewPortalBtn.Image.powerfx`](formulas/imgCrewPortalBtn.Image.powerfx) (SVG) · OnSelect = [`btnCrewPortal.OnSelect.powerfx`](formulas/btnCrewPortal.OnSelect.powerfx) — open the **Crew Portal** (§8) |
| `imgLeafWipe` | Image | `Image` | [`imgLeafWipe.Image.powerfx`](formulas/imgLeafWipe.Image.powerfx) — page‑transition overlay (§8) |
| `tmrLeaf` | Timer | `OnTimerEnd` | [`tmrLeaf.OnTimerEnd.powerfx`](formulas/tmrLeaf.OnTimerEnd.powerfx) — dismisses the overlay (§8) |

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
| `recLoading` (Rectangle, optional) | 0 | 0 | 1136 | 640 | `!varReady` |
| `lblLoading` (Label, optional, "Loading crew data…") | 0 | 0 | 1136 | 640 | `!varReady` |

**Gallery** `galLeaderboard`: `Items = colCrewRest`, `TemplateSize = 30`, `TemplatePadding = 0`,
`ShowScrollbar = false`. Inside it, one Image `imgRow`: `X=0 Y=0`,
`Width = Parent.TemplateWidth`, `Height = Parent.TemplateHeight`, `ImagePosition = Fit`.
(7 rows × 30 = 210 ≈ 212 → all of ranks 4‑10 show without scrolling.)

`imgMyPoints`/`imgCrewGrid` (member & sponsor) and `imgSpectator` occupy the **same** left
column and are swapped purely by their `Visible` rule — no screen switching.

### Loads on open — land on a splash screen, then enter the dashboard

The data build lives in **`scrDashboard.OnVisible`** and runs every time the screen is shown —
**navigating in always builds correctly** (the data is there by then). The only gotcha is the
*very first* open: `PowerBIIntegration.Data` lands a beat after the screen first appears, so a
cold open can be blank. Fix it by **opening on a small landing screen** and entering the
dashboard once data is ready:

1. **`scrLoading`** = the app's **first screen**. Put `imgLoading`
   ([`imgLoading.Image.powerfx`](formulas/imgLoading.Image.powerfx)) full‑screen — a branded
   "Loading crew dashboard…" splash with a spinning ring (self‑contained, no data needed).
2. **Auto‑advance:** Timer `tmrGo` on `scrLoading` (`AutoStart=true`, `Repeat=true`,
   `Duration=500`), `OnTimerEnd` = [`tmrGo.OnTimerEnd.powerfx`](formulas/tmrGo.OnTimerEnd.powerfx)
   → `If(CountRows(PowerBIIntegration.Data)>0, Navigate(scrDashboard,…))`. The instant data
   arrives it enters the dashboard, whose `OnVisible` then builds with data present.
3. **Guaranteed fallback:** a Button `btnEnter` ("View dashboard"),
   `OnSelect` = [`btnEnter.OnSelect.powerfx`](formulas/btnEnter.OnSelect.powerfx). If timers don't
   fire in your visual, one tap still works — exactly the "navigate in" path that already works.

![loading splash](previews/loading.png)

> **Build gotchas already handled in `OnVisible`:** (1) a **blank numeric cell throws on read**
> ("expected 'number' but got 'string'") — every point cell is read with `IfError(pbi.col,0)`
> (`Coalesce`/`Value` can't help; the error is at field access). (2) this environment rejects
> `GroupBy`/`SortByColumns` **string column names** — so the build uses
> `Distinct`/`Filter`/`Sum`/`Sort(<expression>)`/`ForAll` instead.

#### Still blank? Add the diagnostic labels
Add Labels with `Text =` [`lblDebug.Text.powerfx`](formulas/lblDebug.Text.powerfx) and
[`lblDebugSchema.Text.powerfx`](formulas/lblDebugSchema.Text.powerfx) — see **[DEBUG.md](DEBUG.md)**:

| Reading | Meaning → fix |
|---|---|
| `rows=0` always | Power BI is sending **no rows** — add the fields to the PowerApps visual's data well. |
| `rows>0` but `colMembers=0` | Build didn't run / errored. If `varRole` is **blank** → build never ran (don't use a Timer; use `OnVisible`). If you see a red **JSON `expected 'number' got 'string'`** → a numeric column arrives as text (OnVisible already coerces via `Value(field & "")`; else set it to Whole Number in Power BI). Check names/values with `lblDebugSchema`. |
| `colMembers>0`, visuals blank | Image controls not on the latest formulas / wrong `Visible` rules. |

Delete the debug labels once it works.

---

## 3. Roles (built in `OnVisible`)

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

> **Test a role** without changing accounts: drop a **diagnostic button** with `OnSelect` =
> [`btnTestRole.OnSelect.powerfx`](formulas/btnTestRole.OnSelect.powerfx). Each tap cycles the
> viewer through *Guest → crew #1 → crew #2 → … → back to you*. It only sets an override email
> (`varTestEmail`) and **re-runs `OnVisible`** (via the loading screen) — it does **not** recompute
> state itself, so it can't half-break the UI. Needs two one-time lines (both production-safe,
> since `varTestEmail` is blank in production):
> - `App.OnStart`: `Set( varTestEmail, "" )`  (use `""`, not `Blank()`, so the var has a Text type — otherwise you get *"No type found for variable 'varTestEmail'"*)
> - `scrDashboard.OnVisible` step 3: `Set( varUserEmail, If( Len( varTestEmail ) > 0, Lower( varTestEmail ), Lower( User().Email ) ) )`
>
> Remove the button before shipping.

---

## 4. Data model & scoring

`PowerBIIntegration.Data` columns arrive as in the sheet — note spaces / `&` / `?`, so Power Fx
wraps them in single quotes, e.g. `'IB & NS Points'`.

> **`Crew` holds the team's NAME (text)**, not a number. `OnVisible` reads it as trimmed text
> (blank → "Unassigned"); grouping, the YOUR CREW / YOU SPONSOR flag and the left column all
> match on the name. Names are human input, so every SVG that prints one truncates first, then
> XML‑escapes (`&` `<` `>`): podium 16 chars · gallery rows 22 · grid title 20 · spectator 24.
> Ranking ties break alphabetically via a text `SortKey` (no `SortByColumns`).

**Counted toward totals:** `IB & NS Points` · `Manager Sponsor Points` · `New CC Logo Points` ·
`Cap Won Points` · `Cap Requests` · `Customer Centricity Points` · `IP in GL points`.
**Pending** = the three `*Pending` columns.

```
MemberTotal = sum of the 7 point columns (excl. pending)
CrewTotal   = sum of MemberTotal over the crew      Rank = crews by CrewTotal desc (ties: A→Z)
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

Collections built in `OnVisible`: `colMembers` → `colCrew` (ranked) → `colCrewRest` (4‑10),
`colCrewBreak` (per‑crew category sums, for sponsor box + spectator), `colMyCrew` (viewer's crew,
grid), plus the role / box / `varSvgCss` variables.

> **Job role** — `colMembers` also carries `Role`, read from the **`Job Family`** column, used by
> the Crew Portal cards (§8). Make sure `Job Family` is in the PowerApps visual's data well.

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

CSS keyframes embedded in each SVG (`<style>`), defined once as `varSvgCss` in `OnVisible`.
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

## 8. Crew Portal (second page)

A second screen, **`scrPortal`**, opened from a **Crew Portal** button on the dashboard ribbon.
Same locked **1136 × 640**, same HPE tokens and motion language. It shows the viewer's crew as
**profile cards** along the top, a **brief opportunity list** on the left (Name · Funnel Type ·
Account Name), and on the right either a **pipeline overview** (the default "underneath" visual) or
the **full detail** of the opportunity you select.

**Nothing selected** (pipeline overview) &nbsp;·&nbsp; **Opportunity selected** (detail)
![portal overview](previews/full-portal-empty.png)
![portal detail](previews/full-portal.png)

### 8.1 Controls & formulas

| Control | Screen | Type | Property | Formula |
|---|---|---|---|---|
| `imgCrewPortalBtn` | scrDashboard (ribbon) | Image | `Image` + `OnSelect` | SVG button [`imgCrewPortalBtn.Image.powerfx`](formulas/imgCrewPortalBtn.Image.powerfx); OnSelect = [`btnCrewPortal.OnSelect.powerfx`](formulas/btnCrewPortal.OnSelect.powerfx) — arm transition, `Navigate(scrPortal)` |
| **scrPortal** | — | Screen | `OnVisible` | [`Screen_Portal_OnVisible.powerfx`](formulas/Screen_Portal_OnVisible.powerfx) — **parses the pack into `colCrewOpps`** then builds `colOpps` / `colPipe` / `colCrewCards` |
| `imgPortalRibbon` | scrPortal | Image | `Image` | [`imgPortalRibbon.Image.powerfx`](formulas/imgPortalRibbon.Image.powerfx) |
| `imgBackBtn` | scrPortal (ribbon) | Image | `Image` + `OnSelect` | SVG button [`imgBackBtn.Image.powerfx`](formulas/imgBackBtn.Image.powerfx); OnSelect = [`btnBack.OnSelect.powerfx`](formulas/btnBack.OnSelect.powerfx) — `Navigate(scrDashboard)` |
| `imgCrewCards` | scrPortal | Image | `Image` | [`imgCrewCards.Image.powerfx`](formulas/imgCrewCards.Image.powerfx) — roster cards |
| `imgOppHeader` | scrPortal | Image | `Image` | [`imgOppHeader.Image.powerfx`](formulas/imgOppHeader.Image.powerfx) |
| `galCrewOpps` | scrPortal | Gallery (blank vertical) | `Items` | `colOpps` |
| `galCrewOpps` | scrPortal | Gallery | `OnSelect` | [`galCrewOpps.OnSelect.powerfx`](formulas/galCrewOpps.OnSelect.powerfx) — set `varSelOpp` + wrap update text |
| `imgOppRow` (in gallery) | scrPortal | Image | `Image` | [`imgOppRow.Image.powerfx`](formulas/imgOppRow.Image.powerfx) |
| `imgOppDetail` | scrPortal | Image | `Image` | [`imgOppDetail.Image.powerfx`](formulas/imgOppDetail.Image.powerfx) |
| `imgPipeline` | scrPortal | Image | `Image` | [`imgPipeline.Image.powerfx`](formulas/imgPipeline.Image.powerfx) |
| `imgLeafWipe` | both screens | Image | `Image` | [`imgLeafWipe.Image.powerfx`](formulas/imgLeafWipe.Image.powerfx) — transition overlay |
| `tmrLeaf` | both screens | Timer | `OnTimerEnd` | [`tmrLeaf.OnTimerEnd.powerfx`](formulas/tmrLeaf.OnTimerEnd.powerfx) |

Every Image: `ImagePosition = Fit` (except `imgLeafWipe` = **`Fill`**).

### 8.2 Layout — locked 1136 × 640

| Control | X | Y | Width | Height | Visible |
|---|---:|---:|---:|---:|---|
| `imgPortalRibbon` | 0 | 0 | 1136 | 52 | `true` |
| `imgBackBtn` (SVG, OnSelect = back) | 16 | 11 | 132 | 30 | `true` |
| `imgCrewCards` | 16 | 68 | 1104 | 150 | `true` |
| `imgOppHeader` | 16 | 230 | 420 | 30 | `true` |
| `galCrewOpps` | 16 | 262 | 420 | 362 | `true` |
| `imgOppDetail` | 452 | 230 | 668 | 394 | `!IsBlank(varSelOpp.OppId)` |
| `imgPipeline` | 452 | 230 | 668 | 394 | `IsBlank(varSelOpp.OppId)` |
| `imgLeafWipe` (top of z‑order, both screens) | 0 | 0 | 1136 | 640 | `varLeafBusy` |

On the **dashboard ribbon**, place the SVG button **`imgCrewPortalBtn`** at `X=720 Y=11 W=140 H=30`
(`ImagePosition=Fit`) and paste the `btnCrewPortal.OnSelect` formula straight onto the image's
**`OnSelect`** — Image controls are tappable, so no separate Button is needed. (Prefer a real
Button? Use one with that OnSelect: fill brand green `RGBA(1,169,130,1)`, white text "Crew Portal",
radius 15, no border — or lay a transparent Button over the SVG for hover/press feedback.)

**Gallery** `galCrewOpps`: `Items = colOpps`, `TemplateSize = 64`, `TemplatePadding = 0`,
`ShowScrollbar = false`. Inside it, one Image `imgOppRow`: `X=0 Y=0 Width=Parent.TemplateWidth
Height=Parent.TemplateHeight ImagePosition=Fit`. Set the gallery's `OnSelect` to the formula above
(it also fires `Select(galCrewOpps)`‑style when a row image is tapped).

`imgOppDetail` and `imgPipeline` occupy the **same** rectangle and swap purely by their `Visible`
rule — selecting an opp shows the detail and hides the overview; clearing it reverses.

### 8.3 The opportunity data

**`scrPortal.OnVisible`** runs your pack‑parsing formula (so it rebuilds every time the portal
opens — the button just navigates): it reads the signed‑in user's **`Crew Funnel Pack`** from
**`PowerBIIntegration.Data`** (so that column must be in the visual's data well), splits it on `||`
(rows) then `//` (columns), and `Collect`s `colCrewOpps` with `FunnelType · OppId · OppName ·
AccountName · ForecastCategory · CloseDate · TotalValue · MemberName · OppUpdate`. The same
`OnVisible` then turns that into:

> **`Split()` column name:** this environment returns `.Value` (e.g. `Index(Split(row,"//"),2).Value`);
> some Power Fx builds use `.Result`. If you hit "Value/Result isn't recognized", swap the suffix.

```
colOpps   = colCrewOpps + a 0-based Idx           (list rows: stagger + selection)
colPipe   = value + count per Forecast Category    (the overview bars; ordered
            Commit → Best Case → Pipeline → Upside → Omitted, then by value)
varPipeTotal / varPipeMax  = hero total + bar scaling
colCrewCards = the crew roster, viewer first + larger (name · Role · MemberTotal)
```

The roster cards reuse `colMembers` (so the **`Role`** field from §4 is required). The feature card
(index 0 — the viewer for a member, or the top scorer otherwise) is 1.5× wide; the viewer's own
card is green with a **YOU** tag. Card widths come from `varCardBig / varCardSmall / varCardGap`, so
the strip always fills 1104 px for any crew size.

### 8.4 The leaf‑wipe page transition

The "universal transition" between the two pages. `imgLeafWipe` is a full‑screen overlay (on both
screens, top of z‑order, `Visible = varLeafBusy`): a branded green panel sweeps across while leaves
tumble, then exits to clear. Its `<desc>` holds **`varLeafKey`** — every navigation bumps the key,
which changes the Image string so the control **reloads and replays** the CSS animation from the
start (the same `<desc>`/reload trick your original leaf SVG used, but with a richer, self‑contained
vector animation — no external PNG needed).

```
btnCrewPortal / btnBack:  Set(varLeafKey, varLeafKey+1); Set(varLeafBusy, true);
                          Navigate(scr…, ScreenTransition.Cover | .UnCover)
tmrLeaf (both screens):   Duration=1100  Repeat=false  Start=varLeafBusy  Reset=!varLeafBusy
                          OnTimerEnd → Set(varLeafBusy, false)   // removes the overlay
```

**Navigation never depends on the timer** — `Navigate(…, ScreenTransition.Cover/UnCover)` already
runs in the button, so the leaf‑wipe is a flourish on top of a reliable built‑in transition. If
timers are unreliable in your Power BI visual, set `imgLeafWipe.Visible = false` and you still get
the Cover/UnCover transition. To use **your own leaf PNG** instead of the vector leaves, swap the
two `<path>` leaf shapes in `imgLeafWipe.Image.powerfx` for an `<image href='data:image/png;base64,…'/>`
(send me the file and I'll embed the exact base64).

### 8.5 Animations — entrance + the "exit" question

Every portal SVG has an **entrance** animation in the shared `varSvgCss` language: ribbon & cards
**fade‑up** (staggered), opp rows **slide in**, the detail card **fades up** with its tiles, the
pipeline bars **grow**. Because each Image re‑renders when its data changes, **switching opportunity
replays the detail's entrance**, and clearing the selection **replays the pipeline's entrance**.

> PowerApps has **no per‑control "exit" animation** (you can't animate a control while
> `Visible` flips to false — it just disappears). The design covers this two ways: the
> **leaf‑wipe** is the real exit/enter for the *page* change, and within the page the right‑panel
> swap is instant with the *incoming* visual animating in. That's the closest faithful equivalent
> to the requested entrance/exit feel that the platform allows.

| | |
|---|---|
| Crew Portal button · Back button (SVG) | ![portal button](previews/portal-button.png) ![back button](previews/portal-back-button.png) |
| Portal ribbon | ![portal ribbon](previews/portal-ribbon.png) |
| Crew roster cards (viewer larger) | ![portal cards](previews/portal-cards.png) |
| Opp row (selected) · Opp detail | ![opp row](previews/portal-opp-row.png) ![opp detail](previews/portal-opp-detail.png) |
| Pipeline overview · Leaf‑wipe (mid‑sweep) | ![pipeline](previews/portal-pipeline.png) ![leaf](previews/leaf-transition.png) |

---

## 9. Regenerate / verify (optional)

```bash
pip install cairosvg openpyxl
python3 _generate_previews.py    # writes svg/ + previews/ (dashboard + portal + transition)
python3 _verify_powerfx_svg.py   # XML-validates the SVGs + structural-checks the .powerfx
```
