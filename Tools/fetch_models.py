"""Downloads CC0 3D models from Poly Haven (https://polyhaven.com) into a cache OUTSIDE the repository.

Run with any Python 3 (Unreal's embedded one works: Engine\\Binaries\\ThirdParty\\Python3\\Win64\\python.exe):

    python Tools/fetch_models.py rock_07 Barrel_01          # download these slugs (skips what is already cached)
    python Tools/fetch_models.py --all                       # download every slug used by Tools/props_spec.py
    python Tools/fetch_models.py --sizes rock_07 Barrel_01   # only print the download size of each slug (no download)
    python Tools/fetch_models.py --check rock_07             # does the slug exist in the Poly Haven API?
    python Tools/fetch_models.py --notice                    # Markdown table of all used models (for NOTICE.md)

Each model ends up in  <cache>/models/<slug>/<slug>.gltf  (+ <slug>.bin and textures/*.jpg, 1k resolution).
The cache folder is  %USERPROFILE%\\AssetCache  (override with the IA_ASSET_CACHE environment variable).
A finished download has a file `.done` in its folder; a half-finished one is resumed from the missing files.
Poly Haven models are licensed CC0 (public domain); see NOTICE.md.
"""

import hashlib
import json
import os
import sys
import urllib.request

API = "https://api.polyhaven.com"
HEADERS = {"User-Agent": "InstagibArena-asset-fetch/1.0"}
RES = "1k"


def cache_root():
    root = os.environ.get("IA_ASSET_CACHE") or os.path.join(os.path.expanduser("~"), "AssetCache")
    return os.path.join(root, "models")


def _get(url, binary=False):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    return data if binary else json.loads(data.decode("utf-8"))


def file_list(slug, res=RES):
    """Returns (gltf_entry, {relative_path: file_info}) for the glTF variant at the given resolution."""
    files = _get("%s/files/%s" % (API, slug))
    entry = files["gltf"][res]["gltf"]
    items = {os.path.basename(entry["url"]): entry}
    for rel, info in entry.get("include", {}).items():
        items[rel] = info
    return entry, items


def size_mb(slug, res=RES):
    _, items = file_list(slug, res)
    return sum(i.get("size", 0) for i in items.values()) / 1048576.0


def exists(slug):
    try:
        _get("%s/info/%s" % (API, slug))
        return True
    except Exception:
        return False


def info(slug):
    return _get("%s/info/%s" % (API, slug))


def fetch(slug, res=RES, quiet=False):
    """Downloads one model. Returns the path of its .gltf file."""
    folder = os.path.join(cache_root(), slug)
    gltf_path = os.path.join(folder, slug + ".gltf")
    done = os.path.join(folder, ".done")
    if os.path.exists(done) and os.path.exists(gltf_path):
        if not quiet:
            print("cached   %s" % slug)
        return gltf_path
    os.makedirs(folder, exist_ok=True)
    entry, items = file_list(slug, res)
    total = 0
    for rel, finfo in items.items():
        # The .gltf file is stored as <slug>.gltf (the server names it <slug>_<res>.gltf).
        local_rel = slug + ".gltf" if rel.endswith(".gltf") else rel
        dest = os.path.join(folder, *local_rel.split("/"))
        if os.path.exists(dest) and os.path.getsize(dest) == finfo.get("size", -1):
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        data = _get(finfo["url"], binary=True)
        md5 = finfo.get("md5")
        if md5 and hashlib.md5(data).hexdigest() != md5:
            raise RuntimeError("checksum mismatch for %s/%s" % (slug, rel))
        with open(dest, "wb") as f:
            f.write(data)
        total += len(data)
    # The gltf refers to "<slug>_<res>.gltf"-relative names only through bin/textures, which keep their names.
    with open(os.path.join(folder, "info.json"), "w") as f:
        json.dump(info(slug), f)
    with open(done, "w") as f:
        f.write("ok")
    if not quiet:
        print("fetched  %-40s %6.1f MB" % (slug, total / 1048576.0))
    return gltf_path


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")        # author names may contain non-ASCII letters
    except Exception:
        pass
    if not argv:
        print(__doc__)
        return 1
    mode = "fetch"
    if argv[0] == "--sizes":
        mode, argv = "sizes", argv[1:]
    elif argv[0] == "--check":
        mode, argv = "check", argv[1:]
    elif argv[0] == "--notice":
        # Markdown table (slug, name, author, link) of every model used by props_spec.py, for NOTICE.md.
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import props_spec
        print("| Poly Haven asset | Name | Author(s) | Licence |")
        print("|---|---|---|---|")
        for slug in props_spec.slugs():
            meta_file = os.path.join(cache_root(), slug, "info.json")
            meta = json.load(open(meta_file)) if os.path.exists(meta_file) else info(slug)
            authors = ", ".join(sorted(meta.get("authors", {}).keys())) or "Poly Haven"
            print("| [%s](https://polyhaven.com/a/%s) | %s | %s | CC0 |" % (slug, slug, meta.get("name", slug), authors))
        return 0
    elif argv[0] == "--all":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import props_spec
        argv = props_spec.slugs()
    failed = []
    total = 0.0
    for slug in argv:
        try:
            if mode == "sizes":
                mb = size_mb(slug)
                total += mb
                print("%-40s %6.1f MB" % (slug, mb))
            elif mode == "check":
                print("%-40s %s" % (slug, "ok" if exists(slug) else "MISSING"))
            else:
                fetch(slug)
        except Exception as e:                      # keep going; report at the end
            failed.append(slug)
            print("FAILED   %s: %s" % (slug, e))
    if mode == "sizes":
        print("total %.1f MB" % total)
    if failed:
        print("failed: " + " ".join(failed))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
