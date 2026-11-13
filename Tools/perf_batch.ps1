<#
.SYNOPSIS
  Frame time of several maps at several quality levels (fixed camera = player start 0, 1280x720), one summary line each.

  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\exclusive.ps1 -Command "& .\Tools\perf_batch.ps1 -Tag before"
  Output lines "RESULT <tag>_<map>_L<level> ..." and Saved\perf\results.csv. Compare two tags by hand.
#>
param(
    [string]$Tag = "run",
    [string[]]$Maps = @("DM-Forge", "DM-Neon", "DM-Foundry", "DM-Canyon"),
    [int[]]$Levels = @(3, 2, 1, 0),
    [int]$Seconds = 62,
    [string]$ResTable = "50,71,87,100",
    [string]$Cvars = "",
    [int]$Start = 0
)
foreach ($m in $Maps) {
    foreach ($l in $Levels) {
        $label = "{0}_{1}_L{2}" -f $Tag, $m.Replace("DM-", ""), $l
        & (Join-Path $PSScriptRoot "perf_run.ps1") -Map $m -Label $label -Level $l -Start $Start -Seconds $Seconds -Skip 28 -ResTable $ResTable -Cvars $Cvars -Quiet
    }
}
