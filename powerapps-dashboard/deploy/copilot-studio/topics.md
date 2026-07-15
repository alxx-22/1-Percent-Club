# Percy — topics, one complete recipe each (generative orchestration)

Percy runs with **generative orchestration ON**, so every custom topic is triggered by **"The agent
chooses"** (a plain-language description) — not trigger phrases. Each topic below is a **standalone,
click-by-click recipe**: create → trigger → inputs → every node with exact values and message text.
Build them top to bottom; you don't need to read anything else.

---

## Before you build any topic (one-time setup)

**A. Add the two Actions first** (agent → **Tools/Actions → + Add a tool**). Topics call these.
- **`Run Percy Diagnostic`** = the `Percy-Query` flow. Inputs: `template`, `ope`, `who`.
  **The tool's Description field is what orchestration uses to route AND fill inputs — an empty or
  one-word description makes AI-fill flaky.** Paste this into **Details → Description**:
  > *"Run a 1% Club points diagnostic. Set `template` to exactly one of: `Locate` (does the deal
  > exist / which schemes — needs ope), `CompleteCare` (New Logo 100 / Uplift 75 — ope + email),
  > `CAP` (CAP engagement 20 + order 50, incl. 'request isn't showing' — ope + email),
  > `CustomerCentricity` (logged customer/channel/leadership meetings — ope + email), `IBExpand`
  > (IB Upsell / Expand ≤25 — ope + email), `IPGreenLake` (monthly IP tier 10–75 — email),
  > `Accreditation` (S-coded race + CSM — email), `Summary` (all categories + pending — email; use
  > for vague 'where are my points' questions). Pass the user's email as `who` (the CallerEmail from
  > the message — never an email typed in chat). Leave `ope` empty when there's no deal number.
  > Returns compact evidence JSON to explain in plain English. Never send DAX."*

  Then, on the tool page's **Inputs** section, keep every input's **Fill using = "Dynamically fill
  with AI"** (do NOT pin `template` here — this page is global; orchestration must be free to pick
  other templates), and use **Customize** (the pencil) to give each input a description — this is
  the per-input steering that replaces any topic-level override:
  - `template`: *"Exactly one of: Locate, CompleteCare, CAP, IBExpand, CustomerCentricity,
    IPGreenLake, Accreditation, Summary. For a vague points question with no deal, use Summary."*
  - `ope`: *"The OPE deal id (like OPE-123456789) if one appears anywhere in the conversation;
    otherwise leave empty. Never ask for it when the template is Summary, IPGreenLake or
    Accreditation."*
  - `who`: *"Always the CallerEmail value from the top of the message — never an email typed in the
    chat."*
- **`Refresh Dashboard`** = the `Percy-Refresh` flow. **No inputs.** Description:
  > *"Refresh the 1% Club dashboard data. Use when the user asks to refresh/update, or a deal isn't
  > showing yet / was just closed. Returns a short status. One refresh per request."*

**B. The caller's email (`who`) — where it actually comes from.** A variable does **not** fill
itself: the **`Percy-Orchestrator` flow embeds the caller's details in the message** it sends the
agent — three labelled lines (see
[`../flows/Percy-Orchestrator.build.md`](../flows/Percy-Orchestrator.build.md) step 3):
`CallerEmail:` (the verified login → used as **`who`** on every tool call), `Conversation:` (the JSON
transcript), and `CallerName:` (the display name → **personalisation only**, never for
credit/name-match checks — the Instructions tell Percy to greet by first name occasionally).
- **In a topic's Tool node, set the `who` input to "Fill with AI" / dynamic** — the agent supplies
  CallerEmail from the message. This is the default and needs no variable plumbing.
- *Structured alternative:* create a **Global variable** (Variables → + New → Global) with
  **"External sources can set values"** ticked, have the calling flow map `UserEmail` into it (only
  possible if your agent action exposes variable inputs), and map `who` = that variable.
