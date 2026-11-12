"""Extra building helpers for the DM-Forge and DM-Glacier map scripts (additive; mapkit.py is shared with other maps).

    from mapkit_d import Frame, tube, beam
    f = Frame(m, k=1)                      # build in a local frame turned by k * 90 degrees around the map centre
    f.box("Plate", x, y, z, sx, sy, sz, mat=iron)   # same arguments as MapBuilder.box, local coordinates

Everything places StaticMeshActors through MapBuilder._place, so it counts in the box counter like any other piece.
"""

import math

import unreal


def _sphere(b):
    if getattr(b, "sphere_mesh", None) is None:
        b.sphere_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere.Sphere")
    return b.sphere_mesh


def tube(b, label, p0, p1, dia, mat=None, solid=False, mesh=None):
    """A cylinder (or cone, pass mesh) between two points p0 -> p1 (x, y, z)."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-3:
        return None
    hd = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx)) if hd > 1e-6 else 0.0
    pitch = -math.degrees(math.atan2(hd, dz))
    c = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, (p0[2] + p1[2]) / 2.0)
    return b._place(label, mesh or b.cylinder, c, (dia / 100.0, dia / 100.0, length / 100.0), yaw, pitch, mat, solid)


def beam(b, label, p0, p1, w, h, mat=None, solid=False, roll=0.0):
    """A box whose long axis runs from p0 to p1; w is the width (local y) and h the height (local z)."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-3:
        return None
    hd = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx)) if hd > 1e-6 else 0.0
    pitch = math.degrees(math.atan2(dz, hd))
    c = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, (p0[2] + p1[2]) / 2.0)
    actor = b._place(label, b.cube, c, (length / 100.0, w / 100.0, h / 100.0), yaw, pitch, mat, solid)
    return actor


def sphere(b, label, x, y, z, sx, sy, sz, yaw=0.0, mat=None, solid=False):
    """An ellipsoid by centre and full size (drifts, boulders, lamp globes)."""
    return b._place(label, _sphere(b), (x, y, z), (sx / 100.0, sy / 100.0, sz / 100.0), yaw, 0.0, mat, solid)


def diamond(b, label, x, y, z, thick, side, mat=None, along="x", solid=False):
    """A square rotated 45 degrees (gable end of a 45 degree roof). `along` = axis of the thin direction (x or y)."""
    if along == "x":
        actor = b._place(label, b.cube, (x, y, z), (thick / 100.0, side / 100.0, side / 100.0), 0.0, 0.0, mat, solid)
        actor.set_actor_rotation(unreal.Rotator(roll=45.0, pitch=0.0, yaw=0.0), False)
    else:
        actor = b._place(label, b.cube, (x, y, z), (side / 100.0, thick / 100.0, side / 100.0), 0.0, 0.0, mat, solid)
        actor.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=45.0, yaw=0.0), False)
    return actor


def ibeam(b, label, p0, p1, depth=60.0, flange=40.0, tf=6.0, tw=5.0, mat=None, solid=False):
    """An I-section girder from p0 to p1 (horizontal or sloped): web and two flanges, three boxes."""
    n = [beam(b, label + "_web", p0, p1, tw, depth - 2 * tf, mat, solid)]
    for s in (-1, 1):
        off = s * (depth / 2.0 - tf / 2.0)
        q0 = (p0[0], p0[1], p0[2] + off)
        q1 = (p1[0], p1[1], p1[2] + off)
        n.append(beam(b, label + "_fl", q0, q1, flange, tf, mat, solid))
    return n


