import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
unreal.log("PROBE class=%s" % mat.get_class().get_name())
lib = unreal.MaterialEditingLibrary
unreal.log("PROBE vectors=%s" % list(lib.get_vector_parameter_names(mat)))
unreal.log("PROBE scalars=%s" % list(lib.get_scalar_parameter_names(mat)))
unreal.log("PROBE textures=%s" % list(lib.get_texture_parameter_names(mat)))
