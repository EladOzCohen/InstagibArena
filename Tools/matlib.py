"""Realistic world surface library: PBR textures + one world-aligned (triplanar) master material.

Import it in a map script AFTER mapkit (mapkit puts Tools on sys.path):

    import mapkit
    from matlib import surface, glass, water, lava
    b = mapkit.MapBuilder("/Game/Maps/DM-Foo")
    wall = surface("BrickRed")                                   # MI_W_BrickRed, created on first use
    floor = surface("ConcreteDirty", tiling=3.0)                 # same surface, other texture size (a variant MIC)
    paint = surface("ConcreteClean", albedo=(120, 40, 40), tag="Foo")   # recoloured variant MI_W_ConcreteClean_Foo
    b.box("Wall", 0, 0, 200, 800, 40, 400, mat=wall)

What it gives you
  * /Game/Materials/M_IAWorld      master material: textures are projected from the WORLD position (triplanar, top and
                                   side blend by the surface normal), so scaled cubes, cylinders, cones and spheres do
                                   not stretch and neighbouring pieces line up. No UVs are used. No emissive.
  * /Game/Materials/MI_W_<Name>    one instance per entry of SURFACES (about 70 surfaces, see the table below)
  * /Game/Materials/M_IAGlassClear, M_IAWater, M_IALava   glass, calm dark water, lava (the only emissive one)
  * /Game/Textures/World/T_<Set>_D/_N/_R   colour / normal / roughness, 1024 px, BC compressed

Parameters of M_IAWorld (all can be overridden per instance):
  DiffuseTex, NormalTex, RoughnessTex      the texture set
  TilingMeters      real-world size in metres that one texture repeat covers (default 2.0)
  Tint              colour multiplier (default white). Use `albedo=` of surface() to aim at a colour instead.
  Desaturate        0..1, mixes the texture towards grey before Tint (use for repainting a texture in any colour)
  RoughnessScale    multiplies the roughness map (default 1.0), RoughnessBias adds to it (default 0.0); negative bias = wet
  NormalStrength    1.0 = as authored
  Metallic          0..1 (default 0)
  MacroStrength     large-scale brightness/colour variation that breaks up the repeating pattern (default 0.3)
  MacroMeters       size of the macro blotches in metres (default 13)
  DirtAmount, DirtHeight (cm), DirtGroundZ (cm)   darkens and roughens the lower part of walls (default 0 = off)
"""

import hashlib
import math
import os
import random
import struct
import sys
import zlib

import unreal

TOOLS_DIR = os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import fetch_textures as ft  # noqa: E402  (downloads / caches the texture sets)

TEX_DIR = "/Game/Textures/World"
MAT_DIR = "/Game/Materials"
MASTER_PATH = MAT_DIR + "/M_IAWorld"
NOISE_NAME = "T_IAMacroNoise"

lib = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary

# Linear mean colour of the colour map of every texture set (measured once). surface(albedo=...) uses it to aim at a colour.
TEX_MEAN = {
    "Asphalt": (0.102, 0.080, 0.061), "AsphaltCracked": (0.249, 0.232, 0.220), "BrickDark": (0.057, 0.032, 0.026),
    "BrickRed": (0.138, 0.072, 0.045), "BrushedMetal": (0.701, 0.753, 0.813), "Canvas": (0.276, 0.196, 0.102),
    "Cobblestone": (0.201, 0.169, 0.111), "ConcreteBlocks": (0.059, 0.046, 0.029), "ConcreteClean": (0.191, 0.154, 0.102),
    "ConcreteDirty": (0.198, 0.165, 0.108), "ConcretePanels": (0.212, 0.193, 0.165), "ConcreteWorn": (0.094, 0.095, 0.090),
    "ContainerPaint": (0.219, 0.423, 0.497), "CorrugatedGalv": (0.101, 0.099, 0.083), "CorrugatedRust": (0.099, 0.019, 0.006),
    "DiamondPlate": (0.046, 0.029, 0.008), "DirtDry": (0.242, 0.202, 0.148), "Gravel": (0.425, 0.403, 0.347),
    "Ice": (0.135, 0.215, 0.178), "Lava": (0.449, 0.062, 0.025), "PlasterGrey": (0.313, 0.290, 0.230),
    "PlasterWeathered": (0.519, 0.463, 0.388), "RedGround": (0.229, 0.103, 0.059), "RockCliff": (0.240, 0.148, 0.082),
    "RockDark": (0.124, 0.060, 0.028), "RockGrey": (0.416, 0.352, 0.281), "RoofBitumen": (0.041, 0.035, 0.032),
    "RoofSlate": (0.294, 0.250, 0.187), "Rope": (0.207, 0.153, 0.078), "RustCoarse": (0.131, 0.040, 0.011),
    "RustOrange": (0.165, 0.043, 0.022), "Sand": (0.399, 0.319, 0.167), "SandstoneBlocks": (0.455, 0.352, 0.246),
    "SandstoneRough": (0.588, 0.396, 0.226), "SlabsGrey": (0.243, 0.222, 0.180), "Snow": (0.397, 0.397, 0.408),
    "StoneRubble": (0.084, 0.070, 0.054), "WoodPainted": (0.064, 0.054, 0.039), "WoodPlanksDark": (0.125, 0.092, 0.062),
    "WoodPlanksOld": (0.060, 0.057, 0.049),
}


