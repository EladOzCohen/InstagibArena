<#
.SYNOPSIS
  Screenshot of one main-menu screen (inside the exclusive lock): Saved\IAShots\menu_<Name>.png
  powershell -File Tools\menu_shot.ps1 -Page 7 -Tab 2 -Name camp_ladder [-Extra "-IACampStart"]
  Pages: 0 main, 1 custom, 2 multiplayer, 3 character, 4 settings, 5 credits, 6 how to play, 7 campaign (Tab 0 home, 1 new, 2 ladder).
#>
param([int]$Page = 0, [int]$Tab = 0, [string]$Name = "menu", [string]$Extra = "-IACampStart", [int]$Delay = 20)
$proj = Split-Path -Parent $PSScriptRoot
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$shot = "menu_$Name"
$log = Join-Path $env:TEMP "ia_b_logs\$shot.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
$argList = "`"$proj\InstagibArena.uproject`" /Game/Maps/MainMenu -game -windowed -ResX=1600 -ResY=900 -nosound -nosplash -IASkipWelcome -IAMenuPage=$Page -IAMenuTab=$Tab -IAShotDelay=$Delay -IAShotName=$shot $Extra `"-abslog=$log`""
$cmd = "`$p = Start-Process -FilePath '$exe' -ArgumentList '$($argList -replace "'", "''")' -PassThru; if (-not `$p.WaitForExit(240000)) { `$p.Kill() }"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "exclusive.ps1") -Command $cmd *> $null
$src = Join-Path $proj "Saved\IAShots\$shot.png"
if (Test-Path $src) { $src } else { "FAIL (see $log)" }
