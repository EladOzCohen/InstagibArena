"""Creates the character materials and prints a few facts about the mannequin assets.

  /Game/Characters/M_IABody       flat colour + emissive "Glow" (beams, sparks, jump pads, light strips). Kept as it was.
  /Game/Characters/M_IACharacter  matte fabric/armour material of the people: micro normal and roughness detail from a
                                  tiling cloth texture (Poly Haven "Scuba Suede", CC0, see NOTICE.md), a small rim light
                                  for readability and (almost) no emissive. Same parameters as M_IABody plus
                                  Detail, Tile, Rim and Specular, so it can be swapped in everywhere.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_character_assets.py" -unattended -nullrhi -nosplash

The texture files are cached outside the repository (C:\\Users\\<you>\\AssetCache\\textures\\CharSuit, see TEX_DIR). When they
are missing the script downloads them from Poly Haven (CC0) first.
"""

import os
import urllib.request

import unreal

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

PATH = "/Game/Characters"


def recreate(name):
    full = "%s/%s" % (PATH, name)
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        unreal.EditorAssetLibrary.delete_asset(full)
    return tools.create_asset(name, PATH, unreal.Material, unreal.MaterialFactoryNew()), full


# ------------------------------------------------------------------------------------------------ M_IABody (unchanged)
# Only created when missing: map materials, beams, sparks and jump pads are instances of it, and deleting the
# parent would break them.
FULL = "%s/M_IABody" % PATH
def build_body():
    mat = tools.create_asset("M_IABody", PATH, unreal.Material, unreal.MaterialFactoryNew())

    color = lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -700, -200)
    color.set_editor_property("parameter_name", "Color")
    color.set_editor_property("default_value", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))

    rough = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 0)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.55)

    metal = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 120)
    metal.set_editor_property("parameter_name", "Metallic")
    metal.set_editor_property("default_value", 0.15)

    glow = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 260)
    glow.set_editor_property("parameter_name", "Glow")
    glow.set_editor_property("default_value", 0.0)

    emissive = lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -420, 220)
    lib.connect_material_expressions(color, "", emissive, "A")
    lib.connect_material_expressions(glow, "", emissive, "B")

    lib.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    lib.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    mat.set_editor_property("used_with_skeletal_mesh", True)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(FULL)
    unreal.log("CHARASSET material vectors=%s scalars=%s" % (
        list(lib.get_vector_parameter_names(mat)), list(lib.get_scalar_parameter_names(mat))))


if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    unreal.log("CHARASSET M_IABody kept")
else:
    build_body()

# ------------------------------------------------------------------------------------------------ textures
TEX_DIR = os.path.join(os.path.expanduser("~"), "AssetCache", "textures", "CharSuit")
SLUG = "scuba_suede"
FILES = {"D": "diff", "N": "nor_gl", "R": "rough"}
os.makedirs(TEX_DIR, exist_ok=True)
for key, kind in FILES.items():
    local = os.path.join(TEX_DIR, "CharSuit_%s.jpg" % kind)
    if not os.path.exists(local):
        url = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/%s/%s_%s_1k.jpg" % (SLUG, SLUG, kind)
        unreal.log("CHARASSET downloading " + url)
        urllib.request.urlretrieve(url, local)

TEX_PATH = PATH + "/Textures"
textures = {}
for key, kind in FILES.items():
    name = "T_CharSuit_" + key
    full = "%s/%s" % (TEX_PATH, name)
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        unreal.EditorAssetLibrary.delete_asset(full)
    task = unreal.AssetImportTask()
    task.filename = os.path.join(TEX_DIR, "CharSuit_%s.jpg" % kind)
    task.destination_path = TEX_PATH
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    tools.import_asset_tasks([task])
    tex = unreal.EditorAssetLibrary.load_asset(full)
    tex.set_editor_property("power_of_two_mode", unreal.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO)
    if key == "N":
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("flip_green_channel", True)     # Poly Haven normals are OpenGL, Unreal wants DirectX
        tex.set_editor_property("srgb", False)
    elif key == "R":
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
        tex.set_editor_property("srgb", False)
    unreal.EditorAssetLibrary.save_asset(full)
    textures[key] = tex

# ------------------------------------------------------------------------------------------------ M_IACharacter
cm, CFULL = recreate("M_IACharacter")


def node(cls, x, y):
    return lib.create_material_expression(cm, cls, x, y)


def vparam(name, default, x, y):
    n = node(unreal.MaterialExpressionVectorParameter, x, y)
    n.set_editor_property("parameter_name", name)
    n.set_editor_property("default_value", default)
    return n


def sparam(name, default, x, y):
    n = node(unreal.MaterialExpressionScalarParameter, x, y)
    n.set_editor_property("parameter_name", name)
    n.set_editor_property("default_value", default)
    return n


