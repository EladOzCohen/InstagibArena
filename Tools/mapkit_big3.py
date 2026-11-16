"""Helpers for the big city map DM-Downtown (additive: nothing in mapkit / matlib / mapkit_b is changed).

    import mapkit, mapkit_big3 as bg
    bg.register_extra_surfaces()                       # adds the "Grass" surface (CC0 Poly Haven leafy_grass)
    bt = bg.Batches(m)                                 # collects many small boxes into a few static meshes
    paint = bt.get("RoadPaint", mat, shadow=False)     # one Batcher per material
    paint.box(cx, cy, cz, sx, sy, sz, yaw=0)           # world coordinates
    ...
    bt.flush()                                         # builds /Game/Maps/Gen/SM_Downtown_<name>_<cx>_<cy> and places them

Why batches: a 12000 x 8000 city with thousands of kerbs, window ledges, shop fronts, lines and fences as separate
actors would cost far too many draw calls on a small GPU. A Batcher keeps boxes (and bars, cylinders, prisms) per material
and per 2400 x 2400 cell and writes each cell as one generated static mesh (frustum culling still works per cell).
"""

import math
import os
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import mapkit_b  # noqa: E402
import mesh_b  # noqa: E402
import mesh_arch_b  # noqa: E402
import mesh_misc_b  # noqa: E402
from mesh_b import Mesh  # noqa: E402

CELL = 2400.0


# ------------------------------------------------------------------------------------------------ extra surfaces
def register_extra_surfaces():
    """Registers surfaces that the shared library does not have yet (in memory only; the texture is fetched on first use)."""
    import fetch_textures as ft
    import matlib
    if "Grass" not in ft.TEXTURES:
        ft.TEXTURES["Grass"] = ("ph", "leafy_grass", "1k", None)
    if "Grass" not in matlib.SURFACES:
        matlib.SURFACES["Grass"] = matlib.S("Grass", (66, 92, 42), tiling=2.5, desat=1.0, macro=0.45, macro_m=9.0, ns=0.7)
    if "Grass" not in matlib.TEX_MEAN:
        matlib.TEX_MEAN["Grass"] = (0.15, 0.14, 0.05)


# ------------------------------------------------------------------------------------------------ rectangles and transforms
class Xf:
    """The 180 degree rotation about the map centre (s = -1) or nothing (s = +1). Used to build both halves of the map from one
    description: (x, y) -> (s*x, s*y), yaw + 180."""

    def __init__(self, s):
        self.s = 1 if s >= 0 else -1

    def p(self, x, y):
        return (self.s * x, self.s * y)

    def r(self, x0, y0, x1, y1):
        a, b = self.p(x0, y0), self.p(x1, y1)
        return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))

    def yaw(self, a):
        return a if self.s > 0 else a + 180.0


def rect_subtract(rect, holes):
    """rect = (x0, y0, x1, y1); holes = list of rects. Returns rects that tile rect minus the holes (axis aligned)."""
    x0, y0, x1, y1 = rect
    xs = {x0, x1}
    for h in holes:
        for x in (h[0], h[2]):
            if x0 < x < x1:
                xs.add(x)
    xs = sorted(xs)
    out = []
    for i in range(len(xs) - 1):
        a, b = xs[i], xs[i + 1]
        cuts = sorted((max(y0, h[1]), min(y1, h[3])) for h in holes if h[0] < b and h[2] > a and h[3] > y0 and h[1] < y1)
        cur = y0
        for lo, hi in cuts:
            if lo > cur:
                out.append((a, cur, b, lo))
            cur = max(cur, hi)
        if cur < y1:
            out.append((a, cur, b, y1))
    return out


def rect_gaps(lo, hi, gaps):
    """Splits the interval lo..hi around the gaps [(centre, width), ...]; returns the solid intervals."""
    cuts = sorted((c - w / 2.0, c + w / 2.0) for c, w in gaps)
    out, cur = [], lo
    for a, b in cuts:
        if a > cur:
            out.append((cur, min(a, hi)))
        cur = max(cur, b)
    if cur < hi:
        out.append((cur, hi))
    return [(a, b) for a, b in out if b - a > 1.0]


