# Points HQ — the points-breakdown page

A gated admin/sponsor page: **points by crew**, then **tap a crew** for its
**per-member breakdown**. One new screen (`scrPoints`), one new button on the
dashboard ribbon. Same 1136-wide canvas, HPE design language, animated
data-URI SVGs, and environment quirks (no `GroupBy`/string column names,
`ForAll … As`, every divisor `Max(…,1)`-guarded) as the rest of the app.

## Who can see it

`imgPointsHubBtn.Visible` (**the admin email list lives in that one file —
edit it there**):

- anyone on the hardcoded admin list (lowercase emails), **or**
- anyone whose email appears in the data's `Manager Sponsor Email` column
  (checked against `colMembers` directly, NOT via `varRole` — a sponsor who is
  also a member would otherwise lose access).

## Interaction model

```
Dashboard ── Points HQ btn ──▶ scrPoints
                               ├─ [All crews | Crew detail]  segmented toggle
                               ├─ 6 category chips = legend + FILTER
                               │    tap: isolate that category everywhere
                               │    (bars, live re-rank, numbers, tiles)
                               │    tap again: back to stacked
                               ├─ CREWS view: ranked stacked bars, tap → drill
                               └─ DETAIL view: crew hero + 6 tiles + member bars
```

Rank badges re-rank **live** with the category filter; top 3 wear
gold/silver/bronze. The viewer's own member row tints green ("· you").

## Build order

### 1. Dashboard screen (2 minutes)
| Control | Type | Geometry | Formulas |
|---|---|---|---|
| `imgPointsHubBtn` | Image | X=570 Y=11 W=140 H=30, Fit | `Image` ← `imgPointsHubBtn.Image.powerfx` · `OnSelect` ← `imgPointsHubBtn.OnSelect.powerfx` · `Visible` ← `imgPointsHubBtn.Visible.powerfx` **(edit the emails!)** |

### 2. New screen `scrPoints`
Screen `Fill = RGBA(247,247,247,1)`. `OnVisible` ← `Screen_Points_OnVisible.powerfx`.

Copy from the Crew Portal screen: **`imgLeafWipe`** (same Image formula) and
**`tmrLeaf`** (Duration 1100, Start=`varLeafBusy`, Reset=`!varLeafBusy`,
OnTimerEnd=`Set(varLeafBusy,false)`) so the leaf transition plays here too.

| Control | Type | Geometry | Key properties |
|---|---|---|---|
| `imgHubRibbon` | Image | 0, 0, 1136×52 | `Image` ← `imgHubRibbon.Image.powerfx` |
| `imgHubBack` | Image | 16, 11, 132×30 | `Image` + `OnSelect` ← `imgHubBack.powerfx` |
| `imgHubTabCrews` | Image | 16, 68, 150×34 | `Image` + `OnSelect` ← `imgHubTabCrews.powerfx` |
| `imgHubTabDetail` | Image | 166, 68, 170×34 | `Image` + `OnSelect` ← `imgHubTabDetail.powerfx` |
| `galHubLegend` | **Horizontal** gallery | 352, 68, 768×34 | `Items = colHubCats` · TemplateSize 126 · pad 0 · `OnSelect` ← `galHubLegend.OnSelect.powerfx`; template holds Image `imgHubChip` (W=`Parent.TemplateWidth-6`) ← `imgHubChip.Image.powerfx` |
| `imgHubListHead` | Image | 16, 110, 1104×26 | `Image` ← `imgHubListHead.Image.powerfx` · `Visible = varHubView = "crews"` |
| `galHubCrews` | Vertical gallery | 16, 140, 1104×484 | TemplateSize 48 · pad 0 · `Visible = varHubView = "crews"` · `Items` + `OnSelect` ← `galHubCrews.OnSelect.powerfx`; template holds Image `imgHubCrewRow` ← `imgHubCrewRow.Image.powerfx` |
| `imgHubSummary` | Image | 16, 110, 1104×178 | `Image` ← `imgHubSummary.Image.powerfx` · `Visible = varHubView = "detail"` |
| `galHubMembers` | Vertical gallery | 16, 296, 1104×328 | TemplateSize 50 · pad 0 · `Visible = varHubView = "detail"` · `Items` in `imgHubMemberRow.Image.powerfx` header; template holds Image `imgHubMemberRow` |

Gallery template Images: X=0 Y=0, W=`Parent.TemplateWidth`, H=`Parent.TemplateHeight`, `ImagePosition=Fit`.

## Data dependencies

Everything derives from the dashboard build (`colMembers`, `colCrew`,
`colCrewBreak`, `varSvgCss`, `varRibbonChip`, `varMyInitials`) — the page is
only reachable via the dashboard button, so they always exist. Categories and
colours are the SAME entities as `imgMyPoints` (palette validated: all six
colour checks pass on white):

| Key | Label | Colour | Source columns |
|---|---|---|---|
| `newcc` | New CC Logo / IB Upsell | `#0070f8` | IB&NS + New CC Logo |
| `capeng` | CAP Engagement | `#04909d` | Cap Requests |
| `capord` | CAP Orders Booked | `#009a71` | Cap Won |
| `cc` | Customer Centricity | `#7764fc` | Customer Centricity |
| `accred` | Accreditation Race | `#cc54a4` | Manager Sponsor |
| `ip` | IP Push | `#d25f4b` | IP in GL |

## Previews

Static mocks with sample data: `../../svg/points-hub-crews.svg`,
`../../svg/points-hub-detail.svg`, `../../svg/points-hub-button.svg`.
