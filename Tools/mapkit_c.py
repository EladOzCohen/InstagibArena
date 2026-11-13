"""Extra building blocks for the city maps (DM-Skyline, DM-Neon): a facade material with a procedural window grid,
roll-capable shapes, neon letters, cars, rooftop machinery, shopfronts.  Additive: nothing in mapkit/matlib is changed.

    import mapkit, mapkit_c as kc
    b = mapkit.MapBuilder("/Game/Maps/DM-Skyline")
    wall = kc.facade("SkyBrick", wall="BrickRed", ...)     # M_IAFacade instance: wall texture + windows in the shader
    kc.building(b, "Block", 0, 0, 1500, 1500, -1700, 600, wall, roof_mat)

Why a shader for windows: a 12-floor facade with 40 windows per floor would be 500 actors per building. The facade
material (M_IAFacade) draws the window grid (frames, glass, sills, lintels, lit and curtained windows) from world
position, so big backdrop buildings cost one actor. Real geometry (string courses, sills, shopfronts, balconies) is
added only where the player looks closely.
"""

import math
import os
import random
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import mapkit  # noqa: E402
import matlib  # noqa: E402
from matlib import _node, _link, _scalar, _vector, _texobj, _append, _custom, _new_asset  # noqa: E402

lib = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary

FACADE_PATH = "/Game/Materials/M_IAFacade"

# --------------------------------------------------------------------------------------------------- HLSL
HLSL_FACADE_COMMON = """
float3 n = normalize(Nrm);
float2 t2 = normalize(float2(-n.y, n.x) + float2(0.0001, 0.0));
float u = dot(Pos.xy, t2);
float vert = 1.0 - smoothstep(0.30, 0.55, abs(n.z));
float CW = S1.x; float CH = S1.y; float WW = S1.z; float WH = S1.w;
float Sill = S2.x; float Lit = S2.y; float Seed = S2.z; float GridZ = S2.w;
float2 cellsz = float2(CW, CH);
float2 g = float2(u, Pos.z - GridZ) / cellsz;
float2 id = floor(g);
float2 lp = frac(g) * cellsz;
float x0 = (CW - WW) * 0.5; float x1 = x0 + WW;
float y0 = Sill; float y1 = Sill + WH;
float dxm = min(lp.x - x0, x1 - lp.x);
float dym = min(lp.y - y0, y1 - lp.y);
float inside = (dxm > 0.0 && dym > 0.0) ? 1.0 : 0.0;
inside *= vert * step(S3.x, Pos.z);
float FW = Vf.w;
float frameM = inside * ((dxm < FW || dym < FW) ? 1.0 : 0.0);
float barM = inside * ((abs(lp.x - CW * 0.5) < 2.5 || abs(lp.y - (y0 + WH * 0.64)) < 2.5) ? 1.0 : 0.0);
frameM = max(frameM, barM);
float glassM = inside * (1.0 - frameM);
float h1 = frac(sin(dot(id + float2(Seed, Seed * 1.7), float2(127.1, 311.7))) * 43758.5453);
float h2 = frac(sin(dot(id + float2(Seed * 2.3, 5.1), float2(269.5, 183.3))) * 24634.6345);
float litCell = (h1 < Lit) ? 1.0 : 0.0;
// office style: whole floors lit (LitRows = fraction of floors)
float hrow = frac(sin(id.y * 12.9898 + Seed * 7.13) * 43758.5453);
litCell = max(litCell, (hrow < S5.z && h1 < 0.8) ? 1.0 : 0.0);
float gy = saturate((lp.y - y0) / max(WH, 1.0));
float3 litC = Vl.rgb * (0.55 + 0.9 * h2);
"""

