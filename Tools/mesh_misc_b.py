"""More shapes for the map-B scripts: fallen drums, roofs, obelisks, braziers, mountains (pure python)."""

import math
import random

from mesh_b import Mesh, fbm, ridged


def drum_mesh(length, radius, flutes=16, seed=1):
    """A fallen column drum lying along x, centred on the origin."""
    m = Mesh()
    fl = (lambda th, t: 1.0 - 0.045 * (0.5 + 0.5 * math.cos(flutes * th)))
    m.lathe(0, 0, -length / 2.0, length / 2.0, radius, radius * 0.93, sides=max(24, flutes * 2), segments=2, rfn=fl, jitter=0.6, seed=seed)
    out = Mesh()                                          # stand the axis along x: (x, y, z) -> (z, y, -x)
    out.verts = [(v[2], v[1], -v[0]) for v in m.verts]
    out.norms = [(n[2], n[1], -n[0]) for n in m.norms]
    out.tris = list(m.tris)                               # a pure rotation keeps the winding
    return out


def roof_mesh(size, seed=1, missing=(), steps=3, slab_h=70.0, cells=3):
    """A stepped pavilion roof: a slab built from cells x cells blocks (some can be missing: collapsed), then smaller slabs.
    The origin is the centre of the underside."""
    m = Mesh()
    z = 0.0
    s = size
    for k in range(steps):
        cs = s / cells
        h = slab_h * (1.0 - 0.15 * k)
        for ix in range(cells):
            for iy in range(cells):
                if k == 0 and (ix, iy) in missing:
                    continue
                m.box((ix - (cells - 1) / 2.0) * cs, (iy - (cells - 1) / 2.0) * cs, z, cs + 0.5, cs + 0.5, h, base=True,
                      jitter=1.5, top_jitter=7.0 if k == 0 else 3.0, seed=seed * 101 + k * 17 + ix * 5 + iy)
        z += h
        s *= 0.68
    m.box(0, 0, z, 60, 60, 90, base=True, jitter=1.5, seed=seed + 9, taper=0.5)
    return m


def obelisk_mesh(height, width, seed=1):
    """A square tapered pillar with a pyramid tip, origin at the centre of the base."""
    m = Mesh()
    m.box(0, 0, 0, width * 1.5, width * 1.5, height * 0.06, base=True, jitter=0.6, seed=seed)
    m.box(0, 0, height * 0.06, width, width, height * 0.84, base=True, jitter=0.6, seed=seed + 1, taper=0.22)
    zt = height * 0.9
    m.box(0, 0, zt, width * 0.78, width * 0.78, height * 0.1, base=True, jitter=0.3, seed=seed + 2, taper=0.95)
    return m


def brazier_mesh(seed=1):
    """A bronze brazier: three legs, a ring and a wide bowl. About 70 cm tall, origin at the centre of the feet."""
    m = Mesh()
    for k in range(3):
        a = math.radians(120 * k + 20)
        m.box(math.cos(a) * 22, math.sin(a) * 22, 0, 6, 6, 40, base=True, jitter=0.3, seed=seed + k, taper=0.3)
    m.lathe(0, 0, 38, 44, 27, 29, sides=20, segments=1)
    m.lathe(0, 0, 44, 66, 29, 46, sides=24, segments=4, profile=[(0, 1.0), (0.55, 0.98), (1, 1.0)])
    return m


def mesa_mesh(radius, height, seed=1, sides=40, rings=16, base_z=-300.0):
    """A flat-topped butte with terraced, steep sides (hard/soft layers). Origin at the centre of the foot."""
    import random as _r
    rr = _r.Random(seed)
    layers = [rr.uniform(0.0, 1.0) for _ in range(8)]

    def P(i, j):
        th = 2 * math.pi * i / sides
        t = j / float(rings - 1)                    # 0 = foot, 1 = rim of the flat top
        k = min(int(t * 8), 7)
        f = t * 8 - k
        step = layers[k] * 0.10 * math.sin(math.pi * min(1.0, f * 1.4))
        n = fbm(math.cos(th) * 1.6 + seed, math.sin(th) * 1.6 + seed * 0.3, t * 2.0, 3, seed)
        r = radius * (1.0 - 0.38 * t + step) * (1.0 + 0.22 * n)
        z = base_z + (height - base_z) * t
        z += fbm(math.cos(th) * 3.0, math.sin(th) * 3.0, t * 5, 2, seed + 4) * height * 0.025
        return (math.cos(th) * r, math.sin(th) * r, z)
    m = Mesh()
    base = m.grid(sides, rings, P, wrap_u=True, flip=False)
    ring = [P(i, rings - 1) for i in range(sides)]       # flat top
    ctr = (0.0, 0.0, height)
    b = len(m.verts)
    m.verts.append(ctr)
    m.norms.append((0.0, 0.0, 1.0))
    for p in ring:
        m.verts.append(p)
        m.norms.append((0.0, 0.0, 1.0))
    for i in range(sides):
        m.tris.append((b, b + 1 + i, b + 1 + (i + 1) % sides))
    return m


