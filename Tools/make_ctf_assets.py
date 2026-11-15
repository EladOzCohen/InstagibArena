"""Builds the Capture the Flag assets in /Game/CTF (pure python geometry through Geometry Script, materials through the material editing library).

  /Game/CTF/SM_IAFlagPole    the flag pole with a collar and a ball on top (slot: M_IAFlagMetal)
  /Game/CTF/SM_IAFlagCloth   a pennant, 14 x 8 quads, pole edge at u = 0 (slot: M_IAFlag)
  /Game/CTF/SM_IAFlagBeam    an open tube 24 m high for the faint light beam (slot: M_IAFlagBeam)
  /Game/CTF/SM_IABasePad     the base pad: a disc of radius 100 cm, 4 cm high, with a socket in the middle (slot: M_IABase)
  /Game/CTF/M_IAFlag         cloth: parameters TeamColor, WaveStrength; the cloth waves in the vertex shader (world position offset)
  /Game/CTF/M_IAFlagBeam     additive beam: TeamColor, Intensity
  /Game/CTF/M_IABase         pad: TeamColor, Glow (a team coloured ring is the capture zone)
  /Game/CTF/M_IAFlagMetal    dark steel for the pole

The code (IAFlag.cpp, IAFlagBase.cpp) loads the meshes by path and makes dynamic instances of the materials for the team colour.
/Game/CTF is listed in DirectoriesToAlwaysCook (Config/DefaultGame.ini).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools/make_ctf_assets.py -unattended -nullrhi -nosplash
Output lines start with CTFASSETS; the last one is CTFASSETS_DONE.
"""

import math
import os
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import mapkit_b  # noqa: E402  (only used for the winding detection)

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
PATH = "/Game/CTF"


def log(msg):
    unreal.log("CTFASSETS " + msg)


# ------------------------------------------------------------------------------------------------ tiny mesh builder
class M:
    def __init__(self):
        self.v, self.n, self.uv, self.t = [], [], [], []

    def vert(self, p, uv):
        self.v.append(p)
        self.n.append([0.0, 0.0, 0.0])
        self.uv.append(uv)
        return len(self.v) - 1

    def tri(self, a, b, c):
        """(b-a)x(c-a) must point out."""
        self.t.append((a, b, c))
        pa, pb, pc = self.v[a], self.v[b], self.v[c]
        ab = [pb[i] - pa[i] for i in range(3)]
        ac = [pc[i] - pa[i] for i in range(3)]
        nrm = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]]
        for i in (a, b, c):
            for k in range(3):
                self.n[i][k] += nrm[k]

    def finish(self):
        for nn in self.n:
            ln = math.sqrt(nn[0] ** 2 + nn[1] ** 2 + nn[2] ** 2) or 1.0
            nn[0] /= ln
            nn[1] /= ln
            nn[2] /= ln
        return self


