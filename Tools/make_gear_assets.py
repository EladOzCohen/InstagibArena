"""Builds the character gear: one master material, one static mesh per character and bone, and the C++ table that lists them.

  /Game/Characters/Gear/M_IAGear        master material: seven palette roles chosen per vertex by the second UV set (u = role, v = ambient occlusion)
  /Game/Characters/Gear/MI_IAGear       default instance (grey), the characters override the palette with a dynamic instance (IAPlayerCharacter::ApplyLook)
  /Game/Characters/Gear/SM_<Name>_<bone> the pieces of one character on one bone, in the bone's local space (character axes: X forward, Y right, Z up)
  Source/InstagibArena/IACharacterGear.inl  generated list (look index -> bone, mesh path) included by IACharacterRoster.h

The geometry comes from Tools/gear_chars_*.py (pure python, see Tools/gear_preview.py for a quick look without the engine).
Roles (mesh_char.ROLE_NAMES): 0 Plate (suit colour), 1 Cloth, 2 Accent, 3 Team, 4 Trim (dark metal), 5 Glow, 6 Light (off-white).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools/make_gear_assets.py -unattended -nullrhi -nosplash
Environment: IA_GEAR_ONLY=0,3 (only these looks), IA_GEAR_FORCE=1 (rebuild the material). Output lines start with GEAR; the last is GEAR_DONE.
"""

import os
import sys

import unreal

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import gear_body as gb          # noqa: E402
import gear_roster as gr        # noqa: E402
import mapkit_b                 # noqa: E402  (winding detection only)
import mesh_char as mc          # noqa: E402

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary

PATH = "/Game/Characters/Gear"
INL = os.path.join(os.path.dirname(_TOOLS), "Source", "InstagibArena", "IACharacterGear.inl")


def log(msg):
    unreal.log("GEAR " + msg)


if not eal.does_directory_exist(PATH):
    eal.make_directory(PATH)

