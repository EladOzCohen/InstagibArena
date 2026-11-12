<#
.SYNOPSIS
  Runs a Python script in the editor commandlet (headless) under the shared lock and prints the lines that matter.

  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\run_ue.ps1 -Script Tools\import_props.py [-Log Saved\x.log] [-Grep "PROPS|Error"] [-Env "IA_PROPS_ONLY=barrel_red"]
#>
param(
    [Parameter(Mandatory = $true)][string]$Script,
    [string]$Log = "Saved\run_ue.log",
    [string]$Grep = "PROPS |MAKEMAP|DEMO_|LogPython: Error|Fatal|Critical",
    [string]$Env = ""
)
$proj = Split-Path -Parent $PSScriptRoot
$scriptFull = (Resolve-Path (Join-Path $proj $Script)).Path
$logFull = Join-Path $proj $Log
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$envSet = ""
if ($Env) { foreach ($kv in $Env.Split(";")) { $k, $v = $kv.Split("=", 2); $envSet += "`$env:$k='$v'; " } }
$cmd = $envSet + "& '$exe' '$proj\InstagibArena.uproject' -ExecutePythonScript='$scriptFull' -unattended -nullrhi -nosplash -nopause -abslog='$logFull'"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "exclusive.ps1") -Command $cmd *> $null
Select-String -CaseSensitive -Path $logFull -Pattern $Grep | ForEach-Object { $_.Line -replace '^\[[^\]]*\]\[[^\]]*\]', '' }
