"""Pure python mesh builder (no unreal import) used by mapkit_b.py to make real, irregular geometry for the maps.

Everything is built as plain lists (vertices, normals, triangles) so that it can be tested with any python.
Triangle order convention here: (b - a) x (c - a) points OUT of the solid. mapkit_b.commit() flips if the engine wants the other.
Units are cm. A mesh is built in its own local space; the actor placing it adds position, yaw and scale.
"""

import math
import random


# ------------------------------------------------------------------------------------------------ vector helpers
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    l = math.sqrt(dot(a, a))
    if l < 1e-9:
        return (0.0, 0.0, 1.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a), 0.0, 1.0) if b != a else 0.0
    return t * t * (3 - 2 * t)


def rot_z(p, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def rot_y(p, pitch):
    """Rotates about the y axis: positive pitch lifts +x (like an actor pitching its nose up)."""
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)


def rot_x(p, roll):
    c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


# ------------------------------------------------------------------------------------------------ noise
def _h(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 1274126177) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def vnoise(x, y, z=0.0, seed=0):
    """Smooth value noise in 0..1."""
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    c = lambda dx, dy, dz: _h(ix + dx, iy + dy, iz + dz, seed)
    x00 = lerp(c(0, 0, 0), c(1, 0, 0), fx)
    x10 = lerp(c(0, 1, 0), c(1, 1, 0), fx)
    x01 = lerp(c(0, 0, 1), c(1, 0, 1), fx)
    x11 = lerp(c(0, 1, 1), c(1, 1, 1), fx)
    return lerp(lerp(x00, x10, fy), lerp(x01, x11, fy), fz)


def fbm(x, y, z=0.0, octaves=4, seed=0, lac=2.03, gain=0.5):
    """Fractal noise roughly in -1..1."""
    total, amp, norm_sum = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += (vnoise(x, y, z, seed + o * 17) * 2.0 - 1.0) * amp
        norm_sum += amp
        x, y, z = x * lac, y * lac, z * lac
        amp *= gain
    return total / norm_sum


def ridged(x, y, z=0.0, octaves=3, seed=0):
    """0..1 ridges (sharp creases)."""
    total, amp, s = 0.0, 1.0, 0.0
    for o in range(octaves):
        v = 1.0 - abs(vnoise(x, y, z, seed + o * 31) * 2.0 - 1.0)
        total += v * v * amp
        s += amp
        x, y, z = x * 2.1, y * 2.1, z * 2.1
        amp *= 0.5
    return total / s


