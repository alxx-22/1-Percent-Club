# Percy backend — SharePoint + Power Automate (Stage 1: FAQ)

This sets up Percy's brain. **Stage 1** (this doc) answers FAQ‑style questions about
**how points are scored**, using a single AI prompt you write, and logs every
conversation into a SharePoint list **as JSON**. **Stage 2** (later) will add logic that
reads a user's own opportunities and explains *why a specific opp isn't scoring* — that
secondary querying AI is **not** included yet; the hooks are noted at the end.

```
Percy chat (app)
   │  question + sessionId + userEmail + conversation(JSON)
   ▼
Power Automate  "PercyAsk"  (PowerApps V2 trigger)
   ├─ AI (system prompt = your scoring FAQ) ──► answer
   ├─ append answer to the conversation JSON
   ├─ upsert it into SharePoint list  PercyConversations
   └─ Respond to PowerApp ──► answer
   ▼
Percy shows the answer
```

---

## 1. App formulas to add

You already have the UI (see [`../../../PERCY.md`](../../../PERCY.md)). Only the **send**
action changes — it sends the whole transcript as JSON and shows the flow's reply.

### `App.OnStart` (already set, confirm these exist)
```powerfx
Set( varSessionId, GUID() );    // one id per conversation
ClearCollect( colChat,
    { Seq: 1, Role: "percy",
      Body: "Hi, I'm Percy " & Char(128075) & " Ask me anything about the 1% Club dashboard." } );
```

### `imgSend.OnSelect` (replace the stub once the flow exists)
```powerfx
If(
    !IsBlank( Trim( txtChat.Text ) ),

    // 1) show the user's message
    Collect( colChat, { Seq: CountRows(colChat) + 1, Role: "user", Body: txtChat.Text } );
    Set( varPercyQ, txtChat.Text );
    Reset( txtChat );
    Set( varPercyThinking, true );

    // 2) send the WHOLE conversation as JSON + the new question to the flow
    Set( varChatJson, JSON( ShowColumns( colChat, "Seq", "Role", "Body" ) ) );
    Set( varPercyResp,
         PercyAsk.Run( varPercyQ, varSessionId, Lower( User().Email ), varChatJson ) );

    // 3) show Percy's reply (the flow already logged the transcript to SharePoint)
    Collect( colChat, { Seq: CountRows(colChat) + 1, Role: "percy", Body: varPercyResp.answer } );
    Set( varPercyThinking, false )
)
```

- `JSON(ShowColumns(colChat,"Seq","Role","Body"))` → a string like
  `[{"Seq":1,"Role":"percy","Body":"Hi…"},{"Seq":2,"Role":"user","Body":"…"}]`.
- `PercyAsk.Run(...)` returns a record; `.answer` is the reply text (defined by the flow's
  **Respond to a PowerApp** step). Add the flow via the app's **Power Automate** pane first,
  which makes `PercyAsk` available to call.
- *(optional)* show a "Percy is typing…" bubble while `varPercyThinking` is true.

---

## 2. SharePoint list

Create one **list** (SharePoint site → **+ New → List**, blank):

**List name:** `PercyConversations`

| Column | Type | Settings |
|---|---|---|
| `Title` | Single line | leave default (or store the session id here too) |
| `SessionId` | Single line of text | **index it** (List settings → Indexed columns) — used to find the row to update |
| `ConversationJson` | **Multiple lines of text** | **Plain text** (turn *off* "Use enhanced rich text") and allow unlimited length — this holds the JSON transcript |
| `UserEmail` | Single line of text | who asked |
| `LastQuestion` | Multiple lines of text (plain) | latest question, for quick scanning |
| `MessageCount` | Number | optional |

> Keep `ConversationJson` **plain text** — rich text mangles JSON. `Created` / `Modified` /
> `Created By` are automatic, so you also get *when* and *who* for free.

---

## 3. Power Automate flow `PercyAsk`

**Create → Instant cloud flow → trigger "PowerApps (V2)".**

### 3a. Trigger inputs (add four **Text** inputs, in this order)
`question` · `sessionId` · `userEmail` · `conversationJson`

