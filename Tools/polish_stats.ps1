<#
.SYNOPSIS
  Brightness statistics of screenshots (an objective check for exposure): mean luma, share of burnt-out and of crushed pixels.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\polish_stats.ps1 -Files Saved\IAShots\polish\p2_Foundry_auto.png,Saved\IAShots\polish\p2_Glacier_auto.png

  The HUD (top bar, bottom-left box, kill feed) is cropped out first. Columns:
    mean     average brightness 0..255 of the 3D picture (luma = 0.2126 R + 0.7152 G + 0.0722 B on the sRGB values)
    burnt    percent of pixels with luma >= 245 (white, no detail)
    crushed  percent of pixels with luma <= 12 (black, no detail)
    sat      average saturation 0..1 (washed-out pictures have a low value, neon/over-saturated pictures a high one)
  Good pictures of this game: mean 70..115, burnt < 6 percent, crushed < 15 percent (night maps Neon and Forge: mean 35..80).
#>
param([Parameter(Mandatory = $true)][string[]]$Files)

Add-Type -AssemblyName System.Drawing
$Files = $Files | ForEach-Object { $_ -split "," }
foreach ($f in $Files) {
    $path = (Resolve-Path $f).Path
    $src = [System.Drawing.Bitmap]::FromFile($path)
    # crop the HUD: top 12 percent, bottom 14 percent, right 22 percent
    $cx = 0; $cy = [int]($src.Height * 0.12); $cw = [int]($src.Width * 0.78); $ch = [int]($src.Height * 0.74)
    $small = New-Object System.Drawing.Bitmap 200, 100
    $g = [System.Drawing.Graphics]::FromImage($small)
    $g.InterpolationMode = 'HighQualityBilinear'
    $g.DrawImage($src, (New-Object System.Drawing.Rectangle 0, 0, 200, 100), (New-Object System.Drawing.Rectangle $cx, $cy, $cw, $ch), 'Pixel')
    $g.Dispose(); $src.Dispose()
    $sum = 0.0; $burnt = 0; $crushed = 0; $sat = 0.0; $n = 0
    for ($y = 0; $y -lt 100; $y++) {
        for ($x = 0; $x -lt 200; $x++) {
            $c = $small.GetPixel($x, $y)
            $l = 0.2126 * $c.R + 0.7152 * $c.G + 0.0722 * $c.B
            $sum += $l; $n++
            if ($l -ge 245) { $burnt++ }
            if ($l -le 12) { $crushed++ }
            $mx = [Math]::Max($c.R, [Math]::Max($c.G, $c.B)); $mn = [Math]::Min($c.R, [Math]::Min($c.G, $c.B))
            if ($mx -gt 0) { $sat += ($mx - $mn) / $mx }
        }
    }
    $small.Dispose()
    "{0,-34} mean={1,5:N0} burnt={2,5:N1}% crushed={3,5:N1}% sat={4:N2}" -f (Split-Path $f -Leaf), ($sum / $n), (100.0 * $burnt / $n), (100.0 * $crushed / $n), ($sat / $n)
}
