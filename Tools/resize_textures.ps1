<#
.SYNOPSIS
  Makes smaller copies of a cached Poly Haven model's textures (needs only Windows PowerShell + System.Drawing).

    resize_textures.ps1 -Dir C:\Users\me\AssetCache\models\Barrel_01 -Size 512

  Writes <Dir>\textures_<Size>\<same name>.jpg (JPEG quality 88). Existing files are kept, so it is cheap to run again.
  Used by import_props.py to keep the imported Content/Props folder small.
#>
param(
    [Parameter(Mandatory = $true)][string]$Dir,
    [int]$Size = 512
)
Add-Type -AssemblyName System.Drawing
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
$enc = New-Object System.Drawing.Imaging.EncoderParameters(1)
$enc.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]88)
$out = Join-Path $Dir "textures_$Size"
New-Item -ItemType Directory -Force $out | Out-Null
foreach ($f in Get-ChildItem (Join-Path $Dir "textures") -Filter *.jpg) {
    $dest = Join-Path $out $f.Name
    if (Test-Path $dest) { continue }
    $img = [System.Drawing.Image]::FromFile($f.FullName)
    $bmp = New-Object System.Drawing.Bitmap($Size, $Size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.DrawImage($img, 0, 0, $Size, $Size)
    $bmp.Save($dest, $codec, $enc)
    $g.Dispose(); $bmp.Dispose(); $img.Dispose()
}