# ------------------------------------------------------------------------------------------------ master material
MFULL = PATH + "/M_IAGear"
if not eal.does_asset_exist(MFULL) or os.environ.get("IA_GEAR_FORCE") == "1":
    if eal.does_asset_exist(MFULL):
        eal.delete_asset(MFULL)
    mat = tools.create_asset("M_IAGear", PATH, unreal.Material, unreal.MaterialFactoryNew())

    def node(cls, x, y):
        return lib.create_material_expression(mat, cls, x, y)

    def vparam(name, default, x, y):
        n = node(unreal.MaterialExpressionVectorParameter, x, y)
        n.set_editor_property("parameter_name", name)
        n.set_editor_property("default_value", default)
        return n

    def sparam(name, default, x, y):
        n = node(unreal.MaterialExpressionScalarParameter, x, y)
        n.set_editor_property("parameter_name", name)
        n.set_editor_property("default_value", default)
        return n

    def link(a, b, to_input, out=""):
        lib.connect_material_expressions(a, out, b, to_input)

    def mul(a, b, x, y, a_out="", b_out=""):
        n = node(unreal.MaterialExpressionMultiply, x, y)
        link(a, n, "A", a_out)
        link(b, n, "B", b_out)
        return n

    def add(a, b, x, y, a_out="", b_out=""):
        n = node(unreal.MaterialExpressionAdd, x, y)
        link(a, n, "A", a_out)
        link(b, n, "B", b_out)
        return n

    def const(v, x, y):
        n = node(unreal.MaterialExpressionConstant, x, y)
        n.set_editor_property("r", v)
        return n

    suit_n = eal.load_asset("/Game/Characters/Textures/T_CharSuit_N")
    suit_r = eal.load_asset("/Game/Characters/Textures/T_CharSuit_R")
    suit_d = eal.load_asset("/Game/Characters/Textures/T_CharSuit_D")

    # --- parameters
    cols = [vparam("C%d" % i, unreal.LinearColor(0.3, 0.3, 0.3, 0.7), -2000, -900 + i * 110) for i in range(7)]   # rgb colour, a = roughness
    metals = [sparam("Metal%d" % i, 0.0, -2000, 0 + i * 70) for i in range(7)]
    p_glow = sparam("Glow", 0.0, -2000, 600)
    p_teamglow = sparam("TeamGlow", 0.0, -2000, 680)
    p_detail = sparam("Detail", 1.0, -2000, 760)
    p_tile = sparam("Tile", 5.0, -2000, 840)
    p_rim = sparam("Rim", 0.0, -2000, 920)
    p_spec = sparam("Specular", 0.35, -2000, 1000)
    p_rimcolor = vparam("RimColor", unreal.LinearColor(1.0, 1.0, 1.0, 1.0), -2000, 1080)

    # --- role and ao from the second UV set
    uv1 = node(unreal.MaterialExpressionTextureCoordinate, -1700, -1100)
    uv1.set_editor_property("coordinate_index", 1)
    role = node(unreal.MaterialExpressionComponentMask, -1500, -1150)
    for ch, on in (("r", True), ("g", False), ("b", False), ("a", False)):
        role.set_editor_property(ch, on)
    link(uv1, role, "")
    ao = node(unreal.MaterialExpressionComponentMask, -1500, -1050)
    for ch, on in (("r", False), ("g", True), ("b", False), ("a", False)):
        ao.set_editor_property(ch, on)
    link(uv1, ao, "")

    weights = []
    for i in range(7):
        sb = node(unreal.MaterialExpressionSubtract, -1300, -1250 + i * 60)
        link(role, sb, "A")
        sb.set_editor_property("const_b", float(i))
        ab = node(unreal.MaterialExpressionAbs, -1150, -1250 + i * 60)
        link(sb, ab, "")
        om = node(unreal.MaterialExpressionOneMinus, -1000, -1250 + i * 60)
        link(ab, om, "")
        sa = node(unreal.MaterialExpressionSaturate, -850, -1250 + i * 60)
        link(om, sa, "")
        weights.append(sa)

    def weighted_sum(terms, x, y, out=""):
        """terms: list of (node, out) already scaled; returns the sum node."""
        acc = terms[0]
        for k in range(1, len(terms)):
            acc = add(acc, terms[k], x + k * 40, y + k * 40)
        return acc

    # base colour, roughness, metallic
    col_terms = [mul(cols[i], weights[i], -600, -900 + i * 80, "RGB", "") for i in range(7)]
    base0 = weighted_sum(col_terms, -400, -900)
    rough_terms = [mul(cols[i], weights[i], -600, -300 + i * 70, "A", "") for i in range(7)]
    rough0 = weighted_sum(rough_terms, -400, -300)
    metal_terms = [mul(metals[i], weights[i], -600, 250 + i * 70) for i in range(7)]
    metal0 = weighted_sum(metal_terms, -400, 250)

    # per role strength of the cloth detail
    DETAIL = [0.35, 1.0, 0.3, 0.25, 0.4, 0.0, 0.8]
    dk_terms = [mul(const(DETAIL[i], -700, 800 + i * 50), weights[i], -600, 800 + i * 50) for i in range(7)]
    dk_sum = weighted_sum(dk_terms, -400, 800)
    dk = mul(dk_sum, p_detail, -200, 820)

    tc = node(unreal.MaterialExpressionTextureCoordinate, -1700, 600)
    uv = mul(tc, p_tile, -1500, 600)

    def sample(texture, sampler, x, y):
        n = node(unreal.MaterialExpressionTextureSample, x, y)
        n.set_editor_property("texture", texture)
        n.set_editor_property("sampler_type", sampler)
        link(uv, n, "UVs")
        return n

    t_n = sample(suit_n, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -300, 1000)
    t_r = sample(suit_r, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, -300, 1200)
    t_d = sample(suit_d, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -300, 1400)
    flat = node(unreal.MaterialExpressionConstant3Vector, -300, 900)
    flat.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    nrm = node(unreal.MaterialExpressionLinearInterpolate, 0, 1000)
    link(flat, nrm, "A")
    link(t_n, nrm, "B", "RGB")
    link(dk, nrm, "Alpha")

    # roughness + (cloth - 0.5) * 0.6 * dk
    sub = node(unreal.MaterialExpressionSubtract, 0, 1200)
    link(t_r, sub, "A", "R")
    sub.set_editor_property("const_b", 0.5)
    r1 = mul(sub, dk, 150, 1200)
    r2 = node(unreal.MaterialExpressionMultiply, 300, 1200)
    link(r1, r2, "A")
    r2.set_editor_property("const_b", 0.6)
    radd = add(rough0, r2, 450, 1100)
    rcl = node(unreal.MaterialExpressionClamp, 600, 1100)
    link(radd, rcl, "")
    rcl.set_editor_property("min_default", 0.08)
    rcl.set_editor_property("max_default", 1.0)

    # colour variation from the cloth map (+-20 %), scaled by dk, and the ao darkening
    gray = node(unreal.MaterialExpressionDesaturation, 0, 1400)
    link(t_d, gray, "", "RGB")
    ratio = node(unreal.MaterialExpressionDivide, 150, 1400)
    link(gray, ratio, "A")
    ratio.set_editor_property("const_b", 0.12)
    rcl2 = node(unreal.MaterialExpressionClamp, 300, 1400)
    link(ratio, rcl2, "")
    rcl2.set_editor_property("min_default", 0.8)
    rcl2.set_editor_property("max_default", 1.2)
    var = node(unreal.MaterialExpressionLinearInterpolate, 450, 1400)
    var.set_editor_property("const_a", 1.0)
    link(rcl2, var, "B")
    link(dk, var, "Alpha")
    aoc = node(unreal.MaterialExpressionLinearInterpolate, 150, 1550)
    aoc.set_editor_property("const_a", 0.45)
    aoc.set_editor_property("const_b", 1.0)
    link(ao, aoc, "Alpha")
    b1 = mul(base0, var, 650, 1400)
    base = mul(b1, aoc, 800, 1400)

    # emissive: glow role, team role, rim light
    em_glow = mul(cols[5], weights[5], -300, -1300, "RGB", "")
    em_glow2 = mul(em_glow, p_glow, -100, -1300)
    em_team = mul(cols[3], weights[3], -300, -1400, "RGB", "")
    em_team2 = mul(em_team, p_teamglow, -100, -1400)
    fres = node(unreal.MaterialExpressionFresnel, -300, -1550)
    fres.set_editor_property("exponent", 3.5)
    fres.set_editor_property("base_reflect_fraction", 0.0)
    fr_c = mul(p_rimcolor, fres, -100, -1550, "RGB", "")
    fr_r = mul(fr_c, p_rim, 100, -1550)
    em = add(add(em_glow2, em_team2, 200, -1350), fr_r, 350, -1400)

    lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(metal0, "", unreal.MaterialProperty.MP_METALLIC)
    lib.connect_material_property(p_spec, "", unreal.MaterialProperty.MP_SPECULAR)
    lib.connect_material_property(rcl, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)
    lib.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    eal.save_asset(MFULL)
    log("material built, vectors=%s scalars=%s" % (list(lib.get_vector_parameter_names(mat)), list(lib.get_scalar_parameter_names(mat))))

