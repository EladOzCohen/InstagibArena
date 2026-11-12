"""Reusable parts for the city maps (cars, rooftop machinery, water tanks, roof edge curbs). Built on mapkit_c."""

import math

import unreal

from mapkit_c import rbox, cyl, bar


def rot2(x, y, yaw):
    """Rotate a local (x, y) offset by yaw degrees."""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return x * c - y * s, x * s + y * c


def local_box(b, label, ox, oy, oz, sx, sy, sz, base, yaw=0.0, mat=None, solid=True, pitch=0.0, roll=0.0):
    """A box placed in the local frame of base = (x, y, z, yaw): (ox, oy, oz) is the centre offset (oz above z)."""
    byaw = base[3] if len(base) > 3 else 0.0
    dx, dy = rot2(ox, oy, byaw)
    return rbox(b, label, base[0] + dx, base[1] + dy, base[2] + oz, sx, sy, sz, yaw=byaw + yaw, pitch=pitch,
                roll=roll, mat=mat, solid=solid)


def car(b, label, x, y, z, yaw, paint, glass, dark, kind="sedan", solid=True, lights=None, tail=None):
    """A parked car out of boxes: body, cabin with sloped glass, roof, bumpers, wheels. x, y, z = centre on the ground.
    The long axis is local +x (yaw 0). paint/glass/dark are materials; lights/tail optional emissive materials."""
    L, W = (450.0, 186.0) if kind == "sedan" else ((380.0, 178.0) if kind == "hatch" else (480.0, 200.0))
    base = (x, y, z, yaw)
    low = 52.0 if kind != "van" else 70.0
    local_box(b, label + "_body", 0, 0, 14 + low / 2, L, W, low, base, mat=paint, solid=solid)
    local_box(b, label + "_hood", L * 0.28, 0, 14 + low + 3, L * 0.34, W * 0.94, 6, base, mat=paint, solid=False)
    local_box(b, label + "_trunk", -L * 0.36, 0, 14 + low + 3, L * 0.22, W * 0.92, 6, base, mat=paint, solid=False)
    ch = 56.0 if kind != "van" else 78.0
    cl = L * (0.40 if kind == "sedan" else 0.46 if kind == "hatch" else 0.78)
    cxo = -L * (0.04 if kind == "sedan" else 0.10 if kind == "hatch" else 0.0)
    z0 = 14 + low
    local_box(b, label + "_cabin", cxo, 0, z0 + ch / 2, cl, W * 0.88, ch, base, mat=glass, solid=solid)
    local_box(b, label + "_roof", cxo, 0, z0 + ch + 3, cl * 0.9, W * 0.9, 6, base, mat=paint, solid=False)
    if kind != "van":
        for px in (-cl * 0.1, cl * 0.22):
            local_box(b, label + "_pillar", cxo + px, 0, z0 + ch / 2, 8, W * 0.9, ch, base, mat=paint, solid=False)
        for sgn, nm in ((1, "_screen"), (-1, "_rear")):
            xa = cxo + sgn * cl / 2
            xb = xa + sgn * 42.0
            p0 = rot2(xb, 0, yaw)
            p1 = rot2(xa, 0, yaw)
            bar(b, label + nm, (x + p0[0], y + p0[1], z + z0 + 2), (x + p1[0], y + p1[1], z + z0 + ch + 2), 4.0,
                mat=glass, solid=False, depth=W * 0.86)
    for sgn in (1, -1):
        local_box(b, label + "_bump", sgn * (L / 2 + 2), 0, 28, 10, W * 0.98, 22, base, mat=dark, solid=False)
    if lights is not None:
        for sy in (-1, 1):
            local_box(b, label + "_head", L / 2 + 1, sy * W * 0.34, 14 + low - 12, 4, 30, 12, base, mat=lights,
                      solid=False)
    if tail is not None:
        for sy in (-1, 1):
            local_box(b, label + "_tail", -L / 2 - 1, sy * W * 0.36, 14 + low - 10, 4, 34, 10, base, mat=tail,
                      solid=False)
    for sx_ in (-0.32, 0.31):
        for sy in (-1, 1):
            dx, dy = rot2(sx_ * L, sy * (W / 2 - 6), yaw)
            rbox(b, label + "_wheel", x + dx, y + dy, z + 33, 66, 66, 24, yaw=yaw, roll=90.0, mat=dark, solid=False,
                 mesh=b.cylinder)


def chiller(b, label, x, y, z, sx, sy, sz, yaw, body, dark, metal, solid=True):
    """A rooftop air handling unit: body, louvre panels, fan grille with fan ring, pipe stubs. z = roof height."""
    base = (x, y, z, yaw)
    local_box(b, label + "_body", 0, 0, sz / 2, sx, sy, sz, base, mat=body, solid=solid)
    local_box(b, label + "_lid", 0, 0, sz + 3, sx + 8, sy + 8, 6, base, mat=metal, solid=False)
    for sgn in (-1, 1):
        for k in range(3):
            local_box(b, label + "_louv", -sx * 0.28 + k * sx * 0.28, sgn * (sy / 2 + 1.5), sz * 0.5, sx * 0.22, 3,
                      sz * 0.7, base, mat=dark, solid=False)
    d = min(sx, sy) * 0.62
    rbox(b, label + "_fanring", x, y, z + sz + 8, d, d, 10, yaw=yaw, mat=metal, solid=False, mesh=b.cylinder)
    rbox(b, label + "_fan", x, y, z + sz + 9, d * 0.86, d * 0.86, 10, yaw=yaw, mat=dark, solid=False, mesh=b.cylinder)
    for sgn in (-1, 1):
        px, py = rot2(sx / 2 + 14, sgn * sy * 0.25, yaw)
        cyl(b, label + "_pipe", (x + px, y + py, z + 20), (x + px, y + py, z + sz * 0.7), 12, mat=metal, solid=False)


