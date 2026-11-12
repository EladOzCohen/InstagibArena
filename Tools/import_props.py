"""Imports the Poly Haven models listed in props_spec.py into /Game/Props (run inside the editor commandlet).

    UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<proj>\\Tools\\import_props.py -unattended -nullrhi -nosplash -nopause

Environment variables (all optional):
    IA_PROPS_ONLY=barrel_red,fir      only these job names / slugs (default: all jobs)
    IA_PROPS_MASTERS=1                rebuild the master materials even when they exist

What it does for every job in props_spec.JOBS (download the models first: Tools/fetch_models.py --all):
  1. writes a trimmed copy of the glTF (only the wanted nodes, no emissive/extension data) next to the original
     in the cache, and imports it through Interchange into a temporary folder;
  2. moves the meshes to /Game/Props/<Category>/SM_<Name>, the textures to .../Textures/T_*, and replaces the
     glTF materials by instances of our own masters (/Game/Props/Materials/M_Prop, M_Prop_TwoSided, M_Prop_Glass):
     roughness never below ~0.45 for non-metal, no emissive, glass is a faint translucent surface;
  3. builds simple collision (box / convex hulls / trunk capsule) and uses it for traces too;
  4. enables Nanite on dense opaque meshes (rocks, trees, statues...), and generates LODs for the others;
  5. measures the bounds (cm) and writes Tools/props_measured.json, which props.py reads.
"""

import json
import math
import os
import sys

import unreal

TOOLS = os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import props_spec  # noqa: E402

CACHE = os.path.join(os.environ.get("IA_ASSET_CACHE") or os.path.join(os.path.expanduser("~"), "AssetCache"), "models")
ROOT = "/Game/Props"
TMP = ROOT + "/_import"
MEASURED = os.path.join(TOOLS, "props_measured.json")

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS_API = unreal.AssetToolsHelpers.get_asset_tools()
SMS = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

NANITE_MIN_TRIS = 12000
TWO_SIDED_KINDS = ("plant", "tree", "fence", "lamp", "cliff")


def log(msg):
    unreal.log("PROPS " + msg)


def pascal(name):
    return "".join(p[:1].upper() + p[1:] for p in name.split("_"))


