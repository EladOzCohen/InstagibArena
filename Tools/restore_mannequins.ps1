<#
.SYNOPSIS
  Copies Epic's Mannequin characters from your own Unreal Engine install into this project.

.DESCRIPTION
  The characters (and their animations) come from Unreal Engine's free "Characters" content pack.
  They are Epic's content, so they are not stored in this repository. Run this once after cloning.

.PARAMETER EnginePath
  Folder of your Unreal Engine 5.8 install. Default: C:\Program Files\Epic Games\UE_5.8
#>
param(
    [string]$EnginePath = "C:\Program Files\Epic Games\UE_5.8"
)

$ErrorActionPreference = "Stop"
$source = Join-Path $EnginePath "Templates\TemplateResources\High\Characters\Content\Mannequins"
$project = Split-Path -Parent $PSScriptRoot
$target = Join-Path $project "Content\Characters\Mannequins"

if (-not (Test-Path $source)) {
    throw "Could not find the Mannequin content at '$source'. Is Unreal Engine 5.8 installed there? Use -EnginePath to point to it."
}

New-Item -ItemType Directory -Force $target | Out-Null
foreach ($folder in "Meshes", "Materials", "Textures", "Rigs") {
    $dest = Join-Path $target $folder
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }   # copying onto an existing folder would nest a second copy inside it
    Copy-Item -Path (Join-Path $source $folder) -Destination $dest -Recurse -Force
}
New-Item -ItemType Directory -Force (Join-Path $target "Anims") | Out-Null
foreach ($folder in "Unarmed", "Rifle", "Death") {
    $dest = Join-Path $target "Anims\$folder"
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Copy-Item -Path (Join-Path $source "Anims\$folder") -Destination $dest -Recurse -Force
}

# The animation blueprints of the template use Control Rigs that do not compile while cooking, and the game
# does not use them (its animation runs in code, see IAAnimInstance). Leave them out.
Get-ChildItem (Join-Path $target "Anims") -Recurse -Filter "ABP_*.uasset" | Remove-Item -Force

# The Control Rig assets are not used by the game (the animation runs in code) and they do not compile
# during cooking, which would make packaging fail. Leave them out.
Get-ChildItem (Join-Path $target "Rigs") -Filter "CR_Mannequin_*.uasset" -ErrorAction SilentlyContinue | Remove-Item -Force

$count = (Get-ChildItem $target -Recurse -File | Measure-Object).Count
"Copied $count files to $target"
