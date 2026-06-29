# Percy flows — build by hand (no import)

This environment can't import flows, so these are **click-by-click build instructions**, not
importable artifacts.

| File | What it is |
|---|---|
| [`Percy-Orchestrator.build.md`](Percy-Orchestrator.build.md) | Build the SharePoint-triggered flow that reads `ConversationJson` off the item, runs Percy, and writes `AnswerText` + `Status="Answered"`. |
| [`Percy-Tools.build.md`](Percy-Tools.build.md) | Build one diagnostic tool flow, then clone it for the other 7 (only the input + DAX + projection change). |
| [`dax-templates.md`](dax-templates.md) | Which tool uses which DAX template, the parameter injection, and the Power BI action output. |

## What's reliable

- ✅ **DAX bodies** (`dax-templates.md` → build pack §10): correct, paste-ready.
- ✅ **Build steps**: every action, field, and expression is spelled out — follow them in the designer.
- ⚠️ **One connector name varies by tenant:** the **Copilot Studio agent** action used in the
  orchestrator (step 4) — pick whatever "run a prompt / call the agent" action your tenant exposes;
  the rest of the flow is unaffected.

## Order
1. Build the **8 tool flows** first (`Percy-Tools.build.md`) so they exist to add as agent actions.
2. Configure the **Percy agent** in Copilot Studio (`../copilot-studio/`), adding those flows as actions.
3. Build the **`Percy-Orchestrator`** (`Percy-Orchestrator.build.md`) and point its agent step at the
   published Percy agent.

## Connections (no premium service principal)

| Connector | Used by | Account |
|---|---|---|
| SharePoint | orchestrator | signed-in/shared account with access to the site |
| Power BI | every tool flow | **signed-in shared account** with workspace read + dataset **Build** |
| Microsoft Copilot Studio | tool flow trigger/response; orchestrator agent call | the agent's environment |
