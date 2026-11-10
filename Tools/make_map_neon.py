"""DM-Neon: a rain-slick neon street at night. Small duel arena (2-4 players), built for fast close fights.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_neon.py" -unattended -nullrhi -nosplash

Layout: one street (x -1800..1800, y -800..800) around an arcade hall in the middle. Two shop podiums with a
second roof level on opposite corners, an arcade roof that is reached by stairs or by two jump pads.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
from mapkit import MapBuilder

m = MapBuilder("/Game/Maps/DM-Neon")
rng = random.Random(404)

asphalt = m.material("MI_NeonAsphalt", (0.045, 0.045, 0.06), 0.3)
sidewalk = m.material("MI_NeonSidewalk", (0.16, 0.15, 0.20), 0.5)
brick = m.material("MI_NeonBrick", (0.20, 0.09, 0.11))
wallblue = m.material("MI_NeonWall", (0.10, 0.11, 0.19))
metal = m.material("MI_NeonMetal", (0.28, 0.30, 0.36), 0.35)
dark = m.material("MI_NeonDark", (0.03, 0.03, 0.045), 0.4)
paint = m.material("MI_NeonLine", (0.75, 0.72, 0.50), 0.6)
carA = m.material("MI_NeonCarA", (0.55, 0.05, 0.12), 0.25)
carB = m.material("MI_NeonCarB", (0.07, 0.28, 0.55), 0.25)
pink = m.glow("MI_NeonGlowPink", (1.0, 0.08, 0.55), 7.0)
cyan = m.glow("MI_NeonGlowCyan", (0.0, 0.85, 1.0), 7.0)
amber = m.glow("MI_NeonGlowAmber", (1.0, 0.55, 0.10), 6.0)
violet = m.glow("MI_NeonGlowViolet", (0.55, 0.2, 1.0), 6.0)
lime = m.glow("MI_NeonGlowLime", (0.3, 1.0, 0.35), 6.0)
warmwin = m.glow("MI_NeonWindow", (1.0, 0.75, 0.40), 2.5)
glass = m.glow("MI_NeonGlass", (0.04, 0.07, 0.12), 0.0)

PINK, CYAN, AMBER, VIOLET = (1.0, 0.1, 0.55), (0.0, 0.85, 1.0), (1.0, 0.6, 0.15), (0.6, 0.25, 1.0)
HX, HY = 1800.0, 800.0

# ---------------------------------------------------------------- street shell
m.box("Street", 0, 0, -50, HX * 2, HY * 2, 100, mat=asphalt)
for x in range(-1500, 1501, 300):                                    # dashed center line
    m.box("RoadLine", x, 0, 1.5, 150, 18, 3, mat=paint, solid=False)
for y in (-HY + 15, HY - 15):                                        # curb glow
    m.box("CurbGlow", 0, y, 2, HX * 2, 10, 4, mat=cyan, solid=False)

for sy in (-1, 1):
    m.box("Facade", 0, sy * (HY + 150), 650, HX * 2 + 600, 300, 1500, mat=brick if sy > 0 else wallblue)
for sx in (-1, 1):
    m.box("EndWall", sx * (HX + 150), 0, 650, 300, HY * 2, 1500, mat=wallblue)

# windows on the facades above the podiums
for sy in (-1, 1):
    for i, x in enumerate(range(-1650, 1651, 220)):
        for z in (800, 1050, 1300):
            on = rng.random() < 0.55
            mat = warmwin if on else glass
            m.box("Window", x, sy * (HY - 4), z, 130, 10, 140, mat=mat, solid=False)
            if on and rng.random() < 0.3:
                m.point_light("WinLight", (x, sy * (HY - 80), z), (1.0, 0.7, 0.4), 6.0, 500.0)
    # lower shop glass where there is no podium
    for x in (-500, 300, 900, 1400):
        pass

# neon signs on the facades
for sy, signs in ((1, [(900, cyan, CYAN), (-100, violet, VIOLET)]), (-1, [(-900, pink, PINK), (100, amber, AMBER)])):
    for x, mat, rgb in signs:
        m.frame("SignFrame", x, sy * (HY - 12), 880, 700, 360, 24, 20, 0, mat, solid=False)
        m.box("SignPanel", x, sy * (HY - 8), 1060, 640, 8, 280, mat=dark, solid=False)
        for k in range(4):
            m.box("SignBar", x, sy * (HY - 14), 960 + k * 70, 480 - 70 * (k % 2), 8, 24, mat=mat, solid=False)
        m.point_light("SignLight", (x, sy * (HY - 150), 1000), rgb, 90.0, 1400.0)

# vertical blade signs sticking out into the street
for x, sy, mat, rgb in [(-1250, 1, pink, PINK), (1250, -1, cyan, CYAN), (400, 1, lime, (0.3, 1, 0.4)), (-400, -1, amber, AMBER)]:
    m.box("BladeMount", x, sy * (HY - 80), 760, 20, 160, 20, mat=metal, solid=False)
    m.box("BladeSign", x, sy * (HY - 160), 880, 22, 40, 320, mat=mat, solid=False)
    m.point_light("BladeLight", (x, sy * (HY - 260), 880), rgb, 40.0, 900.0)


# ---------------------------------------------------------------- podiums (north one built, south one is its mirror)
def side(s):
    """s = +1 builds the north podium group, s = -1 the south one (rotated 180 degrees)."""
    def P(x, y):
        return (s * x, s * y)
    yawo = 0.0 if s > 0 else 180.0
    tag = "N" if s > 0 else "S"
    # lower podium (z 300)
    x, y = P(-1200, 610)
    m.box("Podium1_" + tag, x, y, 150, 1000, 380, 300, mat=sidewalk)
    # upper podium (z 600)
    x, y = P(-1375, 610)
    m.box("Podium2_" + tag, x, y, 450, 650, 380, 300, mat=sidewalk)
    # stairs
    x, y = P(-300, 610)
    m.stairs("StairsA_" + tag, x, y, 0, 180 + yawo, 260, 10, 30, 40, mat=metal)
    x, y = P(-750, 520)
    m.stairs("StairsB_" + tag, x, y, 300, 180 + yawo, 220, 10, 30, 30, mat=metal)
    # glowing edge lines along the street side of each podium
    x, y = P(-1200, 421)
    m.box("Edge1_" + tag, x, y, 302, 1000, 10, 6, mat=pink if s > 0 else cyan, solid=False)
    x, y = P(-1375, 421)
    m.box("Edge2_" + tag, x, y, 602, 650, 10, 6, mat=pink if s > 0 else cyan, solid=False)
    # railings on the open sides
    x, y = P(-1200, 424)
    m.box("Rail1_" + tag, x, y, 340, 1000, 12, 80, mat=metal)
    x, y = P(-1375, 424)
    m.box("Rail2_" + tag, x, y, 640, 650, 12, 80, mat=metal)
    # shop awning and a vent unit up top
    x, y = P(-1500, 700)
    m.box("Vent_" + tag, x, y, 680, 220, 160, 160, mat=metal)
    x, y = P(-1250, 650)
    m.box("Crate_" + tag, x, y, 355, 120, 120, 110, yaw=20, mat=brick)
    # pad from the street lane to the arcade roof
    x, y = P(0, 650)
    m.jump_pad("RoofPad_" + tag, x, y, 0, (0, s * 250, 700), color=CYAN if s > 0 else PINK)
    # lane lamp posts
    for lx in (-1000, 1000):
        px, py = P(lx, 440)
        m.column("LampPost", px, py, 0, 420, 14, mat=metal)
        m.box("LampArm", px, py + (-s) * 40, 420, 20, 90, 14, mat=metal, solid=False)
        m.box("LampBulb", px, py + (-s) * 80, 410, 50, 30, 12, mat=amber, solid=False)
        m.point_light("LampLight", (px, py + (-s) * 80, 380), AMBER, 55.0, 900.0)


side(1)
side(-1)

# ---------------------------------------------------------------- arcade hall in the middle
m.box("Arcade", 0, 0, 350, 500, 860, 700, mat=wallblue)
m.box("ArcadeRoofTrim", 0, 0, 712, 540, 900, 24, mat=dark)
for sx in (-1, 1):                                                   # marquee on the long faces
    m.box("MarqueePanel", sx * 253, 0, 520, 8, 700, 130, mat=dark, solid=False)
    m.box("MarqueeA", sx * 258, -200, 520, 8, 220, 40, mat=pink, solid=False)
    m.box("MarqueeB", sx * 258, 150, 560, 8, 220, 40, mat=cyan, solid=False)
    m.box("MarqueeC", sx * 258, 150, 480, 8, 320, 40, mat=amber, solid=False)
    m.point_light("MarqueeLight", (sx * 380, 0, 520), PINK if sx > 0 else CYAN, 70.0, 1200.0)
for sy in (-1, 1):                                                   # arcade doorways facing the lanes
    m.frame("ArcadeDoor", 0, sy * 432, 0, 260, 300, 24, 16, 0, cyan if sy > 0 else pink, solid=False)
    m.box("ArcadeDoorGlow", 0, sy * 433, 150, 220, 6, 270, mat=warmwin, solid=False)
# roof access stairs along the east face (24 steps)
m.stairs("ArcadeStairs", 350, -430, 0, 90, 200, 20, 35, 42, mat=metal)
m.box("ArcadeRoofRail", 0, 0, 760, 12, 860, 80, mat=metal)
m.box("ArcadeRoofRailW", 244, 0, 760, 12, 860, 80, mat=metal)
m.point_light("RoofLight", (0, 0, 900), VIOLET, 80.0, 1400.0)
m.box("RoofAntenna", -150, 200, 950, 14, 14, 500, mat=metal, solid=False)
m.box("RoofAntennaTip", -150, 200, 1200, 24, 24, 24, mat=pink, solid=False)

# ---------------------------------------------------------------- plazas: partitions, cars, planters, gates
for sx in (-1, 1):
    m.box("PlazaWall", sx * 1550, 0, 150, 300, 40, 300, mat=brick)
    m.box("PlazaWallTrim", sx * 1550, 0, 305, 300, 44, 10, mat=lime if sx > 0 else violet, solid=False)
    m.frame("EndGate", sx * (HX - 20), 0, 0, 640, 560, 40, 30, 90, pink if sx > 0 else cyan, solid=False)
    m.box("EndGateGlow", sx * (HX - 30), 0, 280, 8, 560, 520, mat=violet, solid=False)
    m.point_light("GateLight", (sx * (HX - 200), 0, 300), PINK if sx > 0 else CYAN, 110.0, 1500.0)

m.box("CarA_body", 850, 130, 55, 460, 190, 80, yaw=12, mat=carA)
m.box("CarA_cabin", 840, 130, 125, 230, 170, 66, yaw=12, mat=dark)
m.box("CarB_body", -900, -220, 55, 460, 190, 80, yaw=-8, mat=carB)
m.box("CarB_cabin", -910, -220, 125, 230, 170, 66, yaw=-8, mat=dark)
for sx, y in ((850, 130), (-900, -220)):
    m.box("CarLights", sx, y, 62, 470, 160, 14, mat=amber, solid=False)

for i, (x, y) in enumerate([(-450, 250), (450, -250), (1200, -230), (-1200, 230), (1000, 420), (-1000, -420)]):
    m.box("Planter_%d" % i, x, y, 45, 220, 90, 90, mat=sidewalk)
    m.box("PlanterGlow_%d" % i, x, y, 96, 200, 70, 10, mat=lime, solid=False)

for i, (x, y, yaw) in enumerate([(1650, -700, 0), (-1650, 700, 0), (-60, 770, 0), (60, -770, 0)]):
    m.box("Dumpster_%d" % i, x, y, 70, 200, 110, 140, yaw=yaw, mat=m.material("MI_NeonDumpster", (0.08, 0.30, 0.20)))

# ---------------------------------------------------------------- backdrop skyline (no collision)
for i in range(30):
    ang = i / 30.0 * 2 * math.pi
    dist = rng.uniform(3200, 5200)
    h = rng.uniform(1800, 4500)
    x, y = math.cos(ang) * dist * 1.25, math.sin(ang) * dist * 0.9
    m.box("Skyline_%d" % i, x, y, h / 2 - 500, rng.uniform(500, 900), rng.uniform(500, 900), h, yaw=rng.uniform(0, 90),
          mat=dark, solid=False)
    for k in range(3):
        m.box("SkylineLit_%d_%d" % (i, k), x, y, rng.uniform(300, h - 300), 520, 520, 40,
              yaw=0, mat=rng.choice([pink, cyan, violet, amber]), solid=False)

# ---------------------------------------------------------------- spawns
starts = [
    (-1500, 600, 600, 0), (-900, 700, 300, 0), (1500, -600, 600, 180), (900, -700, 300, 180),
    (-1650, -300, 0, 20), (-1650, 300, 0, -20), (1650, 300, 0, 200), (1650, -300, 0, 160),
    (-700, -650, 0, 0), (700, 650, 0, 180),
]
m.starts(starts)
m.check_starts()

# ---------------------------------------------------------------- light: night
m.sky(sun_pitch=-35.0, sun_yaw=210.0, sun_intensity=0.9, sun_rgb=(0.45, 0.55, 1.0), sky_intensity=0.35)
m.fog(rgb=(0.20, 0.10, 0.35), density=0.012, falloff=0.25, start=300)
m.point_light("FillCyan", (0, 0, 650), (0.3, 0.7, 1.0), 120.0, 3500.0)
m.finish(kill_z=-1200)
