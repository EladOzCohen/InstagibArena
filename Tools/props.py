"""Realistic 3D props (CC0 models from Poly Haven) for the map scripts.

Use it from a map script, after `import mapkit`:

    import mapkit, props                      # importing props adds .prop / .scatter / ... to mapkit.MapBuilder
    b = mapkit.MapBuilder("/Game/Maps/DM-Canyon")
    b.prop("boulder_a", "rock_red_a_l", 1200, -300, 0, yaw=40)
    b.scatter(["rock_red_small_a", "rock_red_small_b"], ("rect", -3000, -3000, 3000, 3000), 40, seed=7)

THE CATALOGUE  PROPS[name] = dict(
        path   '/Game/Props/<Category>/SM_<Name>.SM_<Name>'     the static mesh (cooked automatically: it is
                                                                  referenced by the map; no need to list the folder)
        size   (x, y, z) in cm of the imported mesh at scale 1.0 (measured by Tools/import_props.py)
        scale  default scale of this entry (rock size classes: rock_x_s = 0.5, rock_x = 1.0, rock_x_l = 2.0 ...)
        kind   'rock' 'cliff' 'tree' 'stump' 'plant' 'barrel' 'crate' 'barrier' 'fence' 'pipe' 'duct' 'machine' 'lamp'
               'vehicle' 'tank' 'bin' 'street' 'junk' 'shelf' 'ladder' 'gate' 'crane' 'furniture' 'structure' 'marine'
               'statue' 'vase' 'brazier'
        solid  True when it has collision by default (players walk on / bump into it)
        tags   maps it suits: foundry temple dock skyline neon forge glacier canyon
        category, tris, nanite, lods, coll   (information)
    )
`size_of(name, scale=1.0)` gives the real size, `names(tag=None, kind=None)` lists catalogue names.
Poly Haven models are real-world sized: a barrel is 56x56x88 cm, a street lamp 3.9 m, rocks are 0.3 - 3 m.
Small rocks and plants are meant to be scaled up (scale=3 ...). All meshes have simple collision only (no
per-polygon collision), and traces hit that collision as well.

THE HELPERS (methods of mapkit.MapBuilder)

    b.prop(label, name, x, y, z, yaw=0.0, scale=1.0, solid=None, pitch=0.0, roll=0.0, sink=0.0, material=None)
        Places catalogue prop `name`. (x, y, z) is where the BOTTOM CENTRE of the prop's bounding box stands: z is
        the ground height (use the floor surface, not the centre). The mesh pivot can be anywhere; this is corrected
        with the measured bounds, also for scale/yaw/pitch/roll. `scale` multiplies the catalogue's own default
        scale. `solid=None` = the catalogue default, False = no collision at all (decoration), True = collision.
        `sink` (0..1) buries that fraction of the height (rocks sit better when slightly sunk). `material` replaces
        all materials of the prop (e.g. a snow material on a rock). Returns the StaticMeshActor.

    b.scatter(names, region, count, seed=1, scale=(0.8, 1.25), min_gap=60.0, max_slope=28.0, z_range=(-1e5, 1e5),
              ground=True, z=0.0, avoid=(), solid=None, sink=0.0, yaw_random=True, label="Scatter", tries=40)
        Places up to `count` random props chosen from `names` (a list; repeat a name to weight it) inside `region`:
            (x0, y0, x1, y1)                       rectangle
            ("rect", x0, y0, x1, y1)               same
            ("circle", cx, cy, r)                  disc
            ("ring", cx, cy, r_inner, r_outer)     ring
            ("poly", [(x, y), ...])                polygon
        Each prop gets a random yaw and a random scale from the (min, max) range (`scale`, relative to the
        catalogue scale) and keeps `min_gap` cm free between itself and the others (props' footprints included).
        ground=True drops each candidate onto the level's geometry with a line trace, refuses spots steeper than `max_slope` degrees (also checked at the footprint's edge) and spots
        outside `z_range`; ground=False uses height `z`. `avoid` is a list of (x, y, radius) circles to keep clear
        (player starts, jump pads). Deterministic for a given seed. Returns the list of actors; logs
        "SCATTER label placed N of count".

    b.prop_names(tag=None, kind=None)       catalogue names suitable for a map tag / kind
    b.ground_at(x, y, z_top=6000, z_bottom=-2000)    -> (z, normal_z) of the geometry below, or None
                                                      (scatter() needs the floor to exist already: place props last)

NOTES
 * Materials are instances of /Game/Props/Materials/M_Prop (parameters BaseColorTex, NormalTex, ARMTex, Tint,
   RoughMin). `material=` in prop() replaces them, e.g. to put a snow or basalt material on a rock.
 * Cliffs (cliff_*) are thin scanned shells: use them as backdrops and walls, the back side is hollow (two-sided material).
 * fire_escape_a/b/c are modular pieces (stairs, platform, ladder); pipe_*, duct_* and fence_* are kit pieces.
 * Poly Haven has no shipping containers, dumpsters or satellite dishes: build those from boxes with a
   MATLIB material. Glass parts (lamps) use M_Prop_Glass (faint translucent).
 * Big meshes are Nanite (rocks, trees, statues ...); the others have 4 LODs. Collision is simple only.

Everything here needs the imported assets (run Tools/fetch_models.py --all, then Tools/import_props.py once).
"""

