"""Creates /Game/Materials/M_Scorch, the deferred decal used for the marks that shots leave on walls.

A soft round mark that is dark in the middle, with a hot glowing core. The game dims it over time through the
parameters Glow (0..1, the hot core) and Alpha (0..1, the whole mark). Color tints the glow.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_decal_assets.py" -unattended -nullrhi -nosplash
Look for DECALASSET_DONE in the log.
"""

import unreal

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

PATH = "/Game/Materials"
NAME = "M_Scorch"
FULL = "%s/%s" % (PATH, NAME)

if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    unreal.EditorAssetLibrary.delete_asset(FULL)

mat = tools.create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)


def node(cls, x, y):
    return lib.create_material_expression(mat, cls, x, y)


# distance from the middle of the decal: 0 in the middle, 1 at the edge of the square
tc = node(unreal.MaterialExpressionTextureCoordinate, -1400, 0)
mid = node(unreal.MaterialExpressionConstant2Vector, -1400, 200)
mid.set_editor_property("r", 0.5)
mid.set_editor_property("g", 0.5)
dist = node(unreal.MaterialExpressionDistance, -1180, 80)
lib.connect_material_expressions(tc, "", dist, "A")
lib.connect_material_expressions(mid, "", dist, "B")
twice = node(unreal.MaterialExpressionMultiply, -980, 80)
two = node(unreal.MaterialExpressionConstant, -1180, 220)
two.set_editor_property("r", 2.0)
lib.connect_material_expressions(dist, "", twice, "A")
lib.connect_material_expressions(two, "", twice, "B")
inv = node(unreal.MaterialExpressionOneMinus, -800, 80)
lib.connect_material_expressions(twice, "", inv, "")
sat = node(unreal.MaterialExpressionSaturate, -640, 80)
lib.connect_material_expressions(inv, "", sat, "")

# the mark: soft edge
edge_pow = node(unreal.MaterialExpressionConstant, -640, 220)
edge_pow.set_editor_property("r", 1.6)
shape = node(unreal.MaterialExpressionPower, -460, 80)
lib.connect_material_expressions(sat, "", shape, "Base")
lib.connect_material_expressions(edge_pow, "", shape, "Exp")

alpha_param = node(unreal.MaterialExpressionScalarParameter, -460, 260)
alpha_param.set_editor_property("parameter_name", "Alpha")
alpha_param.set_editor_property("default_value", 1.0)
opacity = node(unreal.MaterialExpressionMultiply, -240, 120)
lib.connect_material_expressions(shape, "", opacity, "A")
lib.connect_material_expressions(alpha_param, "", opacity, "B")
strength = node(unreal.MaterialExpressionConstant, -240, 260)
strength.set_editor_property("r", 0.9)
opacity2 = node(unreal.MaterialExpressionMultiply, -60, 120)
lib.connect_material_expressions(opacity, "", opacity2, "A")
lib.connect_material_expressions(strength, "", opacity2, "B")

# the hot core: a tight spot that cools down
core_pow = node(unreal.MaterialExpressionConstant, -640, 400)
core_pow.set_editor_property("r", 7.0)
core = node(unreal.MaterialExpressionPower, -460, 400)
lib.connect_material_expressions(sat, "", core, "Base")
lib.connect_material_expressions(core_pow, "", core, "Exp")
glow_param = node(unreal.MaterialExpressionScalarParameter, -460, 540)
glow_param.set_editor_property("parameter_name", "Glow")
glow_param.set_editor_property("default_value", 1.0)
color_param = node(unreal.MaterialExpressionVectorParameter, -460, 640)
color_param.set_editor_property("parameter_name", "Color")
color_param.set_editor_property("default_value", unreal.LinearColor(0.0, 0.9, 1.0, 1.0))
core_glow = node(unreal.MaterialExpressionMultiply, -240, 440)
lib.connect_material_expressions(core, "", core_glow, "A")
lib.connect_material_expressions(glow_param, "", core_glow, "B")
core_color = node(unreal.MaterialExpressionMultiply, -60, 480)
lib.connect_material_expressions(core_glow, "", core_color, "A")
lib.connect_material_expressions(color_param, "", core_color, "B")
bright = node(unreal.MaterialExpressionConstant, -60, 620)
bright.set_editor_property("r", 6.0)
emissive = node(unreal.MaterialExpressionMultiply, 120, 520)
lib.connect_material_expressions(core_color, "", emissive, "A")
lib.connect_material_expressions(bright, "", emissive, "B")

# the base color of the mark: almost black soot
soot = node(unreal.MaterialExpressionConstant3Vector, -60, -80)
soot.set_editor_property("constant", unreal.LinearColor(0.012, 0.011, 0.01, 1.0))

lib.connect_material_property(soot, "", unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(opacity2, "", unreal.MaterialProperty.MP_OPACITY)
lib.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

lib.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(FULL)
unreal.log("DECALASSET vectors=%s scalars=%s" % (list(lib.get_vector_parameter_names(mat)), list(lib.get_scalar_parameter_names(mat))))
unreal.log("DECALASSET_DONE")
