# Build `Percy-Query` by hand (Power Automate) — the single diagnostic flow

One flow serves every diagnostic. The Percy agent calls it with a **template key** + `ope`/`who`
(never DAX); the flow `Switch`es to that key's fixed query
([`dax-templates.md`](dax-templates.md)), runs it via Power BI, and returns the evidence.

**Connections:** Microsoft Copilot Studio (trigger/response), Power BI (signed-in shared account
with workspace read + dataset **Build**).

## 1. Trigger

**Microsoft Copilot Studio → When an agent calls the flow.** Three Text inputs, named exactly:
- **`template`** — the diagnostic key. **Required** (the tool's input description tells the agent
  which key; see `../copilot-studio/topics.md`).
- **`ope`** — the OPE deal id. **Optional** (⋯ → *Make the field optional*).
- **`who`** — the caller's email. **Optional.**

## 2. Input rules (these are what keep production alive)

The `Run_an_agent` BadRequest ("The agent requested human input… specify HITL users") fires when the
agent **suspends mid-run waiting for input**. Three causes, all handled:

1. **Forced collection on a required input the fill-model didn't fill.** `ope`/`who` are optional,
   so only `template` can force collection — and its input description (topics.md) tells the agent
   exactly which key to choose, including the vague-question → `Summary` and bare-OPE → `Locate`
   defaults. **The `ope` no-deal case uses the sentinel `NONE`** — the agent is instructed to pass
   the literal text `NONE` when no deal id exists. "Leave it blank" is unreliable (and unsatisfiable
   on required schemas); a concrete value is an instruction the fill-model can always follow.
   *(Verified working 2026-07-16: run panel showed `template=Summary`, `ope=NONE`, `who=<email>`,
   no prompts.)*
2. **Consent cards** — every tool registration: *Ask the end user before running* = **No**,
   *Credentials to use* = **Maker-provided credentials**.
3. **Question nodes in topics** — none in the diagnostic path.

A question as the agent's **final text reply is not a suspension** — asking for a missing deal
number in chat is safe and is the designed behaviour (GOLDEN RULES in the instructions).

## 3. Switch on `template`

**Control → Switch**, **On** = the `template` input. Add a case per key and type the key into each
case's **Equals** box as plain text (exact spelling — a blank Equals throws
`Flow clientdata is in invalid format … 'case' … null` on save):
`Locate` · `CompleteCare` · `CAP` · `IBExpand` · `CustomerCentricity` · `IPGreenLake` ·
`Accreditation` · `Summary`.

**Inside each case put ONE Compose only** (named `Dax_<key>`, e.g. `Dax_CompleteCare`) — paste that
key's query from [`dax-templates.md`](dax-templates.md) as **plain text**, then insert the `ope` /
`who` dynamic-content chips between the quotes on the `VAR` lines. No fx, no replace(), no
escaping. Do **not** put the Power BI action inside the cases.

> The `NONE` sentinel is harmless in the DAX: user-level queries never read `Ope`, and per-deal
> queries return `Found = "No"` for it — the agent then asks for the real deal number. Optional
> hardening: a Condition before the Switch (`ope` = `NONE` **or** blank, **and** `template` is a
> per-deal key) → respond `{"error":"missing_ope"}`.

**Default case:** Respond to the agent with `evidence` = `{"error":"unknown_template"}` — no
arbitrary key ever runs anything.

## 4. After the Switch — once each

1. **Compose `DaxQuery`** =
   `coalesce(outputs('Dax_Locate'), outputs('Dax_CompleteCare'), outputs('Dax_CAP'), outputs('Dax_IBExpand'), outputs('Dax_CustomerCentricity'), outputs('Dax_IPGreenLake'), outputs('Dax_Accreditation'), outputs('Dax_Summary'))`
   — only the matched case ran, so this returns its DAX. **Names must match your Composes with
   spaces as underscores** (`Dax CC` → `outputs('Dax_CC')`).
2. **Power BI → Run a query against a dataset** — ONE action, after the Switch, never per-case.
   Workspace + Dataset = the 1% Club semantic model; **Query text** = Outputs of `DaxQuery`.
   *("Invalid parameters" until Workspace/Dataset/Query are all set is normal.)*
3. **Respond to the agent** — output Text **`evidence`** =
   `string(outputs('Run_a_query_against_a_dataset')?['body/firstTableRows'])`.

## Flow at a glance
```
When an agent calls the flow   (template required · ope/who OPTIONAL · no-deal ope = "NONE")
├─ Switch(template)
│   ├─ <each key> → Compose Dax_<key>   (paste query, insert ope/who chips)
│   └─ Default    → Respond {"error":"unknown_template"}
├─ Compose DaxQuery = coalesce(all the case Composes)
├─ Power BI: Run a query against a dataset (DaxQuery)   ⟵ ONE action
└─ Respond: evidence = string(firstTableRows)           ⟵ ONE response
```

## After any trigger-input change

Renaming/re-typing/adding options to trigger inputs changes the tool schema; the Copilot Studio
tool holds the old one until you **remove and re-add it** (Description + input Customize texts get
wiped — re-paste), then **Publish**. Symptoms: "Destination agent was updated", "Output binding not
found", inputs typed `unknown`.

## Security
- Approved keys only — unknown `template` hits Default. The agent passes a **key, never a query**;
  there is no endpoint that runs agent-supplied DAX.
- Return only the projected evidence columns — never raw rows or entity ids.
- Least-privilege signed-in shared connection.
