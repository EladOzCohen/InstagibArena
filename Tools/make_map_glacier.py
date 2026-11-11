"""DM-Glacier: an arctic research outpost on a snow plateau. Medium arena (4-8 players).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_glacier.py" -unattended -nullrhi -nosplash

Layout: a central ice ridge with a radio relay deck on top (stairs from the ridge, jump pads from the north and south
snow fields), two huts with walkable roofs, two covered ice tunnels, pines and ice spires for cover, a wall of ice
around the plateau.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
from mapkit import MapBuilder

m = MapBuilder("/Game/Maps/DM-Glacier")
rng = random.Random(88)

snow = m.material("MI_GlacierSnow", (0.78, 0.82, 0.88), 0.9)
snow2 = m.material("MI_GlacierSnowShade", (0.62, 0.70, 0.80), 0.9)
ice = m.material("MI_GlacierIce", (0.42, 0.68, 0.85), 0.15)
deepice = m.material("MI_GlacierDeepIce", (0.18, 0.40, 0.62), 0.2)
rock = m.material("MI_GlacierRock", (0.20, 0.22, 0.26), 0.8)
hutred = m.material("MI_GlacierHutRed", (0.62, 0.12, 0.08), 0.6)
hutgrey = m.material("MI_GlacierHutGrey", (0.30, 0.38, 0.45), 0.6)
metal = m.material("MI_GlacierMetal", (0.45, 0.48, 0.52), 0.4)
wood = m.material("MI_GlacierWood", (0.30, 0.18, 0.09), 0.85)
pine = m.material("MI_GlacierPine", (0.06, 0.22, 0.12), 0.9)
crystal = m.glow("MI_GlacierCrystal", (0.25, 0.75, 1.0), 2.0)
window = m.glow("MI_GlacierWindow", (1.0, 0.75, 0.35), 1.6)
beacon = m.glow("MI_GlacierBeacon", (1.0, 0.1, 0.05), 5.0)

COLD, WARM = (0.4, 0.75, 1.0), (1.0, 0.7, 0.35)
_pl = m.point_light
m.point_light = lambda label, loc, rgb, intensity, radius: _pl(label, loc, rgb, intensity * 0.3, radius)

HX, HY = 3200.0, 2200.0


def rot(s, x, y):
    return (x, y) if s > 0 else (-x, -y)


# ---------------------------------------------------------------- ground and perimeter
m.box("Snowfield", 0, 0, -100, HX * 2, HY * 2, 200, mat=snow)
for i in range(40):                                               # snow drifts (low cover, decoration)
    x, y = rng.uniform(-HX + 200, HX - 200), rng.uniform(-HY + 200, HY - 200)
    if abs(x) < 1100 and abs(y) < 700:
        continue
    m.box("Drift_%d" % i, x, y, 20, rng.uniform(250, 600), rng.uniform(150, 300), 40, yaw=rng.uniform(0, 180), mat=snow2,
          solid=False)

# wall of ice around the plateau, ragged on top
n = 0
for side in range(4):
    horiz = side % 2 == 0
    length = HX * 2 if horiz else HY * 2
    pos = 0.0
    while pos < length:
        w = rng.uniform(350, 700)
        h = rng.uniform(700, 1300)
        a = -(length / 2) + pos + w / 2
        off = (HY if horiz else HX) + 200
        sgn = 1 if side < 2 else -1
        cx, cy = (a, sgn * off) if horiz else (sgn * off, a)
        m.box("IceWall_%d" % n, cx, cy, h / 2 - 100, w if horiz else 400, 400 if horiz else w, h + 100,
              yaw=rng.uniform(-6, 6), mat=ice if n % 3 else deepice)
        if n % 4 == 0:
            m.box("IceGlow_%d" % n, cx - (0 if horiz else sgn * 205), cy - (sgn * 205 if horiz else 0), h * 0.45,
                  w * 0.5 if horiz else 8, 8 if horiz else w * 0.5, h * 0.6, mat=crystal, solid=False)
        pos += w
        n += 1

# distant mountains
for i in range(18):
    ang = i / 18.0 * 2 * math.pi
    d = rng.uniform(6500, 9000)
    h = rng.uniform(2500, 5000)
    m.cone("Mountain_%d" % i, math.cos(ang) * d * 1.3, math.sin(ang) * d, -300, h, rng.uniform(3500, 6000),
           mat=snow2 if i % 2 else rock, solid=False)

# ---------------------------------------------------------------- central ridge
m.box("Ridge", 0, 0, 150, 1800, 1200, 300, mat=ice)
m.box("RidgeTop", 0, 0, 302, 1700, 1100, 4, mat=snow, solid=False)
m.slope("RidgeSlopeW", (-2050, 0, 0), (-900, 0, 300), 900, thickness=60, mat=snow)
m.slope("RidgeSlopeE", (2050, 0, 0), (900, 0, 300), 900, thickness=60, mat=snow)
# cliff faces with glowing ice veins on the long sides
for sy in (-1, 1):
    for i in range(6):
        m.box("IceVein", -700 + i * 280, sy * 604, 150 + rng.uniform(-40, 60), 14, 8, rng.uniform(120, 240), mat=crystal,
              solid=False)
    m.point_light("RidgeGlow", (0, sy * 800, 120), COLD, 120.0, 1400.0)

# relay deck on the ridge
DECK_Z = 650.0
m.box("Deck", 0, 0, DECK_Z - 20, 700, 700, 40, mat=metal)
for sx in (-1, 1):
    for sy in (-1, 1):
        m.column("DeckPost", sx * 310, sy * 310, 300, DECK_Z - 40, 50, mat=metal)
m.stairs("DeckStairs", 830, 0, 300, 180, 260, 12, 29.2, 40, mat=metal)
for sy in (-1, 1):
    m.box("DeckRail", 0, sy * 345, DECK_Z + 50, 700, 10, 100, mat=metal)
m.box("DeckRailW", -345, 0, DECK_Z + 50, 10, 700, 100, mat=metal)
# the mast
for sx in (-1, 1):
    for sy in (-1, 1):
        m.column("MastLeg", sx * 60, sy * 60, DECK_Z, DECK_Z + 1100, 22, mat=metal, solid=False)
for k in range(8):
    m.box("MastBar", 0, 0, DECK_Z + 100 + k * 130, 150, 150, 10, mat=metal, solid=False)
m.box("Dish", 0, 120, DECK_Z + 1000, 24, 260, 260, yaw=0, mat=snow, solid=False)
m.column("Beacon", 0, 0, DECK_Z + 1100, DECK_Z + 1160, 40, mat=beacon, solid=False)
m.point_light("BeaconLight", (0, 0, DECK_Z + 1200), (1.0, 0.1, 0.05), 200.0, 2500.0)
for sy in (-1, 1):                                                  # pads from the snow fields to the deck
    m.jump_pad("DeckPad_%s" % ("N" if sy > 0 else "S"), 0, sy * 1450, 0, (0, sy * 120, DECK_Z), color=(0.3, 0.85, 1.0),
               apex_extra=170.0)

# ---------------------------------------------------------------- huts (door on the side that faces the ridge)
def hut(s, mat, tag):
    def P(x, y):
        return rot(s, x, y)
    x0, x1, y0, y1, wh, t = -2800.0, -2100.0, -1000.0, -400.0, 300.0, 40.0
    cx, cy = P((x0 + x1) / 2, (y0 + y1) / 2)
    # four walls; the east wall (facing the ridge) has a door gap
    for (ax, ay, sx, sy) in [((x0 + x1) / 2, y0 + t / 2, x1 - x0, t), ((x0 + x1) / 2, y1 - t / 2, x1 - x0, t),
                             (x0 + t / 2, (y0 + y1) / 2, t, y1 - y0)]:
        px, py = P(ax, ay)
        m.box("HutWall_" + tag, px, py, wh / 2, sx, sy, wh, mat=mat)
    gap = 280.0
    seg = (y1 - y0 - gap) / 2
    for sgn in (-1, 1):
        px, py = P(x1 - t / 2, (y0 + y1) / 2 + sgn * (gap / 2 + seg / 2))
        m.box("HutWallE_" + tag, px, py, wh / 2, t, seg, wh, mat=mat)
    px, py = P(x1 - t / 2, (y0 + y1) / 2)
    m.box("HutLintel_" + tag, px, py, wh - 30, t, gap, 60, mat=mat)
    px, py = cx, cy
    m.box("HutRoof_" + tag, px, py, wh + 15, x1 - x0 + 40, y1 - y0 + 40, 30, mat=snow)
    # windows and the lamp inside
    for wy in (y0 + 150, y1 - 150):
        wx, wy2 = P(x0 + 150, wy)
        m.box("HutWindow_" + tag, wx, wy2, 180, 140, 10, 90, mat=window, solid=False)
    wx, wy2 = P((x0 + x1) / 2, y0 - 4)
    m.box("HutWindowS_" + tag, wx, wy2, 180, 160, 8, 90, mat=window, solid=False)
    m.point_light("HutLamp_" + tag, (*P((x0 + x1) / 2, (y0 + y1) / 2), 210), WARM, 140.0, 700.0)
    # a crate pile and a barrel outside
    bx, by = P(x1 + 120, y1 + 200)
    m.box("Crates_" + tag, bx, by, 60, 160, 160, 120, yaw=25, mat=wood)
    # stairs to the roof, along the north face
    sx, sy = P(-2100, -300)
    m.stairs("HutStairs_" + tag, sx, sy, 0, 180 if s > 0 else 0, 200, 11, 30, 40, mat=wood)
    # roof props
    rx, ry = P(-2650, -700)
    m.box("RoofVent_" + tag, rx, ry, wh + 90, 120, 120, 120, mat=metal)


hut(1, hutred, "W")
hut(-1, hutgrey, "E")


# ---------------------------------------------------------------- ice tunnels
def tunnel(s, tag):
    x0, x1, y0, y1 = -2900.0, -1700.0, 1150.0, 1850.0
    for ay in (y0 + 50, y1 - 50):
        px, py = rot(s, (x0 + x1) / 2, ay)
        m.box("TunnelWall_" + tag, px, py, 200, x1 - x0, 100, 400, mat=ice)
    px, py = rot(s, (x0 + x1) / 2, (y0 + y1) / 2)
    m.box("TunnelRoof_" + tag, px, py, 430, x1 - x0, y1 - y0, 60, mat=deepice)
    m.box("TunnelSnow_" + tag, px, py, 470, x1 - x0 - 100, y1 - y0 - 60, 20, mat=snow, solid=False)
    for i in range(7):
        cx = x0 + 150 + i * 150
        for ay, tilt in ((y0 + 110, 1), (y1 - 110, -1)):
            px, py = rot(s, cx, ay)
            a = m._place("Crystal_" + tag, m.cube, (px, py, rng.uniform(80, 240)),
                         (0.18, 0.18, rng.uniform(1.2, 2.4)), rng.uniform(0, 90), 0.0, crystal, False)
    for i in range(3):
        px, py = rot(s, x0 + 250 + i * 400, (y0 + y1) / 2)
        m.point_light("TunnelLight_%s%d" % (tag, i), (px, py, 300), COLD, 140.0, 700.0)
    # icicles hanging from the roof
    for i in range(10):
        px, py = rot(s, x0 + 100 + i * 110, (y0 + y1) / 2 + rng.uniform(-180, 180))
        m.cone("Icicle_" + tag, px, py, 330, 400, 40, mat=ice, solid=False)


tunnel(1, "NW")
tunnel(-1, "SE")

# ---------------------------------------------------------------- pines, ice spires, rocks
def tree(x, y, h):
    m.column("Trunk", x, y, 0, h * 0.3, 40, mat=wood)
    m.cone("PineA", x, y, h * 0.2, h * 0.7, 300 * h / 600, mat=pine)
    m.cone("PineB", x, y, h * 0.5, h, 210 * h / 600, mat=pine)
    m.cone("PineSnow", x, y, h * 0.86, h, 120 * h / 600, mat=snow, solid=False)


for i, (x, y) in enumerate([(-1500, -1500), (-900, -1700), (1500, 1500), (900, 1700), (-2900, 250), (2900, -250), (-300, 1800),
                            (300, -1800), (1700, -1500), (-1700, 1450), (2500, 1500), (-2500, -1550)]):
    tree(x, y, rng.uniform(550, 800))

for i, (x, y) in enumerate([(-1250, 1000), (1250, -1000), (-1100, -1150), (1100, 1150), (0, 2000), (0, -2000), (2400, 0),
                            (-2400, 0)]):
    h = rng.uniform(450, 700)
    m.cone("IceSpire_%d" % i, x, y, 0, h, rng.uniform(260, 380), mat=ice)
    m.cone("IceSpireCore_%d" % i, x, y, 0, h * 0.7, 120, mat=crystal, solid=False)

for i in range(8):
    x, y = rng.uniform(-2600, 2600), rng.uniform(-1700, 1700)
    if abs(x) < 1500 and abs(y) < 800:
        continue
    m.box("Rock_%d" % i, x, y, 70, rng.uniform(200, 350), rng.uniform(150, 260), rng.uniform(140, 220), yaw=rng.uniform(0, 180),
          mat=rock)

# a small generator and fuel drums by the huts
for i, (x, y) in enumerate([(-2350, -1150), (2350, 1150), (-1500, 1300), (1500, -1300)]):
    m.column("Drum_%d" % i, x, y, 0, 110, 70, mat=hutred if i % 2 else metal)
    m.column("Drum2_%d" % i, x + 80, y + 20, 0, 110, 70, mat=metal)

# ---------------------------------------------------------------- spawns and light
m.auto_starts(12, (-3000, 3000), (-2000, 2000), [0, 300, 330, 650], step=150.0, seed=11, min_sep=800.0)
m.check_starts()

m.sky(sun_pitch=-28.0, sun_yaw=60.0, sun_intensity=4.0, sun_rgb=(0.85, 0.92, 1.0), sky_intensity=1.6)
m.fog(rgb=(0.55, 0.70, 0.90), density=0.003, falloff=0.1, start=500)
m.post(exposure_bias=0.0, bloom=0.5)
m.finish(kill_z=-1500)
