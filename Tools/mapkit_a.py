"""Building helpers for the realistic rebuilds of DM-Foundry and DM-Dock (additive to mapkit.MapBuilder).

    import mapkit, mapkit_a as ka
    b = mapkit.MapBuilder("/Game/Maps/DM-Foo")
    ka.strut(b, "Brace", (0, 0, 0), (200, 0, 300), 8, steel)       # a box between two 3D points
    ka.rail(b, "Rail", (0, 0, 450), (800, 0, 450), steel)           # handrail: posts + top and mid rail (no collision)
    w = ka.Wall(b, (0, 2400), 180)                                   # frame on a wall: u along it, v into the room
    w.box("Cornice", 0, 20, 1400, 1440, 4800, 60, mat)
    ka.container(b, "C1", 450, 700, 0, 0, mat)                       # shipping container with corner posts and door bars

Everything decorative defaults to solid=False (no collision). Pass solid=True for pieces the players should bump into.
"""

import math

import unreal


def strut(b, label, p0, p1, thick, mat, thick2=None, solid=False, roll=0.0):
    """A box of cross section thick x thick2 running from 3D point p0 to p1 (beams, braces, rails, chains)."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    run = math.hypot(dx, dy)
    length = math.sqrt(run * run + dz * dz)
    if length < 0.5:
        return None
    yaw = math.degrees(math.atan2(dy, dx)) if run > 1e-6 else 0.0
    pitch = math.degrees(math.atan2(dz, run))
    cx, cy, cz = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, (p0[2] + p1[2]) / 2.0
    return b.box(label, cx, cy, cz, length, thick, thick2 if thick2 is not None else thick, yaw=yaw, pitch=pitch,
                 mat=mat, solid=solid)


def rail(b, label, p0, p1, mat, height=105.0, post_every=240.0, post=5.0, solid=False, mid=True, post_mat=None):
    """Handrail from p0 to p1 (x, y, z of the deck surface at both ends; works on slopes). No collision by default."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    n = max(1, int(math.ceil(length / post_every)))
    pm = post_mat or mat
    for i in range(n + 1):
        f = i / float(n)
        x, y, z = p0[0] + dx * f, p0[1] + dy * f, p0[2] + dz * f
        b.box(label + "_post", x, y, z + height / 2.0, post, post, height, mat=pm, solid=solid)
    strut(b, label + "_top", (p0[0], p0[1], p0[2] + height), (p1[0], p1[1], p1[2] + height), post * 1.2, mat, solid=solid)
    if mid:
        strut(b, label + "_mid", (p0[0], p0[1], p0[2] + height * 0.5), (p1[0], p1[1], p1[2] + height * 0.5),
              post * 0.8, mat, solid=solid)


class Wall:
    """A local frame on a wall. origin = point on the room-side face of the wall (x, y); yaw = direction of u in world.

    u runs along the wall, v points from the wall face into the room (negative v = inside the wall), z is world height.
    Wall yaws for a rectangular room: south wall 0, east wall 90, north wall 180, west wall 270.
    """

    def __init__(self, b, origin, yaw):
        self.b = b
        self.ox, self.oy = origin
        self.yaw = yaw
        self.c = math.cos(math.radians(yaw))
        self.s = math.sin(math.radians(yaw))

    def xy(self, u, v):
        return (self.ox + self.c * u - self.s * v, self.oy + self.s * u + self.c * v)

    def box(self, label, u, v, z0, z1, du, dv, mat, solid=False, extra_yaw=0.0):
        """Box with its centre at (u, v), spanning z0..z1, du long along the wall and dv deep."""
        x, y = self.xy(u, v)
        return self.b.box(label, x, y, (z0 + z1) / 2.0, du, dv, z1 - z0, yaw=self.yaw + extra_yaw, mat=mat, solid=solid)

    def strut(self, label, p0, p1, thick, mat, thick2=None, solid=False):
        """p0, p1 = (u, v, z)."""
        a = self.xy(p0[0], p0[1])
        c = self.xy(p1[0], p1[1])
        return strut(self.b, label, (a[0], a[1], p0[2]), (c[0], c[1], p1[2]), thick, mat, thick2, solid)

    def cyl(self, label, u, v, z0, z1, dia, mat, solid=False):
        x, y = self.xy(u, v)
        return self.b.column(label, x, y, z0, z1, dia, mat=mat, solid=solid)


