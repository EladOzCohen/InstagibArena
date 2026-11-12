<#
.SYNOPSIS
  Map agent helper: takes several screenshots of one map (one game launch per view, all inside one exclusive lock).
.EXAMPLE
  powershell -File Tools\shots_b.ps1 -Map DM-Temple -Prefix t1 -Views "spawn=1900,600,170,-5,200;centre=0,-1500,900,-10,90"
  PNGs land in Saved\IAShots\<Prefix>_<viewname>.png
#>
param(
    [Parameter(Mandatory = $true)][string]$Map,
    [Parameter(Mandatory = $true)][string]$Prefix,
    [Parameter(Mandatory = $true)][string]$Views,
    [int]$Delay = 14,
    [int]$ResX = 1600,
    [int]$ResY = 900
)
$proj = Split-Path -Parent $PSScriptRoot
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
if (-not $Map.StartsWith("/")) { $Map = "/Game/Maps/$Map" }
$lines = @()
foreach ($v in $Views.Split(";")) {
    if ($v.Trim() -eq "") { continue }
    $name, $cam = $v.Split("=", 2)
    $shot = "${Prefix}_$name"
    $lines += "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"${Map}?Mode=FFA?Bots=4`" -game -windowed -ResX=$ResX -ResY=$ResY -nosound -nosplash -IASkipWelcome -IAShotDelay=$Delay -IAShotName=$shot -IAShotCam=$cam -log -abslog=`"$env:TEMP\ia_b_logs\shot_$shot.log`"' -PassThru; if (-not `$p.WaitForExit(240000)) { `$p.Kill() }"
}
New-Item -ItemType Directory -Force "$env:TEMP\ia_b_logs" | Out-Null
$script = Join-Path $env:TEMP "ia_b_logs\shots_$Prefix.ps1"
Set-Content -Path $script -Value ($lines -join "`r`n") -Encoding UTF8
$t = Get-Date
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
"done in {0:N0}s" -f ((Get-Date) - $t).TotalSeconds
Get-ChildItem "$proj\Saved\IAShots" -Filter "${Prefix}_*.png" | ForEach-Object { $_.FullName }
