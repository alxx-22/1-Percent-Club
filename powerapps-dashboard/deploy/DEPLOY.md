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
   - **8 diagnostic flows, one per check** ([`flows/Percy-Query.build.md`](flows/Percy-Query.build.md)
     has the pattern + registry): agent trigger with **optional** `ope`/`who` → blank-ope guard
     returns `{"error":"missing_ope"}` → the flow's own fixed DAX from
     [`flows/dax-templates.md`](flows/dax-templates.md) → Power BI "Run a query against a dataset" →
     return `firstTableRows`. **No template input; no required inputs anywhere.**
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

## Tracing a failed ask (end-to-end debugging)

> **The app runs the PUBLISHED agent; the Copilot Studio test pane runs the DRAFT.** Any agent
> change (instructions, tools, topics) reaches the app **only after Publish**. Old behaviour in the
> app + correct behaviour in the pane = you haven't re-published.

When the app shows **"Sorry, I couldn't reach the assistant just now"**, that string comes from
exactly two places — the SharePoint row tells you which:

1. **Open `PercyConversations`, find the row** for the failing message.
   - `AnswerText` **contains the sorry text** → the **orchestrator's error branch** wrote it: the
     agent call (or a tool under it) FAILED. Go to step 2.
   - `AnswerText` **has a real answer** (arrived late) → the app's **poll timed out**
     (`varPollMax × 2s`, default 120s) before the answer landed. Diagnostics can exceed it on a cold
     run — raise `varPollMax` in `App.OnStart`.
   - **Still `Pending` with EMPTY `AnswerText`** → the flow **failed (or hung) without reaching the
     error branch** — the bubble was the app's local timeout text. Two things to check: the failed
     run in the run history (step 2), AND the error branch itself — its **Configure run after** must
     cover the agent-call action (+ Compose + happy-path Update item) with *has failed / has timed
     out*; if it's attached to the wrong action it never fires and rows strand as Pending. Cleanest:
     wrap the happy path in a **Scope** and run the error Update item after the Scope fails.
2. **`Percy-Orchestrator` → run history** → open the failed run → see which action failed. If it's
   the agent call, go deeper:
3. **Copilot Studio → Activity tab** shows the agent's tool calls for that conversation;
   **`Percy-Query` → run history** shows the flow run — which Switch branch ran and whether the
   Power BI action errored.
   - ⚠️ **First-use branch failures are common:** a Switch branch that has never executed (e.g. the
     first ever CompleteCare ask) will surface paste errors in that branch's DAX — and after any
     **trigger-input rename**, every `Dax_*` Compose's dynamic-content chips must be re-picked;
     un-fixed chips break exactly like this, per branch, on first use.
   - ⚠️ **`Run_an_agent` fails with BadRequest: "The agent requested human input, but no users were
     configured to handle the request. Please specify HITL users when invoking the agent."** The
     agent tried to stop and ask a human something mid-run — for a flow-invoked agent there is no
     human, so the whole run fails (and the row strands as Pending if the error branch misses it).
     The usual "human input" is the **"Connect to continue" tool-consent card**: per-user consent
     that you clicked in the test pane but the orchestrator's identity never has. Fix: on **each
     tool's page → Additional details**, set the tool's authentication to the
     **agent-author / maker-provided** option (no end-user consent) — every registration, then
     **Publish**. Fallback: consent once while signed in as the orchestrator's connection account.
     Keep "Allow human escalation" = No on the Run-an-agent action — the goal is an agent with
     nothing left to ask, not a human in the loop. (Mid-run input prompts for required tool inputs
     produce the same error — that's what optional inputs + pinned templates already removed.)
