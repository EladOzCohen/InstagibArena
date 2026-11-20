"""DM-Reactor: a circular reactor hall (80 m across) of a space station. A glowing reactor core in the middle, a catwalk ring at 380 cm with four ramps,
coolant tanks as cover, jump pads from the floor to the ring, and a base hall at each side. Run: Tools\\run_ue.ps1 -Script Tools\\make_map_reactor.py"""

import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import arena_kit as ak  # noqa: E402

A = ak.Arena("/Game/Maps/DM-Reactor", "space_derelict", seed=41, ev=2.0, ambient_gain=10.0)
floor = A.surf("DiamondPlateDark", (104, 108, 116), "RctFloor", tiling=3.0)
wall = A.surf("SteelDark", (84, 90, 100), "RctWall")
trim = A.surf("BrushedMetal", (150, 156, 168), "RctTrim", metal=0.5)
orange = A.glow("RctOrange", (1.0, 0.5, 0.1), 3.5)
blue = A.glow("RctBlue", (0.15, 0.5, 1.0), 3.0)
red = A.glow("RctRed", (1.0, 0.12, 0.08), 3.0)

R = 4000.0
A.col("Disc", 0, 0, -500, 0, 2 * R, floor)
A.col("DiscUnder", 0, 0, -3000, -500, 2 * R - 1500, wall, solid=False)
# the outer wall: 24 segments
SEG = 24
for k in range(SEG):
    a = math.radians(k * 360.0 / SEG)
    x, y = math.cos(a) * (R + 100), math.sin(a) * (R + 100)
    A.boxc("Wall", x, y, 0, 1500, 2 * math.pi * R / SEG + 60, 220, wall, yaw=math.degrees(a) + 90)
    if k % 2 == 0:
        A.boxc("WallStrip", math.cos(a) * (R - 20), math.sin(a) * (R - 20), 760, 800, 2 * math.pi * R / SEG * 0.8, 10, orange if k % 4 == 0 else blue, solid=False, yaw=math.degrees(a) + 90)
# the reactor: a base, a core column and a glowing shell
A.col("ReactorBase", 0, 0, 0, 160, 2100, trim)
A.col("ReactorCore", 0, 0, 160, 1900, 1000, wall)
A.col("ReactorGlow", 0, 0, 260, 1700, 1060, orange, solid=False)
A.col("ReactorCap", 0, 0, 1900, 2000, 1300, trim, solid=False)
A.light("ReactorLight", (0, 0, 800), (1.0, 0.5, 0.2), 300.0, 3600.0)
# the catwalk ring at 380 cm: 24 segments between radius 1700 and 2300, four ramps down to the floor
RING_IN, RING_OUT, RZ = 1750.0, 2350.0, 380.0
for k in range(SEG):
    a = math.radians(k * 360.0 / SEG)
    rm = (RING_IN + RING_OUT) / 2.0
    A.boxc("Ring", math.cos(a) * rm, math.sin(a) * rm, RZ - 40, RZ, 2 * math.pi * rm / SEG + 70, RING_OUT - RING_IN, trim, yaw=math.degrees(a) + 90)
    if k % 3 == 0:
        A.col("RingLeg", math.cos(a) * rm, math.sin(a) * rm, 0, RZ - 40, 140, wall)
    A.boxc("RingEdge", math.cos(a) * (RING_OUT + 8), math.sin(a) * (RING_OUT + 8), RZ, RZ + 14, 2 * math.pi * RING_OUT / SEG + 60, 16, blue, solid=False, yaw=math.degrees(a) + 90)
for deg in (45.0, 135.0, 225.0, 315.0):
    a = math.radians(deg)
    p0 = (math.cos(a) * 3500.0, math.sin(a) * 3500.0, 0.0)
    p1 = (math.cos(a) * 2330.0, math.sin(a) * 2330.0, RZ)
    A.ramp("RingRamp", p0, p1, 440.0, trim)
# four bridges from the ring to the reactor's base platform (a small deck at the same height)
A.col("CoreDeck", 0, 0, RZ - 40, RZ, 2300, trim, solid=False)
for deg in (0.0, 90.0, 180.0, 270.0):
    a = math.radians(deg)
    A.boxc("Bridge", math.cos(a) * 1500, math.sin(a) * 1500, RZ - 40, RZ, 600, 360, trim, yaw=deg)
# cover on the floor: coolant tanks and pipes
for i in range(18):
    ang = math.radians(i * 20.0 + 10.0)
    rr = 2900.0 + (i % 2) * 250.0
    if i % 6 == 0:
        continue
    A.col("Tank", math.cos(ang) * rr, math.sin(ang) * rr, 0, 520, 380, wall)
    A.col("TankBand", math.cos(ang) * rr, math.sin(ang) * rr, 260, 290, 400, blue, solid=False)
for deg in (0.0, 90.0, 180.0, 270.0):
    a = math.radians(deg)
    A.boxc("Wall1", math.cos(a) * 1250, math.sin(a) * 1250, 0, 220, 360, 80, wall, yaw=deg + 90)
# jump pads floor -> ring
for deg in (0.0, 90.0, 180.0, 270.0):
    a = math.radians(deg)
    A.pad("RingPad_%d" % int(deg), math.cos(a) * 3000.0, math.sin(a) * 3000.0, 0.0, (math.cos(a) * 2050.0, math.sin(a) * 2050.0, RZ), color=(0.3, 0.7, 1.0), apex_extra=140.0)
# the bases on the west and east, in front of the wall, with a red or blue light
for s in (-1, 1):
    bx = s * 3300.0
    A.base(0 if s < 0 else 1, bx, 0.0)
    A.light("BaseLight_%d" % s, (bx, 0, 520), (1.0, 0.25, 0.15) if s < 0 else (0.25, 0.4, 1.0), 180.0, 1800.0)
    for k in range(16):
        a = k / 16.0 * 2 * math.pi
        A.boxc("BaseRing", bx + math.cos(a) * 360, math.sin(a) * 360, 0, 6, 50, 50, red if s < 0 else blue, solid=False)
A.team_starts(0, -3350.0, 0.0, 1200.0)
A.team_starts(1, 3350.0, 0.0, 1200.0)
A.mid_starts([(0, 3000, 0), (0, -3000, 0), (1000, 1000, 0), (-1000, -1000, 0), (2050, 0, 380), (-2050, 0, 380), (0, 2050, 380), (0, -2050, 380)])
A.finish(kill_z=-1600)
