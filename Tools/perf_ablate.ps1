<#
.SYNOPSIS
  Switches rendering features off one at a time during ONE run and prints the frame time of every step (what does each feature cost?).

  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\exclusive.ps1 -Command "& Tools\perf_ablate.ps1 -Map DM-Forge -Label abl_forge -Level 3"

  Every step: switch the feature off, wait for two clean 4 s windows, switch it on again, wait for two clean windows.
  Read the timeline: the frame time in the windows after ">>> off" against the windows after ">>> on".
  At the start it also prints a few console variables (their value shows in the game log, Saved\perf\<Label>.log).
#>
param(
    [Parameter(Mandatory = $true)][string]$Map,
    [string]$Label = "ablate",
    [int]$Start = 0,
    [int]$Level = 3,
    [string]$Cvars = "",
    [int]$First = 44,
    [int]$Dwell = 16,
    [string]$Profile = "",
    [string]$Steps = ""
)
# name | command off | command on
$default = @(
    "AllShadows|ShowFlag.DynamicShadows 0|ShowFlag.DynamicShadows 1",
    "PointLights|ShowFlag.PointLights 0|ShowFlag.PointLights 1",
    "SSR|ShowFlag.ScreenSpaceReflections 0|ShowFlag.ScreenSpaceReflections 1",
    "AO|ShowFlag.AmbientOcclusion 0|ShowFlag.AmbientOcclusion 1",
    "Bloom|ShowFlag.Bloom 0|ShowFlag.Bloom 1",
    "MotionBlur|ShowFlag.MotionBlur 0|ShowFlag.MotionBlur 1",
    "Fog|ShowFlag.Fog 0|ShowFlag.Fog 1",
    "Atmosphere|ShowFlag.Atmosphere 0|ShowFlag.Atmosphere 1",
    "SkyLighting|ShowFlag.SkyLighting 0|ShowFlag.SkyLighting 1",
    "AAoff|r.AntiAliasingMethod 0|r.AntiAliasingMethod 4",
    "Res50|r.ScreenPercentage 50|r.ScreenPercentage 100",
    "Translucency|ShowFlag.Translucency 0|ShowFlag.Translucency 1",
    "Characters|ShowFlag.SkeletalMeshes 0|ShowFlag.SkeletalMeshes 1",
    "StaticMeshes|ShowFlag.StaticMeshes 0|ShowFlag.StaticMeshes 1"
)
$list = $default
if ($Steps -and (Test-Path $Steps)) { $list = Get-Content $Steps | Where-Object { $_.Trim() -ne "" } }   # a text file: one "name|off|on" per line
elseif ($Steps) { $list = $Steps.Split("#") }
$t = $First
$parts = @("12:r.Shadow.Virtual.Enable", "13:r.DynamicGlobalIlluminationMethod", "14:r.ReflectionMethod", "15:r.AntiAliasingMethod",
    "16:r.Nanite", "17:r.MegaLights.EnableForProject", "18:r.ScreenPercentage", "19:sg.ShadowQuality", "20:r.ShadowQuality",
    "30:ProfileGPU")
if (-not $Profile) { $parts = $parts | Where-Object { $_ -notlike "*ProfileGPU" } }   # -Profile 1 to print the GPU pass table at 30 s
foreach ($s in $list) {
    $name, $off, $on = $s.Split("|")
    foreach ($c in $off.Split("&")) { $parts += "${t}:$c" }     # several commands in one step: "a 1&b 2"
    $t += $Dwell
    foreach ($c in $on.Split("&")) { $parts += "${t}:$c" }
    $t += $Dwell
}
$seconds = $t + 6
& (Join-Path $PSScriptRoot "perf_run.ps1") -Map $Map -Label $Label -Start $Start -Level $Level -Cvars $Cvars -Console ($parts -join ";") -Seconds $seconds -Skip 36
