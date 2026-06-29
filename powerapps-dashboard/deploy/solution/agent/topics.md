# Percy — topics & tool actions (clone for the solution build)

> 🟩 **PROVIDED.** Mirrors [`../../copilot-studio/topics.md`](../../copilot-studio/topics.md), cloned
> here so the agent build is self-contained. 🟦 **MANUAL ACTION:** add these in Copilot Studio while
> the agent is **inside the solution**.

## Topics (🟦 add where you want deterministic behaviour)

With **generative orchestration on**, the instructions + tool descriptions do most routing. Add
explicit topics where you want guaranteed behaviour. Full design:
[`PERCY_BUILD_PACK.md` §6](../../../formulas/percy/backend/PERCY_BUILD_PACK.md#6-percy-topic-design).

| Topic | Trigger phrases | Does |
|---|---|---|
| **Process Conversation JSON** (system, first) | (on start) | Parse JSON, pick `Role="user"` max `Seq`, scan for OPE, infer metric. |
| **General 1% Club FAQ** | "how do I get points", "how many points for…", "campaign code", "where do I log…" | Answer from rules; no tool. |
| **Complete Care Diagnostic** | "complete care", "CC points", "new logo", "uplift" | Check Complete Care Points Evidence → explain. |
| **CAP Diagnostic** | "CAP order", "CAP request", "my cap request isn't showing" | Check CAP Points Evidence (pass email). |
| **Customer Centricity Diagnostic** | "customer/channel/leadership meeting", "event isn't flowing" | Check Customer Centricity Evidence (pass email). |
| **IB / Expand Diagnostic** | "IB points", "expand", "pen rate", "win-back" | Check IB / Expand Points Evidence. |
| **IP in GreenLake Diagnostic** | "IP points", "GreenLake", "monthly %" | Check IP in GreenLake Evidence (email). |
| **Accreditation Diagnostic** | "accreditation", "S-coded", "CSM", "the race" | Check Accreditation Evidence (email). |
| **Fallback / Clarification** | (no match / missing input) | Friendly menu; ask for OPE; Locate or ask metric. |

## Tool actions (🟦 add all 8 as actions; 🟩 descriptions provided)

Add each tool flow (Step 4) as an **action**, with these descriptions so orchestration picks correctly:

- **Locate Opportunity** — "Metric unclear / no points at all. Input: OPE. Returns which schemes the opp appears in."
- **Check Complete Care Points Evidence** — "Why CC points are/aren't showing. Input: OPE. Returns product line / motion / close date / active contract / New Logo (100) / Uplift (75)."
- **Check CAP Points Evidence** — "CAP engagement (20) or order (50), incl. 'request isn't showing'. Inputs: OPE, user email. Returns existence/date/name-match/approval."
- **Check Customer Centricity Evidence** — "Logged meeting points, incl. mistyped subject. Inputs: OPE, user email. Returns classification / name-match / approval / points."
- **Check IB / Expand Points Evidence** — "IB/Expand (≤25). Input: OPE. Returns motions / win / CC-suppression / awarded value."
- **Check IP in GreenLake Evidence** — "IP tier (10–75). Input: user email. Returns monthly % / tier / points."
- **Check Accreditation Evidence** — "Accreditation/CSM. Input: user email. Returns S-coded / completion / exclusions / CSM / awarded."
- **Get Overall Points Summary** — "All categories + pending. Input: user email."

## Settings (🟦)
- Generative orchestration: **on**.
- General knowledge / web search: **off**.
- 🟨 Authentication / channels: tenant-specific; set per your policy (and re-verify after a solution import — these may not export).
