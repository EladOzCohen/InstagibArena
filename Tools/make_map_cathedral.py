"""DM-Cathedral: a huge gothic cathedral (96 m long) of the Hollow Court. A nave with two rows of pillars, aisles with galleries on top (stairs at both ends),
a transept across the middle, an altar dais with a blood-red window, braziers and stained glass. Run: Tools\\run_ue.ps1 -Script Tools\\make_map_cathedral.py"""

import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import arena_kit as ak  # noqa: E402

A = ak.Arena("/Game/Maps/DM-Cathedral", "dusk", seed=51, ev=1.6)
floor = A.surf("StoneSlabs", (86, 80, 82), "CatFloor", tiling=3.0)
wall = A.surf("BasaltDark", (62, 56, 58), "CatWall", tiling=2.5)
pillar = A.surf("StoneDark", (92, 84, 84), "CatPillar", tiling=2.0)
gold = A.surf("BrushedMetal", (200, 150, 50), "CatGold", metal=0.4)
red = A.glow("CatRed", (1.0, 0.1, 0.08), 3.5)
purple = A.glow("CatPurple", (0.55, 0.2, 1.0), 3.0)
amber = A.glow("CatAmber", (1.0, 0.6, 0.15), 3.0)
blue = A.glow("CatBlue", (0.2, 0.45, 1.0), 3.0)

NX, NY, TX, H = 1900.0, 4800.0, 3800.0, 1800.0   # nave half width / half length, transept half length, wall height
A.box("Floor", -NX, NX, -NY, NY, -300, 0, floor)
A.box("Transept", -TX, TX, -700, 700, -300, 0, floor)
A.box("Under", -TX - 600, TX + 600, -NY - 600, NY + 600, -1200, -300, wall, solid=False)
# walls (the transept makes a cross)
A.box("WallW", -NX - 300, -NX, -NY, -700, 0, H, wall)
A.box("WallW2", -NX - 300, -NX, 700, NY, 0, H, wall)
A.box("WallE", NX, NX + 300, -NY, -700, 0, H, wall)
A.box("WallE2", NX, NX + 300, 700, NY, 0, H, wall)
A.box("WallS", -NX - 300, NX + 300, -NY - 300, -NY, 0, H, wall)
A.box("WallN", -NX - 300, NX + 300, NY, NY + 300, 0, H, wall)
A.box("TrWallW", -TX - 300, -TX, -700, 700, 0, H, wall)
A.box("TrWallE", TX, TX + 300, -700, 700, 0, H, wall)
A.box("TrWallSW", -TX, -NX - 300, -1000, -700, 0, H, wall)
A.box("TrWallNW", -TX, -NX - 300, 700, 1000, 0, H, wall)
A.box("TrWallSE", NX + 300, TX, -1000, -700, 0, H, wall)
A.box("TrWallNE", NX + 300, TX, 700, 1000, 0, H, wall)
A.box("Roof", -TX - 300, TX + 300, -NY - 300, NY + 300, H, H + 200, wall)
# the pillar rows (x = +-900) and the galleries over the aisles (x 950..1900) at 420 cm, stairs at both ends
for s in (-1, 1):
    for y in range(-4000, 4001, 800):
        if abs(y) < 800:
            continue
        A.col("Pillar", s * 900.0, y, 0, 1400, 260, pillar)
        A.col("PillarCap", s * 900.0, y, 1400, 1480, 340, gold, solid=False)
    gx0, gx1 = (950.0, NX) if s > 0 else (-NX, -950.0)
    for seg in ((-4400.0, -1900.0), (1900.0, 4400.0)):
        A.box("Gallery", gx0, gx1, seg[0], seg[1], 380, 420, pillar)
        A.box("GalleryRail", gx0 if s > 0 else gx1 - 14, gx0 + 14 if s > 0 else gx1, seg[0], seg[1], 420, 520, red, solid=False)
    # stairs up to the galleries from the aisles, in the far corners
    A.stairs("GalStair", "y", -900.0, -1900.0, gx0 + 120, gx1 - 120, 0, 420, pillar, step=30.0)
    A.stairs("GalStair", "y", 900.0, 1900.0, gx0 + 120, gx1 - 120, 0, 420, pillar, step=30.0)
# the altar dais at the north end: three wide steps, an altar block, a huge blood-red window behind
A.box("Dais1", -1100, 1100, 3500, 4200, 0, 40, pillar)
A.box("Dais2", -850, 850, 3800, 4200, 0, 80, pillar)
A.box("Dais3", -600, 600, 4050, 4300, 0, 120, pillar)
A.box("Altar", -280, 280, 4150, 4450, 120, 260, gold)
A.box("Window", -420, 420, NY - 6, NY, 500, 1500, red, solid=False)
A.box("WindowL", -1000, -520, NY - 6, NY, 500, 1500, purple, solid=False)
A.box("WindowR", 520, 1000, NY - 6, NY, 500, 1500, purple, solid=False)
A.light("AltarLight", (0, 4000, 900), (1.0, 0.15, 0.1), 400.0, 3500.0)
# stained glass on the long walls and the transept ends
for y in range(-4200, 4201, 700):
    if abs(y) < 1100:
        continue
    for s, g in ((-1, blue), (1, amber)):
        A.box("Glass", (-NX - 6) if s < 0 else NX, (-NX) if s < 0 else NX + 6, y - 180, y + 180, 600, 1400, g if (y // 700) % 2 else purple, solid=False)
A.box("GlassTW", -TX - 6, -TX, -350, 350, 600, 1500, blue, solid=False)
A.box("GlassTE", TX, TX + 6, -350, 350, 600, 1500, amber, solid=False)
# braziers along the nave: a bowl on a post with a glowing flame
for y in range(-3600, 3601, 1200):
    for s in (-1, 1):
        if abs(y) < 1000:
            continue
        A.col("BrazierPost", s * 600.0, y, 0, 160, 50, gold)
        A.col("BrazierBowl", s * 600.0, y, 160, 210, 150, gold)
        A.col("BrazierFlame", s * 600.0, y, 210, 330, 90, amber, solid=False)
        A.light("Brazier_%d_%d" % (s, y), (s * 600.0, y, 360), (1.0, 0.5, 0.2), 50.0, 800.0)
# the crossing: a low round dais, four low walls as cover, and cover blocks in the nave
A.col("Crossing", 0, 0, 0, 40, 900, pillar)
for dx, dy in ((-1400, 0), (1400, 0), (0, -2000), (0, 2000), (-2600, 0), (2600, 0)):
    A.boxc("Block", dx, dy, 0, 150, 360, 160, pillar, yaw=0.0 if dy == 0 else 90.0)
for y in (-2800.0, -1800.0, 1800.0, 2800.0):
    A.boxc("Sarcophagus", 0, y, 0, 140, 320, 120, wall)
# starts: red at the south, blue at the north (they face each other along y)
A.base(0, 0.0, -4000.0)
A.base(1, 0.0, 3300.0)
A.team_starts(0, 0.0, -4000.0, 1400.0, along="x", yaw=90.0)
A.team_starts(1, 0.0, 3200.0, 1400.0, along="x", yaw=270.0)
A.mid_starts([(-3000, 0, 0), (3000, 0, 0), (-1400, -2000, 0), (1400, 2000, 0), (-1400, 2000, 0), (1400, -2000, 0), (1500, -3000, 420), (-1500, 3000, 420)])
A.finish(kill_z=-1500)