def srgb(r, g, b):
    """sRGB 0..255 -> linear 0..1 (what the material wants)."""
    f = lambda c: ((c / 255.0 + 0.055) / 1.055) ** 2.4 if c / 255.0 > 0.04045 else c / 255.0 / 12.92
    return (f(r), f(g), f(b))


# =====================================================================================================
# Surfaces: name -> parameters. albedo = aimed average colour in sRGB 0..255 (the texture's own average is divided out,
# so the texture keeps its pattern and contrast but gets this overall colour); desat=1 ignores the texture's own hue.
# tiling = metres per repeat (None = the real size of the scan). rb/rs = roughness bias/scale, metal = metallic.
# =====================================================================================================

def S(tex, albedo=None, tiling=None, desat=0.0, rs=1.0, rb=0.0, ns=1.0, metal=0.0, macro=0.30, macro_m=13.0,
      dirt=0.0, dirt_h=120.0, tint=(1.0, 1.0, 1.0)):
    return dict(tex=tex, albedo=albedo, tiling=tiling, desat=desat, rs=rs, rb=rb, ns=ns, metal=metal, macro=macro,
                macro_m=macro_m, dirt=dirt, dirt_h=dirt_h, tint=tint)


SURFACES = {
    # ---- concrete ----
    "ConcreteClean":    S("ConcreteClean", (168, 166, 161), ns=0.6),
    "ConcreteDirty":    S("ConcreteDirty", (118, 115, 108), dirt=0.5, ns=0.6),
    "ConcreteWorn":     S("ConcreteWorn", (140, 140, 136)),
    "ConcreteDark":     S("ConcreteWorn", (104, 104, 102)),
    "ConcretePanels":   S("ConcretePanels", (150, 147, 140)),
    "ConcreteBlocks":   S("ConcreteBlocks", (132, 128, 120)),
    "Sidewalk":         S("ConcreteWorn", (156, 154, 148), tiling=2.0),
    # ---- brick and plaster ----
    "BrickRed":         S("BrickRed", (172, 90, 68)),
    "BrickBrown":       S("BrickRed", (118, 80, 64)),
    "BrickDark":        S("BrickDark", (100, 66, 58)),
    "PlasterGrey":      S("PlasterGrey", (178, 176, 168)),
    "PlasterWhite":     S("PlasterGrey", (212, 210, 202)),
    "PlasterWeathered": S("PlasterWeathered", (188, 178, 158)),
    "PlasterSand":      S("PlasterWeathered", (205, 178, 134)),
    "PlasterNight":     S("PlasterGrey", (62, 66, 84)),
    # ---- stone ----
    "SandstoneBlocks":  S("SandstoneBlocks", (192, 160, 118)),
    "SandstoneRough":   S("SandstoneRough", (204, 168, 118)),
    "SandstoneRed":     S("SandstoneBlocks", (180, 108, 72)),
    "Limestone":        S("SandstoneBlocks", (216, 202, 172), desat=0.5),
    "StoneRubble":      S("StoneRubble", (112, 106, 98)),
    "StoneDark":        S("StoneRubble", (66, 64, 62)),
    "StoneSlabs":       S("SlabsGrey", (150, 145, 135)),
    "Cobblestone":      S("Cobblestone", (130, 122, 108)),
    # ---- asphalt and roofs ----
    "Asphalt":          S("Asphalt", (74, 72, 70)),
    "AsphaltWet":       S("Asphalt", (48, 48, 52), rb=-0.35),
    "AsphaltCracked":   S("AsphaltCracked", (88, 87, 85)),
    "RoofTarmac":       S("RoofBitumen", (64, 63, 62), tiling=4.0),
    "RoofSlate":        S("RoofSlate", (84, 86, 90)),
    # ---- metal ----
    "RustOrange":       S("RustOrange", (128, 66, 38)),
    "RustCoarse":       S("RustCoarse", (112, 58, 32)),
    "DiamondPlate":     S("DiamondPlate", (112, 110, 108), metal=0.3, rb=-0.1),
    "DiamondPlateDark": S("DiamondPlate", (72, 72, 74), metal=0.3, rb=-0.1),
    "CorrugatedGalv":   S("CorrugatedGalv", (168, 170, 174), metal=0.5),
    "CorrugatedRust":   S("CorrugatedRust", (132, 70, 42)),
    "CorrugatedDark":   S("CorrugatedGalv", (88, 90, 96), metal=0.5),
    "BrushedMetal":     S("BrushedMetal", (172, 175, 180), metal=0.7),
    "SteelDark":        S("BrushedMetal", (96, 99, 106), metal=0.6, rb=0.05),
    "ForgeIron":        S("BrushedMetal", (84, 76, 72), metal=0.6, rb=0.12),
    "ContainerBlue":    S("ContainerPaint", (36, 82, 140), desat=1.0, metal=0.1),
    "ContainerRed":     S("ContainerPaint", (156, 42, 34), desat=1.0, metal=0.1),
    "ContainerGreen":   S("ContainerPaint", (48, 112, 66), desat=1.0, metal=0.1),
    "ContainerYellow":  S("ContainerPaint", (214, 164, 34), desat=1.0, metal=0.1),
    "ContainerGrey":    S("ContainerPaint", (128, 132, 136), desat=1.0, metal=0.1),
    # ---- wood ----
    "WoodPlanksOld":    S("WoodPlanksOld", (130, 118, 102)),
    "WoodPlanksDark":   S("WoodPlanksDark", (104, 76, 54)),
    "WoodBridge":       S("WoodPlanksDark", (126, 94, 66)),
    "WoodPaintedRed":   S("WoodPainted", (146, 48, 42), desat=1.0),
    "WoodPaintedGrey":  S("WoodPainted", (120, 124, 128), desat=1.0),
    "WoodPaintedWhite": S("WoodPainted", (200, 198, 192), desat=1.0),
    # ---- rock ----
    "RockGrey":         S("RockGrey", (132, 130, 126)),
    "GlacierRock":      S("RockGrey", (112, 118, 126), desat=0.4),
    "RockCliff":        S("RockCliff", (150, 120, 92)),
    "RockCanyonRed":    S("RockCliff", (170, 88, 56), desat=0.3),
    "RockCanyonPale":   S("RockCliff", (200, 150, 110), desat=0.3),
    "BasaltDark":       S("RockDark", (72, 70, 69), desat=1.0),
    # ---- ground ----
    "Sand":             S("Sand", (206, 172, 112)),
    "SandRed":          S("Sand", (200, 118, 72), desat=0.3),
    "DirtDry":          S("DirtDry", (142, 116, 86)),
    "DirtRed":          S("RedGround", (164, 84, 48)),
    "Gravel":           S("Gravel", (134, 128, 120)),
    "Snow":             S("Snow", (226, 231, 240), macro=0.10),
    "SnowBlue":         S("Snow", (150, 168, 200), macro=0.12),
    "Ice":              S("Ice", (140, 176, 196), rb=-0.1, ns=0.5, macro=0.08),
    "IceDeep":          S("Ice", (70, 120, 160), rb=-0.15, ns=0.5, macro=0.08),
    # ---- fabric ----
    "Canvas":           S("Canvas", (176, 156, 108)),
    "CanvasRed":        S("Canvas", (150, 52, 46), desat=1.0),
    "CanvasBlue":       S("Canvas", (52, 82, 130), desat=1.0),
    "Rope":             S("Rope", (178, 150, 104)),
}

