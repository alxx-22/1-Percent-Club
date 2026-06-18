# Percy backend — SharePoint trigger (NO premium) · Stage 1: FAQ

No premium connectors. The app **upserts the conversation into a SharePoint list**, a flow that
triggers **"when an item is created or modified"** generates the answer and **writes it back**,
and the app **polls** the row for the reply. The conversation travels as **JSON**.

```
Percy chat (app)
   │  Patch -> PercyConversations row for this SessionId (one row per conversation)
   │  { …, ConversationJson, AnswerText:"", Status:"Pending" }
   ▼
Power Automate  (SharePoint "When an item is created or modified")
   ├─ Condition: Status = "Pending"   ← stops the trigger looping on its own update
   ├─ AI (system prompt = your scoring FAQ + ConversationJson) -> answer
   └─ Update item: AnswerText = answer, Status = "Answered"
   ▼
tmrPercyPoll (app)  re-reads the row every 2s -> shows Percy's reply
```

Stage 2 ("why isn't my opp scoring?") is **not built yet** — hooks at the end.

---

## 1. App changes (formulas)

Add the **`PercyConversations`** list as a data source (**Data → Add data → SharePoint →** your
site → `PercyConversations`). Standard connector — no premium.

| Control | Property | File |
|---|---|---|
| **App** | `OnStart` | [`../../dashboard/App_OnStart.powerfx`](../../dashboard/App_OnStart.powerfx) — adds `varAskId`, `varPollN` (plus existing `varSessionId`, `varPercyThinking`, `colChat`) |
| `imgSend` | `OnSelect` | [`../imgSend.OnSelect.powerfx`](../imgSend.OnSelect.powerfx) — upsert the row + start polling |
| **`tmrPercyPoll`** (new Timer in `conPercyChat`) | `OnTimerEnd` | [`../tmrPercyPoll.OnTimerEnd.powerfx`](../tmrPercyPoll.OnTimerEnd.powerfx) — poll for the answer |

**`tmrPercyPoll`** settings: `Duration=2000`, `Repeat=true`, `AutoStart=false`,
`Start = varPercyThinking`, `Reset = !varPercyThinking`, `Visible=false`.

