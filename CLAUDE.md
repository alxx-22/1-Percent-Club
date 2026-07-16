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
      tools → 8 diagnostic flows, ONE PER CHECK, each embedding its own fixed DAX (no template
              input, no Switch): Percy-Summary, Percy-Locate, Percy-CompleteCare, Percy-CAP,
              Percy-Meetings, Percy-IBExpand, Percy-IPGreenLake, Percy-Accreditation
            → Percy-Refresh flow (Power BI dataset refresh)
  → flow writes AnswerText + Status=Answered (error branch writes friendly text — MUST stay wired)
  → app polls by row ID (varPollMax × 2s, default 120s)
```

**Tool set (9 tools = 9 flows, registry in `deploy/copilot-studio/topics.md`):** Get My Points
Summary · Locate Deal · Check Complete Care · Check CAP Points · Check Customer Meetings ·
Check IB Expand · Check IP GreenLake · Check Accreditation · Refresh Dashboard. Inputs are only
`ope`/`who`, **ALL optional on every trigger**; per-deal flows guard blank ope by returning
`{"error":"missing_ope"}` and the agent asks for the deal number in normal chat. The old
template-key Switch method is retired.

**Model (TMDL 2026-07) scoring facts the DAX depends on:** CC New Logo 100 (9X + New Solution S +
Won + close ≥ 1 May + no CC contract started before 1 Apr 2026); Uplift 75 (9X + New Solution S OR
Day 1 product, only when New Logo = 0); IB Expand is PRO-RATA (expand share × 25) and suppressed by
any CC points; CAP orders credit by EMAIL, CAP requests by NAME (created-date gate); meetings
classify by `Meeting Type` (Customer/Channel Partner ×10, Leadership ×20, name credit, no date
gate); IP in GL = per-month tiers summed (May + June); `Manager Sponsor Points` = race share +
CSM 30 + crew/individual bonus points. Canonical queries:
`powerapps-dashboard/deploy/flows/dax-templates.md`.

## Hard-won operational truths (violate these and you repeat a day of debugging)

- **The app runs the PUBLISHED agent; the test pane runs the DRAFT.** Any agent change needs
  Publish to reach the app. Pane-works-app-fails almost always = not published or identity issues.
- **Every tool needs:** *Ask the end user before running* = No · *Credentials to use* =
  **Maker-provided credentials** · Completion = *Don't respond*. Otherwise server-side runs die with
  `Run_an_agent` BadRequest: "The agent requested human input… specify HITL users" — a flow-invoked
  agent has no human to ask (consent cards and input prompts both trigger it).
- **Required tool inputs force prompts — so NO flow input is ever required.** No description can
  suppress a required-input prompt. Every trigger input is optional; per-deal flows return
  `{"error":"missing_ope"}` on blank ope and the agent asks conversationally (final-text questions
  are safe; mid-run input requests are what kill flow-invoked agents).
- **AI-fill of free-text inputs is non-deterministic** (same input gave: right key / raw question /
  a prompt). That's why there is no `template` input at all — one tool per check; LLMs are reliable
  at discrete choices (which named tool), unreliable at generating exact strings.
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
| Flow builds (8 diagnostics / Refresh / Orchestrator) | `powerapps-dashboard/deploy/flows/*.build.md` |
| **Canonical DAX** (one query per flow, grounded in the 2026-07 TMDL) | `powerapps-dashboard/deploy/flows/dax-templates.md` |
| Deploy order + failure tracing | `powerapps-dashboard/deploy/DEPLOY.md` · `deploy/README.md` |
| Full design, programme rules (§9), tests (§13) — §10 DAX superseded by dax-templates.md | `powerapps-dashboard/formulas/percy/backend/PERCY_BUILD_PACK.md` |

## Working agreements

- Debug from **evidence** (screenshots, run history, the SharePoint row) — never assert Power
  Platform UI mechanics unverified; when wrong once, verify before advising again.
- Every fix learned in chat gets written into the doc it belongs to, same turn, committed & pushed.
- Keep this file current: when the architecture or tool set changes, update it in the same commit.
- Deferred/known future work: `Add Points` tool for programme owners (needs approver identity +
  audit trail); operations plays (post-renewal customer-care calls, ops logging meetings).
