# Percy — the AI assistant (build guide)

Percy peers over the ribbon, waves, and pops the odd speech bubble. Tap him and a
chat window scales in from the top‑right; type a question, hit send, and a Power
Automate flow (wired up later) answers using a SharePoint knowledge list.

![percy](previews/full-percy.png)

All visuals are **SVG/HTML data‑URIs** (same technique as the rest of the app) so
there are no image assets to manage.

---

## 1. Controls & formulas

| Control | Type | Property | Formula |
|---|---|---|---|
| **App** | — | `OnStart` | [`App_OnStart.powerfx`](formulas/App_OnStart.powerfx) — seeds `varPercyOpen / varChatClosing / varChatKey / varPercyThinking / varSessionId / colChat` |
| `imgPercy` | Image | `Image` | [`imgPercy.Image.powerfx`](formulas/imgPercy.Image.powerfx) — peering Percy + bubbles |
| `imgPercy` | Image | `OnSelect` | [`imgPercy.OnSelect.powerfx`](formulas/imgPercy.OnSelect.powerfx) — open chat |
| **conPercyChat** | Container | `Visible` | `varPercyOpen` |
| `imgChatBg` | Image | `Image` | [`imgChatBg.Image.powerfx`](formulas/imgChatBg.Image.powerfx) — window + entrance/exit |
| `imgClose` | Image | `Image` / `OnSelect` | [`imgClose.Image.powerfx`](formulas/imgClose.Image.powerfx) · [`imgClose.OnSelect.powerfx`](formulas/imgClose.OnSelect.powerfx) |
| `tmrCloseChat` | Timer | `OnTimerEnd` | [`tmrCloseChat.OnTimerEnd.powerfx`](formulas/tmrCloseChat.OnTimerEnd.powerfx) |
| `galChat` | Gallery (blank vertical) | `Items` | [`galChat.Items.powerfx`](formulas/galChat.Items.powerfx) — `Sort(colChat, Seq)` |
| `htmlBubble` (in galChat) | HTML text | `HtmlText` | [`htmlBubble.HtmlText.powerfx`](formulas/htmlBubble.HtmlText.powerfx) |
| `txtChat` | Text input | — | `HintText="Ask Percy a question…"`, `BorderColor=Transparent`, `Fill=Transparent` |
| `imgSend` | Image | `Image` / `OnSelect` | [`imgSend.Image.powerfx`](formulas/imgSend.Image.powerfx) · [`imgSend.OnSelect.powerfx`](formulas/imgSend.OnSelect.powerfx) |

Every Image: `ImagePosition = Fit`.

---

## 2. Layout

**Percy** lives on the ribbon (any screen you want him on). Put `imgPercy` near the
top‑right so he peers over the edge — e.g. `X=900 Y=26 W=210 H=116`. The whole image
is the tap target, so keep him in the corner where there are no live controls beneath
(nudge left/down if he overlaps the identity chip). He shows on a static render too,
so he's always "there".

**The chat** is a **Container `conPercyChat`** (`Visible = varPercyOpen`) so everything
shows/hides as one unit. Suggested container: `X=752 Y=60 Width=368 Height=520`.
Children use coordinates **relative to the container**:

| Child | X | Y | W | H | Notes |
|---|---:|---:|---:|---:|---|
| `imgChatBg` | 0 | 0 | 368 | 520 | back layer |
| `imgClose` | 324 | 16 | 28 | 28 | on the green header |
| `galChat` | 16 | 72 | 336 | 374 | messages |
| `txtChat` | 28 | 470 | 264 | 36 | transparent over the baked input pill |
| `imgSend` | 312 | 470 | 40 | 40 | send |
| `tmrCloseChat` | 0 | 0 | 0 | 0 | `Visible=false` |

`galChat`: blank **vertical** gallery, `TemplatePadding=2`. Inside it one **HTML text**
control `htmlBubble` (`X=0 Y=0 Width=Parent.TemplateWidth`, **`AutoHeight=true`**) with
`HtmlText` = the bubble formula. Turn on the gallery's flexible/auto height so bubbles
size to their text.

