# Percy diagnostic flows — canonical DAX (one query per flow)

One small flow per diagnostic; each flow embeds exactly one of the queries below (no Switch, no
template key). Build steps: [`Percy-Diagnostics.build.md`](Percy-Query.build.md). Grounded in the
live model (2026-07 TMDL): `Final` (calculated point columns `CC New Logo Points`, `CC Points new`,
`CC Points Final`, `CC Points Funnel`, `IB & NS Points NEW`, `IB & NS Points Funnel`), `Teams`
(per-user aggregates + `S Coded?`/`Completed?`/`Job Family`), `Cap Won`, `Cap Requests`,
`Customer Meetings`, `IP GL`.

**Inserting values:** paste each query as **plain text** into the flow's Compose. On the
`VAR Ope = ""` / `VAR Who = ""` lines, put the cursor between the quotes and insert the trigger
input from **Dynamic content**. No `fx`, no `replace()`, no escaping.

**Evidence keys are deliberately unabbreviated** — "CC" is never used alone (Complete Care vs
Customer Centricity). Only CAP and Customer Centricity can ever be "pending"; approval blank =
pending, "Approve" = approved.

---

## 1. Percy-Summary — flow input: `who`

```dax
DEFINE
    VAR Who = ""
EVALUATE
SELECTCOLUMNS (
    FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) ),
    "User",                        'Teams'[User Email],
    "Name",                        'Teams'[Name],
    "Crew",                        'Teams'[Crew],
    "CompleteCarePoints",          'Teams'[New CC Logo Points],
    "IBExpandPoints",              'Teams'[IB & NS Points],
    "CapRequestPoints",            'Teams'[Cap Requests],
    "CapOrderPoints",              'Teams'[Cap Won Points],
    "CustomerCentricityPoints",    'Teams'[Customer Centricity Points],
    "AccreditationAndBonusPoints", 'Teams'[Manager Sponsor Points],
    "IPinGreenLakePoints",         'Teams'[IP in GL points],
    "CapRequestsPending",          'Teams'[Cap Requests Pending],
    "CapOrdersPending",            'Teams'[Cap Won Points Pending],
    "CustomerCentricityPending",   'Teams'[Customer Centricity Points Pending]
)
```
Notes: `Teams[New CC Logo Points]` sums `Final[CC Points Final]`, so it already includes Uplift —
hence the key `CompleteCarePoints`. `AccreditationAndBonusPoints` includes the S-coded race share,
CSM 30, crew spot-prize bonus and individual bonus.

## 2. Percy-Locate — flow input: `ope`

```dax
DEFINE
    VAR Ope = ""
EVALUATE
ROW (
    "OPE", Ope,
    "InOpportunities", COUNTROWS ( FILTER ( ALL ( 'Final' ), 'Final'[HPE Opportunity Id] = Ope ) ) + 0,
    "InCapWon",        COUNTROWS ( FILTER ( ALL ( 'Cap Won' ), 'Cap Won'[HPE Opportunity Id] = Ope ) ) + 0,
    "InCapRequests",   COUNTROWS ( FILTER ( ALL ( 'Cap Requests' ), 'Cap Requests'[Opportunity ID] = Ope ) ) + 0,
    "InMeetings",      COUNTROWS ( FILTER ( ALL ( 'Customer Meetings' ), 'Customer Meetings'[HPE Opportunity Id] = Ope ) ) + 0
)
```

## 3. Percy-CompleteCare — flow inputs: `ope`, `who`