def link(a, b, to_input, out=""):
    lib.connect_material_expressions(a, out, b, to_input)


def const(value, x, y):
    n = node(unreal.MaterialExpressionConstant, x, y)
    n.set_editor_property("r", value)
    return n


def sample(texture, sampler, uv, x, y):
    n = node(unreal.MaterialExpressionTextureSample, x, y)
    n.set_editor_property("texture", texture)
    n.set_editor_property("sampler_type", sampler)
    link(uv, n, "UVs")
    return n


p_color = vparam("Color", unreal.LinearColor(0.35, 0.35, 0.35, 1.0), -1400, -600)
p_color2 = vparam("Color2", unreal.LinearColor(0.12, 0.12, 0.12, 1.0), -1400, -500)     # fabric under the plates
p_rough = sparam("Roughness", 0.78, -1400, -300)
p_rough2 = sparam("Roughness2", 0.9, -1400, -250)
p_metal = sparam("Metallic", 0.0, -1400, -200)
p_glow = sparam("Glow", 0.0, -1400, -100)
p_detail = sparam("Detail", 1.0, -1400, 0)
p_tile = sparam("Tile", 7.0, -1400, 100)
p_rim = sparam("Rim", 0.0, -1400, 200)
p_spec = sparam("Specular", 0.35, -1400, 300)
p_panel = sparam("PanelAmount", 0.0, -1400, 500)

# The mannequin's own albedo map is a plate / fabric map (light = armour plate, dark = fabric and rubber, dark lines = seams).
# Its brightness drives the split between Color (plates) and Color2 (fabric). PanelAmount 0 turns it off (accessories).
panel_tex = node(unreal.MaterialExpressionTextureSampleParameter2D, -1000, 900)
panel_tex.set_editor_property("parameter_name", "PanelTex")
panel_tex.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Textures/Manny/T_Manny_02_D"))
panel_tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
plum = node(unreal.MaterialExpressionDesaturation, -780, 900)
link(panel_tex, plum, "", "RGB")
pm_sub = node(unreal.MaterialExpressionSubtract, -600, 900)
link(plum, pm_sub, "A")
pm_sub.set_editor_property("const_b", 0.12)
pm_mul = node(unreal.MaterialExpressionMultiply, -440, 900)
link(pm_sub, pm_mul, "A")
pm_mul.set_editor_property("const_b", 3.3)
pm_cl = node(unreal.MaterialExpressionClamp, -280, 900)
link(pm_mul, pm_cl, "")
pm = node(unreal.MaterialExpressionLinearInterpolate, -120, 900)      # m: 1 on plates (and everywhere when PanelAmount = 0)
pm.set_editor_property("const_a", 1.0)
link(pm_cl, pm, "B")
link(p_panel, pm, "Alpha")
sh_mul = node(unreal.MaterialExpressionMultiply, -600, 1000)
link(plum, sh_mul, "A")
sh_mul.set_editor_property("const_b", 1.4)
sh_cl = node(unreal.MaterialExpressionClamp, -440, 1000)
link(sh_mul, sh_cl, "")
sh_cl.set_editor_property("min_default", 0.5)
sh_cl.set_editor_property("max_default", 1.0)
shade = node(unreal.MaterialExpressionLinearInterpolate, -280, 1000)  # seam shading on the plates only
shade.set_editor_property("const_a", 1.0)
link(sh_cl, shade, "B")
sh_a = node(unreal.MaterialExpressionMultiply, -440, 1100)             # only where panels are in use AND on plates
link(pm, sh_a, "A")
link(p_panel, sh_a, "B")
link(sh_a, shade, "Alpha")

# Cloth detail is strong on fabric and weak on plates: Detail * lerp(1, 0.4, m)
det_k = node(unreal.MaterialExpressionLinearInterpolate, -120, 1000)
det_k.set_editor_property("const_a", 1.0)
det_k.set_editor_property("const_b", 0.4)
link(pm, det_k, "Alpha")
detail = node(unreal.MaterialExpressionMultiply, 60, 1000)
link(p_detail, detail, "A")
link(det_k, detail, "B")

# UV = TexCoord * Tile
tc = node(unreal.MaterialExpressionTextureCoordinate, -1200, 500)
uv = node(unreal.MaterialExpressionMultiply, -1000, 500)
link(tc, uv, "A")
link(p_tile, uv, "B")

# Normal: lerp(flat, cloth normal, detail)
t_n = sample(textures["N"], unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, uv, -800, 300)
flat = node(unreal.MaterialExpressionConstant3Vector, -800, 150)
flat.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
nrm = node(unreal.MaterialExpressionLinearInterpolate, -560, 250)
link(flat, nrm, "A")
link(t_n, nrm, "B", "RGB")
link(detail, nrm, "Alpha")

