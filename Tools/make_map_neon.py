"""DM-Neon: a city street at night. Small duel arena (2-4 players), built for fast close fights.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_neon.py" -unattended -nullrhi -nosplash

Layout (unchanged): one street (x -1800..1800, y -800..800) around an arcade hall in the middle. Two shop podiums with a
second roof level on opposite corners, an arcade roof that is reached by stairs or by two jump pads.

Look: night_city light preset, natural asphalt (no wet reflections). The mood comes from street lamps, lit shop windows,
a few thin neon signs with matching small lights and lit windows in the facades (shader), not from glowing walls.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit
import props  # noqa: F401
import mapkit_c as kc
import mapkit_b
import kc_parts as kp
from mapkit_c import rbox, cyl, bar
from matlib import surface, srgb

m = mapkit.MapBuilder("/Game/Maps/DM-Neon")
rng = random.Random(404)

HX, HY = 1800.0, 800.0
ARCADE_Z = 240.0
PINK, CYAN, AMBER, VIOLET, LIME = (1.0, 0.10, 0.55), (0.0, 0.85, 1.0), (1.0, 0.60, 0.15), (0.6, 0.25, 1.0), (0.3, 1.0, 0.4)
WARM = (1.0, 0.72, 0.42)

# ------------------------------------------------------------------------------------------------ materials
def S(name, tag, **kw):
    return surface(name, tag="Neon" + tag, **kw)

asphalt = surface("Asphalt")
asphalt_old = surface("AsphaltCracked")
sidewalk = surface("Sidewalk")
slabs = S("StoneSlabs", "Slabs", albedo=(120, 116, 108))
curb_m = S("ConcreteClean", "Kerb", albedo=(140, 138, 132))
paint_w = S("ConcreteClean", "PaintWhite", albedo=(188, 186, 176))
paint_y = S("ConcreteClean", "PaintYellow", albedo=(196, 160, 60))
brick = S("BrickRed", "Brick2", albedo=(122, 90, 80), desat=0.4)        # a little less orange than the raw scan
brick_dark = surface("BrickDark")
plaster_n = S("PlasterGrey", "PlasterBlue", albedo=(120, 126, 142))
concrete = S("ConcreteClean", "Trim", albedo=(146, 143, 136))             # smooth cast trim (ConcretePanels read like clapboard)
arcade_wall = S("PlasterGrey", "ArcadeWall", albedo=(78, 84, 98))
concrete_dark = surface("ConcreteDark")
steel = surface("BrushedMetal", albedo=(92, 95, 102), tag="SteelLit", metal=0.22, rb=0.12, ns=0.4)   # less metallic: no black shapes without reflections
galv = surface("CorrugatedGalv")
galv_dark = surface("CorrugatedDark")
rust = surface("RustOrange")
diamond = surface("DiamondPlateDark")
rubber = kp.car_rubber_mat()
bin_green = S("ContainerGreen", "Wheelie", albedo=(40, 78, 56), rs=0.8)
bin_grey = S("ContainerGrey", "WheelieGrey", albedo=(70, 72, 76), rs=0.8)
soil = S("DirtDry", "Soil", albedo=(60, 46, 36))
car_glass = kp.car_glass_mat()
car_red, car_blue, car_green = kp.car_paint("Red", (120, 24, 28)), kp.car_paint("Blue", (28, 56, 112)), kp.car_paint("Green", (36, 78, 62))
sack = S("Canvas", "Sack", albedo=(150, 134, 104), desat=0.5)
bark = S("WoodPlanksDark", "Bark", albedo=(58, 46, 38))
tree_leaf = mapkit_b.prop_variant("shrub_b", (0.42, 0.78, 0.38), "NeonTreeGreen")
dump_green = surface("ContainerGreen")
glass_dark = S("PlasterGrey", "ShopGlass", albedo=(24, 30, 40), rb=-0.2)
wood_door = surface("WoodPaintedGrey")


def paint(name, rgb, base="WoodPaintedGrey"):
    return S(base, "P" + name, albedo=rgb)

pa_green, pa_maroon, pa_navy = paint("Green", (44, 72, 60)), paint("Maroon", (96, 44, 46)), paint("Navy", (38, 50, 80))
pa_mustard, pa_char, pa_cream = paint("Mustard", (160, 128, 58)), paint("Char", (50, 50, 55)), paint("Cream", (176, 168, 140))
awn_red, awn_blue, awn_green = surface("CanvasRed"), surface("CanvasBlue"), S("Canvas", "AwnGreen", albedo=(60, 100, 76), desat=1.0)
awn_cream = S("Canvas", "AwnCream", albedo=(186, 178, 156), desat=1.0)
pa_white_f, pa_grey_f = paint("WhiteF", (176, 174, 166)), paint("GreyF", (112, 116, 120))
poster = [paint("Pos%d" % i, c, "PlasterGrey") for i, c in enumerate([(150, 70, 60), (60, 96, 120), (180, 150, 70), (90, 110, 80),
                                                                     (140, 120, 130)])]

# emissive materials (M_IABody): window light is modest, the tubes are thin and saturated
win_warm = kc.emit("NeonShopWarm", (1.0, 0.66, 0.34), 0.17)
win_cool = kc.emit("NeonShopCool", (0.62, 0.84, 1.0), 0.15)
win_dim = kc.emit("NeonShopDim", (1.0, 0.62, 0.30), 0.12)
t_pink, t_cyan, t_amber, t_violet, t_lime = (kc.emit("NeonTubePink", PINK, 1.6), kc.emit("NeonTubeCyan", CYAN, 1.6),
                                            kc.emit("NeonTubeAmber", AMBER, 1.6), kc.emit("NeonTubeViolet", VIOLET, 1.8),
                                            kc.emit("NeonTubeLime", LIME, 1.4))
bulb = kc.emit("NeonBulb", (1.0, 0.78, 0.5), 0.9)
TUBE = {PINK: t_pink, CYAN: t_cyan, AMBER: t_amber, VIOLET: t_violet, LIME: t_lime}

# facades: lit windows come from the facade shader (modest glow, some curtains, some dark)
FRAME_WHITE, FRAME_GREEN, FRAME_GREY, FRAME_CREAM = srgb(172, 170, 160), srgb(40, 66, 54), srgb(112, 116, 120), srgb(168, 156, 128)


def fac(tag, wall, **kw):
    kw.setdefault("lit", 0.26)
    kw.setdefault("glow", 0.25)
    kw.setdefault("min_z", 420.0)
    kw.setdefault("frame_w", 9.0)                 # painted frames, wider than before
    kw.setdefault("sill_boost", 1.55)             # the stone sill under every window is a little lighter
    return kc.facade("Neon" + tag, wall=wall, grid_z=400.0, ground_z=0.0, dirt_h=700.0, **kw)

fac_n = fac("N", "BrickRed", albedo=(120, 88, 78), desat=0.4, seed=21, win=(150, 210), cell=(300, 330), sill=80, frame_rgb=FRAME_WHITE)
fac_s = fac("S", "PlasterGrey", albedo=(122, 124, 136), seed=22, win=(130, 210), cell=(260, 330), sill=80, frame_rgb=FRAME_GREEN)
fac_e = fac("E", "PlasterGrey", albedo=(104, 102, 100), seed=23, win=(150, 210), cell=(300, 330), sill=80, lit=0.2, frame_rgb=FRAME_GREY)
fac_bd = [fac("BD%d" % i, w, albedo=a, seed=30 + i, lit=0.34, glow=0.25, win=wn, cell=cl, sill=sl, min_z=-100000.0, frame_rgb=fr,
              lit_rows=lr, desat=ds)
          for i, (w, a, wn, cl, sl, fr, lr, ds) in enumerate([
              ("BrickDark", None, (150, 200), (300, 330), 100, FRAME_CREAM, 0.0, 0.0),
              ("ConcreteDirty", (110, 108, 104), (160, 200), (300, 330), 100, FRAME_GREY, 0.35, 0.0),
              ("PlasterGrey", (120, 118, 126), (140, 200), (280, 330), 100, FRAME_WHITE, 0.0, 0.0),
              ("ConcreteWorn", (96, 98, 104), (140, 300), (160, 330), 15, FRAME_GREY, 0.5, 0.0),
              ("BrickRed", (116, 80, 70), (150, 200), (300, 330), 100, FRAME_GREEN, 0.0, 0.4)])]

# ------------------------------------------------------------------------------------------------ street shell
m.box("Street", 0, 0, -50, HX * 2, HY * 2, 100, mat=asphalt)
for sy in (-1, 1):                                                   # sidewalks along both facades (flat, same level)
    m.box("Sidewalk", 0, sy * (HY - 80), 2, HX * 2, 160, 4, mat=sidewalk, solid=False)
    m.box("Kerb", 0, sy * (HY - 164), 3.5, HX * 2, 14, 7, mat=curb_m, solid=False)
for x in range(-1500, 1501, 300):                                    # dashed center line
    m.box("RoadLine", x, 0, 1.2, 150, 14, 2.4, mat=paint_w, solid=False)
for y in (-HY + 190, HY - 190):                                      # edge lines
    m.box("EdgeLine", 0, y, 1.2, HX * 2 - 100, 10, 2.4, mat=paint_w, solid=False)
for cx in (-1280, 1280):                                             # zebra crossings
    for k in range(-4, 5):
        m.box("Zebra", cx, k * 90, 1.2, 240, 46, 2.4, mat=paint_w, solid=False)
for i, (x, y) in enumerate([(-640, -130), (710, 220), (210, -560), (-300, 480)]):   # manholes
    rbox(m, "Manhole%d" % i, x, y, 1.6, 76, 76, 3.2, mat=diamond, solid=False, mesh=m.cylinder)
    rbox(m, "ManholeRing%d" % i, x, y, 1.0, 90, 90, 2.0, mat=concrete_dark, solid=False, mesh=m.cylinder)
for i, (x, y, sx_, sy_, yaw) in enumerate([(-900, 80, 260, 160, 8), (400, -300, 340, 140, -5), (1100, 120, 220, 200, 20),
                                           (-1500, -300, 300, 180, 0)]):   # patched asphalt
    m.box("Patch%d" % i, x, y, 1.0, sx_, sy_, 2.0, yaw=yaw, mat=asphalt_old, solid=False)
for sy in (-1, 1):                                                   # drain grates at the kerb
    for x in (-700, 600, 1500):
        m.box("Grate", x * (1 if sy > 0 else -1), sy * (HY - 190), 1.5, 90, 36, 3, mat=steel, solid=False)

# the two long facades and the end walls (the facade shader draws windows above the shops)
m.box("Facade_N", 0, HY + 150, 650, HX * 2 + 600, 300, 1500, mat=fac_n)
m.box("Facade_S", 0, -(HY + 150), 650, HX * 2 + 600, 300, 1500, mat=fac_s)
for sx in (-1, 1):
    m.box("EndWall", sx * (HX + 150), 0, 650, 300, HY * 2, 1500, mat=fac_e)
for sy in (-1, 1):                                                   # cornice and parapet at the top of the facades
    m.box("Cornice", 0, sy * (HY - 12), 1385, HX * 2, 30, 36, mat=concrete, solid=False)
    m.box("CorniceTop", 0, sy * (HY + 20), 1428, HX * 2 + 100, 60, 18, mat=concrete, solid=False)
    for k in range(1, 3):                                            # string courses between the floors
        m.box("Course", 0, sy * (HY - 7), 400 + 330 * k, HX * 2, 14, 26, mat=concrete, solid=False)
    m.box("PlinthBand", 0, sy * (HY - 6), 410, HX * 2, 12, 20, mat=concrete, solid=False)
    for x in range(-1650, 1700, 300):                                # pilasters between window bays on the ground floor
        m.box("Pilaster", x, sy * (HY - 9), 205, 36, 18, 410, mat=concrete_dark, solid=False)
for sx in (-1, 1):
    m.box("EndCornice", sx * (HX - 12), 0, 1385, 30, HY * 2, 36, mat=concrete, solid=False)


# ------------------------------------------------------------------------------------------------ shops on the facades
def base_z(s, x):
    """Floor height in front of the facade at x (the podiums raise the shop floor)."""
    xx = s * x                       # south podium is the north one rotated by 180 degrees
    if xx < -1110:
        return 240.0
    if xx < -740:
        return 120.0
    return 0.0


def text_yaw(s):
    return 180.0 if s > 0 else 0.0   # viewers on the north side look toward +y: text reads along -x


def post(label, x, y, z, nax, w, h, i):
    """A flyer on a wall: a paper sheet with a dark title bar, a picture block and a text line.
    nax = axis of the wall normal ('x' or 'y'); (x, y, z) = centre of the sheet."""
    def part(dz, sw, sh, mat, th):
        if nax == "x":
            m.box(label, x, y, z + dz, th, sw, sh, mat=mat, solid=False)
        else:
            m.box(label, x, y, z + dz, sw, th, sh, mat=mat, solid=False)
    part(0, w, h, poster[i % 5], 2.6)
    part(h * 0.31, w * 0.80, h * 0.15, pa_char, 3.2)
    part(-h * 0.06, w * 0.62, h * 0.34, poster[(i + 2) % 5], 3.2)
    part(-h * 0.37, w * 0.70, h * 0.05, pa_char, 3.2)


STICK = [(0.85, 0.15, 0.15), (0.95, 0.8, 0.1), (0.1, 0.5, 0.85), (0.9, 0.9, 0.9), (0.1, 0.7, 0.4)]
_stick_mats = {}


def sticker(label, x, y, z, nax, i, d=11.0):
    """A round sticker (disc) on a wall."""
    key = i % len(STICK)
    if key not in _stick_mats:
        c = STICK[key]
        _stick_mats[key] = S("PlasterGrey", "Stick%d" % key, albedo=tuple(int(255 * v ** 0.45) for v in c), rb=-0.2)
    if nax == "x":
        rbox(m, label, x, y, z, d, d, 0.9, pitch=90, mat=_stick_mats[key], solid=False, mesh=m.cylinder)
    else:
        rbox(m, label, x, y, z, d, d, 0.9, roll=90, mat=_stick_mats[key], solid=False, mesh=m.cylinder)


def swag(label, p0, p1, sag, n=7, th=2.2, mat=None):
    """A sagging cable between two points (n straight pieces)."""
    mat = mat or rubber
    pts = [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n,
            p0[2] + (p1[2] - p0[2]) * i / n - sag * 4.0 * (i / n) * (1 - i / n)) for i in range(n + 1)]
    for i in range(n):
        bar(m, label, pts[i], pts[i + 1], th, mat=mat, solid=False)


def wheelie(label, x, y, yaw, mat):
    """A wheeled bin with a lid (decoration)."""
    base = (x, y, 0, yaw)
    kp.local_box(m, label + "_body", 0, 0, 46, 56, 60, 92, base, mat=mat, solid=False)
    kp.local_box(m, label + "_top", 0, 0, 90, 60, 64, 6, base, mat=mat, solid=False)
    kp.local_box(m, label + "_lid", 0, -2, 96, 62, 66, 5, base, mat=mat, solid=False, pitch=-6)
    kp.local_box(m, label + "_stripe", 0, 31, 62, 40, 1.4, 14, base, mat=pa_white_f, solid=False)
    for sx_ in (-22, 22):
        kp.local_box(m, label + "_wheel", sx_, -26, 9, 6, 16, 16, base, mat=rubber, solid=False)


def aframe(label, x, y, yaw, mat):
    """A sandwich board (A-frame) with a dark writing panel."""
    base = (x, y, 0, yaw)
    for sg in (-1, 1):
        kp.local_box(m, label + "_leg", 0, sg * 17, 44, 52, 3.5, 90, base, mat=mat, solid=False, roll=sg * 10)
    kp.local_box(m, label + "_panel", 0, 18.5, 46, 40, 1.2, 62, base, mat=pa_char, solid=False, roll=10)
    kp.local_box(m, label + "_panelb", 0, -18.5, 46, 40, 1.2, 62, base, mat=pa_char, solid=False, roll=-10)
    kp.local_box(m, label + "_chalk", 0, 19.4, 52, 28, 0.6, 3, base, mat=pa_white_f, solid=False, roll=10)
    kp.local_box(m, label + "_chalk2", 0, 19.4, 40, 20, 0.6, 3, base, mat=pa_white_f, solid=False, roll=10)


def hang_sign(label, x, s, z0, board, logo):
    """A shop sign on a bracket that sticks out of the wall into the street (north wall s=1, south wall s=-1)."""
    y0, y1 = s * (HY - 8), s * (HY - 74)
    zb = z0 + 322
    bar(m, label + "_arm", (x, y0, zb), (x, y1, zb), 4.0, mat=steel, solid=False)
    bar(m, label + "_brace", (x, y0, zb - 40), (x, s * (HY - 52), zb - 2), 3.0, mat=steel, solid=False)
    ym = s * (HY - 48)
    for yy in (s * (HY - 28), s * (HY - 66)):
        bar(m, label + "_chain", (x, yy, zb), (x, yy, zb - 22), 1.6, mat=steel, solid=False)
    rbox(m, label + "_board", x, ym, zb - 22 - 19, 4, 52, 38, mat=board, solid=False)
    rbox(m, label + "_edge", x, ym, zb - 22 - 19, 5, 56, 42, mat=pa_char, solid=False)
    rbox(m, label + "_logo", x, ym, zb - 22 - 19, 6, 22, 22, mat=logo, solid=False, mesh=m.cylinder, pitch=90)


def neon_sign(label, text, x, y, z, yaw, rgb, height, light=True, thick=3.5, cd=25.0, rad=650.0, panel=True, off=60.0):
    """Neon letters on a dark backing board (at x, y), with a small matching light in front (toward the street).
    yaw = reading direction of the text; the wall normal (toward the viewer) is (-sin yaw, cos yaw)."""
    mat = TUBE[rgb]
    nx, ny = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
    width = kc.neon_text(m, label, text, x + nx * 8, y + ny * 8, z, 0, height, mat, thick=thick, yaw=yaw)
    if panel:
        along_x = abs(math.cos(math.radians(yaw))) > 0.5
        sx_, sy_ = (width + 34, 6) if along_x else (6, width + 34)
        rbox(m, label + "_board", x, y, z, sx_, sy_, height + 30, mat=pa_char, solid=False)
    if light:
        m.accent_light(label + "_light", (x + nx * off, y + ny * off, z), rgb, candela=cd, radius=rad)
    return width


def shopfront(s, x, w, kind, name, sign=None, awning=None, fascia=None):
    """One shop bay on the wall of side s (+1 north wall y=+800, -1 south wall y=-800), centre x, width w."""
    z0 = base_z(s, x)
    wy = lambda d: s * (HY - d)       # y at distance d from the wall, into the street
    yaw_t = text_yaw(s)
    fmat = fascia or pa_char
    # window frames are painted in a muted colour that goes with the fascia (white, dark green, grey ...)
    frame_paint = {id(pa_maroon): pa_cream, id(pa_green): pa_cream, id(pa_navy): pa_white_f, id(pa_mustard): pa_char,
                   id(pa_char): pa_grey_f}.get(id(fmat), pa_cream)
    # stall riser, frame, pilasters
    m.box(name + "_riser", x, wy(5), z0 + 40, w - 24, 10, 80, mat=pa_char, solid=False)
    m.box(name + "_fascia", x, wy(8), z0 + 372, w - 12, 16, 84, mat=fmat, solid=False)
    m.box(name + "_fasciaTop", x, wy(11), z0 + 421, w - 4, 22, 14, mat=concrete_dark, solid=False)
    if kind == "glass":
        cx_ = x
        m.box(name + "_pane", cx_, wy(4), z0 + 205, w - 52, 5, 240, mat=win_warm if sign != "PHONES" else win_cool, solid=False)
        m.frame(name + "_frame", cx_, wy(7), z0 + 80, w - 40, 250, 10, 8, 0 if s < 0 else 0, frame_paint, solid=False)
        m.box(name + "_mullion", cx_, wy(8), z0 + 205, 7, 7, 240, mat=frame_paint, solid=False)
        m.box(name + "_transom", cx_, wy(8), z0 + 268, w - 56, 7, 6, mat=frame_paint, solid=False)
        m.box(name + "_sill", cx_, wy(14), z0 + 79, w - 28, 16, 5, mat=concrete, solid=False)       # lighter stone sill
        for k, zz in enumerate((150, 235, 300)):                    # shelves seen through the window
            m.box(name + "_shelf%d" % k, cx_ - (w / 4) * (1 if k % 2 else -1) * 0.6, wy(9), z0 + zz, (w - 90) * 0.42, 6, 5,
                  mat=pa_char, solid=False)
        m.accent_light(name + "_pool", (x, wy(70), z0 + 220), (1.0, 0.72, 0.42) if sign != "PHONES" else (0.7, 0.85, 1.0),
                       candela=10, radius=520)
    elif kind == "door":
        m.frame(name + "_doorframe", x - w * 0.12, wy(7), z0, 120, 250, 12, 10, 0, frame_paint, solid=False)
        m.box(name + "_door", x - w * 0.12, wy(6), z0 + 118, 100, 6, 236, mat=wood_door, solid=False)
        m.box(name + "_doorpane", x - w * 0.12, wy(9.5), z0 + 190, 56, 3, 90, mat=win_dim, solid=False)
        m.box(name + "_step", x - w * 0.12, wy(30), z0 + 3, 150, 50, 6, mat=concrete_dark, solid=False)
        m.box(name + "_lampbox", x + w * 0.22, wy(9), z0 + 245, 22, 14, 22, mat=steel, solid=False)
        m.box(name + "_lampglow", x + w * 0.22, wy(17), z0 + 245, 14, 6, 14, mat=bulb, solid=False)
        m.accent_light(name + "_doorlamp", (x + w * 0.22, wy(45), z0 + 240), WARM, candela=6, radius=420)
        m.box(name + "_sidewin", x + w * 0.2, wy(4), z0 + 215, w * 0.36, 5, 120, mat=glass_dark, solid=False)
        m.frame(name + "_sidewinframe", x + w * 0.2, wy(6), z0 + 150, w * 0.36 + 10, 130, 7, 6, 0, frame_paint, solid=False)
        m.box(name + "_sidesill", x + w * 0.2, wy(12), z0 + 148, w * 0.36 + 16, 14, 4, mat=concrete, solid=False)
    else:  # roller shutter
        sh = rust if (name.endswith("a")) else galv_dark
        m.box(name + "_shutter", x, wy(10), z0 + 150, w - 40, 8, 300, mat=sh, solid=False)
        m.box(name + "_housing", x, wy(14), z0 + 312, w - 30, 22, 26, mat=steel, solid=False)
        for gx in (-1, 1):
            m.box(name + "_guide", x + gx * (w / 2 - 22), wy(11), z0 + 150, 12, 14, 300, mat=steel, solid=False)
    if awning is not None:
        roll = -14 if s > 0 else 14
        rbox(m, name + "_awning", x, wy(62), z0 + 330, w + 20, 130, 5, pitch=0, roll=roll, mat=awning, solid=False)
        n_str = max(4, int((w + 20) // 38))
        for q in range(0, n_str, 2):                                   # cream stripes across the canvas
            sx_ = x - (w + 20) / 2 + (q + 0.5) * (w + 20) / n_str
            rbox(m, name + "_stripe", sx_, wy(62), z0 + 330, (w + 20) / n_str, 130.5, 5.6, pitch=0, roll=roll, mat=awn_cream,
                 solid=False)
        edge_y = wy(62) - s * 63.0                                     # front flap hangs from the outer edge
        rbox(m, name + "_valance", x, edge_y, z0 + 302, w + 20, 3.5, 24, mat=awning, solid=False)
        for gx in (-1, 1):
            rbox(m, name + "_awnframe", x + gx * (w / 2 + 8), wy(62), z0 + 330, 5, 130, 5, roll=roll, mat=steel, solid=False)
    if sign:
        col = {"NOODLES": PINK, "PIZZA": AMBER, "BAR": CYAN, "24H": LIME, "HOTEL": VIOLET, "CAFE": AMBER, "PHONES": CYAN,
               "TAKEAWAY": PINK}[sign]
        neon_sign(name + "_sign", sign, x, wy(14), z0 + 372, yaw_t, col, 40 if len(sign) > 4 else 46, cd=20.0, rad=520.0)


shops_n = [(-1520, 360, "glass", "NOODLES", awn_red, pa_maroon), (-1170, 320, "door", None, None, pa_green),
           (-850, 300, "shutter", None, None, pa_navy), (-560, 290, "glass", "PIZZA", awn_green, pa_char),
           (-270, 300, "door", None, None, pa_mustard), (60, 360, "glass", "PHONES", None, pa_navy),
           (440, 360, "shutter", None, None, pa_maroon), (800, 300, "glass", "BAR", None, pa_char),
           (1130, 320, "door", None, None, pa_green), (1450, 380, "glass", "24H", awn_blue, pa_char)]
shops_s = [(1520, 360, "glass", "CAFE", awn_blue, pa_green), (1170, 320, "shutter", None, None, pa_char),
           (850, 300, "door", None, None, pa_maroon), (560, 290, "glass", "HOTEL", None, pa_navy),
           (270, 300, "shutter", None, None, pa_mustard), (-60, 360, "door", None, None, pa_char),
           (-440, 360, "glass", None, awn_red, pa_char), (-800, 300, "door", None, None, pa_navy),
           (-1130, 320, "glass", "TAKEAWAY", None, pa_maroon), (-1450, 380, "shutter", None, None, pa_green)]
for i, (x, w, kind, sign, awn, fas) in enumerate(shops_n):
    shopfront(1, x, w, kind, "ShopN%d%s" % (i, "a" if i % 2 == 0 else "b"), sign, awn, fas)
for i, (x, w, kind, sign, awn, fas) in enumerate(shops_s):
    shopfront(-1, x, w, kind, "ShopS%d%s" % (i, "a" if i % 2 == 0 else "b"), sign, awn, fas)

# vertical blade signs sticking out into the street (thin, with a small light)
for x, sy, rgb, word in [(-1250, 1, PINK, "BAR"), (1250, -1, CYAN, "INN"), (400, 1, LIME, "24H"), (-400, -1, AMBER, "PUB")]:
    z = 690.0
    y0 = sy * (HY - 100)
    m.box("BladeMount", x, sy * (HY - 40), z + 170, 14, 90, 14, mat=steel, solid=False)
    m.box("BladeBoard", x, y0, z, 12, 70, 320, mat=pa_char, solid=False)
    m.frame("BladeFrame", x, y0, z - 160, 78, 322, 4, 14, 90, TUBE[rgb], solid=False)
    for k, ch in enumerate(word):                                   # letters stacked, readable from both sides
        for fx, yawk in ((7, -90), (-7, 90)):
            kc.neon_text(m, "Blade_%s_%d%s" % (word, k, "a" if fx > 0 else "b"), ch, x + fx, y0, z + 90 - k * 90, 0, 56, TUBE[rgb],
                         thick=3.5, yaw=yawk)
    m.accent_light("BladeLight_%s" % word, (x, sy * (HY - 220), z), rgb, candela=30, radius=700)

# wires across the street and fire escapes / drainpipes / window units / pipes on the upper floors
for i, (x, z0, z1) in enumerate([(-1350, 1010, 1040), (-300, 960, 990), (700, 1080, 1100), (1500, 930, 960)]):
    bar(m, "Wire%d" % i, (x, -HY + 20, z0), (x + 40, HY - 20, z1), 2.5, mat=rubber, solid=False)
    bar(m, "WireB%d" % i, (x + 20, -HY + 20, z0 - 24), (x + 80, HY - 20, z1 - 20), 2.0, mat=rubber, solid=False)
for i, (x, sy, name) in enumerate([(-600, 1, "fire_escape_a"), (1000, 1, "fire_escape_b"), (500, -1, "fire_escape_a"),
                                   (-1100, -1, "fire_escape_b")]):
    m.prop("FireEscape%d" % i, name, x, sy * (HY - 80), 690 if name == "fire_escape_a" else 710, yaw=0 if sy < 0 else 180,
           solid=False)
for i, x in enumerate([-1740, -250, 790, 1730, -1000, 1350]):        # drain pipes
    sy = 1 if i % 2 == 0 else -1
    cyl(m, "Drain%d" % i, (x, sy * (HY - 12), 1380), (x, sy * (HY - 12), 20), 14, mat=steel, solid=False)
for i in range(14):                                                  # window units and cable boxes
    sy = rng.choice((-1, 1))
    x = 150 + 300 * rng.randint(-5, 5)
    z = 400 + 330 * rng.randint(0, 2) + 90
    m.prop("WinAC%d" % i, "aircon_a", x, sy * (HY + 18), z, yaw=0 if sy < 0 else 180, solid=False)
for i, (x, sy) in enumerate([(-1000, 1), (150, 1), (1250, 1), (-750, -1), (350, -1), (1100, -1)]):
    m.prop("Duct%d" % i, "duct_a", x, sy * (HY - 25), 1100 + 40 * (i % 3), yaw=90 if sy > 0 else 270, solid=False)
    m.prop("PipeV%d" % i, "pipe_b", x + 160, sy * (HY - 14), 1000, yaw=0, solid=False)
# roof silhouettes above the cornice (against the night sky)
for i, (x, sy) in enumerate([(-1300, 1), (-300, 1), (900, 1), (1500, -1), (300, -1), (-1100, -1)]):
    kp.water_tank(m, "RoofTank%d" % i, x, sy * (HY + 150), 1400, 260, 380, wood_door, steel, concrete_dark, solid=False) if i % 3 == 0 \
        else rbox(m, "RoofBox%d" % i, x, sy * (HY + 150), 1400 + 110, 240, 200, 220, mat=concrete_dark, solid=False)
for i, x in enumerate([-1650, -800, 200, 1100, 1700]):
    rbox(m, "RoofAntenna%d" % i, x, (HY + 200) * (1 if i % 2 else -1), 1400 + 260, 8, 8, 520, mat=steel, solid=False)


# ------------------------------------------------------------------------------------------------ podiums (north one built, south one is its mirror)
def side(s):
    """s = +1 builds the north podium group, s = -1 the south one (rotated 180 degrees)."""
    def P(x, y):
        return (s * x, s * y)
    tag = "N" if s > 0 else "S"
    # lower podium (z 0..120) and upper podium (z 120..240): terrace with a brick plinth
    x, y = P(-1220, 610)
    m.box("Podium1_" + tag, x, y, 60, 960, 380, 120, mat=slabs)
    m.box("Podium1Face_" + tag, x, s * 419, 52, 964, 8, 104, mat=brick_dark, solid=False)
    m.box("Podium1Cap_" + tag, x, s * 422, 122, 972, 22, 5, mat=curb_m, solid=False)
    x, y = P(-1405, 610)
    m.box("Podium2_" + tag, x, y, 180, 590, 380, 120, mat=slabs)
    m.box("Podium2Face_" + tag, x, s * 419, 172, 594, 8, 104, mat=brick_dark, solid=False)
    m.box("Podium2Cap_" + tag, x, s * 422, 242, 602, 22, 5, mat=curb_m, solid=False)
    # ramps (rise 24 / run 44 keeps the slope under what the 150 cm navigation grid can link)
    x, y = P(-300, 700)
    xe, ye = P(-740, 700)
    m.slope("RampA_" + tag, (x, y, 0), (xe, ye, 120), 200, thickness=50, mat=diamond)
    x, y = P(-740, 520)
    xe, ye = P(-1110, 520)
    m.slope("RampB_" + tag, (x, y, 120), (xe, ye, 240), 220, thickness=50, mat=diamond)
    for rr, (a, b2, w_) in enumerate([((-300, 700), (-740, 700), 200), ((-740, 520), (-1110, 520), 220)]):
        (ax, ay), (bx, by) = P(*a), P(*b2)
        z_a, z_b = (0, 120) if rr == 0 else (120, 240)
        for sd in (-1, 1):
            off = sd * (w_ / 2 - 4)
            bar(m, "RampRail%d%s" % (rr, tag), (ax, ay + off, z_a + 90), (bx, by + off, z_b + 90), 5, mat=steel, solid=False)
            for t in (0.0, 0.5, 1.0):
                rbox(m, "RampPost", ax + (bx - ax) * t, ay + off + (by - ay) * t, z_a + (z_b - z_a) * t + 45, 6, 6, 90,
                     mat=steel, solid=False)
    # railings along the street side of each podium (solid thin panel as before, with a round top rail and posts)
    x, y = P(-1220, 424)
    m.box("Rail1_" + tag, x, y, 160, 960, 12, 80, mat=galv_dark)
    x2, y2 = P(-1405, 424)
    m.box("Rail2_" + tag, x2, y2, 280, 590, 12, 80, mat=galv_dark)
    for (px0, ln, zz, nm) in ((-1220, 960, 120, "1"), (-1405, 590, 240, "2")):
        px, py = P(px0, 424)
        m.box("RailTop" + nm + tag, px, py, zz + 84, ln + 10, 18, 6, mat=steel, solid=False)
        for k in range(int(ln // 160) + 1):
            qx, qy = P(px0 - ln / 2 + k * ln / max(1, int(ln // 160)), 424)
            m.box("RailPost", qx, qy, zz + 44, 8, 8, 90, mat=steel, solid=False)
    # vent unit and crate on the upper podium
    x, y = P(-1550, 700)
    kp.chiller(m, "Vent_" + tag, x, y, 240, 220, 160, 160, 0, galv, steel, galv)
    x, y = P(-1300, 650)
    m.box("Crate_" + tag, x, y, 295, 120, 120, 110, yaw=20, mat=surface("WoodPlanksDark"))
    # pad from the street lane to the arcade roof
    x, y = P(0, 560)
    m.jump_pad("RoofPad_" + tag, x, y, 0, (0, s * 220, ARCADE_Z), color=CYAN if s > 0 else PINK)
    # street lamps along the lane
    for lx in (-1000, 1000):
        px, py = P(lx, 440)
        m.prop("LampPost_%s%d" % (tag, lx), "lamp_street_a", px, py, 0, yaw=(90 if s > 0 else 270), solid=True)
        m.accent_light("LampLight_%s%d" % (tag, lx), (px, py + (-s) * 60, 360), WARM, candela=140, radius=1100)


side(1)
side(-1)

# ------------------------------------------------------------------------------------------------ arcade hall in the middle
m.box("Arcade", 0, 0, ARCADE_Z / 2, 500, 860, ARCADE_Z, mat=arcade_wall)
m.box("ArcadeBase", 0, 0, 14, 520, 880, 28, mat=concrete_dark, solid=False)
m.box("ArcadeCornice", 0, 0, ARCADE_Z - 10, 530, 890, 20, mat=curb_m, solid=False)
m.box("ArcadeRoofCap", 0, 0, ARCADE_Z + 1, 496, 856, 2, mat=surface("RoofTarmac"), solid=False)
for sx in (-1, 1):                                                   # the long faces: dark display band, marquee with neon letters
    m.box("MarqueePanel", sx * 256, 0, 152, 8, 700, 120, mat=pa_char, solid=False)
    m.box("MarqueeFrameT", sx * 258, 0, 216, 6, 716, 8, mat=steel, solid=False)
    m.box("MarqueeFrameB", sx * 258, 0, 90, 6, 716, 8, mat=steel, solid=False)
    kc.neon_text(m, "ArcadeText_%d" % sx, "ARCADE", sx * 260, 0, 152, 0, 66, t_pink if sx > 0 else t_cyan, thick=4.0,
                 yaw=(-90 if sx > 0 else 90))
    m.accent_light("MarqueeLight%d" % sx, (sx * 330, 0, 200), PINK if sx > 0 else CYAN, candela=40, radius=800)
    for k in range(-2, 3):                                           # lower posters
        post("ArcadePoster", sx * 254, k * 130, 55, "x", 62, 78, k + 2 + (sx > 0))
for sy in (-1, 1):                                                   # arcade doors facing the lanes
    m.frame("ArcadeDoor", 0, sy * 432, 0, 260, 215, 14, 12, 0, steel, solid=False)
    m.box("ArcadeDoorGlow", 0, sy * 431, 105, 232, 4, 200, mat=win_warm, solid=False)
    m.box("ArcadeDoorBar", 0, sy * 433, 105, 8, 6, 200, mat=steel, solid=False)
    m.box("ArcadeCanopy", 0, sy * 462, 232, 300, 70, 8, mat=pa_char, solid=False)
    m.accent_light("ArcadeDoorLight%d" % sy, (0, sy * 500, 180), (1.0, 0.7, 0.45), candela=18, radius=650)
# roof access stairs along the east face (24 steps), with handrails
m.slope("ArcadeRamp", (1000, 0, 0), (250, 0, ARCADE_Z), 260, thickness=50, mat=diamond)
for sd in (-1, 1):
    bar(m, "ArcadeRampRail", (1000, sd * 126, 90), (250, sd * 126, ARCADE_Z + 90), 5, mat=steel, solid=False)
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        rbox(m, "ArcadeRampPost", 1000 - 750 * t, sd * 126, ARCADE_Z * t + 45, 6, 6, 90, mat=steel, solid=False)
m.box("ArcadeRoofRailW", -244, 0, ARCADE_Z + 40, 12, 860, 80, mat=concrete_dark)
m.box("ArcadeRoofRailWCap", -244, 0, ARCADE_Z + 84, 24, 870, 8, mat=curb_m, solid=False)
kp.chiller(m, "ArcadeRoofAC1", -150, -230, ARCADE_Z, 160, 120, 90, 10, galv, steel, galv, solid=False)
kp.chiller(m, "ArcadeRoofAC2", -170, 310, ARCADE_Z, 140, 110, 80, -12, galv, steel, galv, solid=False)
m.box("ArcadeRoofHatch", 120, -280, ARCADE_Z + 14, 100, 80, 28, mat=galv, solid=False)
m.box("ArcadeRoofLampBox", -200, 40, ARCADE_Z + 70, 30, 30, 140, mat=steel, solid=False)
m.accent_light("RoofLight", (-200, 40, ARCADE_Z + 160), WARM, candela=35, radius=800)
m.box("RoofAntenna", -150, 200, ARCADE_Z + 250, 8, 8, 500, mat=steel, solid=False)
for hz in (330, 400, 460):
    m.box("RoofAntennaArm", -150, 200, ARCADE_Z + hz, 4, 90 - (hz - 330) * 0.3, 4, mat=steel, solid=False)
rbox(m, "RoofAntennaTip", -150, 200, ARCADE_Z + 505, 14, 14, 14, mat=TUBE[PINK], solid=False, mesh=m.cylinder)

# ------------------------------------------------------------------------------------------------ plazas: partitions, cars, planters, gates
for sx in (-1, 1):
    m.box("PlazaWall", sx * 1550, 0, 150, 300, 40, 300, mat=brick)
    m.box("PlazaWallCap", sx * 1550, 0, 306, 316, 56, 12, mat=curb_m, solid=False)
    m.box("PlazaWallBand", sx * 1550, 0, 40, 306, 46, 80, mat=concrete_dark, solid=False)
    for k, yy in enumerate((-1, 1)):                                 # a poster and a small lamp on each side of the wall
        post("PlazaPoster", sx * 1550 + (-60 if k == 0 else 60), yy * 22, 170, "y", 84, 120, k + (sx > 0) * 2)
        sticker("PlazaSticker", sx * 1550 + (-110 if k == 0 else 110), yy * 21, 130 + 40 * k, "y", k + sx)
    # end of the street: roller gate, side posts, warm lamp
    ex = sx * (HX - 6)
    m.box("EndGate", ex, 0, 280, 10, 560, 560, mat=galv_dark, solid=False)
    for k in range(-5, 6):
        m.box("EndGateRib", ex - sx * 5, k * 50, 280, 4, 8, 560, mat=steel, solid=False)
    m.box("EndGateHousing", ex - sx * 12, 0, 580, 24, 600, 36, mat=steel, solid=False)
    for yy in (-1, 1):
        m.box("EndGatePost", ex - sx * 8, yy * 296, 290, 20, 24, 580, mat=concrete_dark, solid=False)
    m.box("EndLampBox", ex - sx * 20, 0, 640, 16, 60, 18, mat=steel, solid=False)
    m.box("EndLampGlow", ex - sx * 30, 0, 636, 10, 50, 8, mat=bulb, solid=False)
    m.accent_light("GateLight%d" % sx, (ex - sx * 120, 0, 560), (1.0, 0.7, 0.4), candela=60, radius=1300)
    cyl(m, "EndPipe%d" % sx, (ex - sx * 20, 340, 900), (ex - sx * 20, 340, 20), 16, mat=steel, solid=False)
    cyl(m, "EndPipe2%d" % sx, (ex - sx * 20, -340, 900), (ex - sx * 20, -340, 20), 16, mat=steel, solid=False)

tail_lamp = kc.emit("NeonTail", (1.0, 0.05, 0.05), 0.35)
kp.car(m, "CarA", 1450, 300, 0, 12, car_red, car_glass, rubber, "sedan", solid=True, tail=tail_lamp)
kp.car(m, "CarB", -900, -220, 0, -8, car_blue, car_glass, rubber, "hatch", solid=True, tail=tail_lamp)

for i, (x, y) in enumerate([(-450, 250), (450, -250), (1200, -230), (-1200, 230), (1000, 420), (-1000, -420)]):
    m.box("Planter_%d" % i, x, y, 45, 220, 90, 90, mat=concrete)
    m.box("PlanterSoil_%d" % i, x, y, 92, 196, 66, 6, mat=soil, solid=False)
    m.box("PlanterRim_%d" % i, x, y, 90, 232, 102, 10, mat=curb_m, solid=False)
    m.prop("PlanterShrub_%d" % i, "shrub_a", x, y, 94, yaw=rng.uniform(0, 360), scale=0.55, solid=False)
    if i < 4:                                                        # a street tree grows out of four of the planters
        cyl(m, "TreeTrunk_%d" % i, (x, y, 92), (x + 6, y - 4, 330), 22, mat=bark, solid=False)
        for k, (ox, oy, oz, sc_) in enumerate([(0, 0, 250, 1.5), (60, 40, 300, 1.2), (-55, -35, 320, 1.25)]):
            m.prop("TreeCrown_%d_%d" % (i, k), "shrub_b", x + ox, y + oy, oz, yaw=rng.uniform(0, 360), scale=sc_, solid=False, material=tree_leaf)
        for k in range(3):                                           # a few branches into the crown
            cyl(m, "TreeBranch_%d_%d" % (i, k), (x + 6, y - 4, 250), (x + 70 * math.cos(k * 2.1 + i), y + 70 * math.sin(k * 2.1 + i), 330),
                7, mat=bark, solid=False)

for i, (x, y, yaw) in enumerate([(1650, -700, 0), (-1650, 700, 0), (-60, 770, 0), (60, -770, 0)]):
    base = (x, y, 0, yaw)
    kp.local_box(m, "Dumpster%d" % i, 0, 0, 55, 200, 110, 110, base, mat=dump_green)
    kp.local_box(m, "DumpLid%d" % i, 0, -26, 118, 200, 60, 6, base, mat=steel, solid=False, pitch=0)
    kp.local_box(m, "DumpLid2%d" % i, 0, 28, 120, 200, 56, 6, base, mat=steel, solid=False)
    for wx in (-85, 85):
        kp.local_box(m, "DumpWheel", wx, -52, 10, 18, 10, 20, base, mat=rubber, solid=False)
    kp.local_box(m, "DumpRibs", 0, 0, 60, 204, 112, 8, base, mat=galv_dark, solid=False)

# fire barrels and hydrants in the plaza corners (solid, small)
for i, (x, y) in enumerate([(-1700, -600), (1700, 600)]):
    m.prop("FireBarrel%d" % i, "barrel_fire", x, y, 0, solid=True)
    m.accent_light("FireLight%d" % i, (x, y, 100), (1.0, 0.5, 0.15), candela=15, radius=500)
for i, (x, y) in enumerate([(-1100, 760), (1100, -760), (700, 770), (-700, -770)]):
    m.prop("Hydrant%d" % i, "hydrant_a", x, y, 0, solid=False)
for i, (x, y) in enumerate([(-200, 765), (330, 770), (-340, -770), (840, -770), (-1450, 765)]):
    m.prop("Bin%d" % i, "bin_a", x, y, 0, yaw=rng.uniform(-20, 20), solid=(i % 2 == 0))

# tall partitions that break the long sight lines of the street: brick walls with posters and a small neon sign
for i, (x, y0, y1, rgb, word) in enumerate([(-1000, -800, -150, PINK, "OPEN"), (1000, 150, 800, CYAN, "BAR"), (-1400, -800, -350, LIME, None),
                                            (400, 600, 800, AMBER, None), (-400, -800, -600, AMBER, None)]):
    yc = (y0 + y1) / 2
    ln = y1 - y0
    m.box("Partition_%d" % i, x, yc, 140, 40, ln, 280, mat=brick)
    m.box("PartitionCap_%d" % i, x, yc, 286, 56, ln + 10, 12, mat=curb_m, solid=False)
    m.box("PartitionBase_%d" % i, x, yc, 30, 46, ln + 4, 60, mat=concrete_dark, solid=False)
    n_p = max(1, int(ln // 230))
    for sd in (-1, 1):
        for k in range(n_p):
            yy = y0 + ln * (k + 0.5) / n_p
            post("PartPoster", x + sd * 21, yy, 105 if word else 150, "x", 84, 112, i + k + (sd > 0))
            if k % 2 == 0:
                sticker("PartSticker", x + sd * 21, yy + 62, 70 + 40 * (i % 3), "x", i + k)
    if word:
        for sd in (-1, 1):
            neon_sign("PartSign%d%s" % (i, "a" if sd > 0 else "b"), word, x + sd * 21, yc, 232, -90 * sd, rgb, 34, thick=3.2,
                      cd=20.0, rad=520.0, panel=True)

# ------------------------------------------------------------------------------------------------ street dressing (decoration only)
# shop signs on brackets at the door shops
for i, (s_, x_, w_, z_, bd, lg) in enumerate([(1, -1170, 320, 240.0, pa_cream, awn_red), (1, -270, 300, 0.0, pa_navy, pa_mustard),
                                              (1, 1130, 320, 0.0, pa_cream, awn_green), (-1, 850, 300, 120.0, pa_cream, awn_blue),
                                              (-1, -60, 360, 0.0, pa_maroon, pa_cream), (-1, -800, 300, 0.0, pa_cream, awn_red)]):
    hang_sign("HangSign%d" % i, x_ + 0.38 * w_, s_, z_, bd, lg)

# stacked crates, sacks, bins and sandwich boards along the walls (z = street level only)
for (cx_, sy_, yaw0) in [(700, 1, 8), (-640, -1, 188), (1260, 1, -6)]:
    y_ = sy_ * (HY - 52)
    m.prop("CrateA_%d" % cx_, "crate_wood_b", cx_, y_, 0, yaw=yaw0, solid=False)
    m.prop("CrateB_%d" % cx_, "crate_wood_b", cx_ + 6, y_ - sy_ * 2, 45, yaw=yaw0 + 80, solid=False)
    m.prop("CrateC_%d" % cx_, "crate_wood_a", cx_ + 95, y_ + sy_ * 6, 0, yaw=yaw0 - 12, solid=False)
    m.prop("CrateD_%d" % cx_, "crate_wood_a", cx_ + 92, y_ + sy_ * 8, 35, yaw=yaw0 + 20, solid=False)
for (cx_, sy_) in [(930, 1), (-1330, -1)]:
    y_ = sy_ * (HY - 48)
    for r_, (n_, oz) in enumerate([(3, 0), (2, 16), (1, 32)]):
        for q in range(n_):
            rbox(m, "Sack%d_%d_%d" % (cx_, r_, q), cx_ + (q - (n_ - 1) / 2.0) * 58 + rng.uniform(-4, 4), y_ + rng.uniform(-4, 4), oz + 8,
                 56, 36, 16, yaw=rng.uniform(-14, 14), pitch=rng.uniform(-4, 4), mat=sack, solid=False)
wheelie("Wheelie0", 340, HY - 40, 180, bin_green)
wheelie("Wheelie1", -230, -HY + 40, 0, bin_grey)
wheelie("Wheelie2", -1380, -HY + 40, 4, bin_green)
for q, (x_, y_, yaw_) in enumerate([(380, 690, -10), (1010, 690, 12), (-420, -690, 200), (-1260, -690, 170)]):
    aframe("AFrame%d" % q, x_, y_, yaw_, pa_cream if q % 2 else pa_mustard)
# vending machines against the wall (the front faces the street)
for q, (x_, sy_, mt) in enumerate([(620, 1, awn_red), (250, -1, awn_blue)]):
    base = (x_, sy_ * (HY - 30), 0, -90.0 * sy_)
    kp.local_box(m, "Vend%d_body" % q, 0, 0, 90, 60, 80, 180, base, mat=mt, solid=False)
    kp.local_box(m, "Vend%d_frame" % q, 30, -4, 112, 4, 66, 128, base, mat=pa_char, solid=False)
    kp.local_box(m, "Vend%d_front" % q, 31.5, -4, 112, 2, 56, 118, base, mat=win_dim, solid=False)
    kp.local_box(m, "Vend%d_slot" % q, 31, 24, 56, 4, 14, 24, base, mat=pa_char, solid=False)

# sagging cables along the facades (brackets on the wall at both ends)
for q, (xa, xb, z0_, z1_, sg) in enumerate([(-1600, -900, 640, 700, 36), (-900, -250, 700, 610, 30), (-250, 500, 610, 690, 44),
                                            (500, 1250, 690, 640, 34), (1250, 1700, 640, 700, 26)]):
    swag("CableN%d" % q, (xa, HY - 26, z0_), (xb, HY - 26, z1_), sg)
    swag("CableS%d" % q, (-xa, -HY + 26, z0_ + 30), (-xb, -HY + 26, z1_ + 30), sg)
    for sy_, dz in ((1, 0), (-1, 30)):
        for xx, zz in ((xa, z0_), (xb, z1_)):
            rbox(m, "CableBracket", sy_ * xx, sy_ * (HY - 13), zz + dz, 6, 28, 6, mat=steel, solid=False)

# ------------------------------------------------------------------------------------------------ backdrop skyline (no collision)
rng2 = random.Random(405)
for i in range(30):
    ang = i / 30.0 * 2 * math.pi
    dist = rng2.uniform(3200, 5200)
    h = rng2.uniform(2200, 5200)
    x, y = math.cos(ang) * dist * 1.25, math.sin(ang) * dist * 0.9
    wx_, wy_ = rng2.uniform(800, 1300), rng2.uniform(800, 1300)
    m.box("Skyline_%d" % i, x, y, h / 2 - 500, wx_, wy_, h, yaw=0, mat=fac_bd[i % len(fac_bd)], solid=False)
    m.box("SkylineCap_%d" % i, x, y, h - 500 + 10, wx_ + 40, wy_ + 40, 20, mat=concrete_dark, solid=False)
    if i % 4 == 0:
        rbox(m, "SkylineMast_%d" % i, x, y, h - 500 + 300, 10, 10, 600, mat=steel, solid=False)
        rbox(m, "SkylineBeacon_%d" % i, x, y, h - 500 + 610, 24, 24, 24, mat=kc.emit("NeonBeacon", (1.0, 0.05, 0.05), 1.6), solid=False)
    if i % 5 == 1:                                                 # a small neon sign high on a far block
        rgb = [PINK, CYAN, AMBER, VIOLET][i % 4]
        kc.neon_text(m, "FarSign%d" % i, ["HOTEL", "BAR", "CAFE", "INN"][i % 4], x - wx_ / 2 * math.copysign(1, x) - math.copysign(8, x),
                     y * 0.0 + y, h * 0.55 - 500, 0, 150, TUBE[rgb], thick=10, yaw=(90 if x > 0 else -90))

# ------------------------------------------------------------------------------------------------ spawns
def clear_starts():
    for a in m.actor_lib.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart):
            m.actor_lib.destroy_actor(a)
    m.start_count = 0


best = (0, 1)
for seed in range(1, 25):                    # the original had 10 starts: try several random greedy passes until 10 fit
    chosen = m.auto_starts(10, (-1700, 1700), (-750, 750), [0, 120, 240], step=100.0, seed=seed, min_sep=450.0)
    if len(chosen) >= 10:
        break
    best = max(best, (len(chosen), seed))
    clear_starts()
else:
    clear_starts()
    chosen = m.auto_starts(10, (-1700, 1700), (-750, 750), [0, 120, 240], step=100.0, seed=best[1], min_sep=450.0)
unreal.log("NEON starts seed=%d count=%d" % (seed, len(chosen)))
m.check_starts()

# ------------------------------------------------------------------------------------------------ light: night
m.look("night_city")
m.finish(kill_z=-1200)
