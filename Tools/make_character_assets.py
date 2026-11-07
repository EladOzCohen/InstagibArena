"""Creates /Game/Characters/M_IABody, the flat color material used by all five characters and their accessories,
and prints a few facts about the mannequin assets.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_character_assets.py" -unattended -nullrhi -nosplash
"""

import unreal

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

PATH = "/Game/Characters"
NAME = "M_IABody"
FULL = "%s/%s" % (PATH, NAME)

if unreal.EditorAssetLibrary.does_asset_exist(FULL):
    unreal.EditorAssetLibrary.delete_asset(FULL)

mat = tools.create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())

color = lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -700, -200)
color.set_editor_property("parameter_name", "Color")
color.set_editor_property("default_value", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))

rough = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 0)
rough.set_editor_property("parameter_name", "Roughness")
rough.set_editor_property("default_value", 0.55)

metal = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 120)
metal.set_editor_property("parameter_name", "Metallic")
metal.set_editor_property("default_value", 0.15)

glow = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 260)
glow.set_editor_property("parameter_name", "Glow")
glow.set_editor_property("default_value", 0.0)

emissive = lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -420, 220)
lib.connect_material_expressions(color, "", emissive, "A")
lib.connect_material_expressions(glow, "", emissive, "B")

lib.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
lib.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
lib.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

mat.set_editor_property("used_with_skeletal_mesh", True)
lib.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(FULL)
unreal.log("CHARASSET material vectors=%s scalars=%s" % (list(lib.get_vector_parameter_names(mat)), list(lib.get_scalar_parameter_names(mat))))

# Facts about the mannequin pack.
for path in ("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple", "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        unreal.log_error("CHARASSET missing " + path)
        continue
    unreal.log("CHARASSET %s materials=%d physics=%s skeleton=%s" % (
        path.split("/")[-1], len(asset.materials),
        asset.get_editor_property("physics_asset"), asset.get_editor_property("skeleton")))

abp = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
unreal.log("CHARASSET abp=%s" % abp)
unreal.log("CHARASSET_DONE")
