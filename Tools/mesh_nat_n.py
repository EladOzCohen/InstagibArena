"""Natural rock shapes for the NATURE pass (Canyon, Glacier, Temple, Forge): pure python, builds on mesh_b.Mesh.

  Layers          rock strata whose boundaries wander (no straight seams between strips of different rock)
  cliff_strip2    a strip of cliff between two wavy boundaries (shared with the neighbour strip, no cracks), optional rough top
  talus_skirt     the debris slope at the foot of a cliff
  rock_mesh       an irregular boulder (lumpy, ridged, optional bedding ledges, optional crystal ice look)
  rock_pile       several boulders merged into one mesh (talus piles, cairns, rubble)
  pinnacle_mesh   a tall rock needle / hoodoo with ledges
  snow_cap        a thin lumpy slab that follows a box top (roof snow) with a drooping rim
  icicles         a row of icicle cones hanging from an edge
Triangle order convention: (b - a) x (c - a) points out of the solid, like mesh_b.
"""

import math
import random

from mesh_b import Mesh, clamp, fbm, lerp, ridged, vnoise, smoothstep


def plateau(u, h, su, sh, seed, lo=0.38, hi=0.62):
    """0..1 blocky noise: flat-topped patches of size about su x sh with soft edges (jointed rock blocks)."""
    return smoothstep(lo, hi, vnoise(u / su, h / sh, 0.0, seed))


class Layers:
    """Rock strata between the heights `bounds` (ascending). Boundaries wander up and down by about `wob` cm along u."""

    def __init__(self, bounds, seed, wob=45.0, wob_len=520.0, rim=None, rim_from=None):
        """rim(u): height change of the top of the wall (a ragged skyline); it is spread over the strata above `rim_from`
        so that the layers stay in order."""
        self.b = list(bounds)
        rng = random.Random(seed)
        self.hard = [rng.random() for _ in range(len(self.b) - 1)]
        self.seed = seed
        self.wob = wob
        self.len = wob_len
        self.rim = rim
        self.rim_from = rim_from if rim_from is not None else self.b[-1] - 1200.0
        self._cache = {}

    def boundary(self, k, u):
        inner = 0 < k < len(self.b) - 1
        if not inner and not (self.rim and k == len(self.b) - 1):
            return self.b[k]
        key = (k, round(u, 1))
        v = self._cache.get(key)
        if v is None:
            v = self.b[k]
            if inner:
                v += self.wob * (0.8 * fbm(u / self.len + k * 3.1, k * 1.7, 0.0, 2, self.seed + k)
                                 + 0.45 * fbm(u / 140.0 + k, 7.3, 0.0, 1, self.seed + k * 5))
            if self.rim:
                s = clamp((self.b[k] - self.rim_from) / max(1.0, self.b[-1] - self.rim_from), 0.0, 1.0)
                v += self.rim(u) * s
            if len(self._cache) > 200000:
                self._cache.clear()
            self._cache[key] = v
        return v

    def locate(self, u, z):
        """(layer index, 0..1 position inside the layer) at (u, z)."""
        n = len(self.b) - 1
        for k in range(n):
            top = self.boundary(k + 1, u)
            if z < top or k == n - 1:
                lo = self.boundary(k, u)
                return k, clamp((z - lo) / max(1.0, top - lo), 0.0, 1.0)
        return n - 1, 1.0

    def profile(self, u, z, amp=80.0):
        """How far the rock at (u, z) stands out because of the layering: hard layers bulge with an overhanging lip at the
        top, soft layers recede into a concave slope."""
        k, f = self.locate(u, z)
        h = self.hard[k]
        bulge = amp * (h - 0.45)
        lip = amp * 0.45 * h * (math.sin(math.pi * clamp(f, 0.0, 1.0)) ** 0.5) * (0.5 + 0.5 * smoothstep(0.55, 0.95, f))
        talus = -amp * 0.6 * (1.0 - h) * (1.0 - f) ** 2.2
        return bulge + lip + talus


