param([string]$Map = "Quarry", [string]$Mode = "CTF", [int]$Delay = 60, [int]$Wait = 150)
$proj = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $proj "Builds\Windows\InstagibArena\Binaries\Win64\InstagibArena-Win64-Shipping.exe"
$log = Join-Path $proj "Saved\pkg_smoke_${Map}.log"
Remove-Item $log -ErrorAction SilentlyContinue
$args1 = "`"/Game/Maps/DM-${Map}?Mode=${Mode}?Bots=6?BotSkill=3?ScoreLimit=0?TimeLimit=0`" -windowed -ResX=1600 -ResY=900 -nosound -nosplash -IASkipWelcome -IAReport -IAShotDelay=$Delay -IAShotName=pkg_$Map `"-abslog=$log`""
$p = Start-Process -FilePath $exe -ArgumentList $args1 -PassThru
if (-not $p.WaitForExit($Wait * 1000)) { $p.Kill() }
Get-ChildItem -Recurse (Join-Path $proj "Builds\Windows") -Filter "pkg_$Map*.png" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
if (Test-Path $log) { Select-String -Path $log -Pattern "CTF: setup|CAPTURED|FRAMES|Error:|Fatal" | Select-Object -First 8 | ForEach-Object { $_.Line.Substring(0, [Math]::Min(180, $_.Line.Length)) } } else { "no log" }
