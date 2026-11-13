"""Imports the sky panoramas and builds the sky dome assets (run in the editor commandlet, see docs/DEVELOPMENT.md section 18).

    powershell -NoProfile -ExecutionPolicy Bypass -File Tools\\run_ue.ps1 -Script Tools\\import_skies.py -Grep "SKIES"

What it makes (everything under /Game/Sky, which maps reference, so it is cooked with them):
  T_Sky_<look>   TextureCube from the prepared panorama of Tools/fetch_hdri.py (long-lat HDR -> cube map by the editor's importer).
                 BC6H (TC_HDR_Compressed), no streaming, mips, 512 px faces: about 2 MB each in the game.
  M_IASky        unlit sky material: samples the cube map with the view direction. Parameters:
                   Cube (texture), Rotation (yaw in degrees, the sky turns like an actor with that yaw), Brightness, Tint.
                 "Is Sky" (drawn after everything else, never covers geometry), two sided, no lighting.
  SM_SkyDome     the engine's sphere copied into the project (so that no Engine-only asset is referenced), scaled by maplooks.

It also prints the table (sun direction, sun colour, horizon colour per look) that is kept in Tools/maplooks.py (HDRI).
Existing assets are kept unless IA_SKY_FORCE=1 (re-imports the textures and rebuilds the material).
"""

import json
import os
import sys

import unreal

TOOLS_DIR = os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import fetch_hdri as fh  # noqa: E402

SKY_DIR = "/Game/Sky"
MATERIAL = SKY_DIR + "/M_IASky"
DOME = SKY_DIR + "/SM_SkyDome"
FORCE = os.environ.get("IA_SKY_FORCE") == "1"

eal = unreal.EditorAssetLibrary
lib = unreal.MaterialEditingLibrary


def _import_cube(look):
    meta = fh.fetch(look)
    path = "%s/T_Sky_%s" % (SKY_DIR, look)
    if eal.does_asset_exist(path) and not FORCE:
        return eal.load_asset(path), meta
    src = os.path.join(fh.cache_dir(), look + ".hdr")
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", SKY_DIR)
    task.set_editor_property("destination_name", "T_Sky_" + look)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = eal.load_asset(path)
    if tex is None:
        raise RuntimeError("sky import failed: " + src)
    if not isinstance(tex, unreal.TextureCube):
        raise RuntimeError("%s was imported as %s, not as a cube map" % (look, tex.get_class().get_name()))
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_HDR_COMPRESSED)
    tex.set_editor_property("srgb", False)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_SKYBOX)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("compression_no_alpha", True)
    tex.set_editor_property("max_texture_size", 0)
    eal.save_asset(path)
    return tex, meta


def _node(mat, cls, x, y, **props):
    e = lib.create_material_expression(mat, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def _link(src, dst, input_name, out=""):
    if not lib.connect_material_expressions(src, out, dst, input_name):
        raise RuntimeError("could not connect %s -> %s.%s" % (src.get_name(), dst.get_name(), input_name))


SKY_DIR_HLSL = """
float3 d = normalize(V);
float a = radians(Yaw);
float s = sin(a);
float c = cos(a);
return float3(c * d.x + s * d.y, -s * d.x + c * d.y, d.z);
"""


def build_material(default_cube):
    if eal.does_asset_exist(MATERIAL):
        if not FORCE:
            return eal.load_asset(MATERIAL)
        eal.delete_asset(MATERIAL)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_IASky", SKY_DIR, unreal.Material,
                                                                  unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("is_sky", True)

    wpos = _node(mat, unreal.MaterialExpressionWorldPosition, -1100, 0)
    cam = _node(mat, unreal.MaterialExpressionCameraPositionWS, -1100, 150)
    sub = _node(mat, unreal.MaterialExpressionSubtract, -900, 50)
    _link(wpos, sub, "A")
    _link(cam, sub, "B")
    rot = _node(mat, unreal.MaterialExpressionScalarParameter, -900, 250, parameter_name="Rotation", default_value=0.0)
    rot.set_editor_property("group", "Sky")

    c = _node(mat, unreal.MaterialExpressionCustom, -650, 80)
    ci_v, ci_y = unreal.CustomInput(), unreal.CustomInput()
    ci_v.set_editor_property("input_name", "V")
    ci_y.set_editor_property("input_name", "Yaw")
    c.set_editor_property("description", "SkyDirection")
    c.set_editor_property("code", SKY_DIR_HLSL)
    c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    c.set_editor_property("inputs", [ci_v, ci_y])
    _link(sub, c, "V")
    _link(rot, c, "Yaw")

    cube = _node(mat, unreal.MaterialExpressionTextureSampleParameterCube, -400, 80, parameter_name="Cube")
    cube.set_editor_property("texture", default_cube)
    cube.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    cube.set_editor_property("group", "Sky")
    _link(c, cube, "UVs")

    bright = _node(mat, unreal.MaterialExpressionScalarParameter, -400, 300, parameter_name="Brightness", default_value=1.0)
    bright.set_editor_property("group", "Sky")
    tint = _node(mat, unreal.MaterialExpressionVectorParameter, -400, 400, parameter_name="Tint",
                 default_value=unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    tint.set_editor_property("group", "Sky")
    m1 = _node(mat, unreal.MaterialExpressionMultiply, -150, 120)
    _link(cube, m1, "A", "RGB")
    _link(tint, m1, "B")
    m2 = _node(mat, unreal.MaterialExpressionMultiply, 50, 160)
    _link(m1, m2, "A")
    _link(bright, m2, "B")
    lib.connect_material_property(m2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(MATERIAL)
    unreal.log("SKIES material built: " + MATERIAL)
    return mat


def build_dome(mat):
    if eal.does_asset_exist(DOME) and not FORCE:
        return eal.load_asset(DOME)
    if eal.does_asset_exist(DOME):
        eal.delete_asset(DOME)
    if not eal.duplicate_asset("/Engine/BasicShapes/Sphere", DOME):
        raise RuntimeError("could not copy the engine sphere")
    mesh = eal.load_asset(DOME)
    mesh.set_material(0, mat)
    eal.save_asset(DOME)
    ext = mesh.get_bounding_box()
    unreal.log("SKIES dome mesh %s bounds %s .. %s" % (DOME, ext.min, ext.max))
    return mesh


def main():
    if not eal.does_directory_exist(SKY_DIR):
        eal.make_directory(SKY_DIR)
    table = {}
    first = None
    for look in fh.SKIES:
        tex, meta = _import_cube(look)
        first = first or tex
        table[look] = {k: meta[k] for k in ("slug", "sun_azimuth", "sun_elevation", "sun_rgb", "horizon_rgb", "zenith_rgb",
                                            "mean_luminance")}
        unreal.log("SKIES %s: %s sun az %.1f el %.1f" % (look, meta["slug"], meta["sun_azimuth"], meta["sun_elevation"]))
    mat = build_material(first)
    build_dome(mat)
    unreal.log("SKIES_TABLE " + json.dumps(table))
    unreal.log("SKIES_DONE")


main()
