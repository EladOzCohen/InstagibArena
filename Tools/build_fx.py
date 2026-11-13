"""Builds the effect materials of the game (jump pad, flames, embers). Run once in the editor commandlet:

    powershell -File Tools\\run_ue.ps1 -Script Tools\\build_fx.py -Grep "FX_"

Creates (all texture free, everything is drawn from math in the shader):
  /Game/Materials/FX/M_IAPad         lit steel launch plate: raised-rim steel (Rim=1) or painted deck with chevrons (Rim=0)
                                     params PadColor, Glow, Flash, Phase, Rim
  /Game/Materials/FX/M_IAPadColumn   additive open cylinder of rising light streaks. params PadColor, Strength, Flash, Phase, Height
  /Game/Materials/FX/M_IAFlame       additive, unlit flame on a vertical quad. params EdgeColor, CoreColor, Glow, Seed
  /Game/Materials/FX/M_IAEmbers      additive, unlit drifting sparks on a vertical quad. params EmberColor, Seed, Scale
Set IA_FX_FORCE=1 to rebuild materials that exist (after changing the HLSL here).
Code that uses them: Source/InstagibArena/IAJumpPad.cpp, IAFlame.cpp (paths are loaded at BeginPlay; the folder is always cooked).
"""

import os
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

from matlib import _node, _link, _scalar, _vector, _append, _custom, _new_asset  # noqa: E402

lib = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
FX_DIR = "/Game/Materials/FX"
FORCE = os.environ.get("IA_FX_FORCE", "") == "1"


def hash1(expr):
    return "frac(sin(%s) * 43758.5453)" % expr


def vnoise(name, coord):
    """HLSL statements that define float `name` = smooth value noise (0..1) at the float2 expression `coord`."""
    n = name
    return """
float2 {n}_c = {coord};
float2 {n}_i = floor({n}_c);
float2 {n}_f = frac({n}_c);
{n}_f = {n}_f * {n}_f * (3.0 - 2.0 * {n}_f);
float {n}_a = frac(sin(dot({n}_i, float2(127.1, 311.7))) * 43758.5453);
float {n}_b = frac(sin(dot({n}_i + float2(1.0, 0.0), float2(127.1, 311.7))) * 43758.5453);
float {n}_d = frac(sin(dot({n}_i + float2(0.0, 1.0), float2(127.1, 311.7))) * 43758.5453);
float {n}_e = frac(sin(dot({n}_i + float2(1.0, 1.0), float2(127.1, 311.7))) * 43758.5453);
float {n} = lerp(lerp({n}_a, {n}_b, {n}_f.x), lerp({n}_d, {n}_e, {n}_f.x), {n}_f.y);
""".format(n=n, coord=coord)