# Material parameter defaults of the master (and of any instance that does not set them)
DEFAULTS = dict(TilingMeters=2.0, RoughnessScale=1.0, RoughnessBias=0.0, NormalStrength=1.0, Metallic=0.0,
                MacroStrength=0.30, MacroMeters=13.0, Desaturate=0.0, DirtAmount=0.0, DirtHeight=120.0, DirtGroundZ=0.0)


# =====================================================================================================
# Textures
# =====================================================================================================

def _write_png_rgb(path, width, height, rows):
    """rows: list of bytes (width*3 each). Plain PNG writer so that no imaging library is needed."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + r for r in rows)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def _tileable_noise(size, cells, rng):
    grid = [[rng.random() for _ in range(cells)] for _ in range(cells)]
    step = cells / float(size)
    out = [[0.0] * size for _ in range(size)]
    for y in range(size):
        fy = y * step
        y0 = int(fy)
        ty = fy - y0
        ty = ty * ty * (3 - 2 * ty)
        y1 = (y0 + 1) % cells
        row0, row1 = grid[y0], grid[y1]
        for x in range(size):
            fx = x * step
            x0 = int(fx)
            tx = fx - x0
            tx = tx * tx * (3 - 2 * tx)
            x1 = (x0 + 1) % cells
            a = row0[x0] + (row0[x1] - row0[x0]) * tx
            b = row1[x0] + (row1[x1] - row1[x0]) * tx
            out[y][x] = a + (b - a) * ty
    return out


def make_macro_noise(size=256):
    """Tileable noise, 3 channels with different feature sizes: R large blotches, G medium, B small. Mean about 0.5."""
    rng = random.Random(20240611)
    chans = []
    for cell_a, cell_b in ((3, 7), (6, 13), (9, 21)):
        a = _tileable_noise(size, cell_a, rng)
        b = _tileable_noise(size, cell_b, rng)
        vals = [[0.68 * a[y][x] + 0.32 * b[y][x] for x in range(size)] for y in range(size)]
        flat = sorted(v for r in vals for v in r)
        lo, hi = flat[int(len(flat) * 0.02)], flat[int(len(flat) * 0.98)]
        chans.append([[min(1.0, max(0.0, (v - lo) / (hi - lo))) for v in r] for r in vals])
    rows = []
    for y in range(size):
        rows.append(bytes(int(chans[c][y][x] * 255) for x in range(size) for c in range(3)))
    path = os.path.join(unreal.SystemLibrary.get_project_saved_directory(), "ia_macro_noise.png")
    _write_png_rgb(path, size, size, rows)
    return path


def _import_file(src, asset_name):
    path = "%s/%s" % (TEX_DIR, asset_name)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", TEX_DIR)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = eal.load_asset(path)
    if tex is None:
        raise RuntimeError("texture import failed: " + src)
    return tex


def _setup(tex, kind):
    """kind: D colour (sRGB), N normal map (green flipped for Unreal), R single channel linear, M masks / macro noise."""
    tex.set_editor_property("max_texture_size", 1024)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    if kind == "D":
        tex.set_editor_property("srgb", True)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        tex.set_editor_property("compression_no_alpha", True)
    elif kind == "N":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP)
        tex.set_editor_property("flip_green_channel", True)          # sources are OpenGL (Y up), Unreal wants DirectX
    elif kind == "R":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_ALPHA)
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD_SPECULAR)
    else:  # "M"
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        tex.set_editor_property("compression_no_alpha", True)


def import_set(name, force=False):
    """Imports T_<name>_D / _N / _R (and _E for Lava) from the texture cache. Downloads them first if needed."""
    meta = ft.fetch(name)
    out = {}
    plan = (("D", "diff"), ("N", "nor"), ("R", "rough")) + ((("E", "emis"),) if "emis" in meta["files"] else ())
    for suffix, key in plan:
        asset = "T_%s_%s" % (name, suffix)
        path = "%s/%s" % (TEX_DIR, asset)
        if eal.does_asset_exist(path) and not force:
            out[suffix] = eal.load_asset(path)
            continue
        src = os.path.join(ft.cache_dir(), name, meta["files"][key])
        tex = _import_file(src, asset)
        _setup(tex, "D" if suffix in ("D", "E") else suffix)
        eal.save_asset(path)
        out[suffix] = tex
    return out


def ensure_noise():
    path = "%s/%s" % (TEX_DIR, NOISE_NAME)
    if eal.does_asset_exist(path):
        return eal.load_asset(path)
    tex = _import_file(make_macro_noise(), NOISE_NAME)
    _setup(tex, "M")
    tex.set_editor_property("compression_no_alpha", True)
    eal.save_asset(path)
    return tex


# =====================================================================================================
# Material graph helpers
# =====================================================================================================

def _node(mat, cls, x, y, **props):
    e = lib.create_material_expression(mat, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def _link(src, dst, input_name, out=""):
    if not lib.connect_material_expressions(src, out, dst, input_name):
        raise RuntimeError("could not connect %s -> %s.%s" % (src.get_name(), dst.get_name(), input_name))


def _scalar(mat, name, value, x, y, group=""):
    e = _node(mat, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=float(value))
    if group:
        e.set_editor_property("group", group)
    return e


def _vector(mat, name, rgb, x, y, group=""):
    e = _node(mat, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
              default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    if group:
        e.set_editor_property("group", group)
    return e


def _texobj(mat, name, default, sampler, x, y):
    e = _node(mat, unreal.MaterialExpressionTextureObjectParameter, x, y, parameter_name=name)
    e.set_editor_property("texture", default)
    e.set_editor_property("sampler_type", sampler)
    e.set_editor_property("group", "Textures")
    return e


def _append(mat, a, b, x, y):
    e = _node(mat, unreal.MaterialExpressionAppendVector, x, y)
    _link(a, e, "A")
    _link(b, e, "B")
    return e


def _custom(mat, name, code, inputs, out_type, x, y):
    """inputs: list of (input name, source expression). Returns the Custom node."""
    c = _node(mat, unreal.MaterialExpressionCustom, x, y)
    arr = []
    for n, _ in inputs:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        arr.append(ci)
    c.set_editor_property("description", name)
    c.set_editor_property("code", code)
    c.set_editor_property("output_type", out_type)
    c.set_editor_property("inputs", arr)
    for n, src in inputs:
        _link(src, c, n)
    return c


def _new_asset(path, cls, factory):
    folder, name = path.rsplit("/", 1)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)


# Shared triplanar set-up of the HLSL: weights from the world normal, the three plane UVs (u runs to the right as seen from
# outside, v runs down, so wood grain and brick courses stay horizontal on every wall) and their screen derivatives. The
# derivatives are taken before any branch so that SampleGrad is legal inside the "if (weight > 0)" blocks, which skip the
# texture reads of the planes that a face does not use (a flat wall costs one plane, not three).
HLSL_TRI_SETUP = """
float3 n = normalize(Nrm);
float3 w = pow(abs(n), 4.0);
w = w / (w.x + w.y + w.z);
w = w * step(0.05, w);
w = w / (w.x + w.y + w.z);
float3 sg = float3(n.x < 0 ? -1.0 : 1.0, n.y < 0 ? -1.0 : 1.0, n.z < 0 ? -1.0 : 1.0);
float2 uv0[3];
uv0[0] = float2(sg.x * Pos.y, -Pos.z);
uv0[1] = float2(-sg.y * Pos.x, -Pos.z);
uv0[2] = float2(sg.z * Pos.x, -Pos.y);
float2 dx0[3];
float2 dy0[3];
[unroll] for (int k = 0; k < 3; k++) { dx0[k] = ddx(uv0[k]); dy0[k] = ddy(uv0[k]); }
float ws[3];
ws[0] = w.x; ws[1] = w.y; ws[2] = w.z;
"""

HLSL_BASE = HLSL_TRI_SETUP + """
float tiling = P1.x;
float macroScale = P1.y;
float macroStrength = P1.z;
float desat = P1.w;
float3 col = float3(0, 0, 0);
float rough = 0.0;
float2 mac = float2(0, 0);
[unroll] for (int i = 0; i < 3; i++)
{
    if (ws[i] > 0.0)
    {
        float2 uv = uv0[i] * tiling;
        float2 dx = dx0[i] * tiling;
        float2 dy = dy0[i] * tiling;
        col += ws[i] * DTex.SampleGrad(DTexSampler, uv, dx, dy).rgb;
        rough += ws[i] * RTex.SampleGrad(RTexSampler, uv, dx, dy).r;
        float4 m = MTex.SampleGrad(MTexSampler, uv0[i] * macroScale, dx0[i] * macroScale, dy0[i] * macroScale);
        mac += ws[i] * float2(m.r * 0.62 + m.g * 0.38, m.b);
    }
}
float lum = dot(col, float3(0.3, 0.59, 0.11));
col = lerp(col, float3(lum, lum, lum), desat);
col *= P3.rgb;
// large-scale variation: lighter/darker blotches and a slight warm/cool drift
col *= 1.0 + (mac.x - 0.5) * 2.0 * macroStrength;
col *= 1.0 + (mac.y - 0.5) * macroStrength * 0.5 * float3(0.35, 0.0, -0.35);
rough += (mac.x - 0.5) * macroStrength * 0.5;
// dirt: the foot of walls gets darker and rougher
float dirtAmount = P2.z;
float h = saturate(1.0 - (Pos.z - P3.w) / max(P2.w, 1.0));
float wall = 1.0 - abs(n.z) * 0.5;
float d = saturate(dirtAmount * h * h * wall * (0.55 + 0.9 * mac.x));
col *= lerp(1.0, 0.38, d);
rough = lerp(rough, 0.95, d * 0.6);
rough = saturate(rough * P2.x + P2.y);
return float4(col, rough);
"""

HLSL_NORMAL = HLSL_TRI_SETUP + """
float tiling = P1.x;
float3 pert = float3(0, 0, 0);
[unroll] for (int i = 0; i < 3; i++)
{
    if (ws[i] > 0.0)
    {
        float2 t = NTex.SampleGrad(NTexSampler, uv0[i] * tiling, dx0[i] * tiling, dy0[i] * tiling).xy * 2.0 - 1.0;
        float3 tu = (i == 0) ? float3(0, sg.x, 0) : ((i == 1) ? float3(-sg.y, 0, 0) : float3(sg.z, 0, 0));
        float3 tv = (i == 2) ? float3(0, -1, 0) : float3(0, 0, -1);
        pert += ws[i] * (tu * t.x + tv * t.y);
    }
}
return normalize(n + pert * NStr);
"""


def build_master(force=False):
    """Creates /Game/Materials/M_IAWorld (the world-aligned master). Returns the material."""
    if eal.does_asset_exist(MASTER_PATH):
        if not force:
            return eal.load_asset(MASTER_PATH)
        eal.delete_asset(MASTER_PATH)
    ensure_noise()
    base = import_set("ConcreteDirty")          # default textures of the parameters (types must match the samplers)
    noise = eal.load_asset("%s/%s" % (TEX_DIR, NOISE_NAME))

    mat = _new_asset(MASTER_PATH, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("tangent_space_normal", False)       # the triplanar normal is computed in world space
    mat.set_editor_property("used_with_instanced_static_meshes", True)
    mat.set_editor_property("used_with_nanite", True)
    lib.delete_all_material_expressions(mat)

    # parameters
    G = "Surface"
    p_diff = _texobj(mat, "DiffuseTex", base["D"], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -1400, -300)
    p_norm = _texobj(mat, "NormalTex", base["N"], unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -1400, -150)
    p_rough = _texobj(mat, "RoughnessTex", base["R"], unreal.MaterialSamplerType.SAMPLERTYPE_ALPHA, -1400, 0)
    p_noise = _texobj(mat, "MacroNoiseTex", noise, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -1400, 150)
    s_tile = _scalar(mat, "TilingMeters", DEFAULTS["TilingMeters"], -1400, 400, G)
    s_macro_m = _scalar(mat, "MacroMeters", DEFAULTS["MacroMeters"], -1400, 480, G)
    s_macro = _scalar(mat, "MacroStrength", DEFAULTS["MacroStrength"], -1400, 560, G)
    s_desat = _scalar(mat, "Desaturate", DEFAULTS["Desaturate"], -1400, 640, G)
    s_rs = _scalar(mat, "RoughnessScale", DEFAULTS["RoughnessScale"], -1400, 720, G)
    s_rb = _scalar(mat, "RoughnessBias", DEFAULTS["RoughnessBias"], -1400, 800, G)
    s_dirt = _scalar(mat, "DirtAmount", DEFAULTS["DirtAmount"], -1400, 880, G)
    s_dirt_h = _scalar(mat, "DirtHeight", DEFAULTS["DirtHeight"], -1400, 960, G)
    s_dirt_z = _scalar(mat, "DirtGroundZ", DEFAULTS["DirtGroundZ"], -1400, 1040, G)
    s_nstr = _scalar(mat, "NormalStrength", DEFAULTS["NormalStrength"], -1400, 1120, G)
    s_metal = _scalar(mat, "Metallic", DEFAULTS["Metallic"], -1400, 1200, G)
    v_tint = _vector(mat, "Tint", (1.0, 1.0, 1.0), -1400, 1280, G)

    pos = _node(mat, unreal.MaterialExpressionWorldPosition, -1400, 1400)
    nrm = _node(mat, unreal.MaterialExpressionVertexNormalWS, -1400, 1480)

    # uv per centimetre = 0.01 / metres
    c001 = _node(mat, unreal.MaterialExpressionConstant, -1200, 400, r=0.01)
    tiling = _node(mat, unreal.MaterialExpressionDivide, -1050, 400)
    _link(c001, tiling, "A")
    _link(s_tile, tiling, "B")
    macro_scale = _node(mat, unreal.MaterialExpressionDivide, -1050, 480)
    _link(c001, macro_scale, "A")
    _link(s_macro_m, macro_scale, "B")

    p1 = _append(mat, _append(mat, _append(mat, tiling, macro_scale, -900, 400), s_macro, -800, 430), s_desat, -700, 460)
    p2 = _append(mat, _append(mat, _append(mat, s_rs, s_rb, -900, 700), s_dirt, -800, 730), s_dirt_h, -700, 760)
    p3 = _append(mat, v_tint, s_dirt_z, -700, 1000)

    base_node = _custom(mat, "TriplanarBase", HLSL_BASE,
                        [("DTex", p_diff), ("RTex", p_rough), ("MTex", p_noise), ("Pos", pos), ("Nrm", nrm),
                         ("P1", p1), ("P2", p2), ("P3", p3)],
                        unreal.CustomMaterialOutputType.CMOT_FLOAT4, -400, 0)
    norm_node = _custom(mat, "TriplanarNormal", HLSL_NORMAL,
                        [("NTex", p_norm), ("Pos", pos), ("Nrm", nrm), ("P1", p1), ("NStr", s_nstr)],
                        unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 400)

    rgb = _node(mat, unreal.MaterialExpressionComponentMask, -150, 0, r=True, g=True, b=True, a=False)
    _link(base_node, rgb, "")
    ra = _node(mat, unreal.MaterialExpressionComponentMask, -150, 150, r=False, g=False, b=False, a=True)
    _link(base_node, ra, "")

    lib.connect_material_property(rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(ra, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(norm_node, "", unreal.MaterialProperty.MP_NORMAL)
    lib.connect_material_property(s_metal, "", unreal.MaterialProperty.MP_METALLIC)

    lib.recompile_material(mat)
    eal.save_asset(MASTER_PATH)
    unreal.log("MATLIB master built: " + MASTER_PATH)
    return mat


# =====================================================================================================
# Instances
# =====================================================================================================

_cache = {}


def _set_instance(mic, name, spec, tint, tiling, overrides):
    meta = ft.load_meta(spec["tex"]) or ft.fetch(spec["tex"])
    sets = import_set(spec["tex"])
    master = build_master()
    lib.set_material_instance_parent(mic, master)
    lib.set_material_instance_texture_parameter_value(mic, "DiffuseTex", sets["D"])
    lib.set_material_instance_texture_parameter_value(mic, "NormalTex", sets["N"])
    lib.set_material_instance_texture_parameter_value(mic, "RoughnessTex", sets["R"])
    scalars = dict(
        TilingMeters=tiling if tiling is not None else (spec["tiling"] or meta["tile_size_m"]),
        RoughnessScale=spec["rs"], RoughnessBias=spec["rb"], NormalStrength=spec["ns"], Metallic=spec["metal"],
        MacroStrength=spec["macro"], MacroMeters=spec["macro_m"], Desaturate=spec["desat"],
        DirtAmount=spec["dirt"], DirtHeight=spec["dirt_h"], DirtGroundZ=0.0)
    for k, v in overrides.items():
        if v is not None:
            scalars[k] = v
    for k, v in scalars.items():
        lib.set_material_instance_scalar_parameter_value(mic, k, float(v))
    lib.set_material_instance_vector_parameter_value(mic, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))


def _tint_for(spec, albedo):
    """Tint that moves the texture's average colour to `albedo` (sRGB 0..255) times the spec's own tint."""
    tint = spec["tint"]
    if albedo is None:
        return tint
    mean = TEX_MEAN.get(spec["tex"])
    target = srgb(*albedo)
    if mean is None:
        return tuple(target[i] * tint[i] for i in range(3))
    if spec["desat"] >= 0.999:
        lum = 0.3 * mean[0] + 0.59 * mean[1] + 0.11 * mean[2]
        mean = (lum, lum, lum)
    elif spec["desat"] > 0:
        lum = 0.3 * mean[0] + 0.59 * mean[1] + 0.11 * mean[2]
        mean = tuple(mean[i] + (lum - mean[i]) * spec["desat"] for i in range(3))
    return tuple(min(8.0, target[i] / max(mean[i], 0.004)) * tint[i] for i in range(3))


def surface(name, tint=None, tiling=None, albedo=None, tag=None, **params):
    """Returns the material instance for a surface of SURFACES (creates texture imports, master and instance on first use).

    surface("BrickRed")                                  the standard MI_W_BrickRed
    surface("BrickRed", tiling=2.0)                      same, texture repeats every 2 m (a variant instance is created)
    surface("ConcreteClean", albedo=(120, 40, 40))       aim the average colour at sRGB (120, 40, 40)
    surface("Asphalt", tint=(0.8, 0.8, 1.0))             multiply the colour (linear)
    surface("Snow", rb=-0.2, tag="Glacier")              other parameters: rs, rb (roughness scale/bias), ns (normal
                                                         strength), metal, desat, macro, dirt, dirt_h
    `tag` names the variant (MI_W_<name>_<tag>); without it a short hash of the settings is used. Same name and settings
    always give the same asset, so scripts can be run again.
    """
    base_spec = SURFACES[name]
    spec = dict(base_spec)
    keymap = dict(rs="rs", rb="rb", ns="ns", metal="metal", desat="desat", macro="macro", macro_m="macro_m",
                  dirt="dirt", dirt_h="dirt_h")
    for k, v in params.items():
        if k not in keymap:
            raise KeyError("unknown surface parameter " + k)
        spec[keymap[k]] = v
    use_albedo = albedo if albedo is not None else spec["albedo"]
    final_tint = _tint_for(spec, use_albedo)
    if tint is not None:
        final_tint = tuple(final_tint[i] * tint[i] for i in range(3))
    is_variant = bool(params) or tint is not None or tiling is not None or albedo is not None
    asset = "MI_W_" + name
    if is_variant:
        sig = repr((sorted(params.items()), tint, tiling, albedo))
        asset += "_" + (tag or hashlib.md5(sig.encode()).hexdigest()[:6])
    if asset in _cache:
        return _cache[asset]
    path = "%s/%s" % (MAT_DIR, asset)
    if eal.does_asset_exist(path):
        mic = eal.load_asset(path)
    else:
        mic = _new_asset(path, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    _set_instance(mic, name, spec, final_tint, tiling, {})
    lib.update_material_instance(mic)
    eal.save_asset(path)
    _cache[asset] = mic
    return mic


# =====================================================================================================
# Glass, water, lava
# =====================================================================================================

def build_glass(force=False):
    path = MAT_DIR + "/M_IAGlassClear"
    if eal.does_asset_exist(path):
        if not force:
            return eal.load_asset(path)
        eal.delete_asset(path)
    mat = _new_asset(path, unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    try:
        mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    except Exception as e:
        unreal.log_warning("MATLIB glass lighting mode: %s" % e)
    tint = _vector(mat, "GlassTint", (0.03, 0.05, 0.05), -800, 0)
    opa_min = _scalar(mat, "OpacityMin", 0.10, -800, 100)
    opa_max = _scalar(mat, "OpacityEdge", 0.65, -800, 160)
    rough = _scalar(mat, "Roughness", 0.04, -800, 220)
    fres = _node(mat, unreal.MaterialExpressionFresnel, -800, 300, exponent=3.5, base_reflect_fraction=0.04)
    lerp_op = _node(mat, unreal.MaterialExpressionLinearInterpolate, -500, 120)
    _link(opa_min, lerp_op, "A")
    _link(opa_max, lerp_op, "B")
    _link(fres, lerp_op, "Alpha")
    lib.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(lerp_op, "", unreal.MaterialProperty.MP_OPACITY)
    spec = _node(mat, unreal.MaterialExpressionConstant, -800, 400, r=0.9)
    lib.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("MATLIB glass built")
    return mat


HLSL_WATER = """
// P = (uv per cm, speed, strength, 0); T = time in seconds. Two drifting layers of smooth noise, slopes by finite differences.
float2 uv = Pos.xy * P.x;
float t = T * P.y;
float2 a = uv + float2(t * 0.011, t * 0.004);
float2 b = uv * 2.6 + float2(-t * 0.007, t * 0.013) + 0.37;
float e = 0.004;
float h0 = MTex.SampleLevel(MTexSampler, a, 0).g * 0.65 + MTex.SampleLevel(MTexSampler, b, 0).b * 0.35;
float hx = MTex.SampleLevel(MTexSampler, a + float2(e, 0), 0).g * 0.65 + MTex.SampleLevel(MTexSampler, b + float2(e * 2.6, 0), 0).b * 0.35;
float hy = MTex.SampleLevel(MTexSampler, a + float2(0, e), 0).g * 0.65 + MTex.SampleLevel(MTexSampler, b + float2(0, e * 2.6), 0).b * 0.35;
float2 slope = float2(hx - h0, hy - h0) / e * P.z;
return normalize(float3(-slope.x, -slope.y, 1.0));
"""


def build_water(force=False):
    path = MAT_DIR + "/M_IAWater"
    if eal.does_asset_exist(path):
        if not force:
            return eal.load_asset(path)
        eal.delete_asset(path)
    noise = ensure_noise()
    mat = _new_asset(path, unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    mat.set_editor_property("tangent_space_normal", False)
    p_noise = _texobj(mat, "MacroNoiseTex", noise, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -900, 0)
    color = _vector(mat, "WaterColor", (0.006, 0.022, 0.030), -900, 100)
    rough = _scalar(mat, "Roughness", 0.07, -900, 200)
    s_scale = _scalar(mat, "RippleMeters", 6.0, -900, 260)
    s_speed = _scalar(mat, "Speed", 1.0, -900, 320)
    s_str = _scalar(mat, "RippleStrength", 0.012, -900, 380)
    time = _node(mat, unreal.MaterialExpressionTime, -900, 440)
    c001 = _node(mat, unreal.MaterialExpressionConstant, -800, 260, r=0.01)
    uvs = _node(mat, unreal.MaterialExpressionDivide, -650, 260)
    _link(c001, uvs, "A")
    _link(s_scale, uvs, "B")
    zero = _node(mat, unreal.MaterialExpressionConstant, -650, 330, r=0.0)
    p = _append(mat, _append(mat, _append(mat, uvs, s_speed, -500, 260), s_str, -400, 290), zero, -300, 320)
    pos = _node(mat, unreal.MaterialExpressionWorldPosition, -900, 500)
    nrm = _custom(mat, "WaterNormal", HLSL_WATER, [("MTex", p_noise), ("Pos", pos), ("P", p), ("T", time)],
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, -150, 300)
    lib.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("MATLIB water built")
    return mat


HLSL_LAVA_SETUP = """
// P = (uv per cm, speed, intensity, 0); T = time in seconds. Two flowing layers of the lava scan, warped by noise.
float2 uv = Pos.xy * P.x;
float t = T * P.y;
float2 flow = float2(MTex.SampleLevel(MTexSampler, uv * 0.35 + t * 0.012, 0).r,
                     MTex.SampleLevel(MTexSampler, uv * 0.35 + 0.5 - t * 0.009, 0).g) - 0.5;
