# Order Progress rail (`imgOrderAnchor`)

The yearly **order goal** on the dashboard's right-hand edge, drawn as an anchor on a chain.

| File | What it is |
|---|---|
| [`scrDashboard.pa.yaml`](scrDashboard.pa.yaml) | The **whole home screen**, copy-paste ready (squeezed layout + the rail). |
| [`imgOrderAnchor.Image.powerfx`](imgOrderAnchor.Image.powerfx) | Just the rail's `Image` formula. |
| [`Screen_Dashboard_OrderProgress.powerfx`](Screen_Dashboard_OrderProgress.powerfx) | The block appended to the end of `scrDashboard.OnVisible`. |

## The visual

The higher the anchor rides, the closer the crew is to the goal:

| Order Progress | Anchor | State |
|---|---|---|
| **100%** | hoisted to the deck, at the goal line | **GRAND PRIZE** (gold) |
| **50-99%** | part way up, arrow pointing up | **HOISTING** (green) |
| **under 50%** | dropped into the water, arrow pointing down | **DROPPING** (amber) — rewards reduce |

Anchor travel maps 0% → y=470 (in the water) and 100% → y=158 (at the deck), with the
chain running from the winch and a dotted line showing the travel still to go.

## The data

`Order Progress` arrives from the model as **one value repeated on every row**, so
`OnVisible` lifts it out with `Max(PowerBIIntegration.Data, 'Order Progress')`. It accepts
either a 0-1 fraction or a 0-100 percentage, and reads blank/error as 0 so the rail always
draws. Add `Order Progress` to the Power BI visual's field well or the rail shows 0%.

## Layout change

The rail sits at **X=984, Y=68, 136 x 556**. To make room, the right column was squeezed
(the left column is untouched):

| Control | Before | After |
|---|---|---|
| `Image6` (crew grid) | 668 x 300 | 516 x 232 |
| `Image7` (leaderboard header) | 668 x 28 @ y380 | 516 x 22 @ y312 |
| `Gallery1` (rest of crews) | 668 x 237 @ y400, template 27 | 516 x 296 @ y328, template 23 |
| `Image8` (row template) | 658 x 27 | 506 x 23 |

Every SVG's `viewBox` equals its control's W x H, so shrinking width scales the whole card
down proportionally — no reflow, no distortion. The taller gallery also shows ~4 more crews
than before.