# ====================================================================================== master materials
def _expr(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


def build_masters(force=False):
    folder = ROOT + "/Materials"
    white = EAL.load_asset("/Engine/EngineResources/WhiteSquareTexture")
    flat = EAL.load_asset("/Engine/EngineMaterials/DefaultNormal")
    made = {}
    for name, two_sided, glass in (("M_Prop", False, False), ("M_Prop_TwoSided", True, False),
                                   ("M_Prop_Glass", False, True)):
        path = "%s/%s" % (folder, name)
        if EAL.does_asset_exist(path):
            if not force:
                made[name] = EAL.load_asset(path)
                continue
            EAL.delete_asset(path)
        mat = TOOLS_API.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
        mat.set_editor_property("two_sided", two_sided)
        if glass:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            base = _expr(mat, unreal.MaterialExpressionConstant3Vector, -600, -200)
            base.set_editor_property("constant", unreal.LinearColor(0.04, 0.06, 0.07, 1.0))
            MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
            rough = _expr(mat, unreal.MaterialExpressionConstant, -600, 0)
            rough.set_editor_property("r", 0.12)
            MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
            opac = _expr(mat, unreal.MaterialExpressionConstant, -600, 100)
            opac.set_editor_property("r", 0.28)
            MEL.connect_material_property(opac, "", unreal.MaterialProperty.MP_OPACITY)
            mat.set_editor_property("two_sided", True)
        else:
            tex_base = _expr(mat, unreal.MaterialExpressionTextureSampleParameter2D, -1000, -400)
            tex_base.set_editor_property("parameter_name", "BaseColorTex")
            tex_base.set_editor_property("texture", white)
            tint = _expr(mat, unreal.MaterialExpressionVectorParameter, -1000, -200)
            tint.set_editor_property("parameter_name", "Tint")
            tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
            mul = _expr(mat, unreal.MaterialExpressionMultiply, -700, -350)
            MEL.connect_material_expressions(tex_base, "RGB", mul, "A")
            MEL.connect_material_expressions(tint, "", mul, "B")
            MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)

            tex_n = _expr(mat, unreal.MaterialExpressionTextureSampleParameter2D, -1000, 0)
            tex_n.set_editor_property("parameter_name", "NormalTex")
            tex_n.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            tex_n.set_editor_property("texture", flat)
            MEL.connect_material_property(tex_n, "RGB", unreal.MaterialProperty.MP_NORMAL)

            arm = _expr(mat, unreal.MaterialExpressionTextureSampleParameter2D, -1000, 300)
            arm.set_editor_property("parameter_name", "ARMTex")
            arm.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            arm.set_editor_property("texture", white)
            # metallic = B
            MEL.connect_material_property(arm, "B", unreal.MaterialProperty.MP_METALLIC)
            # roughness = max(G, lerp(RoughMin, 0.3, B))  -> never glossy-wet, metal may go down to 0.3
            rmin = _expr(mat, unreal.MaterialExpressionScalarParameter, -1000, 500)
            rmin.set_editor_property("parameter_name", "RoughMin")
            rmin.set_editor_property("default_value", 0.5)
            lerp_r = _expr(mat, unreal.MaterialExpressionLinearInterpolate, -700, 450)
            lerp_r.set_editor_property("const_b", 0.3)
            MEL.connect_material_expressions(rmin, "", lerp_r, "A")
            MEL.connect_material_expressions(arm, "B", lerp_r, "Alpha")
            mx = _expr(mat, unreal.MaterialExpressionMax, -450, 380)
            MEL.connect_material_expressions(arm, "G", mx, "A")
            MEL.connect_material_expressions(lerp_r, "", mx, "B")
            MEL.connect_material_property(mx, "", unreal.MaterialProperty.MP_ROUGHNESS)
            # ambient occlusion = lerp(1, R, 0.8)
            lerp_ao = _expr(mat, unreal.MaterialExpressionLinearInterpolate, -700, 650)
            lerp_ao.set_editor_property("const_a", 1.0)
            lerp_ao.set_editor_property("const_alpha", 0.8)
            MEL.connect_material_expressions(arm, "R", lerp_ao, "B")
            MEL.connect_material_property(lerp_ao, "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
        MEL.recompile_material(mat)
        EAL.save_asset(path)
        made[name] = mat
    return made


# ====================================================================================== glTF trimming
def trim_gltf(job):
    """Writes <slug>/_job_<name>.gltf with only the job's nodes. Returns (path, [triangles per node], {material: texture image names})."""
    src_dir = os.path.join(CACHE, job["slug"])
    g = json.load(open(os.path.join(src_dir, job["slug"] + ".gltf")))
    nodes = g["nodes"]
    wanted = job["nodes"]
    if wanted is None:
        sel = [i for i, n in enumerate(nodes) if "mesh" in n]
    else:
        by_name = {n.get("name"): i for i, n in enumerate(nodes)}
        missing = [w for w in wanted if w not in by_name]
        if missing:
            raise RuntimeError("nodes not in %s: %s" % (job["slug"], missing))
        sel = [by_name[w] for w in wanted]
    new_nodes = []
    for i in sel:
        n = {k: v for k, v in nodes[i].items() if k not in ("children", "camera", "extensions", "extras")}
        new_nodes.append(n)
    if not job["keep_pivot"]:
        if job["mode"] == "combine":
            ref = list(new_nodes[0].get("translation", [0, 0, 0]))
            for n in new_nodes:
                t = n.get("translation", [0, 0, 0])
                n["translation"] = [t[0] - ref[0], t[1] - ref[1], t[2] - ref[2]]
        else:
            for n in new_nodes:
                n.pop("translation", None)
    # prune meshes / materials / textures / images that the nodes do not use
    mesh_map, new_meshes = {}, []
    for n in new_nodes:
        m = n["mesh"]
        if m not in mesh_map:
            mesh_map[m] = len(new_meshes)
            new_meshes.append(json.loads(json.dumps(g["meshes"][m])))
        n["mesh"] = mesh_map[m]
    mat_map, new_mats = {}, []
    for m in new_meshes:
        for p in m["primitives"]:
            mi = p.get("material")
            if mi is None:
                continue
            if mi not in mat_map:
                mat_map[mi] = len(new_mats)
                mat = json.loads(json.dumps(g["materials"][mi]))
                for k in ("emissiveFactor", "emissiveTexture", "occlusionTexture", "extensions", "extras"):
                    mat.pop(k, None)
                new_mats.append(mat)
            p["material"] = mat_map[mi]
    tex_map, new_tex = {}, []

    def remap_tex(ref):
        i = ref["index"]
        if i not in tex_map:
            tex_map[i] = len(new_tex)
            new_tex.append(json.loads(json.dumps(g["textures"][i])))
        ref["index"] = tex_map[i]

    for mat in new_mats:
        pbr = mat.get("pbrMetallicRoughness", {})
        for key in ("baseColorTexture", "metallicRoughnessTexture"):
            if key in pbr:
                remap_tex(pbr[key])
        if "normalTexture" in mat:
            remap_tex(mat["normalTexture"])
    img_map, new_img = {}, []
    for t in new_tex:
        i = t["source"]
        if i not in img_map:
            img_map[i] = len(new_img)
            new_img.append(g["images"][i])
        t["source"] = img_map[i]
    # texture size: explicit in the job, otherwise by the real size of the object (small things need less)
    tex = job["tex"]
    if tex is None:
        biggest = 0.0
        for n in new_nodes:
            for p in new_meshes[n["mesh"]]["primitives"]:
                acc = g["accessors"][p["attributes"]["POSITION"]]
                if "min" in acc:
                    biggest = max(biggest, max(acc["max"][k] - acc["min"][k] for k in range(3)))
        tex = 256 if biggest * job["scale"] < 0.75 else 512
    job["tex_used"] = tex
    if tex != 1024:
        folder = "textures_%d" % tex
        if not os.path.isdir(os.path.join(src_dir, folder)):
            import subprocess
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            os.path.join(TOOLS, "resize_textures.ps1"), "-Dir", src_dir, "-Size", str(tex)],
                           check=True)
        new_img = [dict(im, uri=im["uri"].replace("textures/", folder + "/", 1)) for im in new_img]
    matinfo = {}
    for mat in new_mats:
        pbr = mat.get("pbrMetallicRoughness", {})

        def img_name(ref):
            return new_img[new_tex[ref["index"]]["source"]]["name"] if ref else None
        matinfo[mat["name"]] = {"base": img_name(pbr.get("baseColorTexture")),
                                "normal": img_name(mat.get("normalTexture")),
                                "arm": img_name(pbr.get("metallicRoughnessTexture"))}
    node_tris = []
    for n in new_nodes:
        t = 0
        for p in new_meshes[n["mesh"]]["primitives"]:
            if "indices" in p:
                t += g["accessors"][p["indices"]]["count"] // 3
        node_tris.append(t)
    tris = node_tris
    out = {
        "asset": g["asset"], "scene": 0, "scenes": [{"name": "Scene", "nodes": list(range(len(new_nodes)))}],
        "nodes": new_nodes, "meshes": new_meshes, "materials": new_mats, "textures": new_tex, "images": new_img,
        "samplers": g.get("samplers", [{}]), "accessors": g["accessors"], "bufferViews": g["bufferViews"],
        "buffers": g["buffers"],
    }
    if "extensionsUsed" in g and "KHR_texture_transform" in g["extensionsUsed"]:
        out["extensionsUsed"] = ["KHR_texture_transform"]
    path = os.path.join(src_dir, "_job_%s.gltf" % job["name"])
    with open(path, "w") as f:
        json.dump(out, f)
    return path, tris, matinfo


