"""Downloads the PBR texture sets used by the world material library (Tools/matlib.py).

Sources (all CC0, free for any use, no attribution required but we credit them in NOTICE.md):
  Poly Haven   https://polyhaven.com   (API: https://api.polyhaven.com)
  ambientCG    https://ambientcg.com   (API: https://ambientcg.com/api/v2/full_json)

Every set is stored OUTSIDE the repository, in a cache shared by all worktrees:
  Windows default  C:\\Users\\<you>\\AssetCache\\textures      (override: environment variable IA_TEXTURE_CACHE)
  <cache>/<Name>/<Name>_diff.jpg   colour (sRGB)
  <cache>/<Name>/<Name>_nor.jpg    normal map, OpenGL convention (green up); the importer flips green for Unreal
  <cache>/<Name>/<Name>_rough.jpg  roughness
  <cache>/<Name>/meta.json         source, slug, author, licence, real-world size of one tile in metres

Files that are already there are skipped. This script runs with any Python 3 (stdlib only), for example the one that
ships with Unreal Engine:
  "C:\\Program Files\\Epic Games\\UE_5.8\\Engine\\Binaries\\ThirdParty\\Python3\\Win64\\python.exe" Tools\\fetch_textures.py
  ... fetch_textures.py                 download everything in TEXTURES
  ... fetch_textures.py ConcreteDirty   download only the named sets
  ... fetch_textures.py --notice        only rewrite the "Third-party assets" section of NOTICE.md
"""

import io
import json
import os
import re
import sys
import urllib.request
import zipfile

UA = {"User-Agent": "InstagibArena-texture-fetch/1.0"}

# name -> (source, slug, resolution, tile size in metres or None = read it from Poly Haven)
# "ph" = Poly Haven, "acg" = ambientCG. Name = the surface name used by matlib.py (T_<Name>_D, ...).
TEXTURES = {
    # --- concrete ---------------------------------------------------------------------------------
    "ConcreteClean":    ("ph", "concrete_floor_01", "1k", None),
    "ConcreteDirty":    ("ph", "concrete_floor_02", "1k", None),
    "ConcretePanels":   ("ph", "concrete_slab_wall_02", "1k", None),
    "ConcreteWorn":     ("ph", "concrete_floor_worn_001", "1k", None),
    "ConcreteBlocks":   ("ph", "concrete_block_wall", "1k", None),
    # --- brick, plaster ---------------------------------------------------------------------------
    "BrickRed":         ("ph", "brick_wall_001", "1k", None),
    "BrickDark":        ("ph", "brick_wall_10", "1k", None),
    "PlasterGrey":      ("ph", "plaster_grey_04", "1k", None),
    "PlasterWeathered": ("ph", "plastered_wall_02", "1k", None),
    # --- stone ------------------------------------------------------------------------------------
    "SandstoneBlocks":  ("ph", "sandstone_blocks_05", "1k", None),
    "SandstoneRough":   ("ph", "sandstone_blocks_04", "1k", None),
    "StoneRubble":      ("ph", "rock_wall_08", "1k", None),
    "SlabsGrey":        ("ph", "large_grey_tiles", "1k", None),
    "Cobblestone":      ("ph", "cobblestone_floor_05", "1k", None),
    # --- asphalt, roofing -------------------------------------------------------------------------
    "Asphalt":          ("ph", "asphalt_01", "1k", None),
    "AsphaltCracked":   ("ph", "asphalt_04", "1k", None),
    "RoofBitumen":      ("ph", "bitumen", "1k", None),
    "RoofSlate":        ("ph", "roof_slates_02", "1k", None),
    # --- metal ------------------------------------------------------------------------------------
    "RustOrange":       ("ph", "rusty_painted_metal", "1k", None),
    "RustCoarse":       ("ph", "rust_coarse_01", "1k", None),
    "DiamondPlate":     ("ph", "metal_plate", "1k", None),
    "CorrugatedGalv":   ("ph", "corrugated_iron_02", "1k", None),
    "CorrugatedRust":   ("ph", "rusty_corrugated_iron", "1k", None),
    "BrushedMetal":     ("acg", "Metal012", "1K", 1.0),
    "ContainerPaint":   ("acg", "CorrugatedSteel007A", "1K", 1.0),
    # --- wood -------------------------------------------------------------------------------------
    "WoodPlanksOld":    ("ph", "wood_planks_grey", "1k", None),
    "WoodPlanksDark":   ("ph", "old_planks_02", "1k", None),
    "WoodPainted":      ("ph", "wood_peeling_paint_weathered", "1k", None),
    # --- rock -------------------------------------------------------------------------------------
    "RockGrey":         ("ph", "rock_boulder_dry", "1k", None),
    "RockCliff":        ("ph", "rock_face_03", "1k", None),
    "RockDark":         ("ph", "rock_face", "1k", None),
    # --- ground -----------------------------------------------------------------------------------
    "Sand":             ("ph", "sand_01", "1k", None),
    "RedGround":        ("ph", "red_sand", "1k", None),
    "DirtDry":          ("ph", "dry_ground_01", "1k", None),
    "Gravel":           ("ph", "gravel_floor_02", "1k", None),
    "Snow":             ("ph", "snow_02", "1k", None),
    "Ice":              ("acg", "Ice002", "1K", 2.0),
    # --- fabric, rope -----------------------------------------------------------------------------
    "Canvas":           ("ph", "hessian_230", "1k", None),
    "Rope":             ("acg", "Rope001", "1K", 0.5),
    # --- lava (only used by M_IALava, which is the one emissive material of the library) --------------
    "Lava":             ("acg", "Lava004", "1K", 2.0),
}