# Roughness: lerp(Roughness2, Roughness, m) + (cloth - 0.5) * 0.6 * detail, clamped
t_r = sample(textures["R"], unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, uv, -800, 560)
sub = node(unreal.MaterialExpressionSubtract, -560, 560)
link(t_r, sub, "A", "R")
sub.set_editor_property("const_b", 0.5)
m1 = node(unreal.MaterialExpressionMultiply, -360, 560)
link(sub, m1, "A")
link(detail, m1, "B")
m2 = node(unreal.MaterialExpressionMultiply, -180, 560)
link(m1, m2, "A")
m2.set_editor_property("const_b", 0.6)
rbase = node(unreal.MaterialExpressionLinearInterpolate, -180, 440)
link(p_rough2, rbase, "A")
link(p_rough, rbase, "B")
link(pm, rbase, "Alpha")
radd = node(unreal.MaterialExpressionAdd, 20, 520)
link(rbase, radd, "A")
link(m2, radd, "B")
rclamp = node(unreal.MaterialExpressionClamp, 220, 520)
link(radd, rclamp, "")
rclamp.set_editor_property("min_default", 0.08)
rclamp.set_editor_property("max_default", 1.0)

# Base colour: lerp(Color2, Color, m) * seam shade * cloth brightness variation (grayscale of the cloth diffuse, +-20 %)
t_d = sample(textures["D"], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, uv, -800, 800)
gray = node(unreal.MaterialExpressionDesaturation, -560, 800)
link(t_d, gray, "", "RGB")
ratio = node(unreal.MaterialExpressionDivide, -360, 800)
link(gray, ratio, "A")
ratio.set_editor_property("const_b", 0.12)
rcl = node(unreal.MaterialExpressionClamp, -180, 800)
link(ratio, rcl, "")
rcl.set_editor_property("min_default", 0.8)
rcl.set_editor_property("max_default", 1.2)
var = node(unreal.MaterialExpressionLinearInterpolate, 20, 780)
var.set_editor_property("const_a", 1.0)
link(rcl, var, "B")
link(detail, var, "Alpha")
cmix = node(unreal.MaterialExpressionLinearInterpolate, 20, 640)
link(p_color2, cmix, "A")
link(p_color, cmix, "B")
link(pm, cmix, "Alpha")
base1 = node(unreal.MaterialExpressionMultiply, 220, 700)
link(cmix, base1, "A")
link(var, base1, "B")
base = node(unreal.MaterialExpressionMultiply, 400, 700)
link(base1, base, "A")
link(shade, base, "B")
metal_m = node(unreal.MaterialExpressionMultiply, 400, 560)
link(p_metal, metal_m, "A")
link(pm, metal_m, "B")

# Emissive: Color * Glow  +  RimColor * Fresnel * Rim (a thin readable edge light in the team colour, off by default)
em_glow = node(unreal.MaterialExpressionMultiply, -800, -400)
link(p_color, em_glow, "A")
link(p_glow, em_glow, "B")
fres = node(unreal.MaterialExpressionFresnel, -1000, -250)
fres.set_editor_property("exponent", 3.5)
fres.set_editor_property("base_reflect_fraction", 0.0)
p_rimcolor = vparam("RimColor", unreal.LinearColor(1.0, 1.0, 1.0, 1.0), -1400, 400)
fr_c = node(unreal.MaterialExpressionMultiply, -800, -250)
link(p_rimcolor, fr_c, "A")
link(fres, fr_c, "B")
fr_r = node(unreal.MaterialExpressionMultiply, -600, -250)
link(fr_c, fr_r, "A")
link(p_rim, fr_r, "B")
em = node(unreal.MaterialExpressionAdd, -380, -330)
link(em_glow, em, "A")
link(fr_r, em, "B")

lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(metal_m, "", unreal.MaterialProperty.MP_METALLIC)
lib.connect_material_property(p_spec, "", unreal.MaterialProperty.MP_SPECULAR)
lib.connect_material_property(rclamp, "", unreal.MaterialProperty.MP_ROUGHNESS)
lib.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)
lib.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

cm.set_editor_property("used_with_skeletal_mesh", True)
lib.recompile_material(cm)
unreal.EditorAssetLibrary.save_asset(CFULL)
unreal.log("CHARASSET character material vectors=%s scalars=%s" % (
    list(lib.get_vector_parameter_names(cm)), list(lib.get_scalar_parameter_names(cm))))

# ------------------------------------------------------------------------------------------------ facts
for path in ("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple", "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        unreal.log_error("CHARASSET missing " + path)
        continue
    unreal.log("CHARASSET %s materials=%d physics=%s skeleton=%s" % (
        path.split("/")[-1], len(asset.materials),
        asset.get_editor_property("physics_asset"), asset.get_editor_property("skeleton")))

abp = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
unreal.log("CHARASSET abp=%s" % abp)
unreal.log("CHARASSET_DONE")