def fresh(path):
    """Returns a new empty material at path (or None when it exists and FORCE is off)."""
    if eal.does_asset_exist(path):
        if not FORCE:
            return None
        eal.delete_asset(path)
    mat = _new_asset(path, unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    return mat


# ---------------------------------------------------------------------------------------------------- jump pad plate

HLSL_PAD_COMMON = """
// UV 0..1 over the deck; p runs -1..1, +x = launch direction. A = (Glow, Flash, Phase, Rim). P = PadColor.
float glowK = A.x;
float flash = A.y;
float ph = A.z;
float rimMode = A.w;
float2 p = (UV - 0.5) * 2.0;
float ax = abs(p.x);
float ay = abs(p.y);
float edge = max(ax, ay);
float brush = frac(sin(floor(UV.y * 240.0) * 12.9898 + 4.1) * 43758.5453);
""" + vnoise("mott", "UV * 5.0 + 3.7") + vnoise("mott2", "UV * 23.0 + 1.3") + """
float wear = mott * 0.65 + mott2 * 0.35;
// chevrons: lines of constant s0 = x + 0.85 |y| are '>' shapes pointing along +x
float2 q = p / 0.80;
float s0 = q.x + 0.85 * abs(q.y);
float sc = s0 * 1.25 - 0.18;
float band = frac(sc);
float aa = max(fwidth(sc), 0.002) * 1.5;
float chev = smoothstep(0.0, aa, band) * (1.0 - smoothstep(0.50, 0.50 + aa, band));
float bx = max(abs(q.x) / 0.97, abs(q.y) / 0.85);
chev *= 1.0 - smoothstep(0.985, 1.0, bx);
chev *= 1.0 - rimMode;
// light ln close to the border, and bolts in the corners
float ln = smoothstep(0.885, 0.895, edge) * (1.0 - smoothstep(0.925, 0.935, edge));
float2 bc = abs(p) - 0.835;
float bolt = 1.0 - smoothstep(0.035, 0.05, length(bc));
ln *= 1.0 - rimMode;
bolt *= 1.0 - rimMode;
"""

HLSL_PAD_BASE = HLSL_PAD_COMMON + """
float3 steel = lerp(float3(0.036, 0.039, 0.044), float3(0.085, 0.09, 0.098), wear * 0.55 + brush * 0.25);
// border plate slightly lighter and worn at the very edge
steel *= lerp(1.0, 1.35, smoothstep(0.935, 0.96, edge) * (1.0 - rimMode));
float3 paint = P * (0.40 + 0.18 * wear);
float3 col = lerp(steel, paint, chev);
col = lerp(col, float3(0.14, 0.145, 0.155), bolt);
col = lerp(col, steel * 0.5 + P * 0.05, ln);
float3 rimCol = float3(0.05, 0.054, 0.06) * (0.75 + 0.7 * wear) + brush * 0.008;
col = lerp(col, rimCol, rimMode);
float rough = lerp(0.40, 0.62, wear) * (1.0 - 0.15 * chev) ;
rough = lerp(rough, 0.5, rimMode);
return float4(col, saturate(rough));
"""

HLSL_PAD_EMIS = HLSL_PAD_COMMON + """
// a brighter wave travels along the arrows (launch direction), plus a slow overall breath
float wave = 0.5 + 0.5 * sin(T * 4.5 - s0 * 3.4);
wave = wave * wave;
float breath = 0.80 + 0.20 * sin(T * 2.1 + ph);
float3 e = P * glowK * (chev * (0.22 + 0.78 * wave) * breath + 0.30 * ln * breath);
e += P * flash * (0.9 * chev + 0.6 * ln) * 3.0;
return e;
"""


def build_pad():
    path = FX_DIR + "/M_IAPad"
    mat = fresh(path)
    if mat is None:
        return
    pc = _vector(mat, "PadColor", (0.0, 0.8, 1.0), -900, 0)
    glow = _scalar(mat, "Glow", 2.0, -900, 100)
    flash = _scalar(mat, "Flash", 0.0, -900, 160)
    phase = _scalar(mat, "Phase", 0.0, -900, 220)
    rim = _scalar(mat, "Rim", 0.0, -900, 280)
    time = _node(mat, unreal.MaterialExpressionTime, -900, 340)
    uv = _node(mat, unreal.MaterialExpressionTextureCoordinate, -900, 400)
    A = _append(mat, _append(mat, _append(mat, glow, flash, -700, 100), phase, -600, 130), rim, -500, 160)
    base = _custom(mat, "PadBase", HLSL_PAD_BASE, [("UV", uv), ("T", time), ("P", pc), ("A", A)],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT4, -250, 0)
    emis = _custom(mat, "PadEmissive", HLSL_PAD_EMIS, [("UV", uv), ("T", time), ("P", pc), ("A", A)],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -250, 300)
    rgb = _node(mat, unreal.MaterialExpressionComponentMask, -80, 0, r=True, g=True, b=True, a=False)
    _link(base, rgb, "")
    ra = _node(mat, unreal.MaterialExpressionComponentMask, -80, 150, r=False, g=False, b=False, a=True)
    _link(base, ra, "")
    metal = _node(mat, unreal.MaterialExpressionConstant, -80, 250, r=0.55)
    lib.connect_material_property(rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(ra, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("FX_BUILT M_IAPad")


# ---------------------------------------------------------------------------------------------------- jump pad column

HLSL_COLUMN = """
// Pos = pixel world position, Org = actor position, Nrm = vertex normal, T = time, D = pixel depth, P = PadColor,
// A = (Strength, Flash, Phase, Height in cm). Thin streaks rise along the inside of a 150 cm wide open cylinder.
float3 rel = Pos - Org;
float H = A.w;
float h = saturate((rel.z - 8.0) / H);
float ang = atan2(rel.y, rel.x) * 0.159155 + 0.5;
float ax = ang * 22.0;
float id = floor(ax);
float fx = frac(ax) - 0.5;
float r1 = frac(sin(id * 12.9898 + 1.7) * 43758.5453);
float r2 = frac(sin(id * 78.233 + 9.1) * 43758.5453);
float wd = 0.10 + 0.16 * r1;
float prof = saturate(1.0 - abs(fx) / wd);
prof = prof * prof;
float spd = 0.30 + 0.50 * r2;
float v = frac(h * 0.85 - T * spd + r1 * 7.0);
float streak = pow(v, 5.0) * (1.0 - smoothstep(0.93, 1.0, v));
float rise = pow(1.0 - h, 1.4) * smoothstep(0.0, 0.06, h);
float pulse = 0.70 + 0.30 * sin(T * 1.6 + A.z);
float veil = 0.045 * pow(1.0 - h, 2.5) * smoothstep(0.0, 0.03, h);
float nearF = saturate((D - 90.0) / 170.0);
float noCap = 1.0 - step(0.5, abs(Nrm.z));
float flash = A.y;
float I = (streak * prof * (0.45 + r1) * pulse * rise * 1.25 + veil) * (A.x + flash * 3.0) * nearF * noCap;
return P * I;
"""


def build_column():
    path = FX_DIR + "/M_IAPadColumn"
    mat = fresh(path)
    if mat is None:
        return
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    pc = _vector(mat, "PadColor", (0.0, 0.8, 1.0), -900, 0)
    strength = _scalar(mat, "Strength", 1.0, -900, 100)
    flash = _scalar(mat, "Flash", 0.0, -900, 160)
    phase = _scalar(mat, "Phase", 0.0, -900, 220)
    height = _scalar(mat, "Height", 260.0, -900, 280)
    time = _node(mat, unreal.MaterialExpressionTime, -900, 340)
    pos = _node(mat, unreal.MaterialExpressionWorldPosition, -900, 400)
    org = _node(mat, unreal.MaterialExpressionActorPositionWS, -900, 460)
    nrm = _node(mat, unreal.MaterialExpressionVertexNormalWS, -900, 520)
    depth = _node(mat, unreal.MaterialExpressionPixelDepth, -900, 580)
    A = _append(mat, _append(mat, _append(mat, strength, flash, -700, 100), phase, -600, 130), height, -500, 160)
    emis = _custom(mat, "PadColumn", HLSL_COLUMN, [("Pos", pos), ("Org", org), ("Nrm", nrm), ("T", time), ("D", depth),
                                                    ("P", pc), ("A", A)],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -250, 0)
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("FX_BUILT M_IAPadColumn")


# ---------------------------------------------------------------------------------------------------- flame

HLSL_FLAME = """
// UV over a vertical quad (56 x 78 cm at scale 1). x -1..1 across, h 0 (bottom) .. 1 (top).
// Edge/Core = colours, A = (Glow, Seed, 0, 0)
float x = (UV.x - 0.5) * 2.0;
float h = 1.0 - UV.y;
float seed = A.y;
""" + vnoise("n1", "float2(x * 1.4 + seed, h * 1.9 - T * 1.45 + seed * 0.37)") \
    + vnoise("n2", "float2(x * 3.0 + seed * 1.7, h * 3.9 - T * 2.6)") \
    + vnoise("n3", "float2(h * 1.2 - T * 0.9 + seed, seed + 4.0)") + """
float n = n1 * 0.58 + n2 * 0.42;
float tip = saturate(1.0 - h);
float sway = ((n1 - 0.5) * 0.55 + (n3 - 0.5) * 0.5) * h;
float width = 0.78 * pow(tip, 0.62) * (0.88 + 0.12 * sin(T * 5.3 + seed));
float body = saturate(1.0 - abs(x - sway) / max(width, 0.02));
float flame = saturate(body * 1.9 - (1.0 - n) * (0.04 + 0.75 * h) * 0.8);
flame = smoothstep(0.0, 0.50, flame);
float heat = saturate(flame * (1.0 - 0.75 * h) + (body - 0.5) * 0.3 * (1.0 - h));
float3 col = lerp(Edge, Core, saturate(heat * 1.1 - 0.45));
col = lerp(col, Edge * float3(1.0, 0.45, 0.30), saturate(h * 1.4 - 0.7));
float fade = smoothstep(0.0, 0.07, h) * (1.0 - smoothstep(0.95, 1.0, h)) * (1.0 - smoothstep(0.88, 1.0, abs(x)));
float flick = 0.88 + 0.12 * sin(T * 11.0 + seed * 3.0);
return col * flame * (0.45 + 0.45 * heat) * A.x * fade * flick;
"""


def build_flame():
    path = FX_DIR + "/M_IAFlame"
    mat = fresh(path)
    if mat is None:
        return
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    edge = _vector(mat, "EdgeColor", (1.0, 0.30, 0.05), -900, 0)
    core = _vector(mat, "CoreColor", (1.0, 0.80, 0.40), -900, 60)
    glow = _scalar(mat, "Glow", 1.6, -900, 120)
    seed = _scalar(mat, "Seed", 0.0, -900, 180)
    time = _node(mat, unreal.MaterialExpressionTime, -900, 240)
    uv = _node(mat, unreal.MaterialExpressionTextureCoordinate, -900, 300)
    zero = _node(mat, unreal.MaterialExpressionConstant, -800, 360, r=0.0)
    A = _append(mat, _append(mat, _append(mat, glow, seed, -700, 120), zero, -600, 150), zero, -500, 180)
    emis = _custom(mat, "FlameEmissive", HLSL_FLAME, [("UV", uv), ("T", time), ("Edge", edge), ("Core", core), ("A", A)],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -250, 0)
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("FX_BUILT M_IAFlame")


# ---------------------------------------------------------------------------------------------------- embers

HLSL_EMBERS = """
// UV over a vertical quad of 70 x 190 cm at scale 1. Small sparks rise in 6 lanes and fade out towards the top.
float2 uv = float2(UV.x, 1.0 - UV.y);
float seed = A.y;
float cols = 6.0;
float rows = 9.0;
float lane = floor(uv.x * cols);
float rl = frac(sin((lane + seed) * 12.9898) * 43758.5453);
float sp = 0.55 + 1.0 * rl;
float2 g = float2(uv.x * cols, uv.y * rows - T * sp);
float2 id = floor(g);
float2 f = frac(g);
float r0 = frac(sin(dot(id + seed, float2(127.1, 311.7))) * 43758.5453);
float r1 = frac(sin(dot(id + seed, float2(269.5, 183.3))) * 43758.5453);
float r2 = frac(sin(dot(id + seed, float2(419.2, 371.9))) * 43758.5453);
float present = step(0.6, r0);
float2 cen = float2(0.5 + 0.28 * sin(T * (1.0 + r1) + r2 * 6.28), 0.3 + 0.4 * r1);
float2 dcm = (f - cen) * float2(70.0 / cols, 190.0 / rows) * A.x;
float dist = length(dcm);
float dotm = 1.0 - smoothstep(0.25, 1.1 + 0.8 * r2, dist);
float life = pow(saturate(1.0 - uv.y), 1.3) * smoothstep(0.0, 0.12, uv.y);
float tw = 0.65 + 0.35 * sin(T * 12.0 + r2 * 40.0);
float side = 1.0 - smoothstep(0.7, 1.0, abs(uv.x - 0.5) * 2.0);
return E * dotm * present * life * tw * side * 2.2;
"""


def build_embers():
    path = FX_DIR + "/M_IAEmbers"
    mat = fresh(path)
    if mat is None:
        return
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    col = _vector(mat, "EmberColor", (1.0, 0.55, 0.15), -900, 0)
    seed = _scalar(mat, "Seed", 0.0, -900, 60)
    scale = _scalar(mat, "Scale", 1.0, -900, 120)
    time = _node(mat, unreal.MaterialExpressionTime, -900, 180)
    uv = _node(mat, unreal.MaterialExpressionTextureCoordinate, -900, 240)
    zero = _node(mat, unreal.MaterialExpressionConstant, -800, 300, r=0.0)
    A = _append(mat, _append(mat, _append(mat, scale, seed, -700, 120), zero, -600, 150), zero, -500, 180)
    emis = _custom(mat, "EmberEmissive", HLSL_EMBERS, [("UV", uv), ("T", time), ("E", col), ("A", A)],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -250, 0)
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("FX_BUILT M_IAEmbers")


# ---------------------------------------------------------------------------------------------------- beam / glow shell

HLSL_SHELL = """
// A soft additive shell around a cylinder or sphere: bright where the surface faces the camera, fading to the silhouette.
// Nrm = pixel normal, Cam = camera vector, Axis = object's local Z in world space (cylinder caps are hidden), C = colour,
// A = (Glow, Exponent, HideCaps 0/1, 0)
float3 n = normalize(Nrm);
float f = saturate(abs(dot(n, normalize(Cam))));
float soft = pow(f, A.y);
float cap = A.z * step(0.6, abs(dot(n, normalize(Axis))));
return C * A.x * soft * (1.0 - cap);
"""


def build_shell():
    path = FX_DIR + "/M_IAGlowShell"
    mat = fresh(path)
    if mat is None:
        return
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", False)
    col = _vector(mat, "Color", (0.0, 0.8, 1.0), -900, 0)
    glow = _scalar(mat, "Glow", 3.0, -900, 60)
    expo = _scalar(mat, "Exponent", 1.6, -900, 120)
    caps = _scalar(mat, "HideCaps", 1.0, -900, 180)
    zero = _node(mat, unreal.MaterialExpressionConstant, -800, 240, r=0.0)
    A = _append(mat, _append(mat, _append(mat, glow, expo, -700, 120), caps, -600, 150), zero, -500, 180)
    nrm = _node(mat, unreal.MaterialExpressionPixelNormalWS, -900, 300)
    cam = _node(mat, unreal.MaterialExpressionCameraVectorWS, -900, 360)
    axis = _node(mat, unreal.MaterialExpressionObjectOrientation, -900, 420)
    emis = _custom(mat, "GlowShell", HLSL_SHELL, [("Nrm", nrm), ("Cam", cam), ("Axis", axis), ("C", col), ("A", A)],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -250, 0)
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("FX_BUILT M_IAGlowShell")


def build_all():
    build_pad()
    build_column()
    build_flame()
    build_embers()
    build_shell()
    unreal.log("FX_DONE")


if __name__ == "__main__" or True:
    build_all()
