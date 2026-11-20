"""DM-Casino: a grand hall (90 m x 60 m) of the Neon Syndicate. Red carpet floor, a lit fountain in the middle, rows of slot machines and two bars as cover,
mezzanines along both long walls with stairs at the ends, a skybridge across, neon strips on the walls. Run: Tools\\run_ue.ps1 -Script Tools\\make_map_casino.py"""

import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import arena_kit as ak  # noqa: E402

A = ak.Arena("/Game/Maps/DM-Casino", "night_city", seed=31)
carpet = A.surf("PlasterGrey", (92, 22, 38), "CasCarpet", tiling=3.0)
marble = A.surf("Limestone", (200, 196, 190), "CasMarble", tiling=2.5)
wall = A.surf("PlasterGrey", (52, 40, 58), "CasWall", tiling=2.0)
wood = A.surf("WoodPlanksOld", (96, 58, 36), "CasWood")
gold = A.surf("BrushedMetal", (226, 176, 60), "CasGold", metal=0.4)
dark = A.surf("SteelDark", (30, 30, 36), "CasDark")
pink = A.glow("CasPink", (1.0, 0.15, 0.7), 3.0)
cyan = A.glow("CasCyan", (0.1, 0.85, 1.0), 3.0)
amber = A.glow("CasAmber", (1.0, 0.7, 0.2), 2.5)

FX, FY, CEIL = 4500.0, 3000.0, 1200.0
A.box("Floor", -FX - 300, FX + 300, -FY - 300, FY + 300, -300, 0, carpet)
A.box("WallN", -FX - 300, FX + 300, FY, FY + 300, 0, CEIL, wall)
A.box("WallS", -FX - 300, FX + 300, -FY - 300, -FY, 0, CEIL, wall)
A.box("WallE", FX, FX + 300, -FY, FY, 0, CEIL, wall)
A.box("WallW", -FX - 300, -FX, -FY, FY, 0, CEIL, wall)
# neon strips and a gold dado on the walls
for i, g in enumerate((pink, cyan)):
    for y in (FY - 4, -FY + 4):
        A.box("Neon", -FX, FX, y - 6, y + 6, 880 + i * 120, 910 + i * 120, g, solid=False)
    for x in (FX - 4, -FX + 4):
        A.box("NeonEnd", x - 6, x + 6, -FY, FY, 880 + i * 120, 910 + i * 120, g, solid=False)
A.box("Dado", -FX, FX, FY - 30, FY, 0, 120, gold, solid=False)
A.box("DadoS", -FX, FX, -FY, -FY + 30, 0, 120, gold, solid=False)
# the fountain: a round marble basin with a glowing ring and a tall light column
A.col("Basin", 0, 0, 0, 110, 1500, marble)
A.col("BasinRing", 0, 0, 100, 118, 1380, cyan, solid=False)
A.col("Fountain", 0, 0, 110, 520, 220, marble)
A.col("FountainTop", 0, 0, 520, 760, 460, pink, solid=False)
A.light("FountainLight", (0, 0, 640), (1.0, 0.4, 0.8), 260.0, 2600.0)
A.ring_cols("HallCol", 0, 0, 1700, 10, 0, CEIL, 200, marble)
# mezzanines: 700 deep platforms at 420 cm along both long walls, stairs at both ends, a skybridge across the middle
for s in (-1, 1):
    y0, y1 = (FY - 700, FY) if s > 0 else (-FY, -FY + 700)
    A.box("Mezz", -3000, 3000, y0, y1, 380, 420, marble)
    A.box("MezzBody", -3000, 3000, y0, y1, 300, 380, dark, solid=False)
    for x in range(-3400, 3401, 1130):
        A.col("MezzCol", x, y0 + (40 if s > 0 else 660), 0, 380, 150, marble)
    A.box("Rail", -3000, 3000, (y0 - 12) if s > 0 else (y1 + 2), (y0 - 2) if s > 0 else (y1 + 12), 420, 520, cyan, solid=False)
    for ex in (-1, 1):
        xa = ex * 3000.0
        # a ramp (16 degrees: the bots do not use steps this shallow) from the floor up to the mezzanine's end
        A.ramp("MezzRamp", (xa + ex * 1450, (y0 + y1) / 2.0, 0), (xa, (y0 + y1) / 2.0, 420), 400, marble)
A.box("Skybridge", -300, 300, -FY + 700, FY - 700, 380, 420, marble)
A.box("SkybridgeGlow", -300, 300, -FY + 700, FY - 700, 372, 380, pink, solid=False)
for y in (-1400.0, 0.0, 1400.0):
    A.col("BridgePier", 0, y, 0, 380, 200, marble)
# cover: slot machine rows, two long bars, round tables
for row_y in (-1800.0, -900.0, 900.0, 1800.0):
    for k in range(9):
        x = -3200.0 + k * 800.0
        if abs(x) < 1100 and abs(row_y) < 1000:
            continue
        A.boxc("Slot", x, row_y, 0, 200, 150, 120, dark)
        A.boxc("SlotGlow", x, row_y + (62 if row_y > 0 else -62), 120, 180, 120, 6, A.rng.choice([pink, cyan, amber]), solid=False)
for bx in (-2300.0, 2300.0):
    A.boxc("BarCounter", bx, 0, 0, 120, 360, 1900, wood)
    A.boxc("BarTop", bx, 0, 118, 130, 420, 1960, gold, solid=False)
    A.boxc("BarShelf", bx + (-260 if bx < 0 else 260), 0, 0, 380, 80, 1900, dark, solid=False)
for i in range(10):
    tx, ty = A.rng.uniform(-3600, 3600), A.rng.uniform(-1600, 1600)
    if (abs(tx) < 1900 and abs(ty) < 1900) or abs(abs(tx) - 2300) < 300:
        continue
    A.col("TableLeg", tx, ty, 0, 90, 60, dark)
    A.col("TableTop", tx, ty, 90, 110, 260, gold)
# flags: a stage at each end
for s in (-1, 1):
    bx = s * 3750.0
    A.box("Stage", bx - 450, bx + 450, -600, 600, 0, 40, marble)
    A.base(0 if s < 0 else 1, bx, 0.0)
    A.light("StageLight_%d" % s, (bx, 0, 700), (1.0, 0.3, 0.3) if s < 0 else (0.3, 0.5, 1.0), 220.0, 2200.0)
    for y in (-600, 600):
        A.col("StageCol", bx, y, 0, CEIL, 160, gold)
for x in range(-3600, 3601, 1200):
    for y in (-2000.0, 2000.0):
        A.light("Chandelier_%d_%d" % (x, y), (x, y, 1000), (1.0, 0.8, 0.6), 90.0, 1500.0)
A.team_starts(0, -3750.0, 0.0, 1400.0)
A.team_starts(1, 3750.0, 0.0, 1400.0)
A.mid_starts([(-1500, 1700, 0), (-1500, -1700, 0), (1500, 1700, 0), (1500, -1700, 0), (0, 2500, 420), (0, -2500, 420), (-2500, 2600, 420), (2500, -2600, 420)])
A.finish(kill_z=-1500)
