"""Industrial structures for DM-Quarry, built as merged meshes (few actors): walls with openings, halls, silos, conveyors, trusses,
bridges, haul trucks, excavators, drilling rigs, containers. Pure python on top of mapkit_big2.K, plus put_struct() (needs unreal).

A Struct holds one K mesh per (material key, solid). Build in a local frame (u = x, v = y, z up), place with put_struct(x, y, z, yaw, mirror).
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mesh_b as mb  # noqa: E402
from mapkit_big2 import K  # noqa: E402


class Struct:
    def __init__(self, name):
        self.name = name
        self.g = {}

    def k(self, mat, solid=True):
        key = (mat, solid)
        if key not in self.g:
            self.g[key] = K()
        return self.g[key]

    def tris(self):
        return sum(len(k.tris) for k in self.g.values())


def mirror_x(mesh):
    out = K()
    out.verts = [(-v[0], v[1], v[2]) for v in mesh.verts]
    out.norms = [(-n[0], n[1], n[2]) for n in mesh.norms]
    out.tris = [(a, c, b) for (a, b, c) in mesh.tris]
    return out


def put_struct(m, kb, st, x, y, z, yaw, mats, mirror=False, folder="Structures", tag=""):
    """Commits and places every group of a Struct. mats maps material keys to material instances."""
    actors = []
    for (mat, solid), mesh in sorted(st.g.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if not mesh.tris:
            continue
        mm_ = mirror_x(mesh) if mirror else mesh
        name = "Quarry_%s%s_%s_%s" % (st.name, tag, mat, "S" if solid else "D")
        sm = kb.commit(name, mm_, collision="complex" if solid else "none")
        a = kb.put(m, "%s_%s_%s" % (st.name + tag, mat, "S" if solid else "D"), sm, x, y, z, yaw=yaw, mat=mats[mat], solid=solid, folder=folder)
        if not solid:
            try:
                a.static_mesh_component.set_editor_property("cast_shadow", len(mesh.tris) > 400)
            except Exception:                     # noqa: BLE001
                pass
        actors.append(a)
    return actors


# ---------------------------------------------------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------------------------------------------------
def plate(k, pts, thick):
    """A thin plate through four points (any orientation), `thick` cm below the first-face (normal = (p1-p0)x(p3-p0))."""
    p0, p1, p2, p3 = pts
    n = mb.norm(mb.cross(mb.sub(p1, p0), mb.sub(p3, p0)))
    q = [mb.sub(p, mb.mul(n, thick)) for p in pts]
    allp = list(pts) + q
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    k.convex(allp, faces)
    return k


def wall(st, p0, p1, thick, h, openings=(), lo="conc", up="corr", lo_h=260.0, base=-30.0, solid=True, frame="steel", frame_w=26.0):
    """A wall from (x0, y0) to (x1, y1). openings = (s_center, width, z_bottom, z_top) along the wall; a full door has z_bottom 0.
    Lower part in material `lo` up to lo_h, upper part in `up`. Door frames in `frame`."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx))
    c, s = dx / L, dy / L

    def seg(s0, s1, z0, z1, mat, sol=solid):
        if s1 - s0 < 1.0 or z1 - z0 < 1.0:
            return
        mid = (s0 + s1) / 2.0
        k = st.k(mat, sol)
        k.box(p0[0] + c * mid, p0[1] + s * mid, z0, s1 - s0, thick, z1 - z0, yaw=yaw, base=True)

    def band(s0, s1, z0, z1):
        """A vertical slice of wall between z0 and z1, split at lo_h."""
        if z0 < lo_h:
            seg(s0, s1, z0, min(z1, lo_h), lo)
        if z1 > lo_h:
            seg(s0, s1, max(z0, lo_h), z1, up)

    ops = sorted(openings)
    cur = 0.0
    for (sc, w, zb, zt) in ops:
        a, b = sc - w / 2.0, sc + w / 2.0
        band(cur, a, base, h)
        if zb > 0:
            band(a, b, base, zb)
        band(a, b, zt, h)
        if frame:
            # steel frame: jambs and head, slightly proud of the wall
            for sd, pos in ((-1, a), (1, b)):
                k = st.k(frame, False)
                k.box(p0[0] + c * pos, p0[1] + s * pos, zb, frame_w * 0.5, thick + 6.0, zt - zb, yaw=yaw, base=True)
            k = st.k(frame, False)
            k.box(p0[0] + c * sc, p0[1] + s * sc, zt, w + frame_w * 0.5, thick + 6.0, frame_w * 0.6, yaw=yaw, base=True)
        cur = b
    band(cur, L, base, h)


