"""Builds the Instagib rifle: two static meshes with six material slots and the weapon materials.

  /Game/Characters/Weapon/SM_IARifle_FP   first person rifle (about 8000 triangles, bolts, rail slots, vent slats)
  /Game/Characters/Weapon/SM_IARifle_TP   the rifle the characters carry (about 3500 triangles)
  /Game/Characters/Weapon/M_IAWeapon      master material: BodyColor, AccentColor, Glow, Roughness, Metallic, Detail, Tile ...
  /Game/Characters/Weapon/MI_IAWeapon_*   one instance per slot: Body, Trim, Rubber, Accent, Core, Glass

The geometry comes from Tools/mesh_weapon.py (pure python). The folder is under /Game/Characters, which is always cooked, because
IAPlayerCharacter.cpp loads the rifle by path.  Fine detail (brushed metal normal and roughness) uses the CC0 ambientCG
"Metal012" set that the material library already downloaded (see NOTICE.md), rubber uses the character cloth texture.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools/make_weapon_assets.py -unattended -nullrhi -nosplash
Output lines start with WEAPON; the last one is WEAPON_DONE.
"""

import os
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import mapkit_b          # noqa: E402  (only used for the winding detection)
import mesh_weapon as mw  # noqa: E402

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary

PATH = "/Game/Characters/Weapon"
TEX_PATH = PATH + "/Textures"
CACHE = os.path.join(os.path.expanduser("~"), "AssetCache", "textures", "BrushedMetal")


def log(msg):
    unreal.log("WEAPON " + msg)


# ------------------------------------------------------------------------------------------------ textures
def import_texture(local, name, kind):
    full = "%s/%s" % (TEX_PATH, name)
    if eal.does_asset_exist(full):
        eal.delete_asset(full)
    task = unreal.AssetImportTask()
    task.filename = local
    task.destination_path = TEX_PATH
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    tools.import_asset_tasks([task])
    tex = eal.load_asset(full)
    tex.set_editor_property("power_of_two_mode", unreal.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO)
    tex.set_editor_property("srgb", False)
    if kind == "N":
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("flip_green_channel", True)
    else:
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
    eal.save_asset(full)
    return tex


if not eal.does_directory_exist(PATH):
    eal.make_directory(PATH)
tex_n = import_texture(os.path.join(CACHE, "BrushedMetal_nor.jpg"), "T_Weapon_Metal_N", "N")
tex_r = import_texture(os.path.join(CACHE, "BrushedMetal_rough.jpg"), "T_Weapon_Metal_R", "R")
suit_n = eal.load_asset("/Game/Characters/Textures/T_CharSuit_N")
suit_r = eal.load_asset("/Game/Characters/Textures/T_CharSuit_R")

# ------------------------------------------------------------------------------------------------ master material
MFULL = PATH + "/M_IAWeapon"
if eal.does_asset_exist(MFULL):
    eal.delete_asset(MFULL)
mat = tools.create_asset("M_IAWeapon", PATH, unreal.Material, unreal.MaterialFactoryNew())


def node(cls, x, y):
    return lib.create_material_expression(mat, cls, x, y)


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


