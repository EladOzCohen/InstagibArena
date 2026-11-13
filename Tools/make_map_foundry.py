"""DM-Foundry: an old brick foundry yard. Same floor plan as the blockout (4800 x 4800 yard, catwalk ring at 450,
pinwheel of ramps, raised centre deck at 300, four pillars, eight low blocks), rebuilt as a believable place:
brick walls with pilasters, recessed windows, a cornice and gates; a steel catwalk with handrails; an overhead crane
on the four pillars; scrap bins, barrels and generators; a factory skyline with chimneys behind the walls.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_foundry.py" -unattended -nullrhi -nosplash

Units are Unreal units (1 uu = 1 cm). The floor top is at z = 0.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import mapkit_a as ka  # noqa: E402
import props  # noqa: E402,F401  (adds b.prop / b.scatter)
from matlib import surface  # noqa: E402
import shade_n  # noqa: E402

MAP_PATH = "/Game/Maps/DM-Foundry"
HALF = 2400.0          # inner half-size of the arena
WALL_HEIGHT = 1400.0
RING_Z = 450.0         # top surface of the catwalk ring
RING_WIDTH = 350.0
TOWER_Z = 300.0        # top surface of the central platform
INNER = HALF - RING_WIDTH

b = mapkit.MapBuilder(MAP_PATH)
rng = random.Random(11)

# ------------------------------------------------------------------------------------------------ materials
TAG = "Fd"
brick = surface("BrickRed", albedo=(150, 82, 62), tag=TAG + "Brick")
brick_top = surface("BrickDark", albedo=(104, 70, 60), tag=TAG + "BrickTop")
pier_mat = surface("BrickBrown")
lower_wall = surface("ConcreteBlocks", dirt=0.55, dirt_h=260, tag=TAG + "Lower")
plinth_mat = surface("ConcreteDark")
trim = surface("ConcretePanels", albedo=(160, 156, 148), tiling=1.5, tag=TAG + "Trim")
trim_dirty = surface("ConcreteWorn")
floor_mat = surface("ConcreteWorn", albedo=(152, 150, 143), tiling=3.0, tag=TAG + "Floor")
asphalt = surface("AsphaltCracked", albedo=(84, 83, 82), tag=TAG + "Asphalt")
asphalt_dark = surface("Asphalt")
plate = surface("DiamondPlate", albedo=(128, 126, 124), desat=1.0, macro=0.12, tiling=1.0, tag=TAG + "Plate2")
plate_dark = surface("DiamondPlateDark", desat=1.0, macro=0.12, tiling=1.0, tag=TAG + "PlateD")
steel = surface("SteelDark")
steel_blue = surface("SteelDark", albedo=(88, 94, 102), tag=TAG + "Blue2")
steel_light = surface("BrushedMetal", albedo=(130, 133, 138), tag=TAG + "Light")
yellow = surface("ContainerYellow", albedo=(196, 156, 52), tag=TAG + "Paint2")
rail_yel = surface("ContainerYellow", albedo=(168, 136, 66), macro=0.55, macro_m=2.5, rb=0.14, ns=1.2, tag=TAG + "Rail2")
black_paint = surface("SteelDark", albedo=(34, 34, 36), tag=TAG + "Black")
white_paint = surface("PlasterWhite")
pane = surface("ConcreteWorn", albedo=(44, 54, 64), rb=-0.1, tag=TAG + "Pane")
rust = surface("RustCoarse")
rust_orange = surface("RustOrange")
corr_rust = surface("CorrugatedRust")
corr_galv = surface("CorrugatedGalv", albedo=(150, 152, 156), tag=TAG + "Galv")
corr_dark = surface("CorrugatedDark")
scrap = surface("StoneRubble", albedo=(86, 70, 60), tag=TAG + "Scrap")
oil = surface("Asphalt", albedo=(46, 45, 46), tag=TAG + "Oil")
rust_stain = surface("RustOrange", albedo=(96, 58, 40), tag=TAG + "RustStain")
joint = surface("ConcreteDark", albedo=(70, 70, 68), tag=TAG + "Joint")
wood_old = surface("WoodPlanksOld")
wood_dark = surface("WoodPlanksDark")
slag = surface("Gravel", albedo=(92, 88, 84), tag=TAG + "Slag")
ground_far = surface("Gravel", albedo=(118, 112, 100), tiling=12.0, tag=TAG + "Far")
brick_stack = surface("BrickRed", albedo=(140, 76, 58), tiling=3.0, tag=TAG + "Stack")
band_white = surface("PlasterWhite", tiling=3.0, tag=TAG + "Band")
concrete_big = surface("ConcretePanels", tiling=4.0, tag=TAG + "Big")


# ------------------------------------------------------------------------------------------------ floor + yard
b.box("Floor", 0, 0, -50, HALF * 2 + 200, HALF * 2 + 200, 100, mat=floor_mat)
ground = b.box("YardGround", 0, 0, -160, 90000, 90000, 20, mat=ground_far, solid=False)
ka.set_shadow(ground, False)

# Floor overlays (no collision, a few cm high): paved roads, steel apron, pads, expansion joints, stains, lane paint.
Z_JOINT, Z_PAVE, Z_STAIN, Z_PAINT = 1.2, 2.0, 2.4, 2.9
for k in range(-3, 4):                                         # expansion joints every 6 m
    p = k * 600.0 + 300.0
    b.box("JointX", 0, p, Z_JOINT / 2, HALF * 2, 4.0, Z_JOINT, mat=joint, solid=False)
    b.box("JointY", p, 0, Z_JOINT / 2, 4.0, HALF * 2, Z_JOINT, mat=joint, solid=False)
for ax in (0, 1):                                               # the two crossing asphalt roads, 5 m wide
    sx, sy = (HALF * 2, 500.0) if ax == 0 else (500.0, HALF * 2)
    b.box("Road", 0, 0, Z_PAVE / 2, sx, sy, Z_PAVE, mat=asphalt, solid=False)
for sgn in (-1, 1):                                            # white edge lines of the roads
    for ax in (0, 1):
        for end in (-1, 1):
            if ax == 0:
                b.box("EdgeLine", end * 1475, sgn * 235, Z_PAINT / 2, 1850, 12, Z_PAINT, mat=white_paint, solid=False)
            else:
                b.box("EdgeLine", sgn * 235, end * 1475, Z_PAINT / 2, 12, 1850, Z_PAINT, mat=white_paint, solid=False)
for k in range(8):                                             # yellow dashed centre line
    for sgn in (-1, 1):
        d = 600 + k * 260
        if d < HALF - 100:
            b.box("Dash", sgn * d, 0, Z_PAINT / 2, 120, 12, Z_PAINT, mat=yellow, solid=False)
            b.box("Dash", 0, sgn * d, Z_PAINT / 2, 12, 120, Z_PAINT, mat=yellow, solid=False)
b.box("ApronPlate", 0, 0, Z_PAVE / 2 + 0.2, 1500, 1500, Z_PAVE, mat=plate_dark, solid=False)   # steel apron at the deck
for sx in (-1, 1):
    for sy in (-1, 1):
        b.box("PillarPad", sx * 1700, sy * 1700, Z_PAVE / 2 + 0.1, 520, 520, Z_PAVE, mat=trim_dirty, solid=False)
        b.box("PadFrame", sx * 1700, sy * 1700, Z_PAINT / 2, 580, 580, Z_PAINT - 0.6, mat=yellow, solid=False)
        b.box("PadFrameIn", sx * 1700, sy * 1700, Z_PAINT / 2 + 0.1, 556, 556, Z_PAINT, mat=trim_dirty, solid=False)
for i in range(16):                                            # oil / rust stains, overlapping ellipses
    x, y = rng.uniform(-2200, 2200), rng.uniform(-2200, 2200)
    if abs(x) < 280 or abs(y) < 280:
        continue
    for j in range(3):
        ka.disc(b, "Stain", x + rng.uniform(-60, 60), y + rng.uniform(-60, 60), Z_STAIN, rng.uniform(40, 110),
                rng.uniform(30, 90), 0.6, oil if i % 3 else rust_stain, yaw=rng.uniform(0, 180))

# ------------------------------------------------------------------------------------------------ the brick shell
BAY = 600.0
WIN_W, WIN_Z0, WIN_Z1 = 300.0, 720.0, 1120.0
GATE_U = {"N": (-1500, 900), "S": (-900, 1500), "E": (-1500, 300), "W": (-300, 1500)}

def wall(side, origin, yaw, half):
    w = ka.Wall(b, origin, yaw)
    L2 = half * 2
    n = "Wall_" + side
    w.box(n + "_Lower", 0, -50, -100, RING_Z, L2, 100, lower_wall, solid=True)
    w.box(n + "_Mid", 0, -50, RING_Z, WIN_Z0, L2, 100, brick, solid=True)
    w.box(n + "_Top", 0, -50, WIN_Z1, WALL_HEIGHT, L2, 100, brick_top, solid=True)
    for k in range(-4, 5):                                      # piers between the window openings
        u = k * BAY
        pw = min(WIN_W, half - abs(u) + WIN_W / 2) if abs(u) > half - WIN_W / 2 else WIN_W
        uc = u if abs(u) <= half - WIN_W / 2 else math.copysign(half - pw / 2, u)
        w.box(n + "_Pier", uc, -50, WIN_Z0, WIN_Z1, pw, 100, brick, solid=True)
    for j in range(-4, 4):                                      # windows
        u = j * BAY + BAY / 2
        ka.window(w, "%s_Win%d" % (n, j), u, WIN_Z0, WIN_W, WIN_Z1 - WIN_Z0, steel_blue, trim, pane, mullions=2)
    # a few windows are bricked half-up / boarded for variety
    for j in (-3, 0, 2):
        u = j * BAY + BAY / 2
        w.box(n + "_Board", u, -30, WIN_Z0, WIN_Z0 + 150, WIN_W - 30, 6, corr_rust)
    # plinth, band courses, cornice, coping
    w.box(n + "_Plinth", 0, 7, 0, 110, L2, 14, plinth_mat)
    w.box(n + "_PlinthCap", 0, 9, 110, 124, L2, 18, trim)
    w.box(n + "_Band", 0, 6, RING_Z, RING_Z + 22, L2, 12, trim)
    w.box(n + "_SillBand", 0, 3, WIN_Z0 - 28, WIN_Z0 - 14, L2, 6, brick_top)
    w.box(n + "_Frieze", 0, 5, WIN_Z1 + 20, WIN_Z1 + 60, L2, 10, brick_top)
    w.box(n + "_Cornice", 0, 10, WALL_HEIGHT - 70, WALL_HEIGHT, L2, 20, trim)
    w.box(n + "_CorniceLip", 0, 20, WALL_HEIGHT - 12, WALL_HEIGHT + 10, L2, 40, trim)
    w.box(n + "_Coping", 0, 16, WALL_HEIGHT + 10, WALL_HEIGHT + 34, L2, 70, plinth_mat)
    # pilasters with base and capital
    for k in range(-4, 5):
        u = k * BAY
        if abs(u) > half - 60:
            continue
        w.box(n + "_Pilaster", u, 14, 124, WALL_HEIGHT - 70, 150, 28, pier_mat)
        w.box(n + "_PilBase", u, 18, 124, 190, 190, 36, trim)
        w.box(n + "_PilCap", u, 18, WALL_HEIGHT - 120, WALL_HEIGHT - 70, 190, 36, trim)
    # rain pipes on every second pilaster
    for k in (-3, -1, 1, 3):
        u = k * BAY + 100
        w.cyl(n + "_Downpipe", u, 36, 30, WALL_HEIGHT - 80, 14, black_paint)
        w.cyl(n + "_DownpipeBand", u, 36, 200, 215, 20, steel)
        w.cyl(n + "_DownpipeBand", u, 36, 520, 535, 20, steel)
    # gates under the catwalk
    for gi, u in enumerate(GATE_U[side]):
        w.box(n + "_GateFrameL", u - 175, 10, 0, 345, 28, 22, trim)
        w.box(n + "_GateFrameR", u + 175, 10, 0, 345, 28, 22, trim)
        w.box(n + "_GateHead", u, 10, 330, 370, 378, 22, trim)
        leaf = corr_rust if (gi + len(side)) % 2 else corr_galv
        w.box(n + "_GateLeaf", u, 3, 0, 335, 322, 8, leaf)
        w.box(n + "_GateBeam", u, 9, 150, 162, 322, 6, steel)
        w.box(n + "_GateKick", u, 9, 0, 40, 322, 6, steel)
        w.box(n + "_GateStripe", u, 9, 40, 52, 322, 4, yellow)
        w.cyl(n + "_GateLampArm", u, 22, 345, 350, 10, steel)
        w.box(n + "_GateLamp", u, 22, 372, 395, 40, 26, steel_blue)
    return w

walls = {
    "N": wall("N", (0, HALF), 180, HALF + 100),
    "S": wall("S", (0, -HALF), 0, HALF + 100),
    "E": wall("E", (HALF, 0), 90, HALF),
    "W": wall("W", (-HALF, 0), 270, HALF),
}
# Horizontal pipe runs on the walls under the catwalk (cable tray + two pipes)
for side, w in walls.items():
    hl = HALF - 150
    w.box(side + "_Tray", 0, 8, 388, 400, hl * 2, 16, steel)
    w.box(side + "_TrayWall", 0, 15, 400, 412, hl * 2, 3, steel)
    ka.pipe(b, side + "_Pipe", (*w.xy(-hl, 20), 330), (*w.xy(hl, 20), 330), 14, rust_orange)
    ka.pipe(b, side + "_Pipe2", (*w.xy(-hl, 20), 352), (*w.xy(hl, 20), 352), 10, steel_light)
    for u in range(int(-hl) + 100, int(hl), 450):
        w.box(side + "_PipeBracket", u, 16, 320, 362, 8, 14, steel)

# ------------------------------------------------------------------------------------------------ catwalk ring
ring_c = HALF - RING_WIDTH / 2
ring_t = 40.0
for name, x, y, sx, sy in (("N", 0, ring_c, HALF * 2, RING_WIDTH), ("S", 0, -ring_c, HALF * 2, RING_WIDTH),
                           ("E", ring_c, 0, RING_WIDTH, HALF * 2 - RING_WIDTH * 2),
                           ("W", -ring_c, 0, RING_WIDTH, HALF * 2 - RING_WIDTH * 2)):
    b.box("Ring_" + name, x, y, RING_Z - ring_t / 2, sx, sy, ring_t, mat=plate)

RAMPS = [  # (label, x0, y0, x1, y1, z_top, width)
    ("RingRamp_N", 1000, 750, 1000, INNER, RING_Z, 400),
    ("RingRamp_E", 750, -1000, INNER, -1000, RING_Z, 400),
    ("RingRamp_S", -1000, -750, -1000, -INNER, RING_Z, 400),
    ("RingRamp_W", -750, 1000, -INNER, 1000, RING_Z, 400),
]
TOWER_RAMPS = [
    ("TowerRamp_E", 1350, 0, 450, 0, TOWER_Z, 400),
    ("TowerRamp_W", -1350, 0, -450, 0, TOWER_Z, 400),
    ("TowerRamp_N", 0, 1350, 0, 450, TOWER_Z, 400),
    ("TowerRamp_S", 0, -1350, 0, -450, TOWER_Z, 400),
]


def on_ramp(x, y, pad=60.0):
    for _, x0, y0, x1, y1, _z, wd in RAMPS:
        if abs(x1 - x0) < 1:       # ramp running along y
            if abs(x - x0) < wd / 2 + pad and min(y0, y1) - pad <= y <= max(y0, y1) + pad:
                return True
        elif abs(y - y0) < wd / 2 + pad and min(x0, x1) - pad <= x <= max(x0, x1) + pad:
            return True
    return False


for side, (cx, cy, yaw) in {"N": (0, HALF, 180), "S": (0, -HALF, 0), "E": (HALF, 0, 90), "W": (-HALF, 0, 270)}.items():
    w = ka.Wall(b, (cx, cy), yaw)
    half = HALF if side in "NS" else INNER
    hu = half
    # girders under the deck: two longitudinal, transverse every 3 m, edge channel
    w.box("Ring%s_GirderIn" % side, 0, RING_WIDTH - 12, RING_Z - 90, RING_Z - ring_t, hu * 2, 10, steel_blue)
    w.box("Ring%s_GirderMid" % side, 0, RING_WIDTH * 0.5, RING_Z - 70, RING_Z - ring_t, hu * 2, 10, steel_blue)
    w.box("Ring%s_GirderFlange" % side, 0, RING_WIDTH - 12, RING_Z - 94, RING_Z - 86, hu * 2, 36, steel_blue)
    for u in range(int(-hu) + 150, int(hu), 300):
        w.box("Ring%s_Joist" % side, u, RING_WIDTH / 2, RING_Z - 62, RING_Z - ring_t, 10, RING_WIDTH - 6, steel_blue)
    # columns under the inner edge
    for u in range(int(-hu) + 250, int(hu), 500):
        x, y = w.xy(u, RING_WIDTH - 14)
        if on_ramp(x, y, 110):
            continue
        b.box("Ring%s_Column" % side, x, y, (RING_Z - 90) / 2, 26, 26, RING_Z - 90, mat=steel_blue, solid=True)
        w.box("Ring%s_ColBase" % side, u, RING_WIDTH - 14, 0, 12, 44, 44, steel)
        w.box("Ring%s_ColCap" % side, u, RING_WIDTH - 14, RING_Z - 100, RING_Z - 90, 40, 40, steel)
    # fascia, kick plate, painted edge line and handrail along the inner edge, broken where a ramp arrives
    cuts = []
    for _, x0, y0, x1, y1, _z, wd in RAMPS:
        px, py = x1, y1
        u_r = (px - cx) * w.c + (py - cy) * w.s
        v_r = -(px - cx) * w.s + (py - cy) * w.c
        if abs(v_r - RING_WIDTH) < 30:
            cuts.append((u_r - wd / 2, u_r + wd / 2))
    cuts.sort()
    segs, start = [], -hu
    for c0, c1 in cuts:
        segs.append((start, c0))
        start = c1
    segs.append((start, hu))
    for i, (u0, u1) in enumerate(segs):
        if u1 - u0 > 20:
            w.box("Ring%s_Fascia%d" % (side, i), (u0 + u1) / 2, RING_WIDTH + 2, RING_Z - ring_t - 2, RING_Z + 14,
                  u1 - u0, 5, rail_yel)
            w.box("Ring%s_EdgeLine%d" % (side, i), (u0 + u1) / 2, RING_WIDTH - 12, RING_Z, RING_Z + 0.8,
                  u1 - u0, 14, rail_yel)
            a = (*w.xy(u0, RING_WIDTH - 8), RING_Z)
            c = (*w.xy(u1, RING_WIDTH - 8), RING_Z)
            ka.rail(b, "Ring%s_Rail%d" % (side, i), a, c, rail_yel, post_every=250)


def ramp(label, x0, y0, x1, y1, z_top, width, thickness=40.0, deck=plate):
    p0, p1 = (x0, y0, 0.0), (x1, y1, z_top)
    b.slope(label, p0, p1, width, thickness, mat=deck)
    dx, dy = x1 - x0, y1 - y0
    run = math.hypot(dx, dy)
    length = math.hypot(run, z_top)
    pitch = math.atan2(z_top, run)
    yaw = math.degrees(math.atan2(dy, dx))
    yr = math.radians(yaw)
    lat = (-math.sin(yr), math.cos(yr))
    nrm = (-math.sin(pitch) * math.cos(yr), -math.sin(pitch) * math.sin(yr), math.cos(pitch))
    mid = ((x0 + x1) / 2, (y0 + y1) / 2, z_top / 2 - thickness / 2 * math.cos(pitch))
    for side in (-1, 1):
        off = side * (width / 2 - 5)
        c = (mid[0] + lat[0] * off + nrm[0] * -5, mid[1] + lat[1] * off + nrm[1] * -5, mid[2] + nrm[2] * -5)
        b.box(label + "_Stringer", c[0], c[1], c[2], length, 10, 70, yaw=yaw, pitch=math.degrees(pitch), mat=steel_blue,
              solid=False)
        e0 = (x0 + lat[0] * side * (width / 2 - 3), y0 + lat[1] * side * (width / 2 - 3), 0.0)
        e1 = (x1 + lat[0] * side * (width / 2 - 3), y1 + lat[1] * side * (width / 2 - 3), z_top)
        ka.rail(b, label + "_Rail", e0, e1, rail_yel, post_every=230)
        for t in (0.3, 0.65):                                   # trestle legs under the ramp
            lx = e0[0] + (e1[0] - e0[0]) * t
            ly = e0[1] + (e1[1] - e0[1]) * t
            lz = z_top * t
            b.box(label + "_Leg", lx, ly, (lz - 40) / 2, 18, 18, lz - 40, mat=steel_blue, solid=False)
    # tread strip at the foot of the ramp (hazard)
    fx, fy = x0 + dx / run * 40, y0 + dy / run * 40
    b.box(label + "_Hazard", fx, fy, 2.4, 14, width - 20, 0.8, yaw=yaw, mat=yellow, solid=False)


for r in RAMPS:
    ramp(*r)
for r in TOWER_RAMPS:
    ramp(*r)

# ------------------------------------------------------------------------------------------------ central deck
b.box("Tower_Platform", 0, 0, TOWER_Z - 20, 900, 900, 40, mat=plate)
b.box("Tower_Fascia", 0, 0, TOWER_Z - 46, 912, 912, 12, mat=steel_blue, solid=False)
for k in (-300, 0, 300):                                          # deck joists
    b.box("Tower_Joist", k, 0, TOWER_Z - 56, 12, 880, 24, mat=steel_blue, solid=False)
    b.box("Tower_Joist", 0, k, TOWER_Z - 56, 880, 12, 24, mat=steel_blue, solid=False)
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * 400, sy * 400
        b.box("Tower_Leg", x, y, TOWER_Z / 2 - 20, 100, 100, TOWER_Z - 40, mat=concrete_big)
        b.box("Tower_LegBase", x, y, 14, 130, 130, 28, mat=plinth_mat, solid=False)
        b.box("Tower_LegCap", x, y, TOWER_Z - 46, 124, 124, 12, mat=steel, solid=False)
for sgn in (-1, 1):                                               # X braces between the legs
    for ax in (0, 1):
        pA = (sgn * 400, -400) if ax == 0 else (-400, sgn * 400)
        pB = (sgn * 400, 400) if ax == 0 else (400, sgn * 400)
        ka.strut(b, "Tower_Brace", (pA[0], pA[1], 30), (pB[0], pB[1], TOWER_Z - 60), 7, steel)
        ka.strut(b, "Tower_Brace", (pA[0], pA[1], TOWER_Z - 60), (pB[0], pB[1], 30), 7, steel)
for sgn in (-1, 1):                                               # edge rails with a 4 m gap for the ramp
    for ax in range(2):
        for part in (-1, 1):
            u0, u1 = part * 220, part * 440
            if ax == 0:
                a, c = (sgn * 440, u0, TOWER_Z), (sgn * 440, u1, TOWER_Z)
            else:
                a, c = (u0, sgn * 440, TOWER_Z), (u1, sgn * 440, TOWER_Z)
            ka.rail(b, "Tower_Rail", a, c, rail_yel, post_every=110)
    b.box("Tower_Edge", sgn * 440, 0, TOWER_Z + 0.4, 14, 900, 0.8, mat=yellow, solid=False)
    b.box("Tower_Edge", 0, sgn * 440, TOWER_Z + 0.4, 900, 14, 0.8, mat=yellow, solid=False)
# a bolted maintenance hatch and a painted circle on the deck
ka.disc(b, "Tower_Mark", 0, 0, TOWER_Z + 0.6, 170, 170, 0.6, yellow)
ka.disc(b, "Tower_MarkIn", 0, 0, TOWER_Z + 0.9, 158, 158, 0.6, plate_dark)

# ------------------------------------------------------------------------------------------------ pillars + overhead crane
RUN_Z = 905.0
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * 1700, sy * 1700
        b.box("Pillar", x, y, 450, 200, 200, 900, mat=concrete_big)                # same footprint as the blockout
        b.box("Pillar_Plinth", x, y, 38, 252, 252, 76, mat=plinth_mat, solid=False)
        b.box("Pillar_PlinthCap", x, y, 82, 232, 232, 12, mat=trim, solid=False)
        for z0 in (92, 112):                                                         # hazard band
            b.box("Pillar_Band", x, y, z0 + 10, 206, 206, 18, mat=yellow if z0 == 92 else black_paint, solid=False)
        b.box("Pillar_Corbel", x, y, 868, 270, 270, 36, mat=trim, solid=False)
        b.box("Pillar_Plate", x, y, RUN_Z - 6, 300, 300, 12, mat=steel, solid=False)
        # vertical steel ladder with cage hoops on the outer face
        lx = x + sx * 112
        b.box("Pillar_LadderL", lx, y - 18, 400, 4, 4, 760, mat=steel, solid=False)
        b.box("Pillar_LadderR", lx, y + 18, 400, 4, 4, 760, mat=steel, solid=False)
        for z in range(60, 760, 28):
            b.box("Pillar_Rung", lx, y, z, 3, 38, 3, mat=steel, solid=False)
        # a wall lamp
        ka.strut(b, "Pillar_LampArm", (x - sx * 100, y, 640), (x - sx * 130, y, 660), 4, steel)
# crane runway girders along y on top of the pillars (I-beam: web + two flanges)
for sx in (-1, 1):
    x = sx * 1700
    b.box("Runway_Web", x, 0, RUN_Z + 35, 14, 3500, 70, mat=steel_blue, solid=False)
    b.box("Runway_FlangeTop", x, 0, RUN_Z + 74, 44, 3500, 10, mat=steel_blue, solid=False)
    b.box("Runway_FlangeBot", x, 0, RUN_Z + 2, 44, 3500, 10, mat=steel_blue, solid=False)
    b.box("Runway_Rail", x, 0, RUN_Z + 84, 8, 3500, 10, mat=black_paint, solid=False)
    for y in range(-1650, 1700, 330):
        b.box("Runway_Stiffener", x, y, RUN_Z + 36, 24, 6, 68, mat=steel_blue, solid=False)
# the bridge girder across (box girder), end trucks, trolley, hoist, chains and a ladle
BR_Z = RUN_Z + 98
b.box("Bridge_Girder", 0, 0, BR_Z + 40, 3500, 70, 80, mat=steel_blue, solid=False)
b.box("Bridge_Top", 0, 0, BR_Z + 84, 3500, 90, 8, mat=steel, solid=False)
b.box("Bridge_Walk", 0, 70, BR_Z + 40, 3400, 50, 5, mat=plate_dark, solid=False)
for sx in (-1, 1):
    b.box("Bridge_Truck", sx * 1700, 0, BR_Z + 22, 120, 260, 44, mat=steel, solid=False)
    for sy in (-1, 1):
        b.column("Bridge_Wheel", sx * 1700, sy * 90, BR_Z - 18, BR_Z + 2, 40, mat=black_paint)
for x in range(-1600, 1700, 400):
    ka.strut(b, "Bridge_Diag", (x, 40, BR_Z + 4), (x + 200, 40, BR_Z + 76), 5, steel_blue)
    ka.strut(b, "Bridge_Diag", (x + 200, 40, BR_Z + 76), (x + 400, 40, BR_Z + 4), 5, steel_blue)
TX = -900
b.box("Trolley", TX, 0, BR_Z - 30, 160, 130, 60, mat=steel)
b.box("Trolley_Motor", TX, 70, BR_Z - 20, 80, 50, 60, mat=yellow, solid=False)
ka.strut(b, "Chain", (TX - 25, 0, BR_Z - 60), (TX - 40, 0, 720), 5, black_paint)
ka.strut(b, "Chain", (TX + 25, 0, BR_Z - 60), (TX + 40, 0, 720), 5, black_paint)
ka.cyl(b, "Ladle_Bale", TX, 0, 690, 710, 200, 20, steel)
ka.cyl(b, "Ladle", TX, 0, 510, 690, 190, 190, steel)
ka.cyl(b, "Ladle_Rim", TX, 0, 676, 690, 205, 205, black_paint)
ka.cyl(b, "Ladle_Ring", TX, 0, 580, 592, 204, 204, steel)
# runway end stops and hanging work lights on the bridge
for sx in (-1, 1):
    b.box("Runway_Stop", sx * 1700, 1750, RUN_Z + 90, 40, 16, 40, mat=yellow, solid=False)
    b.box("Runway_Stop", sx * 1700, -1750, RUN_Z + 90, 40, 16, 40, mat=yellow, solid=False)

# ------------------------------------------------------------------------------------------------ low cover blocks -> scrap bins
SCRAP = [(sx * 1500, sy * 400) for sx in (-1, 1) for sy in (-1, 1)] + [(sx * 400, sy * 1550) for sx in (-1, 1) for sy in (-1, 1)]
for i, (x, y) in enumerate(SCRAP):
    kind = i % 4
    yaw = 0.0 if i < 4 else 90.0
    if kind in (0, 2):   # steel scrap bin: rusty bin walls, heap of scrap inside
        b.box("Bin_%d" % i, x, y, 75, 300, 300, 150, mat=corr_rust if kind == 0 else corr_dark)
        b.box("Bin_Rim", x, y, 152, 308, 308, 6, mat=steel, solid=False)
        b.box("Bin_Heap", x, y, 158, 270, 270, 22, mat=scrap, solid=False)
        for j in range(7):
            ka.strut(b, "Scrap", (x + rng.uniform(-110, 110), y + rng.uniform(-110, 110), 160),
                     (x + rng.uniform(-120, 120), y + rng.uniform(-120, 120), 190 + rng.uniform(0, 45)), 6, rust)
        for sxx in (-1, 1):
            b.box("Bin_Foot", x + sxx * 145, y, 7, 14, 320, 14, mat=steel, solid=False)
        b.box("Bin_Stripe", x, y, 115, 303, 303, 8, mat=yellow, solid=False)
    elif kind == 1:      # stacked steel ingots on a concrete pad
        b.box("Ingot_%d" % i, x, y, 75, 300, 300, 150, mat=concrete_big)
        b.box("Ingot_Top", x, y, 153, 280, 280, 6, mat=trim_dirty, solid=False)
        for row in range(4):
            for col in range(3):
                b.box("Ingot", x - 90 + col * 90, y, 166 + row * 18, 80, 230 - row * 10, 16, yaw=yaw if row % 2 else yaw + 90,
                      mat=steel_light if (row + col) % 2 else steel, solid=False)
    else:                # timber pattern store: pallets with wooden crates
        b.box("Pallets_%d" % i, x, y, 75, 300, 300, 150, mat=wood_old)
        for k in range(5):
            b.box("Plank", x, y + 150 + 0.5, 20 + k * 30, 300, 2, 12, mat=wood_dark, solid=False)
        b.box("PalletTop", x, y, 152, 300, 300, 5, mat=wood_dark, solid=False)
        b.box("Crate", x - 40, y - 30, 180, 140, 110, 56, yaw=15, mat=wood_dark, solid=False)
        b.box("Crate", x + 70, y + 40, 178, 100, 100, 52, yaw=-20, mat=wood_old, solid=False)

# ------------------------------------------------------------------------------------------------ soft dark hints (no global illumination here)
# the sky light has no occlusion, so places that should be dim are darkened with soft non-solid gradient quads
for name, x, y, sx, sy in (("N", 0, ring_c, HALF * 2 + 100, 640), ("S", 0, -ring_c, HALF * 2 + 100, 640), ("E", ring_c, 0, 640, HALF * 2 - 300), ("W", -ring_c, 0, 640, HALF * 2 - 300)):
    shade_n.blob(b, "UnderCatwalk_" + name, x, y, 3.4, sx, sy, strength=0.5)
shade_n.blob(b, "UnderTower", 0, 0, 3.4, 1250, 1250, strength=0.5)
for sx in (-1, 1):
    for sy in (-1, 1):
        shade_n.blob(b, "PillarFoot", sx * 1700, sy * 1700, 3.4, 760, 760, strength=0.3)
for i, (x, y) in enumerate(SCRAP):
    shade_n.blob(b, "BinFoot_%d" % i, x, y, 3.4, 520, 520, strength=0.34)
for (rx, ry, sx_, sy_, yw) in ((1000, 1100, 460, 700, 0), (1100, -1000, 700, 460, 0), (-1000, -1100, 460, 700, 0), (-1100, 1000, 700, 460, 0)):
    shade_n.blob(b, "UnderRamp", rx, ry, 3.4, sx_, sy_, strength=0.35, yaw=yw)
for sgn in (-1, 1):                                                  # darker corners of the yard wall bases
    for ax in (0, 1):
        x, y = (sgn * (HALF - 120), 0) if ax == 0 else (0, sgn * (HALF - 120))
        shade_n.blob(b, "WallFoot", x, y, 3.2, 300 if ax == 0 else HALF * 2, HALF * 2 if ax == 0 else 300, strength=0.22)

# ------------------------------------------------------------------------------------------------ spawn points
spawn_pts = []
for sx in (-1, 1):
    for sy in (-1, 1):
        spawn_pts.append((sx * 1900, sy * 1900, 0))
spawn_pts += [(0, 1750, 0), (0, -1750, 0), (1750, 0, 0), (-1750, 0, 0)]
b.face_center_starts(spawn_pts)
avoid = [(x, y, 380) for x, y, _ in spawn_pts]

# ------------------------------------------------------------------------------------------------ props
def P(name, x, y, z=0.0, yaw=0.0, scale=1.0, solid=None):
    return b.prop("P_" + name, name, x, y, z, yaw=yaw, scale=scale, solid=solid)

# north wall (under the ring): drum store and generator
for i, (dx, dy) in enumerate(((0, 0), (60, 15), (25, -62), (-52, -35))):
    P("barrel_red" if i != 2 else "barrel_fire", -1500 + dx, 2285 + dy, yaw=rng.uniform(0, 360))
P("barrel_plastic", -1360, 2300)
P("generator", 300, 2318, yaw=180, scale=1.5)
P("utility_box_a", 150, 2350, yaw=180, scale=1.2)
P("propane_tank", 440, 2330, yaw=30)
P("propane_tank", 480, 2300, yaw=100)
# south wall: pipe stack and crates
for i in range(3):
    P("pipe_b", -1500 + i * 60, -2330, yaw=90, solid=False, scale=1.2)
P("crate_wood_b", -400, -2310, yaw=90, scale=1.3)
P("crate_wood_a", -330, -2300, yaw=95, scale=1.3)
P("crate_wood_b", -380, -2310, z=46, yaw=80, scale=1.3)
P("jerrycan", 1100, -2330, yaw=40, scale=1.2)
P("jerrycan", 1160, -2310, yaw=15, scale=1.2)
for i in range(3):
    P("tyre", 1500, -2310, z=i * 16, yaw=rng.uniform(0, 60), scale=1.4)
P("barrel_red", 2230, -2290)
P("barrel_red", 2165, -2320)
# east wall
P("generator", 2318, -280, yaw=270, scale=1.5)
P("utility_box_a", 2350, -480, yaw=270, scale=1.2)
for i in range(4):
    P("barrel_plastic", 2290 + (i % 2) * 40, 1300 + i * 70, yaw=rng.uniform(0, 360))
P("hydrant_a", 2330, 2000, yaw=90, scale=1.3)
# west wall
P("crate_wood_a", -2310, 700, yaw=0, scale=1.3)
P("crate_wood_b", -2300, 760, yaw=90, scale=1.3)
P("crate_wood_a", -2310, 700, z=35 * 1.3, yaw=8, scale=1.3)
for i in range(3):
    P("barrel_red" if i % 2 == 0 else "barrel_fire", -2290, -1100 - i * 75, yaw=rng.uniform(0, 360))
P("utility_box_a", -2350, -1700, yaw=90, scale=1.2)
P("bin_a", -2320, 1900, scale=1.5)
# security lamps above the gates + hanging lamps on the bridge girder
for side, w in walls.items():
    for u in GATE_U[side]:
        x, y = w.xy(u, 40)
        b.prop("P_lamp_security", "lamp_security", x, y, 396, yaw=w.yaw + 90, scale=1.2, solid=False)
for x in (-1300, -300, 600, 1400):
    b.prop("P_lamp_hanging", "lamp_hanging", x, 0, BR_Z - 142, solid=False)
# small things on the catwalk and the deck: fence panels on the ring (backs against the wall, no routes)
for i in range(3):
    b.prop("P_fence", "fence_b", -1200 + i * 190, 2362, RING_Z, yaw=0, scale=0.9, solid=False)
# forklift-free clutter: scattered rubble/slag piles on the ring and floor corners are small and non-solid
b.scatter(["jerrycan", "tyre", "propane_tank", "crate_wood_a"], ("rect", -2330, -2330, 2330, -2200), 6, seed=5,
          avoid=avoid, solid=False, scale=(1.0, 1.4), min_gap=80, label="FloorClutter")

# ------------------------------------------------------------------------------------------------ the world outside the walls (skyline)
def far_box(label, x, y, z0, z1, sx, sy, mat, yaw=0.0):
    a = b.box(label, x, y, (z0 + z1) / 2, sx, sy, z1 - z0, yaw=yaw, mat=mat, solid=False)
    ka.set_shadow(a, False)
    return a


def far_cyl(label, x, y, z0, z1, dia, mat):
    a = b.column(label, x, y, z0, z1, dia, mat=mat, solid=False)
    ka.set_shadow(a, False)
    return a


def shed(name, x, y, w, d, h, yaw, teeth, wall_mat, roof_mat):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def at(lx, ly):
        return x + c * lx - s * ly, y + s * lx + c * ly
    px, py = at(0, 0)
    far_box(name + "_Body", px, py, -100, h, w, d, wall_mat, yaw)
    tw = w / teeth
    rise = 520.0
    ang = math.atan2(rise, tw)
    for t in range(teeth):
        lx = -w / 2 + t * tw
        cx, cy = at(lx + tw / 2, 0)
        a = b.box(name + "_Roof", cx, cy, h + rise / 2, tw / math.cos(ang), d + 40, 30, yaw=yaw, pitch=math.degrees(ang),
                  mat=roof_mat, solid=False)
        ka.set_shadow(a, False)
        gx, gy = at(lx + tw, 0)
        far_box(name + "_Glaze", gx, gy, h, h + rise, 20, d, pane, yaw)
    for i in range(4):                                                   # roller doors on the long side
        dx, dy = at(-w / 2 + (i + 0.5) * w / 4, -d / 2 - 5)
        far_box(name + "_Door", dx, dy, 0, 560, 520, 20, corr_dark, yaw)


shed("ShedN", -2600, 8200, 6400, 3200, 2400, 0, 5, corr_galv, corr_rust)
shed("ShedS", 2400, -8200, 6000, 3000, 2200, 180, 5, brick, corr_dark)
shed("ShedW", -8400, 1400, 6000, 3200, 2600, 270, 5, corr_galv, corr_galv)
shed("ShedE", 8600, -2400, 5200, 3000, 2000, 90, 4, brick_top, corr_rust)


def stack(name, x, y, h, d0):
    segs = 7
    for i in range(segs):
        z0, z1 = h * i / segs, h * (i + 1) / segs
        dia = d0 * (1.0 - 0.28 * (i / (segs - 1.0)))
        far_cyl("%s_%d" % (name, i), x, y, z0 - 50 if i == 0 else z0, z1, dia, brick_stack)
    far_cyl(name + "_BandA", x, y, h * 0.82, h * 0.90, d0 * 0.74, band_white)
    far_cyl(name + "_BandB", x, y, h * 0.92, h * 0.98, d0 * 0.72, black_paint)
    far_cyl(name + "_Cap", x, y, h * 0.99, h * 1.01, d0 * 0.78, steel)
    far_box(name + "_Base", x, y, -100, 500, d0 * 1.5, d0 * 1.5, brick_top)


stack("StackA", 3800, 9400, 7800, 560)
stack("StackB", -5200, -9000, 6600, 520)
stack("StackC", -9600, 5600, 7200, 600)
stack("StackD", 10200, 4300, 6200, 500)

# silos (a cluster) with cone roofs, a gas holder and a cooling tower
for i, (sx, sy, sd, sh) in enumerate(((9000, -5200, 950, 3000), (9900, -5200, 950, 3400), (9000, -6300, 950, 3000),
                                       (9900, -6300, 950, 2800))):
    far_cyl("Silo_%d" % i, sx, sy, -100, sh, sd, concrete_big)
    cone = b.cone("SiloRoof_%d" % i, sx, sy, sh, sh + 380, sd + 40, mat=steel, solid=False)
    ka.set_shadow(cone, False)
    far_cyl("SiloBand_%d" % i, sx, sy, sh * 0.5, sh * 0.5 + 40, sd + 12, steel)
far_cyl("GasHolder", 3600, -10400, -100, 3200, 3200, steel_blue)
far_cyl("GasHolderRim", 3600, -10400, 3200, 3300, 3350, steel)
ct_prof = [(0, 3400), (500, 3150), (1000, 2950), (1500, 2800), (2000, 2740), (2500, 2800), (3000, 2950), (3500, 3150),
           (4000, 3350), (4500, 3560)]
for i in range(len(ct_prof) - 1):
    far_cyl("CoolTower_%d" % i, -8200, -7600, ct_prof[i][0] - (100 if i == 0 else 0), ct_prof[i + 1][0],
            0.5 * (ct_prof[i][1] + ct_prof[i + 1][1]), band_white if i % 2 else concrete_big)
# pipe rack and gantry crane silhouettes
for i in range(8):
    far_box("RackPost", -3500 + i * 900, 5200, -100, 700, 40, 40, steel, 0)
far_box("RackBeam", 0, 5200, 700, 760, 7400, 60, steel)
ka.pipe(b, "RackPipe", (-3500, 5160, 740), (3500, 5160, 740), 90, rust_orange)
crane = b.prop("P_gantry", "crane_gantry", 4500, 6800, 0, yaw=0, scale=4.0, solid=False)

# more of an industrial skyline: blocks of different heights, brick and steel, one red-white striped stack, a water tower, steam and smoke
for i in range(16):
    ang = i / 16.0 * 2 * math.pi + rng.uniform(-0.12, 0.12)
    d = rng.uniform(9500, 14500)
    bx, by = math.cos(ang) * d, math.sin(ang) * d
    w, dd, hh = rng.uniform(1500, 4200), rng.uniform(900, 2600), rng.uniform(700, 3600)
    mat_ = (brick, corr_galv, corr_dark, concrete_big, brick_top, brick_stack)[i % 6]
    far_box("SkyBlock_%d" % i, bx, by, -100, hh, w, dd, mat_, yaw=math.degrees(ang) + rng.uniform(-20, 20))
    far_box("SkyBlockRoof_%d" % i, bx, by, hh, hh + 90, w + 120, dd + 120, plinth_mat, yaw=math.degrees(ang) + rng.uniform(-20, 20))
    if i % 3 == 0:                                                       # roof plant
        far_box("SkyBlockPlant_%d" % i, bx + w * 0.2, by, hh + 90, hh + 90 + rng.uniform(300, 700), w * 0.3, dd * 0.4, corr_galv)
for z0 in range(0, 6000, 1000):
    far_cyl("StripeStack_%d" % (z0 // 1000), -2600, 10400, z0 - 50 if z0 == 0 else z0, z0 + 1000, 480 - z0 * 0.02, band_white if (z0 // 1000) % 2 else rust_stain)
far_cyl("StripeStackCap", -2600, 10400, 6000, 6080, 380, steel)
far_cyl("WaterTowerTank", 6200, 10800, 2600, 3500, 900, corr_galv)
far_cyl("WaterTowerRoof", 6200, 10800, 3500, 3600, 960, steel)
for lx, ly in ((-380, -380), (380, -380), (380, 380), (-380, 380)):
    far_cyl("WaterTowerLeg", 6200 + lx, 10800 + ly, -100, 2600, 70, steel)
# smoke from the stacks (soft puffs, drifting east) and a big steam plume from the cooling tower
for si, (sx_, sy_, h_) in enumerate(((3800, 9400, 7800), (-5200, -9000, 6600), (-9600, 5600, 7200), (10200, 4300, 6200))):
    for q in range(7):
        f = q / 6.0
        shade_n.puff(b, "StackSmoke_%d_%d" % (si, q), sx_ + 300 + f * f * 3200 + rng.uniform(-100, 100), sy_ + rng.uniform(-150, 150), h_ + 200 + f * 2300,
                     520 + f * 1500 + rng.uniform(0, 200), (0.46, 0.44, 0.42), strength=0.5 - 0.25 * f)
for q in range(9):
    f = q / 8.0
    shade_n.puff(b, "CoolSteam_%d" % q, -8200 + 200 + f * f * 2400, -7600 + rng.uniform(-200, 200), 4500 + 300 + f * 3600, 1500 + f * 2600, (1.05, 1.07, 1.1), strength=0.5 - 0.3 * f)

# ------------------------------------------------------------------------------------------------ light + finish
_over = {k: float(os.environ["IA_" + k.upper()]) for k in ("ev", "sky_intensity", "sun_lux") if os.environ.get("IA_" + k.upper())}
_look = dict(sun_yaw=35.0, ev=0.6, sky_rgb=(1.0, 0.97, 0.90), saturation=0.93)
_look.update(_over)
b.look("day_clear", **_look)
b.finish()