def box(st, mat, cx, cy, z0, sx, sy, sz, yaw=0.0, solid=True):
    st.k(mat, solid).box(cx, cy, z0, sx, sy, sz, yaw=yaw, base=True)


def hcolumn(st, mat, x, y, z0, z1, f=36.0, d=30.0, solid=True):
    k = st.k(mat, solid)
    k.bx(x, y, z0, 5.0, d, z1 - z0)
    for s in (-1, 1):
        k.bx(x, y + s * (d / 2.0 - 2.5), z0, f, 5.0, z1 - z0)


def gable_roof(st, mat, rib, cx, cy, z_eave, L, W, rise, ridge_along_x=True, over=40.0, thick=5.0, trusses=5):
    """Gable roof over L x W with the ridge along x (or y). Two plates plus truss ribs. Non solid."""
    hw = W / 2.0 + over
    hl = L / 2.0 + over
    zr = z_eave + rise * (hw / (W / 2.0))
    k = st.k(mat, False)
    for sgn in (-1, 1):
        if ridge_along_x:
            pts = [(cx - hl, cy + sgn * hw, z_eave - rise * (over / (W / 2.0)) + rise * 0.0), (cx + hl, cy + sgn * hw, z_eave - rise * (over / (W / 2.0))),
                   (cx + hl, cy, z_eave + rise), (cx - hl, cy, z_eave + rise)]
        else:
            pts = [(cx + sgn * hw, cy - hl, z_eave - rise * (over / (W / 2.0))), (cx + sgn * hw, cy + hl, z_eave - rise * (over / (W / 2.0))),
                   (cx, cy + hl, z_eave + rise), (cx, cy - hl, z_eave + rise)]
        if (sgn > 0) == ridge_along_x:
            pts = pts[::-1]
        plate(k, pts if sgn > 0 else pts, thick)
    r = st.k(rib, False)
    for i in range(trusses):
        t = -L / 2.0 + L * (i + 0.5) / trusses
        if ridge_along_x:
            a, b, c_ = (cx + t, cy - W / 2.0, z_eave), (cx + t, cy + W / 2.0, z_eave), (cx + t, cy, z_eave + rise)
            r.beam(a, b, 8.0, 14.0)
            r.beam(a, c_, 8.0, 12.0)
            r.beam(b, c_, 8.0, 12.0)
            r.beam((cx + t, cy, z_eave), c_, 6.0, 8.0)
            r.beam((cx + t, cy - W / 4.0, z_eave), (cx + t, cy, z_eave + rise * 0.5), 5.0, 7.0)
            r.beam((cx + t, cy + W / 4.0, z_eave), (cx + t, cy, z_eave + rise * 0.5), 5.0, 7.0)
        else:
            a, b, c_ = (cx - W / 2.0, cy + t, z_eave), (cx + W / 2.0, cy + t, z_eave), (cx, cy + t, z_eave + rise)
            r.beam(a, b, 8.0, 14.0)
            r.beam(a, c_, 8.0, 12.0)
            r.beam(b, c_, 8.0, 12.0)
            r.beam((cx, cy + t, z_eave), c_, 6.0, 8.0)
    # purlins
    for f in (0.25, 0.5, 0.75):
        for sgn in (-1, 1):
            if ridge_along_x:
                r.beam((cx - L / 2.0, cy + sgn * W / 2.0 * (1 - f), z_eave + rise * f), (cx + L / 2.0, cy + sgn * W / 2.0 * (1 - f), z_eave + rise * f), 6.0, 8.0)


