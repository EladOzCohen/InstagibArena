"""DM-Derelict: a dead starship drifting through a nebula (campaign chapter 4, also CTF / FFA / TDM).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_derelict.py" -unattended -nullrhi -nosplash

Layout (x runs between the bases, centimetres, about 9600 x 4000):
  * the cargo bay (x -2400..2400): a tall hall with a hole in the floor (fall = death) crossed by one walkway at z 450,
    catwalks along both long walls, four ramps (17 degrees) down to the floor, four jump pads, cover crates
  * two low corridors (x +-2400..3300) with ribbed frames and red emergency lights
  * the aft hall (Red, west): the engine room, two engine cores, the flag base in the middle
  * the bridge (Blue, east): a tiered hall with a big window to the nebula, the flag base in the middle
  * hull breaches: openings in the hull closed by glass force fields, the nebula and drifting debris behind them (no collision)
Start tags: Red / Blue for the end halls, 8 untagged starts in the bay.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
from mapkit import MapBuilder  # noqa: E402
from matlib import surface, glass  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Derelict")
rng = random.Random(77)
S = surface
m.look("space_derelict", ev=2.4, ambient_gain=13.0, sky_rgb=(1.0, 0.95, 0.90), saturation=0.68)

floor = S("DiamondPlateDark", albedo=(128, 130, 138), tiling=1.4, metal=0.1, tag="DerFloor2")
hull = S("CorrugatedDark", albedo=(124, 124, 130), metal=0.12, tag="DerHull2")
panel = S("ConcreteDirty", albedo=(122, 126, 134), tiling=2.0, tag="DerPanel")
rust = S("CorrugatedRust", albedo=(120, 70, 46), tag="DerRust")
steel = S("SteelDark", albedo=(130, 134, 144), metal=0.12, tag="DerSteel2")
crate_a = S("ContainerGrey", albedo=(104, 110, 120), tag="DerCrateGrey")
crate_r = S("ContainerRed", albedo=(140, 56, 46), tag="DerCrateRed")
red_floor = S("DiamondPlateDark", albedo=(128, 84, 84), tiling=1.4, metal=0.1, tag="DerRedFloor")
blue_floor = S("DiamondPlateDark", albedo=(84, 98, 130), tiling=1.4, metal=0.1, tag="DerBlueFloor")
gl = glass()
g_red = m.glow("DerGlowRed", (1.0, 0.10, 0.06), 3.0)
g_blue = m.glow("DerGlowBlue", (0.10, 0.30, 1.0), 3.0)
g_teal = m.glow("DerGlowTeal", (0.10, 0.85, 0.80), 3.0)
g_amber = m.glow("DerGlowAmber", (1.0, 0.55, 0.12), 3.0)

_n = [0]


def B(prefix, x0, x1, y0, y1, z0, z1, mat, solid=True, yaw=0.0, pitch=0.0):
    _n[0] += 1
    return m.box("%s_%d" % (prefix, _n[0]), (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), yaw=yaw, pitch=pitch, mat=mat, solid=solid)


def C(prefix, x, y, z0, z1, d, mat, solid=True):
    _n[0] += 1
    return m.column("%s_%d" % (prefix, _n[0]), x, y, z0, z1, d, mat=mat, solid=solid)


BAY_X, BAY_Y, BAY_Z = 2400.0, 2000.0, 1500.0
COR_X, COR_Y, COR_Z = 3300.0, 500.0, 520.0
HALL_X, HALL_Y, HALL_Z = 4800.0, 1500.0, 1000.0
CAT_Z = 450.0

# ---------------------------------------------------------------- the cargo bay: floor with a hole, walls, ceiling with ribs
HOLE_X, HOLE_Y = 800.0, 600.0
B("BayFloor", -BAY_X, BAY_X, HOLE_Y, BAY_Y, -60, 0, floor)
B("BayFloor", -BAY_X, BAY_X, -BAY_Y, -HOLE_Y, -60, 0, floor)
B("BayFloor", -BAY_X, -HOLE_X, -HOLE_Y, HOLE_Y, -60, 0, floor)
B("BayFloor", HOLE_X, BAY_X, -HOLE_Y, HOLE_Y, -60, 0, floor)
for sx in (-1, 1):
    B("HoleEdge", sx * HOLE_X - 15, sx * HOLE_X + 15, -HOLE_Y, HOLE_Y, 0, 30, g_red, solid=False)
for sy in (-1, 1):
    B("HoleEdge", -HOLE_X, HOLE_X, sy * HOLE_Y - 15, sy * HOLE_Y + 15, 0, 30, g_red, solid=False)
    # the long walls with ribs; two hull breaches closed by force fields
    B("BayWall", -BAY_X, BAY_X, min(sy * BAY_Y, sy * (BAY_Y + 100)), max(sy * BAY_Y, sy * (BAY_Y + 100)), -60, BAY_Z, hull)
    for i in range(-5, 6):
        x = i * 440.0
        B("Rib", x - 40, x + 40, min(sy * (BAY_Y - 70), sy * BAY_Y), max(sy * (BAY_Y - 70), sy * BAY_Y), 0, BAY_Z, steel)
for sx in (-1, 1):
    # the end walls of the bay have the corridor openings
    xa, xb = (BAY_X, BAY_X + 100) if sx > 0 else (-BAY_X - 100, -BAY_X)
    B("BayEnd", xa, xb, -BAY_Y - 100, -COR_Y, -60, BAY_Z, hull)
    B("BayEnd", xa, xb, COR_Y, BAY_Y + 100, -60, BAY_Z, hull)
    B("BayEnd", xa, xb, -COR_Y, COR_Y, COR_Z, BAY_Z, hull)
for i in range(-5, 6):
    x = i * 440.0
    B("CeilRib", x - 45, x + 45, -BAY_Y - 100, BAY_Y + 100, BAY_Z - 100, BAY_Z, steel)
B("Ceiling", -BAY_X, BAY_X, -BAY_Y - 100, -900, BAY_Z, BAY_Z + 60, hull)
B("Ceiling", -BAY_X, BAY_X, 900, BAY_Y + 100, BAY_Z, BAY_Z + 60, hull)
B("Ceiling", -BAY_X, -700, -900, 900, BAY_Z, BAY_Z + 60, hull)
B("Ceiling", 700, BAY_X, -900, 900, BAY_Z, BAY_Z + 60, hull)
# the hole in the ceiling above the hole in the floor: the nebula looks in
for sx in (-1, 1):
    B("CeilEdge", min(sx * 700, sx * 760), max(sx * 700, sx * 760), -900, 900, BAY_Z - 10, BAY_Z + 70, rust)
for sy in (-1, 1):
    B("BreachFrame", 1100, 1900, min(sy * (BAY_Y + 40), sy * (BAY_Y + 60)), max(sy * (BAY_Y + 40), sy * (BAY_Y + 60)), 700, 1400, gl)
    B("BreachFrameL", 1090, 1110, sy * (BAY_Y + 50) - 60, sy * (BAY_Y + 50) + 60, 690, 1410, rust, solid=False)
    B("BreachFrameR", 1890, 1910, sy * (BAY_Y + 50) - 60, sy * (BAY_Y + 50) + 60, 690, 1410, rust, solid=False)

# ---------------------------------------------------------------- catwalks: strips along the long walls, a cross walkway over the hole
for sy in (-1, 1):
    y0, y1 = (1550.0, 1950.0) if sy > 0 else (-1950.0, -1550.0)
    B("Catwalk", -2200, 2200, y0, y1, CAT_Z - 40, CAT_Z, floor)
    B("CatRail", -2200, 2200, sy * 1550 - 10, sy * 1550 + 10, CAT_Z, CAT_Z + 110, steel, solid=False)
    B("CatGlow", -2200, 2200, sy * 1550 - 12, sy * 1550 + 12, CAT_Z, CAT_Z + 14, g_amber, solid=False)
    for x in range(-2000, 2001, 800):
        B("CatLeg", x - 30, x + 30, sy * 1750 - 30, sy * 1750 + 30, 0, CAT_Z - 40, steel)
B("CrossWalk", -190, 190, -1950, 1950, CAT_Z - 40, CAT_Z, floor)
for sx in (-1, 1):
    B("CrossRail", sx * 190 - 10, sx * 190 + 10, -1550, 1550, CAT_Z, CAT_Z + 110, steel, solid=False)
    B("CrossGlow", sx * 190 - 12, sx * 190 + 12, -1550, 1550, CAT_Z, CAT_Z + 14, g_amber, solid=False)
# four ramps from the catwalk strips down to the floor (17 degrees)
for sx in (-1, 1):
    for sy in (-1, 1):
        m.slope("Ramp_%d_%d" % (sx, sy), (sx * 1700.0, sy * 1550.0, CAT_Z), (sx * 1700.0, sy * 50.0, 0.0), 360.0, thickness=40.0, mat=floor)
        # the ramps run along y: rotate them with the slope helper (it follows the points)
for sx in (-1, 1):
    for sy in (-1, 1):
        m.jump_pad("CatPad_%d_%d" % (sx, sy), sx * 700.0, sy * 1000.0, 0.0, (sx * 700.0, sy * 1750.0, CAT_Z), color=(1.0, 0.55, 0.15), apex_extra=170.0)

# ---------------------------------------------------------------- cover in the bay
for i, (cx, cy) in enumerate([(-1400, -1100), (-1400, 1100), (1400, -1100), (1400, 1100), (-2000, 0), (2000, 0), (-700, 1300), (700, -1300)]):
    B("Crate", cx - 120, cx + 120, cy - 120, cy + 120, 0, 240, crate_a if i % 2 else crate_r)
    if i % 3 == 1:
        B("CrateTop", cx - 100, cx + 100, cy - 100, cy + 100, 240, 420, crate_r if i % 2 else crate_a)
for x, y, z in [(-300, 900, 0), (300, -900, 0)]:
    B("Wreck", x - 160, x + 160, y - 90, y + 90, z, z + 200, rust, yaw=rng.uniform(-30, 30))

# ---------------------------------------------------------------- the low corridors
for sx in (-1, 1):
    x0, x1 = (BAY_X, COR_X) if sx > 0 else (-COR_X, -BAY_X)
    B("CorFloor", x0, x1, -COR_Y, COR_Y, -60, 0, floor)
    B("CorCeil", x0, x1, -COR_Y - 80, COR_Y + 80, COR_Z, COR_Z + 60, hull)
    for sy in (-1, 1):
        B("CorWall", x0, x1, min(sy * COR_Y, sy * (COR_Y + 80)), max(sy * COR_Y, sy * (COR_Y + 80)), -60, COR_Z + 60, hull)
    for k in range(5):
        x = x0 + (k + 0.5) * (x1 - x0) / 5.0
        B("CorFrame", x - 30, x + 30, -COR_Y, COR_Y, 0, COR_Z, steel, solid=False)
        B("CorLight", x - 18, x + 18, -60, 60, COR_Z - 8, COR_Z, g_red, solid=False)
        m.accent_light("CorLamp_%d_%d" % (sx, k), (x, 0, COR_Z - 60), (1.0, 0.18, 0.12), candela=55.0, radius=900.0)

# ---------------------------------------------------------------- the end halls: aft (Red, engine room) and bridge (Blue)
for sx in (-1, 1):
    x0, x1 = (COR_X, HALL_X) if sx > 0 else (-HALL_X, -COR_X)
    B("HallFloor", x0, x1, -HALL_Y, HALL_Y, -60, 0, blue_floor if sx > 0 else red_floor)
    B("HallCeil", x0, x1, -HALL_Y - 80, HALL_Y + 80, HALL_Z, HALL_Z + 60, hull)
    for sy in (-1, 1):
        B("HallWall", x0, x1, min(sy * HALL_Y, sy * (HALL_Y + 80)), max(sy * HALL_Y, sy * (HALL_Y + 80)), -60, HALL_Z + 60, hull)
    xe = sx * HALL_X
    if sx > 0:
        # the bridge: a big window on the east wall showing the nebula
        B("BridgeSill", HALL_X, HALL_X + 80, -HALL_Y, HALL_Y, -60, 260, hull)
        B("BridgeWindow", HALL_X + 20, HALL_X + 40, -HALL_Y + 80, HALL_Y - 80, 260, HALL_Z, gl)
        for y in (-1500, -750, 0, 750, 1500):
            B("BridgeMullion", HALL_X, HALL_X + 80, y - 35, y + 35, 260, HALL_Z + 60, steel)
        for i, y in enumerate((-1000.0, 0.0, 1000.0)):
            B("Console", 4100, 4500, y - 260, y + 260, 0, 120, steel)
            B("ConsoleScreen", 4150, 4450, y - 240, y + 240, 120, 140, g_teal, solid=False)
    else:
        B("AftWall", -HALL_X - 80, -HALL_X, -HALL_Y, HALL_Y, -60, HALL_Z + 60, hull)
        for y in (-900.0, 900.0):
            C("EngineCore", -4400.0, y, 0, HALL_Z, 520, steel)
            C("EngineRing", -4400.0, y, 300, 340, 560, g_amber, solid=False)
            C("EngineRing", -4400.0, y, 600, 640, 560, g_amber, solid=False)
    fx = sx * 4250.0
    for k in range(2):
        r = 320.0 + k * 90.0
        for j in range(16):
            a = j / 16.0 * 2 * math.pi
            B("BaseRing", fx + math.cos(a) * r - 26, fx + math.cos(a) * r + 26, math.sin(a) * r - 26, math.sin(a) * r + 26, 0, 6, g_blue if sx > 0 else g_red, solid=False)
    for y in (-1000.0, 0.0, 1000.0):
        m.accent_light("HallLamp_%d_%d" % (sx, y), (sx * 4200.0, y, 700.0), (0.3, 0.45, 1.0) if sx > 0 else (1.0, 0.3, 0.2), candela=110.0, radius=1400.0)

# ---------------------------------------------------------------- lights of the bay and drifting debris outside
for x in (-1600.0, 0.0, 1600.0):
    for y in (-1200.0, 1200.0):
        m.accent_light("BayLamp_%d_%d" % (x, y), (x, y, BAY_Z - 120), (1.0, 0.45, 0.30), candela=150.0, radius=1600.0)
m.accent_light("HoleLight", (0, 0, 120), (0.2, 0.9, 0.9), candela=90.0, radius=1500.0)
for i in range(22):
    ang = rng.uniform(0, 2 * math.pi)
    d = rng.uniform(5200, 9000)
    sz = rng.uniform(120, 520)
    B("Debris", math.cos(ang) * d - sz, math.cos(ang) * d + sz, math.sin(ang) * d * 0.6 - sz * 0.6, math.sin(ang) * d * 0.6 + sz * 0.6, rng.uniform(-300, 1800), rng.uniform(-300, 1800) + sz, rust if i % 2 else hull,
      solid=False, yaw=rng.uniform(0, 180), pitch=rng.uniform(-40, 40))

# ---------------------------------------------------------------- flags, starts
for team, nm, fx in ((0, "Red", -4250.0), (1, "Blue", 4250.0)):
    f = m.spawn(unreal.IAFlagBase, "FlagBase_" + nm, (fx, 0.0, 6.0))
    f.set_editor_property("flag_team", team)


def add_start(label, x, y, yaw, tag=None, z=0.0):
    a = m.spawn(unreal.PlayerStart, label, (x, y, z + 110.0), (0, 0, yaw))
    if tag:
        a.set_editor_property("player_start_tag", tag)
    m.start_count += 1


HALL = [(-3800, -1000), (-3800, 1000), (-4500, -1250), (-4500, 1250), (-4250, -650), (-4250, 650), (-3750, 0), (-4650, 0)]
for team, tag in ((0, "Red"), (1, "Blue")):
    for i, (hx, hy) in enumerate(HALL):
        x = -hx if team == 1 else hx
        add_start("Start_%s_%d" % (tag, i), x, hy, 0.0 if team == 0 else 180.0, tag)
for i, (x, y, z) in enumerate([(-1500, 0, 0), (1500, 0, 0), (0, -1750, CAT_Z), (0, 1750, CAT_Z), (-700, -1400, 0), (700, 1400, 0), (-2000, 1300, 0), (2000, -1300, 0)]):
    add_start("Start_Mid_%d" % i, x, y, rng.uniform(0, 360), None, z)

m.check_starts()
m.finish(kill_z=-1400)
unreal.log("DERELICT actors %d" % len(m.actor_lib.get_all_level_actors()))