- ⚠️ **Never use `System.User.Email`** — the agent runs under the shared service account, so that
  would be the service account, not the salesperson.

**C. Every "The agent chooses" trigger** is set the same way: click the **Trigger** node → **Change
trigger** (the ⇄ icon) → **The agent chooses** → paste the topic's description into the box.

**D. Where the first-name touch happens.** A **Send a message** node is static text — topics have no
CallerName variable, so a scripted message **can't** say "Hi Sarah". The personalisation lives in
**agent-composed replies** (FAQ answers, diagnostic explanations, anything orchestration writes), per
the Instructions' USING THEIR NAME section. If you want a topic's final reply personalised too:
**delete its closing Send-a-message and end the topic after the Tool node** — orchestration then
composes the reply from the tool result + the Instructions (name, tone, wording), at the cost of the
locked wording. Keep the static message where determinism matters more.

---

## Topic 1 — General 1% Club FAQ  **(recommended: DON'T build it — instructions answer better)**

*Rules/how-to questions with exact values. No action call.*

> **A `Send a message` node is static** — it sends its exact text verbatim, every time. Someone asking
> "do I need a code for uplift?" would get the whole nine-way list. **The tailored alternative needs
> no topic at all:** the programme rules are already pasted **verbatim** into the agent's
> **Instructions** (the §9 block), with the routing line *"FAQ → answer from the Programme Rules
> below. No tool. Give the exact number."* With no topic intercepting, the agent answers each FAQ
> **generatively, scoped to what was asked** — "campaign code for uplift?" gets just the no-code /
> 75-points answer. The verbatim rules + the hard rule "NEVER invent programme rules or point values"
> keep the numbers exact.
>
> **So: skip this topic.** If you already built it, **delete or disable it** — its trigger swallows
> FAQ questions and forces the static wall of text. Just confirm the §9 rules are in the pasted
> instructions, then test with a narrow question ("how many points for a leadership meeting?") and
> expect a short, specific answer — not the list.

<details><summary><b>Static fallback</b> (only if you must guarantee identical wording every time)</summary>

1. **Create:** Topics → **+ Add a topic → From blank**. Rename to **`General 1% Club FAQ`**.
2. **Trigger → The agent chooses:**
   > *Use when the user asks how 1% Club points are earned, how many points a category is worth,
   > whether a campaign/code is needed, or where to log an activity — general programme-rules
   > questions that don't need a specific deal (OPE).*
3. **Node — Send a message**, paste exactly:
   > Here's how you earn 1% Club points:
   > • **Complete Care – New Logo: 100** — a new Complete Care deal (customer has no active CC
   >   contract), created from 1 May 2026. Auto-calculated, no code needed.
   > • **Complete Care – Uplift: 75** — per uplift in an existing customer environment.
   > • **IB Upsell / Expand: 1 point per 4% expand, max 25** — deal has a renewal *plus* an expand.
   > • **IP in GreenLake (monthly %):** 0–10% = 10, 10–25% = 20, 25–40% = 30, 40–50% = 50, 50%+ = 75.
   > • **CAP Engagement: 20** — per approved CAP request (log in SFDC → Support Requests → CAP Team
   >   Engagement/Support; signed off by Gemma/BD).
   > • **CAP-Generated Order: 50** — won, campaign code **UKIMEA CSLV CAP Adoption**, close date after
   >   1 May 2026 (validated by Gemma).
   > • **Accreditation (S-coded race): 100 / 50 / 20** for your team's 1st / 2nd / 3rd completion.
   > • **Accreditation (CSMs): 30** per completion.
   > • **Customer Centricity: 10** per customer meeting, **10** per channel meeting, **20** per
   >   leadership introduction (log via Opportunity → Activities → New Event; the Subject must start
   >   CUSTOMER / CHANNEL / LEADERSHIP; your manager approves weekly).
   >
   > Want me to check a specific deal? Send me the OPE and I'll take a look.
