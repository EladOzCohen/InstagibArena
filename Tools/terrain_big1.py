"""DM-Citadel terrain (pure python, no unreal import): the height function of the whole map and everything that depends on it.

World: x is the long axis (red keep west, blue keep east), y north (+) / south (-), z up, cm. Playable rectangle: |x| < 6150, -3900 < y < 3550.
Layers (see height()):
  valley    rolling meadow around z = 0 with mounds for cover and a flatter village area
  hills     the two keep plateaus (z = PZ), the north neck behind each keep and the high ridge that joins them along the north edge
  river     N -> S, x about 0 +- 400, water at z = WATER; a gorge where it cuts through the ridge
  edge      outside the playable rectangle the ground climbs steeply (cliffs), continuous with the inside
  pads      flat spots for buildings, bridges, hatches (added by the map script before the mesh is built)
"""

import math

from mesh_b import fbm, ridged, smoothstep, clamp, lerp

PZ = 520.0
CX = 5000.0            # keep centre |x|
KEEP_HX, KEEP_HY = 1750.0, 1550.0
RUN_FRONT, RUN_BACK, RUN_SOUTH = 1900.0, 520.0, 1900.0
NECK_U, NECK_Y0, NECK_Y1 = 850.0, 1300.0, 2800.0
RIDGE_Y0, RIDGE_Y1, RIDGE_X = 2650.0, 3550.0, 5900.0
RUN_STEEP = 470.0
X_EDGE, Y_NORTH, Y_SOUTH = 6950.0, 3550.0, -3900.0
WATER = -40.0
BED = -110.0


def smin_(a, b, k=0.08):
    return max(a, b)


def prof(t):
    """1 inside, falls to 0 at t = 1 (gentle at both ends)."""
    if t <= 0.0:
        return 1.0
    if t >= 1.0:
        return 0.0
    s = t * t * (3.0 - 2.0 * t)
    return 1.0 - (0.8 * t + 0.2 * s)


def river_x(y):
    return 380.0 * math.sin(y / 1250.0 + 0.6) + 130.0 * math.sin(y / 430.0 + 2.0)


def river_dx(y):
    return 380.0 / 1250.0 * math.cos(y / 1250.0 + 0.6) + 130.0 / 430.0 * math.cos(y / 430.0 + 2.0)


def ridge_w(y):
    return smoothstep(2000.0, 2700.0, y)


MOUNDS = [  # x, y, radius, height  (cover hills in the valley)
    (-1500, 900, 380, 130), (-1100, -1100, 420, 150), (-2200, 300, 520, 190), (-1900, -2100, 450, 160), (-2600, 1500, 420, 120),
    (1700, 800, 400, 140), (1250, -1250, 380, 120), (2150, 400, 500, 200), (1800, -2200, 430, 150), (2700, 1700, 400, 130),
    (-700, 1750, 330, 100), (800, 1900, 360, 110), (-300, -3000, 600, 180), (-2300, -3200, 700, 200), (2300, -3100, 700, 210),
    (1000, -600, 250, 80), (-900, 450, 260, 80), (-3300, -400, 480, 160), (3300, -300, 520, 170), (0, 1100, 300, 60),
]


