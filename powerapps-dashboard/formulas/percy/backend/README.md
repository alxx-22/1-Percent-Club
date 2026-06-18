# Percy backend — SharePoint trigger (NO premium) · Stage 1: FAQ

No premium connectors. The app **writes the question to a SharePoint list**, a flow that
triggers **"when an item is created or modified"** generates the answer and **writes it back**,
and the app **polls** the row for the reply. The whole conversation travels as **JSON**.

```
Percy chat (app)
   │  Patch -> new row in  PercyMessages
   │  { SessionId, Question, ConversationJson, AnswerText:"", Status:"Pending" }
   ▼
Power Automate  (SharePoint "When an item is created or modified")
   ├─ Condition: Status = "Pending"   ← stops the trigger looping on its own update
   ├─ AI (system prompt = your scoring FAQ + ConversationJson + Question) -> answer
   └─ Update item: AnswerText = answer, Status = "Answered"
   ▼
tmrPercyPoll (app)  re-reads the row every 2s -> shows Percy's reply
```

Stage 2 ("why isn't my opp scoring?") is **not built yet** — hooks at the end.

---

## 1. App changes (formulas)

Add the **`PercyMessages`** list as a data source first (**Data → Add data → SharePoint →** your
site → `PercyMessages`). It's the **standard** SharePoint connector, so no premium.

| Control | Property | File |
|---|---|---|
| **App** | `OnStart` | [`../../dashboard/App_OnStart.powerfx`](../../dashboard/App_OnStart.powerfx) — adds `varAskId`, `varPollN` (plus the existing `varSessionId`, `varPercyThinking`, `colChat`) |
| `imgSend` | `OnSelect` | [`../imgSend.OnSelect.powerfx`](../imgSend.OnSelect.powerfx) — `Patch` the question + start polling |
| **`tmrPercyPoll`** (new Timer in `conPercyChat`) | `OnTimerEnd` | [`../tmrPercyPoll.OnTimerEnd.powerfx`](../tmrPercyPoll.OnTimerEnd.powerfx) — poll for the answer |

**`tmrPercyPoll`** settings: `Duration=2000`, `Repeat=true`, `AutoStart=false`,
`Start = varPercyThinking`, `Reset = !varPercyThinking`, `Visible=false`.

What the send button does now (no `.Run`):
```powerfx
Set( varPercyQ, Trim( txtChat.Text ) );
Collect( colChat, { Seq: CountRows(colChat) + 1, Role: "user", Body: varPercyQ } );
Reset( txtChat );
Set( varChatJson, JSON( ShowColumns( colChat, "Seq", "Role", "Body" ) ) );
Set( varAsk,
    Patch( PercyMessages, Defaults( PercyMessages ),
        { Title: varSessionId, SessionId: varSessionId, Question: varPercyQ,
          ConversationJson: varChatJson, AnswerText: "", Status: "Pending" } ) );
Set( varAskId, varAsk.ID );
Set( varPollN, 0 );
Set( varPercyThinking, true )
```
`tmrPercyPoll` then re-reads `LookUp(PercyMessages, ID = varAskId)` every 2s until `AnswerText`
arrives (or ~30s timeout), and `Collect`s Percy's reply into `colChat`.

> **Timers in a Power BI–embedded visual can be unreliable.** If polling doesn't tick, add a tiny
> "check for reply" Image/button whose `OnSelect` runs the same body as `tmrPercyPoll.OnTimerEnd`
> (a manual poll). In a standalone canvas app the timer is fine.

---

## 2. SharePoint list  `PercyMessages`

One **row per question** (SharePoint site → **+ New → List**, blank):

| Column | Type | Settings |
|---|---|---|
| `Title` | Single line | default (stores the session id too) |
| `SessionId` | Single line of text | **index it** |
| `Question` | Multiple lines of text | **Plain text** |
| `ConversationJson` | Multiple lines of text | **Plain text**, unlimited length — the JSON transcript |
| `AnswerText` | Multiple lines of text | **Plain text** — the flow writes the reply here |
| `Status` | Single line of text | values `Pending` / `Answered` (a Choice works too — then compare `.Value` in the app) |

> Keep the multi‑line columns **plain text** (turn off enhanced rich text) so JSON/answers aren't
> mangled. `Created` / `Modified` / `Created By` are automatic, so you get who/when for free.

---

## 3. Power Automate flow (you've made the trigger)

**Trigger:** SharePoint **"When an item is created or modified"** on `PercyMessages`.

1. **Condition (critical — prevents an infinite loop):** `Status` **is equal to** `Pending`.
   Put everything below in the **If yes** branch. (When the flow updates the item it becomes
   `Answered`, which re‑fires the trigger but fails this condition, so it stops.)
2. **Generate the answer** — **AI Builder → "Create text with GPT"** (or HTTP → Azure OpenAI):
   - *Instructions / system* = your **scoring FAQ prompt** (section 4).
   - *Prompt / input* =
     ```
     Conversation so far (JSON): @{triggerOutputs()?['body/ConversationJson']}
     Latest user question: @{triggerOutputs()?['body/Question']}
     ```
   - Output used below as **`AiText`**.
3. **Update item** — *Id* = `@{triggerOutputs()?['body/ID']}`,
   `AnswerText` = `AiText`, `Status` = `Answered`. (Leave the other fields untouched.)

That's it — no "Respond to PowerApp" step (that's the premium path). The app sees the update by
polling. Optionally also write the full transcript: set `ConversationJson` to the incoming JSON
with the answer appended (Parse JSON → append → `string(...)`), exactly as before.

---

## 4. The scoring prompt (you write this)

Paste your scoring rules into the AI step's **Instructions**:

```
You are Percy, the friendly AI assistant for the "1% Club" sales gamification dashboard.
Answer ONLY using the scoring rules below. Be concise, friendly, and specific. If a question
isn't covered by the rules, say you can only help with 1% Club scoring for now. Never invent
point values.

SCORING RULES
=============
<< paste your "how points are scored" instructions here >>
```
Mirror the dashboard's category names (New CC Logo / IB Upsell, CAP Engagement, CAP Orders Booked,
Customer Centricity, Accreditation Race, IP Push) and state point values explicitly.

---

## 5. Test

1. Build the list (§2) and the flow (§3); paste your prompt (§4).
2. In the app: add `PercyMessages` as a data source, then apply the §1 formulas.
3. Open Percy, ask "How are CAP orders scored?" → a `Pending` row appears, the flow flips it to
   `Answered` with `AnswerText`, and within ~2s Percy's reply shows in the chat.

Troubleshooting: flow not firing → check the trigger list + the `Pending` condition; reply never
shows → confirm `Status` becomes `Answered` and the app has `PercyMessages` as a data source
(and timers tick — see the §1 note).

---

## 6. Stage 2 (later — not built yet)

"Why isn't my opp scoring?" will add, in the flow: read the caller's opportunities (filtered by
`Created By` / a `UserEmail` column), a second prompt that reasons over those rows against the
scoring rules, and a branch that routes FAQ questions to §3 vs. data questions to the new prompt.
The JSON transcript + author we already capture give it everything it needs — no app changes to
start it.
