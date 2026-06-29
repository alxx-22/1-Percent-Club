# Percy — topics to add (paste-in outlines)

With **generative orchestration** on, the instructions + tool descriptions do most of the routing,
so you may need few explicit topics. Add these where you want deterministic behaviour. Full design:
[`PERCY_BUILD_PACK.md` §6](../../formulas/percy/backend/PERCY_BUILD_PACK.md#6-percy-topic-design).

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
| **Fallback / Clarification** | (no match / missing input) | Greeting/nonsense → friendly menu; missing OPE → ask; ambiguous metric → template `Locate` or ask. |

## The one action to add (build pack §15.2)

Add the single `Percy-Query` flow as the action **"Run Percy Diagnostic"**, with inputs
**`template`** (Locate · CompleteCare · CAP · IBExpand · CustomerCentricity · IPGreenLake ·
Accreditation · Summary), **`ope`**, **`who`**. Give it the description from build pack §15.2 so
orchestration fills the right `template` key. The agent passes a **key, never DAX**.

## Settings
- Generative orchestration: **on**.
- General knowledge / web search: **off** (keeps Percy on-rules).
- Authentication: as your tenant requires; the agent runs server-side from the orchestrator flow.
