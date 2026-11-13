<#
.SYNOPSIS
  Map agent helper: 70 s headless match with 8 bots on one map (inside the exclusive lock), then counts frags and problems.
.EXAMPLE
  powershell -File Tools\bottest_b.ps1 -Map DM-Canyon
#>
param([Parameter(Mandatory = $true)][string]$Map, [int]$Seconds = 70)
$proj = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $env:TEMP "ia_b_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "bots_$Map.log"
Remove-Item $log -ErrorAction SilentlyContinue
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$script = Join-Path $logDir "bots_$Map.ps1"
$line = "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"/Game/Maps/${Map}?Mode=FFA?Bots=8?BotSkill=3?ScoreLimit=0?TimeLimit=0`" -game -nullrhi -nosound -unattended -nosplash -abslog=`"$log`"' -PassThru; Start-Sleep -Seconds ($Seconds + 40); if (-not `$p.HasExited) { `$p.Kill() }"
Set-Content -Path $script -Value $line -Encoding UTF8
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
$t = Get-Content $log
"frags: " + ($t | Select-String "was fragged by").Count
$t | Select-String "NavGrid:" | Select-Object -First 2 | ForEach-Object { $_.Line }
"problems:"
$t | Select-String "LogNet.*(Warning|Error)|Fatal|Assertion|Ensure|ensure|Missing|shader.*(error|fail)|Failed to load" | Where-Object { $_.Line -notmatch "Wintab|DLL|dll" } | Select-Object -First 15 | ForEach-Object { $_.Line }
