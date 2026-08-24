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

The model derives **`Meeting Type` from the Subject's leading word** — `CUSTOMER`,
`CHANNEL` or `LEADERSHIP`. Anything else leaves `Meeting Type` **blank and the meeting
earns nothing**. So the Subject written to SharePoint is always `"<KEYWORD> - <label>"`:

| Dropdown option | Written Subject | Meeting Type | Points |
|---|---|---|---|
| Leadership introduction | `LEADERSHIP - Leadership introduction` | Leadership Meeting | **20** |
| Customer meeting | `CUSTOMER - Customer meeting` | Customer Meeting | **10** |
| Face to face meeting | `CUSTOMER - Face to face meeting` | Customer Meeting | **10** |
| Channel partner meeting | `CHANNEL - Channel partner meeting` | Channel Partner Meeting | **10** |

> ⚠️ **"Face to face meeting" is mapped to `CUSTOMER` deliberately.** On its own the phrase
> starts with "FACE", which classifies as nothing and scores **0**. Treating it as a customer
> meeting (10) is the only reading that scores. If it should be its own thing, the model's
> `Meeting Type` rule has to change first — the app cannot fix that on its own.

The full criteria (mirrored in the on‑screen checklist): Subject prefix ✓, `Created Date`
≥ 1 May 2026 ✓, `Approval Status = "Approve"` ✓, and credit is **by name**
(`Requestor Name` / `Last Modified By: Full Name`) — never by email.

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
Title · Account · HPE Opportunity Id · Subject · Meeting Type
Requestor Name · Requestor Email · Approver · Approval Status · Created Date
```

- `Subject` is the one that **must** be written — it is what drives the scoring.
- `Meeting Type` is a calculated column **in the model**; if your SharePoint list has no
  such column, delete that line.
- If **`Approver`** is a *Person* column rather than text, swap it for the expanded‑user
  record — the exact snippet is in the comment block at the top of `btnMeetSave.OnSelect`.
- `Approval Status` is written blank on purpose = pending. The model treats `"Approve"`
  as approved and blank as pending.
