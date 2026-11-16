"""DM-Citadel helpers, engine side (additive: nothing of the shared tools is changed).

    import mapkit_big1 as k1
    k1.register_surfaces()                              # adds the Citadel surfaces to matlib.SURFACES (grass, castle masonry ...)
    sm = k1.commit_slots("Citadel_Ground_0_0", {0: mesh_a, 2: mesh_b})     # one static mesh, material slot = key
    k1.place(m, "Ground_0_0", sm, x, y, z, mat=[grass, dirt, rock, bed], shadow=True)
    k1.Frame(m, side=-1)                                # a keep's local frame (u toward the map centre, n north), mirrored for the blue one
"""

import hashlib
import math
import os
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import mapkit  # noqa: E402
import mapkit_b as kb  # noqa: E402
import matlib  # noqa: E402
import mesh_big1 as mb1  # noqa: E402
from matlib import S  # noqa: E402

# linear mean colours of the new texture sets (measured on the downloaded colour maps)
TEX_MEAN = {
    "GrassGround": (0.158, 0.119, 0.049), "GrassPath": (0.283, 0.232, 0.137), "MossRock": (0.166, 0.158, 0.103),
    "CastleSlate": (0.278, 0.230, 0.153), "CastleStone": (0.266, 0.231, 0.162), "RiverPebbles": (0.232, 0.196, 0.155),
    "RockyTrail": (0.300, 0.224, 0.152), "ClayRoof": (0.114, 0.037, 0.013),
}

NEW_SURFACES = {
    "CitGrass":       S("GrassGround", (74, 98, 42), tiling=3.6, macro=0.65, macro_m=24.0, ns=1.0),
    "CitGrassDry":    S("GrassGround", (100, 100, 56), tiling=3.4, macro=0.5, macro_m=15.0, ns=1.1),
    "CitMeadowDirt":  S("GrassPath", (98, 86, 56), tiling=2.2, macro=0.5, macro_m=12.0, ns=1.2),
    "CitRock":        S("MossRock", (112, 106, 94), tiling=6.5, macro=0.7, macro_m=16.0, ns=0.9),
    "CitRockDark":    S("MossRock", (84, 80, 72), tiling=7.0, macro=0.6, macro_m=14.0, ns=0.9),
    "CitBed":         S("RiverPebbles", (98, 92, 80), tiling=2.2, macro=0.4, macro_m=7.0, ns=1.2),
    "CitTrail":       S("RockyTrail", (142, 118, 90), tiling=2.0, macro=0.4, macro_m=8.0),
    "CitFir":         S("MossRock", (26, 46, 26), tiling=1.4, macro=0.8, macro_m=2.4, ns=1.3),
    "CitFirLight":    S("MossRock", (42, 66, 30), tiling=1.4, macro=0.8, macro_m=2.4, ns=1.3),
    "CitBark":        S("WoodPlanksDark", (70, 52, 38), tiling=1.0),
    "CitMoss":        S("MossRock", (86, 108, 58), tiling=2.6, macro=0.5, macro_m=7.0),
    "CitCastleGrey":  S("CastleSlate", (150, 146, 138), tiling=2.5, macro=0.4, macro_m=10.0, ns=1.3),
    "CitCastleBlue":  S("CastleSlate", (128, 136, 146), tiling=2.5, macro=0.4, macro_m=10.0, ns=1.3),
    "CitCastleWarm":  S("CastleStone", (150, 132, 108), tiling=2.0, macro=0.4, macro_m=10.0, ns=1.3),
    "CitCastleDark":  S("CastleStone", (96, 90, 84), tiling=2.0, macro=0.4, macro_m=10.0, ns=1.3),
    "CitRoofRed":     S("ClayRoof", (156, 70, 44), tiling=3.0, macro=0.35, macro_m=8.0),
    "CitRoofRedOld":  S("ClayRoof", (130, 76, 56), tiling=3.0, macro=0.45, macro_m=6.0),
}


def register_surfaces():
    matlib.TEX_MEAN.update(TEX_MEAN)
    matlib.SURFACES.update(NEW_SURFACES)


# ------------------------------------------------------------------------------------------------ meshes with material slots
def commit_slots(name, parts, collision="complex"):
    """Builds /Game/Maps/Gen/SM_<name> from {slot: Mesh}; the triangles of a slot get that material index. Returns the StaticMesh."""
    if name in kb._cache:
        return kb._cache[name]
    path = "%s/SM_%s" % (kb.GEN_DIR, name)
    flip = kb._winding_flip()
    dm = unreal.DynamicMesh()
    for slot in sorted(parts):
        mesh = parts[slot]
        if not mesh.verts:
            continue
        buf = unreal.GeometryScriptSimpleMeshBuffers()
        buf.set_editor_property("vertices", [unreal.Vector(*v) for v in mesh.verts])
        buf.set_editor_property("normals", [unreal.Vector(*n) for n in mesh.norms])
        buf.set_editor_property("uv0", [unreal.Vector2D(v[0] / 100.0, v[1] / 100.0) for v in mesh.verts])
        buf.set_editor_property("triangles", [unreal.IntVector(a, c, b) if flip else unreal.IntVector(a, b, c) for (a, b, c) in mesh.tris])
        unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dm, buf, int(slot))
    opts = unreal.GeometryScriptCopyMeshToAssetOptions()
    opts.set_editor_property("enable_recompute_normals", False)
    opts.set_editor_property("enable_recompute_tangents", False)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        sm = unreal.EditorAssetLibrary.load_asset(path)
        unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dm, sm, opts, unreal.GeometryScriptMeshWriteLOD(), True)
    else:
        nopts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
        nopts.set_editor_property("enable_recompute_normals", False)
        nopts.set_editor_property("enable_recompute_tangents", False)
        nopts.set_editor_property("collision_mode", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if collision == "complex" else unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
        res = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, path, nopts)
        sm = res[0] if isinstance(res, tuple) else res
    if sm is None:
        raise RuntimeError("could not create mesh " + path)
    try:
        bs = sm.get_editor_property("body_setup")
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if collision == "complex" else unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    except Exception as e:                       # noqa: BLE001
        unreal.log_warning("collision flag failed for %s: %s" % (name, e))
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    kb._cache[name] = sm
    return sm


