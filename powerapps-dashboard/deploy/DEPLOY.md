# Percy — deployment kit

Importable / runnable artifacts for the Percy build pack
([`../formulas/percy/backend/PERCY_BUILD_PACK.md`](../formulas/percy/backend/PERCY_BUILD_PACK.md)).
Honest reliability tiers up front, then the order of operations.

## What actually imports (reliability tiers)

> **Your live schema (Shape A):** `PercyConversations` already exists. The app writes the whole
> transcript to **`ConversationJson`** + `Status="Pending"`; the flow writes **`AnswerText`** +
> `Status="Answered"`. **No Power Apps changes.** The provisioning script below is **greenfield-only
> (Shape B)** — you can skip it; at most confirm a single-line-text **`Status`** column exists.

| Tier | Piece | Artifact | Notes |
|---|---|---|---|
| ✅ **Already done / run-and-done** | SharePoint `PercyConversations` list | (you have it) — [`sharepoint/Provision-PercyConversations.ps1`](sharepoint/Provision-PercyConversations.ps1) is greenfield-only | Idempotent if you ever rebuild. For your build: just confirm `Status` exists. |
| ✅ **Paste-and-use** | Percy instructions + DAX | [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md), [`flows/dax-templates.md`](flows/dax-templates.md) → build pack §10 | Correct, ready to paste. |
| 🛠️ **Build by hand (no import)** | Power Automate flows (×2) | [`flows/Percy-Orchestrator.build.md`](flows/Percy-Orchestrator.build.md), [`flows/Percy-Query.build.md`](flows/Percy-Query.build.md) | Click-by-click designer steps. Two flows total: the orchestrator + the one `Percy-Query` (Switch over template keys). This environment can't import flows. |
| ❌ **Configure by hand** | Copilot Studio agent · Power Apps canvas app | [`copilot-studio/`](copilot-studio/) (paste-in) | No reliable hand-import. The app stays the copy-paste `.powerfx` in [`../formulas/percy/`](../formulas/percy/). |

There is **no single "import everything" button** without a Dataverse managed-solution (the
premium/service-principal path you've ruled out), and this environment can't import flows — so the
flows are **built by hand from the instructions**, and the rest is paste-ready.

## Order of operations

1. **SharePoint** — you already have `PercyConversations` with `ConversationJson` + `AnswerText`.
   **Just confirm a single-line-text `Status` column exists** (values `Pending` / `Answered`).
   *(Skip the provisioning script — it builds the alternative Shape-B layout for a greenfield app.)*

2. **Power BI** — confirm the signed-in/shared account that the flows will use has **workspace read
   + dataset Build**. Note the **workspace id** and **dataset id**. Confirm whether the model stores
   the OPE with or without the `OPE-` prefix (sets the normalisation in the tool flows).

3. **`Percy-Query`** (one flow) — build by hand following [`flows/Percy-Query.build.md`](flows/Percy-Query.build.md):
   Copilot trigger (`template`,`ope`,`who`) → **`Switch(template)`** pastes the matching DAX from
   [`flows/dax-templates.md`](flows/dax-templates.md) → Power BI "Run a query against a dataset" →
   return `firstTableRows`. The agent passes a **template key, never DAX**.

4. **Copilot Studio agent (Percy)** — paste [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md)
   (append the §9 rules), add the one `Percy-Query` flow as the action "Run Percy Diagnostic", add topics from
   [`copilot-studio/topics.md`](copilot-studio/topics.md), generative orchestration on, web/general
   knowledge off. Publish.

5. **Orchestrator flow** — build `Percy-Orchestrator` by hand following [`flows/Percy-Orchestrator.build.md`](flows/Percy-Orchestrator.build.md):
   SharePoint *item created or modified* → guard `Status=Pending` & `AnswerText` empty → read
   **`ConversationJson`** off the trigger → **run the published Percy agent** (replace the placeholder
   action) → write plain-text **`AnswerText`** + **`Status=Answered`** → error branch (friendly
   `AnswerText` + `Status=Answered`). **No conversation rebuild — the transcript is already on the item.**

6. **Power Apps** — unchanged. The chat UI already exists ([`../PERCY.md`](../PERCY.md)):
   `imgSend.OnSelect` upserts the row with `ConversationJson`+`Status="Pending"`; `tmrPercyPoll` reads
   `AnswerText` when `Status="Answered"` (build pack §3). **Do not edit these formulas.**

## Smoke test

1. In the app, ask **"How do I get points?"** → plain-text list of the nine ways (no tool call).
2. Ask **"Check Complete Care for OPE-…"** with a real OPE → row is `Pending` → flow runs the Complete
   Care tool → `AnswerText` populates, `Status=Answered`, bubble appears within a poll cycle.
3. Ask **"my CAP request for OPE-… isn't showing"** → CAP tool returns existence/approval/name-match;
   Percy explains the real blocker in plain English.
4. Confirm **no** JSON/DAX/IDs ever appear in `AnswerText`.

Full test matrix: build pack §13. Build checklist: build pack §14.