import json
import math
import os
import random
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import mapkit  # noqa: E402

MEASURED_FILE = os.path.join(_TOOLS, "props_measured.json")


def _load_catalogue():
    if not os.path.exists(MEASURED_FILE):
        return {}
    data = json.load(open(MEASURED_FILE))
    cat = {}
    for name, m in data.items():
        cat[name] = {
            "path": m["path"],
            "size": tuple(round(e * 2.0, 1) for e in m["extent"]),
            "scale": m.get("scale", 1.0),
            "kind": m["kind"],
            "solid": bool(m["solid"]),
            "tags": list(m["tags"]),
            "category": m["category"],
            "tris": m.get("tris", 0),
            "nanite": m.get("nanite", False),
            "lods": m.get("lods", 1),
            "coll": m.get("coll", ""),
            "_origin": tuple(m["origin"]),
            "_extent": tuple(m["extent"]),
        }
    return cat


PROPS = _load_catalogue()


def names(tag=None, kind=None):
    return sorted(n for n, e in PROPS.items() if (tag is None or tag in e["tags"]) and (kind is None or e["kind"] == kind))


def size_of(name, scale=1.0):
    e = PROPS[name]
    s = e["scale"] * scale
    return tuple(v * s for v in e["size"])


def _entry(name):
    if name not in PROPS:
        close = [n for n in PROPS if name.split("_")[0] in n][:8]
        raise KeyError("unknown prop '%s' (similar: %s)" % (name, close))
    return PROPS[name]


# ----------------------------------------------------------------------------------------------- MapBuilder methods
def _mesh(self, entry):
    cache = self.__dict__.setdefault("_prop_meshes", {})
    path = entry["path"]
    if path not in cache:
        mesh = unreal.EditorAssetLibrary.load_asset(path)
        if mesh is None:
            raise RuntimeError("prop mesh missing: %s (run Tools/import_props.py)" % path)
        cache[path] = mesh
    return cache[path]


def _prop(self, label, name, x, y, z, yaw=0.0, scale=1.0, solid=None, pitch=0.0, roll=0.0, sink=0.0, material=None):
    e = _entry(name)
    mesh = _mesh(self, e)
    s = e["scale"] * scale
    ox, oy, oz = e["_origin"]
    ex, ey, ez = e["_extent"]
    # bottom centre of the bounding box, in mesh space, scaled
    local = unreal.Vector(ox * s, oy * s, (oz - ez + sink * 2.0 * ez) * s)
    rot = unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)
    off = unreal.MathLibrary.greater_greater_vector_rotator(local, rot)
    loc = unreal.Vector(x - off.x, y - off.y, z - off.z)
    actor = self.actor_lib.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
    actor.set_actor_label(label)
    try:
        actor.set_folder_path("Props")
    except Exception:
        pass
    comp = actor.static_mesh_component
    comp.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(s, s, s))
    if material is not None:
        for i in range(len(comp.get_materials())):
            comp.set_material(i, material)
    if solid is None:
        solid = e["solid"]
    if not solid:
        comp.set_collision_profile_name("NoCollision")
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    self.box_count += 1
    self.__dict__.setdefault("_prop_actors", []).append(actor)
    return actor


