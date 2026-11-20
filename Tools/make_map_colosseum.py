"""DM-Colosseum: a Legion arena. A big sand floor (84 m x 58 m) with stands you can climb on both long sides, a ruined central dais with
stairs, broken columns and blocks as cover, two stone bridges across the arena on the stands' level, and a gate with the flag base at each end.
Run: Tools\\run_ue.ps1 -Script Tools\\make_map_colosseum.py   (arena_kit.py has the helpers)."""

import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import arena_kit as ak  # noqa: E402

A = ak.Arena("/Game/Maps/DM-Colosseum", "day_clear", seed=11)
sand = A.surf("Limestone", (176, 148, 100), "ColSand", tiling=3.0)
stone = A.surf("SandstoneBlocks", (160, 130, 92), "ColStone", tiling=2.5)
dark = A.surf("StoneDark", (110, 100, 92), "ColDark", tiling=3.0)
gold = A.surf("BrushedMetal", (226, 176, 60), "ColGold", metal=0.35)
red = A.surf("PlasterGrey", (150, 40, 34), "ColBanner")

FX, FY = 4200.0, 2900.0          # the floor: x -FX..FX, y -FY..FY
SEAT = 900.0                      # the stands: 900 cm of stairs up to 300 cm
PROM = 420.0                      # the promenade on top
# floor and the outside
A.box("Floor", -FX - 300, FX + 300, -FY - SEAT - PROM - 200, FY + SEAT + PROM + 200, -400, 0, sand)
A.box("Under", -FX - 900, FX + 900, -FY - SEAT - PROM - 900, FY + SEAT + PROM + 900, -1200, -400, dark, solid=False)
for s in (-1, 1):
    # the stands on the long sides: three flights of ten steps, a promenade, a high wall behind
    lo, hi = (FY, FY + SEAT) if s > 0 else (-FY - SEAT, -FY)
    A.stairs("Stand", "y", (FY if s > 0 else -FY), (FY + SEAT if s > 0 else -FY - SEAT), -FX, FX, 0, 300, stone, step=30.0)
    py0, py1 = (FY + SEAT, FY + SEAT + PROM) if s > 0 else (-FY - SEAT - PROM, -FY - SEAT)
    A.box("Prom", -FX, FX, py0, py1, 260, 300, stone)
    A.box("PromBody", -FX, FX, py0, py1, -40, 260, dark)
    wy0, wy1 = (py1, py1 + 150) if s > 0 else (py0 - 150, py0)
    A.box("BackWall", -FX - 300, FX + 300, wy0, wy1, 0, 1100, stone)
    for x in range(-3900, 3901, 600):
        A.col("StandCol", x, py1 - 40 if s > 0 else py0 + 40, 300, 700, 110, stone)
    A.box("Cornice", -FX - 300, FX + 300, wy0 - 40 if s > 0 else wy0, wy1 + (0 if s > 0 else 40), 1100, 1180, gold, solid=False)
# the short ends: walls with the base inside a ring of columns
for s in (-1, 1):
    ex0, ex1 = (FX, FX + 300) if s > 0 else (-FX - 300, -FX)
    A.box("EndWall", ex0, ex1, -FY, FY, 0, 1000, stone)
    A.box("EndGlow", ex0 - 6 if s > 0 else ex1, ex0 if s > 0 else ex1 + 6, -300, 300, 600, 640, A.glow("ColGlow", (1.0, 0.65, 0.2), 2.5), solid=False)
    A.base(0 if s < 0 else 1, s * 3300.0, 0.0)
    A.ring_cols("BaseCol", s * 3300.0, 0, 520, 8, 0, 520, 90, stone)
    A.box("BaseDais", s * 3300.0 - 380, s * 3300.0 + 380, -380, 380, 0, 12, gold, solid=False)
    A.light("EndLight_%d" % s, (s * 3100.0, 0, 500), (1.0, 0.7, 0.35), 150.0, 1800.0)
# the central dais: 1800 x 1100, 180 high, stairs on four sides
A.box("Dais", -900, 900, -550, 550, 0, 180, stone)
A.box("DaisTrim", -930, 930, -580, 580, 160, 190, gold, solid=False)
A.stairs("DaisW", "x", -900, -1260, -300, 300, 0, 180, stone, step=30.0)
A.stairs("DaisE", "x", 900, 1260, -300, 300, 0, 180, stone, step=30.0)
A.stairs("DaisN", "y", 550, 910, -300, 300, 0, 180, stone, step=30.0)
A.stairs("DaisS", "y", -550, -910, -300, 300, 0, 180, stone, step=30.0)
A.ring_cols("DaisCol", 0, 0, 760, 6, 180, 700, 120, stone)
# two stone bridges across the arena on the level of the promenade (reached from the stands)
for bx in (-1500.0, 1500.0):
    A.box("Bridge", bx - 210, bx + 210, -FY - SEAT - 20, FY + SEAT + 20, 250, 300, stone)
    for y in (-2000.0, -700.0, 700.0, 2000.0):
        A.col("BridgePier", bx, y, 0, 250, 200, stone)
# cover: broken columns, blocks and low walls placed with a fixed seed, away from the bases and the dais
placed = []
for i in range(34):
    for _ in range(40):
        x, y = A.rng.uniform(-3000, 3000), A.rng.uniform(-2400, 2400)
        if (abs(x) < 1250 and abs(y) < 800) or abs(abs(x) - 3300) < 700 and abs(y) < 700:
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < 420 ** 2 for px, py in placed):
            continue
        placed.append((x, y))
        if i % 3 == 0:
            A.col("Stump", x, y, 0, A.rng.uniform(220, 420), 150, stone)
        elif i % 3 == 1:
            A.boxc("Block", x, y, 0, A.rng.uniform(140, 260), 300, 160, stone, yaw=A.rng.uniform(0, 180))
        else:
            A.boxc("LowWall", x, y, 0, 120, 420, 60, dark, yaw=A.rng.choice([0.0, 90.0]))
        break
# banners on the end walls and torches by the stands
for s in (-1, 1):
    for y in (-1500.0, 1500.0):
        A.box("Banner", s * (FX - 20) - 6, s * (FX - 20) + 6, y - 180, y + 180, 380, 900, red, solid=False)
for x in range(-3600, 3601, 1200):
    for s in (-1, 1):
        A.light("Torch_%d_%d" % (x, s), (x, s * (FY + 120), 360), (1.0, 0.6, 0.25), 60.0, 900.0)
# starts: both ends, eight in the middle
A.team_starts(0, -3300.0, 0.0, 1200.0)
A.team_starts(1, 3300.0, 0.0, 1200.0)
A.mid_starts([(-2000, 1500, 0), (-2000, -1500, 0), (2000, 1500, 0), (2000, -1500, 0), (0, 1800, 0), (0, -1800, 0), (-1600, 0, 0), (1600, 0, 0)])
A.finish(kill_z=-1500)
