"""Pure python mesh builder for the Instagib rifle (no unreal import, test it with any python).

    import mesh_weapon
    m = mesh_weapon.build_rifle(detail=1)      # detail 1 = first person, 0 = the one carried by the characters
    m.v, m.n, m.uv, m.t (triangles), m.m (material id per triangle)

Units are cm, rifle space: X forward (the muzzle is at +X), Y right, Z up. The pistol grip stands at about x = 4, z = -9 (the
origin is chosen so that the grip sits where the hand of the old rifle was: the animation fit in IAPlayerCharacter.cpp stays valid).
Material ids: 0 body (gunmetal), 1 trim (dark steel), 2 rubber, 3 accent (team colour paint), 4 core (the only glowing parts), 5 glass.
Triangle order convention as in mesh_b: (b - a) x (c - a) points out of the solid (mapkit_b._winding_flip() adapts).
"""

import math

MAT_BODY, MAT_TRIM, MAT_RUBBER, MAT_ACCENT, MAT_CORE, MAT_GLASS = range(6)
MAT_NAMES = ["Body", "Trim", "Rubber", "Accent", "Core", "Glass"]
UVS = 20.0          # one UV unit = 20 cm of rifle (the material's Tile parameter scales it)
BARREL_Z = 0.5      # height of the barrel axis
MUZZLE = (64.4, 0.0, BARREL_Z)


# ------------------------------------------------------------------------------------------------ vectors
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))


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


# ------------------------------------------------------------------------------------------------ frames
class Frame:
    """Local -> rifle space: origin + ex * x + ey * y + ez * z."""

    def __init__(self, origin=(0.0, 0.0, 0.0), ex=(1.0, 0.0, 0.0), ey=(0.0, 1.0, 0.0), ez=(0.0, 0.0, 1.0)):
        self.o, self.ex, self.ey, self.ez = origin, ex, ey, ez

    def pt(self, p):
        return (self.o[0] + self.ex[0] * p[0] + self.ey[0] * p[1] + self.ez[0] * p[2],
                self.o[1] + self.ex[1] * p[0] + self.ey[1] * p[1] + self.ez[1] * p[2],
                self.o[2] + self.ex[2] * p[0] + self.ey[2] * p[1] + self.ez[2] * p[2])

    def dir(self, d):
        return (self.ex[0] * d[0] + self.ey[0] * d[1] + self.ez[0] * d[2],
                self.ex[1] * d[0] + self.ey[1] * d[1] + self.ez[1] * d[2],
                self.ex[2] * d[0] + self.ey[2] * d[1] + self.ez[2] * d[2])


IDENTITY = Frame()


def frame_at(pos, pitch=0.0, roll=0.0):
    """Frame at pos, with +x lifted by pitch degrees and rolled about its own x axis by roll degrees."""
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    ex = (cp, 0.0, sp)
    ey = (0.0, 1.0, 0.0)
    ez = (-sp, 0.0, cp)
    if roll:
        cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        ey, ez = add(mul(ey, cr), mul(ez, sr)), add(mul(ey, -sr), mul(ez, cr))
    return Frame(pos, ex, ey, ez)


def frame_along(p0, p1, up=(0.0, 0.0, 1.0)):
    """Frame with +x from p0 to p1, +y sideways (perpendicular to up) and +z roughly up."""
    ex = norm(sub(p1, p0))
    ey = norm(cross(up, ex))
    ez = cross(ex, ey)
    return Frame(p0, ex, ey, ez)