# ------------------------------------------------------------------------------------------------ mesh
class Mesh:
    def __init__(self):
        self.verts = []
        self.norms = []
        self.tris = []

    # ---- low level
    def poly(self, pts, hint):
        """A flat convex polygon with a hard normal, oriented away from `hint` (a direction vector)."""
        n = (0.0, 0.0, 0.0)
        for i in range(len(pts)):                       # Newell
            a, b = pts[i], pts[(i + 1) % len(pts)]
            n = (n[0] + (a[1] - b[1]) * (a[2] + b[2]), n[1] + (a[2] - b[2]) * (a[0] + b[0]), n[2] + (a[0] - b[0]) * (a[1] + b[1]))
        n = norm(n)
        if dot(n, hint) < 0:
            pts = list(reversed(pts))
            n = (-n[0], -n[1], -n[2])
        base = len(self.verts)
        self.verts.extend(pts)
        self.norms.extend([n] * len(pts))
        for i in range(1, len(pts) - 1):
            self.tris.append((base, base + i, base + i + 1))

    def convex(self, pts, faces, center=None):
        """A convex solid: pts and faces (lists of point indices); every face is oriented away from the centre."""
        if center is None:
            center = mul((sum(p[0] for p in pts), sum(p[1] for p in pts), sum(p[2] for p in pts)), 1.0 / len(pts))
        for f in faces:
            fp = [pts[i] for i in f]
            fc = mul((sum(p[0] for p in fp), sum(p[1] for p in fp), sum(p[2] for p in fp)), 1.0 / len(fp))
            self.poly(fp, sub(fc, center))

    # ---- boxes
    def box(self, cx, cy, cz, sx, sy, sz, yaw=0.0, pitch=0.0, roll=0.0, jitter=0.0, seed=0, base=False, top_jitter=None,
            origin=(0.0, 0.0, 0.0), taper=0.0):
        """A box (centre cx,cy,cz, or cz = bottom when base=True). jitter moves each corner randomly by up to jitter cm,
        top_jitter (default = jitter) the four top corners only. taper shrinks the top face (0..1)."""
        rng = random.Random(seed)
        tj = jitter if top_jitter is None else top_jitter
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        if base:
            cz = cz + hz
        pts = []
        for dz in (-1, 1):
            for dy in (-1, 1):
                for dx in (-1, 1):
                    k = (1.0 - taper) if dz > 0 else 1.0
                    j = tj if dz > 0 else jitter
                    p = (dx * hx * k + rng.uniform(-j, j), dy * hy * k + rng.uniform(-j, j), dz * hz + rng.uniform(-j, j))
                    p = rot_x(p, roll) if roll else p
                    p = rot_y(p, pitch) if pitch else p
                    p = rot_z(p, yaw) if yaw else p
                    pts.append((p[0] + cx + origin[0], p[1] + cy + origin[1], p[2] + cz + origin[2]))
        faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
        self.convex(pts, faces)

    def prism(self, poly2d, y0, y1, yaw=0.0, origin=(0.0, 0.0, 0.0), jitter=0.0, seed=0):
        """Extrudes a convex 2D profile (x, z) between y0 and y1 (the wall plane runs along x, z up)."""
        rng = random.Random(seed)
        pts = []
        for y in (y0, y1):
            for (x, z) in poly2d:
                p = (x + rng.uniform(-jitter, jitter), y, z + rng.uniform(-jitter, jitter))
                p = rot_z(p, yaw) if yaw else p
                pts.append((p[0] + origin[0], p[1] + origin[1], p[2] + origin[2]))
        n = len(poly2d)
        faces = [list(range(n)), list(range(n, 2 * n))]
        for i in range(n):
            faces.append([i, (i + 1) % n, n + (i + 1) % n, n + i])
        self.convex(pts, faces)

    # ---- smooth surfaces
    def grid(self, nu, nv, P, wrap_u=False, flip=False):
        """A parametric surface. P(i, j) -> (x, y, z). The normal is d/du x d/dv (flip reverses). Returns the first vertex index."""
        pts = [[P(i, j) for j in range(nv)] for i in range(nu)]
        base = len(self.verts)
        for i in range(nu):
            for j in range(nv):
                i0, i1 = (i - 1) % nu if wrap_u else max(i - 1, 0), (i + 1) % nu if wrap_u else min(i + 1, nu - 1)
                j0, j1 = max(j - 1, 0), min(j + 1, nv - 1)
                du = sub(pts[i1][j], pts[i0][j])
                dv = sub(pts[i][j1], pts[i][j0])
                n = norm(cross(du, dv))
                if flip:
                    n = (-n[0], -n[1], -n[2])
                self.verts.append(pts[i][j])
                self.norms.append(n)
        idx = lambda i, j: base + (i % nu) * nv + j
        iu = nu if wrap_u else nu - 1
        for i in range(iu):
            for j in range(nv - 1):
                a, b, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
                if flip:
                    self.tris.append((a, c, b))
                    self.tris.append((a, d, c))
                else:
                    self.tris.append((a, b, c))
                    self.tris.append((a, c, d))
        return base

    def lathe(self, cx, cy, z0, z1, r0, r1, sides=24, segments=1, yaw=0.0, rfn=None, zfn=None, cap_bottom=True,
              cap_top=True, jitter=0.0, seed=0, profile=None):
        """A solid of revolution about the vertical axis through (cx, cy), from z0 (radius r0) to z1 (radius r1).
        rfn(theta, t) -> radius multiplier (fluting, wobble); zfn(theta, t) -> z offset (broken tops);
        profile = list of (t, radius multiplier) giving a curved outline (echinus, torus ...)."""
        rng = random.Random(seed)

        def P(i, j):
            th = 2 * math.pi * i / sides + math.radians(yaw)
            t = j / float(segments)
            r = lerp(r0, r1, t)
            if profile:
                for k in range(len(profile) - 1):
                    if profile[k][0] <= t <= profile[k + 1][0]:
                        f = (t - profile[k][0]) / max(1e-6, profile[k + 1][0] - profile[k][0])
                        r = lerp(r0, r1, t) * lerp(profile[k][1], profile[k + 1][1], f)
                        break
            if rfn:
                r *= rfn(th, t)
            z = lerp(z0, z1, t) + (zfn(th, t) if zfn else 0.0)
            jx = rng.uniform(-jitter, jitter) if jitter else 0.0
            jy = rng.uniform(-jitter, jitter) if jitter else 0.0
            return (cx + math.cos(th) * r + jx, cy + math.sin(th) * r + jy, z)

        # outward: du (counter clockwise around z) x dv (up) points outward
        self.grid(sides, segments + 1, P, wrap_u=True)
        for top in (False, True):
            if (top and not cap_top) or (not top and not cap_bottom):
                continue
            j = segments if top else 0
            ring = [P(i, j) for i in range(sides)]
            ctr = (cx, cy, sum(p[2] for p in ring) / sides)
            nrm = (0.0, 0.0, 1.0 if top else -1.0)
            base = len(self.verts)
            self.verts.append(ctr)
            self.norms.append(nrm)
            for p in ring:
                self.verts.append(p)
                self.norms.append(nrm)
            for i in range(sides):
                a, b = base + 1 + i, base + 1 + (i + 1) % sides
                if top:
                    self.tris.append((base, a, b))      # ring runs counter clockwise seen from above: normal up
                else:
                    self.tris.append((base, b, a))
        return self

    def blob(self, cx, cy, cz, rx, ry, rz, nu=18, nv=11, amp=0.25, freq=1.4, seed=0, flat_bottom=0.35, yaw=0.0, octaves=3):
        """A lumpy boulder: lat-long sphere with fractal noise, a flattened bottom at cz (cz = bottom of the rock)."""
        def P(i, j):
            th = 2 * math.pi * i / nu
            ph = math.pi * (j / float(nv - 1))             # 0 = top pole, pi = bottom pole
            ux, uy, uz = math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph)
            n = fbm(ux * freq + 7.3, uy * freq + 1.1, uz * freq + 4.7, octaves, seed)
            k = 1.0 + amp * n
            x, y, z = ux * rx * k, uy * ry * k, uz * rz * k
            if z < -rz * flat_bottom:
                z = -rz * flat_bottom
            p = rot_z((x, y, z + rz * flat_bottom), yaw) if yaw else (x, y, z + rz * flat_bottom)
            return (cx + p[0], cy + p[1], cz + p[2] if not yaw else cz + p[2])
        # u counter clockwise, v goes from the top pole down: du x dv points inward -> flip
        self.grid(nu, nv, P, wrap_u=True, flip=True)

    def append(self, other, offset=(0.0, 0.0, 0.0), yaw=0.0):
        base = len(self.verts)
        for v, n in zip(other.verts, other.norms):
            if yaw:
                v, n = rot_z(v, yaw), rot_z(n, yaw)
            self.verts.append((v[0] + offset[0], v[1] + offset[1], v[2] + offset[2]))
            self.norms.append(n)
        for t in other.tris:
            self.tris.append((t[0] + base, t[1] + base, t[2] + base))

    def bounds(self):
        xs = [v[0] for v in self.verts]
        ys = [v[1] for v in self.verts]
        zs = [v[2] for v in self.verts]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def check(self):
        """Counts triangles whose geometric normal disagrees with the vertex normals (a winding / orientation test)."""
        bad = 0
        for a, b, c in self.tris:
            n = cross(sub(self.verts[b], self.verts[a]), sub(self.verts[c], self.verts[a]))
            vn = add(add(self.norms[a], self.norms[b]), self.norms[c])
            if dot(n, vn) < 0:
                bad += 1
        return bad