master = eal.load_asset(MFULL)
IFULL = PATH + "/MI_IAGear"
if not eal.does_asset_exist(IFULL):
    mi = tools.create_asset("MI_IAGear", PATH, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
else:
    mi = eal.load_asset(IFULL)
lib.set_material_instance_parent(mi, master)
DEF = [(0.18, 0.19, 0.22, 0.6), (0.1, 0.1, 0.11, 0.9), (0.6, 0.35, 0.05, 0.55), (0.6, 0.05, 0.05, 0.55), (0.04, 0.045, 0.055, 0.5), (0.1, 0.9, 1.0, 0.4), (0.8, 0.8, 0.76, 0.9)]
for i, c in enumerate(DEF):
    lib.set_material_instance_vector_parameter_value(mi, "C%d" % i, unreal.LinearColor(*c))
lib.set_material_instance_scalar_parameter_value(mi, "Glow", 0.0)
lib.update_material_instance(mi)
eal.save_asset(IFULL)


# ------------------------------------------------------------------------------------------------ meshes
def disable_lightmap_uvs(sm):
    """The second UV set carries the palette role, so Unreal must not use it for generated lightmap UVs."""
    try:
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        bs = sub.get_lod_build_settings(sm, 0)
        bs.set_editor_property("generate_lightmap_u_vs", False)
        sub.set_lod_build_settings(sm, 0, bs)
    except Exception as e:                  # noqa: BLE001
        log("WARNING lightmap uv setting failed: %s" % e)
    try:
        sm.set_editor_property("light_map_coordinate_index", 0)
    except Exception as e:                  # noqa: BLE001
        log("WARNING light_map_coordinate_index failed: %s" % e)


def commit(name, m, shift):
    path = "%s/SM_%s" % (PATH, name)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    flip = mapkit_b._winding_flip()
    verts = [unreal.Vector(p[0] - shift[0], p[1] - shift[1], p[2] - shift[2]) for p in m.v]
    norms = [unreal.Vector(*n) for n in m.n]
    uv0 = [unreal.Vector2D(u, v) for (u, v) in m.uv]
    uv1 = [unreal.Vector2D(float(r), a) for r, a in zip(m.role, m.ao)]
    idx = [unreal.IntVector(a, c, b) if flip else unreal.IntVector(a, b, c) for (a, b, c) in m.t]
    buf = unreal.GeometryScriptSimpleMeshBuffers()
    buf.set_editor_property("vertices", verts)
    buf.set_editor_property("normals", norms)
    buf.set_editor_property("uv0", uv0)
    buf.set_editor_property("uv1", uv1)
    buf.set_editor_property("triangles", idx)
    dm = unreal.DynamicMesh()
    unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dm, buf, 0)
    nopts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    nopts.set_editor_property("enable_recompute_normals", False)
    nopts.set_editor_property("enable_recompute_tangents", True)
    nopts.set_editor_property("collision_mode", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    res = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, path, nopts)
    sm = res[0] if isinstance(res, tuple) else res
    if sm is None:
        raise RuntimeError("could not create " + path)
    sm = eal.load_asset(path)
    sm.set_material(0, mi)
    disable_lightmap_uvs(sm)
    # no collision: pure decoration
    try:
        bs = sm.get_editor_property("body_setup")
        if bs:
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    except Exception:                       # noqa: BLE001
        pass
    eal.save_loaded_asset(sm)
    return sm