```dax
DEFINE
    VAR Ope = ""
    VAR Who = ""
    VAR OppRows = FILTER ( ALL ( 'Final' ), 'Final'[HPE Opportunity Id] = Ope )
EVALUATE
ROW (
    "OPE", Ope,
    "Found", IF ( COUNTROWS ( OppRows ) > 0, "Yes", "No" ),
    "OpportunityName", MAXX ( OppRows, 'Final'[Opportunity Name] ),
    "Account", MAXX ( OppRows, 'Final'[Account Name] ),
    "ForecastCategory", MAXX ( OppRows, 'Final'[Forecast Category] ),
    "CloseDate", FORMAT ( MAXX ( OppRows, 'Final'[Close Date] ), "yyyy-mm-dd" ),
    "OpportunityOwner", MAXX ( OppRows, 'Final'[Opportunity Owner] ),
    "PrimaryPipelineOwner", MAXX ( OppRows, 'Final'[Primary Pipeline Owner User] ),
    "CreditsToYou",
        IF ( Who <> ""
            && COUNTROWS ( FILTER ( OppRows,
                   LOWER ( 'Final'[Opportunity Owner Email] ) = LOWER ( Who )
                || LOWER ( 'Final'[Primary Pipeline Owner User Email] ) = LOWER ( Who ) ) ) > 0,
            "Yes", "No" ),
    "HasCompleteCareProduct",
        IF ( COUNTROWS ( FILTER ( OppRows, CONTAINSSTRING ( 'Final'[Product Name], "9X" ) ) ) > 0, "Yes", "No" ),
    "HasNewSolutionMotion",
        IF ( COUNTROWS ( FILTER ( OppRows, 'Final'[Sales Motion] = "New Solution S" ) ) > 0, "Yes", "No" ),
    "HasDay1Product",
        IF ( COUNTROWS ( FILTER ( OppRows, CONTAINSSTRING ( 'Final'[Product Name], "Day 1" ) ) ) > 0, "Yes", "No" ),
    "Won", IF ( COUNTROWS ( FILTER ( OppRows, 'Final'[Forecast Category] = "Won" ) ) > 0, "Yes", "No" ),
    "CloseOnOrAfter1May2026",
        IF ( MAXX ( OppRows, 'Final'[Close Date] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "NewLogoPointsAwarded", MAXX ( OppRows, 'Final'[CC New Logo Points] ) + 0,
    "UpliftPointsAwarded", MAXX ( OppRows, 'Final'[CC Points new] ) + 0,
    "CompleteCarePointsTotal", MAXX ( OppRows, 'Final'[CC Points Final] ) + 0,
    "InFunnelNotYetWon",
        IF ( COUNTROWS ( FILTER ( OppRows, 'Final'[CC Points Funnel] = "Y" ) ) > 0, "Yes", "No" )
)
```
Reading it: New Logo pays 100 when product 9X + New Solution S + Won + close ≥ 1 May 2026 and the
customer has no Complete Care contract started before 1 Apr 2026 (entity-matched in the model).
Uplift pays 75 when 9X + (New Solution S or Day 1 product) + Won + close qualifies and New Logo is 0.
If every gate shows Yes but `NewLogoPointsAwarded` is 0 and `UpliftPointsAwarded` is 75, the customer
already had a Complete Care contract — that is the New Logo blocker.

## 4. Percy-IBExpand — flow inputs: `ope`, `who`

```dax
DEFINE
    VAR Ope = ""
    VAR Who = ""
    VAR OppRows = FILTER ( ALL ( 'Final' ), 'Final'[HPE Opportunity Id] = Ope )
EVALUATE
ROW (
    "OPE", Ope,
    "Found", IF ( COUNTROWS ( OppRows ) > 0, "Yes", "No" ),
    "OpportunityName", MAXX ( OppRows, 'Final'[Opportunity Name] ),
    "ForecastCategory", MAXX ( OppRows, 'Final'[Forecast Category] ),
    "CloseDate", FORMAT ( MAXX ( OppRows, 'Final'[Close Date] ), "yyyy-mm-dd" ),
    "OpportunityOwner", MAXX ( OppRows, 'Final'[Opportunity Owner] ),
    "PrimaryPipelineOwner", MAXX ( OppRows, 'Final'[Primary Pipeline Owner User] ),
    "CreditsToYou",
        IF ( Who <> ""
            && COUNTROWS ( FILTER ( OppRows,
                   LOWER ( 'Final'[Opportunity Owner Email] ) = LOWER ( Who )
                || LOWER ( 'Final'[Primary Pipeline Owner User Email] ) = LOWER ( Who )
                || LOWER ( 'Final'[OS Sales Email] ) = LOWER ( Who ) ) ) > 0,
            "Yes", "No" ),
    "HasRenewalMotion",
        IF ( COUNTROWS ( FILTER ( OppRows,
            'Final'[Sales Motion] IN { "Renewal", "Conversion", "PWCP Bus Type 'W'" } ) ) > 0, "Yes", "No" ),
    "HasNewExpandMotion",
        IF ( COUNTROWS ( FILTER ( OppRows,
            'Final'[Sales Motion] IN { "New Solution S", "Per Event P" } ) ) > 0, "Yes", "No" ),
    "Won", IF ( COUNTROWS ( FILTER ( OppRows, 'Final'[Forecast Category] = "Won" ) ) > 0, "Yes", "No" ),
    "CloseOnOrAfter1May2026",
        IF ( MAXX ( OppRows, 'Final'[Close Date] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "SuppressedByCompleteCare",
        IF ( MAXX ( OppRows, 'Final'[CC Points Final] ) > 0, "Yes", "No" ),
    "IBExpandPointsAwarded", MAXX ( OppRows, 'Final'[IB & NS Points NEW] ) + 0,
    "InFunnelNotYetWon",
        IF ( COUNTROWS ( FILTER ( OppRows, 'Final'[IB & NS Points Funnel] = "Y" ) ) > 0, "Yes", "No" )
)
```
Points are pro-rata: expand value ÷ (expand + renewal value) × 25, so partial awards are normal.
A deal that scores any Complete Care points never pays IB/Expand (`SuppressedByCompleteCare`).

