# Percy — topics to add (paste-in outlines)

With **generative orchestration** on, the instructions + tool descriptions do most of the routing,
so you may need few explicit topics. Add these where you want deterministic behaviour. Full design:
[`PERCY_BUILD_PACK.md` §6](../../formulas/percy/backend/PERCY_BUILD_PACK.md#6-percy-topic-design).

| Topic | Trigger phrases | Does |
|---|---|---|
| **Process Conversation JSON** (system, first) | (on start) | Parse the JSON, pick `Role="user"` with max `Seq`, scan all turns for an OPE, infer the metric. Sets variables; no user text. |
| **General 1% Club FAQ** | "how do I get points", "how many points for…", "do I need a campaign code", "where do I log…" | Answer from the rules; no tool. |
| **Complete Care Diagnostic** | "complete care", "CC points", "new logo", "uplift" | Need OPE → Check Complete Care Points Evidence → explain. |
| **CAP Diagnostic** | "CAP order", "CAP request", "my cap request isn't showing", "campaign code" | Check CAP Points Evidence (pass email) → exists/date/name-match/approval. |
| **Customer Centricity Diagnostic** | "customer meeting", "channel meeting", "leadership intro", "my event isn't flowing" | Check Customer Centricity Evidence (pass email) → classification + name-match + approval. |
| **IB / Expand Diagnostic** | "IB points", "expand", "pen rate", "win-back" | Check IB / Expand Points Evidence → motions + CC-suppression. |
| **IP in GreenLake Diagnostic** | "IP points", "GreenLake", "monthly %" | Check IP in GreenLake Evidence (email) → tier. |
| **Accreditation Diagnostic** | "accreditation", "S-coded", "CSM", "the race" | Check Accreditation Evidence (email) → eligibility/status. |
| **Fallback / Clarification** | (no match / missing input) | Greeting/nonsense → friendly menu; missing OPE → ask; ambiguous metric → Locate or ask. |

## Tool actions to add (build pack §15.2)

Add all 8 flows as actions, each with a clear description so orchestration picks correctly:
Locate Opportunity · Check Complete Care Points Evidence · Check CAP Points Evidence · Check
Customer Centricity Evidence · Check IB / Expand Points Evidence · Check IP in GreenLake Evidence ·
Check Accreditation Evidence · Get Overall Points Summary.

## Settings
- Generative orchestration: **on**.
- General knowledge / web search: **off** (keeps Percy on-rules).
- Authentication: as your tenant requires; the agent runs server-side from the orchestrator flow.
