"""DM-Dock: an indoor space-station hangar with mezzanines, a cross bridge, two reactor cores and cargo.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_dock.py" -unattended -nullrhi -nosplash
"""

import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
from mapkit import MapBuilder

m = MapBuilder("/Game/Maps/DM-Dock")

floor = m.material("MI_DockFloor", (0.10, 0.12, 0.16), 0.5)
wall = m.material("MI_DockWall", (0.20, 0.23, 0.30), 0.6)
trim = m.material("MI_DockTrim", (0.95, 0.42, 0.05), 0.5)
cyan = m.material("MI_DockCyan", (0.0, 0.85, 1.0), 0.3)
red = m.material("MI_ContainerRed", (0.60, 0.10, 0.08))
blue = m.material("MI_ContainerBlue", (0.10, 0.22, 0.58))
yellow = m.material("MI_ContainerYellow", (0.82, 0.66, 0.05))
green = m.material("MI_ContainerGreen", (0.10, 0.50, 0.22))
metal = m.material("MI_DockMetal", (0.36, 0.38, 0.42), 0.4)

HX, HY, CEIL = 2800.0, 1300.0, 1300.0
T = 100.0

# ---------------------------------------------------------------- hangar shell
m.box("Floor", 0, 0, -50, HX * 2 + 200, HY * 2 + 200, 100, mat=floor)
m.box("Ceiling", 0, 0, CEIL + 50, HX * 2 + 200, HY * 2 + 200, 100, mat=wall)
m.box("Wall_N", 0, HY + T / 2, CEIL / 2, HX * 2 + 200, T, CEIL + 100, mat=wall)
m.box("Wall_S", 0, -HY - T / 2, CEIL / 2, HX * 2 + 200, T, CEIL + 100, mat=wall)
m.box("Wall_E", HX + T / 2, 0, CEIL / 2, T, HY * 2, CEIL + 100, mat=wall)
m.box("Wall_W", -HX - T / 2, 0, CEIL / 2, T, HY * 2, CEIL + 100, mat=wall)

# Glowing trim strips along the walls (decoration only).
for y in (-HY + 20, HY - 20):
    m.box("TrimStrip", 0, y, 250, HX * 2, 20, 40, mat=trim, solid=False)
    m.box("CyanStrip", 0, y, 1050, HX * 2, 20, 30, mat=cyan, solid=False)

# ---------------------------------------------------------------- mezzanines
MZ_TOP, MZ_T, MZ_W = 450.0, 40.0, 450.0
mz_y = HY - MZ_W / 2
m.box("Mezz_S", 300, -mz_y, MZ_TOP - MZ_T / 2, 4200, MZ_W, MZ_T, mat=metal)   # x from -1800 to 2400
m.box("Mezz_N", -300, mz_y, MZ_TOP - MZ_T / 2, 4200, MZ_W, MZ_T, mat=metal)   # x from -2400 to 1800
m.slope("MezzRamp_S", (-2700, -mz_y, 0), (-1800, -mz_y, MZ_TOP), 400, mat=trim)
m.slope("MezzRamp_N", (2700, mz_y, 0), (1800, mz_y, MZ_TOP), 400, mat=trim)
for x in range(-1800, 2401, 600):
    m.box("MezzSupportS", x, -mz_y, MZ_TOP / 2 - MZ_T, 80, 80, MZ_TOP - MZ_T, mat=wall)
for x in range(-2400, 1801, 600):
    m.box("MezzSupportN", x, mz_y, MZ_TOP / 2 - MZ_T, 80, 80, MZ_TOP - MZ_T, mat=wall)

# Cross bridge between the two mezzanines.
m.box("Bridge", 0, 0, MZ_TOP - MZ_T / 2, 400, HY * 2 - MZ_W * 2 + 20, MZ_T, mat=metal)
m.box("BridgeGlow", 0, 0, MZ_TOP - MZ_T - 20, 80, HY * 2 - MZ_W * 2, 20, mat=cyan, solid=False)

# ---------------------------------------------------------------- reactor cores
for sx in (-1, 1):
    m.box("CoreBase", sx * 1100, 0, 50, 900, 900, 100, mat=metal)
    m.column("CoreShaft", sx * 1100, 0, 100, CEIL, 450, mat=wall)
    m.column("CoreGlow", sx * 1100, 0, 500, 900, 470, mat=cyan, solid=False)

# ---------------------------------------------------------------- cargo
containers = [
    (-1800, 250, 0, red), (-1500, -350, 90, blue), (1600, -250, 0, green), (1900, 350, 90, yellow),
    (450, 700, 0, blue), (-500, -650, 0, red), (-100, 650, 90, green), (700, -700, 90, yellow),
]
for i, (x, y, yaw, mat) in enumerate(containers):
    m.box("Container_%d" % i, x, y, 120, 600, 240, 240, yaw=yaw, mat=mat)
    if i % 2 == 0:
        m.box("ContainerTop_%d" % i, x + 60, y, 360, 480, 240, 240, yaw=yaw, mat=mat)

# ---------------------------------------------------------------- spawns
spawns = [(sx * 2400.0, sy * 500.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
spawns += [(sx * 1000.0, sy * 750.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
m.face_center_starts(spawns)
m.starts([(-700, -mz_y, MZ_TOP, 90), (700, mz_y, MZ_TOP, 270)])

# ---------------------------------------------------------------- light (indoor)
for i, x in enumerate(range(-2400, 2401, 800)):
    for side in (-1, 1):
        warm = (i + (0 if side > 0 else 1)) % 2 == 0
        rgb = (1.0, 0.6, 0.3) if warm else (0.5, 0.85, 1.0)
        m.point_light("CeilingLight", (x, side * 550, CEIL - 120), rgb, 35.0, 1500.0)
for sx in (-1, 1):
    m.point_light("CoreLight", (sx * 1100, 0, 600), (0.2, 0.9, 1.0), 60.0, 1600.0)

# No sky light here: the hangar is closed, so it would only render black.

m.finish(kill_z=-1500)
