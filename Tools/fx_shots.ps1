<#
.SYNOPSIS
  FX helper: optional C++ build + material rebuild + screenshots of /Game/Maps/_FXDemo (Tools/fx_demo.py) inside ONE exclusive lock.
  powershell -File Tools\fx_shots.ps1 -Prefix fx2 [-Build] [-Materials] [-Views "name=x,y,z,pitch,yaw[|extra args];..."]
#>
param(
    [string]$Prefix = "fx",
    [switch]$Build,
    [switch]$Materials,
    [string[]]$MakeMaps = @(),
    [string]$Map = "_FXDemo",
    [string]$Views = "pad=-380,-250,150,-18,35;padtop=0,0,600,-90,0;flames=-1150,650,150,-5,0;barrel=-1450,-650,140,-10,0;impact=-2300,-1800,100,0,0|-IAImpact=-1800,-1800,80;beam=-2000,-2750,140,0,110|-IAFire",
    [int]$Delay = 12
)
$proj = Split-Path -Parent $PSScriptRoot
$ue = "C:\Program Files\Epic Games\UE_5.8\Engine"
$lines = @()
if ($Build) {
    $lines += "& '$ue\Build\BatchFiles\Build.bat' InstagibArenaEditor Win64 Development '-Project=$proj\InstagibArena.uproject' -WaitMutex -NoHotReload *> '$proj\Saved\build.log'"
}
if ($Materials) {
    $lines += "`$env:IA_FX_FORCE='1'; & '$ue\Binaries\Win64\UnrealEditor-Cmd.exe' '$proj\InstagibArena.uproject' -ExecutePythonScript='$proj\Tools\build_fx.py' -unattended -nullrhi -nosplash -nopause -abslog='$proj\Saved\fx.log'; `$env:IA_FX_FORCE=''"
}
foreach ($mm in $MakeMaps) {
    $lines += "& '$ue\Binaries\Win64\UnrealEditor-Cmd.exe' '$proj\InstagibArena.uproject' -ExecutePythonScript='$proj\Tools\make_map_$mm.py' -unattended -nullrhi -nosplash -nopause -abslog='$proj\Saved\mm_$mm.log'"
}
$exe = "$ue\Binaries\Win64\UnrealEditor.exe"
$mapPath = "/Game/Maps/$Map"
foreach ($v in $Views.Split(";")) {
    if ($v.Trim() -eq "") { continue }
    $name, $rest = $v.Split("=", 2)
    $cam, $extra = $rest.Split("|", 2)
    # name may carry a map and a bot count: shotname@DM-Temple@0
    $parts = $name.Split("@")
    $name = $parts[0]
    $thisMap = if ($parts.Count -gt 1 -and $parts[1]) { "/Game/Maps/" + $parts[1] } else { $mapPath }
    $bots = if ($parts.Count -gt 2) { $parts[2] } else { "4" }
    $shot = "${Prefix}_$name"
    $lines += "`$p = Start-Process -FilePath '$exe' -ArgumentList '`"$proj\InstagibArena.uproject`" `"${thisMap}?Mode=FFA?Bots=$bots`" -game -windowed -ResX=1600 -ResY=900 -nosound -nosplash -IASkipWelcome -IAShotDelay=$Delay -IAShotName=$shot -IAShotCam=$cam $extra -log -abslog=`"$proj\Saved\shot_$shot.log`"' -PassThru; if (-not `$p.WaitForExit(240000)) { `$p.Kill() }"
}
$script = Join-Path $proj "Saved\fx_run_$Prefix.ps1"
Set-Content -Path $script -Value ($lines -join "`r`n") -Encoding UTF8
$t = Get-Date
powershell -NoProfile -ExecutionPolicy Bypass -File "$proj\Tools\exclusive.ps1" -Command "& '$script'" | Out-Null
"done in {0:N0}s" -f ((Get-Date) - $t).TotalSeconds
if ($Build) { Select-String -Path "$proj\Saved\build.log" -Pattern "error|Result:" | Select-Object -First 10 | ForEach-Object { $_.Line } }
Get-ChildItem "$proj\Saved\IAShots" -Filter "${Prefix}_*.png" | ForEach-Object { $_.FullName }