def tex_param(name, texture, sampler, uv, x, y):
    n = node(unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    n.set_editor_property("parameter_name", name)
    n.set_editor_property("texture", texture)
    n.set_editor_property("sampler_type", sampler)
    link(uv, n, "UVs")
    return n


p_body = vparam("BodyColor", unreal.LinearColor(0.08, 0.085, 0.095, 1.0), -1400, -600)
p_accent = vparam("AccentColor", unreal.LinearColor(1.0, 0.5, 0.05, 1.0), -1400, -450)
p_rough = sparam("Roughness", 0.5, -1400, -300)
p_metal = sparam("Metallic", 0.7, -1400, -200)
p_glow = sparam("Glow", 0.0, -1400, -100)
p_detail = sparam("Detail", 1.0, -1400, 0)
p_tile = sparam("Tile", 1.0, -1400, 100)
p_spec = sparam("Specular", 0.5, -1400, 200)

tc = node(unreal.MaterialExpressionTextureCoordinate, -1200, 400)
uv = node(unreal.MaterialExpressionMultiply, -1000, 400)
link(tc, uv, "A")
link(p_tile, uv, "B")

t_n = tex_param("NormalTex", tex_n, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, uv, -800, 250)
t_r = tex_param("RoughTex", tex_r, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, uv, -800, 520)

flat = node(unreal.MaterialExpressionConstant3Vector, -800, 100)
flat.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
nrm = node(unreal.MaterialExpressionLinearInterpolate, -540, 220)
link(flat, nrm, "A")
link(t_n, nrm, "B", "RGB")
link(p_detail, nrm, "Alpha")

# roughness: Roughness + (texture - 0.5) * 0.6 * Detail
sub = node(unreal.MaterialExpressionSubtract, -540, 520)
link(t_r, sub, "A", "R")
sub.set_editor_property("const_b", 0.5)
m1 = node(unreal.MaterialExpressionMultiply, -360, 520)
link(sub, m1, "A")
link(p_detail, m1, "B")
m2 = node(unreal.MaterialExpressionMultiply, -180, 520)
link(m1, m2, "A")
m2.set_editor_property("const_b", 0.6)
radd = node(unreal.MaterialExpressionAdd, 20, 480)
link(p_rough, radd, "A")
link(m2, radd, "B")
rcl = node(unreal.MaterialExpressionClamp, 200, 480)
link(radd, rcl, "")
rcl.set_editor_property("min_default", 0.06)
rcl.set_editor_property("max_default", 1.0)

# base colour: BodyColor * (1 + (texture * 2 - 1) * 0.25 * Detail) clamped, a little brightness variation from the same map
v1 = node(unreal.MaterialExpressionMultiply, -540, 700)
link(t_r, v1, "A", "R")
v1.set_editor_property("const_b", 2.0)
vcl = node(unreal.MaterialExpressionClamp, -360, 700)
link(v1, vcl, "")
vcl.set_editor_property("min_default", 0.55)
vcl.set_editor_property("max_default", 1.45)
var = node(unreal.MaterialExpressionLinearInterpolate, -180, 700)
var.set_editor_property("const_a", 1.0)
link(vcl, var, "B")
vk = node(unreal.MaterialExpressionMultiply, -360, 800)
link(p_detail, vk, "A")
vk.set_editor_property("const_b", 0.5)
link(vk, var, "Alpha")
base = node(unreal.MaterialExpressionMultiply, 20, 650)
link(p_body, base, "A")
link(var, base, "B")

em = node(unreal.MaterialExpressionMultiply, -540, -400)
link(p_accent, em, "A")
link(p_glow, em, "B")

lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(p_metal, "", unreal.MaterialProperty.MP_METALLIC)
lib.connect_material_property(p_spec, "", unreal.MaterialProperty.MP_SPECULAR)
lib.connect_material_property(rcl, "", unreal.MaterialProperty.MP_ROUGHNESS)
lib.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)
lib.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
lib.recompile_material(mat)
eal.save_asset(MFULL)
log("master vectors=%s scalars=%s" % (list(lib.get_vector_parameter_names(mat)), list(lib.get_scalar_parameter_names(mat))))

