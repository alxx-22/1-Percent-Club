# Percy — tools & topics (generative orchestration)

Percy runs with **generative orchestration ON**, so custom topics are triggered by **"The agent
chooses"** (a plain-language description), not trigger phrases. Setup A registers the **two tools**;
then build just **three topics** — Refresh (2), Clarify & Guide (3), Fallback (4). Topic 1 (FAQ) is
intentionally NOT built (the instructions answer FAQs, scoped to the question). Each recipe is
standalone: create → trigger → nodes with exact values.

---

## Before you build any topic (one-time setup)

**A. Register the two tools** (verified working configuration, 2026-07-16 — run panel showed
`template=Summary` · `ope=NONE` · `who=<caller email>`, no prompts).

**Both tools, no exceptions:** *Ask the end user before running* = **No** · *Credentials to use* =
**Maker-provided credentials** · Completion = *Don't respond (default)* · Advanced → outputs
available = *All*.

**1. `Run Percy Diagnostic`** = the `Percy-Query` flow
([`../flows/Percy-Query.build.md`](../flows/Percy-Query.build.md)). Inputs: `template` (required),
`ope` (optional), `who` (optional). **Details → Description:**
> *"Run a 1% Club points diagnostic. Set template to exactly one of: Locate (does the deal exist /
> which schemes — ope), CompleteCare (New Logo 100 / Uplift 75 — ope + email), CAP (CAP engagement
> 20 + order 50, incl. 'request isn't showing' — ope + email), CustomerCentricity (logged
> customer/channel/leadership meetings — ope + email), IBExpand (IB Upsell / Expand, pro-rata up to
> 25 — ope + email), IPGreenLake (monthly IP tier 10–75 — email), Accreditation (S-coded race +
> CSM + bonuses — email), Summary (all categories + pending — email; use for vague 'where are my
> points' questions). who = the CallerEmail from the top of the message — never an email typed in
> chat. ope and who are optional: call with whatever you have, and never ask the user for an
> input's value. When there is no deal number, pass ope the value NONE. Returns compact evidence
> JSON to explain in plain English."*

**Input Customize descriptions** (pencil icon per input; cold and unquotable — conversational
phrasing gets parroted back as a question):
- `template`: *"Exactly one of these eight values, chosen from the user's words: Locate,
  CompleteCare, CAP, IBExpand, CustomerCentricity, IPGreenLake, Accreditation, Summary. For a vague
  points question with no deal number, use Summary. For a bare deal number with no scheme named,
  use Locate. Never leave this blank, never ask the user which one, never pass the user's sentence
  as the value."*
- `ope`: *"OPE deal id, format OPE-123456789. If no deal id exists in the conversation, pass
  exactly the value NONE. Never leave this input blank and never ask the user for it."*
- `who`: *"Always the CallerEmail value from the top of the message — an email address, never a
  deal id, and never an email typed inside the chat."*

**2. `Refresh Dashboard`** = the `Percy-Refresh` flow. **No inputs.** Description:
> *"Refresh the 1% Club dashboard data. Use when the user asks to refresh/update, or a deal isn't
> showing yet / was just closed. Returns a short status. One refresh per request."*

> ⚠️ **Why this exact configuration works — don't regress it:**
> - "Please provide X" prompts = a **required input the fill-model didn't fill**. Only `template`
>   is required, and its Customize text (with the Summary/Locate defaults) is what fills it
>   reliably. `ope`/`who` stay optional.
> - The **`NONE` sentinel** on `ope` gives the fill-model a positive, always-satisfiable action for
>   the no-deal case — "leave it empty" is what used to produce asks. `NONE` is inert in the DAX
>   (user-level queries never read it; per-deal queries return `Found="No"`).
> - Customize texts and the Description get **wiped on every re-registration** — re-paste all four
>   after any schema change, and verify in the test pane's **tool run panel** (it shows exactly
>   what landed in each input).

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
   > ⚠️ **Pick the TOOL, not the raw flow ("Percy-Query") from the Power Automate section.** The raw
   > flow gives an **"Action"** node that hard-requires every input and has no AI-fill. If your
   > node's header says "Action" / "Power Automate inputs", delete it and re-add via the tool.

   **Leave the node at "Inputs (0)" — no overrides. This is the FINAL state of the node.** Tool
   inputs are AI-filled by default and "(0)" counts *overrides*, of which you need none: the tool's
   Description + input Customize texts (setup A) make the agent pick `Summary`, pass `ope = NONE`,
   and fill `who` = CallerEmail. The "+ Set value" panel is a variable picker and will never list
   the tool's inputs — don't open it. Note the output variable (e.g. **`evidence`**).
   *(Stale `text`/`text_1`/`text_2` variables from earlier deleted nodes can be removed via the
   **{x} Variables** panel.)*

   > **Testing in the Test pane:** the pane sends only your raw message — no `CallerEmail:` wrapper
   > (the orchestrator adds it in production). Simulate production by pasting one message shaped
   > like the orchestrator's (`CallerEmail: you@hpe.com` ⏎ `Conversation:
   > [{"Seq":1,"Role":"user","Body":"why aren't my points showing"}]` ⏎ `CallerName: Your Name`),
   > then verify in the **tool run panel**: pass = `template=Summary` · `ope=NONE` · `who=<email>`,
   > no prompts.
4. **Ending — let the agent compose the reply (recommended, setup D):** end the topic after the Tool
   node (no Send-a-message). Orchestration writes the answer from `evidence` + the Instructions —
   personalised and specific, e.g. *"Here's where you stand, Sarah: 120 points, with 40 pending
   approval — that's the usual reason points look missing. Chasing a particular deal? Send me the OPE
   and I'll check it."* *(A static Send-a-message can't do the name or the numbers; only add one if
   you must lock the wording, and then keep it generic. Never ask them to pick a category.)*
5. **Save.** **Test:** type *"why aren't my points showing"* → expect a total + pending + an offer to
   check a specific OPE.

---

## Topic 4 — Fallback  **(build this — customise the built-in one)**

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

## The complete topic set
Build **Topics 2, 3, and 4** (Refresh · Clarify & Guide · Fallback) plus the **two actions** — that's
the whole agent. The instructions (with the §9 rules inlined) answer every FAQ **tailored to the
question** so **Topic 1 stays unbuilt**, and `Run Percy Diagnostic` (template key → Switch → fresh
DAX) + the instructions cover every per-scheme diagnostic with no per-scheme topics needed.