HLSL_FACADE_BASE = HLSL_FACADE_COMMON + """
float2 uvw = (abs(n.z) > 0.7) ? Pos.xy : float2(u, -Pos.z);
float2 uvt = uvw * Vw.w;
float2 dxu = ddx(uvt);
float2 dyu = ddy(uvt);
float3 texC = DTex.SampleGrad(DTexSampler, uvt, dxu, dyu).rgb;
float lumW = dot(texC, float3(0.30, 0.59, 0.11));
texC = lerp(texC, float3(lumW, lumW, lumW), S5.x);             // Desat: tames orange / red patches of the scan
float3 wall = texC * Vw.rgb;
float rough = RTex.SampleGrad(RTexSampler, uvt, dxu, dyu).r;
// large soft variation so that big walls do not look tiled
float blot = sin(u * 0.0031 + Seed) * sin(Pos.z * 0.0023 + u * 0.0011) * 0.5 + 0.5;
wall *= 0.86 + 0.28 * blot;
// dirt: dark foot of the building and streaks below sills
float dirt = S3.z * saturate(1.0 - (Pos.z - S3.w) / max(S4.x, 1.0));
float dyb = y0 - lp.y;
float inCol = (lp.x > x0 - 6.0 && lp.x < x1 + 6.0) ? 1.0 : 0.0;
float streak = vert * inCol * ((dyb > 9.0) ? 1.0 : 0.0) * saturate(1.0 - (dyb - 9.0) / 170.0);
wall *= 1.0 - 0.55 * dirt - 0.20 * streak * (0.4 + 0.6 * h2) * (0.4 + S3.z);
// sill (light), lintel (slightly dark), shadow under the sill
float sillM = vert * inCol * ((dyb > 0.0 && dyb < 9.0) ? 1.0 : 0.0);
float lintM = vert * inCol * ((lp.y - y1 > 0.0 && lp.y - y1 < 12.0) ? 1.0 : 0.0);
float3 col = wall;
col = lerp(col, wall * S5.y + 0.02, sillM);
col = lerp(col, wall * 0.75, lintM);
// glass: a darker bottom/lighter top reflection gradient, some windows have curtains
float3 glassC = Vg.rgb * (0.55 + 0.9 * gy) * (0.75 + 0.5 * h2);
glassC *= 0.62 + 0.38 * saturate((y1 - lp.y) / 38.0);
glassC *= 1.0 - S5.w * (1.0 - saturate((min(dxm, dym) - FW) / 14.0));      // reveal: shadow just inside the frame
float curtain = (h2 > 0.80 && litCell < 0.5) ? 1.0 : 0.0;
glassC = lerp(glassC, float3(0.34, 0.29, 0.22) * (0.4 + h2), curtain * 0.85);
glassC = lerp(glassC, litC * 0.25, litCell);
col = lerp(col, glassC, glassM);
col = lerp(col, Vf.rgb, frameM);
float r = lerp(rough, 0.55, frameM);
r = lerp(r, (curtain > 0.5) ? 0.8 : 0.22, glassM);
return float4(col, r);
"""

HLSL_FACADE_EMIS = HLSL_FACADE_COMMON + """
float3 e = litC * Vl.w * litCell * glassM;
return e;
"""

HLSL_FACADE_NORMAL = HLSL_FACADE_COMMON + """
float2 uvw = (abs(n.z) > 0.7) ? Pos.xy : float2(u, -Pos.z);
float2 uvt = uvw * Vw.w;
float2 t = NTex.SampleGrad(NTexSampler, uvt, ddx(uvt), ddy(uvt)).xy * 2.0 - 1.0;
float top = (abs(n.z) > 0.7) ? 1.0 : 0.0;
float3 tu = lerp(float3(t2, 0.0), float3(1.0, 0.0, 0.0), top);
float3 tv = lerp(float3(0.0, 0.0, -1.0), float3(0.0, -1.0, 0.0), top);
float3 pert = tu * t.x + tv * t.y;
float k = S3.y * (1.0 - saturate(inside + 0.0));
return normalize(n + pert * k);
"""


_master_built = False


