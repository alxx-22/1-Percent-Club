# Build `Percy-Refresh` by hand (Power Automate)

The agent's **second** action — "Refresh Dashboard." Dead simple: the agent calls it, it triggers a
Power BI dataset refresh, it replies. Build pack §7.5.

**Connections:** Microsoft Copilot Studio (trigger/response), Power BI. No inputs.

---

## 1. Create the flow
- **Create → Automated cloud flow → Skip**.
- Trigger: **Microsoft Copilot Studio → When Copilot Studio calls a flow**.
- Name: `Percy-Refresh`. (No trigger inputs — it always refreshes the one 1% Club model.)

## 2. Refresh the dataset
Add **Power BI → Refresh a dataset**.
- **Workspace:** the 1% Club workspace.
- **Dataset:** the semantic model.

> **Don't loop.** One refresh per call. Power BI limits refreshes per day (Pro ~8, Premium/PPU ~48),
> so Percy must not fire repeated refreshes — the instruction set already says "one per request".

## 3. (Recommended) handle "already running"
A refresh fails if one is already in progress. Wrap step 2 so that case returns a friendly status
instead of an error:
- On the **Refresh a dataset** action → **⋯ → Configure run after** isn't enough alone; simplest is a
  parallel branch:
  - **Compose `Status` = "started"** (run after Refresh **is successful**).
  - **Compose `Status` = "already_running"** (run after Refresh **has failed / timed out** — the
    connector returns a conflict when a refresh is in progress).
- Then a **Compose `StatusOut`** = `coalesce(outputs('Status_started'),outputs('Status_already'))`.

*(If you'd rather keep it minimal: skip the branch and just return "started"; Percy's copy still reads
well, you just won't distinguish "already running".)*

## 4. Return to Copilot Studio
Add **Microsoft Copilot Studio → Respond to Copilot Studio**.
- **+ Add an output → Text**, name **`status`**, value `outputs('StatusOut')` (or the literal
  `"started"` in the minimal version).

Save, then add this flow to the Percy agent as the action **"Refresh Dashboard"**
(see [`../copilot-studio/topics.md`](../copilot-studio/topics.md)).

---

## Flow at a glance
```
When Copilot Studio calls the flow   (no inputs)
├─ Power BI: Refresh a dataset  (1% Club model)
│    ├─ success  → Compose Status = "started"
│    └─ failed   → Compose Status = "already_running"
├─ Compose StatusOut = coalesce(...)
└─ Respond to Copilot Studio: status = StatusOut
```

## What Percy says (from the returned status)
- `started` → "I've kicked off a refresh — it takes a few minutes. Check back shortly."
- `already_running` → "A refresh is already running — give it a few minutes and it'll be current."
- `error` → "I couldn't start a refresh just now — try again shortly, or ping the programme team."

## Notes
- **Read/refresh only** — this changes data *freshness*, nothing else. It's the only action that
  "does" anything, and even then it's just a refresh.
- **Connection:** the signed-in shared account needs **refresh** permission on the dataset.
- **Deferred:** an `Add Points` action (owners award points) is out of scope — it needs approver
  identity + an audit/approval trail + a governed write. Build it separately when ready.
