"""DM-ThroneHall: a long hall (108 m x 40 m) with a throne at each end (the flag bases), a deep channel across the middle (fall = out) with three bridges and two jump pads,
rows of columns, galleries on both long sides and banners. Made for Capture the Flag. Run: Tools\\run_ue.ps1 -Script Tools\\make_map_thronehall.py"""

import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import arena_kit as ak  # noqa: E402

A = ak.Arena("/Game/Maps/DM-ThroneHall", "dusk", seed=61, ev=1.4)
floor = A.surf("StoneSlabs", (126, 112, 98), "ThrFloor", tiling=3.0)
wall = A.surf("BrickDark", (84, 66, 56), "ThrWall", tiling=2.0)
pillar = A.surf("SandstoneBlocks", (170, 140, 104), "ThrPillar", tiling=2.5)
gold = A.surf("BrushedMetal", (230, 180, 60), "ThrGold", metal=0.45)
banner_r = A.surf("PlasterGrey", (150, 30, 28), "ThrBannerR")
banner_b = A.surf("PlasterGrey", (30, 56, 150), "ThrBannerB")
lava = A.glow("ThrLava", (1.0, 0.35, 0.05), 3.0)
red = A.glow("ThrRed", (1.0, 0.2, 0.15), 2.5)
blue = A.glow("ThrBlue", (0.25, 0.45, 1.0), 2.5)

HX, HY, H = 5400.0, 1900.0, 1500.0
GAP = 450.0                      # the channel: x -GAP..GAP
for s in (-1, 1):
    x0, x1 = (GAP, HX) if s > 0 else (-HX, -GAP)
    A.box("Floor", x0, x1, -HY, HY, -300, 0, floor)
A.box("ChannelBed", -GAP - 200, GAP + 200, -HY, HY, -1500, -1200, lava, solid=False)
A.box("ChannelWall", -GAP - 200, -GAP, -HY, HY, -1500, -300, wall, solid=False)
A.box("ChannelWall", GAP, GAP + 200, -HY, HY, -1500, -300, wall, solid=False)
A.box("Under", -HX - 400, HX + 400, -HY - 400, HY + 400, -1800, -1500, wall, solid=False)
A.light("ChannelGlow", (0, 0, -700), (1.0, 0.4, 0.1), 500.0, 3000.0)
A.box("WallN", -HX - 300, HX + 300, HY, HY + 300, 0, H, wall)
A.box("WallS", -HX - 300, HX + 300, -HY - 300, -HY, 0, H, wall)
A.box("WallE", HX, HX + 300, -HY, HY, 0, H, wall)
A.box("WallW", -HX - 300, -HX, -HY, HY, 0, H, wall)
A.box("Roof", -HX - 300, HX + 300, -HY - 300, HY + 300, H, H + 200, wall)
# three bridges across the channel (flat, 380 wide) and two jump pads on each side that throw you over
for y in (-1100.0, 0.0, 1100.0):
    A.box("Bridge", -GAP - 150, GAP + 150, y - 190, y + 190, -30, 0, pillar)
    A.box("BridgeGlow", -GAP - 150, GAP + 150, y - 190, y - 175, 0, 6, gold, solid=False)
for y in (-1550.0, 1550.0):
    A.pad("ChannelPad_W%d" % int(y), -GAP - 700, y, 0.0, (GAP + 700, y, 0.0), color=(1.0, 0.5, 0.15), apex_extra=240.0)
    A.pad("ChannelPad_E%d" % int(y), GAP + 700, y, 0.0, (-GAP - 700, y, 0.0), color=(1.0, 0.5, 0.15), apex_extra=240.0)
# galleries on both long sides at 420 cm (500 deep) with stairs at four places
for s in (-1, 1):
    y0, y1 = (HY - 500, HY) if s > 0 else (-HY, -HY + 500)
    for sx in (-1, 1):
        gx0, gx1 = (GAP + 2100, HX - 700) if sx > 0 else (-HX + 700, -GAP - 2100)
        A.box("Gallery", gx0, gx1, y0, y1, 380, 420, pillar)
        A.box("GalleryBody", gx0, gx1, y0, y1, 300, 380, wall, solid=False)
        for x in range(int(gx0) + 200, int(gx1), 900):
            A.col("GalCol", x, y0 + (40 if s > 0 else 460), 0, 380, 130, pillar)
        A.ramp("GalRamp", ((gx0 - 1580) if sx > 0 else (gx1 + 1580), (y0 + y1) / 2.0, 0), (gx0 if sx > 0 else gx1, (y0 + y1) / 2.0, 420), 400, pillar)
# the column rows and the thrones
for x in range(-4800, 4801, 800):
    if abs(x) < 900:
        continue
    for y in (-900.0, 900.0):
        A.col("Col", x, y, 0, 1200, 220, pillar)
        A.col("ColCap", x, y, 1200, 1260, 300, gold, solid=False)
for s in (-1, 1):
    tx = s * 4700.0
    A.box("Throne1", tx - 600, tx + 600, -700, 700, 0, 30, pillar)
    A.box("Throne2", tx - 420, tx + 420, -520, 520, 0, 60, pillar)
    A.base(0 if s < 0 else 1, tx, 0.0, z=64.0)
    A.box("ThroneBack", s * (HX - 40) - 40, s * (HX - 40) + 40, -300, 300, 60, 900, gold)
    A.box("Seat", s * (HX - 220) - 100, s * (HX - 220) + 100, -170, 170, 60, 200, gold)
    A.box("Banner", s * (HX - 8) - 6, s * (HX - 8) + 6, -1300, -700, 300, 1100, banner_r if s < 0 else banner_b, solid=False)
    A.box("Banner", s * (HX - 8) - 6, s * (HX - 8) + 6, 700, 1300, 300, 1100, banner_r if s < 0 else banner_b, solid=False)
    A.light("ThroneLight_%d" % s, (tx, 0, 650), (1.0, 0.25, 0.15) if s < 0 else (0.3, 0.45, 1.0), 220.0, 2200.0)
    A.box("ThroneGlow", tx - 600, tx + 600, -700, 700, 0, 6, red if s < 0 else blue, solid=False)
# cover: low walls and blocks on both sides of the channel
for sx in (-1, 1):
    for x, y in ((1600, 0), (2600, 800), (2600, -800), (3600, 0), (1300, 1300), (1300, -1300)):
        A.boxc("Block", sx * x, y, 0, 160, 340, 160, pillar, yaw=0.0 if abs(y) < 900 else 90.0)
A.team_starts(0, -4300.0, 0.0, 1400.0)
A.team_starts(1, 4300.0, 0.0, 1400.0)
A.mid_starts([(-1500, 1000, 0), (-1500, -1000, 0), (1500, 1000, 0), (1500, -1000, 0), (-2800, 1600, 420), (2800, -1600, 420), (-2800, -1600, 420), (2800, 1600, 420)])
A.finish(kill_z=-1000)