def silo(st, cx, cy, z0, r, h, mat="conc", steel="steel", legs=True, hopper=True, roof=True):
    """Concrete silo: lower hopper cone on four legs, cylinder with form-work rings, conical roof, ladder with cage, gallery."""
    zb = z0 + (240.0 if legs else 0.0)
    k = st.k(mat, True)
    if hopper:
        k.frustum(cx, cy, zb - 160.0, zb, r * 0.22, r, sides=20, cap_top=False, cap_bottom=True)
        k.frustum(cx, cy, zb - 205.0, zb - 160.0, r * 0.12, r * 0.22, sides=12, cap_top=False, cap_bottom=True)
    k.cyl(cx, cy, zb, z0 + h, r, sides=28, cap_top=True, cap_bottom=True)
    if legs:
        for sx in (-1, 1):
            for sy in (-1, 1):
                st.k(mat, True).bx(cx + sx * r * 0.72, cy + sy * r * 0.72, z0, 38.0, 38.0, zb - z0 + 10.0)
        for z in (z0 + 90.0,):
            for sa, sb in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
                st.k(steel, False).beam((cx + sa[0] * r * 0.72, cy + sa[1] * r * 0.72, z), (cx + sb[0] * r * 0.72, cy + sb[1] * r * 0.72, z), 14.0, 14.0)
    d = st.k("conc_dark", False)
    n = int((h - 250) / 220.0)
    for i in range(1, n + 1):
        d.cyl(cx, cy, zb + i * 220.0, zb + i * 220.0 + 14.0, r + 5.0, sides=28, cap_top=False, cap_bottom=False)
    if roof:
        st.k(steel, False).frustum(cx, cy, z0 + h, z0 + h + 110.0, r * 1.02, r * 0.18, sides=28, cap_top=True)
        st.k(steel, False).cyl(cx, cy, z0 + h + 110.0, z0 + h + 160.0, r * 0.18, sides=10)
    # ladder with cage on the side facing +u
    lk = st.k(steel, False)
    lx, ly = cx + r + 6.0, cy
    lk.bx(lx, ly - 22.0, zb - 40.0, 3.0, 3.0, z0 + h - zb + 40.0)
    lk.bx(lx, ly + 22.0, zb - 40.0, 3.0, 3.0, z0 + h - zb + 40.0)
    for z in range(int(zb), int(z0 + h), 30):
        lk.bx(lx, ly, z, 3.0, 44.0, 3.0)
    for z in range(int(zb + 160), int(z0 + h), 90):
        lk.cyl(lx + 10.0, ly, z, z + 3.0, 36.0, sides=10, cap_top=False)


