"""DM-Glacier: an arctic research outpost on a snow plateau. Medium arena (4-8 players).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_glacier.py" -unattended -nullrhi -nosplash

Layout (unchanged, bots and balance depend on it): a central rock and ice ridge with a radio relay deck on top (ramp from
the ridge, jump pads from the north and south snow fields), two base modules with walkable roofs, two covered ice tunnels,
trees and ice formations for cover, a wall of ice and rock around the plateau.

Look: real materials (matlib: snow, ice, rock, painted corrugated steel, wood), rock/cliff and fir props from the prop
library, snow drifts, painted huts with doors and windows, radio mast, fuel barrels, crates, fire pit, lamps, snowy
mountains and a pine forest outside the walls. Look preset "arctic".
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import props  # noqa: E402,F401
from mapkit import MapBuilder  # noqa: E402
from matlib import surface, glass  # noqa: E402
from mapkit_d import Frame, hcolumn, tube, beam, sphere, diamond  # noqa: E402
import mapkit_b as kb  # noqa: E402
import mesh_b as mb  # noqa: E402
import mesh_misc_b as mm  # noqa: E402
import mesh_nat_n as nn  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Glacier")
rng = random.Random(88)
S = surface

m.look("arctic", ev=1.0, ambient_gain=0.28125, sky_intensity=4.2, sky_rgb=(0.96, 0.98, 1.0), ground_rgb=(0.62, 0.64, 0.68), sun_lux=12.0, fog_density=0.0020)

# ------------------------------------------------------------------------------------------------ materials
snow = S("Snow", albedo=(212, 218, 230), tiling=7.0, ns=1.0, macro=0.2, tag="Glacier3")
snow_b = S("SnowBlue", tiling=6.0, albedo=(200, 214, 230), ns=1.0, tag="GlacierDrift3")
# Frozen water: the Ice scan looks like a water surface when it fills a whole wall, so big ice faces use a pale blue
# frosted-snow texture with a little gloss (still matte enough not to look wet).
ice = S("SnowBlue", albedo=(196, 212, 226), tiling=3.0, rb=-0.2, ns=1.2, macro=0.2, tag="GlacierIce2")
ice_deep = S("SnowBlue", albedo=(150, 178, 204), tiling=3.0, rb=-0.25, ns=1.2, macro=0.2, tag="GlacierIceDeep2")
grock = S("GlacierRock")
drock = S("GlacierRock", albedo=(96, 102, 112), tag="GlacierDark")
red_corr = S("CorrugatedGalv", albedo=(150, 52, 40), metal=0.2, tag="GlacierRed")
blue_corr = S("CorrugatedGalv", albedo=(70, 98, 128), metal=0.2, tag="GlacierBlue")
white_wood = S("WoodPaintedWhite", tag="Glacier")
red_wood = S("WoodPaintedRed")
wood_dark = S("WoodPlanksDark")
wood_old = S("WoodPlanksOld")
wood_br = S("WoodBridge")
log = S("WoodPlanksOld", albedo=(110, 84, 62), tag="GlacierLog")
roof_tar = S("RoofTarmac")
roof_sl = S("RoofSlate", albedo=(70, 74, 80), tag="Glacier")
steel = S("SteelDark")
steel_l = S("BrushedMetal", albedo=(150, 154, 158), tag="Glacier")
plate = S("DiamondPlateDark")
pane_glow = m.glow("MI_GlacierWindow", (1.0, 0.62, 0.28), 1.0)
bulb = m.glow("MI_GlacierBulb", (1.0, 0.85, 0.6), 2.0)
beacon = m.glow("MI_GlacierBeacon", (1.0, 0.12, 0.05), 2.5)
glass_m = glass()

WARM = (1.0, 0.72, 0.4)
HX, HY = 3200.0, 2200.0

STARTS = [(1500.0, -1100.0, 0), (-1200.0, 100.0, 240), (900.0, 1000.0, 0), (-1200.0, -500.0, 0), (0.0, -500.0, 300),
          (2850.0, -1550.0, 0), (1050.0, 1900.0, 0), (-2850.0, -1850.0, 0), (-1950.0, 1450.0, 0), (2700.0, 250.0, 0),
          (2700.0, 1600.0, 0), (-3000.0, 1900.0, 0)]
PADS = [(0, 1450), (0, -1450)]


def free(x, y, r=120.0):
    for sx, sy, _ in STARTS:
        if math.hypot(x - sx, y - sy) < r + 80:
            return False
    for px, py in PADS:
        if math.hypot(x - px, y - py) < r + 100:
            return False
    return True


def snow_patch(label, x, y, z, sx, sy, sz=8.0, yaw=0.0, mat=None):
    """A low drift of snow (flattened ellipsoid, no collision)."""
    return sphere(m, label, x, y, z, sx, sy, sz * 2, yaw=yaw, mat=mat or snow)


# ------------------------------------------------------------------------------------------------ ground and perimeter
m.box("Snowfield", 0, 0, -100, HX * 2, HY * 2, 200, mat=snow)
m.box("OuterPlain", 0, 0, -205, 60000, 60000, 400, mat=S("Snow", albedo=(206, 212, 224), tiling=8.0, tag="GlacierFar2"), solid=False)

# drifts: undulating snow all over the plateau (low, no collision)
for i in range(70):
    x, y = rng.uniform(-HX + 150, HX - 150), rng.uniform(-HY + 150, HY - 150)
    w = rng.uniform(300, 900)
    snow_patch("Drift_%d" % i, x, y, 4.0, w, w * rng.uniform(0.35, 0.7), sz=rng.uniform(12, 30), yaw=rng.uniform(0, 180),
               mat=snow if i % 3 else snow_b)

# wall around the plateau: ice and rock blocks (solid), cliffs and snow banks in front
n = 0
for side in range(4):
    horiz = side % 2 == 0
    length = HX * 2 if horiz else HY * 2
    pos = 0.0
    while pos < length:
        w = rng.uniform(350, 700)
        h = rng.uniform(520, 680)
        a = -(length / 2) + pos + w / 2
        off = (HY if horiz else HX) + 200
        sgn = 1 if side < 2 else -1
        cx, cy = (a, sgn * off) if horiz else (sgn * off, a)
        kind = (1, 1, 3, 1, 0, 3)[n % 6]
        # the block is only the collision now (hidden): a generated layered cliff with a snow cornice stands in front of it
        wall_box = m.box("Wall_%d" % n, cx, cy, h / 2 - 100, w if horiz else 400, 400 if horiz else w, h + 100,
                         yaw=rng.uniform(-4, 4), mat=(ice, grock, ice_deep, drock)[kind])
        wall_box.set_actor_hidden_in_game(True)
        # a snow bank leaning against the foot of the wall
        bx = cx - (0 if horiz else sgn * 260)
        by = cy - (sgn * 260 if horiz else 0)
        snow_patch("WallBank_%d" % n, bx, by, 20.0, w * 0.9 if horiz else 220, 220 if horiz else w * 0.9, sz=55.0, mat=snow)
        pos += w
        n += 1

# generated layered cliffs with a snow cornice in front of the (now invisible) wall blocks
def smooth(a, b, x):
    return mb.smoothstep(a, b, x)


def cliff_off(seed, lay, reach=420.0, vmin=26.0):
    def off(u, z):
        raw = (lay.profile(u, z, 70.0) + 95.0 * mb.fbm(u / 900.0 + seed, z / 420.0, 0.0, 3, seed) + 40.0 * mb.fbm(u / 160.0, z / 110.0, 0.0, 2, seed + 3)
               + 22.0 * nn.plateau(u, z, 140.0, 80.0, seed + 5) - 40.0 * mb.ridged(u / 130.0, z / 1400.0, 0.0, 2, seed + 7))
        v = 70.0 + raw + 80.0 * smooth(430.0, 560.0, z)            # the snow cornice leans out at the top
        return max(vmin, min(v * (0.45 + 0.55 * smooth(40.0, 300.0, z)), 30.0 + reach * smooth(120.0, 420.0, z)))
    return off


def cliff_run(label, org, yaw, width, zs, mats, seed, depth=700.0, top_snow=True, rim_amp=60.0, cap=True, reach=420.0, vmin=26.0):
    rim = (lambda u: rim_amp * (mb.fbm(u / 700.0 + seed, 0.3, 0.0, 2, seed + 31) - 0.3)) if rim_amp else None
    lay = nn.Layers(zs, seed, wob=22.0, wob_len=380.0, rim=rim, rim_from=zs[0] + (zs[-1] - zs[0]) * 0.5)
    off = cliff_off(seed, lay, reach, vmin)
    for k in range(len(zs) - 1):
        top = k == len(zs) - 2
        mesh = nn.cliff_strip2(width, lambda u, k=k: lay.boundary(k, u), lambda u, k=k: lay.boundary(k + 1, u), off, depth, cell=85.0,
                               cap=bool(top and cap), cap_fn=(lambda u, y: 55.0 * mb.fbm(u / 500.0 + seed, y / 300.0, 0.0, 3, seed + 55)) if (top and cap) else None,
                               skirt_top=top and not cap)
        sm = kb.commit("G%s_%d" % (label, k), mesh, collision="none")
        kb.put(m, "Cliff_%s_%d" % (label, k), sm, org[0], org[1], 0.0, yaw=yaw, mat=mats[k % len(mats)], solid=False, folder="Cliffs")
    return lay, off


PERIM = [("N", (-(HX + 400.0), HY), 0.0, 2 * HX + 800.0, [drock, grock, ice, snow]),
         ("S", (HX + 400.0, -HY), 180.0, 2 * HX + 800.0, [grock, drock, ice_deep, snow]),
         ("E", (HX, HY + 400.0), -90.0, 2 * HY + 800.0, [drock, ice, grock, snow]),
         ("W", (-HX, -(HY + 400.0)), 90.0, 2 * HY + 800.0, [grock, ice_deep, drock, snow])]
for i, (nm, org, yaw, wd, mats_) in enumerate(PERIM):
    cliff_run("Wall" + nm, org, yaw, wd, [-100.0, 140.0, 330.0, 470.0, 610.0], mats_, 50 + i)

# mountains behind the wall: generated craggy peaks (snow and rock), then a pine forest on the plain
mats_m = {"snow": S("SnowBlue", albedo=(196, 210, 228), tiling=8.0, ns=1.2, tag="GlacierFarSnow"), "rock": S("GlacierRock", tiling=8.0, tag="GlacierFar")}
MOUNT_SM = [kb.commit("GMount_%d" % k, mm.mountain_mesh(rng.uniform(4200, 6200), rng.uniform(4200, 6600), seed=400 + k, sides=96, rings=26, ridge=0.4, base_z=-300.0)) for k in range(6)]
HILL_SM = [kb.commit("GHill_%d" % k, mm.mountain_mesh(rng.uniform(1700, 2600), rng.uniform(700, 1500), seed=440 + k, sides=72, rings=18, ridge=0.3, base_z=-300.0)) for k in range(4)]
for i in range(22):
    ang = math.radians(i * (360.0 / 22) + rng.uniform(-6, 6))
    d = rng.uniform(9500, 13500)
    kb.put(m, "Mountain_%d" % i, MOUNT_SM[i % 6], math.cos(ang) * d * 1.2, math.sin(ang) * d, -200.0, yaw=rng.uniform(0, 360),
           scale=(rng.uniform(0.9, 1.4), rng.uniform(0.9, 1.4), rng.uniform(0.8, 1.2)), mat=mats_m["snow" if i % 3 else "rock"], solid=False, folder="Far")
for i in range(14):
    ang = math.radians(i * (360.0 / 14) + rng.uniform(-8, 8))
    d = rng.uniform(5600, 7600)
    kb.put(m, "Hill_%d" % i, HILL_SM[i % 4], math.cos(ang) * d * 1.2, math.sin(ang) * d, -200.0, yaw=rng.uniform(0, 360),
           scale=(rng.uniform(0.9, 1.5), rng.uniform(0.9, 1.5), 1.0), mat=mats_m["snow" if i % 2 else "rock"], solid=False, folder="Far")

# ------------------------------------------------------------------------------------------------ central ridge
m.box("Ridge", 0, 0, 150, 1800, 1200, 300, mat=grock)
m.box("RidgeTop", 0, 0, 302, 1700, 1100, 4, mat=snow, solid=False)
m.slope("RidgeSlopeW", (-2050, 0, 0), (-900, 0, 300), 900, thickness=60, mat=snow)
m.slope("RidgeSlopeE", (2050, 0, 0), (900, 0, 300), 900, thickness=60, mat=snow)
# rock outcrops on the long sides and ends of the ridge (no collision, the box is the wall)
for sy in (-1, 1):
    # the long faces of the ridge: generated layered rock (the box behind it is the collision), snow on the lip
    cliff_run("Ridge" + ("N" if sy > 0 else "S"), (900.0, 600.0) if sy > 0 else (-900.0, -600.0), 180.0 if sy > 0 else 0.0, 1800.0,
              [-20.0, 110.0, 205.0, 302.5], [drock, grock, snow], 70 + sy, depth=640.0, rim_amp=0, cap=False, reach=45.0, vmin=18.0)
    for i in range(4):
        snow_patch("RidgeBank", -600 + i * 400, sy * 680, 8, 480, 200, sz=35)
for sx in (-1, 1):
    for sy in (-1, 1):
        m.prop("SlopeRock", "rock_boulder_s", sx * 1500, sy * 470, 0, yaw=rng.uniform(0, 360), scale=1.3,
               material=grock, solid=False, sink=0.2)
for i in range(10):                                                  # small rocks and snow on top
    m.prop("TopRock_%d" % i, "rock_flat_s", rng.uniform(-750, 750), rng.uniform(-500, 500), 300, yaw=rng.uniform(0, 360),
           scale=rng.uniform(0.6, 1.2), material=grock, solid=False)

# relay deck on the ridge
DECK_Z = 440.0
m.box("Deck", 0, 0, DECK_Z - 20, 700, 700, 40, mat=plate)
m.box("DeckFascia", 0, 0, DECK_Z - 45, 712, 712, 18, mat=steel, solid=False)
for sx in (-1, 1):
    for sy in (-1, 1):
        m.column("DeckPost", sx * 310, sy * 310, 300, DECK_Z - 40, 50, mat=steel)
m.slope("DeckRamp", (850, 0, 300), (350, 0, DECK_Z), 260, thickness=40, mat=plate)
for sy in (-1, 1):
    m.box("DeckRail", 0, sy * 345, DECK_Z + 50, 700, 10, 100, mat=plate)
m.box("DeckRailW", -345, 0, DECK_Z + 50, 10, 700, 100, mat=plate)
for s in (-1, 1):
    mapkit_f = Frame(m, 0)
    mapkit_f.railing("RampRail", (850, s * 135, 300), (350, s * 135, DECK_Z), height=100, post_every=200, mat=steel, rails=2)
# the mast: lattice of four legs, cross bars, a dish, antennas and a beacon
for sx in (-1, 1):
    for sy in (-1, 1):
        tube(m, "MastLeg", (sx * 60, sy * 60, DECK_Z), (sx * 22, sy * 22, DECK_Z + 1100), 12, steel_l)
for k in range(8):
    z = DECK_Z + 100 + k * 130
    w = 120 - k * 11
    for (a, b) in (((-w / 2, -w / 2), (w / 2, -w / 2)), ((w / 2, -w / 2), (w / 2, w / 2)), ((w / 2, w / 2), (-w / 2, w / 2)),
                   ((-w / 2, w / 2), (-w / 2, -w / 2))):
        tube(m, "MastBar", (a[0], a[1], z), (b[0], b[1], z + 60), 5, steel_l)
tube(m, "Antenna", (0, 0, DECK_Z + 1100), (0, 0, DECK_Z + 1400), 8, steel_l)
for z in (DECK_Z + 1000, DECK_Z + 1150, DECK_Z + 1280):
    m.box("AntennaBar", 0, 0, z, 150 - (z - DECK_Z - 1000) * 0.3, 4, 4, mat=steel_l, solid=False)
m.column("DishArm", 40, 0, DECK_Z + 780, DECK_Z + 800, 20, mat=steel, solid=False)
dish = m._place("Dish", m.cylinder, (110, 0, DECK_Z + 800), (2.6, 2.6, 0.06), 0.0, 75.0, white_wood, False)
dish.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=70.0, yaw=0.0), False)
m.column("Beacon", 0, 0, DECK_Z + 1400, DECK_Z + 1430, 22, mat=beacon, solid=False)
m.accent_light("BeaconLight", (0, 0, DECK_Z + 1460), (1.0, 0.15, 0.08), 400.0, 1800.0)
for (gx, gy) in ((600, 600), (-600, 600), (600, -600), (-600, -600)):             # guy wires
    tube(m, "Guy", (gx, gy, 300), (gx * 0.1, gy * 0.1, DECK_Z + 1000), 3, steel)
for sy in (-1, 1):                                                  # pads from the snow fields to the deck
    m.jump_pad("DeckPad_%s" % ("N" if sy > 0 else "S"), 0, sy * 1450, 0, (0, sy * 120, DECK_Z), color=(0.3, 0.85, 1.0),
               apex_extra=170.0)
    m.prop("PadRock_%d" % sy, "rock_boulder_s", 260, sy * 1520, 0, scale=0.9, material=grock, solid=False, sink=0.1)


# ------------------------------------------------------------------------------------------------ base modules (walkable roofs)
def hut(f, wall_mat, trim, tag):
    x0, x1, y0, y1, wh, t = -2800.0, -2100.0, -1000.0, -400.0, 210.0, 40.0
    ym = (y0 + y1) / 2.0
    for (ax, ay, sx, sy) in [((x0 + x1) / 2, y0 + t / 2, x1 - x0, t), ((x0 + x1) / 2, y1 - t / 2, x1 - x0, t),
                             (x0 + t / 2, ym, t, y1 - y0)]:
        f.box("HutWall_" + tag, ax, ay, wh / 2, sx, sy, wh, mat=wall_mat)
    gap = 280.0
    seg = (y1 - y0 - gap) / 2
    for sgn in (-1, 1):
        f.box("HutWallE_" + tag, x1 - t / 2, ym + sgn * (gap / 2 + seg / 2), wh / 2, t, seg, wh, mat=wall_mat)
    f.box("HutLintel_" + tag, x1 - t / 2, ym, wh - 30, t, gap, 60, mat=wall_mat)
    f.box("HutRoof_" + tag, (x0 + x1) / 2, ym, wh + 15, x1 - x0 + 40, y1 - y0 + 40, 30, mat=roof_tar)
    # roof edge trim, snow patches, rails, chimney and aerial
    for sy in (-1, 1):
        f.box("RoofTrim", (x0 + x1) / 2, ym + sy * 322, wh + 30, x1 - x0 + 44, 6, 22, mat=trim, solid=False)
    for sx in (-1, 1):
        f.box("RoofTrim", (x0 + x1) / 2 + sx * 372, ym, wh + 30, 6, y1 - y0 + 44, 22, mat=trim, solid=False)
    # snow cover that follows the roof: lumpy blankets with an irregular edge (the outline is where the surface meets the roof),
    # a drift against the parapet and icicles hanging from the eaves
    for i, (px, py, w, d, th) in enumerate([(-2520, -720, 560, 430, 15.0), (-2230, -860, 250, 190, 12.0), (-2700, -520, 200, 220, 11.0)]):
        wx, wy = f.P(px, py)
        kb.put(m, "RoofSnow_%s_%d" % (tag, i), kb.commit("GRoofSnow_%d" % i, nn.snow_cap(w, d, seed=30 + i, thick=th)), wx, wy, wh + 30.0, yaw=f.Y(rng.uniform(-6, 6)), mat=snow, solid=False)
    for j, (ex, ey, ln, yw) in enumerate([(x0 - 20.0, y0 - 22.0, 740.0, 0.0), (x0 - 20.0, y1 + 22.0, 740.0, 0.0)]):
        wx, wy = f.P(ex, ey)
        kb.put(m, "Icicles_%s_%d" % (tag, j), kb.commit("GIcicles_%d" % j, nn.icicles(ln, 24, seed=7 + j, size=(7.0, 20.0), drop=(14.0, 60.0))), wx, wy, wh + 3.0,
               yaw=f.Y(yw), mat=ice, solid=False)
    f.box("RoofVent_" + tag, -2650, -700, wh + 90, 120, 120, 120, mat=steel)
    f.box("RoofVentCap", -2650, -700, wh + 156, 150, 150, 10, mat=steel_l, solid=False)
    f.tube("Chimney", (-2250, -520, wh + 30), (-2250, -520, wh + 230), 34, steel_l)
    f.tube("ChimneyCap", (-2250, -520, wh + 230), (-2250, -520, wh + 244), 56, steel)
    f.tube("Aerial", (-2400, -900, wh + 30), (-2400, -900, wh + 420), 5, steel_l)
    f.tube("AerialArm", (-2440, -900, wh + 360), (-2360, -900, wh + 360), 4, steel_l)
    f.tube("AerialArm", (-2430, -900, wh + 300), (-2370, -900, wh + 300), 4, steel_l)
    # corner posts, door frame with an open door, windows with frames
    for (cx_, cy_) in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)):
        f.box("CornerPost", cx_, cy_, wh / 2, 16, 16, wh + 2, mat=trim, solid=False)
    f.box("DoorFrame", x1 + 2, ym - 150, 90, 8, 12, 180, mat=trim, solid=False)
    f.box("DoorFrame", x1 + 2, ym + 150, 90, 8, 12, 180, mat=trim, solid=False)
    f.box("DoorFrame", x1 + 2, ym, 186, 8, 312, 12, mat=trim, solid=False)
    f.box("DoorLeaf", x1 + 40, ym - 160, 90, 130, 8, 176, yaw=-80, mat=wood_dark, solid=False)
    for (wx, wy, wyaw, wsx, wsy) in [(x0 + 150, y0 - 3, 0, 150, 6), (x0 + 450, y0 - 3, 0, 150, 6), (x0 + 150, y1 + 3, 0, 150, 6),
                                     (x0 + 450, y1 + 3, 0, 150, 6), (x0 - 3, ym, 0, 6, 160)]:
        f.box("WindowPane", wx, wy, 125, wsx, wsy, 76, mat=pane_glow, solid=False)
        f.box("WindowFrameH", wx, wy, 125, wsx + 12 if wsx > 10 else wsx + 4, wsy + 4 if wsx > 10 else wsy + 12, 6, mat=trim, solid=False)
        f.box("WindowSill", wx, wy, 82, wsx + 20 if wsx > 10 else wsx + 8, wsy + 8 if wsx > 10 else wsy + 20, 6, mat=trim, solid=False)
    f.light("HutLamp_" + tag, (x0 + x1) / 2, ym, 150, WARM, 45.0, 700.0)
    f.light("HutPorch_" + tag, x1 + 140, ym, 230, WARM, 35.0, 600.0)
    f.box("PorchBulb", x1 + 12, ym + 100, 215, 14, 14, 14, mat=bulb, solid=False)
    # clutter around
    f.prop("HutCratesA_" + tag, "crate_wood_b", x1 + 120, y1 + 200, 0, yaw=25, scale=2.4, solid=True)
    f.prop("HutCratesB_" + tag, "crate_wood_a", x1 + 140, y1 + 190, 52, yaw=-10, scale=2.4, solid=False)
    f.prop("HutBarrel_" + tag, "barrel_wood_a", x1 + 60, y0 - 100, 0, scale=1.0, solid=False)
    f.prop("HutGenerator_" + tag, "generator", x0 + 200, y0 - 90, 0, yaw=0, scale=2.2, solid=True)
    f.prop("HutJerry_" + tag, "jerrycan", x0 + 330, y0 - 70, 0, yaw=60, scale=1.6, solid=False)
    f.prop("InsideCrate_" + tag, "crate_wood_a", x0 + 100, ym + 180, 0, yaw=15, scale=2.4, solid=False)
    f.prop("InsideBarrel_" + tag, "barrel_wood_b", x0 + 90, ym - 170, 0, scale=0.9, solid=False)
    # ramp to the roof with side rails
    f.slope("HutRamp_" + tag, (-2450, 420, 0), (-2450, -380, wh + 30), 220, thickness=50, mat=wood_br)
    for s in (-1, 1):
        f.railing("HutRampRail", (-2450 + s * 108, 420, 0), (-2450 + s * 108, -380, wh + 30), height=90, post_every=220, mat=trim, rails=2)


hut(Frame(m, 0), red_corr, white_wood, "W")
hut(Frame(m, 2), blue_corr, white_wood, "E")


# pitched-roof cabins (solid blocks, ridge along local x, door on the +x gable)
def cabin(f, tag, walls=log, roof=roof_sl):
    L, W, WH = 520.0, 400.0, 220.0
    f.box("CabinWalls_" + tag, 0, 0, WH / 2, L, W, WH, mat=walls)
    for sy in (-1, 1):                                                   # roof planes at 45 degrees, with snow on top
        f.beam("CabinRoof_" + tag, (0, sy * (W / 2 + 42), WH - 40), (0, 0, WH + W / 2 + 6), L + 70, 14, mat=roof)
        f.beam("CabinSnow_" + tag, (0, sy * (W / 2 + 36), WH - 30), (0, sy * 8, WH + W / 2 + 14), L + 50, 9, mat=snow)
    f.box("CabinRidge", 0, 0, WH + W / 2 + 14, L + 70, 26, 14, mat=snow, solid=False)
    for sx in (-1, 1):
        wx = sx * (L / 2 - 8)
        wpos = f.P(wx, 0)
        diamond(m, "CabinGable_" + tag, wpos[0], wpos[1], WH, 16, (W + 84) / math.sqrt(2.0), mat=walls,
                along="x" if f.k % 2 == 0 else "y")
    # door, window, step, chimney
    f.box("CabinDoor", L / 2 + 3, 0, 95, 6, 100, 190, mat=wood_dark, solid=False)
    f.box("CabinDoorFrame", L / 2 + 4, -58, 100, 6, 14, 200, mat=white_wood, solid=False)
    f.box("CabinDoorFrame", L / 2 + 4, 58, 100, 6, 14, 200, mat=white_wood, solid=False)
    f.box("CabinDoorFrame", L / 2 + 4, 0, 198, 6, 130, 14, mat=white_wood, solid=False)
    f.box("CabinStep", L / 2 + 50, 0, 10, 90, 150, 20, mat=wood_br, solid=False)
    for sy in (-1, 1):
        f.box("CabinPane", 0, sy * (W / 2 + 3), 130, 110, 6, 70, mat=pane_glow, solid=False)
        f.box("CabinPaneFrame", 0, sy * (W / 2 + 3), 130, 124, 4, 84, mat=white_wood, solid=False)
    f.tube("CabinChimney", (-150, 80, WH + 130), (-150, 80, WH + 330), 36, steel_l)
    f.box("CabinChimneyCap", -150, 80, WH + 336, 60, 60, 10, mat=steel, solid=False)
    f.light("CabinLight_" + tag, L / 2 + 120, 0, 190, WARM, 35.0, 650.0)
    f.prop("CabinBarrel_" + tag, "barrel_red", L / 2 + 30, 110, 0, scale=1.0, solid=False)
    f.prop("CabinLogs_" + tag, "stump_a", -L / 2 - 80, -90, 0, scale=1.0, solid=False)


cabin(Frame(m, 0, -1900.0, -1650.0), "SW")
cabin(Frame(m, 2, 1900.0, 1750.0), "NE")

# ------------------------------------------------------------------------------------------------ ice tunnels
timber = wood_old


def tunnel(f, tag):
    x0, x1, y0, y1 = -2900.0, -1700.0, 1150.0, 1850.0
    for ay in (y0 + 50, y1 - 50):
        f.box("TunnelWall_" + tag, (x0 + x1) / 2, ay, 200, x1 - x0, 100, 400, mat=ice)
    f.box("TunnelRoof_" + tag, (x0 + x1) / 2, (y0 + y1) / 2, 430, x1 - x0, y1 - y0, 60, mat=snow)
    f.box("TunnelRoofUnder_" + tag, (x0 + x1) / 2, (y0 + y1) / 2, 398, x1 - x0 - 100, y1 - y0 - 100, 6, mat=ice_deep,
          solid=False)
    # timber frames inside, lanterns and icicles
    for i in range(4):
        cx = x0 + 250 + i * 330
        for ay in (y0 + 108, y1 - 108):
            f.box("TunnelPost", cx, ay, 195, 16, 16, 390, mat=timber, solid=False)
        f.box("TunnelHeader", cx, (y0 + y1) / 2, 392, 16, 500, 16, mat=timber, solid=False)
    for i in range(3):
        f.light("TunnelLight_%s%d" % (tag, i), x0 + 420 + i * 400, (y0 + y1) / 2, 330, WARM, 28.0, 650.0)
        f.box("TunnelBulb", x0 + 420 + i * 400, (y0 + y1) / 2, 350, 12, 12, 12, mat=bulb, solid=False)
    for i in range(10):
        px, py = x0 + 100 + i * 110, (y0 + y1) / 2 + rng.uniform(-180, 180)
        f.cone("Icicle_" + tag, px, py, 345 - rng.uniform(0, 30), 400, rng.uniform(16, 30), mat=ice, solid=False)
    f.prop("TunnelRock_" + tag, "rock_boulder_s", x0 - 60, y0 - 20, 0, scale=1.6, material=grock, solid=False)
    f.prop("TunnelRock2_" + tag, "rock_boulder_s", x1 + 50, y1 + 10, 0, scale=1.4, material=grock, solid=False)
    f.prop("TunnelCrate_" + tag, "crate_wood_a", x0 + 140, y0 + 150, 0, yaw=20, scale=2.0, solid=False)


tunnel(Frame(m, 0), "NW")
tunnel(Frame(m, 2), "SE")

# ------------------------------------------------------------------------------------------------ trees, ice formations, boulders
for i, (x, y) in enumerate([(-1500, -1500), (-900, -1700), (1500, 1500), (900, 1700), (-2900, 250), (2900, -250), (-300, 1800),
                            (300, -1800), (1700, -1500), (-1700, 1450), (2500, 1500), (-2500, -1550)]):
    if not free(x, y, 60.0):
        continue
    m.prop("Fir_%d" % i, "fir_a", x, y, 0, yaw=rng.uniform(0, 360), scale=rng.uniform(1.3, 1.8))
    snow_patch("FirSnow_%d" % i, x, y, 4, 260, 260, sz=10)

for i, (x, y) in enumerate([(-1250, 1000), (1250, -1000), (-1100, -1150), (1100, 1150), (0, 2000), (0, -2000), (2400, 0),
                            (-2400, 0)]):
    sc = rng.uniform(1.3, 1.9)
    m.prop("IceFormation_%d" % i, "cliff_b", x, y, 0, yaw=rng.uniform(0, 360), scale=sc, material=ice_deep if i % 2 else ice,
           sink=0.05)
    snow_patch("IceBank_%d" % i, x, y, 6, 420, 320, sz=18, mat=snow)

for i in range(8):
    x, y = rng.uniform(-2600, 2600), rng.uniform(-1700, 1700)
    if (abs(x) < 1500 and abs(y) < 800) or not free(x, y, 160.0):
        continue
    if abs(x) > 2000 and abs(y) > 1100 and x < 0 < y:      # keep clear of the tunnel
        continue
    m.prop("Boulder_%d" % i, "rock_boulder_l", x, y, 0, yaw=rng.uniform(0, 360), scale=rng.uniform(0.7, 1.0), material=grock,
           sink=0.1)
    snow_patch("BoulderSnow_%d" % i, x, y, 90, 150, 110, sz=12)

for i, (x, y, yaw) in enumerate([(-600, -1750, 20), (700, 1500, 110), (1900, -300, 70), (-1900, 600, 160)]):
    if free(x, y, 120.0):
        m.prop("DeadTrunk_%d" % i, "trunk_dead_b", x, y, 0, yaw=yaw, scale=1.0, solid=False)

# fuel drums, fire pit, lamps, fences, supplies around the huts
for i, (x, y) in enumerate([(-2350, -1150), (2350, 1150), (-1500, 1300), (1500, -1300)]):
    m.prop("Drum_%d" % i, "barrel_red" if i % 2 else "barrel_fire", x, y, 0, scale=1.0, solid=True)
    m.prop("Drum2_%d" % i, "barrel_red", x + 80, y + 20, 0, scale=1.0, solid=True, yaw=40)
for x, y in ((-1500, 1300), (1500, -1300)):
    m.prop("Propane", "propane_tank", x - 100, y - 20, 0, scale=1.8, solid=False)
m.prop("FirePit", "fire_pit", -2450, -1450, 0, scale=1.1, solid=False)
m.accent_light("FireLight", (-2450, -1450, 80), (1.0, 0.5, 0.18), 45.0, 700.0)
m.prop("FirePitE", "fire_pit", 2450, 1450, 0, scale=1.1, solid=False)
m.accent_light("FireLightE", (2450, 1450, 80), (1.0, 0.5, 0.18), 45.0, 700.0)
for (x, y, yaw) in [(-2300, -1800, 0), (-2100, -1800, 0), (2300, 1850, 0), (2100, 1850, 0)]:
    m.prop("Fence", "fence_b", x, y, 0, yaw=yaw, scale=0.9, solid=False)
for (x, y) in [(-2000, -300), (2000, 300)]:
    m.prop("LampPost", "lamp_street_b", x, y, 0, yaw=0, scale=1.0, solid=False)
    m.accent_light("LampPostLight", (x, y, 150), WARM, 55.0, 800.0)

# forest outside the walls (not walkable): firs in groves on the outer plain
fir_regions = [("rect", -6500, 2850, 6500, 6200), ("rect", -6500, -6200, 6500, -2850), ("rect", 3650, -2800, 7000, 2800),
               ("rect", -7000, -2800, -3650, 2800)]
for j, region in enumerate(fir_regions):
    m.scatter(["fir_a"], region, 18, seed=30 + j, scale=(1.4, 2.4), min_gap=200.0, ground=False, z=-5.0, solid=False,
              label="Forest%d" % j, sink=0.02)

# ------------------------------------------------------------------------------------------------ keep the starts out of each other's sight
def _sees(a, b):
    return not m._trace((a[0], a[1], a[2] + 170), (b[0], b[1], b[2] + 170))[0]


placed_cover = 0
for rnd in range(4):
    pairs = [(i, j) for i in range(len(STARTS)) for j in range(i + 1, len(STARTS)) if _sees(STARTS[i], STARTS[j])]
    unreal.log("GLACIER_LOS round %d: %d pairs in sight" % (rnd, len(pairs)))
    if not pairs or placed_cover >= 16:
        break
    for (i, j) in pairs:
        a, b = STARTS[i], STARTS[j]
        if not _sees(a, b):
            continue
        for t in (0.5, 0.4, 0.6, 0.3, 0.7, 0.45, 0.55, 0.35, 0.65):
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if abs(x) < 1250 and abs(y) < 760:
                continue
            if x < -1650 and y > 1000 or x > 1650 and y < -1000:         # tunnels
                continue
            if x < -1900 and -1100 < y < -300 or x > 1900 and 300 < y < 1100:  # huts
                continue
            if abs(x) > 3000 or abs(y) > 2000 or not free(x, y, 260.0):
                continue
            g = m.ground_at(x, y)
            if g is None or abs(g[0]) > 5:
                continue
            m.prop("LosRock_%d" % placed_cover, "rock_boulder_l", x, y, 0, yaw=rng.uniform(0, 360), scale=rng.uniform(0.9, 1.15),
                   material=grock, sink=0.1)
            snow_patch("LosRockSnow_%d" % placed_cover, x, y, 95, 160, 120, sz=12)
            placed_cover += 1
            break

# ------------------------------------------------------------------------------------------------ spawns
m.face_center_starts(STARTS)
m.check_starts()
m.fog(density=0.0022)
m.finish(kill_z=-1500)