## 5. Percy-CAP — flow inputs: `ope`, `who`

```dax
DEFINE
    VAR Ope = ""
    VAR Who = ""
    VAR CallerName =
        MAXX ( FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) ), 'Teams'[Name] )
    VAR WonRows = FILTER ( ALL ( 'Cap Won' ), 'Cap Won'[HPE Opportunity Id] = Ope )
    VAR ReqRows = FILTER ( ALL ( 'Cap Requests' ), 'Cap Requests'[Opportunity ID] = Ope )
EVALUATE
ROW (
    "OPE", Ope,
    "CallerName", CallerName,
    "InCapWon", IF ( COUNTROWS ( WonRows ) > 0, "Yes", "No" ),
    "CapOrderForecast", MAXX ( WonRows, 'Cap Won'[Forecast Category] ),
    "CapOrderCloseDate", FORMAT ( MAXX ( WonRows, 'Cap Won'[Close Date] ), "yyyy-mm-dd" ),
    "CapOrderCloseQualifies",
        IF ( MAXX ( WonRows, 'Cap Won'[Close Date] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "CapOrderApprovalStatus", MAXX ( WonRows, 'Cap Won'[Approval Status] ),
    "CapOrderCreditsToYou",
        IF ( Who <> ""
            && COUNTROWS ( FILTER ( WonRows,
                   LOWER ( 'Cap Won'[Opportunity Owner Email] ) = LOWER ( Who )
                || LOWER ( 'Cap Won'[Primary Pipeline Owner User Email] ) = LOWER ( Who ) ) ) > 0,
            "Yes", "No" ),
    "InCapRequests", IF ( COUNTROWS ( ReqRows ) > 0, "Yes", "No" ),
    "RequestCreatedDate", FORMAT ( MAXX ( ReqRows, 'Cap Requests'[Created Date Time] ), "yyyy-mm-dd" ),
    "RequestCreatedQualifies",
        IF ( MAXX ( ReqRows, 'Cap Requests'[Created Date Time] ) >= DATE ( 2026, 5, 1 ), "Yes", "No" ),
    "RequestLoggedBy", MAXX ( ReqRows, 'Cap Requests'[Support Request: Created By] ),
    "RequestLoggedByMatchesYou",
        IF ( COUNTROWS ( FILTER ( ReqRows,
            'Cap Requests'[Support Request: Created By] = CallerName ) ) > 0, "Yes", "No" ),
    "RequestApprovalStatus", MAXX ( ReqRows, 'Cap Requests'[Approval Status] )
)
```
CAP orders (50) credit by EMAIL (owner or primary pipeline owner). CAP requests (20) credit by NAME
(logged-by must match the caller's dashboard name). Approval blank = pending Gemma/BD.

## 6. Percy-Meetings — flow inputs: `ope`, `who`

```dax
DEFINE
    VAR Ope = ""
    VAR Who = ""
    VAR CallerName =
        MAXX ( FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) ), 'Teams'[Name] )
EVALUATE
SELECTCOLUMNS (
    FILTER ( ALL ( 'Customer Meetings' ), 'Customer Meetings'[HPE Opportunity Id] = Ope ),
    "MeetingType", 'Customer Meetings'[Meeting Type],
    "Classified",
        IF ( 'Customer Meetings'[Meeting Type]
            IN { "Customer Meeting", "Channel Partner Meeting", "Leadership Meeting" }, "Yes", "No" ),
    "LoggedBy", 'Customer Meetings'[Last Modified By: Full Name],
    "LoggedByMatchesYou",
        IF ( 'Customer Meetings'[Last Modified By: Full Name] = CallerName, "Yes", "No" ),
    "ApprovalStatus", 'Customer Meetings'[Approval Status],
    "PointsWhenApproved",
        SWITCH ( 'Customer Meetings'[Meeting Type],
            "Leadership Meeting", 20,
            "Customer Meeting", 10,
            "Channel Partner Meeting", 10,
            0 )
)
```
Returns one row per meeting on the deal (empty array = none logged). Classification is the
`Meeting Type` field; credit is by name (`Last Modified By: Full Name` vs the caller's dashboard
name); approval blank = pending the weekly manager approval. Scoring applies no date gate to
meetings.

## 7. Percy-IPGreenLake — flow input: `who`

```dax
DEFINE
    VAR Who = ""
    VAR vMay = CALCULATE ( SUM ( 'IP GL'[May] ),  FILTER ( ALL ( 'IP GL' ), LOWER ( 'IP GL'[Email] ) = LOWER ( Who ) ) )
    VAR vJun = CALCULATE ( SUM ( 'IP GL'[June] ), FILTER ( ALL ( 'IP GL' ), LOWER ( 'IP GL'[Email] ) = LOWER ( Who ) ) )
    VAR pMay = SWITCH ( TRUE (), ISBLANK ( vMay ) || vMay <= 0, 0, vMay < 0.1, 10, vMay < 0.25, 20, vMay < 0.4, 30, vMay < 0.5, 50, 75 )
    VAR pJun = SWITCH ( TRUE (), ISBLANK ( vJun ) || vJun <= 0, 0, vJun < 0.1, 10, vJun < 0.25, 20, vJun < 0.4, 30, vJun < 0.5, 50, 75 )
EVALUATE
ROW (
    "User", Who,
    "MayPercent", FORMAT ( vMay, "0.0%" ),
    "MayPoints", pMay,
    "JunePercent", FORMAT ( vJun, "0.0%" ),
    "JunePoints", pJun,
    "TotalIPPoints", pMay + pJun
)
```
Recognised per month and summed (May + June so far). Tiers: under 10% = 10, 10–25% = 20,
25–40% = 30, 40–50% = 50, 50%+ = 75.

## 8. Percy-Accreditation — flow input: `who`

```dax
DEFINE
    VAR Who = ""
EVALUATE
SELECTCOLUMNS (
    FILTER ( 'Teams', LOWER ( 'Teams'[User Email] ) = LOWER ( Who ) ),
    "Name", 'Teams'[Name],
    "Crew", 'Teams'[Crew],
    "ManagerSponsor", 'Teams'[Manager Sponsor],
    "SCoded", 'Teams'[S Coded?],
    "AccreditationCompletionStatus", 'Teams'[Completed?],
    "JobFamily", 'Teams'[Job Family],
    "AccreditationAndBonusPoints", 'Teams'[Manager Sponsor Points]
)
```
Eligibility: `SCoded` must be "S-Coded (Phil)"; Customer Success Architects are excluded unless the
person is Adrian Goggin or Garren Meakin. The 100/50/20 is a team race per manager-sponsor group,
split across the group, decided by completion date; CSMs (L2+) get 30 on completion; the points
figure also contains crew and individual spot bonuses — say "accreditation and bonus points", not
just "accreditation".

---

## Power BI action (same in every flow)

Connector **Power BI → Run a query against a dataset**: Workspace = the 1% Club workspace,
Dataset = the semantic model, **Query text = Outputs of the flow's DAX Compose**. Returns
`firstTableRows` (array of row objects keyed by the names above). The connection is the signed-in
shared account (workspace read + dataset **Build**).