def cache_dir():
    d = os.environ.get("IA_TEXTURE_CACHE") or os.path.join(os.path.expanduser("~"), "AssetCache", "textures")
    os.makedirs(d, exist_ok=True)
    return d


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _json(url):
    return json.loads(_get(url).decode("utf8"))


# sets that also need an emission map (ambientCG only)
EXTRA_EMISSION = ("Lava",)


def _paths(name):
    folder = os.path.join(cache_dir(), name)
    keys = ("diff", "nor", "rough") + (("emis",) if name in EXTRA_EMISSION else ())
    return folder, {k: os.path.join(folder, "%s_%s.jpg" % (name, k)) for k in keys}


def _fetch_polyhaven(name, slug, res):
    folder, paths = _paths(name)
    info = _json("https://api.polyhaven.com/info/" + slug)
    files = _json("https://api.polyhaven.com/files/" + slug)
    for key, api_key in (("diff", "Diffuse"), ("nor", "nor_gl"), ("rough", "Rough")):
        if os.path.exists(paths[key]):
            continue
        url = files[api_key][res]["jpg"]["url"]
        with open(paths[key], "wb") as f:
            f.write(_get(url))
    dims = info.get("dimensions") or [2000, 2000]
    authors = ", ".join(sorted(info.get("authors", {}).keys())) or "Poly Haven"
    return {
        "source": "Poly Haven",
        "slug": slug,
        "url": "https://polyhaven.com/a/" + slug,
        "authors": authors,
        "license": "CC0 1.0",
        "tile_size_m": round(max(dims[0], dims[1]) / 1000.0, 3),
    }


def _fetch_ambientcg(name, asset_id, res, size_m):
    folder, paths = _paths(name)
    if not all(os.path.exists(p) for p in paths.values()):
        data = _get("https://ambientcg.com/get?file=%s_%s-JPG.zip" % (asset_id, res))
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for member in z.namelist():
                low = member.lower()
                for key, suffix in (("diff", "_color.jpg"), ("nor", "_normalgl.jpg"), ("rough", "_roughness.jpg"),
                                    ("emis", "_emission.jpg")):
                    if key in paths and low.endswith(suffix):
                        with open(paths[key], "wb") as f:
                            f.write(z.read(member))
    return {
        "source": "ambientCG",
        "slug": asset_id,
        "url": "https://ambientcg.com/a/" + asset_id,
        "authors": "ambientCG (Lennart Demes)",
        "license": "CC0 1.0",
        "tile_size_m": size_m or 1.0,
    }


def fetch(name):
    """Makes sure the set is in the cache; returns its meta dict."""
    source, slug, res, size_m = TEXTURES[name]
    folder, paths = _paths(name)
    os.makedirs(folder, exist_ok=True)
    meta_path = os.path.join(folder, "meta.json")
    if all(os.path.exists(p) for p in paths.values()) and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf8") as f:
            return json.load(f)
    if source == "ph":
        meta = _fetch_polyhaven(name, slug, res)
    else:
        meta = _fetch_ambientcg(name, slug, res, size_m)
    meta["name"] = name
    meta["resolution"] = res
    meta["files"] = {k: os.path.basename(v) for k, v in paths.items()}
    with open(meta_path, "w", encoding="utf8") as f:
        json.dump(meta, f, indent=1)
    return meta


def load_meta(name):
    """Reads meta.json of a cached set (None when it is not downloaded)."""
    p = os.path.join(cache_dir(), name, "meta.json")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf8") as f:
        return json.load(f)


BEGIN = "<!-- TEXTURES-BEGIN (generated by Tools/fetch_textures.py --notice) -->"
END = "<!-- TEXTURES-END -->"


def write_notice(repo_root=None):
    """Rewrites the generated texture table inside the 'Third-party assets' section of NOTICE.md."""
    repo_root = repo_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo_root, "NOTICE.md")
    with open(path, "r", encoding="utf8") as f:
        text = f.read()
    rows = []
    for name in TEXTURES:
        m = load_meta(name)
        if m is None:
            continue
        rows.append("| %s | %s | [%s](%s) | %s | %s |" % (
            name, m["source"], m["slug"], m["url"], m["authors"], m["license"]))
    block = [BEGIN, "", "| Surface | Source | Asset | Author | Licence |", "|---|---|---|---|---|"] + rows + ["", END]
    intro = (
        "\n## Third-party assets\n\n"
        "Surface textures of the world material library (`Tools/matlib.py`, imported into `Content/Textures/World`) "
        "come from [Poly Haven](https://polyhaven.com) and [ambientCG](https://ambientcg.com). Both publish their "
        "assets under the [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) public-domain dedication "
        "(no attribution required; we credit the authors anyway). `Tools/fetch_textures.py` downloads them into a cache "
        "outside the repository.\n\n")
    if BEGIN in text and END in text:
        pre = text[:text.index(BEGIN)]
        post = text[text.index(END) + len(END):]
        text = pre + "\n".join(block) + post
    else:
        if "## Third-party assets" in text:
            text = text.rstrip() + "\n\n" + "\n".join(block) + "\n"
        else:
            text = text.rstrip() + "\n" + intro + "\n".join(block) + "\n"
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(text)
    print("NOTICE.md updated with %d texture rows" % len(rows))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--notice" not in argv or args:
        names = args or list(TEXTURES)
        for n in names:
            if n not in TEXTURES:
                print("unknown texture set:", n)
                continue
            try:
                meta = fetch(n)
                print("ok   %-18s %-28s tile %.2f m" % (n, meta["slug"], meta["tile_size_m"]))
            except Exception as e:  # keep going: one bad slug must not stop the rest
                print("FAIL %-18s %s" % (n, e))
    write_notice()


if __name__ == "__main__":
    main(sys.argv[1:])