# ------------------------------------------------------------------------------------------------ batches
class Batcher:
    """Boxes, bars, cylinders and prisms of ONE material, written as one static mesh per cell."""

    def __init__(self, name, mat, solid=False, shadow=True, max_dist=0.0, cell=CELL):
        self.name, self.mat, self.solid, self.shadow, self.max_dist, self.cell = name, mat, solid, shadow, max_dist, cell
        self.cells = {}
        self.count = 0

    def _mesh(self, x, y):
        key = (int(math.floor(x / self.cell)), int(math.floor(y / self.cell)))
        if key not in self.cells:
            self.cells[key] = Mesh()
        return self.cells[key]

    def box(self, cx, cy, cz, sx, sy, sz, yaw=0.0, pitch=0.0, roll=0.0):
        self._mesh(cx, cy).box(cx, cy, cz, sx, sy, sz, yaw=yaw, pitch=pitch, roll=roll)
        self.count += 1

    def rect(self, x0, y0, x1, y1, z0, z1, yaw=0.0):
        self.box((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), yaw=yaw)

    def bar(self, p0, p1, thick, depth=None):
        """A bar between two 3D points with a cross section thick x depth (depth is horizontal-ish, thick vertical-ish)."""
        dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length < 0.5:
            return
        yaw = math.degrees(math.atan2(dy, dx))
        pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
        cx, cy, cz = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, (p0[2] + p1[2]) / 2.0
        self.box(cx, cy, cz, length, depth or thick, thick, yaw=yaw, pitch=pitch)

    def cyl(self, cx, cy, z0, z1, r, sides=10, r1=None, caps=True):
        self._mesh(cx, cy).lathe(cx, cy, z0, z1, r, r if r1 is None else r1, sides=sides, cap_bottom=caps, cap_top=caps)
        self.count += 1

    def prism(self, poly2d, y0, y1, yaw=0.0, origin=(0.0, 0.0, 0.0)):
        """Extrudes a convex (x, z) profile between y0 and y1 (like Mesh.prism), turned by yaw about the origin point."""
        self._mesh(origin[0], origin[1]).prism(poly2d, y0, y1, yaw=yaw, origin=origin)
        self.count += 1

    def append_mesh(self, mesh, offset, yaw=0.0):
        """Adds a whole pre-built Mesh (a tree trunk, a lamp) at an offset."""
        self._mesh(offset[0], offset[1]).append(mesh, offset=offset, yaw=yaw)
        self.count += 1

    def text(self, s, x, y, z, height, yaw, thick=3.0, spacing=0.55, font=None):
        """Letters made of bars (strokes of mapkit_c's neon font); (x, y, z) = centre of the text, running along yaw."""
        import mapkit_c as kc
        font = font or kc._FONT
        k = height / 4.0
        adv = (2.0 + spacing * 2.0) * k
        n = len(s)
        total = adv * n - spacing * 2.0 * k
        c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for i, ch in enumerate(s.upper()):
            ox = -total / 2 + i * adv
            for poly in font.get(ch, []):
                for j in range(len(poly) - 1):
                    (ax, ay), (bx, by) = poly[j], poly[j + 1]
                    self.bar((x + c * (ox + ax * k), y + sn * (ox + ax * k), z - height / 2 + ay * k),
                             (x + c * (ox + bx * k), y + sn * (ox + bx * k), z - height / 2 + by * k), thick)
        return total


