"""DM-Orbital: a research station on the edge of a gas giant (campaign chapter 4, also CTF / FFA / TDM).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_orbital.py" -unattended -nullrhi -nosplash

Layout (x runs between the bases, y across the station, z up; centimetres, about 9700 x 4760 playable):
  * the concourse: a long hall x -3600..3600, y -2300..2300, a slotted ceiling that lets the sun in, windows to the planet on both long sides
  * the reactor core: a glowing column in the middle (cover, the landmark of the map)
  * two raised decks (z 420) along the long sides, each with a ramp at both ends (16 degrees, usable by bots) and two jump pads
  * two base halls (Red west, Blue east) behind divider walls with three door openings each; the flag base is in the middle of the hall
  * outside the windows: solar wings, trusses and a habitat module (no collision), the planet and the sun come from the sky
Start tags: Red / Blue for the base halls, 8 untagged starts on the concourse and the decks.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
from mapkit import MapBuilder  # noqa: E402
from matlib import surface, glass  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Orbital")
rng = random.Random(404)
S = surface
m.look("space_orbital", ev=1.6, ambient_gain=10.0)

# ---------------------------------------------------------------- materials
floor = S("ConcreteClean", albedo=(138, 146, 160), tiling=2.0, tag="OrbFloor")
deck = S("DiamondPlateDark", albedo=(74, 80, 92), tiling=1.4, tag="OrbDeck")
wall = S("PlasterGrey", albedo=(214, 220, 230), tiling=2.0, tag="OrbWall")
wall_dark = S("SteelDark", albedo=(70, 76, 88), tag="OrbSteel")
trim = S("BrushedMetal", albedo=(150, 156, 168), metal=0.5, tag="OrbTrim")
crate_a = S("ContainerGrey", albedo=(118, 124, 134), tag="OrbCrateGrey")
crate_o = S("ContainerYellow", albedo=(196, 130, 40), tag="OrbCrateOrange")
panel_blue = S("BrushedMetal", albedo=(26, 40, 88), metal=0.3, tag="OrbSolar")
red_floor = S("ConcreteClean", albedo=(120, 82, 82), tiling=2.0, tag="OrbRedFloor")
blue_floor = S("ConcreteClean", albedo=(82, 94, 128), tiling=2.0, tag="OrbBlueFloor")
gl = glass()
g_cyan = m.glow("OrbGlowCyan", (0.10, 0.85, 1.0), 3.0)
g_orange = m.glow("OrbGlowOrange", (1.0, 0.55, 0.12), 3.0)
g_red = m.glow("OrbGlowRed", (1.0, 0.12, 0.08), 3.0)
g_blue = m.glow("OrbGlowBlue", (0.10, 0.30, 1.0), 3.0)
g_white = m.glow("OrbGlowWhite", (1.0, 0.95, 0.85), 2.5)

_n = [0]


def B(prefix, x0, x1, y0, y1, z0, z1, mat, solid=True, yaw=0.0):
    _n[0] += 1
    return m.box("%s_%d" % (prefix, _n[0]), (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), yaw=yaw, mat=mat, solid=solid)


def C(prefix, x, y, z0, z1, d, mat, solid=True):
    _n[0] += 1
    return m.column("%s_%d" % (prefix, _n[0]), x, y, z0, z1, d, mat=mat, solid=solid)


HX, HY, HZ = 3600.0, 2300.0, 1000.0       # the concourse
BX = 4850.0                                # the end walls
DECK_Z = 420.0

# ---------------------------------------------------------------- floors and the shell
B("Floor", -HX, HX, -HY, HY, -60, 0, floor)
for side in (-1, 1):
    x0, x1 = (HX, BX) if side > 0 else (-BX, -HX)
    B("HallFloor", x0, x1, -HY, HY, -60, 0, blue_floor if side > 0 else red_floor)
    B("EndWall", min(side * BX, side * (BX + 80)), max(side * BX, side * (BX + 80)), -HY - 80, HY + 80, -60, HZ + 60, wall)
    # a glowing seam on the end wall
    B("EndGlow", min(side * (BX - 20), side * BX), max(side * (BX - 20), side * BX), -900, 900, 260, 300, g_blue if side > 0 else g_red, solid=False)
for sy in (-1, 1):
    # the long walls: a solid knee wall, pillars every 600, glass between (windows to the planet)
    B("KneeWall", -BX, BX, min(sy * HY, sy * (HY + 80)), max(sy * HY, sy * (HY + 80)), -60, 180, wall)
    for i in range(-8, 9):
        x = i * 600.0
        B("Pillar", x - 45, x + 45, min(sy * (HY - 20), sy * (HY + 100)), max(sy * (HY - 20), sy * (HY + 100)), 0, HZ, wall_dark)
        if i < 8:
            B("Window", x + 45, x + 555, min(sy * (HY + 30), sy * (HY + 42)), max(sy * (HY + 30), sy * (HY + 42)), 180, HZ - 40, gl)
    B("WallBand", -BX, BX, min(sy * (HY - 10), sy * (HY + 90)), max(sy * (HY - 10), sy * (HY + 90)), HZ - 40, HZ + 20, trim)
    B("WallGlow", -BX + 50, BX - 50, min(sy * (HY - 25), sy * (HY - 10)), max(sy * (HY - 25), sy * (HY - 10)), 220, 250, g_cyan, solid=False)

# slotted ceiling: beams across and along, open strips between them (the sun comes through)
for i in range(-10, 11):
    x = i * 450.0
    B("CeilBeam", x - 30, x + 30, -HY - 80, HY + 80, HZ, HZ + 50, wall_dark)
for y in (-HY, -1150, 0, 1150, HY):
    B("CeilRail", -BX, BX, y - 35, y + 35, HZ + 10, HZ + 60, trim)

# ---------------------------------------------------------------- base halls: dividers with three door openings
OPEN = [(-1420.0, -780.0), (-320.0, 320.0), (780.0, 1420.0)]
SEG = [(-HY - 80, -1420.0), (-780.0, -320.0), (320.0, 780.0), (1420.0, HY + 80)]
for side in (-1, 1):
    xa, xb = (HX, HX + 120.0) if side > 0 else (-HX - 120.0, -HX)
    for y0, y1 in SEG:
        B("Divider", xa, xb, y0, y1, 0, HZ, wall)
    for y0, y1 in OPEN:
        B("Lintel", xa, xb, y0 - 60, y1 + 60, 540, HZ, wall)
        B("DoorGlow", xa - (10 if side > 0 else -10), xb + (10 if side > 0 else -10), y0 + 20, y1 - 20, 520, 540, g_blue if side > 0 else g_red, solid=False)
    # the team ring on the floor of the hall (the flag base stands in its middle)
    fx = side * 4300.0
    for k in range(2):
        r = 330.0 + k * 90.0
        for j in range(16):
            a = j / 16.0 * 2 * math.pi
            B("BaseRing", fx + math.cos(a) * r - 26, fx + math.cos(a) * r + 26, math.sin(a) * r - 26, math.sin(a) * r + 26, 0, 6, g_blue if side > 0 else g_red, solid=False)
    # hall furniture: consoles on the end wall, two lamp columns
    for y in (-1400.0, 1400.0):
        B("Console", side * (BX - 260) - 90, side * (BX - 260) + 90, y - 300, y + 300, 0, 130, wall_dark)
        B("ConsoleTop", side * (BX - 260) - 70, side * (BX - 260) + 40, y - 280, y + 280, 130, 150, g_cyan, solid=False)
    for y in (-700.0, 700.0):
        C("HallColumn", side * 4000.0, y, 0, HZ, 150, wall_dark)
        C("HallColumnGlow", side * 4000.0, y, 300, 340, 160, g_blue if side > 0 else g_red, solid=False)

# ---------------------------------------------------------------- the reactor core
C("Core", 0.0, 0.0, 0, HZ + 20, 980, wall_dark)
C("CoreRing", 0.0, 0.0, 470, 520, 1010, g_cyan, solid=False)
C("CoreRing", 0.0, 0.0, 700, 730, 1010, g_cyan, solid=False)
C("CoreBase", 0.0, 0.0, 0, 90, 1160, trim)
for a in range(4):
    ang = math.radians(45.0 + a * 90.0)
    B("Buttress", math.cos(ang) * 640 - 60, math.cos(ang) * 640 + 60, math.sin(ang) * 640 - 60, math.sin(ang) * 640 + 60, 0, 520, wall, yaw=math.degrees(ang))

# ---------------------------------------------------------------- the decks and their ramps
for sy in (-1, 1):
    y0, y1 = (1500.0, HY) if sy > 0 else (-HY, -1500.0)
    B("Deck", -1700, 1700, y0, y1, 0, DECK_Z, deck)
    B("DeckEdge", -1700, 1700, sy * 1500 - 20, sy * 1500 + 20, DECK_Z, DECK_Z + 26, g_orange, solid=False)
    B("DeckWall", -1700, 1700, sy * (HY - 40) - 10, sy * (HY - 40) + 10, DECK_Z, DECK_Z + 140, wall_dark)
    for x in (-1100.0, 0.0, 1100.0):
        B("DeckCover", x - 140, x + 140, sy * 1760 - 60, sy * 1760 + 60, DECK_Z, DECK_Z + 150, crate_a)
    for sx in (-1, 1):
        ramp = m.slope("Ramp_%d_%d" % (sx, sy), (sx * 1700.0, sy * 1900.0, DECK_Z), (sx * 3100.0, sy * 1900.0, 0.0), 420.0, thickness=40.0, mat=deck)
        B("RampRail", sx * 1700, sx * 3100, sy * 2110 - 15, sy * 2110 + 15, 0, 110, wall_dark, solid=False)

# jump pads from the concourse up to the decks
for sy in (-1, 1):
    for x in (-900.0, 900.0):
        m.jump_pad("DeckPad_%d_%d" % (sy, x), x, sy * 1250.0, 0.0, (x, sy * 1850.0, DECK_Z), color=(0.15, 0.85, 1.0), apex_extra=170.0)

# ---------------------------------------------------------------- cover on the concourse
for i, (cx, cy) in enumerate([(-1500, -650), (-1500, 650), (1500, -650), (1500, 650), (-2500, 0), (2500, 0), (0, -1250), (0, 1250)]):
    B("Crate", cx - 120, cx + 120, cy - 120, cy + 120, 0, 240, crate_a if i % 2 else crate_o)
    if i % 3 == 0:
        B("CrateTop", cx - 90, cx + 90, cy - 90, cy + 90, 240, 420, crate_o if i % 2 else crate_a)
    B("CrateStripe", cx - 125, cx + 125, cy - 125, cy + 125, 110, 128, g_orange, solid=False)
for y in (-500.0, 500.0):
    for x in (-3000.0, 3000.0):
        B("LowWall", x - 180, x + 180, y - 30, y + 30, 0, 150, wall_dark)

# ---------------------------------------------------------------- lights and light strips
for i in range(-3, 4):
    x = i * 1000.0
    for y in (-900.0, 900.0):
        m.accent_light("CeilLight_%d_%d" % (i, y), (x, y, HZ - 80), (0.85, 0.92, 1.0), candela=90.0, radius=1200.0)
for sx in (-1, 1):
    col = (1.0, 0.25, 0.2) if sx < 0 else (0.25, 0.4, 1.0)
    for y in (-1300.0, 0.0, 1300.0):
        m.accent_light("HallLight_%d_%d" % (sx, y), (sx * 4300.0, y, 700.0), col, candela=130.0, radius=1400.0)
m.accent_light("CoreLight", (0, 0, 600), (0.2, 0.85, 1.0), candela=160.0, radius=1800.0)
for sy in (-1, 1):
    m.accent_light("DeckLight_%d" % sy, (0, sy * 1900, DECK_Z + 300), (1.0, 0.75, 0.45), candela=70.0, radius=1400.0)

# ---------------------------------------------------------------- outside the windows (no collision): solar wings, trusses, a habitat module
for sy in (-1, 1):
    for k, x in enumerate((-2700.0, 0.0, 2700.0)):
        B("SolarWing", x - 700, x + 700, sy * 2700, sy * 6300, 620 + 160 * k, 640 + 160 * k, panel_blue, solid=False)
        B("SolarMast", x - 40, x + 40, sy * 2420, sy * 2700, 600 + 160 * k, 660 + 160 * k, trim, solid=False)
        for j in range(5):
            yy = sy * (3000 + j * 700)
            B("SolarRib", x - 700, x + 700, yy - 12, yy + 12, 636 + 160 * k, 650 + 160 * k, trim, solid=False)
    C("Habitat", sy * 0.0 + 3400.0, sy * 5200.0, -500, 1100, 1400, wall, solid=False)
    C("HabitatRing", 3400.0, sy * 5200.0, 250, 300, 1560, g_white, solid=False)
    B("Truss", -4200, 4200, sy * 2700 - 30, sy * 2700 + 30, -400, -340, trim, solid=False)
C("Antenna", -4300.0, 3600.0, 1000, 2600, 60, trim, solid=False)
C("AntennaDish", -4300.0, 3600.0, 2560, 2600, 520, wall, solid=False)

# ---------------------------------------------------------------- flags, starts
for team, nm, fx in ((0, "Red", -4300.0), (1, "Blue", 4300.0)):
    f = m.spawn(unreal.IAFlagBase, "FlagBase_" + nm, (fx, 0.0, 6.0))
    f.set_editor_property("flag_team", team)


def add_start(label, x, y, yaw, tag=None, z=0.0):
    a = m.spawn(unreal.PlayerStart, label, (x, y, z + 110.0), (0, 0, yaw))
    if tag:
        a.set_editor_property("player_start_tag", tag)
    m.start_count += 1


HALL = [(-3950, -1000), (-3950, 1000), (-4500, -1450), (-4500, 1450), (-4300, -700), (-4300, 700), (-3900, 0), (-4650, 0)]
for team, tag in ((0, "Red"), (1, "Blue")):
    s = -1 if team == 0 else 1
    for i, (hx, hy) in enumerate(HALL):
        x = -hx if team == 1 else hx
        add_start("Start_%s_%d" % (tag, i), x, hy, 0.0 if team == 0 else 180.0, tag)
for i, (x, y, z) in enumerate([(-1500, 0, 0), (1500, 0, 0), (0, -1700, DECK_Z), (0, 1700, DECK_Z), (-700, -1100, 0), (700, 1100, 0), (-2800, 1900, 0), (2800, -1900, 0)]):
    add_start("Start_Mid_%d" % i, x, y, rng.uniform(0, 360), None, z)

m.check_starts()
m.finish(kill_z=-1500)
unreal.log("ORBITAL actors %d" % len(m.actor_lib.get_all_level_actors()))
