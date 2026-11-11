"""DM-Forge: a volcanic foundry hall around a lava pit. Medium arena (4-8 players).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_forge.py" -unattended -nullrhi -nosplash

Layout: a square floor with a lava pit in the middle (kill height below the floor), two cross bridges and a central
island, a gantry ring at z=450 with four balconies over the pit. Ramps lead up to the gantry; jump pads on the island
throw players straight onto the balconies. Falling into the lava kills.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
from mapkit import MapBuilder

m = MapBuilder("/Game/Maps/DM-Forge")
rng = random.Random(61)

basalt = m.material("MI_ForgeBasalt", (0.07, 0.065, 0.07), 0.8)
plate = m.material("MI_ForgePlate", (0.15, 0.14, 0.15), 0.45)
iron = m.material("MI_ForgeIron", (0.22, 0.20, 0.21), 0.4)
rust = m.material("MI_ForgeRust", (0.35, 0.15, 0.07), 0.7)
hazard_y = m.material("MI_ForgeHazardY", (0.75, 0.55, 0.05), 0.5)
hazard_k = m.material("MI_ForgeHazardK", (0.04, 0.04, 0.04), 0.5)
brick = m.material("MI_ForgeBrick", (0.22, 0.10, 0.07), 0.9)
lava = m.glow("MI_ForgeLava", (1.0, 0.22, 0.02), 0.8)
ember = m.glow("MI_ForgeEmber", (1.0, 0.40, 0.06), 0.9)
crack = m.glow("MI_ForgeCrack", (1.0, 0.15, 0.02), 1.2)
hot = m.glow("MI_ForgeHot", (1.0, 0.50, 0.12), 1.4)

ORANGE, RED = (1.0, 0.45, 0.12), (1.0, 0.18, 0.05)
_pl = m.point_light
m.point_light = lambda label, loc, rgb, intensity, radius: _pl(label, loc, rgb, intensity * 0.11, radius)

H = 2600.0            # half size of the hall
PIT = 900.0           # half size of the lava pit
CEIL = 1500.0
GZ = 450.0            # gantry height


def R(k, x, y):
    """Rotates a point by k * 90 degrees around the center."""
    for _ in range(k % 4):
        x, y = -y, x
    return x, y


# ---------------------------------------------------------------- shell
m.box("Floor_N", 0, (H + PIT) / 2, -50, H * 2, H - PIT, 100, mat=plate)
m.box("Floor_S", 0, -(H + PIT) / 2, -50, H * 2, H - PIT, 100, mat=plate)
m.box("Floor_E", (H + PIT) / 2, 0, -50, H - PIT, PIT * 2, 100, mat=plate)
m.box("Floor_W", -(H + PIT) / 2, 0, -50, H - PIT, PIT * 2, 100, mat=plate)
m.box("Ceiling", 0, 0, CEIL + 50, H * 2 + 400, H * 2 + 400, 100, mat=basalt)
for k in range(4):
    x, y = R(k, 0, H + 150)
    m.box("Wall_%d" % k, x, y, CEIL / 2 - 100, (H * 2 + 600) if k % 2 == 0 else 300, 300 if k % 2 == 0 else (H * 2 + 600),
          CEIL + 200, mat=basalt)

# lava below the floor level (no collision) and the pit walls
m.box("Lava", 0, 0, -130, PIT * 2, PIT * 2, 10, mat=lava, solid=False)
m.box("LavaDeep", 0, 0, -400, PIT * 2, PIT * 2, 10, mat=lava, solid=False)
for k in range(4):
    x, y = R(k, 0, PIT + 10)
    m.box("PitWall_%d" % k, x, y, -300, PIT * 2 if k % 2 == 0 else 20, 20 if k % 2 == 0 else PIT * 2, 500, mat=basalt,
          solid=False)
m.point_light("LavaLight", (0, 0, -60), RED, 400.0, 3200.0)
for i, (x, y) in enumerate([(-450, -450), (450, -450), (-450, 450), (450, 450)]):
    m.point_light("LavaLightC_%d" % i, (x, y, 80), ORANGE, 150.0, 1600.0)

# hazard stripes on the pit rim
for k in range(4):
    for i in range(-9, 10):
        a, b = R(k, i * 100.0, PIT + 40)
        m.box("Hazard", a, b, 1.5, 100 if k % 2 == 0 else 60, 60 if k % 2 == 0 else 100, 3,
              mat=hazard_y if i % 2 == 0 else hazard_k, solid=False)

# ---------------------------------------------------------------- bridges and island
m.box("Island", 0, 0, -20, 900, 900, 40, mat=iron)
m.box("IslandTrim", 0, 0, 1, 700, 700, 3, mat=rust, solid=False)
for k in (0, 1):
    x, y = R(k, 0, 0)
    m.box("Bridge_%d" % k, 0, 0, -20, 2000 if k == 0 else 380, 380 if k == 0 else 2000, 40, mat=iron)
    for s in (-1, 1):
        px, py = (0, s * 190) if k == 0 else (s * 190, 0)
        m.box("BridgeGlow_%d_%d" % (k, s), px, py, -2, 2000 if k == 0 else 14, 14 if k == 0 else 2000, 6, mat=ember,
              solid=False)
for (x, y) in ((-440, -440), (440, -440), (-440, 440), (440, 440)):  # furnace pillars on the island
    m.column("IslandPillar", x, y, 0, 320, 110, mat=iron)
    m.column("IslandPillarGlow", x, y, 60, 90, 124, mat=hot, solid=False)

# ---------------------------------------------------------------- gantry ring and balconies
RING_IN, RING_OUT = 2150.0, H
for k in range(4):
    x, y = R(k, 0, (RING_IN + RING_OUT) / 2)
    horiz = k % 2 == 0
    side_len = H * 2 if horiz else H * 2 - 2 * (RING_OUT - RING_IN)
    m.box("Gantry_%d" % k, x, y, GZ - 20, side_len if horiz else (RING_OUT - RING_IN),
          (RING_OUT - RING_IN) if horiz else side_len, 40, mat=iron)
    # struts under the gantry
    for i in range(-4, 5):
        a, b = R(k, i * 550.0, RING_IN + 40)
        m.box("Strut", a, b, GZ / 2 - 20, 60, 60, GZ - 40, mat=basalt)
    a, b = R(k, 0, RING_IN - 2)
    m.box("GantryGlow_%d" % k, a, b, GZ - 12, (H * 2) if horiz else 8, 8 if horiz else (H * 2), 8, mat=ember, solid=False)

    # balcony over the pit
    bx, by = R(k, 0, 1850)
    m.box("Balcony_%d" % k, bx, by, GZ - 20, 800 if horiz else 700, 700 if horiz else 800, 40, mat=iron)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = R(k, sx * 330, 1850 + sy * 300)
            m.column("BalconyPost", px, py, 0, GZ - 40, 60, mat=basalt)
    a, b = R(k, 0, 1850 - 345)
    m.box("BalconyRail_%d" % k, a, b, GZ + 45, 700 if horiz else 12, 12 if horiz else 700, 90, mat=iron)
    a, b = R(k, 0, 1850 - 359)
    m.box("BalconyGlow_%d" % k, a, b, GZ - 12, 800 if horiz else 8, 8 if horiz else 800, 8, mat=lava, solid=False)

    # ramp from the floor up to the gantry, along the wall
    p0 = R(k, -1200, 700)        # the ramp runs straight into the front edge of the gantry
    p1 = R(k, -1200, RING_IN)
    m.slope("Ramp_%d" % k, (p0[0], p0[1], 0), (p1[0], p1[1], GZ), 380, mat=plate)
    # a jump pad on the island sends the player to the balcony of this side
    px, py = R(k, 330, 330)
    tx, ty = R(k, 0, 1850)
    m.jump_pad("BalconyPad_%d" % k, px, py, 0, (tx, ty, GZ), color=(1.0, 0.45, 0.1), apex_extra=170.0)

# ---------------------------------------------------------------- towers, props, cover
for k in range(4):
    x, y = R(k, 2250, 2250)
    m.column("Tower_%d" % k, x, y, 0, CEIL, 420, mat=brick)
    m.column("TowerBase_%d" % k, x, y, 0, 120, 500, mat=iron)
    m.column("TowerMouth_%d" % k, x, y, 100, 260, 440, mat=hot, solid=False)
    m.point_light("TowerLight_%d" % k, R(k, 1950, 1950) + (200,), ORANGE, 180.0, 2200.0)
    for j in range(3):
        m.column("TowerBand_%d_%d" % (k, j), x, y, 400 + j * 350, 440 + j * 350, 450, mat=iron, solid=False)

# crates and anvils as cover on the open floor
cover = [(-1700, -1800, 20), (1700, 1800, 70), (-1900, 1500, 0), (1900, -1500, 50), (0, -1700, 0), (0, 1700, 90),
         (-1750, 0, 90), (1750, 0, 0), (-1300, -400, 30), (1300, 400, 60)]
for i, (x, y, yaw) in enumerate(cover):
    m.box("Crate_%d" % i, x, y, 70, 260, 200, 140, yaw=yaw, mat=rust if i % 2 else iron)
    m.box("CrateGlow_%d" % i, x, y, 143, 220, 170, 6, yaw=yaw, mat=ember, solid=False)

# overhead: chain, crucible and pipes
for dx in (-120, 120):
    m.column("Chain", dx, 0, 900, CEIL, 18, mat=iron, solid=False)
m.column("Crucible", 0, 0, 760, 900, 520, mat=hot, solid=False)
m.column("CrucibleBand", 0, 0, 740, 780, 560, mat=iron, solid=False)
m.point_light("CrucibleLight", (0, 0, 700), ORANGE, 300.0, 3000.0)
for i in range(-4, 5):
    m.box("Pipe_X", i * 520, 0, CEIL - 120, 80, H * 2, 80, mat=iron, solid=False)
for i in (-1700, -900, 900, 1700):
    m.box("Pipe_Y", 0, i, CEIL - 260, H * 2, 90, 90, mat=rust, solid=False)

# wall decoration: glowing lava cracks and slag falls
for k in range(4):
    for i in range(14):
        a, b = R(k, rng.uniform(-2300, 2300), H - 6)
        h = rng.uniform(200, 700)
        m.box("Crack", a, b, rng.uniform(550, 1300), 18 if k % 2 == 0 else 8, 8 if k % 2 == 0 else 18, h, mat=crack,
              solid=False)
    for x in (-1500, 1500):
        a, b = R(k, x, H - 30)
        m.box("SlagFall", a, b, 600, 160 if k % 2 == 0 else 30, 30 if k % 2 == 0 else 160, 1200, mat=lava, solid=False)
        a, b = R(k, x, H - 300)
        m.point_light("SlagLight", (a, b, 400), RED, 120.0, 1600.0)

# ---------------------------------------------------------------- spawns
m.auto_starts(12, (-2450, 2450), (-2450, 2450), [0, 450], step=120.0, seed=5, min_sep=500.0)
m.check_starts()

m.post(exposure_bias=-0.2, bloom=0.4)
m.fog(rgb=(0.25, 0.08, 0.04), density=0.003, falloff=0.2, start=300)
m.finish(kill_z=-150)
