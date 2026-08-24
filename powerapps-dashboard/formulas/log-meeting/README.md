# Log a meeting (`scrLogMeeting`)

A **non‑S‑coded** crew member logs a customer meeting from the app instead of going into
SFDC. The row goes to the approvals SharePoint list, their **L1 manager** approves it, and
the Customer Centricity points land.

| File | What it is |
|---|---|
| [`scrLogMeeting.pa.yaml`](scrLogMeeting.pa.yaml) | The **whole screen**, copy‑paste ready. |
| [`Screen_LogMeeting_OnVisible.powerfx`](Screen_LogMeeting_OnVisible.powerfx) | `OnVisible` — meeting‑type table, logger identity, L1 approver, "what I've logged". |
| [`btnMeetSave.OnSelect.powerfx`](btnMeetSave.OnSelect.powerfx) | The write to SharePoint. |
| `imgLogMeetingBtn.*.powerfx` | The Crew Portal button (Image / OnSelect / Visible). |

## The scoring rule this screen is built around

Points come from the **`Customer Centricity Points`** / **`...Points Pending`** measures, which
now read the **`1 Percent Approvals`** list (see
[`Customer_Centricity_Points.dax`](Customer_Centricity_Points.dax)). They match on two fields:

| Dropdown option = `Approval Type` written | Points |
|---|---|
| `F2F Meeting` | **35** |
| `Leadership Meeting` | **20** |
| `Customer Meeting` | **10** |
| `Channel Partner Meeting` | **10** |

- **`Approval Type`** must match the SharePoint choice string **exactly** — the measures compare
  the literal text. The dropdown labels *are* those values, so there is no mapping layer to drift.
- **`Requestor Name`** is how points find a person; the screen writes the logger's dashboard name.
- **`Approval Status`**: blank = pending, `"Approve"` = scored. Written blank on save.
- There is **no date gate** in the new measures.

**`F2F Meeting` is the correct value** — it is exactly what the model's `Meeting Type` SWITCH
produces ([`Meeting_Type.dax`](Meeting_Type.dax)) and what the app writes. `"Face-to-Face Meeting"`,
which an earlier draft of the measures matched on, is produced by nothing and scored zero.

> **How `Meeting Type` really classifies** (it is not a prefix): `CONTAINSSTRING` on the Subject —
> the keyword can be **anywhere**, case does not matter, and the **first match wins** in the order
> **F2F > LEADERSHIP > CUSTOMER > CHANNEL**. So a Subject reading "CUSTOMER F2F review" is an
> **F2F Meeting (35)**, not a Customer Meeting (10). The four labels this screen writes each contain
> their own keyword, so they classify correctly down that path too.

> ⚠️ **Source switch.** These measures no longer read `'Customer Meetings'`. Only meetings present
> in `1 Percent Approvals` score. If meetings logged straight into SFDC are not mirrored into that
> list, they stop counting — worth checking before this goes live.

## Who can see it

The Crew Portal button's `Visible` is `'S Coded?' = "Non S-Coded (Phil)"`, read off the
signed‑in user's model row. **Log meeting** is additionally disabled unless
`varMeetIsEligible` is true, so the screen cannot be used even if reached directly.

## Setup

1. Add the approvals list via **Data ▸ Add data**. It is referenced as
   **`'1 Percent Approvals'`** — single‑quoted because the name contains spaces.
   Change it in `OnVisible`, `btnMeetSave.OnSelect` and `galMeetMine` if yours differs.
2. Add the portal button: paste `imgLogMeetingBtn` into `scrPortal`'s children
   (`X=370 Y=11 W=168 H=30`) and nudge to a free spot on the ribbon.
3. The Power BI visual's field well needs **`S Coded?`** and **`L1 Manager Email`**
   (`L1 Manager Email` is already in the expected column list in `../../DEBUG.md`).

### Column names — confirm these against your list

The Patch writes the fields below. They are the **best reconstruction** of the existing
customer‑meeting approval rows; every one is a single line in `btnMeetSave.OnSelect`, so
correcting a name or deleting an unused column is a one‑line edit:

```
Title · Account · HPE Opportunity Id · Subject · Approval Type
Requestor Name · Requestor Email · Approver · Approval Status · Created Date
```

- **`Approval Type`** and **`Requestor Name`** are the two that must be right — the measures
  match on them. Everything else is descriptive.
- `Subject` is written as the plain label for readability; delete the line if the column
  does not exist.
- If **`Approver`** is a *Person* column rather than text, swap it for the expanded‑user
  record — the exact snippet is in the comment block at the top of `btnMeetSave.OnSelect`.
- `Approval Status` is written blank on purpose = pending. The model treats `"Approve"`
  as approved and blank as pending.
