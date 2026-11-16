"""Imports the procedural space skies (Tools/make_space_sky.py) as cube maps /Game/Sky/T_Sky_space_<name> (editor commandlet):

    powershell -NoProfile -ExecutionPolicy Bypass -File Tools\run_ue.ps1 -Script Tools\import_space_skies.py -Grep "SPACESKY"

The sky dome material (M_IASkySun) and the dome mesh already exist (Tools/import_skies.py); maplooks.py picks the cube map by the look's hdri name.
"""

import os
import sys

import unreal

TOOLS_DIR = os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import fetch_hdri as fh  # noqa: E402

SKY_DIR = "/Game/Sky"
eal = unreal.EditorAssetLibrary

for look in ("space_orbital", "space_derelict", "space_nexus"):
    path = "%s/T_Sky_%s" % (SKY_DIR, look)
    src = os.path.join(fh.cache_dir(), look + ".hdr")
    if not os.path.exists(src):
        unreal.log_error("SPACESKY missing %s (run Tools/make_space_sky.py)" % src)
        continue
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", SKY_DIR)
    task.set_editor_property("destination_name", "T_Sky_" + look)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = eal.load_asset(path)
    if not isinstance(tex, unreal.TextureCube):
        unreal.log_error("SPACESKY %s was not imported as a cube map" % look)
        continue
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_HDR_COMPRESSED)
    tex.set_editor_property("srgb", False)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_SKYBOX)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("compression_no_alpha", True)
    tex.set_editor_property("max_texture_size", 0)
    eal.save_asset(path)
    unreal.log("SPACESKY imported %s" % path)
unreal.log("SPACESKY_DONE")
