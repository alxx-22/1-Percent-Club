# 1% Club — repo context (auto-loaded every session; keep this current)

HPE UKIMEA sales-gamification programme: a Power BI dashboard + embedded Power App ("the app"),
crew portal, and **Percy** — a Copilot Studio chat assistant. Everything lives under
`powerapps-dashboard/`. Percy work happens on branch `claude/percy-production-plan-7r06vr`.

## Percy — architecture (as actually built)

```
Power Apps chat (imgSend creates a NEW SharePoint row per send; whole transcript in ConversationJson)
  → SharePoint list PercyConversations (Status Pending→Answered; AnswerText = the reply)
  → Percy-Orchestrator flow (trigger: "When an item is created" — create-only, NO loop guard)
      message to agent =  CallerEmail: <UserEmail> ⏎ Conversation: <ConversationJson> ⏎ CallerName: <Created By>
  → Percy agent (Copilot Studio, generative orchestration ON, web knowledge OFF)
      tools → Percy-Query flow (Switch on template key → approved DAX → Power BI executeQueries)
            → Percy-Refresh flow (Power BI dataset refresh)
  → flow writes AnswerText + Status=Answered (error branch writes friendly text — MUST stay wired)
  → app polls by row ID (varPollMax × 2s, default 120s)
```

**Current tool set (Option B, 3 tools):**
1. **Get My Points Summary** = Percy-Query registered with `template` pinned *Set as a value* =
   `Summary`, `ope` pinned empty, `who` AI-filled. Deterministic vague-path tool.
2. **Run Percy Diagnostic** = Percy-Query, `template` is a **drop-down enum** on the flow trigger
   (8 keys: Locate, CompleteCare, CAP, IBExpand, CustomerCentricity, IPGreenLake, Accreditation,
   Summary), `ope`/`who` **optional** with cold Customize descriptions.
3. **Refresh Dashboard** = Percy-Refresh (no inputs).
Escalation path if a scheme mis-picks: one pinned tool per scheme (Option A in
`powerapps-dashboard/deploy/copilot-studio/topics.md`).

## Hard-won operational truths (violate these and you repeat a day of debugging)

- **The app runs the PUBLISHED agent; the test pane runs the DRAFT.** Any agent change needs
  Publish to reach the app. Pane-works-app-fails almost always = not published or identity issues.
- **Every tool needs:** *Ask the end user before running* = No · *Credentials to use* =
  **Maker-provided credentials** · Completion = *Don't respond*. Otherwise server-side runs die with
  `Run_an_agent` BadRequest: "The agent requested human input… specify HITL users" — a flow-invoked
  agent has no human to ask (consent cards and input prompts both trigger it).
- **Required tool inputs force prompts.** No description can suppress it. `ope`/`who` are optional
  on the Percy-Query trigger; `template` stays required but is pinned/enum. Never make an input
  required unless it is always AI-resolvable.
- **AI-fill of free-text inputs is non-deterministic** (same input gave: right key / raw question /
  a prompt). Determinism = *Set as a value* pins per tool registration, or trigger drop-down enums.
  LLMs are reliable at discrete choices (which tool / which enum), unreliable at generating strings.
- **Schema changes go stale silently.** Renaming/re-typing trigger inputs, adding enums, or editing
  Respond outputs → the agent-level tool AND any topic Tool node hold the old schema. Fix = remove
  & re-add the tool (re-paste Description + input Customize texts — they get wiped), re-add topic
  nodes. Symptoms: "Destination agent was updated", "Output binding not found", variables typed
  `unknown`.
- **`who` = CallerEmail from the orchestrator message, never `System.User.Email`** (agent runs as
  the shared account), never an email typed in chat. CallerName is personalisation only.
- **Evidence keys must be unambiguous.** `CCPending` was misread as Complete Care; it's Customer
  Centricity → keys renamed (`CustomerCentricityPending`, `CompleteCareNewLogo`). Only CAP and
  Customer Centricity can EVER be "pending"; everything else is auto-calculated.
- **Topic ≠ tool namespace:** a topic named exactly like a tool throws `ToolIdentifierConflict`.
- **DLP:** SharePoint + Power BI + Copilot Studio (`agentnode`) must share one DLP group; blocked
  env fails with status 442. Build in the allowed environment.
- **Tracing a failure:** SharePoint row first (sorry-text in AnswerText = error branch ran; real
  answer late = poll timeout; **Pending + empty = flow died before the error branch** → check the
  branch's run-after wiring) → Percy-Orchestrator run history → Copilot Studio Activity tab →
  Percy-Query run history. Full guide: `powerapps-dashboard/deploy/DEPLOY.md`.

## Where the truth lives (update THESE, not just chat)

| What | File |
|---|---|
| Agent instructions (paste block — must match the tools that actually exist) | `powerapps-dashboard/deploy/copilot-studio/percy-instructions.md` |
| Tool registry, input descriptions, topics | `powerapps-dashboard/deploy/copilot-studio/topics.md` |
| Flow builds (Query / Refresh / Orchestrator) | `powerapps-dashboard/deploy/flows/*.build.md` |
| Deploy order + failure tracing | `powerapps-dashboard/deploy/DEPLOY.md` · `deploy/README.md` |
| Full design, DAX templates (§10), programme rules (§9), tests (§13) | `powerapps-dashboard/formulas/percy/backend/PERCY_BUILD_PACK.md` |

## Working agreements

- Debug from **evidence** (screenshots, run history, the SharePoint row) — never assert Power
  Platform UI mechanics unverified; when wrong once, verify before advising again.
- Every fix learned in chat gets written into the doc it belongs to, same turn, committed & pushed.
- Keep this file current: when the architecture or tool set changes, update it in the same commit.
- Deferred/known future work: `Add Points` tool for programme owners (needs approver identity +
  audit trail); operations plays (post-renewal customer-care calls, ops logging meetings).