def _ground_at(self, x, y, z_top=6000.0, z_bottom=-2000.0):
    """(z, normal_z) of the first geometry below (x, y, z_top): floors, walls and props (not jump pads / starts)."""
    world = self.editor_lib.get_editor_world()
    ignore = self.__dict__.get("_ground_ignore")
    if ignore is None:
        ignore = [a for a in self.actor_lib.get_all_level_actors()
                  if isinstance(a, (unreal.IAJumpPad, unreal.PlayerStart))]
        self._ground_ignore = ignore
    res = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, z_top), unreal.Vector(x, y, z_bottom), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False, ignore, unreal.DrawDebugTrace.NONE, True)
    if res is None:
        return None
    t = res.to_tuple()
    if not t[0]:
        return None
    return t[5].z, t[7].z


def _in_region(region, x, y):
    kind = region[0] if isinstance(region[0], str) else "rect"
    r = region[1:] if isinstance(region[0], str) else region
    if kind == "rect":
        return r[0] <= x <= r[2] and r[1] <= y <= r[3]
    if kind == "circle":
        return math.hypot(x - r[0], y - r[1]) <= r[2]
    if kind == "ring":
        return r[2] <= math.hypot(x - r[0], y - r[1]) <= r[3]
    if kind == "poly":
        pts = r[0]
        inside = False
        j = len(pts) - 1
        for i in range(len(pts)):
            if (pts[i][1] > y) != (pts[j][1] > y) and \
                    x < (pts[j][0] - pts[i][0]) * (y - pts[i][1]) / (pts[j][1] - pts[i][1]) + pts[i][0]:
                inside = not inside
            j = i
        return inside
    raise ValueError("unknown region " + str(kind))


def _region_bounds(region):
    kind = region[0] if isinstance(region[0], str) else "rect"
    r = region[1:] if isinstance(region[0], str) else region
    if kind == "rect":
        return r[0], r[1], r[2], r[3]
    if kind in ("circle", "ring"):
        rad = r[2] if kind == "circle" else r[3]
        return r[0] - rad, r[1] - rad, r[0] + rad, r[1] + rad
    xs = [p[0] for p in r[0]]
    ys = [p[1] for p in r[0]]
    return min(xs), min(ys), max(xs), max(ys)


def _scatter(self, names, region, count, seed=1, scale=(0.8, 1.25), min_gap=60.0, max_slope=28.0,
             z_range=(-1e5, 1e5), ground=True, z=0.0, avoid=(), solid=None, sink=0.0, yaw_random=True,
             label="Scatter", tries=40):
    rng = random.Random(seed)
    x0, y0, x1, y1 = _region_bounds(region)
    placed = []          # (x, y, radius)
    actors = []
    for i in range(count):
        done = False
        for _ in range(tries):
            name = rng.choice(names)
            e = _entry(name)
            sc = rng.uniform(scale[0], scale[1])
            real = e["scale"] * sc
            radius = 0.5 * max(e["size"][0], e["size"][1]) * real * 0.9
            x = rng.uniform(x0, x1)
            y = rng.uniform(y0, y1)
            if not _in_region(region, x, y):
                continue
            if any(math.hypot(x - ax, y - ay) < ar + radius for ax, ay, ar in avoid):
                continue
            if any(math.hypot(x - px, y - py) < pr + radius + min_gap for px, py, pr in placed):
                continue
            gz = z
            if ground:
                g = _ground_at(self, x, y)
                if g is None:
                    continue
                gz, nz = g
                if not (z_range[0] <= gz <= z_range[1]):
                    continue
                if math.degrees(math.acos(max(-1.0, min(1.0, nz)))) > max_slope:
                    continue
                ok = True
                rr = min(radius, 400.0)
                for dx, dy in ((rr, 0), (-rr, 0), (0, rr), (0, -rr)):     # the footprint must stand on the same level
                    g2 = _ground_at(self, x + dx, y + dy)
                    if g2 is None or abs(g2[0] - gz) > max(25.0, rr * math.tan(math.radians(max_slope))):
                        ok = False
                        break
                if not ok:
                    continue
            actor = _prop(self, "%s_%d" % (label, i), name, x, y, gz, yaw=rng.uniform(0, 360) if yaw_random else 0.0,
                          scale=sc, solid=solid, sink=sink)
            placed.append((x, y, radius))
            actors.append(actor)
            done = True
            break
        if not done:
            continue
    unreal.log("SCATTER %s placed %d of %d" % (label, len(actors), count))
    return actors


def _prop_names(self, tag=None, kind=None):
    return names(tag, kind)


mapkit.MapBuilder.prop = _prop
mapkit.MapBuilder.scatter = _scatter
mapkit.MapBuilder.prop_names = _prop_names
mapkit.MapBuilder.ground_at = _ground_at