def water_tank(b, label, x, y, z, dia, h_total, wood, steel, concrete, solid=True):
    """A wooden water tank on a plinth, steel hoops, conical lid, ladder. h_total counts from z."""
    plinth = 90.0
    rbox(b, label + "_plinth", x, y, z + plinth / 2, dia * 0.82, dia * 0.82, plinth, mat=concrete, solid=solid)
    body_top = z + h_total - 70
    rbox(b, label + "_body", x, y, (z + plinth + body_top) / 2, dia, dia, body_top - z - plinth, mat=wood,
         solid=solid, mesh=b.cylinder)
    for k in range(3):
        zz = z + plinth + 40 + k * (body_top - z - plinth - 80) / 2
        rbox(b, label + "_hoop%d" % k, x, y, zz, dia + 8, dia + 8, 7, mat=steel, solid=False, mesh=b.cylinder)
    b.cone(label + "_lid", x, y, body_top, z + h_total, dia + 24, mat=steel, solid=solid)
    for sx_ in (-22, 22):
        rbox(b, label + "_ladder", x + sx_, y + dia / 2 + 10, z + (body_top - z) / 2 + 20, 5, 5, body_top - z - 40,
             mat=steel, solid=False)
    for k in range(10):
        rbox(b, label + "_rung", x, y + dia / 2 + 10, z + plinth + k * (body_top - z - 40 - plinth) / 9 + 10, 44, 4, 4,
             mat=steel, solid=False)


def curb(b, label, cx, cy, sx, sy, z, thick, height, mat, gaps=(), solid=True):
    """A low wall (coping curb) along the 4 edges of a rectangle, its outer face on the roof edge.
    gaps: list of (edge, a, b), edge in 'N','S','E','W', a..b the open interval in world coordinates."""
    edges = {
        "N": ("x", cy + sy / 2 - thick / 2, cx - sx / 2, cx + sx / 2),
        "S": ("x", cy - sy / 2 + thick / 2, cx - sx / 2, cx + sx / 2),
        "E": ("y", cx + sx / 2 - thick / 2, cy - sy / 2, cy + sy / 2),
        "W": ("y", cx - sx / 2 + thick / 2, cy - sy / 2, cy + sy / 2),
    }
    n = 0
    for e, (axis, fixed, lo, hi) in edges.items():
        cuts = sorted((max(lo, a), min(hi, bb)) for (ee, a, bb) in gaps if ee == e and bb > lo and a < hi)
        segs, cur = [], lo
        for a, bb in cuts:
            if a > cur:
                segs.append((cur, a))
            cur = max(cur, bb)
        if cur < hi:
            segs.append((cur, hi))
        for (a, bb) in segs:
            if bb - a < 20:
                continue
            m_ = (a + bb) / 2
            if axis == "x":
                rbox(b, "%s_%s%d" % (label, e, n), m_, fixed, z + height / 2, bb - a, thick, height, mat=mat, solid=solid)
            else:
                rbox(b, "%s_%s%d" % (label, e, n), fixed, m_, z + height / 2, thick, bb - a, height, mat=mat, solid=solid)
            n += 1
    return n


def bridge_gaps(rect, bridges, pad=40.0):
    """Gap intervals on a rectangle's edges where bridges cross them.
    rect = (cx, cy, sx, sy); bridges = list of ((x0, y0), (x1, y1), width). Returns [(edge, a, b)]."""
    cx, cy, sx, sy = rect
    out = []
    x_lo, x_hi, y_lo, y_hi = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2
    for (p0, p1, w) in bridges:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        for edge, axis, val in (("N", "y", y_hi), ("S", "y", y_lo), ("E", "x", x_hi), ("W", "x", x_lo)):
            if axis == "y":
                if abs(uy) < 1e-6:
                    continue
                t = (val - p0[1]) / uy
                ix = p0[0] + ux * t
                half = (w / 2) / abs(uy) if abs(uy) > 0.2 else w / 2 + 1e4
                if -150 <= t <= length + 150 and x_lo - 200 <= ix <= x_hi + 200:
                    out.append((edge, ix - half - pad, ix + half + pad))
            else:
                if abs(ux) < 1e-6:
                    continue
                t = (val - p0[0]) / ux
                iy = p0[1] + uy * t
                half = (w / 2) / abs(ux) if abs(ux) > 0.2 else w / 2 + 1e4
                if -150 <= t <= length + 150 and y_lo - 200 <= iy <= y_hi + 200:
                    out.append((edge, iy - half - pad, iy + half + pad))
    return out
