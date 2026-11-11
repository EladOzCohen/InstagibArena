"""Imports the map pictures in Tools/MapThumbs/<MapName>.png as textures /Game/UI/MapThumbs/T_<MapName>.

Made to be run again and again: existing textures are replaced. Run through Tools/make_thumbnails.ps1, or by hand:

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/import_thumbnails.py" -unattended -nullrhi -nosplash

The game loads these textures by path (see IAMapPreview.cpp); /Game/UI is listed in Config/DefaultGame.ini so that
packaged builds include them.
"""

import os
import unreal

PROJECT_DIR = unreal.SystemLibrary.get_project_directory()
SOURCE = os.path.join(PROJECT_DIR, "Tools", "MapThumbs")
DEST = "/Game/UI/MapThumbs"

tasks = []
paths = []

for f in sorted(os.listdir(SOURCE)) if os.path.isdir(SOURCE) else []:
    if not f.lower().endswith(".png"):
        continue
    stem = os.path.splitext(f)[0]
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SOURCE, f)
    task.destination_path = DEST
    task.destination_name = "T_" + stem
    task.replace_existing = True
    task.automated = True
    task.save = False
    tasks.append(task)
    paths.append(DEST + "/T_" + stem)

if tasks:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

count = 0
for path in paths:
    texture = unreal.EditorAssetLibrary.load_asset(path)
    if not texture:
        unreal.log_error("THUMB_IMPORT_MISSING " + path)
        continue
    # A flat picture for the user interface: no mip maps, no streaming, no compression artefacts on the edges.
    texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property("never_stream", True)
    texture.set_editor_property("srgb", True)
    unreal.EditorAssetLibrary.save_asset(path)
    unreal.log("THUMB_IMPORTED %s" % path)
    count += 1

unreal.log("THUMB_IMPORT_DONE %d textures" % count)