Send button (upsert this session's row, clear the answer, mark Pending):
```powerfx
Set( varPercyQ, Trim( txtChat.Text ) );
Collect( colChat, { Seq: CountRows(colChat) + 1, Role: "user", Body: varPercyQ } );
Reset( txtChat );
Set( varChatJson, JSON( ShowColumns( colChat, "Seq", "Role", "Body" ) ) );
Set( varConvRow, LookUp( PercyConversations, SessionId = varSessionId ) );
Set( varAsk,
    Patch( PercyConversations,
        If( IsBlank( varConvRow ), Defaults( PercyConversations ), varConvRow ),
        { Title: varSessionId, SessionId: varSessionId, ConversationJson: varChatJson,
          UserEmail: Lower(User().Email), LastQuestion: varPercyQ,
          MessageCount: CountRows(colChat), AnswerText: "", Status: "Pending" } ) );
Set( varAskId, varAsk.ID );
Set( varPollN, 0 );
Set( varPercyThinking, true )
```
`tmrPercyPoll` then re-reads `LookUp(PercyConversations, ID = varAskId)` every 2s until
`Status="Answered"` & `AnswerText` is filled, then shows the reply.

> **Timeout** = `tmrPercyPoll.Duration` × `varPollMax` (set in `App.OnStart`; default
> `2000ms × 60 = 120s`). The SharePoint *"created/modified" trigger can take 30–60s+ just to
> fire*, so don't set this too low. Raise `varPollMax` (and/or `Duration`) if Percy times out
> before the flow answers; lower them to give up sooner.

> **Timers in a Power BI–embedded visual can be unreliable.** If polling doesn't tick, add a tiny
> "check for reply" Image/button whose `OnSelect` runs the same body as `tmrPercyPoll.OnTimerEnd`.

---

## 2. SharePoint list  `PercyConversations`

You already have it. **Add the last two columns** (the others are yours, unchanged):

| Column | Type | Notes |
|---|---|---|
| `Title` | Single line | stores the session id |
| `SessionId` | Single line of text | **index it** |
| `ConversationJson` | Multiple lines, **plain text** | the JSON transcript (AI context) |
| `UserEmail` | Single line of text | who asked (for Stage 2) |
| `LastQuestion` | Single/Multiple lines | latest question |
| `MessageCount` | Number | message count |
| **`Status`** ← add | Single line of text | `Pending` / `Answered` |
| **`AnswerText`** ← add | Multiple lines, **plain text** | the flow writes the reply here |

> Keep multi‑line columns **plain text** (turn off enhanced rich text) so JSON/answers aren't
> mangled.
>
> **Make `Status` a *Single line of text* column**, not a Choice. A Choice column returns a
> *record* (`{Value:…}`), which gives *"Incompatible types for comparison: Record, Text"* on
> `Status = "Answered"`. If you must keep it a Choice: read `varPercyRow.Status.Value` in
> `tmrPercyPoll`, and write `Status: { Value: "Pending" }` in the `imgSend` Patch (the choices
> `Pending` / `Answered` must exist).
>
> **After adding/changing any column, refresh the data source** (Data pane → `PercyConversations`
> → ⋯ → Refresh). Otherwise the app keeps the old schema and the new columns show as red
> ("unexpected"/type errors) across the `Patch`.

---

## 3. Power Automate flow (your existing trigger)

**Trigger:** SharePoint **"When an item is created or modified"** on `PercyConversations`.

1. **Condition (critical — prevents an infinite loop):** `Status` **is equal to** `Pending`.
   Put steps 2–3 in the **If yes** branch. (When the flow updates the row it becomes `Answered`,
   which re‑fires the trigger but fails this condition, so it stops.)
2. **Generate the answer** — **AI Builder → "Create text with GPT"** (or HTTP → Azure OpenAI):
   - *Instructions / system* = your **scoring FAQ prompt** (section 4).
   - *Prompt / input* = `Conversation (JSON): @{triggerOutputs()?['body/ConversationJson']}`
   - Output used as **`AiText`**.
3. **Update item** — *Id* = `@{triggerOutputs()?['body/ID']}`, `AnswerText` = `AiText`,
   `Status` = `Answered`. *(Optional: also append the answer into `ConversationJson` and bump
   `MessageCount` so the stored transcript stays complete.)*

No "Respond to PowerApp" step (that's the premium path) — the app sees the update by polling.

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
Mirror the dashboard category names (New CC Logo / IB Upsell, CAP Engagement, CAP Orders Booked,
Customer Centricity, Accreditation Race, IP Push) and state point values explicitly.

---

## 5. Test

1. Add the `Status` + `AnswerText` columns (§2); build the flow (§3) with the **Pending**
   condition; paste your prompt (§4).
2. In the app: add `PercyConversations` as a data source, then apply the §1 formulas.
3. Open Percy, ask "How are CAP orders scored?" → the row's `Status` goes `Pending`, the flow
   flips it to `Answered` with `AnswerText`, and within ~2s Percy's reply appears.

Troubleshooting: flow not firing → check the trigger list + the `Pending` condition; reply never
shows → confirm `Status` becomes `Answered`, `AnswerText` is non‑blank, and the app has
`PercyConversations` as a data source (and timers tick — see the §1 note).

---

## 6. Stage 2 (later — not built yet)

"Why isn't my opp scoring?" will add, in the flow: read the caller's opportunities (filtered by
`UserEmail`), a second prompt that reasons over those rows against the scoring rules, and a branch
routing FAQ questions to §3 vs. data questions to the new prompt. The JSON transcript + `UserEmail`
we already capture give it everything it needs — no app changes to start it.
