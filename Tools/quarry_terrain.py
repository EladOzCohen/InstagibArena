"""DM-Quarry terrain (pure python, no unreal import): the height function of the whole map, haul roads, tunnels and checks.

x is the long axis (red base west, blue base east), the map is mirror symmetric about x = 0 in everything that matters for play
(only cosmetic noise differs). 1 uu = 1 cm.

  H(x, y)             terrain height (pit with terraces, plateau, haul roads, heaps, cliff walls around the map)
  tunnel cells         underground corridors at z = TZ, entered by declines, see tunnel_cells()
  main()               prints a nav connectivity estimate and writes Saved/quarry_top.png (run with UE's embedded python)
"""

import math
import os
import random
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mesh_b import fbm, ridged, vnoise  # noqa: E402


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def S(x, a, b):
    """smoothstep"""
    if b == a:
        return 0.0 if x < a else 1.0
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------------------------------------ layout constants
PX, PY = 6600.0, 4300.0          # half size of the playable rectangle
CX, CY = 0.0, 250.0              # centre of the pit
A, B = 3900.0, 2500.0            # semi axes of the pit rim
ZA, ZB, ZF = -450.0, -900.0, -1350.0     # bench A, bench B, floor
PONDX, PONDY, PONDRX, PONDRY = 0.0, 150.0, 900.0, 400.0
WATER_Z = ZF - 28.0
BASE_X = 5300.0                  # |x| of the flag rooms
TZ = -450.0                      # tunnel floor
TH = 360.0                       # tunnel height
GRID = 80.0                      # terrain cell size (tunnel rectangles are multiples of it)
X0, X1 = -8800.0, 8800.0         # terrain domain
Y0, Y1 = -6480.0, 6480.0


def pol(theta_deg, rho, z):
    t = math.radians(theta_deg)
    return (A * rho * math.cos(t), CY + B * rho * math.sin(t), z)


