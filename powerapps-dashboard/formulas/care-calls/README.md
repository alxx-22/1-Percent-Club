# Customer Care Calls (`scrCareCalls`)

A new screen where a crew member picks one of their crew's recently‑**Won**
opportunities and fills in a short **care‑call survey**. Reached from a Crew
Portal button that only **Non S‑Coded (Phil)** users can see.

## Files

| File | What it is |
|---|---|
| [`scrCareCalls.pa.yaml`](scrCareCalls.pa.yaml) | The **whole screen**, copy‑paste ready. New screen ▸ blank, then paste this over it in the YAML/code view (it's a complete `Screens:` doc). |
| [`Screen_CareCalls_OnVisible.powerfx`](Screen_CareCalls_OnVisible.powerfx) | The `OnVisible` on its own — builds `colCareOpps` and resets to the list view. |
| [`imgCareCallsBtn.Image.powerfx`](imgCareCallsBtn.Image.powerfx) | Crew Portal button image (green pill). |
| [`imgCareCallsBtn.OnSelect.powerfx`](imgCareCallsBtn.OnSelect.powerfx) | Navigates to `scrCareCalls`. |
| [`imgCareCallsBtn.Visible.powerfx`](imgCareCallsBtn.Visible.powerfx) | The access gate (`'S Coded?' = "Non S-Coded (Phil)"`). |

Add the button by pasting `imgCareCallsBtn` into `scrPortal`'s children (an
`Image` at `X=160 Y=11 W=200 H=30`; nudge to a free spot on the ribbon), or
build an Image and paste the three `imgCareCallsBtn.*` formulas onto it.

## How the opp list is built

The list data lives in a per‑crew model column, **`Care Call Pack`** (rows
joined by `||`, fields by `//`), produced by the DAX measure of the same name:
`Status // OppId // OppName // Account // Fcst // Close(yyyy-mm-dd) // Val //
OwnerName // Update`.

`OnVisible` unpacks it with the **same proven pattern the Crew Portal uses** for
`Crew Funnel Pack` — take the crew's row out of `PowerBIIntegration.Data`, then
`Split("||")` → `Split("//")` → `Index(cols, n).Value` into `colCareOpps`.

```
crewLine = First(Filter(PowerBIIntegration.Data, Crew = varMyCrew))
pack     = crewLine.'Care Call Pack'
```

## Two views, one screen (`varCareOpp`)

- **List** (`IsBlank(varCareOpp)`): a gallery of the crew's Won opps (name,
  account, close date, value, owner, "Start survey ›"). Tapping one opens its
  survey. An empty‑state card shows when the crew has no wins in 30 days.
- **Survey** (`varCareOpp` is a record): 5 placeholder questions —
  Q1/Q2 typed (`Classic/TextInput`), Q3/Q4 dropdowns (`Classic/DropDown`),
  Q5 a **1–5 slider** (`Classic/Slider`) with a live value chip.
  **Save & close** currently just resets the inputs and returns to the list.

## Prerequisites / notes

1. **Add both columns to the Power BI field well.** The app reads everything
   from `PowerBIIntegration.Data`, so **`Care Call Pack`** *and* **`S Coded?`**
   must be added as fields to the Power BI visual that feeds the app — otherwise
   `crewLine.'Care Call Pack'` and the button's gate come back blank.
2. **Two control types are new to this app** (it otherwise uses only
   image/gallery/button/text): **`Classic/DropDown@2.3.1`** and
   **`Classic/Slider@1.0.31`**. If a paste flags a version on either, accept
   Studio's suggested version or re‑insert that one control from
   **Insert ▸ Input** — the surrounding formulas rebind unchanged.
3. **SharePoint write is a TODO.** `btnCareSave.OnSelect` closes the survey and
   returns to the list; the future `Patch(...)` to a `CareCallResponses` list is
   written as a commented block right where it belongs.
4. **Packed `Update` is free text.** If a rep's update ever contains `//` or
   `||`, that row's later fields shift — the Crew Portal unpack has the same
   characteristic, so if it's fine there it's fine here.

Navigation in/out is plain `Cover`/`UnCover` (no dependency on the leaf‑wipe
overlay). The screen reuses `varMyCrew`, `varUserEmail`, `varSvgCss`,
`varRibbonChip`, `varMyInitials`, all built by the dashboard before the portal.
