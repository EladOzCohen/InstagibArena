"""DM-Skyline: five rooftops of a city block at dusk, joined by steel bridges. Fall off and you die.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_skyline.py" -unattended -nullrhi -nosplash

Gameplay layout (unchanged since the first version): five roofs (Center 600, North/South 450, East 800, West 300), bridges
as ramps between them, 8 PlayerStarts, kill_z -800.  Everything below is looks only:
  * the buildings reach down to a street 17 m under the lowest roof (non-solid ground, so bots never see it as floor)
  * facades use M_IAFacade (wall texture + window grid in the shader), string courses, pilasters, drain pipes, fire escapes
  * roofs are tarmac / gravel / concrete with coping curbs, stairwells, chimneys, chillers, tanks, vents
  * the gaps show other buildings: a ring of big non-solid blocks (low ones show their roofs, tall ones are the skyline)
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
import kc_parts as kp
from mapkit_c import rbox, cyl, bar
from matlib import surface

m = mapkit.MapBuilder("/Game/Maps/DM-Skyline")
GROUND = -1700.0            # the street, far below the kill zone (kill_z -800)
FLOOR = 330.0

# ------------------------------------------------------------------------------------------------ materials
def S(name, tag, **kw):
    return surface(name, tag=tag, **kw)

tarmac = S("RoofTarmac", "SkyTarmac", albedo=(106, 104, 101))
tarmac_dirty = S("RoofTarmac", "SkyTarmacDirty", albedo=(92, 90, 87), dirt=0.2)
gravel = S("Gravel", "SkyGravelRoof", albedo=(124, 118, 108), tiling=2.6)           # coarser pebbles: reads as gravel, not carpet
gravel_pale = S("Gravel", "SkyGravelPale", albedo=(150, 144, 134), tiling=1.9)
wear_dark = S("RoofTarmac", "SkyWearDark", albedo=(62, 61, 60))
wear_pale = S("ConcreteDirty", "SkyDust", albedo=(132, 128, 120), tiling=2.0)
wear_seam = S("RoofTarmac", "SkySeam", albedo=(42, 42, 44))
roof_conc = S("ConcreteClean", "SkyRoofConc", albedo=(148, 146, 140), tiling=2.5)    # smooth slabs (ConcretePanels read like clapboard)
conc_dirty = surface("ConcreteDirty")
coping = S("ConcreteClean", "SkyCoping", albedo=(150, 147, 140))
band = S("ConcreteClean", "SkyBand", albedo=(165, 160, 150))
steel = surface("BrushedMetal", albedo=(92, 95, 102), tag="SteelLit", metal=0.22, rb=0.12, ns=0.4)   # less metallic: no black shapes without reflections
galv = surface("CorrugatedGalv")
rust = surface("RustOrange")
diamond = S("DiamondPlateDark", "SkyDeck", tiling=1.0)
wood_tank = surface("WoodPlanksDark")
plaster = surface("PlasterWeathered")
brick = surface("BrickRed")
door_grey = surface("WoodPaintedGrey")
door_green = S("WoodPaintedGrey", "SkyDoorGreen", albedo=(58, 84, 70))
rubber = kp.car_rubber_mat()
car_glass = kp.car_glass_mat()
car_red, car_blue, car_grey, car_white, car_green = (kp.car_paint("Red", (120, 24, 28)), kp.car_paint("Blue", (28, 56, 112)),
                                                     kp.car_paint("Grey", (112, 114, 118)), kp.car_paint("White", (196, 196, 190)),
                                                     kp.car_paint("Green", (36, 78, 62)))
asphalt = surface("Asphalt", tiling=3.0)
apron = surface("Sidewalk")
paint_line = S("ConcreteClean", "SkyLine", albedo=(190, 184, 160))
sign_panel = S("PlasterGrey", "SkyBoard", albedo=(34, 48, 70))
sign_letter = S("ConcreteClean", "SkyLetters", albedo=(214, 206, 180))

# window grid parameters per building: all facades share the same floor height (330) and the grid origin = roof level - 60
def fmat(tag, wall, top, **kw):
    kw.setdefault("lit", 0.08)
    kw.setdefault("glow", 0.35)
    return kc.facade("Sky" + tag, wall=wall, grid_z=top - 60.0, ground_z=GROUND, min_z=GROUND + 400.0, **kw)

# (name, cx, cy, size_x, size_y, top_z, facade, roof surface)
ROOFS = [
    ("Center", 0, 0, 1500, 1500, 600, fmat("Center", "BrickRed", 600, seed=1, albedo=(138, 88, 72)), tarmac),
    ("North", 0, 2100, 1700, 1400, 450, fmat("North", "BrickBrown", 450, seed=2, albedo=(112, 82, 68), win=(130, 200), cell=(260, 330)), gravel),
    ("South", 0, -2100, 1700, 1400, 450, fmat("South", "PlasterSand", 450, seed=3, win=(150, 200)), roof_conc),
    ("East", 2300, 0, 1300, 1500, 800, fmat("East", "ConcreteDirty", 800, seed=4, win=(200, 210), cell=(300, 330),
                                            albedo=(132, 130, 124), glass_rgb=(0.04, 0.05, 0.07)), tarmac_dirty),
    ("West", -2300, 0, 1300, 1500, 300, fmat("West", "PlasterWeathered", 300, seed=5, win=(140, 190), cell=(280, 330)),
     conc_dirty),
]

# bridges: (p0, p1, width) as in the original layout
W = 420.0
BRIDGES = []
for x in (-450, 450):
    BRIDGES.append(((x, 750, 600), (x, 1400, 450), W))
    BRIDGES.append(((x, -750, 600), (x, -1400, 450), W))
BRIDGES += [((750, 0, 600), (1650, 0, 800), W), ((-750, 0, 600), (-1650, 0, 300), W),
            ((800, 1700, 450), (1900, 700, 800), 380), ((800, -1700, 450), (1900, -700, 800), 380),
            ((-800, 1700, 450), (-1900, 700, 300), 380), ((-800, -1700, 450), (-1900, -700, 300), 380)]
BR2D = [((p0[0], p0[1]), (p1[0], p1[1]), w) for p0, p1, w in BRIDGES]

# ------------------------------------------------------------------------------------------------ the street far below
m.box("StreetGround", 0, 0, GROUND - 50, 40000, 40000, 100, mat=asphalt, solid=False)
for name, cx, cy, sx, sy, top, fm, rm in ROOFS:
    m.box("Apron_" + name, cx, cy, GROUND + 7, sx + 280, sy + 280, 14, mat=apron, solid=False)
for k, x in enumerate(range(-700, 701, 220)):                    # dashed lines in the four canyons
    m.box("Line_N%d" % k, x, 1075, GROUND + 1.5, 110, 14, 3, mat=paint_line, solid=False)
    m.box("Line_S%d" % k, x, -1075, GROUND + 1.5, 110, 14, 3, mat=paint_line, solid=False)
for k, y in enumerate(range(-700, 701, 220)):
    m.box("Line_E%d" % k, 1200, y, GROUND + 1.5, 14, 110, 3, mat=paint_line, solid=False)
    m.box("Line_W%d" % k, -1200, y, GROUND + 1.5, 14, 110, 3, mat=paint_line, solid=False)
kp.car(m, "StreetCar1", -330, 1030, GROUND + 14, 3, car_red, car_glass, rubber, "sedan", solid=False)
kp.car(m, "StreetCar2", 430, 1120, GROUND + 14, 182, car_grey, car_glass, rubber, "hatch", solid=False)
kp.car(m, "StreetCar3", 150, -1030, GROUND + 14, 0, car_white, car_glass, rubber, "van", solid=False)
kp.car(m, "StreetCar4", 1160, -380, GROUND + 14, 92, car_blue, car_glass, rubber, "sedan", solid=False)
kp.car(m, "StreetCar5", 1250, 420, GROUND + 14, 268, car_green, car_glass, rubber, "hatch", solid=False)
kp.car(m, "StreetCar6", -1180, 60, GROUND + 14, 90, car_grey, car_glass, rubber, "sedan", solid=False)
for i, (x, y, yaw) in enumerate([(-600, 835, 0), (560, 1315, 180), (-560, -835, 0), (640, -1315, 180), (980, 400, 90),
                                 (1420, -500, 270), (-980, -300, 90), (-1420, 480, 270)]):
    m.prop("StreetLamp%d" % i, "lamp_street_a", x, y, GROUND + 14, yaw=yaw, solid=False)
    m.accent_light("StreetLampLight%d" % i, (x, y, GROUND + 380), (1.0, 0.72, 0.42), candela=900, radius=900)

# ------------------------------------------------------------------------------------------------ the five buildings
def building(name, cx, cy, sx, sy, top, fm, roof_mat):
    h = top - GROUND
    m.box("Body_" + name, cx, cy, GROUND + (h - 60) / 2, sx, sy, h - 60, mat=fm)
    m.box("Cornice_" + name, cx, cy, top - 40, sx + 30, sy + 30, 40, mat=band)
    m.box("RoofSlab_" + name, cx, cy, top - 10, sx + 20, sy + 20, 20, mat=roof_mat)
    # string courses on all four faces, pilasters on the corners, drain pipes
    for k in range(1, 5):
        z = top - 60 - FLOOR * k
        m.box("BandN_%s_%d" % (name, k), cx, cy + sy / 2 + 7, z, sx + 28, 14, 28, mat=band, solid=False)
        m.box("BandS_%s_%d" % (name, k), cx, cy - sy / 2 - 7, z, sx + 28, 14, 28, mat=band, solid=False)
        m.box("BandE_%s_%d" % (name, k), cx + sx / 2 + 7, cy, z, 14, sy + 28, 28, mat=band, solid=False)
        m.box("BandW_%s_%d" % (name, k), cx - sx / 2 - 7, cy, z, 14, sy + 28, 28, mat=band, solid=False)
    for ix in (-1, 1):
        for iy in (-1, 1):
            m.box("Pilaster_%s" % name, cx + ix * sx / 2, cy + iy * sy / 2, GROUND + (h - 60) / 2, 44, 44, h - 60,
                  mat=band, solid=False)
    for i, (dx, dy, face) in enumerate([(-0.31, 0.5, "N"), (0.33, 0.5, "N"), (-0.3, -0.5, "S"), (0.31, -0.5, "S"),
                                        (0.5, -0.27, "E"), (-0.5, 0.29, "W")]):
        px, py = cx + dx * sx + (dx if abs(dx) == 0.5 else 0) * 24, cy + dy * sy + (dy if abs(dy) == 0.5 else 0) * 24
        cyl(m, "Drain_%s_%d" % (name, i), (px, py, top - 50), (px, py, top - 1500), 14, mat=steel, solid=False)


for name, cx, cy, sx, sy, top, fm, rm in ROOFS:
    building(name, cx, cy, sx, sy, top, fm, rm)
    gaps = kp.bridge_gaps((cx, cy, sx, sy), BR2D)
    kp.curb(m, "Curb_" + name, cx, cy, sx, sy, top, 36, 22, coping, gaps=gaps, solid=True)

# ------------------------------------------------------------------------------------------------ bridges
for i, (p0, p1, w) in enumerate(BRIDGES):
    m.slope("Bridge_%d" % i, p0, p1, w, mat=diamond)
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    run = math.hypot(dx, dy)
    ux, uy = dx / run, dy / run
    nx, ny = -uy, ux
    for side in (-1, 1):
        ox, oy = nx * side * (w / 2 - 6), ny * side * (w / 2 - 6)
        a = (p0[0] + ox, p0[1] + oy, p0[2] + 95)
        c = (p1[0] + ox, p1[1] + oy, p1[2] + 95)
        bar(m, "BridgeRail%d" % i, a, c, 6, mat=steel, solid=False, depth=6)
        a2 = (a[0], a[1], a[2] - 45)
        c2 = (c[0], c[1], c[2] - 45)
        bar(m, "BridgeRailMid%d" % i, a2, c2, 4, mat=steel, solid=False, depth=4)
        for t in (0.0, 0.17, 0.34, 0.5, 0.67, 0.84, 1.0):
            px, py, pz = p0[0] + dx * t + ox, p0[1] + dy * t + oy, p0[2] + dz * t
            rbox(m, "BridgePost%d" % i, px, py, pz + 48, 8, 8, 96, mat=steel, solid=False)
        # I-beams under the deck and cross braces
        bar(m, "BridgeBeam%d" % i, (p0[0] + ox, p0[1] + oy, p0[2] - 62), (p1[0] + ox, p1[1] + oy, p1[2] - 62), 36,
            mat=rust, solid=False, depth=22)
    for t in (0.15, 0.4, 0.65, 0.9):
        px, py, pz = p0[0] + dx * t, p0[1] + dy * t, p0[2] + dz * t
        yaw = math.degrees(math.atan2(dy, dx))
        rbox(m, "BridgeBrace%d" % i, px, py, pz - 62, 16, w - 40, 22, yaw=yaw, mat=rust, solid=False)

# ------------------------------------------------------------------------------------------------ roofs: cover and dressing
# (the cover positions use the same random numbers as the original blockout)
roof_by = {r[0]: r for r in ROOFS}
tank_count = 0
for i, (name, cx, cy, sx, sy, top, fm, rm) in enumerate(ROOFS):
    rng = random.Random(100 + i)
    for k in range(3):
        x = cx + rng.uniform(-450, 450)
        y = cy + rng.uniform(-450, 450)
        yaw = rng.uniform(0, 90)
        kp.chiller(m, "Chiller_%s_%d" % (name, k), x, y, top, 260, 200, 150 if k != 1 else 120, yaw, galv, steel, galv)
    tx = cx + rng.uniform(-350, 350)
    ty = cy + rng.uniform(-350, 350)
    kp.water_tank(m, "Tank_" + name, tx, ty, top, 300, 420, wood_tank, steel, conc_dirty)

    # a stairwell bulkhead in one corner (and a chimney in another)
    corner = {"Center": (1, -1), "North": (-1, 1), "South": (1, -1), "East": (1, 1), "West": (-1, -1)}[name]
    sw_w, sw_d = (230, 190) if name == "Center" else (300, 240)
    sxp = cx + corner[0] * (sx / 2 - sw_w / 2 - 70)
    syp = cy + corner[1] * (sy / 2 - sw_d / 2 - 70)
    base = (sxp, syp, top, 0)
    rbox(m, "Stair_" + name, sxp, syp, top + 130, sw_w, sw_d, 260, mat=plaster)
    rbox(m, "StairCap_" + name, sxp, syp, top + 268, sw_w + 30, sw_d + 30, 16, mat=band, solid=False)
    inward = (-corner[0], -corner[1])
    # door on the face toward the roof's middle (along x), vents on the other
    dxs = sxp + inward[0] * (sw_w / 2 + 2)
    rbox(m, "StairDoor_" + name, dxs, syp, top + 105, 4, 100, 210, mat=door_grey, solid=False)
    rbox(m, "StairDoorFrame_" + name, dxs + inward[0] * 1, syp, top + 218, 6, 124, 14, mat=steel, solid=False)
    rbox(m, "StairLamp_" + name, dxs + inward[0] * 8, syp + 70, top + 215, 10, 16, 16, mat=band, solid=False)
    # antenna mast and dish on the stairwell roof
    rbox(m, "Mast_" + name, sxp - corner[0] * 70, syp - corner[1] * 50, top + 268 + 180, 6, 6, 360, mat=steel, solid=False)
    for hz in (120, 220, 300):
        rbox(m, "MastArm_" + name, sxp - corner[0] * 70, syp - corner[1] * 50, top + 268 + hz, 90 - hz * 0.1, 4, 4,
             mat=steel, solid=False)
    rbox(m, "Dish_" + name, sxp + corner[0] * 60, syp + corner[1] * 40, top + 268 + 38, 60, 60, 5, pitch=50, yaw=45,
         mat=band, solid=False, mesh=m.cylinder)
    # chimney in the opposite corner of the roof
    chx = cx - corner[0] * (sx / 2 - 140)
    chy = cy - corner[1] * (sy / 2 - 140)
    rbox(m, "Chimney_" + name, chx, chy, top + 150, 110, 110, 300, mat=brick)
    rbox(m, "ChimneyCap_" + name, chx, chy, top + 306, 136, 136, 14, mat=band, solid=False)
    rbox(m, "ChimneyFlue_" + name, chx, chy, top + 335, 40, 40, 50, mat=steel, solid=False, mesh=m.cylinder)

    # roof hatch, vents, ducts and pipes (non-solid clutter) plus a repair patch and walkway slabs
    hx = cx + rng.uniform(-150, 150)
    hy = cy + rng.uniform(300, 520) * (1 if corner[1] < 0 else -1)
    rbox(m, "Hatch_" + name, hx, hy, top + 14, 110, 90, 28, mat=galv, solid=False)
    rbox(m, "HatchLid_" + name, hx, hy, top + 29, 120, 100, 4, mat=steel, solid=False)
    px_, py_ = cx + rng.uniform(-400, 400), cy + rng.uniform(-400, 400)
    m.box("Patch_" + name, px_, py_, top + 1.2, rng.uniform(300, 500), rng.uniform(200, 380), 2.4,
          yaw=rng.uniform(0, 90), mat=tarmac if rm is not tarmac else tarmac_dirty, solid=False)
    m.box("Walk_" + name, (sxp + cx) / 2, (syp + cy) / 2, top + 1.8, 120, abs(syp - cy) * 0.9 + 60, 3.6, mat=roof_conc,
          solid=False)
    for k in range(6):
        vx = cx + rng.uniform(-sx / 2 + 120, sx / 2 - 120)
        vy = cy + rng.uniform(-sy / 2 + 120, sy / 2 - 120)
        if abs(vx - sxp) < 220 and abs(vy - syp) < 200:
            continue
        which = rng.choice(["pipe_b", "pipe_a", "duct_b", "utility_box_a", "barrel_plastic", "pipe_c"])
        m.prop("Clutter_%s_%d" % (name, k), which, vx, vy, top, yaw=rng.uniform(0, 360), solid=False)

    # roof wear (own random numbers: the cover above must not move): dark tar patches, pale dust, tar seams, a few puddle-free stains
    r4 = random.Random(900 + i)
    for k in range(5):
        m.box("Wear_%s_%d" % (name, k), cx + r4.uniform(-sx * 0.42, sx * 0.42), cy + r4.uniform(-sy * 0.42, sy * 0.42), top + 0.5 + 0.1 * k,
              r4.uniform(110, 300), r4.uniform(90, 220), 1.0 + 0.2 * k, yaw=r4.uniform(0, 180), mat=wear_dark if k % 3 != 2 else wear_pale,
              solid=False)
    if rm in (tarmac, tarmac_dirty):
        for k in range(-int(sx // 220), int(sx // 220) + 1):                 # seams between the bitumen sheets
            m.box("Seam_%s_%d" % (name, k), cx + k * 110.0, cy, top + 0.8, 3.5, sy - 90, 1.6, mat=wear_seam, solid=False)
    elif rm is gravel:
        for k in range(-3, 4):                                               # raked bands in the gravel ballast
            m.box("Rake_%s_%d" % (name, k), cx + k * 210.0 + r4.uniform(-20, 20), cy, top + 0.7, 70, sy - 140, 1.2, yaw=r4.uniform(-1.5, 1.5),
                  mat=gravel_pale, solid=False)

# fire escapes and window units on the walls that face the other buildings (decor only, no collision)
for name, face, off, k in [("Center", "N", -150, 1), ("Center", "E", 200, 1), ("North", "S", -150, 1),
                           ("South", "N", 150, 1), ("East", "W", 150, 1), ("West", "E", -150, 1)]:
    _, cx, cy, sx, sy, top, fm, rm = roof_by[name]
    zb = top - 60 - FLOOR * 4
    if face in "NS":
        sgn = 1 if face == "N" else -1
        m.prop("FireEscape_%s%s" % (name, face), "fire_escape_a", cx + off, cy + sgn * (sy / 2 + 80), zb,
               yaw=0 if sgn > 0 else 180, solid=False)
    else:
        sgn = 1 if face == "E" else -1
        m.prop("FireEscape_%s%s" % (name, face), "fire_escape_a", cx + sgn * (sx / 2 + 80), cy + off, zb,
               yaw=90 if sgn > 0 else 270, solid=False)
rng = random.Random(55)
for name, cx, cy, sx, sy, top, fm, rm in ROOFS:
    for k in range(5):
        face = rng.choice("NSEW")
        row = rng.randint(1, 4)
        zb = top - 60 - FLOOR * row + 85
        idx = rng.randint(-2, 2)
        if face in "NS":
            sgn = 1 if face == "N" else -1
            m.prop("WinAC_%s_%d" % (name, k), "aircon_a", cx + 150 + 300 * idx, cy + sgn * (sy / 2 + 20), zb,
                   yaw=0 if sgn > 0 else 180, solid=False)
        else:
            sgn = 1 if face == "E" else -1
            m.prop("WinAC_%s_%d" % (name, k), "aircon_a", cx + sgn * (sx / 2 + 20), cy + 150 + 300 * idx, zb,
                   yaw=90 if sgn > 0 else 270, solid=False)

# ------------------------------------------------------------------------------------------------ billboard on the centre roof
# (a solid post keeps the line-of-sight break of the original; the board is a painted sheet on a steel frame)
rbox(m, "BillboardPost", 0, 0, 600 + 200, 80, 80, 400, mat=steel)
rbox(m, "BillboardPost2", 260, 0, 600 + 130, 50, 50, 260, mat=steel, solid=False)
rbox(m, "BillboardPost3", -260, 0, 600 + 130, 50, 50, 260, mat=steel, solid=False)
rbox(m, "Billboard", 0, -26, 600 + 395, 700, 24, 220, mat=sign_panel, solid=False)
rbox(m, "BillboardFrameT", 0, -26, 600 + 512, 716, 34, 14, mat=steel, solid=False)
rbox(m, "BillboardFrameB", 0, -26, 600 + 278, 716, 34, 14, mat=steel, solid=False)
rbox(m, "BillboardFrameL", -352, -26, 600 + 395, 14, 34, 240, mat=steel, solid=False)
rbox(m, "BillboardFrameR", 352, -26, 600 + 395, 14, 34, 240, mat=steel, solid=False)
rbox(m, "BillboardCatwalk", 0, -50, 600 + 266, 720, 60, 6, mat=diamond, solid=False)
kc.neon_text(m, "BillboardText", "SKYLINE", 0, -42, 600 + 400, 0, 120, sign_letter, thick=12, yaw=0, spacing=0.5)
for sx_ in (-300, -100, 100, 300):                                  # floodlights on the top rail
    rbox(m, "BillFlood", sx_, -70, 600 + 530, 30, 30, 20, mat=steel, solid=False)

# ------------------------------------------------------------------------------------------------ the city around (no collision)
def backdrop_facade(i, rng, top):
    kinds = [("BrickRed", (136, 90, 74), (150, 200), (300, 330), 100, (0.03, 0.04, 0.06)),
             ("BrickBrown", None, (130, 200), (260, 330), 100, (0.03, 0.04, 0.06)),
             ("PlasterWeathered", None, (140, 200), (280, 330), 100, (0.03, 0.04, 0.06)),
             ("PlasterGrey", (176, 172, 160), (200, 210), (300, 330), 90, (0.04, 0.05, 0.07)),
             ("ConcreteClean", (150, 148, 142), (150, 290), (150, 330), 20, (0.05, 0.07, 0.10)),
             ("ConcreteDirty", (120, 118, 112), (160, 200), (300, 330), 100, (0.03, 0.04, 0.06)),
             ("SandstoneBlocks", (180, 160, 130), (150, 200), (300, 330), 100, (0.03, 0.04, 0.06)),
             ("ConcreteWorn", (110, 112, 116), (140, 300), (160, 330), 15, (0.06, 0.08, 0.12))]
    return kinds[i % len(kinds)]


bd_mats = {}
def bd_facade(kind_i, tall):
    key = (kind_i, tall)
    if key not in bd_mats:
        wall, alb, win, cell, sill, glass_rgb = backdrop_facade(kind_i, None, 0)
        bd_mats[key] = kc.facade("SkyBD%d%s" % (kind_i, "T" if tall else "L"), wall=wall, albedo=alb, grid_z=GROUND,
                                 ground_z=GROUND, min_z=GROUND + 400.0, win=win, cell=cell, sill=sill,
                                 lit=0.2 if tall else 0.1, glow=0.4, glass_rgb=glass_rgb, seed=10 + kind_i,
                                 dirt=0.5, lit_rows=0.4 if (tall and kind_i in (1, 4, 7)) else 0.0)
    return bd_mats[key]


SKY_BEACON = kc.emit("SkyBeacon", (1.0, 0.06, 0.04), 2.2)               # aviation light: a tiny red glow
SKY_CLOCK = kc.emit("SkyClock", (1.0, 0.80, 0.52), 0.30)                  # lit clock face
copper = S("RoofSlate", "SkyCopper", albedo=(70, 116, 104), desat=0.4)    # patina roofs of the old towers
stone_tower = S("SandstoneBlocks", "SkyTowerStone", albedo=(170, 152, 126))
gravel_city = S("Gravel", "SkyGravelCity", albedo=(122, 118, 110), tiling=3.0)
fm_twin = kc.facade("SkyLandTwin", wall="ConcreteWorn", albedo=(112, 116, 124), grid_z=GROUND, ground_z=GROUND, min_z=GROUND + 400.0,
                    win=(240, 250), cell=(300, 330), sill=40, lit=0.16, lit_rows=0.45, glow=0.42, glass_rgb=(0.05, 0.07, 0.10), seed=41)
fm_deco = kc.facade("SkyLandDeco", wall="SandstoneBlocks", albedo=(176, 160, 134), grid_z=GROUND, ground_z=GROUND, min_z=GROUND + 400.0,
                    win=(130, 220), cell=(260, 330), sill=70, lit=0.14, lit_rows=0.3, glow=0.42, seed=42)


def far_tank(label, x, y, z, r):
    """A small wooden water tank on four legs (distant roofs): 7 pieces."""
    d, hgt = r.uniform(220, 300), r.uniform(260, 340)
    for lx in (-1, 1):
        for ly in (-1, 1):
            rbox(m, label + "_leg", x + lx * d * 0.36, y + ly * d * 0.36, z + 65, 12, 12, 130, mat=steel, solid=False)
    rbox(m, label + "_body", x, y, z + 130 + hgt / 2, d, d, hgt, mat=wood_tank, solid=False, mesh=m.cylinder)
    rbox(m, label + "_hoop", x, y, z + 130 + hgt * 0.5, d + 8, d + 8, 8, mat=steel, solid=False, mesh=m.cylinder)
    m.cone(label + "_lid", x, y, z + 130 + hgt, z + 130 + hgt + d * 0.4, d * 1.06, mat=steel, solid=False)


def beacon(label, x, y, z):
    rbox(m, label, x, y, z, 26, 26, 26, mat=SKY_BEACON, solid=False)


def lattice_tower(tag, x, y, z0, h, base_r, levels=6):
    """A triangular steel lattice tower (legs, rings and diagonal braces made of bars) with red lights."""
    top_r = 24.0
    legs = [(math.cos(2 * math.pi * k / 3 + 0.35), math.sin(2 * math.pi * k / 3 + 0.35)) for k in range(3)]
    for lv in range(levels):
        t0, t1 = lv / float(levels), (lv + 1) / float(levels)
        r0, r1 = base_r + (top_r - base_r) * t0, base_r + (top_r - base_r) * t1
        za, zb = z0 + h * t0, z0 + h * t1
        thick = 16.0 * (1 - t0) + 5.0
        for k, (cx_, cy_) in enumerate(legs):
            nx_, ny_ = legs[(k + 1) % 3]
            bar(m, "Lat_%s" % tag, (x + cx_ * r0, y + cy_ * r0, za), (x + cx_ * r1, y + cy_ * r1, zb), thick, mat=steel, solid=False)
            bar(m, "LatRing_%s" % tag, (x + cx_ * r1, y + cy_ * r1, zb), (x + nx_ * r1, y + ny_ * r1, zb), thick * 0.5, mat=steel,
                solid=False)
            bar(m, "LatBrace_%s" % tag, (x + cx_ * r0, y + cy_ * r0, za), (x + nx_ * r1, y + ny_ * r1, zb), thick * 0.4, mat=steel,
                solid=False)
    rbox(m, "LatMast_%s" % tag, x, y, z0 + h + 200, 14, 14, 400, mat=steel, solid=False)
    for hz in (0.45, 0.8, 1.0):
        beacon("LatBeacon_%s" % tag, x + 30, y, z0 + h * hz + (400 if hz == 1.0 else 0))


_pyr = {}


def pyramid(label, x, y, z, w, d, h, mat):
    """A four sided pyramid roof (generated mesh, unit size 100 x 100 x 100 scaled)."""
    import mapkit_b
    import mesh_b
    if "sm" not in _pyr:
        mm = mesh_b.Mesh()
        pts = [(-50, -50, 0), (50, -50, 0), (50, 50, 0), (-50, 50, 0), (0, 0, 100)]
        mm.convex(pts, [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], center=(0, 0, 25))
        _pyr["sm"] = mapkit_b.commit("SkyPyramid", mm, collision="none")
    mapkit_b.put(m, label, _pyr["sm"], x, y, z, scale=(w / 100.0, d / 100.0, h / 100.0), mat=mat, solid=False)


def tower_block(tag, bx, by, wx, wy, z_top, fmat, roof_mat):
    h = z_top - GROUND
    m.box("LM_%s" % tag, bx, by, GROUND + h / 2 - 10, wx, wy, h - 20, mat=fmat, solid=False)
    m.box("LMCornice_%s" % tag, bx, by, z_top - 45, wx + 30, wy + 30, 36, mat=band, solid=False)
    m.box("LMRoof_%s" % tag, bx, by, z_top - 10, wx + 20, wy + 20, 20, mat=roof_mat, solid=False)


def landmark(kind, tag, bx, by, wx, wy, fm, r3):
    """A recognisable silhouette in the distance: clock tower, art deco stepped tower, twin glass towers, radio mast."""
    if kind == "clock":
        top = GROUND + FLOOR * 13
        tower_block(tag + "a", bx, by, wx, wy, top, fm, tarmac_dirty)
        tw, th = 560.0, 1500.0
        m.box("ClockShaft", bx, by, top + th / 2 - 10, tw, tw, th, mat=stone_tower, solid=False)
        for k in range(4):
            m.box("ClockBand%d" % k, bx, by, top + 300 + k * 330, tw + 30, tw + 30, 28, mat=band, solid=False)
        ztop = top + th
        m.box("ClockCornice", bx, by, ztop - 25, tw + 70, tw + 70, 40, mat=band, solid=False)
        m.box("ClockBelfry", bx, by, ztop + 150, tw - 70, tw - 70, 300, mat=stone_tower, solid=False)
        for sg in (-1, 1):                                                   # four lit clock faces
            for ax in ("x", "y"):
                px, py = (bx + sg * (tw - 70) / 2, by) if ax == "x" else (bx, by + sg * (tw - 70) / 2)
                rbox(m, "ClockFace", px + sg * 2 * (ax == "x"), py + sg * 2 * (ax == "y"), ztop + 160, 250, 250, 8, mat=SKY_CLOCK,
                     solid=False, mesh=m.cylinder, pitch=90 if ax == "x" else 0, roll=0 if ax == "x" else 90)
                rbox(m, "ClockRing", px + sg * 1 * (ax == "x"), py + sg * 1 * (ax == "y"), ztop + 160, 280, 280, 9, mat=steel,
                     solid=False, mesh=m.cylinder, pitch=90 if ax == "x" else 0, roll=0 if ax == "x" else 90)
                if ax == "x":
                    bar(m, "ClockHand", (px + sg * 8, py, ztop + 160), (px + sg * 8, py + 20, ztop + 255), 8, mat=pa_dark, solid=False)
                    bar(m, "ClockHand2", (px + sg * 8, py, ztop + 160), (px + sg * 8, py - 70, ztop + 130), 6, mat=pa_dark, solid=False)
                else:
                    bar(m, "ClockHand", (px, py + sg * 8, ztop + 160), (px + 20, py + sg * 8, ztop + 255), 8, mat=pa_dark, solid=False)
                    bar(m, "ClockHand2", (px, py + sg * 8, ztop + 160), (px - 70, py + sg * 8, ztop + 130), 6, mat=pa_dark, solid=False)
        pyramid("ClockRoof", bx, by, ztop + 290, tw + 40, tw + 40, 820, copper)
        rbox(m, "ClockFinial", bx, by, ztop + 290 + 820 + 70, 14, 14, 160, mat=steel, solid=False)
        beacon("ClockBeacon", bx, by, ztop + 290 + 820 + 160)
    elif kind == "deco":
        top = GROUND + FLOOR * 15
        tower_block(tag + "a", bx, by, wx, wy, top, fm_deco, tarmac_dirty)
        z = top
        for k, (kw, fl) in enumerate([(0.82, 4), (0.62, 4), (0.44, 3), (0.28, 3)]):
            hh = FLOOR * fl
            tower_block("%sb%d" % (tag, k), bx, by, wx * kw, wy * kw, z + hh, fm_deco, tarmac_dirty)
            for ix in (-1, 1):                                               # vertical fins at the corners of each tier
                for iy in (-1, 1):
                    rbox(m, "DecoFin", bx + ix * wx * kw * 0.5, by + iy * wy * kw * 0.5, z + hh / 2, 26, 26, hh, mat=band, solid=False)
            z += hh
        m.cone("DecoSpire", bx, by, z, z + 1600, wx * 0.16, mat=copper, solid=False)
        rbox(m, "DecoSpireBand", bx, by, z + 330, wx * 0.2, wx * 0.2, 30, mat=band, solid=False, mesh=m.cylinder)
        beacon("DecoBeacon", bx, by, z + 1612)
        for ix, iy in ((-1, -1), (1, 1)):
            beacon("DecoCornerLight", bx + ix * wx * 0.1, by + iy * wy * 0.1, z + 18)
    elif kind == "twin":
        for k, (ox, fl) in enumerate([(-0.27, 27), (0.27, 22)]):
            z_top = GROUND + FLOOR * fl
            tw_ = wx * 0.42
            tower_block("%sa%d" % (tag, k), bx + ox * wx * 1.2, by, tw_, wy * 0.8, z_top, fm_twin, tarmac_dirty)
            m.box("TwinCrown%d" % k, bx + ox * wx * 1.2, by, z_top + 120, tw_ * 0.7, wy * 0.56, 240, mat=band, solid=False)
            for ix_, iy_ in ((-1, -1), (1, 1)):
                beacon("TwinLight%d" % k, bx + ox * wx * 1.2 + ix_ * tw_ * 0.4, by + iy_ * wy * 0.3, z_top + 14)
            rbox(m, "TwinMast%d" % k, bx + ox * wx * 1.2, by, z_top + 240 + 250, 12, 12, 500, mat=steel, solid=False)
            beacon("TwinMastLight%d" % k, bx + ox * wx * 1.2, by, z_top + 760)
        m.box("TwinSkyBridge", bx, by, GROUND + FLOOR * 16 + 150, wx * 0.5, 160, 300, mat=fm_twin, solid=False)
    elif kind == "radio":
        top = GROUND + FLOOR * 6
        tower_block(tag + "a", bx, by, wx * 0.8, wy * 0.8, top, fm, gravel_city)
        rbox(m, "RadioHut", bx + 250, by - 200, top + 130, 300, 240, 260, mat=plaster, solid=False)
        lattice_tower(tag, bx, by, top, 2600, 260)


def pa_dark_mat():
    return S("ConcreteClean", "SkyDark", albedo=(26, 26, 28))


pa_dark = pa_dark_mat()
LANDMARKS = {(-3, 3): "clock", (3, -3): "deco", (-4, -3): "radio", (3, 4): "twin"}

arena_rects = [(r[1], r[2], r[3] + 500, r[4] + 500) for r in ROOFS]
bridge_segs = [(p0[:2], p1[:2]) for p0, p1, w in BRIDGES]


def near_bridge(x, y, margin):
    for (a, b_) in bridge_segs:
        ax, ay, bx, by = a[0], a[1], b_[0], b_[1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        if math.hypot(x - (ax + dx * t), y - (ay + dy * t)) < margin:
            return True
    return False


rng = random.Random(77)
count = 0
PITCH = 2000.0
for gi in range(-5, 6):
    for gj in range(-5, 6):
        bx = gi * PITCH + rng.uniform(-120, 120)
        by = gj * PITCH + rng.uniform(-120, 120)
        wx, wy = rng.uniform(1150, 1500), rng.uniform(1150, 1500)
        if any(abs(bx - r[0]) < (wx + r[2]) / 2 + 60 and abs(by - r[1]) < (wy + r[3]) / 2 + 60 for r in arena_rects):
            continue
        if near_bridge(bx, by, 800):
            continue
        r_ = math.hypot(bx, by)
        if r_ > 11500:
            continue
        if r_ < 6200:
            n_floors = rng.choice([4, 5, 6, 7, 8, 9, 10, 12])
        else:
            n_floors = rng.randint(9, 24)
        top = GROUND + FLOOR * n_floors
        tall = top > 1200
        kind_i = rng.randrange(8)
        fm = bd_facade(kind_i, tall)
        h = top - GROUND
        tag = "%d_%d" % (gi, gj)
        # the random draws below are the same as in the first version, so the block layout does not move
        roof_kind = tarmac_dirty if kind_i % 2 else gravel_city
        stair_p = (rng.uniform(-300, 300), rng.uniform(-300, 300)) if top < 1100 else None
        ac_p = (rng.uniform(-400, 400), rng.uniform(-400, 400)) if top < 1100 else None
        chim_p = (rng.uniform(-400, 400), rng.uniform(-400, 400)) if top < 1100 else None
        mast_p = None
        if top >= 1100 and rng.random() < 0.6:
            mast_p = (rng.uniform(-300, 300), rng.uniform(-300, 300))
        r3 = random.Random(5000 + gi * 37 + gj * 11)              # decoration only (extra random numbers)
        if (gi, gj) in LANDMARKS:
            landmark(LANDMARKS[(gi, gj)], tag, bx, by, wx, wy, fm, r3)
            count += 1
            continue
        m.box("City_" + tag, bx, by, GROUND + h / 2 - 10, wx, wy, h - 20, mat=fm, solid=False)
        m.box("CityRoof_" + tag, bx, by, top - 10, wx + 40, wy + 40, 20, mat=roof_kind, solid=False)
        m.box("CityCornice_" + tag, bx, by, top - 45, wx + 30, wy + 30, 36, mat=band, solid=False)
        count += 1
        ztop = top
        if tall and n_floors >= 11 and r3.random() < 0.5:           # setback: a narrower upper tier with its own cornice
            tw, td = wx * r3.uniform(0.55, 0.75), wy * r3.uniform(0.55, 0.75)
            tx, ty = bx + r3.uniform(-0.15, 0.15) * wx, by + r3.uniform(-0.15, 0.15) * wy
            th = FLOOR * r3.randint(2, 5)
            m.box("CityTier_" + tag, tx, ty, top + th / 2 - 10, tw, td, th, mat=fm, solid=False)
            m.box("CityTierCornice_" + tag, tx, ty, top + th - 35, tw + 24, td + 24, 30, mat=band, solid=False)
            m.box("CityTierRoof_" + tag, tx, ty, top + th - 8, tw + 10, td + 10, 14, mat=tarmac_dirty, solid=False)
            ztop = top + th
            bx2, by2, wx2, wy2 = tx, ty, tw, td
        else:
            bx2, by2, wx2, wy2 = bx, by, wx, wy
        if top < 1100:                                              # low blocks show their roof gear
            rbox(m, "CityStair_" + tag, bx + stair_p[0], by + stair_p[1], top + 130, 260, 220, 260, mat=plaster, solid=False)
            rbox(m, "CityStairCap_" + tag, bx + stair_p[0], by + stair_p[1], top + 266, 280, 240, 12, mat=band, solid=False)
            rbox(m, "CityAC_" + tag, bx + ac_p[0], by + ac_p[1], top + 80, 260, 200, 160, mat=galv, solid=False)
            rbox(m, "CityACfan_" + tag, bx + ac_p[0], by + ac_p[1], top + 166, 140, 140, 10, mat=steel, solid=False, mesh=m.cylinder)
            rbox(m, "CityChimney_" + tag, bx + chim_p[0], by + chim_p[1], top + 150, 110, 110, 300, mat=brick, solid=False)
            rbox(m, "CityChimneyCap_" + tag, bx + chim_p[0], by + chim_p[1], top + 306, 134, 134, 12, mat=band, solid=False)
            for k, nm in enumerate(r3.sample(["pipe_b", "duct_b", "utility_box_a", "barrel_plastic", "pipe_c", "aircon_a", "bin_a"], 3)):
                m.prop("CityGear_%s_%d" % (tag, k), nm, bx + r3.uniform(-wx * 0.38, wx * 0.38), by + r3.uniform(-wy * 0.38, wy * 0.38),
                       top, yaw=r3.uniform(0, 360), solid=False)
            if r3.random() < 0.3:
                far_tank("CityTank_" + tag, bx + r3.uniform(-wx * 0.3, wx * 0.3), by + r3.uniform(-wy * 0.3, wy * 0.3), top, r3)
            if r3.random() < 0.5:                                   # a vent stack with a hood
                vx, vy = bx + r3.uniform(-wx * 0.4, wx * 0.4), by + r3.uniform(-wy * 0.4, wy * 0.4)
                cyl(m, "CityVent_" + tag, (vx, vy, top), (vx, vy, top + 170), 34, mat=galv, solid=False)
                m.cone("CityVentHood_" + tag, vx, vy, top + 170, top + 215, 64, mat=steel, solid=False)
        elif mast_p is not None:                                    # tall blocks: a mast with cross arms and a red light
            mx_, my_ = bx2 + mast_p[0] * 0.5, by2 + mast_p[1] * 0.5
            mh = r3.uniform(500, 900)
            rbox(m, "CityMast_" + tag, mx_, my_, ztop + mh / 2, 10, 10, mh, mat=steel, solid=False)
            for hz in (0.55, 0.75, 0.9):
                rbox(m, "CityMastArm_" + tag, mx_, my_, ztop + mh * hz, 120 - 60 * hz, 5, 5, mat=steel, solid=False)
            rbox(m, "CityBeacon_" + tag, mx_, my_, ztop + mh + 14, 26, 26, 26, mat=SKY_BEACON, solid=False)
        if tall and mast_p is None and r3.random() < 0.4:           # a spire or a water tower instead
            sx2, sy2 = bx2 + r3.uniform(-0.2, 0.2) * wx2, by2 + r3.uniform(-0.2, 0.2) * wy2
            if r3.random() < 0.5:
                sh = r3.uniform(600, 1100)
                m.cone("CitySpire_" + tag, sx2, sy2, ztop, ztop + sh, min(wx2, wy2) * 0.3, mat=copper, solid=False)
                rbox(m, "CitySpireBeacon_" + tag, sx2, sy2, ztop + sh + 12, 26, 26, 26, mat=SKY_BEACON, solid=False)
            else:
                far_tank("CityTowerTank_" + tag, sx2, sy2, ztop, r3)
        elif tall and top > 2800 and r3.random() < 0.6:              # corner aviation lights on the tallest roofs
            for ix_, iy_ in ((-1, -1), (1, 1)):
                rbox(m, "CityCornerLight_" + tag, bx2 + ix_ * wx2 * 0.45, by2 + iy_ * wy2 * 0.45, ztop + 14, 24, 24, 24, mat=SKY_BEACON,
                     solid=False)
unreal.log("SKYLINE city blocks: %d" % count)

# ------------------------------------------------------------------------------------------------ spawns
starts = [(sx * 400.0, sy * 400.0, 600, math.degrees(math.atan2(-sy, -sx))) for sx in (-1, 1) for sy in (-1, 1)]
starts += [(0, 2300, 450, 270), (0, -2300, 450, 90), (2500, 0, 800, 180), (-2500, 0, 300, 0)]
m.starts(starts)

# ------------------------------------------------------------------------------------------------ light: low sun
m.look("dusk", sun_pitch=-22.0, sun_yaw=225.0, sun_lux=6.5, sun_rgb=(1.0, 0.76, 0.52), sky_intensity=9.0, ev=0.5, ambient_gain=0.1266, saturation=0.9, fog_max_opacity=0.4)
m.finish(kill_z=-800)