# ------------------------------------------------------------------------------------------------ composed shapes
def column_mesh(height, radius, flutes=16, drums=4, seed=1, plinth_k=2.4, abacus_k=2.6, sides=None, broken_at=None,
                entasis=0.88, top_noise=0.0):
    """A classical column: square plinth, round base, tapered drums with visible joints, neck, echinus and abacus.
    Origin: centre of the base at z = 0. Returns a Mesh. broken_at (cm) cuts the shaft with a jagged top."""
    rng = random.Random(seed)
    m = Mesh()
    sides = sides or max(24, flutes * 2)
    r = radius
    plinth_h = height * 0.035
    torus_h = height * 0.035
    cap_h = height * 0.055
    abacus_h = height * 0.04
    shaft_h = height - plinth_h - torus_h - cap_h - abacus_h
    z = 0.0
    m.box(0, 0, z, r * plinth_k, r * plinth_k, plinth_h, jitter=r * 0.015, seed=seed, base=True, top_jitter=0)
    z += plinth_h
    m.lathe(0, 0, z, z + torus_h, r * 1.22, r * 1.05, sides=sides, segments=3, profile=[(0, 1.0), (0.4, 1.06), (1, 1.0)], cap_bottom=False)
    z += torus_h
    fl = (lambda th, t: 1.0 - 0.045 * (0.5 + 0.5 * math.cos(flutes * th))) if flutes else None
    z_end = z + shaft_h if broken_at is None else min(z + shaft_h, broken_at)
    n_dr = max(1, int(round(drums * (z_end - z) / shaft_h))) if broken_at is not None else drums
    dz = (z_end - z) / n_dr
    for k in range(n_dr):
        t0 = (z - plinth_h - torus_h + k * dz) / shaft_h
        t1 = t0 + dz / shaft_h
        ra = r * (1.0 - (1.0 - entasis) * clamp(t0, 0, 1))
        rb = r * (1.0 - (1.0 - entasis) * clamp(t1, 0, 1))
        off = rng.uniform(-1.2, 1.2)
        top = (k == n_dr - 1) and broken_at is not None
        zf = None
        if top:
            s2 = seed * 13 + 5
            zf = lambda th, t, s2=s2: (fbm(math.cos(th) * 1.8 + 3, math.sin(th) * 1.8 + 3, 0, 3, s2)) * (r * 0.9) * t + (r * 0.9) * t * 0.2
        m.lathe(off * 0.4, off * 0.3, z + k * dz + 0.6, z + (k + 1) * dz - 0.6 + (0 if not top else 0.6), ra * (1 + 0.004 * k), rb, sides=sides, segments=2,
                rfn=fl, zfn=zf, cap_top=True, cap_bottom=True, seed=seed + k)
    if broken_at is not None and broken_at < z + shaft_h:
        return m
    z += shaft_h
    m.lathe(0, 0, z, z + cap_h * 0.35, r * 0.84, r * 0.9, sides=sides, segments=1)       # neck rings
    z += cap_h * 0.35
    m.lathe(0, 0, z, z + cap_h * 0.65, r * 0.9, r * 1.32, sides=sides, segments=4, profile=[(0, 1.0), (0.5, 0.97), (1, 1.0)])
    z += cap_h * 0.65
    m.box(0, 0, z, r * abacus_k, r * abacus_k, abacus_h, jitter=r * 0.012, seed=seed + 3, base=True, top_jitter=0)
    return m
