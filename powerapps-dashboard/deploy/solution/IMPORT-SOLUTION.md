# Percy — "Import a Solution" (Dataverse) — TEST branch

Goal: the end state where someone clicks **Solutions → Import solution**, uploads one **`.zip`**, and
gets Percy (agent + flows). This branch holds the **packable solution source** that becomes that zip.

> [!CAUTION]
> **Honest status — read this.** A fully hand-authored solution `.zip` (with a Copilot Studio agent
> inside) is **not** something that's guaranteed to import. The files here are a **structured
> scaffold** with **placeholder GUIDs** that you `pac solution pack` into a zip — expect to validate
> and iterate. The **guaranteed** one-click zip is produced by **building the components once in a
> Dataverse maker portal and clicking Export** (the platform writes correct GUIDs/agent components).
> Use this scaffold to accelerate that, not to skip it. The agent (bot) is **not** in this source —
> add it in the portal and re-export so it joins the bundle.

## 🎨 Colour key (manual entry)
🟥 <span style="color:#C00000">**MANUAL VALUE**</span> (type/paste) ·
🟦 <span style="color:#0070F8">**MANUAL ACTION**</span> (click/select) ·
🟩 <span style="color:#01A982">**PROVIDED**</span> (in this repo) ·
🟨 <span style="color:#D36D00">**LIMITATION / DECISION**</span>

## What's in `src/` (the pack folder)
```
src/
├── [Content_Types].xml                          🟩 package manifest
├── Other/Solution.xml                           🟩 solution + publisher + root components (🟥 prefix/GUIDs)
├── Other/Customizations.xml                     🟩 flows + connection refs + environment variables
└── Workflows/
    ├── Percy-Orchestrator-...101.json           🟩 orchestrator definition (Shape A)
    └── Percy-Tool-CompleteCare-...102.json      🟩 tool-flow pattern (replicate ×7 — flows-manifest.md)
```
🟨 Only the orchestrator + one tool are scaffolded; 🟦 replicate the `<Workflow>` block + a
`/Workflows/*.json` for the other 7 tools, and 🟦 add the **agent** in the portal (Step 3).

## Step 1 — Pack the source into a zip
🟩 Provided script (needs the Power Platform CLI):
```bash
cd powerapps-dashboard/deploy/solution
./pack-solution.sh                # → ./out/Percy1PctClub.zip
# or directly:
pac solution pack --zipfile ./out/Percy1PctClub.zip --folder ./src --packagetype Unmanaged
```
🟨 If `pac` reports schema errors, that's the scaffold needing a fix — diff a flow against one from a
**real exported** solution and align the `Customizations.xml` attributes.

## Step 2 — Import a Solution
1. 🟦 Target env → **Solutions → Import solution** → upload **`out/Percy1PctClub.zip`**.
2. 🟦 **Bind connection references**: `percy_sp` (SharePoint), `percy_pbi` (🟥 Power BI signed-in
   shared account, Build perm), `percy_copilot` (Copilot Studio).
3. 🟥 **Set environment variable Current Values**: `percy_WorkspaceId`, `percy_DatasetId`,
   `percy_SiteUrl` (`percy_ListName` defaults to `PercyConversations`).
4. 🟦 **Import** → then 🟦 turn the flows **On** and 🟦 **publish** the agent.

## Step 3 — Fold in the Copilot Studio agent (to get the real one-click bundle)
🟨 The agent isn't hand-authored here. To get a single import that includes it:
1. 🟦 In a Dataverse env, build Percy **inside** a solution (agent + the 9 flows) using
   [`agent/percy-instructions.md`](agent/percy-instructions.md), [`agent/topics.md`](agent/topics.md),
   [`flows-manifest.md`](flows-manifest.md).
2. 🟦 **Export** → that zip is your guaranteed "Import a Solution" artifact for any target.
3. 🟩 *(optional)* `pac solution unpack` it back over `src/` to keep the real source in git.

## 🟨 Limitations (same as the packaging guide)
- 🟨 Needs **Dataverse** in source + target; 🟨 your current env's import block likely applies here too.
- 🟨 **SharePoint list** + **Power BI dataset** aren't in the solution (list = provisioned separately;
  dataset = referenced by env var).
- 🟨 **Connections** don't export (only references) — bind on import.
- 🟨 **Licensing** (Copilot Studio, Power BI) unchanged by packaging.
- 🟨 Placeholder **GUIDs/prefix** must be unique/consistent; the platform owns these on a real export.

## 🧾 Manual input for THIS artifact

| # | Where | What | Type | Value/source |
|---|---|---|---|---|
| 1 | `Solution.xml` | publisher prefix / unique name / GUIDs | 🟥 | yours (or let export own them) |
| 2 | pack | run `pac solution pack` | 🟦 | `pack-solution.sh` |
| 3 | Import | bind `percy_sp` / `percy_pbi` / `percy_copilot` | 🟦 | pick/create connections |
| 4 | Import | Power BI connection account | 🟥 | signed-in shared (Build perm) |
| 5 | Import | env vars `percy_WorkspaceId` / `percy_DatasetId` / `percy_SiteUrl` | 🟥 | target ids/url |
| 6 | Flows | replicate 7 tool flows + bind env vars/refs | 🟦 / 🟩 | `flows-manifest.md` |
| 7 | Flows | paste DAX bodies (`@@OPE@@`/`@@WHO@@`) | 🟩 | `../flows/dax-templates.md` |
| 8 | Orchestrator | replace the "run agent" placeholder | 🟦 / 🟨 | Copilot Studio action |
| 9 | Agent | build agent in-solution + re-export | 🟦 | Step 3 |
| 10 | Import | turn flows **On**, **publish** agent | 🟦 | — |

See also the conceptual walkthrough: [`SOLUTION-PACKAGING.md`](SOLUTION-PACKAGING.md).
