"""DM-Quarry: a huge open-pit quarry (about 13000 x 8600 uu playable) for Capture the Flag, free-for-all and team deathmatch. 8-12 players.

  powershell -File Tools\\run_ue.ps1 -Script Tools\\make_map_quarry.py -Log Saved\\mk_quarry.log -Grep "MAKEMAP_DONE|Traceback|LogPython: Error"

Layout (mirror symmetric about x = 0; red base west, blue base east):
  * the pit (centre 0, 250; rim 3900 x 2500, three terraces: rim 0, bench A -450, bench B -900, floor -1350) with a turquoise pond;
  * three lanes: the pit floor (reached by a 29 degree main ramp from each base or by two haul roads that wind down the north and south
    walls), the rim and two gantry bridges (north rim to south rim), and the tunnels under the south country (declines in the base yards,
    a central hall, exit shafts to the south plateau and a mouth onto bench A);
  * red base: crushing plant with silos and conveyors; blue base: loading dock with a gantry crane, office and trucks.
The terrain is ONE height function (Tools/quarry_terrain.py) cut into tile meshes by material and rock bed (Tools/mapkit_big2.py); the
structures are merged generated meshes (Tools/quarry_struct*.py, quarry_bases.py), matlib surfaces and catalogue props.
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
import mapkit_a as ka  # noqa: E402
import mapkit_b as kb  # noqa: E402
import mesh_b as mb  # noqa: E402
import mesh_misc_b as mm  # noqa: E402
import quarry_terrain as qt  # noqa: E402
import mapkit_big2 as bg  # noqa: E402
import quarry_struct as qs  # noqa: E402
import quarry_struct2 as q2  # noqa: E402
import quarry_bases as qb  # noqa: E402
from matlib import surface, water  # noqa: E402

m = MapBuilder("/Game/Maps/DM-Quarry")
rng = random.Random(41)
S = surface

# ---------------------------------------------------------------- look
m.look("desert", sun_yaw=215.0, sun_pitch=-38.0, ev=1.15, ambient_gain=0.1477, sky_intensity=6.0, fog_density=0.0021)

# ---------------------------------------------------------------- surfaces
MAT = {
    "plateau": S("DirtDry", tiling=4.0, albedo=(168, 134, 98), macro=0.45, macro_m=18.0, tag="QPlateau"),
    "plateau2": S("Gravel", tiling=3.0, albedo=(170, 142, 106), macro=0.4, macro_m=12.0, tag="QPlateau2b"),
    "gravel": S("Gravel", tiling=2.5, albedo=(146, 128, 108), tag="QBench"),
    "rubble": S("StoneRubble", tiling=3.0, albedo=(150, 118, 92), ns=1.3, tag="QRubble"),
    "floor": S("Sand", tiling=5.0, albedo=(196, 164, 118), macro=0.4, macro_m=16.0, tag="QFloor"),
    "floor2": S("DirtRed", tiling=4.0, albedo=(188, 146, 104), tag="QFloor2b"),
    "bed": S("Sand", tiling=4.0, albedo=(200, 190, 150), tag="QBed"),
    "road": S("DirtDry", tiling=3.0, albedo=(184, 152, 114), macro=0.3, macro_m=9.0, tag="QRoad"),
    "heap_gravel": S("Gravel", tiling=2.0, albedo=(122, 116, 108), tag="QHeapG"),
    "heap_sand": S("Sand", tiling=3.0, albedo=(218, 188, 132), tag="QHeapS"),
    "heap_ore": S("DirtRed", tiling=2.0, albedo=(132, 62, 40), tag="QHeapO"),
    "red": S("RockCanyonRed", tiling=6.0, albedo=(176, 98, 64), ns=1.4, macro=0.5, macro_m=6.0, tag="QRed"),
    "pale": S("SandstoneRough", tiling=3.6, albedo=(214, 178, 132), ns=1.6, macro=0.3, macro_m=5.0, tag="QPale"),
    "cliff": S("RockCliff", tiling=6.0, albedo=(158, 122, 92), ns=1.4, macro=0.5, macro_m=7.0, tag="QCliff"),
    "dark": S("RockCliff", tiling=6.0, albedo=(104, 78, 62), ns=1.4, macro=0.5, macro_m=7.0, tag="QDark"),
}
tun_floor = S("Gravel", tiling=2.5, albedo=(118, 104, 88), tag="QTunnelFloor2")
tun_wall = S("RockCliff", tiling=4.0, albedo=(120, 94, 74), ns=1.2, tag="QTunnelWall")
tun_ceil = S("RockCliff", tiling=4.0, albedo=(88, 70, 58), ns=1.2, tag="QTunnelCeil")


def water_instance(name, rgb):
    parent = water()
    path = "/Game/Maps/Gen/MI_%s" % name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mic = unreal.EditorAssetLibrary.load_asset(path)
    else:
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_" + name, "/Game/Maps/Gen", unreal.MaterialInstanceConstant,
                                                                      unreal.MaterialInstanceConstantFactoryNew())
    lib = unreal.MaterialEditingLibrary
    lib.set_material_instance_parent(mic, parent)
    lib.set_material_instance_vector_parameter_value(mic, "WaterColor", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    lib.set_material_instance_scalar_parameter_value(mic, "RippleStrength", 0.006)
    lib.update_material_instance(mic)
    unreal.EditorAssetLibrary.save_asset(path)
    return mic


water_m = water_instance("Quarry_Pond", (0.015, 0.22, 0.22))

# materials of the structures (keys used by quarry_struct / quarry_bases)
common = {
    "conc": S("ConcreteDirty", tiling=2.0, albedo=(142, 134, 122), tag="QConc"),
    "conc_dark": S("ConcreteDark", tiling=2.0, albedo=(96, 90, 84), dirt=0.6, tag="QConcDark"),
    "conc_clean": S("ConcreteClean", tiling=2.0, albedo=(176, 172, 164), tag="QConcClean"),
    "steel": S("SteelDark", tiling=1.5, albedo=(92, 94, 98), tag="QSteel"),
    "plate": S("DiamondPlate", tiling=1.5, albedo=(112, 110, 106), desat=1.0, tag="QPlate2"),
    "yellow": S("ContainerYellow", tiling=1.5, albedo=(188, 150, 62), macro=0.45, macro_m=3.0, tag="QYellow"),
    "rustc": S("RustCoarse", tiling=1.5, albedo=(104, 58, 34), tag="QRust"),
    "dark": S("SteelDark", tiling=1.5, albedo=(52, 54, 58), tag="QDarkSteel"),
    "rubber": S("Asphalt", tiling=1.5, albedo=(34, 34, 36), tag="QRubber"),
    "tire": S("Asphalt", tiling=0.8, albedo=(30, 30, 32), tag="QTire"),
    "belt": S("Asphalt", tiling=1.5, albedo=(40, 40, 42), tag="QBelt"),
    "floor": S("ConcreteWorn", tiling=3.0, albedo=(132, 126, 116), dirt=0.5, tag="QHallFloor"),
    "glass_dark": S("Asphalt", tiling=1.5, albedo=(36, 44, 50), rb=-0.4, tag="QGlass"),
    "paint_y": S("ContainerYellow", tiling=1.5, albedo=(196, 146, 40), macro=0.5, macro_m=2.5, dirt=0.5, tag="QPaintY"),
    "paint_b": S("ContainerBlue", tiling=1.5, albedo=(42, 84, 140), dirt=0.4, tag="QPaintB"),
    "ore": S("DirtRed", tiling=2.0, albedo=(120, 60, 40), tag="QOre"),
    "wood": S("WoodPlanksDark", tiling=1.5, albedo=(96, 70, 50), tag="QWood"),
    "cont_r": S("ContainerRed", tiling=1.5, albedo=(138, 52, 40), dirt=0.5, tag="QContR"),
    "cont_g": S("ContainerGreen", tiling=1.5, albedo=(58, 100, 70), dirt=0.5, tag="QContG"),
    "cont_y": S("ContainerYellow", tiling=1.5, albedo=(190, 150, 54), dirt=0.5, tag="QContY"),
    "cont_b": S("ContainerBlue", tiling=1.5, albedo=(44, 84, 134), dirt=0.5, tag="QContB"),
    "cont_w": S("ContainerGrey", tiling=1.5, albedo=(170, 172, 170), dirt=0.5, tag="QContW"),
}
mats_red = dict(common)
mats_red.update({"corr": S("CorrugatedRust", tiling=2.0, albedo=(104, 62, 46), dirt=0.5, tag="QCorrR2"),
                 "roof": S("CorrugatedRust", tiling=2.0, albedo=(96, 60, 46), tag="QRoofR2"),
                 "team": S("ContainerRed", tiling=1.5, albedo=(170, 40, 30), tag="QTeamR")})
mats_blue = dict(common)
mats_blue.update({"corr": S("CorrugatedGalv", tiling=2.0, albedo=(142, 152, 164), metal=0.3, tag="QCorrB"),
                  "roof": S("CorrugatedGalv", tiling=2.0, albedo=(110, 120, 134), metal=0.3, tag="QRoofB"),
                  "team": S("ContainerBlue", tiling=1.5, albedo=(38, 80, 160), tag="QTeamB")})
barrel_m = kb.prop_variant("barrel_red", (0.55, 1.4, 1.4), "QuarryBarrel")
bush_m = kb.prop_variant("bush_dry_a", (1.3, 1.1, 0.7), "QuarryBush")

_orig_prop = m.prop


def _prop(label, name, *a, **kw):
    if name == "barrel_red" and "material" not in kw:
        kw["material"] = barrel_m
    return _orig_prop(label, name, *a, **kw)


m.prop = _prop

# ---------------------------------------------------------------- terrain
unreal.log("QUARRY terrain grid")
grid = qt.Grid()
for (ti, tj, key), mesh in sorted(bg.build_terrain(grid).items()):
    sm = kb.commit("Quarry_T%d%d_%s" % (ti, tj, key), mesh)
    kb.put(m, "Terrain_%d%d_%s" % (ti, tj, key), sm, 0, 0, 0, mat=MAT[key], solid=True, folder="Terrain")
tn = bg.build_tunnels(grid)
for part, mat in (("floor", tun_floor), ("walls", tun_wall), ("ceil", tun_ceil)):
    kb.put(m, "Tunnel_" + part, kb.commit("Quarry_Tunnel_" + part, tn[part]), 0, 0, 0, mat=mat, solid=True, folder="Tunnels")
ka.disc(m, "Pond", qt.PONDX, qt.PONDY, qt.WATER_Z, qt.PONDRX * 1.05, qt.PONDRY * 1.05, 4.0, water_m)


def gz(x, y):
    return grid.sample(x, y)


def flat_spot(x, y, r, tries=40):
    """The nearest spot to (x, y) where the terrain under a footprint of radius r is flat (for pylons)."""
    best = (1e9, x, y)
    for i in range(tries):
        a = i * 2.4
        d = 0.0 if i == 0 else 18.0 * math.sqrt(i) * 6.0
        px, py = x + d * math.cos(a), y + d * math.sin(a)
        hs = [gz(px + dx * r, py + dy * r) for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1), (0, 0))]
        spread = max(hs) - min(hs)
        if spread < best[0]:
            best = (spread, px, py)
        if spread < 18.0:
            break
    return best[1], best[2]


# ---------------------------------------------------------------- the two bases
FX = qt.BASE_X
FY = 250.0


def W(team, u, v):
    return (-FX + u, FY + v) if team == 0 else (FX - u, FY + v)


unreal.log("QUARRY bases")
qs.put_struct(m, kb, qb.red_plant(), -FX, FY, 0.0, 0.0, mats_red, folder="RedBase")
qs.put_struct(m, kb, qb.blue_dock(), FX, FY, 0.0, 0.0, mats_blue, mirror=True, folder="BlueBase")
banner_sm = kb.commit("Quarry_Banner", mm.cloth_mesh(120.0, 230.0, waves=2.0, amp=8.0, seed=3))
canvas_red = S("CanvasRed", tiling=1.5, albedo=(150, 40, 32), tag="QCanvasR")
canvas_blue = S("CanvasBlue", tiling=1.5, albedo=(40, 80, 150), tag="QCanvasB")
for team, cm in ((0, canvas_red), (1, canvas_blue)):
    for sv in (-1, 1):
        x, y = W(team, 820.0, sv * 330.0)
        m.column("BannerPole_%d_%d" % (team, sv), x, y, 0.0, 520.0, 12, mat=common["steel"], solid=False)
        kb.put(m, "Banner_%d_%d" % (team, sv), banner_sm, x + (60 if team == 0 else -60), y, 270.0, yaw=0.0, mat=cm, solid=False)

# flags
for team, nm in ((0, "Red"), (1, "Blue")):
    fx, fy = W(team, 0.0, 0.0)
    f = m.spawn(unreal.IAFlagBase, "FlagBase_" + nm, (fx, fy, 6.0))
    f.set_editor_property("flag_team", team)


def add_start(label, x, y, yaw, tag=None, z=None):
    zz = gz(x, y) if z is None else z
    a = m.spawn(unreal.PlayerStart, label, (x, y, zz + 110.0), (0, 0, yaw))
    if tag:
        a.set_editor_property("player_start_tag", tag)
    m.start_count += 1


BASE_STARTS = [(-1000.0, 800.0, 0.0), (340.0, 1560.0, 0.0), (-900.0, -900.0, 0.0), (900.0, -1000.0, 0.0), (-350.0, -520.0, 6.0),
               (-560.0, 380.0, 6.0), (1150.0, 520.0, 0.0), (1150.0, -520.0, 0.0)]
for team, tag in ((0, "Red"), (1, "Blue")):
    for i, (u, v, zz) in enumerate(BASE_STARTS):
        x, y = W(team, u, v)
        face = math.degrees(math.atan2(FY - y, (-FX if team == 0 else FX) - x)) if i in (4, 5) else (0.0 if team == 0 else 180.0)
        add_start("Start_%s_%d" % (tag, i), x, y, face, tag, z=(zz if zz > 0 else gz(x, y)))
for i, (x, y) in enumerate([(-1800, -500), (1800, 900), (-900, 900), (-2700, 3650), (2000, 3700), (-1200, -2850), (1800, -3200), (-800, 2340)]):
    add_start("Start_Mid_%d" % i, x, y, rng.uniform(0, 360))

# jump pads: floor -> bench B, bench A -> plateau
for sgn in (-1, 1):
    for th_a, th_b in ((207.0, 222.0), (95.0, 135.0)):
        ta = th_a if sgn < 0 else 180.0 - th_a
        tb = th_b if sgn < 0 else 180.0 - th_b
        fx, fy = qt.ring_point(ta, 1700.0)
        tx, ty = qt.ring_point(tb, 915.0)
        m.jump_pad("PadFloor_%d_%d" % (sgn, th_a), fx, fy, gz(fx, fy), (tx, ty, gz(tx, ty)), color=(1.0, 0.55, 0.15), apex_extra=140.0)
    for th_a, th_b in ((160.0, 170.0), (200.0, 190.0)):
        ta = th_a if sgn < 0 else 180.0 - th_a
        tb = th_b if sgn < 0 else 180.0 - th_b
        fx, fy = qt.ring_point(ta, 400.0)
        tx, ty = qt.ring_point(tb, -330.0)
        m.jump_pad("PadBench_%d_%d" % (sgn, th_a), fx, fy, gz(fx, fy), (tx, ty, gz(tx, ty)), color=(0.3, 0.85, 1.0), apex_extra=150.0)

# ---------------------------------------------------------------- the gantry bridges (north rim -> south rim)
unreal.log("QUARRY bridges")
for bx in (-1500.0, 1500.0):
    st = qs.Struct("Bridge" + ("W" if bx < 0 else "E"))
    y_s, y_n = -2260.0, 2830.0
    DZ = 190.0
    qs.girder_bridge(st, bx, y_s, bx, y_n, DZ, DZ, 380.0, deck="plate", steel="steel", yellow="yellow", truss_h=300.0)
    # ramps down to the ground at both ends (solid plates with rails)
    for (ya, yb) in ((y_n, y_n + 720.0), (y_s, y_s - 720.0)):
        za, zb = DZ, gz(bx, yb) + 4.0
        pts = [(bx - 190.0, ya, za), (bx + 190.0, ya, za), (bx + 190.0, yb, zb), (bx - 190.0, yb, zb)]
        if mb.cross(mb.sub(pts[1], pts[0]), mb.sub(pts[3], pts[0]))[2] < 0:
            pts = pts[::-1]
        qs.plate(st.k("plate", True), pts, 14.0)
        for sd in (-1, 1):
            st.k("yellow", False).rail((bx + sd * 182.0, ya, za), (bx + sd * 182.0, yb, zb), h=105.0, every=240.0)
        for sd in (-1, 1):
            st.k("steel", False).beam((bx + sd * 190.0, ya, za - 14.0), (bx + sd * 190.0, yb, zb - 14.0), 10.0, 40.0)
    # pylons on flat ground
    for py in (1900.0, 640.0, -560.0, -1560.0):
        px, pyy = flat_spot(bx, py, 190.0)
        g0 = min(gz(px + dx * 190, pyy + dy * 190) for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)))
        st.k("steel", False).lattice_tower(px, pyy, g0 - 20.0, DZ - 30.0, 380.0, 230.0, levels=max(2, int((DZ - g0) / 230.0)), leg=18.0)
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            st.k("conc", True).bx(px + dx * 190.0, pyy + dy * 190.0, g0 - 30.0, 52.0, 52.0, 70.0)
        st.k("steel", False).beam((px - 150.0, pyy, DZ - 45.0), (px + 150.0, pyy, DZ - 45.0), 14.0, 36.0)
    # a covered conveyor on one side with its own trestles
    qs.conveyor(st, (bx + 330.0, y_s + 200.0, DZ + 40.0), (bx + 330.0, y_n - 200.0, DZ + 40.0), w=90.0, hood=True, supports=False, rollers=True)
    for yy in range(int(y_s + 400), int(y_n - 300), 600):
        px, pyy = bx + 330.0, float(yy)
        g0 = gz(px, pyy)
        st.k("steel", False).beam((px - 70.0, pyy, g0), (px - 40.0, pyy, DZ + 20.0), 12.0, 12.0)
        st.k("steel", False).beam((px + 70.0, pyy, g0), (px + 40.0, pyy, DZ + 20.0), 12.0, 12.0)
    qs.put_struct(m, kb, st, 0.0, 0.0, 0.0, 0.0, common, folder="Bridges")

# ---------------------------------------------------------------- tunnel dressing
unreal.log("QUARRY tunnels")
ts = qs.Struct("TunnelSets")
tlights = []
for (x0, y0, x1, y1) in qt._TUN_ALL:
    wx, wy = x1 - x0, y1 - y0
    along_x = wx >= wy
    L = max(wx, wy)
    if min(wx, wy) > 700.0:          # the hall: pillars instead of timber sets
        for px in (x0 + 240.0, x1 - 240.0):
            for py in (y0 + 260.0, y1 - 260.0):
                ts.k("conc", True).bx(px, py, qt.TZ, 100.0, 100.0, qt.TH)
                ts.k("yellow", False).bx(px, py, qt.TZ + 40.0, 104.0, 104.0, 14.0)
        tlights.append(((x0 + x1) / 2.0 - 300.0, (y0 + y1) / 2.0, qt.TZ + 300.0))
        tlights.append(((x0 + x1) / 2.0 + 300.0, (y0 + y1) / 2.0, qt.TZ + 300.0))
        continue
    n = int(L // 400.0)
    for i in range(n):
        s = (i + 0.5) * L / n
        px, py = (x0 + s, (y0 + y1) / 2.0) if along_x else ((x0 + x1) / 2.0, y0 + s)
        fz_ = qt.tunnel_floor(px, py)
        gi, gj = int((px - qt.X0) / qt.GRID), int((py - qt.Y0) / qt.GRID)
        if qt.cell_open(grid, gi, gj):
            continue
        w = min(wx, wy)
        if along_x:
            posts = [(px, y0 + 12.0), (px, y1 - 12.0)]
            cap = ((px, y0), (px, y1))
        else:
            posts = [(x0 + 12.0, py), (x1 - 12.0, py)]
            cap = ((x0, py), (x1, py))
        for (qx, qy) in posts:
            ts.k("wood", False).bx(qx, qy, fz_, 26.0, 26.0, qt.TH - 24.0)
        ts.k("wood", False).beam((cap[0][0], cap[0][1], fz_ + qt.TH - 14.0), (cap[1][0], cap[1][1], fz_ + qt.TH - 14.0), 24.0, 28.0)
        if i % 2 == 1:
            tlights.append((px, py, fz_ + qt.TH - 60.0))
# portal frames: pit mouth (first covered row along x = 0) and the shaft/decline heads
mouth = None
y = -2000.0
while y > -2760.0:
    gi, gj = int((0.0 - qt.X0) / qt.GRID), int((y - qt.Y0) / qt.GRID)
    if not qt.cell_open(grid, gi, gj):
        mouth = y
        break
    y -= qt.GRID
if mouth is not None:
    for sx in (-1, 1):
        ts.k("conc", True).bx(sx * 262.0, mouth + 40.0, qt.TZ, 44.0, 90.0, qt.TH + 30.0)
    ts.k("yellow", False).bx(0.0, mouth + 40.0, qt.TZ + qt.TH, 560.0, 70.0, 26.0)
    unreal.log("QUARRY pit mouth at y=%.0f" % mouth)
qs.put_struct(m, kb, ts, 0.0, 0.0, 0.0, 0.0, common, folder="Tunnels", tag="Sets")
for i, (lx, ly, lz) in enumerate(tlights[:34]):
    m.accent_light("TunnelLamp_%d" % i, (lx, ly, lz), (1.0, 0.70, 0.40), candela=38.0, radius=620.0)

# ---------------------------------------------------------------- pit floor ruins, lane yards
unreal.log("QUARRY yards")
rs = qs.Struct("PitRuins")
for (x, y, yaw) in ((-1350.0, -330.0, 30.0), (1500.0, 720.0, 205.0)):
    q2.drill_rig(rs, x, y, gz(x, y) - 8.0, yaw)
for (x, y, yaw) in ((-760.0, 870.0, -40.0), (1000.0, -300.0, 150.0)):
    q2.excavator(rs, x, y, gz(x, y) - 8.0, yaw)
for (x, y, yaw) in ((-2050.0, -850.0, 70.0), (2150.0, 760.0, -100.0)):
    qs.haul_truck(rs, paint="paint_y", x=x, y=y, yaw=yaw, scale=1.0)
    rs_z = gz(x, y)
for (x, y, yaw, col) in ((-1950.0, 420.0, 15.0, "cont_g"), (1900.0, -420.0, 80.0, "cont_r"), (-250.0, -820.0, 0.0, "cont_y")):
    qs.container(rs, col, x, y, gz(x, y) - 6.0, yaw, doors=1)
qs.put_struct(m, kb, rs, 0.0, 0.0, 0.0, 0.0, common, folder="PitRuins")

ys = qs.Struct("Yards")
# north and south lane: stacks of containers, tanks, trucks, ore bins, scaffolds
for (x, y, yaw, col, stack) in ((-3300.0, 3550.0, 0.0, "cont_r", 2), (-3300.0, 3790.0, 0.0, "cont_g", 1), (-600.0, 3800.0, 0.0, "cont_y", 2),
                                (1900.0, 3650.0, 90.0, "cont_b", 2), (3350.0, 3700.0, 0.0, "cont_w", 1), (2900.0, 3350.0, 20.0, "cont_g", 1),
                                (-2300.0, -3250.0, 0.0, "cont_y", 2), (400.0, -2900.0, 90.0, "cont_r", 1), (2400.0, -3500.0, 0.0, "cont_b", 2),
                                (-3600.0, -3500.0, 0.0, "cont_w", 1), (1000.0, -3700.0, 0.0, "cont_g", 2)):
    for s in range(stack):
        qs.container(ys, col, x, y, gz(x, y) + s * 250.0 - 4.0, yaw + s * 6.0, doors=1 if s == 0 else 0)
for (x, y) in ((-2200.0, 3300.0), (2300.0, 3300.0), (-1300.0, -3100.0), (3500.0, -2900.0)):
    q2.water_tank(ys, x, y, gz(x, y) - 6.0)
for (x, y) in ((-3000.0, 3050.0), (3100.0, 3050.0), (-3900.0, -2800.0), (3900.0, -2800.0), (0.0, 3100.0)):
    q2.scaffold(ys, x, y, gz(x, y) - 6.0, 200.0, 880.0 if abs(x) > 1000 else 660.0)
for (x, y, yaw) in ((-800.0, 3500.0, 0.0), (900.0, 3450.0, 180.0), (-3000.0, -3000.0, 90.0), (2000.0, -2800.0, 270.0)):
    qs.haul_truck(ys, paint="paint_y", x=x, y=y, yaw=yaw, scale=1.0, loaded=True)
for (x, y, yaw) in ((-1800.0, 3700.0, 0.0), (1400.0, 3300.0, 180.0), (-600.0, -3350.0, 0.0), (2800.0, -2600.0, 90.0)):
    z0 = gz(x, y) - 6.0
    for (dx, dy, sx, sy) in ((0, -150, 520, 36), (0, 150, 520, 36), (-244, 0, 36, 336)):
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        ys.k("conc_dark", True).box(x + dx * c - dy * s, y + dx * s + dy * c, z0, sx, sy, 210.0, yaw=yaw, base=True)
q2.excavator(ys, -4100.0, 3300.0, gz(-4100.0, 3300.0) - 6.0, -30.0)
q2.excavator(ys, 4100.0, -3000.0, gz(4100.0, -3000.0) - 6.0, 160.0)
qs.put_struct(m, kb, ys, 0.0, 0.0, 0.0, 0.0, common, folder="Yards")

# ---------------------------------------------------------------- props
unreal.log("QUARRY props")
PA = [(0.0, 0.0, 0.0)]


def prop_set(team, items):
    for i, (name, u, v, yaw, sc, solid, z) in enumerate(items):
        x, y = W(team, u, v)
        m.prop("BaseProp_%d_%s_%d" % (team, name, i), name, x, y, z if z is not None else 0.0, yaw=yaw, scale=sc, solid=solid)


common_items = [("barrel_red", -700.0, -520.0, 0, 1.0, True, 6.0), ("barrel_red", -650.0, -560.0, 20, 1.0, True, 6.0), ("crate_wood_b", -720.0, 520.0, 10, 1.2, True, 6.0),
                ("crate_wood_a", -650.0, 560.0, 70, 1.3, True, 6.0), ("generator", -300.0, -590.0, 90, 1.5, True, 6.0),
                ("lamp_street_a", 800.0, 600.0, 0, 1.0, False, 0.0), ("lamp_street_a", 800.0, -600.0, 0, 1.0, False, 0.0),
                ("lamp_street_a", 0.0, 880.0, 0, 1.0, False, 0.0), ("lamp_street_a", 0.0, -900.0, 0, 1.0, False, 0.0),
                ("barrel_red", -1000.0, -700.0, 0, 1.0, True, 0.0), ("crate_wood_b", 900.0, -800.0, 30, 1.2, True, 0.0),
                ("propane_tank", -1050.0, -720.0, 0, 1.4, True, 0.0), ("barrier_a", 1250.0, 420.0, 90, 1.0, True, 0.0),
                ("barrier_b", 1250.0, -420.0, 90, 1.0, True, 0.0), ("fence_b", -1100.0, 600.0, 90, 1.0, True, 0.0),
                ("fence_b", -1100.0, 790.0, 90, 1.0, True, 0.0), ("fence_b", -1100.0, -600.0, 90, 1.0, True, 0.0),
                ("fence_b", -1100.0, -790.0, 90, 1.0, True, 0.0), ("utility_box_a", 700.0, 600.0, 0, 1.5, True, 0.0),
                ("crate_wood_a", 1000.0, 1700.0, 20, 1.3, True, 0.0), ("barrel_red", 1100.0, 1650.0, 0, 1.0, True, 0.0),
                ("jerrycan", -1000.0, 900.0, 0, 1.6, False, 0.0), ("tyre", 1000.0, -1250.0, 0, 1.6, True, 0.0)]
prop_set(0, common_items)
prop_set(1, common_items)

# base lights
for team in (0, 1):
    warm = (1.0, 0.72, 0.42) if team == 0 else (0.82, 0.90, 1.0)
    for i, (u, v, z, cd, rad) in enumerate([(-300.0, 0.0, 600.0, 55.0, 760.0), (300.0, 0.0, 600.0, 55.0, 760.0), (-620.0, 300.0, 330.0, 40.0, 560.0), (-620.0, -300.0, 330.0, 40.0, 560.0),
                                            (430.0, 760.0, 420.0, 40.0, 600.0), (430.0, -760.0, 420.0, 40.0, 600.0), (820.0, 0.0, 480.0, 50.0, 800.0),
                                            (0.0, 1230.0, 1500.0, 60.0, 900.0), (0.0, -1500.0, 420.0, 40.0, 700.0)]):
        x, y = W(team, u, v)
        m.accent_light("BaseLamp_%d_%d" % (team, i), (x, y, z), warm, candela=cd, radius=rad)

# work clusters on the lanes and around the pit ruins: barrels, crates, generators, lamp posts, fences, barriers
CLUSTERS = [(-3000, 3450), (-1400, 3300), (300, 3550), (1800, 3250), (3300, 3500), (-3400, -3000), (-1700, -3350), (-200, -3000), (1500, -3150), (3200, -3400),
            (-1700, -700), (1650, 300), (-300, -900), (350, 1000), (-2500, 2250), (2500, 2250), (-2500, -1700), (2500, -1700)]
for ci, (cx, cy) in enumerate(CLUSTERS):
    r2 = random.Random(500 + ci)
    for k in range(r2.randint(4, 7)):
        name = r2.choice(["barrel_red", "barrel_red", "crate_wood_a", "crate_wood_b", "jerrycan", "propane_tank", "tyre", "barrier_a", "barrier_b", "generator", "utility_box_a"])
        x, y = cx + r2.uniform(-150, 150), cy + r2.uniform(-150, 150)
        g = gz(x, y)
        m.prop("Cluster_%d_%d" % (ci, k), name, x, y, g, yaw=r2.uniform(0, 360), scale=1.0 if name != "jerrycan" else 1.6, solid=name not in ("jerrycan", "tyre"))
    x, y = cx + 220, cy - 120
    m.prop("ClusterLamp_%d" % ci, "lamp_street_a", x, y, gz(x, y), yaw=r2.uniform(0, 360), solid=False)
for ci, (fx_, fy_, fyaw) in enumerate([(-4200, 3700, 0), (-3900, 3700, 0), (4200, 3600, 0), (3900, 3600, 0), (-4200, -3500, 0), (4200, -3400, 0), (-3500, 3050, 90), (3500, 3050, 90)]):
    for k in range(4):
        x, y = fx_ + math.cos(math.radians(fyaw)) * k * 190.0, fy_ + math.sin(math.radians(fyaw)) * k * 190.0
        m.prop("Fence_%d_%d" % (ci, k), "fence_b", x, y, gz(x, y), yaw=fyaw, solid=False)

# rocks, bushes, pebbles
avoid = [(x, y, 260.0) for x, y, _ in [(a.get_actor_location().x, a.get_actor_location().y, 0) for a in m.actor_lib.get_all_level_actors() if isinstance(a, unreal.PlayerStart)]]
avoid += [(-FX, FY, 1500.0), (FX, FY, 1500.0)]
for bx_ in (-1500.0, 1500.0):
    for yy_ in range(-3000, 3600, 260):
        avoid.append((bx_ + 130.0, float(yy_), 560.0))
regions = {"north": ("rect", -6300, 2800, 6300, 4100), "south": ("rect", -6300, -4100, 6300, -2300),
           "floor": ("rect", -2400, -1200, 2400, 1600), "benchA": ("rect", -3400, 1900, 3400, 2750), "benchS": ("rect", -3400, -2150, 3400, -1500)}
rock_names = ["rock_red_a_s", "rock_red_b_s", "rock_red_c_s", "rock_red_small_l", "rock_boulder_s"]
for key, region, cnt in (("north", regions["north"], 55), ("south", regions["south"], 55), ("floor", regions["floor"], 40), ("benchA", regions["benchA"], 16), ("benchS", regions["benchS"], 14)):
    m.scatter(rock_names, region, cnt, seed=300 + len(key), scale=(0.6, 1.5), min_gap=100, avoid=avoid, label="Rock_" + key, solid=False, max_slope=30)
    m.scatter(["rock_red_a", "rock_red_b", "rock_red_c", "rock_boulder"], region, max(3, cnt // 8), seed=310 + len(key), scale=(0.8, 1.4), min_gap=250, avoid=avoid, label="Boulder_" + key, max_slope=22)
    kb.retint(m.scatter(["bush_dry_a", "bush_dry_b"], region, cnt // 2, seed=320 + len(key), scale=(0.7, 1.4), min_gap=120, avoid=avoid, label="Bush_" + key, solid=False, max_slope=25), bush_m)
m.scatter(["rock_red_b_l", "rock_red_c_l", "rock_red_a_l"], ("rect", -2000, -1000, 2000, 1500), 6, seed=340, scale=(0.9, 1.3), min_gap=500, avoid=avoid, label="PitBoulder", max_slope=20)
for i in range(14):
    ang = i / 14.0 * 2 * math.pi
    pass

# distance culling for small props
small = 0
for a in m.__dict__.get("_prop_actors", []):
    try:
        comp = a.static_mesh_component
        ext = a.get_actor_bounds(False)[1]
        if max(ext.x, ext.y, ext.z) < 160.0:
            comp.set_editor_property("ld_max_draw_distance", 7000.0)
            small += 1
    except Exception:                       # noqa: BLE001
        pass
unreal.log("QUARRY culled %d small props" % small)

# distant mesas and peaks in the haze (no collision)
far_red = S("RockCanyonRed", tiling=60.0, albedo=(160, 98, 72), tag="QFarRed")
far_pale = S("RockCanyonPale", tiling=60.0, albedo=(200, 160, 124), tag="QFarPale")
for i in range(22):
    ang = i / 22.0 * 2 * math.pi + rng.uniform(-0.1, 0.1)
    d = rng.uniform(13500, 20000)
    sm = kb.commit("Quarry_FarMesa_%d" % (i % 8), mm.mesa_mesh(rng.uniform(1600, 3200), rng.uniform(2200, 4200), seed=60 + i % 8))
    kb.put(m, "FarMesa_%d" % i, sm, math.cos(ang) * d * 1.25, math.sin(ang) * d * 0.9, -300.0, yaw=rng.uniform(0, 360), scale=(1.0, rng.uniform(0.7, 1.3), 1.0),
           mat=far_red if i % 3 else far_pale, solid=False, folder="Far")
for i in range(8):
    ang = i / 8.0 * 2 * math.pi + 0.3
    d = rng.uniform(26000, 34000)
    sm = kb.commit("Quarry_FarPeak_%d" % (i % 4), mm.mountain_mesh(rng.uniform(5000, 8000), rng.uniform(5000, 8000), seed=90 + i % 4))
    kb.put(m, "FarPeak_%d" % i, sm, math.cos(ang) * d, math.sin(ang) * d, -400.0, yaw=rng.uniform(0, 360), mat=far_pale, solid=False, folder="Far")

for a in m.actor_lib.get_all_level_actors():
    if a.get_actor_label().startswith(("FarMesa", "FarPeak")):
        ka.set_shadow(a, False)

m.check_starts()
m.finish(kill_z=-2300)
unreal.log("QUARRY actors %d" % len(m.actor_lib.get_all_level_actors()))
