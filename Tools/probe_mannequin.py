"""Dumps the reference pose of the Mannequin (bone positions in CHARACTER space: X forward, Y right, Z up, cm, mesh scale 1)
and its render triangles to <AssetCache>/char_probe/*.json, for Tools/preview_char.py (a quick fit check for the gear).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools/probe_mannequin.py -unattended -nullrhi -nosplash
"""

import json
import os

import unreal

OUT = os.path.join(os.path.expanduser("~"), "AssetCache", "char_probe")
os.makedirs(OUT, exist_ok=True)


def to_char(x, y, z):
    # the mesh component is rotated -90 degrees about Z inside the actor: actor X = mesh Y, actor Y = -mesh X
    return (y, -x, z)


for label, path in (("manny", "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"), ("quinn", "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")):
    sk = unreal.EditorAssetLibrary.load_asset(path)
    mod = unreal.SkeletonModifier()
    mod.set_skeletal_mesh(sk)
    bones = {}
    for name in mod.get_all_bone_names():
        name = str(name)
        t = mod.get_bone_transform(name, True)
        p = t.translation
        bones[name] = {"pos": to_char(p.x, p.y, p.z), "parent": str(mod.get_parent_name(name))}
    unreal.log("PROBE %s bones=%d" % (label, len(bones)))
    with open(os.path.join(OUT, label + "_bones.json"), "w") as f:
        json.dump(bones, f, indent=1)
    dm = unreal.DynamicMesh()
    opts = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD(unreal.GeometryScriptLODType.MAX_AVAILABLE, 0)
    res = unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(sk, dm, opts, lod)
    unreal.log("PROBE copy -> %s" % (res,))
    pos = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(dm, False)
    pos = [e for e in pos if not isinstance(e, (bool, unreal.DynamicMesh))][0] if isinstance(pos, tuple) else pos
    idx = unreal.GeometryScript_MeshQueries.get_all_triangle_indices(dm, False)
    idx = [e for e in idx if not isinstance(e, (bool, unreal.DynamicMesh))][0] if isinstance(idx, tuple) else idx
    unreal.log("PROBE idx dirs %s" % [n for n in dir(idx) if not n.startswith("_") and "conv" in n or "tri" in n])
    pos = pos.convert_vector_list_to_array()
    verts = [to_char(p.x, p.y, p.z) for p in pos]
    idx = idx.convert_triangle_list_to_array()
    tris = [(t.x, t.y, t.z) for t in idx]
    normals = [(0.0, 0.0, 1.0)] * len(verts)
    unreal.log("PROBE %s verts=%d tris=%d" % (label, len(verts), len(tris)))
    with open(os.path.join(OUT, label + "_body.json"), "w") as f:
        json.dump({"v": verts, "n": normals, "t": tris}, f)
unreal.log("PROBE_DONE")
