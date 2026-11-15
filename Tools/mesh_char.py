"""Pure python mesh builder for character gear (helmets, plates, pauldrons, packs, cloth ...). No unreal import.

    import mesh_char as mc
    m = mc.GM()
    m.lathe([(0, 0), (9, 0), (10, 8), (7, 16), (0, 18)], sides=20, fr=mc.fr((0, 0, 4)), role=mc.R_PLATE)
    m.plate(surface_fn, us, vs, thick_fn, role=...)

Space: character space, centimetres, X forward, Y right, Z up. A piece is built around the origin of the bone it will be attached to
(the offsets are already in character space, see IACharacterRoster.h). Every vertex has a normal, a UV, a ROLE (which colour of the
character's palette the pixel takes: see make_gear_assets.py / M_IAGear) and an ao value (0..1, darkens crevices).
Triangle order convention as in mesh_b: (b - a) x (c - a) points out of the solid (mapkit_b._winding_flip() adapts).
"""

import math
import random

R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT = range(7)
ROLE_NAMES = ["Plate", "Cloth", "Accent", "Team", "Trim", "Glow", "Light"]
UVS = 24.0


# ------------------------------------------------------------------------------------------------ vectors
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def lerp(a, b, t): return a + (b - a) * t
def lerp3(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
def clamp(x, lo, hi): return lo if x < lo else hi if x > hi else x


def norm(a):
    l = length(a)
    return (0.0, 0.0, 1.0) if l < 1e-9 else (a[0] / l, a[1] / l, a[2] / l)


def centroid(pts):
    k = 1.0 / len(pts)
    return (sum(p[0] for p in pts) * k, sum(p[1] for p in pts) * k, sum(p[2] for p in pts) * k)


def newell(pts):
    n = (0.0, 0.0, 0.0)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n = (n[0] + (a[1] - b[1]) * (a[2] + b[2]), n[1] + (a[2] - b[2]) * (a[0] + b[0]), n[2] + (a[0] - b[0]) * (a[1] + b[1]))
    return n


def _rz(p, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def _ry(p, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)


def _rx(p, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


# ------------------------------------------------------------------------------------------------ frames
class Frame:
    """Local -> character space: o + ex * x + ey * y + ez * z."""

    def __init__(self, o=(0.0, 0.0, 0.0), ex=(1.0, 0.0, 0.0), ey=(0.0, 1.0, 0.0), ez=(0.0, 0.0, 1.0)):
        self.o, self.ex, self.ey, self.ez = o, ex, ey, ez

    def pt(self, p):
        return (self.o[0] + self.ex[0] * p[0] + self.ey[0] * p[1] + self.ez[0] * p[2],
                self.o[1] + self.ex[1] * p[0] + self.ey[1] * p[1] + self.ez[1] * p[2],
                self.o[2] + self.ex[2] * p[0] + self.ey[2] * p[1] + self.ez[2] * p[2])

    def dr(self, d):
        return (self.ex[0] * d[0] + self.ey[0] * d[1] + self.ez[0] * d[2],
                self.ex[1] * d[0] + self.ey[1] * d[1] + self.ez[1] * d[2],
                self.ex[2] * d[0] + self.ey[2] * d[1] + self.ez[2] * d[2])


IDENT = Frame()


def fr(pos=(0.0, 0.0, 0.0), yaw=0.0, pitch=0.0, roll=0.0):
    """Frame at pos rotated by roll (about x), then pitch (about y, + lifts the nose), then yaw (about z)."""
    def rot(v):
        v = _rx(v, roll) if roll else v
        v = _ry(v, pitch) if pitch else v
        v = _rz(v, yaw) if yaw else v
        return v
    return Frame(pos, rot((1.0, 0.0, 0.0)), rot((0.0, 1.0, 0.0)), rot((0.0, 0.0, 1.0)))


def frame_x(p0, p1, up=(0.0, 0.0, 1.0)):
    """Frame at p0 whose +x axis runs from p0 to p1 (z as close as possible to up)."""
    ex = norm(sub(p1, p0))
    ref = up if abs(dot(ex, norm(up))) < 0.95 else (1.0, 0.0, 0.0)
    ey = norm(cross(ref, ex))
    ez = cross(ex, ey)
    return Frame(p0, ex, ey, ez)


def frame_z(p0, p1, up=(0.0, 0.0, 1.0)):
    """Frame at p0 whose +z axis runs from p0 to p1 (x is as close as possible to forward)."""
    ez = norm(sub(p1, p0))
    ref = (1.0, 0.0, 0.0) if abs(dot(ez, (1.0, 0.0, 0.0))) < 0.95 else (0.0, 1.0, 0.0)
    ey = norm(cross(ez, ref))
    ex = cross(ey, ez)
    return Frame(p0, ex, ey, ez)


# ------------------------------------------------------------------------------------------------ noise
def _h(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 1274126177) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def vnoise(x, y, seed=0):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = lerp(_h(ix, iy, seed), _h(ix + 1, iy, seed), fx), lerp(_h(ix, iy + 1, seed), _h(ix + 1, iy + 1, seed), fx)
    return lerp(a, b, fy) * 2.0 - 1.0


def fbm(x, y, seed=0, octaves=3):
    t, a, s = 0.0, 1.0, 0.0
    for o in range(octaves):
        t += vnoise(x, y, seed + o * 17) * a
        s += a
        x, y, a = x * 2.03, y * 2.03, a * 0.5
    return t / s


# ------------------------------------------------------------------------------------------------ 2D rings
def circle(rx, ry=None, n=16, cx=0.0, cy=0.0, rot=0.0):
    ry = rx if ry is None else ry
    return [(cx + rx * math.cos(rot + 2 * math.pi * i / n), cy + ry * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]


def rr(y0, y1, z0, z1, ch):
    """A rectangle with chamfered corners (8 points)."""
    ch = max(0.02, min(ch, (y1 - y0) * 0.49, (z1 - z0) * 0.49))
    return [(y0 + ch, z0), (y1 - ch, z0), (y1, z0 + ch), (y1, z1 - ch), (y1 - ch, z1), (y0 + ch, z1), (y0, z1 - ch), (y0, z0 + ch)]


# ------------------------------------------------------------------------------------------------ mesh
class GM:
    def __init__(self):
        self.v, self.n, self.uv, self.role, self.ao, self.t = [], [], [], [], [], []

    # ---- bookkeeping
    def _vert(self, p, n, uv, role, ao):
        self.v.append(p)
        self.n.append(n)
        self.uv.append(uv)
        self.role.append(role)
        self.ao.append(ao)
        return len(self.v) - 1

    def tri_count(self):
        return len(self.t)

    def bounds(self):
        return (tuple(min(v[k] for v in self.v) for k in range(3)), tuple(max(v[k] for v in self.v) for k in range(3)))

    def roles_used(self):
        return sorted(set(self.role))

    # ---- a flat convex polygon with a hard normal
    def poly(self, pts, hint, role, ao=1.0):
        n = newell(pts)
        area = length(n)
        if area < 1e-6:
            return
        n = mul(n, 1.0 / area)
        if dot(n, hint) < 0:
            pts = list(reversed(pts))
            n = mul(n, -1.0)
        ax = max(range(3), key=lambda k: abs(n[k]))
        i0, i1 = [(1, 2), (0, 2), (0, 1)][ax]
        ids = [self._vert(p, n, (p[i0] / UVS, p[i1] / UVS), role, ao) for p in pts]
        for i in range(1, len(ids) - 1):
            self.t.append((ids[0], ids[i], ids[i + 1]))

    def quad(self, a, b, c, d, hint, role, ao=1.0):
        self.poly([a, b, c, d], hint, role, ao)

    # ---- a parametric grid with smooth normals. P[i][j] are 3D points; normal = du x dv, flipped to point away from `inside`
    def grid(self, P, role, wrap_u=False, inside=None, flip=False, ao=None, uvmul=1.0):
        nu, nv = len(P), len(P[0])
        # arc length uv
        us = [0.0] * nu
        for i in range(1, nu):
            us[i] = us[i - 1] + length(sub(P[i][nv // 2], P[i - 1][nv // 2]))
        vs = [0.0] * nv
        for j in range(1, nv):
            vs[j] = vs[j - 1] + length(sub(P[nu // 2][j], P[nu // 2][j - 1]))
        base = len(self.v)
        raw = []
        for i in range(nu):
            for j in range(nv):
                i0, i1 = ((i - 1) % nu, (i + 1) % nu) if wrap_u else (max(i - 1, 0), min(i + 1, nu - 1))
                j0, j1 = max(j - 1, 0), min(j + 1, nv - 1)
                du = sub(P[i1][j], P[i0][j])
                dv = sub(P[i][j1], P[i][j0])
                cr = cross(du, dv)
                raw.append(norm(cr) if length(cr) > 1e-9 else None)
        for i in range(nu):                   # poles (coincident rows): take the normal of the next row in
            for j in range(nv):
                if raw[i * nv + j] is None:
                    for jj in ((j + 1, j - 1, j + 2, j - 2)):
                        if 0 <= jj < nv and raw[i * nv + jj] is not None:
                            raw[i * nv + j] = raw[i * nv + jj]
                            break
                    else:
                        raw[i * nv + j] = (0.0, 0.0, 1.0)
        sign = -1.0 if flip else 1.0
        if inside is not None:
            s = 0.0
            for i in range(nu):
                for j in range(nv):
                    s += dot(raw[i * nv + j], sub(P[i][j], inside))
            if s < 0:
                sign = -sign
        for i in range(nu):
            for j in range(nv):
                n = mul(raw[i * nv + j], sign)
                self._vert(P[i][j], n, (us[i] * uvmul / UVS, vs[j] * uvmul / UVS), role, 1.0 if ao is None else ao[i][j] if isinstance(ao, list) else ao)
        iu = nu if wrap_u else nu - 1
        for i in range(iu):
            for j in range(nv - 1):
                a = base + i * nv + j
                b = base + ((i + 1) % nu) * nv + j
                c = base + ((i + 1) % nu) * nv + j + 1
                d = base + i * nv + j + 1
                if sign > 0:
                    self.t.append((a, b, c)); self.t.append((a, c, d))
                else:
                    self.t.append((a, c, b)); self.t.append((a, d, c))
        return base

    # ---- a ring-by-ring loft (rings = lists of 3D points, same count). smooth = shared normals, else flat quads
    def loft(self, rings, role, smooth=False, caps=(True, True), closed=True, ao=1.0, flip=False):
        nr = len(rings[0])
        cen = [centroid(r) for r in rings]
        if smooth:
            # grid() wants P[i][j] with i around the ring and j along the loft
            Q = [[rings[k][i % nr] for k in range(len(rings))] for i in range(nr if closed else nr)]
            self.grid(Q, role, wrap_u=closed, flip=flip, ao=ao)
        else:
            for k in range(len(rings) - 1):
                mid = mul(add(cen[k], cen[k + 1]), 0.5)
                for i in range(nr if closed else nr - 1):
                    j = (i + 1) % nr
                    q = [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]
                    self.poly(q, sub(centroid(q), mid), role, ao)
        if caps[0] and closed:
            self.poly(rings[0], sub(cen[0], cen[1]) if len(rings) > 1 else (-1.0, 0.0, 0.0), role, ao)
        if caps[1] and closed:
            self.poly(rings[-1], sub(cen[-1], cen[-2]) if len(rings) > 1 else (1.0, 0.0, 0.0), role, ao)

    # ---- chamfered boxes and tapered slabs (flat shaded, hard edges)
    def slab(self, secs, role, f=IDENT, caps=(True, True), ao=1.0):
        """secs = [(x, y0, y1, z0, z1, chamfer), ...] along local x; rings are chamfered rectangles."""
        rings = [[f.pt((x, y, z)) for (y, z) in rr(y0, y1, z0, z1, ch)] for (x, y0, y1, z0, z1, ch) in secs]
        self.loft(rings, role, smooth=False, caps=caps, ao=ao)

    def box(self, c, size, role, ch=0.6, f=IDENT, taper=1.0, ao=1.0):
        """A chamfered box (centre c in the frame f, size = (sx, sy, sz)). taper < 1 shrinks the +x end in y and z."""
        sx, sy, sz = size
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        ch = max(0.05, min(ch, hx * 0.9, hy * 0.9, hz * 0.9))
        t = taper
        secs = [(c[0] - hx, c[1] - hy + ch * 0.6, c[1] + hy - ch * 0.6, c[2] - hz + ch * 0.6, c[2] + hz - ch * 0.6, ch * 0.5),
                (c[0] - hx + ch, c[1] - hy, c[1] + hy, c[2] - hz, c[2] + hz, ch),
                (c[0] + hx - ch, c[1] - hy * t, c[1] + hy * t, c[2] - hz * t, c[2] + hz * t, ch * t),
                (c[0] + hx, c[1] - hy * t + ch * 0.6, c[1] + hy * t - ch * 0.6, c[2] - hz * t + ch * 0.6, c[2] + hz * t - ch * 0.6, ch * 0.5)]
        self.slab(secs, role, f, ao=ao)

    # ---- solids of revolution about the local z axis of the frame f
    def lathe(self, profile, role, sides=18, f=IDENT, sy=1.0, creases=(), caps=(True, True), smooth=True, ao=1.0, rot=0.0, arc=None,
              rfn=None, flip=False, double=False):
        """Solid of revolution about the local z axis of f. profile = [(radius, z), ...] travelled so that the OUTSIDE is on the
        right in the (r right, z up) plane (a plain bottom -> top outline is right; a closed band goes inner-bottom, outer-bottom,
        outer-top, inner-top, inner-bottom). sy stretches y. creases = profile indices where the shading breaks. arc=(a0, a1) degrees
        builds an open slice. rfn(theta, t) -> radius multiplier (t = 0..1 along the profile): pleats, lumps, wavy rims."""
        if double:       # thin cones (collars, skirts, cuffs) must be visible from both sides
            self.lathe(profile, role, sides, f, sy, creases, caps, smooth, ao, rot, arc, rfn, not flip, False)
        n_prof = len(profile)
        runs, start = [], 0
        for k in sorted(creases):
            if 0 < k < n_prof - 1:
                runs.append((start, k))
                start = k
        runs.append((start, n_prof - 1))

        def ang(i):
            return rot + 2 * math.pi * i / sides if arc is None else math.radians(lerp(arc[0], arc[1], i / float(sides)))

        def pt(i, k):
            r, z = profile[k]
            th = ang(i)
            if rfn:
                r = r * rfn(th, k / float(max(1, n_prof - 1)))
            return f.pt((r * math.cos(th), r * sy * math.sin(th), z))

        ncols = sides if arc is None else sides + 1
        for (a, b) in runs:
            cols = [[pt(i, k) for k in range(a, b + 1)] for i in range(ncols)]
            if smooth:
                self.grid(cols, role, wrap_u=arc is None, flip=flip, ao=ao)
            else:
                for i in range(sides):
                    i2 = (i + 1) % ncols
                    for j in range(len(cols[0]) - 1):
                        q = [cols[i][j], cols[i2][j], cols[i2][j + 1], cols[i][j + 1]]
                        h = cross(sub(q[1], q[0]), sub(q[3], q[0]))
                        if length(h) < 1e-9:
                            h = cross(sub(q[1], q[2]), sub(q[3], q[2]))
                        self.poly(q, mul(h, -1.0 if flip else 1.0), role, ao)
        if arc is None:
            if caps[0] and profile[0][0] > 1e-4:
                self.poly([pt(i, 0) for i in range(sides)], f.dr((0, 0, -1)), role, ao)
            if caps[1] and profile[-1][0] > 1e-4:
                self.poly([pt(i, n_prof - 1) for i in range(sides)], f.dr((0, 0, 1)), role, ao)

    def sweep(self, pts, radii, role, sides=8, sy=1.0, caps=(True, True), smooth=True, up=(0.0, 0.0, 1.0), ao=1.0, flat=None):
        """A tube along a polyline with a radius per point (horns, tails, antennas, straps). sy flattens the section.
        flat=(a_scale, b_scale) overrides the section's two axes."""
        n = len(pts)
        tang = []
        for k in range(n):
            a = pts[max(k - 1, 0)]
            b = pts[min(k + 1, n - 1)]
            tang.append(norm(sub(b, a)))
        rings = []
        a_prev = None
        for k in range(n):
            t = tang[k]
            if a_prev is None:
                ref = up if abs(dot(t, norm(up))) < 0.95 else (1.0, 0.0, 0.0)
                a_vec = norm(cross(t, ref))
            else:
                a_vec = norm(sub(a_prev, mul(t, dot(a_prev, t))))
            b_vec = cross(t, a_vec)
            a_prev = a_vec
            r = radii[k]
            ring = []
            for i in range(sides):
                th = 2 * math.pi * i / sides
                ca, cb = (1.0, sy) if flat is None else flat
                ring.append(add(pts[k], add(mul(a_vec, r * ca * math.cos(th)), mul(b_vec, r * cb * math.sin(th)))))
            rings.append(ring)
        self.loft(rings, role, smooth=smooth, caps=caps, ao=ao)

    def ellipsoid(self, c, rx, ry, rz, role, nu=14, nv=9, f=IDENT, cut=None, ao=1.0):
        """A lat-long ellipsoid. cut=(v0, v1) keeps only latitudes between those fractions (0 = top pole, 1 = bottom pole)."""
        v0, v1 = (0.0, 1.0) if cut is None else cut
        P = []
        for i in range(nu):
            th = 2 * math.pi * i / nu
            col = []
            for j in range(nv):
                ph = math.pi * lerp(v0, v1, j / float(nv - 1))
                col.append(f.pt((c[0] + rx * math.sin(ph) * math.cos(th), c[1] + ry * math.sin(ph) * math.sin(th), c[2] + rz * math.cos(ph))))
            P.append(col)
        self.grid(P, role, wrap_u=True, inside=f.pt(c), ao=ao)

    # ---- a curved armour plate: a surface offset by a thickness profile, with edge strips
    def plate(self, surf, us, vs, thick, role, inside, inner=False, ao=1.0, wrap_u=False, edge_role=None):
        """surf(u, v) -> point on the body-side surface; us, vs = parameter samples; thick(u, v) -> thickness above the surface.
        `inside` is a point inside the body (decides which side is out). Edges get their own strips."""
        u_lo, u_hi, v_lo, v_hi = min(us), max(us), min(vs), max(vs)

        def base_normal(u, v):
            e = 1e-3
            if wrap_u:
                ua, ub = u - e, u + e
            else:
                ua, ub = max(u - e, u_lo), min(u + e, u_hi)
            va, vb = max(v - e, v_lo), min(v + e, v_hi)
            du = sub(surf(ub, v), surf(ua, v))
            dv = sub(surf(u, vb), surf(u, va))
            c = cross(du, dv)
            if length(c) < 1e-7:             # a pole (all points of the row coincide): look slightly inside
                v2 = v + (0.03 if v - v_lo < 0.5 * (v_hi - v_lo) else -0.03) * (v_hi - v_lo)
                du = sub(surf(ub, v2), surf(ua, v2))
                dv = sub(surf(u, v2 + e), surf(u, v2 - e))
                c = cross(du, dv)
            return norm(c)
        mid = surf(us[len(us) // 2], vs[len(vs) // 2])
        n0 = base_normal(us[len(us) // 2], vs[len(vs) // 2])
        s = 1.0 if dot(n0, sub(mid, inside)) > 0 else -1.0
        inner_pts, outer_pts = [], []
        for u in us:
            ci, co = [], []
            for v in vs:
                p = surf(u, v)
                n = mul(base_normal(u, v), s)
                ci.append(p)
                co.append(add(p, mul(n, thick(u, v))))
            inner_pts.append(ci)
            outer_pts.append(co)
        self.grid(outer_pts, role, wrap_u=wrap_u, inside=inside, ao=ao)
        er = role if edge_role is None else edge_role
        nu, nv = len(us), len(vs)
        edges = []
        if not wrap_u:
            edges.append([(outer_pts[0][j], inner_pts[0][j]) for j in range(nv)])
            edges.append([(outer_pts[nu - 1][j], inner_pts[nu - 1][j]) for j in range(nv)])
        edges.append([(outer_pts[i][0], inner_pts[i][0]) for i in range(nu)])
        edges.append([(outer_pts[i][nv - 1], inner_pts[i][nv - 1]) for i in range(nu)])
        cen = centroid([p for row in outer_pts for p in row])
        for e in edges:
            for k in range(len(e) - 1):
                (a0, b0), (a1, b1) = e[k], e[k + 1]
                if length(sub(a0, b0)) < 0.05 and length(sub(a1, b1)) < 0.05:
                    continue
                q = [a0, a1, b1, b0]
                self.poly(q, sub(centroid(q), cen), er, ao * 0.8)
        if inner:
            self.grid(inner_pts, role, wrap_u=wrap_u, inside=inside, flip=True, ao=0.5)

    # ---- tubes and cones
    def tube(self, a, b, r0, r1, role, sides=10, caps=(True, True), smooth=True, sy=1.0, ao=1.0):
        f = frame_z(a, b)
        L = length(sub(b, a))
        self.lathe([(r0, 0.0), (r1, L)], role, sides=sides, f=f, sy=sy, caps=caps, smooth=smooth, ao=ao)

    def cone(self, base, tip, r, role, sides=8, ao=1.0, sy=1.0, smooth=True):
        f = frame_z(base, tip)
        L = length(sub(tip, base))
        self.lathe([(r, 0.0), (0.0, L)], role, sides=sides, f=f, caps=(True, False), smooth=smooth, ao=ao, sy=sy)

    # ---- thin cloth: a grid P[i][j] given a thickness, double sided with a rim
    def cloth(self, P, role, thick=0.5, inside=None, ao=1.0, wrap_u=False):
        nu, nv = len(P), len(P[0])
        front = [[None] * nv for _ in range(nu)]
        back = [[None] * nv for _ in range(nu)]
        ctr = centroid([p for row in P for p in row])
        ref = ctr if inside is None else inside
        nat_mid = None
        want = None
        for i in range(nu):
            for j in range(nv):
                i0, i1 = ((i - 1) % nu, (i + 1) % nu) if wrap_u else (max(i - 1, 0), min(i + 1, nu - 1))
                j0, j1 = max(j - 1, 0), min(j + 1, nv - 1)
                n = norm(cross(sub(P[i1][j], P[i0][j]), sub(P[i][j1], P[i][j0])))
                if inside is not None and dot(n, sub(P[i][j], inside)) < 0:
                    n = mul(n, -1.0)
                front[i][j] = add(P[i][j], mul(n, thick * 0.5))
                back[i][j] = sub(P[i][j], mul(n, thick * 0.5))
                if i == nu // 2 and j == nv // 2:
                    want = n
                    nat_mid = norm(cross(sub(P[i1][j], P[i0][j]), sub(P[i][j1], P[i][j0])))
        flip_front = dot(nat_mid, want) < 0
        self.grid(front, role, wrap_u=wrap_u, flip=flip_front, ao=ao)
        self.grid(back, role, wrap_u=wrap_u, flip=not flip_front, ao=ao * 0.8)
        rim = []
        if not wrap_u:
            rim.append([(front[0][j], back[0][j]) for j in range(nv)])
            rim.append([(front[nu - 1][j], back[nu - 1][j]) for j in range(nv)])
        rim.append([(front[i][0], back[i][0]) for i in range(nu)])
        rim.append([(front[i][nv - 1], back[i][nv - 1]) for i in range(nu)])
        for e_ in rim:
            for k in range(len(e_) - 1):
                (a0, b0), (a1, b1) = e_[k], e_[k + 1]
                q = [a0, a1, b1, b0]
                self.poly(q, sub(centroid(q), ctr), role, ao * 0.8)

    # ---- combining
    def append(self, other, f=IDENT):
        base = len(self.v)
        for p, n, uv, r, a in zip(other.v, other.n, other.uv, other.role, other.ao):
            self.v.append(f.pt(p))
            self.n.append(norm(f.dr(n)))
            self.uv.append(uv)
            self.role.append(r)
            self.ao.append(a)
        for (a, b, c) in other.t:
            self.t.append((a + base, b + base, c + base))

    def mirrored(self):
        """The copy mirrored across the y = 0 plane (left <-> right), with the winding reversed."""
        m = GM()
        m.v = [(p[0], -p[1], p[2]) for p in self.v]
        m.n = [(n[0], -n[1], n[2]) for n in self.n]
        m.uv = list(self.uv)
        m.role = list(self.role)
        m.ao = list(self.ao)
        m.t = [(a, c, b) for (a, b, c) in self.t]
        return m

    def transformed(self, f):
        m = GM()
        m.append(self, f)
        return m

    def check(self):
        """Triangles whose geometric normal disagrees with their vertex normals (winding test); should be 0 or tiny."""
        bad = 0
        for a, b, c in self.t:
            g = cross(sub(self.v[b], self.v[a]), sub(self.v[c], self.v[a]))
            if dot(g, add(add(self.n[a], self.n[b]), self.n[c])) < 0:
                bad += 1
        return bad
