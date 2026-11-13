"""Pure python generated cars for the city maps (no unreal import): lofted body with wheel arches, raked greenhouse, glass,
tyres, hubs, lamps, door seams. Used by kc_parts.car through mapkit_b.commit(name, mesh).

    parts = mesh_car.build("sedan")      # dict: paint, dark, steel, glass, head, tail  (each a mesh_b.Mesh)
    parts["info"]                        # dict: length, width, body_h, cab_h, cab_x0, cab_x1 ... (collision box sizes)

Local frame: +x is the front of the car, y left/right, z up, origin on the ground in the middle of the footprint. Units cm.
One mesh per material, so a car is six static mesh actors that share the same assets between all cars of a kind.
"""

import math

from mesh_b import Mesh, rot_x, rot_z, norm, cross, sub, add, mul, lerp, clamp, smoothstep


def spow(v, e):
    return math.copysign(abs(v) ** e, v)


def curve(pts, x):
    """Cubic Hermite through (x, v) control points (sorted by x) with finite difference tangents."""
    n = len(pts)
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    i = 0
    while not (pts[i][0] <= x <= pts[i + 1][0]):
        i += 1

    def tangent(a):
        a0, a1 = max(a - 1, 0), min(a + 1, n - 1)
        return (pts[a1][1] - pts[a0][1]) / max(1e-6, pts[a1][0] - pts[a0][0])

    x0, v0 = pts[i]
    x1, v1 = pts[i + 1]
    dx = x1 - x0
    t = (x - x0) / dx
    m0, m1 = tangent(i) * dx, tangent(i + 1) * dx
    return ((2 * t ** 3 - 3 * t ** 2 + 1) * v0 + (t ** 3 - 2 * t ** 2 + t) * m0 + (-2 * t ** 3 + 3 * t ** 2) * v1 +
            (t ** 3 - t ** 2) * m1)


# ------------------------------------------------------------------------------------------------ the three kinds
# body control points (x, half width, bottom z, top z); cabin control points (x, roof z, half width at the belt)
SPECS = {
    "sedan": dict(
        body=[(-226, 68, 38, 80), (-222, 80, 32, 92), (-205, 88, 26, 98), (-165, 92, 22, 98), (-120, 93, 22, 93),
              (70, 93, 22, 93), (120, 93, 22, 90), (170, 92, 22, 84), (205, 87, 24, 76), (220, 78, 30, 68), (226, 66, 38, 62)],
        belt=93.0, n_body=6.5, n_cab=5.5, tumble=0.14,
        cab=[(-160, 94, 78), (-152, 98, 80), (-135, 110, 81), (-115, 126, 82), (-95, 140, 82), (-70, 145, 82), (-30, 146, 82),
             (6, 145, 83), (24, 140, 83), (42, 128, 83), (62, 110, 82), (78, 94, 80)],
        wheels=(137.0, -137.0), wheel_r=32.5, wheel_w=21.0, arch_r=39.0,
        side=[(-98.0, -9.0), (4.0, 70.0)], side_zmin=0.0, rear=(-150.0, -100.0), front=(20.0, 76.0),
        seams=[72.0, -92.0], cab_seam=[], handles=[40.0, -52.0], mirror_x=64.0, head_y=52.0, tail_y=56.0),
    "hatch": dict(
        body=[(-197, 66, 38, 86), (-192, 78, 32, 94), (-178, 87, 26, 96), (-150, 91, 22, 93), (-100, 92, 22, 91),
              (60, 92, 22, 91), (95, 92, 22, 89), (140, 90, 22, 82), (178, 85, 24, 74), (192, 76, 28, 66), (198, 64, 36, 60)],
        belt=91.0, n_body=6.5, n_cab=5.5, tumble=0.14,
        cab=[(-194, 92, 76), (-186, 108, 78), (-170, 132, 80), (-150, 148, 81), (-120, 154, 82), (-60, 155, 82),
             (-10, 152, 83), (10, 143, 83), (28, 126, 83), (46, 108, 82), (62, 92, 80)],
        wheels=(120.0, -120.0), wheel_r=31.0, wheel_w=20.0, arch_r=37.0,
        side=[(-150.0, -34.0), (-24.0, 56.0)], side_zmin=0.0, rear=(-188.0, -140.0), front=(8.0, 58.0),
        seams=[60.0, -32.0], cab_seam=[], handles=[30.0], mirror_x=52.0, head_y=50.0, tail_y=54.0),
    "van": dict(
        body=[(-240, 88, 36, 86), (-230, 96, 28, 92), (-200, 100, 22, 92), (180, 100, 22, 92), (218, 98, 22, 88),
              (234, 92, 26, 80), (240, 82, 32, 70)],
        belt=92.0, n_body=6.0, n_cab=8.0, tumble=0.05,
        cab=[(-240, 94, 86), (-236, 150, 90), (-226, 196, 94), (-200, 198, 96), (120, 196, 96), (135, 186, 96),
             (150, 160, 96), (166, 120, 95), (178, 93, 94)],
        wheels=(150.0, -150.0), wheel_r=34.0, wheel_w=22.0, arch_r=41.0,
        side=[(104.0, 172.0), (-40.0, 40.0)], side_zmin=128.0, rear=None, front=(128.0, 176.0),
        seams=[168.0, 92.0, -62.0], cab_seam=[168.0, 92.0, -62.0], handles=[130.0, 70.0], mirror_x=166.0, head_y=60.0,
        tail_y=84.0),
}

