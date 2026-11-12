"""Builds small throwaway test maps, one per light and shading look, to judge a look with screenshots.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools\\make_looks.py -unattended -nullrhi -nosplash -nopause

Environment (optional):
  IA_LOOKS   comma separated look names (default: all, see maplooks.LOOKS)
  IA_PREFIX  map name prefix (default LookTest), maps are saved as /Game/Dev/Looks/<prefix>_<look>
  IA_OVER    overrides for every look as key=value pairs separated by ";" (example: "ev=4.5;bloom=0.1")

The maps hold grey/colour reference boxes, spheres from matte to mirror, walls and a floor, so that exposure, shadow
depth, ambient colour, fog and shininess can be judged. They are NOT part of the game (do not list or commit them).
Look at them with a showroom (characters in front of the camera):

  UnrealEditor.exe InstagibArena.uproject /Game/Dev/Looks/LookTest_day_clear -game -windowed -ResX=1600 -ResY=900
     -IAShowroom=300,0,100,180 -IAShotCam=-350,0,170,-3,0 -IAShotDelay=14 -IAShotName=look_day_clear
"""

import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import maplooks  # noqa: E402

FOLDER = "/Game/Dev/Looks"
PREFIX = os.environ.get("IA_PREFIX", "LookTest")
NAMES = [n for n in os.environ.get("IA_LOOKS", ",".join(maplooks.available())).split(",") if n]
OVER = {}
for pair in [p for p in os.environ.get("IA_OVER", "").split(";") if "=" in p]:
    k, v = pair.split("=", 1)
    try:
        OVER[k.strip()] = float(v)
    except ValueError:
        OVER[k.strip()] = v.strip()


def mat(name, rgb, roughness=0.85, metallic=0.0):
    full = "%s/MI_%s" % (FOLDER, name)
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        return unreal.EditorAssetLibrary.load_asset(full)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mic = tools.create_asset("MI_" + name, FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    lib = unreal.MaterialEditingLibrary
    lib.set_material_instance_parent(mic, unreal.EditorAssetLibrary.load_asset("/Game/Characters/M_IABody"))
    lib.set_material_instance_vector_parameter_value(mic, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    lib.set_material_instance_scalar_parameter_value(mic, "Roughness", roughness)
    lib.set_material_instance_scalar_parameter_value(mic, "Metallic", metallic)
    lib.set_material_instance_scalar_parameter_value(mic, "Glow", 0.0)
    lib.update_material_instance(mic)
    unreal.EditorAssetLibrary.save_asset(full)
    return mic


def build(look):
    path = "%s/%s_%s" % (FOLDER, PREFIX, look)
    m = mapkit.MapBuilder(path)
    sphere = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere.Sphere")
    floor = mat("Floor", (0.30, 0.30, 0.30))
    wall = mat("Wall", (0.55, 0.55, 0.55))
    # Ground and walls: a floor, a back wall (x), a side wall (y) with a window-sized gap for the sky.
    m.box("Floor", 0, 0, -50, 7000, 7000, 100, mat=floor)
    m.box("Wall_Back", 3000, 0, 600, 100, 7000, 1200, mat=wall)
    m.box("Wall_Side", 0, -3000, 600, 7000, 100, 1200, mat=wall)
    # A shaded corridor to judge the shadow side: a roof slab with a pillar.
    m.box("Roof", 900, 2000, 400, 900, 900, 60, mat=wall)
    m.box("Pillar", 900, 1500, 200, 80, 80, 400, mat=wall)
    # Reference boxes: 18 % grey, white, black, red, green, blue, gold.
    refs = [("White", (0.80, 0.80, 0.80)), ("Grey18", (0.18, 0.18, 0.18)), ("Black", (0.04, 0.04, 0.04)),
            ("Red", (0.55, 0.06, 0.05)), ("Green", (0.08, 0.45, 0.08)), ("Blue", (0.06, 0.12, 0.60)),
            ("Sand", (0.55, 0.42, 0.25))]
    for i, (name, rgb) in enumerate(refs):
        m.box("Ref_" + name, 1500, -1050 + i * 350, 100, 160, 160, 200, mat=mat("Ref" + name, rgb))
    # Spheres: matte -> glossy (how wet does it look?).
    for i, rough in enumerate((0.95, 0.7, 0.45, 0.2)):
        m._place("Sphere_%d" % i, sphere, (1000, -600 + i * 400, 60), (1.2, 1.2, 1.2), 0, 0,
                 mat("Sphere%d" % i, (0.4, 0.4, 0.42), rough), True)
    m._place("Sphere_Metal", sphere, (1000, 1000, 60), (1.2, 1.2, 1.2), 0, 0, mat("SphereMetal", (0.8, 0.7, 0.45), 0.35, 1.0), True)
    m.starts([(-2800, 0, 0, 0), (-2800, 400, 0, 0)])
    m.look(look, **OVER)
    # one accent light, to judge the accent light helper
    m.accent_light("AccentTest", (1400, 1800, 250), (1.0, 0.45, 0.15), candela=40.0, radius=500.0)
    m.finish(kill_z=-2000)


for name in NAMES:
    build(name)
unreal.log("LOOKS_DONE %s" % ",".join(NAMES))
