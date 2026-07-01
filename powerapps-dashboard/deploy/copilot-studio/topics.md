# Percy — topics for a **generative-orchestration** agent (paste-in)

Percy runs with **generative orchestration ON**. That changes how topics work:

- **Routing is done by the agent**, from the **Overview → Instructions** + the **two action
  descriptions** — not by trigger-phrase matching. Every custom topic is triggered by **"The agent
  chooses"**: you write a short **description** of *when* the topic applies and the agent routes to it.
- **You build far fewer topics.** The `Run Percy Diagnostic` action already covers all eight
  diagnostics; the agent calls it and explains the result in plain English using the instructions. So
  the per-scheme diagnostic topics are **optional** — build one only when you want that scheme's
  wording locked/deterministic.
- **The conversation-JSON parsing is not a topic.** The agent reads `ConversationJson`, finds the
  latest user turn, and scans for an OPE **per the instructions** — no Power Fx topic needed.

Full decision logic per topic: [`PERCY_BUILD_PACK.md` §6](../../formulas/percy/backend/PERCY_BUILD_PACK.md#6-percy-topic-design).

---

## Step 0 — the two actions ARE the routing engine (build these first)

With orchestration on, these two agent-level **Actions** (Tools) do most of the work. Add them under
the agent's **Tools/Actions**, paste the descriptions (build pack §15.2) so the orchestrator fills the
right inputs, then most diagnostics need **no topic at all**.

1. **`Run Percy Diagnostic`** = the **`Percy-Query`** flow — inputs **`template`** (Locate ·
   CompleteCare · CAP · IBExpand · CustomerCentricity · IPGreenLake · Accreditation · Summary),
   **`ope`**, **`who`**. The agent passes a **template key, never DAX**. Description:
   > *"Run a 1% Club points diagnostic. Set `template` to exactly one of: `Locate` (does the deal exist
   > / which schemes — input ope), `CompleteCare` (New Logo 100 / Uplift 75 — ope + user email), `CAP`
   > (CAP engagement 20 + order 50, incl. 'request isn't showing' — ope + email), `CustomerCentricity`
   > (logged customer/channel/leadership meetings, incl. mistyped subject — ope + email), `IBExpand`
   > (IB Upsell / Expand ≤25 — ope + email), `IPGreenLake` (monthly IP tier 10–75 — email),
   > `Accreditation` (S-coded race + CSM — email), `Summary` (all categories + pending — email). Pass
   > the user's email as `who` for CompleteCare/IBExpand/CAP/CustomerCentricity so the check confirms
   > the points credit to THIS person. Returns compact evidence JSON to interpret in plain English.
   > Never send DAX — only a template key and ope/who."*
2. **`Refresh Dashboard`** = the **`Percy-Refresh`** flow — **no inputs**. Description:
   > *"Refresh the 1% Club dashboard data. Use when the user asks to refresh/update, or a deal isn't
   > showing yet / was just closed. Returns a short status. One refresh per request."*

> **`who` in a topic:** map it to the **`UserEmail`** the orchestrator passes into the agent (it's on
> the SharePoint row). Reference that variable wherever a topic calls the action with `who`.

---

## How to create a topic (click-by-click)

1. **Topics → + Add a topic → From blank**; **name** it (top-left).
2. Click the **Trigger** node → **Change trigger** → **"The agent chooses"** → paste the topic's
   **description** (below). **Don't** pick *"A message is received"* (fires on every message and
   swallows everything).
3. Add nodes with **+**: **Send a message** (plain-text answer) · **Ask a question** (capture the OPE
   into a variable) · **Add a condition** (branch) · **Add a tool** (call `Run Percy Diagnostic` /
   `Refresh Dashboard`, map inputs, read the output in a following message).
4. **Save**, then exercise it in the **Test** pane.

---

## Topics to build

Legend: **[Build]** = create it · **[Optional]** = the `Run Percy Diagnostic` action + instructions
already handle this; build only to lock the wording.

### 1. General 1% Club FAQ  **[Build]**  *(no tool)*
- **The agent chooses — description:** *"Use when the user asks how 1% Club points are earned, how many
  points a category is worth, whether a campaign/code is needed, or where to log an activity — general
  programme-rules questions that don't need a specific deal (OPE)."*
- **Nodes:** a single **Send a message** with the answer. For "how do I get points?", list the nine
  ways (build pack §9) with exact values. No action call. *(A topic here gives consistent, exact rule
  wording instead of a paraphrase.)*

### 2. Refresh Dashboard  **[Build]**  *(calls `Refresh Dashboard`)*
- **Description:** *"Use when the user asks to refresh or update the dashboard, or says their
  points/deal aren't showing yet, they just closed a deal today, or the data isn't updating."*
- **Nodes:** **Add a tool → Refresh Dashboard** → **Add a condition** on the returned status →
  **Send a message**: *started* → "I've kicked off a refresh — give it a few minutes and check again.";
  *already running* → "It's already updating — check back shortly." **One refresh per request.**

### 3. Clarify & Guide — the vague message  **[Build]**  *(calls `Run Percy Diagnostic` → Summary)*
- **Description:** *"Use when the user asks a vague question about their points with no specific deal
  and no clear category — e.g. 'why aren't my points showing', 'where are my points', 'I should have
  more', 'nothing's showing up'."*
- **Nodes:** **Add a tool → Run Percy Diagnostic** (`template = Summary`, `who = UserEmail`) →
  **Send a message**: lead with their **total** and what's **pending** (waiting on approval is the #1
  reason points look missing), then **offer** one next step — "Chasing a particular deal? Send me the
  OPE and I'll check it." **Do not** ask them to pick a category, and never ask two things at once.