N_BODY = 36      # points around the body section
LOW_K = 6        # |k| <= LOW_K around the bottom is the dark skirt
N_ARC = 25       # points over the cabin (0..180 degrees)


# ------------------------------------------------------------------------------------------------ surfaces
def _normals(P, wrap):
    nk, nj = len(P), len(P[0])
    out = [[None] * nj for _ in range(nk)]
    for k in range(nk):
        for j in range(nj):
            k0, k1 = ((k - 1) % nk, (k + 1) % nk) if wrap else (max(k - 1, 0), min(k + 1, nk - 1))
            j0, j1 = max(j - 1, 0), min(j + 1, nj - 1)
            n = cross(sub(P[k1][j], P[k0][j]), sub(P[k][j1], P[k][j0]))
            out[k][j] = norm(n)
    return out


def _surf(mesh, P, Nn, ks, js, offset=0.0, quad_ok=None):
    """Adds the part of the grid (positions P[k][j], normals Nn) given by the index lists ks, js to the mesh."""
    nj = len(js)
    used = {}

    def vert(a, b):
        key = (a, b)
        if key not in used:
            k, j = ks[a], js[b]
            used[key] = len(mesh.verts)
            mesh.verts.append(add(P[k][j], mul(Nn[k][j], offset)))
            mesh.norms.append(Nn[k][j])
        return used[key]

    for a in range(len(ks) - 1):
        for b in range(nj - 1):
            if quad_ok is not None and not quad_ok(ks[a], ks[a + 1], js[b], js[b + 1]):
                continue
            v00, v10, v11, v01 = vert(a, b), vert(a + 1, b), vert(a + 1, b + 1), vert(a, b + 1)
            mesh.tris.append((v00, v10, v11))
            mesh.tris.append((v00, v11, v01))


def _place(dst, src, offset=(0.0, 0.0, 0.0), rotx=0.0):
    """Appends src to dst, rotated about x then moved."""
    base = len(dst.verts)
    for v, n in zip(src.verts, src.norms):
        if rotx:
            v, n = rot_x(v, rotx), rot_x(n, rotx)
        dst.verts.append((v[0] + offset[0], v[1] + offset[1], v[2] + offset[2]))
        dst.norms.append(n)
    for t in src.tris:
        dst.tris.append((t[0] + base, t[1] + base, t[2] + base))


def _signed_volume(m):
    v = 0.0
    for a, b, c in m.tris:
        pa, pb, pc = m.verts[a], m.verts[b], m.verts[c]
        v += pa[0] * (pb[1] * pc[2] - pb[2] * pc[1]) - pa[1] * (pb[0] * pc[2] - pb[2] * pc[0]) + pa[2] * (pb[0] * pc[1] - pb[1] * pc[0])
    return v / 6.0


