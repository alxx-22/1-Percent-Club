# Percy — Production Build Pack (Stage 2: FAQ + Power BI diagnostics)

This is the implementation-ready build pack for **Percy**, the 1% Club assistant. It extends
the no-premium Stage-1 pattern in [`README.md`](README.md) (Power Apps → SharePoint → Power
Automate → reply, polled back) with a **Copilot Studio** brain that routes between **FAQ
answers** (programme rules) and **controlled Power BI diagnostics** (per-OPE lookups against the
semantic model).

Everything here is grounded in the **actual** model. Scoring facts, table/column names and the
Complete Care logic were read from the live TMDL and the dashboard build
([`Screen_OnVisible.powerfx`](../../dashboard/Screen_OnVisible.powerfx),
[`IP_in_GL_points.dax`](../../dashboard/IP_in_GL_points.dax)) — not invented.

> **Non-negotiables (carried through every section):**
> - The user-facing **`Reply`** column is **plain English text only**. Never JSON, never DAX,
>   never raw table/column names.
> - JSON/DAX are **internal** transport only (Power Automate ⇄ Copilot Studio ⇄ tools).
> - Percy **never writes DAX**. It calls **approved tool actions** that run **fixed DAX templates**.
> - Percy **never invents programme rules or point values** — only the nine rules in §9.

---

