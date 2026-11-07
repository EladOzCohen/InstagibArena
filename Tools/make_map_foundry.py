"""Builds the DM-Foundry blockout map.

Run headless from the project folder:
  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_foundry.py" -unattended -nullrhi -nosplash

Units are Unreal units (1 uu = 1 cm). The floor top is at z = 0.
"""

import math
import unreal

MAP_PATH = "/Game/Maps/DM-Foundry"
HALF = 2400.0          # inner half-size of the arena
WALL_HEIGHT = 1400.0
RING_Z = 450.0         # top surface of the catwalk ring
RING_WIDTH = 350.0
TOWER_Z = 300.0        # top surface of the central platform

level_lib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_lib = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")

count = {"boxes": 0}


def box(label, cx, cy, cz, sx, sy, sz, yaw=0.0, pitch=0.0):
    """A solid box. Position is the center, size is the full extent in uu."""
    actor = actor_lib.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(cx, cy, cz),
        unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw),
    )
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    count["boxes"] += 1
    return actor


def ramp(label, x0, y0, x1, y1, z_top, width, thickness=40.0):
    """A ramp whose low end is at (x0, y0, 0) and high end at (x1, y1, z_top)."""
    dx, dy = x1 - x0, y1 - y0
    run = math.hypot(dx, dy)
    length = math.hypot(run, z_top)
    pitch = math.degrees(math.atan2(z_top, run))
    yaw = math.degrees(math.atan2(dy, dx))
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    return box(label, cx, cy, z_top / 2.0 - thickness / 2.0 * math.cos(math.radians(pitch)),
               length, width, thickness, yaw=yaw, pitch=pitch)


def spawn(cls, label, loc=(0, 0, 0), rot=(0, 0, 0)):
    actor = actor_lib.spawn_actor_from_class(
        cls, unreal.Vector(*loc), unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    actor.set_actor_label(label)
    return actor


# ---------------------------------------------------------------- new level
level_lib.new_level(MAP_PATH)

# ---------------------------------------------------------------- shell
box("Floor", 0, 0, -50, HALF * 2 + 200, HALF * 2 + 200, 100)
t = 100.0
box("Wall_N", 0, HALF + t / 2, WALL_HEIGHT / 2 - 50, HALF * 2 + 200, t, WALL_HEIGHT + 100)
box("Wall_S", 0, -HALF - t / 2, WALL_HEIGHT / 2 - 50, HALF * 2 + 200, t, WALL_HEIGHT + 100)
box("Wall_E", HALF + t / 2, 0, WALL_HEIGHT / 2 - 50, t, HALF * 2, WALL_HEIGHT + 100)
box("Wall_W", -HALF - t / 2, 0, WALL_HEIGHT / 2 - 50, t, HALF * 2, WALL_HEIGHT + 100)

# ---------------------------------------------------------------- catwalk ring
ring_c = HALF - RING_WIDTH / 2
ring_t = 40.0
box("Ring_N", 0, ring_c, RING_Z - ring_t / 2, HALF * 2, RING_WIDTH, ring_t)
box("Ring_S", 0, -ring_c, RING_Z - ring_t / 2, HALF * 2, RING_WIDTH, ring_t)
box("Ring_E", ring_c, 0, RING_Z - ring_t / 2, RING_WIDTH, HALF * 2 - RING_WIDTH * 2, ring_t)
box("Ring_W", -ring_c, 0, RING_Z - ring_t / 2, RING_WIDTH, HALF * 2 - RING_WIDTH * 2, ring_t)

# Pinwheel of ramps from the floor up to the ring.
inner = HALF - RING_WIDTH
ramp("RingRamp_N", 1000, 750, 1000, inner, RING_Z, 400)
ramp("RingRamp_E", 750, -1000, inner, -1000, RING_Z, 400)
ramp("RingRamp_S", -1000, -750, -1000, -inner, RING_Z, 400)
ramp("RingRamp_W", -750, 1000, -inner, 1000, RING_Z, 400)

# ---------------------------------------------------------------- central tower
box("Tower_Platform", 0, 0, TOWER_Z - 20, 900, 900, 40)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("Tower_Leg", sx * 400, sy * 400, TOWER_Z / 2 - 20, 100, 100, TOWER_Z - 40)
ramp("TowerRamp_E", 1350, 0, 450, 0, TOWER_Z, 400)
ramp("TowerRamp_W", -1350, 0, -450, 0, TOWER_Z, 400)
ramp("TowerRamp_N", 0, 1350, 0, 450, TOWER_Z, 400)
ramp("TowerRamp_S", 0, -1350, 0, -450, TOWER_Z, 400)

# ---------------------------------------------------------------- cover
for sx in (-1, 1):
    for sy in (-1, 1):
        box("Pillar", sx * 1700, sy * 1700, 450, 200, 200, 900)
        box("Crate", sx * 1500, sy * 400, 75, 300, 300, 150)
        box("CrateB", sx * 400, sy * 1550, 75, 300, 300, 150)

# ---------------------------------------------------------------- spawn points
starts = []
for sx in (-1, 1):
    for sy in (-1, 1):
        starts.append((sx * 1900, sy * 1900))
starts += [(0, 1750), (0, -1750), (1750, 0), (-1750, 0)]
for i, (x, y) in enumerate(starts):
    yaw = math.degrees(math.atan2(-y, -x))
    spawn(unreal.PlayerStart, "PlayerStart_%d" % i, (x, y, 110), (0, 0, yaw))

# ---------------------------------------------------------------- lighting
spawn(unreal.DirectionalLight, "Sun", (0, 0, 2000), (0, -50, 35))
spawn(unreal.SkyAtmosphere, "SkyAtmosphere")
sky = spawn(unreal.SkyLight, "SkyLight", (0, 0, 1500))
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("real_time_capture", True)
spawn(unreal.ExponentialHeightFog, "Fog", (0, 0, 200))

# ---------------------------------------------------------------- save
level_lib.save_current_level()
unreal.log("MAKEMAP_DONE %s boxes=%d starts=%d" % (MAP_PATH, count["boxes"], len(starts)))