def cliff_strip2(width, z_lo, z_hi, off_fn, depth, cell=70.0, lo_wavy=None, hi_wavy=None, top_fn=None, cap=False, cap_fn=None,
                 skirt_bottom=False, skirt_top=False):
    """One horizontal strip of a cliff wall (closed shell). x along the wall 0..width, the visible face looks toward -y,
    the rock mass behind it reaches y = depth. Rows run from the lower boundary z_lo(u) to the upper boundary z_hi(u)
    (callables taking u, or floats). off_fn(u, z) = how far the face stands out toward the viewer.
    Strips that share a boundary function and the same off_fn meet without cracks.
    top_fn(u): extra height added to the top row (the ragged rim). cap=True closes the top with a rough surface
    (cap_fn(u, y) = extra height of the ground behind the rim)."""
    lo_f = z_lo if callable(z_lo) else (lambda u, c=z_lo: c)
    hi_f = z_hi if callable(z_hi) else (lambda u, c=z_hi: c)
    m = Mesh()
    nu = max(2, int(width / cell) + 1)
    zmid = 0.5 * (lo_f(0.0) + hi_f(0.0))
    nv = max(2, int(round((hi_f(0.0) - lo_f(0.0)) / (cell * 0.75))) + 1)
    us = [width * i / (nu - 1) for i in range(nu)]
    rows = {}

    def zrow(i, j):
        a = lo_f(us[i])
        b = hi_f(us[i])
        z = lerp(a, b, j / float(nv - 1))
        if top_fn and j == nv - 1:
            z += top_fn(us[i])
        return z

    def front(i, j):
        key = (i, j)
        p = rows.get(key)
        if p is None:
            z = zrow(i, j)
            zq = z - (top_fn(us[i]) if (top_fn and j == nv - 1) else 0.0)
            p = (us[i], -off_fn(us[i], zq), z)
            rows[key] = p
        return p
    m.grid(nu, nv, front)
    ymax = depth
    zlo_all = min(lo_f(u) for u in us)
    ztop = max(front(i, nv - 1)[2] for i in range(nu))
    nc = 7
    yf = [front(i, nv - 1) for i in range(nu)]

    def C(i, jj):
        t = jj / float(nc - 1)
        y = lerp(yf[i][1], ymax, t)
        z = yf[i][2]
        if cap_fn:
            z += cap_fn(us[i], y) * smoothstep(0.0, 0.25, t) * (1.0 - 0.5 * smoothstep(0.75, 1.0, t))
        return (us[i], y, z)
    if cap:
        capz = max(C(i, jj)[2] for i in range(nu) for jj in range(nc))
    else:
        capz = ztop
    m.poly([(0, ymax, zlo_all), (width, ymax, zlo_all), (width, ymax, capz), (0, ymax, capz)], (0, 1, 0))
    for i in (0, nu - 1):
        sx = -1.0 if i == 0 else 1.0
        for j in range(nv - 1):
            a, b = front(i, j), front(i, j + 1)
            m.poly([a, b, (b[0], ymax, b[2]), (a[0], ymax, a[2])], (sx, 0, 0))
    if cap:
        m.grid(nu, nc, C)
        for i in (0, nu - 1):
            sx = -1.0 if i == 0 else 1.0
            for jj in range(nc - 1):
                a, b = C(i, jj), C(i, jj + 1)
                m.poly([a, b, (b[0], b[1], b[2] - 300.0), (a[0], a[1], a[2] - 300.0)], (sx, 0, 0))
    if skirt_top and not cap:
        for i in range(nu - 1):
            a, b = front(i, nv - 1), front(i + 1, nv - 1)
            m.poly([a, b, (b[0], ymax, b[2]), (a[0], ymax, a[2])], (0, 0, 1))
    if skirt_bottom:
        for i in range(nu - 1):
            a, b = front(i, 0), front(i + 1, 0)
            m.poly([a, b, (b[0], ymax, b[2]), (a[0], ymax, a[2])], (0, 0, -1))
    return m