### 3b. The AI step (the FAQ brain)
Add **AI Builder → "Create text with GPT"** (or an HTTP call to Azure OpenAI — see note):
- **Instructions / system** = your **scoring FAQ prompt** (section 4 below).
- **Prompt / input** =
  ```
  Conversation so far (JSON): @{triggerBody()?['text_3']}      ← conversationJson
  Latest user question: @{triggerBody()?['text']}              ← question
  ```
  (Field names like `text`, `text_1`… are whatever the trigger generates — pick them from the
  dynamic content; the labels are what matter.)
- Output used below as **`AiText`**.

### 3c. Append the answer to the transcript JSON
1. **Parse JSON** — *Content* = `conversationJson`; *Schema*:
   ```json
   { "type": "array", "items": { "type": "object",
     "properties": { "Seq": {"type":"integer"}, "Role": {"type":"string"}, "Body": {"type":"string"} } } }
   ```
2. **Initialize variable** `convArray` (Array) = output of **Parse JSON**.
3. **Append to array variable** `convArray`:
   ```json
   { "Seq": @{add(length(variables('convArray')),1)}, "Role": "percy", "Body": @{outputs('Create_text_with_GPT')?['text']} }
   ```
4. **Compose** `finalJson` = `@{string(variables('convArray'))}`.

### 3d. Upsert into SharePoint (one row per session)
1. **Get items** — *Site/List* = `PercyConversations`; *Filter Query* =
   `SessionId eq '@{triggerBody()?['text_1']}'`; *Top Count* = 1.
2. **Condition** — `length(outputs('Get_items')?['body/value'])` **is greater than** `0`:
   - **If yes → Update item**: *Id* = `@{first(outputs('Get_items')?['body/value'])?['ID']}`,
     `ConversationJson` = `finalJson`, `LastQuestion` = `question`, `UserEmail` = `userEmail`,
     `MessageCount` = `@{length(variables('convArray'))}`.
   - **If no → Create item**: `Title`/`SessionId` = `sessionId`, `ConversationJson` = `finalJson`,
     `LastQuestion` = `question`, `UserEmail` = `userEmail`, `MessageCount` = `@{length(variables('convArray'))}`.

### 3e. Return the answer
**Respond to a PowerApp or flow** → add a **Text** output named **`answer`** = `AiText`
(the "Create text with GPT" output). That's what `PercyAsk.Run(...).answer` reads.

> **Azure OpenAI instead of AI Builder?** Replace 3b with an **HTTP** action POSTing to your
> chat‑completions endpoint, `messages` = `[{role:"system",content:<prompt>}]` + the parsed
> `convArray` mapped to `{role,content}` + `{role:"user",content:question}`. Everything else
> (3c–3e) is unchanged.

---

## 4. The scoring prompt (you write this)

The whole of Stage 1 is driven by one system prompt. Paste your scoring rules into the AI
step's **Instructions**. Skeleton:

```
You are Percy, the friendly AI assistant for the "1% Club" sales gamification dashboard.
Answer ONLY using the scoring rules below. Be concise, friendly, and specific. If a question
isn't covered by the rules, say you can only help with 1% Club scoring for now and suggest
they rephrase. Never invent point values.

SCORING RULES
=============
<< paste your "how points are scored" instructions here — e.g. which columns count,
   what each category is worth, pending vs counted, deadlines, ties, etc. >>
```

Tips: keep it factual and bulleted; mirror the dashboard's category names (New CC Logo / IB
Upsell, CAP Engagement, CAP Orders Booked, Customer Centricity, Accreditation Race, IP Push);
state point values explicitly so Percy never guesses.

---

## 5. Test

1. Build the SharePoint list (§2) and the flow (§3); paste your prompt (§4).
2. In the app, add `PercyAsk` via the **Power Automate** pane and swap in the `imgSend.OnSelect`
   from §1.
3. Open Percy, ask "How are CAP orders scored?" → you get an answer, and a row appears/updates
   in `PercyConversations` with the full JSON transcript.

---

## 6. Stage 2 (later — not built yet)

Goal: help a user understand **why their own opportunities aren't scoring**. It will add:
- a step in the flow to **read the caller's opportunities** (from `PowerBIIntegration`‑equivalent
  SharePoint/Dataverse, filtered by `userEmail`),
- a second prompt that reasons over those rows against the scoring rules,
- routing in the flow: FAQ questions → §3 prompt; "why isn't X scoring?" questions → the data
  prompt.

The JSON transcript and `userEmail` we already log give Stage 2 everything it needs — no app
changes required to start it.