# ====================================================================================== import one job
def _combine_behavior(combine):
    e = unreal.InterchangeCombineStaticMeshesBehavior
    names = [n for n in dir(e) if n.isupper()]
    want = "ALL" if combine else "DO_NOT_COMBINE"
    for n in names:
        if n == want:
            return getattr(e, n)
    log("combine enum values: %s" % names)
    return None


def import_job_raw(job, gltf_path):
    dest = "%s/%s" % (TMP, job["name"])
    if EAL.does_directory_exist(dest):
        EAL.delete_directory(dest)
    task = unreal.AssetImportTask()
    task.filename = gltf_path
    task.destination_path = dest
    task.automated = True
    task.replace_existing = True
    task.save = False
    pipe = unreal.InterchangeGenericAssetsPipeline()
    pipe.common_meshes_properties.force_all_mesh_as_type = unreal.InterchangeForceMeshType.IFMT_STATIC_MESH
    pipe.mesh_pipeline.set_editor_property("build_nanite", False)
    pipe.mesh_pipeline.set_editor_property("combine_static_meshes_behavior", _combine_behavior(job["mode"] == "combine"))
    stack = unreal.InterchangePipelineStackOverride()       # replaces the project's default import pipelines
    stack.add_pipeline(pipe)
    task.options = stack
    TOOLS_API.import_asset_tasks([task])
    meshes, texs = [], {}
    for p in EAL.list_assets(dest, recursive=True):
        a = EAL.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            meshes.append(a)
        elif isinstance(a, unreal.Texture2D):
            texs[str(a.get_name())] = a
    return dest, meshes, texs