def truss(b, label, p0, p1, height, panels, chord=14.0, mat=None, solid=False, width=14.0):
    """A flat truss between p0 and p1 (same height) whose top chord is `height` above the bottom chord.

    p0/p1 are the ends of the BOTTOM chord. panels = number of Warren triangles. Used for the roof."""
    n = []
    top0 = (p0[0], p0[1], p0[2] + height)
    top1 = (p1[0], p1[1], p1[2] + height)
    n.append(beam(b, label + "_bot", p0, p1, width, chord, mat, solid))
    n.append(beam(b, label + "_top", top0, top1, width, chord, mat, solid))
    pts_b = [(p0[0] + (p1[0] - p0[0]) * i / panels, p0[1] + (p1[1] - p0[1]) * i / panels, p0[2]) for i in range(panels + 1)]
    for i in range(panels):
        a = pts_b[i]
        c = pts_b[i + 1]
        up_a = (a[0], a[1], a[2] + height)
        up_c = (c[0], c[1], c[2] + height)
        mid_top = ((a[0] + c[0]) / 2.0, (a[1] + c[1]) / 2.0, a[2] + height)
        mid_bot = ((a[0] + c[0]) / 2.0, (a[1] + c[1]) / 2.0, a[2])
        if i % 2 == 0:
            n.append(beam(b, label + "_d", a, mid_top, width * 0.7, chord * 0.7, mat, solid))
            n.append(beam(b, label + "_d", mid_top, c, width * 0.7, chord * 0.7, mat, solid))
        else:
            n.append(beam(b, label + "_d", up_a, mid_bot, width * 0.7, chord * 0.7, mat, solid))
            n.append(beam(b, label + "_d", mid_bot, up_c, width * 0.7, chord * 0.7, mat, solid))
    return n


