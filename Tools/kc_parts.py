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


_car_cache = {}


def car_paint(tag, rgb, **kw):
    """Glossy car paint in the sRGB colour rgb (0..255)."""
    from matlib import surface
    return surface("PlasterWhite", albedo=rgb, tag="CarPaintP" + tag, rs=0.32, rb=-0.35, ns=0.0, macro=0.03, metal=0.15, **kw)


def car_glass_mat():
    from matlib import surface
    return surface("PlasterWhite", albedo=(16, 20, 28), tag="CarGlassP2", rs=0.2, rb=-0.4, ns=0.0, macro=0.0, metal=0.0)


def car_rubber_mat():
    from matlib import surface
    return surface("StoneDark", albedo=(20, 20, 22), tag="CarRubberMat", rs=0.95, ns=0.25, macro=0.0)


def _car_assets(kind):
    """The six generated meshes of a car kind (paint, dark, steel, glass, head, tail) and its size info."""
    if kind not in _car_cache:
        import mapkit_b
        import mesh_car
        parts = mesh_car.build(kind)
        sms = {k: mapkit_b.commit("Car_%s_%s" % (kind, k), parts[k], collision="none")
               for k in ("paint", "dark", "steel", "glass", "head", "tail")}
        _car_cache[kind] = (sms, parts["info"])
    return _car_cache[kind]


def car(b, label, x, y, z, yaw, paint, glass, dark, kind="sedan", solid=True, lights=None, tail=None):
    """A parked car: six generated meshes (paint, glass, tyres + trim, hubs, head and tail lamps; see Tools/mesh_car.py).
    x, y, z = centre on the ground, the long axis is local +x (yaw 0). kind: sedan, hatch or van. paint/glass/dark are
    materials, lights/tail optional emissive materials. solid=True adds two hidden box colliders (body and cabin)."""
    import mapkit_b
    from matlib import surface
    sms, info = _car_assets(kind)
    hub = surface("BrushedMetal", albedo=(104, 106, 110), tag="CarHub2", metal=0.4, rb=0.15, ns=0.3)
    head_m = lights or surface("PlasterWhite", albedo=(196, 196, 186), tag="CarLensP", rs=0.3, ns=0.0, macro=0.0)
    tail_m = tail or surface("PlasterWhite", albedo=(120, 20, 20), tag="CarTailLensP", rs=0.4, ns=0.0, macro=0.0)
    for part, mat in (("paint", paint), ("dark", dark), ("steel", hub), ("glass", glass), ("head", head_m), ("tail", tail_m)):
        mapkit_b.put(b, "%s_%s" % (label, part), sms[part], x, y, z, yaw=yaw, mat=mat, solid=False)
    if solid:
        base = (x, y, z, yaw)
        bt = info["body_top"]
        a = local_box(b, label + "_body", 0, 0, (18.0 + bt - 3.0) / 2, info["length"] - 14.0, info["width"] - 14.0, bt - 21.0, base,
                      mat=None, solid=True)
        a.set_actor_hidden_in_game(True)
        cx = (info["cab_x0"] + info["cab_x1"]) / 2.0
        a = local_box(b, label + "_cabin", cx, 0, (bt + info["cab_top"] - 8.0) / 2, info["cab_x1"] - info["cab_x0"], info["cab_w"],
                      info["cab_top"] - 8.0 - bt, base, mat=None, solid=True)
        a.set_actor_hidden_in_game(True)


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
