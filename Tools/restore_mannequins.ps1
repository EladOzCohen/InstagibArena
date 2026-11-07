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
    Copy-Item -Path (Join-Path $source $folder) -Destination (Join-Path $target $folder) -Recurse -Force
}
New-Item -ItemType Directory -Force (Join-Path $target "Anims") | Out-Null
foreach ($folder in "Unarmed", "Death") {
    Copy-Item -Path (Join-Path $source "Anims\$folder") -Destination (Join-Path $target "Anims\$folder") -Recurse -Force
}

$count = (Get-ChildItem $target -Recurse -File | Measure-Object).Count
"Copied $count files to $target"
