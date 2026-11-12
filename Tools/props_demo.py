"""Builds the throwaway level /Game/Maps/_PropDemo that shows every prop of the catalogue (Tools/props.py).

    powershell -File Tools\\run_ue.ps1 -Script Tools\\props_demo.py            (needs the imported assets)

Every prop stands in a row (props of one category, small to large) with its catalogue name and real size written in
front of it, next to a 1 m red cube and a 2 m blue post as rulers. The script also writes Saved/propdemo_cams.json
with one camera (x, y, z, pitch, yaw) per row; Tools/props_demo_shots.ps1 takes the screenshots with the game
executable. The last row tests MapBuilder.scatter(). Delete the level when you are done
(Tools/props_demo_shots.ps1 -Delete).
"""

import json
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import props  # noqa: E402

MAP = "/Game/Maps/_PropDemo"
ROW_WIDTH = 2400.0        # cm of props per row
ROW_SPACING = 9000.0      # rows stand side by side along X, each filmed from -Y
GAP = 90.0
MAX_PER_ROW = 9

b = mapkit.MapBuilder(MAP)
floor_mat = b.material("MI_DemoFloor", (0.30, 0.31, 0.32), 0.9)
cube_red = b.material("MI_DemoRed", (0.8, 0.05, 0.05), 0.8)
post_blue = b.material("MI_DemoBlue", (0.05, 0.15, 0.8), 0.8)
b.sky(sun_pitch=-45, sun_yaw=-35, sun_intensity=10.0, sky_intensity=2.0)
b.box("Floor", 150000, 0, -10, 320000, 40000, 20, mat=floor_mat)
b.starts([(-5000, -5000, 0, 45)])


def label(text, x, y, size):
    a = b.spawn(unreal.TextRenderActor, "Label_" + text.split("\n")[0], (x, y, size * 1.2), (0, 0, -90))
    comp = a.get_component_by_class(unreal.TextRenderComponent)
    comp.set_editor_property("text", text)
    comp.set_editor_property("world_size", size)
    comp.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    comp.set_editor_property("text_render_color", unreal.Color(r=255, g=255, b=255, a=255))
    return a


def real(e):
    return [v * e["scale"] for v in e["size"]]


entries = [(n, e) for n, e in props.PROPS.items() if not (n.endswith("_s") or n.endswith("_l"))]
cats = {}
for n, e in entries:
    cats.setdefault(e["category"], []).append((n, e))
rows = []
for cat in sorted(cats):
    items = sorted(cats[cat], key=lambda ne: max(real(ne[1])))
    cur, width = [], 0.0
    for n, e in items:
        w = max(real(e)[0], real(e)[1]) + GAP
        if cur and (width + w > ROW_WIDTH or len(cur) >= MAX_PER_ROW):
            rows.append((cat, cur))
            cur, width = [], 0.0
        cur.append((n, e, w))
        width += w
    if cur:
        rows.append((cat, cur))

cams = []
for ri, (cat, row) in enumerate(rows):
    rx = ri * ROW_SPACING
    height = max(real(e)[2] for n, e, w in row)
    total = sum(w for n, e, w in row) + 400
    dist = max(420.0, total * 0.5, height * 1.4)
    txt = dist / 38.0
    x = rx - total / 2.0 + 150
    b.box("Ruler1m_%d" % ri, x, 0, 50, 100, 100, 100, mat=cube_red)
    b.box("Ruler2m_%d" % ri, x + 130, 0, 100, 10, 10, 200, mat=post_blue)
    x += 250
    for n, e, w in row:
        cx = x + w / 2.0
        r = real(e)
        b.prop("P_" + n, n, cx, 0.0, 0.0)
        label("%s\n%dx%dx%d cm" % (n, r[0], r[1], r[2]), cx, -(max(r[1] / 2.0, 30.0) + txt * 2.5), txt)
        x += w
    cams.append({"name": "%s_%d" % (cat, ri), "cam": [rx, -dist, min(height * 0.5 + 100, 700.0), -4.0, 90.0],
                 "count": len(row)})

# scatter test: rocks and trees on the flat floor
sx = len(rows) * ROW_SPACING
rocks = [n for n in props.names(kind="rock") if not n.endswith(("_s", "_l"))][:8]
trees = props.names(kind="tree")[:3]
actors = b.scatter(rocks, ("circle", sx, 3000, 2500), 25, seed=3, scale=(1.0, 2.0), min_gap=100, label="ScR")
actors += b.scatter(trees, ("circle", sx, 3000, 2500), 12, seed=5, scale=(0.8, 1.4), min_gap=300, label="ScT")
cams.append({"name": "scatter", "cam": [sx, -3200.0, 500.0, -10.0, 90.0], "count": len(actors)})

b.finish(kill_z=-5000)
with open(os.path.join(unreal.SystemLibrary.get_project_directory(), "Saved", "propdemo_cams.json"), "w") as f:
    json.dump(cams, f, indent=1)
unreal.log("DEMO_DONE props=%d rows=%d" % (len(entries), len(cams)))
