<#
.SYNOPSIS
  Screenshots of the character gear: five characters in a row in DM-Foundry (the showroom of IADevSubsystem) seen from the front,
  the side or the back, written to Saved\IAShots\<Name>.png. Runs one game under the shared lock.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\gear_shots.ps1 -Name gear_a_front -From 0
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\gear_shots.ps1 -Name gear_a_back -From 0 -View back
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\gear_shots.ps1 -Name gear_close -From 0 -View close -Extra "-IAShowroomWalk"

  -From N shows characters N..N+4. Views: front, back, side (camera from the character's right), q34, close (only the middle one, N+2).
#>
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [int]$From = 0,
    [string]$View = "front",
    [string]$Extra = "",
    [string]$Mode = "FFA",
    [int]$Delay = 16,
    [int]$W = 1600,
    [int]$H = 900,
    [string]$Map = "DM-Foundry",
    [string]$Spot = "1750,0,100"
)
$proj = Split-Path -Parent $PSScriptRoot
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$s = $Spot.Split(",") | ForEach-Object { [double]$_ }
$x = $s[0]; $y = $s[1]; $z = $s[2]
# the characters face -X (yaw 180) and stand in a row along Y, 130 cm apart; the camera is in front of them
$cam = switch ($View) {
    "front" { "{0},{1},{2},0,0" -f ($x - 420), $y, ($z + 20) }
    "back"  { "{0},{1},{2},0,180" -f ($x + 420), $y, ($z + 20) }
    "side"  { "{0},{1},{2},0,90" -f $x, ($y - 460), ($z + 20) }
    "q34"   { "{0},{1},{2},0,25" -f ($x - 380), ($y - 160), ($z + 30) }
    "close" { "{0},{1},{2},0,0" -f ($x - 230), $y, ($z + 15) }
    default { "{0},{1},{2},0,0" -f ($x - 420), $y, ($z + 20) }
}
$logDir = Join-Path $proj "Saved\ShotLogs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "$Name.log"
$cmd = "& '$exe' '$proj\InstagibArena.uproject' '/Game/Maps/${Map}?Mode=${Mode}?Bots=0?ScoreLimit=0?TimeLimit=0' -game -windowed -ResX=$W -ResY=$H -nosound -nosplash -IASkipWelcome " +
       "-IAShotDelay=$Delay -IAShotName=$Name '-IAShowroom=$x,$y,$z,180' -IAShowroomFrom=$From '-IAShotCam=$cam' $Extra '-abslog=$log'"
$t = Get-Date
$png = Join-Path $proj "Saved\IAShots\$Name.png"
if (Test-Path $png) { Remove-Item $png }
$out = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "exclusive.ps1") -Command $cmd 2>&1
"{0:N0} s -> {1} (exists: {2})" -f ((Get-Date) - $t).TotalSeconds, $png, (Test-Path $png)
if (-not (Test-Path $png)) { $out | Select-Object -Last 15 | ForEach-Object { "$_" } }
if (Test-Path $log) { Select-String -Path $log -Pattern "Gear |Warning: .*(Look|Gear)|Fatal|Assertion|Ensure" | Select-Object -First 12 | ForEach-Object { $_.Line } }
