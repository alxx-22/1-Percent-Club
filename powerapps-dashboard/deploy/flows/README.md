# Percy flows — build by hand (no import)

This environment can't import flows, so these are **click-by-click build instructions**, not
importable artifacts. There are **two flows total**.

| File | What it is |
|---|---|
| [`Percy-Orchestrator.build.md`](Percy-Orchestrator.build.md) | The SharePoint-triggered flow: reads `ConversationJson` off the item, runs Percy, writes `AnswerText` + `Status="Answered"`. |
| [`Percy-Query.build.md`](Percy-Query.build.md) | The **one** diagnostic flow: agent passes a **template key** + `ope`/`who`; a `Switch` picks the approved DAX, runs it via Power BI, returns the evidence. |
| [`dax-templates.md`](dax-templates.md) | Which template key maps to which DAX, the insert, and the Power BI output. |

## What's reliable

- ✅ **DAX bodies** (`dax-templates.md` → build pack §10): correct, paste-ready.
- ✅ **Build steps**: every action, field, and expression is spelled out.
- ⚠️ **One connector name varies by tenant:** the **Copilot Studio agent** action used in the
  orchestrator (run-the-agent step) — pick whatever "run a prompt / call the agent" action your
  tenant exposes.

## Why one diagnostic flow (not eight, not agent-supplied DAX)

The agent passes a **template key**, so the **DAX stays server-side and approved**: Percy never
generates DAX (your hard rule), and there's no "run any DAX" endpoint to prompt-inject or exfiltrate
the model through. One flow to build/maintain. (Build pack §1.2 / §7.)

## Order
1. Build **`Percy-Query`** (`Percy-Query.build.md`) so it exists to add as the agent action.
2. Configure the **Percy agent** in Copilot Studio (`../copilot-studio/`), adding `Percy-Query` as
   the single action **"Run Percy Diagnostic"**.
3. Build **`Percy-Orchestrator`** (`Percy-Orchestrator.build.md`) and point its agent step at the
   published Percy agent.

## Connections (no premium service principal)

| Connector | Used by | Account |
|---|---|---|
| SharePoint | orchestrator | signed-in/shared account with access to the site |
| Power BI | `Percy-Query` | **signed-in shared account** with workspace read + dataset **Build** |
| Microsoft Copilot Studio | `Percy-Query` trigger/response; orchestrator agent call | the agent's environment |
