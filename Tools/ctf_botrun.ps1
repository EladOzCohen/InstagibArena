<#
.SYNOPSIS
  Headless Capture the Flag bot match on one map (inside the exclusive lock). Prints captures, fallback bases, nav stats and problems.
  powershell -File Tools\ctf_botrun.ps1 -Map Citadel [-Seconds 180] [-Bots 8] [-Skill 3] [-Mode CTF]
#>
param([string]$Map = "Foundry", [int]$Seconds = 180, [int]$Bots = 8, [int]$Skill = 3, [string]$Mode = "CTF")
$proj = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $env:TEMP "ia_b_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "ctf_${Map}_$Mode.log"
Remove-Item $log -ErrorAction SilentlyContinue
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$script = Join-Path $logDir "ctf_${Map}_$Mode.ps1"
$line = "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"/Game/Maps/DM-${Map}?Mode=${Mode}?Bots=${Bots}?BotSkill=${Skill}?ScoreLimit=0?TimeLimit=0`" -game -nullrhi -nosound -unattended -nosplash -IAReport -abslog=`"$log`"' -PassThru; Start-Sleep -Seconds ($Seconds + 60); if (-not `$p.HasExited) { `$p.Kill() }"
Set-Content -Path $script -Value $line -Encoding UTF8
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
$t = Get-Content $log
"map=$Map mode=$Mode frags: " + ($t | Select-String "was fragged by").Count
"captures lines: " + ($t | Select-String "CAPTURED").Count
$t | Select-String "CTF:|CTFREPORT|NAVSTATS|NavGrid:|BOT CARRY TIMEOUT" | Select-Object -First 25 | ForEach-Object { $_.Line }
"problems:"
$t | Select-String "LogNet.*(Warning|Error)|Fatal|Assertion|Ensure|ensure|Missing|shader.*(error|fail)|Failed to load /Game" | Where-Object { $_.Line -notmatch "Wintab|DLL|dll" } | Select-Object -First 15 | ForEach-Object { $_.Line }
