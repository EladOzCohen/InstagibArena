<#
.SYNOPSIS
  Builds the Windows game and the installer.

.DESCRIPTION
  1. Packages the game (build + cook + pak) into Builds\Windows with Unreal's Automation Tool.
  2. Copies the player README into the package.
  3. Compiles the Inno Setup installer into Builds\InstagibArena_Setup_<version>.exe.

  Needs Unreal Engine 5.8, Visual Studio 2022 with the "Game development with C++" workload,
  and Inno Setup 6 (https://jrsoftware.org/isinfo.php).

.PARAMETER EnginePath
  Folder of your Unreal Engine 5.8 install.
.PARAMETER InnoPath
  Folder of your Inno Setup 6 install. Default: the per-user location the Inno installer uses.
#>
param(
    [string]$EnginePath = "C:\Program Files\Epic Games\UE_5.8",
    [string]$InnoPath = "$env:LOCALAPPDATA\Programs\Inno Setup 6"
)

$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
$uproject = Join-Path $project "InstagibArena.uproject"
$builds = Join-Path $project "Builds"
$package = Join-Path $builds "Windows"

Write-Host "== 1/3 Packaging the game (this takes a while)"
& (Join-Path $EnginePath "Engine\Build\BatchFiles\RunUAT.bat") BuildCookRun "-project=$uproject" -noP4 -platform=Win64 `
    -clientconfig=Shipping -cook -build -stage -pak -compressed -prereqs -archive "-archivedirectory=$builds" -utf8output -nodebuginfo
if ($LASTEXITCODE -ne 0) { throw "Packaging failed (exit code $LASTEXITCODE)." }

Write-Host "== 2/3 Adding the player README"
Copy-Item (Join-Path $PSScriptRoot "installer\GameReadme.txt") (Join-Path $package "README.txt") -Force

Write-Host "== 3/3 Building the installer"
& (Join-Path $InnoPath "ISCC.exe") (Join-Path $PSScriptRoot "installer\InstagibArena.iss")
if ($LASTEXITCODE -ne 0) { throw "Installer build failed (exit code $LASTEXITCODE)." }

Get-ChildItem (Join-Path $builds "InstagibArena_Setup_*.exe") | Select-Object Name, @{n = 'MB'; e = { [math]::Round($_.Length / 1MB) } }
