"""DM-Forge: a steel mill (foundry hall) on the flank of a volcano, built around a lava pit. Medium arena (4-8 players).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_forge.py" -unattended -nullrhi -nosplash

Layout (unchanged, bots and balance depend on it): a square floor with a lava pit in the middle (kill height below the
floor), two cross bridges and a central island, a gantry ring at z=450 with four balconies over the pit. Ramps lead up
to the gantry; jump pads on the island throw players straight onto the balconies. Falling into the lava kills.

Look: real materials (matlib), steel structure (H-columns, I-beam roof trusses, an overhead crane with a ladle), brick
and panel walls with high windows that look out on a volcanic landscape, work lamps with warm accent lights, the lava
as the only big glow. Look preset "volcanic".
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import props  # noqa: E402,F401  (adds prop / scatter to MapBuilder)
from mapkit import MapBuilder  # noqa: E402
from matlib import surface, glass  # noqa: E402
from mapkit_d import Frame, hcolumn, tube, beam, sphere, ibeam, truss, lava_instance  # noqa: E402
import mapkit_b as kb  # noqa: E402
import mesh_b as mb  # noqa: E402
import mesh_misc_b as mm  # noqa: E402
import mesh_nat_n as nn  # noqa: E402
import shade_n  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Forge")
rng = random.Random(61)
S = surface

# ------------------------------------------------------------------------------------------------ look
m.look("volcanic", sun_lux=5.0, sun_pitch=-32.0, sun_yaw=55.0, sun_rgb=(1.0, 0.72, 0.5), sky_intensity=3.4,
       sky_rgb=(0.80, 0.78, 0.78), ev=0.3, ambient_gain=0.15, fog_density=0.0014, fog_rgb=(0.10, 0.07, 0.06), fog_start=600.0,
       fog_max_opacity=0.75)

# ------------------------------------------------------------------------------------------------ materials
# the stock red barrel is a saturated toy red: an oxide-red, scuffed variant of its own material
barrel_m = kb.prop_variant("barrel_red", (0.55, 1.5, 1.5), "ForgeBarrel")
_orig_prop = m.prop


def _prop_muted(label, name, *a, **kw):
    if name == "barrel_red" and "material" not in kw:
        kw["material"] = barrel_m
    return _orig_prop(label, name, *a, **kw)


m.prop = _prop_muted
floor_m = S("ConcreteDark", tiling=3.0, tag="ForgeFloor")
floor_b = S("StoneSlabs", albedo=(82, 80, 76), tag="ForgeSlab")
floor_c = S("AsphaltCracked", albedo=(60, 58, 56), tag="ForgeCrack")
plate = S("DiamondPlateDark")
steel = S("SteelDark")
iron = S("ForgeIron")
rust_c = S("RustCoarse", albedo=(92, 50, 30), tag="Forge")
rust_o = S("CorrugatedRust", albedo=(108, 60, 38), tag="Forge")
brick = S("BrickDark", dirt=0.7, dirt_h=380.0, tag="ForgeBrick")
brick_r = S("BrickRed", albedo=(112, 62, 46), dirt=0.6, dirt_h=300.0, tag="ForgeBrickR")
panel = S("ConcretePanels", albedo=(88, 86, 82), tag="ForgePanel")
corr = S("CorrugatedDark")
basalt = S("BasaltDark")
stone = S("StoneDark")
slag = S("StoneRubble", albedo=(52, 48, 46), tag="ForgeSlag")
yellow = S("ContainerYellow", albedo=(184, 150, 72), macro=0.45, macro_m=3.0, tag="Forge2")
blk = S("Asphalt", albedo=(40, 40, 42), tag="Forge")
wood = S("WoodPlanksDark", albedo=(88, 64, 46), tag="Forge")
wood_o = S("WoodPlanksOld", albedo=(96, 86, 76), tag="Forge")
pane = glass()
lava_m = lava_instance("MI_ForgeLava", intensity=2.4, tiling=2.5, speed=0.6)
ember = m.glow("MI_ForgeSlit", (1.0, 0.42, 0.1), 0.9)
bulb = m.glow("MI_ForgeBulb", (1.0, 0.8, 0.5), 2.5)

WARM = (1.0, 0.74, 0.44)
COOL = (0.74, 0.84, 1.0)
ORANGE = (1.0, 0.40, 0.12)
RED = (1.0, 0.22, 0.06)

H = 2600.0            # half size of the hall
PIT = 900.0           # half size of the lava pit
CEIL = 1500.0
GZ = 450.0            # gantry height
LAVA_Z = -250.0
RING_IN, RING_OUT = 2150.0, H

STARTS = [(-1490.0, -290.0, 0), (1630.0, 1270.0, 0), (-1250.0, 1990.0, 0), (-2450.0, -1010.0, 0),
          (-2330.0, -890.0, 450), (430.0, 1150.0, 0), (-1730.0, 2230.0, 0), (-2450.0, -2450.0, 450),
          (2230.0, -1730.0, 0), (430.0, -2450.0, 0)]
PADS = [(330, 330), (-330, 330), (-330, -330), (330, -330)]


def R(k, x, y):
    for _ in range(k % 4):
        x, y = -y, x
    return x, y


def free(x, y, r=140.0):
    """True when (x, y) is not near a player start or a jump pad."""
    for sx, sy, _ in STARTS:
        if math.hypot(x - sx, y - sy) < r + 60:
            return False
    for px, py in PADS:
        if math.hypot(x - px, y - py) < r + 90:
            return False
    return True


# ------------------------------------------------------------------------------------------------ floor and pit
m.box("Floor_N", 0, (H + PIT) / 2, -50, H * 2, H - PIT, 100, mat=floor_m)
m.box("Floor_S", 0, -(H + PIT) / 2, -50, H * 2, H - PIT, 100, mat=floor_m)
m.box("Floor_E", (H + PIT) / 2, 0, -50, H - PIT, PIT * 2, 100, mat=floor_m)
m.box("Floor_W", -(H + PIT) / 2, 0, -50, H - PIT, PIT * 2, 100, mat=floor_m)

# worn patches on the floor (flush, no collision): slabs, cracked asphalt, scorched areas
for i in range(18):
    x, y = rng.uniform(-2300, 2300), rng.uniform(-2300, 2300)
    if abs(x) < PIT + 260 and abs(y) < PIT + 260:
        continue
    w, d = rng.uniform(260, 700), rng.uniform(260, 700)
    m.box("Patch_%d" % i, x, y, 0.8 + (i % 3) * 0.3, w, d, 1.6, yaw=rng.choice([0, 0, 90, 20, -15]),
          mat=floor_b if i % 3 else floor_c, solid=False)

# plate walkway and hazard border around the pit
for k in range(4):
    f = Frame(m, k)
    f.box("PitWalk", 0, PIT + 230, 1.2, 2 * PIT + 520, 460, 2.4, mat=plate, solid=False)
    f.box("PitLip", 0, PIT + 7, 4, 2 * PIT + 40, 14, 8, mat=steel, solid=False)
    f.box("HazardBase", 0, PIT + 60, 2.4, 2 * PIT, 60, 1.0, mat=blk, solid=False)
    for i in range(-9, 10, 2):
        f.box("Hazard", i * 100.0, PIT + 60, 2.8, 100, 60, 1.2, mat=yellow, solid=False)

# the pit: dark basalt walls, crust and lava far below, boulders on the rim
m.box("Lava", 0, 0, LAVA_Z, PIT * 2 + 120, PIT * 2 + 120, 10, mat=lava_m, solid=False)
for k in range(4):
    f = Frame(m, k)
    f.box("PitWall", 0, PIT + 55, LAVA_Z / 2 - 1.5, PIT * 2 + 260, 120, -LAVA_Z + 4, mat=basalt, solid=False)
    # cooled crust plates floating on the lava near the wall
    for i in range(5):
        f.box("Crust", rng.uniform(-700, 700), PIT - rng.uniform(40, 220), LAVA_Z + 4, rng.uniform(140, 380),
              rng.uniform(100, 260), 7, yaw=rng.uniform(0, 180), mat=stone, solid=False)
for i, (x, y) in enumerate([(-800, -800), (820, -780), (-780, 800), (800, 810)]):
    m.prop("PitRock_%d" % i, "rock_red_c_s", x, y, LAVA_Z - 10, yaw=i * 70, scale=2.2, material=basalt, solid=False)

m.accent_light("LavaGlow_C", (0, 0, 90), ORANGE, 170.0, 2300.0, source_radius=120.0)
for i, (x, y) in enumerate([(-600, -600), (600, -600), (-600, 600), (600, 600)]):
    m.accent_light("LavaGlow_%d" % i, (x, y, -140), RED, 150.0, 1500.0, source_radius=80.0)

# ------------------------------------------------------------------------------------------------ bridges and island
m.box("Island", 0, 0, -20, 900, 900, 40, mat=plate)
m.column("IslandStem", 0, 0, LAVA_Z, -40, 380, mat=basalt, solid=False)
m.column("IslandStemRing", 0, 0, -140, -110, 430, mat=steel, solid=False)
m.box("IslandEdgeN", 0, 452, -22, 920, 8, 56, mat=steel, solid=False)
m.box("IslandEdgeS", 0, -452, -22, 920, 8, 56, mat=steel, solid=False)
m.box("IslandEdgeE", 452, 0, -22, 8, 920, 56, mat=steel, solid=False)
m.box("IslandEdgeW", -452, 0, -22, 8, 920, 56, mat=steel, solid=False)
for k in (0, 1):
    f = Frame(m, k)
    f.box("Bridge", 0, 0, -20, 2000, 380, 40, mat=plate)
    for s in (-1, 1):
        f.ibeam("BridgeGirder", (-1000, s * 175, -90), (1000, s * 175, -90), depth=90, flange=34, tf=7, tw=6, mat=steel)
        for (a, b) in ((-1000, -462), (462, 1000)):
            f.railing("BridgeRail", (a, s * 188, 0), (b, s * 188, 0), height=105, post_every=250, mat=steel, rails=2,
                      toe=10)
    for i in range(-7, 8):
        f.box("BridgeRib", i * 130.0, 0, -62, 8, 346, 28, mat=steel, solid=False)
for (x, y) in ((-440, -440), (440, -440), (-440, 440), (440, 440)):      # heat-shield pillars on the island
    m.column("IslandPillar", x, y, 0, 320, 110, mat=iron)
    m.column("PillarBase", x, y, 0, 70, 150, mat=brick_r, solid=False)
    m.column("PillarCap", x, y, 320, 340, 150, mat=steel, solid=False)
    for z in (110, 190, 270):
        m.column("PillarBand", x, y, z, z + 14, 124, mat=rust_c, solid=False)
    m.accent_light("IslandLamp", (x * 0.85, y * 0.85, 360), WARM, 40.0, 900.0)

# ------------------------------------------------------------------------------------------------ walls, gantry, balconies
WIN = (-975.0, -325.0, 325.0, 975.0)
for k in range(4):
    f = Frame(m, k)
    # brick wall up to the window level, panels above, windows with steel frames
    f.box("WallLow", 0, H + 150, 210, 5800, 300, 820, mat=brick)
    f.box("WallUpL", -2100, H + 150, 1060, 1600, 300, 880, mat=panel)
    f.box("WallUpR", 2100, H + 150, 1060, 1600, 300, 880, mat=panel)
    for c in WIN:
        f.box("Sill", c, H + 150, 680, 650, 300, 120, mat=panel)
        f.box("Lintel", c, H + 150, 1395, 650, 300, 210, mat=panel)
        f.box("Jamb", c - 277.5, H + 150, 1015, 95, 300, 550, mat=panel)
        f.box("Jamb", c + 277.5, H + 150, 1015, 95, 300, 550, mat=panel)
        f.box("Pane", c, H + 120, 1015, 460, 6, 550, mat=pane)
        f.box("Mullion", c, H - 4, 1015, 8, 8, 550, mat=steel, solid=False)
        for z in (900.0, 1130.0):
            f.box("Transom", c, H - 4, z, 460, 8, 8, mat=steel, solid=False)
        f.box("Frame", c, H - 6, 745, 480, 14, 10, mat=steel, solid=False)
        f.box("Frame", c, H - 6, 1285, 480, 14, 10, mat=steel, solid=False)
    # steel piers (H-sections) every 650 cm
    for px in range(-1950, 1951, 650):
        hcolumn(f, "Pier", px, H - 25, 0, CEIL, flange=60, depth=50, tf=8, tw=6, mat=steel, solid=False)
        f.box("Corbel", px, H - 40, 950, 40, 70, 70, mat=steel, solid=False)
    # wall pipes at the top and big sliding doors in the brick
    f.tube("WallPipe", (-2560, H - 62, 1400), (2560, H - 62, 1400), 56, mat=rust_c)
    f.tube("WallPipe2", (-2560, H - 62, 1285), (2560, H - 62, 1285), 34, mat=steel)
    for px in range(-1950, 1951, 650):
        f.tube("PipeFlange", (px, H - 69, 1400), (px, H - 55, 1400), 80, mat=steel)
        f.box("PipeBracket", px, H - 40, 1370, 30, 40, 60, mat=steel, solid=False)
    for c in (-1625.0, 1625.0):
        f.box("DoorLeaf", c, H - 14, 190, 340, 14, 380, mat=rust_o, solid=False)
        f.box("DoorBand", c, H - 22, 40, 340, 6, 80, mat=yellow, solid=False)
        f.box("DoorTrack", c, H - 30, 405, 640, 24, 22, mat=steel, solid=False)
        f.box("DoorPost", c - 180, H - 14, 190, 24, 24, 380, mat=steel, solid=False)
        f.box("DoorPost", c + 180, H - 14, 190, 24, 24, 380, mat=steel, solid=False)
    # gantry deck, fascia, columns, rails
    length = 2 * H if k % 2 == 0 else 2 * H - 2 * (RING_OUT - RING_IN)
    mid = (RING_IN + RING_OUT) / 2.0
    f.box("Gantry", 0, mid, GZ - 20, length, RING_OUT - RING_IN, 40, mat=plate)
    f.box("GantryFascia", 0, RING_IN - 5, GZ - 55, length, 10, 110, mat=steel, solid=False)
    f.box("GantryJoist", 0, RING_IN + 150, GZ - 62, length, 24, 44, mat=steel, solid=False)
    f.box("GantryJoist", 0, RING_IN + 330, GZ - 62, length, 24, 44, mat=steel, solid=False)
    for i in range(-4, 5):
        f.box("Strut", i * 550.0, 2190, (GZ - 40) / 2, 60, 50, GZ - 40, mat=steel, solid=True)
    for (a, b) in ((-2150, -1410), (-990, -410), (410, 2150)):
        f.railing("GantryRail", (a, RING_IN - 8, GZ), (b, RING_IN - 8, GZ), height=105, post_every=230, mat=steel, rails=2,
                  toe=10)
    # balcony over the pit
    f.box("Balcony", 0, 1850, GZ - 20, 800, 700, 40, mat=plate)
    for sx in (-1, 1):
        for sy in (-1, 1):
            hcolumn(f, "BalconyPost", sx * 330, 1850 + sy * 300, 0, GZ - 40, flange=50, depth=50, tf=8, tw=6, mat=steel)
    f.box("BalconyRail", 0, 1505, GZ + 45, 700, 12, 90, mat=plate)
    f.tube("BalconyHandrail", (-395, 1505, GZ + 100), (395, 1505, GZ + 100), 5, mat=steel)
    for sx in (-1, 1):
        f.railing("BalconySide", (sx * 395, 1505, GZ), (sx * 395, 2150, GZ), height=105, post_every=215, mat=steel, rails=2,
                  toe=10)
    f.box("BalconyFascia", 0, 1497, GZ - 52, 800, 8, 96, mat=steel, solid=False)
    # ramp from the floor up to the gantry, with stringers, rails and supports
    f.slope("Ramp", (-1200, 700, 0), (-1200, 2150, GZ), 380, thickness=40, mat=plate)
    for s in (-1, 1):
        x = -1200 + s * 190
        f.beam("Stringer", (x, 700, -38), (x, 2150, GZ - 38), 10, 76, mat=steel)
        f.railing("RampRail", (x, 700, 0), (x, 2150, GZ), height=105, post_every=260, mat=steel, rails=2)
    for yy in (1500.0, 1900.0):
        top = (yy - 700) / 1450.0 * GZ - 40
        for s in (-1, 1):
            f.box("RampLeg", -1200 + s * 170, yy, top / 2, 24, 24, top, mat=steel, solid=False)
    # a jump pad on the island sends the player to the balcony of this side
    px, py = R(k, 330, 330)
    tx, ty = R(k, 0, 1850)
    m.jump_pad("BalconyPad_%d" % k, px, py, 0, (tx, ty, GZ), color=(1.0, 0.45, 0.1), apex_extra=170.0)

# ------------------------------------------------------------------------------------------------ roof: trusses, purlins, skylights
TRUSS_X = [-2275 + 650 * i for i in range(8)]          # trusses sit between the piers; x = 0 stays free for the crane
for tx in TRUSS_X:
    truss(m, "Truss", (tx, -2580, 1160), (tx, 2580, 1160), 330, 8, chord=16, mat=steel, width=18)
for py in range(-2275, 2276, 650):
    m.box("Purlin", 0, py, 1511, 5200, 14, 22, mat=steel, solid=False)
SKY_BAYS = ((-950, -350), (350, 950))
deck = [(-2600, -950), (-350, 350), (950, 2600)]
for i, (a, b) in enumerate(deck):
    m.box("RoofDeck_%d" % i, (a + b) / 2, 0, 1515, b - a, 5200, 30, mat=corr)
for i, (a, b) in enumerate(SKY_BAYS):
    for s in (-1, 1):
        m.box("RoofEnd_%d_%d" % (i, s), (a + b) / 2, s * 2250, 1515, b - a, 700, 30, mat=corr)
        m.box("SkyLightKerb", (a + b) / 2, s * 1900, 1560, b - a + 40, 20, 90, mat=steel, solid=False)
        m.box("SkyLightKerb", a if s < 0 else b, 0, 1560, 20, 3800, 90, mat=steel, solid=False)

# overhead pipe runs and ducts under the trusses
for i, px in enumerate((-1625.0, 1625.0, 2275.0, -2275.0)):
    tube(m, "DuctPipe", (px, -2500, 1100), (px, 2500, 1100), 62 if i < 2 else 46, rust_c if i % 2 else steel)
    for py in (-1950.0, -650.0, 650.0, 1950.0):
        m.box("PipeHanger", px, py, 1135, 12, 12, 70, mat=steel, solid=False)
for i, py in enumerate((-1625.0, 1625.0)):
    m.box("Duct", 0, py, 1060, 4200, 110, 90, mat=S("CorrugatedGalv", albedo=(96, 98, 102), tag="Forge"), solid=False)
    for px in TRUSS_X:
        m.box("DuctHanger", px, py, 1115, 10, 10, 60, mat=steel, solid=False)

# ------------------------------------------------------------------------------------------------ overhead crane and ladle
for s in (-1, 1):
    ibeam(m, "Runway", (-2540, s * (H - 100), 1100), (2540, s * (H - 100), 1100), depth=100, flange=60, tf=10, tw=8, mat=steel)
CX = 0.0
for dx in (-85, 85):
    ibeam(m, "CraneBridge", (CX + dx, -2500, 1200), (CX + dx, 2500, 1200), depth=150, flange=60, tf=12, tw=9, mat=iron)
for s in (-1, 1):
    m.box("EndTruck", CX, s * (H - 100), 1150, 280, 190, 110, mat=iron, solid=False)
    m.box("EndTruckWheel", CX - 110, s * (H - 100), 1100, 24, 140, 70, mat=steel, solid=False)
    m.box("EndTruckWheel", CX + 110, s * (H - 100), 1100, 24, 140, 70, mat=steel, solid=False)
m.box("Trolley", CX, 0, 1330, 300, 300, 110, mat=iron, solid=False)
m.box("TrolleyMotor", CX, 0, 1410, 140, 180, 70, mat=rust_c, solid=False)
for dy in (-60, 60):
    tube(m, "HoistRope", (CX, dy, 1300), (CX, dy * 0.6, 1095), 8, steel)
m.box("HookBlock", CX, 0, 1060, 150, 110, 70, mat=iron, solid=False)
for sgn in (-1, 1):
    tube(m, "LadleChain", (CX + sgn * 25, 0, 1040), (CX + sgn * 265, 0, 870), 12, steel)
# the ladle
LZ = 620.0
m.column("LadleBody", CX, 0, LZ, LZ + 330, 540, mat=iron, solid=False)
m.column("LadleLowerA", CX, 0, LZ - 55, LZ, 440, mat=iron, solid=False)
m.column("LadleLowerB", CX, 0, LZ - 95, LZ - 55, 320, mat=rust_c, solid=False)
m.column("LadleRim", CX, 0, LZ + 320, LZ + 345, 580, mat=steel, solid=False)
m.column("LadleBand", CX, 0, LZ + 150, LZ + 168, 556, mat=rust_c, solid=False)
m.column("LadleMetal", CX, 0, LZ + 322, LZ + 332, 500, mat=lava_m, solid=False)
for sgn in (-1, 1):
    tube(m, "Trunnion", (CX + sgn * 255, 0, LZ + 250), (CX + sgn * 330, 0, LZ + 250), 46, steel)
m.accent_light("LadleLight", (CX, 0, LZ + 440), ORANGE, 150.0, 1500.0, source_radius=60.0)

# ------------------------------------------------------------------------------------------------ furnace towers and chimneys
for k in range(4):
    f = Frame(m, k)
    x, y = 2250.0, 2250.0
    f.column("Tower", x, y, 0, CEIL, 420, mat=brick)
    f.column("TowerBase", x, y, 0, 120, 500, mat=steel)
    f.column("TowerPlinth", x, y, 120, 150, 470, mat=rust_c, solid=False)
    for z in (330.0, 640.0, 950.0, 1260.0):
        f.column("TowerBand", x, y, z, z + 30, 446, mat=iron, solid=False)
    f.column("Chimney", x, y, CEIL, CEIL + 900, 300, mat=brick, solid=False)
    f.column("ChimneyBand", x, y, CEIL + 780, CEIL + 840, 330, mat=steel, solid=False)
    # furnace door and a small fire slit facing the hall centre
    dx, dy = -math.cos(math.radians(45)), -math.sin(math.radians(45))
    fx, fy = x + dx * 205, y + dy * 205
    f.box("FurnaceDoor", fx, fy, 130, 26, 150, 190, yaw=225, mat=iron, solid=False)
    f.box("FurnaceFrame", x + dx * 212, y + dy * 212, 130, 20, 190, 230, yaw=225, mat=steel, solid=False)
    f.box("FurnaceSlit", x + dx * 220, y + dy * 220, 150, 4, 90, 16, yaw=225, mat=ember, solid=False)
    f.light("FurnaceLight", x + dx * 330, y + dy * 330, 120, ORANGE, 70.0, 900.0)
    # pipes from the tower up into the roof
    f.tube("TowerPipe", (x - 215, y + 10, 100), (x - 215, y + 10, CEIL), 40, mat=rust_c)

# ------------------------------------------------------------------------------------------------ cover on the open floor
cover = [(-1700, -1800, 20), (1700, 1800, 70), (-1900, 1500, 0), (1900, -1500, 50), (0, -1700, 0), (0, 1700, 90),
         (-1750, 0, 90), (1750, 0, 0), (-1300, -400, 30), (1300, 400, 60)]
for i, (x, y, yaw) in enumerate(cover):
    t = i % 5
    if t == 0:                                    # slag bin
        m.box("Bin_%d" % i, x, y, 70, 260, 200, 140, yaw=yaw, mat=rust_o)
        m.box("BinFill", x, y, 134, 236, 176, 10, yaw=yaw, mat=slag, solid=False)
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        m.prop("BinRock_%d" % i, "rock_red_a_s", x + c * 30, y + s * 30, 138, yaw=yaw + 20, scale=0.9, material=basalt, solid=False)
        m.box("BinBand", x, y, 120, 266, 206, 14, yaw=yaw, mat=steel, solid=False)
    elif t == 1:                                  # crate stack
        m.box("Crates_%d" % i, x, y, 70, 260, 200, 140, yaw=yaw, mat=wood)
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            ox, oy = sx * 127 * c - sy * 97 * s, sx * 127 * s + sy * 97 * c
            m.box("CrateEdge", x + ox, y + oy, 70, 8, 8, 144, yaw=yaw, mat=wood_o, solid=False)
        m.box("CrateMid", x, y, 70, 266, 8, 146, yaw=yaw, mat=wood_o, solid=False)
        m.prop("CrateBarrel_%d" % i, "barrel_red", x, y, 140, yaw=yaw * 3, scale=1.0, solid=False)
    elif t == 2:                                  # ingot stack
        m.box("Ingots_%d" % i, x, y, 70, 260, 200, 140, yaw=yaw, mat=iron)
        m.box("IngotBand", x, y, 28, 264, 204, 26, yaw=yaw, mat=yellow, solid=False)
        m.box("IngotTop", x, y, 141, 240, 180, 3, yaw=yaw, mat=plate, solid=False)
        for j in range(3):
            m.box("IngotSlit", x, y, 62 + j * 32, 264, 204, 4, yaw=yaw, mat=blk, solid=False)
    elif t == 3:                                  # machine housing
        m.box("Machine_%d" % i, x, y, 70, 260, 200, 140, yaw=yaw, mat=panel)
        m.box("MachineTrim", x, y, 138, 266, 206, 8, yaw=yaw, mat=yellow, solid=False)
        m.prop("MachineGen_%d" % i, "generator", x, y, 142, yaw=yaw, scale=1.7, solid=False)
        m.box("MachineVent", x, y, 80, 270, 150, 60, yaw=yaw, mat=steel, solid=False)
    else:                                         # slag heap
        blocker = m.box("Heap_%d" % i, x, y, 70, 260, 200, 140, yaw=yaw, mat=slag)
        m.prop("HeapA_%d" % i, "rock_red_c_s", x + 20, y, 80, yaw=yaw, scale=1.5, material=basalt, solid=False)
        m.prop("HeapB_%d" % i, "rock_red_b_s", x - 50, y + 20, 70, yaw=yaw + 100, scale=1.4, material=basalt, solid=False)

# ------------------------------------------------------------------------------------------------ clutter and lamps
def clutter(name, x, y, z, yaw=0.0, scale=1.0, solid=False, label=None):
    if not free(x, y, 90.0):
        return None
    return m.prop(label or name, name, x, y, z, yaw=yaw, scale=scale, solid=solid)


for k in range(4):
    f = Frame(m, k)
    # under the gantry: barrels and crates against the wall, generators
    for i, (x, kind) in enumerate([(-1010, "barrel_red"), (-940, "barrel_red"), (-1710, "crate_wood_b"), (900, "generator"),
                                   (1500, "barrel_red"), (1570, "barrel_red"), (1535, "barrel_red"), (-300, "crate_wood_a")]):
        sc = {"crate_wood_b": 2.0, "crate_wood_a": 2.4, "generator": 1.9, "barrel_red": 1.0}[kind]
        wx, wy = f.P(x, H - 110 if kind != "generator" else H - 100)
        clutter(kind, wx, wy, 0, yaw=f.Y(90 + rng.uniform(-20, 20)), scale=sc, label="Under_%d_%d" % (k, i))
    # work lamps under the gantry (warm pools)
    for x in (-1625.0, -325.0, 975.0, 1950.0):
        f.light("UnderLamp", x, 2380, 370, WARM, 55.0, 850.0)
        f.box("UnderLampBulb", x, 2380, 395, 24, 24, 12, mat=bulb, solid=False)
    # hanging lamps above the gantry level and over the hall
    for x in (-1300.0, 1300.0):
        wx, wy = f.P(x, 2350)
        m.prop("HangLamp", "lamp_hanging", wx, wy, 970, scale=1.4, solid=False)
        f.light("HangLampLight", x, 2350, 950, COOL, 80.0, 1300.0)
        f.box("HangLampBulb", x, 2350, 985, 26, 26, 14, mat=bulb, solid=False)
for i, (x, y) in enumerate([(-1500, -1500), (1500, -1500), (-1500, 1500), (1500, 1500), (-1500, 0), (1500, 0), (650, -1500),
                            (-650, 1500), (650, 1500), (-650, -1500)]):
    m.prop("HallLamp_%d" % i, "lamp_hanging", x, y, 970, scale=1.4, solid=False)
    # a mix of cold work lights (steel-grey hall) and warm sodium lamps near the furnaces
    m.accent_light("HallLampLight_%d" % i, (x, y, 950), COOL if i % 2 == 0 else WARM, 95.0 if i % 2 == 0 else 105.0, 1500.0)
    m.box("HallLampBulb", x, y, 985, 26, 26, 14, mat=bulb, solid=False)

# scattered clutter: barrels, tyres, jerrycans, propane bottles
for i, (x, y, kind, sc) in enumerate([(-2050, -1500, "barrel_red", 1.0), (-2090, -1440, "barrel_red", 1.0), (2060, 1580, "tyre", 1.6),
                                      (2100, 1500, "tyre", 1.6), (-2000, 1950, "propane_tank", 1.8), (-1950, 1900, "jerrycan", 1.8),
                                      (2000, -1950, "barrel_red", 1.0), (1950, -2050, "barrel_red", 1.0), (1500, -900, "crate_wood_b", 2.0),
                                      (-1500, 950, "crate_wood_b", 2.2), (-1040, -1620, "tyre", 1.6), (1100, 1640, "barrel_red", 1.0)]):
    clutter(kind, x, y, 0, yaw=rng.uniform(0, 360), scale=sc, label="Clutter_%d" % i)

# ------------------------------------------------------------------------------------------------ the world outside the windows
# Dark volcanic country: a black cone with glowing lava streaks, a plume of ash that is lit orange from below, dark craggy ridges
# (generated meshes, not scaled scans) and a few red glows. Seen through the windows from the gantry and the floor.
ASH = S("StoneRubble", albedo=(40, 37, 36), tiling=8.0, tag="ForgeAsh2")
BASALT_FAR = S("BasaltDark", albedo=(46, 42, 42), tiling=30.0, ns=1.2, tag="ForgeFarBasalt")
for i, (cx, cy, sx, sy) in enumerate([(0, 12000, 30000, 18200), (0, -12000, 30000, 18200), (12000, 0, 18200, 6000), (-12000, 0, 18200, 6000)]):
    m.box("OutGround_%d" % i, cx, cy, -400, sx, sy, 600, mat=ASH, solid=False)
VOLCANO = (2400.0, 15500.0)
VR, VZ0, VZ1 = 4200.0, -400.0, 5000.0                                    # base radius, base z, crater rim z (low enough to show in the windows)
m.cone("Volcano", VOLCANO[0], VOLCANO[1], VZ0, VZ1, VR * 2, mat=BASALT_FAR, solid=False)
for i in range(10):                                                      # foothills and spurs around the cone (craggy, dark)
    a = i / 10.0 * 2 * math.pi + 0.3
    sm = kb.commit("FSpur_%d" % (i % 5), mm.mountain_mesh(rng.uniform(1300, 2400), rng.uniform(1000, 2600), seed=520 + i % 5, sides=40, rings=12, base_z=-300.0))
    kb.put(m, "Spur_%d" % i, sm, VOLCANO[0] + math.cos(a) * rng.uniform(3600, 5200), VOLCANO[1] + math.sin(a) * rng.uniform(3600, 5200), -300.0, yaw=rng.uniform(0, 360),
           mat=BASALT_FAR, solid=False, folder="Far")
m.column("VolcanoCrater", VOLCANO[0], VOLCANO[1], VZ1 - 60, VZ1 + 40, 700, mat=lava_m, solid=False)


def cone_pt(t, ang, lift=120.0):
    r = VR * (1.0 - t)
    return (VOLCANO[0] + math.cos(ang) * (r + lift), VOLCANO[1] + math.sin(ang) * (r + lift), VZ0 + (VZ1 - VZ0) * t)


for k in range(9):                                                       # lava streaks running down the flank (towards the hall: south side)
    a0 = math.radians(258.0 + rng.uniform(-60, 60))
    t = 0.97
    prev = cone_pt(t, a0)
    for seg in range(rng.randint(6, 10)):
        t2 = max(0.12, t - rng.uniform(0.05, 0.11))
        a0 += rng.uniform(-0.06, 0.06)
        cur = cone_pt(t2, a0)
        beam(m, "LavaStreak_%d_%d" % (k, seg), prev, cur, rng.uniform(900, 1700) * (1.0 - 0.45 * (1.0 - t2)), 240, mat=lava_m)
        prev, t = cur, t2
        if t <= 0.13:
            break
# the plume: dark ash, lit from below by the crater glow (puffs get darker and grayer higher up, drift east)
for i in range(16):
    f = i / 15.0
    col = (0.36, 0.13, 0.05) if i < 3 else ((0.16, 0.075, 0.05) if i < 6 else ((0.075, 0.062, 0.06) if i < 11 else (0.045, 0.042, 0.045)))
    shade_n.puff(m, "Plume_%d" % i, VOLCANO[0] + 200 + f * f * 4200 + rng.uniform(-200, 200), VOLCANO[1] + rng.uniform(-400, 400), VZ1 + 200 + f * 4200,
                 900 + f * 2600 + rng.uniform(0, 400), col, strength=0.62 if i > 2 else 0.5)
m.accent_light("VolcanoGlow", (VOLCANO[0], VOLCANO[1] - 900, VZ1 + 500), ORANGE, 9000.0, 9000.0, source_radius=300.0)
# distant ridges and crags: generated craggy peaks in black basalt with a faint red rim glow from the volcano
RIDGE_SM = [kb.commit("FRidge_%d" % k, mm.mountain_mesh(rng.uniform(3200, 5200), rng.uniform(1800, 3800), seed=560 + k, sides=44, rings=13, ridge=0.6, base_z=-300.0)) for k in range(6)]
for i in range(14):
    ang = math.radians(i * (360.0 / 14) + 12.0 + rng.uniform(-6, 6))
    d = rng.uniform(10500, 14500)
    kb.put(m, "Ridge_%d" % i, RIDGE_SM[i % 6], math.cos(ang) * d, math.sin(ang) * d, -420.0, yaw=rng.uniform(0, 360), scale=(rng.uniform(0.9, 1.4), rng.uniform(0.9, 1.4), rng.uniform(0.8, 1.3)),
           mat=BASALT_FAR, solid=False, folder="Far")
CRAG_SM = [kb.commit("FCrag_%d" % k, mm.mountain_mesh(rng.uniform(700, 1300), rng.uniform(500, 1400), seed=600 + k, sides=32, rings=10, ridge=0.6, base_z=-200.0)) for k in range(4)]
for i in range(12):
    ang = math.radians(i * 30 + 5 + rng.uniform(-8, 8))
    d = rng.uniform(5200, 7600)
    kb.put(m, "Crag_%d" % i, CRAG_SM[i % 4], math.cos(ang) * d, math.sin(ang) * d, -420.0, yaw=rng.uniform(0, 360), mat=BASALT_FAR, solid=False, folder="Far")
# a few small ground fissures glowing in the dark plain (thin emissive lines, far away)
for i in range(5):
    x0, y0 = rng.uniform(-7000, 7000), rng.choice((-1, 1)) * rng.uniform(6500, 9500)
    ang = rng.uniform(0, 180)
    for j in range(5):
        a = math.radians(ang + rng.uniform(-25, 25))
        m.box("Fissure_%d_%d" % (i, j), x0 + math.cos(math.radians(ang)) * j * 500, y0 + math.sin(math.radians(ang)) * j * 500, -90, rng.uniform(380, 600), 55, 6,
              yaw=ang + rng.uniform(-20, 20), mat=lava_m, solid=False)

# ------------------------------------------------------------------------------------------------ cool daylight from the skylights, soft contact shade
# the skylight bays let in a little cold daylight (the rest of the hall is lit by warm lamps and the lava)
for sx_ in (-1, 1):
    for yy in (-1400.0, 0.0, 1400.0):
        m.accent_light("SkylightPool", (sx_ * 650.0, yy, 1380.0), (0.70, 0.82, 1.0), 120.0, 1900.0)
# dark soft hints where light cannot reach: under the gantry ring and at the foot of the pit walls (no global illumination here)
for k in range(4):
    f = Frame(m, k)
    wx, wy = f.P(0, 2330)
    shade_n.blob(m, "UnderGantry_%d" % k, wx, wy, 2.5, 5000 if k % 2 == 0 else 4400, 520, strength=0.5, yaw=f.Y(0))
for k, (cx, cy, sx_, sy_) in enumerate([(0, 1010, 2000, 220), (0, -1010, 2000, 220), (1010, 0, 220, 2000), (-1010, 0, 220, 2000)]):
    shade_n.blob(m, "PitEdgeShade_%d" % k, cx, cy, 3.0, sx_, sy_, strength=0.3)

# ------------------------------------------------------------------------------------------------ spawns
m.face_center_starts(STARTS)
m.check_starts()

# the hall fog is neutral dark smoke, not an orange wall; slightly less saturated picture overall
m.fog(rgb=(0.075, 0.068, 0.07))
m.post(saturation=0.92)
m.finish(kill_z=-150)
