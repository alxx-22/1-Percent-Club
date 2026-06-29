# Build the Percy tool flows by hand (Power Automate)

Click-by-click build for the **diagnostic tool flows** — **no import**. All 8 are the same shape;
build one, then clone and change three things (input, DAX, single-row vs array). Each is called **by
the Percy agent** in Copilot Studio, runs an **approved DAX template** against the semantic model via
the **Power BI** connector (signed-in shared account — no service principal), and returns compact
JSON the agent explains in plain English.

**Connections used:** Microsoft Copilot Studio (the trigger/response), Power BI.

---

## Part A — build one tool flow (worked example: `Percy-Tool-CompleteCare`)

### 1. Create the flow
- Power Automate → **Create → Automated cloud flow** → **Skip** (pick the trigger manually).
- Add trigger: **Microsoft Copilot Studio** → **When Copilot Studio calls a flow** (formerly
  "When Power Virtual Agents calls a flow").
- Name: `Percy-Tool-CompleteCare`.

### 2. Trigger inputs
- On the trigger, **+ Add an input → Text**, name it **`ope`**.
- *(CAP and Customer Centricity tools only: add a second Text input **`who`** for the caller email.)*

### 3. Validate the input
> **Do the strict OPE regex in Copilot Studio (Power Fx), not here.** In the topic, before calling
> the action, gate with `IsMatch(OPE, "^OPE-?\d{6,12}$")` and only call the tool with a clean value.
> Logic-Apps expressions have no regex, so the flow just does a non-empty guard.

Add **Control → Condition**:
- Left: from **Dynamic content**, pick the **`ope`** input (don't hand-type `triggerBody()`); operator
  **is not equal to**; right value: leave **blank**.

Everything below goes in **If yes**. In **If no**, add the response from step 7 returning
`{"error":"invalid_ope"}`.

### 4. (skip a Compose — build the DAX in the Power BI action itself)

> ⚠️ **Do NOT use an `fx replace('…@@OPE@@…')` expression.** Building DAX inside an expression string
> means doubling every single quote (`''Final''`) and hand-typing the input reference — that's what
> throws **"invalid parameters"**. Paste the DAX as **plain text** instead and drop the OPE in as
> **dynamic content**. No expression, no escaping.

### 5. Run the query (Power BI) — paste the DAX as plain text
Add **Power BI → Run a query against a dataset**.
- **Workspace:** 🔎 the workspace holding the 1% Club semantic model.
- **Dataset:** the semantic model.
- **Query text:** click the field and **paste the matching DAX template** from
  [`dax-templates.md`](dax-templates.md) (here **Template B**, build pack §10.2) **as plain text**.
  On the **`VAR Ope = "…"`** line, **clear whatever is between the quotes** and, with the cursor
  there, insert the **`ope`** input from **Dynamic content**. Done — no `replace`, no quote-doubling.
  - *(DAX `=` on text is case-insensitive, so you don't need to upper-case the OPE.)*
  - **Two-input tools** (CAP, Customer Centricity): do the same on the **`VAR Who = "…"`** line with
    the **`who`** input.

> Prefer a separate Compose? You still can — add **Compose `DaxQuery`**, but **type the DAX as plain
> text** in its input and insert the `ope` dynamic content between the `VAR Ope = ""` quotes (don't
> open the `fx` editor). Then set **Query text** = `Outputs` of `DaxQuery`. Same result, no escaping.

This action returns **`firstTableRows`** — an array of row objects with keys like `[OPE]`, `[Found]`,
`[CCPointsTotal]`, … (the column names from the DAX, in square brackets).

### 6. Project the evidence
Add **Data Operation → Compose**, name it `Evidence`:
- **Single-row tools** (all except Customer Centricity): Inputs = `first(outputs('Run_a_query_against_a_dataset')?['body/firstTableRows'])`
- **Customer Centricity** (returns several meeting rows): Inputs = `outputs('Run_a_query_against_a_dataset')?['body/firstTableRows']` (the whole array).

### 7. Return to Copilot Studio
Add **Microsoft Copilot Studio → Respond to Copilot Studio** (a.k.a. "Return value(s)…").
- **+ Add an output → Text**, name it **`evidence`**.
- Value: `string(outputs('Evidence'))`.
- In the **If no** branch, add the same response action with `evidence` = `{"error":"invalid_ope"}`.

Save. (You'll wire this flow into the Percy agent as an **action** in Copilot Studio — see
`../copilot-studio/topics.md`.)

---

## Part B — clone for the other 7 tools

**Save As** the flow above, rename, and change only: the **input(s)**, the **DAX template**, and the
**projection** (single row vs array). Everything else is identical.

| Flow name | Trigger input(s) | DAX template (paste from `dax-templates.md` / build pack §10) | Project (step 6) |
|---|---|---|---|
| `Percy-Tool-Locate`             | `ope`        | A | single row |
| `Percy-Tool-CompleteCare`       | `ope`        | B | single row |
| `Percy-Tool-CAP`                | `ope`, `who` | E | single row |
| `Percy-Tool-IBExpand`           | `ope`        | H | single row |
| `Percy-Tool-CustomerCentricity` | `ope`, `who` | F | **whole array** |
| `Percy-Tool-IPGreenLake`        | `who`        | I | single row |
| `Percy-Tool-Accreditation`      | `who`        | J | single row |
| `Percy-Tool-Summary`            | `who`        | G | single row |

For each clone: paste that tool's DAX as plain text into the Power BI **Query** field, then insert
the **`ope`** and/or **`who`** dynamic content between the empty `VAR Ope = ""` / `VAR Who = ""`
quotes (same plain-text method as Part A — no `replace`, no escaping). The `who`-only tools (IP,
Accreditation, Summary) have just a `VAR Who = ""` and a non-empty guard on `who`.

---

## Security recap (per tool)
- **OPE regex** (`^OPE-?\d{6,12}$`) and **email = caller/admin** are enforced in **Copilot Studio**
  before the action is called; the flow keeps a non-empty guard as a backstop. This keeps the
  validated value as the only thing substituted into the fixed DAX (injection-safe).
- The Power BI connection is the **signed-in shared account** with workspace read + dataset **Build**.
- Return **only** the projected fields (build pack §7 output schemas) — never raw rows or entity IDs.

Build pack cross-ref: §7 (tool specs), §10 (DAX), §15.2 (tool descriptions for the agent).
