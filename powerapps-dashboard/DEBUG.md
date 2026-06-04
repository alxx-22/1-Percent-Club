# Debug: dashboard shows but is blank (0 people / 0 crews)

> **Most common cause & fix (confirmed):** if `lblDebug` shows `rows = 86` (data is there)
> but `colMembers = 0` **and `varRole` is blank**, the build simply **never ran** — Timer
> controls don't fire reliably in the Power BI visual. **Move the entire build into
> `Screen.OnVisible`** ([`formulas/Screen_OnVisible.powerfx`](formulas/Screen_OnVisible.powerfx))
> and set `App.OnStart` = `Set(varReady,false)`. `OnVisible` runs on every screen show (and on a
> button that navigates here), so it always populates. Remove/ignore the `tmrLoad` timer.
> The labels below confirm it (after the fix: `colMembers` and `varRole` are populated).


Add **two Labels** to the dashboard screen and read them in Power BI. They tell us
exactly where the pipeline stalls. Both: `Wrap = true`, `AutoHeight = true`, on top.

### Label 1 — counts → `lblDebug`
`Text` = contents of [`formulas/lblDebug.Text.powerfx`](formulas/lblDebug.Text.powerfx)
(`Color = Red`, `X=16 Y=70 Width=700`). Shows:

```
rows in PowerBIIntegration.Data = ?
colMembers = ?   colCrew = ?
colMyCrew = ?    colCrewBreak = ?
varReady = ?     varRole = ?
varMyCrew = ?    varDispName = ?
viewer User().Email = ?
```

### Label 2 — real columns → `lblDebugSchema`  ← the important one
`Text` = contents of [`formulas/lblDebugSchema.Text.powerfx`](formulas/lblDebugSchema.Text.powerfx)
(`X=16 Y=180 Width=700`). It dumps the first data row as JSON, so you see the
**exact column names Power BI is sending**.

---

## Read it like this

| `rows` | `colMembers` | Meaning → fix |
|---:|---:|---|
| **0** | 0 | **No data reaching the visual.** In Power BI, select the PowerApps visual and drag the fields into its **data well** (Name, Crew, User Email, Manager Sponsor Email, Manager Sponsor, and every points column). Until `rows > 0` nothing can render. Label 2 will show `{}` / blank. |
| **> 0** | **0** | **Data is there but the build failed — almost always a column‑name mismatch.** Compare Label 2's JSON names to the EXPECTED list below. Power BI often renames fields (e.g. `Sum of IB & NS Points`, `IB and NS Points`, `Crew.Name`). Fix by renaming the field in the visual to match, *or* editing the name in the formulas. |
| > 0 | > 0 | Build worked. If visuals still look empty, the **Image controls** aren't on the latest formulas, or `imgMyPoints.Visible` / `imgSpectator.Visible` rules are wrong, or you're a *spectator* (email not found) so the left shows the scroll, not My Points. Check `varRole`. |

### EXPECTED column names (must match Label 2 exactly)
```
Name · Crew · User Email · L1 Manager Email · Manager Sponsor Email · Manager Sponsor ·
Cap Won Points Pending · Cap Requests Pending · IB & NS Points · Manager Sponsor Points ·
New CC Logo Points · Cap Won Points · Cap Requests · Customer Centricity Points Pending ·
Customer Centricity Points · IP in GL points
```

## Most likely answer
Because re‑navigating to the screen **no longer** helps, this is very likely the
**`rows = 0`** case (fields not on the visual) or a **column‑name mismatch** — not timing.
Label 2 settles it in one look. Tell me what `rows =` shows and paste the JSON from Label 2,
and I'll wire the formulas to your exact column names.

Delete both labels once it works.
