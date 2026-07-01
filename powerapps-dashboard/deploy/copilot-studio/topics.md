# Percy — topics to add (paste-in outlines)

With **generative orchestration** on, the instructions + tool descriptions do most of the routing,
so you may need few explicit topics. Add these where you want deterministic behaviour. Full design:
[`PERCY_BUILD_PACK.md` §6](../../formulas/percy/backend/PERCY_BUILD_PACK.md#6-percy-topic-design).

## What to actually build (don't build all 12)

Because orchestration is **on**, the agent routes from the **instructions + the two action
descriptions** — it picks the template and calls `Run Percy Diagnostic` itself. So:

- ✅ **Build the two Actions first** (agent-level, §"two actions" below) — this is the real work.
- ✅ **Build ~3 topics for determinism:** `General 1% Club FAQ`, `Refresh Dashboard`, and use the
  built-in **Conversation Start** / **Fallback** system topics.
- ⏭️ **Skip the per-scheme diagnostic topics** (Complete Care, CAP, IB, CustomerCentricity,
  IPGreenLake, Accreditation) — orchestration handles them from the instructions. Build one only if
  you want that scheme scripted/deterministic.
- ⏭️ **Skip `Process Conversation JSON` as a topic** — in orchestration mode the model parses the JSON
  per the instructions; you don't script it with Power Fx nodes.

## How to create a topic (click-by-click, Copilot Studio)

1. Open the **Percy** agent → left nav **Topics** → **+ Add a topic → From blank**.
2. **Name** it (top-left), e.g. *General 1% Club FAQ*.
3. Click the **Trigger** node → **Phrases** → paste the trigger phrases from the table below.
   *(Generative mode also lets you describe the trigger in plain language instead.)*
4. Add nodes with **+**:
   - **Send a message** — plain-text answer (FAQ → the nine ways to earn points).
   - **Ask a question** — capture input (e.g. the OPE) into a variable, only if the topic needs it.
   - **Add a tool / Call an action** — invoke `Run Percy Diagnostic`, map inputs
     `template` / `ope` / `who`, then a **Send a message** that reads the returned evidence in words.
5. **Save**, then exercise it in the **Test** pane.

**Worked example — FAQ (no tool):** Trigger = the FAQ phrases → one **Send a message** node with the
nine ways to earn points (build pack §9). That's the whole topic.

**Worked example — a diagnostic topic (only if you want it deterministic), Complete Care:**
Trigger phrases → **Condition** `ope` known? → if not, **Ask a question** "What's the deal number?"
→ **Call an action** `Run Percy Diagnostic` (`template = CompleteCare`, `ope`, `who = UserEmail`) →
**Send a message** explaining the flags in plain English. *(With orchestration on you can skip this.)*

| Topic | Trigger phrases | Does |
|---|---|---|
| **Process Conversation JSON** (system, first) | (on start) | Parse the JSON, pick `Role="user"` with max `Seq`, scan all turns for an OPE, infer the metric. Sets variables; no user text. |
| **General 1% Club FAQ** | "how do I get points", "how many points for…", "do I need a campaign code", "where do I log…" | Answer from the rules; no tool. |
| **Complete Care Diagnostic** | "complete care", "CC points", "new logo", "uplift" | Need OPE → Run Percy Diagnostic (template `CompleteCare`, ope) → explain. |
| **CAP Diagnostic** | "CAP order", "CAP request", "my cap request isn't showing", "campaign code" | Run Percy Diagnostic (template `CAP`, ope + who) → exists/date/name-match/approval. |
| **Customer Centricity Diagnostic** | "customer meeting", "channel meeting", "leadership intro", "my event isn't flowing" | Run Percy Diagnostic (template `CustomerCentricity`, ope + who) → classification + name-match + approval. |
| **IB / Expand Diagnostic** | "IB points", "expand", "pen rate", "win-back" | Run Percy Diagnostic (template `IBExpand`, ope) → motions + CC-suppression. |
| **IP in GreenLake Diagnostic** | "IP points", "GreenLake", "monthly %" | Run Percy Diagnostic (template `IPGreenLake`, who) → tier. |
| **Accreditation Diagnostic** | "accreditation", "S-coded", "CSM", "the race" | Run Percy Diagnostic (template `Accreditation`, who) → eligibility/status. |
| **Clarify & Guide** (the vague one) | "why aren't my points showing", "where are my points", "I should have more" | **Act first:** Run Percy Diagnostic (template `Summary`, who) → lead with total + **pending**, then offer "send me the OPE". Metric named but no OPE → ask only for the OPE. Bare OPE → `Locate` then route. **One question at a time; never dump the list.** |
| **Refresh Dashboard** | "refresh", "update the dashboard", "not there yet", "I closed it today", "not updating" | Call **Refresh Dashboard** action → "kicked off a refresh, check back in a few minutes" (or "already updating"). One per request. |
| **Fallback / Clarification** | (no match / off-topic) | Greeting/nonsense → friendly one-liner on what Percy can do; off-topic → politely redirect. Never loop; never dump the category list. |

## The two actions to add (build pack §15.2)

1. **"Run Percy Diagnostic"** = the `Percy-Query` flow, inputs **`template`** (Locate · CompleteCare ·
   CAP · IBExpand · CustomerCentricity · IPGreenLake · Accreditation · Summary), **`ope`**, **`who`**.
   Description from build pack §15.2 so orchestration fills the right `template`. The agent passes a
   **key, never DAX**.
2. **"Refresh Dashboard"** = the `Percy-Refresh` flow, **no inputs**. Description: *"Refresh the 1%
   Club dashboard data. Use when the user asks to refresh/update, or a deal isn't showing yet. Returns
   a short status."* One refresh per request.

## Settings
- Generative orchestration: **on**.
- General knowledge / web search: **off** (keeps Percy on-rules).
- Authentication: as your tenant requires; the agent runs server-side from the orchestrator flow.