def window(w, label, u, z0, width, height, frame_mat, sill_mat, pane_mat, mullions=2, depth=-60.0, sill_out=14.0):
    """A recessed window in wall frame w: dark pane set back in the opening, frame, mullions, projecting sill and head.

    The opening itself must already exist (the wall is built from piers and bands around it)."""
    t = 8.0
    w.box(label + "_pane", u, depth, z0, z0 + height, width, 4.0, pane_mat, solid=True)
    for side in (-1, 1):
        w.box(label + "_jamb", u + side * (width / 2 - t / 2), depth + 6, z0, z0 + height, t, 14.0, frame_mat)
    w.box(label + "_head", u, depth + 6, z0 + height - t, z0 + height, width, 14.0, frame_mat)
    w.box(label + "_bottom", u, depth + 6, z0, z0 + t, width, 14.0, frame_mat)
    for i in range(mullions):
        f = (i + 1) / float(mullions + 1)
        w.box(label + "_mull", u - width / 2 + width * f, depth + 6, z0, z0 + height, 5.0, 10.0, frame_mat)
    w.box(label + "_transom", u, depth + 6, z0 + height * 0.62, z0 + height * 0.62 + 5, width, 10.0, frame_mat)
    w.box(label + "_sill", u, sill_out / 2 - 2, z0 - 12, z0, width + 40, sill_out + 4, sill_mat)
    w.box(label + "_lintel", u, sill_out / 2 - 2, z0 + height, z0 + height + 20, width + 40, sill_out + 4, sill_mat)


def container(b, label, x, y, z0, yaw, mat, length=600.0, width=240.0, height=240.0, steel=None, solid=True,
              doors_at=1, dark=None):
    """A shipping container: body (corrugated paint), corner posts, top and bottom rails, door bars on one end."""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cz = z0 + height / 2.0
    body = b.box(label, x, y, cz, length, width, height, yaw=yaw, mat=mat, solid=solid)
    st = steel or mat
    hl, hw = length / 2.0, width / 2.0
    p = 12.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = x + c * sx * (hl - p / 2) - s * sy * (hw + 0.5)
            py = y + s * sx * (hl - p / 2) + c * sy * (hw + 0.5)
            b.box(label + "_post", px, py, cz, p, p, height + 2, yaw=yaw, mat=st, solid=False)
    for sy in (-1, 1):
        for zz in (z0 + 4, z0 + height - 4):
            px = x - s * sy * (hw + 0.5)
            py = y + c * sy * (hw + 0.5)
            b.box(label + "_rail", px, py, zz, length - 2 * p, 7.0, 8.0, yaw=yaw, mat=st, solid=False)
    if doors_at:
        ex, ey = x + c * doors_at * (hl + 1.0), y + s * doors_at * (hl + 1.0)
        for k in (-0.55, -0.18, 0.18, 0.55):
            b.box(label + "_bar", ex - s * k * hw, ey + c * k * hw, cz, 3.0, 4.0, height - 22, yaw=yaw, mat=st,
                  solid=False)
        b.box(label + "_hinge", ex, ey, cz, 4.0, width - 20, 6.0, yaw=yaw, mat=st, solid=False)
    return body


def pallet(b, label, x, y, z0, yaw=0.0, mat=None, length=120.0, width=100.0):
    """A wooden pallet (deck boards on three runners). Returns the top height."""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for k in (-1, 0, 1):
        b.box(label + "_runner", x - s * k * (width / 2 - 6), y + c * k * (width / 2 - 6), z0 + 5, length, 10.0, 10.0,
              yaw=yaw, mat=mat, solid=False)
    b.box(label + "_deck", x, y, z0 + 12, length, width, 4.0, yaw=yaw, mat=mat, solid=False)
    return z0 + 14.0


def tank_bands(b, label, x, y, z0, z1, dia, mat, every=180.0, extra=8.0, h=14.0):
    """Weld seams / stiffening rings around a vertical tank (thin wide cylinders)."""
    z = z0 + every / 2.0
    while z < z1:
        b.column(label + "_ring", x, y, z - h / 2, z + h / 2, dia + extra, mat=mat, solid=False)
        z += every