# ====================================================================================== materials per mesh
def find_texture(texs, image_name):
    if not image_name:
        return None
    if image_name in texs:
        return texs[image_name]
    flat = image_name.replace("/", "_")
    for k, v in texs.items():
        if k == flat or k.startswith(flat) or flat.startswith(k):
            return v
    return None


def convert_materials(job, matinfo, texs, masters):
    """Returns {gltf material name: our material instance}; moves the textures to /Game/Props/<Cat>/Textures."""
    cat_folder = "%s/%s" % (ROOT, job["category"])
    out = {}
    for mname, info in matinfo.items():
        glass = "glass" in mname.lower()
        short = "%s_%s" % (pascal(job["slug"]), mname.replace(job["slug"], "").strip("_"))
        short = short.rstrip("_")
        mi_path = "%s/Materials/MI_%s" % (cat_folder, short)
        if EAL.does_asset_exist(mi_path):
            EAL.delete_asset(mi_path)
        mi = TOOLS_API.create_asset("MI_" + short, cat_folder + "/Materials", unreal.MaterialInstanceConstant,
                                    unreal.MaterialInstanceConstantFactoryNew())
        if glass:
            MEL.set_material_instance_parent(mi, masters["M_Prop_Glass"])
        else:
            two = job["kind"] in TWO_SIDED_KINDS or any(k in mname.lower() for k in ("leaf", "leaves", "twig"))
            MEL.set_material_instance_parent(mi, masters["M_Prop_TwoSided" if two else "M_Prop"])
            for key, mparam, suffix in (("base", "BaseColorTex", "D"), ("normal", "NormalTex", "N"),
                                        ("arm", "ARMTex", "ARM")):
                t = find_texture(texs, info[key])
                if t is None:
                    log("WARNING %s: material %s has no %s texture (%s)" % (job["name"], mname, key, info[key]))
                    continue
                new_path = "%s/Textures/T_%s_%s" % (cat_folder, short, suffix)
                if EAL.does_asset_exist(new_path):
                    EAL.delete_asset(new_path)
                EAL.rename_asset(t.get_path_name().split(".")[0], new_path)
                t2 = EAL.load_asset(new_path)
                if suffix == "D":
                    t2.set_editor_property("srgb", True)
                    t2.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
                elif suffix == "N":
                    t2.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                    t2.set_editor_property("srgb", False)
                    t2.set_editor_property("flip_green_channel", True)   # glTF normals are +Y, Unreal wants -Y
                else:
                    t2.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                    t2.set_editor_property("srgb", False)
                MEL.set_material_instance_texture_parameter_value(mi, mparam, t2)
        MEL.update_material_instance(mi)
        EAL.save_asset(mi_path)
        out[mname] = mi
    return out