# ------------------------------------------------------------------------------------------------ instances, one per mesh slot
# name, BodyColor, AccentColor, Roughness, Metallic, Glow, Detail, Tile, textures
SLOTS = [
    ("Body",   (0.15, 0.155, 0.17),    (1, 1, 1),        0.42, 0.5,  0.0, 1.0, 1.0, None),
    ("Trim",   (0.06, 0.065, 0.072),   (1, 1, 1),        0.52, 0.5,  0.0, 1.0, 1.5, None),
    ("Rubber", (0.045, 0.045, 0.05),   (1, 1, 1),        0.86, 0.0,  0.0, 1.0, 3.0, (suit_n, suit_r)),
    ("Accent", (0.55, 0.30, 0.04),     (1.0, 0.5, 0.05), 0.48, 0.25, 0.0, 0.6, 1.0, None),
    ("Core",   (0.03, 0.08, 0.1),      (0.1, 0.9, 1.0),  0.25, 0.0,  2.0, 0.0, 1.0, None),
    ("Glass",  (0.006, 0.01, 0.014),   (1, 1, 1),        0.06, 0.0,  0.0, 0.0, 1.0, None),
]
instances = []
for (name, body, acc, rough, metal, glow, detail, tile, texs) in SLOTS:
    iname = "MI_IAWeapon_" + name
    full = "%s/%s" % (PATH, iname)
    if eal.does_asset_exist(full):
        eal.delete_asset(full)
    mic = tools.create_asset(iname, PATH, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    lib.set_material_instance_parent(mic, mat)
    lib.set_material_instance_vector_parameter_value(mic, "BodyColor", unreal.LinearColor(body[0], body[1], body[2], 1.0))
    lib.set_material_instance_vector_parameter_value(mic, "AccentColor", unreal.LinearColor(acc[0], acc[1], acc[2], 1.0))
    lib.set_material_instance_scalar_parameter_value(mic, "Roughness", rough)
    lib.set_material_instance_scalar_parameter_value(mic, "Metallic", metal)
    lib.set_material_instance_scalar_parameter_value(mic, "Glow", glow)
    lib.set_material_instance_scalar_parameter_value(mic, "Detail", detail)
    lib.set_material_instance_scalar_parameter_value(mic, "Tile", tile)
    if texs:
        lib.set_material_instance_texture_parameter_value(mic, "NormalTex", texs[0])
        lib.set_material_instance_texture_parameter_value(mic, "RoughTex", texs[1])
    lib.update_material_instance(mic)
    eal.save_asset(full)
    instances.append(mic)


# ------------------------------------------------------------------------------------------------ meshes
def commit(name, m):
    path = "%s/SM_%s" % (PATH, name)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    flip = mapkit_b._winding_flip()
    dm = unreal.DynamicMesh()
    for slot in range(len(SLOTS)):
        tris = [(t, mid) for t, mid in zip(m.t, m.m) if mid == slot]
        if not tris:
            raise RuntimeError("slot %d has no triangles" % slot)
        remap = {}
        verts, norms, uvs, idx = [], [], [], []
        for (a, b, c), _ in tris:
            tri = []
            for vi in (a, b, c):
                if vi not in remap:
                    remap[vi] = len(verts)
                    verts.append(unreal.Vector(*m.v[vi]))
                    norms.append(unreal.Vector(*m.n[vi]))
                    uvs.append(unreal.Vector2D(m.uv[vi][0], m.uv[vi][1]))
                tri.append(remap[vi])
            idx.append(unreal.IntVector(tri[0], tri[2], tri[1]) if flip else unreal.IntVector(*tri))
        buf = unreal.GeometryScriptSimpleMeshBuffers()
        buf.set_editor_property("vertices", verts)
        buf.set_editor_property("normals", norms)
        buf.set_editor_property("uv0", uvs)
        buf.set_editor_property("triangles", idx)
        unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dm, buf, slot)
    nopts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    nopts.set_editor_property("enable_recompute_normals", False)
    nopts.set_editor_property("enable_recompute_tangents", True)
    nopts.set_editor_property("collision_mode", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    res = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, path, nopts)
    sm = res[0] if isinstance(res, tuple) else res
    if sm is None:
        raise RuntimeError("could not create " + path)
    sm = eal.load_asset(path)
    n_slots = len(sm.static_materials)
    log("%s slots=%d verts=%d tris=%d" % (name, n_slots, len(m.v), len(m.t)))
    for i, (slot_name, mic) in enumerate(zip([s[0] for s in SLOTS], instances)):
        if i < n_slots:
            sm.set_material(i, mic)
    eal.save_loaded_asset(sm)
    return sm


commit("IARifle_FP", mw.build_rifle(1))
commit("IARifle_TP", mw.build_rifle(0))
b = eal.load_asset(PATH + "/SM_IARifle_FP").get_bounds()
log("FP bounds origin=%s extent=%s" % (b.origin, b.box_extent))
unreal.log("WEAPON_DONE")
