"""DM-Canyon: a desert canyon with a river ravine, rope bridges, two high mesas and rock spires. 8-10 bots.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_canyon.py" -unattended -nullrhi -nosplash

Gameplay layout (unchanged): x is the long axis. Two canyon floors (z = 0) north and south of a ravine (kill height below), three bridges
across it, a mesa at each end (z = 450) reached by long ramps, four rock spires beside the mesas joined to them by plank bridges, jump pads
on the floors that throw players up to the spire tops. Falling into the ravine kills. The 12 player starts are the old positions.

Visuals (this version): the walls of the canyon, the ravine and the mesas are layered cliffs generated as meshes (hard and soft strata in
several rock surfaces, buttresses, cracks, ragged rim); the old boxes stay as invisible collision. Terraced buttes and rock pillars,
sand dunes, dirt and gravel patches, real rock / dead tree / dry bush props, wooden rope bridges with separate boards, rope rails and
posts, canvas tents with crates and barrels, a river with boulders in the ravine, craggy distant mesas in the haze.
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
import mapkit_b as kb  # noqa: E402
import mesh_b as mb  # noqa: E402
import mesh_arch_b as ma  # noqa: E402
import mesh_misc_b as mm  # noqa: E402
import mesh_nat_n as nn  # noqa: E402
from matlib import surface, water  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Canyon")
rng = random.Random(23)

# ---------------------------------------------------------------- surfaces
sand_m = surface("Sand", tiling=6.0, albedo=(190, 148, 98), macro=0.45, macro_m=22.0, tag="CSand3")
sand2_m = surface("Sand", tiling=4.0, albedo=(206, 166, 112), macro=0.4, macro_m=14.0, tag="CSand4")
dirt_m = surface("DirtRed", tiling=4.0, albedo=(150, 92, 58), tag="CDirt")
dry_m = surface("DirtDry", tiling=3.0, albedo=(146, 118, 88), tag="CDry")
gravel_m = surface("Gravel", tiling=2.5, albedo=(150, 128, 104), tag="CGravel")
mud_m = surface("AsphaltCracked", tiling=2.4, albedo=(198, 158, 116), ns=1.2, tag="CMudCrack2")   # dry riverbed: cracked clay
path_m = surface("DirtDry", tiling=3.0, albedo=(170, 128, 92), tag="CPath2")                     # worn, compacted trail
top_m = surface("DirtDry", tiling=5.0, albedo=(160, 120, 84), tag="CTop")
# rock: more relief (normal strength), blotchy macro colour so a band is not one flat tint; the pale band is a warm
# sandstone, not cream paper
rock_red = surface("RockCanyonRed", tiling=6.0, ns=1.4, macro=0.5, macro_m=6.0, tag="CRed2")
rock_pale = surface("SandstoneRough", tiling=3.6, albedo=(206, 146, 98), ns=1.7, macro=0.3, macro_m=5.0, tag="CPale4")
rock_cliff = surface("RockCliff", tiling=6.0, albedo=(148, 104, 76), ns=1.4, macro=0.5, macro_m=7.0, tag="CCliff2")
rock_sr = surface("RockCliff", tiling=6.0, albedo=(172, 98, 64), ns=1.4, macro=0.5, macro_m=6.0, tag="CSR2")
rock_dark = surface("RockCliff", tiling=6.0, albedo=(88, 60, 46), ns=1.4, macro=0.5, macro_m=7.0, tag="CDark2")
rock_rough = surface("SandstoneRough", tiling=4.5, albedo=(196, 138, 92), ns=1.5, macro=0.4, macro_m=5.0, tag="CRough3")
talus_m = surface("StoneRubble", tiling=3.0, albedo=(138, 104, 80), ns=1.4, tag="CTalus")
far_red = surface("RockCanyonRed", tiling=60.0, albedo=(160, 92, 66), tag="CFarRed")
far_pale = surface("RockCanyonPale", tiling=60.0, albedo=(196, 150, 116), tag="CFarPale")
wood_m = surface("WoodBridge", tiling=1.5, tag="CWood")
wood_old = surface("WoodPlanksOld", tiling=1.5, albedo=(120, 104, 86), tag="CWoodOld")
wood_dark = surface("WoodPlanksDark", tiling=1.5, albedo=(80, 58, 42), tag="CWoodDark")
rope_m = surface("Rope", tiling=0.5, tag="CRope")
canvas_m = surface("Canvas", tiling=1.5, albedo=(170, 150, 112), tag="CCanvas")
canvas_red = surface("CanvasRed", tiling=1.5, albedo=(138, 66, 52), tag="CCanvasR")
canvas_blue = surface("CanvasBlue", tiling=1.5, albedo=(70, 92, 112), tag="CCanvasB")
water_m = water()
bush_m = kb.prop_variant("shrub_a", (1.7, 1.25, 0.55), "ScrubKhaki")
trunk_m = kb.prop_variant("trunk_quiver", (0.75, 0.5, 0.32), "TrunkWarm")
STRATA_MATS = [rock_red, rock_pale, rock_cliff, rock_sr, rock_dark, rock_pale, rock_red, rock_rough]

FX, FY = 3000.0, 2400.0
RAV = 350.0
MESA_Z = 450.0
MESA_CX = FX + 700.0


def hide(actor):
    """Keeps the collision (the old gameplay box) but does not draw it: a generated cliff mesh stands in front of it."""
    actor.set_actor_hidden_in_game(True)
    return actor


def smooth(a, b, x):
    return mb.smoothstep(a, b, x)


# ---------------------------------------------------------------- gameplay collision (invisible where a mesh replaces it)
m.box("Floor_N", 0, (RAV + FY) / 2, -400, FX * 2, FY - RAV, 800, mat=sand_m)
m.box("Floor_S", 0, -(RAV + FY) / 2, -400, FX * 2, FY - RAV, 800, mat=sand_m)
for sx in (-1, 1):
    tag = "W" if sx < 0 else "E"
    hide(m.box("Mesa_" + tag, sx * MESA_CX, 0, MESA_Z / 2 - 400, 1400, FY * 2 + 400, MESA_Z + 800, mat=rock_red))
    hide(m.box("MesaBack_" + tag, sx * (FX + 1500), 0, 800, 200, FY * 2 + 800, 2400, mat=rock_red))
    m.box("MesaTop_" + tag, sx * MESA_CX, 0, MESA_Z + 0.6, 1396, FY * 2 + 200, 1.0, mat=top_m, solid=False)
for sy in (-1, 1):
    hide(m.box("CanyonWall", 0, sy * (FY + 250), 700, (FX + 1500) * 2, 500, 2200, mat=rock_red))

# ---------------------------------------------------------------- cliffs: walls, ravine faces, mesa faces
# Every strip is one mesh between two WAVY strata boundaries (shared with the neighbour strip), so no seam is a straight line.
# The face carries relief at several scales: strata (hard layers with lips, soft layers receding), big buttresses, jointed
# blocks, vertical erosion flutes and fine chips.
CLIFF = {}        # label -> dict(lay, off, org, yaw, n) for placing talus and rim rocks afterwards


def make_off(seed, mode, lay, g=0.0):
    def off(u, z):
        h = z - g
        raw = (lay.profile(u, z, 120.0) + 470.0 * mb.fbm(u / 1300.0 + seed * 0.37, h / 1700.0, 0.0, 3, seed)
               + 120.0 * mb.fbm(u / 300.0, h / 260.0, 0.0, 3, seed + 5) - 170.0 * mb.ridged(u / 700.0, h / 5000.0, 0.0, 2, seed + 9)
               - 110.0 * mb.ridged(u / 230.0, h / 3500.0, 0.0, 2, seed + 13)
               + 85.0 * mb.fbm(u / 95.0, h / 70.0, 0.0, 2, seed + 17) + 58.0 * nn.plateau(u, h, 170.0, 95.0, seed + 21)
               - 60.0 * mb.ridged(u / 150.0, h / 2300.0, 0.0, 2, seed + 23))
        v = max(3.0, raw + 200.0)
        if mode == "wall":
            v = min(v * (0.42 + 0.58 * smooth(150.0, 900.0, h)), 55.0 + 900.0 * smooth(100.0, 650.0, h))
        elif mode == "mesa":
            v = min(v * (0.25 + 0.50 * smooth(100.0, 450.0, h)) * (1.0 - smooth(MESA_Z - 120.0, MESA_Z - 8.0, z)), 45.0 + 600.0 * smooth(60.0, 400.0, h))
        else:                                              # ravine: no bulge at the lip, growing downwards
            v = v * smooth(0.0, 160.0, -z) * 0.9
        return v
    return off


def rim_fn(seed, amp=700.0):
    """Ragged skyline: broad swells, notches and teeth (cm, mostly negative)."""
    return lambda u: (amp * (0.55 * mb.fbm(u / 1800.0 + seed, 0.3, 0.0, 2, seed + 31) + 0.45 * mb.fbm(u / 470.0 + seed, 1.7, 0.0, 2, seed + 37)
                             + 0.3 * (mb.ridged(u / 650.0 + seed, 0.5, 0.0, 2, seed + 7) - 0.5)) - 0.75 * amp)


def hills_fn(seed):
    return lambda u, y: 240.0 * mb.fbm(u / 650.0 + seed, y / 380.0, 0.0, 3, seed + 55) + 110.0 * mb.ridged(u / 240.0, y / 190.0, 0.0, 2, seed + 57)


def wall_strips(label, org, yaw, width, zs, mats, seed, mode, g=0.0, rim_amp=None, depth=900.0, wob=45.0):
    rim = rim_fn(seed, rim_amp) if rim_amp else None
    lay = nn.Layers(zs, seed, wob=wob, rim=rim, rim_from=zs[0] + (zs[-1] - zs[0]) * 0.38 if rim else None)
    off = make_off(seed, mode, lay, g)
    n = len(zs) - 1
    for k in range(n):
        top = k == n - 1
        zt = zs[k + 1]
        cell = 55.0 if zt < 1200.0 else (65.0 if zt < 1800.0 else 100.0)
        if mode != "wall":
            cell = 70.0
        mesh = nn.cliff_strip2(width, lambda u, k=k: lay.boundary(k, u), lambda u, k=k: lay.boundary(k + 1, u), off, depth, cell=cell,
                               cap=bool(top and rim), cap_fn=hills_fn(seed) if (top and rim) else None, skirt_top=top and not rim)
        sm = kb.commit("C%s_%d" % (label, k), mesh, collision="none")
        kb.put(m, "Cliff_%s_%d" % (label, k), sm, org[0], org[1], 0.0, yaw=yaw, mat=mats[(k + len(label)) % len(mats)], solid=False, folder="Cliffs")
    CLIFF[label] = dict(lay=lay, off=off, org=org, yaw=yaw, n=n, width=width, g=g)
    gaps = min(lay.boundary(k + 1, u) - lay.boundary(k, u) for k in range(n) for u in range(0, int(width), 200))
    unreal.log("CLIFF %s min strip thickness %.0f cm" % (label, gaps))
    return lay


def local_to_world(c, u, y):
    """Cliff-local (u along the wall, y toward the rock mass) -> world x, y."""
    a = math.radians(c["yaw"])
    return c["org"][0] + u * math.cos(a) - y * math.sin(a), c["org"][1] + u * math.sin(a) + y * math.cos(a)


wall_strips("WallN", (-4800.0, FY), 0.0, 9600.0, [-60, 240, 520, 860, 1150, 1480, 1800, 2150, 2500, 2800], STRATA_MATS, 11, "wall", rim_amp=700.0)
wall_strips("WallS", (4800.0, -FY), 180.0, 9600.0, [-60, 240, 520, 860, 1150, 1480, 1800, 2150, 2500, 2800], STRATA_MATS[2:] + STRATA_MATS[:2], 12, "wall", rim_amp=700.0)
wall_strips("BackE", (FX + 1400.0, 2800.0), -90.0, 5600.0, [380, 700, 1150, 1650, 2200, 2800], STRATA_MATS, 13, "wall", g=MESA_Z, rim_amp=700.0)
wall_strips("BackW", (-FX - 1400.0, -2800.0), 90.0, 5600.0, [380, 700, 1150, 1650, 2200, 2800], STRATA_MATS[3:] + STRATA_MATS[:3], 14, "wall", g=MESA_Z, rim_amp=700.0)
wall_strips("MesaE", (FX, 2600.0), -90.0, 5200.0, [-800, -500, -200, 60, 250, MESA_Z - 2], [rock_dark, rock_red, rock_cliff, rock_pale, rock_sr], 15, "mesa", wob=30.0)
wall_strips("MesaW", (-FX, -2600.0), 90.0, 5200.0, [-800, -500, -200, 60, 250, MESA_Z - 2], [rock_dark, rock_cliff, rock_red, rock_sr, rock_pale], 16, "mesa", wob=30.0)
wall_strips("RavineN", (-FX, RAV), 0.0, FX * 2, [-800, -560, -340, -160, -2], [rock_dark, rock_red, rock_pale, rock_cliff], 17, "ravine", wob=25.0)
wall_strips("RavineS", (FX, -RAV), 180.0, FX * 2, [-800, -560, -340, -160, -2], [rock_dark, rock_cliff, rock_pale, rock_red], 18, "ravine", wob=25.0)

# ---- talus: the debris slope at the foot of the big walls, with boulder piles on it
PILE_SM = [kb.commit("CPile_%d" % i, nn.rock_pile(200 + i, count=6 + i % 3, spread=170.0, size=(40.0, 120.0), height_k=0.75, bedding=0.07)) for i in range(6)]
for label, base_z in (("WallN", 0.0), ("WallS", 0.0), ("BackE", MESA_Z), ("BackW", MESA_Z)):
    c = CLIFF[label]
    sd = 70 + len(label) * 3 + int(base_z)
    off = c["off"]
    sk = nn.talus_skirt(c["width"], lambda u, sd=sd: 95.0 + 55.0 * mb.fbm(u / 260.0, 1.0, 0.0, 2, sd), lambda u, sd=sd: 100.0 + 60.0 * mb.fbm(u / 330.0, 5.0, 0.0, 2, sd + 1),
                        cell=60.0, face_fn=lambda u, off=off, c=c: -off(u, c["g"] + 40.0) + 8.0, seed=sd)
    kb.put(m, "Talus_" + label, kb.commit("CTalus_" + label, sk, collision="none"), c["org"][0], c["org"][1], base_z, yaw=c["yaw"], mat=talus_m, solid=False, folder="Cliffs")
    # boulder piles standing on it (several shapes, rotated and scaled)
    wmats = [rock_cliff, rock_rough, rock_red, talus_m, rock_pale, rock_dark]
    for i in range(30 if label in ("WallN", "WallS") else 14):
        u = rng.uniform(150.0, c["width"] - 150.0)
        yl = -off(u, c["g"] + 40.0) - rng.uniform(15.0, 90.0)
        wx, wy = local_to_world(c, u, yl)
        sc = rng.uniform(0.8, 1.7)
        kb.put(m, "TalusPile_%s_%d" % (label, i), PILE_SM[i % 6],
               wx, wy, base_z - 6.0, yaw=rng.uniform(0, 360), scale=(sc, sc * rng.uniform(0.8, 1.2), sc * rng.uniform(0.7, 1.1)), mat=wmats[i % 6], solid=False, folder="Cliffs")

# ---- pinnacles, hoodoos and buttes on the skyline
PIN_SM = [kb.commit("CPin_%d" % k, nn.pinnacle_mesh(rng.uniform(700.0, 1300.0), rng.uniform(95.0, 170.0), seed=300 + k, mush=(0.0, 0.0, 0.45, 0.0, 0.5, 0.0, 0.0, 0.4)[k]))
          for k in range(8)]
for label, count in (("WallN", 15), ("WallS", 15), ("BackE", 7), ("BackW", 7)):
    c = CLIFF[label]
    lay = c["lay"]
    for i in range(count):
        u = (i + rng.uniform(0.1, 0.9)) * c["width"] / count
        yl = rng.uniform(30.0, 720.0)
        zr = lay.boundary(c["n"], u) + 60.0 * mb.fbm(u / 300.0, yl / 300.0, 0.0, 2, 5) - 120.0
        wx, wy = local_to_world(c, u, yl)
        sx_ = rng.uniform(0.9, 1.8)
        kb.put(m, "Pinnacle_%s_%d" % (label, i), PIN_SM[i % 8], wx, wy, zr - 220.0, yaw=rng.uniform(0, 360),
               scale=(sx_, sx_ * rng.uniform(0.85, 1.15), rng.uniform(0.75, 1.5)), mat=STRATA_MATS[(i * 3 + len(label)) % 8], solid=False, folder="Cliffs")

# the ravine floor: a dark bed, the river and boulders
m.box("RiverBed", 0, 0, -770, FX * 2 + 200, RAV * 2 + 300, 30, mat=rock_dark, solid=False)
m.box("River", 0, 0, -682, FX * 2, RAV * 2 - 120, 4, mat=water_m, solid=False)

# ---------------------------------------------------------------- floors: dunes with wind ripples, mud flats, trails
def dune(label, x, y, sx, sy, hmax, seed, yaw=0.0, mat=None):
    def h(px, py):
        u, v = px / (sx / 2.0), py / (sy / 2.0)
        env = max(0.0, 1.0 - (u * u + v * v)) ** 1.5
        rip = 0.9 + 0.1 * mb.fbm(px / 120.0, py / 120.0, 0.0, 3, seed)
        wave = math.sin((px * 0.94 + py * 0.34) / 52.0 + 2.5 * mb.fbm(px / 260.0, py / 260.0, 0.0, 2, seed + 4))   # wind ripples
        return -6.0 + (hmax + 6.0) * env * rip + 1.3 * wave * env ** 0.6
    sm = kb.commit("CDune2_%s" % label, ma.heightfield(-sx / 2.0, -sy / 2.0, sx / 2.0, sy / 2.0, 60.0, h, floor_z=-30.0))
    kb.put(m, "Dune_" + label, sm, x, y, 0.0, yaw=yaw, mat=mat or sand_m)


STARTS = [(-2100, 700, 0, -18), (-4300, -100, 450, 1), (-2700, -1900, 0, 35), (-3300, 1900, 450, -30), (2900, 2100, 0, -144), (-900, -1900, 0, 65),
          (4100, 1100, 450, -165), (100, 500, 0, -101), (-100, 2300, 0, -88), (-2500, 1900, 0, -37), (2500, -1700, 0, 146), (1500, 1500, 0, -135)]
PADS = [(sx * (FX - 550.0 - 1100.0), sy * 900.0) for sx in (-1, 1) for sy in (-1, 1)]
ROCKS = [(-2200, 1300, 600, 380, 440), (-1000, 1900, 420, 520, 300), (800, 1500, 500, 420, 520), (900, 2050, 380, 400, 380),
         (-1800, -950, 520, 400, 420), (-600, -1500, 480, 520, 330), (1100, -1900, 430, 380, 480), (2200, -850, 520, 460, 400),
         (0, 900, 300, 300, 260), (0, -900, 300, 300, 260), (-1300, 700, 260, 260, 220), (1400, -700, 260, 260, 220)]
keep_clear = [(x, y, 380.0) for x, y, z, _ in STARTS if z == 0] + [(x, y, 520.0) for x, y in PADS] + [(x, y, max(sx_, sy_) / 2.0 + 260.0) for x, y, sx_, sy_, _ in ROCKS]
for i, (x, y, sx_, sy_, hm, yw, mt) in enumerate([
        (-1500, 1050, 800, 440, 36, 20, sand2_m), (300, 1700, 900, 460, 40, -10, sand2_m), (1900, 600, 700, 400, 34, 35, sand2_m),
        (-700, -700, 760, 420, 34, -25, sand2_m), (1100, -1250, 800, 420, 38, 15, sand2_m), (-2700, -400, 600, 380, 30, 0, sand2_m),
        (400, 2150, 700, 300, 30, 0, sand2_m), (-1700, -2100, 800, 300, 34, 5, sand2_m), (2800, -700, 520, 360, 28, 40, sand2_m)]):
    if any(math.hypot(x - cx, y - cy) < cr + max(sx_, sy_) * 0.35 for cx, cy, cr in keep_clear):
        continue
    dune("%d" % i, x, y, sx_, sy_, hm, 3 + i, yw, sand_m)

# ground patches with irregular outlines (they cross the floor where the noisy surface crosses z = 0): cracked mud near the
# riverbed, dirt, gravel, worn trails from the bridge ends. They have no collision.
PATCH_SHAPES = [(600, 420), (780, 360), (500, 500), (900, 300), (420, 320), (700, 480)]
PATCH_SM = {}
for kind, peak in (("mud", 2.5), ("dirt", 4.0), ("gravel", 5.0), ("rough", 3.0)):
    for k, (psx, psy) in enumerate(PATCH_SHAPES):
        PATCH_SM[(kind, k)] = kb.commit("CPatch_%s_%d" % (kind, k), nn.patch_mesh(psx, psy, seed=500 + k * 7 + len(kind), peak=peak))
TRAIL_SM = [kb.commit("CTrail_%d" % k, nn.patch_mesh(lx, ly, seed=700 + k, peak=3.5, cell=40.0, wobble=1.7)) for k, (lx, ly) in enumerate(((1100, 240), (800, 200), (1400, 280)))]
PATCH_MAT = {"mud": mud_m, "dirt": dirt_m, "gravel": gravel_m, "rough": dry_m}
for i in range(44):
    # most mud flats lie along the ravine, the rest anywhere on the floor
    if i < 18:
        x, y = rng.uniform(-FX + 300, FX - 300), rng.choice((-1, 1)) * rng.uniform(RAV + 150, RAV + 800)
        kind = "mud"
    else:
        x, y = rng.uniform(-FX + 100, FX - 100), rng.choice((-1, 1)) * rng.uniform(RAV + 120, FY - 100)
        kind = ("dirt", "gravel", "rough", "dirt", "mud")[i % 5]
    sc = rng.uniform(0.8, 1.5)
    kb.put(m, "Patch_%d" % i, PATCH_SM[(kind, i % 6)], x, y, 0.0, yaw=rng.uniform(0, 180), scale=(sc, sc * rng.uniform(0.8, 1.2), 1.0), mat=PATCH_MAT[kind], solid=False,
           folder="Ground")
for bx in (-2000.0, 0.0, 2000.0):                           # worn trails leading away from the bridge ends
    for sy in (-1, 1):
        kb.put(m, "Trail_%d_%d" % (bx, sy), TRAIL_SM[int(abs(bx) / 1000) % 3], bx + rng.uniform(-30, 30), sy * (RAV + 600.0), 0.0, yaw=90.0 + rng.uniform(-8, 8), mat=path_m,
               solid=False, folder="Ground")
for (x0, y0, x1, y1) in ((-2100, 700, -900, 1500), (900, 1500, 1500, 2300), (-1800, -1800, -700, -900)):   # a few trails between the spawn areas
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    kb.put(m, "Trail_%d_%d" % (x0, y0), TRAIL_SM[2], (x0 + x1) / 2.0, (y0 + y1) / 2.0, 0.0, yaw=ang, scale=(1.0, 1.0, 1.0), mat=path_m, solid=False, folder="Ground")
for sx in (-1, 1):
    for i in range(18):
        x, y = sx * MESA_CX + rng.uniform(-620, 620), rng.uniform(-2200, 2200)
        kind = ("gravel", "rough", "dirt")[i % 3]
        sc = rng.uniform(0.7, 1.3)
        kb.put(m, "MesaPatch_%d_%d" % (sx, i), PATCH_SM[(kind, i % 6)], x, y, MESA_Z + 0.6, yaw=rng.uniform(0, 180), scale=(sc, sc * rng.uniform(0.8, 1.2), 1.0),
               mat=PATCH_MAT[kind], solid=False, folder="Ground")

# ---------------------------------------------------------------- ramps to the mesas (solid wedges, same slope as before)
for sx in (-1, 1):
    for sy in (-1, 1):
        sm = kb.commit("CRampWedge", mm.ramp_wedge(FX - 1500.0, MESA_Z, 480.0))
        kb.put(m, "MesaRamp_%d_%d" % (sx, sy), sm, sx * 1500.0, sy * 1700.0, 0.0, yaw=0.0 if sx > 0 else 180.0, mat=dirt_m)
        for k in range(3):                                 # rubble on the sides of the ramp
            for side in (-1, 1):
                f = rng.uniform(0.1, 0.9)
                m.prop("RampRock_%d_%d_%d_%d" % (sx, sy, k, side), rng.choice(("rock_red_small_l", "rock_red_a_s", "rock_red_small_l")),
                       sx * (1500.0 + f * 1500.0), sy * 1700.0 + side * 262.0, MESA_Z * f, yaw=rng.uniform(0, 360), scale=rng.uniform(0.7, 1.1), solid=False)

# ---------------------------------------------------------------- rock spires, plank bridges to the mesas, jump pads
SPIRE_X = FX - 550.0
spire_zs = [-300.0, 60.0, 260.0, MESA_Z]
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * SPIRE_X, sy * 900.0
        seed = 40 + sx * 3 + sy

        def spire_r(th, t, z0=0.0, z1=1.0, seed=seed):
            z = z0 + (z1 - z0) * t
            base = 330.0 - 62.0 * (z + 300.0) / 750.0
            n = mb.fbm(math.cos(th) * 1.6 + seed, math.sin(th) * 1.6, z / 230.0, 3, seed)
            ledge = 14.0 * math.sin(z / 47.0 + seed)
            return (base + (n * 38.0 + ledge) * (1.0 - 0.85 * smooth(380.0, MESA_Z, z)))
        for k in range(3):
            z0, z1 = spire_zs[k], spire_zs[k + 1]
            seg = mb.Mesh()
            seg.lathe(0, 0, z0, z1, 1.0, 1.0, sides=40, segments=max(2, int((z1 - z0) / 45.0)), rfn=lambda th, t, z0=z0, z1=z1, seed=seed: spire_r(th, t, z0, z1, seed),
                      cap_bottom=False, cap_top=(k == 2))
            kb.put(m, "Spire_%d_%d_%d" % (sx, sy, k), kb.commit("CSpire_%d_%d_%d" % (sx, sy, k), seg), x, y, 0.0, yaw=0.0,
                   mat=(rock_red, rock_sr, rock_pale)[k])
        # plank bridge from the spire top to the mesa
        px = sx * (FX - 150.0)
        hide(m.box("SpirePlank", px, y, MESA_Z - 15, 520, 260, 30, mat=wood_m))
        kb.put(m, "SpirePlankDeck", kb.commit("CPlankDeck520", mm.plank_deck(520.0, 252.0, board=24.0, gap=3.0, seed=5, top=0.3)),
               px, y, MESA_Z, yaw=90.0, mat=wood_m, solid=False)
        for side in (-1, 1):
            m.box("SpireBeam", px, y + side * 118, MESA_Z - 26, 540, 14, 16, mat=wood_dark, solid=False)
            rope_pts = [(px + (i / 6.0 - 0.5) * 520.0 * 1.0, y + side * 133.0, MESA_Z + 55.0 - 6.0 * math.sin(math.pi * i / 6.0)) for i in range(7)]
            kb.put(m, "SpireRope", kb.commit("CSpireRope_%d_%d" % (sx * 10 + sy, side), mm.tube(rope_pts, 2.6, 6, 0.1, 3)), 0, 0, 0, mat=rope_m, solid=False)
            for t in (-1, 0, 1):
                m.box("SpirePost", px + t * 240, y + side * 133, MESA_Z + 28, 9, 9, 66, mat=wood_dark, solid=False)
        # pad on the floor that lands on the spire top
        pxx = sx * (SPIRE_X - 1100.0)
        m.jump_pad("SpirePad_%d_%d" % (sx, sy), pxx, y, 0, (x, y, MESA_Z), color=(1.0, 0.6, 0.15), apex_extra=140.0)
        m.column("PadStones", pxx, y, 0.0, 6.0, 430, mat=rock_dark, solid=False)
        m.column("PadStones2", pxx, y, 0.0, 9.0, 330, mat=gravel_m, solid=False)

# ---------------------------------------------------------------- the three rope bridges
for bx in (-2000.0, 0.0, 2000.0):
    wide = 520.0 if bx == 0 else 420.0
    hide(m.box("Bridge_%d" % bx, bx, 0, -20, wide, RAV * 2 + 100, 40, mat=wood_m))
    kb.put(m, "BridgeDeck_%d" % bx, kb.commit("CBridgeDeck_%d" % wide, mm.plank_deck(RAV * 2 + 100.0, wide - 8.0, board=27.0, gap=2.5, seed=int(wide), top=0.3)),
           bx, 0, 0.0, mat=wood_m, solid=False)
    for side in (-1, 1):                                    # stringers and cross beams under the boards
        m.box("Stringer", bx + side * (wide / 2 - 30), 0, -22, 26, RAV * 2 + 160, 30, mat=wood_dark, solid=False)
    for k in range(-3, 4):
        m.box("Crossbeam", bx, k * 118.0, -43, wide - 4, 18, 14, mat=wood_dark, solid=False)
    posts = mb.Mesh()
    rope_top = [[], []]
    rope_low = [[], []]
    ys = [-RAV - 20.0 + i * (2 * RAV + 40.0) / 6.0 for i in range(7)]
    for si, side in enumerate((-1, 1)):
        xr = side * (wide / 2.0 - 8.0)
        for i, yy in enumerate(ys):
            big = i in (0, 6)
            posts.box(xr, yy, 0, 20 if big else 11, 20 if big else 11, 150 if big else 108, base=True, jitter=0.5, seed=i * 7 + si, taper=0.15)
            rope_top[si].append((bx + xr, yy, 100.0 if not big else 138.0))
            rope_low[si].append((bx + xr, yy, 52.0))
    kb.put(m, "BridgePosts_%d" % bx, kb.commit("CBridgePosts_%d" % wide, posts), bx, 0, 0.0, mat=wood_dark, solid=False)
    for si in range(2):
        for nm, pts in (("T", rope_top[si]), ("L", rope_low[si])):
            curve = []
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                for s in range(4):
                    t = s / 4.0
                    curve.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t - 7.0 * math.sin(math.pi * t)))
            curve.append(pts[-1])
            kb.put(m, "BridgeRope_%d_%s%d" % (bx, nm, si), kb.commit("CBridgeRope_%d_%s%d" % (wide, nm, si), mm.tube([(p[0] - bx, p[1], p[2]) for p in curve], 2.8, 6, 0.1, si + 2)),
                   bx, 0, 0.0, mat=rope_m, solid=False)
    # banner poles at both ends of the bridge: muted cloth
    for sy2, cm in ((1, canvas_red), (-1, canvas_blue)):
        px, py = bx, sy2 * (RAV + 60.0)
        m.column("BannerPole", px, py, 0.0, 380.0, 12, mat=wood_dark, solid=False)
        kb.put(m, "Banner", kb.commit("CBanner", mm.cloth_mesh(110.0, 190.0, waves=2.2, amp=7.0, seed=2)), px + 62, py, 185.0, mat=cm, solid=False)

# ---------------------------------------------------------------- big rocks on the floors (terraced buttes) and natural arches
for i, (x, y, sx_, sy_, h) in enumerate(ROCKS):
    sm = kb.commit("CButte_%d" % (i % 4), mm.mesa_mesh(100.0, 100.0, seed=20 + i % 4, base_z=-8.0, sides=28, rings=12))
    kb.put(m, "Rock_%d" % i, sm, x, y, 0.0, yaw=rng.uniform(0, 360), scale=(sx_ / 200.0, sy_ / 200.0, (h + 8.0) / 108.0), mat=(rock_red, rock_pale, rock_cliff, rock_sr)[i % 4])
    for k in range(3):
        a = rng.uniform(0, 2 * math.pi)
        r = max(sx_, sy_) * 0.52
        m.prop("RockSkirt_%d_%d" % (i, k), rng.choice(("rock_red_a_s", "rock_red_b_s", "rock_red_small_l")), x + math.cos(a) * r, y + math.sin(a) * r, 0.0,
               yaw=rng.uniform(0, 360), scale=rng.uniform(0.8, 1.3), solid=False)

for ai, (x, y) in enumerate(((-1500, -1300), (1500, 1300))):
    arch = ma.arch_frame(440.0, 640.0, 250.0, tk=160.0, seed=9 + ai, segments=13)
    sm = kb.commit("CArch_%d" % ai, arch)
    kb.put(m, "Arch_%d" % ai, sm, x, y + 125.0, 0.0, yaw=0.0, mat=rock_sr)
    for side in (-1, 1):
        m.prop("ArchRock_%d_%d" % (ai, side), "rock_red_c_s", x + side * 360, y + rng.uniform(-80, 80), 0.0, yaw=rng.uniform(0, 360), scale=1.2, solid=False)

# ---------------------------------------------------------------- the mesas: ruined walls, tents, supplies
for sx in (-1, 1):
    cxm = sx * MESA_CX
    for i, (dx, dy, w, d, h) in enumerate([(-250, -1000, 400, 80, 200), (200, 900, 80, 400, 220), (0, 0, 300, 300, 160), (350, -300, 240, 100, 120), (-300, 450, 120, 240, 260)]):
        cx, cy = cxm + dx, dy
        if i == 2:
            # a chunky leaning rock block (same footprint and height as before) with rubble around it
            blk = mb.Mesh()
            blk.box(0, 0, 0, w, d, h, base=True, jitter=7.0, top_jitter=0.0, seed=100 + sx, taper=0.0)
            blk.box(0, 0, h, w - 40, d - 40, 1.0, base=True, jitter=0.0)
            kb.put(m, "MesaCover_%d_%d" % (sx, i), kb.commit("CMesaBlock2_%d" % (sx + 1), blk), cx, cy, MESA_Z, mat=rock_cliff)
            for k in range(4):
                a = k * 1.6 + rng.uniform(0, 1)
                m.prop("OutcropRock_%d_%d" % (sx, k), rng.choice(("rock_red_a_s", "rock_red_b_s", "rock_red_small_l")), cx + math.cos(a) * 190.0, cy + math.sin(a) * 190.0, MESA_Z,
                       yaw=rng.uniform(0, 360), scale=rng.uniform(0.8, 1.3), solid=False)
            continue
        along, thick = max(w, d), min(w, d)
        yaw = 0.0 if w >= d else 90.0
        prof = []
        x0 = 0.0
        while x0 < along - 1:
            step = min(rng.uniform(70, 150), along - x0)
            prof.append((x0, x0 + step, float(h - rng.choice((0, 0, 15, 30, 45)))))
            x0 += step
        ox, oy = cx - math.cos(math.radians(yaw)) * along / 2.0 + math.sin(math.radians(yaw)) * thick / 2.0, cy - math.sin(math.radians(yaw)) * along / 2.0 - math.cos(math.radians(yaw)) * thick / 2.0
        kb.put(m, "MesaCover_%d_%d" % (sx, i), kb.commit("CMesaWall_%d_%d" % (sx + 1, i), ma.wall_run(along, prof, thick, seed=i + 40 * (sx + 2), jitter=3.0)), ox, oy, MESA_Z,
               yaw=yaw, mat=rock_rough)
    # a tent with a table of supplies
    tx, ty = sx * (FX + 800.0), 1500.0
    kb.put(m, "Tent_%d" % sx, kb.commit("CTent", mm.tent_mesh(420.0, 320.0, 300.0, 0.5, seed=3)), tx, ty, MESA_Z, mat=canvas_m if sx > 0 else canvas_red, solid=False)
    for px_, py_ in ((-205, -155), (205, -155), (-205, 155), (205, 155)):
        m.column("TentPole", tx + px_, ty + py_, MESA_Z, MESA_Z + 150.0 + (150.0 if abs(py_) < 1 else 0.0), 9, mat=wood_dark, solid=False)
    for nm, name, dx, dy, yw, sc in (("c1", "crate_wood_a", -60, -40, 20, 1.6), ("c2", "crate_wood_b", 70, 30, -35, 1.4), ("b1", "barrel_wood_a", -130, 60, 0, 1.0),
                                    ("b2", "barrel_red", 140, -80, 0, 1.0), ("j1", "jerrycan", 20, 100, 70, 1.6), ("l1", "lantern", -20, -90, 0, 2.0)):
        m.prop("TentProp_%d_%s" % (sx, nm), name, tx + dx, ty + dy, MESA_Z, yaw=yw, scale=sc, solid=(nm not in ("j1", "l1")))
    m.accent_light("TentLight_%d" % sx, (tx, ty, MESA_Z + 130.0), (1.0, 0.72, 0.42), candela=18.0, radius=420.0)
    m.prop("FirePit_%d" % sx, "fire_pit", sx * (FX + 1100.0), 1100.0, MESA_Z, yaw=rng.uniform(0, 360), scale=0.9, solid=False)
    m.prop("Tyre_%d" % sx, "tyre", sx * (FX + 900.0), 1200.0, MESA_Z, yaw=40, scale=1.2, solid=False)

# ---------------------------------------------------------------- the ravine: boulders in the river, stumps
for i in range(14):
    m.prop("RiverRock_%d" % i, rng.choice(("rock_red_c_l", "rock_red_b_l", "rock_red_a_l", "rock_red_c_s", "rock_boulder_l")), rng.uniform(-FX + 200, FX - 200), rng.uniform(-230, 230), -770.0,
           yaw=rng.uniform(0, 360), scale=rng.uniform(0.7, 1.4), solid=False, sink=0.2)

# ---------------------------------------------------------------- distant mesas and mountains (in the haze)
for i in range(22):
    ang = i / 22.0 * 2 * math.pi + rng.uniform(-0.1, 0.1)
    d = rng.uniform(9500, 16000)
    h = rng.uniform(2800, 5200)
    r = rng.uniform(1600, 3200)
    sm = kb.commit("CFarMesa_%d" % (i % 8), mm.mesa_mesh(r, h, seed=60 + i % 8))
    kb.put(m, "FarMesa_%d" % i, sm, math.cos(ang) * d * 1.15, math.sin(ang) * d * 0.85, -300.0, yaw=rng.uniform(0, 360), scale=(1.0, rng.uniform(0.7, 1.3), 1.0),
           mat=far_red if i % 3 else far_pale, solid=False)
for i in range(8):
    ang = i / 8.0 * 2 * math.pi + 0.3
    d = rng.uniform(22000, 30000)
    sm = kb.commit("CFarPeak_%d" % (i % 4), mm.mountain_mesh(rng.uniform(5000, 8000), rng.uniform(5000, 8000), seed=90 + i % 4))
    kb.put(m, "FarPeak_%d" % i, sm, math.cos(ang) * d, math.sin(ang) * d, -400.0, yaw=rng.uniform(0, 360), mat=far_pale, solid=False)

# ---------------------------------------------------------------- spawns (the old positions) and light
m.starts(STARTS)

# ---------------------------------------------------------------- props scattered last (they need the finished ground)
avoid = [(x, y, 300.0) for x, y, z, _ in STARTS] + [(x, y, 520.0) for x, y in PADS] + [(bx, 0.0, 380.0) for bx in (-2000.0, 0.0, 2000.0)]
floor_ranges = [("rect", -FX + 80, RAV + 100, FX - 80, FY - 90), ("rect", -FX + 80, -FY + 90, FX - 80, -RAV - 100)]
for k, region in enumerate(floor_ranges):
    m.scatter(["rock_red_small", "rock_red_small_s", "rock_red_small_l", "rock_red_small_s"], region, 110, seed=100 + k, scale=(0.5, 1.4), min_gap=45, avoid=avoid, label="Pebble%d" % k, solid=False,
              max_slope=30)
    m.scatter(["rock_red_a_s", "rock_red_b_s", "rock_red_c_s", "rock_flat_s"], region, 22, seed=110 + k, scale=(0.8, 1.4), min_gap=160, avoid=avoid, label="Stone%d" % k, max_slope=25)
    # generated cairns / rubble heaps (non-solid, lumpy sandstone with bedding) so the floor is not only scanned rocks
    for j in range(9):
        for _ in range(12):
            x, y = rng.uniform(region[1] + 60, region[3] - 60), rng.uniform(region[2] + 60, region[4] - 60)
            if all(math.hypot(x - ax, y - ay) > ar + 130.0 for ax, ay, ar in avoid) and all(math.hypot(x - rx, y - ry) > max(rsx, rsy) / 2.0 + 180.0 for rx, ry, rsx, rsy, _ in ROCKS):
                kb.put(m, "Cairn_%d_%d" % (k, j), PILE_SM[(j + k) % 6], x, y, -4.0, yaw=rng.uniform(0, 360), scale=rng.uniform(0.35, 0.75),
                       mat=(rock_cliff, rock_rough, rock_red, rock_pale)[j % 4], solid=False, folder="Ground")
                break
    kb.retint(m.scatter(["shrub_a", "shrub_b", "shrub_a"], region, 34, seed=120 + k, scale=(0.35, 0.8), min_gap=90, avoid=avoid, label="Bush%d" % k, solid=False), bush_m)
    m.scatter(["tree_quiver_b"], region, 4, seed=130 + k, scale=(1.5, 2.6), min_gap=300, avoid=avoid, label="Tree%d" % k, solid=False, max_slope=15)
    kb.retint(m.scatter(["trunk_quiver"], region, 4, seed=135 + k, scale=(1.3, 2.2), min_gap=300, avoid=avoid, label="Trunk%d" % k, solid=False, max_slope=15), trunk_m)
    m.scatter(["trunk_dead_b", "stump_a"], region, 2, seed=140 + k, scale=(1.0, 1.6), min_gap=300, avoid=avoid, label="Dead%d" % k, max_slope=10)
for k, region in enumerate((("rect", FX + 100, -2300, FX + 1300, 2300), ("rect", -FX - 1300, -2300, -FX - 100, 2300))):
    m.scatter(["rock_red_small", "rock_red_small_s", "rock_red_small_l"], region, 22, seed=150 + k, scale=(0.6, 1.3), min_gap=80, avoid=avoid + [(sx * (FX + 800.0), 1500.0, 360.0) for sx in (-1, 1)],
              label="MesaPebble%d" % k, solid=False, z_range=(MESA_Z - 20, MESA_Z + 20))
    kb.retint(m.scatter(["shrub_a", "shrub_b"], region, 10, seed=160 + k, scale=(0.35, 0.7), min_gap=120, avoid=avoid + [(sx * (FX + 800.0), 1500.0, 360.0) for sx in (-1, 1)],
                        label="MesaBush%d" % k, solid=False, z_range=(MESA_Z - 20, MESA_Z + 20)), bush_m)
# talus at the foot of the big walls (the cliffs are non-solid: these rocks stand on the floors)
for k, (y0, y1) in enumerate(((FY - 230.0, FY - 20.0), (-FY + 20.0, -FY + 230.0))):
    m.scatter(["rock_red_b_l", "rock_red_c_l", "rock_red_a_l", "rock_red_c_s", "rock_boulder_l"], ("rect", -FX + 100, y0, FX - 100, y1), 7, seed=170 + k, scale=(0.8, 1.4), min_gap=200,
              avoid=avoid, label="Talus%d" % k, solid=False, max_slope=60)

# buttes standing on the rim of the big walls (a ragged skyline), and scanned cliffs in the far haze
for label in ("WallN", "WallS"):
    c = CLIFF[label]
    for k in range(6):
        u = (k + rng.uniform(0.2, 0.8)) * c["width"] / 6.0
        yl = rng.uniform(500.0, 800.0)
        sm = kb.commit("CRimButte_%d" % (k % 4), mm.mesa_mesh(rng.uniform(380, 640), rng.uniform(500, 1000), seed=200 + k % 4, base_z=-500.0, sides=30, rings=14))
        wx, wy = local_to_world(c, u, yl)
        kb.put(m, "RimButte_%s%d" % (label, k), sm, wx, wy, c["lay"].boundary(c["n"], u) - 60.0, yaw=rng.uniform(0, 360), mat=STRATA_MATS[(k + 1) % 4], solid=False)
for k in range(10):
    ang = k / 10.0 * 2 * math.pi + 0.2
    d = rng.uniform(8500, 12000)
    m.prop("FarCliff_%d" % k, "cliff_red_a", math.cos(ang) * d * 1.2, math.sin(ang) * d * 0.9, -300.0, yaw=math.degrees(ang) + 90.0, scale=rng.uniform(9.0, 14.0), solid=False)

m.look("desert", sun_yaw=215.0, sun_pitch=-38.0, ev=0.7, ambient_gain=0.1477, sky_intensity=6.0)
m.finish(kill_z=-700)
