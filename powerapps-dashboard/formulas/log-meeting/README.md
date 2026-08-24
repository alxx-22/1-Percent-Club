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

### Columns (verified against the list)

`1 Percent Approvals` has: **HPE Opportunity ID** (capital ID) · **Account Name** ·
**Approval Type** · **Requestor Name** · **Notes** · **Opportunity Name** · **Approver** ·
**Approval Status**.

The screen writes five of them:

| Column | Written from |
|---|---|
| `Account Name` | the Account box |
| `HPE Opportunity ID` | the Opportunity box (blank if none) |
| `Approval Type` | the dropdown — **this is what the measures score on** |
| `Requestor Name` | the logger's dashboard name — **this is what the measures join on** |
| `Approver` | the logger's `L1 Manager Email` |

Left alone deliberately:

- **`Approval Status`** — *not written at all*. The Pending measure tests `= BLANK()`, and an
  empty string is not blank in DAX, so writing `""` would drop the row out of **both** measures.
  Leaving it unset keeps it genuinely null = pending until the manager sets `"Approve"`.
- **`Notes`** and **`Opportunity Name`** — nothing on the screen captures these yet. Say the word
  and they become two more inputs.
- `Created Date` does not exist as a column; SharePoint stamps `Created` itself, and the measures
  have no date gate.

If **`Approver`** turns out to be a *Person* column rather than text, swap that one line for the
expanded-user record — the snippet is in the comment block at the top of `btnMeetSave.OnSelect`.
