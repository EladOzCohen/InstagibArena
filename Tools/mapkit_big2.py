"""Helpers for the big maps of BIG2 (DM-Quarry): terrain and tunnel meshes from the pure python height function, plus a mesh kit
for steel structures (beams, rails, stairs, tanks ...). Pure python except for the thin wrappers at the end.

  build_terrain(g)        {(tile_x, tile_y, material key): Mesh}  terrain tiles split by material (strata bands on steep faces)
  build_tunnels(g)        {part: Mesh}  floor / walls / ceiling of the underground corridors (holes are cut by build_terrain)
  K                       mesh kit: K().beam(p0, p1, w, h), .rail, .stairs, .cyl, .frustum, .truss ... (local coordinates)
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quarry_terrain as qt  # noqa: E402
import mesh_b as mb  # noqa: E402
from mesh_b import Mesh, fbm, vnoise, norm, cross, sub, add, mul, dot  # noqa: E402

# ---- strata: beds of random thickness that dip a little (planar boundaries f = z - dip(x, y) = const); triangles of steep faces
# are clipped against them so that every band is a clean piece of one rock material
def _make_beds():
    r = random.Random(77)
    bounds, mats = [], []
    f = -6000.0
    last = None
    pool = ["red"] * 4 + ["pale"] * 3 + ["cliff"] * 3 + ["dark"] * 2
    while f < 6000.0:
        t = r.choice((70.0, 90.0, 110.0, 140.0, 170.0, 210.0, 260.0))
        bounds.append(f)
        m_ = r.choice(pool)
        while m_ == last:
            m_ = r.choice(pool)
        mats.append(m_)
        last = m_
        f += t
    bounds.append(f)
    return bounds, mats


BEDS, BED_MATS = _make_beds()


def bed_f(x, y, z):
    return z - 0.028 * (x * 0.8 + y * 0.6)


def _clip(poly, lo, hi):
    """Sutherland-Hodgman against lo <= bed_f <= hi; poly = list of (pos, normal)."""
    def clip_one(pts, side):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            fa = bed_f(*a[0]) - lo if side == 0 else hi - bed_f(*a[0])
            fb = bed_f(*b[0]) - lo if side == 0 else hi - bed_f(*b[0])
            if fa >= 0:
                out.append(a)
            if (fa >= 0) != (fb >= 0):
                t = fa / (fa - fb)
                pos = tuple(a[0][c] + (b[0][c] - a[0][c]) * t for c in range(3))
                nr = tuple(a[1][c] + (b[1][c] - a[1][c]) * t for c in range(3))
                out.append((pos, nr))
        return out
    pts = clip_one(poly, 0)
    if len(pts) >= 3:
        pts = clip_one(pts, 1)
    return pts


def _bisect(arr, v):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < v:
            lo = mid + 1
        else:
            hi = mid
    return lo


def classify(g, x, y, z, nz, road_w, heap_kind):
    """Material key of a (not steep) terrain triangle."""
    if heap_kind:
        return "heap_" + heap_kind
    if road_w > 0.92 and z > qt.ZF + 20.0:
        return "road"
    n = fbm(x / 700.0, y / 700.0, 8.0, 2, 35)
    if z < qt.ZF - 25.0:
        return "bed"
    if z < qt.ZF + 60.0:
        return "floor" if n > -0.2 else "floor2"
    if z < -60.0:
        return "gravel" if n > -0.1 else "rubble"
    if abs(x) > qt.PX or abs(y) > qt.PY:
        return "rubble"
    return "plateau" if n > -0.15 else "plateau2"


def build_terrain(g, tiles=(4, 3)):
    nx, ny = g.nx, g.ny
    tw, th = nx // tiles[0], ny // tiles[1]
    out = {}
    verts = {}
    for ti in range(tiles[0]):
        for tj in range(tiles[1]):
            i0, i1 = ti * tw, (ti + 1) * tw if ti < tiles[0] - 1 else nx
            j0, j1 = tj * th, (tj + 1) * th if tj < tiles[1] - 1 else ny
            for i in range(i0, i1):
                for j in range(j0, j1):
                    cx, cy = g.x(i) + qt.GRID / 2.0, g.y(j) + qt.GRID / 2.0
                    if qt.tunnel_cell(cx, cy) and qt.cell_open(g, i, j):
                        continue
                    h00, h10, h01, h11 = g.at(i, j), g.at(i + 1, j), g.at(i, j + 1), g.at(i + 1, j + 1)
                    if abs(h00 - h11) <= abs(h10 - h01):
                        tris = (((i, j), (i + 1, j), (i + 1, j + 1)), ((i, j), (i + 1, j + 1), (i, j + 1)))
                    else:
                        tris = (((i, j), (i + 1, j), (i, j + 1)), ((i + 1, j), (i + 1, j + 1), (i, j + 1)))
                    for tri in tris:
                        pts = [(g.x(a), g.y(b), g.at(a, b)) for a, b in tri]
                        n = norm(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])))
                        if n[2] < 0:
                            n = (-n[0], -n[1], -n[2])
                            tri = (tri[0], tri[2], tri[1])
                            pts = [pts[0], pts[2], pts[1]]
                        gx = sum(p[0] for p in pts) / 3.0
                        gy = sum(p[1] for p in pts) / 3.0
                        gz = sum(p[2] for p in pts) / 3.0
                        if n[2] < 0.70:
                            poly = [(pts[k], g.normal(tri[k][0], tri[k][1])) for k in range(3)]
                            fs = [bed_f(*p[0]) for p in poly]
                            klo = max(0, _bisect(BEDS, min(fs)) - 1)
                            for k in range(klo, len(BEDS) - 1):
                                if BEDS[k] > max(fs):
                                    break
                                piece = _clip(poly, BEDS[k], BEDS[k + 1])
                                if len(piece) < 3:
                                    continue
                                mkey = (ti, tj, BED_MATS[k])
                                m = out.get(mkey)
                                if m is None:
                                    m = out[mkey] = Mesh()
                                base = len(m.verts)
                                for pos, nr in piece:
                                    m.verts.append(pos)
                                    l = math.sqrt(dot(nr, nr)) or 1.0
                                    m.norms.append((nr[0] / l, nr[1] / l, nr[2] / l))
                                for q in range(1, len(piece) - 1):
                                    cr = cross(sub(piece[q][0], piece[0][0]), sub(piece[q + 1][0], piece[0][0]))
                                    if dot(cr, cr) < 1e-3:
                                        continue
                                    m.tris.append((base, base + q, base + q + 1))
                            continue
                        rw, _, _ = qt.road_blend(gx, gy)
                        hv, hk = qt.heap_height(gx, gy)
                        key = classify(g, gx, gy, gz, n[2], rw, hk if hv > 8.0 else None)
                        k = (ti, tj, key)
                        m = out.get(k)
                        if m is None:
                            m = out[k] = Mesh()
                            verts[k] = {}
                        vm = verts[k]
                        idx = []
                        for (a, b) in tri:
                            v = vm.get((a, b))
                            if v is None:
                                v = len(m.verts)
                                vm[(a, b)] = v
                                m.verts.append((g.x(a), g.y(b), g.at(a, b)))
                                m.norms.append(g.normal(a, b))
                            idx.append(v)
                        m.tris.append(tuple(idx))
    return out


def build_tunnels(g):
    """Floors, walls and ceilings of the corridors. Wall and fascia heights follow the terrain at open cells."""
    floor, walls, ceil = Mesh(), Mesh(), Mesh()
    cells = set()
    opens = {}
    for i in range(g.nx):
        for j in range(g.ny):
            cx, cy = g.x(i) + qt.GRID / 2.0, g.y(j) + qt.GRID / 2.0
            if abs(cx) < 6000 and cy < -1500 and qt.tunnel_cell(cx, cy):
                cells.add((i, j))
                opens[(i, j)] = qt.cell_open(g, i, j)
    G = qt.GRID

    def fz(x, y):
        return qt.tunnel_floor(x, y)

    for (i, j) in cells:
        x0, y0 = g.x(i), g.y(j)
        x1, y1 = x0 + G, y0 + G
        zf = [fz(x0, y0), fz(x1, y0), fz(x1, y1), fz(x0, y1)]
        floor.poly([(x0, y0, zf[0]), (x1, y0, zf[1]), (x1, y1, zf[2]), (x0, y1, zf[3])], (0, 0, 1))
        op = opens[(i, j)]
        if not op:
            zc = [z + qt.TH for z in zf]
            ceil.poly([(x0, y0, zc[0]), (x1, y0, zc[1]), (x1, y1, zc[2]), (x0, y1, zc[3])], (0, 0, -1))
        # four edges: (neighbour cell, edge points a->b, direction from neighbour into this cell)
        for (di, dj, ea, eb, hint) in (
                (-1, 0, (x0, y0), (x0, y1), (1, 0, 0)), (1, 0, (x1, y0), (x1, y1), (-1, 0, 0)),
                (0, -1, (x0, y0), (x1, y0), (0, 1, 0)), (0, 1, (x0, y1), (x1, y1), (0, -1, 0))):
            nb = (i + di, j + dj)
            if nb in cells:
                # fascia between a covered cell and an open neighbour
                if not op and opens[nb]:
                    for p, q in ((ea, eb),):
                        ha = g.at(int(round((p[0] - qt.X0) / G)), int(round((p[1] - qt.Y0) / G)))
                        hb = g.at(int(round((q[0] - qt.X0) / G)), int(round((q[1] - qt.Y0) / G)))
                        za, zb = fz(*p) + qt.TH, fz(*q) + qt.TH
                        if ha > za + 1 or hb > zb + 1:
                            walls.poly([(p[0], p[1], za), (q[0], q[1], zb), (q[0], q[1], max(hb, zb + 2)), (p[0], p[1], max(ha, za + 2))],
                                       (-hint[0], -hint[1], 0))
                continue
            za_f, zb_f = fz(*ea), fz(*eb)
            if op:
                ha = g.at(int(round((ea[0] - qt.X0) / G)), int(round((ea[1] - qt.Y0) / G)))
                hb = g.at(int(round((eb[0] - qt.X0) / G)), int(round((eb[1] - qt.Y0) / G)))
                ta, tb = max(ha, za_f), max(hb, zb_f)
            else:
                ta, tb = za_f + qt.TH, zb_f + qt.TH
            if ta - za_f < 0.5 and tb - zb_f < 0.5:
                continue
            walls.poly([(ea[0], ea[1], za_f), (eb[0], eb[1], zb_f), (eb[0], eb[1], tb), (ea[0], ea[1], ta)], hint)
    return {"floor": floor, "walls": walls, "ceil": ceil}


# =====================================================================================================================
# Mesh kit for structures
# =====================================================================================================================
class K(Mesh):
    """A Mesh with helpers for built things. Everything is in the local frame of the structure (x, y, z in cm)."""

    def bx(self, cx, cy, z0, sx, sy, sz, yaw=0.0, pitch=0.0, roll=0.0):
        """Box with its bottom at z0."""
        self.box(cx, cy, z0, sx, sy, sz, yaw=yaw, pitch=pitch, roll=roll, base=True)
        return self

    def bc(self, cx, cy, cz, sx, sy, sz, yaw=0.0):
        self.box(cx, cy, cz, sx, sy, sz, yaw=yaw)
        return self

    def beam(self, p0, p1, w, h, up=(0.0, 0.0, 1.0)):
        """Box whose long axis runs from p0 to p1, w wide (horizontal) and h high (vertical for horizontal beams)."""
        d = sub(p1, p0)
        l = math.sqrt(dot(d, d))
        if l < 0.5:
            return self
        dn = mul(d, 1.0 / l)
        s = cross(up, dn)
        if dot(s, s) < 1e-6:
            s = (1.0, 0.0, 0.0)
        s = norm(s)
        u = norm(cross(dn, s))
        pts = []
        for a in (p0, p1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    pts.append((a[0] + s[0] * sy * w / 2.0 + u[0] * sz * h / 2.0, a[1] + s[1] * sy * w / 2.0 + u[1] * sz * h / 2.0,
                                a[2] + s[2] * sy * w / 2.0 + u[2] * sz * h / 2.0))
        # index = a*4 + sy*2 + sz  (a: 0 start 1 end)
        faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
        self.convex(pts, faces, center=mul(add(p0, p1), 0.5))
        return self

    def ibeam(self, p0, p1, depth=40.0, flange=26.0, tf=4.0, tw=3.0):
        self.beam(p0, p1, tw, depth - 2 * tf)
        for s in (-1, 1):
            off = (0, 0, s * (depth / 2.0 - tf / 2.0))
            self.beam(add(p0, off), add(p1, off), flange, tf)
        return self

    def cyl(self, cx, cy, z0, z1, r, sides=16, cap_top=True, cap_bottom=False):
        self.lathe(cx, cy, z0, z1, r, r, sides=sides, segments=1, cap_top=cap_top, cap_bottom=cap_bottom)
        return self

    def frustum(self, cx, cy, z0, z1, r0, r1, sides=16, cap_top=False, cap_bottom=False):
        self.lathe(cx, cy, z0, z1, r0, r1, sides=sides, segments=1, cap_top=cap_top, cap_bottom=cap_bottom)
        return self

    def pipe(self, p0, p1, r, sides=8):
        """A round pipe between two points (capped ends)."""
        d = sub(p1, p0)
        l = math.sqrt(dot(d, d))
        if l < 0.5:
            return self
        dn = mul(d, 1.0 / l)
        up = (0.0, 0.0, 1.0) if abs(dn[2]) < 0.95 else (1.0, 0.0, 0.0)
        s = norm(cross(up, dn))
        u = norm(cross(dn, s))

        def P(i, j):
            th = 2 * math.pi * i / sides
            c = (p0 if j == 0 else p1)
            return (c[0] + (s[0] * math.cos(th) + u[0] * math.sin(th)) * r, c[1] + (s[1] * math.cos(th) + u[1] * math.sin(th)) * r,
                    c[2] + (s[2] * math.cos(th) + u[2] * math.sin(th)) * r)
        self.grid(sides, 2, P, wrap_u=True, flip=True)
        for c, nrm in ((p0, mul(dn, -1.0)), (p1, dn)):
            ring = [(c[0] + (s[0] * math.cos(2 * math.pi * i / sides) + u[0] * math.sin(2 * math.pi * i / sides)) * r,
                     c[1] + (s[1] * math.cos(2 * math.pi * i / sides) + u[1] * math.sin(2 * math.pi * i / sides)) * r,
                     c[2] + (s[2] * math.cos(2 * math.pi * i / sides) + u[2] * math.sin(2 * math.pi * i / sides)) * r) for i in range(sides)]
            self.poly(ring, nrm)
        return self

    def post(self, x, y, z0, z1, w=8.0):
        return self.bx(x, y, z0, w, w, z1 - z0)

    def rail(self, p0, p1, h=105.0, every=200.0, w=4.0, mid=True, toe=0.0):
        """Handrail from deck point p0 to deck point p1 (posts + top rail + mid rail)."""
        d = sub(p1, p0)
        l = math.sqrt(dot(d, d))
        n = max(1, int(math.ceil(l / every)))
        for i in range(n + 1):
            f = i / float(n)
            p = add(p0, mul(d, f))
            self.bx(p[0], p[1], p[2], w, w, h)
        self.beam(add(p0, (0, 0, h)), add(p1, (0, 0, h)), w * 1.3, w * 1.3)
        if mid:
            self.beam(add(p0, (0, 0, h * 0.5)), add(p1, (0, 0, h * 0.5)), w * 0.9, w * 0.9)
        if toe > 0:
            self.beam(add(p0, (0, 0, toe / 2.0)), add(p1, (0, 0, toe / 2.0)), 2.0, toe)
        return self

    def stairs(self, x0, y0, z0, x1, y1, z1, width, tread=26.0, stringers=True, riser_closed=False):
        """Stairs from the foot point (x0, y0, z0) up to the top point (x1, y1, z1), `width` wide. Each step is a floating tread plus
        two stringers (solid enough to walk on; every step is a box from the stringer line up)."""
        dx, dy = x1 - x0, y1 - y0
        run = math.hypot(dx, dy)
        yaw = math.degrees(math.atan2(dy, dx))
        n = max(2, int(round((z1 - z0) / 19.0)))
        rise = (z1 - z0) / n
        step = run / n
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for i in range(n):
            d = (i + 0.5) * step
            top = z0 + (i + 1) * rise
            if riser_closed:
                self.box(x0 + c * d, y0 + s * d, z0, step + 0.4, width, top - z0, yaw=yaw, base=True)
            else:
                self.box(x0 + c * d, y0 + s * d, top - 5.0, step + 0.4, width, 5.0, yaw=yaw, base=True)
        if stringers and not riser_closed:
            for sd in (-1, 1):
                ox, oy = -s * sd * (width / 2.0 - 3.0), c * sd * (width / 2.0 - 3.0)
                p0 = (x0 + ox, y0 + oy, z0 + 2.0)
                p1 = (x1 + ox, y1 + oy, z1 - 3.0)
                self.beam(p0, p1, 6.0, 26.0)
        return self

    def truss(self, p0, p1, height, panels, chord=10.0, web=6.0, width=10.0):
        """A Warren truss with vertical posts: bottom chord from p0 to p1, top chord `height` above."""
        d = sub(p1, p0)
        top = (0.0, 0.0, height)
        self.beam(p0, p1, width, chord)
        self.beam(add(p0, top), add(p1, top), width, chord)
        pts = [add(p0, mul(d, i / float(panels))) for i in range(panels + 1)]
        for i in range(panels + 1):
            self.beam(pts[i], add(pts[i], top), width * 0.7, web)
        for i in range(panels):
            a, b = pts[i], pts[i + 1]
            if i % 2 == 0:
                self.beam(a, add(b, top), width * 0.6, web * 0.8)
            else:
                self.beam(add(a, top), b, width * 0.6, web * 0.8)
        return self

    def lattice_tower(self, cx, cy, z0, z1, w0, w1, levels=None, leg=10.0):
        """A four legged tapering tower with horizontal rings and X braces. Legs are boxes (w0 at the foot, w1 at the top)."""
        levels = levels or max(2, int((z1 - z0) / 220.0))
        legs = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                legs.append((sx, sy))

        def pos(sx, sy, t):
            w = mb.lerp(w0, w1, t) / 2.0
            return (cx + sx * w, cy + sy * w, z0 + (z1 - z0) * t)
        for sx, sy in legs:
            self.beam(pos(sx, sy, 0.0), pos(sx, sy, 1.0), leg, leg, up=(0.0, 1.0, 0.0) if False else (0.0, 0.0, 1.0))
        for k in range(levels + 1):
            t = k / float(levels)
            ring = [pos(-1, -1, t), pos(1, -1, t), pos(1, 1, t), pos(-1, 1, t)]
            if k % 1 == 0:
                for a, b in zip(ring, ring[1:] + ring[:1]):
                    self.beam(a, b, leg * 0.7, leg * 0.7)
        for k in range(levels):
            t0, t1 = k / float(levels), (k + 1) / float(levels)
            for (sa, sb) in ((( -1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
                if (k + sa[0] + sb[1]) % 2 == 0:
                    self.beam(pos(sa[0], sa[1], t0), pos(sb[0], sb[1], t1), leg * 0.5, leg * 0.5)
                else:
                    self.beam(pos(sb[0], sb[1], t0), pos(sa[0], sa[1], t1), leg * 0.5, leg * 0.5)
        return self

    def hex_nut(self, cx, cy, z, r):
        return self.cyl(cx, cy, z, z + r * 0.6, r, sides=6)

    def merge(self, other, ox=0.0, oy=0.0, oz=0.0, yaw=0.0):
        self.append(other, offset=(ox, oy, oz), yaw=yaw)
        return self


def gable_roof(k, cx, cy, z0, length, width, rise, yaw=0.0, thick=6.0, overhang=30.0):
    """A corrugated gable roof (two sloped slabs) over a building of length (x) x width (y), ridge along x."""
    for side in (-1, 1):
        run = width / 2.0 + overhang
        ang = math.degrees(math.atan2(rise, width / 2.0))
        l = math.hypot(run, rise * (run / (width / 2.0)))
        yy = side * run / 2.0
        zz = z0 + rise - rise * (run / 2.0) / (width / 2.0) + (rise * (run / 2.0) / (width / 2.0))   # centre height of the slab
        zc = z0 + rise * (1.0 - (run / 2.0) / (width / 2.0)) if False else z0 + rise - (rise * (run / 2.0) / (width / 2.0))
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        px = cx - s * yy
        py = cy + c * yy
        k.box(px, py, zc + rise * 0.0, length + overhang, l, thick, yaw=yaw, roll=-side * ang)
    return k


def mesh_stats(m):
    return len(m.verts), len(m.tris)
