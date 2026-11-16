"""DM-Downtown: a big downtown district at the end of the day. Capture the Flag, team deathmatch and free for all.

  Tools\\run_ue.ps1 -Script Tools\\make_map_downtown.py -Log Saved\\mk_downtown.log -Grep "MAKEMAP_DONE|Traceback|LogPython: Error"

The district is 12000 x 8400 cm: three columns x two rows of city blocks around a wide central avenue (y = +-900) with two narrower
side streets (x = +-1800..2700) and a plaza with a fountain where they meet. The whole map is rotationally symmetric (180 degrees
about the centre) in everything that matters for play; the two halves are only dressed differently:

  NW  RED BASE   the bank: marble hall, galleries, a vault door.     SE  BLUE BASE  the station: iron hall under a glass vault.
  NE  shops and cafes around a courtyard                              SW  shops and a parking lot around a courtyard
  NM  park (grass, pond, trees, pavilion)                             SM  construction site (frames, scaffolds, crane)
  centre: the plaza with the fountain; under it the metro passage, with stairs up to the plaza and the side street crossings.

Three lanes: street level, the rooftops (everything walkable is at 640 or 960 and linked by flat steel bridges across the avenue
and the side streets) and the underground passage. Jump pads are shortcuts to the roofs.

Local frames: Xf(s) maps (x, y) -> (s*x, s*y). Things built for s = +1 are mirrored by rotation for s = -1.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit
import props  # noqa: F401  (adds b.prop / b.scatter)
import mapkit_c as kc
import mapkit_b
import kc_parts as kp
import mesh_b
import mapkit_big3 as bg
from mapkit_c import rbox, cyl, bar
from matlib import surface, srgb, glass, water

bg.register_extra_surfaces()

m = mapkit.MapBuilder("/Game/Maps/DM-Downtown")
bt = bg.Batches(m)
rng = random.Random(2468)
DRESS = os.environ.get("DT_DRESS", "1") == "1"

HX, HY = 6000.0, 4200.0          # playable half extents
Z1, Z2 = 640.0, 960.0            # low and high roofs (3 floors of 320 = 960)
TOWER = 2560.0                   # unwalkable towers
TUN = -400.0                     # floor of the metro passage (ceiling at -100: 300 clear)
WARM = (1.0, 0.72, 0.42)
EXTRA_STARTS = []

# ------------------------------------------------------------------------------------------------ materials
def S(name, tag, **kw):
    return surface(name, tag="Dt" + tag, **kw)


asphalt = surface("Asphalt", tiling=3.0)
asphalt_worn = S("AsphaltCracked", "AsphaltWorn", albedo=(84, 83, 81), tiling=3.0)
sidewalk = S("Sidewalk", "Walk", albedo=(150, 147, 140), tiling=2.0)
paving = S("StoneSlabs", "Paving", albedo=(158, 148, 130), tiling=1.5)
paving_dark = S("StoneSlabs", "PavingDark", albedo=(104, 98, 90), tiling=1.5)
cobble = S("Cobblestone", "Cobble", albedo=(128, 118, 104))
kerb_m = S("ConcreteClean", "Kerb", albedo=(158, 156, 150))
paint_w = S("ConcreteClean", "PaintW", albedo=(200, 198, 188))
paint_y = S("ConcreteClean", "PaintY", albedo=(212, 170, 56))
concrete = S("ConcreteClean", "Concrete", albedo=(150, 148, 142))
concrete_dark = surface("ConcreteDark")
concrete_dirty = surface("ConcreteDirty")
concrete_pale = S("ConcreteClean", "ConcretePale", albedo=(176, 172, 164))
ground_m = S("ConcreteDirty", "Ground", albedo=(100, 98, 92))
tile_wall = S("StoneSlabs", "MetroTile", albedo=(190, 186, 170), tiling=0.6, rb=-0.3)
tile_floor = S("StoneSlabs", "MetroFloor", albedo=(96, 94, 90), tiling=1.2, rb=-0.2)
marble_floor = S("StoneSlabs", "MarbleFloor", albedo=(206, 198, 182), tiling=1.8, rb=-0.45)
marble_wall = S("SandstoneBlocks", "MarbleWall", albedo=(220, 212, 196), desat=0.7, rb=-0.3, tiling=2.0)
marble_dark = S("StoneSlabs", "MarbleDark", albedo=(60, 58, 56), tiling=1.8, rb=-0.4)
limestone = S("SandstoneBlocks", "Limestone", albedo=(214, 200, 172), desat=0.5)
sand_floor = S("PlasterWeathered", "StationPlaster", albedo=(200, 186, 150))
steel = surface("BrushedMetal", albedo=(92, 95, 102), tag="SteelLit", metal=0.22, rb=0.12, ns=0.4)
steel_dark = S("BrushedMetal", "SteelDark", albedo=(52, 54, 58), metal=0.3, rb=0.1, ns=0.4)
galv = surface("CorrugatedGalv")
galv_dark = surface("CorrugatedDark")
rust = surface("RustOrange")
diamond = S("DiamondPlateDark", "Deck", tiling=1.0)
roof_tar = S("RoofTarmac", "RoofTar", albedo=(88, 86, 84), tiling=4.0)
roof_gravel = S("Gravel", "RoofGravel", albedo=(126, 120, 110), tiling=2.6)
brick_m = S("BrickRed", "BrickWall", albedo=(120, 84, 72), desat=0.4)
brick_dark = surface("BrickDark")
wood_dark = surface("WoodPlanksDark")
wood_bench = S("WoodPlanksDark", "Bench", albedo=(122, 88, 58))
wood_door = surface("WoodPaintedGrey")
grass = surface("Grass")
grass_dry = S("Grass", "GrassDry", albedo=(96, 98, 52), desat=1.0)
dirt = S("DirtDry", "Soil", albedo=(86, 66, 48))
gravel_path = S("Gravel", "ParkPath", albedo=(168, 156, 132), tiling=1.4)
rubber = kp.car_rubber_mat()
car_glass = kp.car_glass_mat()
bark = S("WoodPlanksDark", "Bark", albedo=(66, 52, 42))
leaf_a = mapkit_b.prop_variant("shrub_b", (0.50, 0.80, 0.38), "DowntownLeafA")
leaf_b = mapkit_b.prop_variant("shrub_b", (0.62, 0.74, 0.34), "DowntownLeafB")
leaf_c = mapkit_b.prop_variant("shrub_a", (0.46, 0.76, 0.40), "DowntownLeafC")
glass_m = glass()
water_m = water()
awn_red, awn_blue = surface("CanvasRed"), surface("CanvasBlue")
awn_green = S("Canvas", "AwnGreen", albedo=(62, 98, 72), desat=1.0)
awn_cream = S("Canvas", "AwnCream", albedo=(190, 180, 156), desat=1.0)
awn_ochre = S("Canvas", "AwnOchre", albedo=(176, 128, 52), desat=1.0)


def paint(name, rgb, base="WoodPaintedGrey"):
    return S(base, "P" + name, albedo=rgb)


pa_green, pa_maroon, pa_navy = paint("Green", (44, 72, 60)), paint("Maroon", (104, 46, 48)), paint("Navy", (38, 52, 84))
pa_mustard, pa_char, pa_cream = paint("Mustard", (168, 134, 58)), paint("Char", (50, 50, 55)), paint("Cream", (186, 178, 148))
pa_white, pa_grey = paint("White", (190, 188, 180)), paint("Grey", (112, 116, 120))
pa_red, pa_blue, pa_teal = paint("Red", (150, 48, 42)), paint("Blue", (44, 80, 130)), paint("Teal", (44, 110, 108))
FASCIA = [pa_green, pa_maroon, pa_navy, pa_mustard, pa_char, pa_teal, pa_red, pa_blue]

# emissive (M_IAEmit): lit windows are modest at this exposure, signs and lamp heads stronger
win_warm = kc.emit("DtShopWarm", (1.0, 0.68, 0.36), 0.40)
win_cool = kc.emit("DtShopCool", (0.66, 0.86, 1.0), 0.34)
lamp_head = kc.emit("DtLampHead", (1.0, 0.80, 0.52), 1.6)
tube_white = kc.emit("DtTube", (0.82, 0.92, 1.0), 1.5)
tube_warm = kc.emit("DtTubeWarm", (1.0, 0.78, 0.5), 1.3)
sign_amber = kc.emit("DtSignAmber", (1.0, 0.62, 0.16), 2.2)
sign_cyan = kc.emit("DtSignCyan", (0.2, 0.85, 1.0), 2.0)
sign_pink = kc.emit("DtSignPink", (1.0, 0.18, 0.5), 2.0)
sign_green = kc.emit("DtSignGreen", (0.3, 1.0, 0.45), 1.8)
sign_red = kc.emit("DtSignRed", (1.0, 0.15, 0.10), 2.2)
beacon_m = kc.emit("DtBeacon", (1.0, 0.05, 0.03), 2.4)
tail_lamp = kc.emit("DtTail", (1.0, 0.05, 0.05), 0.5)
car_red, car_blue, car_green = kp.car_paint("Red", (120, 24, 28)), kp.car_paint("Blue", (28, 56, 112)), kp.car_paint("Green", (36, 78, 62))
car_grey, car_white = kp.car_paint("Grey", (112, 114, 118)), kp.car_paint("White", (196, 196, 190))
car_yellow, car_black = kp.car_paint("Yellow", (200, 160, 36)), kp.car_paint("Black", (30, 30, 34))
FRAME_CREAM, FRAME_WHITE, FRAME_GREY, FRAME_GREEN = srgb(172, 160, 130), srgb(176, 174, 166), srgb(112, 116, 120), srgb(44, 70, 58)


def fac(tag, wall, **kw):
    kw.setdefault("lit", 0.30)
    kw.setdefault("glow", 0.55)
    kw.setdefault("min_z", 330.0)
    kw.setdefault("frame_w", 8.0)
    kw.setdefault("sill_boost", 1.5)
    kw.setdefault("cell", (300.0, 320.0))
    kw.setdefault("sill", 70.0)
    return kc.facade("Dt" + tag, wall=wall, grid_z=0.0, ground_z=0.0, dirt_h=600.0, **kw)


f_brick = fac("Brick", "BrickRed", albedo=(124, 86, 74), desat=0.4, seed=11, win=(150, 190), frame_rgb=FRAME_CREAM)
f_brown = fac("Brown", "BrickRed", albedo=(100, 74, 62), desat=0.5, seed=12, win=(140, 190), frame_rgb=FRAME_WHITE)
f_plaster = fac("Plaster", "PlasterWeathered", albedo=(190, 172, 140), seed=13, win=(150, 190), frame_rgb=FRAME_GREEN)
f_cream = fac("Cream", "PlasterGrey", albedo=(184, 178, 160), seed=14, win=(160, 190), frame_rgb=FRAME_GREY)
f_conc = fac("Conc", "ConcreteDirty", albedo=(128, 124, 116), seed=15, win=(200, 200), lit_rows=0.3, frame_rgb=FRAME_GREY)
f_bank = fac("Bank", "SandstoneBlocks", albedo=(204, 190, 160), desat=0.4, seed=16, win=(170, 200), sill=70, frame_rgb=srgb(120, 110, 92),
             min_z=380.0, lit=0.25)
f_station = fac("Station", "BrickRed", albedo=(128, 80, 62), desat=0.3, seed=17, win=(170, 200), frame_rgb=FRAME_CREAM, min_z=380.0)
f_tower = fac("Tower", "ConcreteWorn", albedo=(112, 118, 128), seed=18, win=(240, 240), lit=0.28, lit_rows=0.35, frame_rgb=FRAME_GREY,
              glass_rgb=(0.05, 0.07, 0.10), sill=40)
f_tower2 = fac("Tower2", "ConcreteClean", albedo=(168, 162, 150), seed=19, win=(210, 220), lit=0.25, lit_rows=0.4, frame_rgb=FRAME_WHITE,
               glass_rgb=(0.04, 0.06, 0.09), sill=50)
f_wall = fac("Wall", "ConcreteDirty", albedo=(120, 116, 108), seed=20, win=(200, 210), lit=0.25, lit_rows=0.3, frame_rgb=FRAME_GREY, min_z=640.0)
f_frame = fac("Frame", "ConcreteDirty", albedo=(168, 164, 156), seed=21, win=(260, 260), lit=0.0, frame_w=0.0, min_z=330.0,
              glass_rgb=(0.20, 0.20, 0.20), sill=30)
f_garage = fac("Garage", "ConcreteClean", albedo=(158, 154, 146), seed=22, win=(240, 140), lit=0.0, frame_rgb=FRAME_GREY, sill=90)

# ------------------------------------------------------------------------------------------------ batches
def B(name, mat, **kw):
    return bt.get(name, mat, **kw)


b_kerb = B("Kerb", kerb_m, shadow=False)
b_pw = B("PaintW", paint_w, shadow=False)
b_py = B("PaintY", paint_y, shadow=False)
b_cornice = B("Cornice", limestone, max_dist=14000.0)
b_cornice2 = B("CorniceConc", concrete, max_dist=14000.0)
b_parapet = B("Parapet", concrete, solid=True)
b_roof = B("RoofTar", roof_tar, shadow=False)
b_roofg = B("RoofGravel", roof_gravel, shadow=False)
b_steel = B("Steel", steel, max_dist=12000.0)
b_steeld = B("SteelDark", steel_dark, max_dist=12000.0)
b_steel_solid = B("SteelSolid", steel, solid=True)
b_galv = B("Galv", galv, max_dist=10000.0)
b_cover = B("RoofCover", galv_dark, solid=True)
b_deck = B("Deck", diamond, solid=True)
b_glass = B("Glass", glass_m, shadow=False, max_dist=16000.0)
b_winwarm = B("WinWarm", win_warm, shadow=False, max_dist=9000.0)
b_wincool = B("WinCool", win_cool, shadow=False, max_dist=9000.0)
b_lamp = B("LampHead", lamp_head, shadow=False, max_dist=14000.0)
b_tube = B("TubeWhite", tube_white, shadow=False, max_dist=9000.0)
b_tubew = B("TubeWarm", tube_warm, shadow=False, max_dist=9000.0)
b_conc_s = B("ConcSolid", concrete, solid=True)
b_concd_s = B("ConcDarkSolid", concrete_dark, solid=True)
b_wood = B("WoodBench", wood_bench, max_dist=9000.0)
b_woods = B("WoodSolid", wood_bench, solid=True, max_dist=9000.0)
b_rubber = B("Rubber", rubber, max_dist=9000.0)
b_pavd = B("PavingDark", paving_dark, shadow=False)
b_marble = B("Marble", marble_wall, max_dist=14000.0)
b_marble_s = B("MarbleSolid", marble_wall, solid=True)
b_marbled = B("MarbleDark", marble_dark, max_dist=14000.0)
b_tilew = B("TileWall", tile_wall, shadow=False)
b_tilef = B("TileFloor", tile_floor, shadow=False)
b_soil = B("Soil", dirt, shadow=False)
b_path = B("Path", gravel_path, shadow=False)
b_sign = {"amber": B("SignAmber", sign_amber, shadow=False, max_dist=12000.0), "cyan": B("SignCyan", sign_cyan, shadow=False, max_dist=12000.0),
          "pink": B("SignPink", sign_pink, shadow=False, max_dist=12000.0), "green": B("SignGreen", sign_green, shadow=False, max_dist=12000.0),
          "red": B("SignRed", sign_red, shadow=False, max_dist=12000.0)}
b_fascia = [B("Fascia%d" % i, mt, max_dist=9000.0) for i, mt in enumerate(FASCIA)]
b_awn = [B("AwnR", awn_red, max_dist=9000.0), B("AwnB", awn_blue, max_dist=9000.0), B("AwnG", awn_green, max_dist=9000.0),
         B("AwnC", awn_cream, max_dist=9000.0), B("AwnO", awn_ochre, max_dist=9000.0)]
b_frame_cream = B("FrameCream", pa_cream, max_dist=9000.0)
b_riser = B("Riser", pa_char, max_dist=9000.0)
b_doorw = B("DoorWood", wood_door, max_dist=9000.0)
b_beacon = B("Beacon", beacon_m, shadow=False, max_dist=30000.0)
b_brick_s = B("BrickSolid", brick_m, solid=True)

# ------------------------------------------------------------------------------------------------ helpers
def box(label, x0, y0, x1, y1, z0, z1, mat, solid=True):
    return m.box(label, (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), mat=mat, solid=solid)


def ov(label, rect, top, mat, holes=None, z0=0.0):
    """A visible, non-solid cover layer on the ground (z0 .. top), with holes cut out (stairs pits)."""
    for i, r in enumerate(bg.rect_subtract(rect, holes if holes is not None else PITS)):
        box("%s%d" % (label, i), r[0], r[1], r[2], r[3], z0, top, mat, solid=False)


def parapet(rect, z, gaps=None, edges="NSEW", th=36.0, h=100.0, bat=None):
    """A solid coping wall on the edges of a roof rectangle. gaps = {'N': [(centre, width), ...]} along the edge (world coordinates)."""
    x0, y0, x1, y1 = rect
    gaps = gaps or {}
    bat = bat or b_parapet
    for e in edges:
        if e == "N":
            lo, hi, fixed, ax = x0, x1, y1 - th / 2, "x"
        elif e == "S":
            lo, hi, fixed, ax = x0, x1, y0 + th / 2, "x"
        elif e == "E":
            lo, hi, fixed, ax = y0, y1, x1 - th / 2, "y"
        else:
            lo, hi, fixed, ax = y0, y1, x0 + th / 2, "y"
        for a, b in bg.rect_gaps(lo, hi, gaps.get(e, [])):
            if ax == "x":
                bat.rect(a, fixed - th / 2, b, fixed + th / 2, z, z + h)
            else:
                bat.rect(fixed - th / 2, a, fixed + th / 2, b, z, z + h)


# pits of the metro passage (stairs up to the street): the ground has holes there
ENDSTAIRS = [(1360.0, -450.0, 2560.0, 450.0), (-2560.0, -450.0, -1360.0, 450.0)]
SHAFTS = [(400.0, 450.0, 800.0, 1650.0), (-800.0, 450.0, -400.0, 1650.0), (400.0, -1650.0, 800.0, -450.0), (-800.0, -1650.0, -400.0, -450.0)]
PITS = ENDSTAIRS + SHAFTS
CORR = (-1360.0, -450.0, 1360.0, 450.0)

# ================================================================================================== GROUND AND METRO
for i, r in enumerate(bg.rect_subtract((-HX - 400, -HY - 400, HX + 400, HY + 400), PITS + [CORR])):
    box("Ground%d" % i, r[0], r[1], r[2], r[3], -600.0, 0.0, ground_m)

# the metro passage: floor, ceiling (= the street over it), and the stairs
box("MetroFloor", CORR[0], CORR[1], CORR[2], CORR[3], -600.0, TUN, tile_floor)
box("MetroCeiling", CORR[0], CORR[1], CORR[2], CORR[3], -100.0, 0.0, concrete_dark)
for sgn in (1, -1):
    bg.stair_ramp(m, "MetroEnd%d" % sgn, sgn * 1360.0, 0.0, TUN, 0.0 if sgn > 0 else 180.0, 900, 400, 1200.0, mat=concrete)
for i, (x0, y0, x1, y1) in enumerate(SHAFTS):
    north = y0 > 0
    bg.stair_ramp(m, "MetroShaft%d" % i, (x0 + x1) / 2.0, 450.0 if north else -450.0, TUN, 90.0 if north else 270.0, 400, 400, 1200.0,
                   mat=concrete)

# ---- street level layers (visual only; the ground itself is solid)
ov("Road", (-HX, -600.0, HX, 600.0), 3.0, asphalt)
for (xa, xb) in ((2000.0, 2500.0), (-2500.0, -2000.0)):
    ov("SideRoadN", (xa, 600.0, xb, HY), 6.0, asphalt)
    ov("SideRoadS", (xa, -HY, xb, -600.0), 6.0, asphalt)
for (ya, yb) in ((600.0, 900.0), (-900.0, -600.0)):                      # avenue sidewalks (the plaza has its own paving)
    for xa, xb in ((-HX, -1800.0), (1800.0, HX)):
        ov("AveWalk", (xa, ya, xb, yb), 5.0, sidewalk)
for (xa, xb) in ((1800.0, 2000.0), (2500.0, 2700.0), (-2000.0, -1800.0), (-2700.0, -2500.0)):   # side street sidewalks
    ov("SideWalkN", (xa, 900.0, xb, HY), 5.0, sidewalk)
    ov("SideWalkS", (xa, -HY, xb, -900.0), 5.0, sidewalk)
ov("Plaza", (-1800.0, -1800.0, 1800.0, 1800.0), 4.0, paving)
ov("PlazaRing", (-1800.0, -1800.0, 1800.0, -1500.0), 4.6, paving_dark)
ov("PlazaRing", (-1800.0, 1500.0, 1800.0, 1800.0), 4.6, paving_dark)
ov("PlazaCobble", (-1300.0, -1300.0, 1300.0, 1300.0), 4.5, cobble)
ov("PlazaCobble", (-1450.0, -450.0, 1450.0, 450.0), 4.6, cobble)

# ---- the perimeter: tall buildings (inner face with windows) and the highway embankment at the avenue ends
box("WallN", -HX - 400, HY, HX + 400, HY + 400, -600.0, TOWER, f_wall)
box("WallS", -HX - 400, -HY - 400, HX + 400, -HY, -600.0, TOWER, f_wall)
for sx in (-1, 1):
    x0, x1 = (HX, HX + 400) if sx > 0 else (-HX - 400, -HX)
    box("WallEn", x0, 900.0, x1, HY, -600.0, TOWER, f_wall)
    box("WallEs", x0, -HY, x1, -900.0, -600.0, TOWER, f_wall)
    box("Embankment", x0 - (0 if sx > 0 else 0), -900.0, x1, 900.0, -600.0, 1300.0, concrete_dirty)

# ================================================================================================== BRIDGES (decks, rails, trusses)
BRIDGE_GAPS = {}          # building key -> {'N': [(c, w)], ...}


def bridge(label, p0, p1, z0, z1, width=360.0):
    """A steel skybridge between two roof edges: deck (solid), low kerbs, rails, posts and an under-deck truss."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    run = math.hypot(dx, dy)
    ux, uy = dx / run, dy / run
    ext = 70.0
    a = (p0[0] - ux * ext, p0[1] - uy * ext, z0)
    c = (p1[0] + ux * ext, p1[1] + uy * ext, z1)
    m.slope(label, a, c, width, thickness=55.0, mat=diamond)
    nx, ny = -uy, ux
    total = run + 2 * ext
    n_posts = max(2, int(total // 200.0))
    for side in (-1, 1):
        ox, oy = nx * side * (width / 2.0 - 8.0), ny * side * (width / 2.0 - 8.0)
        pts = []
        for k in range(n_posts + 1):
            t = k / float(n_posts)
            pts.append((a[0] + (c[0] - a[0]) * t + ox, a[1] + (c[1] - a[1]) * t + oy, z0 + (z1 - z0) * t))
        for k in range(n_posts + 1):
            px, py, pz = pts[k]
            b_steel.box(px, py, pz + 52, 6, 6, 104)
        b_steel.bar((pts[0][0], pts[0][1], pts[0][2] + 104), (pts[-1][0], pts[-1][1], pts[-1][2] + 104), 7, 7)
        b_steel.bar((pts[0][0], pts[0][1], pts[0][2] + 55), (pts[-1][0], pts[-1][1], pts[-1][2] + 55), 4, 4)
        # truss under the deck: lower chord and zig-zag diagonals
        depth = min(190.0, total * 0.09)
        for k in range(n_posts):
            p, q = pts[k], pts[k + 1]
            lo0 = (p[0], p[1], p[2] - 55 - depth * math.sin(math.pi * k / n_posts))
            lo1 = (q[0], q[1], q[2] - 55 - depth * math.sin(math.pi * (k + 1) / n_posts))
            b_steeld.bar(lo0, lo1, 12, 12)
            b_steeld.bar((p[0], p[1], p[2] - 52), lo1 if k % 2 == 0 else lo0, 8, 8)
            b_steeld.bar((q[0], q[1], q[2] - 52), lo0 if k % 2 == 0 else lo1, 8, 8)
    return total


# decks and the gaps they need in the parapets of the roofs they land on
def add_gap(key, edge, c, w=460.0):
    BRIDGE_GAPS.setdefault(key, {}).setdefault(edge, []).append((c, w))


# avenue: x = +-3000 (flat, 960 <-> 960) and x = +-5700 (640 -> 960), NE/SW sides with the base across the avenue
for s in (1, -1):
    bridge("SkyAve3_%d" % s, (s * 3000.0, s * 900.0), (s * 3000.0, -s * 900.0), Z2, Z2)
    bridge("SkyAve5_%d" % s, (s * 5700.0, s * 900.0), (s * 5700.0, -s * 900.0), Z1, Z2)
    add_gap("O%d_A" % s, "S" if s > 0 else "N", s * 3000.0)
    add_gap("O%d_B" % s, "S" if s > 0 else "N", s * 5700.0)
    add_gap("B%d" % s, "S" if s > 0 else "N", s * 3000.0)
    add_gap("B%d" % s, "S" if s > 0 else "N", s * 5700.0)
# side streets: the middle wing roofs to the outer buildings (x = 1800..2700, y = +-2250 and +-3750)
for s in (1, -1):
    for y in (2250.0, 3750.0):
        bridge("SkySide_%d_%d" % (s, y), (s * 1800.0, s * y), (s * 2700.0, s * y), Z2, Z2)
        add_gap("M%d_E" % s, "E" if s > 0 else "W", s * y)
        add_gap("O%d_W" % s, "W" if s > 0 else "E", s * y)
        # the bank / station roof against the other middle wing
        bridge("SkySideB_%d_%d" % (s, y), (-s * 1800.0, s * y), (-s * 2700.0, s * y), Z2, Z2)
        add_gap("M%d_W" % s, "W" if s > 0 else "E", s * y)
        add_gap("B%d" % s, "E" if s > 0 else "W", s * y)
# the small bridge over the gap in each west wing of the outer blocks
for s in (1, -1):
    bridge("SkyGap_%d" % s, (s * 3000.0, s * 2700.0), (s * 3000.0, s * 3300.0), Z2, Z2, width=340.0)
    add_gap("O%d_W1" % s, "N" if s > 0 else "S", s * 3000.0)
    add_gap("O%d_W2" % s, "S" if s > 0 else "N", s * 3000.0)

# ================================================================================================== THE TWO BASES
# Local frame of a base (u east, v from the avenue into the block); bank: world = (-6000 + u, 900 + v); station: rotated 180 degrees.
BW = 3300.0
SKY = (700.0, 900.0, 2600.0, 2500.0)            # skylight opening in the roof
FLAG_UV = (1650.0, 2050.0)
BASE_DOORS_S = [(600.0, 360.0, 360.0), (1650.0, 600.0, 420.0), (2700.0, 360.0, 360.0)]     # (centre u, width, height)
BASE_DOORS_E = [(900.0, 420.0, 360.0), (2100.0, 420.0, 360.0)]                             # (centre v, width, height)
COLS_UV = [(u, v) for v in (1250.0, 2350.0) for u in (720.0, 1230.0, 2070.0, 2580.0)]
BASE_FLAG = {}


def build_base(s, kind):
    X = bg.Xf(s)
    bank = kind == "bank"
    T, H = 90.0, 860.0
    gaps = BRIDGE_GAPS.get("B%d" % s, {})
    fm = f_bank if bank else f_station
    clad = b_marble if bank else B("StationClad", sand_floor, max_dist=14000.0)
    clad_dark = b_marbled if bank else B("StationCladDark", pa_green, max_dist=14000.0)

    def R(u0, v0, u1, v1):
        return X.r(-HX + u0, 900.0 + v0, -HX + u1, 900.0 + v1)

    def P(u, v):
        return X.p(-HX + u, 900.0 + v)

    def sol(label, u0, v0, u1, v1, z0, z1, mat, solid=True):
        r = R(u0, v0, u1, v1)
        return box(label, r[0], r[1], r[2], r[3], z0, z1, mat, solid)

    def cl(bat, u0, v0, u1, v1, z0, z1):
        r = R(u0, v0, u1, v1)
        bat.rect(r[0], r[1], r[2], r[3], z0, z1)

    tag = "Bank" if bank else "Station"
    # ---- outer walls with the door openings
    for i, (a, b) in enumerate(bg.rect_gaps(0, BW, [(c, w) for c, w, h in BASE_DOORS_S])):
        sol("%sWallS%d" % (tag, i), a, 0, b, T, 0, Z2, fm)
    for c, w, h in BASE_DOORS_S:
        sol("%sLintelS" % tag, c - w / 2, 0, c + w / 2, T, h, Z2, fm)
    for i, (a, b) in enumerate(bg.rect_gaps(0, BW, [(c, w) for c, w, h in BASE_DOORS_E])):
        sol("%sWallE%d" % (tag, i), BW - T, a, BW, b, 0, Z2, fm)
    for c, w, h in BASE_DOORS_E:
        sol("%sLintelE" % tag, BW - T, c - w / 2, BW, c + w / 2, h, Z2, fm)
    sol(tag + "WallW", 0, T, T, BW - T, 0, Z2, fm)
    sol(tag + "WallN", 0, BW - T, BW, BW, 0, Z2, fm)
    # ---- roof slab with the skylight opening
    for i, r in enumerate(bg.rect_subtract((0, 0, BW, BW), [SKY])):
        sol("%sRoof%d" % (tag, i), r[0], r[1], r[2], r[3], H, Z2, roof_tar)
        cl(b_roof, r[0], r[1], r[2], r[3], Z2, Z2 + 4)
    t = 36.0
    for (u0, v0, u1, v1) in ((SKY[0] - t, SKY[1] - t, SKY[2] + t, SKY[1]), (SKY[0] - t, SKY[3], SKY[2] + t, SKY[3] + t),
                             (SKY[0] - t, SKY[1], SKY[0], SKY[3]), (SKY[2], SKY[1], SKY[2] + t, SKY[3])):
        r = R(u0, v0, u1, v1)
        b_parapet.rect(r[0], r[1], r[2], r[3], Z2, Z2 + 130)
    parapet(R(0, 0, BW, BW), Z2, gaps)
    # ---- inside: floor, wall cladding, ceiling
    ov(tag + "Floor", R(T, T, BW - T, BW - T), 3.0, marble_floor if bank else tile_floor, holes=[])
    for (a, b) in bg.rect_gaps(T, BW - T, [(c, w) for c, w, h in BASE_DOORS_S]):
        cl(clad, a, T, b, T + 8, 0, H)
    for (a, b) in bg.rect_gaps(T, BW - T, [(c, w) for c, w, h in BASE_DOORS_E]):
        cl(clad, BW - T - 8, a, BW - T, b, 0, H)
    cl(clad, T, T, T + 8, BW - T, 0, H)
    cl(clad, T, BW - T - 8, BW - T, BW - T, 0, H)
    for r in bg.rect_subtract((T, T, BW - T, BW - T), [SKY]):
        cl(clad, r[0], r[1], r[2], r[3], H - 8, H)
    # ---- columns (bank: marble, fluted; station: slim cast iron) and the central desk
    if bank:
        col = bg.mesh_asset("BankCol", lambda: mesh_b.column_mesh(H, 55, flutes=14, drums=3, seed=2, plinth_k=2.3, abacus_k=2.5))
        col_mat = marble_wall
    else:
        col = bg.mesh_asset("StationCol", lambda: mesh_b.column_mesh(H, 42, flutes=0, drums=2, seed=5, plinth_k=2.2, abacus_k=2.0, entasis=0.95))
        col_mat = pa_green
    for i, (u, v) in enumerate(COLS_UV):
        x, y = P(u, v)
        mapkit_b.put(m, "%sCol%d" % (tag, i), col, x, y, 0.0, mat=col_mat)
    sol(tag + "Desk", 1440, 1020, 1860, 1280, 0, 130, marble_dark if bank else pa_char)
    sol(tag + "DeskTop", 1425, 1005, 1875, 1295, 130, 146, marble_wall if bank else wood_dark)
    sol(tag + "DeskTall", 1560, 1090, 1740, 1210, 146, 270, marble_wall if bank else pa_green)
    for (u0, u1) in ((520.0, 1100.0), (2300.0, 3050.0)):                       # teller counters / ticket booths
        sol(tag + "Counter", u0, 620, u1, 740, 0, 112, marble_dark if bank else pa_char)
        sol(tag + "CounterTop", u0 - 10, 610, u1 + 10, 750, 112, 126, marble_wall if bank else wood_dark)
        cl(b_glass, u0, 665, u1, 670, 126, 300)
        b_steel.rect(*R(u0, 662, u1, 673)[:4], 296, 304)
    # ---- galleries (west and north, joined), two stairs, balustrades
    sol(tag + "GalleryW", T, 1170, 490, BW - T, 300, 340, marble_wall if bank else sand_floor)
    sol(tag + "GalleryN", 490, 2750, 2190, BW - T, 300, 340, marble_wall if bank else sand_floor)
    sx, sy = P(290.0, 150.0)
    bg.stair_ramp(m, tag + "StairW", sx, sy, 0.0, X.yaw(90.0), 400, 340, 1020.0, mat=marble_wall if bank else sand_floor)
    sx, sy = P(BW - T, 2980.0)
    bg.stair_ramp(m, tag + "StairE", sx, sy, 0.0, X.yaw(180.0), 460, 340, 1020.0, mat=marble_wall if bank else sand_floor)
    bal = b_marble_s if bank else B("StationBal", pa_green, solid=True)
    for (u0, v0, u1, v1) in ((470, 1170, 490, 2750), (490, 2730, 2190, 2750), (470, 2730, 490, 2750)):
        r = R(u0, v0, u1, v1)
        bal.rect(r[0], r[1], r[2], r[3], 340, 450)
    for (u0, v0, u1, v1) in ((470, 1170, 490, 2750), (490, 2730, 2190, 2750)):       # top rail
        r = R(u0 - 6, v0, u1 + 6, v1)
        b_steel.rect(r[0], r[1], r[2], r[3], 450, 460)
    # ---- the flag stand
    fx, fy = P(*FLAG_UV)
    rbox(m, tag + "FlagPlinth", fx, fy, 7, 330, 330, 14, mat=marble_dark if bank else pa_char, solid=False, mesh=m.cylinder)
    rbox(m, tag + "FlagPlinthRing", fx, fy, 11, 360, 360, 6, mat=steel, solid=False, mesh=m.cylinder)
    BASE_FLAG[s] = (fx, fy)
    flag = m.spawn(unreal.IAFlagBase, "FlagBase_Red" if s > 0 else "FlagBase_Blue", (fx, fy, 0.0), (0, 0, X.yaw(0.0)))
    flag.set_editor_property("flag_team", 0 if s > 0 else 1)


build_base(1, "bank")
build_base(-1, "station")


# ================================================================================================== OUTER BLOCKS (NE and SW)
def flip_edges(s, edges):
    if s > 0:
        return edges
    tr = {"N": "S", "S": "N", "E": "W", "W": "E"}
    return "".join(tr[c] for c in edges)


def gaps_of(*keys):
    out = {}
    for key in keys:
        for edge, lst in BRIDGE_GAPS.get(key, {}).items():
            out.setdefault(edge, []).extend(lst)
    return out


O_PARTS = {"A": (2700.0, 900.0, 3900.0, 1800.0, Z2), "B": (4500.0, 900.0, 6000.0, 1800.0, Z1), "W1": (2700.0, 1800.0, 3300.0, 2700.0, Z2),
           "W2": (2700.0, 3300.0, 3300.0, 4200.0, Z2), "N": (3300.0, 3600.0, 5400.0, 4200.0, Z1), "T": (5400.0, 2400.0, 6000.0, 4200.0, TOWER)}
O_COURT = [(3300.0, 1800.0, 5400.0, 3600.0), (5400.0, 1800.0, 6000.0, 2400.0)]
ROOF_RECTS = []          # (rect, top, name): walkable roofs, for the rooftop dressing


def oblock(s, theme):
    X = bg.Xf(s)
    k = "O%d" % s
    cafe = theme == "cafe"
    F = (dict(A=f_brick, B=f_plaster, W1=f_cream, W2=f_brown, N=f_brick, T=f_tower) if cafe else
         dict(A=f_brown, B=f_cream, W1=f_plaster, W2=f_brick, N=f_conc, T=f_tower2))
    for name, (x0, y0, x1, y1, top) in O_PARTS.items():
        r = X.r(x0, y0, x1, y1)
        box("%s_%s" % (k, name), r[0], r[1], r[2], r[3], 0.0, top, F[name])
        if top < TOWER:
            b_roof.rect(r[0], r[1], r[2], r[3], top, top + 4)
            ROOF_RECTS.append((r, top, "%s_%s" % (k, name)))
    # parapets on the street edges (gaps where the bridges land)
    edges = {"A": "SWE", "B": "SW", "W1": "WN", "W2": "WS", "N": "", "T": ""}
    gk = {"A": ("O%d_A" % s,), "B": ("O%d_B" % s,), "W1": ("O%d_W1" % s, "O%d_W" % s), "W2": ("O%d_W2" % s, "O%d_W" % s)}
    for name, ed in edges.items():
        if ed:
            x0, y0, x1, y1, top = O_PARTS[name]
            parapet(X.r(x0, y0, x1, y1), top, gaps_of(*gk[name]), flip_edges(s, ed))
    # courtyard and alley ground
    for i, rr in enumerate(O_COURT):
        ov("%s_Court%d" % (k, i), X.r(*rr), 4.0, cobble if cafe else asphalt_worn, holes=[])
    ov(k + "_Alley", X.r(3900.0, 900.0, 4500.0, 1800.0), 4.0, sidewalk, holes=[])
    ov(k + "_GapW", X.r(2700.0, 2700.0, 3300.0, 3300.0), 4.0, sidewalk, holes=[])
    # access: a long ramp (dressed as stairs) along the west wing up to a podium at the low roof level, a ramp from the podium /
    # north row roof up to the high roof, and a ramp from the courtyard to the low roof of the avenue building B
    x, y = X.p(3480.0, 1850.0)
    bg.stair_ramp(m, k + "_Ramp", x, y, 0.0, X.yaw(90.0), 360, Z1, 1250.0, mat=concrete)
    r = X.r(3300.0, 3100.0, 3960.0, 3600.0)
    box(k + "_Podium", r[0], r[1], r[2], r[3], 0.0, Z1, concrete)
    b_roof.rect(r[0], r[1], r[2], r[3], Z1, Z1 + 4)
    x, y = X.p(3920.0, 3900.0)
    bg.stair_ramp(m, k + "_RoofRamp", x, y, Z1, X.yaw(180.0), 360, Z2 - Z1, 620.0, mat=concrete)
    x, y = X.p(4300.0, 1980.0)
    bg.stair_ramp(m, k + "_RampB", x, y, 0.0, X.yaw(0.0), 360, Z1, 1250.0, mat=concrete)
    r = X.r(5550.0, 1800.0, 5900.0, 2160.0)
    box(k + "_LandB", r[0], r[1], r[2], r[3], 0.0, Z1, concrete)
    b_roof.rect(r[0], r[1], r[2], r[3], Z1, Z1 + 4)
    # jump pads: avenue sidewalk -> high roof; side street -> west wing roof
    px, py = X.p(3300.0, 760.0)
    tx, ty = X.p(3300.0, 1350.0)
    m.jump_pad(k + "_PadAve", px, py, 5.0, (tx, ty, Z2), color=(0.0, 0.8, 1.0) if s > 0 else (1.0, 0.45, 0.1))
    px, py = X.p(2250.0, 3000.0)
    tx, ty = X.p(3000.0, 3700.0)
    m.jump_pad(k + "_PadSide", px, py, 6.0, (tx, ty, Z2), color=(0.0, 0.8, 1.0) if s > 0 else (1.0, 0.45, 0.1))


oblock(1, "cafe")
oblock(-1, "parking")


# ================================================================================================== MIDDLE BLOCKS (NM park, SM construction site)
M_PARTS = {"W": (-1800.0, 1800.0, -1200.0, 4200.0, Z2), "E": (1200.0, 1800.0, 1800.0, 4200.0, Z2), "N": (-1200.0, 3600.0, 1200.0, 4200.0, Z2)}
M_YARD = (-1200.0, 1800.0, 1200.0, 3600.0)


def mblock(s, theme):
    X = bg.Xf(s)
    k = "M%d" % s
    park = theme == "park"
    F = dict(W=f_plaster, E=f_brick, N=f_cream) if park else dict(W=f_frame, E=f_frame, N=f_frame)
    for name, (x0, y0, x1, y1, top) in M_PARTS.items():
        r = X.r(x0, y0, x1, y1)
        box("%s_%s" % (k, name), r[0], r[1], r[2], r[3], 0.0, top, F[name])
        b_roof.rect(r[0], r[1], r[2], r[3], top, top + 4)
        ROOF_RECTS.append((r, top, "%s_%s" % (k, name)))
    parapet(X.r(*M_PARTS["W"][:4]), Z2, gaps_of("M%d_W" % s), flip_edges(s, "WS"))
    parapet(X.r(*M_PARTS["E"][:4]), Z2, gaps_of("M%d_E" % s), flip_edges(s, "ES"))
    ov(k + "_Yard", X.r(*M_YARD), 4.0, grass if park else dirt, holes=[])
    x, y = X.p(-1020.0, 1800.0)
    bg.stair_ramp(m, k + "_RampW", x, y, 0.0, X.yaw(90.0), 360, Z2, 1800.0, mat=concrete)
    x, y = X.p(1020.0, 3600.0)
    bg.stair_ramp(m, k + "_RampE", x, y, 0.0, X.yaw(270.0), 360, Z2, 1800.0, mat=concrete)
    # jump pads from the plaza edge onto the west / east wing roofs
    px, py = X.p(-1500.0, 1650.0)
    tx, ty = X.p(-1500.0, 2300.0)
    m.jump_pad(k + "_PadW", px, py, 4.0, (tx, ty, Z2), color=(0.0, 0.8, 1.0) if s > 0 else (1.0, 0.45, 0.1))
    px, py = X.p(1500.0, 1650.0)
    tx, ty = X.p(1500.0, 2300.0)
    m.jump_pad(k + "_PadE", px, py, 4.0, (tx, ty, Z2), color=(0.0, 0.8, 1.0) if s > 0 else (1.0, 0.45, 0.1))


mblock(1, "park")
mblock(-1, "site")

# ================================================================================================== PLAZA (structure)
rbox(m, "FountainBasin", 0, 0, 55, 1000, 1000, 110, mat=limestone, mesh=m.cylinder)
rbox(m, "FountainWater", 0, 0, 80, 900, 900, 4, mat=water_m, solid=False, mesh=m.cylinder)
rbox(m, "FountainTier1", 0, 0, 170, 360, 360, 120, mat=limestone, mesh=m.cylinder)
rbox(m, "FountainTier2", 0, 0, 300, 200, 200, 140, mat=limestone, mesh=m.cylinder)

# ================================================================================================== DRESSING
LIGHTS = [0]


def light(label, loc, rgb, cd, radius):
    LIGHTS[0] += 1
    return m.accent_light(label, loc, rgb, candela=cd, radius=radius)


def mirror2(fn):
    """Calls fn(s) for s = +1 and -1 (rotation by 180 degrees: points (x, y) -> (s*x, s*y))."""
    for s in (1, -1):
        fn(s)


# ---- A. road markings and kerbs (batches, no shadows)
def stripe(bat, x0, y0, x1, y1, z=3.0):
    bat.rect(x0, y0, x1, y1, z, z + 1.3)


for (xa, xb) in ((-5950.0, -2580.0), (2580.0, 5950.0)):
    stripe(b_py, xa, -14.0, xb, -2.0)                                      # double yellow centre line
    stripe(b_py, xa, 2.0, xb, 14.0)
    for sy in (-1, 1):
        stripe(b_pw, xa, sy * 575.0 - 6.0, xb, sy * 575.0 + 6.0)           # edge lines
        x = xa + 200
        while x < xb - 300:
            if not (1950 < abs(x) < 2600):
                stripe(b_pw, x, sy * 300.0 - 7.0, x + 300.0, sy * 300.0 + 7.0)   # lane dashes
            x += 650.0
for sx in (-1, 1):
    for xc in (sx * 2660.0,):
        for k in range(-5, 6):
            stripe(b_pw, xc - 70, k * 100.0 - 26.0, xc + 70, k * 100.0 + 26.0)  # zebra over the avenue at the plaza
    for sy in (-1, 1):
        for xa_, xb_ in ((sx * 2000.0, sx * 2500.0),):
            lo, hi = min(xa_, xb_), max(xa_, xb_)
            yy = sy * 1000.0
            while abs(yy) < HY - 200:
                if abs(yy) < 1500 or abs(yy) > 1700:
                    stripe(b_py, (lo + hi) / 2 - 5, yy, (lo + hi) / 2 + 5, yy + sy * 260.0, z=6.0)
                yy += sy * 520.0
            for k in range(-2, 3):
                stripe(b_pw, lo + 250 + k * 90.0 - 22, sy * 1000.0 + sy * 560.0 - 80, lo + 250 + k * 90.0 + 22, sy * 1000.0 + sy * 560.0 + 80, z=6.0)
            stripe(b_pw, lo + 20, sy * 700.0 - 5, hi - 20, sy * 700.0 + 5, z=6.0)   # stop line
for (xa, xb) in ((-HX, -2500.0), (2500.0, HX), (-2000.0, 2000.0)):          # kerbs along the avenue
    if xa == -2000.0:
        continue
    for sy in (-1, 1):
        b_kerb.rect(xa, sy * 600.0 - 10, xb, sy * 600.0 + 10, 0.0, 10.0)
for sx in (-1, 1):
    for xe in (2000.0, 2500.0):
        for sy in (-1, 1):
            b_kerb.rect(sx * xe - 10, sy * 600.0, sx * xe + 10, sy * HY, 0.0, 10.0)

# ---- B. ledges: cornices, string courses and plinths around every building
def ledges(rect, top, big=False, courses=True):
    x0, y0, x1, y1 = rect
    out = 35.0 if big else 22.0
    bt_ = b_cornice if big else b_cornice2
    for (a, b, c, d) in ((x0 - out, y0 - out, x1 + out, y0), (x0 - out, y1, x1 + out, y1 + out),
                         (x0 - out, y0, x0, y1), (x1, y0, x1 + out, y1)):
        bt_.rect(a, b, c, d, top - 55.0, top - 8.0)
    if courses:
        for zc in (320.0, 640.0):
            if zc < top - 100:
                for (a, b, c, d) in ((x0 - 10, y0 - 10, x1 + 10, y0), (x0 - 10, y1, x1 + 10, y1 + 10), (x0 - 10, y0, x0, y1), (x1, y0, x1 + 10, y1)):
                    b_cornice2.rect(a, b, c, d, zc - 10.0, zc + 10.0)


for r, top, nm in ROOF_RECTS:
    ledges(r, top)
for s in (1, -1):
    X_ = bg.Xf(s)
    ledges(X_.r(5400.0, 2400.0, 6000.0, 4200.0), TOWER, big=True, courses=False)
    ledges(X_.r(-HX, 900.0, -HX + BW, 900.0 + BW), Z2, big=True)
    # tower crown: setbacks with lit windows and a mast
    a = X_.r(5460.0, 2700.0, 5940.0, 4140.0)
    box("TowerCrown%d" % s, a[0], a[1], a[2], a[3], TOWER, TOWER + 640.0, f_tower2)
    b_cornice.rect(a[0] - 20, a[1] - 20, a[2] + 20, a[3] + 20, TOWER + 640.0, TOWER + 690.0)
    cx, cy = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    b_steel.rect(cx - 6, cy - 6, cx + 6, cy + 6, TOWER + 690.0, TOWER + 1300.0)
    b_beacon.rect(cx - 14, cy - 14, cx + 14, cy + 14, TOWER + 1300.0, TOWER + 1328.0)


# ---- C. shop fronts (all batches)
SIGNS = ["CAFE", "BAR", "PIZZA", "BOOKS", "DELI", "FLORIST", "PHARMACY", "NOODLES", "SHOES", "OPEN", "BAKERY", "GRILL"]
SIGN_KEYS = ["amber", "cyan", "pink", "green", "red"]
shop_i = [0]


def shop_bay(wf, a0, w, kind, name=None, awning=True):
    i = shop_i[0]
    shop_i[0] += 1
    a1 = a0 + w
    fm = i % len(b_fascia)
    fr = b_frame_cream
    wf.rect(b_riser, a0 + 8, a1 - 8, 0, 7, 0, 62)
    if kind == "glass":
        wf.rect(b_winwarm if i % 3 else b_wincool, a0 + 16, a1 - 16, 2, 6, 62, 256)
        wf.rect(fr, a0 + 8, a0 + 20, 0, 11, 56, 266)
        wf.rect(fr, a1 - 20, a1 - 8, 0, 11, 56, 266)
        wf.rect(fr, a0 + 8, a1 - 8, 0, 11, 256, 266)
        wf.rect(fr, a0 + 8, a1 - 8, 0, 11, 56, 66)
        wf.rect(fr, (a0 + a1) / 2 - 4, (a0 + a1) / 2 + 4, 0, 10, 56, 266)
        wf.rect(b_riser, a0 + 30, a1 - 30, 8, 34, 130, 136)
        wf.rect(b_riser, a0 + 30, a1 - 30, 8, 30, 190, 196)
    elif kind == "door":
        dw = 110.0
        da = a0 + w * 0.3
        wf.rect(b_doorw, da, da + dw, 2, 8, 0, 240)
        wf.rect(b_winwarm, da + 20, da + dw - 20, 9, 11, 120, 220)
        wf.rect(fr, da - 10, da, 0, 12, 0, 252)
        wf.rect(fr, da + dw, da + dw + 10, 0, 12, 0, 252)
        wf.rect(fr, da - 10, da + dw + 10, 0, 12, 240, 252)
        wf.rect(b_wincool, da + dw + 50, a1 - 24, 2, 6, 90, 230)
        wf.rect(b_conc_s, da - 10, da + dw + 10, 0, 40, 0, 6)
        wf.rect(b_lamp, a0 + 22, a0 + 42, 6, 22, 246, 262)
    else:
        wf.rect(b_galv, a0 + 14, a1 - 14, 2, 9, 0, 256)
        wf.rect(b_steel, a0 + 10, a1 - 10, 0, 14, 256, 276)
        for gx in (a0 + 8, a1 - 20):
            wf.rect(b_steel, gx, gx + 12, 0, 12, 0, 256)
    wf.rect(b_fascia[fm], a0 + 2, a1 - 2, 0, 18, 274, 330)
    wf.rect(b_cornice2, a0 + 2, a1 - 2, 0, 24, 330, 340)
    if name:
        key = SIGN_KEYS[i % len(SIGN_KEYS)]
        tw = wf.text_width(name, 30)
        if tw < w - 30:
            wf.text(b_sign[key], name, (a0 + a1) / 2, 20, 302, 30, thick=3.0)
    if awning and kind != "shutter":
        wf.prism(b_awn[i % len(b_awn)], a0 + 6, a1 - 6, [(16, 262), (150, 222), (150, 208), (16, 248)])


def shop_row(wf, a0, a1, seed, kinds=("glass", "door", "glass", "shutter", "glass", "door")):
    r = random.Random(seed)
    a = a0 + 20
    k = r.randint(0, 5)
    while a < a1 - 280:
        w = r.choice((300.0, 330.0, 360.0, 420.0))
        w = min(w, a1 - 20 - a)
        if w < 260:
            break
        kind = kinds[k % len(kinds)]
        k += 1
        shop_bay(wf, a, w, kind, SIGNS[(shop_i[0] * 5 + seed) % len(SIGNS)] if kind == "glass" and r.random() < 0.8 else None)
        a += w + 12.0


def shops_for(s):
    X_ = bg.Xf(s)

    def wf(p, d, n):
        return bg.WF(X_.p(*p), X_.p(*d), X_.p(*n))
    shop_row(wf((2700.0, 900.0), (1, 0), (0, -1)), 0.0, 1200.0, 3 + s)            # OA avenue face
    shop_row(wf((4500.0, 900.0), (1, 0), (0, -1)), 0.0, 1500.0, 5 + s)            # OB avenue face
    shop_row(wf((2700.0, 900.0), (0, 1), (-1, 0)), 0.0, 900.0, 7 + s)             # OA side street face
    shop_row(wf((2700.0, 1800.0), (0, 1), (-1, 0)), 0.0, 900.0, 9 + s)            # OW1
    shop_row(wf((2700.0, 3300.0), (0, 1), (-1, 0)), 0.0, 900.0, 11 + s)           # OW2
    shop_row(wf((3900.0, 900.0), (0, 1), (1, 0)), 0.0, 900.0, 13 + s, kinds=("shutter", "door"))      # alley faces
    shop_row(wf((4500.0, 900.0), (0, 1), (-1, 0)), 0.0, 900.0, 15 + s, kinds=("door", "shutter"))
    shop_row(wf((3300.0, 1800.0), (0, 1), (1, 0)), 0.0, 900.0, 17 + s, kinds=("glass", "door"))      # courtyard faces
    shop_row(wf((3960.0, 3600.0), (1, 0), (0, -1)), 0.0, 1400.0, 19 + s, kinds=("glass", "door", "glass"))
    if s < 0:
        return
    # middle wings (park side only): plaza face and park face
    shop_row(wf((-1800.0, 1800.0), (1, 0), (0, -1)), 0.0, 600.0, 21 + s)
    shop_row(wf((1200.0, 1800.0), (1, 0), (0, -1)), 0.0, 600.0, 23 + s)
    shop_row(wf((1800.0, 1800.0), (0, 1), (1, 0)), 0.0, 2400.0, 25 + s, kinds=("door", "shutter", "door"))
    shop_row(wf((-1800.0, 1800.0), (0, 1), (-1, 0)), 0.0, 2400.0, 27 + s, kinds=("door", "glass", "door"))


if DRESS:
    mirror2(shops_for)
    # the bank / station fronts on the avenue and on the side street get their own treatment (see the base dressing)

# ---- D. rooftops: cover units, vents, tanks, antennas
def unit(x, y, z, sx, sy, sz, yaw=0.0, solid=True):
    bat = b_cover if solid else b_galv
    bat.box(x, y, z + sz / 2, sx, sy, sz, yaw=yaw)
    b_steel.box(x, y, z + sz + 3, sx + 8, sy + 8, 6, yaw=yaw)
    d = min(sx, sy) * 0.6
    b_steeld.cyl(x, y, z + sz + 6, z + sz + 12, d / 2, sides=12)
    b_steel.cyl(x + sx * 0.3, y, z + sz, z + sz + 70, 9, sides=8)


def vent(x, y, z, h=90.0, r=22.0):
    b_galv.cyl(x, y, z, z + h, r, sides=8)
    b_galv.cyl(x, y, z + h, z + h + 16, r * 1.6, sides=8, r1=r * 0.6)


def tank(x, y, z, r=130.0, h=300.0):
    for dx in (-1, 1):
        for dy in (-1, 1):
            b_steeld.box(x + dx * r * 0.55, y + dy * r * 0.55, z + 55, 12, 12, 110)
    B("TankWood", wood_dark, max_dist=12000.0).cyl(x, y, z + 110, z + 110 + h, r, sides=14)
    for hz in (0.25, 0.55, 0.85):
        b_steeld.cyl(x, y, z + 110 + h * hz, z + 110 + h * hz + 7, r + 5, sides=14)
    b_steeld.cyl(x, y, z + 110 + h, z + 110 + h + r * 0.45, r * 1.06, sides=14, r1=0.1)


def antenna(x, y, z, h=520.0):
    b_steel.box(x, y, z + h / 2, 7, 7, h)
    for k, hz in enumerate((0.55, 0.75, 0.9)):
        b_steel.box(x, y, z + h * hz, 90 - 22 * k, 5, 5)
    b_beacon.box(x, y, z + h + 8, 18, 18, 18)


def roofs_for(s):
    X_ = bg.Xf(s)
    r_ = random.Random(40 + s)

    def P(x, y):
        return X_.p(x, y)
    # NE / SW outer block roofs
    x, y = P(3420.0, 1150.0)
    unit(x, y, Z2, 260, 190, 150, yaw=X_.yaw(0.0))
    x, y = P(3750.0, 1650.0)
    tank(x, y, Z2, 120, 280)
    x, y = P(5150.0, 1200.0)
    unit(x, y, Z1, 300, 200, 140, yaw=X_.yaw(0.0))
    x, y = P(4700.0, 3900.0)
    unit(x, y, Z1, 260, 180, 130, yaw=X_.yaw(0.0))
    for (vx, vy, vz) in ((3100.0, 1350.0, Z2), (3800.0, 1000.0, Z2), (2900.0, 2100.0, Z2), (3000.0, 3500.0, Z2), (5600.0, 1100.0, Z1),
                         (4100.0, 3750.0, Z1), (5000.0, 1500.0, Z1)):
        x, y = P(vx, vy)
        vent(x, y, vz)
    x, y = P(2850.0, 3950.0)
    antenna(x, y, Z2)
    x, y = P(5700.0, 1550.0)
    antenna(x, y, Z1, 420.0)
    # middle wing roofs
    for (vx, vy) in ((-1500.0, 2100.0), (-1550.0, 3300.0), (1450.0, 2800.0), (700.0, 3900.0), (-700.0, 3950.0)):
        x, y = P(vx, vy)
        vent(x, y, Z2, 80.0)
    x, y = P(1500.0, 3900.0)
    antenna(x, y, Z2, 600.0)
    x, y = P(-1500.0, 3950.0)
    tank(x, y, Z2, 120, 260)


if DRESS:
    mirror2(roofs_for)

# ---- E. street furniture: lamps, trees, benches, bins, bollards, cars, buses
def lamp(x, y, toward, h=520.0, lit=False, label="Lamp"):
    """toward = unit vector the arm reaches to (over the road)."""
    b_steeld.cyl(x, y, 0.0, h, 7.0, sides=8, r1=5.0)
    b_steeld.cyl(x, y, 0.0, 34.0, 13.0, sides=8, r1=9.0)
    ax, ay = x + toward[0] * 110.0, y + toward[1] * 110.0
    b_steeld.bar((x, y, h - 12), (ax, ay, h + 4), 6.0)
    b_lamp.box(ax, ay, h - 2, 46 if abs(toward[0]) > 0.5 else 22, 22 if abs(toward[0]) > 0.5 else 46, 9)
    b_steeld.box(ax, ay, h + 5, 52 if abs(toward[0]) > 0.5 else 28, 28 if abs(toward[0]) > 0.5 else 52, 7)
    if lit:
        light(label, (ax, ay, h - 30), WARM, 110.0, 1000.0)


TRUNKS = [bg.tree_trunk_mesh(h_, r_, seed=k_) for k_, (h_, r_) in enumerate(((520.0, 20.0), (580.0, 22.0), (470.0, 18.0)))]
b_trunk = B("Trunks", bark, max_dist=14000.0)
tree_count = [0]


def tree(x, y, z=0.0, scale=1.0, seed=0, crowns=2):
    r_ = random.Random(seed * 7 + int(x) + int(y))
    k = tree_count[0] % len(TRUNKS)
    tree_count[0] += 1
    b_trunk.append_mesh(TRUNKS[k], (x, y, z), yaw=r_.uniform(0, 360))
    hh = (520.0, 580.0, 470.0)[k] * scale
    base = z + hh * 0.5
    mats = (leaf_a, leaf_b, leaf_c)
    m.prop("TreeCrownA", "shrub_b", x + r_.uniform(-20, 20), y + r_.uniform(-20, 20), base, yaw=r_.uniform(0, 360), scale=3.4 * scale,
           solid=False, material=mats[k % 3])
    if crowns > 1:
        a = r_.uniform(0, 6.28)
        m.prop("TreeCrownB", "shrub_b", x + math.cos(a) * 130 * scale, y + math.sin(a) * 130 * scale, base + 170 * scale,
               yaw=r_.uniform(0, 360), scale=2.7 * scale, solid=False, material=mats[(k + 1) % 3])


def bench(x, y, yaw, solid=True):
    c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    bat = b_woods if solid else b_wood
    bat.box(x, y, 46, 170 * abs(c) + 52 * abs(sn), 170 * abs(sn) + 52 * abs(c), 9)
    bx, by = x - sn * 0 + (-sn) * -22, y + c * -22
    bat.box(x + sn * 24, y - c * 24, 78, 170 * abs(c) + 8 * abs(sn), 170 * abs(sn) + 8 * abs(c), 44)
    for sg in (-1, 1):
        b_steeld.box(x + c * 70 * sg, y + sn * 70 * sg, 22, 8 * abs(c) + 44 * abs(sn), 8 * abs(sn) + 44 * abs(c), 44)


def planter(x, y, sx=200.0, sy=200.0, h=70.0, shrub=True):
    b_conc_s.rect(x - sx / 2, y - sy / 2, x + sx / 2, y + sy / 2, 0, h)
    b_soil.rect(x - sx / 2 + 12, y - sy / 2 + 12, x + sx / 2 - 12, y + sy / 2 - 12, h, h + 4)
    if shrub:
        m.prop("PlanterShrub", "shrub_a", x, y, h, yaw=rng.uniform(0, 360), scale=min(sx, sy) / 150.0, solid=False, material=leaf_c)


def bin_(x, y):
    B("Bins", S("ContainerGreen", "BinGreen", albedo=(44, 78, 60)), max_dist=6000.0).cyl(x, y, 0, 86, 26, sides=10)
    b_steeld.cyl(x, y, 86, 92, 28, sides=10)


def bollard(x, y):
    b_concd_s.cyl(x, y, 0, 80, 12, sides=8)


def hydrant(x, y):
    B("Hydrant", S("WoodPaintedRed", "Hydrant", albedo=(150, 40, 34)), max_dist=5000.0).cyl(x, y, 0, 60, 12, sides=8)


def street_furniture(s):
    X_ = bg.Xf(s)
    # lamps along the avenue sidewalks (north side s=+1 mirrored): every 800, offset between the trees
    for i, x in enumerate(range(-5600, 5601, 800)):
        if abs(x) < 2800 or abs(x) > 5700:
            continue
        if abs(abs(x) - 2250) < 400:
            continue
        px, py = X_.p(x, 760.0)
        toward = X_.p(0, -1)
        lamp(px, py, toward, lit=(i % 3 == 0))
    # lamps in the side streets
    for yy in (1400.0, 2600.0, 3800.0):
        for xx, tw in ((2100.0, (1, 0)), (2400.0, (-1, 0))):
            if (xx == 2100.0 and yy != 2600.0) or (xx == 2400.0 and yy == 2600.0):
                continue
            px, py = X_.p(xx + (-40 if xx == 2100 else 40), yy)
            lamp(px, py, X_.p(*tw))
    # street trees: sidewalk edge in front of the shops, avenue and side streets
    for x in (-5400, -4600, -3200, 3200, 4600, 5400):
        px, py = X_.p(x * 1.0, 700.0)
        tree(px, py, 5.0, 0.95, seed=3)
    for y in (1500.0, 3200.0):
        px, py = X_.p(1900.0, y)
        tree(px, py, 5.0, 0.9, seed=5)
        px, py = X_.p(2600.0, y + 700)
        tree(px, py, 5.0, 0.9, seed=6)
    # bins, bollards, hydrants along the sidewalks
    for x in (-4900, -3700, 3700, 4900):
        px, py = X_.p(x * 1.0, 840.0)
        bin_(px, py)
    for x in (-5100, -3350, 3350, 5100):
        px, py = X_.p(x * 1.0, 640.0)
        hydrant(px, py)
    for yy_ in (-780.0, -650.0, -520.0, 520.0, 650.0, 780.0):
        px, py = X_.p(1820.0, yy_)
        bollard(px, py)


if DRESS:
    mirror2(street_furniture)

# vehicles on the avenue: cars are generated meshes, buses and trucks are boxes (batches) with a hidden collider
b_bus = {}


def vehicle(x, y, yaw, length, width, height, colour, glassy=True, kind="bus"):
    key = colour
    if key not in b_bus:
        b_bus[key] = B("Veh_" + key, {"white": car_white, "red": car_red, "blue": car_blue, "yellow": car_yellow,
                                      "green": car_green, "grey": car_grey}[key], max_dist=12000.0)
    bat = b_bus[key]
    c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def at(dx, dy):
        return x + c * dx - sn * dy, y + sn * dx + c * dy
    cx, cy = x, y
    bat.box(cx, cy, 55 + (height - 55) / 2, length, width, height - 55, yaw=yaw)
    B("VehDark", car_glass, max_dist=12000.0).box(cx, cy, 55 + (height - 55) * 0.66, length - 30, width + 4, (height - 55) * 0.32, yaw=yaw)
    b_rubber.box(cx, cy, 30, length - 60, width - 20, 60, yaw=yaw)
    for dx in (-length * 0.32, length * 0.32):
        for dy in (-width / 2 - 2, width / 2 + 2):
            px, py = at(dx, dy)
            b_rubber.box(px, py, 48, 100, 24, 96, yaw=yaw)
    b_steel.box(cx, cy, height + 8, length * 0.5, width * 0.5, 16, yaw=yaw)
    hx, hy = at(length / 2 - 4, 0)
    b_lamp.box(hx, hy, 110, 8, width * 0.8, 30, yaw=yaw)
    tx, ty = at(-length / 2 + 4, 0)
    B("VehTail", tail_lamp, shadow=False, max_dist=9000.0).box(tx, ty, 110, 8, width * 0.8, 30, yaw=yaw)
    col = m.box("VehCollider", x, y, height / 2, length - 30, width - 10, height, yaw=yaw, mat=None, solid=True)
    col.set_actor_hidden_in_game(True)


CARS = [(-5200.0, -440.0, 3.0, "sedan", car_red), (-4700.0, 260.0, 178.0, "van", car_white), (-4150.0, -150.0, 8.0, "hatch", car_blue),
        (-3600.0, 440.0, -6.0, "sedan", car_grey), (-3050.0, -330.0, 2.0, "hatch", car_green), (-5700.0, 400.0, 182.0, "sedan", car_black),
        (-2980.0, 120.0, 14.0, "van", car_yellow)]
if DRESS:
    paints_b = [car_blue, car_yellow, car_white, car_red, car_grey, car_green, car_black]
    for i, (x, y, yaw, kind, paint_) in enumerate(CARS):
        kp.car(m, "CarR%d" % i, x, y, 0.0, yaw, paint_, car_glass, rubber, kind, solid=True, tail=tail_lamp)
        kp.car(m, "CarB%d" % i, -x, -y, 0.0, yaw + 180.0, paints_b[i], car_glass, rubber, kind, solid=True, tail=tail_lamp)
    vehicle(-3300.0, 40.0, 0.0, 1150.0, 250.0, 320.0, "yellow")
    vehicle(3300.0, -40.0, 180.0, 1150.0, 250.0, 320.0, "blue")
    vehicle(-4900.0, -30.0, 176.0, 800.0, 240.0, 280.0, "white", kind="truck")
    vehicle(4900.0, 30.0, -4.0, 800.0, 240.0, 280.0, "red", kind="truck")
    # barricades and planters that cut the long sight lines of the avenue
    for s_ in (1, -1):
        for (x, y) in ((2850.0, 130.0), (2850.0, -300.0)):
            b_concd_s.rect(s_ * x - 22, s_ * y - 130, s_ * x + 22, s_ * y + 130, 0, 100)
        planter(s_ * 1400.0, s_ * 640.0, 300, 160, 80)
        planter(s_ * 5100.0, s_ * 20.0, 240, 140, 80)

# ---- F. plaza: fountain jets, benches, tree planters, kiosks, lamps, the metro entrances
def plaza_dress():
    for (dx, dy, hh) in ((0, 0, 330), (95, 0, 160), (-95, 0, 160), (0, 95, 160), (0, -95, 160)):
        rbox(m, "Jet", dx, dy, 430 + hh / 2 if dx == dy == 0 else 380 + hh / 2, 16 if dx == dy == 0 else 10, 16 if dx == dy == 0 else 10, hh,
             mat=glass_m, solid=False, mesh=m.cylinder)
    for k in range(10):
        a = 2 * math.pi * k / 10
        rbox(m, "FountainSpout", math.cos(a) * 400, math.sin(a) * 400, 150, 12, 12, 130, pitch=0, mat=glass_m, solid=False, mesh=m.cylinder)
    b_marble.cyl(0, 0, 110, 118, 500, sides=28)
    for k in range(8):                                                       # benches around the fountain
        a = 2 * math.pi * (k + 0.5) / 8
        bench(math.cos(a) * 780, math.sin(a) * 780, math.degrees(a) + 90.0 + 180.0)
    for (px, py) in ((-1550.0, -1050.0), (1550.0, 1050.0), (-1550.0, 1050.0), (1550.0, -1050.0), (-1050.0, -1550.0), (1050.0, 1550.0),
                     (-1050.0, 1550.0), (1050.0, -1550.0)):
        planter(px, py, 260, 260, 60, shrub=False)
        tree(px, py, 60.0, 1.1, seed=9, crowns=2)
    for (px, py, tw) in ((-1000.0, 560.0, (0, -1)), (1000.0, -560.0, (0, 1)), (-1000.0, -1300.0, (0, 1)), (1000.0, 1300.0, (0, -1))):
        lamp(px, py, tw, h=640.0, lit=True, label="PlazaLamp")
    for (kx, ky) in ((-1250.0, -700.0), (1250.0, 700.0)):                       # newsstand kiosks
        b_conc_s.rect(kx - 160, ky - 100, kx + 160, ky + 100, 0, 250)
        b_riser.rect(kx - 170, ky - 110, kx + 170, ky + 110, 250, 275)
        b_winwarm.rect(kx - 140, ky - 104, kx + 140, ky - 100, 90, 200) if ky < 0 else b_winwarm.rect(kx - 140, ky + 100, kx + 140, ky + 104, 90, 200)
        b_awn[0].box(kx, ky - 130 if ky < 0 else ky + 130, 225, 330, 90, 8)
    # metro entrances: kerbs, handrails, a glass canopy over the stairs and a sign
    for (x0, y0, x1, y1) in SHAFTS:
        north = y0 > 0
        for xs in (x0 - 34, x1):
            b_conc_s.rect(xs, y0 + 2, xs + 34, y1, 0, 95)
            b_steel.rect(xs - 2, y0, xs + 36, y1, 95, 103)
        far, near = (y1, y0) if north else (y0, y1)
        sgn = 1 if north else -1
        for (px, py) in ((x0 - 17, far - sgn * 40), (x1 + 17, far - sgn * 40), (x0 - 17, far - sgn * 360), (x1 + 17, far - sgn * 360)):
            b_steeld.box(px, py, 175, 12, 12, 160)
        ya, yb = sorted((far - sgn * 40, far - sgn * 360))
        for xs in (x0 - 17, x1 + 17):
            b_steeld.rect(xs - 6, ya - 6, xs + 6, yb + 6, 250, 262)
        b_glass.rect(x0 - 30, ya - 20, x1 + 30, yb + 20, 262, 268)
        b_steeld.rect(x0 - 40, ya - 24, x1 + 40, ya - 8, 255, 285) if sgn < 0 else b_steeld.rect(x0 - 40, yb + 8, x1 + 40, yb + 24, 255, 285)
        wf = bg.WF(((x0 + x1) / 2, far - sgn * 40 + sgn * 14), (1, 0) if north else (-1, 0), (0, 1) if north else (0, -1))
        wf.text(b_sign["cyan"], "METRO", 0, 12, 340, 34, thick=3.0)
        b_steeld.rect(x0 - 40, min(far + sgn * 4, far + sgn * 22), x1 + 40, max(far + sgn * 4, far + sgn * 22), 305, 375)
        light("MetroLight", ((x0 + x1) / 2, far - sgn * 150, 230), (0.7, 0.9, 1.0), 25.0, 500.0)


def metro_dress():
    segs = bg.rect_gaps(CORR[0], CORR[2], [(-600.0, 400.0), (600.0, 400.0)])
    for (a, b) in segs:
        for sy in (-1, 1):
            if sy > 0:
                b_tilew.rect(a, 444, b, 450, TUN, -110.0)
                b_marbled.rect(a, 438, b, 450, TUN, TUN + 90)
            else:
                b_tilew.rect(a, -450, b, -444, TUN, -110.0)
                b_marbled.rect(a, -450, b, -438, TUN, TUN + 90)
    for x in range(-1300, 1301, 260):
        for sy in (-150.0, 150.0):
            b_tube.rect(x - 80, sy - 14, x + 80, sy + 14, -112.0, -102.0)
    for x in range(-1200, 1201, 400):
        B("MetroBeam", concrete_dark).rect(x - 22, -450, x + 22, 450, -118.0, -100.0)
    for (x, sy) in ((-1150.0, -1), (-250.0, 1), (250.0, -1), (1150.0, 1)):                 # kiosks / ticket machines (cover)
        y0, y1 = (-450.0, -110.0) if sy < 0 else (110.0, 450.0)
        b_concd_s.rect(x - 140, y0, x + 140, y1, TUN, TUN + 280)
        b_steeld.rect(x - 146, y0 - 4 if sy < 0 else y0, x + 146, y1 if sy < 0 else y1 + 4, TUN + 280, TUN + 292)
        yface = y1 if sy < 0 else y0
        b_tube.rect(x - 100, yface - 3 if sy < 0 else yface - 1, x + 100, yface + 1 if sy < 0 else yface + 3, TUN + 170, TUN + 250)
    for x in (-700.0, 0.0, 700.0):
        b_concd_s.cyl(x, 0, TUN, TUN + 300, 75, sides=12)
        b_tilew.cyl(x, 0, TUN, TUN + 300, 78, sides=12)
    for xs, name in ((-1000.0, "METRO"), (1000.0, "METRO")):
        wf = bg.WF((xs, 444.0), (1, 0), (0, -1))
        wf.text(b_sign["cyan"], "METRO", 0, 3, -230, 46, thick=3.0)
    for xs in (-1150.0, 1150.0):
        wf = bg.WF((xs, -444.0), (-1, 0), (0, 1))
        wf.text(b_sign["amber"], "EXIT", 0, 3, -230, 40, thick=3.0)
    for x in (-1000.0, -330.0, 330.0, 1000.0):
        light("MetroLamp", (x, 0, -170), (0.78, 0.9, 1.0), 38.0, 750.0)


if DRESS:
    plaza_dress()
    metro_dress()

# ---- H. park (north) and construction site (south), in north coordinates through Xf
def park_dress():
    for (x0, y0, x1, y1) in ((-110.0, 1800.0, 110.0, 3600.0), (-800.0, 2330.0, 800.0, 2420.0), (-800.0, 3120.0, 800.0, 3200.0)):
        b_path.rect(x0, y0, x1, y1, 4.0, 4.8)
    pr = (0.0, 2780.0)
    rbox(m, "PondRim", pr[0], pr[1], 22, 900, 900, 44, mat=limestone, solid=False, mesh=m.cylinder)
    rbox(m, "PondWater", pr[0], pr[1], 36, 810, 810, 4, mat=water_m, solid=False, mesh=m.cylinder)
    for (tx, ty, sc) in ((-720.0, 2150.0, 1.1), (720.0, 2150.0, 1.1), (-720.0, 3350.0, 1.2), (720.0, 3350.0, 1.2), (-560.0, 2780.0, 1.0),
                         (560.0, 2780.0, 1.0), (0.0, 2050.0, 0.9), (-720.0, 2800.0, 1.0)):
        tree(tx, ty, 4.0, sc, seed=11)
    hedge = B("Hedge", S("Grass", "Hedge", albedo=(40, 66, 34), desat=1.0, tiling=1.0), solid=True)
    for (x0, y0, x1, y1) in ((-650.0, 2420.0, -250.0, 2480.0), (250.0, 2420.0, 650.0, 2480.0), (-650.0, 3080.0, -250.0, 3140.0),
                             (250.0, 3080.0, 650.0, 3140.0), (-780.0, 2540.0, -720.0, 2820.0), (720.0, 2540.0, 780.0, 2820.0)):
        hedge.rect(x0, y0, x1, y1, 4.0, 100.0)
    for (bx, by, yaw) in ((-200.0, 2250.0, 0.0), (200.0, 2250.0, 0.0), (-200.0, 3330.0, 180.0), (200.0, 3330.0, 180.0), (-880.0, 2600.0, 90.0),
                          (880.0, 2600.0, 270.0)):
        bench(bx, by, yaw)
    # the pavilion: a small cafe with a roof overhang (cover in the middle of the park)
    box("ParkCafe", -400.0, 2980.0, 400.0, 3480.0, 0.0, 300.0, f_plaster)
    b_roofg.rect(-440.0, 2940.0, 440.0, 3520.0, 300.0, 330.0)
    b_cornice.rect(-440.0, 2940.0, 440.0, 3520.0, 300.0, 340.0)
    wf = bg.WF((0.0, 2980.0), (1, 0), (0, -1))
    shop_bay(wf, -380.0, 360.0, "glass", "PARK", awning=True)
    shop_bay(wf, 20.0, 360.0, "glass", "CAFE", awning=True)
    for (fx, fy, mt) in ((-460.0, 2000.0, 0), (460.0, 2000.0, 1), (-460.0, 3500.0, 2), (460.0, 3500.0, 0)):
        B("Flower%d" % mt, S("Canvas", "Flower%d" % mt, albedo=[(170, 50, 60), (200, 170, 50), (130, 70, 150)][mt], desat=1.0), shadow=False).rect(
            fx - 120, fy - 120, fx + 120, fy + 120, 4.0, 20.0)
    for (lx, ly, tw) in ((-340.0, 2000.0, (0, 1)), (340.0, 2000.0, (0, 1)), (-340.0, 3550.0, (0, -1)), (340.0, 3550.0, (0, -1))):
        lamp(lx, ly, tw, lit=False)
    for (bx, by) in ((-120.0, 2000.0), (130.0, 3560.0)):
        bin_(bx, by)


def crane(x, y, h=1900.0):
    yel = B("CraneYellow", S("WoodPaintedGrey", "CraneYellow", albedo=(206, 164, 28)), max_dist=16000.0)
    w = 130.0
    b_concd_s.rect(x - 150, y - 150, x + 150, y + 150, 0, 100)
    n = int(h // 150)
    for k in range(n):
        z0, z1 = k * 150.0, (k + 1) * 150.0
        for sx_ in (-1, 1):
            for sy_ in (-1, 1):
                yel.box(x + sx_ * w / 2, y + sy_ * w / 2, (z0 + z1) / 2, 9, 9, 152)
        for (ax, ay, bx_, by_) in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
            yel.bar((x + ax * w / 2, y + ay * w / 2, z0 if k % 2 == 0 else z1), (x + bx_ * w / 2, y + by_ * w / 2, z1 if k % 2 == 0 else z0), 6.0)
    zt = n * 150.0
    yel.box(x, y, zt + 40, 190, 190, 80)
    yel.box(x + 330, y, zt + 150, 1100, 30, 24)                                 # jib
    yel.box(x + 330, y, zt + 112, 1100, 30, 14)
    for k in range(9):
        a_, b_ = x - 200 + k * 130, x - 200 + (k + 1) * 130
        yel.bar((a_, y, zt + 114 if k % 2 == 0 else zt + 148), (b_, y, zt + 148 if k % 2 == 0 else zt + 114), 8.0)
    yel.box(x - 330, y, zt + 130, 360, 30, 24)                                  # counter jib + weights
    B("CraneWeight", concrete_dark, max_dist=16000.0).box(x - 480, y, zt + 60, 200, 110, 110)
    yel.box(x - 10, y, zt + 250, 14, 14, 160)
    yel.bar((x - 10, y, zt + 330), (x + 800, y, zt + 156), 5.0)
    yel.bar((x - 10, y, zt + 330), (x - 450, y, zt + 142), 5.0)
    steel_ = b_steeld
    steel_.bar((x + 700, y, zt + 112), (x + 700, y, zt - 300), 4.0)
    yel.box(x + 700, y, zt - 330, 40, 40, 50)
    b_beacon.box(x - 10, y, zt + 345, 20, 20, 20)


def site_dress():
    """The construction site in the south middle block (the north park rotated by 180 degrees; written in north coordinates)."""
    T = bg.Xf(-1)
    P = T.p
    cont = {c: B("Cont%s" % c, surface("Container" + c), solid=True) for c in ("Red", "Blue", "Green", "Yellow", "Grey")}
    for (cx, cy, yaw, c, lvl) in ((-520.0, 2100.0, 0.0, "Red", 0), (-520.0, 2100.0, 0.0, "Blue", 1), (460.0, 2350.0, 90.0, "Blue", 0),
                                  (0.0, 3100.0, 0.0, "Green", 0), (-600.0, 3300.0, 90.0, "Yellow", 0), (550.0, 3250.0, 0.0, "Grey", 0),
                                  (550.0, 3250.0, 0.0, "Red", 1)):
        x, y = P(cx, cy)
        cont[c].box(x, y, 130 + lvl * 260.0, 600, 240, 260, yaw=yaw)
    for (dx, dy, r) in ((-250.0, 2650.0, 380.0), (300.0, 2800.0, 300.0)):
        x, y = P(dx, dy)
        m.cone("DirtMound", x, y, 0.0, 190.0, r * 2, mat=dirt, solid=True)
    jb = B("Jersey", concrete_pale, solid=True)
    for (x0, y0, x1, y1) in ((-700.0, 2480.0, -350.0, 2540.0), (350.0, 2850.0, 700.0, 2910.0), (-250.0, 3480.0, 200.0, 3540.0), (-100.0, 1980.0, 260.0, 2040.0)):
        r = T.r(x0, y0, x1, y1)
        jb.rect(r[0], r[1], r[2], r[3], 0, 110)
    for (px, py) in ((-300.0, 3500.0), (350.0, 3550.0)):
        x, y = P(px, py)
        B("Pallet", wood_dark, solid=True).rect(x - 60, y - 50, x + 60, y + 50, 0, 120)
    x, y = P(-150.0, 3050.0)
    crane(x, y)
    stack = B("Bricks", brick_m, solid=True)
    for (x0, y0, x1, y1, h) in ((300.0, 2050.0, 500.0, 2200.0, 110.0), (320.0, 2220.0, 500.0, 2300.0, 70.0)):
        r = T.r(x0, y0, x1, y1)
        stack.rect(r[0], r[1], r[2], r[3], 0, h)
    for (lx, ly) in ((-340.0, 2000.0), (340.0, 3550.0)):
        x, y = P(lx, ly)
        light("SiteLamp", (x, y, 380), (1.0, 0.85, 0.6), 60.0, 900.0)
        b_steeld.cyl(x, y, 0, 380, 7, sides=8)
        b_lamp.box(x, y, 380, 70, 30, 10)
    # scaffolding on the inner faces of the two wings and the north row (pipes, boards, green netting)
    net = B("SiteNet", S("Canvas", "SiteNet", albedo=(60, 96, 64), desat=1.0), shadow=False, max_dist=16000.0)
    for (x0, y0, x1, y1, face) in ((-1200.0, 1900.0, -1200.0, 3600.0, "E"), (1200.0, 1900.0, 1200.0, 3600.0, "W"), (-1200.0, 3600.0, 1200.0, 3600.0, "S")):
        a, b = P(x0, y0), P(x1, y1)
        along_y = abs(a[0] - b[0]) < 1
        lo, hi = (min(a[1], b[1]), max(a[1], b[1])) if along_y else (min(a[0], b[0]), max(a[0], b[0]))
        # which side is 'out' (into the yard): world direction from the wall into the yard
        yard_c = P(0.0, 2700.0)
        sgn = 1 if ((yard_c[0] - a[0]) > 0 if along_y else (yard_c[1] - a[1]) > 0) else -1
        for lvl in range(0, 3):
            z0 = lvl * 320.0
            k = lo + 100.0
            while k < hi - 50:
                if along_y:
                    b_steeld.box(a[0] + sgn * 120, k, z0 + 160, 7, 7, 320)
                else:
                    b_steeld.box(k, a[1] + sgn * 120, z0 + 160, 7, 7, 320)
                k += 300.0
            if along_y:
                B("Boards", wood_dark, max_dist=12000.0).rect(min(a[0], a[0] + sgn * 120), lo + 60, max(a[0], a[0] + sgn * 120), hi - 60, z0 + 318, z0 + 330)
                b_steeld.rect(a[0] + sgn * 120 - 3, lo + 60, a[0] + sgn * 120 + 3, hi - 60, z0 + 160, z0 + 166)
                net.rect(a[0] + sgn * 124 - 1, lo + 60, a[0] + sgn * 124 + 1, hi - 60, z0 + 40, z0 + 300) if lvl == 2 else None
            else:
                B("Boards", wood_dark, max_dist=12000.0).rect(lo + 60, min(a[1], a[1] + sgn * 120), hi - 60, max(a[1], a[1] + sgn * 120), z0 + 318, z0 + 330)
                b_steeld.rect(lo + 60, a[1] + sgn * 120 - 3, hi - 60, a[1] + sgn * 120 + 3, z0 + 160, z0 + 166)
                net.rect(lo + 60, a[1] + sgn * 124 - 1, hi - 60, a[1] + sgn * 124 + 1, z0 + 40, z0 + 300) if lvl == 2 else None


if DRESS:
    park_dress()
    site_dress()


# ---- I. the two bases: front, details inside, skylights, chandeliers, vault / departures board
gold_m = S("BrushedMetal", "Brass", albedo=(176, 138, 62), metal=0.75, rb=0.05, ns=0.4)
gold = B("Gold", gold_m, max_dist=12000.0)
team_ring = {1: kc.emit("DtTeamRed", (1.0, 0.06, 0.05), 1.0), -1: kc.emit("DtTeamBlue", (0.12, 0.35, 1.0), 1.2)}
clock_face = kc.emit("DtClockFace", (1.0, 0.88, 0.62), 0.5)


def base_dress(s, kind):
    X = bg.Xf(s)
    bank = kind == "bank"
    T = 90.0
    H = 860.0

    def P(u, v):
        return X.p(-HX + u, 900.0 + v)

    def R(u0, v0, u1, v1):
        return X.r(-HX + u0, 900.0 + v0, -HX + u1, 900.0 + v1)
    fr = bg.WF(P(0, 0), X.p(1, 0), X.p(0, 1))        # a along u, o along v (into the block)
    fr2 = bg.WF(P(0, 0), X.p(0, 1), X.p(1, 0))       # a along v, o along u
    fm_b = b_marble if bank else B("StationTrim", sand_floor, max_dist=14000.0)
    # ---- the avenue front
    if bank:
        col = bg.mesh_asset("BankColPortico", lambda: mesh_b.column_mesh(800.0, 52, flutes=14, drums=3, seed=4, plinth_k=2.2, abacus_k=2.4))
        for i, u in enumerate((900.0, 1250.0, 2050.0, 2400.0)):
            x, y = P(u, -150.0)
            mapkit_b.put(m, "BankPorticoCol%d" % i, col, x, y, 0.0, mat=marble_wall)
        fr.rect(fm_b, 780, 2520, -270, 0, 800, 890)
        fr2.prism(fm_b, -270, 0, [(780, 890), (2520, 890), (1650, 1080)])
        fr.rect(fm_b, 760, 2540, -290, -270, 800, 900)
        wf = bg.WF(P(1650, -272), X.p(-1, 0), X.p(0, -1))
        wf.text(b_sign["amber"], "BANK", 0, 4, 845, 64, thick=5.0)
    else:
        fr.rect(b_steeld, 900, 2400, -330, 0, 440, 470)
        fr.rect(b_glass, 900, 2400, -330, 0, 470, 474)
        for u in (920.0, 2380.0):
            fr.rect(b_steeld, u - 8, u + 8, -330, -314, 0, 440)
        fr.rect(fm_b, 780, 2520, -20, 0, 700, 960)
        wf = bg.WF(P(1650, -22), X.p(-1, 0), X.p(0, -1))
        wf.text(b_sign["amber"], "UNION STATION", 0, 4, 560, 44, thick=4.0)
        x, y = P(1650, -14)
        rbox(m, "StationClock", x, y, 830, 250, 250, 14, roll=90, mat=clock_face, solid=False, mesh=m.cylinder)
        rbox(m, "StationClockRing", x, y - (14 if s > 0 else -14), 830, 285, 285, 14, roll=90, mat=steel, solid=False, mesh=m.cylinder)
    for (c, w, h) in BASE_DOORS_S:                                            # door jambs
        fr.rect(fm_b, c - w / 2 - 22, c - w / 2, -4, 90, 0, h + 20)
        fr.rect(fm_b, c + w / 2, c + w / 2 + 22, -4, 90, 0, h + 20)
        fr.rect(fm_b, c - w / 2 - 22, c + w / 2 + 22, -4, 90, h, h + 24)
    for (a, b) in bg.rect_gaps(T, BW - T, [(c, w + 60) for c, w, h in BASE_DOORS_S]):
        if b - a > 360:
            fr.rect(b_winwarm, a + 70, b - 70, -4, -1, 70, 330)
            fr.rect(fm_b, a + 56, a + 70, -6, 0, 60, 342)
            fr.rect(fm_b, b - 70, b - 56, -6, 0, 60, 342)
            fr.rect(fm_b, a + 56, b - 56, -6, 0, 330, 346)
            fr.rect(fm_b, a + 56, b - 56, -6, 0, 56, 70)
    for (c, w, h) in BASE_DOORS_E:
        fr2.rect(fm_b, c - w / 2 - 22, c - w / 2, BW - 90, BW + 4, 0, h + 20)
        fr2.rect(fm_b, c + w / 2, c + w / 2 + 22, BW - 90, BW + 4, 0, h + 20)
    # ---- inside: pilasters, banners, floor ring, vault door or departures board
    for v in range(500, 3000, 600):
        fr2.rect(fm_b, v - 25, v + 25, 90, 124, 0, H - 8)
    for u in range(600, 3000, 600):
        fr.rect(fm_b, u - 25, u + 25, BW - 124, BW - 90, 0, H - 8)
    ban = B("Banner%d" % s, pa_red if s > 0 else pa_blue, max_dist=14000.0)
    for u in (1000.0, 2300.0):
        fr.rect(ban, u - 70, u + 70, BW - 100, BW - 92, 470, 840)
        fr.rect(gold, u - 78, u + 78, BW - 102, BW - 90, 835, 845)
    fx, fy = P(*FLAG_UV)
    rbox(m, "FlagRing%d" % s, fx, fy, 16, 420, 420, 4, mat=team_ring[s], solid=False, mesh=m.cylinder)
    if bank:
        vx, vy = P(1650, BW - T - 22)
        rbox(m, "VaultRing", vx, vy, 190, 400, 400, 36, roll=90, mat=steel_dark, solid=False, mesh=m.cylinder)
        rbox(m, "VaultDoor", vx, vy + (-14 if s > 0 else 14), 190, 320, 320, 40, roll=90, mat=steel, solid=False, mesh=m.cylinder)
        rbox(m, "VaultHub", vx, vy + (-34 if s > 0 else 34), 190, 90, 90, 30, roll=90, mat=gold_m, solid=False, mesh=m.cylinder)
        for k in range(3):
            a = k * math.pi / 3
            ex, ey = P(1650 + math.cos(a) * 80, BW - T - 22)
            bar(m, "VaultSpoke", (ex, vy + (-52 if s > 0 else 52), 190 + math.sin(a) * 80), (P(1650 - math.cos(a) * 80, 0)[0], vy + (-52 if s > 0 else 52), 190 - math.sin(a) * 80), 8,
                mat=gold_m, solid=False)
        for (u0, u1) in ((780.0, 1330.0), (1970.0, 2520.0)):
            for ci in range(8):
                for ri in range(6):
                    uu = u0 + 30 + ci * (u1 - u0 - 60) / 7.0
                    fr.rect(gold, uu - 24, uu + 24, BW - 112, BW - 90, 40 + ri * 52, 40 + ri * 52 + 44)
    else:
        fr.rect(b_riser, 1000, 2300, BW - 100, BW - 90, 110, 345)
        wf = bg.WF(P(1650, BW - T - 14), X.p(-1, 0), X.p(0, -1))
        wf.text(b_sign["amber"], "DEPARTURES", 0, 2, 300, 36, thick=3.0)
        for k, line in enumerate(("1  NORTH EXPRESS  ON TIME", "2  RED LINE  DELAYED", "3  HARBOUR  ON TIME")):
            wf2 = bg.WF(P(1650, BW - T - 14), X.p(-1, 0), X.p(0, -1))
            wf2.text(b_sign["cyan" if k != 1 else "red"], line, 0, 2, 245 - k * 44, 22, thick=2.5)
    # ---- skylight glass: gable lantern (bank) / barrel vault (station)
    if bank:
        for (vo, vr) in ((900.0, 1700.0), (2500.0, 1700.0)):
            fr.prism(b_glass, 700, 2600, [(vo, 1090), (vr, 1440), (vr, 1446), (vo, 1096)])
            for a in range(700, 2601, 380):
                fr.prism(b_steeld, a - 6, a + 6, [(vo, 1090), (vr, 1440), (vr, 1456), (vo, 1106)])
        fr.prism(b_glass, 700, 706, [(900, 1090), (2500, 1090), (1700, 1440)])
        fr.prism(b_glass, 2594, 2600, [(900, 1090), (2500, 1090), (1700, 1440)])
        fr.rect(b_steeld, 700, 2600, 1690, 1710, 1436, 1462)
    else:
        Rr = (800.0 ** 2 + 520.0 ** 2) / (2 * 520.0)
        zc = 1090.0 + 520.0 - Rr
        th = math.asin(800.0 / Rr)
        nseg = 8
        pts = [(1700.0 + Rr * math.sin(-th + 2 * th * k / nseg), zc + Rr * math.cos(-th + 2 * th * k / nseg)) for k in range(nseg + 1)]
        pin = [(1700.0 + (Rr - 14) * math.sin(-th + 2 * th * k / nseg), zc + (Rr - 14) * math.cos(-th + 2 * th * k / nseg)) for k in range(nseg + 1)]
        for k in range(nseg):
            quad = [pts[k], pts[k + 1], pin[k + 1], pin[k]]
            for a in range(700, 2601, 380):
                fr.prism(b_steeld, a - 7, a + 7, quad)
            mid = [(pts[k][0], pts[k][1] - 4), (pts[k + 1][0], pts[k + 1][1] - 4), (pts[k + 1][0], pts[k + 1][1] - 9), (pts[k][0], pts[k][1] - 9)]
            fr.prism(b_glass, 700, 2600, mid)
    # ---- chandeliers (lit rings with a light each)
    for (u, v) in ((1650.0, 450.0), (400.0, 2000.0), (2900.0, 1700.0), (1650.0, 2800.0)):
        x, y = P(u, v)
        b_steeld.cyl(x, y, 700, H - 8, 4, sides=6)
        b_tubew.cyl(x, y, 690, 700, 90, sides=16)
        b_tubew.cyl(x, y, 700, 708, 55, sides=14)
        gold.cyl(x, y, 684, 690, 96, sides=16)
        light("Chandelier", (x, y, 620), (1.0, 0.82, 0.58), 90.0, 1100.0)
    # ---- roof: cover units, vents, antennas
    for (u, v) in ((1000.0, 450.0), (2300.0, 450.0)):
        x, y = P(u, v)
        unit(x, y, Z2, 260, 190, 150, yaw=X.yaw(0.0))
    for (u, v) in ((200.0, 3200.0), (3100.0, 3200.0), (3200.0, 2600.0), (200.0, 1000.0)):
        x, y = P(u, v)
        vent(x, y, Z2)
    x, y = P(2000.0, 2900.0)
    antenna(x, y, Z2, 600.0)
    x, y = P(2900.0, 450.0)
    tank(x, y, Z2, 120, 260)


if DRESS:
    base_dress(1, "bank")
    base_dress(-1, "station")


# ---- J. the city around: distant blocks with lit windows (no collision), low towards the sunset in the west
def skyline():
    r_ = random.Random(77)
    kinds = [("Brick", "BrickRed", (130, 90, 76), (150, 190)), ("Conc", "ConcreteDirty", (128, 124, 116), (200, 200)),
             ("Cream", "PlasterGrey", (184, 176, 158), (160, 190)), ("Tower", "ConcreteWorn", (112, 118, 130), (240, 240)),
             ("Sand", "SandstoneBlocks", (190, 170, 138), (150, 200)), ("Glass", "ConcreteClean", (150, 160, 170), (260, 250))]
    mats = [kc.facade("DtSky%s" % t, wall=w, albedo=a, grid_z=0.0, ground_z=0.0, cell=(300.0, 320.0), win=wn, sill=60.0, lit=0.32, glow=0.6,
                      lit_rows=0.3, seed=30 + i, min_z=-100000.0, dirt=0.3, glass_rgb=(0.04, 0.06, 0.09), frame_rgb=FRAME_GREY)
            for i, (t, w, a, wn) in enumerate(kinds)]
    cap = B("SkyCap", concrete_dark, max_dist=40000.0)
    n = [0]

    def blk(x, y, w, d, h):
        n[0] += 1
        k = r_.randrange(len(mats))
        box("Sky%d" % n[0], x - w / 2, y - d / 2, x + w / 2, y + d / 2, -400.0, h, mats[k], solid=False)
        cap.rect(x - w / 2 - 15, y - d / 2 - 15, x + w / 2 + 15, y + d / 2 + 15, h, h + 40)
        if h > 3000 and n[0] % 3 == 0:
            b_steel.box(x, y, h + 250, 8, 8, 500)
            b_beacon.box(x, y, h + 510, 26, 26, 26)
    x = -9800.0
    while x < 9800.0:
        w = r_.uniform(800, 1300)
        blk(x, 5400 + r_.uniform(0, 500), w, r_.uniform(900, 1400), r_.uniform(1800, 4200))
        blk(x + r_.uniform(-200, 200), -5400 - r_.uniform(0, 500), w, r_.uniform(900, 1400), r_.uniform(1800, 4200))
        if abs(x) > 3000 or True:
            blk(x, 8200 + r_.uniform(0, 900), r_.uniform(1000, 1500), r_.uniform(1000, 1500), r_.uniform(4200, 8200))
            blk(x + 300, -8200 - r_.uniform(0, 900), r_.uniform(1000, 1500), r_.uniform(1000, 1500), r_.uniform(4200, 8200))
        x += w + r_.uniform(80, 260)
    y = -4800.0
    while y < 4800.0:
        d = r_.uniform(800, 1300)
        blk(7400 + r_.uniform(0, 400), y, r_.uniform(900, 1400), d, r_.uniform(1800, 4600))
        blk(10200 + r_.uniform(0, 900), y + 200, r_.uniform(1000, 1500), d, r_.uniform(4600, 8600))
        # west: low-rise warehouses so that the low sun is visible over the end of the avenue
        blk(-7400 - r_.uniform(0, 400), y, r_.uniform(900, 1400), d, r_.uniform(500, 1100) if abs(y) < 3600 else r_.uniform(1800, 3200))
        blk(-10400 - r_.uniform(0, 900), y + 150, r_.uniform(1000, 1500), d, r_.uniform(900, 1500) if abs(y) < 3600 else r_.uniform(3000, 5200))
        y += d + r_.uniform(80, 240)
    for yy in (-7500.0, 7500.0):                                           # far towers beyond the sun sector in the west
        blk(-15000.0, yy, 1500.0, 1500.0, 4600.0)
        blk(-15500.0, yy * 1.2, 1700.0, 1500.0, 5600.0)


if DRESS:
    skyline()

# @@DRESSING5@@

# ================================================================================================== BUILD THE BATCHES
bt.flush()
unreal.log("DT actors so far: %d" % m.box_count)


# ================================================================================================== PLAYER STARTS
def all_starts():
    return [a for a in m.actor_lib.get_all_level_actors() if isinstance(a, unreal.PlayerStart)]


def pick(label, count, xr, yr, levels, seed, tag=None, step=120.0, min_sep=500.0):
    """Chooses starts automatically (standing room, hidden from each other), tags and renames them. Returns [(x, y, z, yaw)]."""
    before = set(a.get_actor_label() for a in all_starts())
    m.auto_starts(count, xr, yr, levels, step=step, seed=seed, min_sep=min_sep, face=(0.0, 0.0))
    out = []
    k = 0
    for a in all_starts():
        lab = a.get_actor_label()
        if lab in before or lab.startswith("Start_"):
            continue
        loc = a.get_actor_location()
        yaw = a.get_actor_rotation().yaw
        a.set_actor_label("Start_%s_%d" % (label, k))
        if tag:
            a.set_editor_property("player_start_tag", tag)
        out.append((loc.x, loc.y, loc.z - 110.0, yaw))
        k += 1
    return out


def mirror_starts(label, pts, tag=None):
    """The same starts rotated 180 degrees about the map centre."""
    for k, (x, y, z, yaw) in enumerate(pts):
        a = m.spawn(unreal.PlayerStart, "Start_%s_%d" % (label, k), (-x, -y, z + 110.0), (0, 0, yaw + 180.0))
        if tag:
            a.set_editor_property("player_start_tag", tag)
        m.start_count += 1


def all_labels():
    return set(a.get_actor_label() for a in all_starts())


red = []
red += pick("RedHall", 5, (-5880.0, -2820.0), (990.0, 4110.0), [0.0, 340.0], seed=3, tag="Red")
red += pick("RedCourt", 2, (-5300.0, -3400.0), (-3550.0, -1850.0), [0.0], seed=5, tag="Red")
red += pick("RedSide", 2, (-2650.0, -1850.0), (1000.0, 4100.0), [0.0], seed=12, tag="Red")
unreal.log("DT red starts: %d" % len(red))
mirror_starts("Blue", red, tag="Blue")

mid = []
mid += pick("MidNorth", 3, (-1700.0, 1700.0), (2000.0, 3500.0), [0.0], seed=6)
mid += pick("MidAve", 2, (-1700.0, 1700.0), (-420.0, 420.0), [TUN], seed=7)
mid += pick("MidCourt", 2, (3400.0, 5300.0), (1850.0, 3550.0), [0.0], seed=9)
mirror_starts("MidS", mid[3:])                          # the tunnel and courtyard starts are mirrored, the two yards differ
mid += pick("MidSite", 3, (-1700.0, 1700.0), (-3500.0, -2000.0), [0.0], seed=16, min_sep=450.0)
m.check_starts()

# ---- how well can each flag be seen from outside? (line traces from street points at eye height)
for s_, (fx_, fy_) in BASE_FLAG.items():
    seen, total, far_seen = 0, 0, 0
    for x_ in range(-6000, 6001, 300):
        for y_ in (-800, -450, 0, 450, 800, 1500, 2300, 3100, 3900, -1500, -2300, -3100, -3900):
            if math.hypot(x_ - fx_, y_ - fy_) < 150 or (abs(x_) > 2700 and abs(y_) > 900 and (x_ * s_ < 0) and (y_ * s_ > 0)):
                continue                                          # inside the base itself
            if (abs(x_) > 2700 and abs(y_) > 900) or (abs(x_) < 1800 and abs(y_) > 1800):
                continue                                          # inside some other building
            hit, _ = m._trace((x_, y_, 170.0), (fx_, fy_, 150.0))
            total += 1
            if not hit:
                seen += 1
                if math.hypot(x_ - fx_, y_ - fy_) > 2500:
                    far_seen += 1
    unreal.log("FLAG_EXPOSURE team %d: visible from %d of %d street points (%d from more than 25 m)" % (s_, seen, total, far_seen))

# @@APPEND@@
# ================================================================================================== LIGHT AND FINISH
m.look("dusk", sun_yaw=8.0, sun_lux=8.0, sky_intensity=9.0, ambient_gain=0.1266, ev=0.5, fog_density=0.0007, fog_max_opacity=0.45)
unreal.log("DT actors: %d" % m.box_count)
m.finish(kill_z=-1200)
