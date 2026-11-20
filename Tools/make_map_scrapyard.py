"""DM-Scrapyard: a big junk yard (90 m x 60 m) of the Rustborn. Container alleys, junk piles you can climb, wrecked cars, a crane deck in the middle
with two ramps, and a base in a ring of containers at each end. Run: Tools\\run_ue.ps1 -Script Tools\\make_map_scrapyard.py"""

import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import arena_kit as ak  # noqa: E402

A = ak.Arena("/Game/Maps/DM-Scrapyard", "overcast", seed=21)
dirt = A.surf("AsphaltCracked", (96, 84, 72), "ScrDirt", tiling=4.0)
conc = A.surf("ConcreteDark", (110, 108, 104), "ScrConc", tiling=3.0)
rust = A.surf("CorrugatedRust", (150, 78, 40), "ScrRust")
yellow = A.surf("ContainerYellow", (214, 168, 40), "ScrYellow")
grey = A.surf("ContainerGrey", (112, 124, 132), "ScrGrey")
steel = A.surf("SteelDark", (62, 66, 72), "ScrSteel")
glow = A.glow("ScrGlow", (1.0, 0.55, 0.15), 3.0)

FX, FY = 4500.0, 3000.0
A.box("Floor", -FX - 400, FX + 400, -FY - 400, FY + 400, -400, 0, dirt)
A.box("Under", -FX - 2000, FX + 2000, -FY - 2000, FY + 2000, -1400, -400, conc, solid=False)
# the fence walls: corrugated sheets
A.box("WallN", -FX - 400, FX + 400, FY, FY + 200, 0, 800, rust)
A.box("WallS", -FX - 400, FX + 400, -FY - 200, -FY, 0, 800, rust)
A.box("WallE", FX, FX + 200, -FY, FY, 0, 800, rust)
A.box("WallW", -FX - 200, -FX, -FY, FY, 0, 800, rust)
for x in range(-4200, 4201, 700):
    A.col("PostN", x, FY - 30, 0, 900, 90, steel)
    A.col("PostS", x, -FY + 30, 0, 900, 90, steel)

# the crane deck in the middle: 1600 x 1400 at 300 cm with a ramp on the west and east sides
A.box("Deck", -800, 800, -700, 700, 260, 300, steel)
for dx in (-700, 700):
    for dy in (-600, 600):
        A.col("DeckLeg", dx, dy, 0, 260, 140, steel)
A.ramp("DeckRampW", (-2300, 0, 0), (-800, 0, 300), 420, steel)
A.ramp("DeckRampE", (2300, 0, 0), (800, 0, 300), 420, steel)
A.boxc("CraneMast", 0, 0, 300, 1300, 220, 220, yellow, solid=False)
A.boxc("CraneArm", 0, 0, 1280, 1340, 2600, 120, yellow, solid=False, yaw=20.0)
A.col("Magnet", 1100, 330, 700, 1280, 60, steel, solid=False)
A.col("MagnetDisc", 1100, 330, 640, 700, 380, glow, solid=False)

# container alleys: rows with gaps of 380 cm
rows = [(-2200, 0), (-1000, 1), (1000, 0), (2200, 1)]
for y, stagger in rows:
    x = -3300.0 + (600.0 if stagger else 0.0)
    while x < 3300.0:
        if abs(x) < 1500 and abs(y) < 1200:
            x += 980.0
            continue
        mat = A.rng.choice([yellow, grey, rust])
        tall = A.rng.random() < 0.4
        A.boxc("Container", x, y, 0, 260, 600, 240, mat, yaw=0.0)
        if tall:
            A.boxc("ContainerTop", x + A.rng.choice([-80, 0, 80]), y, 260, 520, 600, 240, A.rng.choice([yellow, grey]), yaw=0.0)
            # a ramp of crates up to the stack: three steps of 40 cm
            for k in range(3):
                A.box("Crate", x - 300 - 120 * (k + 1), x - 300 - 120 * k, y - 140, y + 140, 0, 40 * (3 - k), rust)
        x += 980.0
# junk piles: three tiers of 40 cm so that the character can walk up
for i in range(10):
    px, py = A.rng.uniform(-3600, 3600), A.rng.uniform(-2400, 2400)
    if abs(py) < 700 and abs(px) < 2400:
        continue
    if abs(abs(px) - 3800) < 900:
        continue
    yaw = A.rng.uniform(0, 180)
    for k, (w, d) in enumerate(((760, 520), (540, 380), (340, 240))):
        A.boxc("Pile", px, py, 0, 40 * (k + 1), w, d, A.rng.choice([rust, steel, grey]), yaw=yaw)
# wrecked cars
for i in range(14):
    cx, cy = A.rng.uniform(-3800, 3800), A.rng.uniform(-2600, 2600)
    if abs(abs(cx) - 3800) < 800 or (abs(cx) < 2400 and abs(cy) < 800):
        continue
    yaw = A.rng.uniform(0, 180)
    A.boxc("CarBody", cx, cy, 0, 120, 450, 190, A.rng.choice([rust, grey, yellow]), yaw=yaw)
    A.boxc("CarCabin", cx, cy, 120, 210, 230, 170, steel, solid=False, yaw=yaw)

# bases: a ring of containers round each flag
for s in (-1, 1):
    bx = s * 3800.0
    A.base(0 if s < 0 else 1, bx, 0.0)
    for k in range(8):
        a = math.radians(k * 45.0 + 22.5)
        A.boxc("BaseBox", bx + math.cos(a) * 640, math.sin(a) * 640, 0, 220, 300, 200, yellow if s < 0 else grey, yaw=math.degrees(a) + 90)
    A.light("BaseLamp_%d" % s, (bx, 0, 520), (1.0, 0.62, 0.3) if s < 0 else (0.5, 0.65, 1.0), 160.0, 1800.0)
for x in range(-3000, 3001, 1500):
    for y in (-2500, 0, 2500):
        A.light("Lamp_%d_%d" % (x, y), (x, y, 600), (1.0, 0.85, 0.65), 70.0, 1300.0)
A.team_starts(0, -3900.0, 0.0, 1400.0)
A.team_starts(1, 3900.0, 0.0, 1400.0)
A.mid_starts([(-1800, 1800, 0), (-1800, -1800, 0), (1800, 1800, 0), (1800, -1800, 0), (0, 2500, 0), (0, -2500, 0), (-400, 0, 300), (400, 0, 300)])
A.finish(kill_z=-1500)
