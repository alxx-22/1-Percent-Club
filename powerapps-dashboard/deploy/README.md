# Percy — build runbook (START HERE)

This is the **index + build order** for standing up Percy (the Copilot Studio agent + its two
flows). Follow the phases **top to bottom** — the order matters:

- The agent can only add **`Percy-Query`** as an action **after that flow exists**, so build the
  flow **before** the agent.
- The **`Percy-Orchestrator`** flow calls the **published** agent, so build it **after** the agent.

```
Phase 1            Phase 2          Phase 3              Phase 4             Phase 5         Phase 6
SharePoint  ──►  Power BI    ──►  Build the 2 action ─►  Create the     ──►  Build         ──►  Test
list (have it)   prereqs          (diagnostic flow)     Percy agent         Percy-Orchestrator
                                                        (adds the flow      (calls the
                                                         as its action)      published agent)
```

> Power Apps chat UI is **already built** and **unchanged** ([`../PERCY.md`](../PERCY.md)) — it isn't
> a phase here. It already creates a **new row per send**, which is exactly what the create-only
> trigger needs. The full step detail lives in [`DEPLOY.md`](DEPLOY.md); this page is the map + order.

---

## Build order (do these in sequence)

### Phase 1 — SharePoint list *(prerequisite)*
Confirm `PercyConversations` exists with a single-line-text **`Status`** column (`ConversationJson`
in, `AnswerText` out). You already have it.
- 📄 [`../formulas/percy/backend/PERCY_BUILD_PACK.md` §2](../formulas/percy/backend/PERCY_BUILD_PACK.md#2-sharepoint-list-design) — columns + who writes what.
- 📄 [`sharepoint/Provision-PercyConversations.ps1`](sharepoint/Provision-PercyConversations.ps1) — *greenfield only* (skip if you have the list).

### Phase 2 — Power BI prerequisites
Note the **workspace id** + **semantic model (dataset) id**, and confirm the **signed-in shared
account** the flow will use has workspace read + dataset **Build**.
- 📄 [`PERCY_BUILD_PACK.md` §1.1](../formulas/percy/backend/PERCY_BUILD_PACK.md#1-recommended-architecture), [§10](../formulas/percy/backend/PERCY_BUILD_PACK.md#10-dax-templates) — connection model + DAX library.

### Phase 3 — Build the two agent-action flows *(build these FIRST, so they exist to attach)*
- **`Percy-Query`** — Copilot trigger (`template`,`ope`,`who`) → `Switch(template)` pastes the
  approved DAX → Power BI "Run a query against a dataset" → return `firstTableRows`. **Template key,
  never DAX.**
- **`Percy-Refresh`** — Copilot trigger (no inputs) → Power BI "Refresh a dataset" → status back.
- 📄 [`flows/Percy-Query.build.md`](flows/Percy-Query.build.md) · [`flows/Percy-Refresh.build.md`](flows/Percy-Refresh.build.md) — **the click-by-click builds**.
- 📄 [`flows/dax-templates.md`](flows/dax-templates.md) — which template key → which DAX → what to insert.
- 📄 [`PERCY_BUILD_PACK.md` §7](../formulas/percy/backend/PERCY_BUILD_PACK.md#7-the-single-diagnostic-action--percy-query) — action specs (Query §7.1–7.4, Refresh §7.5).

### Phase 4 — Create the Percy agent *(Copilot Studio)*  — do these **in this sub-order**
1. **Paste the Overview → Instructions** — one self-contained block, nine rules already inlined.
   - 📄 [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md) — the FINAL paste block (+ "what's left" checklist).
   - 📄 [`PERCY_BUILD_PACK.md` §9](../formulas/percy/backend/PERCY_BUILD_PACK.md#9-programme-rules-canonical) — canonical rules copy (update both together if rules change).
2. **Add the two actions:** "Run Percy Diagnostic" = `Percy-Query` (inputs `template`/`ope`/`who`) and
   "Refresh Dashboard" = `Percy-Refresh` (no inputs).
   - 📄 [`PERCY_BUILD_PACK.md` §15.2](../formulas/percy/backend/PERCY_BUILD_PACK.md#152-the-two-actions--their-descriptions-for-copilot-studio-orchestration) — the action descriptions to give them.
3. **Add the topics** (or rely on generative orchestration).
   - 📄 [`copilot-studio/topics.md`](copilot-studio/topics.md) — topics + the action.
   - 📄 [`PERCY_BUILD_PACK.md` §6](../formulas/percy/backend/PERCY_BUILD_PACK.md#6-percy-topic-design) — topic design + routing map.
4. **Settings + publish:** generative orchestration **on**, web/general knowledge **off**; **Publish**.

### Phase 5 — Build `Percy-Orchestrator` *(build this LAST)*
SharePoint ***item created*** (new row per send → no loop guard) → read `ConversationJson` →
**run the published Percy agent** (Phase 4) → write `AnswerText` + `Status="Answered"` → error
branch. **No Power Apps changes** — the app already creates a new row per send.
- 📄 [`flows/Percy-Orchestrator.build.md`](flows/Percy-Orchestrator.build.md) — **the click-by-click build**.
- 📄 [`PERCY_BUILD_PACK.md` §4](../formulas/percy/backend/PERCY_BUILD_PACK.md#4-main-power-automate-flow-percy-orchestrator) — flow design; [§3](../formulas/percy/backend/PERCY_BUILD_PACK.md#3-power-apps-behaviour) — the Power Apps write contract.

### Phase 6 — Test
Run the smoke test, then the full matrix.
- 📄 [`DEPLOY.md` § Smoke test](DEPLOY.md#smoke-test) — quick end-to-end.
- 📄 [`PERCY_BUILD_PACK.md` §13](../formulas/percy/backend/PERCY_BUILD_PACK.md#13-testing-plan) — the 32-case matrix.

---

## Document map — every file, its role, and when you use it

| # | Document | What it is | Used in |
|---|---|---|---|
| — | [`PERCY_BUILD_PACK.md`](../formulas/percy/backend/PERCY_BUILD_PACK.md) | **The full design & reference** (architecture, instructions, topics, the one action, DAX library, TMDL analysis, tests). Read for the "why"; the docs below are the "how". | all phases |
| — | [`DEPLOY.md`](DEPLOY.md) | The detailed **order-of-operations** + reliability tiers + smoke test. Same order as this page, with more step detail. | all phases |
| 1 | [`PERCY_BUILD_PACK.md` §2](../formulas/percy/backend/PERCY_BUILD_PACK.md#2-sharepoint-list-design) · [`sharepoint/Provision-PercyConversations.ps1`](sharepoint/Provision-PercyConversations.ps1) | SharePoint list design; greenfield provisioning script. | Phase 1 |
| 3 | [`flows/Percy-Query.build.md`](flows/Percy-Query.build.md) | Build the **diagnostic action** (Switch over template keys). | Phase 3 |
| 3 | [`flows/Percy-Refresh.build.md`](flows/Percy-Refresh.build.md) | Build the **Refresh Dashboard action** (Power BI refresh). | Phase 3 |
| 3 | [`flows/dax-templates.md`](flows/dax-templates.md) | template key → DAX → insert (canonical DAX is build pack §10). | Phase 3 |
| 4 | [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md) | The agent **Overview → Instructions** to paste. | Phase 4.1 |
| 4 | [`copilot-studio/topics.md`](copilot-studio/topics.md) | **Topics** + the two actions to add. | Phase 4.3 |
| 5 | [`flows/Percy-Orchestrator.build.md`](flows/Percy-Orchestrator.build.md) | Build the **orchestrator flow** that runs the agent. | Phase 5 |
| — | [`flows/README.md`](flows/README.md) | Overview of the **three flows** + connections. | Phase 3 & 5 |
| — | [`../PERCY.md`](../PERCY.md) | The **Power Apps chat UI** build (already built; unchanged). | reference |
| — | [`../formulas/percy/backend/README.md`](../formulas/percy/backend/README.md) | The no-premium SharePoint-trigger pattern (Stage 1) + Stage-2 pointer. | reference |
| — | [`../README.md`](../README.md) | The dashboard repo overview (Percy lives within it). | reference |

**TL;DR order:** SharePoint (have it) → Power BI prereqs → **build `Percy-Query`** → **create the
agent** (instructions → action → topics → publish) → **build `Percy-Orchestrator`** → test.