# ====================================================================================== collision / nanite / LODs
def set_collision(mesh, coll, bounds):
    SMS.remove_collisions(mesh)
    ext = bounds.box_extent
    org = bounds.origin
    if coll == "none":
        pass
    elif coll == "box":
        SMS.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)
    elif coll.startswith("convex"):
        n = int(coll.split(":")[1])
        if n <= 1:
            SMS.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.NDOP26)
        else:
            SMS.set_convex_decomposition_collisions(mesh, n, 24, 100000)
    elif coll.startswith("trunk"):
        radius = float(coll.split(":")[1])
        height = ext.z * 2.0 * 0.6                       # only the lower 60 percent blocks (not the crown)
        length = max(0.0, height - 2.0 * radius)
        body = mesh.get_editor_property("body_setup")
        agg = body.get_editor_property("agg_geom")
        sph = unreal.KSphylElem()
        sph.set_editor_property("radius", radius)
        sph.set_editor_property("length", length)
        sph.set_editor_property("center", unreal.Vector(0.0, 0.0, org.z - ext.z + height / 2.0))
        agg.set_editor_property("sphyl_elems", [sph])
        body.set_editor_property("agg_geom", agg)
    body = mesh.get_editor_property("body_setup")
    if body is not None:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        try:
            body.invalidate_physics_data()
            body.create_physics_meshes()
        except Exception:
            pass


def set_nanite(mesh, tris):
    ns = SMS.get_nanite_settings(mesh)
    ns.enabled = True
    ns.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    ns.fallback_percent_triangles = max(0.02, min(1.0, 6000.0 / max(1, tris)))
    SMS.set_nanite_settings(mesh, ns, True)


def set_lods(mesh, tris, big):
    # Four levels; the first reduces very dense sources as well.
    first = 1.0 if tris < 40000 else 40000.0 / tris
    percents = [first, first * 0.5, first * 0.25, first * 0.1]
    screens = [1.0, 0.35, 0.12, 0.04] if big else [1.0, 0.25, 0.08, 0.02]
    opts = unreal.StaticMeshReductionOptions()
    opts.auto_compute_lod_screen_size = False
    settings = []
    for p, s in zip(percents, screens):
        r = unreal.StaticMeshReductionSettings()
        r.percent_triangles = p
        r.screen_size = s
        settings.append(r)
    opts.reduction_settings = settings
    SMS.set_lods(mesh, opts)


