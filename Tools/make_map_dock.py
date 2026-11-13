"""DM-Dock: a harbour transit shed. Same floor plan as the blockout (5600 x 2600 hall, two mezzanines with ramps, a
cross bridge, two big vertical tanks, stacked shipping containers), rebuilt as a believable place: brick and corrugated
cladding, clerestory windows that look out on the quay, a ship and cranes, a roof of steel trusses with skylights that
let the sun fall in patches on the floor, hanging lamps, hangar doors at both ends.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_dock.py" -unattended -nullrhi -nosplash
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import mapkit_a as ka  # noqa: E402
import props  # noqa: E402,F401
from matlib import surface, glass, water  # noqa: E402

MAP_PATH = "/Game/Maps/DM-Dock"
b = mapkit.MapBuilder(MAP_PATH)
rng = random.Random(23)

HX, HY, CEIL = 2800.0, 1300.0, 1300.0
MZ_TOP, MZ_T, MZ_W = 450.0, 40.0, 450.0

# ------------------------------------------------------------------------------------------------ materials
TAG = "Dk"
floor_mat = surface("ConcreteWorn", albedo=(150, 148, 142), tiling=3.0, tag=TAG + "Floor")
brick_low = surface("BrickDark", albedo=(116, 80, 66), dirt=0.5, dirt_h=260, tag=TAG + "Brick")
clad = surface("CorrugatedGalv", albedo=(150, 153, 156), tag=TAG + "Clad")
clad_dark = surface("CorrugatedDark", albedo=(96, 100, 106), tag=TAG + "CladD")
clad_rust = surface("CorrugatedRust")
ceil_mat = surface("CorrugatedDark", albedo=(104, 108, 114), tiling=2.0, tag=TAG + "Ceil")
steel = surface("SteelDark")
steel_paint = surface("SteelDark", albedo=(88, 94, 100), tag=TAG + "Paint")
steel_light = surface("BrushedMetal", albedo=(130, 133, 138), tag=TAG + "Light")
black_paint = surface("SteelDark", albedo=(34, 34, 36), tag="FdBlack")
yellow = surface("ContainerYellow")
plate = surface("DiamondPlate", albedo=(128, 126, 124), desat=1.0, macro=0.12, tiling=1.0, tag="FdPlate2")
plate_dark = surface("DiamondPlateDark", desat=1.0, macro=0.12, tiling=1.0, tag="FdPlateD")
trim = surface("ConcretePanels", albedo=(160, 156, 148), tiling=1.5, tag="FdTrim")
plinth_mat = surface("ConcreteDark")
concrete_big = surface("ConcretePanels", tiling=4.0, tag="FdBig")
tank_mat = surface("ContainerGrey")
white_paint = surface("PlasterWhite")
rust_orange = surface("RustCoarse", albedo=(96, 62, 46), tag=TAG + "Pipe")
oil = surface("Asphalt", albedo=(84, 83, 84), tag="DkOil")
joint = surface("ConcreteDark", albedo=(70, 70, 68), tag="FdJoint")
wood_old = surface("WoodPlanksOld")
wood_dark = surface("WoodPlanksDark")
c_red, c_blue = surface("ContainerRed"), surface("ContainerBlue")
c_green, c_yel, c_grey = surface("ContainerGreen"), surface("ContainerYellow"), surface("ContainerGrey")
yard = surface("Asphalt", tiling=6.0, tag=TAG + "Yard")
quay = surface("ConcreteDirty", tiling=4.0, tag=TAG + "Quay")
hull = surface("SteelDark", albedo=(40, 44, 52), tag=TAG + "Hull")
hull_red = surface("RustCoarse", albedo=(110, 40, 34), tag=TAG + "HullRed")
glass_mat = glass()
water_mat = water()
bulb = b.glow("MI_DockBulb", (1.0, 0.85, 0.6), 2.0)
beacon = b.glow("MI_DockBeacon", (1.0, 0.55, 0.1), 2.5)
green_led = b.glow("MI_DockGreen", (0.2, 1.0, 0.3), 2.0)
red_led = b.glow("MI_DockRed", (1.0, 0.15, 0.1), 2.0)

# ------------------------------------------------------------------------------------------------ floor
b.box("Floor", 0, 0, -50, HX * 2 + 200, HY * 2 + 200, 100, mat=floor_mat)
Z_JOINT, Z_PAVE, Z_STAIN, Z_PAINT = 1.2, 2.0, 2.4, 2.9
for k in range(-3, 4):
    b.box("JointY", k * 700.0, 0, Z_JOINT / 2, 4.0, HY * 2, Z_JOINT, mat=joint, solid=False)
for y in (-650, 0, 650):
    b.box("JointX", 0, y, Z_JOINT / 2, HX * 2, 4.0, Z_JOINT, mat=joint, solid=False)
for y in (-820, 820):                                         # painted mezzanine edge line
    b.box("EdgeLine", 0, y, Z_PAINT / 2, HX * 2, 14, Z_PAINT, mat=yellow, solid=False)
for y in (-520, 520):                                         # crane rails let into the floor
    b.box("CraneRail", 0, y, Z_PAVE / 2, HX * 2, 18, Z_PAVE, mat=steel, solid=False)
    b.box("CraneRailCap", 0, y, Z_PAINT / 2 + 0.2, HX * 2, 7, Z_PAINT, mat=steel_light, solid=False)
for sx in (-1, 1):
    x = sx * 1100
    for dx, dy, sxx, syy in ((0, 475, 970, 12), (0, -475, 970, 12), (485, 0, 12, 970), (-485, 0, 12, 970)):
        b.box("TankKeepClear", x + dx, dy, Z_PAINT / 2, sxx, syy, Z_PAINT, mat=yellow, solid=False)
for i in range(14):
    x, y = rng.uniform(-2600, 2600), rng.uniform(-1000, 1000)
    for j in range(3):
        ka.disc(b, "Stain", x + rng.uniform(-60, 60), y + rng.uniform(-60, 60), Z_STAIN, rng.uniform(40, 120),
                rng.uniform(30, 90), 0.6, oil, yaw=rng.uniform(0, 180))
for x, y in ((-2000, 0), (2000, 0), (0, -400), (0, 400)):      # floor drains
    b.box("Drain", x, y, 1.5, 60, 30, 3.0, mat=black_paint, solid=False)

# ------------------------------------------------------------------------------------------------ side walls (N, S)
BAY = 700.0
WIN_W, WIN_Z0, WIN_Z1 = 420.0, 880.0, 1180.0


def side_wall(name, origin, yaw):
    w = ka.Wall(b, origin, yaw)
    half = HX + 100
    L2 = half * 2
    n = "Wall_" + name
    w.box(n + "_Lower", 0, -50, -50, MZ_TOP, L2, 100, brick_low, solid=True)
    w.box(n + "_Mid", 0, -50, MZ_TOP, WIN_Z0, L2, 100, clad, solid=True)
    w.box(n + "_Top", 0, -50, WIN_Z1, CEIL + 50, L2, 100, clad_dark, solid=True)
    for k in range(-4, 5):                                       # piers between the windows
        u = k * BAY
        w.box(n + "_Pier", u, -50, WIN_Z0, WIN_Z1, 280.0, 100, clad, solid=True)
    for j in range(-4, 4):
        u = j * BAY + BAY / 2
        ka.window(w, "%s_Win%d" % (n, j), u, WIN_Z0, WIN_W, WIN_Z1 - WIN_Z0, steel_paint, trim, glass_mat, mullions=3,
                  sill_out=10.0)
    w.box(n + "_Plinth", 0, 7, 0, 90, L2, 14, plinth_mat)
    w.box(n + "_Band", 0, 5, MZ_TOP, MZ_TOP + 20, L2, 10, trim)
    w.box(n + "_Girt", 0, 6, WIN_Z0 - 40, WIN_Z0 - 22, L2, 12, steel_paint)
    w.box(n + "_Eaves", 0, 9, WIN_Z1 + 10, WIN_Z1 + 30, L2, 18, steel_paint)
    for k in range(-4, 5):                                       # steel stanchions with base plates
        u = k * BAY
        if abs(u) > HX - 50:
            continue
        w.box(n + "_Stanchion", u, 14, 0, CEIL - 20, 34, 28, steel_paint)
        w.box(n + "_StanFlange", u, 22, 0, CEIL - 20, 50, 8, steel_paint)
        w.box(n + "_StanBase", u, 14, 0, 12, 70, 44, steel)
    for gi, u in enumerate((-1400, 700)):                        # service doors under the mezzanine
        w.box(n + "_DoorFrameL", u - 105, 8, 0, 235, 20, 20, trim)
        w.box(n + "_DoorFrameR", u + 105, 8, 0, 235, 20, 20, trim)
        w.box(n + "_DoorHead", u, 8, 220, 245, 230, 20, trim)
        w.box(n + "_DoorLeaf", u, 3, 0, 225, 190, 8, clad_rust if gi == 0 else steel_paint)
        w.box(n + "_DoorStripe", u, 8, 0, 30, 190, 4, yellow)
        w.box(n + "_DoorLamp", u, 18, 252, 268, 40, 22, steel)
        w.box(n + "_DoorLed", u + 60, 6, 170, 180, 12, 3, green_led if gi == 0 else red_led)
    hl = 2500
    w.box(n + "_Tray", 0, 8, 380, 392, hl * 2, 16, steel)
    ka.pipe(b, n + "_Pipe", (*w.xy(-hl, 20), 300), (*w.xy(hl, 20), 300), 14, rust_orange)
    ka.pipe(b, n + "_Pipe2", (*w.xy(-hl, 20), 330), (*w.xy(hl, 20), 330), 10, steel_light)
    for u in range(-hl + 100, hl, 450):
        w.box(n + "_PipeBracket", u, 16, 292, 338, 8, 14, steel)
    return w


wN = side_wall("N", (0, HY), 180)
wS = side_wall("S", (0, -HY), 0)

# ------------------------------------------------------------------------------------------------ end walls with hangar doors
def end_wall(name, origin, yaw):
    w = ka.Wall(b, origin, yaw)
    half = HY
    n = "Wall_" + name
    w.box(n + "_Lower", 0, -50, -50, MZ_TOP, half * 2, 100, brick_low, solid=True)
    w.box(n + "_Upper", 0, -50, MZ_TOP, CEIL + 50, half * 2, 100, clad, solid=True)
    w.box(n + "_Plinth", 0, 7, 0, 90, half * 2, 14, plinth_mat)
    w.box(n + "_Band", 0, 5, MZ_TOP, MZ_TOP + 20, half * 2, 10, trim)
    # sliding hangar door: two leaves on a track, hazard edges, guide rail on the floor
    DH = 1020.0
    for side in (-1, 1):
        uc = side * 570
        w.box(n + "_Leaf", uc, 12, 0, DH, 1140, 22, clad_dark)
        w.box(n + "_LeafFrameT", uc, 20, DH - 30, DH, 1140, 10, steel_paint)
        w.box(n + "_LeafFrameB", uc, 20, 0, 40, 1140, 10, steel_paint)
        w.box(n + "_LeafFrameM", uc, 20, DH * 0.45, DH * 0.45 + 24, 1140, 8, steel_paint)
        w.box(n + "_LeafFrameO", uc + side * 560, 20, 0, DH, 20, 10, steel_paint)
        for k in (-1, 0, 1):
            w.box(n + "_LeafRib", uc + k * 380, 20, 40, DH - 30, 14, 8, steel_paint)
        w.box(n + "_Stripe", side * 22, 20, 0, DH, 44, 6, yellow)
        w.box(n + "_Wheel", uc - 300, 14, DH + 20, DH + 70, 50, 14, black_paint)
        w.box(n + "_Wheel", uc + 300, 14, DH + 20, DH + 70, 50, 14, black_paint)
    w.box(n + "_Track", 0, 26, DH + 55, DH + 105, 2400, 44, steel_paint)
    w.box(n + "_TrackTop", 0, 20, DH + 105, DH + 125, 2420, 18, steel)
    w.box(n + "_GuideRail", 0, 22, 0, 2.5, 2400, 12, steel_light)
    w.box(n + "_DoorHeader", 0, 6, DH + 125, DH + 180, 2500, 12, trim)
    for u in (-1210, 1210):
        w.box(n + "_Jamb", u, 12, 0, DH + 125, 70, 30, trim)
    for sgn in (-1, 1):                                          # bollards and a door lamp
        for u in (sgn * 300, sgn * 900):
            w.cyl(n + "_Bollard", u, 110, 0, 90, 22, yellow)
    w.box(n + "_Beacon", 0, 22, DH + 190, DH + 215, 26, 26, beacon)
    w.box(n + "_BeaconBase", 0, 22, DH + 180, DH + 190, 36, 36, steel)
    w.box(n + "_LedL", -1180, 8, 600, 610, 10, 3, green_led)
    w.box(n + "_LedR", 1180, 8, 600, 610, 10, 3, red_led)
    # a duct and a vent fan high on the wall
    w.box(n + "_Duct", 0, 36, 1180, 1250, 1900, 70, steel_light)
    for u in (-600, 0, 600):
        w.cyl(n + "_Fan", u, 6, 1180, 1182, 90, black_paint)
    return w


end_wall("E", (HX, 0), 90)
end_wall("W", (-HX, 0), 270)

# ------------------------------------------------------------------------------------------------ roof: ceiling with skylights, trusses
SKY_X = [-2100 + 700 * k for k in range(7)]
SKY_W, SKY_D = 500.0, 260.0
ceil_z0, ceil_z1 = CEIL, CEIL + 100
xmin, xmax = -HX - 100, HX + 100
for (y0, y1) in ((-HY - 100, -650.0), (-390.0, 390.0), (650.0, HY + 100)):
    b.box("Ceiling", (xmin + xmax) / 2, (y0 + y1) / 2, (ceil_z0 + ceil_z1) / 2, xmax - xmin, y1 - y0, 100, mat=ceil_mat)
for yc in (-520.0, 520.0):
    edges = [xmin] + [v for x in SKY_X for v in (x - SKY_W / 2, x + SKY_W / 2)] + [xmax]
    for i in range(0, len(edges), 2):
        xa, xb = edges[i], edges[i + 1]
        b.box("CeilingPiece", (xa + xb) / 2, yc, (ceil_z0 + ceil_z1) / 2, xb - xa, SKY_D, 100, mat=ceil_mat)
    for x in SKY_X:                                              # steel frames under the skylight openings
        for sgn in (-1, 1):
            b.box("SkyFrame", x, yc + sgn * (SKY_D / 2 + 8), CEIL - 8, SKY_W + 40, 16, 16, mat=steel_paint, solid=False)
            b.box("SkyFrame", x + sgn * (SKY_W / 2 + 8), yc, CEIL - 8, 16, SKY_D + 40, 16, mat=steel_paint, solid=False)
        b.box("SkyBar", x, yc, CEIL - 6, 8, SKY_D, 8, mat=steel_paint, solid=False)
TRUSS_X = [-2400 + 800 * k for k in range(7)]
for x in TRUSS_X:
    b.box("Truss_Bottom", x, 0, CEIL - 120, 16, HY * 2 - 10, 20, mat=steel_paint, solid=False)
    b.box("Truss_Top", x, 0, CEIL - 14, 20, HY * 2 - 10, 28, mat=steel_paint, solid=False)
    n = 8
    for i in range(n):
        y0 = -HY + 10 + i * (HY * 2 - 20) / n
        y1 = y0 + (HY * 2 - 20) / n
        if i % 2 == 0:
            ka.strut(b, "Truss_Diag", (x, y0, CEIL - 120), (x, y1, CEIL - 28), 8, steel_paint)
        else:
            ka.strut(b, "Truss_Diag", (x, y0, CEIL - 28), (x, y1, CEIL - 120), 8, steel_paint)
    for i in range(n + 1):
        y = -HY + 10 + i * (HY * 2 - 20) / n
        b.box("Truss_Post", x, y, CEIL - 74, 10, 10, 92, mat=steel_paint, solid=False)
for y in (-1000, 0, 1000):                                       # purlins and cable trays along the hall
    b.box("Purlin", 0, y, CEIL - 132, HX * 2, 18, 14, mat=steel_paint, solid=False)
ka.pipe(b, "AirDuct", (-2780, -250, 1120), (2780, -250, 1120), 90, steel_light)
ka.pipe(b, "AirDuct2", (-2780, 250, 1140), (2780, 250, 1140), 60, rust_orange)
for x in TRUSS_X:
    b.box("DuctHanger", x, -250, 1180, 6, 6, 100, mat=steel, solid=False)
    b.box("DuctHanger", x, 250, 1190, 6, 6, 100, mat=steel, solid=False)
for x in range(-2400, 2401, 800):                                # cable tray with cables
    b.box("TrayBracket", x, 0, 1100, 8, 100, 8, mat=steel, solid=False)
b.box("CableTray", 0, 0, 1090, HX * 2, 60, 8, mat=steel, solid=False)

# overhead bridge crane on runways along the long walls
RZ = 1060.0
for sy in (-1, 1):
    y = sy * (HY - 80)
    b.box("Runway", 0, y, RZ, HX * 2, 40, 60, mat=steel_paint, solid=False)
    b.box("RunwayRail", 0, y, RZ + 35, HX * 2, 14, 12, mat=black_paint, solid=False)
    for x in range(-2600, 2601, 650):
        b.box("RunwayBracket", x, y + sy * 25, RZ - 50, 8, 50, 120, mat=steel, solid=False)
CX = 600.0
b.box("CraneGirder", CX, 0, RZ + 90, 120, HY * 2 - 160, 90, mat=yellow, solid=False)
b.box("CraneWalk", CX + 70, 0, RZ + 40, 40, HY * 2 - 160, 6, mat=plate_dark, solid=False)
for sy in (-1, 1):
    b.box("CraneTruck", CX, sy * (HY - 80), RZ + 60, 200, 80, 60, mat=steel, solid=False)
b.box("CraneTrolley", CX, 200, RZ + 20, 110, 120, 50, mat=steel, solid=False)
ka.strut(b, "CraneRope", (CX - 20, 200, RZ), (CX - 20, 200, 700), 4, black_paint)
ka.strut(b, "CraneRope", (CX + 20, 200, RZ), (CX + 20, 200, 700), 4, black_paint)
b.box("CraneHook", CX, 200, 680, 40, 30, 40, mat=yellow, solid=False)
b.box("CraneHookBlock", CX, 200, 650, 14, 14, 30, mat=steel, solid=False)

# ------------------------------------------------------------------------------------------------ mezzanines
def mezzanine(name, origin, yaw):
    w = ka.Wall(b, origin, yaw)
    n = "Mezz_" + name
    # deck: the same slab as the blockout (u -1800..2400, 450 deep, top at 450)
    w.box(n + "_Deck", 300, MZ_W / 2, MZ_TOP - MZ_T, MZ_TOP, 4200, MZ_W, plate, solid=True)
    w.box(n + "_EdgeBeam", 300, MZ_W - 4, MZ_TOP - MZ_T - 28, MZ_TOP - MZ_T, 4200, 8, steel_paint)
    w.box(n + "_EdgeFlange", 300, MZ_W - 10, MZ_TOP - MZ_T - 32, MZ_TOP - MZ_T - 26, 4200, 24, steel_paint)
    w.box(n + "_WallBeam", 300, 10, MZ_TOP - MZ_T - 28, MZ_TOP - MZ_T, 4200, 14, steel_paint)
    for u in range(-1700, 2400, 300):
        w.box(n + "_Joist", u, MZ_W / 2, MZ_TOP - MZ_T - 26, MZ_TOP - MZ_T, 8, MZ_W - 20, steel_paint)
    for u in range(-1800, 2401, 600):                            # columns (same footprint as the blockout supports)
        w.box(n + "_Column", u, MZ_W / 2, 0, MZ_TOP - MZ_T + 2, 80, 80, steel_paint, solid=True)
        w.box(n + "_ColBase", u, MZ_W / 2, 0, 14, 130, 130, steel, solid=False)
        w.box(n + "_ColFlange", u, MZ_W / 2 + 44, 0, MZ_TOP - MZ_T, 90, 8, steel_paint)
        for sgn in (-1, 1):
            w.strut(n + "_Knee", (u, MZ_W / 2 + 40, 300), (u + sgn * 150, MZ_W / 2 + 40, MZ_TOP - MZ_T - 30), 8, steel_paint)
    for u in range(-1500, 2100, 1200):                           # X braces in every second bay
        w.strut(n + "_Brace", (u, MZ_W / 2 + 46, 20), (u + 600, MZ_W / 2 + 46, MZ_TOP - MZ_T - 30), 8, steel_paint)
        w.strut(n + "_Brace", (u, MZ_W / 2 + 46, MZ_TOP - MZ_T - 30), (u + 600, MZ_W / 2 + 46, 20), 8, steel_paint)
    # handrail on the hall side, broken for the bridge, closed at the far end
    for (u0, u1) in ((-1800, -200), (200, 2400)):
        a = (*w.xy(u0, MZ_W - 8), MZ_TOP)
        c = (*w.xy(u1, MZ_W - 8), MZ_TOP)
        ka.rail(b, n + "_Rail", a, c, yellow, post_every=240)
        w.box(n + "_Fascia", (u0 + u1) / 2, MZ_W + 2, MZ_TOP - MZ_T - 2, MZ_TOP + 14, u1 - u0, 5, yellow)
        w.box(n + "_EdgeLine", (u0 + u1) / 2, MZ_W - 12, MZ_TOP, MZ_TOP + 0.8, u1 - u0, 14, yellow)
    ka.rail(b, n + "_RailEnd", (*w.xy(2392, 8), MZ_TOP), (*w.xy(2392, MZ_W - 8), MZ_TOP), yellow, post_every=225)
    # ramp from the floor to the deck (same line as the blockout)
    p0 = (*w.xy(-2700, MZ_W / 2), 0.0)
    p1 = (*w.xy(-1800, MZ_W / 2), MZ_TOP)
    ka.ramp(b, n + "_Ramp", p0, p1, 400, plate, steel_paint, yellow)
    return w


mezzanine("S", (0, -HY), 0)
mezzanine("N", (0, HY), 180)

# cross bridge: the same deck as the blockout, with side girders, joists and rails
BR_L = HY * 2 - MZ_W * 2 + 20
b.box("Bridge", 0, 0, MZ_TOP - MZ_T / 2, 400, BR_L, MZ_T, mat=plate)
for sx in (-1, 1):
    x = sx * 190
    b.box("Bridge_Girder", x, 0, MZ_TOP - MZ_T - 38, 10, BR_L - 10, 76, mat=steel_paint, solid=False)
    b.box("Bridge_Flange", x, 0, MZ_TOP - MZ_T - 76, 30, BR_L - 10, 8, mat=steel_paint, solid=False)
    for i in range(8):
        y0 = -BR_L / 2 + 10 + i * (BR_L - 20) / 8
        y1 = y0 + (BR_L - 20) / 8
        ka.strut(b, "Bridge_Diag", (x, y0, MZ_TOP - MZ_T - 72) if i % 2 == 0 else (x, y0, MZ_TOP - MZ_T - 4),
                 (x, y1, MZ_TOP - MZ_T - 4) if i % 2 == 0 else (x, y1, MZ_TOP - MZ_T - 72), 6, steel_paint)
    ka.rail(b, "Bridge_Rail", (x, -BR_L / 2 + 10, MZ_TOP), (x, BR_L / 2 - 10, MZ_TOP), yellow, post_every=215)
for i in range(1, 8):
    b.box("Bridge_Joist", 0, -BR_L / 2 + i * BR_L / 8, MZ_TOP - MZ_T - 20, 380, 8, 40, mat=steel_paint, solid=False)

# ------------------------------------------------------------------------------------------------ the two tanks
for sx in (-1, 1):
    x = sx * 1100
    b.box("TankBase", x, 0, 50, 900, 900, 100, mat=concrete_big)
    b.box("TankBaseEdge", x, 0, 104, 920, 920, 8, mat=trim, solid=False)
    b.column("TankShaft", x, 0, 100, CEIL, 450, mat=tank_mat)
    ka.cyl(b, "TankFoot", x, 0, 100, 130, 520, 520, steel)
    z = 100 + 90
    while z < CEIL - 40:
        ka.cyl(b, "TankRing", x, 0, z - 7, z + 7, 468, 468, steel_paint)
        z += 180
    ka.cyl(b, "TankHead", x, 0, CEIL - 40, CEIL, 520, 520, steel_paint)
    ya = 232
    b.box("TankLadderL", x - 18, ya, 700, 4, 4, 1200, mat=steel, solid=False)
    b.box("TankLadderR", x + 18, ya, 700, 4, 4, 1200, mat=steel, solid=False)
    for z in range(130, 1280, 30):
        b.box("TankRung", x, ya, z, 40, 3, 3, mat=steel, solid=False)
    for z in range(300, 1250, 300):
        ka.cyl(b, "TankCage", x, ya - 12, z, z + 5, 70, 70, steel)
    for ang in (35, 150):                                        # pipes with flanges up to the roof
        px = x + 250 * math.cos(math.radians(ang))
        py = 250 * math.sin(math.radians(ang)) * 0.9
        b.column("TankPipe", px, py, 100, 1140, 34, mat=steel_light, solid=False)
        for z in (250, 650, 1000):
            b.column("TankPipeFlange", px, py, z, z + 10, 52, mat=steel, solid=False)
    ka.pipe(b, "TankPipeHoriz", (x + 250 * math.cos(math.radians(35)), 143, 1120), (x + 250 * math.cos(math.radians(35)), 1290, 1120), 34, steel_light)
    for dx, dy in ((-440, -440), (440, -440), (440, 440), (-440, 440)):
        b.column("Bollard", x + dx, dy, 100, 190, 22, mat=yellow, solid=False)
    ka.cyl(b, "ValveWheel", x - 250, -150, 190, 196, 60, 60, red_led if False else steel)
    b.box("TankPlate", x, -229, 700, 90, 3, 40, mat=white_paint, solid=False)

# ------------------------------------------------------------------------------------------------ cargo
CONT = [(-1800, 250, 0, c_red), (-1500, -350, 90, c_blue), (1600, -250, 0, c_green), (1900, 350, 90, c_yel),
        (450, 700, 0, c_blue), (-500, -650, 0, c_red), (-100, 650, 90, c_green), (700, -700, 90, c_grey)]
for i, (x, y, yaw, mat) in enumerate(CONT):
    ka.container(b, "Container_%d" % i, x, y, 0, yaw, mat, steel=steel_paint)
    if i % 2 == 0:
        top_mat = (c_yel, c_blue, c_red, c_grey)[(i // 2) % 4]
        ka.container(b, "ContainerTop_%d" % i, x + 60, y, 240, yaw, top_mat, length=480, steel=steel_paint, doors_at=-1)
        for sxx in (-1, 1):                                       # twist locks between the boxes
            b.box("Twistlock", x + 60 + sxx * 200, y, 240, 14, 14, 6, mat=black_paint, solid=False)

# ------------------------------------------------------------------------------------------------ spawn points
spawns = [(sx * 2400.0, sy * 500.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
spawns += [(sx * 1000.0, sy * 750.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
b.face_center_starts(spawns)
mz_y = HY - MZ_W / 2
b.starts([(-700, -mz_y, MZ_TOP, 90), (700, mz_y, MZ_TOP, 270)])

# ------------------------------------------------------------------------------------------------ props
def P(name, x, y, z=0.0, yaw=0.0, scale=1.0, solid=None):
    return b.prop("P_" + name, name, x, y, z, yaw=yaw, scale=scale, solid=solid)


def pallet_stack(label, x, y, yaw, n=2, loads=True):
    z = ka.pallet(b, label + "_P0", x, y, 0, yaw, wood_old)
    if loads:
        for k in range(n):
            b.box(label + "_Sack", x, y, z + 40 + k * 78, 112, 92, 76, yaw=yaw + rng.uniform(-4, 4), mat=surface("Canvas"), solid=False)
        b.box(label + "_Wrap", x, y, z + 40 + (n - 1) * 39, 118, 98, n * 78 + 4, yaw=yaw, mat=white_paint, solid=False) if False else None


# under the north mezzanine (y 850..1300, deck 410): drums, crates, pallets, a generator
for i, (dx, dy) in enumerate(((0, 0), (62, 12), (24, -62))):
    P("barrel_wood_a" if i != 1 else "barrel_wood_b", -2000 + dx, 1180 + dy, yaw=rng.uniform(0, 360))
P("generator", -1100, 1230, yaw=180, scale=1.5)
P("barrel_red", -600, 1230)
P("barrel_red", -540, 1240)
P("barrel_plastic", -480, 1225)
pallet_stack("PalN1", 150, 1180, 10)
pallet_stack("PalN2", 280, 1190, -5)
P("crate_wood_b", 1000, 1220, yaw=90, scale=1.3)
P("crate_wood_a", 1060, 1215, yaw=95, scale=1.3)
P("jerrycan", 1400, 1230, yaw=40, scale=1.2)
P("jerrycan", 1445, 1215, yaw=15, scale=1.2)
# under the south mezzanine
P("bin_a", -2200, -1230, scale=1.4)
for i in range(3):
    P("tyre", -1500, -1220, z=i * 16, yaw=rng.uniform(0, 60), scale=1.4)
P("generator", -300, -1230, yaw=0, scale=1.5)
pallet_stack("PalS1", 600, -1180, 20)
pallet_stack("PalS2", 720, -1195, 0, n=3)
for i in range(3):
    P("barrel_wood_b" if i else "barrel_wood_a", 1500 + (i % 2) * 70, -1190 + i * 40, yaw=rng.uniform(0, 360))
P("utility_box_a", 2200, -1260, yaw=0, scale=1.2)
# the ends: buoys and fenders next to the hangar doors, a few drums
P("buoy", -2600, 1050, yaw=40, scale=0.9)
P("buoy", 2600, -1050, yaw=120, scale=0.9)
P("barrel_red", 2640, 1100)
P("barrel_fire", 2600, 1160)
P("barrel_plastic", -2640, -1100)
# hanging lamps with a warm bulb and a light each
LAMPS = [(x, y) for x in TRUSS_X for y in (-110, 110)]
for i, (x, y) in enumerate(LAMPS):
    b.prop("P_lamp_hanging", "lamp_hanging", x, y, CEIL - 120 - 136, solid=False)
    b.box("LampChain", x, y, CEIL - 60, 4, 4, 100, mat=steel, solid=False)
    ka.cyl(b, "LampBulb", x, y, CEIL - 258, CEIL - 252, 34, 34, bulb)
    b.accent_light("Lamp_%d" % i, (x, y, CEIL - 280), (1.0, 0.86, 0.66), candela=140.0, radius=1100.0)
for sx in (-1, 1):                                                 # amber beacons over the hangar doors
    b.accent_light("DoorBeacon", (sx * (HX - 60), 0, 1150), (1.0, 0.6, 0.2), candela=50.0, radius=500.0)

# ------------------------------------------------------------------------------------------------ the harbour outside
def far_box(label, x, y, z0, z1, sx, sy, mat, yaw=0.0, shadow=False):
    a = b.box(label, x, y, (z0 + z1) / 2, sx, sy, z1 - z0, yaw=yaw, mat=mat, solid=False)
    ka.set_shadow(a, shadow)
    return a


def far_cyl(label, x, y, z0, z1, dia, mat):
    a = b.column(label, x, y, z0, z1, dia, mat=mat, solid=False)
    ka.set_shadow(a, False)
    return a


far_box("Ground", 0, -20550, -400, -10, 90000, 48900, yard, shadow=False)
far_box("Apron", 0, 2700, -400, -4, 26000, 2600, quay, shadow=True)              # the quay, y 1400..4000
far_box("QuayWall", 0, 3950, -600, -4, 26000, 100, plinth_mat)
far_box("Sea", 0, 22000, -420, -300, 90000, 36000, water_mat)
for x in range(-11000, 11001, 700):
    far_cyl("QuayBollard", x, 3850, -4, 70, 50, black_paint)
# the ship alongside (hull, deck, container blocks, superstructure)
far_box("ShipHull", -2000, 6000, -700, 1500, 26000, 3400, hull, shadow=True)
far_box("ShipWaterline", -2000, 6000, -400, -150, 26040, 3440, hull_red)
far_box("ShipBulwark", -2000, 6000, 1500, 1640, 26000, 3400, hull)
x0 = -13000
for i in range(8):
    cx = -11500 + i * 2300
    for layer in range(5):
        mats = (c_red, c_blue, c_green, c_yel, c_grey)
        far_box("ShipCont", cx + rng.uniform(-60, 60), 6000 + rng.uniform(-30, 30), 1640 + layer * 260,
                1640 + (layer + 1) * 260 - 6, 2000, 2900, mats[(i * 2 + layer * 3 + (i % 3)) % 5])
far_box("ShipSuper", 9600, 6000, 1500, 4600, 2600, 2800, white_paint)
far_box("ShipBridge", 9600, 6000, 4600, 5200, 1700, 3300, white_paint)
far_box("ShipBridgeWin", 8280, 6000, 4800, 5000, 20, 3200, glass_mat)
far_cyl("ShipFunnel", 10600, 6000, 4600, 6200, 600, c_red)
far_cyl("ShipMast", 9600, 6000, 5200, 7600, 60, steel)
# two ship-to-shore cranes on the quay
for cx in (-4200, 3600):
    for lx in (-650, 650):
        for ly in (3000, 3750):
            far_box("CraneLeg", cx + lx, ly, -4, 3900, 160, 160, c_red)
    far_box("CraneBeamA", cx, 3000, 3900, 4100, 1560, 160, c_red)
    far_box("CraneBeamB", cx, 3750, 3900, 4100, 1560, 160, c_red)
    far_box("CraneTie", cx - 650, 3375, 3900, 4100, 160, 900, c_red)
    far_box("CraneTie", cx + 650, 3375, 3900, 4100, 160, 900, c_red)
    far_box("CraneBoom", cx, 5800, 4100, 4260, 360, 9400, c_red)
    far_box("CraneBoomTop", cx, 5800, 4260, 4300, 220, 9400, steel_paint)
    far_box("CraneHouse", cx, 3000, 4100, 4800, 900, 700, steel_paint)
    for k in range(5):
        ka.strut(b, "CraneStay", (cx, 3000, 5400 if False else 4800), (cx, 3200 + k * 1500, 4260), 30, black_paint)
    far_box("CraneSpreader", cx, 6100, 3100, 3300, 280, 1200, black_paint)
# quay sheds and lamp masts
for sx, sw in ((-9000, 4000), (8200, 5000)):
    far_box("QuayShed", sx, 2500, -4, 1100, sw, 1000, clad)
    far_box("QuayShedRoof", sx, 2500, 1100, 1180, sw + 100, 1100, clad_dark)
for x in (-8000, -1000, 1000, 8000):
    far_cyl("LampMast", x, 2200, -4, 2800, 36, steel)
    far_box("LampHead", x, 2200, 2800, 2860, 220, 140, steel)
# south: container yard with rubber-tyred gantry cranes
for row, y in enumerate((-2800, -4600, -6400)):
    for i in range(8):
        cx = -7000 + i * 2000
        n = 3 + ((i + row) % 3)
        mats = (c_red, c_blue, c_green, c_yel, c_grey)
        for layer in range(n):
            far_box("YardCont", cx, y + rng.uniform(-40, 40), layer * 260, (layer + 1) * 260 - 4, 1800, 480 * 2 + 40,
                    mats[(i + layer * 2 + row) % 5])
for cx in (-3500, 3000):
    for lx in (-600, 600):
        for ly in (-3700, -5300):
            far_box("RtgLeg", cx + lx, ly, 0, 2300, 140, 140, yellow)
    far_box("RtgBeam", cx, -4500, 2300, 2480, 1500, 1800, yellow)
    far_box("RtgTrolley", cx, -4500, 2480, 2620, 300, 400, steel_paint)
for x in (-6000, 0, 6000):
    far_cyl("YardMast", x, -2000, 0, 3200, 40, steel)
    far_box("YardMastHead", x, -2000, 3200, 3280, 300, 160, steel)
# east and west of the shed: more yard and a pair of warehouses (seen over the ends when on the mezzanines)
far_box("WarehouseE", 7600, 0, -4, 1800, 3000, 5000, clad_dark, shadow=True)
far_box("WarehouseW", -7600, 0, -4, 1600, 3000, 5000, brick_low, shadow=True)

# ------------------------------------------------------------------------------------------------ light + finish
_over = {k: float(os.environ["IA_" + k.upper()]) for k in ("ev", "sky_intensity", "sun_lux") if os.environ.get("IA_" + k.upper())}
_look = dict(sun_yaw=35.0, sun_pitch=-52.0, sun_lux=9.0, sky_intensity=2.6, ev=0.5, sky_rgb=(1.0, 0.97, 0.92),
             saturation=0.93, fog_density=0.0008)
_look.update(_over)
b.look("day_clear", **_look)
b.finish(kill_z=-1500)
