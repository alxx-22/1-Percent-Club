# DAX bodies for `Percy-Query`

The **canonical, commented DAX** for every template lives in
[`../../formulas/percy/backend/PERCY_BUILD_PACK.md` §10](../../formulas/percy/backend/PERCY_BUILD_PACK.md#10-dax-templates).
This file is the **deployment mapping**: which **template key** (the `Switch` case in the single
`Percy-Query` flow — see [`Percy-Query.build.md`](Percy-Query.build.md)) uses which DAX, what it
inserts, and the Power BI action output. Keep §10 as the single source of truth — copy each query
into the matching `Switch` case.

## template key → DAX → insert

| `template` (Switch case) | Build-pack DAX | Insert | Returns |
|---|---|---|---|
| `Locate`             | A | `ope` | existence across schemes |
| `CompleteCare`       | B | `ope`, `who` | New Logo / Uplift + credits-to-you |
| `CAP`                | E | `ope`, `who` | engagement + order + name-match |
| `IBExpand`           | H | `ope`, `who` | renewal+expand + CC-suppression + credits-to-you |
| `CustomerCentricity` | F | `ope`, `who` | per-meeting classification + name-match |
| `IPGreenLake`        | I | `who` | monthly % tier |
| `Accreditation`      | J | `who` | S-coded / CSM eligibility |
| `Summary`            | G | `who` | all categories + pending |
| *(reference only)*   | C, D | `ope` | current / expected CC points |

## Dropping the OPE / email into the DAX (the simple way)

> ⚠️ **Don't build the DAX inside an `fx replace('…@@OPE@@…')` expression.** That forces you to double
> every single quote (`''Final''`) and hand-type the input reference — it throws **"invalid
> parameters"**. Paste the DAX as **plain text** and insert the value as **dynamic content** instead.

Each template has a **`VAR Ope = "…"`** line (and `VAR Who = "…"` for the two-input tools). In the
Power BI **Run a query against a dataset** action:

1. Paste the template into **Query text** as plain text.
2. On the `VAR Ope = "…"` line, **clear what's between the quotes** and insert the **`ope`** input
   from **Dynamic content**. (Two-input tools: do the same on `VAR Who = "…"` with **`who`**.)

No `replace`, no escaping, no concatenation. Injection-safety comes from the **input validation**,
which runs **before** the action is called:

- **OPE:** validate `^OPE-?\d{6,12}$` in **Copilot Studio** (Power Fx `IsMatch`) before calling the
  tool; the flow keeps a non-empty backstop. (DAX `=` on text is case-insensitive, so no upper-casing
  is needed for matching.)
- **Email (`Who`):** must be the signed-in caller (or an allowed admin); if absent, leave `VAR Who = ""`
  and the name-match flags return `"No"` by design.

## Power BI action — "Run a query against a dataset"

Connector: **Power BI**, action **Run a query against a dataset** (added in the designer — see
[`Percy-Query.build.md`](Percy-Query.build.md) step 5).

> **Placement: ONE action, *after* the Switch — not one per branch.** Each Switch case holds only a
> `Compose Dax_<key>` (its DAX text). After the Switch, a single `Compose DaxQuery = coalesce(all the
> branch Composes)` picks whichever branch ran, and this **one** Power BI action reads it. Adding the
> query action inside every branch means maintaining it 8× — don't.

- **Workspace** = the workspace holding the 1% Club semantic model.
- **Dataset** = the semantic model.
- **Query text** = the **Outputs** of your `DaxQuery` Compose (the injected DAX).

> In the `coalesce`, reference each branch by its **internal** name — spaces become underscores
> (`Dax CC` → `outputs('Dax_CC')`). A blank/`null` `DaxQuery` (and a Power BI action stuck on
> **"Invalid parameters"**) is almost always a name mismatch here, or the Workspace/Dataset/Query
> fields not yet filled — not a wiring problem.

The connector returns **`firstTableRows`** — an array of row objects whose keys are the DAX column
names in square brackets:

```json
{ "firstTableRows": [ { "[OPE]": "OPE-123456789", "[Found]": "Yes", "[CCPointsTotal]": 0, "...": "..." } ] }
```

Project it (a Compose) then return it to the agent via **Respond to Copilot Studio**:
- single-row tools → `first(outputs('Run_a_query_against_a_dataset')?['body/firstTableRows'])`
- Customer Centricity (several meeting rows) → the whole `firstTableRows` array.

The agent reads this compact JSON and explains it in plain English — it's **never** echoed raw to the user.

> **Connection:** the Power BI connection uses the **signed-in shared account** (no service
> principal). That account needs workspace read + **Build** permission on the dataset.
