# Percy — deployment kit

Importable / runnable artifacts for the Percy build pack
([`../formulas/percy/backend/PERCY_BUILD_PACK.md`](../formulas/percy/backend/PERCY_BUILD_PACK.md)).
Honest reliability tiers up front, then the order of operations.

## What actually imports (reliability tiers)

| Tier | Piece | Artifact | Notes |
|---|---|---|---|
| ✅ **Run-and-done** | SharePoint `PercyConversations` list | [`sharepoint/Provision-PercyConversations.ps1`](sharepoint/Provision-PercyConversations.ps1) (PnP) or [`sharepoint/percyconversations.sitescript.json`](sharepoint/percyconversations.sitescript.json) | Creates every column/type/index. Idempotent. |
| ✅ **Paste-and-use** | Percy instructions + DAX | [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md), [`flows/dax-templates.md`](flows/dax-templates.md) → build pack §10 | Correct, ready to paste. |
| ⚠️ **Scaffold, verify on import** | Power Automate flows | [`flows/Percy-Orchestrator.flow.json`](flows/Percy-Orchestrator.flow.json), [`flows/Percy-Tool-template.flow.json`](flows/Percy-Tool-template.flow.json) | Logic correct; connector ids/connections need verifying. Build-from-designer recommended — see [`flows/README.md`](flows/README.md). |
| ❌ **Configure by hand** | Copilot Studio agent · Power Apps canvas app | [`copilot-studio/`](copilot-studio/) (paste-in) | No reliable hand-import. The app stays the copy-paste `.powerfx` in [`../formulas/percy/`](../formulas/percy/). |

There is **no single "import everything" button** without a Dataverse managed-solution (the
premium/service-principal path you've ruled out). This kit automates the parts that can be, and makes
the rest paste-ready.

## Order of operations

1. **SharePoint** — run the PnP script (or apply the site script):
   ```powershell
   Install-Module PnP.PowerShell -Scope CurrentUser
   # one-time app reg if you don't have a ClientId:
   #   Register-PnPEntraIDApp -ApplicationName "PnP-Percy" -Tenant <tenant>.onmicrosoft.com -Interactive
   ./sharepoint/Provision-PercyConversations.ps1 `
       -SiteUrl "https://hpe-my.sharepoint.com/personal/alex_cohen_hpe_com" `
       -ClientId "<your-app-client-id>"
   ```
   Then add `PercyConversations` as a data source in Power Apps and **Refresh**.

2. **Power BI** — confirm the signed-in/shared account that the flows will use has **workspace read
   + dataset Build**. Note the **workspace id** and **dataset id**. Confirm whether the model stores
   the OPE with or without the `OPE-` prefix (sets the normalisation in the tool flows).

3. **Tool flows** (×8) — build each from [`flows/Percy-Tool-template.flow.json`](flows/Percy-Tool-template.flow.json),
   pasting the matching DAX from [`flows/dax-templates.md`](flows/dax-templates.md). Validate input →
   Power BI "Run a query against a dataset" → return JSON.

4. **Copilot Studio agent (Percy)** — paste [`copilot-studio/percy-instructions.md`](copilot-studio/percy-instructions.md)
   (append the §9 rules), add the 8 tool flows as actions, add topics from
   [`copilot-studio/topics.md`](copilot-studio/topics.md), generative orchestration on, web/general
   knowledge off. Publish.

5. **Orchestrator flow** — build `Percy-Orchestrator` from [`flows/Percy-Orchestrator.flow.json`](flows/Percy-Orchestrator.flow.json):
   SharePoint *item created* → guard `Role=user` → `Status=Processing` → get/compose conversation
   JSON → **run the published Percy agent** (replace the placeholder action) → write plain-text
   `Reply` + `Status=Complete` → error branch.

6. **Power Apps** — the chat UI already exists ([`../PERCY.md`](../PERCY.md)). Confirm `imgSend.OnSelect`
   writes a row per user turn and `tmrPercyPoll` reads `Reply`/`Status` (build pack §3).

## Smoke test

1. In the app, ask **"How do I get points?"** → plain-text list of the nine ways (no tool call).
2. Ask **"Check Complete Care for OPE-…"** with a real OPE → row goes `Processing` → flow runs the
   Complete Care tool → `Reply` populates, `Status=Complete`, bubble appears within a poll cycle.
3. Ask **"my CAP request for OPE-… isn't showing"** → CAP tool returns existence/approval/name-match;
   Percy explains the real blocker in plain English.
4. Confirm **no** JSON/DAX/IDs ever appear in `Reply`.

Full test matrix: build pack §13. Build checklist: build pack §14.
