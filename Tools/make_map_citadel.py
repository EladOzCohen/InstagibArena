"""DM-Citadel: two stone keeps on hills facing each other across a wide green valley with a river. Capture the Flag, FFA and TDM.

  Tools\\run_ue.ps1 -Script Tools\\make_map_citadel.py -Log Saved\\mk_citadel.log -Grep "MAKEMAP_DONE|Traceback|LogPython: Error"

Layout (x long axis, y north, z up, cm; playable area about 13600 x 7450):
  red keep on a plateau at x = -4900 (z = 700), blue keep at x = +4900; main gates face the valley, side gates lead north onto a causeway
  that joins the ridge (a long high walkway along the north edge, z = 700, with a viaduct over the river gorge) and south to the slopes;
  a river runs north -> south through the middle (x about 0); a ruined chapel / market village sits on both banks with a stone bridge;
  underneath the meadow a stone tunnel (z = -700) with four ramps to the surface; two jump pads up to the ridge, two across the river.
Everything is generated: terrain (Tools/terrain_big1.py), masonry and buildings (Tools/mesh_big1.py), matlib surfaces, catalogue props.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
from mapkit import MapBuilder  # noqa: E402
import props  # noqa: E402,F401
import mapkit_fx  # noqa: E402,F401
import mapkit_b as kb  # noqa: E402
import mapkit_big1 as k1  # noqa: E402
import mesh_b as mb  # noqa: E402
import mesh_big1 as mb1  # noqa: E402
import terrain_big1 as tb  # noqa: E402
import mesh_misc_b as mm  # noqa: E402
import mesh_arch_b as ma  # noqa: E402
import mesh_nat_n as nn  # noqa: E402
from matlib import surface, water  # noqa: E402

k1.register_surfaces()
m = MapBuilder("/Game/Maps/DM-Citadel")
rng = random.Random(1305)
T = tb.Terrain(seed=7)
G = T.height
PZ = tb.PZ
CAT = "Citadel_"

# ---------------------------------------------------------------- surfaces
grass_m = surface("CitGrass")
grass_dry_m = surface("CitGrassDry")
dirt_m = surface("CitMeadowDirt")
rock_m = surface("CitRock")
rock_dark_m = surface("CitRockDark")
bed_m = surface("CitBed")
trail_m = surface("CitTrail")
moss_m = surface("CitMoss")
water_m = water()
GROUND_MATS = [grass_m, dirt_m, rock_m, bed_m, rock_dark_m]
wall_red = surface("CitCastleWarm")
wall_blue = surface("CitCastleBlue")
wall_grey = surface("CitCastleGrey")
wall_dark = surface("CitCastleDark")
roof_red = surface("CitRoofRed")
roof_old = surface("CitRoofRedOld")
roof_slate = surface("RoofSlate")
lime_m = surface("Limestone", tiling=2.6)
cobble_m = surface("Cobblestone", tiling=2.2)
slabs_m = surface("StoneSlabs", tiling=3.0)
wood_m = surface("WoodPlanksDark", tiling=1.6)
wood_old = surface("WoodPlanksOld", tiling=1.6)
cloth_red = surface("CanvasRed", tiling=1.2)
cloth_blue = surface("CanvasBlue", tiling=1.2)
canvas_m = surface("Canvas", tiling=1.2)
far_m = surface("CitRockDark", tiling=40.0)

# ---------------------------------------------------------------- layout data used by terrain pads and holes
PORTAL_X = (-1500.0, 1500.0)
TUN_Y = -1900.0
TUN_Z = -620.0
TUN_X0, TUN_X1 = -1900.0, 1900.0
HOLES = []
for xc in PORTAL_X:
    T.add_pad(xc, -950.0, 400.0, 600.0, 0.0, blend=300.0)
    T.add_pad(xc, -2850.0, 400.0, 600.0, 0.0, blend=300.0)
    HOLES.append((xc - 250.0, -1300.0, xc + 250.0, -600.0))
    HOLES.append((xc - 250.0, -3200.0, xc + 250.0, -2500.0))

HOUSES = [  # name, x, y, yaw (door faces the river), w, d, h, enterable-start
    ("HW1", -1000.0, 950.0, 90.0, 560.0, 460.0, 300.0),
    ("HW2", -1050.0, 350.0, 90.0, 560.0, 460.0, 300.0),
    ("HW3", -950.0, -1550.0, 90.0, 600.0, 480.0, 300.0),
    ("HE1", 1050.0, 950.0, -90.0, 560.0, 460.0, 300.0),
    ("HE2", 1200.0, 350.0, -90.0, 560.0, 460.0, 300.0),
    ("HE3", 950.0, -1550.0, -90.0, 600.0, 480.0, 300.0),
]
for _n, hx, hy, _y, hw, hd, _h in HOUSES:
    T.add_pad(hx, hy, 340.0, 340.0, 0.0, blend=260.0)
CHAPEL = (-850.0, -700.0)
T.add_pad(CHAPEL[0], CHAPEL[1], 700.0, 420.0, 0.0, blend=300.0)
T.add_pad(900.0, -650.0, 400.0, 400.0, 0.0, blend=300.0)                       # market
T.add_pad(-650.0, 0.0, 500.0, 450.0, 0.0, blend=300.0)                          # bridge approaches
T.add_pad(1300.0, 0.0, 500.0, 450.0, 0.0, blend=300.0)
for sx in (-1, 1):
    T.add_pad(sx * 1100.0, 1450.0, 450.0, 300.0, 0.0, blend=300.0)              # foot of the ridge stairs
    T.add_pad(sx * 1800.0, 3050.0, 450.0, 450.0, PZ, blend=250.0)               # ridge huts
T.add_pad(-800.0, 3050.0, 300.0, 450.0, PZ, blend=200.0)                       # viaduct ends
T.add_pad(1000.0, 3050.0, 300.0, 450.0, PZ, blend=200.0)

# ---------------------------------------------------------------- the ground: 16 tiles with four material slots
TILE_X = [-8000.0, -4000.0, 0.0, 4000.0, 8000.0]
TILE_Y = [-5400.0, -2700.0, 0.0, 2700.0, 5400.0]
CELL = 100.0


def build_ground():
    for i in range(4):
        for j in range(4):
            hl = [h for h in HOLES if h[2] >= TILE_X[i] and h[0] <= TILE_X[i + 1] and h[3] >= TILE_Y[j] and h[1] <= TILE_Y[j + 1]]
            parts = mb1.terrain_tile(TILE_X[i], TILE_Y[j], TILE_X[i + 1], TILE_Y[j + 1], CELL, G, lambda nz, z, x, y: tb.slot_for(nz, z, x, y), holes=hl)
            for slot in range(5):                                  # every slot exists, so the material indices line up
                if slot not in parts:
                    dummy = mb.Mesh()
                    cx, cy = TILE_X[i] + 50.0, TILE_Y[j] + 50.0
                    dummy.poly([(cx, cy, -400.0), (cx + 20.0, cy, -400.0), (cx, cy + 20.0, -400.0)], (0, 0, 1))
                    parts[slot] = dummy
            sm = k1.commit_slots(CAT + "Ground_%d_%d" % (i, j), parts)
            k1.place(m, "Ground_%d_%d" % (i, j), sm, 0.0, 0.0, 0.0, mat=GROUND_MATS, folder="Ground")


build_ground()


def river_ribbon():
    pts = [(tb.river_x(y), y) for y in range(-4300, 4001, 150)]
    rm = mb1.ribbon(pts, lambda s: 1500.0, lambda x, y: tb.WATER, lift=0.0, edge=0.0, cross_n=3, step=150.0, wobble=0.0, closed_ends=False)
    sm = kb.commit(CAT + "River", rm, collision="none")
    k1.place(m, "River", sm, 0, 0, 0, mat=water_m, solid=False, shadow=False, folder="Ground")


river_ribbon()

EW = 300.0
for label, cx, cy, sx, sy in (("W", -tb.X_EDGE - EW / 2, 0.0, EW, 12000.0), ("E", tb.X_EDGE + EW / 2, 0.0, EW, 12000.0),
                              ("N", 0.0, tb.Y_NORTH + EW / 2, 16000.0, EW), ("S", 0.0, tb.Y_SOUTH - EW / 2, 16000.0, EW)):
    k1.invisible_wall(m, "Edge_" + label, cx, cy, 2000.0, sx, sy, 7000.0)

STARTS_TEAM = {0: [], 1: []}
STARTS_FREE = []
FLAGS = {}
AVOID = []                         # (x, y, r) kept free of scattered props


def put(label, mesh, x, y, z, yaw=0.0, mat=None, solid=True, shadow=True, cull=None, name=None, folder=None):
    sm = kb.commit(CAT + (name or label), mesh, collision="complex" if solid else "none")
    return k1.place(m, label, sm, x, y, z, yaw=yaw, mat=mat, solid=solid, shadow=shadow, cull=cull, folder=folder)


def cloth(label, x, y, z, yaw, mat, w=170.0, h=420.0, seed=1):
    return put(label, mm.cloth_mesh(w, h, waves=2.0, amp=9.0, seed=seed), x, y, z, yaw=yaw, mat=mat, solid=False, shadow=False, cull=7000, folder="Banners")


# ================================================================ the keeps
WT, WH = 380.0, 620.0


def build_keep(side, tag):
    s = side
    red = s < 0
    cx = s * tb.CX
    F = k1.Frame(m, s, cx, PZ, CAT + tag)
    wmat = wall_red if red else wall_blue
    rmat = roof_red if red else roof_slate
    cmat = cloth_red if red else cloth_blue
    cren = dict(outer=True, inner=False)

    def mk(length, ops, seed):
        return mb1.wall(length, WH, WT, ops, seed=seed + (0 if red else 40), crenel=cren, plinth=110.0, ring=34.0, corbel=44.0)

    F.put("WallFront", mk(2580, [dict(u0=1100, u1=1480, z0=0, z1=430, arch=True)], 1), 1440, -1290, 0, yaw=90, mat=wmat)
    F.put("WallNorth", mk(2880, [dict(u0=1570, u1=1910, z0=0, z1=390, arch=True)], 2), 1440, 1290, 0, yaw=180, mat=wmat)
    F.put("WallBack", mk(2580, [], 3), -1440, 1290, 0, yaw=270, mat=wmat)
    F.put("WallSouth", mk(2880, [dict(u0=1620, u1=1960, z0=0, z1=390, arch=True)], 4), -1440, -1290, 0, yaw=0, mat=wmat)
    # corner towers: platforms at the height of the wall walks, with gaps in the parapet where the walks come in
    gaps = {(1, 1): [(180, 26), (270, 26)], (1, -1): [(180, 26), (90, 26)], (-1, 1): [(0, 26), (270, 26)], (-1, -1): [(0, 26), (90, 26)]}
    for (su, sn), gp in gaps.items():
        r_ = 340.0 if (su > 0) else 360.0
        F.put("Tower_%d_%d" % (su, sn), mb1.drum_tower(r_, WH, gaps=gp, seed=3 + su + sn), su * 1250.0, sn * 1100.0, 0, mat=wmat)
    # gate towers with conical roofs
    for sn in (-1, 1):
        F.put("GateTower_%d" % sn, mb1.drum_tower(230.0, 900.0, roof=430.0, merlons=False, seed=11 + sn, sides=22), 1590.0, sn * 430.0, 0, mat=wmat)
    for sn in (-1, 1):                                    # roofs are separate: other material
        pass
    # the hall: flag room
    doors = [(1, 290, 260, 340), (1, 790, 260, 340), (0, 330, 200, 300), (2, 470, 200, 300)]
    windows = [(3, 240, 70, 150, 260), (3, 540, 70, 150, 260), (3, 840, 70, 150, 260), (0, 600, 70, 150, 280), (2, 150, 70, 150, 280)]
    hall = mb1.building(800, 1080, 620, thick=40.0, doors=doors, windows=windows, seed=5 + (0 if red else 9), ring=26.0, plinth=100.0)
    F.put("HallWalls", hall["walls"], -630, 0, 0, mat=wmat)
    F.put("HallFloor", hall["floor"], -630, 0, 3.0, mat=slabs_m, solid=False, shadow=False)
    F.put("HallCeiling", hall["ceil"], -630, 0, 0, mat=wood_m)
    F.put("HallRoof", mb1.gable_roof(800, 1080, 470.0, 60.0, seed=2, ridge_along_x=False), -630, 0, 640.0, mat=rmat)
    # wings (armoury / chapel): spawn rooms beside the hall
    for sn in (1, -1):
        wd = [(0, 330, 200, 290), (1, 185, 200, 290)] if sn > 0 else [(2, 400, 200, 290), (1, 185, 200, 290)]
        ww = [(2, 365, 70, 140, 150)] if sn > 0 else [(0, 365, 70, 140, 150)]
        wing = mb1.building(730, 370, 360, thick=36.0, doors=wd, windows=ww, seed=21 + sn, ring=20.0, plinth=80.0)
        F.put("Wing%d" % sn, wing["walls"], -665, sn * 725, 0, mat=wmat)
        F.put("WingFloor%d" % sn, wing["floor"], -665, sn * 725, 3.0, mat=wood_old, solid=False, shadow=False)
        F.put("WingCeil%d" % sn, wing["ceil"], -665, sn * 725, 0, mat=wood_m)
        F.put("WingRoof%d" % sn, mb1.gable_roof(730, 370, 200.0, 40.0, seed=3, ridge_along_x=True), -665, sn * 725, 380.0, mat=rmat)
    # two guard huts beside the avenue (spawn rooms, one door each, facing the avenue)
    for sn in (1, -1):
        hd = [(0, 260, 150, 240)] if sn > 0 else [(2, 260, 150, 240)]
        hw_ = [(1, 190, 60, 110, 120)]
        hut = mb1.building(520, 380, 280, thick=34.0, doors=hd, windows=hw_, seed=31 + sn, ring=16.0, plinth=60.0)
        F.put("Hut%d" % sn, hut["walls"], 700, sn * 420, 0, mat=wmat)
        F.put("HutFloor%d" % sn, hut["floor"], 700, sn * 420, 3.0, mat=wood_old, solid=False, shadow=False)
        F.put("HutCeil%d" % sn, hut["ceil"], 700, sn * 420, 0, mat=wood_m)
        F.put("HutRoof%d" % sn, mb1.gable_roof(520, 380, 190.0, 35.0, seed=4, ridge_along_x=True), 700, sn * 420, 298.0, mat=rmat)
    # stairs to the wall walks, along the inner face of the north and south walls
    st = ma.stairs_mesh(300.0, 14, 44.3, 70.0, seed=4)
    for sn in (-1, 1):
        F.put("WalkStairs%d" % sn, st, 80, sn * 760, 0, mat=wall_dark)
    # courtyard paving (visual only; the plateau is the floor)
    F.box("Paving", 0, 0, 1.5, 2120, 1820, 3, mat=cobble_m, solid=False, shadow=False)
    # banners
    for sn in (-1, 1):
        wx, wy = F.world(1452, sn * 640)
        cloth("Banner_%s_%d" % (tag, sn), wx, wy, PZ + 150.0, F.world_yaw(90.0), cmat, seed=sn + 3)
    for sn in (-1, 1):
        wx, wy = F.world(-1015, sn * 380)
        cloth("HallBanner_%s_%d" % (tag, sn), wx, wy, PZ + 170.0, F.world_yaw(90.0), cmat, w=200.0, h=380.0, seed=sn + 7)
    # flag base and dais
    wx, wy = F.world(-630, 0)
    fb = m.spawn(unreal.IAFlagBase, "FlagBase_" + tag, (wx, wy, PZ))
    fb.set_editor_property("flag_team", 0 if red else 1)
    dais = mb.Mesh()
    dais.lathe(0, 0, 0, 14.0, 130.0, 118.0, sides=28, segments=1)
    F.put("Dais", dais, -630, 0, 3.0, mat=lime_m, solid=False, shadow=False)
    # props: braziers, crates, statue
    for nm, name, u, n, yw, sc in (("Fire1", "fire_pit", -430, 330, 0, 0.9), ("Fire2", "fire_pit", -430, -330, 0, 0.9), ("Fire3", "fire_pit", 1000, 520, 0, 0.9),
                                   ("Fire4", "fire_pit", 1000, -520, 0, 0.9), ("Barrel1", "barrel_wood_a", 300, 440, 0, 1.0), ("Barrel2", "barrel_wood_b", 360, 380, 0, 1.0),
                                   ("Crate1", "crate_wood_a", 300, -440, 20, 1.6), ("Crate2", "crate_wood_b", 360, -380, -30, 1.4), ("Crate3", "crate_wood_a", 330, -500, 50, 1.4),
                                   ("Barrel3", "barrel_wood_a", -180, 880, 0, 1.0), ("Crate4", "crate_wood_b", -180, -880, 0, 1.4), ("Statue", "statue_gothic", 140, 540, 200, 1.2)):
        wx, wy = F.world(u, n)
        m.prop("%s_%s" % (tag, nm), name, wx, wy, PZ, yaw=F.world_yaw(yw), scale=sc, solid=True)
    # cover walls in the yard
    cov = ma.wall_run(300.0, [(0, 100, 120.0), (100, 200, 110.0), (200, 300, 120.0)], 60.0, seed=7, jitter=1.0)
    F.put("Cover1", cov, 120, 120, 0, yaw=90, mat=wmat)
    F.put("Cover2", cov, 120, -120, 0, yaw=90, mat=wmat)
    # starts
    for u, n in ((-800, 725), (-800, -725), (-880, 0), (700, 420), (700, -420), (-120, 700), (-120, -700), (900, 0)):
        wx, wy = F.world(u, n)
        STARTS_TEAM[0 if red else 1].append((wx, wy, PZ, F.world_yaw(0.0)))
    AVOID.append((cx, 0.0, 1900.0))
    return F


FR = build_keep(-1, "Red")
FB = build_keep(1, "Blue")

# ================================================================ the ridge: ramps, viaduct, huts
stone_grey = wall_grey
for sx in (-1, 1):
    steps = 12
    stair = ma.stairs_mesh(460.0, steps, PZ / steps, 90.0, seed=8)
    put("RidgeStairs_%d" % sx, stair, sx * 1100.0, 2650.0 - steps * 90.0, 0.0, yaw=90.0, mat=wall_dark, name="RidgeStairs")
    side = mb.Mesh()
    for sy in (-1, 1):
        side.box(0, sy * 250.0, 0, steps * 90.0, 40.0, 130.0, base=True, jitter=1.0, top_jitter=2.0, seed=sy + 3)
    AVOID.append((sx * 1100.0, 2000.0, 500.0))
    T_pad = None


def viaduct():
    x0, x1, yc = -480.0, 700.0, 3050.0
    L = x1 - x0
    deck = mb.Mesh()
    deck.box(0, 0, -70.0, L, 560.0, 70.0, base=True, jitter=0.0, top_jitter=0.0)
    deck.box(0, 0, -150.0, L - 60.0, 540.0, 82.0, base=True, jitter=0.4, seed=3)
    for sy in (-1, 1):
        deck.box(0, sy * 262.0, 0.0, L, 40.0, 100.0, base=True, jitter=0.4, top_jitter=0.3, seed=5 + sy)
    for px in (-60.0, 250.0):
        deck.box(px - (x0 + x1) / 2.0, 0, -900.0, 130.0, 380.0, 760.0, base=True, jitter=0.6, seed=int(px))
    put("Viaduct", deck, (x0 + x1) / 2.0, yc, PZ, mat=wall_grey)
    AVOID.append(((x0 + x1) / 2.0, yc, 800.0))


viaduct()


def make_building(label, x, y, yaw, w, d, h, wmat, rmat, doors, windows, seed, ring=0.0, ridge_x=True, rise=None, cz=0.0):
    b = mb1.building(w, d, h, thick=36.0, doors=doors, windows=windows, seed=seed, ring=ring, plinth=70.0)
    put(label + "_Walls", b["walls"], x, y, cz, yaw=yaw, mat=wmat)
    put(label + "_Floor", b["floor"], x, y, cz + 3.0, yaw=yaw, mat=wood_old, solid=False, shadow=False)
    put(label + "_Ceil", b["ceil"], x, y, cz, yaw=yaw, mat=wood_m)
    span = d if ridge_x else w
    put(label + "_Roof", mb1.gable_roof(w, d, rise or span / 2.0 * 1.1, 45.0, seed=seed, ridge_along_x=ridge_x), x, y, cz + h + 18.0, yaw=yaw, mat=rmat)


for sx in (-1, 1):                       # ridge huts: spawn rooms, door to the south
    make_building("RidgeHut_%d" % sx, sx * 1800.0, 3050.0, 0.0, 500.0, 420.0, 300.0, wall_dark, roof_slate,
                  [(0, 250, 150, 250), (2, 250, 150, 250)], [(1, 210, 70, 130, 140), (3, 210, 70, 130, 140)], 61 + sx, ring=20.0, cz=PZ)
    STARTS_FREE.append((sx * 1800.0, 3050.0, PZ, 270.0 if sx < 0 else 270.0))
    AVOID.append((sx * 1800.0, 3050.0, 500.0))

# ================================================================ the village
def village():
    for name, x, y, yaw, w, d, h in HOUSES:
        side = (0, 250, 150, 250)
        make_building(name, x, y, yaw, w, d, h, wall_red if x < 0 else wall_grey, roof_old, [(0, w / 2.0, 160, 250), (2, w / 2.0, 150, 250)],
                      [(1, d / 2.0, 80, 120, 130), (3, d / 2.0, 80, 120, 130), (0, w / 2.0 - 190, 70, 110, 130), (0, w / 2.0 + 190, 70, 110, 130)], sum(ord(c) for c in name), ring=18.0)
        # these houses have the door in the wall that faces the river: yaw 90 turns the -y wall (door) to +x
        STARTS_FREE.append((x, y, 0.0, 0.0 if x < 0 else 180.0))
        AVOID.append((x, y, 420.0))
    # chapel ruin
    cxp, cyp = CHAPEL
    LEN, WID, TK = 800.0, 520.0, 70.0
    rr = random.Random(5)

    def prof(length, hmax, hole=None):
        out, x = [], 0.0
        while x < length - 1:
            w_ = min(rr.uniform(90, 220), length - x)
            top = hmax - rr.choice((0, 0, 60, 140, 260, 380, 460))
            if hole and hole[0] <= x + w_ / 2.0 <= hole[1]:
                top = 40.0
            out.append((x, x + w_, float(max(top, 80.0))))
            x += w_
        return out
    pieces = [("N", LEN, 0, (cxp - LEN / 2.0, cyp + WID / 2.0 - TK), 0.0, None), ("S", LEN, 1, (cxp - LEN / 2.0, cyp - WID / 2.0), 0.0, (400, 560)),
              ("E", WID, 2, (cxp + LEN / 2.0 - TK, cyp - WID / 2.0), 90.0, (200, 360)), ("W", WID, 3, (cxp - LEN / 2.0 + TK, cyp + WID / 2.0), -90.0, None)]
    for nm, length, k, org, yaw, hole in pieces:
        put("Chapel_" + nm, ma.wall_run(length, prof(length, 760.0, hole), TK, seed=k + 3, jitter=3.0), org[0], org[1], 0.0, yaw=yaw, mat=wall_grey, name="ChapelWall" + nm)
    tower = mb1.square_tower(300.0, 300.0, 820.0, seed=9, merlons=False)
    put("Chapel_Tower", tower, cxp - LEN / 2.0 - 120.0, cyp + WID / 2.0, 0.0, mat=wall_grey, name="ChapelTower")
    heaps = [nn.block_heap(900 + k, count=7, spread=170.0) for k in range(3)]
    for k, (hx, hy) in enumerate(((cxp - 150, cyp + 80), (cxp + 220, cyp - 120), (cxp - 420, cyp - 60))):
        put("Rubble_%d" % k, heaps[k], hx, hy, 0.0, yaw=rr.uniform(0, 360), mat=wall_grey, solid=False, name="ChapelRubble%d" % k)
    m.prop("ChapelStatue", "statue_gothic", cxp - 360, cyp, 0.0, yaw=0.0, scale=1.3)
    for k, (gx, gy) in enumerate(((cxp - 600, cyp + 300), (cxp - 640, cyp + 100), (cxp - 650, cyp - 120), (cxp - 620, cyp - 330))):
        gm = mb.Mesh()
        gm.box(0, 0, -10, 70, 20, 120, base=True, jitter=3.0, top_jitter=6.0, seed=k)
        put("Grave_%d" % k, gm, gx, gy, 0.0, yaw=rr.uniform(-10, 10) + 90, mat=lime_m, name="Grave%d" % k)
    AVOID.append((cxp, cyp, 760.0))
    STARTS_FREE.append((cxp, cyp - 40.0, 0.0, 0.0))
    # market on the east bank: stalls with canvas roofs
    mx, my = 900.0, -650.0
    tent = mm.tent_mesh(300.0, 230.0, 230.0, 0.55, seed=3)
    for k, (dx, dy, yw, mt) in enumerate(((-300, -180, 0, canvas_m), (0, -190, 0, cloth_red), (300, -180, 0, cloth_blue), (-300, 180, 180, cloth_red), (0, 190, 180, canvas_m), (300, 180, 180, cloth_blue))):
        sx_, sy_ = mx + dx, my + dy
        put("StallRoof_%d" % k, tent, sx_, sy_, 130.0, yaw=yw, mat=mt, solid=False, shadow=True, name="StallRoof")
        tb_ = mb.Mesh()
        tb_.box(0, 0, 0, 220, 70, 85, base=True, jitter=1.0, seed=k)
        for px_ in (-130, 130):
            for py_ in (-100, 100):
                tb_.box(px_, py_, 0, 10, 10, 190, base=True, jitter=0.5, seed=k + 5)
        put("StallTable_%d" % k, tb_, sx_, sy_, 0.0, yaw=yw, mat=wood_m, name="StallTable")
    m.prop("MarketBarrel1", "barrel_wood_a", mx - 20, my + 4, 0, scale=1.0)
    m.prop("MarketCrate", "crate_wood_a", mx + 120, my - 40, 0, yaw=30, scale=1.6)
    AVOID.append((mx, my, 560.0))
    # well
    wm_ = mb.Mesh()
    wm_.lathe(0, 0, 0, 90.0, 120.0, 110.0, sides=20, segments=2, cap_top=True)
    put("Well", wm_, 800.0, -1100.0, 0.0, mat=wall_grey, name="Well")
    AVOID.append((800.0, -1100.0, 250.0))


village()


def main_bridge():
    yc = 0.0
    deck = mb.Mesh()
    deck.box(325.0, 0, -60.0, 1550.0, 520.0, 130.0, base=True, jitter=0.0, top_jitter=0.0)       # top at z = 70 (x from -450 to 1100)
    for sy in (-1, 1):
        deck.box(325.0, sy * 240.0, 70.0, 1550.0, 44.0, 100.0, base=True, jitter=0.5, top_jitter=0.4, seed=sy + 3)
    for px in (-100.0, 330.0, 760.0):
        deck.box(px, 0, -210.0, 150.0, 440.0, 170.0, base=True, jitter=0.6, seed=int(px) % 97)
    put("Bridge", deck, 0.0, yc, 0.0, mat=wall_grey)
    for k, sx in enumerate((-1, 1)):
        x0 = -850.0 if sx < 0 else 1500.0
        put("BridgeApproach_%d" % k, mm.ramp_wedge(400.0, 70.0, 520.0), x0, yc, 0.0, yaw=0.0 if sx < 0 else 180.0, mat=wall_grey, name="BridgeApproach")
    AVOID.append((330.0, 0.0, 900.0))


main_bridge()

# ================================================================ the tunnel
def tunnel():
    L = TUN_X1 - TUN_X0
    ops_n = [dict(u0=L - (xc - TUN_X0) - 165.0, u1=L - (xc - TUN_X0) + 165.0, z0=0.0, z1=250.0, arch=True) for xc in PORTAL_X]
    ops_s = [dict(u0=(xc - TUN_X0) - 165.0, u1=(xc - TUN_X0) + 165.0, z0=0.0, z1=250.0, arch=True) for xc in PORTAL_X]
    c = mb1.vault_corridor(L, 330.0, 250.0, 70.0, seed=3, openings_n=ops_n, openings_s=ops_s)
    ox, oy, oz = TUN_X0, TUN_Y, TUN_Z
    put("Tunnel_Floor", c["floor"], ox, oy, oz, mat=slabs_m, name="TunnelFloor")
    put("Tunnel_Walls", c["walls"], ox, oy, oz, mat=wall_dark, name="TunnelWalls")
    put("Tunnel_Vault", c["vault"], ox, oy, oz, mat=wall_grey, name="TunnelVault")
    put("Tunnel_Ribs", c["ribs"], ox, oy, oz, mat=wall_dark, name="TunnelRibs")
    caps = mb.Mesh()
    for sx in (0.0, L):
        caps.box(sx + (-20.0 if sx == 0.0 else 20.0), 0, -40.0, 40.0, 410.0, 460.0, base=True, jitter=0.0)
    put("Tunnel_Caps", caps, ox, oy, oz, mat=wall_dark, name="TunnelCaps")
    # four ramps to the surface
    ang = math.degrees(math.atan2(620.0, 1120.0))
    cp, sp = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    Lv = 435.0 / cp
    Lt = 1120.0 / cp
    for xc in PORTAL_X:
        for d in (1, -1):
            parts = mb1.vault_corridor(Lv, 330.0, 250.0, 70.0, seed=5, ribs_every=320.0)
            tr = mb.Mesh()
            tr.box((Lv + Lt) / 2.0, 0, -40.0, Lt - Lv, 330.0, 40.0, base=True, jitter=0.0)
            for sy in (-1, 1):
                # horizontal wall tops 60 above the ground (z = 60 in the world)
                def top(x):
                    return (620.0 + 60.0 - x * sp) / cp
                poly = [(Lv, -40.0), (Lt + 40.0, -40.0), (Lt + 40.0, top(Lt + 40.0)), (Lv, top(Lv))]
                tr.prism(poly, sy * 165.0 + (0.0 if sy > 0 else -85.0), sy * 165.0 + (85.0 if sy > 0 else 0.0), jitter=0.0)
            allm = mb.Mesh()
            for k in ("floor", "walls", "vault"):
                allm.append(parts[k])
            ribs = parts["ribs"]
            y0 = TUN_Y + d * 165.0
            for nm, mesh, mt in (("Ramp", allm, wall_grey), ("RampRibs", ribs, wall_dark), ("RampTrench", tr, wall_dark)):
                xm = mb1.xform(mesh, yaw=90.0 * d, pitch=ang)
                put("Portal_%d_%d_%s" % (int(xc), d, nm), xm, xc, y0, TUN_Z, mat=mt, name="Portal%d_%d_%s" % (int(xc), d, nm))
            stairs = ma.stairs_mesh(330.0, 14, 620.0 / 14.0, 80.0, seed=int(xc) % 17 + d)
            put("PortalStairs_%d_%d" % (int(xc), d), mb1.xform(stairs, yaw=90.0 * d), xc, y0, TUN_Z, mat=slabs_m, name="PortalStairs%d_%d" % (int(xc), d))
    for k, xt in enumerate((-1500.0, -500.0, 500.0, 1500.0)):
        m.flame("TunnelTorch_%d" % k, xt, TUN_Y - 150.0, TUN_Z + 170.0, scale=0.5, light=12.0, radius=450.0, embers=False)
    for xc in PORTAL_X:
        STARTS_FREE.append((xc, TUN_Y, TUN_Z, 90.0))
    AVOID.extend([(xc, y, 650.0) for xc in PORTAL_X for y in (-950.0, -2850.0)])


tunnel()

# ================================================================ roads and ground patches
def road(points, width=420.0, mat=None, seed=1, name="Road"):
    rm = mb1.ribbon(points, lambda s_: width, G, lift=4.0, edge=-5.0, cross_n=5, step=80.0, wobble=0.22, seed=seed)
    put(name, rm, 0, 0, 0, mat=mat or trail_m, solid=False, shadow=False, name=name, folder="Ground")


for s_, tag in ((-1, "R"), (1, "B")):
    cxk = s_ * tb.CX
    road([(s_ * 3500.0, 0.0), (s_ * 2900.0, -60.0), (s_ * 2300.0, -150.0), (s_ * 1500.0, -80.0), (s_ * 850.0, -10.0)], mat=trail_m, seed=3, name="Road_" + tag)
    road([(s_ * 5300.0, 1450.0), (s_ * 5300.0, 2150.0), (s_ * 4300.0, 2800.0), (s_ * 3500.0, 3030.0), (s_ * 2200.0, 3050.0), (s_ * 1100.0, 3050.0)],
         width=380.0, mat=trail_m, seed=5, name="RidgeTrail_" + tag)
    road([(s_ * 4650.0, -1450.0), (s_ * 4300.0, -2300.0), (s_ * 3000.0, -2900.0), (s_ * 1600.0, -3000.0)], width=380.0, mat=trail_m, seed=7, name="SouthTrail_" + tag)

PATCH_KINDS = [(dirt_m, 9, (260, 520)), (grass_dry_m, 12, (400, 900)), (moss_m, 7, (300, 600))]
pn = 0
for mat_, count, (rmin, rmax) in PATCH_KINDS:
    placed = 0
    tries = 0
    while placed < count and tries < 400:
        tries += 1
        x, y = rng.uniform(-3600, 3600), rng.uniform(-3400, 2300)
        if abs(x - tb.river_x(y)) < 650 or any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in AVOID):
            continue
        if T.slope_deg(x, y) > 24:
            continue
        pn += 1
        placed += 1
        pm = mb1.patch(x, y, rng.uniform(rmin, rmax), rng.uniform(rmin, rmax) * 0.8, G, seed=pn, yaw=rng.uniform(0, 180), cell=70.0, lift=4.0)
        if len(pm.tris) > 0:
            put("Patch_%d" % pn, pm, 0, 0, 0, mat=mat_, solid=False, shadow=False, name="Patch%d" % pn, folder="Ground")

# ================================================================ jump pads
def pad(label, x, y, tx, ty, tz, color):
    m.jump_pad(label, x, y, G(x, y), (tx, ty, tz), color=color, apex_extra=200.0)
    AVOID.append((x, y, 260.0))


pad("RidgePad_W", -700.0, 1950.0, -700.0, 2950.0, PZ, (0.3, 0.85, 1.0))
pad("RidgePad_E", 700.0, 1950.0, 700.0, 2950.0, PZ, (0.3, 0.85, 1.0))
pad("RiverPad_W", -820.0, -1000.0, 850.0, -900.0, G(850.0, -900.0), (1.0, 0.7, 0.2))
pad("RiverPad_E", 950.0, -1050.0, -750.0, -950.0, G(-750.0, -950.0), (1.0, 0.7, 0.2))

# ================================================================ nature
def scatter(names, region, count, seed, label, scale=(0.8, 1.2), gap=120.0, solid=None, shadow=False, cull=7000, slope=30, zr=(-1e5, 1e5), sink=0.0):
    a = m.scatter(names, region, count, seed=seed, scale=scale, min_gap=gap, avoid=AVOID, solid=solid, label=label, max_slope=slope, z_range=zr, sink=sink)
    k1.tune(a, shadow=shadow, cull=cull)
    return a


import mesh_trees_big1 as mtb  # noqa: E402

fir_mats = [surface("CitFir"), surface("CitFirLight"), surface("CitBark")]
FIR_SM = []
for v in range(5):
    fol, trk = mtb.fir_tree(height=650.0 + 40.0 * v, radius=175.0 + 8.0 * v, seed=10 + v, tiers=8 + v % 2, sides=12)
    FIR_SM.append(k1.commit_slots(CAT + "Fir_%d" % v, {0: fol, 1: trk}, collision="none"))
FIR_PLACED = []


def firs(region, count, label, collide, cull, slope=30, gap=230.0, scale=(0.8, 1.5), shadow=True):
    x0, y0, x1, y1 = region
    placed = 0
    for _ in range(count * 30):
        if placed >= count:
            break
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if abs(x - tb.river_x(y)) < (700.0 if y < 2300 else 520.0) and y < 3600:
            continue
        if any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in AVOID):
            continue
        if any(math.hypot(x - px, y - py) < gap for px, py in FIR_PLACED):
            continue
        if T.slope_deg(x, y, 60.0) > slope:
            continue
        z = G(x, y)
        v = rng.randrange(5)
        sc = rng.uniform(*scale)
        a = k1.place(m, "%s_%d" % (label, placed), FIR_SM[v], x, y, z - 6.0, yaw=rng.uniform(0, 360), scale=(sc, sc, sc * rng.uniform(0.9, 1.15)), mat=[fir_mats[rng.randrange(2)], fir_mats[2]],
                     solid=False, shadow=shadow, cull=cull, folder="Trees")
        if collide:
            c = m.column("%s_Trunk_%d" % (label, placed), x, y, z - 10.0, z + 320.0, 40.0, mat=None, solid=True)
            c.set_actor_hidden_in_game(True)
            c.static_mesh_component.set_cast_shadow(False)
        FIR_PLACED.append((x, y))
        placed += 1
    unreal.log("CITADEL firs %s placed %d of %d" % (label, placed, count))


firs((-3300, -1900, -1500, 1900), 18, "FirW", True, 15000)
firs((1500, -1900, 3300, 1900), 18, "FirE", True, 15000)
firs((-3300, -3600, 3300, -2400), 24, "FirS", True, 15000)
firs((-5600, 1500, 5600, 2500), 16, "FirN", True, 15000)
firs((-6200, 2700, 6200, 3500), 14, "FirRidge", True, 15000)
firs((-6200, -3800, -3000, -1700), 30, "FirBgW", False, 20000, slope=36, gap=260.0, scale=(1.0, 1.9), shadow=False)
firs((3000, -3800, 6200, -1700), 30, "FirBgE", False, 20000, slope=36, gap=260.0, scale=(1.0, 1.9), shadow=False)
scatter(["rock_moss_big_a", "rock_moss_big_b", "rock_moss_big_c", "rock_moss_big_d", "rock_boulder_l"], ("rect", -5800, -3700, 5800, 3400), 60, 31, "Rock", scale=(0.8, 1.7), gap=250.0, solid=True, cull=9000, slope=35)
scatter(["rock_moss_small_a", "rock_moss_small_b", "rock_moss_small_c", "rock_flat_s"], ("rect", -5800, -3700, 5800, 3400), 120, 32, "Stone", scale=(0.6, 1.3), gap=100.0, solid=False, cull=5000, slope=40)
scatter(["fern_a", "fern_b", "shrub_a", "shrub_b"], ("rect", -5800, -3700, 5800, 3400), 220, 33, "Plant", scale=(1.2, 2.4), gap=70.0, solid=False, cull=4500, slope=34)
scatter(["stump_a", "trunk_dead_b"], ("rect", -3400, -3500, 3400, 2300), 10, 34, "Dead", scale=(1.0, 1.6), gap=300.0, solid=True, cull=8000, slope=25)


# distant mountains (no collision)
for i in range(11):
    ang = i / 11.0 * 2.0 * math.pi + 0.2
    mx_, my_ = math.cos(ang) * rng.uniform(14500, 17500), math.sin(ang) * rng.uniform(11000, 13500)
    sm = kb.commit(CAT + "FarMountain_%d" % i, mm.mountain_mesh(rng.uniform(4500, 6500), rng.uniform(3500, 6000), seed=i * 5 + 3), collision="none")
    k1.place(m, "FarMountain_%d" % i, sm, mx_, my_, -300.0, yaw=rng.uniform(0, 360), mat=far_m, solid=False, shadow=False, folder="Far")

# ================================================================ starts, light
for team, tag in ((0, "Red"), (1, "Blue")):
    for i, (x, y, z, yaw) in enumerate(STARTS_TEAM[team]):
        ps = m.spawn(unreal.PlayerStart, "PlayerStart_%s_%d" % (tag, i), (x, y, z + 110.0), (0, 0, yaw))
        ps.set_editor_property("player_start_tag", tag)
        m.start_count += 1
for i, (x, y, z, yaw) in enumerate(STARTS_FREE):
    m.spawn(unreal.PlayerStart, "PlayerStart_Free_%d" % i, (x, y, z + 110.0), (0, 0, yaw))
    m.start_count += 1

m.look("day_clear", sun_yaw=110.0)
m.check_starts()
m.finish(kill_z=-2500)