def conveyor(st, p0, p1, w=70.0, steel="steel", belt="belt", hood=False, supports=True, every=520.0, solid=False, rollers=True):
    """An inclined belt conveyor gantry between two points: side plates, belt, rollers, hood, A-frame trestles to the ground."""
    d = mb.sub(p1, p0)
    L = math.sqrt(mb.dot(d, d))
    dn = mb.mul(d, 1.0 / L)
    flat = math.hypot(dn[0], dn[1])
    s = (-dn[1] / flat, dn[0] / flat, 0.0) if flat > 1e-6 else (1.0, 0.0, 0.0)
    k = st.k(steel, solid)
    for sd in (-1, 1):
        off = (s[0] * sd * w / 2.0, s[1] * sd * w / 2.0, 0.0)
        k.beam(mb.add(p0, off), mb.add(p1, off), 6.0, 36.0)
    st.k(belt, False).beam(mb.add(p0, (0, 0, 12.0)), mb.add(p1, (0, 0, 12.0)), w - 10.0, 6.0)
    if rollers:
        n = int(L / 90.0)
        rk = st.k(steel, False)
        for i in range(1, n):
            q = mb.add(p0, mb.mul(d, i / float(n)))
            rk.beam(mb.add(q, (s[0] * (w / 2.0 - 3.0), s[1] * (w / 2.0 - 3.0), 4.0)), mb.add(q, (-s[0] * (w / 2.0 - 3.0), -s[1] * (w / 2.0 - 3.0), 4.0)), 7.0, 7.0)
    if hood:
        hk = st.k(steel, False)
        hk.beam(mb.add(p0, (0, 0, 70.0)), mb.add(p1, (0, 0, 70.0)), w + 12.0, 5.0)
        for sd in (-1, 1):
            off = (s[0] * sd * (w / 2.0 + 4.0), s[1] * sd * (w / 2.0 + 4.0), 0.0)
            hk.beam(mb.add(p0, mb.add(off, (0, 0, 40.0))), mb.add(p1, mb.add(off, (0, 0, 40.0))), 4.0, 60.0)
    if supports:
        n = max(1, int(L / every))
        sk = st.k(steel, solid)
        for i in range(n + 1):
            q = mb.add(p0, mb.mul(d, i / float(n)))
            if q[2] < 30.0:
                continue
            for sd in (-1, 1):
                foot = (q[0] + s[0] * sd * (w / 2.0 + 55.0), q[1] + s[1] * sd * (w / 2.0 + 55.0), 0.0)
                sk.beam(foot, (q[0] + s[0] * sd * w / 2.0, q[1] + s[1] * sd * w / 2.0, q[2] - 18.0), 12.0, 12.0)
            if q[2] > 160.0:
                sk.beam((q[0] + s[0] * (w / 2.0), q[1] + s[1] * (w / 2.0), q[2] - 18.0), (q[0] - s[0] * (w / 2.0), q[1] - s[1] * (w / 2.0), q[2] - 18.0), 10.0, 10.0)


def container(st, mat, x, y, z0, yaw=0.0, length=600.0, width=240.0, height=250.0, steel="steel", doors=1, solid=True):
    k = st.k(mat, solid)
    k.box(x, y, z0, length, width, height, yaw=yaw, base=True)
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    sk = st.k(steel, False)
    hl, hw = length / 2.0, width / 2.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            sk.box(x + c * sx * (hl - 6) - s * sy * (hw + 1), y + s * sx * (hl - 6) + c * sy * (hw + 1), z0, 12.0, 12.0, height + 2, yaw=yaw, base=True)
    # corrugation ribs along the long sides
    n = int(length / 40.0)
    for i in range(1, n):
        t = -hl + length * i / n
        for sy in (-1, 1):
            sk.box(x + c * t - s * sy * (hw + 1.5), y + s * t + c * sy * (hw + 1.5), z0 + 10.0, 7.0, 3.0, height - 20.0, yaw=yaw, base=True)
    for sy in (-1, 1):
        for zz in (z0, z0 + height - 8.0):
            sk.box(x - s * sy * (hw + 1), y + c * sy * (hw + 1), zz, length, 6.0, 8.0, yaw=yaw, base=True)
    if doors:
        e = doors
        ex, ey = x + c * e * (hl + 1.5), y + s * e * (hl + 1.5)
        for kk in (-0.55, -0.18, 0.18, 0.55):
            sk.box(ex - s * kk * hw, ey + c * kk * hw, z0 + 10.0, 3.0, 5.0, height - 22.0, yaw=yaw, base=True)
        sk.box(ex, ey, z0 + height * 0.5, 4.0, width - 16.0, 6.0, yaw=yaw, base=True)


def wheel(st, mat_tire, mat_hub, cx, cy, cz, r, width, axis="y", sides=20):
    """A tyre (cylinder lying along `axis`) with a hub. Built by a lathe rotated about x or y."""
    t = K()
    t.lathe(0, 0, -width / 2.0, width / 2.0, r, r, sides=sides, segments=1, cap_top=True, cap_bottom=True)
    h = K()
    h.lathe(0, 0, -width / 2.0 - 3.0, width / 2.0 + 3.0, r * 0.48, r * 0.48, sides=sides, segments=1, cap_top=True, cap_bottom=True)
    for src, dst in ((t, st.k(mat_tire, True)), (h, st.k(mat_hub, True))):
        for v, n in zip(src.verts, src.norms):
            # lathe axis is z; turn it so the axis becomes y: (x, y, z) -> (x, z, -y)
            dst_v = (v[0] + cx, v[2] + cy, -v[1] + cz)
            dst.verts.append(dst_v)
            dst.norms.append((n[0], n[2], -n[1]))
        base = len(dst.verts) - len(src.verts)
        for (a, b, c) in src.tris:
            dst.tris.append((a + base, b + base, c + base))