# ------------------------------------------------------------------------------------------------ the car
class Car:
    def __init__(self, kind):
        self.kind = kind
        s = self.s = SPECS[kind]
        self.bc = sorted(s["body"])
        self.cc = sorted(s["cab"])
        self.x0, self.x1 = self.bc[0][0], self.bc[-1][0]
        self.theta = [math.radians(-90.0 + 360.0 * k / N_BODY) for k in range(N_BODY)]
        self.lo = [(N_BODY - LOW_K + i) % N_BODY for i in range(2 * LOW_K + 1)]
        self.up = list(range(LOW_K, N_BODY - LOW_K + 1))

    # ---- body surface as a function of (x, k)
    def prof(self, x):
        b = self.bc
        return (curve([(c[0], c[1]) for c in b], x), curve([(c[0], c[2]) for c in b], x), curve([(c[0], c[3]) for c in b], x))

    def body_pt(self, x, k):
        s = self.s
        w, zb, zt = self.prof(x)
        zt = max(zt, zb + 12.0)
        th = self.theta[k]
        c, sn = math.cos(th), math.sin(th)
        e = 2.0 / s["n_body"]
        zc, hh = (zb + zt) / 2.0, (zt - zb) / 2.0
        y = w * spow(c, e)
        z = zc + hh * spow(sn, e)
        if sn > 0:
            y *= 1.0 - 0.07 * sn * sn
        # wheel arches: lift the lower outer part of the section on a circle around every wheel centre
        zw, ra = s["wheel_r"], s["arch_r"]
        zbn = zb
        for xc in s["wheels"]:
            d = abs(x - xc)
            if d < ra:
                arch = zw + math.sqrt(ra * ra - d * d)
                blend = smoothstep(w - 50.0, w - 24.0, abs(y))
                zbn = max(zbn, lerp(zb, arch, blend))
        zbn = min(zbn, zt - 10.0)
        z = zbn + (z - zb) / max(1e-6, zt - zb) * (zt - zbn)
        return (x, y, z)

    def cab_prof(self, x):
        c = self.cc
        return (max(curve([(q[0], q[1]) for q in c], x), self.s["belt"]), curve([(q[0], q[2]) for q in c], x))

    def cab_pt(self, x, i):
        """i = 0 base right, 1..25 arc from the right belt over the roof to the left belt, 26 base left."""
        s = self.s
        zt, w = self.cab_prof(x)
        belt = s["belt"]
        hh = zt - belt
        if i == 0 or i == N_ARC + 1:
            return (x, w if i == 0 else -w, belt - 16.0)
        th = math.radians(180.0 * (i - 1) / (N_ARC - 1))
        c, sn = math.cos(th), math.sin(th)
        e = 2.0 / s["n_cab"]
        return (x, w * spow(c, e) * (1.0 - s["tumble"] * sn * sn), belt + hh * spow(sn, e))

    def stations(self, lo, hi, ctrl_x, extra=()):
        xs = set(ctrl_x) | set(extra)
        x = lo
        while x < hi:
            xs.add(round(x, 3))
            x += 6.0
        xs.add(hi)
        return sorted(xs)

    # ---- build
    def build(self):
        s = self.s
        paint, dark, steel, glass, head, tail = (Mesh() for _ in range(6))
        # body loft
        arch_x = []
        for xc in s["wheels"]:
            ra, zw = s["arch_r"], s["wheel_r"]
            zb = 22.0
            d0 = math.sqrt(max(0.0, ra * ra - (zb - zw) ** 2))
            for dd in (d0 - 1.0, d0, d0 + 1.0, ra - 1.0, ra, ra + 0.5):
                arch_x += [xc + dd, xc - dd]
        xs = self.stations(self.x0, self.x1, [c[0] for c in self.bc], [x for x in arch_x if self.x0 < x < self.x1])
        P = [[self.body_pt(x, k) for x in xs] for k in range(N_BODY)]
        Nn = _normals(P, True)
        js = list(range(len(xs)))
        _surf(paint, P, Nn, self.up, js)
        _surf(dark, P, Nn, self.lo, js)
        nj = len(xs)
        for j, hint in ((0, (-1.0, 0, 0)), (nj - 1, (1.0, 0, 0))):                 # flat nose and tail
            paint.poly([P[k][j] for k in self.up], hint)
            dark.poly([P[k][j] for k in self.lo], hint)
        # cabin loft
        cx = self.stations(self.cc[0][0], self.cc[-1][0], [c[0] for c in self.cc])
        C = [[self.cab_pt(x, i) for x in cx] for i in range(N_ARC + 2)]
        CN = _normals(C, False)
        cj = list(range(len(cx)))
        _surf(paint, C, CN, list(range(N_ARC + 2)), cj)
        # glass: parts of the cabin surface pushed out by 7 mm
        def window(ks, ranges, zmin=0.0, gaps=()):
            def ok(k0, k1, j0, j1):
                xa, xb = cx[j0], cx[j1]
                if not any(xa >= r0 - 0.01 and xb <= r1 + 0.01 for (r0, r1) in ranges):
                    return False
                if any(xb > g0 and xa < g1 for (g0, g1) in gaps):
                    return False
                return all(C[k][j][2] >= zmin for k in (k0, k1) for j in (j0, j1))
            _surf(glass, C, CN, ks, cj, offset=0.7, quad_ok=ok)
        win = list(range(1, 8))
        for ks in (win, [26 - i for i in reversed(win)]):
            window(ks, [r for r in s["side"]], zmin=s["side_zmin"])
        wind = list(range(9, 18))
        window(wind, [s["front"]])
        if s["rear"]:
            window(wind, [s["rear"]])
        # door seams: thin dark ribbons following the surface
        for sx in s["seams"]:
            for sgn in (1, -1):
                self.ribbon(dark, self.body_pt, sx, [7, 8, 9, 10, 11, 12], sgn)
        for sx in s["cab_seam"]:
            for sgn in (1, -1):
                self.ribbon(dark, self.cab_pt, sx, [1, 2, 3, 4, 5], sgn)
        # door handles
        for hx in s["handles"]:
            for sgn in (1, -1):
                x_, y_, z_ = self.body_pt(hx, 12)
                y_ *= sgn
                dark.box(x_, y_ + sgn * 0.6, z_, 14.0, 2.4, 2.4)
        # mirrors
        mx = s["mirror_x"]
        zt, w = self.cab_prof(mx)
        for sgn in (1, -1):
            paint.box(mx, sgn * (w + 6.0), s["belt"] + (14.0 if self.kind != "van" else 40.0), 12.0, 10.0, 8.0, yaw=sgn * 18.0)
            dark.box(mx - 2.0, sgn * (w + 1.0), s["belt"] + (9.0 if self.kind != "van" else 35.0), 3.0, 8.0, 3.0)
        # nose: grille and lamps; tail: lamps and plates
        fx = self.x1
        fw, fzb, fzt = self.prof(fx)
        zc = (fzb + fzt) / 2.0
        dark.box(fx - 1.0, 0.0, zc - 1.0, 5.0, fw * 1.1, 11.0)
        steel.box(fx + 0.5, 0.0, zc - 8.0, 3.0, 26.0, 7.0)                           # plate holder
        for sgn in (1, -1):
            head.box(self.x1 - 5.0, sgn * s["head_y"], fzt - 4.0 + (4 if self.kind != "van" else 6), 8.0, 27.0, 9.0)
        rx, rzb, rzt = self.x0, self.prof(self.x0)[1], self.prof(self.x0)[2]
        for sgn in (1, -1):
            if self.kind == "van":
                tail.box(rx + 5.0, sgn * s["tail_y"], 78.0, 7.0, 8.0, 52.0)
            else:
                tail.box(rx + 5.0, sgn * s["tail_y"], rzt - 8.0, 8.0, 26.0, 8.0)
        dark.box(rx - 0.5, 0.0, (rzb + rzt) / 2.0 - 5.0, 3.0, 40.0, 12.0)            # rear apron
        # wheels
        r, ww = s["wheel_r"], s["wheel_w"]
        tyre = Mesh().lathe(0.0, 0.0, -ww / 2.0, ww / 2.0, r, r, sides=22, segments=8,
                            profile=[(0, 0.82), (0.06, 0.96), (0.18, 1.0), (0.82, 1.0), (0.94, 0.96), (1, 0.82)])
        hub = Mesh()
        cap = Mesh()
        for sg in (1, -1):
            z0, z1 = (ww / 2.0 - 0.6, ww / 2.0 + 1.4) if sg > 0 else (-ww / 2.0 - 1.4, -ww / 2.0 + 0.6)
            hub.lathe(0.0, 0.0, z0, z1, r * 0.66, r * 0.62, sides=18, segments=1)
            c0, c1 = (z1 - 0.2, z1 + 1.2) if sg > 0 else (z0 - 1.2, z0 + 0.2)
            cap.lathe(0.0, 0.0, c0, c1, r * 0.2, r * 0.18, sides=12, segments=1)
        for xw in s["wheels"]:
            for sgn in (1, -1):
                wy = sgn * (self.prof(xw)[0] - 15.0)
                _place(dark, tyre, (xw, wy, r), rotx=90.0)
                _place(steel, hub, (xw, wy, r), rotx=90.0)
                _place(dark, cap, (xw, wy, r), rotx=90.0)
        # a pipe under the tail
        steel.box(self.x0 + 2.0, -s["tail_y"] * 0.6, 28.0, 14.0, 7.0, 7.0)
        info = dict(length=self.x1 - self.x0, width=2.0 * self.prof(0.0)[0], x0=self.x0, x1=self.x1,
                    body_top=s["belt"], cab_top=max(c[1] for c in self.cc),
                    cab_x0=min(c[0] for c in self.cc if c[1] > s["belt"] + 20.0), cab_x1=max(c[0] for c in self.cc if c[1] > s["belt"] + 20.0),
                    cab_w=2.0 * max(c[2] for c in self.cc) * 0.8)
        return dict(paint=paint, dark=dark, steel=steel, glass=glass, head=head, tail=tail, info=info)

    def ribbon(self, mesh, fn, x, ks, sgn, width=1.0, off=0.45):
        """A thin strip across the surface at station x (fn(x, k) -> point of the right side), pushed out a little.
        sgn = -1 mirrors it to the left side (the order is reversed so that it still faces out)."""
        xs = (x - width / 2.0, x + width / 2.0)
        order = list(ks) if sgn > 0 else list(ks)[::-1]
        P = [[(p[0], p[1] * sgn, p[2]) for p in (fn(xx, k) for xx in xs)] for k in order]
        Nn = _normals(P, False)
        _surf(mesh, P, Nn, list(range(len(P))), [0, 1], offset=off)


def build(kind):
    parts = Car(kind).build()
    return parts