def set_shadow(actor, cast=True):
    """Switch off shadow casting for distant decor (saves shadow map cost)."""
    if actor is None:
        return
    try:
        actor.static_mesh_component.set_editor_property("cast_shadow", bool(cast))
    except Exception:  # noqa: BLE001
        pass


def ramp(b, label, p0, p1, width, deck, steel, rail_mat, thickness=40.0, legs=(0.3, 0.65), post_every=230.0):
    """A solid ramp slab (like MapBuilder.slope) with side stringers, handrails and trestle legs (all without collision)."""
    b.slope(label, p0, p1, width, thickness, mat=deck)
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    run = math.hypot(dx, dy)
    length = math.hypot(run, dz)
    pitch = math.atan2(dz, run)
    yaw = math.degrees(math.atan2(dy, dx))
    yr = math.radians(yaw)
    lat = (-math.sin(yr), math.cos(yr))
    nrm = (-math.sin(pitch) * math.cos(yr), -math.sin(pitch) * math.sin(yr), math.cos(pitch))
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2 - thickness / 2 * math.cos(pitch))
    for side in (-1, 1):
        off = side * (width / 2 - 5)
        c = (mid[0] + lat[0] * off - nrm[0] * 5, mid[1] + lat[1] * off - nrm[1] * 5, mid[2] - nrm[2] * 5)
        b.box(label + "_Stringer", c[0], c[1], c[2], length, 10, 70, yaw=yaw, pitch=math.degrees(pitch), mat=steel,
              solid=False)
        o = side * (width / 2 - 3)
        e0 = (p0[0] + lat[0] * o, p0[1] + lat[1] * o, p0[2])
        e1 = (p1[0] + lat[0] * o, p1[1] + lat[1] * o, p1[2])
        rail(b, label + "_Rail", e0, e1, rail_mat, post_every=post_every)
        for t in legs:
            lx, ly, lz = (e0[0] + (e1[0] - e0[0]) * t, e0[1] + (e1[1] - e0[1]) * t, e0[2] + dz * t)
            if lz - 40 > 20:
                b.box(label + "_Leg", lx, ly, (lz - 40) / 2, 18, 18, lz - 40, mat=steel, solid=False)


def pipe(b, label, p0, p1, dia, mat, solid=False):
    """A round pipe (the engine cylinder) between two 3D points, any direction."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 0.5:
        return None
    pitch = math.degrees(math.acos(max(-1.0, min(1.0, dz / length))))
    yaw = math.degrees(math.atan2(-dy, -dx)) if math.hypot(dx, dy) > 1e-6 else 0.0
    return b._place(label, b.cylinder, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2),
                    (dia / 100.0, dia / 100.0, length / 100.0), yaw, pitch, mat, solid)


def disc(b, label, x, y, z_top, rx, ry, thick, mat, yaw=0.0):
    """A flat elliptical disc lying on the ground (stains, patches, round plates). No collision."""
    return b._place(label, b.cylinder, (x, y, z_top - thick / 2.0), (rx * 2 / 100.0, ry * 2 / 100.0, thick / 100.0),
                    yaw, 0.0, mat, False)


def cyl(b, label, x, y, z0, z1, dia_x, dia_y, mat, yaw=0.0, solid=False):
    """Elliptical or round vertical cylinder."""
    h = z1 - z0
    return b._place(label, b.cylinder, (x, y, z0 + h / 2.0), (dia_x / 100.0, dia_y / 100.0, h / 100.0), yaw, 0.0, mat,
                    solid)


# Thin non-solid details do not need to cast shadows (saves shadow-map cost on weak GPUs): patch MapBuilder._place.
def _install_shadow_patch():
    import mapkit
    if getattr(mapkit.MapBuilder, "_ka_patched", False):
        return
    orig = mapkit.MapBuilder._place

    def _place(self, label, mesh, loc, scale, yaw, pitch, mat, solid):
        actor = orig(self, label, mesh, loc, scale, yaw, pitch, mat, solid)
        try:
            if not solid and min(scale) <= 0.13:
                actor.static_mesh_component.set_editor_property("cast_shadow", False)
        except Exception:  # noqa: BLE001
            pass
        return actor

    mapkit.MapBuilder._place = _place
    mapkit.MapBuilder._ka_patched = True


_install_shadow_patch()