def lathe(m, profile, sides, uv_fn=None):
    """Surface of revolution around Z. profile = [(radius, z), ...] from the bottom up. Outward normals."""
    rows = []
    for (r, z) in profile:
        row = []
        for s in range(sides):
            a = 2.0 * math.pi * s / sides
            u = s / float(sides)
            uv = uv_fn(r, z, a) if uv_fn else (u, z / 100.0)
            row.append(m.vert([r * math.cos(a), r * math.sin(a), z], uv))
        rows.append(row)
    for i in range(len(profile) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            a, b = rows[i][s], rows[i][s2]
            c, d = rows[i + 1][s], rows[i + 1][s2]
            if profile[i][0] > 1e-6:
                m.tri(a, b, c)
            if profile[i + 1][0] > 1e-6:
                m.tri(b, d, c)


def build_pole():
    m = M()
    profile = [(0.01, 0.0), (10.0, 0.0), (10.0, 5.0), (5.5, 9.0), (3.3, 13.0), (3.2, 236.0), (4.6, 238.0), (6.2, 242.0),
               (6.6, 247.0), (5.4, 251.0), (3.0, 254.0), (0.01, 255.5)]
    lathe(m, profile, 12)
    return m.finish()


def build_cloth():
    nx, nz = 14, 8
    width, height = 118.0, 86.0
    top = 233.0
    pole_gap = 3.4
    m = M()
    grid = []
    for iz in range(nz + 1):
        row = []
        for ix in range(nx + 1):
            u = ix / float(nx)
            v = iz / float(nz)
            h = height * (1.0 - 0.42 * u)              # pennant: the free end is shorter
            y = pole_gap + width * u
            z = top - h * v
            row.append(m.vert([0.0, y, z], (u, v)))
        grid.append(row)
    for iz in range(nz):
        for ix in range(nx):
            a, b = grid[iz][ix], grid[iz][ix + 1]
            c, d = grid[iz + 1][ix], grid[iz + 1][ix + 1]
            # facing +X: (b-a) x (c-a) with b along +Y, c along -Z gives +X ... check below: y x (-z) = -x, so use (a, c, b)
            m.tri(a, c, b)
            m.tri(b, c, d)
    return m.finish()


def build_beam():
    m = M()
    sides = 14
    height = 2400.0
    steps = 6
    rows = []
    for i in range(steps + 1):
        k = i / float(steps)
        r = 15.0 - 7.0 * k
        row = []
        for s in range(sides + 1):                       # a duplicate seam vertex so the uv wraps cleanly
            a = 2.0 * math.pi * (s % sides) / sides
            row.append(m.vert([r * math.cos(a), r * math.sin(a), height * k], (s / float(sides), k)))
        rows.append(row)
    for i in range(steps):
        for s in range(sides):
            a, b = rows[i][s], rows[i][s + 1]
            c, d = rows[i + 1][s], rows[i + 1][s + 1]
            m.tri(a, b, c)
            m.tri(b, d, c)
    return m.finish()


def build_pad():
    m = M()
    sides = 64

    def planar(r, z, a):
        return (0.5 + 0.5 * (r / 100.0) * math.cos(a), 0.5 + 0.5 * (r / 100.0) * math.sin(a))

    # Outer wall with a small bevel, then the top face as one fan (centre at z = 4).
    prof = [(100.0, 0.0), (100.0, 2.4), (98.2, 4.0), (14.0, 4.0), (14.0, 9.0), (11.0, 12.0), (0.01, 12.0)]
    lathe(m, prof, sides, planar)
    return m.finish()


# ------------------------------------------------------------------------------------------------ materials
def node(mat, cls, x, y):
    return lib.create_material_expression(mat, cls, x, y)


def link(a, b, to_input, out=""):
    lib.connect_material_expressions(a, out, b, to_input)


class MB:
    """Small expression builder for one material."""

    def __init__(self, mat):
        self.mat = mat
        self.x = -1200
        self.y = 0

    def _pos(self):
        self.y += 90
        return self.x, self.y

    def const(self, v):
        n = node(self.mat, unreal.MaterialExpressionConstant, *self._pos())
        n.set_editor_property("r", v)
        return n

    def const3(self, r, g, b):
        n = node(self.mat, unreal.MaterialExpressionConstant3Vector, *self._pos())
        n.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
        return n

    def vparam(self, name, rgb):
        n = node(self.mat, unreal.MaterialExpressionVectorParameter, *self._pos())
        n.set_editor_property("parameter_name", name)
        n.set_editor_property("default_value", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        return n

    def sparam(self, name, v):
        n = node(self.mat, unreal.MaterialExpressionScalarParameter, *self._pos())
        n.set_editor_property("parameter_name", name)
        n.set_editor_property("default_value", v)
        return n

    def op(self, cls, a, b=None, ia="A", ib="B", out_a=""):
        n = node(self.mat, cls, *self._pos())
        link(a, n, ia, out_a)
        if b is not None:
            link(b, n, ib)
        return n

    def mul(self, a, b):
        return self.op(unreal.MaterialExpressionMultiply, a, b)

    def add(self, a, b):
        return self.op(unreal.MaterialExpressionAdd, a, b)

    def sub(self, a, b):
        return self.op(unreal.MaterialExpressionSubtract, a, b)

    def lerp(self, a, b, alpha):
        n = node(self.mat, unreal.MaterialExpressionLinearInterpolate, *self._pos())
        link(a, n, "A")
        link(b, n, "B")
        link(alpha, n, "Alpha")
        return n

    def sat(self, a):
        n = node(self.mat, unreal.MaterialExpressionSaturate, *self._pos())
        link(a, n, "")
        return n

    def sin(self, a):
        n = node(self.mat, unreal.MaterialExpressionSine, *self._pos())
        n.set_editor_property("period", 6.2831853)
        link(a, n, "")
        return n

    def power(self, a, e):
        n = node(self.mat, unreal.MaterialExpressionPower, *self._pos())
        link(a, n, "Base")
        link(e, n, "Exponent")
        return n

    def uv(self):
        return node(self.mat, unreal.MaterialExpressionTextureCoordinate, *self._pos())

    def comp(self, a, ch):
        n = node(self.mat, unreal.MaterialExpressionComponentMask, *self._pos())
        n.set_editor_property("r", ch == "r")
        n.set_editor_property("g", ch == "g")
        n.set_editor_property("b", ch == "b")
        link(a, n, "")
        return n

    def time(self):
        return node(self.mat, unreal.MaterialExpressionTime, *self._pos())

    def band(self, r, a, b, k=60.0):
        """1 where a < r < b, with soft edges."""
        rising = self.sat(self.mul(self.sub(r, self.const(a)), self.const(k)))
        falling = self.sat(self.mul(self.sub(self.const(b), r), self.const(k)))
        return self.mul(rising, falling)


def new_material(name):
    full = "%s/%s" % (PATH, name)
    if eal.does_asset_exist(full):
        eal.delete_asset(full)
    return tools.create_asset(name, PATH, unreal.Material, unreal.MaterialFactoryNew())


def finish_material(mat):
    lib.recompile_material(mat)
    eal.save_asset("%s/%s" % (PATH, mat.get_name()))


def make_cloth_material():
    mat = new_material("M_IAFlag")
    mat.set_editor_property("two_sided", True)
    b = MB(mat)
    team = b.vparam("TeamColor", (1.0, 0.08, 0.08))
    strength = b.sparam("WaveStrength", 1.0)
    uv = b.uv()
    u = b.comp(uv, "r")
    v = b.comp(uv, "g")
    t = b.time()

    # Two travelling waves along the flag; the pole edge (u = 0) stays still, the free end moves most.
    phase1 = b.add(b.mul(t, b.const(3.4)), b.add(b.mul(u, b.const(7.0)), b.mul(v, b.const(2.2))))
    phase2 = b.add(b.mul(t, b.const(5.6)), b.add(b.mul(u, b.const(13.0)), b.mul(v, b.const(3.5))))
    w1 = b.mul(b.sin(phase1), b.const(8.0))
    w2 = b.mul(b.sin(phase2), b.const(2.6))
    amp = b.mul(b.mul(u, u), strength)
    # a wind that pushes the cloth a little to one side and the free end downwards a bit when it flaps
    disp_x = b.mul(b.add(w1, w2), amp)
    disp_z = b.mul(b.mul(u, u), b.mul(b.sub(b.const(0.0), b.sat(b.add(b.sin(phase1), b.const(0.4)))), b.mul(strength, b.const(4.0))))
    wpo = node(mat, unreal.MaterialExpressionAppendVector, -400, 400)
    xy = node(mat, unreal.MaterialExpressionAppendVector, -600, 400)
    link(disp_x, xy, "A")
    link(b.const(0.0), xy, "B")
    link(xy, wpo, "A")
    link(disp_z, wpo, "B")
    lib.connect_material_property(wpo, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    # Cloth shading: fold shading from the same wave, a darker lower edge, a lighter hem along the top.
    fold = b.add(b.const(0.88), b.mul(b.sin(phase1), b.const(0.12)))
    edge_dark = b.lerp(b.const(1.0), b.const(0.72), b.power(v, b.const(2.0)))
    hem = b.band(v, -0.1, 0.07, 80.0)
    base = b.mul(team, b.mul(fold, edge_dark))
    base = b.lerp(base, b.mul(team, b.const(1.8)), b.mul(hem, b.const(0.5)))
    lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(b.mul(team, b.const(0.07)), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.connect_material_property(b.const(0.86), "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(b.const(0.0), "", unreal.MaterialProperty.MP_METALLIC)
    lib.connect_material_property(b.const(0.2), "", unreal.MaterialProperty.MP_SPECULAR)
    finish_material(mat)
    return mat


def make_beam_material():
    mat = new_material("M_IAFlagBeam")
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    b = MB(mat)
    team = b.vparam("TeamColor", (1.0, 0.08, 0.08))
    intensity = b.sparam("Intensity", 1.0)
    uv = b.uv()
    u = b.comp(uv, "r")
    v = b.comp(uv, "g")                                  # 0 at the foot, 1 at the top
    # Fades out toward the top, and in over the first metre; the sides are softer than the middle of the tube.
    up = b.power(b.sub(b.const(1.0), v), b.const(1.6))
    foot = b.sat(b.mul(v, b.const(60.0)))
    shimmer = b.add(b.const(0.85), b.mul(b.sin(b.add(b.mul(b.time(), b.const(1.5)), b.mul(v, b.const(9.0)))), b.const(0.15)))
    glow = b.mul(b.mul(up, foot), b.mul(shimmer, b.mul(intensity, b.const(0.16))))
    lib.connect_material_property(b.mul(team, glow), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish_material(mat)
    return mat


def make_base_material():
    mat = new_material("M_IABase")
    b = MB(mat)
    team = b.vparam("TeamColor", (1.0, 0.08, 0.08))
    glow = b.sparam("Glow", 0.55)
    uv = b.uv()
    centre = node(mat, unreal.MaterialExpressionConstant2Vector, -1200, 700)
    centre.set_editor_property("r", 0.5)
    centre.set_editor_property("g", 0.5)
    dist = node(mat, unreal.MaterialExpressionDistance, -1000, 700)
    link(uv, dist, "A")
    link(centre, dist, "B")
    r = b.mul(dist, b.const(2.0))                         # 0 in the middle, 1 at the edge

    outer = b.band(r, 0.915, 0.985, 70.0)                 # the capture zone ring
    inner = b.band(r, 0.60, 0.62, 90.0)                   # a thin inner ring
    plate = b.sat(b.mul(b.sub(b.const(0.17), r), b.const(60.0)))   # the socket in the middle
    ring = b.sat(b.add(outer, b.mul(inner, b.const(0.7))))
    zone = b.sat(b.mul(b.sub(b.const(0.915), r), b.const(30.0)))

    concrete = b.const3(0.055, 0.058, 0.062)
    metal = b.const3(0.03, 0.03, 0.034)
    floor_col = b.add(concrete, b.mul(team, b.mul(zone, b.const(0.06))))   # a faint team tint over the whole zone
    base = b.lerp(floor_col, team, ring)
    base = b.lerp(base, metal, plate)
    lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(b.mul(team, b.mul(ring, glow)), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.connect_material_property(b.lerp(b.lerp(b.const(0.86), b.const(0.4), ring), b.const(0.35), plate), "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(b.mul(plate, b.const(0.9)), "", unreal.MaterialProperty.MP_METALLIC)
    finish_material(mat)
    return mat


def make_metal_material():
    mat = new_material("M_IAFlagMetal")
    b = MB(mat)
    lib.connect_material_property(b.const3(0.10, 0.105, 0.115), "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(b.const(0.8), "", unreal.MaterialProperty.MP_METALLIC)
    lib.connect_material_property(b.const(0.42), "", unreal.MaterialProperty.MP_ROUGHNESS)
    finish_material(mat)
    return mat


# ------------------------------------------------------------------------------------------------ meshes
def commit(name, m, material):
    path = "%s/SM_%s" % (PATH, name)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    flip = mapkit_b._winding_flip()
    buf = unreal.GeometryScriptSimpleMeshBuffers()
    buf.set_editor_property("vertices", [unreal.Vector(*p) for p in m.v])
    buf.set_editor_property("normals", [unreal.Vector(*n) for n in m.n])
    buf.set_editor_property("uv0", [unreal.Vector2D(u[0], u[1]) for u in m.uv])
    buf.set_editor_property("triangles", [unreal.IntVector(a, c, b) if flip else unreal.IntVector(a, b, c) for (a, b, c) in m.t])
    dm = unreal.DynamicMesh()
    unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dm, buf, 0)
    nopts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    nopts.set_editor_property("enable_recompute_normals", False)
    nopts.set_editor_property("enable_recompute_tangents", True)
    nopts.set_editor_property("collision_mode", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    res = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, path, nopts)
    sm = res[0] if isinstance(res, tuple) else res
    if sm is None:
        raise RuntimeError("could not create " + path)
    sm = eal.load_asset(path)
    sm.set_material(0, material)
    # No collision at all: the flag and the pad are looked at, never bumped into.
    try:
        bs = sm.get_editor_property("body_setup")
        if bs:
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
            bs.set_editor_property("agg_geom", unreal.KAggregateGeom())
    except Exception as e:                       # noqa: BLE001
        log("collision reset failed for %s: %s" % (name, e))
    eal.save_loaded_asset(sm)
    b = sm.get_bounds()
    log("%s verts=%d tris=%d bounds origin=%s extent=%s" % (name, len(m.v), len(m.t), b.origin, b.box_extent))
    return sm


if not eal.does_directory_exist(PATH):
    eal.make_directory(PATH)

mat_cloth = make_cloth_material()
mat_beam = make_beam_material()
mat_base = make_base_material()
mat_metal = make_metal_material()

commit("IAFlagPole", build_pole(), mat_metal)
commit("IAFlagCloth", build_cloth(), mat_cloth)
commit("IAFlagBeam", build_beam(), mat_beam)
commit("IABasePad", build_pad(), mat_base)
unreal.log("CTFASSETS_DONE")
