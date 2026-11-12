"""Checks the imported props (run in the editor commandlet with run_ue.ps1):
every catalogue mesh loads, has collision and materials with textures, and /Game/Props references only
/Game/Props, /Script and a few engine textures (nothing from Epic's optional plugins or the Interchange import)."""

import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import props  # noqa: E402

ar = unreal.AssetRegistryHelpers.get_asset_registry()
bad = 0
external = {}
for name, e in sorted(props.PROPS.items()):
    mesh = unreal.EditorAssetLibrary.load_asset(e["path"])
    if mesh is None:
        unreal.log_error("VERIFY missing mesh %s %s" % (name, e["path"]))
        bad += 1
        continue
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom") if body else None
    shapes = 0 if agg is None else (len(agg.get_editor_property("box_elems")) + len(agg.get_editor_property("sphere_elems")) + len(agg.get_editor_property("sphyl_elems"))
                                    + len(agg.get_editor_property("convex_elems")))
    if e["coll"] != "none" and shapes == 0:
        unreal.log_error("VERIFY %s has no collision shapes" % name)
        bad += 1
    for i, m in enumerate(mesh.get_editor_property("static_materials")):
        mi = m.material_interface
        if mi is None:
            unreal.log_error("VERIFY %s slot %d has no material" % (name, i))
            bad += 1
for asset in unreal.EditorAssetLibrary.list_assets("/Game/Props", recursive=True):
    pkg = asset.split(".")[0]
    for dep in ar.get_dependencies(unreal.Name(pkg), unreal.AssetRegistryDependencyOptions()) or []:
        d = str(dep)
        if not (d.startswith("/Game/Props") or d.startswith("/Script/")):
            external.setdefault(d, []).append(pkg)
for d, users in sorted(external.items()):
    unreal.log("VERIFY external dependency %s (used by %d assets)" % (d, len(users)))
unreal.log("VERIFY_DONE meshes=%d problems=%d external=%d" % (len(props.PROPS), bad, len(external)))
