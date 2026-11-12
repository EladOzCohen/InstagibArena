"""Map-B helpers (DM-Temple, DM-Canyon): generated static meshes (columns, cliffs, dunes ...) and placing them.

    import mapkit, mapkit_b, mesh_b
    sm = mapkit_b.commit("TempleColumn", mesh_b.column_mesh(700, 80))        # builds /Game/Maps/Gen/SM_TempleColumn
    mapkit_b.put(m, "Col_1", sm, x, y, z, yaw=20, mat=surface("Limestone"))  # z = where the mesh's z=0 stands

Meshes come from mesh_b.Mesh (pure python buffers) through Geometry Script. Collision is the mesh itself (complex as simple),
so players and the nav grid can walk on dunes, steps and rocks exactly as they look.
"""

import hashlib
import json
import os
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

GEN_DIR = "/Game/Maps/Gen"
_state = {"flip": None}
_cache = {}


def _winding_flip():
    """True when this engine wants the opposite triangle order to mesh_b's convention ((b-a)x(c-a) points out)."""
    if _state["flip"] is not None:
        return _state["flip"]
    flip = False
    try:
        dm = unreal.DynamicMesh()
        unreal.GeometryScript_Primitives.append_box(dm, unreal.GeometryScriptPrimitiveOptions(), unreal.Transform(), 100, 100, 100,
                                                    0, 0, 0, unreal.GeometryScriptPrimitiveOriginMode.CENTER)
        q = unreal.GeometryScript_MeshQueries

        r = q.get_triangle_positions(dm, 0)
        vecs = [e for e in (r if isinstance(r, tuple) else [r]) if isinstance(e, unreal.Vector)]
        if len(vecs) < 3:
            raise RuntimeError("get_triangle_positions gave %s" % (r,))
        a, b, c = vecs[:3]
        ab = (b.x - a.x, b.y - a.y, b.z - a.z)
        ac = (c.x - a.x, c.y - a.y, c.z - a.z)
        n = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        ctr = ((a.x + b.x + c.x) / 3.0, (a.y + b.y + c.y) / 3.0, (a.z + b.z + c.z) / 3.0)      # box is centred at the origin
        outward = n[0] * ctr[0] + n[1] * ctr[1] + n[2] * ctr[2]
        flip = outward < 0
        unreal.log("WINDING engine box: (b-a)x(c-a).outward = %.1f -> flip=%s" % (outward, flip))
    except Exception as e:                       # noqa: BLE001
        unreal.log_warning("WINDING detection failed (%s); assuming flip=False" % e)
    _state["flip"] = flip
    return flip


def commit(name, mesh, collision="complex"):
    """Builds (or rebuilds) the static mesh /Game/Maps/Gen/SM_<name> from a mesh_b.Mesh and returns it.
    collision: "complex" (mesh = collision), "none"."""
    path = "%s/SM_%s" % (GEN_DIR, name)
    digest = hashlib.md5((repr(mesh.verts[:50]) + str(len(mesh.verts)) + str(len(mesh.tris)) + repr(mesh.verts[-20:]) + collision).encode()).hexdigest()
    if name in _cache:
        return _cache[name]
    flip = _winding_flip()
    buf = unreal.GeometryScriptSimpleMeshBuffers()
    buf.set_editor_property("vertices", [unreal.Vector(*v) for v in mesh.verts])
    buf.set_editor_property("normals", [unreal.Vector(*n) for n in mesh.norms])
    buf.set_editor_property("uv0", [unreal.Vector2D(v[0] / 100.0, v[1] / 100.0) for v in mesh.verts])
    buf.set_editor_property("triangles", [unreal.IntVector(a, c, b) if flip else unreal.IntVector(a, b, c) for (a, b, c) in mesh.tris])
    dm = unreal.DynamicMesh()
    unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dm, buf, 0)
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
        nopts.set_editor_property("collision_mode", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if collision == "complex"
                                  else unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
        res = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, path, nopts)
        sm = res[0] if isinstance(res, tuple) else res
    if sm is None:
        raise RuntimeError("could not create mesh " + path)
    try:
        bs = sm.get_editor_property("body_setup")
        if collision == "complex":
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        else:
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    except Exception as e:                       # noqa: BLE001
        unreal.log_warning("collision flag failed for %s: %s" % (name, e))
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    _cache[name] = sm
    return sm


def put(m, label, sm, x, y, z, yaw=0.0, pitch=0.0, scale=1.0, mat=None, solid=True, folder=None):
    """Places a generated mesh. scale may be a float or (sx, sy, sz)."""
    s = (scale, scale, scale) if isinstance(scale, (int, float)) else tuple(scale)
    a = m._place(label, sm, (x, y, z), s, yaw, pitch, mat, solid)
    if folder:
        try:
            a.set_folder_path(folder)
        except Exception:                        # noqa: BLE001
            pass
    return a


def cached(name, builder, collision="complex"):
    """commit(name, builder()) but builds the mesh only the first time in this run."""
    if name in _cache:
        return _cache[name]
    return commit(name, builder(), collision)


def prop_variant(name, tint, tag):
    """A material instance of a catalogue prop's own material with another Tint (lighter bushes, redder rocks ...)."""
    import props
    key = "PV_" + tag
    if key in _cache:
        return _cache[key]
    mesh = unreal.EditorAssetLibrary.load_asset(props.PROPS[name]["path"])
    base = mesh.get_material(0)
    full = "%s/MI_%s" % (GEN_DIR, key)
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        mic = unreal.EditorAssetLibrary.load_asset(full)
    else:
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_" + key, GEN_DIR, unreal.MaterialInstanceConstant,
                                                                       unreal.MaterialInstanceConstantFactoryNew())
    lib = unreal.MaterialEditingLibrary
    lib.set_material_instance_parent(mic, base)
    lib.set_material_instance_vector_parameter_value(mic, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    lib.update_material_instance(mic)
    unreal.EditorAssetLibrary.save_asset(full)
    _cache[key] = mic
    return mic


def retint(actors, mat):
    for a in actors:
        comp = a.static_mesh_component
        for i in range(len(comp.get_materials())):
            comp.set_material(i, mat)
