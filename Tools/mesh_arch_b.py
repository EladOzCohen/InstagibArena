"""Architecture and terrain shapes for the map-B scripts (pure python, builds on mesh_b.Mesh)."""

import math
import random

from mesh_b import Mesh, clamp, fbm, lerp, ridged


# ------------------------------------------------------------------------------------------------ architecture
def stairs_mesh(width, steps, rise, run, seed=1, nose=3.0):
    """Stairs climbing along +x from x=0 (ground, z=0). Every step is a solid block from the ground (like mapkit.stairs).
    Tops are exactly level (the nav grid needs that); the sides and fronts are slightly irregular."""
    rng = random.Random(seed)
    m = Mesh()
    for i in range(steps):
        h = (i + 1) * rise
        w = width + rng.uniform(-3, 3)
        ext = nose if i else 0.0
        x0 = i * run - ext
        m.box(x0 + (run + ext) / 2.0, 0, 0, run + ext, w, h, base=True, jitter=0.8, top_jitter=0.0, seed=seed + i)
    return m


def wall_run(length, profile, thickness, seed=1, jitter=2.0, base_z=-60.0):
    """A wall running along +x from 0 to length, y from 0 to thickness; profile = list of (x0, x1, top_z).
    Block-size steps of different heights give a ruined skyline. One mesh."""
    rng = random.Random(seed)
    m = Mesh()
    for k, (x0, x1, top) in enumerate(profile):
        m.box((x0 + x1) / 2.0, thickness / 2.0, base_z, x1 - x0 + 0.2, thickness + rng.uniform(-1.5, 1.5), top - base_z, base=True,
              jitter=0.3, top_jitter=jitter, seed=seed * 31 + k)
    return m


