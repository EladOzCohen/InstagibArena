"""Builds the test level /Game/Maps/_MatDemo to look at every surface of the world material library (Tools/matlib.py).

  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<proj>\\Tools\\matlib_demo.py -unattended -nullrhi -nosplash -nopause
Then look at it with the game executable, one picture per row (camera table: ROWS below, printed as DEMO_CAM lines):
  UnrealEditor.exe <uproject> /Game/Maps/_MatDemo -game -windowed -ResX=1920 -ResY=1080 -nosound -nosplash
      -IAShotDelay=14 -IAShotName=matdemo_row0 -IAShotCam=900,-950,330,-14,90
Delete /Game/Maps/_MatDemo when you are done (it is only a test level, not part of the game).

Layout: row k holds 6 surfaces (cubes 2.2 m) at y = k * 1800, x = 0, 300, ..., 1500, each with a label.
After the rows: shapes row (cylinder, cone, sphere, rotated and scaled boxes), a big floor + wall (tiling test), and
glass / water / lava.
"""
import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import matlib  # noqa: E402

MAP = "/Game/Maps/_MatDemo"
PER_ROW = 8
COL_STEP = 280.0
ROW_STEP = 600.0         # rows inside a page
ROWS_PER_PAGE = 3
PAGE_STEP = 3600.0       # one camera view ("page") shows 3 rows of 8 surfaces


def label(b, text, x, y, z, size=26.0, yaw=270.0):
    actor = b.spawn(unreal.TextRenderActor, "Label_" + text, (x, y, z), (0, 0, yaw))
    comp = actor.text_render
    comp.set_text(text)
    comp.set_world_size(size)
    comp.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    comp.set_text_render_color(unreal.Color(r=255, g=255, b=255, a=255))
    return actor


b = mapkit.MapBuilder(MAP)
b.sky(sun_pitch=-48.0, sun_yaw=215.0, sun_intensity=4.0, sky_intensity=2.0)
ppv = b.post(exposure_bias=0.0, bloom=0.3)
_s = ppv.get_editor_property("settings")
_s.set_editor_property("override_motion_blur_amount", True)
_s.set_editor_property("motion_blur_amount", 0.0)
ppv.set_editor_property("settings", _s)
names = list(matlib.SURFACES)
rows = int(math.ceil(len(names) / float(PER_ROW)))
pages = int(math.ceil(rows / float(ROWS_PER_PAGE)))

# floor under everything
floor = matlib.surface("ConcreteWorn")
b.box("Floor", 1000, pages * PAGE_STEP / 2.0 + 3000, -10, 6000, pages * PAGE_STEP + 12000, 20, mat=floor)

for idx, name in enumerate(names):
    k, i = divmod(idx, PER_ROW)
    page, r = divmod(k, ROWS_PER_PAGE)
    x, y = i * COL_STEP, page * PAGE_STEP + r * ROW_STEP
    b.box("Cube_" + name, x, y, 100, 200, 200, 200, mat=matlib.surface(name))
    label(b, name, x, y - 105, 215, size=20.0)
for p in range(pages):
    unreal.log("DEMO_CAM page%d -IAShotCam=%d,%d,820,-30,90" % (p, 980, p * PAGE_STEP - 1300))

# shapes row: other meshes and orientations
ky = pages * PAGE_STEP
shape_cam = ky
cyl = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
sph = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere.Sphere")
b.column("Cyl_ConcreteDirty", 0, ky, 0, 260, 200, mat=matlib.surface("ConcreteDirty"))
label(b, "cylinder ConcreteDirty", 0, ky - 125, 285)
b.cone("Cone_RockGrey", 300, ky, 0, 260, 220, mat=matlib.surface("RockGrey"))
label(b, "cone RockGrey", 300, ky - 125, 285)
b._place("Sphere_BrickRed", sph, (600, ky, 110), (2.2, 2.2, 2.2), 0.0, 0.0, matlib.surface("BrickRed"), True)
label(b, "sphere BrickRed", 600, ky - 125, 285)
b._place("CylSide_RustOrange", cyl, (900, ky, 100), (2.0, 2.0, 3.0), 0.0, 90.0, matlib.surface("RustOrange"), True)
label(b, "lying cylinder RustOrange", 900, ky - 160, 285)
b.box("Rot_Sandstone", 1200, ky, 110, 220, 220, 220, yaw=30.0, mat=matlib.surface("SandstoneBlocks"))
label(b, "yaw 30 SandstoneBlocks", 1200, ky - 160, 285)
b.box("Slab_Wood", 1500, ky, 40, 300, 60, 80, pitch=0.0, mat=matlib.surface("WoodPlanksOld"))
b.box("Wall_Corr", 1500, ky + 200, 150, 300, 30, 300, yaw=0.0, mat=matlib.surface("CorrugatedGalv"))
label(b, "slab + wall", 1500, ky - 125, 285)
unreal.log("DEMO_CAM shapes -IAShotCam=750,%d,330,-14,90" % (ky - 1100))

# big floor + wall: tiling and macro variation test (22 m x 22 m)
by = ky + 1800.0
b.box("BigFloor", 750, by + 1100, 0.5, 2200, 2200, 1, mat=matlib.surface("ConcreteDirty", tag="DemoBig"))
b.box("BigWall", 750, by + 2200, 300, 2200, 30, 600, mat=matlib.surface("BrickRed", tag="DemoBig"))
label(b, "big floor ConcreteDirty / wall BrickRed", 750, by - 100, 200, size=60)
unreal.log("DEMO_CAM bigfloor -IAShotCam=750,%d,420,-22,90" % (by - 700))

# glass, water, lava
gy = by + 1800.0
b.box("GlassBackBox", 0, gy + 100, 110, 160, 160, 220, mat=matlib.surface("ContainerRed"))
glass_mat = matlib.glass()
b.box("GlassPane", 0, gy - 60, 130, 300, 6, 260, mat=glass_mat, solid=False)
label(b, "glass in front of red box", 0, gy - 160, 300)
water_mat = matlib.water()
b.box("WaterPool", 600, gy, -2, 700, 700, 8, mat=water_mat, solid=False)
b.box("PoolEdgeN", 600, gy + 380, 20, 760, 40, 60, mat=matlib.surface("StoneSlabs"))
b.box("PoolEdgeS", 600, gy - 380, 20, 760, 40, 60, mat=matlib.surface("StoneSlabs"))
b.box("PoolEdgeW", 220, gy, 20, 40, 720, 60, mat=matlib.surface("StoneSlabs"))
b.box("PoolEdgeE", 980, gy, 20, 40, 720, 60, mat=matlib.surface("StoneSlabs"))
label(b, "water", 600, gy - 420, 120)
lava_mat = matlib.lava()
b.box("LavaPool", 1400, gy, -2, 700, 700, 8, mat=lava_mat, solid=False)
for nm, (cx, cy, sx, sy) in {"N": (1400, gy + 390, 780, 60), "S": (1400, gy - 390, 780, 60),
                             "W": (1010, gy, 60, 720), "E": (1790, gy, 60, 720)}.items():
    b.box("LavaEdge" + nm, cx, cy, 25, sx, sy, 70, mat=matlib.surface("BasaltDark"))
label(b, "lava", 1400, gy - 420, 120)
unreal.log("DEMO_CAM liquids -IAShotCam=800,%d,330,-16,90" % (gy - 1000))

b.starts([(1250, -2500, 0, 90)])
b.finish()