### 4. Complete Care Diagnostic  **[Optional]**  *(→ `CompleteCare`)*
- **Description:** *"Use when the user asks why Complete Care / New Logo / uplift points are or aren't
  showing for a specific deal (OPE)."*
- **Nodes:** **Condition** — is the OPE known (from context)? If not, **Ask a question** ("What's the
  deal number? looks like OPE-123456789"). → **Add a tool → Run Percy Diagnostic** (`template =
  CompleteCare`, `ope`, `who = UserEmail`) → **Send a message** explaining the flags: found / product
  line / sales motion / close date / active contract / awarded points / in-funnel / **creditsToYou**.
  **If it scores points but `creditsToYou = No`, that's the answer** — it credits to the
  opportunity/pipeline owner, not the caller.

### 5. CAP Diagnostic  **[Optional]**  *(→ `CAP`)*
- **Description:** *"Use when the user asks about CAP points for a deal — a CAP engagement/request or a
  CAP-generated order, incl. 'my CAP request isn't showing', 'Gemma', 'campaign code'."*
- **Nodes:** (OPE condition as above) → **Run Percy Diagnostic** (`template = CAP`, `ope`, `who`) →
  **Send a message** naming the FIRST failing gate. *Engagement:* exists in CAP requests? → created
  ≥ 1 May 2026? → logged-by name matches the caller? → approval blank = **pending Gemma/BD sign-off**
  (not "ineligible"). *Order:* in CAP-won? → won? → close ≥ 1 May? → approval. Mention the campaign
  code **UKIMEA CSLV CAP Adoption** for orders but say you can't verify it from here.

### 6. Customer Centricity Diagnostic  **[Optional]**  *(→ `CustomerCentricity`)*
- **Description:** *"Use when the user asks why a logged customer / channel / leadership meeting (or
  'event/activity') isn't scoring for a deal."*
- **Nodes:** (OPE condition) → **Run Percy Diagnostic** (`template = CustomerCentricity`, `ope`,
  `who`) → **Send a message** per meeting: **classified?** (subject must START with CUSTOMER / CHANNEL
  / LEADERSHIP — quote back the prefix for typos like "CUSTMER"); **createdQualifies?** (meetings
  created **before 1 May 2026** don't count — Customer Centricity gates on **created date**);
  name-match; approval (manager approves weekly). Values: 10 customer/channel, 20 leadership.

### 7. IB / Expand Diagnostic  **[Optional]**  *(→ `IBExpand`)*
- **Description:** *"Use when the user asks about IB Upsell / Expand (pen-rate) points for a deal —
  'IB', 'expand', 'renewal + expand', 'win-back', 'naked box'."*
- **Nodes:** (OPE condition) → **Run Percy Diagnostic** (`template = IBExpand`, `ope`, `who`) →
  **Send a message**: needs BOTH a renewal/IB motion AND an expand/new motion, **Won**, close ≥ 1 May.
  **Two gotchas:** (1) if the deal already scores Complete Care, IB/Expand is **suppressed on that deal
  by design** — say so; (2) if it earns points but **`creditsToYou = No`**, it credits to the
  owner / pipeline / OS-sales person, not the caller. Not won → shows in the funnel only.

### 8. IP in GreenLake Diagnostic  **[Optional]**  *(→ `IPGreenLake`, user-level)*
- **Description:** *"Use when the user asks about IP-in-GreenLake points or their monthly IP % — this
  is per-user, not per-deal."*
- **Nodes:** **Add a tool → Run Percy Diagnostic** (`template = IPGreenLake`, `who = UserEmail`) →
  **Send a message** with the % band and tier (0–10→10, 10–25→20, 25–40→30, 40–50→50, 50%+→75). No OPE
  needed; no row / 0% → 0.

### 9. Accreditation Diagnostic  **[Optional]**  *(→ `Accreditation`, user-level)*
- **Description:** *"Use when the user asks about accreditation-race or CSM points, being 'S-coded',
  'the race', or completion — person/team-level, not per-deal."*
- **Nodes:** **Add a tool → Run Percy Diagnostic** (`template = Accreditation`, `who = UserEmail`) →
  **Send a message**: S-coded? accreditation COMPLETE? excluded job family/individual? CSM L2+ → 30.
  The 100/50/20 is a **team race** decided by completion standings — the tool shows eligibility/status.

### 10. Fallback / Clarification  **[Build — customise the system topic]**  *(usually no tool)*
- **Trigger:** this is the built-in **Fallback** system topic (fires when nothing else matches) — edit
  it, don't recreate it.
- **Nodes:** greeting / nonsense / mixed → be friendly, pull out any real intent and answer it; if
  there's genuinely none, one line on what Percy can do (points questions · check a deal · refresh the
  board). Off-topic → politely redirect. **Never loop; never dump the category list.**

> **Not a topic — `Process Conversation JSON`:** under orchestration the agent parses the transcript
> and finds the latest user turn + any OPE from the **instructions**. Don't build a topic for it.

---

## Settings (confirm these)
- **Generative orchestration: ON.** (This is why triggers are "The agent chooses", not phrases.)
- **General knowledge / web search: OFF** — keeps Percy strictly on the programme rules.
- **Authentication:** as your tenant requires; the agent runs server-side from the orchestrator flow.

## Minimum viable set
If you build nothing else: the **two actions** + **General FAQ** + **Clarify & Guide** + the
**Fallback** topic already give a complete Percy — the action + instructions cover every diagnostic.
Add the per-scheme **[Optional]** topics later only where you want the wording locked.