float2 uvA = uv + flow * 0.30 + float2(t * 0.020, t * 0.008);
float2 uvB = uv * 0.63 + flow * 0.22 + float2(-t * 0.012, t * 0.018);
float mixer = MTex.SampleLevel(MTexSampler, uv * 0.12 + t * 0.004, 0).b;
"""

HLSL_LAVA_EMIS = HLSL_LAVA_SETUP + """
float3 eA = ETex.Sample(ETexSampler, uvA).rgb;
float3 eB = ETex.Sample(ETexSampler, uvB).rgb;
float pulse = 0.88 + 0.12 * sin(t * 1.3 + mixer * 6.2831);
return pow(saturate(lerp(eA, eB, mixer)), 1.8) * P.z * pulse;
"""

HLSL_LAVA_COL = HLSL_LAVA_SETUP + """
float3 cA = DTex.Sample(DTexSampler, uvA).rgb;
float3 cB = DTex.Sample(DTexSampler, uvB).rgb;
return lerp(cA, cB, mixer) * 0.35;
"""


def build_lava(force=False):
    path = MAT_DIR + "/M_IALava"
    if eal.does_asset_exist(path):
        if not force:
            return eal.load_asset(path)
        eal.delete_asset(path)
    noise = ensure_noise()
    sets = import_set("Lava")
    mat = _new_asset(path, unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    p_noise = _texobj(mat, "MacroNoiseTex", noise, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -900, 0)
    p_diff = _texobj(mat, "DiffuseTex", sets["D"], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -900, 100)
    p_emis = _texobj(mat, "EmissiveTex", sets["E"], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -900, 200)
    s_scale = _scalar(mat, "TilingMeters", 2.5, -900, 300)
    s_speed = _scalar(mat, "Speed", 1.0, -900, 360)
    s_int = _scalar(mat, "Intensity", 5.0, -900, 420)
    time = _node(mat, unreal.MaterialExpressionTime, -900, 480)
    c001 = _node(mat, unreal.MaterialExpressionConstant, -800, 300, r=0.01)
    uvs = _node(mat, unreal.MaterialExpressionDivide, -650, 300)
    _link(c001, uvs, "A")
    _link(s_scale, uvs, "B")
    zero = _node(mat, unreal.MaterialExpressionConstant, -650, 380, r=0.0)
    p = _append(mat, _append(mat, _append(mat, uvs, s_speed, -500, 300), s_int, -400, 330), zero, -300, 360)
    pos = _node(mat, unreal.MaterialExpressionWorldPosition, -900, 560)
    emis = _custom(mat, "LavaEmissive", HLSL_LAVA_EMIS,
                   [("MTex", p_noise), ("ETex", p_emis), ("Pos", pos), ("P", p), ("T", time)],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -100, 300)
    col = _custom(mat, "LavaColor", HLSL_LAVA_COL,
                  [("MTex", p_noise), ("DTex", p_diff), ("Pos", pos), ("P", p), ("T", time)],
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, -100, 0)
    rough = _node(mat, unreal.MaterialExpressionConstant, -100, 150, r=0.75)
    lib.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(path)
    unreal.log("MATLIB lava built")
    return mat


def glass():
    """/Game/Materials/M_IAGlassClear (translucent, subtle reflection). Parameters: GlassTint, OpacityMin, OpacityEdge, Roughness."""
    return build_glass()


def water():
    """/Game/Materials/M_IAWater (calm dark water, flat in XY). Parameters: WaterColor, Roughness, RippleMeters, Speed, RippleStrength."""
    return build_water()


def lava():
    """/Game/Materials/M_IALava (the only emissive material). Parameters: TilingMeters, Speed, Intensity."""
    return build_lava()


def build_all(force_master=False):
    """Imports every texture set and creates the master, all MI_W_* instances, glass, water and lava."""
    build_master(force_master)
    n = 0
    for name in SURFACES:
        surface(name)
        n += 1
    build_glass(force_master)
    build_water(force_master)
    build_lava(force_master)
    unreal.log("MATLIB_DONE %d surfaces" % n)