def tube(points, radius, sides=6, jitter=0.0, seed=1):
    """A thin round tube (rope, pole) along a polyline of 3D points. Open ends (they sit inside posts)."""
    rr = random.Random(seed)
    m = Mesh()
    n = len(points)

    def P(i, j):
        a = points[max(j - 1, 0)]
        b = points[min(j + 1, n - 1)]
        d = norm_(sub_(b, a))
        up = (0.0, 0.0, 1.0) if abs(d[2]) < 0.95 else (1.0, 0.0, 0.0)
        s = norm_(cross_(d, up))
        u = cross_(s, d)
        th = 2 * math.pi * i / sides
        r = radius * (1.0 + (rr.uniform(-jitter, jitter) if jitter else 0.0))
        p = points[j]
        return (p[0] + (s[0] * math.cos(th) + u[0] * math.sin(th)) * r, p[1] + (s[1] * math.cos(th) + u[1] * math.sin(th)) * r,
                p[2] + (s[2] * math.cos(th) + u[2] * math.sin(th)) * r)
    m.grid(sides, n, P, wrap_u=True, flip=True)
    return m


def norm_(a):
    l = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


def sub_(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross_(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def cloth_mesh(w, h, waves=2.0, amp=8.0, seed=1, nu=14, nv=8, droop=0.0):
    """A hanging cloth in the x-z plane (x width, z from 0 down? no: z up from 0 to h), waving in y. Two sided. Origin at the bottom centre."""
    def P(i, j):
        u, v = i / float(nu - 1), j / float(nv - 1)
        y = amp * math.sin(u * waves * math.pi + seed) * (0.4 + 0.6 * v) + amp * 0.3 * math.sin(v * 5.0 + u * 3.0)
        return ((u - 0.5) * w, y, v * h - droop * u * (1 - u) * h)
    m = Mesh()
    m.grid(nu, nv, P, flip=False)
    m.grid(nu, nv, P, flip=True)
    return m


def plank_deck(length, width, board=26.0, gap=2.5, seed=1, top=0.0, thick=7.0):
    """Wooden boards laid across a walkway. The walkway runs along y (length) and the boards along x (width); the top is at z = top
    (every board within 0.4 cm of it). Origin at the centre. Returns a Mesh."""
    rr = random.Random(seed)
    m = Mesh()
    n = int(length // (board + gap))
    total = n * (board + gap)
    for i in range(n):
        y = -total / 2.0 + (i + 0.5) * (board + gap)
        w = width - rr.uniform(0, 6)
        m.box(rr.uniform(-1.5, 1.5), y, top - thick - rr.uniform(0, 0.4), w, board - rr.uniform(0, 3), thick, base=True, jitter=0.25, top_jitter=0.0, seed=seed * 1000 + i,
              yaw=rr.uniform(-0.6, 0.6))
    return m


def tent_mesh(w, d, h, eave=0.55, seed=1, nu=12, nv=6):
    """A canvas gable tent roof (no walls): ridge along x at height h, eaves at h*eave on y = +-d/2. Two sided. Origin: centre on the ground."""
    m = Mesh()
    for side in (-1, 1):
        def P(i, j, side=side):
            u, v = i / float(nu - 1), j / float(nv - 1)
            sag = 7.0 * math.sin(math.pi * u) * math.sin(math.pi * min(1.0, v * 1.0)) + 2.5 * math.sin(u * 17 + seed + v * 3)
            return ((u - 0.5) * w, side * v * d / 2.0, h - (h - h * eave) * v - sag)
        m.grid(nu, nv, P, flip=(side > 0))
        m.grid(nu, nv, P, flip=(side < 0))
    return m


def ramp_wedge(run, rise, width, seed=1):
    """A solid ramp wedge climbing along +x from (0, z=0) to (run, rise); the top is exactly the sloped plane."""
    m = Mesh()
    m.prism([(0.0, -40.0), (run, -40.0), (run, rise), (0.0, 0.0)], -width / 2.0, width / 2.0, jitter=0.0)
    return m


def mountain_mesh(radius, height, seed=1, sides=44, rings=12, ridge=0.55, base_z=-400.0):
    """A craggy distant mountain / mesa with fractal ridges. Origin at the centre of its base (z = 0 is the foot)."""
    def P(i, j):
        th = 2 * math.pi * i / sides
        t = j / float(rings - 1)                    # 0 = foot, 1 = summit
        n = fbm(math.cos(th) * 1.3 + seed, math.sin(th) * 1.3 + seed * 0.7, 0.0, 3, seed)
        r = radius * (1.0 - t) ** 0.9 * (1.0 + 0.35 * n)
        rid = ridged(math.cos(th) * 2.2 + 3 * t, math.sin(th) * 2.2, t * 2.0, 3, seed + 3)
        z = base_z + (height - base_z) * (t ** 0.8) * (1.0 - ridge + ridge * (0.5 + rid))
        z += fbm(math.cos(th) * 4 + t * 3, math.sin(th) * 4, t * 3, 3, seed + 9) * height * 0.05
        return (math.cos(th) * r, math.sin(th) * r, z)
    m = Mesh()
    m.grid(sides, rings, P, wrap_u=True, flip=False)
    return m