def haul_truck(st, paint="paint_y", steel="steel", tire="tire", dark="dark", x=0.0, y=0.0, yaw=0.0, scale=1.0, loaded=False):
    """A rigid dump truck about 1000 x 560 x 560 cm (scale 1). Built in a local frame, then rotated/offset into st."""
    t = Struct("tmp")
    s = scale
    # chassis rails and axles
    k = t.k(steel, True)
    k.bx(0, -120 * s, 60 * s, 900 * s, 40 * s, 70 * s)
    k.bx(0, 120 * s, 60 * s, 900 * s, 40 * s, 70 * s)
    k.bx(-300 * s, 0, 70 * s, 50 * s, 330 * s, 50 * s)
    k.bx(260 * s, 0, 70 * s, 50 * s, 330 * s, 50 * s)
    # dump body: a deep box with a raked front and a canopy over the cab
    b = t.k(paint, True)
    b.bx(-60 * s, 0, 130 * s, 640 * s, 470 * s, 40 * s)
    for sy in (-1, 1):
        b.bx(-60 * s, sy * 225 * s, 130 * s, 640 * s, 22 * s, 260 * s)
    b.bx(-370 * s, 0, 130 * s, 30 * s, 470 * s, 260 * s)
    b.beam((250 * s, 0, 130 * s), (250 * s, 0, 130 * s), 1, 1)
    # raked front plate (a sloped slab) and canopy
    plate(b, [(260 * s, -235 * s, 130 * s), (260 * s, 235 * s, 130 * s), (180 * s, 235 * s, 400 * s), (180 * s, -235 * s, 400 * s)], 18 * s)
    b.bx(-80 * s, 0, 390 * s, 560 * s, 470 * s, 18 * s) if False else None
    can = t.k(paint, False)
    plate(can, [(300 * s, -250 * s, 360 * s), (300 * s, 250 * s, 360 * s), (60 * s, 250 * s, 470 * s), (60 * s, -250 * s, 470 * s)][::-1], 14 * s)
    # cab (left front), engine hood, ladder
    cab = t.k(paint, True)
    cab.bx(330 * s, -140 * s, 120 * s, 170 * s, 170 * s, 230 * s)
    cab.bx(380 * s, 0, 110 * s, 200 * s, 300 * s, 150 * s)
    gl = t.k(dark, False)
    gl.bx(412 * s, -140 * s, 230 * s, 4 * s, 150 * s, 100 * s)
    gl.bx(330 * s, -226 * s, 230 * s, 150 * s, 4 * s, 100 * s)
    # exhaust stack, grille, steps
    st_k = t.k(steel, False)
    st_k.cyl(420 * s, 120 * s, 260 * s, 380 * s, 8 * s, sides=8)
    st_k.bx(481 * s, 0, 120 * s, 6 * s, 240 * s, 110 * s)
    for i in range(4):
        st_k.bx(460 * s, -240 * s, 50 * s + i * 45 * s, 40 * s, 36 * s, 6 * s)
    # wheels: front pair and rear pair (the rear is a twin)
    for sy in (-1, 1):
        wheel(t, tire, steel, 300 * s, sy * 255 * s, 120 * s, 120 * s, 100 * s)
        for dy in (0, 1):
            wheel(t, tire, steel, -300 * s, sy * (250 + dy * 85) * s, 120 * s, 120 * s, 80 * s)
    if loaded:
        rk = t.k("ore", False)
        rk.blob(-60 * s, 0, 215 * s, 270 * s, 205 * s, 110 * s, seed=3, amp=0.18, flat_bottom=0.1)
    # copy into st with rotation and offset
    c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for (mat, solid), mesh in t.g.items():
        dst = st.k(mat, solid)
        base = len(dst.verts)
        for v, n in zip(mesh.verts, mesh.norms):
            dst.verts.append((x + v[0] * c - v[1] * sn, y + v[0] * sn + v[1] * c, v[2]))
            dst.norms.append((n[0] * c - n[1] * sn, n[0] * sn + n[1] * c, n[2]))
        for (a, b_, c_) in mesh.tris:
            dst.tris.append((a + base, b_ + base, c_ + base))