def _spiral(th0, th1, rho0, rho1, z1, n=34, lead=0.07, tail=0.07, rho_mid=None):
    """Points of a haul road that winds from the plateau (z = 0) down to the pit floor (z = z1)."""
    xy = []
    for i in range(n + 1):
        t = i / float(n)
        th = lerp(th0, th1, t)
        rr = lerp(rho0, rho1, S(t, 0.0, 1.0))
        p = pol(th, rr, 0.0)
        xy.append((p[0], p[1]))
    cum = [0.0]
    for a, b in zip(xy[:-1], xy[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1]
    lead_l, tail_l = 650.0, 650.0
    pts = []
    for (x, y), s in zip(xy, cum):
        zt = clamp((s - lead_l) / (total - lead_l - tail_l), 0.0, 1.0)
        pts.append((x, y, z1 * zt))
    return pts


def build_roads():
    """Roads of the west (red) half; x is mirrored for the east half. Each is (points, width)."""
    roads = []
    north = _spiral(176, 44, 1.14, 0.40, ZF)
    south = _spiral(184, 316, 1.14, 0.40, ZF)
    roads.append((north, 560.0))
    roads.append((south, 560.0))
    out = []
    for pts, w in roads:
        out.append((pts, w))
        out.append(([(-x, y, z) for x, y, z in pts], w))
    return out


ROADS = build_roads()
SHOULDER = 170.0


class Seg:
    __slots__ = ("x0", "y0", "z0", "x1", "y1", "z1", "dx", "dy", "l2", "lo_x", "hi_x", "lo_y", "hi_y", "half")


def _segments(roads):
    segs = []
    for pts, w in roads:
        half = w / 2.0
        for a, b in zip(pts[:-1], pts[1:]):
            s = Seg()
            s.x0, s.y0, s.z0 = a
            s.x1, s.y1, s.z1 = b
            s.dx, s.dy = b[0] - a[0], b[1] - a[1]
            s.l2 = max(1e-6, s.dx * s.dx + s.dy * s.dy)
            m = half + SHOULDER + 5.0
            s.lo_x, s.hi_x = min(a[0], b[0]) - m, max(a[0], b[0]) + m
            s.lo_y, s.hi_y = min(a[1], b[1]) - m, max(a[1], b[1]) + m
            s.half = half
            segs.append(s)
    return segs


SEGS = _segments(ROADS)


def road_blend(x, y):
    """(weight 0..1, road z, distance to the centre line) of the strongest road at x, y (weight 0 when none is near)."""
    best_w, best_z, best_d = 0.0, 0.0, 1e9
    for s in SEGS:
        if x < s.lo_x or x > s.hi_x or y < s.lo_y or y > s.hi_y:
            continue
        t = clamp(((x - s.x0) * s.dx + (y - s.y0) * s.dy) / s.l2, 0.0, 1.0)
        px, py = s.x0 + s.dx * t, s.y0 + s.dy * t
        d = math.hypot(x - px, y - py)
        if d < best_d:
            best_d, best_z = d, s.z0 + (s.z1 - s.z0) * t
            best_w = 1.0 - S(d, s.half, s.half + SHOULDER)
    return best_w, best_z, best_d


# ------------------------------------------------------------------------------------------------ tunnels
def _rect(x0, y0, x1, y1):
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def tunnel_rects_west():
    """Corridors of the west half as (x0, y0, x1, y1) rectangles (multiples of GRID). Declines are listed in DECLINES."""
    r = []
    r.append(_rect(-5440, -3320, -4960, -2800))          # bottom of the red decline
    r.append(_rect(-5440, -3320, -3440, -2840))          # first leg east
    r.append(_rect(-3920, -3800, -3440, -3320))          # chicane
    r.append(_rect(-3920, -3800, -800, -3320))           # second leg east
    r.append(_rect(-2640, -3320, -2160, -1800))          # exit shaft up to the south plateau (sloped)
    r.append(_rect(-800, -3800, 800, -2760))             # central hall
    r.append(_rect(-240, -2760, 240, -2000))             # exit to the pit (bench A)
    return r


def tunnel_rects():
    out = []
    for q in tunnel_rects_west():
        out.append(q)
        out.append(_rect(-q[0], q[1], -q[2], q[3]))
    return out


# slopes: (x0, y0, x1, y1, axis, y_start, y_end, z_start, z_end): floor goes linearly from z_start at s0 to z_end at s1 along `axis`
def _sloped():
    s = []
    for sgn in (-1, 1):
        # red decline: from the base yard (y -1700, z 0) down to y -2800 (z TZ); its rectangle continues flat below
        x0, x1 = (-5440, -4960) if sgn < 0 else (4960, 5440)
        s.append((x0, -3100.0, x1, -1700.0, "y", -1700.0, -3100.0, 0.0, TZ))
        # exit shaft: from the hall corridor (y -3320, TZ) north to the plateau (y -1800, z 0)
        x0, x1 = (-2640, -2160) if sgn < 0 else (2160, 2640)
        s.append((x0, -3320.0, x1, -1800.0, "y", -3320.0, -1800.0, TZ, 0.0))
    return s


SLOPED = _sloped()
DECLINE_RECTS = [(q[0], q[1], q[2], q[3]) for q in (_rect(-5440, -3100, -4960, -1700), _rect(4960, -3100, 5440, -1700))]
SHAFT_RECTS = [_rect(-2640, -3320, -2160, -1800), _rect(2160, -3320, 2640, -1800)]
_TUN_ALL = tunnel_rects() + DECLINE_RECTS


def tunnel_cell(cx, cy):
    """True when the point (cell centre) is inside any tunnel rectangle."""
    for q in _TUN_ALL:
        if q[0] <= cx <= q[2] and q[1] <= cy <= q[3]:
            return True
    return False


def tunnel_floor(x, y):
    for (x0, y0, x1, y1, axis, s0, s1, z0, z1) in SLOPED:
        if x0 <= x <= x1 and y0 <= y <= y1:
            t = clamp((y - s0) / (s1 - s0), 0.0, 1.0)
            return lerp(z0, z1, t)
    return TZ


# ------------------------------------------------------------------------------------------------ heaps (walkable piles)
HEAPS = []     # (x, y, radius, height, material key)


def _make_heaps():
    h = []
    # plateau stockpiles along the north and south lanes, in the base yards and on the pit floor
    spec = [
        (-2900, 3250, 420, 230, "gravel"), (-1900, 3600, 330, 170, "sand"), (-300, 3350, 460, 250, "gravel"),
        (1250, 3650, 360, 190, "ore"), (2600, 3200, 420, 220, "sand"), (4000, 3500, 380, 200, "gravel"),
        (-4100, -2500, 380, 200, "sand"), (-2100, -1500, 400, 215, "gravel"), (-600, -2850, 0, 0, "x"),
        (-3400, 1700, 0, 0, "x"), (-1100, 2900, 360, 190, "ore"),
        (-1300, -620, 360, 150, "gravel"), (1450, 800, 340, 140, "sand"), (-2000, 800, 300, 120, "gravel"),
        (-5600, -2300, 400, 200, "sand"), (-5900, 3300, 450, 250, "gravel"),
    ]
    for x, y, r, hh, k in spec:
        if r <= 0:
            continue
        h.append((x, y, r, hh, k))
        h.append((-x, y, r * 0.95, hh * 1.05, k))       # the east half gets its own, slightly different pile
    return h


HEAPS = _make_heaps()


def heap_height(x, y):
    best = 0.0
    kind = None
    for cx, cy, r, hh, k in HEAPS:
        d = math.hypot(x - cx, y - cy)
        if d < r:
            t = d / r
            v = hh * (1.0 - t) ** 1.25
            v *= 0.85 + 0.3 * vnoise(x / 70.0, y / 70.0, 1.0, 3)
            if v > best:
                best, kind = v, k
    return best, kind


def ring_point(theta_deg, d):
    """World (x, y) on the ray from the pit centre at angle theta whose distance d inside the rim contour is `d` (cm)."""
    t = math.radians(theta_deg)
    lo, hi = 0.0, 1.6
    for _ in range(40):
        mid = (lo + hi) / 2.0
        x, y = A * mid * math.cos(t), CY + B * mid * math.sin(t)
        if _pit_d(abs(x), y) > d:
            lo = mid
        else:
            hi = mid
    rho = (lo + hi) / 2.0
    return (A * rho * math.cos(t), CY + B * rho * math.sin(t))


# ------------------------------------------------------------------------------------------------ the height function
def _pit_d(ax, y):
    py = y - CY
    rho = math.hypot(ax / A, py / B)
    if rho < 1e-9:
        return 9999.0
    g = math.hypot(ax / (A * A), py / (B * B)) / rho
    return (1.0 - rho) / g


def wall_profile(e):
    """Height of the boundary cliff e cm outside the playable rectangle: five steep strata with small ledges."""
    z = 0.0
    z += 520.0 * S(e, 40.0, 130.0)
    z += 480.0 * S(e, 190.0, 290.0)
    z += 560.0 * S(e, 350.0, 450.0)
    z += 600.0 * S(e, 520.0, 640.0)
    z += 700.0 * S(e, 720.0, 860.0)
    z += 0.42 * max(0.0, e - 900.0)
    return z


def base_flat_mask(x, y):
    """0 on the base platforms and lanes where the plateau must stay flat, 1 in free country (for hills)."""
    ax = abs(x)
    m = 1.0
    m = min(m, S(math.hypot(ax - BASE_X, y - 250.0), 1500.0, 2600.0))
    d = _pit_d(ax, y)
    m = min(m, S(-d, 500.0, 1100.0))
    return m


def height_raw(x, y):
    """Terrain without roads and heaps (fast part)."""
    ax = abs(x)
    d0 = _pit_d(ax, y)
    d = d0 + 70.0 * fbm(ax / 650.0 + 1.3, y / 650.0, 0.0, 3, 11) + 16.0 * fbm(ax / 110.0, y / 110.0, 4.0, 2, 12)
    z = ZA * S(d, 0.0, 130.0) + (ZB - ZA) * S(d, 580.0, 700.0) + (ZF - ZB) * S(d, 1150.0, 1270.0)
    # a little life in the flat parts
    if d > 130.0:
        z += 10.0 * fbm(ax / 170.0, y / 170.0, 3.0, 2, 14) * S(d, 130.0, 200.0)
    if d > 1270.0:
        z += 26.0 * fbm(ax / 520.0 + 5.0, y / 520.0, 0.0, 3, 15)
        pr = math.hypot((ax - PONDX) / PONDRX, (y - PONDY) / PONDRY)
        z -= 95.0 * (1.0 - S(pr, 0.50, 1.30))
    # plateau
    if d < 130.0:
        mk = base_flat_mask(x, y)
        z += 20.0 * fbm(ax / 800.0, y / 800.0, 6.0, 2, 16) + 6.0 * fbm(x / 120.0, y / 120.0, 7.0, 2, 17)
        # rolling country in the north and south, away from the lanes
        hills = 150.0 * (0.5 + 0.5 * fbm(ax / 1300.0 + 2.0, y / 1300.0, 9.0, 3, 18)) * mk
        hills *= S(abs(y), 3000.0, 3800.0)
        z += hills
        # flat platforms for the two bases
        bdx, bdy = max(abs(ax - BASE_X) - 1100.0, 0.0), max(abs(y - 250.0) - 1400.0, 0.0)
        bw = 1.0 - S(math.hypot(bdx, bdy), 0.0, 350.0)
        if bw > 0.0:
            z = lerp(z, 0.0, bw)
    # cliffs around the map
    ex, ey = max(abs(x) - PX, 0.0), max(abs(y) - PY, 0.0)
    e = math.hypot(ex, ey)
    if e > 0.0:
        e += 70.0 * fbm(x / 420.0, y / 420.0, 11.0, 3, 21) * S(e, 0.0, 200.0) + 25.0 * fbm(x / 90.0, y / 90.0, 12.0, 2, 22)
        z += wall_profile(max(e, 0.0)) * (1.0 + 0.06 * fbm(x / 800.0, y / 800.0, 13.0, 2, 23))
        z += 30.0 * ridged(x / 160.0, y / 160.0, 2.0, 2, 24) * S(e, 100.0, 300.0)
    return z


def height(x, y):
    z = height_raw(x, y)
    w, rz, rd = road_blend(x, y)
    if w > 0.0:
        z = lerp(z, rz, w)
    hv, _ = heap_height(x, y)
    if hv > 0.0:
        z += hv
    return z


# ------------------------------------------------------------------------------------------------ the grid
class Grid:
    """All terrain heights at the grid vertices (cell GRID)."""

    def __init__(self, cache=None):
        self.nx = int(round((X1 - X0) / GRID))
        self.ny = int(round((Y1 - Y0) / GRID))
        self.h = []
        for i in range(self.nx + 1):
            col = []
            x = X0 + i * GRID
            for j in range(self.ny + 1):
                col.append(height(x, Y0 + j * GRID))
            self.h.append(col)

    def x(self, i):
        return X0 + i * GRID

    def y(self, j):
        return Y0 + j * GRID

    def at(self, i, j):
        return self.h[clamp(i, 0, self.nx)][clamp(j, 0, self.ny)]

    def normal(self, i, j):
        i = int(i)
        j = int(j)
        dx = (self.at(i + 1, j) - self.at(i - 1, j)) / (2.0 * GRID)
        dy = (self.at(i, j + 1) - self.at(i, j - 1)) / (2.0 * GRID)
        l = math.sqrt(dx * dx + dy * dy + 1.0)
        return (-dx / l, -dy / l, 1.0 / l)

    def sample(self, x, y):
        fi, fj = (x - X0) / GRID, (y - Y0) / GRID
        i, j = int(math.floor(fi)), int(math.floor(fj))
        i = int(clamp(i, 0, self.nx - 1))
        j = int(clamp(j, 0, self.ny - 1))
        tx, ty = clamp(fi - i, 0.0, 1.0), clamp(fj - j, 0.0, 1.0)
        a, b, c, d = self.at(i, j), self.at(i + 1, j), self.at(i, j + 1), self.at(i + 1, j + 1)
        return lerp(lerp(a, b, tx), lerp(c, d, tx), ty)


def cell_open(g, i, j):
    """For a cell inside a tunnel rectangle: True when the terrain sheet must be removed (the terrain is below the ceiling)."""
    cx, cy = g.x(i) + GRID / 2.0, g.y(j) + GRID / 2.0
    zc = tunnel_floor(cx, cy) + TH
    hs = (g.at(i, j), g.at(i + 1, j), g.at(i, j + 1), g.at(i + 1, j + 1))
    return min(hs) < zc + 40.0


# ------------------------------------------------------------------------------------------------ analysis
def _png(path, w, h, rows):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def nav_estimate(g, starts, cell=150.0):
    """Cheap copy of IANavGrid: nodes where the slope is walkable (normal z >= 0.7), links when the height step is <= 110.
    Tunnel cells add a second layer. Returns (labels dict, node dict, component sizes, start components)."""
    nodes = {}
    x = X0 + cell / 2.0
    ix = 0
    while x < X1:
        y = Y0 + cell / 2.0
        iy = 0
        while y < Y1:
            # walk the terrain: use the max slope over the cell
            z = g.sample(x, y)
            zx = (g.sample(x + 45, y) - g.sample(x - 45, y)) / 90.0
            zy = (g.sample(x, y + 45) - g.sample(x, y - 45)) / 90.0
            nz = 1.0 / math.sqrt(zx * zx + zy * zy + 1.0)
            if abs(x) <= PX + 50 and abs(y) <= PY + 50:
                fi, fj = int((x - X0) / GRID), int((y - Y0) / GRID)
                inside_tunnel = tunnel_cell(x, y)
                if inside_tunnel and cell_open(g, fi, fj):
                    pass            # sheet removed
                elif nz >= 0.9455:
                    nodes[(ix, iy, 0)] = (x, y, z)
                if inside_tunnel:
                    nodes[(ix, iy, 1)] = (x, y, tunnel_floor(x, y))
            y += cell
            iy += 1
        x += cell
        ix += 1
    labels = {}
    comp = 0
    sizes = []
    for k in nodes:
        if k in labels:
            continue
        stack = [k]
        labels[k] = comp
        n = 0
        while stack:
            c = stack.pop()
            n += 1
            cx, cy, cz = nodes[c]
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    for layer in (0, 1):
                        nk = (c[0] + dx, c[1] + dy, layer)
                        if nk in nodes and nk not in labels:
                            if abs(nodes[nk][2] - cz) <= 110.0 and not (layer != c[2] and False):
                                # a surface node over a tunnel node is not connected: they differ by more than 110 except at mouths
                                labels[nk] = comp
                                stack.append(nk)
        sizes.append(n)
        comp += 1
    return labels, nodes, sizes


def render(g, path, labels=None, nodes=None, scale=1.0 / 40.0, marks=()):
    w = int((X1 - X0) * scale)
    h = int((Y1 - Y0) * scale)
    rows = []
    comp_col = {}
    for py in range(h):
        y = Y1 - (py + 0.5) / scale
        row = bytearray()
        for px in range(w):
            x = X0 + (px + 0.5) / scale
            z = g.sample(x, y)
            zl = g.sample(x - 60, y + 60)
            sh = clamp(0.5 + (z - zl) * 0.004, 0.25, 1.0)
            t = clamp((z + 1500.0) / 1500.0, 0.0, 1.0)
            r, gg, b = 90 + 130 * t, 70 + 110 * t, 60 + 80 * t
            if abs(x) > PX or abs(y) > PY:
                r, gg, b = 60, 60, 70
            if tunnel_cell(x, y):
                r, gg, b = r * 0.5 + 60, gg * 0.5, b * 0.5 + 60
            row += bytes((int(r * sh), int(gg * sh), int(b * sh)))
        rows.append(row)
    for (mx, my, col) in marks:
        px = int((mx - X0) * scale)
        py = int((Y1 - my) * scale)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if 0 <= py + dy < h and 0 <= px + dx < w:
                    rows[py + dy][(px + dx) * 3:(px + dx) * 3 + 3] = bytes(col)
    _png(path, w, h, rows)


def main():
    import time
    t0 = time.time()
    g = Grid()
    print("grid %dx%d in %.1fs" % (g.nx, g.ny, time.time() - t0))
    lo = min(min(c) for c in g.h)
    hi = max(max(c) for c in g.h)
    print("height range %.0f .. %.0f" % (lo, hi))
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Saved")
    os.makedirs(out, exist_ok=True)
    render(g, os.path.join(out, "quarry_top.png"))
    return g


if __name__ == "__main__":
    main()