def build_facade_master(force=False):
    """/Game/Materials/M_IAFacade: wall texture (world aligned) + procedural window grid. Returns the material."""
    global _master_built
    force = force or (os.environ.get("IA_FACADE_FORCE") == "1" and not _master_built)
    if eal.does_asset_exist(FACADE_PATH):
        if not force:
            return eal.load_asset(FACADE_PATH)
        eal.delete_asset(FACADE_PATH)
    _master_built = True
    base = matlib.import_set("ConcreteDirty")
    mat = _new_asset(FACADE_PATH, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("tangent_space_normal", False)
    mat.set_editor_property("used_with_instanced_static_meshes", True)
    mat.set_editor_property("used_with_nanite", True)
    lib.delete_all_material_expressions(mat)
    G = "Facade"
    p_diff = _texobj(mat, "DiffuseTex", base["D"], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -1400, -300)
    p_norm = _texobj(mat, "NormalTex", base["N"], unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -1400, -150)
    p_rough = _texobj(mat, "RoughnessTex", base["R"], unreal.MaterialSamplerType.SAMPLERTYPE_ALPHA, -1400, 0)

    def sc(name, v, y):
        return _scalar(mat, name, v, -1400, y, G)

    def vec(name, rgb, y):
        return _vector(mat, name, rgb, -1100, y, G)

    cw, ch, ww, wh = sc("CellW", 300, 400), sc("CellH", 330, 450), sc("WinW", 170, 500), sc("WinH", 190, 550)
    sill, lit, seed, gridz = sc("Sill", 100, 600), sc("LitFraction", 0.0, 650), sc("Seed", 1.0, 700), sc("GridZ", 0.0, 750)
    minz, nstr, dirt, groundz = sc("WinMinZ", -100000.0, 800), sc("NormalStrength", 0.8, 850), sc("DirtAmount", 0.4, 900), sc("GroundZ", 0.0, 950)
    dirth, glow, fw, gr = sc("DirtHeight", 900.0, 1000), sc("LitGlow", 1.8, 1050), sc("FrameWidth", 7.0, 1100), sc("GlassRough", 0.2, 1150)
    wtile = sc("WallTilingPerCm", 0.01, 1200)
    desat, sillb, litrows, reveal = sc("Desat", 0.0, 1250), sc("SillBoost", 1.35, 1280), sc("LitRows", 0.0, 1310), sc("Reveal", 0.45, 1340)
    v_wall = vec("WallTint", (1, 1, 1), 1300)
    v_glass = vec("GlassColor", (0.03, 0.04, 0.06), 1350)
    v_frame = vec("FrameColor", (0.05, 0.05, 0.05), 1400)
    v_lit = vec("LitColor", (1.0, 0.7, 0.4), 1450)

    S1 = _append(mat, _append(mat, _append(mat, cw, ch, -900, 400), ww, -800, 430), wh, -700, 460)
    S2 = _append(mat, _append(mat, _append(mat, sill, lit, -900, 500), seed, -800, 530), gridz, -700, 560)
    S3 = _append(mat, _append(mat, _append(mat, minz, nstr, -900, 600), dirt, -800, 630), groundz, -700, 660)
    S4 = _append(mat, _append(mat, _append(mat, dirth, glow, -900, 700), fw, -800, 730), gr, -700, 760)
    S5 = _append(mat, _append(mat, _append(mat, desat, sillb, -900, 800), litrows, -800, 830), reveal, -700, 860)
    Vw = _append(mat, v_wall, wtile, -700, 800)
    Vg = _append(mat, v_glass, gr, -700, 860)
    Vf = _append(mat, v_frame, fw, -700, 920)
    Vl = _append(mat, v_lit, glow, -700, 980)
    pos = _node(mat, unreal.MaterialExpressionWorldPosition, -1400, 1500)
    nrm = _node(mat, unreal.MaterialExpressionVertexNormalWS, -1400, 1580)

    common = [("Pos", pos), ("Nrm", nrm), ("S1", S1), ("S2", S2), ("S3", S3), ("S4", S4), ("S5", S5),
              ("Vw", Vw), ("Vg", Vg), ("Vf", Vf), ("Vl", Vl)]
    base_node = _custom(mat, "FacadeBase", HLSL_FACADE_BASE, [("DTex", p_diff), ("RTex", p_rough)] + common,
                        unreal.CustomMaterialOutputType.CMOT_FLOAT4, -300, 0)
    emis_node = _custom(mat, "FacadeEmissive", HLSL_FACADE_EMIS, common,
                        unreal.CustomMaterialOutputType.CMOT_FLOAT3, -300, 300)
    norm_node = _custom(mat, "FacadeNormal", HLSL_FACADE_NORMAL, [("NTex", p_norm)] + common,
                        unreal.CustomMaterialOutputType.CMOT_FLOAT3, -300, 600)
    rgb = _node(mat, unreal.MaterialExpressionComponentMask, -100, 0, r=True, g=True, b=True, a=False)
    _link(base_node, rgb, "")
    ra = _node(mat, unreal.MaterialExpressionComponentMask, -100, 150, r=False, g=False, b=False, a=True)
    _link(base_node, ra, "")
    lib.connect_material_property(rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(ra, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(emis_node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.connect_material_property(norm_node, "", unreal.MaterialProperty.MP_NORMAL)
    lib.recompile_material(mat)
    eal.save_asset(FACADE_PATH)
    unreal.log("KC facade master built")
    return mat


_fcache = {}


def facade(tag, wall="BrickRed", albedo=None, tiling=None, grid_z=0.0, ground_z=0.0, cell=(300.0, 330.0),
           win=(170.0, 190.0), sill=100.0, lit=0.0, glow=1.8, lit_rgb=(1.0, 0.70, 0.40), glass_rgb=(0.030, 0.040, 0.060),
           frame_rgb=(0.045, 0.045, 0.05), frame_w=7.0, min_z=-100000.0, dirt=0.45, dirt_h=900.0, seed=1.0, nstr=0.8,
           glass_rough=0.2, tint=None, desat=0.0, sill_boost=1.35, lit_rows=0.0, reveal=0.45):
    """An instance of M_IAFacade named MI_F_<tag>. Wall texture from matlib.SURFACES[wall] (aimed at `albedo`)."""
    asset = "MI_F_" + tag
    if asset in _fcache:
        return _fcache[asset]
    master = build_facade_master()
    spec = dict(matlib.SURFACES[wall])
    spec["desat"] = max(spec["desat"], desat)
    use_albedo = albedo if albedo is not None else spec["albedo"]
    wt = matlib._tint_for(spec, use_albedo)
    if tint is not None:
        wt = tuple(wt[i] * tint[i] for i in range(3))
    sets = matlib.import_set(spec["tex"])
    meta = matlib.ft.load_meta(spec["tex"]) or matlib.ft.fetch(spec["tex"])
    tile_m = tiling if tiling is not None else (spec["tiling"] or meta["tile_size_m"])
    path = "/Game/Materials/" + asset
    mic = eal.load_asset(path) if eal.does_asset_exist(path) else _new_asset(
        path, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    lib.set_material_instance_parent(mic, master)
    lib.set_material_instance_texture_parameter_value(mic, "DiffuseTex", sets["D"])
    lib.set_material_instance_texture_parameter_value(mic, "NormalTex", sets["N"])
    lib.set_material_instance_texture_parameter_value(mic, "RoughnessTex", sets["R"])
    scal = dict(CellW=cell[0], CellH=cell[1], WinW=win[0], WinH=win[1], Sill=sill, LitFraction=lit, Seed=seed,
                GridZ=grid_z, WinMinZ=min_z, NormalStrength=nstr, DirtAmount=dirt, GroundZ=ground_z, DirtHeight=dirt_h,
                LitGlow=glow, FrameWidth=frame_w, GlassRough=glass_rough, WallTilingPerCm=0.01 / tile_m,
                Desat=spec["desat"], SillBoost=sill_boost, LitRows=lit_rows, Reveal=reveal)
    for k, v in scal.items():
        lib.set_material_instance_scalar_parameter_value(mic, k, float(v))
    for k, c in (("WallTint", wt), ("GlassColor", glass_rgb), ("FrameColor", frame_rgb), ("LitColor", lit_rgb)):
        lib.set_material_instance_vector_parameter_value(mic, k, unreal.LinearColor(c[0], c[1], c[2], 1.0))
    lib.update_material_instance(mic)
    eal.save_asset(path)
    _fcache[asset] = mic
    return mic


EMIT_PATH = "/Game/Materials/M_IAEmit"


def build_emit_master(force=False):
    """/Game/Materials/M_IAEmit: a plain lit surface with an emissive colour (parameters Color, Intensity, Roughness)."""
    if eal.does_asset_exist(EMIT_PATH):
        if not force:
            return eal.load_asset(EMIT_PATH)
        eal.delete_asset(EMIT_PATH)
    mat = _new_asset(EMIT_PATH, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("used_with_instanced_static_meshes", True)
    lib.delete_all_material_expressions(mat)
    col = _vector(mat, "Color", (1.0, 0.7, 0.4), -600, 0)
    inten = _scalar(mat, "Intensity", 0.4, -600, 120)
    rough = _scalar(mat, "Roughness", 0.5, -600, 200)
    mul = _node(mat, unreal.MaterialExpressionMultiply, -300, 0)
    _link(col, mul, "A")
    _link(inten, mul, "B")
    base = _node(mat, unreal.MaterialExpressionMultiply, -300, 150)
    _link(col, base, "A")
    k = _node(mat, unreal.MaterialExpressionConstant, -450, 220, r=0.05)
    _link(k, base, "B")
    lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.recompile_material(mat)
    eal.save_asset(EMIT_PATH)
    return mat


_ecache = {}


def emit(name, rgb, intensity):
    """An emissive instance (window pane, neon tube, bulb): emissive = rgb * intensity (about 0.3 for a lit window,
    1.0-2.0 for a thin neon tube). MI_E_<name>."""
    if name in _ecache:
        return _ecache[name]
    master = build_emit_master()
    path = "/Game/Materials/MI_E_" + name
    mic = eal.load_asset(path) if eal.does_asset_exist(path) else _new_asset(
        path, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    lib.set_material_instance_parent(mic, master)
    lib.set_material_instance_vector_parameter_value(mic, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    lib.set_material_instance_scalar_parameter_value(mic, "Intensity", float(intensity))
    lib.update_material_instance(mic)
    eal.save_asset(path)
    _ecache[name] = mic
    return mic


# --------------------------------------------------------------------------------------------------- shapes
def rbox(b, label, cx, cy, cz, sx, sy, sz, yaw=0.0, pitch=0.0, roll=0.0, mat=None, solid=True, mesh=None):
    """Like b.box but with roll too (mesh defaults to the cube; size is the full size before rotation)."""
    mesh = mesh or b.cube
    actor = b.actor_lib.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(cx, cy, cz),
                                               unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw))
    actor.set_actor_label(label)
    comp = actor.static_mesh_component
    comp.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    if mat is not None:
        comp.set_material(0, mat)
    if not solid:
        comp.set_collision_profile_name("NoCollision")
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    b.box_count += 1
    return actor


def cyl(b, label, p0, p1, d, mat=None, solid=True):
    """A cylinder from point p0 to point p1 (any direction), diameter d."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    cx, cy, cz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2
    if abs(dx) < 1e-3 and abs(dy) < 1e-3:
        return rbox(b, label, cx, cy, cz, d, d, length, mat=mat, solid=solid, mesh=b.cylinder)
    # tilt the cylinder's Z axis onto the direction: yaw to face the direction, then pitch 90-elevation
    yaw = math.degrees(math.atan2(dy, dx))
    elev = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return rbox(b, label, cx, cy, cz, d, d, length, yaw=yaw, pitch=elev - 90.0, mat=mat, solid=solid, mesh=b.cylinder)


def bar(b, label, p0, p1, thick, mat=None, solid=False, depth=None):
    """A square bar from p0 to p1 lying in a vertical plane (or any direction: yaw+pitch). Used for neon tubes, rails."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    cx, cy, cz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return rbox(b, label, cx, cy, cz, length, depth or thick, thick, yaw=yaw, pitch=pitch, mat=mat, solid=solid)


# --------------------------------------------------------------------------------------------------- neon letters
# Strokes on a 2 x 4 grid (x 0..2, y 0..4 up). Each letter is a list of polylines.
_FONT = {
    "A": [[(0, 0), (0, 3), (1, 4), (2, 3), (2, 0)], [(0, 2), (2, 2)]],
    "B": [[(0, 0), (0, 4), (1.6, 4), (2, 3.2), (1.6, 2), (0, 2)], [(1.6, 2), (2, 1), (1.6, 0), (0, 0)]],
    "C": [[(2, 3.2), (1.4, 4), (0.6, 4), (0, 3.2), (0, 0.8), (0.6, 0), (1.4, 0), (2, 0.8)]],
    "D": [[(0, 0), (0, 4), (1.2, 4), (2, 3), (2, 1), (1.2, 0), (0, 0)]],
    "E": [[(2, 4), (0, 4), (0, 0), (2, 0)], [(0, 2), (1.5, 2)]],
    "F": [[(2, 4), (0, 4), (0, 0)], [(0, 2), (1.5, 2)]],
    "G": [[(2, 3.2), (1.4, 4), (0.6, 4), (0, 3.2), (0, 0.8), (0.6, 0), (1.6, 0), (2, 0.8), (2, 2), (1, 2)]],
    "H": [[(0, 0), (0, 4)], [(2, 0), (2, 4)], [(0, 2), (2, 2)]],
    "I": [[(1, 0), (1, 4)]],
    "J": [[(2, 4), (2, 0.8), (1.4, 0), (0.6, 0), (0, 0.8)]],
    "K": [[(0, 0), (0, 4)], [(2, 4), (0, 1.8)], [(0.6, 2.4), (2, 0)]],
    "L": [[(0, 4), (0, 0), (2, 0)]],
    "M": [[(0, 0), (0, 4), (1, 2.4), (2, 4), (2, 0)]],
    "N": [[(0, 0), (0, 4), (2, 0), (2, 4)]],
    "O": [[(0.6, 0), (0, 0.8), (0, 3.2), (0.6, 4), (1.4, 4), (2, 3.2), (2, 0.8), (1.4, 0), (0.6, 0)]],
    "P": [[(0, 0), (0, 4), (1.6, 4), (2, 3.2), (1.6, 2), (0, 2)]],
    "Q": [[(0.6, 0), (0, 0.8), (0, 3.2), (0.6, 4), (1.4, 4), (2, 3.2), (2, 0.8), (1.4, 0), (0.6, 0)], [(1.2, 1), (2, -0.2)]],
    "R": [[(0, 0), (0, 4), (1.6, 4), (2, 3.2), (1.6, 2), (0, 2)], [(1, 2), (2, 0)]],
    "S": [[(2, 3.4), (1.4, 4), (0.6, 4), (0, 3.2), (0.6, 2.1), (1.4, 1.9), (2, 0.8), (1.4, 0), (0.6, 0), (0, 0.6)]],
    "T": [[(0, 4), (2, 4)], [(1, 4), (1, 0)]],
    "U": [[(0, 4), (0, 0.8), (0.6, 0), (1.4, 0), (2, 0.8), (2, 4)]],
    "V": [[(0, 4), (1, 0), (2, 4)]],
    "W": [[(0, 4), (0.5, 0), (1, 2), (1.5, 0), (2, 4)]],
    "X": [[(0, 4), (2, 0)], [(2, 4), (0, 0)]],
    "Y": [[(0, 4), (1, 2), (2, 4)], [(1, 2), (1, 0)]],
    "Z": [[(0, 4), (2, 4), (0, 0), (2, 0)]],
    "0": [[(0.6, 0), (0, 0.8), (0, 3.2), (0.6, 4), (1.4, 4), (2, 3.2), (2, 0.8), (1.4, 0), (0.6, 0)], [(0.3, 0.6), (1.7, 3.4)]],
    "1": [[(0.4, 3), (1.2, 4), (1.2, 0)]],
    "2": [[(0, 3.2), (0.6, 4), (1.4, 4), (2, 3.2), (2, 2.6), (0, 0), (2, 0)]],
    "3": [[(0, 3.6), (0.6, 4), (1.4, 4), (2, 3.4), (1.4, 2.1), (2, 1.0), (1.4, 0), (0.6, 0), (0, 0.4)], [(0.8, 2.1), (1.4, 2.1)]],
    "4": [[(1.6, 0), (1.6, 4), (0, 1.2), (2, 1.2)]],
    "5": [[(2, 4), (0.2, 4), (0, 2.2), (1.2, 2.5), (2, 1.8), (2, 0.8), (1.4, 0), (0.6, 0), (0, 0.6)]],
    "&": [[(2, 0), (0.2, 2.6), (0.4, 3.6), (1, 4), (1.6, 3.6), (1.6, 3), (0, 1), (0.4, 0.2), (1.2, 0), (2, 1.2)]],
    "-": [[(0.3, 2), (1.7, 2)]],
    "!": [[(1, 4), (1, 1.2)], [(1, 0.2), (1, 0)]],
    "'": [[(1, 4), (1, 3)]],
    " ": [],
}


def neon_text(b, label, text, x, y, z, width_dir, height, mat, thick=3.5, yaw=0.0, spacing=0.55, rgb=None,
              out_dir=None, solid=False):
    """Letters made of glowing tubes standing on a wall. (x, y, z) = centre of the text; the text runs along `yaw`
    (0 = along +x, so the wall faces -y/+y; 90 = along +y, wall faces +-x). Letter height `height` cm.
    Returns the total width. Tubes are `thick` cm and stand out of the wall by `thick`."""
    k = height / 4.0
    adv = (2.0 + spacing * 2.0) * k
    n = len(text)
    total = adv * n - spacing * 2.0 * k
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for i, ch in enumerate(text.upper()):
        strokes = _FONT.get(ch, [])
        ox = -total / 2 + i * adv
        for si, poly in enumerate(strokes):
            for j in range(len(poly) - 1):
                (ax, ay), (bx, by) = poly[j], poly[j + 1]
                pa = (x + c * (ox + ax * k), y + s * (ox + ax * k), z - height / 2 + ay * k)
                pb = (x + c * (ox + bx * k), y + s * (ox + bx * k), z - height / 2 + by * k)
                bar(b, "%s_%s%d_%d" % (label, ch, si, j), pa, pb, thick, mat=mat, solid=solid)
    return total
