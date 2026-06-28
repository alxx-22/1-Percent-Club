<#
.SYNOPSIS
    Provisions the PercyConversations SharePoint list (columns + types + indexing)
    used by the Percy assistant. Idempotent — safe to re-run.

.DESCRIPTION
    Creates the list if it doesn't exist, then adds every column from the build pack
    (PERCY_BUILD_PACK.md §2, "one row per message" shape). Multi-line columns are
    forced to PLAIN TEXT (RichText=FALSE) so JSON/answers aren't HTML-mangled. Role
    and Status are single-line text (NOT Choice) so `Role = "user"` comparisons don't
    return a record.

.PREREQUISITES
    - PnP.PowerShell module:  Install-Module PnP.PowerShell -Scope CurrentUser
    - An Entra app registration PnP can use. Either:
        * one-time:  Register-PnPEntraIDApp -ApplicationName "PnP-Percy" -Tenant <tenant>.onmicrosoft.com -Interactive
        * then pass the resulting -ClientId below.
      (Microsoft removed the built-in PnP Management Shell app; you must supply a ClientId.)

.EXAMPLE
    ./Provision-PercyConversations.ps1 `
        -SiteUrl "https://hpe-my.sharepoint.com/personal/alex_cohen_hpe_com" `
        -ClientId "00000000-0000-0000-0000-000000000000"
#>
param(
    [Parameter(Mandatory = $true)] [string] $SiteUrl,
    [Parameter(Mandatory = $true)] [string] $ClientId,
    [string] $ListName = "PercyConversations"
)

$ErrorActionPreference = "Stop"
Write-Host "Connecting to $SiteUrl ..." -ForegroundColor Cyan
Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $ClientId

# 1) List ---------------------------------------------------------------------
$list = Get-PnPList -Identity $ListName -ErrorAction SilentlyContinue
if (-not $list) {
    Write-Host "Creating list '$ListName' ..." -ForegroundColor Green
    $list = New-PnPList -Title $ListName -Template GenericList -OnQuickLaunch
} else {
    Write-Host "List '$ListName' already exists — adding any missing columns." -ForegroundColor Yellow
}

# 2) Fields (internal name -> field XML). Plain-text Note fields use RichText=FALSE.
#    ConversationId + Status are Indexed for fast Get-items filtering.
$fields = [ordered]@{
    "ConversationId" = '<Field Type="Text"   DisplayName="ConversationId" Name="ConversationId" StaticName="ConversationId" Indexed="TRUE"  MaxLength="255" />'
    "Seq"            = '<Field Type="Number" DisplayName="Seq"            Name="Seq"            StaticName="Seq"            Decimals="0" />'
    "Role"           = '<Field Type="Text"   DisplayName="Role"           Name="Role"           StaticName="Role"           MaxLength="32" />'
    "Body"           = '<Field Type="Note"   DisplayName="Body"           Name="Body"           StaticName="Body"           RichText="FALSE" RichTextMode="Compatible" NumLines="6"  AppendOnly="FALSE" />'
    "Reply"          = '<Field Type="Note"   DisplayName="Reply"          Name="Reply"          StaticName="Reply"          RichText="FALSE" RichTextMode="Compatible" NumLines="6"  AppendOnly="FALSE" />'
    "Status"         = '<Field Type="Text"   DisplayName="Status"         Name="Status"         StaticName="Status"         Indexed="TRUE"  MaxLength="32" />'
    "ErrorMessage"   = '<Field Type="Note"   DisplayName="ErrorMessage"   Name="ErrorMessage"   StaticName="ErrorMessage"   RichText="FALSE" RichTextMode="Compatible" NumLines="6"  AppendOnly="FALSE" />'
    "UserEmail"      = '<Field Type="Text"   DisplayName="UserEmail"      Name="UserEmail"      StaticName="UserEmail"      MaxLength="255" />'
    "MetricType"     = '<Field Type="Text"   DisplayName="MetricType"     Name="MetricType"     StaticName="MetricType"     MaxLength="64" />'
    "OPE"            = '<Field Type="Text"   DisplayName="OPE"            Name="OPE"            StaticName="OPE"            MaxLength="64" />'
}

foreach ($name in $fields.Keys) {
    $existing = Get-PnPField -List $ListName -Identity $name -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host ("  = {0} already present" -f $name)
        continue
    }
    Write-Host ("  + adding {0}" -f $name) -ForegroundColor Green
    Add-PnPFieldFromXml -List $ListName -FieldXml $fields[$name] | Out-Null
}

# 3) Default view: show the working columns -----------------------------------
$viewFields = @("Title","ConversationId","Seq","Role","Body","Reply","Status","UserEmail","MetricType","OPE","Created","Modified")
try {
    Set-PnPView -List $ListName -Identity "All Items" -Fields $viewFields -ErrorAction Stop
    Write-Host "Default view updated." -ForegroundColor Green
} catch {
    Write-Host "Could not update the default view (non-fatal): $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`nDone. '$ListName' is provisioned. Remember to add it as a data source in Power Apps and Refresh." -ForegroundColor Cyan