def railing(b, label, p0, p1, height=100.0, post_every=220.0, mat=None, solid=False, rails=2, post=5.0, rail=4.0,
            toe=0.0, toe_mat=None):
    """A handrail between two points (may slope). Posts, a top rail, `rails`-1 lower rails and an optional toe board."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    n = max(1, int(round(length / (post_every * 1.35))))
    out = []
    for i in range(n + 1):
        t = i / float(n)
        x, y, z = p0[0] + dx * t, p0[1] + dy * t, p0[2] + dz * t
        out.append(b.box(label + "_p", x, y, z + height / 2.0, post, post, height, mat=mat, solid=solid))
    for j in range(1, rails + 1):
        hz = height * j / float(rails)
        out.append(tube(b, label + "_r", (p0[0], p0[1], p0[2] + hz), (p1[0], p1[1], p1[2] + hz), rail, mat, solid))
    if toe > 0:
        out.append(beam(b, label + "_t", (p0[0], p0[1], p0[2] + toe / 2.0), (p1[0], p1[1], p1[2] + toe / 2.0), 2.0, toe,
                        toe_mat or mat, solid))
    return out


class Frame:
    """Local coordinates turned by k * 90 degrees around the map centre (plus an optional offset and mirror).

    Local (x, y) -> world: first mirror x if mirror, rotate by k quarter turns, then add (ox, oy)."""

    def __init__(self, b, k=0, ox=0.0, oy=0.0, mirror=False):
        self.b, self.k, self.ox, self.oy, self.mirror = b, k % 4, ox, oy, mirror

    def P(self, x, y):
        if self.mirror:
            x = -x
        for _ in range(self.k):
            x, y = -y, x
        return x + self.ox, y + self.oy

    def Y(self, yaw):
        if self.mirror:
            yaw = 180.0 - yaw
        return yaw + 90.0 * self.k

    def box(self, label, x, y, z, sx, sy, sz, yaw=0.0, pitch=0.0, mat=None, solid=True):
        wx, wy = self.P(x, y)
        return self.b.box(label, wx, wy, z, sx, sy, sz, yaw=self.Y(yaw), pitch=pitch, mat=mat, solid=solid)

    def column(self, label, x, y, z0, z1, dia, mat=None, solid=True):
        wx, wy = self.P(x, y)
        return self.b.column(label, wx, wy, z0, z1, dia, mat=mat, solid=solid)

    def cone(self, label, x, y, z0, z1, dia, mat=None, solid=True):
        wx, wy = self.P(x, y)
        return self.b.cone(label, wx, wy, z0, z1, dia, mat=mat, solid=solid)

    def tube(self, label, p0, p1, dia, mat=None, solid=False):
        a, c = self.P(p0[0], p0[1]), self.P(p1[0], p1[1])
        return tube(self.b, label, (a[0], a[1], p0[2]), (c[0], c[1], p1[2]), dia, mat, solid)

    def beam(self, label, p0, p1, w, h, mat=None, solid=False):
        a, c = self.P(p0[0], p0[1]), self.P(p1[0], p1[1])
        return beam(self.b, label, (a[0], a[1], p0[2]), (c[0], c[1], p1[2]), w, h, mat, solid)

    def ibeam(self, label, p0, p1, depth=60.0, flange=40.0, tf=6.0, tw=5.0, mat=None, solid=False):
        a, c = self.P(p0[0], p0[1]), self.P(p1[0], p1[1])
        return ibeam(self.b, label, (a[0], a[1], p0[2]), (c[0], c[1], p1[2]), depth, flange, tf, tw, mat, solid)

    def truss(self, label, p0, p1, height, panels, chord=14.0, mat=None, solid=False, width=14.0):
        a, c = self.P(p0[0], p0[1]), self.P(p1[0], p1[1])
        return truss(self.b, label, (a[0], a[1], p0[2]), (c[0], c[1], p1[2]), height, panels, chord, mat, solid, width)

    def railing(self, label, p0, p1, **kw):
        a, c = self.P(p0[0], p0[1]), self.P(p1[0], p1[1])
        return railing(self.b, label, (a[0], a[1], p0[2]), (c[0], c[1], p1[2]), **kw)

    def sphere(self, label, x, y, z, sx, sy, sz, yaw=0.0, mat=None, solid=False):
        wx, wy = self.P(x, y)
        return sphere(self.b, label, wx, wy, z, sx, sy, sz, self.Y(yaw), mat, solid)

    def prop(self, label, name, x, y, z, yaw=0.0, **kw):
        wx, wy = self.P(x, y)
        return self.b.prop(label, name, wx, wy, z, yaw=self.Y(yaw), **kw)

    def slope(self, label, p0, p1, width, thickness=40.0, mat=None):
        a, c = self.P(p0[0], p0[1]), self.P(p1[0], p1[1])
        return self.b.slope(label, (a[0], a[1], p0[2]), (c[0], c[1], p1[2]), width, thickness, mat)

    def light(self, label, x, y, z, rgb, candela=30.0, radius=450.0, **kw):
        wx, wy = self.P(x, y)
        return self.b.accent_light(label, (wx, wy, z), rgb, candela, radius, **kw)


def hcolumn(f, label, x, y, z0, z1, flange=60.0, depth=50.0, tf=8.0, tw=6.0, mat=None, solid=True):
    """An H-section column in Frame f: flanges parallel to local x, web along local y."""
    h = z1 - z0
    zc = (z0 + z1) / 2.0
    out = [f.box(label + "_web", x, y, zc, tw, depth - 2 * tf, h, mat=mat, solid=solid)]
    for s in (-1, 1):
        out.append(f.box(label + "_fl", x, y + s * (depth / 2.0 - tf / 2.0), zc, flange, tf, h, mat=mat, solid=solid))
    return out


def hide_render(actor):
    """Keep collision, drop rendering (an invisible blocker under decoration props)."""
    comp = actor.static_mesh_component
    comp.set_editor_property("hidden_in_game", True)
    comp.set_editor_property("visible", False)
    return actor


def lava_instance(name, intensity=3.0, tiling=2.5, speed=1.0):
    """A child instance of M_IALava with its own intensity (the master's default is very bright)."""
    from matlib import lava
    path = "/Game/Materials/" + name
    parent = lava()
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mic = unreal.EditorAssetLibrary.load_asset(path)
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mic = tools.create_asset(name, "/Game/Materials", unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
    lib = unreal.MaterialEditingLibrary
    lib.set_material_instance_parent(mic, parent)
    lib.set_material_instance_scalar_parameter_value(mic, "Intensity", float(intensity))
    lib.set_material_instance_scalar_parameter_value(mic, "TilingMeters", float(tiling))
    lib.set_material_instance_scalar_parameter_value(mic, "Speed", float(speed))
    lib.update_material_instance(mic)
    unreal.EditorAssetLibrary.save_asset(path)
    return mic
