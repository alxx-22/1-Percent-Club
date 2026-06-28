# Percy flows — what's here and how to import

Two reference workflow definitions plus the DAX mapping. **Read the reliability note first** —
these are scaffolds to speed up a hand-build, not guaranteed one-click imports.

| File | What it is |
|---|---|
| `Percy-Orchestrator.flow.json` | The SharePoint-triggered flow that reads `ConversationJson` off the item, runs Percy, and writes `AnswerText` + `Status="Answered"` (matches the live Shape-A app). |
| `Percy-Tool-template.flow.json` | The shape **all 8 tool flows** share (Copilot calls it → Power BI query → return JSON). Example wired for Complete Care. |
| `dax-templates.md` | Which tool uses which DAX template + the injection + Power BI payload. |

## Reliability — be realistic

- ✅ **DAX bodies** (`dax-templates.md` → build pack §10): correct and directly usable. Paste into
  the Power BI action.
- ✅ **Flow *logic* / step order**: correct — mirrors build pack §4 and §7.
- ⚠️ **Connector `operationId`s and connection references**: I've used the known ids
  (`GetOnNewItems`, `PatchItem`, `GetItems`, `ExecuteQueries`, the Copilot Studio trigger/response),
  but these can differ by tenant/connector version. **Verify on import** — if a step shows "operation
  not found", re-add that one action from the designer and the rest stays intact.
- ❌ **The Copilot Studio agent call** in the orchestrator is a **placeholder HTTP action**. Replace
  it with the actual Copilot Studio agent action once your agent is published (there's no stable
  hand-authorable id for "run this agent").

## Recommended path: build from the designer (most reliable)

1. Create **`Percy-Orchestrator`** in Power Automate from scratch, following build pack §4, using
   `Percy-Orchestrator.flow.json` as the step-by-step blueprint (trigger *created or modified* →
   guard `Status=Pending` & `AnswerText` empty → read `ConversationJson` off the item → run agent →
   write `AnswerText` + `Status="Answered"` → error branch). No get-items/rebuild — the transcript is
   already on the triggering item.
2. Create **one tool flow per scheme** (`Percy-Tool-Locate`, `-CompleteCare`, `-CAP`, `-IBExpand`,
   `-CustomerCentricity`, `-IPGreenLake`, `-Accreditation`, `-Summary`) from
   `Percy-Tool-template.flow.json`: Copilot trigger (inputs `ope` [+ `who`]) → validate → Compose
   the DAX (paste the matching template from `dax-templates.md`) → **Power BI "Run a query against a
   dataset"** → project first row → **return to Copilot**.
3. Add each tool flow to the Percy agent as an **action** (build pack §14 / §15.2).

## Alternative: legacy import package (.zip)

If you'd rather import: wrap a definition in the legacy package layout and import via **Power
Automate → My flows → Import → Import Package (legacy)**:

```
<package>.zip
├── manifest.json                       # lists the flow resource + its connection dependencies
└── Microsoft.Flow/flows/<guid>/
    └── definition.json                 # { "name","id","type","properties": { "definition": <the WDL above>, "connectionReferences": {...} } }
```

On import you'll be asked to **select/create the connections** (SharePoint, Power BI, Copilot
Studio). The fragile bit is `manifest.json`'s connection-dependency block — if import errors,
build from the designer (above) instead. I can generate the full `.zip`s on request, but the
designer path is what I'd trust for a first deploy.

## Connections used (no premium service principal)

| Connector | Used by | Account |
|---|---|---|
| SharePoint (`shared_sharepointonline`) | orchestrator | signed-in/shared account with access to the site |
| Power BI (`shared_pbi`) | every tool flow | **signed-in shared account** with workspace read + dataset **Build** |
| Microsoft Copilot Studio | tool flow trigger/response; orchestrator agent call | the agent's environment |
