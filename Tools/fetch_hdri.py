"""Downloads and prepares the sky panoramas (HDRIs) used by the sky dome (Tools/maplooks.py, Tools/import_skies.py).

Source (CC0, free for any use, no attribution required but we credit it in NOTICE.md):
  Poly Haven   https://polyhaven.com   (API: https://api.polyhaven.com/files/<slug>), the "pure skies" panoramas.

Everything is stored OUTSIDE the repository, in a cache shared by all worktrees:
  Windows default  C:\\Users\\<you>\\AssetCache\\hdri      (override: environment variable IA_HDRI_CACHE)
  <cache>/<slug>_<res>.hdr         the download (Radiance RGBE, equirectangular)
  <cache>/<look>.hdr               the prepared panorama that is imported: normalised so that the mean brightness of the
                                   upper hemisphere (sun disc excluded) is 1.0, the sun disc is limited to SUN_CAP so that it
                                   cannot bloom the whole screen or double the light of the directional light
  <cache>/<look>.json              measurements: sun direction (azimuth/elevation in the panorama), sun colour,
                                   horizon colour (for the fog), zenith colour, mean brightness before normalising, author, ...

Runs with any Python 3 without extra packages (pure python), for example the one that ships with Unreal Engine:
  "C:\\Program Files\\Epic Games\\UE_5.8\\Engine\\Binaries\\ThirdParty\\Python3\\Win64\\python.exe" Tools\\fetch_hdri.py
  ... fetch_hdri.py                download and prepare everything in SKIES
  ... fetch_hdri.py dusk night     only the named looks
  ... fetch_hdri.py --notice       only rewrite the sky credits in NOTICE.md
  ... fetch_hdri.py --preview out.png slug1 slug2 ...    contact sheet of arbitrary Poly Haven slugs (1k), for choosing
"""

import array
import json
import math
import os
import struct
import sys
import urllib.request
import zlib

UA = {"User-Agent": "InstagibArena-hdri-fetch/1.0"}

# look name -> (Poly Haven slug, resolution of the download)
SKIES = {
    "day_clear": ("kloofendal_48d_partly_cloudy_puresky", "2k"),
    "overcast":  ("kloofendal_overcast_puresky", "2k"),
    "dusk":      ("evening_road_01_puresky", "2k"),
    "night_city": ("kloppenheim_07_puresky", "2k"),
    "volcanic":  ("scythian_tombs_puresky", "2k"),
    "arctic":    ("syferfontein_18d_clear_puresky", "2k"),
    "desert":    ("kloofendal_43d_clear_puresky", "2k"),
}

# Brightness (relative to the mean of the upper hemisphere = 1) that the sun disc is limited to.
SUN_CAP = 14.0
# Elevation (degrees) below which the panorama is faded to its horizon colour (the maps have a ground of their own).
OUT_W = {"1k": 1024, "2k": 2048}


def cache_dir():
    d = os.environ.get("IA_HDRI_CACHE") or os.path.join(os.path.expanduser("~"), "AssetCache", "hdri")
    os.makedirs(d, exist_ok=True)
    return d


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def _json(url):
    return json.loads(_get(url).decode("utf8"))


# ---------------------------------------------------------------------------------------------------------
# Radiance .hdr reader / writer (RGBE, run-length encoded)
# ---------------------------------------------------------------------------------------------------------
def read_hdr(path):
    """Returns (width, height, rgb) where rgb is an array('f') of width*height*3 linear floats, top row first."""
    with open(path, "rb") as f:
        data = f.read()
    pos = 0
    w = h = 0
    flip = False
    while True:
        end = data.index(b"\n", pos)
        line = data[pos:end].decode("ascii", "replace").strip()
        pos = end + 1
        if line.startswith("-Y") or line.startswith("+Y"):
            parts = line.split()
            h, w = int(parts[1]), int(parts[3])
            flip = parts[0] == "+Y"
            break
    rgbe = bytearray(w * h * 4)
    for y in range(h):
        row = bytearray(w * 4)
        c0, c1 = data[pos], data[pos + 1]
        if 8 <= w < 32768 and c0 == 2 and c1 == 2 and not (data[pos + 2] & 0x80):
            pos += 4
            for ch in range(4):
                x = 0
                while x < w:
                    n = data[pos]
                    pos += 1
                    if n > 128:
                        n -= 128
                        v = data[pos]
                        pos += 1
                        row[ch + 4 * x: ch + 4 * (x + n): 4] = bytes([v]) * n
                    else:
                        row[ch + 4 * x: ch + 4 * (x + n): 4] = data[pos:pos + n]
                        pos += n
                    x += n
        else:
            row[:] = data[pos:pos + 4 * w]
            pos += 4 * w
        rgbe[y * w * 4:(y + 1) * w * 4] = row
    scale = [0.0] + [math.ldexp(1.0, e - 136) for e in range(1, 256)]
    out = array.array("f", bytes(4 * 3 * w * h))
    for i in range(w * h):
        e = rgbe[4 * i + 3]
        if e:
            s = scale[e]
            out[3 * i] = rgbe[4 * i] * s
            out[3 * i + 1] = rgbe[4 * i + 1] * s
            out[3 * i + 2] = rgbe[4 * i + 2] * s
    if flip:
        rows = [out[3 * w * y:3 * w * (y + 1)] for y in range(h)]
        rows.reverse()
        out = array.array("f")
        for r in rows:
            out.extend(r)
    return w, h, out