4. **Save**, test with *"how do I get points?"*.
</details>

---

## Topic 2 — Refresh Dashboard  **(build this)**

*Kicks a data refresh when someone's numbers aren't showing yet.*

1. **Create:** + Add a topic → From blank. Rename to **`Refresh Dashboard`**.
2. **Trigger → The agent chooses:**
   > *Use when the user asks to refresh or update the dashboard, or says their points/deal aren't
   > showing yet, they just closed a deal today, or the data isn't updating.*
3. **Node — call the Refresh flow.** This node runs `Percy-Refresh` and captures what it returns.
   - Under the trigger click **+ → Add a tool**.
   - In the tool list, pick **Refresh Dashboard** (the `Percy-Refresh` flow you added in setup Step A).
     *If it isn't listed, choose **+ Add a tool / New tool → Flow**, find `Percy-Refresh`, add it, then
     select **Refresh Dashboard** here.*
   - **Inputs:** none — `Percy-Refresh` takes no inputs, so there's nothing to fill in.
   - **Outputs:** the flow's "Respond to Copilot Studio" returns a **Text** output named **`status`**;
     Copilot Studio stores it in a variable of the same name. Click the node to confirm you see
     **`status`** — that's what Step 4 branches on. Values: **`started`** / **`already_running`**.
   - *If you built the **minimal** `Percy-Refresh` (returns `"started"` only), `status` is always
     `started` and the other branches below simply won't fire — that's fine.*
   - ⚠️ **"Output status has been removed because variable data type not eligible" / "Destination
     agent was updated" / "Output binding 'status' is not found, refresh this flow to get the latest
     bindings" / output variable shows `unknown`:** the flow was re-saved after this node was added,
     so the node holds a stale snapshot of the flow's outputs. **A page/tool refresh will NOT fix
     this** — once the topic variable is typed `unknown` it stays broken; it must be rebuilt. (The
     variable is scoped to this topic — nothing elsewhere binds it, and topic build order is
     irrelevant.) In order:
     1. Flow side: confirm *Respond to the agent* has one **Text** output `status` whose value is the
        **Outputs of `StatusOut`** (hover the chip to check it's not another action's), and save.
     2. **Delete the Tool node** in the topic (⋯ → Delete) and **re-add it** (+ → Add a tool →
        Refresh Dashboard) — a fresh node reads the current schema; on its output row click **`>` →
        Create a new variable** (`Topic.status`, string). *(This is on the Tool **node in the topic
        canvas** — Outputs row, right-hand chip. NOT the agent-level **Tools → Percy-Refresh** page:
        that page only defines display name/description and has no variables. While you're on that
        page though, give `status` a description — "'started' = new refresh kicked off,
        'already_running' = one in progress, 'error' = failed" — it helps orchestration read it.)*
     3. **Re-select `Topic.status` in the Condition node** — it still points at the dead variable.
     4. Still `unknown`? The **agent-level tool** is caching the old schema: agent → **Tools** →
        remove Percy-Refresh → re-add it → redo step 2. And if the flow shows under Copilot Studio's
        **Flows** tab as an agent flow, make sure it's **published**, not draft.
     This applies any time a flow's inputs/outputs change after it's attached: the mapping never
     auto-heals — rebuild it.
4. **Node — Add a condition:** **+ → Add a condition**.
   - Condition: **`status`** **is equal to** `already_running`.
     - **Send a message:** *"It's already updating — give it a few minutes and your points will be
       current."*
   - **+ New branch → `status` is equal to** `error`.
     - **Send a message:** *"I couldn't start a refresh just now — try again shortly, or ping the
       programme team."*
   - **All other conditions (else):**
     - **Send a message:** *"I've kicked off a refresh — it takes a few minutes. Check back shortly
       and your points should be up to date."*
   - *Personalised variant (setup D): skip this Condition + messages entirely and end the topic after
     the Tool node — the agent composes the reply from `status` + the Instructions ("Good news,
     Sarah — refresh is running…"), at the cost of locked wording.*
5. **Save.** **Test:** type *"my points aren't showing, refresh it"* → expect the "kicked off"
   message. **One refresh per request** — don't add a loop.

---

## Topic 3 — Clarify & Guide (the vague message)  **(build this — most common)**

*Handles "why aren't my points showing" with no deal and no category: act first, then offer.*

1. **Create:** + Add a topic → From blank. Rename to **`Clarify and Guide`**.
2. **Trigger → The agent chooses:**
   > *Use when the user asks a vague question about their points with no specific deal and no clear
   > category — e.g. "why aren't my points showing", "where are my points", "I should have more",
   > "nothing's showing up".*
3. **Node — Add a tool:** **+ → Add a tool → Run Percy Diagnostic**.
   > ⚠️ **Pick the TOOL ("Run Percy Diagnostic"), not the raw flow ("Percy-Query") from the Power
   > Automate section.** Adding the raw flow gives an **"Action"** node that hard-requires every
   > input (red *"Input variable 'ope' is required"*) and has **no AI-fill option**. If your node's
   > header says "Action" / "Power Automate inputs", delete it and re-add via the tool.

   **Leave the node at "Inputs (0)" — no overrides.** That's correct, not empty-broken: tool inputs
   are **AI-filled by default** and "(0)" counts *overrides*, of which you need none. Don't fight the
   "+ Set value" panel (it's a variable picker, not an input list) — the steering lives at the
   **tool level** instead: the tool's **Description** + per-input **Customize** descriptions (setup A)
   make the agent pick `Summary`, fill `who` = CallerEmail, and leave `ope` empty. Two prerequisites
   make this prompt-free:
   1. **`ope`/`who` are optional on the `Percy-Query` trigger** (see `Percy-Query.build.md` step 2) —
      while they're *required*, AI-fill can't pass blank and falls back to **prompting the user**
      ("Please enter your input for ope"), which this act-first topic must never do.
   2. **The tool + input descriptions from setup A are pasted** — an empty tool description makes
      AI-fill flaky.
   - Note the output variable (e.g. **`evidence`**).

   > **Testing in the Test pane:** the pane sends only your raw message — there's **no
   > `CallerEmail:` wrapper** (the orchestrator adds it in production), so a *"Please provide the
   > input for 'who'"* prompt in the pane is **expected** while `who` is required. Either answer it,
   > or simulate production by pasting one message shaped like the orchestrator's
   > (`CallerEmail: you@hpe.com` ⏎ `Conversation: [{"Seq":1,"Role":"user","Body":"why aren't my
   > points showing"}]` ⏎ `CallerName: Your Name`). Making `who` optional on the flow trigger also
   > stops the pane prompt.
   - *Can't get `template` mapped at all? Leave **Inputs (0)** — the trigger description + the
     instructions playbook steer the agent to Summary anyway; you only lose the hard guarantee.*
   - *If the picker shows stale `text` / `text_1` / `text_2` variables from earlier deleted nodes,
     delete them via the **{x} Variables** panel to keep it clean.*

   > **No "Dynamically fill with AI" option in your tenant?** Then delete this whole topic instead —
   > the Instructions' TWO MESSAGES playbook A already makes orchestration do exactly this (Summary,
   > who = CallerEmail, total + pending, offer the OPE), personalised. The topic is optional
   > determinism, not functionality.
4. **Ending — let the agent compose the reply (recommended, setup D):** end the topic after the Tool
   node (no Send-a-message). Orchestration writes the answer from `evidence` + the Instructions —
   personalised and specific, e.g. *"Here's where you stand, Sarah: 120 points, with 40 pending
   approval — that's the usual reason points look missing. Chasing a particular deal? Send me the OPE
   and I'll check it."* *(A static Send-a-message can't do the name or the numbers; only add one if
   you must lock the wording, and then keep it generic. Never ask them to pick a category.)*
5. **Save.** **Test:** type *"why aren't my points showing"* → expect a total + pending + an offer to
   check a specific OPE.

---

## Topic 4 — Complete Care Diagnostic  *(optional — the action already covers this)*

*Explains why Complete Care / New Logo / uplift points are or aren't showing for a deal.*

1. **Create:** + Add a topic → From blank. Rename to **`Complete Care Diagnostic`**.
2. **Trigger → The agent chooses:**
   > *Use when the user asks why Complete Care, New Logo, or uplift points are or aren't showing for a
   > specific deal (OPE).*
3. **Trigger inputs (agent-filled):** under the trigger, **+ Add an input** → name **`ope`**, type
   **String**, description *"The deal / OPE number the user mentioned, e.g. OPE-123456789."* The agent
   fills this from the conversation.
4. **Node — Add a condition** (get the OPE if the agent didn't): condition **`ope`** **is blank**.
   - **Ask a question:** message *"Sure — what's the deal number? (looks like OPE-123456789)"*;
     **save the response in `ope`**; identify as **User's entire response** (or Text).
   - *(All other conditions: do nothing — carry on.)*
5. **Node — Add a tool → Run Percy Diagnostic.** Map inputs:
   - **`template`** = `CompleteCare`
   - **`ope`** = **`Topic.ope`**
   - **`who`** = **"Fill with AI"** (the agent supplies CallerEmail — see setup B)
6. **Node — Send a message** (let the agent explain the returned evidence in plain English). If you
   want the wording locked, add a **Condition** on the returned fields and use these exact lines:
   - `creditsToYou = No` and points > 0 → *"This deal IS scoring Complete Care points, but they're
     crediting to the opportunity/pipeline owner, not you. If you should hold it, get the owner
     updated on the deal."*  ← **this is the usual answer**
   - `ccPointsTotal = 100` → *"Scoring the full 100 Complete Care New Logo points — and they credit to
     you."*
   - `inFunnelNotYetWon = Yes` → *"Qualifies on product and timing, but it hasn't been Won yet —
     points land on win."*
   - `activeCCContract = Yes` → *"The customer already has an active Complete Care contract, so it
     fails New Logo; an uplift would score 75 — want me to re-check as uplift?"*
   - `hasCCProductLine = No` → *"No Complete Care product lines on this opp, so it isn't picking up CC
     points."*
   - `found = No` → *"Can't find that deal in the scoring yet — check the number, or it may need a
     refresh."*
7. **Save & Test:** *"why no complete care points on OPE-123456789"*.

---

## Topic 5 — CAP Diagnostic  *(optional)*

*Explains CAP engagement (20) and CAP-generated order (50) points for a deal.*

1. **Create → rename** `CAP Diagnostic`.
2. **Trigger → The agent chooses:**
   > *Use when the user asks about CAP points for a deal — a CAP engagement/request or a CAP-generated
   > order, including "my CAP request isn't showing", "Gemma", or "campaign code".*
3. **Trigger input:** **`ope`** (String) — *"The deal / OPE number, e.g. OPE-123456789."*
4. **Condition `ope` is blank → Ask a question** *"What's the deal number? (looks like OPE-123456789)"*
   → save to **`ope`**.
5. **Add a tool → Run Percy Diagnostic:** `template` = `CAP`, `ope` = `Topic.ope`, `who` =
   "Fill with AI" (CallerEmail).
6. **Send a message** (agent explains; exact lines if you lock it — surface the FIRST failing gate):
   - `inCapRequests = No` → *"No CAP request logged against this opp — log it in SFDC → Support
     Requests → CAP Team Engagement/Support."*
   - `capRequestCreatedQualifies = No` → *"Logged, but created before the 1 May 2026 cut-off."*
   - `capRequestLoggedByMatchesCaller = No` → *"Logged under someone else's name, not yours — that's
     why it isn't crediting to you."*
   - request logged, approval blank → *"Logged and eligible — pending sign-off by Gemma/BD; 20 points
     on approval."*
   - order won + qualifies, approval blank → *"Won and eligible, but pending Gemma's validation — 50
     points on approval. Also confirm the campaign code UKIMEA CSLV CAP Adoption."*
   - `capWonCloseQualifies = No` → *"Close date is before 1 May 2026, the CAP-order cut-off."*
7. **Save & Test:** *"my cap request isn't showing on OPE-123456789"*.

---

## Topic 6 — Customer Centricity Diagnostic  *(optional)*

*Explains logged customer / channel / leadership meeting points for a deal.*

1. **Create → rename** `Customer Centricity Diagnostic`.
2. **Trigger → The agent chooses:**
   > *Use when the user asks why a logged customer / channel / leadership meeting (or "event" /
   > "activity") isn't scoring for a deal.*
3. **Trigger input:** **`ope`** (String) — *"The deal / OPE number, e.g. OPE-123456789."*
4. **Condition `ope` is blank → Ask a question** → save to **`ope`**.
5. **Add a tool → Run Percy Diagnostic:** `template` = `CustomerCentricity`, `ope` = `Topic.ope`,
   `who` = "Fill with AI" (CallerEmail).
6. **Send a message** (agent explains; exact lines if locked — it returns one row per meeting):
   - `meetingCount = 0` → *"No logged events on this opp — add one via Opportunity → Activities → New
     Event."*
   - `meetingClassified = No` → *"Your meeting's subject doesn't START with CUSTOMER / CHANNEL /
     LEADERSHIP, so it isn't classified — re-log with the keyword at the very start (watch for typos
     like 'CUSTMER')."*
   - `createdQualifies = No` → *"This meeting was logged before the 1 May 2026 cut-off, so it doesn't
     count."*  *(Customer Centricity gates on **created date**.)*
   - `loggedByMatchesCaller = No` → *"Logged under someone else, so it's crediting to them, not you."*
   - classified, approval blank → *"I can see a {meetingType} — {points} points once your manager
     approves (weekly)."*
7. **Save & Test:** *"logged a customer meeting on OPE-123456789 but no points"*.

---

## Topic 7 — IB / Expand Diagnostic  *(optional)*

*Explains IB Upsell / Expand pen-rate points (1 per 4% expand, ≤25) for a deal.*

1. **Create → rename** `IB Expand Diagnostic`.
2. **Trigger → The agent chooses:**
   > *Use when the user asks about IB Upsell / Expand (pen-rate) points for a deal — "IB", "expand",
   > "renewal + expand", "win-back", "naked box".*
3. **Trigger input:** **`ope`** (String).
4. **Condition `ope` is blank → Ask a question** → save to **`ope`**.
5. **Add a tool → Run Percy Diagnostic:** `template` = `IBExpand`, `ope` = `Topic.ope`, `who` =
   "Fill with AI" (CallerEmail).
6. **Send a message** (agent explains; exact lines if locked):
   - `completeCarePointsPresent = Yes`, award 0 → *"This deal already scores Complete Care points, so
     IB/Expand isn't paid on the same deal — it's counted under Complete Care."*
   - one motion missing → *"IB/Expand needs BOTH a renewal/IB motion and an expand motion; I only see
     one."*
   - `creditsToYou = No`, points > 0 → *"It earns IB/Expand points, but they credit to the owner /
     pipeline / OS-sales person, not you."*
   - `inFunnelNotYetWon = Yes` → *"Qualifies but hasn't been Won yet — IB/Expand lands on win."*
   - points > 0, `creditsToYou = Yes` → *"Scoring your IB/Expand points (renewal + expand, capped 25)."*
7. **Save & Test:** *"why no expand points on OPE-123456789"*.

---

## Topic 8 — IP in GreenLake Diagnostic  *(optional — user-level, no OPE)*

*Explains IP-in-GreenLake tier points (10–75) for the caller.*

1. **Create → rename** `IP in GreenLake Diagnostic`.
2. **Trigger → The agent chooses:**
   > *Use when the user asks about IP-in-GreenLake points or their monthly IP % — this is per-user,
   > not per-deal.*
3. **No `ope` input.** (This scheme is per-person.)
4. **Add a tool → Run Percy Diagnostic:** `template` = `IPGreenLake`, `who` = "Fill with AI" (CallerEmail)
   *(leave `ope` blank)*.
5. **Send a message** (agent explains; exact lines if locked):
   - row present → *"Your IP-in-GreenLake for this month is in the {band} band — {points} points."*
     (bands: 0–10→10, 10–25→20, 25–40→30, 40–50→50, 50%+→75)
   - `hasIPGLRow = No` / 0% → *"No IP-in-GreenLake figure for you this month, so no points from that
     scheme yet (it's recognised monthly from SFDC)."*
6. **Save & Test:** *"how are my greenlake points"*.

---

## Topic 9 — Accreditation Diagnostic  *(optional — user-level, no OPE)*

*Explains accreditation-race / CSM eligibility for the caller.*

1. **Create → rename** `Accreditation Diagnostic`.
2. **Trigger → The agent chooses:**
   > *Use when the user asks about accreditation-race or CSM points, being "S-coded", "the race", or
   > "completion" — person/team-level, not per-deal.*
3. **No `ope` input.**
4. **Add a tool → Run Percy Diagnostic:** `template` = `Accreditation`, `who` = "Fill with AI" (CallerEmail).
5. **Send a message** (agent explains; exact lines if locked):
   - not S-coded → *"The race is for S-coded individuals; your record isn't flagged as S-coded."*
   - not COMPLETE → *"Your accreditation isn't COMPLETE yet — the team race credits once the sponsor
     group is complete."*
   - excluded individual → *"This scheme excludes Adrian and Garren."*
   - CSM L2+ → *"As a CSM (L2+) you're eligible for 30 points on completion."*
   - eligible, points > 0 → *"You've got {n} accreditation points — the 100/50/20 is a team race
     decided by completion standings."*
6. **Save & Test:** *"am I in the accreditation race"*.

---

## Topic 10 — Fallback  **(build this — customise the built-in one)**

*Handles greetings, nonsense, off-topic. Don't create a new topic — edit the existing **Fallback**
system topic.*

1. **Open:** Topics → **System** → **Fallback**.
2. **Node — Send a message** (replace the default text):
   > I'm Percy — I help with 1% Club points. I can explain how points are earned, check why a
   > specific deal is or isn't scoring (just send the OPE), or refresh the dashboard for you. What
   > would you like?
3. Keep it to **one friendly line of intent** — never loop, never dump the full category list.
4. **Save.**

> **Not a topic — conversation parsing.** The agent reads the transcript and finds the latest user
> turn + any OPE from the **Overview → Instructions**. Don't build a topic for it.

---

## Settings (confirm)
- **Generative orchestration: ON** (this is why triggers are "The agent chooses").
- **General knowledge / web search: OFF** (keeps Percy on the programme rules).
- **Authentication:** as your tenant requires; the agent runs server-side from the orchestrator flow.

## Minimum viable Percy
Build just **Topics 2, 3, and 10** (Refresh · Clarify & Guide · Fallback) plus the **two actions** —
that's a complete assistant: the instructions (with the §9 rules) answer every FAQ **tailored to the
question** (Topic 1 stays unbuilt), and `Run Percy Diagnostic` + the instructions cover every
per-scheme diagnostic. Add **Topics 4–9** later only where you want the wording locked.
