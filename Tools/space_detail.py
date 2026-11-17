"""Detail kit for the space arenas (boxes, columns and glow only; no collision, nothing that changes the gameplay).

    import space_detail as sd
    sd.pipes(m, mats, x0, x1, y, z, n=3)             a bundle of long pipes with brackets
    sd.wall_panels(m, mats, axis, fixed, a0, a1, z0, z1, side)   grooved wall panels with small lights
    sd.grating(m, mats, x0, x1, y0, y1, z)           floor grating: dark strips with a lit seam
    sd.hologram(m, mats, x, y, z, h)                 a floating holographic display on a pedestal
    sd.cable_run(m, mats, pts)                       a run of cables as thin boxes
mats is a dict with keys steel, dark, glow_a, glow_b (material instances).
"""

import math


def _box(m, label, x0, x1, y0, y1, z0, z1, mat, solid=False, yaw=0.0):
    return m.box(label, (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), yaw=yaw, mat=mat, solid=solid)


def pipes(m, mats, x0, x1, y, z, n=3, tag="Pipe"):
    for i in range(n):
        d = 34.0 - i * 6.0
        yy = y + (i - (n - 1) / 2.0) * 46.0
        _box(m, "%sBox_%d_%d" % (tag, int(y), i), x0, x1, yy - d / 2.0, yy + d / 2.0, z - d / 2.0, z + d / 2.0, mats["steel"] if i % 2 == 0 else mats["dark"])
    k = 0
    xx = x0 + 150.0
    while xx < x1 - 100.0:
        _box(m, "%sBracket_%d_%d" % (tag, int(y), k), xx - 8, xx + 8, y - 30 - n * 22, y + 30 + n * 22, z - 40, z + 40, mats["dark"])
        k += 1
        xx += 420.0


def wall_panels(m, mats, along_x, fixed, a0, a1, z0, z1, side, tag="Panel"):
    """Panels on a wall. along_x: the wall runs along x at y = fixed (side +1 or -1 = which way the panels stick out)."""
    step = 260.0
    k = 0
    a = a0 + 60.0
    while a + 200.0 <= a1:
        for j, (zz0, zz1) in enumerate(((z0, z0 + (z1 - z0) * 0.42), (z0 + (z1 - z0) * 0.5, z1))):
            t = 14.0
            if along_x:
                _box(m, "%s_%d_%d" % (tag, k, j), a, a + 200.0, fixed, fixed + side * t, zz0, zz1, mats["dark"])
                _box(m, "%sGlow_%d_%d" % (tag, k, j), a + 20.0, a + 180.0, fixed + side * t, fixed + side * (t + 2), zz0 + 8, zz0 + 14, mats["glow_a"] if (k + j) % 3 else mats["glow_b"])
            else:
                _box(m, "%s_%d_%d" % (tag, k, j), fixed, fixed + side * t, a, a + 200.0, zz0, zz1, mats["dark"])
                _box(m, "%sGlow_%d_%d" % (tag, k, j), fixed + side * t, fixed + side * (t + 2), a + 20.0, a + 180.0, zz0 + 8, zz0 + 14, mats["glow_a"] if (k + j) % 3 else mats["glow_b"])
        k += 1
        a += step


def grating(m, mats, x0, x1, y0, y1, z, tag="Grate"):
    k = 0
    y = y0
    while y < y1:
        _box(m, "%s_%d" % (tag, k), x0, x1, y, y + 14.0, z, z + 3.0, mats["dark"])
        k += 1
        y += 64.0
    _box(m, "%sSeam" % tag, x0, x1, (y0 + y1) / 2.0 - 3.0, (y0 + y1) / 2.0 + 3.0, z, z + 4.0, mats["glow_a"])


def hologram(m, mats, x, y, z, h=220.0, tag="Holo"):
    """A holographic data column: a pedestal, a projector ring, a ring of glowing bars of different heights and a turning cube on top."""
    k = "%d_%d" % (int(x), int(y))
    _box(m, "%sBase_%s" % (tag, k), x - 50, x + 50, y - 50, y + 50, z, z + 70, mats["dark"], solid=True)
    _box(m, "%sRing_%s" % (tag, k), x - 56, x + 56, y - 56, y + 56, z + 70, z + 78, mats["glow_a"])
    heights = (0.55, 0.9, 0.7, 1.0, 0.45, 0.8, 0.62, 0.95)
    for j, f in enumerate(heights):
        a = j / float(len(heights)) * 2.0 * math.pi
        bx, by = x + math.cos(a) * 34.0, y + math.sin(a) * 34.0
        _box(m, "%sBar_%s_%d" % (tag, k, j), bx - 6, bx + 6, by - 6, by + 6, z + 90, z + 90 + h * f, mats["glow_a"] if j % 3 else mats["glow_b"])
    _box(m, "%sFrame_%s" % (tag, k), x - 46, x + 46, y - 46, y + 46, z + 96 + h, z + 100 + h, mats["glow_a"], yaw=0.0)
    _box(m, "%sCube_%s" % (tag, k), x - 14, x + 14, y - 14, y + 14, z + 112 + h, z + 140 + h, mats["glow_b"], yaw=45.0)
    m.accent_light("%sLight_%s" % (tag, k), (x, y, z + 160), (0.3, 0.9, 1.0), candela=25.0, radius=600.0)


def cable_run(m, mats, pts, tag="Cable"):
    for i in range(len(pts) - 1):
        (xa, ya, za), (xb, yb, zb) = pts[i], pts[i + 1]
        _box(m, "%s_%d_%d" % (tag, int(xa), i), min(xa, xb) - 6, max(xa, xb) + 6, min(ya, yb) - 6, max(ya, yb) + 6, min(za, zb) - 6, max(za, zb) + 6, mats["dark"])
