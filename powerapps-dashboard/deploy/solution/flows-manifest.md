# Percy — flows manifest (for the solution build)

The 9 flows to build **inside the solution**. Step-by-step designer build is in
[`../flows/Percy-Orchestrator.build.md`](../flows/Percy-Orchestrator.build.md) and
[`../flows/Percy-Tools.build.md`](../flows/Percy-Tools.build.md); 🟩 DAX bodies are in
[`../flows/dax-templates.md`](../flows/dax-templates.md) → build pack §10.

> **Solution-specific changes vs the plain build:**
> - 🟦 Bind every connector to a **connection reference** (`percy_sp`, `percy_pbi`, `percy_copilot`) — not a direct connection.
> - 🟦 Use **environment variables** for ids/urls: `percy_WorkspaceId`, `percy_DatasetId`, `percy_SiteUrl`, `percy_ListName`.

## Orchestrator

| Flow | Trigger | Reads | Writes | Conn refs | Env vars |
|---|---|---|---|---|---|
| `Percy-Orchestrator` | SharePoint **item created or modified** | `ConversationJson` (off the item) | `AnswerText` + `Status="Answered"` | `percy_sp`, `percy_copilot` | `percy_SiteUrl`, `percy_ListName` |

🟩 Logic: guard `Status="Pending"` & empty `AnswerText` → run Percy agent → write `AnswerText`/`Answered`
→ error branch (friendly text, `Answered`). 🟦 The "run the agent" action is tenant-specific (pick it).

## Tool flows (8) — all share the shape: Copilot trigger → validate → Compose DAX → Power BI → respond

| Flow | 🟦 Input(s) | 🟩 DAX (§10) | 🟩 Project | Conn refs | Env vars |
|---|---|---|---|---|---|
| `Percy-Tool-Locate`             | `ope`        | A | single row | `percy_pbi`, `percy_copilot` | `percy_WorkspaceId`, `percy_DatasetId` |
| `Percy-Tool-CompleteCare`       | `ope`        | B | single row | `percy_pbi`, `percy_copilot` | ″ |
| `Percy-Tool-CAP`                | `ope`, `who` | E | single row | `percy_pbi`, `percy_copilot` | ″ |
| `Percy-Tool-IBExpand`           | `ope`        | H | single row | `percy_pbi`, `percy_copilot` | ″ |
| `Percy-Tool-CustomerCentricity` | `ope`, `who` | F | **whole array** | `percy_pbi`, `percy_copilot` | ″ |
| `Percy-Tool-IPGreenLake`        | `who`        | I | single row | `percy_pbi`, `percy_copilot` | ″ |
| `Percy-Tool-Accreditation`      | `who`        | J | single row | `percy_pbi`, `percy_copilot` | ″ |
| `Percy-Tool-Summary`            | `who`        | G | single row | `percy_pbi`, `percy_copilot` | ″ |

🟥 **Manual per tool flow:** paste the DAX body (with the `@@OPE@@`/`@@WHO@@` token), and in the
Power BI **Run a query against a dataset** action set Workspace = 🟦 `percy_WorkspaceId` env var,
Dataset = 🟦 `percy_DatasetId` env var.

> 🟨 **Validation reminder:** the strict OPE regex (`^OPE-?\d{6,12}$`) runs in **Copilot Studio
> (Power Fx `IsMatch`)** before the action is called; the flow keeps a non-empty backstop. Power
> Automate expressions have no regex.