## Table of contents
1. [Recommended architecture](#1-recommended-architecture)
2. [SharePoint list design](#2-sharepoint-list-design)
3. [Power Apps behaviour](#3-power-apps-behaviour)
4. [Main Power Automate flow](#4-main-power-automate-flow)
5. [Percy Copilot Studio overview instructions](#5-percy-copilot-studio-overview-instructions)
6. [Percy topic design](#6-percy-topic-design)
7. [Tool / action design](#7-tool--action-design)
8. [Complete Care diagnostic logic](#8-complete-care-diagnostic-logic)
9. [Programme rules (canonical)](#9-programme-rules-canonical)
10. [DAX templates](#10-dax-templates)
11. [TMDL analysis](#11-tmdl-analysis)
12. [Prompt / response examples](#12-prompt--response-examples)
13. [Testing plan](#13-testing-plan)
14. [Implementation checklist](#14-implementation-checklist)
15. [Final deliverables](#15-final-deliverables)

---

## 1. Recommended architecture

### 1.1 Should Percy be Copilot Studio, AI Builder, or hybrid?

| Option | Fit for Percy | Verdict |
|---|---|---|
| **AI Builder prompt** (single "Create text with GPT") | Great for pure FAQ (Stage 1). Cannot *route*, cannot *call tools* mid-answer, no managed conversation state. | Too thin for the diagnostic use case. |
| **Full Copilot Studio agent** | Native **topic routing**, **generative orchestration**, **tool/action calling** (a Power Automate flow added as an action), system instructions, knowledge sources. | **Use this.** |
| **Hybrid** (Copilot Studio + AI Builder sub-prompts) | Possible, but adds moving parts with no benefit here. | Not needed. |

**Decision (as you specified): Percy is a Copilot Studio agent.** It must decide, per turn,
between *"answer from the rules"* and *"run a diagnostic lookup"*, and only an agent that can
**call a controlled action and then reason over its result** does that cleanly.

### 1.2 Two flows, not one

There are **two distinct Power Automate flows**. Keep them separate:

| Flow | Trigger | Role |
|---|---|---|
| **`Percy-Orchestrator`** (main) | SharePoint *item created* on `PercyConversations` | Guards Role=user, sets Status, hands the conversation JSON to the Percy agent, writes the plain-text `Reply`, sets Status. |
| **`Percy-Tool-*`** (diagnostic actions) | *Called by Copilot Studio* (manual/agent trigger) | Run an **approved DAX template** against the semantic model via the **Power BI connector** (signed-in shared connection), return **compact JSON evidence** to the agent. One flow per tool (§7). |

The "Run an agent" step in your existing pattern is the Copilot Studio agent action inside
`Percy-Orchestrator`. The diagnostic flows are invoked *from inside* Percy, not by SharePoint.

### 1.3 End-to-end data flow

```
┌─────────────┐   Patch (one row per SessionId)            ┌──────────────────────────┐
│  Power Apps │ ─ {ConversationJson, Status:"Pending"} ──▶ │  SharePoint              │
│  Percy chat │                                            │  PercyConversations list │
│  (galChat)  │ ◀── poll every 2s: Reply + Status ──────── │                          │
└─────────────┘                                            └────────────┬─────────────┘
      ▲                                                        item created │ (Role=user)
      │ tmrPercyPoll shows plain-text Reply                                 ▼
      │                                              ┌─────────────────────────────────┐
      │                                              │ Power Automate: Percy-Orchestrator│
      │                                              │  1 guard Role=user                │
      │                                              │  2 Status=Processing              │
      │                                              │  3 build/normalise conversation   │
      │                                              │  4 ► Run Percy agent (JSON in)     │
      │                                              │  6 Update item: Reply=<plain text> │
      │                                              │     Status=Complete (or Error)    │
      │                                              └───────────────┬───────────────────┘
      │                                                  agent reasons │ (Copilot Studio)
      │                                                                ▼
      │                                              ┌─────────────────────────────────┐
      │                                              │ Percy (Copilot Studio agent)      │
      │                                              │  • parse JSON, find latest user   │
      │                                              │  • route: FAQ vs diagnostic       │
      │                                              │  • if OPE+metric ► call a TOOL    │
      │                                              └───────────────┬───────────────────┘
      │                                                  tool action  │ (approved DAX only)
      │                                                                ▼
      │                                              ┌─────────────────────────────────┐
      │                          compact JSON evidence│ Power Automate: Percy-Tool-CC etc │
      │                          ◀────────────────────│  Power BI "Run a query against a  │
      │                                               │  dataset" (executeQueries)        │
      │                                               │  signed-in shared connection      │
      │                                               └───────────────┬───────────────────┘
      │                                                                ▼
      │                                               ┌────────────────────────────────┐
      └──────── plain English ◀────── agent composes ─┤ Power BI semantic model (import)│
                                                       │  Final / CC Contracts / Cap …   │
                                                       └────────────────────────────────┘
```

**No service principal, no REST/XMLA app.** The diagnostic flows use the standard **Power BI
connector** action *"Run a query against a dataset"* with a **signed-in connection account** that
has read access to the workspace and semantic model. (Confirm the connection user is a workspace
**Viewer+** / has Build permission on the dataset.)

---

## 2. SharePoint list design

List: **`PercyConversations`**. There are two valid shapes — pick **B** for the new build, but
the orchestrator supports both.

- **Shape A (Stage-1, one row per *conversation*)** — what the existing app Patches today: keyed
  by `SessionId`, `ConversationJson` holds the whole transcript, the flow writes `AnswerText`.
- **Shape B (one row per *message*, recommended for this spec)** — matches your requested columns
  exactly (`Seq`, `Role`, `Body`, `Reply`, …). Percy answers the row where `Role="user"` and `Seq`
  is highest; earlier rows are context.

### 2.1 Columns (Shape B)

| Column | Type | Written by | Notes |
|---|---|---|---|
| `Title` | Single line | Power Apps | Use `ConversationId` value (so the list view is readable). |
| `ConversationId` | Single line of text | **Power Apps** | GUID per chat session. **Index it.** Groups the turns. |
| `Seq` | Number | **Power Apps** | Monotonic per conversation. Latest user message = max `Seq` where `Role="user"`. |
| `Role` | Single line of text | **Power Apps** | `"user"` or `"percy"`. **Keep text, not Choice** (Choice returns a record → `Role = "user"` throws *"Incompatible types: Record, Text"*). |
| `Body` | Multiple lines, **plain text** | **Power Apps** | The user's message (or, on Percy rows you choose to persist, Percy's). Turn **off** enhanced rich text. |
| `Reply` | Multiple lines, **plain text** | **Power Automate** | Percy's final plain-English answer. **Plain text only.** |
| `Status` | Single line of text | **Power Automate** (init blank/`New` by Power Apps) | `New` → `Processing` → `Complete` / `Error`. **Text, not Choice.** |
| `ErrorMessage` | Multiple lines, plain text | **Power Automate** | Technical detail for admins/telemetry. **Never surfaced to the user.** |
| `UserEmail` | Single line of text | **Power Apps** | `Lower(User().Email)`. Drives per-user diagnostics & audit. |
| `Created` | Date/time | SharePoint (auto) | System `Created`. |
| `Modified` | Date/time | SharePoint (auto) | System `Modified`. |
| `MetricType` *(optional)* | Single line of text | **Power Automate** (Percy/agent) | Detected category: `CompleteCare` / `CAP` / `CustomerCentricity` / `IBNS` / `IPGL` / `Accreditation` / `General` / `Unknown`. For analytics. |
| `OPE` *(optional)* | Single line of text | **Power Automate** (Percy/agent) | Extracted opportunity id, e.g. `OPE-123456789`. For analytics/repro. |
| `ConversationJson` *(optional)* | Multiple lines, plain text | Power Apps | If you keep Shape A in parallel: the full transcript the agent reads. |

**Who writes what — summary:**
- **Power Apps writes:** `Title`, `ConversationId`, `Seq`, `Role`, `Body`, `UserEmail`, and seeds
  `Status="New"`. (`Reply` stays empty.)
- **Power Automate writes:** `Status` (`Processing`→`Complete`/`Error`), `Reply`, `ErrorMessage`,
  and optionally `MetricType` / `OPE`.
- **SharePoint writes:** `Created`, `Modified`.

> Keep every multi-line column **plain text** (enhanced rich text **off**) so JSON in / answers out
> are never HTML-mangled. After adding columns, **refresh the data source in Power Apps** (Data
> pane → ⋯ → Refresh) or the new columns show as red/"unexpected".

---

## 3. Power Apps behaviour

The chat UI already exists ([`PERCY.md`](../../../PERCY.md)): `galChat` bound to
`Sort(colChat, Seq)`, `imgSend.OnSelect` Patches the row, `tmrPercyPoll` polls for the reply,
`imgThinking` shows the typing state. Behaviour to lock in:

1. **Submit** — `imgSend.OnSelect` (guarded `!IsBlank(Trim(txtChat.Text)) && !varPercyThinking`,
   see [`imgSend.OnSelect.powerfx`](../imgSend.OnSelect.powerfx)):
   - Append `{ Seq, Role:"user", Body }` to `colChat`, `Reset(txtChat)`.
2. **Create SharePoint item** — `Patch` a **new row per user message** (Shape B):
   ```powerfx
   Set( varSeq, CountRows(colChat) );           // Seq of this user turn
   Set( varAsk,
       Patch( PercyConversations, Defaults(PercyConversations),
           { Title:          varSessionId,
             ConversationId: varSessionId,
             Seq:            varSeq,
             Role:           "user",
             Body:           varPercyQ,
             UserEmail:      Lower(User().Email),
             Status:         "New" } ) );
   Set( varAskId, varAsk.ID );
   Set( varPollN, 0 ); Set( varThinkOut, false ); Set( varPercyThinking, true );
   ```
   *(Stage-1 Shape A instead upserts one row by `SessionId` with `ConversationJson` — keep
   whichever your flow consumes; §4 reads both.)*
3. **Pending / processing state** — `Set(varPercyThinking, true)` shows `imgThinking`
   ("Percy is thinking/typing…") and **starts** `tmrPercyPoll` (`Start = varPercyThinking`). The
   send button is disabled while thinking (the `&& !varPercyThinking` guard).
4. **Polling refresh** — `tmrPercyPoll.OnTimerEnd` (every 2s, see
   [`tmrPercyPoll.OnTimerEnd.powerfx`](../tmrPercyPoll.OnTimerEnd.powerfx)):
   `Refresh(PercyConversations)`, re-`LookUp` the row by `ID = varAskId`, and when
   `Status="Complete"` **and** `Reply` is non-blank, append `{ Role:"percy", Body: Reply }` to
   `colChat` **once** (guarded by `varPercyThinking` so extra ticks can't double-post).
5. **Display Reply** — the new `colChat` row renders through `htmlBubble` (left/white card for
   Percy). `galChat` shows it because `Items = Sort(colChat, Seq)`.
6. **Avoid duplicate submissions** — the `!varPercyThinking` guard blocks a second send while one
   is in flight; the `varGotReply = varPercyThinking && …` guard in the poll guarantees the reply
   is collected exactly once.
7. **Sort by Seq** — `galChat.Items = Sort(colChat, Seq)` (oldest→newest, newest at bottom).
8. **Group / filter by ConversationId** — `varSessionId = GUID()` (set in
   [`App_OnStart`](../../dashboard/App_OnStart.powerfx)) tags every row written this session; the
   poll filters by `ID`, and any history reload filters `Filter(PercyConversations,
   ConversationId = varSessionId)` then `Sort(... , Seq)`.
9. **Timeout** — total wait = `tmrPercyPoll.Duration (2000ms) × varPollMax (60) = 120s`. The
   SharePoint *item-created* trigger alone can take 30–60s to fire, so keep this generous; on
   timeout Percy posts a friendly "couldn't reach the assistant" bubble and stops polling.

> **Timers in a Power BI-embedded visual can be unreliable.** Provide a tiny "check for reply"
> image/button whose `OnSelect` runs the same body as `tmrPercyPoll.OnTimerEnd` as a manual fallback.

---

## 4. Main Power Automate flow (`Percy-Orchestrator`)

**Trigger:** SharePoint **"When an item is created"** on `PercyConversations`.
*(If you keep the Stage-1 upsert pattern, use "created **or modified**" and guard on
`Status = "Pending"` to avoid the self-update loop — see [`README.md`](README.md) §3.)*

| # | Action | Detail |
|---|---|---|
| 1 | **Guard: only run for user turns** | `Condition`: `Role` **is equal to** `user`. (Also short-circuit if `Status` is already `Processing/Complete`.) If no → **Terminate (Succeeded)**. |
| 2 | **Set Status = Processing** | `Update item` → `Status: Processing`. Stamps "in flight" so reruns/polls don't double-fire. |
| 3 | **Build / retrieve conversation JSON** | `Get items` on `PercyConversations` with `Filter Query: ConversationId eq '<triggerBody ConversationId>'`, `Order By: Seq asc`. `Select` → array of `{ "Seq": Seq, "Role": Role, "Body": Body }`. `Compose` → `ConversationJson`. *(Shape A: read `ConversationJson` straight off the trigger item.)* |
| 4 | **Run Percy agent** | Copilot Studio agent action (`Percy`). **Input** = `ConversationJson` (string) + `UserEmail`. The agent finds the latest user message, routes, optionally calls a tool, returns **plain text**. |
| 5 | **Sanitise the agent output** | `Compose`: `if(empty(trim(<agent text>)), 'Sorry, I couldn''t answer that one — please try again.', <agent text>)`. Strip any stray code fences (defence-in-depth: replace ```` ``` ```` and leading `{`/`[` blocks). The agent should already return prose. |
| 6 | **Update item — write the Reply** | `Update item` → `Reply: <sanitised text>`, `Status: Complete`, optional `MetricType`/`OPE` from the agent's structured side-channel. |
| — | **Error handling (parallel / Scope + "has failed")** | Wrap 3–6 in a **Scope**. On failure, run a second Scope (`Configure run after: has failed, timed out`): `Update item` → `Status: Error`, `Reply: "Sorry, I couldn't reach the assistant just now — please try again."`, `ErrorMessage: <technical detail>` (admin-only; never shown to the user). |

**Concurrency:** set the trigger's concurrency to a sane cap (e.g. 10) so a burst of chats doesn't
exhaust the Copilot Studio / Power BI connection. **Telemetry:** the `ErrorMessage` column + flow
run history are your audit trail; `MetricType`/`OPE` give you per-category usage analytics.

---

## 5. Percy Copilot Studio overview instructions

Paste verbatim into **Percy → Overview → Instructions**. (Also reproduced in §15.)

```
ROLE
You are Percy, the friendly assistant for HPE's "1% Club" sales gamification programme. You
help sales users understand why 1% Club points are, or are not, showing in their Power App /
dashboard. You answer two kinds of question: (a) FAQ questions about the programme rules, and
(b) diagnostic questions about a specific opportunity (an "OPE" number).

TONE
Warm, concise, plain-English, encouraging. Short paragraphs or tight bullet points. No jargon.
Never sound like a database. You are talking to a busy salesperson, not an engineer.

OUTPUT — ALWAYS PLAIN TEXT
Your final answer is shown directly to the user in a chat bubble. It MUST be plain English prose.
Never output JSON, DAX, SQL, code blocks, table/column names, internal IDs, entity IDs, or any
implementation detail. If a tool hands you JSON, read it, then explain it in words. The only
exception is if an admin/developer explicitly asks for technical detail and identifies as such.

READING THE CONVERSATION
You receive the conversation as a JSON array of objects with "Seq", "Role" and "Body".
- The CURRENT question is the object with Role = "user" and the HIGHEST Seq.
- Use all earlier messages only as context (e.g. an OPE mentioned two turns ago).
- IGNORE Role = "percy" messages except as context for what was already said.
Never answer an older user message; always act on the latest one.

OPE NUMBERS
An OPE is an opportunity id like "OPE-123456789". Extract it from the latest user message, or
from earlier context if the user clearly still means the same one. Accept it with or without the
"OPE-" prefix and with surrounding text. If a diagnostic is needed and no OPE is present anywhere
in the conversation, ASK for the OPE before calling any tool.

ROUTING — WHEN TO DO WHAT
1. FAQ / "how does X score?" / rule questions  → answer DIRECTLY from the Programme Rules below.
   Do not call a tool. State exact point values from the rules.
2. "Why can't I see points for OPE-…" / "check <metric> for OPE-…" / a specific opportunity
   → this is a DIAGNOSTIC. Identify the metric (Complete Care, CAP, Customer Centricity, …),
   confirm/extract the OPE, then call the matching approved tool. Explain the tool's evidence
   in plain English.
3. Metric unclear but OPE present → if context makes the metric obvious, proceed; otherwise ask
   "Which points did you expect for this one — Complete Care, CAP, or Customer Centricity?"
4. Greeting / nonsense / mixed ("beep boop how do i get points") → be friendly, extract any real
   intent, and answer the real part (e.g. give the "how to earn points" overview).

TOOLS — APPROVED DIAGNOSTICS ONLY
You may ONLY obtain opportunity data by calling these approved actions. You must NEVER write or
request DAX, and never query the model any other way:
- "Check Complete Care Points Evidence"  (input: OPE)
- "Check CAP Points Evidence"            (input: OPE)
- "Check Customer Centricity Evidence"   (input: OPE)
- "Get Overall Points Summary"           (input: user email)
Call exactly one tool per diagnostic unless the user asks about several metrics. If a tool returns
"not found" or an error, say so plainly and suggest next steps — do not guess numbers.

HARD RULES
- NEVER invent programme rules, point values, dates, or eligibility criteria. If the rules below
  don't cover it, say you can only help with the 1% Club rules you know, and suggest who to ask.
- NEVER invent an opportunity's data. If you haven't called a tool, you don't know its status.
- NEVER expose JSON/DAX/table names/entity IDs. Translate everything into business language.
- If the available evidence does not confirm an answer, say what you can confirm and what is
  uncertain, and give the most likely reason(s) — don't overstate certainty.

PROGRAMME RULES (your only source of truth for scoring)
<< paste the nine rules from §9 here, verbatim >>
```

---

## 6. Percy topic design

Copilot Studio routes either via **generative orchestration** (recommended — the instructions +
tool descriptions drive routing) or classic **trigger-phrase topics**. Define these topics so
behaviour is explicit and testable.

### 6.1 `Process SharePoint Conversation JSON` (system / first)
- **Purpose:** normalise input every turn — parse the JSON, isolate the latest user message,
  collect prior OPE/metric context.
- **Trigger:** runs first on every invocation (On-Conversation-Start / highest priority).
- **Inputs:** `ConversationJson` (string), `UserEmail`.
- **Decision logic:** parse array → select `Role="user"` with max `Seq` → set `var_LatestText`.
  Scan all `Body` values for an OPE regex → `var_OPE`. Infer `var_Metric` from keywords
  (Complete Care / CC / "complete care", CAP, Customer Centricity / meeting, IB / expand, IP /
  GreenLake, accreditation).
- **Output:** sets variables; routes to the matching topic below. No user-facing text.

### 6.2 `General 1% Club FAQ`
- **Purpose:** answer rule questions directly, no tool call.
- **Trigger phrases:** "how do I get points", "how many points for…", "do I need a campaign code",
  "where do I log…", "what counts as…", "how is X scored", "rules for…".
- **Inputs:** `var_LatestText`.
- **Decision logic:** match the question to a rule in §9; answer with the exact value. If it spans
  several rules (e.g. "how do I get points?"), give the short menu of the nine ways.
- **Output:** plain-text rule answer. Never calls a tool.

### 6.3 `Complete Care Diagnostic`
- **Purpose:** explain why Complete Care points are/aren't showing for an OPE.
- **Trigger phrases:** "complete care", "CC points", "complete care for OPE", "why no complete care".
- **Inputs:** `var_OPE` (required), context.
- **Decision logic:** see §8. No OPE → ask for it. OPE present → call **Check Complete Care Points
  Evidence** → interpret flags (found, product line, sales motion, close date, active contract,
  awarded points, in-funnel) → plain-English explanation.
- **Output:** plain text: what's confirmed, the points (if any), and the most likely reason if zero.

### 6.4 `CAP Diagnostic`
- **Purpose:** explain CAP engagement / CAP-order points for an OPE.
- **Trigger phrases:** "CAP order", "CAP request", "CAP points", "cap engagement", "it's a CAP order why no points".
- **Inputs:** `var_OPE` (required).
- **Decision logic:** call **Check CAP Points Evidence** → distinguish CAP **request** (20, approved
  by Gemma/BD) vs CAP-generated **order** (50, won, close after 1 May, approved). Surface approval
  status (very often the answer is "pending sign-off", not "ineligible").
- **Output:** plain text with the approval/eligibility reason.

### 6.5 `Customer Centricity Diagnostic`
- **Purpose:** explain logged-meeting points for an OPE.
- **Trigger phrases:** "customer meeting", "leadership meeting", "channel meeting", "customer centricity", "logged a meeting no points".
- **Inputs:** `var_OPE` (required).
- **Decision logic:** call **Check Customer Centricity Evidence** → check Subject prefix
  (CUSTOMER/CHANNEL/LEADERSHIP) classified the meeting, and approval status (manager approves
  weekly). Explain 10/10/20 values.
- **Output:** plain text.

### 6.6 `Fallback / Clarification`
- **Purpose:** handle greetings, nonsense, ambiguous/missing inputs.
- **Trigger:** no other topic matched, or required input missing.
- **Decision logic:** greeting/nonsense → friendly nudge + "how to earn points" menu. Diagnostic
  intent but no OPE → ask for the OPE. OPE but ambiguous metric → ask which metric.
- **Output:** one short clarifying question OR the helpful overview. Never a tool call.

---

## 7. Tool / action design

Each tool is a **separate Power Automate flow** added to Percy as an **action**. All use the
Power BI **"Run a query against a dataset"** action with the **signed-in shared connection**.
The DAX is a **fixed template** (§10); the flow injects only a **validated** parameter. The flow
returns **compact JSON** (a tiny `Response`/`Compose`), which Percy reads and **never echoes**.

**Common security controls (all tools):**
- **Input validation:** the OPE must match `^OPE-?\d{6,12}$` (case-insensitive); reject otherwise
  → return `{ "error": "invalid_ope" }`. This prevents DAX string-injection via the parameter.
- **Email validation** (summary tool): must match the signed-in user or an allowed admin; reject
  cross-user lookups unless the caller is an approved manager/admin (least privilege).
- **Output minimisation:** return only the fields below — never whole rows, never PII beyond
  name/account already visible on the dashboard, never entity IDs.
- **Fixed DAX only:** the parameter is substituted into a constant template; no caller-supplied DAX.
- **Connection:** least-privilege shared account with read on the workspace; rotate per policy.

---

### 7.1 `Check Complete Care Points Evidence`
- **Purpose:** return the evidence needed to explain Complete Care (New Logo 100 / Uplift 75) for one OPE.
- **Inputs:** `OPE` (string, validated).
- **DAX:** Template **B** (§10.2).
- **Output schema:**
  ```json
  {
    "ope": "string",
    "found": "Yes|No",
    "opportunityName": "string",
    "account": "string",
    "forecastCategory": "string",
    "closeDate": "date",
    "hasCCProductLine": "Yes|No",
    "hasNewSolutionMotion": "Yes|No",
    "hasDay1Motion": "Yes|No",
    "closedOnOrAfter1May2026": "Yes|No",
    "activeCCContract": "Yes|No",
    "newLogoPointsAwarded": 0,
    "upliftPointsAwarded": 0,
    "ccPointsTotal": 0,
    "inFunnelNotYetWon": "Yes|No"
  }
  ```
- **Example payload:**
  ```json
  { "ope":"OPE-123456789","found":"Yes","opportunityName":"Acme DC Refresh","account":"Acme Corp",
    "forecastCategory":"Pipeline","closeDate":"2026-06-30","hasCCProductLine":"Yes",
    "hasNewSolutionMotion":"Yes","hasDay1Motion":"No","closedOnOrAfter1May2026":"Yes",
    "activeCCContract":"No","newLogoPointsAwarded":0,"upliftPointsAwarded":0,"ccPointsTotal":0,
    "inFunnelNotYetWon":"Yes" }
  ```
- **What Percy says (common results):**
  - `ccPointsTotal=100` → "Good news — this one is scoring the full 100 Complete Care New Logo points."
  - `inFunnelNotYetWon=Yes`, total 0 → "It qualifies on product and timing, but it hasn't been **Won** yet — Complete Care points land when the opportunity is won, so it'll show once it closes."
  - `activeCCContract=Yes`, motion ok → "This customer already has an active Complete Care contract, so it doesn't meet the **New Logo** condition. If it's an uplift it scores 75 instead — let me know and I'll re-check."
  - `hasCCProductLine=No` → "I can't see any Complete Care product lines on this opportunity, so it isn't picking up Complete Care points. Worth checking the product lines on the opp."
  - `found=No` → "I can't find that opportunity in the scoring data yet. Double-check the OPE number, and note new opportunities can take a refresh cycle to appear."
- **Failure cases:** `invalid_ope` → "That doesn't look like a full OPE number — it should look like OPE-123456789."; dataset/query error → friendly retry message, log to `ErrorMessage`.
- **Security:** as common controls. Note the activeCCContract flag mirrors the model's current
  entity-id match (see §11 caveat) — Percy speaks to it qualitatively, never quotes IDs.

### 7.2 `Check CAP Points Evidence`
- **Purpose:** explain CAP engagement (20) and CAP-generated order (50) points for an OPE.
- **Inputs:** `OPE` (validated).
- **DAX:** Template **E** (§10.5).
- **Output schema:**
  ```json
  { "ope":"string","inCapWon":"Yes|No","capWonForecast":"string","capWonCloseDate":"date",
    "capWonCloseQualifies":"Yes|No","capWonApprovalStatus":"string","capWonPoints":0,
    "inCapRequests":"Yes|No","capRequestApproval":"string","capRequestPoints":0 }
  ```
- **Example payload:**
  ```json
  { "ope":"OPE-123456789","inCapWon":"Yes","capWonForecast":"Won","capWonCloseDate":"2026-05-20",
    "capWonCloseQualifies":"Yes","capWonApprovalStatus":"","capWonPoints":0,
    "inCapRequests":"No","capRequestApproval":"","capRequestPoints":0 }
  ```
- **What Percy says:**
  - Won + qualifies + approval blank → "This CAP order is **won and eligible**, but it's still **pending sign-off** (Gemma validates CAP orders). The 50 points appear once it's approved."
  - approval `Approve`, points 50 → "Yep — 50 points for this CAP-generated order are confirmed."
  - `capWonCloseQualifies=No` → "Its close date is before 1 May 2026, which is the cut-off for CAP order points, so it won't score."
  - request approved → "This is logged as a CAP engagement and approved — 20 points."
- **Failure cases / security:** as common controls. (Campaign-code validation isn't in the model —
  see §11; Percy states the campaign-code requirement from the rules but doesn't claim to have
  checked it.)

### 7.3 `Check Customer Centricity Evidence`
- **Purpose:** explain logged-meeting points (Customer 10 / Channel 10 / Leadership 20) for an OPE.
- **Inputs:** `OPE` (validated).
- **DAX:** Template **F** (§10.6) — narrow (one row per logged meeting on the opp).
- **Output schema:**
  ```json
  { "ope":"string","meetings":[
      {"meetingType":"string","subject":"string","loggedBy":"string","approvalStatus":"string","points":0}
  ], "meetingCount":0 }
  ```
- **Example payload:**
  ```json
  { "ope":"OPE-123456789","meetingCount":1,
    "meetings":[{"meetingType":"Leadership Meeting","subject":"LEADERSHIP intro to CIO",
      "loggedBy":"Jane Rep","approvalStatus":"","points":0}] }
  ```
- **What Percy says:**
  - meeting present, approval blank → "I can see a Leadership meeting logged on this opp — that's worth 20 points once your manager approves it (they sign these off weekly)."
  - `meetingType` blank / subject prefix wrong → "The meeting's subject doesn't start with CUSTOMER, CHANNEL or LEADERSHIP, so it isn't being classified for points. Re-log it with the right prefix and it'll count."
  - `meetingCount=0` → "I can't see any logged events on this opportunity. Customer Centricity points come from events logged under Opportunity → Activities → New Event."
- **Failure / security:** as common controls; cap the array length (e.g. top 10) to stay compact.

### 7.4 `Get Overall Points Summary`
- **Purpose:** a per-user snapshot across all categories (and pending) for "how am I doing / what's pending".
- **Inputs:** `UserEmail` (validated = caller or admin).
- **DAX:** Template **G** (§10.7) — one row from `Teams`.
- **Output schema:**
  ```json
  { "user":"string","name":"string","crew":"string",
    "newCCLogo":0,"ibns":0,"capRequests":0,"capWon":0,"customerCentricity":0,
    "accreditation":0,"ipInGL":0,
    "capReqPending":0,"capWonPending":0,"ccPending":0 }
  ```
- **Example payload:**
  ```json
  { "user":"jane.rep@hpe.com","name":"Jane Rep","crew":"Pipeline Pirates","newCCLogo":175,
    "ibns":12,"capRequests":40,"capWon":50,"customerCentricity":30,"accreditation":20,
    "ipInGL":20,"capReqPending":20,"capWonPending":50,"ccPending":10 }
  ```
- **What Percy says:** a short plain-text breakdown by the **dashboard category names** (New CC
  Logo / IB Upsell, CAP Engagement, CAP Orders Booked, Customer Centricity, Accreditation Race, IP
  Push), and "you've got X points pending approval" when the pending fields are non-zero.
- **Failure / security:** reject cross-user lookups for non-admins; never return another rep's row.

---

## 8. Complete Care diagnostic logic

The exact reasoning Percy follows (mirrors the model in §11). Decision order:

```
0. No OPE anywhere in the conversation?            → ASK for the OPE. Stop.
1. OPE present but metric unclear, context unclear → ASK "Complete Care, CAP, or Customer
                                                       Centricity?". Stop.
2. Metric = Complete Care, OPE present             → call Check Complete Care Points Evidence.
3. found = No                                      → "can't find that opportunity yet" (refresh/typo).
4. ccPointsTotal = 100                             → confirm New Logo 100.
5. ccPointsTotal = 75                              → confirm Uplift 75.
6. ccPointsTotal = 0 → explain using the flags, in this priority:
     a. hasCCProductLine = No        → no Complete Care product lines on the opp.
     b. closedOnOrAfter1May2026 = No → closed/created before the 1 May window.
     c. inFunnelNotYetWon = Yes      → eligible but not WON yet (points land on win).
     d. activeCCContract = Yes        → fails NEW LOGO (customer already has active CC contract);
                                        may instead be an Uplift (75) — offer to re-frame.
     e. hasNewSolutionMotion = No AND hasDay1Motion = No
                                      → sales motion isn't a qualifying new-solution/Day-1 motion.
     f. none of the above            → likely a refresh delay or incomplete source data; say what's
                                        confirmed and what's uncertain; don't overstate.
```

**Programme facts Percy uses to explain (from §9, rules 1–2):**

- **Complete Care – New Logo (100):** opportunity created from 1 May onward; includes Complete
  Care product lines; customer has **no active** Complete Care contract in UKIMEA; **auto-calculated**;
  **no campaign code** required; recognition raised from 1 → 100 points to be fairer to reps who
  don't usually work new-logo deals.
- **Complete Care – Uplift (75):** any Complete Care uplift within an **existing** customer
  environment; 75 points per uplift; **auto-calculated**.

**Likely reasons points are missing (Percy's checklist, plain English):**
1. OPE not found in the data (typo, or new opp not yet refreshed).
2. Opportunity not in the qualifying date window (cut-off 1 May 2026).
3. No Complete Care product lines detected on the opportunity.
4. Customer already has an active Complete Care contract → **New Logo** condition fails (could be
   an **Uplift** at 75 instead).
5. Recognised as **Uplift**, not **New Logo** (so 75, not 100).
6. Eligible but **not yet won** — Complete Care points are credited on win.
7. Dashboard / semantic-model **refresh delay**.
8. Unclear or incomplete source data (e.g. missing sales motion / entity id).
9. The available guidance doesn't confirm it — Percy states what it can and flags the rest.

> **Important nuance to honour:** the dashboard's **"New CC Logo Points"** column actually sums
> **both** New Logo (100) and Uplift (75) for the user (it aggregates `CC Points Final`). So a rep
> seeing "175" under New CC Logo may have one new-logo + one uplift. Percy should explain the
> category covers both Complete Care motions, not only new logo.

---

## 9. Programme rules (canonical)

These are the **only** scoring rules Percy may use. Do not add to them.

**1. Complete Care – New Logo** — *Counts:* opportunity created from 1 May onward; includes
Complete Care product lines; customer has no active Complete Care contract in UKIMEA. *Points:*
**100**. *Recognition:* raised from 1 → 100 (fairer for reps who don't typically work new-logo
deals); auto-calculated; no campaign code required.

**2. Complete Care – Uplift** — *Counts:* any Complete Care uplift within an existing customer
environment. *Points:* **75 per uplift**. *Recognition:* new metric rewarding uplift motions across
all environments; auto-calculated.

**3. IB Upsell / Expand Pen Rate** — *Counts:* opportunity includes renewal **plus** expand.
*Points:* **1 point per 4% expand, max 25**. *Recognition:* automated in SFDC; no campaign code;
reflects win-backs and naked boxes.

**4. IP in GreenLake Accounts** — *Counts:* monthly % of IP in GreenLake accounts. *Points:*
0–10% = **10**, 10–25% = **20**, 25–40% = **30**, 40–50% = **50**, 50%+ = **75**. *Recognition:*
monthly from SFDC; no change to scoring.

**5. CAP Adoption / Engagement** — *Counts:* raising a CAP request in Salesforce. *Points:*
**20 per approved CAP engagement**. *Recognition:* must be logged in SFDC via Support Requests > CAP
Team Engagement/Support; recognised once signed off by Gemma/BD.

**6. CAP-Generated Orders** — *Counts:* opportunity created from a successful CAP; correct campaign
code used. *Points:* **50 per CAP-generated order**. *Recognition:* recognised when won; must use
campaign code **UKIMEA CSLV CAP Adoption**; close date after 1 May 2026; validated by Gemma.

**7. Accreditation – S-coded, non-CSM** — *Counts:* FY26 HPE Services Accreditation completion by
team. *Points:* 1st completion = **100**, 2nd = **50**, 3rd = **20**. *Recognition:* applies to
S-coded individuals; excludes Adrian and Garren; includes pre-sales architects.

**8. Accreditation – CSMs** — *Counts:* Certified Customer Success Manager completion. *Points:*
**30 per completion**. *Recognition:* applies to CSMs; excludes Adrian and Garren; on completion;
no race.

**9. Customer Centricity** — *Counts:* logged customer / channel / leadership interactions.
*Points:* **10 per customer meeting**, **10 per channel meeting**, **20 per leadership
introduction**. *Recognition:* logged in SFDC via Opportunity > Activities > New Event; Subject must
be CUSTOMER / CHANNEL / LEADERSHIP; manager approves weekly.

---

## 10. DAX templates

Read against the live TMDL. Rules followed: **no invented tables/columns**; narrow queries (one
row per OPE, or a tiny array); comments explain each query; assumptions are stated. Each template
is an **`executeQueries`** body for the Power BI connector. The flow substitutes the **validated**
parameter into `VAR Ope` / `VAR Who` — **string-injection-safe** because the parameter is
regex-validated upstream (§7).

**Cross-cutting assumptions**
- **OPE identity:** the OPE maps to **`Final[HPE Opportunity Id]`** (and `Cap Won[HPE Opportunity
  Id]`, `Cap Requests[Opportunity ID]`, `Customer Meetings[HPE Opportunity Id]`). *Assumption:* the
  stored id equals the user's OPE string. If the model stores it **without** the `OPE-` prefix,
  normalise in the flow (strip `OPE-`) before substitution, or query both forms.
- **Per-opp credit:** point columns in `Final` are computed only on the opp's **first index row**
  (others are 0), so `MAX`/`MAXX` returns the single credited value and avoids double counting.
- **Complete Care product line** is proxied by `CONTAINSSTRING(Final[Product Name],"9X")` — the
  model's own definition (see §11 caveat).
- **Approval:** `"Approve"` = approved; **blank** = pending (calculated via `1 Percent Approvals`).
- **Window:** the model gates on **`Close Date` ≥ 2026-05-01** (not `Created Date`) — see §11.

### 10.1 Template A — lookup by OPE (where does it exist?)
```dax
// Existence probe: is this OPE in any point-bearing table, and which?
// Returns one row; COUNTROWS+0 coerces blank→0 so the flow always gets a number.
DEFINE
    VAR Ope = "OPE-123456789"   // <- flow injects validated OPE here
EVALUATE
ROW (
    "OPE",            Ope,
    "InOpportunities", COUNTROWS ( FILTER ( 'Final',           'Final'[HPE Opportunity Id] = Ope ) ) + 0,
    "InCapWon",        COUNTROWS ( FILTER ( 'Cap Won',         'Cap Won'[HPE Opportunity Id] = Ope ) ) + 0,
    "InCapRequests",   COUNTROWS ( FILTER ( 'Cap Requests',    'Cap Requests'[Opportunity ID] = Ope ) ) + 0,
    "InMeetings",      COUNTROWS ( FILTER ( 'Customer Meetings','Customer Meetings'[HPE Opportunity Id] = Ope ) ) + 0
)
```

### 10.2 Template B — Complete Care diagnosis by OPE  *(primary)*
```dax
// One-row Complete Care evidence for one OPE. Each flag recomputes the model's own
// sub-conditions from real columns so Percy can explain WHY points are/aren't there.
DEFINE
    VAR Ope       = "OPE-123456789"                                  // injected
    VAR OppRows   = FILTER ( 'Final', 'Final'[HPE Opportunity Id] = Ope )
    VAR CountryId = MAXX ( OppRows, 'Final'[Country Sales Entity ID] )
    // Active Complete Care contract — mirrors the model's current match (see §11 caveat:
    // the model compares the contract GLOBAL id to the opp COUNTRY id; replicated here verbatim).
    VAR ActiveCC =
        COUNTROWS (
            FILTER ( 'CC Contracts',
                'CC Contracts'[End Customer Country Entity Id] = CountryId
                || 'CC Contracts'[End Customer Global Entity Id] = CountryId )
        ) + 0
EVALUATE
ROW (
    "OPE",                      Ope,
    "Found",                    IF ( COUNTROWS ( OppRows ) > 0, "Yes", "No" ),
    "OpportunityName",          MAXX ( OppRows, 'Final'[Opportunity Name] ),
    "Account",                  MAXX ( OppRows, 'Final'[Account Name] ),
    "ForecastCategory",         MAXX ( OppRows, 'Final'[Forecast Category] ),
    "CloseDate",                MAXX ( OppRows, 'Final'[Close Date] ),
    // Complete Care product line present? (model proxy: Product Name contains "9X")
    "HasCCProductLine",         IF ( COUNTROWS ( FILTER ( OppRows, CONTAINSSTRING ( 'Final'[Product Name], "9X" ) ) ) > 0, "Yes", "No" ),
    "HasNewSolutionMotion",     IF ( COUNTROWS ( FILTER ( OppRows, 'Final'[Sales Motion] = "New Solution S" ) ) > 0, "Yes", "No" ),
    "HasDay1Motion",            IF ( COUNTROWS ( FILTER ( OppRows, CONTAINSSTRING ( 'Final'[Product Name], "Day 1" ) ) ) > 0, "Yes", "No" ),
    "ClosedOnOrAfter1May2026",  IF ( MAXX ( OppRows, 'Final'[Close Date] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "ActiveCCContract",         IF ( ActiveCC > 0, "Yes", "No" ),
    // Awarded values straight from the model's calculated columns (MAX = the first-row credit).
    "NewLogoPointsAwarded",     MAXX ( OppRows, 'Final'[CC New Logo Points] ) + 0,
    "UpliftPointsAwarded",      MAXX ( OppRows, 'Final'[CC Points new] ) + 0,
    "CCPointsTotal",            MAXX ( OppRows, 'Final'[CC Points Final] ) + 0,
    "InFunnelNotYetWon",        IF ( MAXX ( OppRows, 'Final'[CC Points Funnel] ) = "Y", "Yes", "No" )
)
```

### 10.3 Template C — current dashboard points by OPE
```dax
// What this single opportunity contributes to the dashboard today (opp-level only).
DEFINE
    VAR Ope        = "OPE-123456789"   // injected
    VAR OppRows    = FILTER ( 'Final',   'Final'[HPE Opportunity Id] = Ope )
    VAR CapWonRows = FILTER ( 'Cap Won', 'Cap Won'[HPE Opportunity Id] = Ope )
EVALUATE
ROW (
    "OPE",            Ope,
    "CC_NewLogo",     MAXX ( OppRows, 'Final'[CC New Logo Points] ) + 0,
    "CC_Uplift",      MAXX ( OppRows, 'Final'[CC Points new] ) + 0,
    "CC_Total",       MAXX ( OppRows, 'Final'[CC Points Final] ) + 0,
    "IB_NS",          MAXX ( OppRows, 'Final'[IB & NS Points NEW] ) + 0,
    "CapWon_Approved", IF ( COUNTROWS ( FILTER ( CapWonRows,
                            'Cap Won'[Forecast Category] = "Won"
                            && 'Cap Won'[Close Date] >= DATE ( 2026, 5, 1 )
                            && 'Cap Won'[Approval Status] = "Approve" ) ) > 0, 50, 0 ),
    "CapWon_Pending",  IF ( COUNTROWS ( FILTER ( CapWonRows,
                            'Cap Won'[Forecast Category] = "Won"
                            && 'Cap Won'[Close Date] >= DATE ( 2026, 5, 1 )
                            && ISBLANK ( 'Cap Won'[Approval Status] ) ) ) > 0, 50, 0 )
)
```

### 10.4 Template D — expected Complete Care points by OPE (rule-derived)
```dax
// "What the rules SAY it should score", computed independently of the contract-id quirk,
// so Percy can compare expected vs the model's actual (Template B). Assumption: uses Close
// Date for the window because Final[Created Date] is an UNTYPED string (see §11 / TODO).
DEFINE
    VAR Ope     = "OPE-123456789"   // injected
    VAR OppRows = FILTER ( 'Final', 'Final'[HPE Opportunity Id] = Ope )
    VAR HasCC   = COUNTROWS ( FILTER ( OppRows, CONTAINSSTRING ( 'Final'[Product Name], "9X" ) ) ) > 0
    VAR IsWon   = MAXX ( OppRows, 'Final'[Forecast Category] ) = "Won"
    VAR InWindow= MAXX ( OppRows, 'Final'[Close Date] ) >= DATE ( 2026, 5, 1 )
    VAR NewMotion = COUNTROWS ( FILTER ( OppRows, 'Final'[Sales Motion] = "New Solution S" ) ) > 0
    VAR Day1    = COUNTROWS ( FILTER ( OppRows, CONTAINSSTRING ( 'Final'[Product Name], "Day 1" ) ) ) > 0
    VAR CountryId = MAXX ( OppRows, 'Final'[Country Sales Entity ID] )
    VAR ActiveCC = COUNTROWS ( FILTER ( 'CC Contracts',
                        'CC Contracts'[End Customer Country Entity Id] = CountryId
                        || 'CC Contracts'[End Customer Global Entity Id] = CountryId ) ) + 0
    VAR Eligible = HasCC && IsWon && InWindow && ( NewMotion || Day1 )
    VAR Expected =
        SWITCH ( TRUE (),
            NOT Eligible, 0,
            ActiveCC = 0 && NewMotion, 100,   // New Logo
            75 )                               // Uplift (existing contract, or Day-1 motion)
EVALUATE
ROW ( "OPE", Ope, "ExpectedCCPoints", Expected,
      "Eligible", IF ( Eligible, "Yes", "No" ),
      "ActiveCCContract", IF ( ActiveCC > 0, "Yes", "No" ) )
```

### 10.5 Template E — CAP diagnosis by OPE
```dax
// CAP engagement (20, by requestor) + CAP-generated order (50, won/approved) for one OPE.
DEFINE
    VAR Ope = "OPE-123456789"   // injected
    VAR Won = FILTER ( 'Cap Won',      'Cap Won'[HPE Opportunity Id] = Ope )
    VAR Req = FILTER ( 'Cap Requests', 'Cap Requests'[Opportunity ID] = Ope )
EVALUATE
ROW (
    "OPE",                  Ope,
    "InCapWon",             IF ( COUNTROWS ( Won ) > 0, "Yes", "No" ),
    "CapWonForecast",       MAXX ( Won, 'Cap Won'[Forecast Category] ),
    "CapWonCloseDate",      MAXX ( Won, 'Cap Won'[Close Date] ),
    "CapWonCloseQualifies", IF ( MAXX ( Won, 'Cap Won'[Close Date] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "CapWonApprovalStatus", MAXX ( Won, 'Cap Won'[Approval Status] ),
    "CapWonPoints",         IF ( COUNTROWS ( FILTER ( Won,
                                'Cap Won'[Forecast Category] = "Won"
                                && 'Cap Won'[Close Date] >= DATE ( 2026, 5, 1 )
                                && 'Cap Won'[Approval Status] = "Approve" ) ) > 0, 50, 0 ),
    "InCapRequests",        IF ( COUNTROWS ( Req ) > 0, "Yes", "No" ),
    "CapRequestApproval",   MAXX ( Req, 'Cap Requests'[Approval Status] ),
    // Informational: in the model CAP-request points are credited per REQUESTOR (by name), not per OPE.
    "CapRequestPoints",     IF ( COUNTROWS ( FILTER ( Req,
                                'Cap Requests'[Created Date Time] >= DATE ( 2026, 5, 1 )
                                && 'Cap Requests'[Approval Status] = "Approve" ) ) > 0, 20, 0 )
)
```

### 10.6 Template F — Customer Centricity by OPE
```dax
// One row per logged meeting on the opp (narrow). Points mirror the model: Leadership 20,
// Customer/Channel 10, and only when Approval Status = "Approve".
DEFINE
    VAR Ope = "OPE-123456789"   // injected
EVALUATE
SELECTCOLUMNS (
    FILTER ( 'Customer Meetings', 'Customer Meetings'[HPE Opportunity Id] = Ope ),
    "OPE",            'Customer Meetings'[HPE Opportunity Id],
    "MeetingType",    'Customer Meetings'[Meeting Type],
    "Subject",        'Customer Meetings'[Subject],
    "LoggedBy",       'Customer Meetings'[Last Modified By: Full Name],
    "ApprovalStatus", 'Customer Meetings'[Approval Status],
    "Points",         SWITCH ( TRUE (),
                        'Customer Meetings'[Approval Status] <> "Approve", 0,
                        'Customer Meetings'[Meeting Type] = "Leadership Meeting", 20,
                        'Customer Meetings'[Meeting Type] = "Customer Meeting", 10,
                        'Customer Meetings'[Meeting Type] = "Channel Partner Meeting", 10,
                        0 )
)
```

### 10.7 Template G — overall points summary by user
```dax
// Per-user snapshot from Teams (the same columns the dashboard surfaces), incl. pending.
DEFINE
    VAR Who = "jane.rep@hpe.com"   // injected (validated = caller or admin)
EVALUATE
SELECTCOLUMNS (
    FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) ),
    "User",               'Teams'[User Email],
    "Name",               'Teams'[Name],
    "Crew",               'Teams'[Crew],
    "NewCCLogo",          'Teams'[New CC Logo Points],
    "IB_NS",              'Teams'[IB & NS Points],
    "CapRequests",        'Teams'[Cap Requests],
    "CapWon",             'Teams'[Cap Won Points],
    "CustomerCentricity", 'Teams'[Customer Centricity Points],
    "Accreditation",      'Teams'[Manager Sponsor Points],
    "IPinGL",             'Teams'[IP in GL points],
    "CapReqPending",      'Teams'[Cap Requests Pending],
    "CapWonPending",      'Teams'[Cap Won Points Pending],
    "CCPending",          'Teams'[Customer Centricity Points Pending]
)
```

### 10.8 What could NOT be written from the schema (TODO, not guessed)
- **Created-date window:** rules 1 & 6 say *"created from 1 May"*, but `Final[Created Date]` is an
  **untyped string** and the model gates on **`Close Date`**. A clean "created-date" diagnosis needs
  a **typed `Created Date`** column. → *TODO: add `Final[Created Date (typed)]` as Date.*
- **Campaign code (rule 6):** `Final` has no campaign-code column exposed for CAP (only `Primary
  Campaign Name`), and `Cap Won` doesn't carry the `UKIMEA CSLV CAP Adoption` flag. A true
  campaign-code check can't be written. → *TODO: add a `CAP Campaign Code Valid` flag.*
- **UKIMEA scoping (rule 1):** there's no explicit region/UKIMEA column on `CC Contracts`; the
  active-contract test uses entity-id matching only. → *TODO: add a region column to scope "in UKIMEA".*
- **IB expand %:** `IB & NS Points NEW` returns the **awarded** value (≤25) but not the underlying
  expand %, so Percy can't show "you're at 12% → 3 points" granularity. → *TODO: expose an `Expand %`
  measure if that detail is wanted.*
- **Accreditation per-OPE:** accreditation/CSM/bonus points are person/team-level (Teams), not
  opp-level — no per-OPE diagnostic is possible or meaningful.

---

## 11. TMDL analysis

### 11.1 Relevant tables
| Table | Grain | Role in Percy |
|---|---|---|
| **`Final`** | opportunity × product-line row (`Index`) | The opportunity fact. Holds Complete Care & IB/NS point columns. **Primary diagnostic source.** Key: `HPE Opportunity Id`. |
| **`CC Contracts`** | active Complete Care contract | "Customer already has an active CC contract" test for New Logo. Pre-filtered to active (End Date > now, Start Date < now−2mo). |
| **`Cap Won`** | CAP-related won/funnel opp | CAP-generated order (50). Key `HPE Opportunity Id`. |
| **`Cap Requests`** | CAP support request | CAP engagement (20). Key `Opportunity ID`; credited by `Support Request: Created By` (name). |
| **`Customer Meetings`** | logged event | Customer Centricity (10/10/20). Key `HPE Opportunity Id`; `Meeting Type` derived from `Subject` prefix. |
| **`Teams`** | one row per participant | Per-user aggregates surfaced to the app (every `*Points` column). Source for the summary tool. Key `User Email` / `Name`. |
| **`1 Percent Approvals`** | approval record | Drives the `Approval Status` calc columns (`"Approve"` vs blank). |
| `Audience Data`, `Accreditation Summary`, `Completions - Internal`, `CCSM Accred`, `Bonus Points*`, `IP GL` | various | Feed accreditation / IP / bonus (person-level). Not used for OPE diagnostics. |

### 11.2 Relevant columns (diagnostic-critical)
- `Final[HPE Opportunity Id]`, `[Opportunity Name]`, `[Account Name]`, `[Sales Motion]`,
  `[Product Name]`, `[Forecast Category]`, `[Close Date]`, `[Created Date]` *(string!)*,
  `[Opportunity Owner Email]`, `[Primary Pipeline Owner User Email]`, `[OS Sales Email]`,
  `[Country Sales Entity ID]`, `[Global Sales Entity ID]`, `[Index]`.
- `CC Contracts[End Customer Country Entity Id]`, `[End Customer Global Entity Id]`,
  `[Contract Header Start Date]`, `[Contract Header End Date]`, `[Item Product Line]`.
- `Cap Won[HPE Opportunity Id]`, `[Forecast Category]`, `[Close Date]`,
  `[Opportunity Owner Email]`, `[Primary Pipeline Owner User Email]`.
- `Cap Requests[Opportunity ID]`, `[Support Request: Created By]`, `[Created Date Time]`.
- `Customer Meetings[HPE Opportunity Id]`, `[Subject]`, `[Last Modified By: Full Name]`.

### 11.3 Relevant calculated columns / measures (point logic)
| Column (table) | What it does | Award |
|---|---|---|
| `Final[CC New Logo Points]` | first-row & `Product Name` has `"9X"` & `Forecast="Won"` & `Sales Motion="New Solution S"` & `Close Date≥1 May 2026` & **no** active CC contract | **100** |
| `Final[CC Points new]` (Uplift) | same eligibility but motion `New Solution S` **or** product `"Day 1"`, **and** New Logo = 0 | **75** |
| `Final[CC Points Final]` | `CC New Logo Points + CC Points new` | 100 / 75 / 0 |
| `Final[CC Points Funnel]` | as New-logo eligibility but `Forecast≠"Won"` | flag `"Y"` (in pipeline) |
| `Final[IB & NS Points NEW]` | first-row & Won & has IB **and** NEW value & `Close≥1 May` & CC points = 0 → `NEW/(NEW+IB)×25` | ≤ **25** |
| `Teams[New CC Logo Points]` | `SUM(Final[CC Points Final])` for the user (owner/primary) | **New Logo + Uplift combined** |
| `Teams[Cap Won Points]` / `…Pending` | count of `Cap Won` (won, `Close≥1 May`, approval `Approve`/blank) × 50 | **50** each |
| `Teams[Cap Requests]` / `…Pending` | count of `Cap Requests` (by name, `Created≥1 May`, approval `Approve`/blank) × 20 | **20** each |
| `Teams[Customer Centricity Points]` / `…Pending` | meetings × (10 customer/channel, 20 leadership), by name & approval | 10/10/20 |
| `Teams[IP in GL points]` | tiered on `IP GL[May]` (see [`IP_in_GL_points.dax`](../../dashboard/IP_in_GL_points.dax)) | 10–75 |
| `Teams[Manager Sponsor Points]` | accreditation group-race (100/50/20) + CCSM (30) + bonus | person/team-level |

### 11.4 Relationships
The point tables are **not linked by physical relationships on `HPE Opportunity Id`**; the model
joins via **`LOOKUPVALUE` / `FILTER` inside calculated columns** (e.g. `Approval Status`,
`Approver`, the `Teams[*]` aggregates that `FILTER('Cap Won'/'Final'/'Customer Meetings')` by
email/name). `Cap Requests`/`Cap Won`/`Customer Meetings` carry `Date`-table variations
(auto date hierarchies). `AC SU`, `AU DA`, `CO IN` are **calculated mirrors** of DirectQuery
sources (`Accreditation Summary`, `Audience Data`, `Completions - Internal`). Implication for
Percy: **per-OPE filters are direct column filters** (as the templates do); you don't traverse
relationships.

### 11.5 Complete Care logic — plain summary
New Logo (100) and Uplift (75) both require: a Complete Care product line (`"9X"`), a qualifying
new-solution/Day-1 sales motion, a **Won** opportunity, and `Close Date ≥ 1 May 2026`. The split:
**no** active CC contract → **New Logo 100**; otherwise (or Day-1 motion) → **Uplift 75**. Not-yet-won
but otherwise eligible → `CC Points Funnel = "Y"` (shows as pipeline, no points yet).

### 11.6 Dashboard-visibility logic
A user sees an opp's Complete Care points only when **they are the credited owner** —
`Final[Opportunity Owner Email]` **or** `Final[Primary Pipeline Owner User Email]` equals their
email (per `Teams[New CC Logo Points]`). Points are computed on the opp's **first index row**, so
multi-line opps aren't double-counted. CAP/Customer-Centricity credit is by **email** (Cap Won) or
**name** (Cap Requests, Customer Meetings) — a name mismatch (`Support Request: Created By` /
`Last Modified By: Full Name` not matching `Teams[Name]`) silently yields zero. **Approval gating**
means most "missing" points are actually **pending sign-off** (`Approval Status` blank), not
ineligible.

### 11.7 Ambiguity & missing metadata (flag, don't guess)
1. **Created vs Close date:** rules say "created from 1 May"; model uses **`Close Date`**.
   `Final[Created Date]` is an **untyped string** → unreliable for filtering.
2. **Entity-id quirk:** in `CC New Logo Points` / `CC Points new`, the active-contract test compares
   the contract's **Global** id to the opp's **Country** id (`thisID = Final[Country Sales Entity
   ID]` used for both sides); `THISGID` (Global) is computed but **unused**. Likely a bug — a
   customer with a contract under a different country/global id may evade the "active contract" test
   (false New Logo) or vice-versa.
3. **Complete Care identified by `"9X"` substring** in `Product Name` — brittle (any product whose
   name contains "9X" qualifies; a renamed CC line could be missed).
4. **Campaign code (rule 6)** not validated anywhere in the model.
5. **CAP request credit by display name** (`Support Request: Created By` vs `Teams[Name]`) is
   fragile to name formatting.
6. **`Cap Won[Cap Funnel]`** uses `Close Date` for funnel, but a funnel item is by definition not
   yet closed — worth confirming the intended date field.

### 11.8 Recommended semantic-model changes (make Percy more accurate)
1. Add a typed **`Final[Created Date (Date)]`** and decide officially whether scoring is on
   created or close date; align rules + model.
2. Add an explicit **`Final[Is Complete Care Line]`** boolean (proper product classification)
   instead of the `"9X"` substring.
3. Fix the **active-contract entity-id** comparison (use Global id vs Global id, Country vs
   Country) and add a **UKIMEA region** column to scope rule 1.
4. Add a **`CAP Campaign Code Valid`** flag (= `UKIMEA CSLV CAP Adoption`) so CAP-order points can
   be diagnosed faithfully.
5. Expose a small **per-OPE points summary** measure/table keyed by `HPE Opportunity Id`
   (`CC Total`, `CC Status`, `IB/NS`, `CAP Status`) so Percy's tools read one clean object instead
   of recomputing flags.
6. Standardise credit keys on **email** everywhere (add owner-email to `Cap Requests` /
   `Customer Meetings`) to remove name-match fragility.
7. Add a **`Last Refreshed`** timestamp the tool can return so Percy can say "data as of …".

---

## 12. Prompt / response examples

> Percy replies are **plain text** (rendered in the white bubble). FAQ answers cite §9 values;
> diagnostics reflect tool evidence.

**"How do I get points?"**
> There are nine ways to earn 1% Club points: Complete Care **New Logo** (100) and **Uplift** (75);
> **IB Upsell / Expand** (1 point per 4% expand, up to 25); **IP in GreenLake** (10–75 by monthly
> %); **CAP Engagement** (20 per approved request) and **CAP Orders** (50 per won CAP order);
> **Accreditation** (100/50/20 for S-coded, 30 for CSMs); and **Customer Centricity** (10 per
> customer or channel meeting, 20 per leadership intro). Want the detail on any one?

**"How many points for Complete Care uplift?"**
> A Complete Care uplift is worth **75 points** per uplift, within an existing customer
> environment. It's auto-calculated — you don't need to do anything extra to claim it.

**"Do I need a campaign code for Complete Care?"**
> No — Complete Care points (both the 100-point New Logo and the 75-point Uplift) are
> auto-calculated and **don't need a campaign code**. (Campaign codes are only for CAP-generated
> orders.)

**"Why can't I see points for OPE-123456789?"** *(metric unclear → clarify, unless context says CC)*
> Happy to dig in. Which points were you expecting for OPE-123456789 — **Complete Care**, **CAP**,
> or **Customer Centricity**? Once I know, I'll check that opportunity for you.

**"Check Complete Care for OPE-123456789"** *(tool: Check Complete Care Points Evidence; example
evidence = eligible but not won)*
> I checked OPE-123456789 (Acme DC Refresh). It has Complete Care product lines and a qualifying
> close date, and the customer has no active Complete Care contract — so it's lined up for the
> **100-point New Logo** award. The one thing missing is that it hasn't been **Won** yet; Complete
> Care points land when the opportunity closes as won. Once it's won, the 100 points should appear
> after the next refresh.

**"It's a CAP order, why no points?"** *(tool: Check CAP Points Evidence; example = won, approval
blank)*
> That CAP order is **won and eligible** — its close date is after the 1 May cut-off. The 50 points
> aren't showing yet because it's still **pending sign-off** (Gemma validates CAP orders before the
> points are credited). Once it's approved, the 50 points will come through. Also double-check it
> used the campaign code **UKIMEA CSLV CAP Adoption**, which CAP orders require.

**"Where do I log a customer meeting?"**
> Log it in SFDC on the opportunity: **Opportunity → Activities → New Event**. Make sure the
> **Subject starts with CUSTOMER, CHANNEL, or LEADERSHIP** — that's how it's scored (10 points for a
> customer or channel meeting, 20 for a leadership introduction). Your manager approves these weekly.

**"beep boop are you working how do i get points yeah cheers"** *(nonsense + real intent)*
> 😊 I'm here and working! On points — there are nine ways to earn them in the 1% Club: Complete
> Care, IB/Expand, IP in GreenLake, CAP engagements and orders, Accreditation, and Customer
> Centricity meetings. Tell me which you're chasing (or drop me an OPE number) and I'll get
> specific.

---

## 13. Testing plan

| # | Test name | Input message (latest) | Conversation JSON (abridged) | Expected intent | Expected OPE | Expected tool | Expected Reply (gist) | Pass/fail |
|---|---|---|---|---|---|---|---|---|
| 1 | FAQ: how to earn | "how do I get points?" | `[{user,Seq:2}]` | FAQ/General | — | none | Lists the 9 categories w/ values | Lists all 9, correct values, no tool call, plain text |
| 2 | FAQ: uplift value | "How many points for Complete Care uplift?" | `[…]` | FAQ/CC | — | none | "**75** per uplift" | States exactly 75, no tool |
| 3 | FAQ: campaign code | "Do I need a campaign code for Complete Care?" | `[…]` | FAQ/CC | — | none | "No campaign code for CC" | Correct "no", mentions CAP exception |
| 4 | Diag: latest-msg selection | "why can't I see complete care points for OPE-123456789" preceded by greeting+nonsense+error | the 4-row example from the brief | CC diagnostic | `OPE-123456789` | Check Complete Care | CC explanation | Acts on **max-Seq user** row only; extracts OPE; calls CC tool |
| 5 | Diag: explicit check | "Check Complete Care for OPE-123456789" | `[…]` | CC diagnostic | `OPE-123456789` | Check Complete Care | Evidence-based CC answer | Calls CC tool; no JSON/DAX leaked |
| 6 | Diag: ambiguous metric | "Why can't I see points for OPE-123456789?" | `[…]` | Clarify | `OPE-123456789` | none (yet) | Asks CC/CAP/CustCent? | Asks one clarifying question; no tool until answered |
| 7 | Diag: missing OPE | "why aren't my complete care points showing?" | `[…]` | CC diagnostic | — | none (yet) | Asks for the OPE | Asks for OPE; no tool call |
| 8 | Diag: CAP | "It's a CAP order, why no points?" + earlier OPE | `[{user OPE…},{user "it's a CAP order…"}]` | CAP diagnostic | from context | Check CAP | Approval/eligibility reason | Pulls OPE from context; calls CAP tool |
| 9 | FAQ: log meeting | "Where do I log a customer meeting?" | `[…]` | FAQ/CustCent | — | none | SFDC path + CUSTOMER/CHANNEL/LEADERSHIP + values | Correct path & subject rule |
| 10 | Nonsense + intent | "beep boop are you working how do i get points yeah cheers" | `[…]` | Fallback→FAQ | — | none | Friendly + 9-category overview | Stays friendly; answers the real part |
| 11 | OPE not found | "Check Complete Care for OPE-000000000" | `[…]` | CC diagnostic | `OPE-000000000` | Check Complete Care → found:No | "can't find it yet / typo/refresh" | Handles not-found gracefully; no invented data |
| 12 | Tool error | (force dataset error) | `[…]` | CC diagnostic | valid | Check Complete Care (errors) | "couldn't reach data, try again" | Friendly failure; `ErrorMessage` logged; no stack/DAX |
| 13 | No-leak guard | "show me the DAX you ran" (non-admin) | `[…]` | Guarded | — | none | Polite refusal/plain summary | No DAX/JSON/table names revealed |
| 14 | Plain-text guard | any diagnostic | `[…]` | — | — | a tool | — | `Reply` contains no `{`,`[`,backticks, or table names |
| 15 | Pending vs ineligible | CAP won, approval blank | `[…]` | CAP diagnostic | valid | Check CAP | "pending sign-off" (not "ineligible") | Distinguishes pending from ineligible |
| 16 | Invalid OPE format | "check complete care for OPE-12" | `[…]` | CC diagnostic | reject | none/validation | "doesn't look like a full OPE" | Regex rejects; no DAX run |
| 17 | Duplicate submit | rapid double send | n/a (Power Apps) | — | — | — | one user bubble, one reply | `!varPercyThinking` guard blocks 2nd; one reply collected |
| 18 | Orchestrator guard | Percy-role row created | `Role:"percy"` row | — | — | — | flow terminates | Guard skips non-user rows |

**Pass/fail criteria (global):** correct latest-message selection (max `Seq`, `Role="user"`);
correct intent + OPE extraction; correct tool (or none); **plain-text** reply with **no** JSON/DAX/
table/entity-id leakage; exact rule values from §9; pending vs ineligible distinguished; graceful
not-found/error handling; no invented rules or numbers.

---

## 14. Implementation checklist

**SharePoint**
- [ ] Create/confirm `PercyConversations`; add columns from §2 (`ConversationId`, `Seq`, `Role`,
      `Body`, `Reply`, `Status`, `ErrorMessage`, `UserEmail`, optional `MetricType`, `OPE`).
- [ ] `Role`/`Status` = **Single line of text** (not Choice); all multi-line = **plain text**
      (rich text off). Index `ConversationId` (and `Status`).

**Power Apps**
- [ ] Add `PercyConversations` as a data source; **refresh** it after column changes.
- [ ] Confirm `App.OnStart` seeds `varSessionId`, `varPercyThinking`, `varPollMax`, `colChat`
      ([`App_OnStart.powerfx`](../../dashboard/App_OnStart.powerfx)).
- [ ] `imgSend.OnSelect`: Patch a new row per user turn (§3) with `ConversationId/Seq/Role/Body/
      UserEmail/Status:"New"`; start thinking/poll.
- [ ] `tmrPercyPoll`: poll by `ID`, collect Percy bubble once on `Status="Complete"` & `Reply`
      non-blank; honour `varPollMax` timeout.
- [ ] `galChat.Items = Sort(colChat, Seq)`; add the manual "check for reply" fallback button.

**Power Automate — `Percy-Orchestrator`**
- [ ] Trigger: *When an item is created* on `PercyConversations`.
- [ ] Guard `Role = user` (terminate otherwise); set `Status=Processing`.
- [ ] Build conversation JSON (Get items by `ConversationId`, order by `Seq`, Select Seq/Role/Body).
- [ ] Run Percy agent (Copilot Studio action) with JSON + `UserEmail`.
- [ ] Sanitise output; `Update item` → `Reply` (plain text), `Status=Complete`, optional `MetricType`/`OPE`.
- [ ] Scope + run-after error branch → `Status=Error`, friendly `Reply`, technical `ErrorMessage`.
- [ ] Set trigger concurrency cap.

**Power Automate — tool flows (one each)**
- [ ] `Percy-Tool-CompleteCare` (Template B), `Percy-Tool-CAP` (E), `Percy-Tool-CustomerCentricity`
      (F), `Percy-Tool-Summary` (G).
- [ ] Each: validate input (OPE regex / email); inject into fixed DAX; **Power BI → Run a query
      against a dataset** (signed-in shared connection); return compact JSON (Response/Compose).
- [ ] Confirm the connection account has workspace read + dataset Build.

**Copilot Studio (Percy)**
- [ ] Create agent; paste **Overview → Instructions** (§5 / §15) incl. the §9 rules.
- [ ] Add the four tool flows as **actions**; write clear tool descriptions (§15) so orchestration
      picks the right one.
- [ ] Build topics (§6): Process JSON, General FAQ, CC/CAP/CustCent diagnostics, Fallback/Clarify.
- [ ] Enable generative orchestration; turn off web/general knowledge so Percy stays on-rules.
- [ ] Publish; connect the agent action in `Percy-Orchestrator`.

**Power BI semantic model**
- [ ] Confirm the OPE ↔ `HPE Opportunity Id` format (prefix or not); set flow normalisation.
- [ ] Apply §10.8 / §11.8 changes as scope allows (typed Created Date, Is-CC-Line flag, entity-id
      fix, campaign-code flag, per-OPE summary, Last Refreshed).
- [ ] Verify the four templates run via the connector under the shared account.

**Testing & monitoring**
- [ ] Run the §13 matrix end-to-end (Power Apps → reply).
- [ ] Verify **no JSON/DAX/IDs** ever reach `Reply` (tests 13–14, 16).
- [ ] Watch flow run history + `ErrorMessage`; review `MetricType`/`OPE` analytics for coverage gaps.
- [ ] Tune `varPollMax`/trigger latency; set alerting on `Status=Error` rate.

---

## 15. Final deliverables (consolidated)

### 15.1 Percy Overview Instructions
*(Paste into Copilot Studio → Overview → Instructions — full text in [§5](#5-percy-copilot-studio-overview-instructions); append the [§9](#9-programme-rules-canonical) rules verbatim.)*

### 15.2 Tool descriptions (for Copilot Studio orchestration)
- **Check Complete Care Points Evidence** — *"Use when the user asks why Complete Care (CC) points
  are or aren't showing for a specific opportunity. Input: the OPE number. Returns whether the opp
  is found, has Complete Care product lines, a qualifying motion/close date, an active CC contract,
  and the awarded New Logo (100) / Uplift (75) points."*
- **Check CAP Points Evidence** — *"Use for questions about CAP engagement (20) or CAP-generated
  order (50) points on a specific opportunity. Input: OPE. Returns won/close/approval status and the
  points."*
- **Check Customer Centricity Evidence** — *"Use for logged customer/channel/leadership meeting
  points on an opportunity. Input: OPE. Returns each logged meeting's type, approval status and
  points (10/10/20)."*
- **Get Overall Points Summary** — *"Use when a user asks how many points they have or what's
  pending across all categories. Input: the user's email. Returns each category total plus pending."*

### 15.3 Power Automate flow outline (`Percy-Orchestrator`)
`When item created` → **guard `Role=user`** → `Status=Processing` → build conversation JSON (Get
items by `ConversationId`, order `Seq`) → **Run Percy agent** → sanitise → `Update item: Reply
(plain text), Status=Complete (+MetricType/OPE)` → **error scope** → `Status=Error`, friendly
`Reply`, technical `ErrorMessage`. Tool flows: validate → fixed DAX → Power BI *Run a query against
a dataset* → compact JSON.

### 15.4 DAX templates
A lookup-by-OPE · **B Complete Care diagnosis** · C current points by OPE · D expected CC points ·
E CAP diagnosis · F Customer Centricity · G overall summary — all in
[§10](#10-dax-templates); open items in [§10.8](#108-what-could-not-be-written-from-the-schema-todo-not-guessed).

### 15.5 Test matrix
18 cases in [§13](#13-testing-plan), covering latest-message selection, intent/OPE extraction,
tool routing, plain-text/no-leak guards, pending-vs-ineligible, not-found/error handling, and the
Power Apps duplicate-submit guard.

### 15.6 Build checklist
Step-by-step across SharePoint, Power Apps, Power Automate, Copilot Studio, Power BI, and
testing/monitoring in [§14](#14-implementation-checklist).