# ====================================================================================== main loop
def process_job(job, masters, measured):
    gltf, tris, matinfo = trim_gltf(job)
    dest, meshes, texs = import_job_raw(job, gltf)
    if not meshes:
        raise RuntimeError("no static mesh imported")
    mats = convert_materials(job, matinfo, texs, masters)
    cat_folder = "%s/%s" % (ROOT, job["category"])
    # decide the catalogue name of each mesh
    meshes.sort(key=lambda m: str(m.get_name()))
    if job["mode"] == "combine":
        pairs = [(job["name"], meshes[0])]
        if len(meshes) > 1:
            log("WARNING %s: %d meshes imported, expected 1: %s" % (job["name"], len(meshes), [m.get_name() for m in meshes]))
            meshes.sort(key=lambda m: -m.get_bounds().sphere_radius)
            pairs = [(job["name"], meshes[0])]
    else:
        by_name = {str(m.get_name()): m for m in meshes}
        pairs = []
        if len(meshes) == 1 and len(job["nodes"] or [1]) == 1:      # a single node: Interchange names it after the file
            by_name = {(job["nodes"] or ["x"])[0]: meshes[0]}
        for i, node in enumerate(job["nodes"] or sorted(by_name)):
            m = by_name.get(node)
            if m is None:           # Interchange appends a digit when the name is already taken by another asset
                cands = sorted(k for k in by_name if k.startswith(node) and len(k) - len(node) <= 2)
                m = by_name[cands[0]] if cands else None
            if m is None:
                log("WARNING %s: mesh for node %s missing (have %s)" % (job["name"], node, list(by_name)))
                continue
            pairs.append(("%s_%s" % (job["name"], "abcdefghijklmnop"[i]), m))
    for cname, mesh in pairs:
        final = "%s/SM_%s" % (cat_folder, pascal(cname))
        if EAL.does_asset_exist(final):
            EAL.delete_asset(final)
        EAL.rename_asset(mesh.get_path_name().split(".")[0], final)
        mesh = EAL.load_asset(final)
        # materials
        has_glass = False
        for idx, sm in enumerate(mesh.static_materials):
            mi = mats.get(str(sm.material_slot_name))
            if mi is None:
                mi = mats.get(str(sm.material_interface.get_name())) if sm.material_interface else None
            if mi is not None:
                mesh.set_material(idx, mi)
                if "Glass" in mi.parent.get_name():
                    has_glass = True
            else:
                log("WARNING %s slot %d (%s) has no converted material" % (cname, idx, sm.material_slot_name))
        b = mesh.get_bounds()
        if job["mode"] == "combine":
            mesh_tris = sum(tris)
        else:
            i = "abcdefghijklmnop".index(cname[-1])
            mesh_tris = tris[i] if i < len(tris) else sum(tris)
        log("  %s source tris=%d, imported verts=%d" % (cname, mesh_tris, SMS.get_number_verts(mesh, 0)))
        set_collision(mesh, job["coll"], b)
        use_nanite = job["nanite"] if job["nanite"] is not None else (mesh_tris >= NANITE_MIN_TRIS and not has_glass)
        if use_nanite:
            set_nanite(mesh, mesh_tris)
        elif mesh_tris > 2500:
            set_lods(mesh, mesh_tris, big=max(b.box_extent.x, b.box_extent.y, b.box_extent.z) > 150)
        EAL.save_asset(final)
        b = mesh.get_bounds()
        measured[cname] = {
            "slug": job["slug"], "path": final + "." + final.split("/")[-1], "kind": job["kind"],
            "category": job["category"], "tags": job["tags"], "solid": bool(job["solid"] and job["coll"] != "none"),
            "scale": job["scale"], "origin": [b.origin.x, b.origin.y, b.origin.z],
            "extent": [b.box_extent.x, b.box_extent.y, b.box_extent.z], "tris": int(mesh_tris),
            "nanite": bool(use_nanite), "lods": int(mesh.get_num_lods()), "coll": job["coll"],
        }
        for suffix, mult in job["sizes"].items():
            measured[cname + suffix] = dict(measured[cname], scale=job["scale"] * mult)
        log("OK %-26s %-34s size=%.0fx%.0fx%.0f cm tris=%d nanite=%s lods=%d" % (
            cname, mesh.get_name(), b.box_extent.x * 2, b.box_extent.y * 2, b.box_extent.z * 2, mesh_tris, use_nanite,
            mesh.get_num_lods()))
    EAL.delete_directory(dest)


def main():
    only = [s for s in os.environ.get("IA_PROPS_ONLY", "").split(",") if s]
    masters = build_masters(force=bool(os.environ.get("IA_PROPS_MASTERS")))
    measured = {}
    if os.path.exists(MEASURED):
        measured = json.load(open(MEASURED))
    failed = []
    for job in props_spec.JOBS:
        if only and job["name"] not in only and job["slug"] not in only:
            continue
        try:
            process_job(job, masters, measured)
        except Exception as e:
            import traceback
            failed.append(job["name"])
            log("FAILED %s: %s\n%s" % (job["name"], e, traceback.format_exc()))
        with open(MEASURED, "w") as f:
            json.dump(measured, f, indent=1, sort_keys=True)
    if EAL.does_directory_exist(TMP):
        EAL.delete_directory(TMP)
    EAL.save_directory(ROOT, only_if_is_dirty=True, recursive=True)
    log("IMPORT_DONE jobs=%d failed=%s" % (len(measured), failed))


main()
