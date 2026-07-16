# Percy diagnostic flows — build by hand (8 small flows, one per check)

Each diagnostic is its own Power Automate flow with its own embedded DAX — no template key, no
Switch. The Percy agent calls each flow as a separate tool. DAX per flow:
[`dax-templates.md`](dax-templates.md). Registering the flows as tools:
[`../copilot-studio/topics.md`](../copilot-studio/topics.md).

**Connections:** Microsoft Copilot Studio (trigger/response), Power BI (signed-in shared account
with workspace read + dataset **Build**).

## The flow registry

| Flow | Inputs (ALL optional) | DAX | Returns |
|---|---|---|---|
| `Percy-Summary` | `who` | dax-templates §1 | totals + pending per category (1 row) |
| `Percy-Locate` | `ope` | §2 | which schemes the deal appears in (1 row) |
| `Percy-CompleteCare` | `ope`, `who` | §3 | New Logo / Uplift evidence + credits-to-you (1 row) |
| `Percy-IBExpand` | `ope`, `who` | §4 | pro-rata expand evidence + CC suppression (1 row) |
| `Percy-CAP` | `ope`, `who` | §5 | order (email credit) + request (name credit) evidence (1 row) |
| `Percy-Meetings` | `ope`, `who` | §6 | one row per meeting on the deal |
| `Percy-IPGreenLake` | `who` | §7 | monthly % + tier points (1 row) |
| `Percy-Accreditation` | `who` | §8 | eligibility + status + points (1 row) |

*(`Percy-Refresh` is separate and unchanged — [`Percy-Refresh.build.md`](Percy-Refresh.build.md).)*

## Non-negotiable input rules

The `Run_an_agent` BadRequest ("The agent requested human input… specify HITL users") fires when
the agent **suspends mid-run waiting for input** — a flow-invoked agent has nobody to wait on.
Exactly three things can suspend it, and this design eliminates all three:

1. **A required input the fill-model didn't confidently fill** — the platform *forces* a collection
   step; no description or instruction can override it. This is why the old design kept failing:
   `ope`/`who` were optional, but the `template` key **had to stay required**, and it was the input
   the model fumbled. Fix here is structural: **the template input no longer exists**, and **every
   remaining input (`ope`/`who`) is optional** on every trigger (**⋯ → Make the field optional**).
   There is no field left anywhere that the platform is ever obliged to collect.
2. **A connection consent card** ("Connect to continue") — fixed per tool registration:
   *Credentials to use* = **Maker-provided credentials** (set it on every registration; it does not
   carry over).
3. **Question/input nodes inside topics** — keep none in the diagnostic path.

A question as the agent's **final text reply is NOT a suspension** — it flows through the
orchestrator into `AnswerText` like any answer, and the user replies on the next send. That is why
the blank-`ope` guard works: per-deal flows return `{"error":"missing_ope"}` instead of querying,
and the agent asks for the deal number **as its reply** (post-call, final-text — the safe kind),
never as a pre-call input request.

## Build pattern — per-deal flows (CompleteCare, IBExpand, CAP, Meetings, Locate)

1. **Create → Automated cloud flow → Skip**; trigger **Microsoft Copilot Studio → When an agent
   calls the flow**. Name it from the registry.
2. **Trigger inputs:** + Add an input → Text → name it exactly `ope` (and `who` where the registry
   says so). **⋯ → Make the field optional** on every input.
3. **Guard:** **Control → Condition** — `ope` (dynamic content) **is equal to** *(leave the value
   box empty)*.
   - **If yes** (blank): **Respond to the agent** → output Text `evidence` =
     `{"error":"missing_ope"}`.
   - **If no:** steps 4–6 go here.
4. **Compose `Dax`:** paste the flow's query from [`dax-templates.md`](dax-templates.md) as plain
   text; insert the `ope` / `who` dynamic-content chips between the quotes on the `VAR` lines.
5. **Power BI → Run a query against a dataset:** Workspace + Dataset = the 1% Club semantic model;
   **Query text** = Outputs of `Dax`.
6. **Respond to the agent:** output Text `evidence` =
   `string(outputs('Run_a_query_against_a_dataset')?['body/firstTableRows'])`.
7. **Save.**

## Build pattern — user-level flows (Summary, IPGreenLake, Accreditation)

Same as above with one input `who` (optional) and the guard on `who`:
blank → `{"error":"missing_who"}` (production always supplies it — the orchestrator embeds
CallerEmail — so this only fires in bare test-pane runs).

## After any flow change

Editing a trigger input (name, optional flag, add/remove) changes the tool schema. The tool in
Copilot Studio holds the old schema until you **remove and re-add it** (re-paste its Description and
input Customize texts — they get wiped), then **Publish** the agent. Symptoms of a stale schema:
"Destination agent was updated", "Output binding not found", inputs typed `unknown`.

## Security

- Each flow runs exactly one fixed, approved query — the agent supplies only `ope`/`who` values,
  never query text. There is no endpoint that runs agent-supplied DAX.
- Return only the projected columns — never raw rows or entity ids.
- Connection: least-privilege signed-in shared account.