def arch_frame(width, height, depth, tk=45.0, seed=1, segments=9):
    """A round-arched doorway frame in the x-z plane, protruding toward -y (y from -depth to 0).
    The opening is `width` wide and `height` high (to the top of the arch); x = 0 is the centre, z = 0 the floor."""
    rng = random.Random(seed)
    m = Mesh()
    R = width / 2.0
    zs = height - R                      # spring line
    for sgn in (-1, 1):                  # jambs, two blocks each
        cx = sgn * (R + tk / 2.0)
        h1 = zs * rng.uniform(0.45, 0.58)
        m.box(cx, -depth / 2.0, 0, tk + 6, depth, h1, base=True, jitter=0.8, seed=seed * 7 + sgn)
        m.box(cx + rng.uniform(-1, 1), -depth / 2.0, h1, tk + 4, depth, zs - h1 + 2, base=True, jitter=0.8, seed=seed * 7 + sgn + 5)
    for k in range(segments):
        a0 = math.pi * k / segments
        a1 = math.pi * (k + 1) / segments
        ex = tk * (1.35 if k == segments // 2 else 1.0)
        pts = [(R * math.cos(a0), zs + R * math.sin(a0)), (R * math.cos(a1), zs + R * math.sin(a1)),
               ((R + ex) * math.cos(a1), zs + (R + ex) * math.sin(a1)), ((R + ex) * math.cos(a0), zs + (R + ex) * math.sin(a0))]
        m.prism(pts, -depth + rng.uniform(0, 4), 0, jitter=0.6, seed=seed * 3 + k)
    return m


def lintel_frame(width, height, depth, tk=45.0, seed=1):
    """A square doorway frame with a heavy lintel (opening width x height, floor z = 0, x = 0 centre, protrudes toward -y)."""
    m = Mesh()
    for sgn in (-1, 1):
        m.box(sgn * (width / 2.0 + tk / 2.0), -depth / 2.0, 0, tk, depth, height, base=True, jitter=0.8, seed=seed + sgn)
    m.box(0, -depth / 2.0 - 4, height - 1, width + tk * 2.0 + 24, depth + 8, tk * 0.9, base=True, jitter=0.8, seed=seed + 4)
    m.box(0, -depth / 2.0 - 8, height + tk * 0.9 - 2, width + tk * 2.0 + 44, depth + 16, tk * 0.35, base=True, jitter=0.8, seed=seed + 5)
    return m


def frieze(length, height, depth, seed=1, unit=60.0):
    """A band of raised squares (a stylised meander) in the x-z plane, protruding toward -y."""
    rng = random.Random(seed)
    m = Mesh()
    m.box(length / 2.0, -depth * 0.3, 0, length, depth * 0.6, height, base=True, jitter=0.5, seed=seed)
    n = int(length // unit)
    for i in range(n):
        x = (i + 0.5) * length / n
        if (i + int(rng.random() * 2)) % 3 == 0:
            continue
        m.box(x, -depth * 0.6 - depth * 0.25, height * 0.18, length / n * 0.7, depth * 0.5, height * 0.64, base=True, jitter=0.6, seed=seed + i)
    return m


def cornice(length, depth, height, seed=1):
    """A projecting cornice (3 stepped courses), runs along +x, protrudes toward -y from y=0."""
    m = Mesh()
    h = height / 3.0
    for k in range(3):
        d = depth * (0.45 + 0.28 * k)
        m.box(length / 2.0, -d / 2.0 + 1, k * h, length, d, h + 0.5, base=True, jitter=0.3, seed=seed + k)
    return m


# ------------------------------------------------------------------------------------------------ terrain and cliffs
class Strata:
    """Rock layers: boundaries at random heights, each with a hardness (hard layers bulge out, soft ones recede)."""

    def __init__(self, seed, vmax, thickness=(110.0, 320.0)):
        rng = random.Random(seed)
        self.b = [0.0]
        self.hard = []
        while self.b[-1] < vmax:
            self.b.append(self.b[-1] + rng.uniform(*thickness))
            self.hard.append(rng.random())

    def layer(self, v):
        for k in range(len(self.hard)):
            if v < self.b[k + 1]:
                return k
        return len(self.hard) - 1

    def profile(self, v, amp=70.0):
        k = self.layer(v)
        f = clamp((v - self.b[k]) / (self.b[k + 1] - self.b[k]), 0.0, 1.0)
        h = self.hard[k]
        bulge = amp * (h - 0.4)
        lip = amp * 0.35 * h * (math.sin(math.pi * f) ** 0.4)
        talus = -amp * 0.55 * (1.0 - h) * (1.0 - f) ** 2
        return bulge + lip + talus


def cliff_strip(width, z0, z1, off_fn, depth, cell=70.0, top_fn=None, skirt_top=False, skirt_bottom=False):
    """One horizontal strip of a cliff wall (closed shell). Local frame: x along the wall 0..width, the visible face
    looks toward -y, rock mass behind it to y = depth, z from z0 to z1. off_fn(u, z) = how far the face stands out
    toward the viewer (cm, can be negative). Adjacent strips with the same off_fn meet without cracks."""
    m = Mesh()
    nu = max(2, int(width / cell) + 1)
    nv = max(2, int(round((z1 - z0) / (cell * 0.8))) + 1)
    us = [width * i / (nu - 1) for i in range(nu)]
    zs = [lerp(z0, z1, j / float(nv - 1)) for j in range(nv)]

    def front(i, j):
        z = zs[j]
        if top_fn and j == nv - 1:
            z = z1 + top_fn(us[i])
        return (us[i], -off_fn(us[i], z), z)
    m.grid(nu, nv, front)
    ymax = depth
    ztop = z1 + (max(top_fn(u) for u in us) if top_fn else 0.0)
    m.poly([(0, ymax, z0), (width, ymax, z0), (width, ymax, ztop), (0, ymax, ztop)], (0, 1, 0))
    for i in (0, nu - 1):                                    # side skirts
        sx = -1.0 if i == 0 else 1.0
        for j in range(nv - 1):
            a, b = front(i, j), front(i, j + 1)
            m.poly([a, b, (b[0], ymax, b[2]), (a[0], ymax, a[2])], (sx, 0, 0))
    if skirt_top:
        for i in range(nu - 1):
            a, b = front(i, nv - 1), front(i + 1, nv - 1)
            m.poly([a, b, (b[0], ymax, b[2]), (a[0], ymax, a[2])], (0, 0, 1))
    if skirt_bottom:
        for i in range(nu - 1):
            a, b = front(i, 0), front(i + 1, 0)
            m.poly([a, b, (b[0], ymax, b[2]), (a[0], ymax, a[2])], (0, 0, -1))
    return m


def heightfield(x0, y0, x1, y1, cell, h_fn, floor_z=-40.0):
    """A closed solid heightfield (dunes, drifts, mounds): top surface z = h_fn(x, y), sides and bottom closed."""
    m = Mesh()
    nx = max(2, int((x1 - x0) / cell) + 1)
    ny = max(2, int((y1 - y0) / cell) + 1)
    xs = [lerp(x0, x1, i / float(nx - 1)) for i in range(nx)]
    ys = [lerp(y0, y1, j / float(ny - 1)) for j in range(ny)]
    m.grid(nx, ny, lambda i, j: (xs[i], ys[j], h_fn(xs[i], ys[j])))
    m.poly([(x0, y0, floor_z), (x1, y0, floor_z), (x1, y1, floor_z), (x0, y1, floor_z)], (0, 0, -1))
    for j in range(ny - 1):
        for xi, sx in ((0, -1.0), (nx - 1, 1.0)):
            a, b = (xs[xi], ys[j], h_fn(xs[xi], ys[j])), (xs[xi], ys[j + 1], h_fn(xs[xi], ys[j + 1]))
            m.poly([a, b, (b[0], b[1], floor_z), (a[0], a[1], floor_z)], (sx, 0, 0))
    for i in range(nx - 1):
        for yj, sy in ((0, -1.0), (ny - 1, 1.0)):
            a, b = (xs[i], ys[yj], h_fn(xs[i], ys[yj])), (xs[i + 1], ys[yj], h_fn(xs[i + 1], ys[yj]))
            m.poly([a, b, (b[0], b[1], floor_z), (a[0], a[1], floor_z)], (0, sy, 0))
    return m
