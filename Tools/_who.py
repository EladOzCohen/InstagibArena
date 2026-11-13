import unreal
lvl = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
lvl.load_level("/Game/Maps/DM-Foundry")
act = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
big = []
for a in act.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if max(e.x, e.y, e.z) > 8000:
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        unreal.log("WHO %s class=%s ext=(%.0f,%.0f,%.0f) coll=%s profile=%s actor_coll=%s" % (a.get_actor_label(), a.get_class().get_name(), e.x, e.y, e.z,
            comp.get_collision_enabled() if comp else None, comp.get_collision_profile_name() if comp else None, a.get_actor_enable_collision()))
unreal.log("WHO_DONE")
