"""DM-Temple: a sunken sandstone temple courtyard with a stepped ziggurat, a colonnade, four corner pavilions and an altar on top.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_temple.py" -unattended -nullrhi -nosplash

Gameplay layout (unchanged): 4800 x 4800 courtyard, three ziggurat tiers (tops z = 200 / 400 / 600) with stairs on all four sides,
four pavilion platforms (z = 200) in the corners, a ring of colonnade columns, four low cover walls, eight player starts on the ground.
Visuals (this version): real masonry surfaces (matlib), generated meshes (fluted tapered columns with capitals, broken columns and fallen
drums, ruined wall runs with pilasters, arched doorways, cornices and friezes, stepped roofs, sand drifts, layered cliffs that make the
pit), catalogue props (moss rocks, ferns, shrubs, statues, vases), water basins, small braziers with a few low accent lights.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
from mapkit import MapBuilder  # noqa: E402
import props  # noqa: E402,F401  (adds b.prop / b.scatter)
import mapkit_b as kb  # noqa: E402
import mesh_b as mb  # noqa: E402
import mesh_arch_b as ma  # noqa: E402
import mesh_misc_b as mm  # noqa: E402
from matlib import surface, water  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Temple")
rng = random.Random(11)

# ---------------------------------------------------------------- surfaces
wall_m = surface("SandstoneBlocks", tiling=3.4, dirt=0.5, dirt_h=450, tag="TWall")
wall2_m = surface("SandstoneBlocks", tiling=2.8, albedo=(176, 146, 108), tag="TWall2")
lime_m = surface("Limestone", tiling=2.6, albedo=(208, 194, 164), tag="TLime")
lime_dirty_m = surface("Limestone", tiling=3.0, albedo=(176, 160, 132), dirt=0.4, dirt_h=250, tag="TLimeD")
pave_m = surface("StoneSlabs", tiling=4.2, albedo=(158, 146, 124), tag="TPave")
pave2_m = surface("StoneSlabs", tiling=3.0, albedo=(178, 162, 134), tag="TPave2")
sand_m = surface("Sand", tiling=5.0, albedo=(196, 164, 108), tag="TSand")
dirt_m = surface("DirtDry", tiling=3.0, albedo=(120, 98, 70), tag="TDirt")
gravel_m = surface("Gravel", tiling=3.0, albedo=(140, 130, 112), tag="TGravel")
dark_m = surface("StoneDark", tiling=2.5, albedo=(54, 50, 46), tag="TDark")
roof_m = surface("StoneRubble", tiling=3.0, albedo=(122, 104, 88), tag="TRoof")
bronze_m = surface("BrushedMetal", albedo=(112, 86, 52), metal=0.4, rb=0.2, tag="TBronze")
cliff_ms = [surface("RockCliff", tiling=6.0, albedo=(140, 112, 86), tag="TCliffA"),
            surface("SandstoneRough", tiling=5.0, albedo=(176, 142, 104), tag="TCliffB"),
            surface("RockCliff", tiling=7.0, albedo=(112, 92, 74), tag="TCliffC"),
            surface("RockGrey", tiling=6.0, albedo=(132, 118, 98), tag="TCliffD")]
mount_m = surface("RockGrey", tiling=40.0, albedo=(118, 112, 108), tag="TMount")
water_m = water()
flame_m = m.glow("MI_TempleFlame", (1.0, 0.42, 0.10), 3.0)

HALF = 2300.0
T = 100.0
WALL_TOP = 1350.0


def L(org, yaw, lx, ly):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return (org[0] + lx * c - ly * s, org[1] + lx * s + ly * c)


# ---------------------------------------------------------------- ground
m.box("Floor", 0, 0, -54, 5000, 5000, 100, mat=sand_m)                 # top at z = -4 (sand)
m.box("Plaza", 0, 0, -15, 3000, 3000, 30, mat=pave_m)                   # top at z = 0 (paving)
for sx in (-1, 1):
    m.box("AvenueX_%d" % sx, sx * 1900, 0, -15, 800, 500, 30, mat=pave_m)
    m.box("AvenueY_%d" % sx, 0, sx * 1900, -15, 500, 800, 30, mat=pave_m)
# ragged edge of the paving: loose patches (same surface, same height, so no visible seams) and dirt/gravel patches on the sand
for i in range(34):
    a = rng.choice((0, 1, 2, 3))
    if a < 2:                       # along the plaza edge
        e = rng.choice((-1, 1)) * (1500 + rng.uniform(-40, 140))
        t = rng.uniform(-1500, 1500)
        x, y = (e, t) if a == 0 else (t, e)
    else:                           # along the avenues
        e = rng.choice((-1, 1)) * (250 + rng.uniform(-30, 120))
        t = rng.choice((-1, 1)) * rng.uniform(1500, 2250)
        x, y = (t, e) if a == 2 else (e, t)
    s = rng.uniform(160, 420)
    m.box("PaveBreak_%d" % i, x, y, -15, s, s * rng.uniform(0.5, 1.0), 30, yaw=rng.uniform(0, 90), mat=pave_m)
for i in range(30):
    x, y = rng.uniform(-2250, 2250), rng.uniform(-2250, 2250)
    if abs(x) < 1500 and abs(y) < 1500:
        continue
    if abs(x) < 280 or abs(y) < 280:
        continue
    s = rng.uniform(250, 700)
    m.box("Patch_%d" % i, x, y, -5.0 + 0.07 * i - 0.0, s, s * rng.uniform(0.4, 0.9), 2.0, yaw=rng.uniform(0, 180),
          mat=rng.choice((dirt_m, gravel_m, dirt_m)), solid=False)

# sand drifts piled against the walls and in the corners (the mesh is the collision: low, gentle, walkable)
def drift(label, x, y, sx, sy, hmax, seed, yaw=0.0):
    def h(px, py):
        u, v = px / (sx / 2.0), py / (sy / 2.0)
        r2 = u * u + v * v
        env = max(0.0, 1.0 - r2) ** 1.6
        rip = mb.fbm(px / 140.0, py / 140.0, 0, 3, seed) * 0.08 + 0.92
        return -8.0 + (hmax + 8.0) * env * rip
    sm = kb.commit("TDrift_%s" % label, ma.heightfield(-sx / 2.0, -sy / 2.0, sx / 2.0, sy / 2.0, 60.0, h, floor_z=-30.0))
    kb.put(m, "Drift_" + label, sm, x, y, 0.0, yaw=yaw, mat=sand_m)


for i, (x, y, sx, sy, hm, yw) in enumerate([
        (-1500, 2190, 900, 220, 70, 0), (1200, 2200, 700, 200, 55, 0), (-300, -2200, 800, 200, 60, 0),
        (1700, -2190, 600, 240, 80, 0), (2190, -1000, 240, 800, 60, 0), (2200, 1500, 220, 700, 70, 0),
        (-2200, 1100, 220, 800, 65, 0), (-2190, -1600, 240, 700, 75, 0), (2150, 2150, 500, 500, 90, 30),
        (-2150, -2150, 520, 460, 85, -20)]):
    drift("%d" % i, x, y, sx, sy, hm, 5 + i, yw)

# ---------------------------------------------------------------- the four temple walls (ruined, with pilasters, doorways, friezes)
SIDES = [("N", (-2400.0, 2300.0), 0.0), ("S", (2400.0, -2300.0), 180.0), ("E", (2300.0, 2400.0), -90.0), ("W", (-2300.0, -2400.0), 90.0)]
LEN = 4800.0
DOORS = (1200.0, 3600.0)


def top_at(profile, u):
    for x0, x1, t in profile:
        if x0 <= u < x1:
            return t
    return profile[-1][2]


def wall_profile(seed, breach):
    r = random.Random(seed)
    prof, x = [], 0.0
    while x < LEN - 1:
        w = min(r.uniform(130, 380), LEN - x)
        top = WALL_TOP
        if r.random() < 0.34:
            top = r.choice((1050, 1100, 1150, 1200, 1250, 1300))
        near_door = any(abs((x + w / 2.0) - d) < 330 for d in DOORS)
        if near_door:
            top = WALL_TOP
        if breach and breach[0] <= x < breach[1]:
            top = r.choice((760, 820, 900))
        prof.append((x, x + w, float(top)))
        x += w
    return prof


door_fill = mb.Mesh()
_R, _H = 110.0, 430.0
_zs = _H - _R
door_fill.prism([(-_R, 0.0), (_R, 0.0)] + [(_R * math.cos(math.pi * k / 10.0), _zs + _R * math.sin(math.pi * k / 10.0)) for k in range(0, 11)], -1.5, 0.0)
door_fill_sm = kb.commit("TDoorFill", door_fill, collision="none")

wall_profiles = {}
for wi, (name, org, yaw) in enumerate(SIDES):
    prof = wall_profile(100 + wi, breach=(1700, 2250) if name in ("N", "W") else None)
    wall_profiles[name] = (prof, org, yaw)
    core = kb.commit("TWall_" + name, ma.wall_run(LEN, prof, T, seed=wi + 1, jitter=2.5))
    kb.put(m, "Wall_" + name, core, org[0], org[1], 0.0, yaw=yaw, mat=wall_m if wi % 2 == 0 else wall2_m)
    # pilasters + capitals (limestone), a frieze band, cornices on the intact stretches, a dark plinth course
    pil = mb.Mesh()
    for k in range(8):
        u = 300.0 + 600.0 * k
        tp = top_at(prof, u)
        hp = min(1230.0, tp - 70.0)
        h1 = hp * 0.5 + rng.uniform(-20, 20)
        pil.box(u, -19, 0, 112, 38, h1, base=True, jitter=0.8, seed=wi * 40 + k)
        pil.box(u + rng.uniform(-1, 1), -19, h1, 108, 36, hp - h1, base=True, jitter=0.8, seed=wi * 40 + k + 9)
        if tp >= WALL_TOP - 1:
            pil.box(u, -28, hp, 170, 56, 52, base=True, jitter=0.8, seed=wi * 40 + k + 3)
            pil.box(u, -36, hp + 50, 190, 72, 24, base=True, jitter=0.8, seed=wi * 40 + k + 5)
    kb.put(m, "Pilasters_" + name, kb.commit("TPilasters_" + name, pil), org[0], org[1], 0.0, yaw=yaw, mat=lime_m)
    cor = mb.Mesh()
    run_start = None
    for x0, x1, t in prof + [(LEN, LEN, 0.0)]:
        if t >= WALL_TOP - 1 and run_start is None:
            run_start = x0
        if (t < WALL_TOP - 1) and run_start is not None:
            cor.append(ma.cornice(x0 - run_start, 38.0, 70.0, seed=wi), offset=(run_start, 0, WALL_TOP - 70.0))
            run_start = None
    kb.put(m, "Cornice_" + name, kb.commit("TCornice_" + name, cor), org[0], org[1], 0.0, yaw=yaw, mat=lime_dirty_m)
    kb.put(m, "Frieze_" + name, kb.commit("TFrieze_" + name, ma.frieze(LEN, 90.0, 16.0, seed=wi + 7)), org[0], org[1], 1000.0, yaw=yaw, mat=lime_dirty_m)
    px, py = L(org, yaw, LEN / 2.0, -7.0)
    m.box("Plinth_" + name, px, py, 30, LEN, 14, 120, yaw=yaw, mat=dark_m, solid=False)
    for di, du in enumerate(DOORS):
        fx, fy = L(org, yaw, du, 0.0)
        kb.put(m, "Door_%s_%d" % (name, di), kb.commit("TArch_%d" % (wi % 2), ma.arch_frame(220.0, 430.0, 36.0, tk=46.0, seed=wi % 2 + 3)),
               fx, fy, 0.0, yaw=yaw, mat=lime_m)
        kb.put(m, "DoorFill_%s_%d" % (name, di), door_fill_sm, fx, fy, 0.0, yaw=yaw, mat=dark_m, solid=False)
        vx, vy = L(org, yaw, du, -85.0)
        m.prop("Vase_%s_%d" % (name, di), "vase_ceramic" if di else "vase_brass", vx, vy, 0.0, yaw=yaw, scale=2.4 if di else 2.0)

# ---------------------------------------------------------------- the ziggurat
tiers = [(2000.0, 200.0, 200.0), (1100.0, 400.0, 200.0), (500.0, 600.0, 140.0)]
tier_mats = [wall2_m, lime_dirty_m, lime_m]
stair_meshes = {200.0: kb.commit("TStairs200", ma.stairs_mesh(380.0, 2, 100.0, 200.0, seed=4)),
                140.0: kb.commit("TStairs140", ma.stairs_mesh(380.0, 2, 100.0, 140.0, seed=5))}
prev_top = 0.0
for i, (size, top, run) in enumerate(tiers):
    m.box("Tier_%d" % i, 0, 0, top / 2.0, size, size, top, mat=tier_mats[i])
    m.box("TierTop_%d" % i, 0, 0, top + 1.0, size - 8, size - 8, 2.0, mat=pave2_m if i else pave_m, solid=False)
    half = size / 2.0
    for yaw_out in (0, 90, 180, 270):
        ox, oy = math.cos(math.radians(yaw_out)), math.sin(math.radians(yaw_out))
        dist = half + 2 * run
        kb.put(m, "Stairs_%d_%d" % (i, yaw_out), stair_meshes[run], ox * dist, oy * dist, prev_top, yaw=yaw_out + 180, mat=pave2_m)
        # frieze panels left and right of the stairs, a cornice lip along the top edge
        phi = yaw_out + 90.0
        face_h = top - prev_top
        seg = half - 190.0 - 60.0
        for side in (-1, 1):
            lx0 = (-half + 40.0) if side < 0 else (190.0 + 30.0)
            org = (ox * half, oy * half)
            wx, wy = L(org, phi, lx0 - 0.0, 0.0)
            kb.put(m, "TierFrieze_%d_%d_%d" % (i, yaw_out, side), kb.commit("TTierFrieze_%d_%d" % (i, int(seg)), ma.frieze(seg, face_h * 0.45, 12.0, seed=i * 3 + 1)),
                   wx, wy, prev_top + face_h * 0.28, yaw=phi, mat=lime_m, solid=False)
        cx, cy = L((ox * half, oy * half), phi, -half - 6.0, 0.0)
        kb.put(m, "TierLip_%d_%d" % (i, yaw_out), kb.commit("TTierLip_%d" % i, ma.cornice(size + 12.0, 22.0, 36.0, seed=i)),
               cx, cy, top - 34.0, yaw=phi, mat=lime_m, solid=False)
    prev_top = top

# altar: a stone block, a bronze brazier on it, two obelisks, braziers at the corners of the top tier
m.box("Altar", 0, 0, 640, 200, 200, 80, mat=lime_m)
brazier_sm = kb.commit("TBrazier", mm.brazier_mesh())
altar_flames = [(0.0, 0.0, 680.0)] + [(sx * 205.0, sy * 205.0, 600.0) for sx in (-1, 1) for sy in (-1, 1)]
for k, (bx, by, bz) in enumerate(altar_flames):
    kb.put(m, "Brazier_%d" % k, brazier_sm, bx, by, bz, mat=bronze_m, solid=False)
    m.cone("Flame_%d" % k, bx, by, bz + 62, bz + 112, 26, mat=flame_m, solid=False)
    m.accent_light("BrazierLight_%d" % k, (bx, by, bz + 110), (1.0, 0.55, 0.22), candela=35.0 if k else 55.0, radius=520.0)
obel = kb.commit("TObelisk", mm.obelisk_mesh(160.0, 44.0))
for sx in (-1, 1):
    kb.put(m, "AltarPost_%d" % sx, obel, sx * 180.0, 0.0, 600.0, mat=dark_m)

# four guardians on the middle tier
for sx in (-1, 1):
    for sy in (-1, 1):
        m.box("GuardPlinth", sx * 450, sy * 450, 420, 200, 200, 40, mat=lime_m)
        m.prop("Guardian_%d_%d" % (sx, sy), "statue_gothic", sx * 450, sy * 450, 440, yaw=math.degrees(math.atan2(-sy, -sx)), scale=1.15)

# ---------------------------------------------------------------- corner pavilions
col_pav = kb.commit("TColPav", mb.column_mesh(620.0, 56.0, flutes=16, drums=4, seed=3, plinth_k=2.3, abacus_k=2.5))
beam_frame = mb.Mesh()
for k, (bx, by, sxl, syl) in enumerate([(0, 350, 880, 96), (0, -350, 880, 96), (350, 0, 96, 880), (-350, 0, 96, 880)]):
    beam_frame.box(bx, by, 0, sxl, syl, 74, base=True, jitter=1.2, seed=k + 50)
beam_sm = kb.commit("TPavBeams", beam_frame)
pav_missing = {(1, 1): (), (-1, 1): ((2, 2),), (-1, -1): ((0, 0), (1, 0)), (1, -1): ((1, 2), (2, 2), (2, 1))}
for sx in (-1, 1):
    for sy in (-1, 1):
        px, py = sx * 1650.0, sy * 1650.0
        m.box("Pavilion", px, py, 100, 800, 800, 200, mat=wall_m)
        m.box("PavTop", px, py, 201.0, 792, 792, 2, mat=pave2_m, solid=False)
        kb.put(m, "PavStairX", stair_meshes[200.0], px - sx * 850, py, 0, yaw=0 if sx > 0 else 180, mat=pave2_m)
        kb.put(m, "PavStairY", stair_meshes[200.0], px, py - sy * 850, 0, yaw=90 if sy > 0 else 270, mat=pave2_m)
        for cx in (-1, 1):
            for cy in (-1, 1):
                kb.put(m, "PavColumn", col_pav, px + cx * 350, py + cy * 350, 200, yaw=rng.uniform(0, 90), mat=lime_m)
        kb.put(m, "PavBeams", beam_sm, px, py, 820, mat=lime_dirty_m)
        kb.put(m, "PavRoof", kb.commit("TRoof_%d_%d" % (sx, sy), mm.roof_mesh(900.0, seed=sx * 3 + sy + 9, missing=pav_missing[(sx, sy)])),
               px, py, 894, yaw=rng.uniform(-3, 3), mat=roof_m)
        m.box("PavBust", px, py, 240, 120, 120, 80, mat=lime_m)
        m.prop("PavBustProp", "bust_marble", px, py, 280, yaw=math.degrees(math.atan2(-sy, -sx)), scale=2.6)

# ---------------------------------------------------------------- colonnade: full columns, broken ones, fallen drums, beams
col_a = kb.commit("TColA", mb.column_mesh(700.0, 76.0, flutes=18, drums=5, seed=1))
col_b = kb.commit("TColB", mb.column_mesh(700.0, 76.0, flutes=18, drums=5, seed=2))
broken = {("N", 1): 330.0, ("E", -2): 470.0, ("S", -1): 220.0, ("W", 2): 400.0, ("N", -2): 560.0}
_bm = mb.Mesh()
_bm.box(0, 0, 0, 470, 100, 74, base=True, jitter=1.2, seed=77)
beam_one = kb.commit("TBeam", _bm)
fallen = 0
for side, (ax, ay, yaw_side) in {"N": (0, 1, 0), "S": (0, -1, 0), "E": (1, 0, 90), "W": (-1, 0, 90)}.items():
    for i in range(-2, 3):
        x, y = (i * 400.0, ay * 1250.0) if ax == 0 else (ax * 1250.0, i * 400.0)
        key = (side, i)
        if key in broken:
            sm = kb.commit("TColBroken_%s%d" % (side, i), mb.column_mesh(700.0, 76.0, flutes=18, drums=5, seed=10 + i + ord(side), broken_at=broken[key]))
            kb.put(m, "ColBroken_%s%d" % (side, i), sm, x, y, 0, yaw=rng.uniform(0, 90), mat=lime_dirty_m)
            for q in range(2):                      # drums that fell off
                if ax == 0:
                    dx, dy = rng.uniform(150, 300) * (1 if q else -1), ay * rng.uniform(130, 260)
                else:
                    dx, dy = ax * rng.uniform(130, 260), rng.uniform(150, 300) * (1 if q else -1)
                fallen += 1
                kb.put(m, "FallenDrum_%d" % fallen, kb.commit("TDrum_%d" % (fallen % 3), mm.drum_mesh(110.0 + 20 * (fallen % 3), 62.0, flutes=18, seed=fallen)),
                       x + dx, y + dy, 62.0 * 0.95, yaw=rng.uniform(0, 180), mat=lime_dirty_m)
        else:
            kb.put(m, "Column_%s%d" % (side, i), col_a if (i + ord(side)) % 2 else col_b, x, y, 0, yaw=rng.uniform(0, 90), mat=lime_m)
    for i in range(-2, 2):
        if (side, i) in broken or (side, i + 1) in broken:
            continue
        x, y = ((i + 0.5) * 400.0, ay * 1250.0) if ax == 0 else (ax * 1250.0, (i + 0.5) * 400.0)
        kb.put(m, "Architrave_%s%d" % (side, i), beam_one, x, y, 700.0, yaw=yaw_side, mat=lime_dirty_m)
        # a fallen beam near broken bays
for k, (x, y, yw) in enumerate([(960, 1090, 30), (-1090, -700, 80), (860, -1130, -20), (1110, 840, 75)]):
    kb.put(m, "FallenBeam_%d" % k, beam_one, x, y, 0.0, yaw=yw, pitch=4.0, mat=lime_dirty_m)

# ---------------------------------------------------------------- ruined low cover walls and the two water basins
for label, x, y, yaw in [("CoverE", 1750, 0, 90), ("CoverW", -1750, 0, 90), ("CoverN", 0, 1750, 0), ("CoverS", 0, -1750, 0)]:
    prof = [(0, 130, 130.0), (130, 260, 118.0), (260, 380, 130.0), (380, 500, 112.0)]
    sm = kb.commit("TCover_" + label, ma.wall_run(500.0, prof, 120.0, seed=len(label) + x % 7, jitter=1.0))
    ox, oy = L((x, y), yaw, -250.0, -60.0)
    kb.put(m, label, sm, ox, oy, 0.0, yaw=yaw, mat=wall2_m)

for sy in (-1, 1):
    cx, cy = 0.0, sy * 2150.0
    for k, (dx, dy, sx_, sy_) in enumerate([(0, 130, 660, 30), (0, -130, 660, 30), (315, 0, 30, 260), (-315, 0, 30, 260)]):
        m.box("BasinRim_%d_%d" % (sy, k), cx + dx, cy + dy, 28, sx_, sy_, 56, mat=lime_m)
    m.box("BasinWater_%d" % sy, cx, cy, 38, 630, 230, 3, mat=water_m, solid=False)
    m.box("BasinBed_%d" % sy, cx, cy, 8, 630, 230, 16, mat=dark_m, solid=False)
for sx in (-1, 1):
    m.box("StatuePlinth_%d" % sx, sx * 2140, 0, 40, 240, 240, 80, mat=lime_m)
    m.prop("Statue_%d" % sx, "statue_gothic", sx * 2140, 0, 80, yaw=180 if sx > 0 else 0, scale=1.5)

# ---------------------------------------------------------------- the pit: layered cliffs all round, craggy mountains behind
PIT = 3500.0
PIT_H = 3000.0
for ci, (name, org, yaw) in enumerate([("N", (-4600.0, PIT), 0.0), ("S", (4600.0, -PIT), 180.0), ("E", (PIT, 4600.0), -90.0), ("W", (-PIT, -4600.0), 90.0)]):
    st = ma.Strata(40 + ci, PIT_H + 200.0)
    seed = 70 + ci

    def off(u, z, st=st, seed=seed):
        lean = -z * 0.17
        big = 300.0 * mb.fbm(u / 1300.0 + seed * 0.37, z / 1700.0, 0.0, 3, seed)
        mid = 70.0 * mb.fbm(u / 260.0, z / 240.0, 0.0, 3, seed + 5)
        cr = -90.0 * mb.ridged(u / 420.0, z / 4000.0, 0.0, 2, seed + 9)
        return lean + st.profile(z, 120.0) + big + mid + cr

    def rim(u, seed=seed):
        return -600.0 + 900.0 * mb.fbm(u / 1500.0 + 3.1, 0.5, 0.0, 3, seed + 20) - 250.0 * mb.ridged(u / 300.0, 0.0, 0.0, 2, seed + 21)

    zs = [0.0, 420.0, 900.0, 1350.0, 1900.0, 2450.0, PIT_H]
    for k in range(len(zs) - 1):
        top = k == len(zs) - 2
        sm = kb.commit("TCliff_%s_%d" % (name, k), ma.cliff_strip(9200.0, zs[k], zs[k + 1], off, 1500.0, cell=100.0,
                                                                  top_fn=rim if top else None, skirt_top=top), collision="none")
        kb.put(m, "Cliff_%s_%d" % (name, k), sm, org[0], org[1], 0.0, yaw=yaw, mat=cliff_ms[(k + ci) % 4], solid=False)

for i in range(9):
    ang = i / 9.0 * 2 * math.pi + rng.uniform(-0.15, 0.15)
    d = rng.uniform(15000, 24000)
    h = rng.uniform(3500, 7000)
    sm = kb.commit("TMountain_%d" % i, mm.mountain_mesh(rng.uniform(3500, 6000), h, seed=i * 5 + 2))
    kb.put(m, "Mountain_%d" % i, sm, math.cos(ang) * d, math.sin(ang) * d, -300.0, yaw=rng.uniform(0, 360), mat=mount_m, solid=False)

# ---------------------------------------------------------------- spawns
spawns = [(sx * 1900.0, sy * 600.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
spawns += [(sx * 600.0, sy * 1900.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
m.face_center_starts(spawns)
avoid = [(x, y, 260.0) for x, y, _ in spawns]
avoid += [(0.0, sy * 2150.0, 420.0) for sy in (-1, 1)]

# ---------------------------------------------------------------- props: rubble, moss rocks, ferns, shrubs, rim growth (scattered last, they use the finished floor)
moss = ["rock_moss_small_a", "rock_moss_small_b", "rock_moss_small_c", "rock_moss_big_c", "rock_flat_s"]
for k, region in enumerate([("rect", -2250, 2020, 2250, 2290), ("rect", -2250, -2290, 2250, -2020), ("rect", 2020, -2250, 2290, 2250), ("rect", -2290, -2250, -2020, 2250)]):
    m.scatter(moss, region, 9, seed=20 + k, scale=(0.7, 1.3), min_gap=90, avoid=avoid, label="WallRubble%d" % k, max_slope=40)
m.scatter(["rock_moss_small_a", "rock_flat_s", "rock_moss_small_b"], ("ring", 0, 0, 1330, 1450), 14, seed=31, scale=(0.5, 1.0), min_gap=120,
          avoid=avoid, label="PlazaRubble", solid=False)
m.scatter(["rock_moss_big_a", "rock_moss_big_b", "rock_moss_big_d", "rock_moss_big_c"], ("poly", [(1000, 1000), (2150, 1000), (2150, 2150), (1000, 2150)]), 3, seed=41,
          scale=(0.9, 1.3), min_gap=300, avoid=avoid + [(1650, 1650, 560)], label="CornerRocks", max_slope=40)
m.scatter(["rock_moss_big_a", "rock_moss_big_b", "rock_moss_big_d", "rock_moss_big_c"], ("poly", [(-1000, -1000), (-2150, -1000), (-2150, -2150), (-1000, -2150)]), 3, seed=42,
          scale=(0.9, 1.3), min_gap=300, avoid=avoid + [(-1650, -1650, 560)], label="CornerRocks2", max_slope=40)
plants = ["fern_a", "fern_b", "fern_a", "plant_anthurium_a", "plant_anthurium_b", "plant_calathea_a", "plant_calathea_b", "shrub_a"]
for k, region in enumerate([("rect", -2280, 2040, 2280, 2290), ("rect", -2280, -2290, 2280, -2040), ("rect", 2040, -2280, 2290, 2280), ("rect", -2290, -2280, -2040, 2280)]):
    m.scatter(plants, region, 26, seed=50 + k, scale=(1.3, 2.4), min_gap=40, avoid=avoid, label="WallPlants%d" % k, solid=False)
m.scatter(plants, ("ring", 0, 0, 1000, 1500), 36, seed=61, scale=(1.2, 2.0), min_gap=60, avoid=avoid, label="PlazaPlants", solid=False, z_range=(-20, 30))
m.scatter(["shrub_a", "shrub_b", "fern_a"], ("rect", -2250, -2250, 2250, 2250), 40, seed=62, scale=(1.2, 2.2), min_gap=80, avoid=avoid + [(0, 0, 1250)],
          label="CourtPlants", solid=False, z_range=(-20, 30))
for name, (prof, org, yaw) in wall_profiles.items():
    for k in range(11):
        u = rng.uniform(150, LEN - 150)
        px, py = L(org, yaw, u, 50.0)
        m.prop("WallGrowth_%s_%d" % (name, k), rng.choice(("shrub_a", "shrub_b", "shrub_a", "fern_a")), px, py, top_at(prof, u) - 15.0,
               yaw=rng.uniform(0, 360), scale=rng.uniform(1.8, 3.2), solid=False)

# ---------------------------------------------------------------- light: strong sun into a pit, cool sky, warm braziers
m.look("day_clear", sun_yaw=205.0, sun_pitch=-52.0, sun_lux=10.0, sky_intensity=5.0, ev=1.0, sun_rgb=(1.0, 0.9, 0.74), sky_rgb=(0.97, 0.95, 0.98))
m.finish(kill_z=-2000)