def patch_mesh(sx, sy, seed, peak=7.0, cell=55.0, floor_z=-14.0, lumps=1.5, under=-4.0, wobble=0.55):
    """A thin organic ground patch (dry mud, gravel, a worn path): a heightfield whose outline is where the noisy surface
    crosses the floor (z = 0), so the edge is irregular, not a rectangle. Place it with its z = 0 on the floor.
    Closed, centred on the origin, footprint about sx x sy."""
    import mesh_arch_b as ma

    def h(x, y):
        u, v = x / (sx / 2.0), y / (sy / 2.0)
        r = math.hypot(u, v)
        n = fbm(x / 130.0 + seed, y / 130.0, 0.0, 3, seed)
        edge = 1.0 - r + wobble * n
        top = under + (peak - under) * smoothstep(0.0, 0.45, edge)
        return top + lumps * fbm(x / 38.0, y / 38.0, 2.0, 2, seed + 3) * smoothstep(0.0, 0.4, edge)
    return ma.heightfield(-sx / 2.0, -sy / 2.0, sx / 2.0, sy / 2.0, cell, h, floor_z=floor_z)


def talus_skirt(width, height_fn, out_fn, cell=60.0, face_fn=None, seed=1, depth_back=80.0):
    """The debris slope at the foot of a cliff in the cliff's local frame (face looks toward -y, floor at z = 0).
    height_fn(u): how high the heap reaches at the cliff face; out_fn(u): how far it reaches onto the floor (cm);
    face_fn(u): y of the cliff face at the foot (negative = toward the viewer). Not closed (only the visible top)."""
    m = Mesh()
    nu = max(2, int(width / cell) + 1)
    nv = 7
    us = [width * i / (nu - 1) for i in range(nu)]

    def P(i, j):
        u = us[i]
        t = -0.35 + 1.35 * j / float(nv - 1)         # t < 0: tucked into the cliff, t = 1: the toe on the floor
        y0 = face_fn(u) if face_fn else 0.0
        out = out_fn(u)
        tt = clamp(t, 0.0, 1.0)
        h = height_fn(u) * (1.0 - tt) ** 1.5
        h += (22.0 * fbm(u / 90.0, t * 3.0, 0.0, 2, seed) * math.sin(math.pi * tt) ** 0.7
              + 10.0 * ridged(u / 55.0, t * 4.0, 1.0, 2, seed + 3) * (1.0 - tt))
        if tt > 0.9:
            h = min(h, 6.0 * (1.0 - tt) / 0.1)
        return (u, y0 - t * out, max(h, 0.0) - (3.0 if tt >= 1.0 else 0.0))
    m.grid(nu, nv, P, flip=True)
    return m


# ------------------------------------------------------------------------------------------------ boulders
def rock_mesh(rx, ry, rz, seed=1, nu=22, nv=13, amp=0.32, ridge=0.35, bedding=0.0, bed_freq=5.0, flat_bottom=0.3, ice=False,
              freq=1.5):
    """An irregular boulder centred on the origin in x/y with its flat bottom at z = 0 (about rz tall). Lumpy fractal noise,
    optional sharp ridged creases and horizontal bedding ledges. ice=True: smoother with a few crystal-like facets."""
    def P(i, j):
        th = 2 * math.pi * i / nu
        ph = math.pi * (j / float(nv - 1))
        ux, uy, uz = math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph)
        n = fbm(ux * freq + 7.3, uy * freq + 1.1, uz * freq + 4.7, 3, seed)
        r = 1.0 + amp * n
        if ridge:
            r += ridge * amp * (ridged(ux * freq * 1.7 + 3.0, uy * freq * 1.7, uz * freq * 1.7 + 1.0, 2, seed + 7) - 0.45)
        if bedding:
            s = math.sin(uz * bed_freq * math.pi + 4.0 * fbm(ux * 1.2, uy * 1.2, 0.0, 2, seed + 11))
            r += bedding * (s * 0.5 if not ice else 0.0)
            r -= bedding * 0.5 * (abs(s) ** 6)
        if ice:
            r = 1.0 + amp * 0.6 * n + 0.10 * (ridged(ux * 3.0 + 1.0, uy * 3.0, uz * 3.0, 2, seed + 5) - 0.5)
        x, y, z = ux * rx * r, uy * ry * r, uz * rz * r
        if z < -rz * flat_bottom:
            z = -rz * flat_bottom
        return (x, y, z + rz * flat_bottom)
    m = Mesh()
    m.grid(nu, nv, P, wrap_u=True, flip=True)
    for i in range(nu):                                  # the pole rows have no u-tangent: give them the vertical normal
        m.norms[i * nv] = (0.0, 0.0, 1.0)
        m.norms[i * nv + nv - 1] = (0.0, 0.0, -1.0)
    return m