> **Prefer one control over a gallery?** You can drop the gallery and render the whole
> transcript in a single AutoHeight HTML text control with
> `Concat( Sort(colChat, Seq), <the htmlBubble markup> )`, placed inside a 1‑row
> scrolling gallery. Same bubble markup; no per‑item height fuss.

### Open / close animation (no screen switch)
- **Open:** `imgPercy.OnSelect` sets `varPercyOpen=true`, `varChatClosing=false`, and
  bumps `varChatKey`. `imgChatBg`'s `<desc>` contains `varChatKey`, so the image reloads
  and replays its **`cin`** (scale‑up from the top‑right) animation.
- **Close:** `imgClose.OnSelect` sets `varChatClosing=true` (+ bumps `varChatKey`).
  `imgChatBg` reloads and plays **`cout`** (scale‑down). The container is *still visible*.
- **Then hide:** `tmrCloseChat` (`Start=varChatClosing`, `Duration=360`, `Repeat=false`)
  fires when the exit finishes and sets `varPercyOpen=false` (and clears `varChatClosing`).
  Navigation never depends on the timer — only the final hide does.

---

## 3. Data model

`colChat` rows: `{ Seq: Number, Role: "user" | "percy", Body: Text }`. `App.OnStart`
seeds Percy's greeting. `varSessionId` (a `GUID()`) tags the conversation so the flow /
SharePoint can group it.

---

## 4. SharePoint + Power Automate (wire up later)

### 4a. SharePoint lists
1. **`PercyKnowledge`** (what Percy knows) — columns: `Title`, `Answer` (multi‑line),
   `Keywords` (text), `Category` (choice). Fill it with FAQ‑style rows (scoring rules,
   CAP definitions, deadlines, etc.).
2. **`PercyChatLog`** (optional transcript) — columns: `SessionId` (text),
   `Role` (choice user/percy), `Message` (multi‑line), `Seq` (number), `Asked By` (person).

### 4b. Flow `PercyAsk` (instant cloud flow, **PowerApps (V2)** trigger)
Inputs: `question` (text), `sessionId` (text). Steps:
1. *(optional)* **Get items** from `PercyKnowledge` (filter on keywords) to build context.
2. **Generate the answer** — use **AI Builder → "Create text with GPT"** (or an HTTP
   action to **Azure OpenAI**), prompt = your context + the `question`.
3. *(optional)* **Create item** in `PercyChatLog` for the question and the answer.
4. **Respond to a PowerApp or flow** → output `answer` = the generated text.

### 4c. Connect it in the app
Add the flow to the app (**Power Automate** pane), then swap the stub in
[`imgSend.OnSelect.powerfx`](formulas/imgSend.OnSelect.powerfx) for the real call:

```powerfx
Set( varPercyA, PercyAsk.Run( varPercyQ, varSessionId ).answer );
Collect( colChat, { Seq: CountRows(colChat) + 1, Role: "percy", Body: varPercyA } );
```

Until then the stub collects a placeholder reply so the whole UI is testable.

> **Async alternative:** instead of `.Run` (synchronous), the flow can *write* the answer
> to `PercyChatLog`; the app then reads new rows (e.g. a Timer doing
> `ClearCollect(colChat, Filter(PercyChatLog, SessionId = varSessionId))`). Simpler to
> start with `.Run`.

---

## 5. Components
| | |
|---|---|
| Percy (two bubbles) | ![percy](previews/percy.png) ![percy2](previews/percy-bubble2.png) |
| Chat window · Send · Close | ![bg](previews/chat-bg.png) ![send](previews/send-button.png) ![close](previews/close-button.png) |

## 6. Notes
- **Typing indicator:** `varPercyThinking` is set while awaiting the reply — show a small
  "Percy is typing…" label/HTML bubble bound to it if you like.
- **Send on Enter:** Text input has no native Enter event; keep the send button (or use a
  hidden button with a keyboard shortcut component).
- **Reduced motion:** every Percy/chat animation honours `prefers-reduced-motion`.
