# Percy flows — build by hand (no import)

This environment can't import flows, so these are **click-by-click build instructions**, not
importable artifacts. There are **three flows** — one orchestrator + two agent actions.

| File | What it is |
|---|---|
| [`Percy-Orchestrator.build.md`](Percy-Orchestrator.build.md) | The SharePoint-triggered flow: reads `ConversationJson` off the item, runs Percy, writes `AnswerText` + `Status="Answered"`. |
| [`Percy-Query.build.md`](Percy-Query.build.md) | Agent action **"Run Percy Diagnostic"** (read-only): agent passes a **template key** + `ope`/`who`; a `Switch` picks the approved DAX, runs it via Power BI, returns the evidence. |
| [`Percy-Refresh.build.md`](Percy-Refresh.build.md) | Agent action **"Refresh Dashboard"**: no inputs → Power BI "Refresh a dataset" → status back. |
| [`dax-templates.md`](dax-templates.md) | Which template key maps to which DAX, the insert, and the Power BI output. |

## What's reliable

- ✅ **DAX bodies** (`dax-templates.md`, one query per Switch case, 2026-07 model): paste-ready. How
  the agent reads each evidence shape → build pack §7.3.
- ✅ **Build steps**: every action, field, and expression is spelled out.
- ⚠️ **One connector name varies by tenant:** the **Copilot Studio agent** action used in the
  orchestrator (run-the-agent step) — pick whatever "run a prompt / call the agent" action your
  tenant exposes.

## Why one diagnostic flow (not eight, not agent-supplied DAX)

The agent passes a **template key**, so the **DAX stays server-side and approved**: Percy never
generates DAX (your hard rule), and there's no "run any DAX" endpoint to prompt-inject or exfiltrate
the model through. One flow to build/maintain. (Build pack §1.2 / §7.)

## Order
1. Build **`Percy-Query`** (`Percy-Query.build.md`) and **`Percy-Refresh`** (`Percy-Refresh.build.md`)
   so both exist to add as agent actions.
2. Configure the **Percy agent** in Copilot Studio (`../copilot-studio/`), adding the two actions —
   **"Run Percy Diagnostic"** (`Percy-Query`) and **"Refresh Dashboard"** (`Percy-Refresh`).
3. Build **`Percy-Orchestrator`** (`Percy-Orchestrator.build.md`) and point its agent step at the
   published Percy agent.

## Connections (no premium service principal)

| Connector | Used by | Account |
|---|---|---|
| SharePoint | orchestrator | signed-in/shared account with access to the site |
| Power BI | `Percy-Query` (read), `Percy-Refresh` (refresh) | **signed-in shared account** with workspace read + dataset **Build** + **refresh** |
| Microsoft Copilot Studio | `Percy-Query` / `Percy-Refresh` trigger+response; orchestrator agent call | the agent's environment |