def girder_bridge(st, x0, y0, x1, y1, z0, z1, width, deck="plate", steel="steel", yellow="yellow", rail_h=105.0, truss_h=300.0, panels=None, belt=True):
    """A deck truss bridge from (x0, y0, z0) to (x1, y1, z1): two Warren trusses, cross beams, a diamond plate deck, handrails inside the
    trusses and a covered conveyor along one side. Solid: the deck. Returns the deck centre line length."""
    d = (x1 - x0, y1 - y0, z1 - z0)
    L = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    flat = math.hypot(d[0], d[1])
    dn = (d[0] / L, d[1] / L, d[2] / L)
    s = (-d[1] / flat, d[0] / flat, 0.0)
    panels = panels or max(4, int(L / 220.0))
    dk = st.k(deck, True)
    pts = [(x0 + s[0] * width / 2, y0 + s[1] * width / 2, z0), (x1 + s[0] * width / 2, y1 + s[1] * width / 2, z1),
           (x1 - s[0] * width / 2, y1 - s[1] * width / 2, z1), (x0 - s[0] * width / 2, y0 - s[1] * width / 2, z0)]
    # deck slab as a plate whose top is the walking surface (normal up)
    pl = pts if mb.cross(mb.sub(pts[1], pts[0]), mb.sub(pts[3], pts[0]))[2] > 0 else pts[::-1]
    plate(dk, pl, 14.0)
    sk = st.k(steel, False)
    bk = st.k(steel, True)
    for sd in (-1, 1):
        a = (x0 + s[0] * sd * (width / 2 + 6), y0 + s[1] * sd * (width / 2 + 6), z0 - 14.0)
        b = (x1 + s[0] * sd * (width / 2 + 6), y1 + s[1] * sd * (width / 2 + 6), z1 - 14.0)
        sk.truss(a, b, truss_h + 14.0, panels, chord=16.0, web=9.0, width=12.0)
        # cheek plate under the deck edge
        bk.beam(a, b, 10.0, 46.0)
    # cross beams and under-bracing
    n = int(L / 110.0)
    for i in range(n + 1):
        f = i / float(n)
        c0 = (x0 + d[0] * f, y0 + d[1] * f, z0 + d[2] * f - 14.0)
        sk.beam((c0[0] + s[0] * width / 2, c0[1] + s[1] * width / 2, c0[2] - 10.0), (c0[0] - s[0] * width / 2, c0[1] - s[1] * width / 2, c0[2] - 10.0), 8.0, 20.0)
    # handrails along both edges, on top of the deck
    for sd in (-1, 1):
        a = (x0 + s[0] * sd * (width / 2 - 8), y0 + s[1] * sd * (width / 2 - 8), z0)
        b = (x1 + s[0] * sd * (width / 2 - 8), y1 + s[1] * sd * (width / 2 - 8), z1)
        st.k(yellow, False).rail(a, b, h=rail_h, every=220.0, w=4.0, toe=0.0)
    return L


def tower_legs(st, x, y, z_top, ground_z, w, steel="steel", leg=16.0):
    k = st.k(steel, False)
    k.lattice_tower(x, y, ground_z - 20.0, z_top, w * 1.9, w, leg=leg)
    # foot blocks
    st.k("conc", True).bx(x, y, ground_z - 30.0, w * 1.9 + 40.0, w * 1.9 + 40.0, 40.0)
