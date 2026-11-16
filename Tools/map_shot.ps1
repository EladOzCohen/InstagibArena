<#
.SYNOPSIS
  One screenshot of a map from a chosen camera (inside the exclusive lock): Saved\IAShots\<Name>.png
  powershell -File Tools\map_shot.ps1 -Map Orbital -Cam "-3300,0,380,0,0" -Name orb_a [-Opts "Mode=FFA?Bots=4"] [-Delay 22]
  Cam = x,y,z,pitch,yaw. Several shots: pass -Cams "x,y,z,p,y;x,y,z,p,y" and -Name prefix (files <Name>_1.png ...).
#>
param([string]$Map = "Orbital", [string]$Cam = "", [string]$Cams = "", [string]$Name = "mapshot", [string]$Opts = "Mode=FFA?Bots=2", [int]$Delay = 22, [int]$W = 1600, [int]$H = 900)
$proj = Split-Path -Parent $PSScriptRoot
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$list = @()
if ($Cams) { $list = $Cams -split ";" } elseif ($Cam) { $list = @($Cam) }
$i = 0
foreach ($c in $list) {
    $i++
    $shot = if ($list.Count -gt 1) { "${Name}_$i" } else { $Name }
    $log = Join-Path $env:TEMP "ia_b_logs\$shot.log"
    New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
    $argList = "`"$proj\InstagibArena.uproject`" `"/Game/Maps/DM-${Map}?$Opts`" -game -windowed -ResX=$W -ResY=$H -nosound -nosplash -IASkipWelcome -IAShotDelay=$Delay -IAShotName=$shot -IAShotCam=$c `"-abslog=$log`""
    $cmd = "`$p = Start-Process -FilePath '$exe' -ArgumentList '$($argList -replace "'", "''")' -PassThru; if (-not `$p.WaitForExit(240000)) { `$p.Kill() }"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "exclusive.ps1") -Command $cmd *> $null
    $src = Join-Path $proj "Saved\IAShots\$shot.png"
    if (Test-Path $src) { $src } else { "FAIL $shot (see $log)" }
}
