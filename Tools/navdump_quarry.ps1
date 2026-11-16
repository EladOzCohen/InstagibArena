<#
  Dumps every NavGrid node of DM-Quarry (headless, short) into %TEMP%\ia_b_logs\navdump.log, then Tools\_qt_navmap.py draws it.
#>
param([int]$Seconds = 25)
$proj = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $env:TEMP "ia_b_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "navdump.log"
Remove-Item $log -ErrorAction SilentlyContinue
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$script = Join-Path $logDir "navdump.ps1"
$line = "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"/Game/Maps/DM-Quarry?Mode=FFA?Bots=0`" -game -nullrhi -nosound -unattended -nosplash -IANavDump=0,0,0,30000 -abslog=`"$log`"' -PassThru; Start-Sleep -Seconds $Seconds; if (-not `$p.HasExited) { `$p.Kill() }"
Set-Content -Path $script -Value $line -Encoding UTF8
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
(Select-String -Path $log -Pattern "NAVDUMP").Count
