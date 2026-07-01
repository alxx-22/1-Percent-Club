# Build `Percy-Orchestrator` by hand (Power Automate)

Click-by-click build for the main flow — **no import**. It triggers when the app writes a chat row,
hands the transcript to the Percy agent, and writes the plain-text answer back. Matches the live
Shape-A app (`ConversationJson` in → `AnswerText` out, `Status` `Pending → Answered`).

**Connections used:** SharePoint, and the Copilot Studio agent action. No premium, no service principal.

> **Trigger = "When an item is created" (not "created or modified").** The app writes a **new row on
> every send**, and each row carries the **whole conversation so far** in `ConversationJson` (it's the
> cumulative transcript, so the agent always has full context). One created row = one question to
> answer. This also means **no loop guard is needed**: when the flow writes `AnswerText` + `Status =
> "Answered"` it *modifies* the row, and a create-only trigger ignores modifies — so it can't re-fire
> itself. Simpler flow, no self-trigger, one run per question.

---

## 1. Create the flow
- Power Automate → **Create → Automated cloud flow**.
- Name: `Percy-Orchestrator`.
- Trigger: search **SharePoint** → **When an item is created** → **Create**.

## 2. Trigger — When an item is created
- **Site Address:** your site (the one holding `PercyConversations`).
- **List Name:** `PercyConversations`.

*(No Condition/guard step. Every created row is a fresh ask — `Status = "Pending"`, `AnswerText`
empty — because only the app creates rows, and it always seeds them that way. The old
`Status = "Pending"` guard existed only to swallow the self-modify from a "created or modified"
trigger; a create-only trigger never sees that modify, so the guard is gone.)*

## 3. Run the Percy agent
Add the **Copilot Studio** action that runs your published Percy agent (e.g. *Microsoft Copilot
Studio → Run a prompt / call an agent*; the exact name depends on your tenant's connector version).

- **Input `ConversationJson`** = `ConversationJson` (trigger dynamic content) — the whole transcript.
- **Input `UserEmail`** = `UserEmail` (trigger dynamic content).
- The agent finds the latest user message (`Role="user"`, highest `Seq`) inside the JSON, routes,
  optionally calls a tool, and returns **plain text**. Note the **output property that holds the
  text** (e.g. `text` / `outputText`) — you'll reference it next.

> **No Copilot Studio agent connector?** Substitute **AI Builder → Create text with GPT**:
> *Instructions* = the Percy overview instructions (`../copilot-studio/percy-instructions.md`) +
> the §9 rules; *Prompt* = `Conversation (JSON): ` then the `ConversationJson` dynamic content.
> (FAQ-only; the per-OPE tools need the Copilot Studio agent path.)

## 4. Compose — sanitise the answer
Add **Data Operation → Compose**, name it `AnswerTextOut`. In the **Inputs**, paste this expression
(swap `body('Run_a_prompt')?['text']` for your agent action's real output path):

```
if(empty(trim(coalesce(body('Run_a_prompt')?['text'], ''))), 'Sorry, I couldn''t answer that one — please try again.', body('Run_a_prompt')?['text'])
```

## 5. Update item — write `AnswerText` + `Status = Answered`
Add **SharePoint → Update item**.
- **Site Address / List Name:** same as the trigger.
- **Id:** `ID` (trigger dynamic content).
- **AnswerText:** `Outputs` of `AnswerTextOut` (the Compose).
- **Status:** `Answered`.
- *(Optional, if you added the columns)* **MetricType / OPE:** from the agent's structured output.

## 6. Error branch — friendly answer on failure
The app's poll only shows a bubble when `Status = "Answered"`, so on failure we still write
`Answered` with a friendly message (don't invent an `Error` status the app won't read).

- Add another **SharePoint → Update item** (call it **Update item — on error**).
- **Id:** `ID`; **AnswerText:** `Sorry, I couldn't reach the assistant just now — please try again.`;
  **Status:** `Answered`. *(If you added an `ErrorMessage` column, put technical detail there.)*
- On this action click **⋯ → Configure run after** → tick **has failed** and **has timed out**
  (untick *is successful*). Set the run-after to depend on **Run the Percy agent**, the **Compose**,
  and **Update item** (so any failure in the happy path routes here).

## 7. Settings (recommended)
- Flow **⋯ → Settings → Concurrency Control: On**, Degree of Parallelism ~10 (so a burst of chats
  doesn't exhaust the agent / Power BI connection).
- Save. Test by sending a message from the app and watching the run history.

---

### Flow at a glance
```
When an item is created  (PercyConversations)     ⟵ create-only: no self-trigger, no guard
├─ Run Percy agent            (in: ConversationJson, UserEmail   → out: plain text)
├─ Compose AnswerTextOut      (sanitise / fallback if empty)
├─ Update item                (AnswerText = AnswerTextOut, Status = "Answered")
└─ Update item — on error     (run after: failed/timed out → friendly text, Status = "Answered")
```
Build pack cross-ref: §4. App write contract (new row per send): §3.
