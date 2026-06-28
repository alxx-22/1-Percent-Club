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

Connector: **Power BI** (`shared_pbi`), action **Run a query against a dataset** (REST shape below).

- **Workspace** = your workspace id (the one holding the 1% Club semantic model).
- **Dataset** = the semantic model id.
- **Query text** = `@{outputs('Compose_DaxQuery')}` (the injected DAX).

The action posts the standard `executeQueries` body:

```json
{
  "queries": [ { "query": "<the DAX from Compose_DaxQuery>" } ],
  "serializerSettings": { "includeNulls": true }
}
```

Response shape (what the flow parses, then returns to Percy — never echoed raw to the user):

```json
{ "results": [ { "tables": [ { "rows": [ { "[OPE]": "OPE-123456789", "[Found]": "Yes", "...": "..." } ] } ] } ] }
```

The flow projects `results[0].tables[0].rows[0]` (or the `rows` array for the narrow Customer
Centricity table) into the compact JSON in the tool's output schema (build pack §7), then returns it
via **"Return value(s) to Power Virtual Agents / Copilot"**.

> **Connection:** the Power BI connection uses the **signed-in shared account** (no service
> principal). That account needs workspace read + **Build** permission on the dataset.
