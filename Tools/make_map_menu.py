"""Builds the MainMenu backdrop level: a stone gate in the golden hour, a dais for the character and the menu camera.

Run headless from the project folder:
  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_menu.py" -unattended -nullrhi -nosplash
  (or: powershell -File Tools\\run_ue.ps1 -Script Tools\\make_map_menu.py, look for MAKEMAP_DONE)

The picture (seen from the menu camera, which looks along +x): a paved plaza, in the middle a round dais with a glowing orange ring where the
selected character stands (the menu controller, IAMenuPlayerController, puts the preview character at camera + 430 forward + 190 right, so the
camera and the dais below are placed together: CAM and HERO), behind it a long flight of steps up to a tall triumphal gate with banners,
columns and braziers, ruined wings to both sides and far mountains. The low sun ("dusk" look, a photographic sky) stands in the gate: the
character is lit from behind by the sun, from the front by a warm key spot light and from the side by a cool rim light. The left third of
the screen is covered by the menu panel, so the interesting part of the picture is on the right.

Everything is built from the project's own kits (matlib surfaces, generated meshes, catalogue props, flames), nothing from the engine
content except the basic shapes.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
from mapkit import MapBuilder  # noqa: E402
import props  # noqa: E402,F401  (adds m.prop / m.scatter)
import mapkit_a as ka  # noqa: E402,F401  (thin decoration does not cast shadows)
import mapkit_b as kb  # noqa: E402
import mapkit_fx  # noqa: E402,F401  (adds m.flame)
import mesh_b as mb  # noqa: E402
import mesh_arch_b as ma  # noqa: E402
import mesh_misc_b as mm  # noqa: E402
import looktweak_n as lt  # noqa: E402
from matlib import surface  # noqa: E402

MAP_PATH = os.environ.get("IA_MENU_MAP", "/Game/Maps/MainMenu")      # another name for experiments (never commit those)
KEYMUL = float(os.environ.get("IA_KEYMUL", "1"))
m = MapBuilder(MAP_PATH)
rng = random.Random(21)

# ---------------------------------------------------------------- where things are (cm; the camera looks along +x)
CAM = (-430.0, -190.0, 140.0)      # camera; the preview character is put 430 ahead and 190 to the right of it = HERO
HERO = (CAM[0] + 430.0, CAM[1] + 190.0)
GX = 2300.0                        # the plane of the gate wall
GY = 250.0                         # the middle of the gate (the low sun is seen through it)
SUN_AZ = 10.0                      # the sun stands at this azimuth (0 = +x, towards +y)
GATE_W, GATE_T, GATE_H = 2000.0, 300.0, 1150.0
OPEN_R, OPEN_SPRING = 380.0, 500.0
PLAT_Z = 88.0                      # floor of the gate platform

# ---------------------------------------------------------------- surfaces
ground_m = surface("Gravel", tiling=4.0, albedo=(104, 92, 78), tag="MenuGround")
pave_m = surface("StoneSlabs", tiling=3.6, albedo=(122, 110, 94), tag="MenuPave")
dais_m = surface("Limestone", tiling=2.4, albedo=(170, 154, 130), tag="MenuDais")
dark_m = surface("StoneDark", tiling=2.4, albedo=(64, 60, 56), tag="MenuDark")
path_m = surface("Cobblestone", tiling=2.4, albedo=(96, 88, 78), tag="MenuPath")
wall_m = surface("SandstoneBlocks", tiling=3.0, albedo=(178, 146, 108), dirt=0.5, dirt_h=500, tag="MenuWall")
wall2_m = surface("SandstoneBlocks", tiling=2.6, albedo=(160, 132, 98), dirt=0.6, dirt_h=350, tag="MenuWall2")
lime_m = surface("Limestone", tiling=2.6, albedo=(208, 192, 160), tag="MenuLime")
bronze_m = surface("BrushedMetal", albedo=(112, 86, 52), metal=0.4, rb=0.2, tag="MenuBronze")
rod_m = surface("ForgeIron", tag="MenuRod")
mount_m = surface("RockGrey", tiling=40.0, albedo=(100, 94, 98), tag="MenuMount")
red_m = surface("CanvasRed", tag="MenuBannerRed")
blue_m = surface("CanvasBlue", tag="MenuBannerBlue")
ring_m = m.glow("MI_MenuRing", (1.0, 0.24, 0.0), 1.6)


def put(label, mesh_name, mesh, x, y, z, **kw):
    return kb.put(m, label, kb.commit(mesh_name, mesh), x, y, z, **kw)


# ---------------------------------------------------------------- ground, plaza, dais
m.box("Ground", 3000, 0, -64, 60000, 60000, 80, mat=ground_m)                          # top z = -24
m.box("Plaza", 1500, 900, -16, 6600, 7800, 16, mat=pave_m)                              # top z = -8
m.column("DaisStep", HERO[0], HERO[1], -10, -3, 900, mat=dark_m)
m.column("Dais", HERO[0], HERO[1], -10, 0, 660, mat=dais_m)                              # the character stands at z = 0


def ring_mesh(radius, width, segments=72):
    r = mb.Mesh()
    length = 2.0 * math.pi * radius / segments * 1.08
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        r.box(math.cos(a) * radius, math.sin(a) * radius, 0.0, length, width, 1.4, yaw=math.degrees(a) + 90.0, base=True)
    return r


put("DaisRing", "MenuRing", ring_mesh(300.0, 7.0), HERO[0], HERO[1], 0.3, mat=ring_m, solid=False)
put("DaisRing2", "MenuRing2", ring_mesh(262.0, 2.5, 64), HERO[0], HERO[1], 0.3, mat=ring_m, solid=False)

# a worn path from the dais to the steps leads the eye to the gate
px0, py0, px1, py1 = HERO[0] + 330.0, HERO[1], 1650.0, GY
plen = math.hypot(px1 - px0, py1 - py0)
m.box("Path", (px0 + px1) / 2.0, (py0 + py1) / 2.0, -5.5, plen, 230.0, 5.0,
      yaw=math.degrees(math.atan2(py1 - py0, px1 - px0)), mat=path_m, solid=False)
for i in range(7):                                      # a few loose slabs at the edge of the plaza
    s = rng.uniform(140, 320)
    m.box("PaveBreak_%d" % i, rng.uniform(-1500, 0), rng.uniform(-1900, 1400), -7.5, s, s * rng.uniform(0.5, 1.0), 3.0,
          yaw=rng.uniform(0, 90), mat=path_m, solid=False)

# ---------------------------------------------------------------- the gate (piers, a round opening, spandrels, arch ring, cornice, frieze)


def gate_mesh():
    g = mb.Mesh()
    W, T, H, R, ZS = GATE_W, GATE_T, GATE_H, OPEN_R, OPEN_SPRING
    for sgn in (-1, 1):
        x0, x1 = R, W / 2.0
        g.box(sgn * (x0 + x1) / 2.0, 0.0, -60.0, x1 - x0, T, H + 60.0, base=True)
    n = 24
    for k in range(n):
        xa, xb = -R + 2 * R * k / n, -R + 2 * R * (k + 1) / n
        za, zb = ZS + math.sqrt(max(0.0, R * R - xa * xa)), ZS + math.sqrt(max(0.0, R * R - xb * xb))
        g.prism([(xa, za), (xb, zb), (xb, H), (xa, H)], -T / 2.0, T / 2.0)
    return g


def gate_trim():
    """Lime trim on the front face: arch ring, pilasters, plinth, string courses, frieze and cornice."""
    g = mb.Mesh()
    W, T, H, R, ZS = GATE_W, GATE_T, GATE_H, OPEN_R, OPEN_SPRING
    g.append(ma.arch_frame(2 * R, ZS + R, 70.0, tk=52.0, seed=4), offset=(0.0, -T / 2.0, 0.0))
    for sgn in (-1, 1):
        g.box(sgn * (W / 2.0 - 35.0), -T / 2.0 - 15.0, -60.0, 70.0, 30.0, H + 60.0 - 140.0, base=True, seed=3)             # outer pilasters
        g.box(sgn * (W / 2.0 - 35.0), -T / 2.0 - 25.0, H - 140.0, 96.0, 50.0, 40.0, base=True, seed=5)                      # capitals
        g.box(sgn * ((R + W / 2.0) / 2.0), -T / 2.0 - 12.0, -60.0, W / 2.0 - R + 30.0, 24.0, 150.0, base=True, seed=6)      # plinth course
        g.box(sgn * ((R + W / 2.0) / 2.0), -T / 2.0 - 10.0, 540.0, W / 2.0 - R - 120.0, 20.0, 22.0, base=True, seed=7)      # string course
    g.append(ma.frieze(W - 140.0, 90.0, 14.0, seed=9), offset=(-(W - 140.0) / 2.0, -T / 2.0, H - 300.0))
    g.append(ma.cornice(W + 90.0, 80.0, 100.0, seed=2), offset=(-(W + 90.0) / 2.0, -T / 2.0 + 4.0, H - 100.0))
    return g


put("Gate", "MenuGate", gate_mesh(), GX, GY, 0.0, yaw=-90.0, mat=wall_m, solid=True)
put("GateTrim", "MenuGateTrim", gate_trim(), GX, GY, 0.0, yaw=-90.0, mat=lime_m, solid=False)

# ruined wings to both sides (they run along y, the same front plane as the gate)
WING_T = 240.0
WING_LEN = 3600.0


def wing_profile(seed):
    r = random.Random(seed)
    prof, x = [], 0.0
    while x < WING_LEN - 1:
        w = min(r.uniform(160, 420), WING_LEN - x)
        prof.append((x, x + w, r.choice((640, 700, 740, 780, 820, 860))))
        x += w
    return prof


wings = [("R", GY + GATE_W / 2.0 + WING_LEN, 31), ("L", GY - GATE_W / 2.0, 47)]
for name, org_y, seed in wings:
    prof = wing_profile(seed)
    put("Wing_" + name, "MenuWing_" + name, ma.wall_run(WING_LEN, prof, WING_T, seed=seed, jitter=3.0, base_z=-60.0),
        GX - WING_T / 2.0, org_y, 0.0, yaw=-90.0, mat=wall2_m, solid=True)
    # pilasters on the front face, every 620 cm, as high as the wall there
    for k in range(6):
        u = 240.0 + k * 620.0
        top = next(t for x0, x1, t in prof if x0 <= u < x1)
        wy = org_y - u                                   # the wing runs towards -y from org_y
        m.box("WingPilaster_%s_%d" % (name, k), GX - WING_T / 2.0 - 16.0, wy, (top - 140.0) / 2.0,
              56.0, 90.0, top - 20.0, mat=lime_m, solid=False)
        m.box("WingCap_%s_%d" % (name, k), GX - WING_T / 2.0 - 20.0, wy, top - 60.0, 70.0, 110.0, 36.0, mat=lime_m, solid=False)

# ---------------------------------------------------------------- steps and platform in front of the gate
m.box("Platform", 3350.0, GY, (PLAT_Z - 8.0) / 2.0, 2680.0, 2100.0, PLAT_Z + 8.0, mat=pave_m)                    # x 2010 .. 4690
m.stairs("GateStairs", 1650.0, GY, -8.0, 0.0, 1140.0, 4, 24.0, 90.0, mat=lime_m)
for sgn in (-1, 1):                                                                                                # cheek walls of the stairs
    m.box("StairCheek_%d" % sgn, 1830.0, GY + sgn * 590.0, (PLAT_Z - 8.0) / 2.0, 400.0, 40.0, PLAT_Z + 8.0, mat=wall_m, solid=False)

# ---------------------------------------------------------------- columns, banners, braziers, statues
col_sm = kb.commit("MenuColumn", mb.column_mesh(760.0, 66.0, flutes=16, drums=4, seed=3))
col_sm2 = kb.commit("MenuColumnB", mb.column_mesh(760.0, 66.0, flutes=16, drums=4, seed=6))
for sgn in (-1, 1):
    kb.put(m, "Column_%d" % sgn, col_sm if sgn < 0 else col_sm2, GX - GATE_T / 2.0 - 45.0, GY + sgn * 560.0, PLAT_Z, mat=lime_m, solid=False)

banner_front = GX - GATE_T / 2.0 - 30.0
for sgn, mat in ((-1, blue_m), (1, red_m)):
    by = GY + sgn * 800.0
    kb.put(m, "Banner_%d" % sgn, kb.commit("MenuBanner" + ("L" if sgn < 0 else "R"), mm.cloth_mesh(230.0, 560.0, waves=1.6, amp=6.0, seed=3 + sgn, nu=14, nv=10)),
           banner_front, by, 420.0, yaw=90.0, mat=mat, solid=False)
    m.box("BannerRod_%d" % sgn, banner_front - 4.0, by, 990.0, 14.0, 280.0, 14.0, mat=rod_m, solid=False)
    m.box("BannerRodTip_%d" % sgn, banner_front - 4.0, by - 150.0, 990.0, 24.0, 24.0, 24.0, mat=bronze_m, solid=False)
    m.box("BannerRodTip2_%d" % sgn, banner_front - 4.0, by + 150.0, 990.0, 24.0, 24.0, 24.0, mat=bronze_m, solid=False)

brazier_sm = kb.commit("MenuBrazier", mm.brazier_mesh())
for k, (bx, by, sc) in enumerate([(1000.0, 800.0, 1.7), (1000.0, -800.0, 1.7), (1700.0, 1100.0, 1.7), (1700.0, -1100.0, 1.7),
                                  (1760.0, GY + 650.0, 1.4), (1760.0, GY - 650.0, 1.4)]):
    ped = 90.0 * sc / 1.7
    m.box("Pedestal_%d" % k, bx, by, ped / 2.0 - 4.0, 110.0 * sc / 1.7, 110.0 * sc / 1.7, ped + 8.0, mat=lime_m)
    kb.put(m, "Brazier_%d" % k, brazier_sm, bx, by, ped, scale=sc, mat=bronze_m, solid=False)
    m.flame("Flame_%d" % k, bx, by, ped + 66.0 * sc, scale=1.5 * sc / 1.7, light=40.0 if k < 4 else 25.0, radius=650.0)

for k, (sx_, sy_, yaw) in enumerate([(1950.0, GY + 1250.0, 190.0), (1950.0, GY - 1250.0, 170.0)]):
    m.box("Plinth_%d" % k, sx_, sy_, 55.0, 190.0, 190.0, 126.0, mat=lime_m)
    m.prop("Statue_%d" % k, "statue_gothic", sx_, sy_, 118.0, yaw=yaw, scale=1.35)

# ---------------------------------------------------------------- plants and rocks (the greenery is what makes it look lived in)
avoid = [(HERO[0], HERO[1], 520.0), (1000.0, 800.0, 160.0), (1000.0, -800.0, 160.0), (1700.0, 1100.0, 160.0), (1700.0, -1100.0, 160.0)]
m.scatter(["fern_a", "fern_b", "shrub_a", "shrub_b", "plant_calathea_a", "fern_a"], ("rect", 1250.0, 1050.0, 2100.0, 3200.0), 16, seed=5,
          scale=(1.2, 2.0), min_gap=120.0, avoid=avoid, label="WingPlants")
m.scatter(["fern_a", "fern_b", "shrub_a", "shrub_b"], ("rect", 1250.0, -3000.0, 2100.0, -900.0), 10, seed=8,
          scale=(1.2, 2.0), min_gap=120.0, avoid=avoid, label="WingPlantsL")
m.scatter(["rock_moss_small_a", "rock_moss_small_b", "rock_moss_small_c"], ("rect", 600.0, 900.0, 2100.0, 2400.0), 8, seed=3,
          scale=(1.6, 2.6), min_gap=160.0, avoid=avoid, sink=0.2, label="Rubble")
m.prop("Rock_A", "rock_moss_big_a", 2050.0, 1780.0, -8.0, yaw=40.0, scale=1.5, sink=0.2)
m.prop("Rock_B", "rock_moss_big_c", 760.0, 1560.0, -8.0, yaw=110.0, scale=1.1, sink=0.25)
m.prop("Rock_C", "rock_moss_big_b", 1500.0, -1700.0, -8.0, yaw=200.0, scale=1.4, sink=0.2)
m.prop("Rock_D", "rock_boulder_l", 2300.0, 2700.0, -8.0, yaw=70.0, scale=1.2, sink=0.3)

# ---------------------------------------------------------------- far mountains (seen through the gate and over the wings)
for i, (az, dist, h, r) in enumerate([(-34.0, 17000.0, 3600.0, 4200.0), (2.0, 24000.0, 2200.0, 5200.0), (17.0, 26000.0, 2400.0, 5200.0),
                                      (30.0, 16000.0, 3900.0, 4600.0), (52.0, 18000.0, 3000.0, 4800.0)]):   # none near the sun (azimuth 10)
    a = math.radians(az)
    kb.put(m, "Mountain_%d" % i, kb.commit("MenuMountain_%d" % i, mm.mountain_mesh(r, h, seed=40 + i * 3)),
           math.cos(a) * dist, math.sin(a) * dist, -300.0, yaw=rng.uniform(0, 360), mat=mount_m, solid=False)

# ---------------------------------------------------------------- light: the low sun stands in the gate, key and rim light on the hero
m.look("dusk", sun_yaw=SUN_AZ - 180.0, sky_intensity=1.7, ev=1.0, sun_lux=10.0, sun_rgb=(1.0, 0.60, 0.30), saturation=1.15, contrast=1.12,
       fog_density=0.0010, fog_max_opacity=0.5)
lt.grade(m, tint=(1.0, 0.96, 0.90))


def aim(src, dst):
    dx, dy, dz = dst[0] - src[0], dst[1] - src[1], dst[2] - src[2]
    return (0.0, math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx)))


def spot(label, loc, target, rgb, candela, inner, outer, radius=1800.0, shadows=False, source_radius=30.0, spec=0.5):
    actor = m.spawn(unreal.SpotLight, label, loc, aim(loc, target))
    comp = actor.get_component_by_class(unreal.SpotLightComponent)
    mapkit.maplooks._set(comp, "mobility", unreal.ComponentMobility.MOVABLE)
    mapkit.maplooks._set(comp, "intensity_units", unreal.LightUnits.CANDELAS)
    mapkit.maplooks._set(comp, "intensity", float(candela))
    mapkit.maplooks._set(comp, "light_color", mapkit.maplooks._color8(rgb))
    mapkit.maplooks._set(comp, "attenuation_radius", float(radius))
    mapkit.maplooks._set(comp, "inner_cone_angle", float(inner))
    mapkit.maplooks._set(comp, "outer_cone_angle", float(outer))
    mapkit.maplooks._set(comp, "source_radius", float(source_radius))
    mapkit.maplooks._set(comp, "cast_shadows", bool(shadows))
    mapkit.maplooks._set(comp, "specular_scale", float(spec))
    mapkit.maplooks._set(comp, "use_inverse_squared_falloff", True)
    return actor


TARGET = (HERO[0], HERO[1], 105.0)
spot("KeyLight", (HERO[0] - 360.0, HERO[1] - 420.0, 330.0), TARGET, (1.0, 0.86, 0.68), 1500.0 * KEYMUL, 10.0, 22.0)
spot("RimLight", (HERO[0] + 430.0, HERO[1] + 400.0, 300.0), TARGET, (0.55, 0.72, 1.0), 700.0 * KEYMUL, 12.0, 30.0)
m.accent_light("GateGlow", (GX - 500.0, GY, 330.0), (1.0, 0.62, 0.30), candela=120.0, radius=900.0, source_radius=40.0)

# the fog glows towards the sun (cheap: no volumetric fog)
for actor in m.actor_lib.get_all_level_actors():
    if isinstance(actor, unreal.ExponentialHeightFog):
        fc = actor.get_component_by_class(unreal.ExponentialHeightFogComponent)
        mapkit.maplooks._set(fc, "directional_inscattering_luminance", unreal.LinearColor(0.55, 0.30, 0.12, 1.0))
        mapkit.maplooks._set(fc, "directional_inscattering_exponent", 6.0)
        mapkit.maplooks._set(fc, "directional_inscattering_start_distance", 500.0)
    if isinstance(actor, unreal.PostProcessVolume):
        s = actor.get_editor_property("settings")
        s.set_editor_property("override_vignette_intensity", True)
        s.set_editor_property("vignette_intensity", 0.3)
        s.set_editor_property("override_bloom_intensity", True)
        s.set_editor_property("bloom_intensity", 0.32)
        actor.set_editor_property("settings", s)

# ---------------------------------------------------------------- the camera the menu controller looks through
cam = m.spawn(unreal.CameraActor, "MenuCamera", CAM, (0.0, -2.0, 0.0))
cc = cam.get_component_by_class(unreal.CameraComponent)
mapkit.maplooks._set(cc, "field_of_view", 82.0)
mapkit.maplooks._set(cc, "constrain_aspect_ratio", False)

# This level uses the menu game mode instead of the match game mode.
world = m.editor_lib.get_editor_world()
menu_mode = unreal.load_class(None, "/Script/InstagibArena.IAMenuGameMode")
world.get_world_settings().set_editor_property("default_game_mode", menu_mode)

m.level_lib.save_current_level()
unreal.log("MAKEMAP_DONE %s gamemode=%s boxes=%d" % (MAP_PATH, menu_mode.get_name() if menu_mode else None, m.box_count))
