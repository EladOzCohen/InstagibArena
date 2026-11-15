"""Tiny software renderer for character gear (pure python, no unreal): orthographic views of the mannequin plus gear, written as PNG.
Used to check how pieces fit the body before a slow engine run.

    python -I Tools/preview_char.py <char index> [views...]      views: front side back q34 (default: front side back)
Writes <AssetCache>/char_probe/prev_<name>_<view>.png and prev_<name>_all.png (a row of views).
Needs the body dump made by Tools/probe_mannequin.py.
"""

import json
import math
import os
import struct
import sys
import zlib

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import mesh_char as mc  # noqa: E402

PROBE = os.path.join(os.path.expanduser("~"), "AssetCache", "char_probe")

ROLE_RGB = {
    mc.R_PLATE: (0.55, 0.57, 0.62), mc.R_CLOTH: (0.30, 0.34, 0.26), mc.R_ACCENT: (0.9, 0.55, 0.1), mc.R_TEAM: (0.9, 0.1, 0.1),
    mc.R_TRIM: (0.12, 0.12, 0.14), mc.R_GLOW: (0.2, 1.0, 1.0), mc.R_LIGHT: (0.85, 0.85, 0.8),
}


def write_png(path, w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(rgb[y * w * 3:(y + 1) * w * 3])
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def load_body(quinn=False):
    """The mannequin, decimated by vertex clustering (cached as <name>_body_lo.json)."""
    name = "quinn" if quinn else "manny"
    lo = os.path.join(PROBE, name + "_body_lo.json")
    if not os.path.exists(lo):
        with open(os.path.join(PROBE, name + "_body.json")) as f:
            d = json.load(f)
        V = d["v"]
        cell = 1.4
        m, newv, remap = {}, [], []
        for p in V:
            k = (round(p[0] / cell), round(p[1] / cell), round(p[2] / cell))
            if k not in m:
                m[k] = len(newv)
                newv.append([0.0, 0.0, 0.0, 0])
            i = m[k]
            for a in range(3):
                newv[i][a] += p[a]
            newv[i][3] += 1
            remap.append(i)
        nv = [[x[0] / x[3], x[1] / x[3], x[2] / x[3]] for x in newv]
        tris = set()
        for a, b, c in d["t"]:
            a, b, c = remap[a], remap[b], remap[c]
            if a != b and b != c and a != c:
                tris.add((a, b, c))
        with open(lo, "w") as f:
            json.dump({"v": nv, "t": [list(t) for t in tris]}, f)
    with open(lo) as f:
        d = json.load(f)
    g = mc.GM()
    g.v = [tuple(p) for p in d["v"]]
    g.t = [tuple(t) for t in d["t"]]
    acc = [(0.0, 0.0, 0.0)] * len(g.v)
    for a, b, c in g.t:
        n = mc.cross(mc.sub(g.v[b], g.v[a]), mc.sub(g.v[c], g.v[a]))
        for i in (a, b, c):
            acc[i] = mc.add(acc[i], n)
    # the engine's triangle order is the opposite of ours: flip so that normals point out
    g.n = [mc.mul(mc.norm(a), -1.0) for a in acc]
    g.t = [(a, c, b) for (a, b, c) in g.t]
    g.uv = [(0, 0)] * len(g.v)
    g.role = [7] * len(g.v)
    g.ao = [1.0] * len(g.v)
    return g


def render(meshes, palettes, view_yaw, scale=3.0, w=360, h=620, zmin=-5.0, zmax=200.0, cx=0.0, light=(0.5, 0.6, 0.8)):
    """meshes: list of (GM, scale_about_origin, offset) already placed in character space. palettes: list of role->rgb dicts."""
    c = (math.cos(math.radians(view_yaw)), math.sin(math.radians(view_yaw)), 0.0)
    right = (c[1], -c[0], 0.0)
    up = (0.0, 0.0, 1.0)
    ldir = mc.norm(add3(add3(mc.mul(right, -light[0]), mc.mul(up, light[1])), mc.mul(c, light[2])))
    color = bytearray([226, 230, 236] * (w * h))
    depth = [-1e9] * (w * h)
    for mesh, pal in zip(meshes, palettes):
        P = []
        for p in mesh.v:
            sx = (mc.dot(p, right) - cx) * scale + w / 2.0
            sy = h - 8 - (p[2] - zmin) * scale
            P.append((sx, sy, mc.dot(p, c)))
        for (a, b, cc) in mesh.t:
            pa, pb, pc = P[a], P[b], P[cc]
            minx = max(0, int(min(pa[0], pb[0], pc[0])))
            maxx = min(w - 1, int(max(pa[0], pb[0], pc[0])) + 1)
            miny = max(0, int(min(pa[1], pb[1], pc[1])))
            maxy = min(h - 1, int(max(pa[1], pb[1], pc[1])) + 1)
            if minx > maxx or miny > maxy:
                continue
            den = (pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1])
            if abs(den) < 1e-9:
                continue
            n = mc.norm(add3(add3(mesh.n[a], mesh.n[b]), mesh.n[cc]))
            # back-face cull in view space
            if mc.dot(n, c) < -0.05:
                continue
            lam = max(0.0, mc.dot(n, ldir))
            shade = 0.38 + 0.72 * lam
            role = mesh.role[a]
            base = pal.get(role, (0.5, 0.5, 0.5))
            ao = (mesh.ao[a] + mesh.ao[b] + mesh.ao[cc]) / 3.0
            col = tuple(int(min(1.0, (base[k] ** 0.8) * shade * (0.55 + 0.45 * ao)) * 255) for k in range(3))
            inv = 1.0 / den
            for y in range(miny, maxy + 1):
                for x in range(minx, maxx + 1):
                    l1 = ((pb[1] - pc[1]) * (x + 0.5 - pc[0]) + (pc[0] - pb[0]) * (y + 0.5 - pc[1])) * inv
                    l2 = ((pc[1] - pa[1]) * (x + 0.5 - pc[0]) + (pa[0] - pc[0]) * (y + 0.5 - pc[1])) * inv
                    l3 = 1.0 - l1 - l2
                    if l1 < -0.02 or l2 < -0.02 or l3 < -0.02:
                        continue
                    z = l1 * pa[2] + l2 * pb[2] + l3 * pc[2]
                    i = y * w + x
                    if z > depth[i]:
                        depth[i] = z
                        color[i * 3:i * 3 + 3] = bytes(col)
    return w, h, color