only = os.environ.get("IA_GEAR_ONLY")
wanted = [int(x) for x in only.split(",")] if only else list(range(len(gr.LOOKS)))
table = {}
for i in range(len(gr.LOOKS)):
    look = gr.LOOKS[i]
    try:
        kit = gr.build(i)
    except KeyError:
        table[i] = []
        continue
    B = gb.body(look["quinn"])
    pieces = []
    name = look["name"].replace("-", "").replace(" ", "")
    for bone in sorted(kit.parts):
        g = kit.parts[bone]
        pieces.append((bone, "/Game/Characters/Gear/SM_%s_%s" % (name, bone)))
        if i in wanted:
            commit("%s_%s" % (name, bone), g, B.bone(bone))
    table[i] = pieces
    log("%d %s: %d pieces, %d triangles%s" % (i, look["name"], len(pieces), kit.tri_count(), "" if i in wanted else " (not rebuilt)"))

with open(INL, "w", encoding="utf-8", newline="\n") as f:
    f.write("// Generated by Tools/make_gear_assets.py - do not edit. One list per look: the bone a gear mesh is attached to and its asset path.\n")
    for i in range(len(gr.LOOKS)):
        f.write("{ // %d %s\n" % (i, gr.LOOKS[i]["name"]))
        for bone, path in table.get(i, []):
            f.write('\t{ TEXT("%s"), TEXT("%s.%s") },\n' % (bone, path, path.split("/")[-1]))
        f.write("},\n")
log("wrote " + INL)
unreal.log("GEAR_DONE")
