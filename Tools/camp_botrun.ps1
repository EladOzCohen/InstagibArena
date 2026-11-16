<#
.SYNOPSIS
  Headless campaign match with bots only (inside the exclusive lock): prints the squad, the result line and problems.
  powershell -File Tools\camp_botrun.ps1 -Match 4 [-Seconds 150]
  Match = 1..20 (the ladder). Starts a fresh test campaign in the ini of this project (-IACampStart).
#>
param([int]$Match = 1, [int]$Seconds = 150, [string]$Mode = "", [string]$MapName = "", [string]$Opts = "")
$proj = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $env:TEMP "ia_b_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "camp_$Match.log"
Remove-Item $log -ErrorAction SilentlyContinue
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$script = Join-Path $logDir "camp_$Match.ps1"
$url = "/Game/Maps/DM-${MapName}?${Opts}"
$line = "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"$url`" -game -nullrhi -nosound -unattended -nosplash -IACampStart -IAReport -abslog=`"$log`"' -PassThru; Start-Sleep -Seconds ($Seconds + 60); if (-not `$p.HasExited) { `$p.Kill() }"
Set-Content -Path $script -Value $line -Encoding UTF8
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
$t = Get-Content $log
"match=$Match url=$url frags: " + ($t | Select-String "was fragged by").Count
$t | Select-String "Match setup|Campaign:|Player joined|Bot .*joined|CTF: setup|CAPTURED" | Select-Object -First 14 | ForEach-Object { $_.Line.Substring(0, [Math]::Min(190, $_.Line.Length)) }
"problems:"
$t | Select-String "Fatal|Assertion|Ensure|ensure|Failed to load /Game|LogNet.*(Warning|Error)" | Where-Object { $_.Line -notmatch "Wintab|DLL|dll" } | Select-Object -First 10 | ForEach-Object { $_.Line }
