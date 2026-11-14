<#
.SYNOPSIS
  A screenshot of a running bot match (the player's view, or the automatic overview with -Auto) to judge how the characters read in a map.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\gear_game_shot.ps1 -Name gear_game_tdm -Map DM-Foundry -Mode TDM -Bots 10 -Extra "-IAFire"
#>
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$Map = "DM-Foundry",
    [string]$Mode = "TDM",
    [int]$Bots = 10,
    [int]$Delay = 24,
    [string]$Extra = "",
    [switch]$Auto
)
$proj = Split-Path -Parent $PSScriptRoot
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$logDir = Join-Path $proj "Saved\ShotLogs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "$Name.log"
$autoArg = if ($Auto) { "-IAShotAuto" } else { "" }
$cmd = "& '$exe' '$proj\InstagibArena.uproject' '/Game/Maps/${Map}?Mode=${Mode}?Bots=${Bots}?BotSkill=1?ScoreLimit=0?TimeLimit=0' -game -windowed -ResX=1600 -ResY=900 -nosound -nosplash -IASkipWelcome " +
       "-IAShotDelay=$Delay -IAShotName=$Name $autoArg $Extra '-abslog=$log'"
$png = Join-Path $proj "Saved\IAShots\$Name.png"
if (Test-Path $png) { Remove-Item $png }
$t = Get-Date
$out = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "exclusive.ps1") -Command $cmd 2>&1
"{0:N0} s -> {1} (exists: {2})" -f ((Get-Date) - $t).TotalSeconds, $png, (Test-Path $png)
if (-not (Test-Path $png)) { $out | Select-Object -Last 10 | ForEach-Object { "$_" } }
if (Test-Path $log) { Select-String -Path $log -Pattern "Gear |Warning: .*(Look|Gear)|Fatal|Assertion|Ensure" | Select-Object -First 12 | ForEach-Object { $_.Line } }
