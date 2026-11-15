"""Imports the WAV files made by gen_audio.py into the project as sound assets.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/import_audio.py" -unattended -nullrhi -nosplash

Assets end up in /Game/Audio/SFX (S_*) and /Game/Audio/Music (M_*, set to loop).
"""

import os
import unreal

PROJECT_DIR = unreal.SystemLibrary.get_project_directory()
SOURCE = os.path.join(PROJECT_DIR, "Tools", "audio_out")

tasks = []
names = []


def add(folder, filename, asset_name, dest):
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SOURCE, folder, filename)
    task.destination_path = dest
    task.destination_name = asset_name
    task.replace_existing = True
    task.automated = True
    task.save = True
    tasks.append(task)
    names.append((dest + "/" + asset_name, folder == "music"))


# IA_AUDIO_ONLY=flag_ imports only the files whose name starts with one of the comma separated prefixes
# (keeps the other assets untouched in git when only a few sounds were added).
ONLY = [p for p in os.environ.get("IA_AUDIO_ONLY", "").split(",") if p]

for f in sorted(os.listdir(os.path.join(SOURCE, "sfx"))):
    if ONLY and not any(f.startswith(p) for p in ONLY):
        continue
    if f.endswith(".wav"):
        stem = os.path.splitext(f)[0]
        add("sfx", f, "S_" + "".join(p.capitalize() for p in stem.split("_")), "/Game/Audio/SFX")

for f in ([] if ONLY else sorted(os.listdir(os.path.join(SOURCE, "music")))):
    if f.endswith(".wav"):
        stem = os.path.splitext(f)[0]
        add("music", f, "M_" + "".join(p.capitalize() for p in stem.split("_")), "/Game/Audio/Music")

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

for path, is_music in names:
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        unreal.log_error("IMPORT_MISSING " + path)
        continue
    if is_music:
        asset.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_asset(path)
    unreal.log("IMPORTED %s%s" % (path, " (looping)" if is_music else ""))

unreal.log("IMPORT_DONE %d assets" % len(names))