class Batches:
    def __init__(self, m):
        self.m = m
        self.all = {}

    def get(self, name, mat, solid=False, shadow=True, max_dist=0.0):
        if name not in self.all:
            self.all[name] = Batcher(name, mat, solid, shadow, max_dist)
        return self.all[name]

    def flush(self):
        placed = 0
        tris = 0
        for name, b in self.all.items():
            for (ix, iy), mesh in sorted(b.cells.items()):
                if not mesh.verts:
                    continue
                nm = "Downtown_%s_%d_%d" % (name, ix + 50, iy + 50)
                sm = mapkit_b.commit(nm, mesh, collision="complex" if b.solid else "none")
                a = mapkit_b.put(self.m, nm, sm, 0.0, 0.0, 0.0, mat=b.mat, solid=b.solid)
                comp = a.static_mesh_component
                if not b.shadow:
                    comp.set_editor_property("cast_shadow", False)
                if b.max_dist:
                    comp.set_editor_property("ld_max_draw_distance", float(b.max_dist))
                placed += 1
                tris += len(mesh.tris)
        unreal.log("BATCHES placed %d meshes, %d triangles" % (placed, tris))
        return placed


# ------------------------------------------------------------------------------------------------ generated shapes
_named = {}


def mesh_asset(name, builder, collision="complex"):
    """Commits (once per run) the mesh builder() under the name Downtown_<name>."""
    if name not in _named:
        _named[name] = mapkit_b.commit("Downtown_" + name, builder(), collision=collision)
    return _named[name]


def stairs_asset(width, steps, rise, run, collision="complex"):
    """Stairs climbing along +x from x = 0 (z = 0): every step a solid block down to z = 0. width along y (centred)."""
    name = "Stairs_%d_%d_%d_%d" % (width, steps, rise, int(round(run * 100)))
    return mesh_asset(name, lambda: mesh_arch_b.stairs_mesh(width, steps, rise, run, seed=3, nose=0.0), collision)


def wedge_asset(run, rise, width, collision="complex"):
    """A closed ramp wedge climbing along +x from z = 0 to rise; width along y (centred)."""
    name = "Wedge_%d_%d_%d" % (run, rise, width)
    if collision == "convex":
        # a convex hull as SIMPLE collision: the navigation grid's capsule test is lenient with convex shapes (a triangle mesh
        # rejects every node on a slope over 20 degrees and accepts nodes inside the solid)
        if name not in _named:
            sm = mapkit_b.commit("Downtown_" + name, mesh_misc_b.ramp_wedge(run, rise, width), collision="none")
            sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            try:
                sub.remove_collisions(sm)
            except Exception:                              # noqa: BLE001
                pass
            n = sub.set_convex_decomposition_collisions(sm, 1, 24, 100000)
            unreal.log("WEDGE %s convex hulls: %s" % (name, n))
            unreal.EditorAssetLibrary.save_loaded_asset(sm)
            _named[name] = sm
        return _named[name]
    return mesh_asset(name, lambda: mesh_misc_b.ramp_wedge(run, rise, width), collision)


def flat_stairs(m, label, x, y, z0, yaw, width, rise, steps=None, step_h=20.0, run=36.0, mat=None):
    """Places a solid stair flight whose first step starts at (x, y) at height z0 and climbs along yaw. Returns the run length."""
    steps = steps or int(round(rise / step_h))
    sh = rise / float(steps)
    sm = stairs_asset(int(width), steps, int(round(sh)), run)
    mapkit_b.put(m, label, sm, x, y, z0, yaw=yaw, mat=mat)
    return steps * run


def stair_ramp(m, label, x, y, z0, yaw, width, rise, run, mat=None, step_h=20.0):
    """Looks like stairs, walks like a ramp: the bots' navigation grid cannot link the cells of real steps (the capsule always
    touches a riser) but it links slopes up to about 28 degrees. So the collision is a hidden wedge and the visible steps (no
    collision) sit 10 cm lower, which puts the walking plane halfway between the nosings and the treads."""
    steps = max(1, int(round(rise / step_h)))
    sm = stairs_asset(int(width), steps, int(round(rise / steps)), run / float(steps), collision="none")
    mapkit_b.put(m, label, sm, x, y, z0 - 10.0, yaw=yaw, mat=mat, solid=False)
    wedge = wedge_asset(int(run), int(rise), int(width), collision="convex")
    a = mapkit_b.put(m, label + "_Col", wedge, x, y, z0, yaw=yaw, mat=mat, solid=True)
    a.set_actor_hidden_in_game(True)
    return run


