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
A refresh **fails** if one is already in progress, so we turn success/failure into a friendly status.

> **First, the thing that confuses everyone:** *Refresh a dataset* returns an **empty body — it has NO
> dynamic outputs, ever.* That's normal. You will NOT pick dynamic content into these Composes; you
> **type literal text** (`started` / `already_running`). The signal we're capturing is whether the
> Refresh action **succeeded or failed**, and that's captured with **Configure run after** — not with
> outputs.

Build it like this:

1. **Two parallel Composes under the Refresh.** Click the **+** directly under **Refresh a dataset**
   → **Add a parallel branch** (not "Add an action").
   - Branch A: **Compose**, rename it exactly **`Status_started`**, **Inputs:** type the plain text
     `started` (the dynamic-content pane is empty — ignore it).
   - Branch B: **Compose**, rename it exactly **`Status_already`**, **Inputs:** type `already_running`.
2. **Make branch B the failure branch.** Select `Status_already` → **⋯ / Settings → Configure run
   after** → under *Refresh a dataset* tick **has failed** + **has timed out**, untick **is
   successful**. (`Status_started` keeps the default *is successful*.)
3. **Compose `StatusOut` — rejoining the branches.** There's no "merge" line to draw: **the join IS
   the run-after dependencies** — an action "rejoins" branches by running after *both* of them.
   Two ways to get there:
   - **The converge +:** below the whole parallel block (where the two branch lines meet and the flow
     returns to a single column) there's a centre **+** — an action added *there* depends on both
     branches automatically. ⚠️ The + hanging under either Compose extends **that branch only**.
   - **By hand (always works):** add the Compose anywhere after the branches (even inside one), then
     open **Configure run after** on it and **add the other branch's Compose as a second predecessor**
     ("+ select actions").

   Either way: rename it **`StatusOut`** and set **Inputs** via the **fx / Expression** tab (not
   plain text): `coalesce(outputs('Status_started'), outputs('Status_already'))`
4. **⚠️ Run-after on `StatusOut` — the trap.** In any run exactly one branch executes while the other
   is **Skipped**. Open **Configure run after** on `StatusOut` and for **each** predecessor tick
   **is successful AND is skipped**. If you leave the default, `StatusOut` is skipped whenever either
   branch is — i.e. every run — and the flow dies. With *is skipped* ticked, the skipped Compose's
   `outputs()` is just null and `coalesce` returns the one that ran.
   - **Verify the join here too:** this dialog must list **both** `Status_started` and
     `Status_already` as predecessors, each with *successful + skipped* ticked. Only one listed =
     the branches haven't rejoined — add the missing one.

> **Naming:** `outputs('…')` uses the **internal** name — spaces become underscores (`Status started`
> → `outputs('Status_started')`). Name the Composes with underscores from the start.

*(Minimal alternative: skip all of step 3 and return the literal `started` in step 4 — works fine, you
just can't distinguish "already running".)*

## 4. Return to Copilot Studio
Add **Microsoft Copilot Studio → Respond to Copilot Studio**.
- **+ Add an output → Text**, name **`status`**, value via **fx**: `outputs('StatusOut')` (or the
  literal text `started` in the minimal version).

Save, then add this flow to the Percy agent as the action **"Refresh Dashboard"**
(see [`../copilot-studio/topics.md`](../copilot-studio/topics.md)).

---

## Flow at a glance
```
When Copilot Studio calls the flow   (no inputs)
├─ Power BI: Refresh a dataset   (1% Club model — returns an EMPTY body, no dynamic outputs)
│    ├─ Compose Status_started = "started"          (typed text · run after: is successful)
│    └─ Compose Status_already = "already_running"  (typed text · run after: has failed/timed out)
├─ Compose StatusOut = coalesce(outputs('Status_started'), outputs('Status_already'))
│                                    (run after BOTH: is successful + IS SKIPPED)
└─ Respond to Copilot Studio: status = outputs('StatusOut')
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
