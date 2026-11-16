<#
.SYNOPSIS
  DM-Citadel: frame time at 1280x720 (windowed, 4 bots, the local player walks), inside the exclusive lock. Prints the FRAMES lines.
  powershell -File Tools\perf_citadel.ps1 [-Seconds 75]
#>
param([int]$Seconds = 75, [string]$Map = "DM-Citadel")
$proj = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $env:TEMP "ia_b_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "perf_$Map.log"
Remove-Item $log -ErrorAction SilentlyContinue
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$script = Join-Path $logDir "perf_$Map.ps1"
$line = "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"/Game/Maps/${Map}?Mode=FFA?Bots=6`" -game -windowed -ResX=1280 -ResY=720 -nosound -nosplash -IASkipWelcome -IAReport -IAWalk -abslog=`"$log`"' -PassThru; Start-Sleep -Seconds $Seconds; if (-not `$p.HasExited) { `$p.Kill() }"
Set-Content -Path $script -Value $line -Encoding UTF8
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
Get-Content $log | Select-String "FRAMES" | Select-Object -Last 12 | ForEach-Object { $_.Line }
