# Build `Percy-Query` by hand (Power Automate)

Click-by-click build for the **single** diagnostic flow — **no import**. The Percy agent calls it
with an approved **template key** + `ope`/`who` (**never DAX**); the flow `Switch`es to the matching
fixed DAX (§10 / [`dax-templates.md`](dax-templates.md)), runs it via Power BI, and returns the
evidence. One flow covers every diagnostic.

**Connections:** Microsoft Copilot Studio (trigger/response), Power BI. No premium service principal.

> **Why one flow + a key (not 8 flows, not agent-supplied DAX):** the DAX stays **server-side and
> approved**, so Percy never generates DAX and there's no "run any DAX" endpoint to misuse — and you
> build/maintain one flow instead of eight. See build pack §1.2 / §7.

---

## 1. Create the flow
- **Create → Automated cloud flow → Skip** (pick the trigger manually).
- Trigger: **Microsoft Copilot Studio → When Copilot Studio calls a flow** (formerly "When Power
  Virtual Agents calls a flow").
- Name: `Percy-Query`.

## 2. Trigger inputs (three Text inputs)
On the trigger, **+ Add an input → Text** three times:
- **`template`** — the diagnostic key (Locate, CompleteCare, CAP, IBExpand, CustomerCentricity, IPGreenLake, Accreditation, Summary).
- **`ope`** — the OPE number (blank for the user-level templates).
- **`who`** — the user's email (blank for ope-only templates).

## 3. (validation lives in Copilot Studio)
> The strict OPE regex (`^OPE-?\d{6,12}$`) and "email = caller/admin" run in **Copilot Studio**
> (Power Fx `IsMatch`) **before** this flow is called. No flow-side regex needed.

## 4. Switch on the template → set the DAX
Add **Control → Switch**. Set **On** = the **`template`** input (Dynamic content).

For **each case** (`Locate`, `CompleteCare`, `CAP`, `IBExpand`, `CustomerCentricity`, `IPGreenLake`,
`Accreditation`, `Summary`):
1. Add **Data Operation → Compose** named e.g. `Dax_CompleteCare`.
2. In its **Inputs**, **paste that template's DAX as plain text** from [`dax-templates.md`](dax-templates.md)
   (→ build pack §10). On the `VAR Ope = "…"` line, **clear what's between the quotes** and insert the
   **`ope`** input from **Dynamic content**. For the **owner/name templates** (`CompleteCare`,
   `IBExpand`, `CAP`, `CustomerCentricity`), also clear the `VAR Who = "…"` quotes and insert the
   **`who`** input.
   - *(Plain text + dynamic content — **no** `fx replace()`, no quote-doubling. DAX `=` on text is
     case-insensitive, so no upper-casing needed.)*

In the Switch's **Default**, respond with the error in step 7 (no DAX runs).

> **Collect the result with one Compose:** after the Switch, add **Compose `DaxQuery`** =
> `coalesce(outputs('Dax_Locate'), outputs('Dax_CompleteCare'), outputs('Dax_CAP'), outputs('Dax_IBExpand'), outputs('Dax_CustomerCentricity'), outputs('Dax_IPGreenLake'), outputs('Dax_Accreditation'), outputs('Dax_Summary'))`
> — only the matched case ran, so `coalesce` returns that case's DAX.

## 5. Run the query (Power BI) — once, after the Switch
Add **Power BI → Run a query against a dataset**.
- **Workspace / Dataset:** the 1% Club workspace + semantic model.
- **Query text:** the **Outputs** of `DaxQuery`.
- Returns **`firstTableRows`** — an array of row objects keyed by the DAX column names in `[...]`.

## 6. Project the evidence
Add **Compose `Evidence`** = `outputs('Run_a_query_against_a_dataset')?['body/firstTableRows']`
(the whole array — 1 row for single-row templates, several for `CustomerCentricity`). The agent
reads the array; no need to special-case here.

## 7. Return to Copilot Studio
Add **Microsoft Copilot Studio → Respond to Copilot Studio**.
- **+ Add an output → Text**, name **`evidence`**, value `string(outputs('Evidence'))`.
- In the Switch **Default** path (unknown template), respond with `evidence` = `{"error":"unknown_template"}`.

Save. Add this one flow to the Percy agent as the action **"Run Percy Diagnostic"** (see
[`../copilot-studio/topics.md`](../copilot-studio/topics.md)).

---

## Flow at a glance
```
When Copilot Studio calls the flow   (inputs: template, ope, who)
├─ Switch(template)
│   ├─ Locate              → Compose Dax_Locate              (Template A, insert ope)
│   ├─ CompleteCare        → Compose Dax_CompleteCare        (Template B, insert ope + who)
│   ├─ CAP                 → Compose Dax_CAP                 (Template E, insert ope + who)
│   ├─ IBExpand            → Compose Dax_IBExpand            (Template H, insert ope + who)
│   ├─ CustomerCentricity  → Compose Dax_CustomerCentricity  (Template F, insert ope + who)
│   ├─ IPGreenLake         → Compose Dax_IPGreenLake         (Template I, insert who)
│   ├─ Accreditation       → Compose Dax_Accreditation       (Template J, insert who)
│   ├─ Summary             → Compose Dax_Summary             (Template G, insert who)
│   └─ Default             → Respond {"error":"unknown_template"}   ⟵ no arbitrary DAX ever runs
├─ Compose DaxQuery   = coalesce(all the case Composes)
├─ Power BI: Run a query against a dataset (DaxQuery)   ⟵ ONE action
├─ Compose Evidence   = firstTableRows
└─ Respond to Copilot Studio: evidence = string(Evidence)   ⟵ ONE response
```

## Template registry (which DAX each key runs)
| `template` | DAX (§10 / dax-templates.md) | Insert | Returns |
|---|---|---|---|
| `Locate` | A | ope | counts per scheme |
| `CompleteCare` | B | ope + who | CC evidence + credits-to-you (1 row) |
| `CAP` | E | ope + who | CAP evidence (1 row) |
| `IBExpand` | H | ope + who | IB evidence + credits-to-you (1 row) |
| `CustomerCentricity` | F | ope + who | one row per meeting |
| `IPGreenLake` | I | who | tier (1 row) |
| `Accreditation` | J | who | eligibility (1 row) |
| `Summary` | G | who | totals (1 row) |

## Security recap
- **Approved keys only:** an unknown `template` hits Default → error. The agent passes a **key, not a
  query**, so there's no endpoint that runs agent-supplied DAX (the core guardrail).
- **Validation** (OPE regex / email = caller-or-admin) in Copilot Studio before the call.
- **Connection:** signed-in shared account with workspace read + dataset **Build**.
- Return only the projected columns (build pack §7) — never raw rows or entity IDs.

Build pack cross-ref: §7 (action spec), §10 (DAX), §15.2 (action description for the agent).