def rock_pile(seed, count=7, spread=160.0, size=(35.0, 110.0), height_k=0.7, bedding=0.06, mound=0.0):
    """Several boulders merged into one mesh (a talus heap, a cairn, rubble). Footprint about 2*spread, origin on the ground."""
    rng = random.Random(seed)
    out = Mesh()
    placed = []
    for k in range(count):
        s = rng.uniform(*size) * (1.3 - 0.6 * k / max(1, count - 1))
        for _ in range(12):
            a = rng.uniform(0, 2 * math.pi)
            d = abs(rng.gauss(0.0, spread * 0.45)) if k else 0.0
            x, y = math.cos(a) * d, math.sin(a) * d
            if all(math.hypot(x - px, y - py) > 0.55 * (s + ps) for px, py, ps in placed):
                break
        placed.append((x, y, s))
        rk = rock_mesh(s, s * rng.uniform(0.7, 1.15), s * height_k * rng.uniform(0.7, 1.2), seed=seed * 31 + k, nu=14, nv=9,
                       amp=rng.uniform(0.25, 0.4), bedding=bedding, bed_freq=rng.uniform(3, 6), flat_bottom=0.35)
        # yaw and lean
        yaw = rng.uniform(0, 360)
        lean = rng.uniform(-14, 14)
        rk.verts = [_xf(v, yaw, lean) for v in rk.verts]
        rk.norms = [_xf(n, yaw, lean) for n in rk.norms]
        out.append(rk, offset=(x, y, -s * height_k * 0.18))
    return out


def _xf(p, yaw, lean):
    c, s = math.cos(math.radians(lean)), math.sin(math.radians(lean))
    x, z = p[0] * c - p[2] * s, p[0] * s + p[2] * c
    c2, s2 = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return (x * c2 - p[1] * s2, x * s2 + p[1] * c2, z)


def pinnacle_mesh(height, radius, seed=1, sides=26, mush=0.0, base_z=0.0, taper=0.55):
    """A tall rock needle / hoodoo, axis through the origin, from base_z up to `height`. Ledges every ~height/7, noise on the
    radius, a rounded irregular top. mush > 0 swells the radius at some ledges (a cap rock on a thin stem)."""
    rng = random.Random(seed)
    ledge = [rng.uniform(0.7, 1.0) for _ in range(9)]
    segs = max(10, int((height - base_z) / 55.0))
    m = Mesh()

    def R(th, t):
        k = min(int(t * 8), 7)
        f = t * 8 - k
        step = (ledge[k] - 0.85) * 0.22 * math.sin(math.pi * min(1.0, f * 1.2))
        n = fbm(math.cos(th) * 1.5 + seed, math.sin(th) * 1.5, t * 4.0, 3, seed)
        shape = (1.0 - taper * t ** 1.4)
        if mush:
            shape *= 1.0 + mush * (smoothstep(0.62, 0.72, t) - smoothstep(0.9, 1.0, t)) * 1.6 - mush * 0.35 * smoothstep(0.1, 0.5, t) * (1.0 - smoothstep(0.55, 0.65, t))
        cap = 1.0 - smoothstep(0.93, 1.0, t) ** 2 * 0.9
        return radius * (shape + step) * (1.0 + 0.3 * n) * cap
    m.lathe(0, 0, base_z, height, 1.0, 1.0, sides=sides, segments=segs, rfn=lambda th, t: R(th, t) / 1.0, cap_bottom=False, cap_top=True)
    return m