def write_hdr(path, w, h, rgb):
    """Writes an RLE Radiance file (literal runs only: valid for every reader, small enough)."""
    frexp = math.frexp
    with open(path, "wb") as f:
        f.write(b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n" % (h, w))
        for y in range(h):
            chans = [bytearray(w) for _ in range(4)]
            base = 3 * w * y
            for x in range(w):
                r, g, b = rgb[base + 3 * x], rgb[base + 3 * x + 1], rgb[base + 3 * x + 2]
                m = max(r, g, b)
                if m < 1e-32:
                    continue
                mant, ex = frexp(m)
                k = mant * 256.0 / m
                chans[0][x] = min(255, int(r * k))
                chans[1][x] = min(255, int(g * k))
                chans[2][x] = min(255, int(b * k))
                chans[3][x] = ex + 128
            f.write(bytes([2, 2, (w >> 8) & 255, w & 255]))
            for ch in chans:
                x = 0
                while x < w:
                    n = min(128, w - x)
                    f.write(bytes([n]))
                    f.write(bytes(ch[x:x + n]))
                    x += n


# ---------------------------------------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------------------------------------
def lum(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def direction(u, v):
    """Unit direction (x forward, y right, z up) of the panorama pixel at (u, v) in 0..1.
    u=0.5 looks along +x, u grows towards +y (the convention of Unreal's long-lat cubemap import)."""
    az = (u - 0.5) * 2.0 * math.pi
    el = (0.5 - v) * math.pi
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))