def place(m, label, sm, x, y, z, yaw=0.0, pitch=0.0, scale=1.0, mat=None, solid=True, folder=None, shadow=True, cull=None):
    """kb.put plus: a list of materials (one per slot), no shadow, a draw distance."""
    mats = mat if isinstance(mat, (list, tuple)) else None
    a = kb.put(m, label, sm, x, y, z, yaw=yaw, pitch=pitch, scale=scale, mat=None if mats else mat, solid=solid, folder=folder)
    comp = a.static_mesh_component
    if mats:
        for i, mm in enumerate(mats):
            if mm is not None:
                comp.set_material(i, mm)
    if not shadow:
        comp.set_cast_shadow(False)
    if cull:
        comp.set_editor_property("ld_max_draw_distance", float(cull))
    return a


def tune(actors, shadow=None, cull=None):
    """Applies shadow / draw distance settings to actors made by scatter() or prop()."""
    for a in actors:
        comp = a.static_mesh_component
        if shadow is not None:
            comp.set_cast_shadow(bool(shadow))
        if cull:
            comp.set_editor_property("ld_max_draw_distance", float(cull))
    return actors


def hide(actor):
    """Keeps the collision but does not draw the actor."""
    actor.set_actor_hidden_in_game(True)
    return actor


def invisible_wall(m, label, cx, cy, cz, sx, sy, sz, yaw=0.0):
    """A box that blocks players and shots but is not drawn."""
    a = m.box(label, cx, cy, cz, sx, sy, sz, yaw=yaw, mat=None, solid=True)
    a.set_actor_hidden_in_game(True)
    a.static_mesh_component.set_cast_shadow(False)
    return a


# ------------------------------------------------------------------------------------------------ keep frame
class Frame:
    """The local frame of a keep: u points to the map centre, n north, z is height above the plateau base z0.
    side = -1: red keep (west), +1: blue (east). The blue one is the mirror image in x, so meshes are mirrored (and their winding flipped)."""

    def __init__(self, m, side, cx, z0, prefix):
        self.m, self.s, self.cx, self.z0, self.prefix = m, side, cx, z0, prefix
        self.mirror = side > 0
        self.count = 0

    def world(self, u, n):
        return (self.cx - self.s * u, n)

    def world_yaw(self, yaw_local):
        """Yaw of a direction that has local angle yaw_local (0 = toward the centre, 90 = north)."""
        return (180.0 - yaw_local) if self.mirror else yaw_local

    def put(self, label, mesh, u, n, z, yaw=0.0, mat=None, solid=True, shadow=True, cull=None, folder=None, name=None):
        """Places a mesh built in local axes (x = u direction, y = n direction), rotated by yaw, at local (u, n, z above the base)."""
        self.count += 1
        nm = name or ("%s_%s_%d" % (self.prefix, label, self.count))
        wx, wy = self.world(u, n)
        mm = mb1.xform(mesh, yaw=yaw, mirror=self.mirror)
        sm = kb.commit(nm, mm, collision="complex" if solid else "none")
        return place(self.m, self.prefix + "_" + label, sm, wx, wy, self.z0 + z, mat=mat, solid=solid, folder=folder or self.prefix, shadow=shadow, cull=cull)

    def put_slots(self, label, parts, u, n, z, yaw=0.0, mat=None, solid=True, shadow=True, cull=None, folder=None):
        self.count += 1
        nm = "%s_%s_%d" % (self.prefix, label, self.count)
        wx, wy = self.world(u, n)
        sm = commit_slots(nm, {k: mb1.xform(v, yaw=yaw, mirror=self.mirror) for k, v in parts.items()}, collision="complex" if solid else "none")
        return place(self.m, self.prefix + "_" + label, sm, wx, wy, self.z0 + z, mat=mat, solid=solid, folder=folder or self.prefix, shadow=shadow, cull=cull)

    def box(self, label, u, n, z, su, sn, sz, yaw=0.0, mat=None, solid=True, shadow=True):
        """A plain engine cube given in local axes (centre at local u, n, z)."""
        wx, wy = self.world(u, n)
        return self.m.box(self.prefix + "_" + label, wx, wy, self.z0 + z, su, sn, sz, yaw=self.world_yaw(yaw), mat=mat, solid=solid)

    def spawn_at(self, cls, label, u, n, z, yaw=0.0):
        wx, wy = self.world(u, n)
        return self.m.spawn(cls, label, (wx, wy, self.z0 + z), (0, 0, self.world_yaw(yaw)))
