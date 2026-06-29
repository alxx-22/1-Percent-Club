# DAX bodies for the Percy tool flows

The **canonical, commented DAX** for every tool lives in
[`../../formulas/percy/backend/PERCY_BUILD_PACK.md` §10](../../formulas/percy/backend/PERCY_BUILD_PACK.md#10-dax-templates).
This file is the **deployment mapping**: which flow uses which template, what parameter it injects,
and the exact Power BI action payload. Keep §10 as the single source of truth — copy each query from
there into the matching flow.

## Tool flow → template → input

| Tool flow | Build-pack template | Input param(s) injected | Returns |
|---|---|---|---|
| `Percy-Tool-Locate`            | A | `Ope` | existence across schemes |
| `Percy-Tool-CompleteCare`      | B | `Ope` | New Logo / Uplift evidence |
| `Percy-Tool-CAP`               | E | `Ope`, `Who` | engagement + order + name-match |
| `Percy-Tool-IBExpand`          | H | `Ope` | renewal+expand + CC-suppression |
| `Percy-Tool-CustomerCentricity`| F | `Ope`, `Who` | per-meeting classification + name-match |
| `Percy-Tool-IPGreenLake`       | I | `Who` | monthly % tier |
| `Percy-Tool-Accreditation`     | J | `Who` | S-coded / CSM eligibility |
| `Percy-Tool-Summary`           | G | `Who` | all categories + pending |
| *(reference only)*             | C, D | `Ope` | current / expected CC points |

## Parameter injection (injection-safe)

The flow validates the input **before** building the query, then string-replaces the `VAR` line.
Validate first so a caller can't inject DAX:

- **OPE:** must match `^OPE-?\d{6,12}$` (case-insensitive). Reject otherwise → `{ "error": "invalid_ope" }`.
- **Email (`Who`):** must match the signed-in caller (or an allowed admin). If absent, inject `Who = ""`
  (the name-match flags then return `"No"`, by design).

In the flow, hold the template as a string with a placeholder and `replace()` it, e.g. for Template B:

```
Compose "DaxQuery" =
replace(
  'DEFINE VAR Ope = "@@OPE@@"  ... (paste Template B from §10.2) ...',
  '@@OPE@@',
  toUpper(trim(triggerBody()?['ope']))
)
```

Use a literal placeholder token (`@@OPE@@` / `@@WHO@@`) rather than concatenating, so the validated
value lands in exactly one spot.

## Power BI action — "Run a query against a dataset"

Connector: **Power BI**, action **Run a query against a dataset** (added in the designer — see
[`Percy-Tools.build.md`](Percy-Tools.build.md) step 5).

- **Workspace** = the workspace holding the 1% Club semantic model.
- **Dataset** = the semantic model.
- **Query text** = the **Outputs** of your `DaxQuery` Compose (the injected DAX).

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
