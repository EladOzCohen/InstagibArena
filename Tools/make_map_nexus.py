"""DM-Nexus: the oldest arena of the Apex League, a round stone platform floating beside a black hole (campaign finale, also CTF / FFA / TDM).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_nexus.py" -unattended -nullrhi -nosplash

Layout (centimetres, a disc of 7200 across, open to space: the edge is a fall):
  * the arena floor: a stone disc; a raised dais in the middle (z 300) with four ramps (13 degrees, usable by bots), a glowing obelisk on top
  * eight arches round the rim (pillars and a lintel), eight low cover blocks around the dais
  * the two bases at x +-2750 (Red west, Blue east): a ring of light on the floor, a gold gateway behind each flag
  * jump pads from the floor to the dais, drifting rock below the disc (no collision)
Start tags: Red / Blue round the bases, 8 untagged starts round the dais.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
from mapkit import MapBuilder  # noqa: E402
from matlib import surface  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Nexus")
rng = random.Random(1919)
S = surface
m.look("space_nexus", ev=2.4, ambient_gain=14.0)

floor = S("StoneSlabs", albedo=(120, 112, 104), tiling=3.0, tag="NexFloor")
floor_dark = S("StoneDark", albedo=(92, 86, 84), tiling=3.0, tag="NexFloorDark")
dais = S("Limestone", albedo=(160, 148, 128), tiling=2.5, tag="NexDais")
pillar = S("SandstoneBlocks", albedo=(150, 128, 104), tiling=2.5, tag="NexPillar")
gold = S("BrushedMetal", albedo=(222, 170, 52), metal=0.35, tag="NexGold")
rock = S("BasaltDark", albedo=(88, 72, 66), tiling=4.0, tag="NexRock")
g_orange = m.glow("NexGlowOrange", (1.0, 0.50, 0.10), 3.0)
g_red = m.glow("NexGlowRed", (1.0, 0.10, 0.06), 3.0)
g_blue = m.glow("NexGlowBlue", (0.10, 0.30, 1.0), 3.0)
g_gold = m.glow("NexGlowGold", (1.0, 0.75, 0.25), 2.5)

_n = [0]


def B(prefix, cx, cy, z0, z1, sx, sy, mat, solid=True, yaw=0.0, pitch=0.0):
    _n[0] += 1
    return m.box("%s_%d" % (prefix, _n[0]), cx, cy, (z0 + z1) / 2.0, sx, sy, abs(z1 - z0), yaw=yaw, pitch=pitch, mat=mat, solid=solid)


def C(prefix, x, y, z0, z1, d, mat, solid=True):
    _n[0] += 1
    return m.column("%s_%d" % (prefix, _n[0]), x, y, z0, z1, d, mat=mat, solid=solid)


def P(r, deg):
    a = math.radians(deg)
    return math.cos(a) * r, math.sin(a) * r


R = 3600.0
DAIS_Z = 300.0

# ---------------------------------------------------------------- the disc
C("Arena", 0, 0, -300, 0, 2 * R, floor)
C("ArenaUnder", 0, 0, -1500, -300, 2 * R - 800, floor_dark, solid=False)
C("ArenaCore", 0, 0, -3200, -1500, 2200, rock, solid=False)
for k in range(48):
    x, y = P(R - 15, k * 7.5)
    B("RimGlow", x, y, 0, 8, 160, 40, g_orange, solid=False, yaw=k * 7.5 + 90)
for ring_r in (1900.0, 2500.0):
    for k in range(36):
        x, y = P(ring_r, k * 10.0)
        B("FloorInlay", x, y, 0, 4, 330 if ring_r < 2000 else 440, 24, floor_dark, solid=False, yaw=k * 10.0 + 90)

# ---------------------------------------------------------------- the dais and its obelisk
C("Dais", 0, 0, 0, DAIS_Z, 1900, dais)
C("DaisTrim", 0, 0, DAIS_Z - 4, DAIS_Z + 14, 1960, gold)
C("DaisGlow", 0, 0, DAIS_Z + 14, DAIS_Z + 22, 1500, g_orange, solid=False)
B("Obelisk", 0, 0, DAIS_Z, DAIS_Z + 900, 240, 240, pillar)
B("ObeliskCap", 0, 0, DAIS_Z + 900, DAIS_Z + 1020, 300, 300, gold)
B("ObeliskCore", 0, 0, DAIS_Z + 200, DAIS_Z + 800, 250, 250, g_orange, solid=False, yaw=45.0)
for deg in (45.0, 135.0, 225.0, 315.0):
    p0 = (P(2400.0, deg)[0], P(2400.0, deg)[1], 0.0)
    p1 = (P(950.0, deg)[0], P(950.0, deg)[1], DAIS_Z)
    m.slope("DaisRamp_%d" % int(deg), p0, p1, 440.0, thickness=40.0, mat=dais)
for deg in (0.0, 90.0, 180.0, 270.0):
    x, y = P(1050.0, deg)
    B("DaisBlock", x, y, DAIS_Z, DAIS_Z + 140, 260, 260, pillar)

# ---------------------------------------------------------------- eight arches round the rim, cover blocks round the dais
for k in range(8):
    deg = k * 45.0
    x, y = P(R - 380.0, deg)
    tx, ty = -math.sin(math.radians(deg)), math.cos(math.radians(deg))
    for sd in (-1, 1):
        B("ArchPillar", x + tx * sd * 330, y + ty * sd * 330, 0, 920, 150, 150, pillar)
        B("ArchBase", x + tx * sd * 330, y + ty * sd * 330, 0, 60, 230, 230, gold)
    B("ArchLintel", x, y, 920, 1030, 150, 880, pillar, yaw=deg)
    B("ArchGlow", x, y, 880, 905, 130, 640, g_orange, solid=False, yaw=deg)
    m.accent_light("ArchLight_%d" % k, (x * 0.93, y * 0.93, 600), (1.0, 0.55, 0.22), candela=95.0, radius=1400.0)
for k in range(8):
    deg = 22.5 + k * 45.0
    x, y = P(1650.0, deg)
    B("Cover", x, y, 0, 190, 360, 140, pillar, yaw=deg + 90)
    B("CoverTrim", x, y, 190, 206, 380, 160, gold, yaw=deg + 90)

# ---------------------------------------------------------------- bases: a gateway behind each flag, rings of light
for team, nm, sx in ((0, "Red", -1), (1, "Blue", 1)):
    fx = sx * 2750.0
    f = m.spawn(unreal.IAFlagBase, "FlagBase_" + nm, (fx, 0.0, 6.0))
    f.set_editor_property("flag_team", team)
    g = g_blue if team else g_red
    for k in range(2):
        r = 330.0 + k * 90.0
        for j in range(16):
            a = j / 16.0 * 2 * math.pi
            B("BaseRing", fx + math.cos(a) * r, math.sin(a) * r, 0, 6, 52, 52, g, solid=False)
    gx = sx * 3250.0
    for sd in (-1, 1):
        B("GatePillar", gx, sd * 520, 0, 1100, 170, 170, pillar)
        B("GateBase", gx, sd * 520, 0, 70, 260, 260, gold)
    B("GateLintel", gx, 0, 1100, 1230, 190, 1260, pillar)
    B("GateGlow", gx, 0, 1000, 1030, 150, 860, g, solid=False)
    m.accent_light("BaseLight_" + nm, (fx, 0, 520), (0.25, 0.4, 1.0) if team else (1.0, 0.25, 0.18), candela=160.0, radius=1800.0)

# ---------------------------------------------------------------- jump pads floor -> dais
for deg in (0.0, 90.0, 180.0, 270.0):
    px, py = P(2000.0, deg)
    tx, ty = P(1000.0, deg)
    m.jump_pad("DaisPad_%d" % int(deg), px, py, 0.0, (tx, ty, DAIS_Z), color=(1.0, 0.6, 0.2), apex_extra=160.0)

# ---------------------------------------------------------------- drifting rock under and around the disc (no collision)
for i in range(26):
    ang = rng.uniform(0, 360)
    d = rng.uniform(R * 0.5, R + 3800)
    x, y = P(d, ang)
    sz = rng.uniform(260, 1100)
    B("Drift", x, y, rng.uniform(-3200, -400), rng.uniform(-3200, -400) + sz, sz, sz * rng.uniform(0.6, 1.2), rock, solid=False, yaw=rng.uniform(0, 180), pitch=rng.uniform(-35, 35))
for i in range(10):
    ang = rng.uniform(0, 360)
    x, y = P(R + rng.uniform(900, 2600), ang)
    B("Shard", x, y, -200, rng.uniform(600, 1800), 220, 220, rock, solid=False, yaw=rng.uniform(0, 90), pitch=rng.uniform(-10, 10))

# ---------------------------------------------------------------- starts


def add_start(label, x, y, yaw, tag=None, z=0.0):
    a = m.spawn(unreal.PlayerStart, label, (x, y, z + 110.0), (0, 0, yaw))
    if tag:
        a.set_editor_property("player_start_tag", tag)
    m.start_count += 1


for team, tag, sx in ((0, "Red", -1), (1, "Blue", 1)):
    for i in range(8):
        a = math.radians(i * 45.0)
        r = 420.0 if i % 2 == 0 else 720.0
        x, y = sx * 2750.0 + math.cos(a) * r * 0.9, math.sin(a) * r
        add_start("Start_%s_%d" % (tag, i), x, y, 0.0 if team == 0 else 180.0, tag)
for i in range(8):
    x, y = P(1450.0 if i % 2 == 0 else 2200.0, 22.5 + i * 45.0)
    add_start("Start_Mid_%d" % i, x, y, math.degrees(math.atan2(-y, -x)), None)

m.check_starts()
m.finish(kill_z=-1600)
unreal.log("NEXUS actors %d" % len(m.actor_lib.get_all_level_actors()))
