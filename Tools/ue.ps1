<#
.SYNOPSIS
  Map agent helper: runs the editor commandlet with a python script inside the exclusive lock and prints the GS/MAKEMAP lines.
.EXAMPLE
  powershell -File Tools\ue.ps1 -Script Tools\make_map_temple.py -Log temple.log -Grep "MAKEMAP_DONE|Error"
#>
param(
    [Parameter(Mandatory = $true)][string]$Script,
    [string]$Log = "run.log",
    [string]$Grep = "MAKEMAP_DONE|Error:|Traceback|exception",
    [int]$Tail = 40
)
$proj = Split-Path -Parent $PSScriptRoot
$scriptFull = (Resolve-Path $Script).Path
$logDir = Join-Path $env:TEMP "ia_b_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$logFull = Join-Path $logDir $Log
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$cmd = "& '$exe' '$proj\InstagibArena.uproject' -ExecutePythonScript='$scriptFull' -unattended -nullrhi -nosplash -nopause '-abslog=$logFull'"
$t = Get-Date
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command $cmd | Out-Null
"elapsed {0:N0}s, log {1}" -f ((Get-Date) - $t).TotalSeconds, $logFull
Select-String -Path $logFull -Pattern $Grep | Where-Object { $_.Line -notmatch "LogAutomationTest|UnifiedErrorTest|Error test|Error with|FError" } | Select-Object -Last $Tail | ForEach-Object { $_.Line }