def add3(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def hstack(images):
    h = max(i[1] for i in images)
    w = sum(i[0] for i in images)
    out = bytearray([226, 230, 236] * (w * h))
    x0 = 0
    for (iw, ih, col) in images:
        for y in range(ih):
            out[(y * w + x0) * 3:(y * w + x0 + iw) * 3] = col[y * iw * 3:(y + 1) * iw * 3]
        x0 += iw
    return w, h, out


def ruler(img, scale=3.0, zmin=-5.0):
    w, h, col = img
    for z in range(0, 200, 10):
        y = int(h - 8 - (z - zmin) * scale)
        ln = 14 if z % 50 == 0 else 6
        if 0 <= y < h:
            for x in range(ln):
                col[(y * w + x) * 3:(y * w + x) * 3 + 3] = bytes((200, 40, 40) if z % 50 == 0 else (120, 120, 130))
    return img


def sheet(pieces, palette, path, quinn=False, views=(0, 90, 180, 45), bodypal=(0.42, 0.44, 0.48), with_body=True, scale=3.0):
    """pieces: list of GM in character space. Writes one PNG with the requested view yaws side by side."""
    meshes = list(pieces)
    pals = [palette] * len(pieces)
    if with_body:
        meshes = [load_body(quinn)] + meshes
        pals = [{7: bodypal}] + pals
    imgs = [ruler(render(meshes, pals, yaw, scale=scale), scale) for yaw in views]
    w, h, col = hstack(imgs)
    write_png(path, w, h, col)
