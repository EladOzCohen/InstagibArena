<#
  DM-Quarry bot test: headless match (inside the exclusive lock) and a summary of frags, NavGrid lines and problems.
  powershell -File Tools\bottest_quarry.ps1 -Mode FFA -Bots 10 -Seconds 100
#>
param([string]$Mode = "FFA", [int]$Bots = 10, [int]$Seconds = 100, [string]$Map = "DM-Quarry")
$proj = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $env:TEMP "ia_b_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "quarry_$Mode.log"
Remove-Item $log -ErrorAction SilentlyContinue
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$script = Join-Path $logDir "quarry_$Mode.ps1"
$line = "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"/Game/Maps/${Map}?Mode=${Mode}?Bots=${Bots}?BotSkill=3?ScoreLimit=0?TimeLimit=0`" -game -nullrhi -nosound -unattended -nosplash -abslog=`"$log`"' -PassThru; Start-Sleep -Seconds ($Seconds + 50); if (-not `$p.HasExited) { `$p.Kill() }"
Set-Content -Path $script -Value $line -Encoding UTF8
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
$t = Get-Content $log
"frags: " + ($t | Select-String "was fragged by").Count
$t | Select-String "NavGrid:" | Select-Object -First 14 | ForEach-Object { $_.Line -replace '^\[[^\]]*\]\[[^\]]*\]', '' }
"problems:"
$t | Select-String "LogNet.*(Warning|Error)|Fatal|Assertion|Ensure|ensure|Failed to load" | Where-Object { $_.Line -notmatch "Wintab|DLL|dll" } | Select-Object -First 15 | ForEach-Object { $_.Line }