# ------------------------------------------------------------------------------------------------ rings
def circle(r, n=16, cy=0.0, cz=0.0, rot=0.0):
    return [(cy + r * math.cos(rot + 2 * math.pi * i / n), cz + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]


def rr(y0, y1, z0, z1, ch):
    """A rectangle with chamfered corners (8 points)."""
    ch = max(0.02, min(ch, (y1 - y0) * 0.49, (z1 - z0) * 0.49))
    return [(y0 + ch, z0), (y1 - ch, z0), (y1, z0 + ch), (y1, z1 - ch), (y1 - ch, z1), (y0 + ch, z1), (y0, z1 - ch), (y0, z0 + ch)]


# ------------------------------------------------------------------------------------------------ mesh
class WMesh:
    def __init__(self):
        self.v, self.n, self.uv, self.t, self.m = [], [], [], [], []

    # ---- flat polygon (hard normal, planar UV from the dominant axis of the normal)
    def poly(self, pts, hint, mat):
        n = newell(pts)
        area = length(n)
        if area < 1e-5:
            return
        n = mul(n, 1.0 / area)
        if dot(n, hint) < 0:
            pts = list(reversed(pts))
            n = mul(n, -1.0)
        ax = max(range(3), key=lambda k: abs(n[k]))
        i0, i1 = [(1, 2), (0, 2), (0, 1)][ax]
        base = len(self.v)
        for p in pts:
            self.v.append(p)
            self.n.append(n)
            self.uv.append((p[i0] / UVS, p[i1] / UVS))
        for i in range(1, len(pts) - 1):
            self.t.append((base, base + i, base + i + 1))
            self.m.append(mat)

    # ---- generic loft of equal-count rings along local x
    def loft(self, secs, mat, fr=IDENTITY, smooth=False, caps=(True, True)):
        """secs: [(x, [(y, z), ...]), ...] with the same number of ring points everywhere."""
        P = [[fr.pt((x, y, z)) for (y, z) in ring] for (x, ring) in secs]
        ns, nr = len(P), len(P[0])
        cen = [centroid(r) for r in P]
        if not smooth:
            for k in range(ns - 1):
                mid = mul(add(cen[k], cen[k + 1]), 0.5)
                for i in range(nr):
                    j = (i + 1) % nr
                    q = [P[k][i], P[k][j], P[k + 1][j], P[k + 1][i]]
                    self.poly(q, sub(centroid(q), mid), mat)
        else:
            # shared vertices with averaged normals; a seam column carries the texture wrap
            idx = {}
            norms = {}
            vids = []
            dist = 0.0
            for k in range(ns):
                if k:
                    dist += length(sub(cen[k], cen[k - 1]))
                circ = sum(length(sub(P[k][i], P[k][(i + 1) % nr])) for i in range(nr))
                row = []
                for i in range(nr + 1):
                    p = P[k][i % nr]
                    row.append(len(self.v))
                    self.v.append(p)
                    self.n.append((0.0, 0.0, 1.0))
                    self.uv.append((circ * i / nr / UVS, dist / UVS))
                vids.append(row)
            acc = {}
            for k in range(ns - 1):
                mid = mul(add(cen[k], cen[k + 1]), 0.5)
                for i in range(nr):
                    a, b, c, d = (k, i), (k, i + 1), (k + 1, i + 1), (k + 1, i)
                    pa, pb, pc, pd = P[k][i], P[k][(i + 1) % nr], P[k + 1][(i + 1) % nr], P[k + 1][i]
                    hint = sub(centroid([pa, pb, pc, pd]), mid)
                    n1 = cross(sub(pb, pa), sub(pc, pa))
                    n2 = cross(sub(pc, pa), sub(pd, pa))
                    flip = dot(add(n1, n2), hint) < 0
                    ia, ib, ic, idd = vids[k][i], vids[k][i + 1], vids[k + 1][i + 1], vids[k + 1][i]
                    tris = [(ia, ic, ib), (ia, idd, ic)] if flip else [(ia, ib, ic), (ia, ic, idd)]
                    for tri, nn in zip(tris, (n1, n2)):
                        if length(nn) < 1e-7:
                            continue
                        self.t.append(tri)
                        self.m.append(mat)
                        nn = nn if not flip else mul(nn, -1.0)
                        for vi in tri:
                            key = (self._key(vi, vids, nr))
                            acc[key] = add(acc.get(key, (0.0, 0.0, 0.0)), nn)
            for k in range(ns):
                for i in range(nr + 1):
                    self.n[vids[k][i]] = norm(acc.get((k, i % nr), (0.0, 0.0, 1.0)))
        # end caps (flat)
        if caps[0]:
            self.poly(P[0], sub(cen[0], cen[1]) if ns > 1 else (-1.0, 0.0, 0.0), mat)
        if caps[1]:
            self.poly(P[-1], sub(cen[-1], cen[-2]) if ns > 1 else (1.0, 0.0, 0.0), mat)

    @staticmethod
    def _key(vi, vids, nr):
        # vertex id -> (section, ring index modulo nr); vids are consecutive per section
        for k, row in enumerate(vids):
            if row[0] <= vi <= row[-1]:
                return (k, (vi - row[0]) % nr)
        return (0, 0)

    def bounds(self):
        return (tuple(min(v[k] for v in self.v) for k in range(3)), tuple(max(v[k] for v in self.v) for k in range(3)))

    def tri_count(self):
        return len(self.t)


# ------------------------------------------------------------------------------------------------ shapes
def lofts(m, specs, mat, fr=IDENTITY, caps=(True, True)):
    """specs: [(x, y0, y1, z0, z1, chamfer), ...]  (a tapering chamfered body)."""
    m.loft([(s[0], rr(s[1], s[2], s[3], s[4], s[5])) for s in specs], mat, fr, False, caps)


def bbox(m, x0, x1, y0, y1, z0, z1, ch, mat, fr=IDENTITY, e=None):
    """A box whose long edges and end edges are chamfered."""
    e = ch * 0.8 if e is None else e
    e = min(e, (x1 - x0) * 0.3, (y1 - y0) * 0.3, (z1 - z0) * 0.3)
    cc = max(0.02, ch - e * 0.0)
    lofts(m, [(x0, y0 + e, y1 - e, z0 + e, z1 - e, cc),
              (x0 + e, y0, y1, z0, z1, ch),
              (x1 - e, y0, y1, z0, z1, ch),
              (x1, y0 + e, y1 - e, z0 + e, z1 - e, cc)], mat, fr)


def strut(m, p0, p1, w, h, ch, mat, up=(0.0, 0.0, 1.0)):
    """A chamfered bar between two points (w sideways, h along the up direction)."""
    fr = frame_along(p0, p1, up)
    bbox(m, 0.0, length(sub(p1, p0)), -w / 2.0, w / 2.0, -h / 2.0, h / 2.0, ch, mat, fr, e=min(ch, 0.3))


def lathe(m, prof, mat, n=20, cy=0.0, cz=BARREL_Z, fr=IDENTITY, smooth=True, caps=(True, True), rot=0.0):
    """Solid of revolution about the x axis through (cy, cz); prof = [(x, radius), ...]."""
    m.loft([(x, circle(max(r, 0.001), n, cy, cz, rot)) for (x, r) in prof], mat, fr, smooth, caps)


def prism_xz(m, pts, y0, y1, mat, fr=IDENTITY):
    """Convex polygon in the x-z plane extruded between y0 and y1."""
    a = [fr.pt((x, y0, z)) for (x, z) in pts]
    b = [fr.pt((x, y1, z)) for (x, z) in pts]
    c = centroid(a + b)
    m.poly(a, sub(centroid(a), c), mat)
    m.poly(b, sub(centroid(b), c), mat)
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        q = [a[i], a[j], b[j], b[i]]
        m.poly(q, sub(centroid(q), c), mat)


def bolt(m, pos, direction, r=0.42, depth=0.3, mat=MAT_TRIM):
    fr = frame_along(pos, add(pos, direction), up=(0.0, 0.0, 1.0) if abs(direction[2]) < 0.9 else (1.0, 0.0, 0.0))
    m.loft([(0.0, circle(r, 8)), (depth * 0.5, circle(r, 8)), (depth, circle(r * 0.8, 8))], mat, fr, False, (False, True))


# ------------------------------------------------------------------------------------------------ the rifle
def build_rifle(detail=1):
    """detail 1: first person (bolts, rail slots, vent slats, six cage ribs); detail 0: lighter copy for the characters."""
    m = WMesh()
    zb = BARREL_Z
    n_round = 24 if detail else 14
    D = detail

    # ---- receiver: a long chamfered body, higher at the rear (cheek), with the energy cell and rail below and above
    lofts(m, [(-8.5, -2.6, 2.6, -3.4, 3.4, 0.9),
              (-6.5, -3.0, 3.0, -4.3, 4.0, 1.0),
              (24.0, -3.0, 3.0, -4.5, 4.2, 1.0),
              (27.0, -2.7, 2.7, -4.0, 3.8, 0.9)], MAT_BODY)
    # rear cap and stock mount
    bbox(m, -10.5, -8.4, -2.8, 2.8, -3.6, 3.6, 0.7, MAT_TRIM)
    # painted side plates (team colour) with a raised dark frame behind
    for s in (1, -1):
        y0, y1 = (2.95, 3.5) if s > 0 else (-3.5, -2.95)
        # gunmetal cover plate with a painted stripe and a painted end block
        bbox(m, 1.0, 19.5, y0, y1, -2.7, 2.6, 0.5, MAT_BODY)
        ya, yb = (y1 - 0.05, y1 + 0.2) if s > 0 else (y0 - 0.2, y0 + 0.05)
        bbox(m, 2.6, 17.4, ya, yb, -2.3, -1.0, 0.2, MAT_ACCENT)
        bbox(m, 1.5, 3.0, ya, yb, -0.2, 2.2, 0.2, MAT_ACCENT)
        bbox(m, 0.4, 20.1, (3.0 if s > 0 else -3.2), (3.2 if s > 0 else -3.0), -3.2, 3.1, 0.3, MAT_TRIM)
        # vent grille behind the plate
        slats = 5 if D else 3
        for i in range(slats):
            x = -5.8 + i * (6.0 / max(1, slats - 1)) * (1.0 if D else 1.0)
            bbox(m, x, x + 0.6, (3.0 if s > 0 else -3.35), (3.35 if s > 0 else -3.0), -2.4, 2.6, 0.2, MAT_TRIM)
        # bolts on the plates
        if D:
            for (bx, bz) in ((2.2, 1.7), (18.3, 1.7), (2.2, -1.8), (18.3, -1.8)):
                bolt(m, (bx, 3.5 * s, bz), (0.0, float(s), 0.0), 0.42, 0.28, MAT_TRIM)

    # ---- top rail with slots and the sight
    if D:
        bbox(m, -6.0, 31.0, -1.15, 1.15, 4.0, 4.9, 0.25, MAT_BODY)
        x = -5.5
        while x < 29.5:
            bbox(m, x, x + 1.55, -1.55, 1.55, 4.2, 5.25, 0.3, MAT_TRIM)
            x += 2.45
    else:
        bbox(m, -6.0, 31.0, -1.5, 1.5, 4.0, 5.2, 0.3, MAT_TRIM)
    # holographic sight: mounts, tube, bezels, glass and a glowing dot
    for (a, b) in ((5.3, 7.0), (9.3, 11.0)):
        bbox(m, a, b, -1.4, 1.4, 5.0, 6.6, 0.3, MAT_BODY)
    sz = 7.6
    lathe(m, [(3.8, 2.4), (4.2, 2.55), (11.6, 2.55), (12.0, 2.4)], MAT_BODY, n_round, 0.0, sz)
    lathe(m, [(3.15, 2.35), (3.35, 2.85), (4.4, 2.85), (4.7, 2.5)], MAT_TRIM, n_round, 0.0, sz)
    lathe(m, [(11.2, 2.5), (11.6, 2.95), (13.1, 2.95), (13.3, 2.6)], MAT_TRIM, n_round, 0.0, sz)
    lathe(m, [(2.95, 2.05), (3.25, 2.05)], MAT_GLASS, n_round, 0.0, sz, smooth=False)
    lathe(m, [(12.9, 2.15), (13.4, 2.15)], MAT_GLASS, n_round, 0.0, sz, smooth=False)
    lathe(m, [(2.85, 0.3), (3.0, 0.3)], MAT_CORE, 8, 0.0, sz, smooth=False)
    bbox(m, 6.4, 10.0, -0.9, 0.9, 10.0, 10.55, 0.2, MAT_ACCENT) if D else None

    # ---- stock: two chamfered rails, braces, rubber buttpad and cheek riser
    if D:
        # first person: only the root of the stock can be in view, it ends in a short stub
        strut(m, (-9.5, 0.0, 2.5), (-15.5, 0.0, 2.2), 3.0, 2.3, 0.5, MAT_BODY)
        strut(m, (-9.5, 0.0, -2.7), (-15.5, 0.0, -5.2), 3.0, 2.3, 0.5, MAT_BODY)
        bbox(m, -17.2, -15.2, -2.4, 2.4, -7.4, 3.6, 0.9, MAT_RUBBER)
        bbox(m, -9.4, -8.2, -1.6, 1.6, 3.6, 4.6, 0.3, MAT_ACCENT)
    else:
        strut(m, (-9.5, 0.0, 2.5), (-24.5, 0.0, 1.5), 3.0, 2.3, 0.5, MAT_BODY)
        strut(m, (-9.5, 0.0, -2.7), (-24.0, 0.0, -9.6), 3.0, 2.3, 0.5, MAT_BODY)
        strut(m, (-14.0, 0.0, 2.3), (-13.4, 0.0, -5.0), 2.4, 1.7, 0.4, MAT_TRIM, up=(1.0, 0.0, 0.0))
        strut(m, (-19.3, 0.0, 2.0), (-18.9, 0.0, -7.9), 2.4, 1.7, 0.4, MAT_TRIM, up=(1.0, 0.0, 0.0))
        bbox(m, -27.6, -24.2, -2.5, 2.5, -11.8, 2.9, 1.0, MAT_RUBBER)
        bbox(m, -22.5, -11.5, -2.2, 2.2, 1.9, 3.9, 0.7, MAT_RUBBER)

    # ---- pistol grip (rubber, ridged), trigger guard, trigger
    g0 = (5.9, 0.0, -3.9)
    g1 = (2.9, 0.0, -16.2)
    gfr = frame_along(g0, g1, up=(1.0, 0.0, 0.0))     # +x down the grip, +y sideways, +z forward
    glen = length(sub(g1, g0))
    gs = []
    steps = 9 if D else 4
    for i in range(steps + 1):
        t = i / float(steps)
        depth_f = 2.6 + 0.35 * t + (0.25 if (D and i % 2 == 1) else 0.0)
        gs.append((glen * t, -2.2 - 0.15 * t, 2.2 + 0.15 * t, -2.45 - 0.3 * t, depth_f, 0.9))
    lofts(m, gs, MAT_RUBBER, gfr)
    bbox(m, glen - 0.2, glen + 0.9, -2.7, 2.7, -3.3, 3.5, 0.5, MAT_TRIM, gfr)
    strut(m, (14.2, 0.0, -4.0), (14.9, 0.0, -9.6), 1.4, 1.3, 0.35, MAT_BODY, up=(1.0, 0.0, 0.0))
    strut(m, (15.0, 0.0, -9.7), (7.4, 0.0, -9.0), 1.4, 1.3, 0.35, MAT_BODY)
    strut(m, (6.4, 0.0, -8.8), (6.0, 0.0, -5.5), 1.4, 1.3, 0.35, MAT_BODY, up=(1.0, 0.0, 0.0))
    strut(m, (11.2, 0.0, -4.1), (10.4, 0.0, -7.6), 0.9, 1.3, 0.3, MAT_TRIM, up=(1.0, 0.0, 0.0))

    # ---- energy cell below the receiver, with three glowing level bars on each side
    lofts(m, [(15.8, -2.5, 2.5, -12.0, -4.0, 0.8), (25.2, -2.5, 2.5, -12.0, -4.0, 0.8)], MAT_TRIM)
    bbox(m, 15.5, 25.5, -2.75, 2.75, -13.2, -11.6, 0.5, MAT_ACCENT)
    for s in (1, -1):
        for zc in (-6.0, -7.6, -9.2):
            y0, y1 = (2.4, 2.65) if s > 0 else (-2.65, -2.4)
            bbox(m, 17.2, 23.8, y0, y1, zc - 0.4, zc + 0.4, 0.15, MAT_CORE)
        if D:
            bbox(m, 16.2, 17.0, (2.4 if s > 0 else -2.9), (2.9 if s > 0 else -2.4), -11.2, -4.4, 0.2, MAT_BODY)
            bbox(m, 24.0, 24.8, (2.4 if s > 0 else -2.9), (2.9 if s > 0 else -2.4), -11.2, -4.4, 0.2, MAT_BODY)

    # ---- handguard: ribbed cage around the glowing core rod, rail and foregrip
    lathe(m, [(26.0, 3.4), (26.5, 4.8), (28.5, 4.8), (29.0, 4.1)], MAT_TRIM, n_round, 0.0, zb)
    lathe(m, [(29.0, 1.7), (60.8, 1.7)], MAT_CORE, 16 if D else 10, 0.0, zb)
    ribs = 6 if D else 4
    angles = [30, 90, 150, 210, 270, 330] if D else [45, 135, 225, 315]
    for a in angles[:ribs]:
        ra = math.radians(a)
        R = 3.45
        ey = (0.0, -math.sin(ra), math.cos(ra))
        ex = (1.0, 0.0, 0.0)
        ez = cross(ex, ey)
        fr = Frame((28.8, R * math.cos(ra), zb + R * math.sin(ra)), ex, ey, ez)
        bbox(m, 0.0, 15.4, -0.65, 0.65, -0.5, 0.5, 0.2, MAT_ACCENT if a == 90 else MAT_BODY, fr)
    lathe(m, [(28.8, 4.0), (29.1, 4.3), (30.0, 4.3), (30.3, 4.0)], MAT_TRIM, n_round, 0.0, zb)
    lathe(m, [(35.4, 4.0), (35.7, 4.45), (36.9, 4.45), (37.2, 4.0)], MAT_ACCENT, n_round, 0.0, zb)
    lathe(m, [(43.0, 4.0), (43.4, 4.55), (44.6, 4.55), (45.0, 3.6)], MAT_TRIM, n_round, 0.0, zb)
    bbox(m, 29.5, 43.0, -1.4, 1.4, -4.7, -3.0, 0.4, MAT_TRIM)
    # foregrip, leaning slightly forward
    f0 = (38.2, 0.0, -4.4)
    f1 = (39.8, 0.0, -14.4)
    ffr = frame_along(f0, f1, up=(1.0, 0.0, 0.0))
    flen = length(sub(f1, f0))
    fs = []
    for i in range(7 if D else 3):
        t = i / float((6 if D else 2))
        fs.append((flen * t, -1.9 - 0.2 * t, 1.9 + 0.2 * t, -2.0 - 0.1 * t, 2.0 + 0.1 * t + (0.22 if (D and i % 2 == 1) else 0.0), 0.7))
    lofts(m, fs, MAT_RUBBER, ffr)
    bbox(m, flen - 0.1, flen + 0.8, -2.4, 2.4, -2.5, 2.6, 0.4, MAT_TRIM, ffr)

    # ---- emitter: focusing coils along the glowing rod, prongs and the muzzle
    for i, x in enumerate((46.2, 50.4, 54.6)):
        lathe(m, [(x, 3.0), (x + 0.4, 3.95), (x + 1.35, 3.95), (x + 1.75, 3.0)], MAT_BODY, n_round, 0.0, zb)
        lathe(m, [(x + 0.55, 4.0), (x + 1.2, 4.0)], MAT_ACCENT, n_round, 0.0, zb)
    lathe(m, [(58.4, 2.7), (58.8, 3.5), (60.4, 3.5), (60.8, 2.7)], MAT_BODY, n_round, 0.0, zb)
    lathe(m, [(60.8, 2.6), (61.5, 3.35), (62.8, 3.6), (63.9, 3.0), (64.2, 2.3)], MAT_TRIM, n_round, 0.0, zb)
    lathe(m, [(64.0, 1.55), (64.4, 1.55)], MAT_CORE, 12, 0.0, zb, smooth=False)
    for s in (1, -1):
        # two slim prongs on each side, spread like the electrodes of a lightning gun
        for dz in (2.1, -2.1):
            strut(m, (44.2, 4.6 * s, zb + dz), (61.5, 7.6 * s, zb + dz * 1.6), 0.5, 1.5, 0.18, MAT_ACCENT)
        bbox(m, 43.4, 46.4, (3.6 if s > 0 else -5.2), (5.2 if s > 0 else -3.6), zb - 3.2, zb + 3.2, 0.3, MAT_TRIM)
    return m


# ------------------------------------------------------------------------------------------------ sanity check
def check(m):
    """Counts triangles whose geometric normal disagrees with the vertex normals."""
    bad = 0
    for (a, b, c) in m.t:
        n = cross(sub(m.v[b], m.v[a]), sub(m.v[c], m.v[a]))
        vn = add(add(m.n[a], m.n[b]), m.n[c])
        if dot(n, vn) < 0:
            bad += 1
    return bad


if __name__ == "__main__":
    for d in (1, 0):
        mm = build_rifle(d)
        print("detail", d, "verts", len(mm.v), "tris", len(mm.t), "bad", check(mm), "bounds", mm.bounds())
