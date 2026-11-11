"""DM-Canyon: a big open desert canyon with a ravine, rope bridges, two high mesas and rock spires. 8-10 bots.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_canyon.py" -unattended -nullrhi -nosplash

Layout (x is the long axis, 8800 wide): two canyon floors north and south of a ravine (kill height below), three bridges
across it, a mesa at each end (z=700) reached by long ramps, four rock spires beside the mesas that are joined to them by
plank bridges. Jump pads on the floors throw players up to the spire tops. Falling into the ravine kills.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
from mapkit import MapBuilder

m = MapBuilder("/Game/Maps/DM-Canyon")
rng = random.Random(23)

sand = m.material("MI_CanyonSand", (0.62, 0.44, 0.26), 0.95)
orange = m.material("MI_CanyonOrange", (0.55, 0.27, 0.12), 0.9)
red = m.material("MI_CanyonRed", (0.42, 0.16, 0.09), 0.9)
pale = m.material("MI_CanyonPale", (0.70, 0.55, 0.38), 0.9)
shadow = m.material("MI_CanyonDark", (0.22, 0.12, 0.09), 0.9)
wood = m.material("MI_CanyonWood", (0.32, 0.19, 0.09), 0.85)
rope = m.material("MI_CanyonRope", (0.55, 0.45, 0.30), 0.9)
water = m.material("MI_CanyonWater", (0.05, 0.22, 0.30), 0.2)
cloth = m.glow("MI_CanyonCloth", (0.9, 0.12, 0.05), 0.6)
cloth2 = m.glow("MI_CanyonClothB", (0.1, 0.55, 0.75), 0.6)

FX, FY = 3000.0, 2400.0      # floor half sizes (x, y) between the mesas
RAV = 350.0                  # half width of the ravine
MESA_Z = 700.0
LAYERS = [orange, red, pale, orange, shadow, pale]

# ---------------------------------------------------------------- ground
for sy in (-1, 1):
    m.box("Floor_%s" % ("N" if sy > 0 else "S"), 0, sy * (RAV + FY) / 2, -400, FX * 2, FY - RAV, 800, mat=sand)
m.box("River", 0, 0, -680, FX * 2, RAV * 2, 10, mat=water, solid=False)

# ravine walls: layered strata (decoration on the faces of the floors)
for sy in (-1, 1):
    for i in range(6):
        m.box("Strata", 0, sy * (RAV - 6), -100 - i * 110, FX * 2, 14, 100, mat=LAYERS[i], solid=False)

# mesas at both ends
for sx in (-1, 1):
    m.box("Mesa_%s" % ("W" if sx < 0 else "E"), sx * (FX + 700), 0, MESA_Z / 2 - 400, 1400, FY * 2 + 400, MESA_Z + 800, mat=sand)
    m.box("MesaTop_%s" % ("W" if sx < 0 else "E"), sx * (FX + 700), 0, MESA_Z + 1, 1380, FY * 2, 4, mat=pale, solid=False)
    for i in range(6):                                          # strata on the mesa faces
        m.box("MesaStrata", sx * (FX - 6), 0, MESA_Z - 60 - i * 110, 14, FY * 2, 100, mat=LAYERS[i], solid=False)
    # boundary walls behind the mesas
    m.box("MesaBack_%s" % ("W" if sx < 0 else "E"), sx * (FX + 1500), 0, 800, 200, FY * 2 + 800, 2400, mat=red)

# canyon outer walls (north and south) with stepped rock
for sy in (-1, 1):
    m.box("CanyonWall", 0, sy * (FY + 250), 700, (FX + 1500) * 2, 500, 2200, mat=red)
    x = -FX - 1400
    i = 0
    while x < FX + 1400:
        w = rng.uniform(300, 700)
        h = rng.uniform(300, 1300)
        m.box("WallRock_%d" % i, x + w / 2, sy * (FY - 120 - rng.uniform(0, 80)), h / 2 - 100, w, 260,
              h, yaw=rng.uniform(-4, 4), mat=rng.choice(LAYERS), solid=False)
        x += w
        i += 1

# ---------------------------------------------------------------- bridges across the ravine
for bx in (-2000.0, 0.0, 2000.0):
    wide = 520.0 if bx == 0 else 420.0
    m.box("Bridge_%d" % bx, bx, 0, -20, wide, RAV * 2 + 100, 40, mat=wood)
    for k in range(-6, 7):                                       # plank lines
        m.box("Plank", bx, k * 60, 1, wide - 20, 6, 3, mat=shadow, solid=False)
    for sx in (-1, 1):
        m.box("Rope", bx + sx * (wide / 2 - 8), 0, 80, 8, RAV * 2 + 100, 8, mat=rope, solid=False)
        for k in (-1, 0, 1):
            m.column("RopePost", bx + sx * (wide / 2 - 8), k * (RAV - 20), 0, 120, 20, mat=wood, solid=False)
    m.box("Flag", bx, RAV + 20, 330, 160, 6, 100, mat=cloth if bx else cloth2, solid=False)
    m.column("FlagPole", bx, RAV + 20, 0, 400, 14, mat=wood, solid=False)
    m.column("FlagPole2", bx, -RAV - 20, 0, 400, 14, mat=wood, solid=False)
    m.box("Flag2", bx, -RAV - 20, 330, 160, 6, 100, mat=cloth2 if bx else cloth, solid=False)

# ---------------------------------------------------------------- ramps to the mesas
for sx in (-1, 1):
    for sy in (-1, 1):
        m.slope("MesaRamp", (sx * 1500, sy * 1700, 0), (sx * FX, sy * 1700, MESA_Z), 480, thickness=60, mat=pale)
        for k in range(8):                                        # stone stripes on the ramp
            f = (k + 0.5) / 8
            m.box("RampMark", sx * (1500 + f * 1500), sy * 1700, MESA_Z * f + 3, 8, 480, 6, mat=shadow, solid=False)

# ---------------------------------------------------------------- spires beside the mesas, planks, pads
SPIRE_X = FX - 550
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * SPIRE_X, sy * 900
        m.column("SpireBase", x, y, -300, 250, 640, mat=red)
        m.column("SpireMid", x, y, 250, 520, 560, mat=orange)
        m.column("SpireTop", x, y, 520, MESA_Z, 520, mat=pale)
        m.column("SpireCap", x, y, MESA_Z - 12, MESA_Z, 540, mat=sand)
        # plank bridge to the mesa edge
        m.box("SpirePlank", sx * (FX - 150), y, MESA_Z - 15, 520, 260, 30, mat=wood)
        m.box("SpirePlankEdge", sx * (FX - 150), y + 135, MESA_Z + 5, 520, 8, 8, mat=rope, solid=False)
        m.box("SpirePlankEdge", sx * (FX - 150), y - 135, MESA_Z + 5, 520, 8, 8, mat=rope, solid=False)
        # pad on the floor that lands on the spire top
        px = sx * (SPIRE_X - 1100)
        m.jump_pad("SpirePad_%d_%d" % (sx, sy), px, y + sy * 0, 0, (x, y, MESA_Z), color=(1.0, 0.6, 0.15), apex_extra=140.0)
        m.box("PadStones", px, y, 2, 420, 420, 4, mat=shadow, solid=False)

# ---------------------------------------------------------------- floor cover: big rocks, slabs, arches
rocks = [(-2200, 1300, 600, 380, 440), (-1000, 1900, 420, 520, 300), (800, 1500, 500, 420, 520), (900, 2050, 380, 400, 380),
         (-1800, -950, 520, 400, 420), (-600, -1500, 480, 520, 330), (1100, -1900, 430, 380, 480), (2200, -850, 520, 460, 400),
         (0, 900, 300, 300, 260), (0, -900, 300, 300, 260), (-1300, 700, 260, 260, 220), (1400, -700, 260, 260, 220)]
for i, (x, y, sx, sy, h) in enumerate(rocks):
    m.box("Rock_%d" % i, x, y, h / 2, sx, sy, h, yaw=rng.uniform(0, 90), mat=rng.choice(LAYERS))
    m.box("RockCap_%d" % i, x, y, h + 10, sx * 0.8, sy * 0.8, 24, yaw=rng.uniform(0, 90), mat=sand)
# natural arches: two pillars and a lintel (solid), large enough to walk under
for x, y in ((-1500, -300 - 1000), (1500, 1300)):
    m.box("ArchPillarA", x - 300, y, 300, 160, 240, 600, mat=orange)
    m.box("ArchPillarB", x + 300, y, 300, 160, 240, 600, mat=orange)
    m.box("ArchLintel", x, y, 650, 900, 260, 140, mat=red)
# boulders (decoration, no collision) and desert plants
for i in range(70):
    x, y = rng.uniform(-FX + 100, FX - 100), rng.choice((-1, 1)) * rng.uniform(RAV + 80, FY - 100)
    s = rng.uniform(40, 120)
    m._place("Pebble_%d" % i, m.cube, (x, y, s * 0.3), (s / 100, s / 100 * 1.2, s / 100 * 0.6), rng.uniform(0, 90), 0.0, rng.choice(LAYERS), False)
for i in range(16):
    x, y = rng.uniform(-FX + 200, FX - 200), rng.choice((-1, 1)) * rng.uniform(RAV + 150, FY - 150)
    m.column("Cactus", x, y, 0, rng.uniform(180, 320), 36, mat=m.material("MI_CanyonCactus", (0.12, 0.32, 0.12)), solid=False)

# mesa props: ruined walls, cover and a tent
for sx in (-1, 1):
    for i, (dx, dy, w, d, h) in enumerate([(-250, -1000, 400, 80, 200), (200, 900, 80, 400, 220), (0, 0, 300, 300, 160),
                                           (350, -300, 240, 100, 120), (-300, 450, 120, 240, 260)]):
        m.box("MesaCover_%d_%d" % (sx, i), sx * (FX + 700) + dx, dy, MESA_Z + h / 2, w, d, h, mat=rng.choice(LAYERS))
    m.box("TentPole", sx * (FX + 800), 1500, MESA_Z + 150, 20, 20, 300, mat=wood, solid=False)
    m.box("Tent", sx * (FX + 800), 1500, MESA_Z + 300, 420, 320, 16, mat=cloth if sx > 0 else cloth2, solid=False, yaw=0)

# distant mesas and buttes for the horizon (no collision)
for i in range(22):
    ang = i / 22.0 * 2 * math.pi + rng.uniform(-0.1, 0.1)
    d = rng.uniform(9000, 13000)
    h = rng.uniform(1500, 3200)
    w = rng.uniform(1200, 2600)
    m.box("Butte_%d" % i, math.cos(ang) * d * 1.2, math.sin(ang) * d * 0.8, h / 2 - 500, w, w * rng.uniform(0.6, 1.2), h + 1000,
          yaw=rng.uniform(0, 90), mat=LAYERS[i % len(LAYERS)], solid=False)
    m.box("ButteCap_%d" % i, math.cos(ang) * d * 1.2, math.sin(ang) * d * 0.8, h + 10, w * 0.9, w * 0.8, 40, mat=pale, solid=False)

# ---------------------------------------------------------------- spawns and light
m.auto_starts(12, (-FX - 1300, FX + 1300), (-FY + 100, FY - 100), [0, MESA_Z], step=200.0, seed=3, min_sep=1200.0)
m.check_starts()

m.sky(sun_pitch=-36.0, sun_yaw=215.0, sun_intensity=6.0, sun_rgb=(1.0, 0.80, 0.58), sky_intensity=1.5,
      sky_rgb=(1.0, 0.72, 0.45))
m.fog(rgb=(0.80, 0.55, 0.35), density=0.0015, falloff=0.08, start=800)
m.post(exposure_bias=-0.2, bloom=0.4)
m.finish(kill_z=-700)
