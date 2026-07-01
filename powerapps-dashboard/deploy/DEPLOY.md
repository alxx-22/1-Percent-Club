# Percy — deployment kit

> **New here? Start with [`README.md`](README.md)** — the build runbook: the exact creation **order**
> (build `Percy-Query` → create the agent → build `Percy-Orchestrator`) and a map of every doc and
> what it does. This page is the detailed order-of-operations behind that runbook.

Runnable artifacts for the Percy build pack
([`../formulas/percy/backend/PERCY_BUILD_PACK.md`](../formulas/percy/backend/PERCY_BUILD_PACK.md)).
Honest reliability tiers up front, then the order of operations.

## What actually imports (reliability tiers)

> **Your live schema (Shape A):** `PercyConversations` already exists. The app already writes the
> whole transcript to **`ConversationJson`** + `Status="Pending"` as a **new row per send** (`imgSend`
> patches `Defaults(PercyConversations)`); the flow (trigger: *item created*) writes **`AnswerText`**
> + `Status="Answered"`. **No Power Apps change** — new-row-per-send is exactly what lets the flow
> trigger on *item created* only. The provisioning script below is **greenfield-only (Shape B)** —
> skip it; at most confirm a single-line-text **`Status`** column exists.

| Tier | Piece | Artifact | Notes |
|---|---|---|---|
| ✅ **Already done / run-and-done** | SharePoint `PercyConversations` list | (you have it) — [`sharepoint/Provision-PercyConversations.ps1`](sharepoint/Provision-PercyConversations.ps1) is greenfield-only | Idempotent if you ever rebuild. For your build: just confirm `Status` exists. |
| ✅ **Paste-and-use** | Percy instructions + DAX | [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md), [`flows/dax-templates.md`](flows/dax-templates.md) → build pack §10 | Correct, ready to paste. |
| 🛠️ **Build by hand (no import)** | Power Automate flows (×3) | [`flows/Percy-Orchestrator.build.md`](flows/Percy-Orchestrator.build.md), [`flows/Percy-Query.build.md`](flows/Percy-Query.build.md), [`flows/Percy-Refresh.build.md`](flows/Percy-Refresh.build.md) | Click-by-click designer steps: the orchestrator + two agent actions (`Percy-Query` diagnostic, `Percy-Refresh`). This environment can't import flows. |
| ❌ **Configure by hand** | Copilot Studio agent · Power Apps canvas app | [`copilot-studio/`](copilot-studio/) (paste-in) | No reliable hand-import. The app stays the copy-paste `.powerfx` in [`../formulas/percy/`](../formulas/percy/). |

There is **no single "import everything" button** without a Dataverse managed-solution (the
premium/service-principal path you've ruled out), and this environment can't import flows — so the
flows are **built by hand from the instructions**, and the rest is paste-ready.

## Order of operations

> ⚠️ **Before you start — environment governance (DLP/ACP).** The **SharePoint**, **Power BI**, and
> **Copilot Studio agent** (`agentnode`) connectors must all be in the **same DLP data group** for
> your environment, or flows that combine them are blocked. Symptom when the agent connector is
> disallowed: adding the "Run a prompt / call an agent" action fails with **status 442 — "Request
> blocked due to data loss prevention (DLP) or advanced connector policies (ACP)"**. Fix = a Power
> Platform admin allows the Copilot Studio connector in that environment's data policy (Admin Center →
> **Policies → Data policies**). See [`flows/Percy-Orchestrator.build.md`](flows/Percy-Orchestrator.build.md).

1. **SharePoint** — you already have `PercyConversations` with `ConversationJson` + `AnswerText`.
   **Just confirm a single-line-text `Status` column exists** (values `Pending` / `Answered`).
   *(Skip the provisioning script — it builds the alternative Shape-B layout for a greenfield app.)*

2. **Power BI** — confirm the signed-in/shared account that the flows will use has **workspace read
   + dataset Build**. Note the **workspace id** and **dataset id**. Confirm whether the model stores
   the OPE with or without the `OPE-` prefix (sets the normalisation in the tool flows).

3. **Agent-action flows** — build by hand:
   - **`Percy-Query`** ([`flows/Percy-Query.build.md`](flows/Percy-Query.build.md)): Copilot trigger
     (`template`,`ope`,`who`) → **`Switch(template)`** pastes the matching DAX from
     [`flows/dax-templates.md`](flows/dax-templates.md) → Power BI "Run a query against a dataset" →
     return `firstTableRows`. The agent passes a **template key, never DAX**.
   - **`Percy-Refresh`** ([`flows/Percy-Refresh.build.md`](flows/Percy-Refresh.build.md)): no inputs →
     Power BI "Refresh a dataset" → status back. One refresh per request.

4. **Copilot Studio agent (Percy)** — paste [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md)
   (append the §9 rules), add the two actions — "Run Percy Diagnostic" (`Percy-Query`) and "Refresh Dashboard" (`Percy-Refresh`), add topics from
   [`copilot-studio/topics.md`](copilot-studio/topics.md), generative orchestration on, web/general
   knowledge off. Publish.

5. **Orchestrator flow** — build `Percy-Orchestrator` by hand following [`flows/Percy-Orchestrator.build.md`](flows/Percy-Orchestrator.build.md):
   SharePoint ***item created*** (no loop guard — new row per send) → read **`ConversationJson`** off
   the trigger → **run the published Percy agent** (replace the placeholder action) → write plain-text
   **`AnswerText`** + **`Status=Answered`** → error branch (friendly `AnswerText` + `Status=Answered`).
   **No conversation rebuild — the transcript is already on the item.**

6. **Power Apps** — unchanged. The chat UI already exists ([`../PERCY.md`](../PERCY.md)):
   `imgSend.OnSelect` already creates a **new row per send** (`Patch(Defaults(...))`) with
   `ConversationJson`+`Status="Pending"`; `tmrPercyPoll` reads `AnswerText` (by `ID`) when
   `Status="Answered"` (build pack §3). **No formula change** — see
   [`../formulas/percy/imgSend.OnSelect.powerfx`](../formulas/percy/imgSend.OnSelect.powerfx).

## Smoke test

1. In the app, ask **"How do I get points?"** → plain-text list of the nine ways (no tool call).
2. Ask **"Check Complete Care for OPE-…"** with a real OPE → row is `Pending` → flow runs the Complete
   Care tool → `AnswerText` populates, `Status=Answered`, bubble appears within a poll cycle.
3. Ask **"my CAP request for OPE-… isn't showing"** → CAP tool returns existence/approval/name-match;
   Percy explains the real blocker in plain English.
4. Confirm **no** JSON/DAX/IDs ever appear in `AnswerText`.

Full test matrix: build pack §13. Build checklist: build pack §14.