def analyse(w, h, rgb):
    """Finds the sun and the colours of horizon, zenith and sky. Returns a dict (all colours linear)."""
    # brightest region of the upper hemisphere
    best, bi = -1.0, 0
    for y in range(h // 2):
        base = 3 * w * y
        for x in range(w):
            L = lum(rgb[base + 3 * x], rgb[base + 3 * x + 1], rgb[base + 3 * x + 2])
            if L > best:
                best, bi = L, y * w + x
    by, bx = divmod(bi, w)
    bu, bv = (bx + 0.5) / w, (by + 0.5) / h
    bd = direction(bu, bv)
    # the sun: pixels within 6 degrees of the peak that are brighter than a quarter of it
    sx = sy = sz = 0.0
    ws = 0.0
    col = [0.0, 0.0, 0.0]
    cos6 = math.cos(math.radians(6.0))
    for y in range(max(0, by - h // 20), min(h // 2, by + h // 20)):
        for x in range(w):
            d = direction((x + 0.5) / w, (y + 0.5) / h)
            if d[0] * bd[0] + d[1] * bd[1] + d[2] * bd[2] < cos6:
                continue
            i = 3 * (y * w + x)
            L = lum(rgb[i], rgb[i + 1], rgb[i + 2])
            if L < 0.25 * best:
                continue
            wt = L
            sx += d[0] * wt
            sy += d[1] * wt
            sz += d[2] * wt
            ws += wt
            col[0] += rgb[i]
            col[1] += rgb[i + 1]
            col[2] += rgb[i + 2]
    n = math.sqrt(sx * sx + sy * sy + sz * sz) or 1.0
    sd = (sx / n, sy / n, sz / n)
    sun_az = math.degrees(math.atan2(sd[1], sd[0]))
    sun_el = math.degrees(math.asin(max(-1.0, min(1.0, sd[2]))))
    cm = max(col) or 1.0
    sun_rgb = [c / cm for c in col]

    # sky statistics, the sun surroundings (25 degrees) left out so that a bright sun does not decide the exposure
    cos25 = math.cos(math.radians(25.0))
    tot = 0.0
    wsum = 0.0
    hor = [0.0, 0.0, 0.0]
    hw = 0.0
    zen = [0.0, 0.0, 0.0]
    zw = 0.0
    for y in range(h // 2):
        v = (y + 0.5) / h
        el = (0.5 - v) * 180.0
        coslat = math.cos(math.radians(el))
        base = 3 * w * y
        for x in range(0, w, 2):
            d = direction((x + 0.5) / w, v)
            if d[0] * sd[0] + d[1] * sd[1] + d[2] * sd[2] > cos25:
                continue
            i = base + 3 * x
            r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
            tot += lum(r, g, b) * coslat
            wsum += coslat
            if el < 12.0:
                hor[0] += r
                hor[1] += g
                hor[2] += b
                hw += 1
            if el > 65.0:
                zen[0] += r * coslat
                zen[1] += g * coslat
                zen[2] += b * coslat
                zw += coslat
    mean = tot / max(wsum, 1e-9)
    hor = [c / max(hw, 1) for c in hor]
    zen = [c / max(zw, 1e-9) for c in zen]
    return {
        "sun_azimuth": sun_az, "sun_elevation": sun_el, "sun_peak": best,
        "sun_rgb": sun_rgb, "mean_luminance": mean,
        "horizon_rgb_raw": hor, "zenith_rgb_raw": zen,
        "horizon_rgb": [c / mean for c in hor], "zenith_rgb": [c / mean for c in zen],
    }


def prepare(w, h, rgb, info):
    """Normalises the panorama (upper hemisphere mean = 1), limits the sun, replaces the lower hemisphere by a smooth
    fade from the horizon colour to a darker ground colour so that no photographed ground shows below the maps."""
    k = 1.0 / info["mean_luminance"]
    out = array.array("f", bytes(4 * len(rgb)))
    half = h // 2
    for y in range(half):
        base = 3 * w * y
        for x in range(w):
            i = base + 3 * x
            r, g, b = rgb[i] * k, rgb[i + 1] * k, rgb[i + 2] * k
            L = lum(r, g, b)
            if L > SUN_CAP:
                s = SUN_CAP / L
                r, g, b = r * s, g * s, b * s
            out[i], out[i + 1], out[i + 2] = r, g, b
    # below the horizon: the colour of the horizon row of each column, fading darker towards the nadir
    edge = 3 * w * (half - 1)
    for y in range(half, h):
        el = (0.5 - (y + 0.5) / h) * 180.0
        f = 1.0 - 0.55 * min(1.0, -el / 25.0)
        base = 3 * w * y
        for x in range(3 * w):
            out[base + x] = out[edge + x] * f
    return out


# ---------------------------------------------------------------------------------------------------------
# Preview (PNG, tone mapped) - used to choose panoramas by eye
# ---------------------------------------------------------------------------------------------------------
def _png(path, w, h, rows):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def tonemap_rows(w, h, rgb, out_w, exposure=1.0):
    """Reinhard-ish tone map, nearest-neighbour downscale to out_w wide."""
    out_h = out_w * h // w
    rows = []
    for oy in range(out_h):
        y = oy * h // out_h
        row = bytearray()
        for ox in range(out_w):
            x = ox * w // out_w
            i = 3 * (y * w + x)
            px = []
            for c in range(3):
                v = rgb[i + c] * exposure
                v = v / (1.0 + v)
                v = v ** (1.0 / 2.2)
                px.append(min(255, int(v * 255)))
            row += bytes(px)
        rows.append(bytes(row))
    return out_w, out_h, rows


def preview(out_path, slugs, res="1k"):
    cells = []
    for slug in slugs:
        p = download(slug, res)[0]
        w, h, rgb = read_hdr(p)
        a = analyse(w, h, rgb)
        print("%-42s sun az %7.1f el %5.1f  mean %.3f  horizon %s" % (
            slug, a["sun_azimuth"], a["sun_elevation"], a["mean_luminance"], ["%.2f" % c for c in a["horizon_rgb"]]))
        # exposure so that the upper hemisphere mean is mid grey
        cells.append(tonemap_rows(w, h, rgb, 512, exposure=0.6 / a["mean_luminance"]))
    cols = 2
    rows_out = []
    for i in range(0, len(cells), cols):
        grp = cells[i:i + cols]
        for r in range(grp[0][1]):
            rows_out.append(b"".join(g[2][r] if r < g[1] else b"\0" * (g[0] * 3) for g in grp))
    _png(out_path, 512 * cols, len(rows_out), rows_out)
    print("wrote", out_path)


# ---------------------------------------------------------------------------------------------------------
def download(slug, res):
    """Downloads <slug> at <res> into the cache. Returns (path, poly haven info dict)."""
    path = os.path.join(cache_dir(), "%s_%s.hdr" % (slug, res))
    info_path = os.path.join(cache_dir(), "%s.info.json" % slug)
    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf8") as f:
            info = json.load(f)
    else:
        info = _json("https://api.polyhaven.com/info/" + slug)
        with open(info_path, "w", encoding="utf8") as f:
            json.dump(info, f, indent=1)
    if not os.path.exists(path):
        files = _json("https://api.polyhaven.com/files/" + slug)
        url = files["hdri"][res]["hdr"]["url"]
        with open(path, "wb") as f:
            f.write(_get(url))
    return path, info


def fetch(look):
    """Downloads, measures and prepares the panorama of one look; returns its meta dict."""
    slug, res = SKIES[look]
    meta_path = os.path.join(cache_dir(), look + ".json")
    out_path = os.path.join(cache_dir(), look + ".hdr")
    if os.path.exists(meta_path) and os.path.exists(out_path):
        with open(meta_path, "r", encoding="utf8") as f:
            return json.load(f)
    path, pinfo = download(slug, res)
    w, h, rgb = read_hdr(path)
    meta = analyse(w, h, rgb)
    write_hdr(out_path, w, h, prepare(w, h, rgb, meta))
    authors = ", ".join(sorted(pinfo.get("authors", {}).keys())) or "Poly Haven"
    meta.update({"look": look, "slug": slug, "resolution": res, "source": "Poly Haven",
                 "url": "https://polyhaven.com/a/" + slug, "authors": authors, "license": "CC0 1.0",
                 "width": w, "height": h})
    with open(meta_path, "w", encoding="utf8") as f:
        json.dump(meta, f, indent=1)
    return meta


def load_meta(look):
    p = os.path.join(cache_dir(), look + ".json")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf8") as f:
        return json.load(f)


BEGIN = "<!-- SKIES-BEGIN (generated by Tools/fetch_hdri.py --notice) -->"
END = "<!-- SKIES-END -->"


def write_notice(repo_root=None):
    """Rewrites the generated sky table in NOTICE.md (a section of its own, before the 3D models)."""
    repo_root = repo_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo_root, "NOTICE.md")
    with open(path, "r", encoding="utf8") as f:
        text = f.read()
    rows = []
    for look in SKIES:
        m = load_meta(look)
        if m is None:
            continue
        rows.append("| %s | Poly Haven | [%s](%s) | %s | CC0 1.0 |" % (look, m["slug"], m["url"], m["authors"]))
    block = [BEGIN, "", "| Look | Source | Asset | Author | Licence |", "|---|---|---|---|---|"] + rows + ["", END]
    intro = (
        "\n### Sky panoramas (Poly Haven, CC0)\n\n"
        "The photographic skies behind the maps (`/Game/Sky/T_Sky_<look>`, shown by the sky dome `M_IASky`) are HDR panoramas from "
        "[Poly Haven](https://polyhaven.com), released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) "
        "(public domain, no attribution required; credited here anyway). `Tools/fetch_hdri.py` downloads them (2k) into a cache "
        "outside the repository and prepares them (brightness normalised, sun disc limited, ground below the horizon replaced by a smooth fade); "
        "`Tools/import_skies.py` imports them as cube maps.\n\n")
    if BEGIN in text and END in text:
        pre = text[:text.index(BEGIN)]
        post = text[text.index(END) + len(END):]
        text = pre + "\n".join(block) + post
    else:
        marker = "### 3D models (Poly Haven, CC0)"
        section = intro + "\n".join(block) + "\n\n"
        if marker in text:
            i = text.index(marker)
            text = text[:i].rstrip() + "\n" + section + text[i:]
        else:
            text = text.rstrip() + "\n" + section
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(text)
    print("NOTICE.md updated with %d sky rows" % len(rows))


def main(argv):
    if argv and argv[0] == "--preview":
        preview(argv[1], argv[2:])
        return
    args = [a for a in argv if not a.startswith("--")]
    if "--notice" not in argv or args:
        for look in (args or list(SKIES)):
            if look not in SKIES:
                print("unknown look:", look)
                continue
            try:
                m = fetch(look)
                print("ok   %-11s %-40s sun az %7.1f el %5.1f  mean %.3f" % (
                    look, m["slug"], m["sun_azimuth"], m["sun_elevation"], m["mean_luminance"]))
            except Exception as e:  # keep going: one bad slug must not stop the rest
                print("FAIL %-11s %s" % (look, e))
    write_notice()


if __name__ == "__main__":
    main(sys.argv[1:])
