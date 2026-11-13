<#
.SYNOPSIS
  Gameplay and performance check of the maps: 8 bots fight for about 80 seconds per map (headless), then a windowed
  frame-time measurement at 1280x720. Prints one result line per map.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\polish_check.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\polish_check.ps1 -Maps Neon,Forge -SkipFrames

  RESULT lines:
    frags      kills among 8 bots in 80 s at skill 3. Reference (older, skill-1 numbers): Foundry 76, Temple 118, Dock 69,
               Skyline 114, Neon 135, Forge 80, Glacier 57, Canyon 83. It must not drop below about 50 percent of that
               and must not be 0.
    nav        NavGrid line of the log (node count). A drop of more than 30 percent compared to before means the new
               props/colliders cut the walkable space: look at that.
    bad        any LogNet warning/error, Fatal, Assertion, Ensure, missing material or shader error. Must be empty.
    frame_ms   average frame time in the windowed run (lower is better; about 25-37 ms on the Intel Iris Xe test laptop
               at 1280x720 before the performance work).
#>
param(
    [string[]]$Maps = @("Foundry", "Temple", "Dock", "Skyline", "Neon", "Forge", "Glacier", "Canyon"),
    [int]$BotSeconds = 80,
    [switch]$SkipFrames
)

$Maps = $Maps | ForEach-Object { $_ -split "," }
$proj = Split-Path -Parent $PSScriptRoot
$exeCmd = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$exeWin = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$out = Join-Path $proj "Saved\polish_check"
New-Item -ItemType Directory -Force $out | Out-Null
$lock = Join-Path $PSScriptRoot "exclusive.ps1"

foreach ($m in $Maps) {
    $log = Join-Path $out "$m.bots.log"
    if (Test-Path $log) { Remove-Item $log -Force }
    $a = "`"$proj\InstagibArena.uproject`" `"/Game/Maps/DM-${m}?Mode=FFA?Bots=8?BotSkill=3?ScoreLimit=0?TimeLimit=0`" -game -nullrhi -nosound -unattended -nosplash `"-abslog=$log`""
    $cmd = "`$p = Start-Process -FilePath '$exeCmd' -ArgumentList '$($a -replace "'", "''")' -PassThru; Start-Sleep -Seconds $($BotSeconds + 25); if (-not `$p.HasExited) { Stop-Process -Id `$p.Id -Force }"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $lock -Command $cmd *> $null
    $frags = (Select-String -Path $log -Pattern 'was fragged by' -ErrorAction SilentlyContinue).Count
    $nav = (Select-String -Path $log -Pattern 'NavGrid' -ErrorAction SilentlyContinue | Select-Object -First 2 | ForEach-Object { ($_.Line -replace '^\[.*?\]\[.*?\]', '').Trim() }) -join ' | '
    $bad = (Select-String -Path $log -Pattern 'LogNet: (Warning|Error)|Fatal error|Assertion failed|Ensure condition failed|Failed to load /Game|Missing material|shader.*error' -ErrorAction SilentlyContinue | Select-Object -First 3 | ForEach-Object { $_.Line.Substring(0, [Math]::Min(160, $_.Line.Length)) }) -join ' || '

    $frame = "-"
    if (-not $SkipFrames) {
        $flog = Join-Path $out "$m.frames.log"
        if (Test-Path $flog) { Remove-Item $flog -Force }
        $fa = "`"$proj\InstagibArena.uproject`" `"/Game/Maps/DM-${m}?Mode=FFA?Bots=6`" -game -windowed -ResX=1280 -ResY=720 -nosound -nosplash -IASkipWelcome -IAReport -IAWalk `"-abslog=$flog`""
        $fcmd = "`$p = Start-Process -FilePath '$exeWin' -ArgumentList '$($fa -replace "'", "''")' -PassThru; Start-Sleep -Seconds 75; if (-not `$p.HasExited) { Stop-Process -Id `$p.Id -Force }"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $lock -Command $fcmd *> $null
        $vals = Select-String -Path $flog -Pattern 'FRAMES .* avg=([0-9.]+) ms' -ErrorAction SilentlyContinue | Select-Object -Last 3 | ForEach-Object { [double]$_.Matches[0].Groups[1].Value }
        if ($vals) { $frame = [math]::Round(($vals | Measure-Object -Average).Average, 1) }
    }
    Write-Host "RESULT $m frags=$frags frame_ms=$frame bad=[$bad] nav=[$nav]"
}
