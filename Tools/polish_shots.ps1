<#
.SYNOPSIS
  Takes the standard set of review screenshots of the maps (4 views each) into Saved\IAShots\polish\.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\polish_shots.ps1 -Tag before
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\polish_shots.ps1 -Tag after -Maps Neon,Skyline

  Views per map (file Saved\IAShots\polish\<Tag>_<Map>_<view>.png):
    spawn   what a player sees when the match starts (first person)
    auto    an automatic high camera over the start area (-IAShotAuto)
    skyA    the horizon and sky, looking along +X from the middle of the map, a little above the floor
    skyB    the horizon and sky, looking along +Y

  It takes a few minutes per map and runs one game at a time under the shared lock (Tools\exclusive.ps1).
  Then LOOK at the PNG files (an image viewer, or the image-reading tool of your agent) and judge them.
#>
param(
    [string]$Tag = "shot",
    [string[]]$Maps = @("Foundry", "Temple", "Dock", "Skyline", "Neon", "Forge", "Glacier", "Canyon"),
    [int]$W = 1600,
    [int]$H = 900,
    [int]$Delay = 22,
    [string[]]$ViewNames = @("spawn", "auto", "skyA", "skyB")
)

$Maps = $Maps | ForEach-Object { $_ -split "," }
$ViewNames = $ViewNames | ForEach-Object { $_ -split "," }
$proj = Split-Path -Parent $PSScriptRoot
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$out = Join-Path $proj "Saved\IAShots\polish"
$logDir = Join-Path $proj "Saved\ShotLogs"
New-Item -ItemType Directory -Force $out, $logDir | Out-Null

# Camera heights that are above the floor and inside the open space of each map (x,y,z,pitch,yaw is added per view).
$camZ = @{ Foundry = 700; Temple = 900; Dock = 500; Skyline = 1400; Neon = 600; Forge = 700; Glacier = 600; Canyon = 700 }

$views = @(
    @{ Name = "spawn"; Extra = "" },
    @{ Name = "auto";  Extra = "-IAShotAuto" },
    @{ Name = "skyA";  Extra = "CAM:0" },
    @{ Name = "skyB";  Extra = "CAM:90" }
)

$views = $views | Where-Object { $ViewNames -contains $_.Name }
foreach ($m in $Maps) {
    foreach ($v in $views) {
        $shotName = "polish_${Tag}_${m}_$($v.Name)"
        $extra = $v.Extra
        if ($extra -like "CAM:*") {
            $yaw = $extra.Substring(4)
            $extra = "-IAShotCam=0,0,$($camZ[$m]),12,$yaw"
        }
        $log = Join-Path $logDir "$shotName.log"
        $argList = "`"$proj\InstagibArena.uproject`" `"/Game/Maps/DM-${m}?Mode=FFA?Bots=4`" -game -windowed -ResX=$W -ResY=$H -nosound -nosplash -IASkipWelcome -IAShotDelay=$Delay -IAShotName=$shotName $extra `"-abslog=$log`""
        $cmd = "`$p = Start-Process -FilePath '$exe' -ArgumentList '$($argList -replace "'", "''")' -PassThru; if (-not `$p.WaitForExit(420000)) { `$p.Kill() }"
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "exclusive.ps1") -Command $cmd *> $null
        $src = Join-Path $proj "Saved\IAShots\$shotName.png"
        if (Test-Path $src) {
            Move-Item $src (Join-Path $out "${Tag}_${m}_$($v.Name).png") -Force
            Write-Host "ok   ${Tag}_${m}_$($v.Name).png"
        } else {
            Write-Host "FAIL ${Tag}_${m}_$($v.Name) (see $log)"
        }
    }
}
Write-Host "Pictures are in $out"
