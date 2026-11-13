<#
.SYNOPSIS
  Performance measurement helper: runs one map from a fixed camera and prints the frame timings of the game.

.DESCRIPTION
  Wrap it in the shared lock, because timings are only meaningful when nothing else runs on the PC:
    powershell -NoProfile -ExecutionPolicy Bypass -File Tools\exclusive.ps1 -Command "& Tools\perf_run.ps1 -Map DM-Forge -Label forge_epic -Level 3"
  The game logs "FRAMES ... avg= gpu= game= render=" every 4 s (-IAReport). The first -Skip seconds are ignored (shaders, streaming).
  -Level 0..3 sets all sg.* scalability groups (Low, Medium, High, Epic) through -ExecCmds; -Cvars adds more console variables
  ("r.Shadow.Virtual.Enable 0,r.SSR.Quality 0"), -Console is a timeline for the game itself ("40:stat unit;60:r.Foo 1").
  Output: a timeline of FRAMES / CONSOLE lines and a RESULT line (also appended to Saved\perf\results.csv).
#>
param(
    [Parameter(Mandatory = $true)][string]$Map,
    [string]$Label = "run",
    [int]$Start = 0,
    [int]$Level = -1,
    [string]$Cvars = "",
    [string]$Console = "",
    [int]$Seconds = 70,
    [int]$Skip = 30,
    [int]$ResQ = -1,
    [string]$ResTable = "50,71,87,100",
    [int]$ResX = 1280,
    [int]$ResY = 720,
    [string]$Extra = "",
    [string]$ShotName = "",
    [switch]$Quiet
)
$proj = Split-Path -Parent $PSScriptRoot
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$dir = Join-Path $proj "Saved\perf"
New-Item -ItemType Directory -Force $dir | Out-Null
$log = Join-Path $dir "$Label.log"
if (Test-Path $log) { Remove-Item $log -Force }
if (-not $Map.StartsWith("/")) { $Map = "/Game/Maps/$Map" }

$cmds = @("r.VSync 0", "t.MaxFPS 0")
if ($Level -ge 0) {
    # The game starts with the quality saved in GameUserSettings.ini (the sg.* keys): write the level there, so that it is in force
    # from the first frame (setting it with -ExecCmds only works when it differs from what the previous run saved).
    # The Quality buttons of the video settings set the resolution scale too: that is the project's table (Config/DefaultScalability.ini).
    $table = $ResTable.Split(",")
    $resQuality = $(if ($ResQ -gt 0) { $ResQ } else { $table[$Level] })
    $gus = Join-Path $proj "Saved\Config\WindowsEditor\GameUserSettings.ini"
    if (Test-Path $gus) {
        $out = foreach ($line in (Get-Content $gus)) {
            if ($line -match '^sg\.ResolutionQuality=') { "sg.ResolutionQuality=$resQuality" }
            elseif ($line -match '^sg\.\w+Quality=') { ($line -replace '=.*$', "=$Level") }
            else { $line }
        }
        Set-Content -Path $gus -Value $out
    }
}
if ($Cvars) { $cmds += $Cvars.Split(",") }
$exec = ($cmds -join ",")
$shot = if ($ShotName) { $ShotName } else { $Label }
$argList = "`"$proj\InstagibArena.uproject`" `"${Map}?Mode=FFA?Bots=6`" -game -windowed -ResX=$ResX -ResY=$ResY -nosound -nosplash -IASkipWelcome -IANoAutoQuality " +
    "-IAReport -IAShotDelay=$Seconds -IAShotName=$shot -IAShotStart=$Start -ExecCmds=`"$exec`" -abslog=`"$log`" $Extra"
if ($Console) { $argList += " -IAConsole=`"$Console`"" }
$p = Start-Process -FilePath $exe -ArgumentList $argList -PassThru
if (-not $p.WaitForExit(($Seconds + 150) * 1000)) { $p.Kill(); Write-Host "[perf] killed after timeout" }
Start-Sleep -Seconds 2

function Get-Stamp($line) {
    if ($line -match '^\[(\d{4})\.(\d\d)\.(\d\d)-(\d\d)\.(\d\d)\.(\d\d):(\d{3})\]') {
        return ([datetime]::new([int]$Matches[1], [int]$Matches[2], [int]$Matches[3], [int]$Matches[4], [int]$Matches[5], [int]$Matches[6], [int]$Matches[7])).Ticks / 1e7
    }
    return $null
}
$lines = Select-String -Path $log -Pattern "LogInstagib: (FRAMES|CONSOLE)" | ForEach-Object { $_.Line }
$t0 = $null
$sum = @{ avg = 0.0; gpu = 0.0; game = 0.0; render = 0.0; n = 0 }
foreach ($l in $lines) {
    $t = Get-Stamp $l
    if ($null -eq $t) { continue }
    if ($null -eq $t0) { $t0 = $t }
    $rel = [math]::Round($t - $t0, 0)
    if ($l -match "FRAMES .* avg=([\d\.]+) ms max=([\d\.]+) ms .* gpu=([\d\.]+) game=([\d\.]+) render=([\d\.]+)") {
        $a = [double]$Matches[1]; $mx = [double]$Matches[2]; $g = [double]$Matches[3]; $gm = [double]$Matches[4]; $r = [double]$Matches[5]
        if (-not $Quiet) { Write-Host ("  t+{0,3}  frame {1,5:N1} ms (max {2,6:N1})  gpu {3,5:N1}  game {4,5:N1}  render {5,5:N1}" -f $rel, $a, $mx, $g, $gm, $r) }
        if ($rel -ge $Skip) { $sum.avg += $a; $sum.gpu += $g; $sum.game += $gm; $sum.render += $r; $sum.n++ }
    } elseif ($l -match "CONSOLE ([\d\.]+): (.*)$") {
        if (-not $Quiet) { Write-Host ("  t+{0,3}  >>> {1}" -f $rel, $Matches[2]) }
    }
}
if ($sum.n -gt 0) {
    $res = "RESULT {0} map={1} level={2} frame={3:N1} ms ({4:N1} fps) gpu={5:N1} game={6:N1} render={7:N1} windows={8}" -f $Label, ($Map.Split("/")[-1]), $Level,
        ($sum.avg / $sum.n), (1000.0 / ($sum.avg / $sum.n)), ($sum.gpu / $sum.n), ($sum.game / $sum.n), ($sum.render / $sum.n), $sum.n
    Write-Host $res
    $n = $sum.n
    Add-Content -Path (Join-Path $dir "results.csv") -Value ("{0},{1},{2},{3:N2},{4:N2},{5:N2},{6:N2},{7}" -f $Label, ($Map.Split("/")[-1]), $Level, ($sum.avg / $n), ($sum.gpu / $n), ($sum.game / $n), ($sum.render / $n), $Cvars)
} else {
    Write-Host "RESULT $Label no FRAMES windows after $Skip s (see $log)"
}