# ------------------------------------------------------------------------------------------------ snow
def snow_cap(w, d, seed=1, thick=16.0, cell=28.0, lump=4.0, under=-6.0, edge_noise=0.22):
    """A lumpy snow blanket for a flat roof or a ledge: about w x d, centred on the origin, to be placed with z = 0 on the
    roof top. It is a heightfield that dips below z = 0 towards its border, so the visible outline is where the noisy
    surface crosses the roof: irregular, thinning to nothing, never a disc or a rectangle. Open below (the roof hides it)."""
    hw, hd = w / 2.0, d / 2.0
    nx = max(3, int(w / cell) + 1)
    ny = max(3, int(d / cell) + 1)

    def H(u, v):
        e = ((abs(u) / hw) ** 3.0 + (abs(v) / hd) ** 3.0) ** (1.0 / 3.0)
        e += edge_noise * fbm(u / 95.0 + seed, v / 95.0, 3.0, 3, seed + 6)
        body = thick * (0.65 + 0.5 * fbm(u / 130.0 + seed, v / 130.0, 0.0, 3, seed))
        z = under + (body - under) * smoothstep(1.0, 0.55, e)
        return z + lump * fbm(u / 30.0, v / 30.0, 2.0, 2, seed + 2) * smoothstep(1.0, 0.7, e)
    m = Mesh()
    m.grid(nx, ny, lambda i, j: (-hw + w * i / (nx - 1), -hd + d * j / (ny - 1), H(-hw + w * i / (nx - 1), -hd + d * j / (ny - 1))))
    return m

def icicles(length, count, seed=1, size=(8.0, 26.0), drop=(18.0, 70.0)):
    """A row of icicle cones along +x from 0 to `length`, hanging down from z = 0 (tips at -drop). Origin at the left end."""
    rng = random.Random(seed)
    m = Mesh()
    for k in range(count):
        x = (k + rng.uniform(0.15, 0.85)) * length / count
        r = rng.uniform(*size) * 0.5
        h = rng.uniform(*drop) * (0.4 + 0.6 * rng.random())
        sides = 5
        ring = [(x + math.cos(2 * math.pi * s / sides) * r, math.sin(2 * math.pi * s / sides) * r, 0.0) for s in range(sides)]
        tip = (x + rng.uniform(-2, 2), rng.uniform(-2, 2), -h)
        for s in range(sides):
            a, b = ring[s], ring[(s + 1) % sides]
            mid = ((a[0] + b[0]) / 2.0 - x, (a[1] + b[1]) / 2.0, -0.2)
            m.poly([a, b, tip], mid)
    return m


def block_heap(seed, count=7, spread=140.0, size=(70.0, 150.0)):
    """A heap of fallen cut stone blocks (chipped corners, tilted, some stacked), origin on the ground."""
    rng = random.Random(seed)
    m = Mesh()
    for k in range(count):
        sx = rng.uniform(*size)
        sy = sx * rng.uniform(0.5, 0.9)
        sz = sx * rng.uniform(0.3, 0.6)
        a = rng.uniform(0, 2 * math.pi)
        d = abs(rng.gauss(0.0, spread * 0.5))
        z0 = -6.0 if k < count * 0.6 else rng.uniform(20.0, 55.0)
        m.box(math.cos(a) * d, math.sin(a) * d, z0, sx, sy, sz, yaw=rng.uniform(0, 360), pitch=rng.uniform(-12, 12), roll=rng.uniform(-12, 12),
              jitter=sx * 0.05, seed=seed * 17 + k, base=True)
    return m
