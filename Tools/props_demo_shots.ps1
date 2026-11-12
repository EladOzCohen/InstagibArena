<#
.SYNOPSIS
  Takes one screenshot per row of the /Game/Maps/_PropDemo level (built by props_demo.py) with the game executable.

    props_demo_shots.ps1                 all rows
    props_demo_shots.ps1 -Only Rocks_0   only rows whose name matches
    props_demo_shots.ps1 -Delete         delete the demo level and its helper materials (Content/Maps/_PropDemo.umap ...)

  PNGs land in Saved\IAShots\propdemo_<row>.png. Each shot is a separate game start under the shared lock.
#>
param([string[]]$Only = @(), [int]$Delay = 14, [int]$Width = 1600, [int]$Height = 900, [switch]$Delete, [string]$Tag = "propdemo")
$proj = Split-Path -Parent $PSScriptRoot
if ($Delete) {
    Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $proj "Content\Maps\_PropDemo.umap")
    Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $proj "Content\Materials\MI_Demo*.uasset")
    Write-Host "demo level deleted"
    return
}
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$cams = Get-Content (Join-Path $proj "Saved\propdemo_cams.json") -Raw | ConvertFrom-Json
foreach ($c in $cams) {
    if ($Only.Count -gt 0 -and -not ($Only | Where-Object { $c.name -like "*$_*" })) { continue }
    $cam = ($c.cam | ForEach-Object { [string]::Format([cultureinfo]::InvariantCulture, "{0:0.##}", $_) }) -join ","
    $name = "${Tag}_" + $c.name
    $gameArgs = "`"$proj\InstagibArena.uproject`" /Game/Maps/_PropDemo -game -windowed -ResX=$Width -ResY=$Height -nosound -nosplash -IASkipWelcome -IAShotDelay=$Delay -IAShotName=$name -IAShotCam=$cam `"-abslog=$proj\Saved\shot_$name.log`""
    $cmd = "`$p = Start-Process -FilePath '$exe' -ArgumentList '$($gameArgs.Replace("'", "''"))' -PassThru; if (-not `$p.WaitForExit(900000)) { `$p.Kill() }"
    Write-Host "shot $name ($cam)"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "exclusive.ps1") -Command $cmd *> $null
}