class Terrain:
    def __init__(self, seed=7):
        self.seed = seed
        self.pads = []        # (cx, cy, hx, hy, yaw_deg, z, blend)
        self._cache = {}

    # -------------------------------------------------------------------------------- pads
    def add_pad(self, cx, cy, hx, hy, z, blend=200.0, yaw=0.0):
        self.pads.append((cx, cy, hx, hy, yaw, z, blend))

    def _pad_weight(self, x, y, p):
        cx, cy, hx, hy, yaw, z, blend = p
        a = math.radians(-yaw)
        dx, dy = x - cx, y - cy
        lx, ly = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
        ox, oy = max(0.0, abs(lx) - hx), max(0.0, abs(ly) - hy)
        d = math.hypot(ox, oy)
        return 1.0 - smoothstep(0.0, blend, d)

    # -------------------------------------------------------------------------------- layers
    def hill_f(self, x, y):
        """0..1 height fraction of the high ground (1 = plateau / ridge top). Returns (f, f_keep, f_ridge)."""
        ax = abs(x)
        s = -1.0 if x < 0 else 1.0
        u = -s * (x - s * CX)                              # towards the map centre
        # keep plateau
        ou = max(0.0, u - KEEP_HX) / RUN_FRONT if u > 0 else max(0.0, -u - KEEP_HX) / RUN_BACK
        oy = max(0.0, abs(y) - KEEP_HY) / (RUN_SOUTH if y < 0 else RUN_STEEP)
        fk = prof(math.hypot(ou, oy))
        # neck behind the keep (north)
        nu = max(0.0, abs(u) - NECK_U) / RUN_STEEP
        ny = max(0.0, NECK_Y0 - y) / RUN_STEEP
        fn = prof(math.hypot(nu, ny)) if y < NECK_Y1 + 600 else 1.0
        # ridge along the north edge
        rx = max(0.0, ax - RIDGE_X) / RUN_STEEP
        ry = max(0.0, RIDGE_Y0 - y) / RUN_STEEP
        fr = prof(math.hypot(rx, ry))
        f = max(fk, fn, fr)
        return f, max(fk, 0.0), max(fn, fr)

    def valley(self, x, y):
        s = self.seed
        vil = 1.0 - smoothstep(900.0, 1900.0, math.hypot(x * 0.8, y * 1.05 + 150.0))      # flatter around the village
        amp = 0.25 + 0.75 * (1.0 - vil)
        z = 48.0 * fbm(x / 2300.0, y / 2100.0, 0.0, 3, s) + 16.0 * fbm(x / 650.0, y / 600.0, 0.0, 2, s + 3) + 5.0 * fbm(x / 230.0, y / 230.0, 0.0, 2, s + 9)
        z *= amp
        for mx, my, r, h in MOUNDS:
            d2 = ((x - mx) ** 2 + (y - my) ** 2) / (r * r)
            if d2 < 6.0:
                z += 0.62 * h * math.exp(-d2 * 1.15) * (1.0 - 0.35 * vil)
        z += 260.0 * smoothstep(-2300.0, -3850.0, y) * (0.7 + 0.3 * fbm(x / 1500.0, y / 700.0, 0.0, 2, s + 4))      # the south slope
        return z

    def inner(self, x, y):
        """Height inside the playable rectangle rules (no edge wall, no pads)."""
        zv = self.valley(x, y)
        f, fk, fr = self.hill_f(x, y)
        z = zv * (1.0 - f) + PZ * f
        # the ridge top and the neck are not billiard tables
        if f > 0.0:
            wrough = max(0.0, fr - fk * 0.999) * smoothstep(0.55, 1.0, f)
            z += wrough * (34.0 * fbm(x / 520.0, y / 430.0, 0.0, 3, self.seed + 21) + 14.0 * fbm(x / 170.0, y / 170.0, 0.0, 2, self.seed + 22))
            if f < 0.995:      # craggy flanks
                steep = (1.0 - abs(2.0 * f - 1.0)) * (1.0 if fr > fk else 0.0)
                z += steep * (70.0 * ridged(x / 330.0, y / 300.0, 0.0, 2, self.seed + 31) - 28.0 + 40.0 * fbm(x / 120.0, y / 120.0, 0.0, 2, self.seed + 33))
        for p in self.pads:
            w = self._pad_weight(x, y, p)
            if w > 0.0:
                z = lerp(z, p[5], w)
        # river
        yy = y
        r = abs(x - river_x(yy)) / math.sqrt(1.0 + river_dx(yy) ** 2)
        wr = ridge_w(yy) if yy < Y_NORTH + 800 else 1.0
        rin = 240.0
        rout = 850.0 - 420.0 * wr
        if r < rout:
            k = 1.0 if r < rin else math.cos((r - rin) / (rout - rin) * math.pi / 2.0) ** 2
            bed = BED + 40.0 * wr + 10.0 * fbm(x / 300.0, y / 300.0, 0.0, 2, 5)
            z = z * (1.0 - k) + bed * k
        return z

    def height(self, x, y):
        key = (round(x, 3), round(y, 3))
        v = self._cache.get(key)
        if v is not None:
            return v
        cx = clamp(x, -X_EDGE, X_EDGE)
        cy = clamp(y, Y_SOUTH, Y_NORTH)
        z = self.inner(cx, cy)
        d = math.hypot(x - cx, y - cy)
        if d > 0.0:
            n = fbm(x / 400.0, y / 400.0, 0.0, 3, self.seed + 41)
            terr = 90.0 * math.sin(d / 260.0 + 2.0 * n)
            z += min(2300.0, 1.7 * d + terr * smoothstep(0.0, 500.0, d) + 160.0 * ridged(x / 700.0, y / 700.0, 0.0, 2, self.seed + 43) * smoothstep(0.0, 700.0, d))
        if len(self._cache) > 400000:
            self._cache.clear()
        self._cache[key] = z
        return z

    def slope_deg(self, x, y, e=60.0):
        dzx = (self.height(x + e, y) - self.height(x - e, y)) / (2 * e)
        dzy = (self.height(x, y + e) - self.height(x, y - e)) / (2 * e)
        return math.degrees(math.atan(math.hypot(dzx, dzy)))


# ---------------------------------------------------------------------------------------------- slot choice for the mesh
SLOT_GRASS, SLOT_DIRT, SLOT_ROCK, SLOT_BED = 0, 1, 2, 3


def slot_for(nz, z, x, y, seed=3):
    n = 0.05 * fbm(x / 140.0, y / 140.0, 0.0, 2, seed)
    if z < WATER - 12.0 + 20.0 * fbm(x / 90.0, y / 90.0, 0.0, 2, seed + 5):
        return SLOT_BED
    t = nz + n
    if t < 0.80:
        band = int((z + 40.0 + 60.0 * fbm(x / 500.0, y / 500.0, 0.0, 2, seed + 8)) / 150.0)
        return 4 if band % 2 else SLOT_ROCK
    return SLOT_GRASS
