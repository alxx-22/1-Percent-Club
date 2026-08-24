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

> **Deployment kit:** runnable/importable artifacts for this pack (SharePoint provisioning script,
> flow scaffolds, paste-in Copilot Studio instructions, ordered deploy guide) live in
> [`../../../deploy/`](../../../deploy/DEPLOY.md) — with honest reliability tiers (what truly imports
> vs. what's configured by hand).

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

### 1.2 The flows

**One orchestrator + two agent actions:**

| Flow | Trigger | Role |
|---|---|---|
| **`Percy-Orchestrator`** (main) | SharePoint *item **created*** on `PercyConversations` | Hands the new row's conversation JSON to the Percy agent, writes the plain-text answer, sets Status. (New row per send → create-only trigger, no loop guard.) |
| **`Percy-Query`** (diagnostic action, read-only) | *Called by Copilot Studio* (agent action) | The agent passes an **approved template key** (`CompleteCare`, `CAP`, …) + `ope`/`who` — **never DAX**. The flow `Switch`es to the matching **approved DAX template** (§10), runs it via the **Power BI connector** (signed-in shared connection), and returns **compact JSON evidence**. One flow for all diagnostics (§7). |
| **`Percy-Refresh`** (refresh action) | *Called by Copilot Studio* (agent action) | The agent calls it when the user asks to refresh / a deal isn't in the data yet. It triggers a **Power BI "Refresh a dataset"** on the semantic model and returns a short status (started / already running). No inputs. (§7.5) |

> *(A future `Add Points` action — programme owners asking Percy to award points — is deliberately
> deferred; it needs approval/identity context and a governed write path. Not in scope here.)*

> **Why one flow, not eight, and why the agent passes a *key* not a *query*.** The 8 per-metric
> flows were near-identical, so they collapse into one `Percy-Query` with a `Switch`. Crucially the
> agent passes a **template key**, so the **DAX stays server-side and approved** — Percy still never
> generates DAX (your hard rule), and there's no "run any DAX" endpoint to prompt-inject or
> exfiltrate the model through. One flow to build/maintain; the guardrail holds. (See §7.)

The "Run an agent" step in your existing pattern is the Copilot Studio agent action inside
`Percy-Orchestrator`. `Percy-Query` is invoked *from inside* Percy, not by SharePoint.

### 1.3 End-to-end data flow

```
┌─────────────┐   Patch (NEW row per send)                 ┌──────────────────────────┐
│  Power Apps │ ─ {ConversationJson, Status:"Pending"} ──▶ │  SharePoint              │
│  Percy chat │                                            │  PercyConversations list │
│  (galChat)  │ ◀── poll every 2s: Reply + Status ──────── │                          │
└─────────────┘                                            └────────────┬─────────────┘
      ▲                                                        item created │
      │ tmrPercyPoll shows plain-text Reply                                 ▼
      │                                              ┌─────────────────────────────────┐
      │                                              │ Power Automate: Percy-Orchestrator│
      │                                              │  (trigger: item created only)     │
      │                                              │  1 ► Run Percy agent (JSON in)     │
      │                                              │  2 sanitise the answer            │
      │                                              │  3 Update item: AnswerText=<plain> │
      │                                              │     Status=Answered (or fallback) │
      │                                              └───────────────┬───────────────────┘
      │                                                  agent reasons │ (Copilot Studio)
      │                                                                ▼
      │                                              ┌─────────────────────────────────┐
      │                                              │ Percy (Copilot Studio agent)      │
      │                                              │  • parse JSON, find latest user   │
      │                                              │  • route: FAQ vs diagnostic       │
      │                                              │  • if diagnostic ► call Percy-Query│
      │                                              │    with template key + ope/who     │
      │                                              └───────────────┬───────────────────┘
      │                                       template key + params  │ (NO DAX from agent)
      │                                                                ▼
      │                                              ┌─────────────────────────────────┐
      │                          compact JSON evidence│ Power Automate: Percy-Query        │
      │                          ◀────────────────────│  Switch(template) → approved DAX   │
      │                                               │  Power BI "Run a query against a  │
      │                                               │  dataset" (executeQueries)        │
      │                                               │  signed-in shared connection      │
      │                                               └───────────────┬───────────────────┘
      │                                                                ▼
      │                                               ┌────────────────────────────────┐
      └──────── plain English ◀────── agent composes ─┤ Power BI semantic model (import)│
                                                       │  Final / CC Contracts / Cap …   │
                                                       └────────────────────────────────┘
```

**No service principal, no REST/XMLA app.** `Percy-Query` uses the standard **Power BI connector**
action *"Run a query against a dataset"* with a **signed-in connection account** that has read
access to the workspace and semantic model. (Confirm the connection user is a workspace **Viewer+** /
has Build permission on the dataset.) The agent supplies only a **template key + ope/who** — the DAX
is selected server-side, so there is no endpoint that runs agent-supplied DAX.

---

## 2. SharePoint list design

List: **`PercyConversations`** — **already created**. There are two possible shapes; **your live
build uses Shape A, and that is the path the flow targets. The app already creates a new item per
send, so no Power Apps formula change is needed.**

- **Shape A (IN USE — one row per *send*)** — the app creates a **new item on every send**
  (`Patch(PercyConversations, Defaults(...), …)`), and that item holds the **whole conversation so
  far** in **`ConversationJson`** (the cumulative transcript, so the agent always has full context);
  the flow reads it and writes the answer to **`AnswerText`**, flipping **`Status`** `Pending →
  Answered`. Percy finds the latest user message *inside the JSON* (`Role="user"`, highest `Seq`);
  earlier entries are context. **New row per send is what lets the flow trigger on _item created_
  only** — the answer write-back is a *modify*, which a create-only trigger ignores, so no loop guard
  is needed.
- **Shape B (alternative, greenfield only)** — one row per message with discrete `Seq`/`Role`/
  `Body`/`Reply` columns. **Not your build** — documented in §2.2 for reference; ignore it unless you
  ever restructure the app.

### 2.1 Columns (Shape A — your live schema)

These are the columns the existing app + flow use. You already have these; nothing to rename.

| Column | Type | Written by | Notes |
|---|---|---|---|
| `Title` | Single line | **Power Apps** | Stores the `SessionId` (readable list view). |
| `SessionId` | Single line of text | **Power Apps** | Conversation/session id (a `GUID()`). **Index it.** |
| `ConversationJson` | Multiple lines, **plain text** | **Power Apps** | The **whole transcript so far** as JSON (the agent's input). Rich text **off**. |
| `AnswerText` | Multiple lines, **plain text** | **Power Automate** | Percy's final **plain-English** answer (the app polls this). Rich text **off**. **Plain text only.** |
| `Status` | Single line of text | **Power Apps** seeds `Pending`; **Power Automate** sets `Answered` | The app polls for `Status = "Answered"`. **Text, not Choice.** Keep these exact values. |
| `UserEmail` | Single line of text | **Power Apps** | `Lower(User().Email)` — drives per-user diagnostics (IP / Accreditation / Summary) and audit. |
| `LastQuestion` | Single/Multiple lines | **Power Apps** | The latest user message (convenience; the agent can also read it from the JSON). |
| `MessageCount` | Number | **Power Apps** | Turn count (convenience). |
| `Created` / `Modified` | Date/time | SharePoint (auto) | System fields. |
| `MetricType` *(optional, add if wanted)* | Single line of text | **Power Automate** | Detected category for analytics (`CompleteCare`/`CAP`/…). |
| `OPE` *(optional, add if wanted)* | Single line of text | **Power Automate** | Extracted OPE for analytics/repro. |
| `ErrorMessage` *(optional, add if wanted)* | Multiple lines, plain text | **Power Automate** | Technical detail for admins. **Never shown to the user.** If you don't add it, log errors to flow run history instead. |

**Who writes what:**
- **Power Apps writes:** `Title`, `SessionId`, `ConversationJson`, `UserEmail`, `LastQuestion`,
  `MessageCount`, and seeds `Status = "Pending"`. (`AnswerText` stays empty.) — **unchanged; no edits.**
- **Power Automate writes:** `AnswerText`, `Status = "Answered"`, and optionally `MetricType` / `OPE`
  / `ErrorMessage`.

> Keep `ConversationJson` and `AnswerText` as **plain-text** multi-line columns (enhanced rich text
> **off**) so the JSON in / answer out is never HTML-mangled.
>
> **Only thing to confirm you have:** a **`Status`** *Single line of text* column (the no-premium
> loop guard). If it's missing, add it — that's a column add, **not** a Power Apps formula change.

### 2.2 Columns (Shape B — alternative, not your build)

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

> **This is the existing app — no formula changes needed.** Steps below describe what
> [`imgSend.OnSelect.powerfx`](../imgSend.OnSelect.powerfx) and
> [`tmrPercyPoll.OnTimerEnd.powerfx`](../tmrPercyPoll.OnTimerEnd.powerfx) already do; they're here so
> the flow contract is unambiguous.

1. **Submit** — `imgSend.OnSelect` (guarded `!IsBlank(Trim(txtChat.Text)) && !varPercyThinking`):
   append `{ Seq, Role:"user", Body }` to `colChat`, `Reset(txtChat)`.
2. **Create a new SharePoint row (Shape A)** — Patch a **fresh** row with the **whole conversation
   so far** as JSON, answer empty, `Status = "Pending"`:
   ```powerfx
   Set( varChatJson, JSON( ShowColumns( colChat, Seq, Role, Body ) ) );
   Set( varAsk,
       Patch( PercyConversations,
           Defaults( PercyConversations ),
           { Title: Text(varSessionId) & " - " & Text(Now(), "yyyymmddhhmmss"),
             SessionId: Text(varSessionId), ConversationJson: varChatJson,
             UserEmail: Lower(User().Email), LastQuestion: varPercyQ,
             MessageCount: CountRows(colChat), AnswerText: "", Status: "Pending" } ) );
   Set( varAskId, varAsk.ID ); Set( varPollN, 0 ); Set( varPercyThinking, true );
   ```
   *(This is the existing app formula — nothing to change. Each send creates a new row carrying the
   cumulative transcript, so the created item the flow fires on always has the full conversation.
   `SessionId` still tags every row for the same chat; the poll keys off the returned `varAskId`.)*
3. **Pending / typing state** — `Set(varPercyThinking, true)` shows `imgThinking` and **starts**
   `tmrPercyPoll` (`Start = varPercyThinking`). The send button is disabled while thinking.
4. **Polling refresh** — `tmrPercyPoll.OnTimerEnd` (every 2s): `Refresh(PercyConversations)`,
   re-`LookUp` the row by `ID = varAskId`, and when **`Status="Answered"`** **and** `AnswerText` is
   non-blank, append `{ Role:"percy", Body: AnswerText }` to `colChat` **once** (guarded by
   `varPercyThinking` so extra ticks can't double-post).
5. **Display the answer** — the new `colChat` row renders through `htmlBubble` (left/white card).
   `galChat` shows it because `Items = Sort(colChat, Seq)`.
6. **Avoid duplicate submissions** — the `!varPercyThinking` guard blocks a second send while one is
   in flight; the `varGotReply = varPercyThinking && …` guard collects the answer exactly once.
7. **Sort by Seq** — `galChat.Items = Sort(colChat, Seq)` (oldest→newest, newest at bottom).
8. **Group / filter by session** — `varSessionId = GUID()` (set in
   [`App_OnStart`](../../dashboard/App_OnStart.powerfx)) tags the row; the poll filters by `ID`.
9. **Timeout** — total wait = `tmrPercyPoll.Duration (2000ms) × varPollMax (60) = 120s`. The
   SharePoint trigger alone can take 30–60s to fire, so keep this generous; on timeout Percy posts a
   friendly "couldn't reach the assistant" bubble and stops polling.

> **Timers in a Power BI-embedded visual can be unreliable.** Provide a tiny "check for reply"
> image/button whose `OnSelect` runs the same body as `tmrPercyPoll.OnTimerEnd` as a manual fallback.

---

## 4. Main Power Automate flow (`Percy-Orchestrator`)

**Trigger:** SharePoint **"When an item is created"** on `PercyConversations`.
*(The app writes a **new row on every send** with `ConversationJson` filled, `AnswerText` empty,
`Status = "Pending"`. Create-only fires once per question and — because the answer write-back is a
*modify* it ignores — **never re-triggers itself, so no loop guard is needed**. See §3 / [`README.md`](README.md) §3.)*

| # | Action | Detail |
|---|---|---|
| 1 | **Read the conversation** | Take **`ConversationJson`** straight off the trigger item — it already holds the whole transcript. **No Get items / rebuild.** Capture `triggerBody()?['ID']` and `UserEmail`. *(No guard step: a freshly created row is always a fresh ask — `Status="Pending"`, `AnswerText` empty — since only the app creates rows.)* |
| 2 | **Run Percy agent** | Copilot Studio agent action (`Percy`). **Input** = `ConversationJson` (string) + `UserEmail`. The agent finds the latest user message (`Role="user"`, highest `Seq`) inside the JSON, routes, optionally calls a tool, returns **plain text**. |
| 3 | **Sanitise the agent output** | `Compose`: `if(empty(trim(<agent text>)), 'Sorry, I couldn''t answer that one — please try again.', <agent text>)`. Defence-in-depth: strip stray code fences / leading `{`/`[`. The agent should already return prose. |
| 4 | **Update item — write `AnswerText`** | `Update item` (by `ID`) → **`AnswerText`: `<sanitised text>`**, **`Status`: `Answered`**, optional `MetricType`/`OPE`. The app's poll is watching exactly this. |
| — | **Error handling (Scope + "has failed")** | Wrap 1–4 in a **Scope**. On failure (`Configure run after: has failed, timed out`): `Update item` → **`AnswerText`: "Sorry, I couldn't reach the assistant just now — please try again."**, **`Status`: `Answered`** (so the user actually sees the message — the app only displays when `Status="Answered"`), and `ErrorMessage: <technical detail>` **if that column exists** (else rely on flow run history). |

**Why `Status="Answered"` even on error:** your app's poll
([`tmrPercyPoll.OnTimerEnd.powerfx`](../tmrPercyPoll.OnTimerEnd.powerfx)) shows the bubble only when
`Status = "Answered"` and `AnswerText` is non-blank. Writing a friendly failure into `AnswerText`
with `Status = "Answered"` surfaces it immediately rather than making the user wait out the poll
timeout. (Use a distinct `Status` like `Error` only if you also teach the app to read it — which
you don't want to, so don't.)

**Concurrency:** cap the trigger's concurrency (e.g. 10) so a burst of chats doesn't exhaust the
Copilot Studio / Power BI connection. **Telemetry:** flow run history (plus an optional
`ErrorMessage` column) is your audit trail; `MetricType`/`OPE` give per-category usage analytics.

---

## 5. Percy Copilot Studio overview instructions

> **Canonical instructions live in one place:**
> [`deploy/copilot-studio/percy-instructions.md`](../../../deploy/copilot-studio/percy-instructions.md)
> — the paste-ready block (self-contained: the §9 rules are inlined, no separate append step). It
> is written for the **two-tool** agent (`Run Percy Diagnostic` = Percy-Query, `Refresh Dashboard`
> = Percy-Refresh) and the fresh-DAX evidence keys (§7.3). Paste that file verbatim into
> **Overview → Instructions**; do not re-type the block here (a second copy only drifts).
>
> This section previously duplicated the full block; it now defers to that file so there is a
> single source of truth. If the programme rules change, update **§9 here AND the inlined copy
> in percy-instructions.md together.**

---

## 6. Percy topic design

Percy runs with **generative orchestration ON**: routing is driven by the **instructions + the two
action descriptions**, and each custom topic is triggered by **"The agent chooses"** (a plain-language
description of when it applies) — **not** classic trigger phrases. The "trigger phrases" listed per
topic below are the **intents each description should cover** (and what you'd paste if orchestration
were off). The per-topic decision logic still applies as the agent's reasoning, whether it runs inside
a scripted topic or straight from the instructions + `Run Percy Diagnostic` action.

> **Build few topics.** Because the `Run Percy Diagnostic` action covers all eight diagnostics, the
> per-scheme topics (6.4–6.9) are **optional** — build one only to lock that scheme's wording. The
> paste-in, orchestration-native version (descriptions + node flows, marked Build vs Optional) is
> [`deploy/copilot-studio/topics.md`](../../../deploy/copilot-studio/topics.md).

> **Design for vague input.** Most real messages are short and underspecified ("why aren't my
> points showing", a bare OPE, "cap??"). The topics below are built to **act first** (Summary /
> Locate) and only ask when they must — one small question at a time. See the instruction block §5
> ("GOLDEN RULES" + "THE TWO MESSAGES") — the topics implement it.

### 6.1 `Process SharePoint Conversation JSON` (system / first)
- **Purpose:** normalise input every turn — parse the JSON, isolate the latest user message,
  collect prior OPE/metric context, and classify how vague it is.
- **Trigger:** runs first on every invocation (On-Conversation-Start / highest priority).
- **Inputs:** `ConversationJson` (string), `UserEmail`.
- **Decision logic:** parse array → select `Role="user"` with max `Seq` → set `var_LatestText`.
  **Scan ALL `Body` values** (not just the latest) for an OPE with a forgiving regex
  (`OPE-?\d{6,12}`, case-insensitive, allow surrounding text) → `var_OPE`. Infer `var_Metric` from
  **loose** keywords (cc / "cc thing" / new logo / uplift; cap / support request / gemma / campaign;
  meeting / customer / channel / leadership / event; ib / expand / renewal / pen rate; ip / greenlake;
  accred / s-coded / csm / race; refresh / update / "not there yet"). Set `var_Shape`:
  `has_ope+has_metric` · `has_ope_only` · `metric_only` · `neither` · `refresh` · `faq`.
- **Output:** sets `var_LatestText / var_OPE / var_Metric / var_Shape`; routes:
  `has_ope+metric`→scheme topic · `has_ope_only`→Locate (6.4→route) · `metric_only`→scheme topic (ask
  OPE) · `neither`→Clarify (6.11, defaults to Summary) · `refresh`→Refresh (6.12) · `faq`→FAQ. No
  user-facing text.

### 6.2 Query routing map (symptom → metric → template key)

This is the heart of "Percy identifies which query is required." Percy classifies the latest user
message to a metric, then calls the **one** action `Run Percy Diagnostic` (`Percy-Query`) with the
matching **template key**. The DAX behind each key lives in the flow (§7), not in the agent.

| User says / symptom | Metric | template key | DAX behind it (§10) | Pass |
|---|---|---|---|---|
| "does this opp exist", "no points at all", metric unclear | (probe) | `Locate` | A | ope |
| "complete care", "CC", "new logo", "uplift", "9X" | Complete Care | `CompleteCare` | B | ope + who |
| "CAP request not showing", "support request", "engagement", "Gemma" | CAP engagement (20) | `CAP` | E | ope (+who) |
| "CAP order", "CAP-generated order", "campaign code", "why no 50" | CAP order (50) | `CAP` | E | ope (+who) |
| "customer meeting", "channel meeting", "leadership intro", "logged event/activity" | Customer Centricity | `CustomerCentricity` | F | ope (+who) |
| "IB", "expand", "renewal + expand", "pen rate", "win-back" | IB / Expand | `IBExpand` | H | ope + who |
| "IP", "GreenLake", "IP in GL", "monthly %" | IP in GreenLake | `IPGreenLake` | I | who |
| "accreditation", "S-coded", "CSM", "the race", "completion" | Accreditation | `Accreditation` | J | who |
| "how many points do I have", "what's pending", "my total" | all | `Summary` | G | who |

> **Pass the user's email (`who`)** with `CompleteCare`, `IBExpand`, `CAP` and `CustomerCentricity`
> whenever you have it (you usually do — it's on the SharePoint row). It's how the query checks the
> points actually **credit to THIS user**: `CompleteCare`/`IBExpand` credit by **owner email**
> (opportunity owner / primary pipeline owner / OS sales), so a deal can score points that go to
> someone else (`CreditsToYou = No`); `CAP`/`CustomerCentricity` credit by **name**, so it flags a
> **name mismatch**. Both are frequent reasons points "don't flow" to the person asking.

### 6.3 `General 1% Club FAQ`
- **Purpose:** answer rule questions directly, no tool call.
- **Trigger phrases:** "how do I get points", "how many points for…", "do I need a campaign code",
  "where do I log…", "what counts as…", "how is X scored", "rules for…".
- **Inputs:** `var_LatestText`.
- **Decision logic:** match the question to a rule in §9; answer with the exact value. If it spans
  several rules (e.g. "how do I get points?"), give the short menu of the nine ways.
- **Output:** plain-text rule answer. Never calls a tool.

### 6.4 `Complete Care Diagnostic`
- **Purpose:** explain why Complete Care points are/aren't showing for an OPE.
- **Trigger phrases:** "complete care", "CC points", "complete care for OPE", "why no complete care".
- **Inputs:** `var_OPE` (required), context.
- **Decision logic:** see §8. No OPE → ask for it. OPE present → call `Run Percy Diagnostic`
  (template **`CompleteCare`**, ope **+ who**) → interpret flags (found, product line, sales motion,
  close date, active contract, awarded points, in-funnel, **credits-to-you**) → plain-English
  explanation. **If it scores CC points but `creditsToYou = No`, that's the answer** — the deal
  credits to the opportunity/pipeline owner, not the caller.
- **Output:** plain text: what's confirmed, the points (if any), and the most likely reason if zero.

### 6.5 `CAP Diagnostic`
- **Purpose:** explain CAP **engagement** (20) and CAP-generated **order** (50) points for an OPE.
- **Trigger phrases:** "CAP order", "CAP request", "CAP points", "cap engagement", "it's a CAP order why no points", "my cap request isn't showing".
- **Inputs:** `var_OPE` (required), `UserEmail` (optional but preferred).
- **Decision logic:** call `Run Percy Diagnostic` (template **`CAP`**, ope [+who]). For an
  **engagement** question, check in
  this order: exists in CAP requests? → created on/after 1 May? → logged-by name matches the caller's
  dashboard name? → approval status (`Approve` vs blank = pending Gemma/BD sign-off). For an **order**
  question: exists in CAP-won? → won? → close date after 1 May? → approval status. Surface the FIRST
  failing gate; if all gates pass but approval is blank, say "pending sign-off" (not "ineligible").
  State the campaign-code requirement (`UKIMEA CSLV CAP Adoption`) for orders but be clear you can't
  verify the code from here.
- **Output:** plain text naming the exact blocker (not found / wrong date / name mismatch / pending /
  approved).

### 6.6 `Customer Centricity Diagnostic`
- **Purpose:** explain logged customer / channel / leadership meeting points for an OPE.
- **Trigger phrases:** "customer meeting", "leadership meeting", "channel meeting", "customer centricity", "logged a meeting no points", "my event isn't flowing".
- **Inputs:** `var_OPE` (required), `UserEmail` (optional but preferred).
- **Decision logic:** call `Run Percy Diagnostic` (template **`CustomerCentricity`**, ope [+who]).
  For each meeting on the opp check:
  is it **classified** (`meetingType` non-blank)? If not, the **Subject didn't start with CUSTOMER /
  CHANNEL / LEADERSHIP** — quote back the `subjectPrefix` and tell them to re-log with the keyword at
  the very start (covers typos like "CUSTMER", wrong word, or a leading phrase before the keyword).
  Also check **`createdQualifies`** — meetings logged **before 1 May 2026** don't count (Customer
  Centricity gates on **created date**). Then check the **logged-by name matches** the caller, and the **approval status** (manager approves
  weekly). Explain 10 (customer/channel) / 20 (leadership) values.
- **Output:** plain text naming the blocker (no meeting / unrecognised subject prefix / name mismatch
  / pending approval / approved).

### 6.7 `IB / Expand Diagnostic`
- **Purpose:** explain IB Upsell / Expand Pen Rate points (1 per 4% expand, ≤25) for an OPE.
- **Trigger phrases:** "IB points", "expand", "renewal plus expand", "pen rate", "win-back", "naked box".
- **Inputs:** `var_OPE` (required).
- **Decision logic:** call `Run Percy Diagnostic` (template **`IBExpand`**, ope **+ who**) → needs
  BOTH a renewal/IB motion AND
  an expand/new motion, **Won**, close ≥ 1 May. **Key gotchas:** (1) if the opp already scores
  Complete Care points, IB/Expand is **suppressed on that opp by design** — say so; (2) if it earns
  IB/Expand but **`creditsToYou = No`**, it credits to the owner / pipeline / OS-sales person, not the
  caller. If not won, it shows in the funnel only.
- **Output:** plain text with the awarded value or the blocker (incl. the CC-suppression case).

### 6.8 `IP in GreenLake Diagnostic`
- **Purpose:** explain IP-in-GreenLake tier points (10–75) for the user.
- **Trigger phrases:** "IP points", "GreenLake", "IP in GL", "my monthly %".
- **Inputs:** `UserEmail` (required) — this scheme is per-user, not per-OPE.
- **Decision logic:** call `Run Percy Diagnostic` (template **`IPGreenLake`**, who) → is there an
  IP-GL row for the user?
  what's the monthly %? which tier (0–10→10, 10–25→20, 25–40→30, 40–50→50, 50%+→75)? No row / 0% → 0.
- **Output:** plain text with the % band and points (no OPE needed).

### 6.9 `Accreditation Diagnostic`
- **Purpose:** explain accreditation-race / CSM points eligibility for the user.
- **Trigger phrases:** "accreditation", "S-coded", "CSM", "the race", "completion points".
- **Inputs:** `UserEmail` (required) — person/team-level, not per-OPE.
- **Decision logic:** call `Run Percy Diagnostic` (template **`Accreditation`**, who) → is the user
  **S-coded** ("S-Coded
  (Phil)")? accreditation status **COMPLETE**? job family (Customer Success Architects are excluded
  from the S-coded race unless Adrian/Garren)? excluded individual (Adrian/Garren)? CSM L2+ → 30.
  Explain that the 100/50/20 is a **team race** decided by completion standings, so the tool shows
  eligibility/status, and the awarded figure comes from the standings.
- **Output:** plain text: eligibility, completion status, and what's blocking (not S-coded / not
  complete / excluded), or the CSM 30.

### 6.10 `Fallback / Clarification`
- **Purpose:** handle greetings, nonsense, off-topic.
- **Trigger:** no other topic matched.
- **Decision logic:** greeting/nonsense/mixed → be friendly, pull out any real intent and answer
  that; if there's genuinely none, one line on what Percy can do (points questions · check a deal ·
  refresh the board). Off-topic → politely redirect. **Never loop; never dump the category list.**
- **Output:** one short friendly line. Usually no tool call.

### 6.11 `Clarify & Guide` (the vague-message handler — the important one)
- **Purpose:** the catch for the most common real message — **vague, no deal, no metric** ("why
  aren't my points showing", "where are my points", "I should have more"). Act first, don't interrogate.
- **Trigger:** `var_Shape = neither` (diagnostic intent, no OPE, no clear metric); low-context.
- **Decision logic (act-before-ask):**
  1. **Default to Summary.** Call `Run Percy Diagnostic` (template **`Summary`**, who) and lead with
     their total + **what's pending** (approval is the #1 reason points look missing).
  2. Then **offer** one next step: "Chasing a particular deal? Pop the OPE in and I'll check it." —
     do **not** ask them to pick a category.
  3. If they only named a **metric** but no OPE (`var_Shape = metric_only`) → ask the single thing you
     need: "Sure — what's the deal number? (looks like OPE-123456789)". One question, plain words.
  4. If they gave a **bare OPE** (`var_Shape = has_ope_only`) → this is the Locate path (6.4 routes
     here): call `Locate`, then route to the one scheme, or say what's on the deal and ask which they
     meant. Don't ask before Locate.
- **Output:** their summary (+ pending) and an open door, OR one small clarifying question. Never two
  questions; never a wall of text.

### 6.12 `Refresh Dashboard`
- **Purpose:** refresh the data when a deal isn't in the scoring yet or the user asks to update.
- **Trigger phrases:** "refresh", "update the dashboard", "my points aren't there yet", "I closed it
  today", "it's not updating", "still not showing after…". Also reached from other topics when a
  diagnostic returns *not found* / *just closed*.
- **Inputs:** none.
- **Decision logic:** call the **Refresh Dashboard** action (`Percy-Refresh`, §7.5) → tell them a
  refresh takes a few minutes and to check back. **One refresh per request** — if it reports one is
  already running, say it's already updating. Don't loop refreshes.
- **Output:** a short "kicked off a refresh — check back in a few minutes" (or "already updating").

---

## 7. The single diagnostic action — `Percy-Query`

There is **one** Power Automate flow, `Percy-Query`, added to Percy as the action **"Run Percy
Diagnostic"**. The agent passes an **approved template key** + `ope`/`who` — **never DAX**. The flow
`Switch`es on the key to the matching **fixed DAX template** (§10), runs it via the Power BI
connector (signed-in shared connection), and returns **compact JSON** the agent reads and **never
echoes**. One flow replaces the earlier eight per-metric flows, while keeping every guardrail.

### 7.1 `Percy-Query` action
- **Inputs:**
  - `template` (string, **required**) — exactly one of `Locate`, `CompleteCare`, `CAP`, `IBExpand`,
    `CustomerCentricity`, `IPGreenLake`, `Accreditation`, `Summary`.
  - `ope` (string, optional) — for opportunity templates.
  - `who` (string, optional) — caller email for user-level / name-match templates.
- **Logic:** validate inputs → **`Switch(template)`** sets the approved DAX (§10) with `ope`/`who`
  dropped in → **Power BI "Run a query against a dataset"** → return `firstTableRows`. An unknown key
  hits the `default` branch → `{ "error":"unknown_template" }`, so **only approved queries ever run**.
- **Shape (this trips people up):** each Switch case holds **only a `Compose Dax_<key>`** — its DAX
  text, nothing else. **After** the Switch, a single `Compose DaxQuery = coalesce(<all branch Composes>)`
  picks whichever branch ran, feeding **one** Power BI "Run a query" action. The query action is
  **placed once, after the Switch — NOT one inside each branch** (that would mean maintaining it 8×).
  In the `coalesce`, reference each Compose by its internal name (spaces → underscores: `Dax CC` →
  `outputs('Dax_CC')`). Click-by-click: [`Percy-Query.build.md`](../../../deploy/flows/Percy-Query.build.md) steps 4–5.
- **Output:** `evidence` (string) = the `firstTableRows` JSON array — **one** row for the single-row
  templates, **several** rows for `CustomerCentricity` (one per logged meeting). Percy reads the array
  and explains it in plain English; it never echoes the JSON.
- **Build steps:** [`../../../deploy/flows/Percy-Query.build.md`](../../../deploy/flows/Percy-Query.build.md).

### 7.2 Template registry (what each key runs)
Canonical query per key: [`dax-templates.md`](../../../deploy/flows/dax-templates.md) (2026-07 model).

| `template` | Metric | Needs | Returns |
|---|---|---|---|
| `Locate` | existence probe | `ope` | counts per scheme (1 row) |
| `CompleteCare` | New Logo 100 / Uplift 75 | `ope` (+`who`) | CC evidence + credits-to-you (1 row) |
| `CAP` | CAP request 20 + order 50 | `ope` (+`who`) | CAP evidence (1 row) |
| `IBExpand` | IB / Expand, pro-rata ≤25 | `ope` (+`who`) | IB evidence + credits-to-you (1 row) |
| `CustomerCentricity` | meetings 10 / 10 / 20 | `ope` (+`who`) | one row **per meeting** |
| `IPGreenLake` | IP tier 10–75 (per month, summed) | `who` | monthly tiers (1 row) |
| `Accreditation` | S-coded race + CSM + bonuses | `who` | eligibility + status (1 row) |
| `Summary` | all categories + pending | `who` | totals (1 row) |

### 7.3 Per-template evidence & what Percy says

Each block: the exact evidence keys the fresh DAX returns (dax-templates.md), and how to turn them
into a plain-English answer. All flag fields are `"Yes"`/`"No"` strings; approval blank = pending.

**`Locate`** — `{ OPE, InOpportunities, ScoresCompleteCare, ScoresIBExpand, OpportunityOwner, InCapWon, InCapRequests, InMeetings }`.
- `ScoresCompleteCare=Yes` or `ScoresIBExpand=Yes` → **the deal is scoring points on this deal** — go
  straight to that diagnostic (CompleteCare/IBExpand) **with `who`**. If it comes back
  `CreditsToYou=No`, that's the answer: "this deal scored its points, but they credit to
  **<OpportunityOwner>**, not you." (This is the #1 "my deal has no points" cause — do NOT report
  "no scoring activity" just because CAP/meetings are empty; check the CC/IB flags first.)
- CAP/meeting counts > 0 → route to that scheme's diagnostic.
- in opportunities only, both scoring flags `No`, no CAP/meetings → "the deal's in the system but
  isn't scoring anything yet — if you've just submitted something it may need a refresh."
- `InOpportunities=0` and all others 0 → "I can't find that opportunity anywhere yet — double-check the number, or it may be awaiting a refresh."

**`CompleteCare`** — `{ OPE, Found, OpportunityName, Account, ForecastCategory, CloseDate, OpportunityOwner, PrimaryPipelineOwner, CreditsToYou, HasCompleteCareProduct, HasNewSolutionMotion, HasDay1Product, Won, CloseOnOrAfter1May2026, NewLogoPointsAwarded, UpliftPointsAwarded, CompleteCarePointsTotal, InFunnelNotYetWon }`.
- `CompleteCarePointsTotal=100`, `CreditsToYou=Yes` → "scoring the full 100 Complete Care New Logo points — and they're crediting to you."
- `CompleteCarePointsTotal>0`, `CreditsToYou=No` → "this deal IS scoring Complete Care points, but they're crediting to **<OpportunityOwner>** (the opportunity / pipeline owner), not you. If you should hold it, get the owner updated on the deal."
- `NewLogoPointsAwarded=0` but `UpliftPointsAwarded=75` → "it's scoring as an **Uplift (75)**, not New Logo 100 — the customer already had a Complete Care contract before April 2026, so New Logo doesn't apply. That's correct, not missing points."
- `InFunnelNotYetWon=Yes`, total 0 → "qualifies on product and timing, but it hasn't been **Won** yet — points land on win."
- `HasCompleteCareProduct=No` → "no Complete Care (9X) product lines on this opp, so it isn't picking up CC points."
- `Found=No` → "can't find it in the scoring data yet — check the OPE, new opps take a refresh."

**`CAP`** — `{ OPE, CallerName, InCapWon, CapOrderForecast, CapOrderCloseDate, CapOrderCloseQualifies, CapOrderApprovalStatus, CapOrderCreditsToYou, InCapRequests, RequestCreatedDate, RequestCreatedQualifies, RequestLoggedBy, RequestLoggedByMatchesYou, RequestApprovalStatus }`.
- request: `InCapRequests=No` → "no CAP request logged against this opp (log it in SFDC: Support Requests → CAP Team Engagement/Support)."
- `RequestCreatedQualifies=No` → "logged, but created before the 1 May 2026 cut-off."
- `RequestLoggedByMatchesYou=No` → "logged under **<RequestLoggedBy>**, not your dashboard name — that's why it isn't crediting to you."
- request logged, `RequestApprovalStatus` blank → "logged and eligible — **pending sign-off** by Gemma/BD; 20 points on approval."
- order: `InCapWon=Yes` + `CapOrderCloseQualifies=Yes` + `CapOrderApprovalStatus` blank → "**won and eligible** but **pending Gemma's validation** — 50 points on approval; also confirm campaign code **UKIMEA CSLV CAP Adoption**."
- `CapOrderCloseQualifies=No` → "close date before 1 May 2026, the CAP-order cut-off."
- `CapOrderCreditsToYou=No` (order scores) → "the order credits to the opportunity/pipeline owner, not you."

**`IBExpand`** — `{ OPE, Found, OpportunityName, ForecastCategory, CloseDate, OpportunityOwner, PrimaryPipelineOwner, CreditsToYou, HasRenewalMotion, HasNewExpandMotion, Won, CloseOnOrAfter1May2026, SuppressedByCompleteCare, IBExpandPointsAwarded, InFunnelNotYetWon }`.
- `IBExpandPointsAwarded>0`, `CreditsToYou=Yes` → "scoring <IBExpandPointsAwarded> IB/Expand points. It's pro-rata (the expand share of the deal value × 25), so a partial figure is normal."
- `IBExpandPointsAwarded>0`, `CreditsToYou=No` → "this deal earns IB/Expand points, but they credit to **<OpportunityOwner>** (owner / pipeline / OS-sales), not you."
- `SuppressedByCompleteCare=Yes`, award 0 → "this deal already scores Complete Care points, so IB/Expand isn't paid on the same deal — it's counted under Complete Care instead."
- `HasRenewalMotion=No` or `HasNewExpandMotion=No` → "IB/Expand needs **both** a renewal/IB motion and an expand motion; I only see one."
- `InFunnelNotYetWon=Yes` → "qualifies but hasn't been **won** yet — IB/Expand lands on win."

**`CustomerCentricity`** — array (one row per meeting) of `{ MeetingType, Classified, LoggedBy, LoggedByMatchesYou, ApprovalStatus, PointsWhenApproved }`.
- empty array → "no logged meetings on this opp (Opportunity → Activities → New Event)."
- `Classified=No` → "this activity's Meeting Type isn't Customer / Channel Partner / Leadership, so it isn't classified — re-log it with the right Meeting Type."
- `LoggedByMatchesYou=No` → "logged under **<LoggedBy>**, not you, so it's crediting to them."
- classified, `ApprovalStatus` blank → "I see a <MeetingType> — <PointsWhenApproved> points once your manager approves (weekly)."
- classified, `ApprovalStatus="Approve"` → "confirmed — <PointsWhenApproved> points for this <MeetingType>."

**`IPGreenLake`** — `{ User, MayPercent, MayPoints, JunePercent, JunePoints, TotalIPPoints }`.
- `TotalIPPoints>0` → "your IP-in-GreenLake is <MayPercent> in May (<MayPoints>) and <JunePercent> in June (<JunePoints>) — **<TotalIPPoints> points** so far."
- `TotalIPPoints=0` → "no IP-in-GreenLake percentage for you yet, so no points from that scheme (it's recognised monthly from SFDC)."

**`Accreditation`** — `{ Name, Crew, ManagerSponsor, SCoded, AccreditationCompletionStatus, JobFamily, AccreditationAndBonusPoints }`.
- `SCoded≠"S-Coded (Phil)"` → "the race is for S-coded individuals; your record isn't flagged as S-coded."
- `AccreditationCompletionStatus≠"COMPLETE"` → "your accreditation isn't COMPLETE yet — the team race credits once everyone in your sponsor group is complete."
- `JobFamily="Customer Success Architect"` (and not Adrian/Garren) → "Customer Success Architects are excluded from the S-coded race."
- `AccreditationAndBonusPoints>0` → "you've got <AccreditationAndBonusPoints> points here — this figure is the S-coded team race (100/50/20 split per group) plus any CSM completion (30) and crew/individual bonuses. Call it 'accreditation and bonus points', not just accreditation."

**`Summary`** — `{ User, Name, Crew, CompleteCarePoints, IBExpandPoints, CapRequestPoints, CapOrderPoints, CustomerCentricityPoints, AccreditationAndBonusPoints, IPinGreenLakePoints, CapRequestsPending, CapOrdersPending, CustomerCentricityPending }`. Plain-text breakdown by category + "you've got X points pending approval" when any pending field is non-zero. *(Keys deliberately unabbreviated — "CC" alone is ambiguous. ONLY `CapRequestsPending`, `CapOrdersPending`, `CustomerCentricityPending` can ever be non-zero; every other category is auto-calculated and never "pending".)*

### 7.4 Security controls
- **Approved keys only — the core guardrail.** The agent passes a **key**, not a query; an unknown
  `template` returns an error. There is **no endpoint that runs agent-supplied DAX**, so there's
  nothing to prompt-inject or exfiltrate the model through.
- **Input validation:** OPE `^OPE-?\d{6,12}$` and email = caller/admin are enforced in **Copilot
  Studio** before the action is called; the flow keeps a non-empty backstop. (DAX `=` on text is
  case-insensitive, so no upper-casing is needed for matching.)
- **Output minimisation:** return only the projected columns (the shapes in §7.3) — never whole
  rows, PII beyond the name/account already on the dashboard, or entity IDs.
- **Connection:** least-privilege **signed-in shared account** with workspace read + dataset
  **Build**; rotate per policy. The New Logo existing-contract check is baked into the model's
  `CC New Logo Points` column (entity-id match, §11 caveat); Percy sees only the resulting
  `NewLogoPointsAwarded`/`UpliftPointsAwarded` figures and speaks to them qualitatively.

### 7.5 `Percy-Refresh` — the second action (refresh the dashboard)
The agent's other action. Simple by design (build steps: `deploy/flows/Percy-Refresh.build.md`).

- **Purpose:** kick a data refresh so newly-closed deals / logged activity show up. Percy calls it
  when the user asks to "refresh/update" the dashboard, or when a diagnostic returns *not found* /
  *just closed*.
- **Trigger:** Copilot Studio calls the flow. **No inputs** (it always refreshes the one 1% Club
  semantic model).
- **Logic:** **Power BI → Refresh a dataset** (workspace + dataset from env/config) → return a short
  status to the agent.
- **Output:** `status` (string) — `"started"` | `"already_running"` | `"error"`.
- **What Percy says:**
  - `started` → "I've kicked off a refresh — it takes a few minutes. Check back shortly and your
    points should be up to date."
  - `already_running` → "A refresh is already running — give it a few minutes and it'll be current."
  - `error` → "I couldn't start a refresh just now — try again shortly, or ping the programme team."
- **Guardrails / notes:**
  - **Rate limits:** Power BI caps scheduled+API refreshes per day (Pro ~8/day, Premium/PPU ~48).
    The flow should **not** refresh on a loop — **one refresh per user request**; if a refresh is in
    progress, return `already_running` rather than starting another. (Check the last refresh status
    before triggering, or just handle the connector's "another refresh is in progress" response.)
  - **Read/refresh only:** this triggers a refresh; it does **not** write to the model. It's the
    only "action that changes something," and even then only the data's freshness.
  - **Connection:** the same signed-in shared account (needs dataset refresh permission).
- **Future (deferred):** an `Add Points` action (programme owners award points) is **out of scope**
  — it needs approver identity, an approval/audit trail, and a governed write to the source, not a
  quick action. Design it separately when ready.

## 8. Complete Care diagnostic logic

> **Evidence keys below are OLD-MODEL.** The canonical CompleteCare shape and interpretation is
> [§7.3](#73-per-template-evidence--what-percy-says) (fresh keys `CompleteCarePointsTotal`,
> `HasCompleteCareProduct`, `NewLogoPointsAwarded`/`UpliftPointsAwarded`, etc.); the query is in
> [`dax-templates.md`](../../../deploy/flows/dax-templates.md). One live change to the decision tree:
> there is no longer an `activeCCContract` flag — when every gate passes but the award lands as
> **Uplift 75, not New Logo 100**, that *is* the "existing Complete Care contract" case (the model
> checks a contract started before Apr 2026). Read this tree for the reasoning, §7.3 for the keys.

The exact reasoning Percy follows (mirrors the model in §11). Decision order:

```
0. No OPE anywhere in the conversation?            → ASK for the OPE. Stop.
1. OPE present but metric unclear, context unclear → ASK "Complete Care, CAP, or Customer
                                                       Centricity?". Stop.
2. Metric = Complete Care, OPE present             → call `Run Percy Diagnostic` (template
                                                     `CompleteCare`, ope + who).
3. found = No                                      → "can't find that opportunity yet" (refresh/typo).
3b. ccPointsTotal > 0 AND creditsToYou = No         → **this is the answer:** the deal IS scoring CC
                                                     points, but they credit to the opportunity /
                                                     pipeline owner (name in the evidence), not the
                                                     caller. Say who; suggest the owner be corrected
                                                     if the caller should hold the deal. Stop.
4. ccPointsTotal = 100 (creditsToYou = Yes)         → confirm New Logo 100.
5. ccPointsTotal = 75 (creditsToYou = Yes)          → confirm Uplift 75.
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
2. **The deal scores CC points, but they credit to the opportunity / primary pipeline owner — not the
   caller** (they're not the owner on the deal). Very common; check `creditsToYou` first.
3. Opportunity not in the qualifying date window (cut-off 1 May 2026).
4. No Complete Care product lines detected on the opportunity.
5. Customer already has an active Complete Care contract → **New Logo** condition fails (could be
   an **Uplift** at 75 instead).
6. Recognised as **Uplift**, not **New Logo** (so 75, not 100).
7. Eligible but **not yet won** — Complete Care points are credited on win.
8. Dashboard / semantic-model **refresh delay**.
9. Unclear or incomplete source data (e.g. missing sales motion / entity id).
10. The available guidance doesn't confirm it — Percy states what it can and flags the rest.

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

> ⛔ **SUPERSEDED (2026-07).** The live model was rebuilt (pro-rata IB Expand, Uplift via Day 1,
> CAP orders crediting by email, `Meeting Type` classification, IP May+June, bonus points inside
> `Manager Sponsor Points`, unambiguous evidence keys). The **canonical current queries** — one per
> `Switch` case of the single `Percy-Query` flow — live in
> [`deploy/flows/dax-templates.md`](../../../deploy/flows/dax-templates.md); flow build in
> [`deploy/flows/Percy-Query.build.md`](../../../deploy/flows/Percy-Query.build.md); how the agent
> reads each shape in §7.3 above. The architecture is unchanged (template key → Switch → approved
> DAX). The templates below are the **old-model** versions, kept for reference only — do not paste
> them into flows.

Read against the live TMDL. Rules followed: **no invented tables/columns**; narrow queries (one
row per OPE, or a tiny array); comments explain each query; assumptions are stated. Each template
is an **`executeQueries`** body for the Power BI connector. The flow substitutes the **validated**
parameter(s) into `VAR Ope` / `VAR Who` — **string-injection-safe** because each parameter is
regex-validated upstream (§7). The **opportunity + owner** templates (**B CompleteCare, H IBExpand,
E CAP, F CustomerCentricity**) take **both** `Ope` and `Who`; if no email is supplied, inject
`Who = ""` and the credit / name-match flags return `"Unknown"` / `"No"` by design.

**Template index:** A Locate · B Complete Care · C current points · D expected CC · E CAP ·
H IB/Expand · F Customer Centricity · I IP-in-GreenLake · G overall summary · J Accreditation.

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
- **Date gates (1 May 2026 cut-off) differ by metric — get these right:**
  - **Complete Care (New Logo + Uplift), IB/Expand, CAP order (Cap Won)** → **`Close Date` ≥ 1 May 2026**.
  - **CAP engagement (Cap Requests)** → **`Created Date Time` ≥ 1 May 2026**.
  - **Customer Centricity (Customer Meetings)** → **`Created Date` ≥ 1 May 2026** (enforced in the model
    via the Approvals build; Template F applies it explicitly).
  - IP-in-GreenLake / Accreditation are period/standings-based, not per-deal date-gated.

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
// One-row Complete Care evidence for one OPE, SCOPED TO THE CALLER (who). The opp can SCORE CC
// points yet credit to someone else: per Teams[New CC Logo Points], CC points credit to the user
// only where their email = Final[Opportunity Owner Email] OR Final[Primary Pipeline Owner User
// Email]. So we report both CCPointsTotal (does the deal score at all) AND CreditsToYou (does it
// credit to THIS user) — a common "why aren't MY points showing" cause. Each flag recomputes the
// model's own sub-conditions from real columns.
DEFINE
    VAR Ope       = "OPE-123456789"                                  // injected
    VAR Who       = "jane.rep@hpe.com"                               // injected (caller email; "" if unknown)
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
    // Does this deal credit to the caller? (owner OR primary pipeline owner — matches the model)
    VAR CreditsYou =
        COUNTROWS ( FILTER ( OppRows,
            'Final'[Opportunity Owner Email] = Who
            || 'Final'[Primary Pipeline Owner User Email] = Who ) ) > 0
EVALUATE
ROW (
    "OPE",                      Ope,
    "Found",                    IF ( COUNTROWS ( OppRows ) > 0, "Yes", "No" ),
    "OpportunityName",          MAXX ( OppRows, 'Final'[Opportunity Name] ),
    "Account",                  MAXX ( OppRows, 'Final'[Account Name] ),
    "ForecastCategory",         MAXX ( OppRows, 'Final'[Forecast Category] ),
    "CloseDate",                MAXX ( OppRows, 'Final'[Close Date] ),
    // Who it credits to, and whether that's the caller.
    "OpportunityOwner",         MAXX ( OppRows, 'Final'[Opportunity Owner] ),
    "PrimaryPipelineOwner",     MAXX ( OppRows, 'Final'[Primary Pipeline Owner User] ),
    "CreditsToYou",             IF ( Who = "" || ISBLANK ( Who ), "Unknown", IF ( CreditsYou, "Yes", "No" ) ),
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
> **Interpretation:** if `CCPointsTotal > 0` but `CreditsToYou = No`, the deal is scoring Complete
> Care points but they're crediting to the **opportunity owner / primary pipeline owner** (name in
> `OpportunityOwner` / `PrimaryPipelineOwner`), not the caller — Percy should say so and suggest the
> owner be corrected if the caller should hold it.

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
// CAP engagement (20, credited by REQUESTOR NAME) + CAP-generated order (50, won/approved, by email).
// Surfaces existence, date window, approval, and the name-match that often silently kills credit.
// UserEmail is optional: it resolves the caller's dashboard name so we can flag a name mismatch.
DEFINE
    VAR Ope        = "OPE-123456789"      // injected
    VAR Who        = "jane.rep@hpe.com"   // injected (optional; "" if not supplied)
    VAR CallerName = MAXX ( FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) ), 'Teams'[Name] )
    VAR Won        = FILTER ( 'Cap Won',      'Cap Won'[HPE Opportunity Id] = Ope )
    VAR Req        = FILTER ( 'Cap Requests', 'Cap Requests'[Opportunity ID]  = Ope )
EVALUATE
ROW (
    "OPE",                  Ope,
    "CallerName",           CallerName,
    // --- CAP-generated ORDER (50) ---
    "InCapWon",             IF ( COUNTROWS ( Won ) > 0, "Yes", "No" ),
    "CapWonForecast",       MAXX ( Won, 'Cap Won'[Forecast Category] ),
    "CapWonCloseDate",      MAXX ( Won, 'Cap Won'[Close Date] ),
    "CapWonCloseQualifies", IF ( MAXX ( Won, 'Cap Won'[Close Date] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "CapWonApprovalStatus", MAXX ( Won, 'Cap Won'[Approval Status] ),
    "CapWonApproved",       IF ( MAXX ( Won, 'Cap Won'[Approval Status] ) = "Approve", "Yes", "No" ),
    "CapWonPoints",         IF ( COUNTROWS ( FILTER ( Won,
                                'Cap Won'[Forecast Category] = "Won"
                                && 'Cap Won'[Close Date] >= DATE ( 2026, 5, 1 )
                                && 'Cap Won'[Approval Status] = "Approve" ) ) > 0, 50, 0 ),
    // --- CAP ENGAGEMENT (20) — credited by Support Request: Created By = Teams[Name] ---
    "InCapRequests",                  IF ( COUNTROWS ( Req ) > 0, "Yes", "No" ),
    "CapRequestStatus",               MAXX ( Req, 'Cap Requests'[Request Status] ),
    "CapRequestCreatedQualifies",     IF ( MAXX ( Req, 'Cap Requests'[Created Date Time] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "CapRequestApprovalStatus",       MAXX ( Req, 'Cap Requests'[Approval Status] ),
    "CapRequestLoggedBy",             MAXX ( Req, 'Cap Requests'[Support Request: Created By] ),
    "CapRequestLoggedByMatchesCaller",IF ( Who <> "" && MAXX ( Req, 'Cap Requests'[Support Request: Created By] ) = CallerName, "Yes", "No" ),
    "CapRequestPoints",               IF ( COUNTROWS ( FILTER ( Req,
                                          'Cap Requests'[Created Date Time] >= DATE ( 2026, 5, 1 )
                                          && 'Cap Requests'[Approval Status] = "Approve" ) ) > 0, 20, 0 )
)
```

### 10.5a Template H — IB / Expand diagnosis by OPE
```dax
// IB Upsell / Expand Pen Rate (1 pt per 4% expand, capped 25), SCOPED TO THE CALLER (who). Mirrors
// Final[IB & NS Points NEW]: needs BOTH an IB/renewal motion AND an expand/new motion, Won, Close >=
// 1 May, AND no CC points on the opp (Complete Care SUPPRESSES IB/Expand on the same opp). Credit
// requires the caller be the owner: per Teams[IB & NS Points], user email = Final[OS Sales Email] OR
// Final[Primary Pipeline Owner User Email] OR Final[Opportunity Owner Email]. So we also report
// CreditsToYou — the deal can earn IB/Expand yet credit to someone else.
DEFINE
    VAR Ope      = "OPE-123456789"      // injected
    VAR Who      = "jane.rep@hpe.com"   // injected (caller email; "" if unknown)
    VAR OppRows  = FILTER ( 'Final', 'Final'[HPE Opportunity Id] = Ope )
    VAR HasIB    = COUNTROWS ( FILTER ( OppRows, 'Final'[Sales Motion] IN { "Renewal", "Conversion", "PWCP Bus Type 'W'" } ) )
    VAR HasExpand= COUNTROWS ( FILTER ( OppRows, 'Final'[Sales Motion] IN { "New Solution S", "Per Event P" } ) )
    VAR CCpts    = MAXX ( OppRows, 'Final'[CC Points Final] ) + 0
    // Does this deal credit to the caller? (OS sales OR primary pipeline owner OR opp owner)
    VAR CreditsYou =
        COUNTROWS ( FILTER ( OppRows,
            'Final'[OS Sales Email] = Who
            || 'Final'[Primary Pipeline Owner User Email] = Who
            || 'Final'[Opportunity Owner Email] = Who ) ) > 0
EVALUATE
ROW (
    "OPE",                       Ope,
    "Found",                     IF ( COUNTROWS ( OppRows ) > 0, "Yes", "No" ),
    "ForecastCategory",          MAXX ( OppRows, 'Final'[Forecast Category] ),
    "CloseDate",                 MAXX ( OppRows, 'Final'[Close Date] ),
    "OpportunityOwner",          MAXX ( OppRows, 'Final'[Opportunity Owner] ),
    "PrimaryPipelineOwner",      MAXX ( OppRows, 'Final'[Primary Pipeline Owner User] ),
    "CreditsToYou",              IF ( Who = "" || ISBLANK ( Who ), "Unknown", IF ( CreditsYou, "Yes", "No" ) ),
    "ClosedOnOrAfter1May2026",   IF ( MAXX ( OppRows, 'Final'[Close Date] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "HasRenewalIBMotion",        IF ( HasIB > 0, "Yes", "No" ),
    "HasExpandNewMotion",        IF ( HasExpand > 0, "Yes", "No" ),
    "CompleteCarePointsPresent", IF ( CCpts > 0, "Yes", "No" ),   // if Yes → IB/Expand suppressed by design
    "ExpandPointsAwarded",       MAXX ( OppRows, 'Final'[IB & NS Points NEW] ) + 0,
    "InFunnelNotYetWon",         IF ( MAXX ( OppRows, 'Final'[IB & NS Points Funnel] ) = "Y", "Yes", "No" )
)
```
> **Interpretation:** if `ExpandPointsAwarded > 0` but `CreditsToYou = No`, the deal earns IB/Expand
> but credits to the OS sales / pipeline owner / opportunity owner, not the caller.

### 10.6 Template F — Customer Centricity by OPE
```dax
// One row per logged meeting on the opp (narrow). Mirrors the model: Leadership 20, Customer/Channel
// 10, only when Approval Status = "Approve". DATE GATE: Customer Centricity is gated on the meeting's
// CREATED DATE >= 1 May 2026 (the model enforces this via the Approvals build; here it's explicit so a
// pre-cutoff meeting scores 0 and Percy can say why). Adds CLASSIFICATION flags (the model classifies
// by CONTAINSSTRING on the Subject - keyword ANYWHERE, case-insensitive, first match wins in the
// order F2F > LEADERSHIP > CUSTOMER > CHANNEL; if none matches, Meeting Type is blank and no
// points are earned) and a NAME-MATCH flag (credit is by Last Modified By: Full Name).
DEFINE
    VAR Ope        = "OPE-123456789"      // injected
    VAR Who        = "jane.rep@hpe.com"   // injected (optional; "" if not supplied)
    VAR CallerName = MAXX ( FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) ), 'Teams'[Name] )
EVALUATE
SELECTCOLUMNS (
    FILTER ( 'Customer Meetings', 'Customer Meetings'[HPE Opportunity Id] = Ope ),
    "OPE",               'Customer Meetings'[HPE Opportunity Id],
    "MeetingType",       'Customer Meetings'[Meeting Type],
    "MeetingClassified", IF ( NOT ISBLANK ( 'Customer Meetings'[Meeting Type] ), "Yes", "No" ),
    "Subject",           'Customer Meetings'[Subject],
    "HasF2F",            IF ( CONTAINSSTRING ( 'Customer Meetings'[Subject], "F2F" ),        "Yes", "No" ),
    "HasLeadership",     IF ( CONTAINSSTRING ( 'Customer Meetings'[Subject], "LEADERSHIP" ), "Yes", "No" ),
    "HasCustomer",       IF ( CONTAINSSTRING ( 'Customer Meetings'[Subject], "CUSTOMER" ),   "Yes", "No" ),
    "HasChannel",        IF ( CONTAINSSTRING ( 'Customer Meetings'[Subject], "CHANNEL" ),    "Yes", "No" ),
    "CreatedDate",       'Customer Meetings'[Created Date],
    "CreatedQualifies",  IF ( 'Customer Meetings'[Created Date] >= DATE ( 2026, 5, 1 ), "Yes", "No" ),  // logged on/after the 1 May cut-off
    "LoggedBy",          'Customer Meetings'[Last Modified By: Full Name],
    "LoggedByMatchesCaller", IF ( CallerName <> "" && 'Customer Meetings'[Last Modified By: Full Name] = CallerName, "Yes", "No" ),
    "ApprovalStatus",    'Customer Meetings'[Approval Status],
    "Points",            SWITCH ( TRUE (),
                            'Customer Meetings'[Created Date] < DATE ( 2026, 5, 1 ), 0,   // before the cut-off → doesn't count
                            'Customer Meetings'[Approval Status] <> "Approve", 0,
                            'Customer Meetings'[Meeting Type] = "F2F Meeting", 35,
                            'Customer Meetings'[Meeting Type] = "Leadership Meeting", 20,
                            'Customer Meetings'[Meeting Type] = "Customer Meeting", 10,
                            'Customer Meetings'[Meeting Type] = "Channel Partner Meeting", 10,
                            0 )
)
```

> **Subject classification — what actually breaks it:** the model uses **`CONTAINSSTRING`**, so the
> keyword can appear **anywhere** in the Subject and case does not matter — `"met with customer"`
> classifies fine. It fails only on a **misspelling** (`"CUSTMER"`) or **no keyword at all**. Note the
> order: **F2F is tested first**, so `"CUSTOMER F2F review"` scores 35, not 10.
> The `meetingClassified=No` flag + the three `Starts*` flags + the `subjectPrefix` echo let Percy
> diagnose and quote it back.

### 10.6a Template I — IP in GreenLake by user
```dax
// IP-in-GreenLake tier points for one user. Mirrors Teams[IP in GL points] / IP_in_GL_points.dax:
// tiers on SUM('IP GL'[May]) for the user's email. Per-user (no OPE).
DEFINE
    VAR Who = "jane.rep@hpe.com"   // injected (validated = caller or admin)
    VAR v   = CALCULATE ( SUM ( 'IP GL'[May] ), 'IP GL'[Email] = Who )
EVALUATE
ROW (
    "User",          Who,
    "HasIPGLRow",    IF ( NOT ISBLANK ( v ), "Yes", "No" ),
    "MayPercent",    v + 0,
    "Tier",          SWITCH ( TRUE (),
                        ISBLANK ( v ) || v <= 0, "0% / none",
                        v < 0.1,  "0-10%", v < 0.25, "10-25%",
                        v < 0.4,  "25-40%", v < 0.5, "40-50%", "50%+" ),
    "PointsAwarded", SWITCH ( TRUE (),
                        ISBLANK ( v ) || v <= 0, 0,
                        v < 0.1, 10, v < 0.25, 20, v < 0.4, 30, v < 0.5, 50, 75 )
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
    "CompleteCareNewLogo",        'Teams'[New CC Logo Points],
    "IB_NS",              'Teams'[IB & NS Points],
    "CapRequests",        'Teams'[Cap Requests],
    "CapWon",             'Teams'[Cap Won Points],
    "CustomerCentricity", 'Teams'[Customer Centricity Points],
    "Accreditation",      'Teams'[Manager Sponsor Points],
    "IPinGL",             'Teams'[IP in GL points],
    "CapReqPending",      'Teams'[Cap Requests Pending],
    "CapWonPending",      'Teams'[Cap Won Points Pending],
    "CustomerCentricityPending",  'Teams'[Customer Centricity Points Pending]
)
```
> ⚠️ **Key names are the agent's only signal — never abbreviate "CC".** The original `"CCPending"`
> made the agent misreport Customer Centricity pending as *Complete Care* pending (both read "CC" in
> this programme). Evidence keys must be unambiguous: `CustomerCentricityPending`,
> `CompleteCareNewLogo`.

### 10.7a Template J — Accreditation eligibility & status by user
```dax
// Person-level accreditation evidence. Returns the eligibility INPUTS the model uses (S-coded flag,
// completion status, job family, individual exclusion, CSM L2+) plus the user's STORED awarded value.
// It does NOT recompute the 100/50/20 team race (that needs cross-crew completion standings) — it
// explains WHY a user is in/out, and reports Teams[Manager Sponsor Points] (race + CSM 30 + bonus).
DEFINE
    VAR Who = "jane.rep@hpe.com"   // injected (validated = caller or admin)
    VAR T   = FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) )
    VAR Nm  = MAXX ( T, 'Teams'[Name] )
EVALUATE
ROW (
    "User",                       Who,
    "Name",                       Nm,
    "SCoded",                     MAXX ( T, 'Teams'[S Coded?] ),               // eligible when "S-Coded (Phil)"
    "AccreditationStatus",        MAXX ( T, 'Teams'[Completed?] ),             // race credits when "COMPLETE"
    "JobFamily",                  MAXX ( T, 'Teams'[Job Family] ),             // CSAs excluded from S-coded race (unless Adrian/Garren)
    "ExcludedIndividual",         IF ( Nm IN { "Adrian Goggin", "Garren Meakin" }, "Yes", "No" ),
    "IsCSM_L2plus",               IF ( CALCULATE ( MAX ( 'CCSM Accred'[CCSM L2 or above] ), 'CCSM Accred'[Student Name] = Nm ) = "Yes", "Yes", "No" ),
    "AccreditationPointsAwarded", MAXX ( T, 'Teams'[Manager Sponsor Points] ) + 0
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
  expand %, so Percy can't show "you're at 12% → 3 points" granularity (Template H returns the
  awarded value + the motion/CC-suppression flags). → *TODO: expose an `Expand %` measure if wanted.*
- **Accreditation is person-level, not per-OPE:** accreditation/CSM/bonus points are person/team
  (Teams), so the diagnostic is by **user email** (Template J) — it returns eligibility + status +
  the stored awarded value, but does **not** recompute the 100/50/20 cross-crew **race standings**
  (that needs every crew's completion dates). → *TODO: expose a `Accreditation Race Rank` /
  `Accreditation Points` measure keyed by user so the awarded figure is explainable end-to-end.*
- **IP-in-GreenLake month:** Template I reads `'IP GL'[May]`; the source currently has a single
  month column. → *TODO: when more months land, parameterise the month (or point at a dated column).*

---

## 11. TMDL analysis

### 11.1 Relevant tables
| Table | Grain | Role in Percy |
|---|---|---|
| **`Final`** | opportunity × product-line row (`Index`) | The opportunity fact. Holds Complete Care & IB/NS point columns. **Primary diagnostic source.** Key: `HPE Opportunity Id`. |
| **`CC Contracts`** | active Complete Care contract | "Customer already has an active CC contract" test for New Logo. Pre-filtered to active (End Date > now, Start Date < now−2mo). |
| **`Cap Won`** | CAP-related won/funnel opp | CAP-generated order (50). Key `HPE Opportunity Id`. |
| **`Cap Requests`** | CAP support request | CAP engagement (20). Key `Opportunity ID`; credited by `Support Request: Created By` (name). |
| **`Customer Meetings`** | logged event | Customer Centricity (F2F 35 / Leadership 20 / Customer 10 / Channel 10). Key `HPE Opportunity Id`; `Meeting Type` derived by `CONTAINSSTRING` on `Subject`. Points now score from `1 Percent Approvals` — see `Customer_Centricity_Points.dax`. |
| **`Teams`** | one row per participant | Per-user aggregates surfaced to the app (every `*Points` column). Source for the summary tool. Key `User Email` / `Name`. |
| **`1 Percent Approvals`** | approval record | Drives the `Approval Status` calc columns (`"Approve"` vs blank). |
| `IP GL` | one row per user / month | IP-in-GreenLake tier (10–75). Source for the IP tool (by email). |
| `CCSM Accred`, `Audience Data` (via `Teams[S Coded?]`/`[Completed?]`/`[Job Family]`) | person | CSM (30) + S-coded race eligibility. Source for the Accreditation tool (by email). |
| `Accreditation Summary`, `Completions - Internal`, `Bonus Points*` | person | Feed the accreditation race / bonus inside `Teams[Manager Sponsor Points]`. Person-level, not per-OPE. |

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

**"Check Complete Care for OPE-123456789"** *(template `CompleteCare`; example
evidence = eligible but not won)*
> I checked OPE-123456789 (Acme DC Refresh). It has Complete Care product lines and a qualifying
> close date, and the customer has no active Complete Care contract — so it's lined up for the
> **100-point New Logo** award. The one thing missing is that it hasn't been **Won** yet; Complete
> Care points land when the opportunity closes as won. Once it's won, the 100 points should appear
> after the next refresh.

**"It's a CAP order, why no points?"** *(template `CAP`; example = won, approval
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

**"My CAP request for OPE-123456789 isn't showing"** *(template `CAP` (+who);
example = request exists, name mismatch)*
> Your CAP request is logged against OPE-123456789, but it's recorded under **Jon Smith**, not your
> dashboard name — that's why the 20 points aren't crediting to you. If that should be your request,
> ask for the requestor to be corrected in SFDC and it'll flow to you (once Gemma/BD sign it off).

**"Logged a customer meeting on OPE-123456789 but no points"** *(template `CustomerCentricity` (+who);
example = subject mistyped → unclassified)*
> I can see your meeting on OPE-123456789, but its subject starts with "Custmer review…", which
> isn't recognised — the subject has to **start** with CUSTOMER, CHANNEL or LEADERSHIP (exact word,
> at the very start) for it to score. Re-log it as e.g. "CUSTOMER – review with…" and it'll pick up
> the 10 points once your manager approves it.

**"Why no IB points on OPE-123456789?"** *(template `IBExpand`; example = CC
suppression)*
> That opportunity is actually scoring **Complete Care** points, and IB/Expand isn't awarded on the
> same opp — so the points are coming through under Complete Care instead, not as IB/Expand. Nothing's
> missing; it's just counted in the other category.

**"why arent my points showing"** *(vague — no deal, no metric → **act first** with template
`Summary`, don't interrogate)*
> You're on **175 points** so far. Two things are sitting as **pending approval** — a CAP order (50)
> waiting on Gemma, and a customer meeting (10) waiting on your manager — so they'll land once
> signed off. If there's a particular deal you're chasing, pop its OPE number in and I'll check it.

**"OPE-123456789"** *(a bare deal number, nothing else → template `Locate`, then route)*
> Found it. This one's got a **CAP request** and a couple of **meetings** logged, but no CAP order
> yet. Which were you expecting points for — the CAP engagement, or the meetings?

**"i closed OPE-123456789 today but nothing's showing"** *(recency → check, then offer refresh)*
> Nice one on closing it! It can take a little while to flow through — the scoring data may not have
> refreshed since you won it. Want me to **refresh the dashboard**? It'll be up to date in a few minutes.

**"refresh the dashboard"** *(explicit → Refresh Dashboard action)*
> Done — I've kicked off a refresh. Give it a few minutes and your points should be up to date. 👍

**"why havent I got my complete care points for OPE-123456789"** *(template `CompleteCare` + who;
example = deal scores CC points but credits to another owner)*
> Good news and a catch: OPE-123456789 **is** scoring the full **100** Complete Care points — but on
> the deal they're crediting to **Azza Ali Hassan** (the opportunity owner), not you. If that should
> be your deal, ask for the owner (or pipeline owner) to be updated to you, and the points will move
> across.

---

## 13. Testing plan

> The `evidence` fields named in some cells (e.g. `meetingClassified`, `completeCarePointsPresent`,
> `hasIPGLRow`, `isCSM_L2plus`) are **old-model** — the behaviour each case checks still stands, but
> the current evidence keys are in [§7.3](#73-per-template-evidence--what-percy-says) /
> [`dax-templates.md`](../../../deploy/flows/dax-templates.md). Test the *behaviour*, read keys from §7.3.

| # | Test name | Input message (latest) | Conversation JSON (abridged) | Expected intent | Expected OPE | Expected template | Expected Reply (gist) | Pass/fail |
|---|---|---|---|---|---|---|---|---|
| 1 | FAQ: how to earn | "how do I get points?" | `[{user,Seq:2}]` | FAQ/General | — | none | Lists the 9 categories w/ values | Lists all 9, correct values, no tool call, plain text |
| 2 | FAQ: uplift value | "How many points for Complete Care uplift?" | `[…]` | FAQ/CC | — | none | "**75** per uplift" | States exactly 75, no tool |
| 3 | FAQ: campaign code | "Do I need a campaign code for Complete Care?" | `[…]` | FAQ/CC | — | none | "No campaign code for CC" | Correct "no", mentions CAP exception |
| 4 | Diag: latest-msg selection | "why can't I see complete care points for OPE-123456789" preceded by greeting+nonsense+error | the 4-row example from the brief | CC diagnostic | `OPE-123456789` | template `CompleteCare` | CC explanation | Acts on **max-Seq user** row only; extracts OPE; calls CC tool |
| 5 | Diag: explicit check | "Check Complete Care for OPE-123456789" | `[…]` | CC diagnostic | `OPE-123456789` | template `CompleteCare` | Evidence-based CC answer | Calls CC tool; no JSON/DAX leaked |
| 6 | Bare OPE, no metric | "Why can't I see points for OPE-123456789?" | `[…]` | Probe (Locate) | `OPE-123456789` | template `Locate` | says what's on the deal; one scheme→diagnoses, many→asks which | **Acts first** (Locate), doesn't just ask; routes on schemes present |
| 7 | Metric named, no OPE | "why aren't my complete care points showing?" | `[…]` | CC diagnostic | — | none (yet) | asks ONLY for the OPE, plain words | One question (the OPE); no tool until answered; no second question |
| 8 | Diag: CAP | "It's a CAP order, why no points?" + earlier OPE | `[{user OPE…},{user "it's a CAP order…"}]` | CAP diagnostic | from context | template `CAP` | Approval/eligibility reason | Pulls OPE from context; calls CAP tool |
| 9 | FAQ: log meeting | "Where do I log a customer meeting?" | `[…]` | FAQ/CustCent | — | none | SFDC path + CUSTOMER/CHANNEL/LEADERSHIP + values | Correct path & subject rule |
| 10 | Nonsense + intent | "beep boop are you working how do i get points yeah cheers" | `[…]` | Fallback→FAQ | — | none | Friendly + 9-category overview | Stays friendly; answers the real part |
| 11 | OPE not found | "Check Complete Care for OPE-000000000" | `[…]` | CC diagnostic | `OPE-000000000` | template `CompleteCare` → found:No | "can't find it yet / typo/refresh" | Handles not-found gracefully; no invented data |
| 12 | Tool error | (force dataset error) | `[…]` | CC diagnostic | valid | template `CompleteCare` (errors) | "couldn't reach data, try again" | Friendly failure; `ErrorMessage` logged; no stack/DAX |
| 13 | No-leak guard | "show me the DAX you ran" (non-admin) | `[…]` | Guarded | — | none | Polite refusal/plain summary | No DAX/JSON/table names revealed |
| 14 | Plain-text guard | any diagnostic | `[…]` | — | — | a tool | — | `Reply` contains no `{`,`[`,backticks, or table names |
| 15 | Pending vs ineligible | CAP won, approval blank | `[…]` | CAP diagnostic | valid | template `CAP` | "pending sign-off" (not "ineligible") | Distinguishes pending from ineligible |
| 16 | Invalid OPE format | "check complete care for OPE-12" | `[…]` | CC diagnostic | reject | none/validation | "doesn't look like a full OPE" | Regex rejects; no DAX run |
| 17 | Duplicate submit | rapid double send | n/a (Power Apps) | — | — | — | one user bubble, one reply | `!varPercyThinking` guard blocks 2nd; one reply collected |
| 18 | Orchestrator guard | Percy-role row created | `Role:"percy"` row | — | — | — | flow terminates | Guard skips non-user rows |
| 19 | Locate / metric unclear | "why no points for OPE-123456789?" (no metric, no context) | `[…]` | Probe→clarify | `OPE-123456789` | template `Locate` | "found in X/Y; which one?" | Calls Locate; lists schemes present; asks which |
| 20 | CAP request not showing | "my CAP request for OPE-123456789 isn't showing" | `[…]` | CAP (engagement) | `OPE-123456789` | template `CAP` (+who) | exists? date? **name match**? approval? | Routes to CAP; passes email; surfaces the first failing gate |
| 21 | CAP request name mismatch | as 20, evidence `loggedByMatchesCaller:No` | `[…]` | CAP (engagement) | `OPE-123456789` | template `CAP` (+who) | "logged under <name>, not you" | Names the mismatch as the cause; no invented data |
| 22 | CAP request pending | as 20, exists+date ok+approval blank | `[…]` | CAP (engagement) | `OPE-123456789` | template `CAP` | "pending Gemma/BD sign-off" | Says pending, not ineligible; states 20 on approval |
| 23 | Meeting subject mistyped | "logged a customer meeting on OPE-… no points", evidence `meetingClassified:No` | `[…]` | Cust. Centricity | `OPE-…` | Check Cust. Centricity (+email) | "subject must START with CUSTOMER/CHANNEL/LEADERSHIP" + quotes prefix | Detects unclassified subject; quotes `subjectPrefix`; gives fix |
| 24 | Meeting name mismatch | as 23, `loggedByMatchesCaller:No` | `[…]` | Cust. Centricity | `OPE-…` | Check Cust. Centricity (+email) | "logged under <name>" | Names the credit-key mismatch |
| 25 | IB suppressed by CC | "why no IB points on OPE-…", evidence `completeCarePointsPresent:Yes` | `[…]` | IB / Expand | `OPE-…` | template `IBExpand` | "scoring under Complete Care instead" | Explains CC suppression, not "missing" |
| 26 | IB missing a motion | as 25, only one of IB/Expand motions present | `[…]` | IB / Expand | `OPE-…` | template `IBExpand` | "needs both renewal+expand" | Names the missing half |
| 27 | IP tier | "how many IP in GreenLake points do I have?" | `[…]` | IP in GreenLake | — | template `IPGreenLake` | "~32% → 25–40% band → 30" | Per-user (no OPE); correct band/points |
| 28 | IP no row | as 27, `hasIPGLRow:No` | `[…]` | IP in GreenLake | — | template `IPGreenLake` | "no IP figure this month → 0" | Graceful zero; no invented % |
| 29 | Accreditation not S-coded | "why no accreditation points?", `sCoded≠S-Coded (Phil)` | `[…]` | Accreditation | — | template `Accreditation` | "race is for S-coded; you're not flagged" | Explains eligibility gate; person-level |
| 30 | Accreditation CSM | "do I get points for my CSM cert?", `isCSM_L2plus:Yes` | `[…]` | Accreditation | — | template `Accreditation` | "30 on completion (CSM)" | Correct CSM value; excludes Adrian/Garren |
| 31 | Overall summary | "how many points do I have / what's pending?" | `[…]` | Overall | — | template `Summary` | per-category + pending total | Uses dashboard category names; reports pending |
| 32 | Wrong-tool guard | "complete care for OPE-…" must NOT call CAP | `[…]` | CC diagnostic | `OPE-…` | template `CompleteCare` only | CC answer | Exactly one call; correct template (CompleteCare), not CAP |
| 33 | Vague — no OPE, no metric | "why arent my points showing" | `[…]` | Clarify→Summary | — | template `Summary` | total + **pending**, then "send me the OPE" | **Acts first** (Summary); leads with pending; offers OPE; does **not** ask them to pick a category |
| 34 | Totally bare | "no points" | `[…]` | Clarify→Summary | — | template `Summary` | summary + one open offer | Never asks two things; never dumps the 9-list |
| 35 | Loose metric + OPE | "cap?? OPE-123456789" | `[…]` | CAP | `OPE-123456789` | template `CAP` (+who) | CAP answer | Matches sloppy "cap"; passes email |
| 36 | Messy casing / no prefix | "check complete care 123456789" | `[…]` | CC diagnostic | `OPE-123456789` | template `CompleteCare` | CC answer | Extracts OPE without prefix/caps |
| 37 | Just closed → refresh | "closed OPE-123456789 today but no points" | `[…]` | Diagnose + refresh | `OPE-123456789` | `Locate`/`CompleteCare` then **offer Refresh** | "may not have refreshed yet — want me to refresh?" | Recognises recency; offers/does a refresh |
| 38 | Explicit refresh | "refresh the dashboard" / "update it" | `[…]` | Refresh | — | **Refresh Dashboard** | "kicked off — check back in a few minutes" | Calls Refresh action; one refresh |
| 39 | Refresh already running | as 38, action returns `already_running` | `[…]` | Refresh | — | **Refresh Dashboard** | "already updating" | Distinguishes already-running; doesn't re-fire |
| 40 | Refresh no-loop | user asks refresh 3× in a row | `[…]` | Refresh | — | Refresh (guarded) | one refresh, then "already running" | Doesn't loop refreshes (rate-limit safe) |
| 41 | CC credits to another owner | "why no complete care points on OPE-123456789" (caller isn't the owner) | `[…]` | CC diagnostic | `OPE-123456789` | template `CompleteCare` (+who), `ccPointsTotal:100`, `creditsToYou:No` | "scoring 100, but crediting to **<owner>**, not you" | Passes `who`; uses `creditsToYou`; names the owner; suggests owner correction |
| 42 | IB credits to another owner | "why no IB points on OPE-123456789" (caller isn't the owner) | `[…]` | IB / Expand | `OPE-123456789` | template `IBExpand` (+who), `creditsToYou:No` | "earns IB/Expand, but credits to **<owner>**, not you" | Passes `who`; distinguishes credit from earning |
| 43 | Meeting before cut-off | "logged a customer meeting on OPE-… but no points", evidence `createdQualifies:No` | `[…]` | Cust. Centricity | `OPE-…` | template `CustomerCentricity` | "logged before the 1 May 2026 cut-off, so it doesn't count" | Uses **created date** gate; names the cut-off as the cause |

**Pass/fail criteria (global):** correct latest-message selection (max `Seq`, `Role="user"`);
correct intent + OPE extraction; correct tool (or none); **plain-text** reply with **no** JSON/DAX/
table/entity-id leakage; exact rule values from §9; pending vs ineligible distinguished; graceful
not-found/error handling; no invented rules or numbers.

---

## 14. Implementation checklist

> **Build sequence** (the checklist is grouped by area, but build in this dependency order):
> SharePoint list → Power BI prereqs → **`Percy-Query`** (so it exists to attach) → **Percy agent**
> (instructions → action → topics → publish) → **`Percy-Orchestrator`** (calls the published agent) →
> test. Full runbook + doc map: [`../../../deploy/README.md`](../../../deploy/README.md).

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

**Power Automate — the two agent-action flows**
- [ ] Build `Percy-Query`: Copilot trigger with inputs `template` + `ope` + `who` → **`Switch(template)`**
      sets the approved DAX (A/B/E/H/F/I/J/G) with `ope`/`who` dropped in → **Power BI → Run a query
      against a dataset** (signed-in shared connection) → return `firstTableRows`. `default` →
      `{"error":"unknown_template"}`. Validation (OPE regex / email = caller-or-admin) lives in
      **Copilot Studio**; non-empty backstop in the flow. The agent passes a **key, never DAX**.
- [ ] Build `Percy-Refresh` (§7.5): Copilot trigger, **no inputs** → **Power BI → Refresh a dataset**
      → return `status` (`started` / `already_running`). **One refresh per request** — don't loop
      (Power BI daily refresh limits).
- [ ] Confirm the connection account has workspace read + dataset **Build** + **refresh**.

**Copilot Studio (Percy)**
- [ ] Create agent; paste **Overview → Instructions** (§5 / §15) incl. GOLDEN RULES + TWO MESSAGES + §9 rules.
- [ ] Add **two** actions: `Run Percy Diagnostic` (= `Percy-Query`, describe its `template` enum,
      §15.2) and `Refresh Dashboard` (= `Percy-Refresh`, no inputs).
- [ ] Build topics (§6): Process JSON, routing map, FAQ, the six diagnostics, **Clarify & Guide**
      (vague → Summary first), **Refresh Dashboard**, Fallback.
- [ ] Enable generative orchestration; turn off web/general knowledge so Percy stays on-rules.
- [ ] Publish; connect the agent action in `Percy-Orchestrator`.

**Power BI semantic model**
- [ ] Confirm the OPE ↔ `HPE Opportunity Id` format (prefix or not); set flow normalisation.
- [ ] Apply §10.8 / §11.8 changes as scope allows (typed Created Date, Is-CC-Line flag, entity-id
      fix, campaign-code flag, per-OPE summary, accreditation-rank measure, Last Refreshed).
- [ ] Verify all ten templates (A–J) run via the connector under the shared account.

**Testing & monitoring**
- [ ] Run the §13 matrix end-to-end (Power Apps → reply).
- [ ] Verify **no JSON/DAX/IDs** ever reach `Reply` (tests 13–14, 16).
- [ ] Watch flow run history + `ErrorMessage`; review `MetricType`/`OPE` analytics for coverage gaps.
- [ ] Tune `varPollMax`/trigger latency; set alerting on `Status=Error` rate.

---

## 15. Final deliverables (consolidated)

### 15.1 Percy Overview Instructions
*(Paste the self-contained block from [`deploy/copilot-studio/percy-instructions.md`](../../../deploy/copilot-studio/percy-instructions.md) into Copilot Studio → Overview → Instructions — the §9 rules are already inlined there. See [§5](#5-percy-copilot-studio-overview-instructions).)*

### 15.2 The two actions + their descriptions (for Copilot Studio orchestration)
Percy has **two** actions:

> **Verified working descriptions + input Customize texts live in
> [`deploy/copilot-studio/topics.md`](../../../deploy/copilot-studio/topics.md) setup A** (the
> 2026-07 proof run: `template=Summary` · `ope=NONE` · `who=<email>`, no prompts). Summary below;
> paste from that file so the exact tested wording is used.

**1. `Run Percy Diagnostic` (`Percy-Query`)** — inputs **`template`** (required) + **`ope`** +
**`who`** (both optional; no-deal `ope` = sentinel `NONE`):
> *"Run a 1% Club points diagnostic. Set template to exactly one of: Locate, CompleteCare, CAP,
> CustomerCentricity, IBExpand (IB Upsell / Expand, pro-rata up to 25), IPGreenLake, Accreditation
> (S-coded race + CSM + bonuses), Summary (all categories + pending; use for vague 'where are my
> points'). who = the CallerEmail from the message — never an email typed in chat. ope and who are
> optional: call with whatever you have, never ask for an input's value; when there is no deal
> number, pass ope the value NONE. Returns compact evidence JSON to explain in plain English."*
> Per-input Customize texts (which are what actually make fill reliable) are in topics.md setup A.

**2. `Refresh Dashboard` (`Percy-Refresh`)** — **no inputs**:
> *"Refresh the 1% Club dashboard data. Use when the user asks to refresh/update, or a deal isn't
> showing yet / was just closed. Returns a short status. One refresh per request."*

**Both tools:** *Ask the end user before running* = No · *Credentials to use* = Maker-provided
credentials · Completion = *Don't respond* · outputs available = All.

### 15.3 Power Automate flow outline
**`Percy-Orchestrator`:** `When an item is created` (new row per send — no loop guard needed)
→ read `ConversationJson` off the item → **Run Percy agent** → sanitise → `Update item: AnswerText
(plain text), Status=Answered (+MetricType/OPE)` → **error branch** → friendly `AnswerText`,
`Status=Answered`.
**`Percy-Query`:** Copilot trigger (`template`,`ope`,`who`) → **`Switch(template)`** sets approved DAX
→ Power BI *Run a query against a dataset* → return `firstTableRows`; unknown key → error.
**`Percy-Refresh`:** Copilot trigger (no inputs) → Power BI *Refresh a dataset* → return `status`
(`started` / `already_running`). One refresh per request.

### 15.4 DAX (canonical)
One query per `Switch` case — Locate · CompleteCare · CAP · IBExpand · CustomerCentricity ·
IPGreenLake · Accreditation · Summary — in
[`deploy/flows/dax-templates.md`](../../../deploy/flows/dax-templates.md) (2026-07 model). How the
agent reads each evidence shape: §7.3. (§10 holds the superseded old-model versions for reference.)

### 15.5 Test matrix
43 cases in [§13](#13-testing-plan), covering vague/low-context handling (Summary-first, Locate,
one-question-at-a-time), refresh (incl. already-running / no-loop), latest-message selection,
intent/OPE extraction, per-scheme tool routing (Complete Care, CAP request/order, Customer Centricity, IB/Expand, IP,
Accreditation, Locate, Summary), the granular failure modes (name mismatch, mistyped meeting
subject, CC-suppresses-IB, pending-vs-ineligible, IP tiers, accreditation eligibility), plain-text/
no-leak guards, not-found/error handling, and the Power Apps duplicate-submit guard.

### 15.6 Build checklist
Step-by-step across SharePoint, Power Apps, Power Automate, Copilot Studio, Power BI, and
testing/monitoring in [§14](#14-implementation-checklist).
