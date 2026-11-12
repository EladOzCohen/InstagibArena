<#
.SYNOPSIS
  Makes a preview picture for every map listed in Source\InstagibArena\IAMapList.h and imports them into the project.

.DESCRIPTION
  For each map in the list it
    1. runs the game once on that map with -IAShotAuto (an overview camera, no HUD) and takes a screenshot,
    2. copies the picture to Tools\MapThumbs\<MapName>.png,
    3. writes the recommended player counts into Source\InstagibArena\IAMapRecommended.inl (from the number of
       player starts the run found; rebuild the game afterwards to use them),
  then imports all pictures as textures /Game/UI/MapThumbs/T_<MapName> with Tools\import_thumbnails.py.

  Safe to run again at any time, for example after a new map was added to IAMapList.h. Every game and editor run
  waits for its turn through Tools\exclusive.ps1, so it can run while other people build or test.

.PARAMETER Only
  Only these maps (short names such as DM-Foundry), for example -Only DM-Foundry,DM-Dock.
.PARAMETER SkipImport
  Make the pictures but do not import them.
.PARAMETER EnginePath
  Folder of Unreal Engine 5.8. Default: C:\Program Files\Epic Games\UE_5.8
.PARAMETER Width
  Picture size (16:9). Default 960x540.
#>
param(
    [string[]]$Only = @(),
    [switch]$SkipImport,
    [string]$EnginePath = "C:\Program Files\Epic Games\UE_5.8",
    [int]$Width = 960,
    [int]$DelaySeconds = 16
)

$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
$uproject = Join-Path $project "InstagibArena.uproject"
$exclusive = Join-Path $PSScriptRoot "exclusive.ps1"
$game = Join-Path $EnginePath "Engine\Binaries\Win64\UnrealEditor.exe"
$cmd = Join-Path $EnginePath "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$height = [int]($Width * 9 / 16)
$thumbDir = Join-Path $project "Tools\MapThumbs"
$logDir = Join-Path $project "Saved\ThumbLogs"
New-Item -ItemType Directory -Force $thumbDir, $logDir | Out-Null

# --- 1. read the map list
$header = Get-Content (Join-Path $project "Source\InstagibArena\IAMapList.h") -Raw
$paths = [regex]::Matches($header, 'TEXT\("(/Game/Maps/[^"]+)"\)') | ForEach-Object { $_.Groups[1].Value } |
    Where-Object { $_ -notmatch 'MainMenu' } | Select-Object -Unique
if ($Only.Count -gt 0) { $paths = $paths | Where-Object { $Only -contains ($_ -replace '^.*/', '') } }
"Maps: " + (($paths | ForEach-Object { $_ -replace '^.*/', '' }) -join ", ")

# --- 2. one game run per map
$darkMaps = @{ "DM-Neon" = 1.5 }
$recommended = @{}
foreach ($path in $paths) {
    $name = $path -replace '^.*/', ''
    $shot = "Thumb_$name"
    $png = Join-Path $project "Saved\IAShots\$shot.png"
    Remove-Item $png -ErrorAction SilentlyContinue
    $log = Join-Path $logDir "$name.log"

    $url = "$path`?Mode=FFA`?Bots=0`?ScoreLimit=0`?TimeLimit=0"
    # Dark maps need a brighter picture (exposure bias in stops). Add a line here when a new map looks too dark.
    $exposure = 0
    if ($darkMaps.ContainsKey($name)) { $exposure = $darkMaps[$name] }
    $gameArgs = "`"$uproject`" `"$url`" -game -windowed -ResX=$Width -ResY=$height -nosound -nosplash -IAShotAuto -IAShotExposure=$exposure -IAShotDelay=$DelaySeconds -IAShotName=$shot `"-abslog=$log`""
    $line = "& { `$p = Start-Process -FilePath '$game' -ArgumentList '$($gameArgs.Replace("'", "''"))' -PassThru; if (-not `$p.WaitForExit(300000)) { `$p.Kill() } }"
    "[$name] running the game..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File $exclusive -Command $line | Out-Null

    if (Test-Path $png) {
        Copy-Item $png (Join-Path $thumbDir "$name.png") -Force
        "[$name] picture saved"
    } else {
        Write-Warning "[$name] no picture was made, see $log"
    }
    $info = Select-String -Path $log -Pattern "THUMB_INFO" -ErrorAction SilentlyContinue | Select-Object -Last 1
    if ($info -and $info.Line -match 'starts=(\d+)') {
        $starts = [int]$Matches[1]
        if ($starts -gt 0) {
            $min = [Math]::Max(2, [int][Math]::Round($starts * 0.35))
            $max = [Math]::Min(11, [Math]::Max($min + 2, [int][Math]::Round($starts * 0.75)))
            $recommended[$path] = @($min, $max)
            "[$name] $starts player starts -> recommended $min-$max players"
        }
    }
}

# --- 3. recommended player counts (merged with what is already in the file)
$inlPath = Join-Path $project "Source\InstagibArena\IAMapRecommended.inl"
$entries = [ordered]@{}
foreach ($m in [regex]::Matches((Get-Content $inlPath -Raw), '\{ TEXT\("([^"]+)"\), (\d+), (\d+) \}')) {
    $entries[$m.Groups[1].Value] = @([int]$m.Groups[2].Value, [int]$m.Groups[3].Value)
}
foreach ($key in $recommended.Keys) { $entries[$key] = $recommended[$key] }
$out = @(
    "// Recommended player counts per map (humans plus bots). Written by Tools/make_thumbnails.ps1 from the",
    "// number of player starts it finds in each level. Maps that are not listed fall back to 2-8."
)
foreach ($key in $entries.Keys) { $out += "{ TEXT(`"$key`"), $($entries[$key][0]), $($entries[$key][1]) }," }
Set-Content -Path $inlPath -Value $out -Encoding Ascii

# --- 4. import the pictures as textures
if (-not $SkipImport) {
    $py = Join-Path $PSScriptRoot "import_thumbnails.py"
    $importLog = Join-Path $logDir "import.log"
    $line = "& '$cmd' '$uproject' -ExecutePythonScript='$py' -unattended -nullrhi -nosplash -nopause '-abslog=$importLog'"
    "Importing textures..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File $exclusive -Command $line | Out-Null
    Select-String -Path $importLog -Pattern "THUMB_IMPORTED|THUMB_IMPORT_DONE|THUMB_IMPORT_MISSING" | ForEach-Object { $_.Line }
}
"Done. Rebuild the game if IAMapRecommended.inl changed."
