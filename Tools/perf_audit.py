"""Performance audit of the shipped maps (read-only: it opens each map and logs numbers, saves nothing).

Run: powershell -File Tools\run_ue.ps1 -Script Tools\perf_audit.py -Log Saved\perf_audit.log -Grep "PERFAUDIT"
Env IA_AUDIT_MAPS=DM-Forge,DM-Neon limits the maps.
"""
import collections
import os

import unreal

MAPS = ["DM-Foundry", "DM-Temple", "DM-Dock", "DM-Skyline", "DM-Neon", "DM-Forge", "DM-Glacier", "DM-Canyon", "MainMenu"]
sel = os.environ.get("IA_AUDIT_MAPS")
if sel:
    MAPS = sel.split(",")

level_lib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_lib = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    unreal.log("PERFAUDIT " + msg)


for name in MAPS:
    if not level_lib.load_level("/Game/Maps/" + name):
        log("%s could not load" % name)
        continue
    actors = actor_lib.get_all_level_actors()
    classes = collections.Counter(type(a).__name__ for a in actors)
    log("%s actors=%d classes=%s" % (name, len(actors), dict(classes.most_common(12))))

    # lights
    lights = [a for a in actors if isinstance(a, (unreal.PointLight, unreal.SpotLight, unreal.RectLight))]
    shadow_lights = 0
    radii = []
    for l in lights:
        c = l.get_component_by_class(unreal.LightComponent)
        if c.get_editor_property("cast_shadows"):
            shadow_lights += 1
        try:
            radii.append(c.get_editor_property("attenuation_radius"))
        except Exception:
            pass
    big = [r for r in radii if r > 1000]
    if os.environ.get("IA_AUDIT_LIGHTS"):
        for l in lights:
            c = l.get_component_by_class(unreal.LightComponent)
            try:
                log("%s LIGHT %s class=%s loc=(%.0f,%.0f,%.0f) radius=%.0f intensity=%.1f units=%s shadows=%s spec=%.2f" % (
                    name, l.get_actor_label(), type(l).__name__, l.get_actor_location().x, l.get_actor_location().y,
                    l.get_actor_location().z, c.get_editor_property("attenuation_radius"), c.get_editor_property("intensity"),
                    c.get_editor_property("intensity_units"), c.get_editor_property("cast_shadows"),
                    c.get_editor_property("specular_scale")))
            except Exception as exc:
                log("%s LIGHT %s (%s)" % (name, l.get_actor_label(), exc))
    notmov = 0
    for l in lights:
        if l.get_component_by_class(unreal.LightComponent).get_editor_property("mobility") != unreal.ComponentMobility.MOVABLE:
            notmov += 1
    log("%s lights=%d shadow_casting=%d not_movable=%d radius_avg=%.0f radius_max=%.0f radius>1000=%d" % (
        name, len(lights), shadow_lights, notmov,
        sum(radii) / max(1, len(radii)), max(radii) if radii else 0, len(big)))

    # static meshes
    sm_actors = [a for a in actors if isinstance(a, unreal.StaticMeshActor)]
    meshes = collections.Counter()
    mats = collections.Counter()
    nanite = 0
    cast_shadow = 0
    sizes = []
    for a in sm_actors:
        comp = a.static_mesh_component
        sm = comp.static_mesh
        if sm is None:
            continue
        meshes[sm.get_path_name()] += 1
        for i in range(comp.get_num_materials()):
            m = comp.get_material(i)
            if m is not None:
                mats[m.get_path_name()] += 1
        try:
            if sm.get_editor_property("nanite_settings").get_editor_property("enabled"):
                nanite += 1
        except Exception:
            pass
        if comp.get_editor_property("cast_shadow"):
            cast_shadow += 1
        ext = a.get_actor_bounds(False)[1]
        sizes.append(max(ext.x, ext.y, ext.z) * 2)
    sizes.sort()

    def pct(p):
        return sizes[int(len(sizes) * p)] if sizes else 0

    log("%s staticmesh_actors=%d unique_meshes=%d unique_mats=%d nanite_actor_uses=%d cast_shadow=%d size_cm p10=%.0f p25=%.0f p50=%.0f p75=%.0f p90=%.0f" % (
        name, len(sm_actors), len(meshes), len(mats), nanite, cast_shadow, pct(.1), pct(.25), pct(.5), pct(.75), pct(.9)))
    log("%s topmeshes=%s" % (name, [(k.split('/')[-1], v) for k, v in meshes.most_common(10)]))
    log("%s topmats=%s" % (name, [(k.split('/')[-1], v) for k, v in mats.most_common(8)]))
    small = sum(1 for s in sizes if s < 100)
    mid = sum(1 for s in sizes if 100 <= s < 300)
    log("%s size<1m=%d size1-3m=%d size>=3m=%d" % (name, small, mid, len(sizes) - small - mid))