def ramp(m, label, x, y, z0, yaw, width, rise, run, mat=None):
    sm = wedge_asset(int(run), int(rise), int(width))
    mapkit_b.put(m, label, sm, x, y, z0, yaw=yaw, mat=mat)
    return run


def tree_trunk_mesh(height, radius, seed=1):
    """A broadleaf tree trunk: flared foot, tapered stem, a fork into 4 limbs that reach into the crown. Origin: foot centre at z = 0."""
    import random
    rr = random.Random(seed)
    m = Mesh()
    m.lathe(0, 0, 0, height * 0.18, radius * 1.45, radius * 1.05, sides=10, segments=2, cap_bottom=True, cap_top=False)
    m.lathe(0, 0, height * 0.18, height * 0.62, radius * 1.05, radius * 0.78, sides=10, segments=2, cap_bottom=False, cap_top=False,
            rfn=lambda th, t: 1.0 + 0.06 * math.sin(th * 3 + seed))
    top = (0.0, 0.0, height * 0.62)
    n_limbs = 4
    for i in range(n_limbs):
        a = 2 * math.pi * i / n_limbs + rr.uniform(-0.4, 0.4)
        reach = height * rr.uniform(0.24, 0.34)
        end = (math.cos(a) * reach, math.sin(a) * reach, height * rr.uniform(0.9, 1.05))
        mid = (end[0] * 0.35, end[1] * 0.35, height * 0.74)
        pts = [top, mid, end]
        m.append(mesh_misc_b.tube(pts, radius * 0.62, sides=7, jitter=0.05, seed=seed + i))
        # one twig off each limb
        tw = (end[0] * 1.25 + rr.uniform(-30, 30), end[1] * 1.25 + rr.uniform(-30, 30), end[2] + height * 0.08)
        m.append(mesh_misc_b.tube([mid, end, tw], radius * 0.3, sides=5, seed=seed + 9 + i))
    return m


# ------------------------------------------------------------------------------------------------ frames on walls
class WF:
    """A frame on a straight axis-aligned wall. p0 = a point on the wall plane, d = unit vector along the wall, n = unit
    vector pointing out of the wall (toward the viewer). a = distance along d, o = distance out of the wall, z = height.
    Everything goes into Batchers, so a whole shop front costs no actors."""

    def __init__(self, p0, d, n):
        self.p0, self.d, self.n = (float(p0[0]), float(p0[1])), d, n

    def pt(self, a, o):
        return (self.p0[0] + self.d[0] * a + self.n[0] * o, self.p0[1] + self.d[1] * a + self.n[1] * o)

    def rect(self, bat, a0, a1, o0, o1, z0, z1):
        p, q = self.pt(a0, o0), self.pt(a1, o1)
        bat.rect(min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]), z0, z1)

    def prism(self, bat, a0, a1, poly):
        """poly = convex profile [(o, z), ...] extruded along the wall from a0 to a1 (awnings, cornices, pediments)."""
        yaw = math.degrees(math.atan2(self.n[1], self.n[0]))
        ly = (-self.n[1], self.n[0])
        sgn = self.d[0] * ly[0] + self.d[1] * ly[1]
        y0, y1 = sorted((a0 * sgn, a1 * sgn))
        bat.prism(poly, y0, y1, yaw=yaw, origin=(self.p0[0], self.p0[1], 0.0))

    def text(self, bat, s, a, o, z, height, thick=3.0):
        x, y = self.pt(a, o)
        yaw = math.degrees(math.atan2(-self.n[0], self.n[1]))
        return bat.text(s, x, y, z, height, yaw, thick=thick)

    def text_width(self, s, height, spacing=0.55):
        k = height / 4.0
        return (2.0 + spacing * 2.0) * k * len(s) - spacing * 2.0 * k
