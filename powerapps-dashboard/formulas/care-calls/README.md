# Customer Care Calls (`scrCareCalls`)

A crew member picks one of their crew's recently‑**Won** opportunities and records the
**HPE Services Post‑Renewal Questionnaire** against it. Answers are written to the
SharePoint list, and answered/cleared opportunities drop off the list. Reached from a
Crew Portal button.

## Files

| File | What it is |
|---|---|
| [`scrCareCalls.pa.yaml`](scrCareCalls.pa.yaml) | The **whole screen**, copy‑paste ready. New screen ▸ blank, then paste this over it in the YAML/code view. |
| [`Screen_CareCalls_OnVisible.powerfx`](Screen_CareCalls_OnVisible.powerfx) | The `OnVisible` on its own — unpack, caller roster, alignment. |
| [`imgCareCallsBtn.Image.powerfx`](imgCareCallsBtn.Image.powerfx) | Crew Portal button image (green pill). |
| [`imgCareCallsBtn.OnSelect.powerfx`](imgCareCallsBtn.OnSelect.powerfx) | Navigates to `scrCareCalls`. |
| [`imgCareCallsBtn.Visible.powerfx`](imgCareCallsBtn.Visible.powerfx) | The access gate. **Currently a testing lock to `alex.cohen@hpe.com`**; the `'S Coded?' = "Non S-Coded (Phil)"` production gate is kept commented out inside. |

## Setup (required)

1. **Add the SharePoint list** `HPE_Services_Post_Renewal_Questionnaire` to the app
   (**Data ▸ Add data**). If your list is named differently, rename it in three places:
   `OnVisible`, `btnCareSave.OnSelect`, `btnCareNoContact.OnSelect`.
2. **Add to the Power BI field well**: `Care Call Pack` (the opp list) and `S Coded?`
   (the caller roster). Both are read off `PowerBIIntegration.Data`.

### Column‑type assumptions

The Patch uses the questionnaire's own column display names. Two things vary by how the
list was created — both are called out in comments inside `btnCareSave.OnSelect`:

- **Title** — if your list keeps a required built‑in `Title`, add `Title: varCareOpp.OppId,`.
- **`Open to a mapping session? (Yes/No)`** — if it is a **Choice** column rather than
  text, pass `{ Value: drpCareMap.Selected.Value }`.
- `Opportunity` is written as the **OPE id**, because it is the key the list is matched on.

## The survey

A **2‑step wizard** (`varCareStep`) so 11 inputs stay readable on a 640px canvas:

- **Step 1** — Contact Name, Contact Email, Q1–Q4.
- **Step 2** — Q5–Q7, *Open to a mapping session?*, Follow‑up Notes.

Account, Opportunity, Renewal Rep and Renewal Date come from the opportunity;
Response Date is stamped on save. All 16 questionnaire columns are written.

### Engage the rep first

Both the list header and every survey card carry a standing amber instruction:
**speak to the aligned sales rep first and ask them to organise the call — never
contact a customer cold.** The card names the rep for that opportunity.

### "Rep says do not contact"

If the rep judges that contacting the customer is a bad idea, that button clears the
opportunity off the list. It uses **existing fields only** — no new column:

- **`Follow-up Notes`** carries the reason
  (`DO NOT CONTACT - the aligned sales rep advised against contacting this customer.`,
  plus anything typed in the notes box), and
- **`Response Date`** stamps it as actioned.

The list hides any opportunity that already has a row in the SharePoint list, so a
cleared opp disappears exactly like an answered one.

## How opportunities are aligned to callers

`OnVisible` builds the roster of **Non S‑Coded (Phil)** people in the crew (the callers),
then deals work out:

- every opportunity belonging to the **same sales rep goes to the same caller**, so one
  caller builds one relationship with one rep, and
- reps are dealt **round‑robin** across the callers (both lists sorted, so the allocation
  is deterministic and stable), which keeps each caller's volume similar.

Balance is even across *reps*; if one rep owns far more opps than another, their caller
carries more. If that shows up in practice, the fix is to deal by opportunity count
rather than by rep.

If the signed‑in user is not on the caller roster (e.g. during testing), the screen shows
the **whole crew's** list instead of an empty one, and the header says so.

## Notes

- `colCareDone` is read with `ForAll(...)` over the list — non‑delegable, so it sees the
  first 500 rows (raise the app's data row limit if the list ever gets bigger).
- The packed `Update` field is free text; if a rep's update contains `//` or `||` that
  row's later fields shift. The Crew Portal unpack has the same characteristic.
- Navigation in/out is plain `Cover`/`UnCover`. The screen reuses `varMyCrew`,
  `varUserEmail`, `varSvgCss`, `varRibbonChip`, `varMyInitials` from the dashboard build.
