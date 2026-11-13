"""Cheap fake ambient occlusion for maps that have no GI: soft dark gradient quads (the NATURE pass).

    import shade_n
    shade_n.blob(m, "UnderCatwalk", x, y, z, 700, 360, strength=0.45, yaw=0)        # horizontal, on a floor
    shade_n.blob(m, "Corner", x, y, z, 300, 400, strength=0.4, pitch=90, yaw=90)    # vertical, on a wall

/Game/Materials/M_IAShade is translucent and unlit: black with an opacity that falls off smoothly to 0 at the quad's edge
(rounded-rectangle falloff in the quad's own UV, so a long thin quad gets a long thin soft shadow). One instance per
strength, M_IAShade_<n>. No collision, no shadow casting, depth tested, so it only costs the pixels it covers.
Keep the count per map in the dozens: every quad is a translucent draw.
"""

import unreal

lib = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
PATH = "/Game/Materials/M_IAShade"
_cache = {}

HLSL = """
float2 d = abs(UV - 0.5) * 2.0;
float e = pow(pow(d.x, 3.0) + pow(d.y, 3.0), 1.0 / 3.0);
float s = saturate(1.0 - e);
s = s * s * (3.0 - 2.0 * s);
return s * Strength;
"""


def _node(mat, cls, x, y, **props):
    e = lib.create_material_expression(mat, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def build(force=False):
    if eal.does_asset_exist(PATH):
        if not force:
            return eal.load_asset(PATH)
        eal.delete_asset(PATH)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset("M_IAShade", "/Game/Materials", unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    uv = _node(mat, unreal.MaterialExpressionTextureCoordinate, -600, 0)
    strength = _node(mat, unreal.MaterialExpressionScalarParameter, -600, 120, parameter_name="Strength", default_value=0.5)
    shade_rgb = _node(mat, unreal.MaterialExpressionVectorParameter, -600, 240, parameter_name="ShadeColor",
                      default_value=unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    c = _node(mat, unreal.MaterialExpressionCustom, -300, 40)
    arr = []
    for n in ("UV", "Strength"):
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        arr.append(ci)
    c.set_editor_property("description", "ShadeFalloff")
    c.set_editor_property("code", HLSL)
    c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    c.set_editor_property("inputs", arr)
    lib.connect_material_expressions(uv, "", c, "UV")
    lib.connect_material_expressions(strength, "", c, "Strength")
    lib.connect_material_property(shade_rgb, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.connect_material_property(c, "", unreal.MaterialProperty.MP_OPACITY)
    lib.recompile_material(mat)
    eal.save_asset(PATH)
    unreal.log("SHADE material built")
    return mat


def instance(strength, color=(0.0, 0.0, 0.0)):
    """Material instance with the given peak opacity (0..1) and shade colour (linear, default black)."""
    key = (round(strength, 3), tuple(color))
    if key in _cache:
        return _cache[key]
    parent = build()
    name = "MI_IAShade_%d%s" % (int(round(strength * 100)), "" if tuple(color) == (0.0, 0.0, 0.0) else "_c%d" % abs(hash(tuple(color)) % 1000))
    path = "/Game/Materials/" + name
    if eal.does_asset_exist(path):
        mic = eal.load_asset(path)
    else:
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, "/Game/Materials", unreal.MaterialInstanceConstant,
                                                                      unreal.MaterialInstanceConstantFactoryNew())
    lib.set_material_instance_parent(mic, parent)
    lib.set_material_instance_scalar_parameter_value(mic, "Strength", float(strength))
    lib.set_material_instance_vector_parameter_value(mic, "ShadeColor", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    lib.update_material_instance(mic)
    eal.save_asset(path)
    _cache[key] = mic
    return mic


def blob(m, label, x, y, z, sx, sy, strength=0.45, yaw=0.0, pitch=0.0, roll=0.0, color=(0.0, 0.0, 0.0), mat=None):
    """A soft dark quad centred at (x, y, z), sx x sy cm. Horizontal by default (lying on a floor: put z about 1.5 cm above it);
    for walls use wall_stain()."""
    plane = _cache.get("plane")
    if plane is None:
        plane = _cache["plane"] = eal.load_asset("/Engine/BasicShapes/Plane.Plane")
    actor = m._place(label, plane, (x, y, z), (sx / 100.0, sy / 100.0, 1.0), yaw, pitch, mat or instance(strength, color), False)
    if roll:
        actor.set_actor_rotation(unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw), False)
    comp = actor.static_mesh_component
    comp.set_editor_property("cast_shadow", False)
    try:
        actor.set_folder_path("Shade")
    except Exception:                                  # noqa: BLE001
        pass
    return actor


# ------------------------------------------------------------------------------------------------ coloured stains (moss, soot, damp)
STAIN_PATH = "/Game/Materials/M_IAStain"


def build_stain(force=False):
    """Lit translucent version of the shade quad with a colour: moss, damp, soot, rust streaks on walls and floors."""
    if eal.does_asset_exist(STAIN_PATH):
        if not force:
            return eal.load_asset(STAIN_PATH)
        eal.delete_asset(STAIN_PATH)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset("M_IAStain", "/Game/Materials", unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    try:
        mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    except Exception as e:                              # noqa: BLE001
        unreal.log_warning("STAIN lighting mode: %s" % e)
    uv = _node(mat, unreal.MaterialExpressionTextureCoordinate, -600, 0)
    strength = _node(mat, unreal.MaterialExpressionScalarParameter, -600, 120, parameter_name="Strength", default_value=0.5)
    color = _node(mat, unreal.MaterialExpressionVectorParameter, -600, 240, parameter_name="StainColor",
                  default_value=unreal.LinearColor(0.03, 0.05, 0.015, 1.0))
    rough = _node(mat, unreal.MaterialExpressionConstant, -600, 360, r=0.95)
    spec = _node(mat, unreal.MaterialExpressionConstant, -600, 420, r=0.15)
    c = _node(mat, unreal.MaterialExpressionCustom, -300, 40)
    arr = []
    for n in ("UV", "Strength"):
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        arr.append(ci)
    c.set_editor_property("description", "StainFalloff")
    # a little noise in the falloff so that the edge of a stain is not a clean oval
    c.set_editor_property("code", """
float2 d = abs(UV - 0.5) * 2.0;
float n = frac(sin(dot(floor(UV * 9.0), float2(12.9898, 78.233))) * 43758.5453);
float n2 = frac(sin(dot(floor(UV * 23.0), float2(39.346, 11.135))) * 24634.6345);
float e = pow(pow(d.x, 2.5) + pow(d.y, 2.5), 1.0 / 2.5) + (n - 0.5) * 0.22 + (n2 - 0.5) * 0.12;
float s = saturate(1.0 - e);
s = s * s * (3.0 - 2.0 * s);
return s * Strength;
""")
    c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    c.set_editor_property("inputs", arr)
    lib.connect_material_expressions(uv, "", c, "UV")
    lib.connect_material_expressions(strength, "", c, "Strength")
    lib.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    lib.connect_material_property(c, "", unreal.MaterialProperty.MP_OPACITY)
    lib.recompile_material(mat)
    eal.save_asset(STAIN_PATH)
    unreal.log("STAIN material built")
    return mat


def stain_instance(rgb, strength=0.6):
    """rgb: linear colour of the stain (moss green about (0.035, 0.06, 0.015), soot (0.01, 0.01, 0.01), rust (0.12, 0.04, 0.012))."""
    key = ("stain", tuple(round(v, 3) for v in rgb), round(strength, 3))
    if key in _cache:
        return _cache[key]
    parent = build_stain()
    name = "MI_IAStain_%d%d%d_%d" % (int(rgb[0] * 1000), int(rgb[1] * 1000), int(rgb[2] * 1000), int(round(strength * 100)))
    path = "/Game/Materials/" + name
    if eal.does_asset_exist(path):
        mic = eal.load_asset(path)
    else:
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, "/Game/Materials", unreal.MaterialInstanceConstant,
                                                                      unreal.MaterialInstanceConstantFactoryNew())
    lib.set_material_instance_parent(mic, parent)
    lib.set_material_instance_scalar_parameter_value(mic, "Strength", float(strength))
    lib.set_material_instance_vector_parameter_value(mic, "StainColor", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    lib.update_material_instance(mic)
    eal.save_asset(path)
    _cache[key] = mic
    return mic


def stain(m, label, x, y, z, sx, sy, rgb, strength=0.6, yaw=0.0):
    """A coloured soft stain lying on a floor (centre x, y; z about 1.5 cm above the surface), sx x sy cm."""
    return blob(m, label, x, y, z, sx, sy, strength, yaw=yaw, mat=stain_instance(rgb, strength))


def wall_stain(m, label, x, y, z, width, height, face_yaw, rgb=None, strength=0.5, black=False, mat=None):
    """A soft stain / shade on a wall: centre (x, y, z) already 2-3 cm in front of the surface, `width` along the wall,
    `height` up, face_yaw = the direction the wall faces (towards the viewer). Black=True uses the dark shade material."""
    if mat is None:
        mat = instance(strength) if black else stain_instance(rgb, strength)
    plane = _cache.get("plane")
    if plane is None:
        plane = _cache["plane"] = eal.load_asset("/Engine/BasicShapes/Plane.Plane")
    actor = m._place(label, plane, (x, y, z), (height / 100.0, width / 100.0, 1.0), face_yaw + 180.0, 90.0, mat, False)
    actor.static_mesh_component.set_editor_property("cast_shadow", False)
    try:
        actor.set_folder_path("Shade")
    except Exception:                                   # noqa: BLE001
        pass
    return actor


# ------------------------------------------------------------------------------------------------ smoke / steam puffs
SMOKE_PATH = "/Game/Materials/M_IASmoke"


def build_smoke(force=False):
    """Soft translucent puff for spheres: opaque in the middle, fading to nothing at the silhouette (fresnel), unlit colour."""
    if eal.does_asset_exist(SMOKE_PATH):
        if not force:
            return eal.load_asset(SMOKE_PATH)
        eal.delete_asset(SMOKE_PATH)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset("M_IASmoke", "/Game/Materials", unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", False)
    color = _node(mat, unreal.MaterialExpressionVectorParameter, -600, 0, parameter_name="SmokeColor",
                  default_value=unreal.LinearColor(0.05, 0.05, 0.05, 1.0))
    strength = _node(mat, unreal.MaterialExpressionScalarParameter, -600, 120, parameter_name="Strength", default_value=0.6)
    fres = _node(mat, unreal.MaterialExpressionFresnel, -600, 240, exponent=2.2, base_reflect_fraction=0.0)
    one_minus = _node(mat, unreal.MaterialExpressionOneMinus, -420, 240)
    lib.connect_material_expressions(fres, "", one_minus, "")
    mul = _node(mat, unreal.MaterialExpressionMultiply, -240, 180)
    lib.connect_material_expressions(one_minus, "", mul, "A")
    lib.connect_material_expressions(strength, "", mul, "B")
    lib.connect_material_property(color, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.connect_material_property(mul, "", unreal.MaterialProperty.MP_OPACITY)
    lib.recompile_material(mat)
    eal.save_asset(SMOKE_PATH)
    unreal.log("SMOKE material built")
    return mat


def smoke_instance(rgb, strength=0.6):
    key = ("smoke", tuple(round(v, 3) for v in rgb), round(strength, 3))
    if key in _cache:
        return _cache[key]
    parent = build_smoke()
    name = "MI_IASmoke_%d_%d_%d_%d" % (int(rgb[0] * 1000), int(rgb[1] * 1000), int(rgb[2] * 1000), int(round(strength * 100)))
    path = "/Game/Materials/" + name
    if eal.does_asset_exist(path):
        mic = eal.load_asset(path)
    else:
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, "/Game/Materials", unreal.MaterialInstanceConstant,
                                                                      unreal.MaterialInstanceConstantFactoryNew())
    lib.set_material_instance_parent(mic, parent)
    lib.set_material_instance_scalar_parameter_value(mic, "Strength", float(strength))
    lib.set_material_instance_vector_parameter_value(mic, "SmokeColor", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    lib.update_material_instance(mic)
    eal.save_asset(path)
    _cache[key] = mic
    return mic


def puff(m, label, x, y, z, dia, rgb, strength=0.6, squash=0.8):
    """A soft smoke / steam puff (sphere), no collision, no shadow. Stack a few with growing size for a plume."""
    sphere = _cache.get("sphere")
    if sphere is None:
        sphere = _cache["sphere"] = eal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
    actor = m._place(label, sphere, (x, y, z), (dia / 100.0, dia / 100.0, dia * squash / 100.0), 0.0, 0.0, smoke_instance(rgb, strength), False)
    actor.static_mesh_component.set_editor_property("cast_shadow", False)
    try:
        actor.set_folder_path("Smoke")
    except Exception:                                   # noqa: BLE001
        pass
    return actor
