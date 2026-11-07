"""Builds the MainMenu backdrop level: a lit stage, a few props and a camera.

Run headless from the project folder:
  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_menu.py" -unattended -nullrhi -nosplash
"""

import unreal

MAP_PATH = "/Game/Maps/MainMenu"

level_lib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_lib = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor_lib = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
cylinder = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")


def prop(label, mesh, loc, scale, rot=(0, 0, 0)):
    actor = actor_lib.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*loc),
        unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor


def spawn(cls, label, loc=(0, 0, 0), rot=(0, 0, 0)):
    actor = actor_lib.spawn_actor_from_class(
        cls, unreal.Vector(*loc), unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    actor.set_actor_label(label)
    return actor


import os
import sys

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit

mapkit.begin_level(MAP_PATH)

# Stage.
prop("Floor", cube, (0, 0, -50), (60, 60, 1))
prop("Back_Wall", cube, (1800, 0, 400), (1, 40, 10))
prop("Pillar_L", cylinder, (900, -700, 250), (1.6, 1.6, 5))
prop("Pillar_R", cylinder, (900, 700, 250), (1.6, 1.6, 5))
prop("Block_A", cube, (1200, -250, 100), (3, 3, 2), (0, 0, 25))
prop("Block_B", cube, (1100, 300, 60), (2, 2, 1.2), (0, 0, -15))
prop("Ramp", cube, (500, 0, 80), (6, 4, 0.4), (0, 15, 0))

# Lighting.
spawn(unreal.DirectionalLight, "Sun", (0, 0, 1500), (0, -35, -40))
spawn(unreal.SkyAtmosphere, "SkyAtmosphere")
sky = spawn(unreal.SkyLight, "SkyLight", (0, 0, 1200))
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("real_time_capture", True)
spawn(unreal.ExponentialHeightFog, "Fog", (0, 0, 100))

# The menu controller looks through this camera.
spawn(unreal.CameraActor, "MenuCamera", (-500, 450, 260), (0, -6, -22))

# This level uses the menu game mode instead of the match game mode.
world = editor_lib.get_editor_world()
menu_mode = unreal.load_class(None, "/Script/InstagibArena.IAMenuGameMode")
world.get_world_settings().set_editor_property("default_game_mode", menu_mode)

level_lib.save_current_level()
unreal.log("MAKEMAP_DONE %s gamemode=%s" % (MAP_PATH, menu_mode.get_name() if menu_mode else None))
