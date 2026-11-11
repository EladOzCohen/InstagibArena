"""Small toolkit for building blockout maps from engine shapes with Python.

Used by make_map_temple.py, make_map_dock.py and make_map_skyline.py.
Units are Unreal units (1 uu = 1 cm). Boxes are given by their center and full size.
"""

import math
import os
import random
import sys

import unreal

PROJECT_TOOLS = os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools")
if PROJECT_TOOLS not in sys.path:
    sys.path.insert(0, PROJECT_TOOLS)


def _color(rgb):
    """unreal.Color from 0..1 floats. The Python constructor takes (b, g, r, a), so always use keywords."""
    return unreal.Color(r=int(rgb[0] * 255), g=int(rgb[1] * 255), b=int(rgb[2] * 255), a=255)


def begin_level(map_path):
    """Opens a fresh empty level at map_path. An existing map is emptied in place and reused.

    (new_level refuses to overwrite an existing asset, and in that case the script would
    silently edit whatever level happened to be open, so it must never be called for those.)
    """
    level_lib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_lib = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not level_lib.load_level(map_path):
            raise RuntimeError("could not open existing map " + map_path)
        removed = 0
        for actor in actor_lib.get_all_level_actors():
            try:
                if actor_lib.destroy_actor(actor):
                    removed += 1
            except Exception:
                pass
        unreal.log("BEGIN_LEVEL emptied %s (%d actors removed)" % (map_path, removed))
    else:
        if not level_lib.new_level(map_path):
            raise RuntimeError("could not create map " + map_path)
        unreal.log("BEGIN_LEVEL created %s" % map_path)


class MapBuilder:
    def __init__(self, map_path):
        self.level_lib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        self.actor_lib = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        self.editor_lib = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        self.cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
        self.cylinder = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
        self.map_path = map_path
        self.mats = {}
        self.box_count = 0
        self.start_count = 0
        begin_level(map_path)

    # ------------------------------------------------------------ materials
    def material(self, name, rgb, roughness=0.85):
        """A colored material instance of the engine's basic shape material."""
        if name in self.mats:
            return self.mats[name]
        folder = "/Game/Materials"
        full = "%s/%s" % (folder, name)
        if unreal.EditorAssetLibrary.does_asset_exist(full):
            mic = unreal.EditorAssetLibrary.load_asset(full)
        else:
            tools = unreal.AssetToolsHelpers.get_asset_tools()
            mic = tools.create_asset(name, folder, unreal.MaterialInstanceConstant,
                                     unreal.MaterialInstanceConstantFactoryNew())
        lib = unreal.MaterialEditingLibrary
        lib.set_material_instance_parent(
            mic, unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"))
        lib.set_material_instance_vector_parameter_value(mic, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        lib.set_material_instance_scalar_parameter_value(mic, "Roughness", roughness)
        lib.update_material_instance(mic)
        unreal.EditorAssetLibrary.save_asset(full)
        self.mats[name] = mic
        return mic

    # --------------------------------------------------------------- shapes
    def _place(self, label, mesh, loc, scale, yaw, pitch, mat, solid):
        actor = self.actor_lib.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw))
        actor.set_actor_label(label)
        comp = actor.static_mesh_component
        comp.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(*scale))
        if mat is not None:
            comp.set_material(0, mat)
        if not solid:
            comp.set_collision_profile_name("NoCollision")
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        self.box_count += 1
        return actor

    def box(self, label, cx, cy, cz, sx, sy, sz, yaw=0.0, pitch=0.0, mat=None, solid=True):
        return self._place(label, self.cube, (cx, cy, cz), (sx / 100.0, sy / 100.0, sz / 100.0), yaw, pitch, mat, solid)

    def column(self, label, cx, cy, z_bottom, z_top, diameter, mat=None, solid=True):
        h = z_top - z_bottom
        return self._place(label, self.cylinder, (cx, cy, z_bottom + h / 2.0),
                           (diameter / 100.0, diameter / 100.0, h / 100.0), 0.0, 0.0, mat, solid)

    def slope(self, label, p0, p1, width, thickness=40.0, mat=None):
        """A ramp from point p0=(x,y,z) up (or down) to p1=(x,y,z). The top surface passes through both points."""
        dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        run = math.hypot(dx, dy)
        length = math.hypot(run, dz)
        pitch = math.degrees(math.atan2(dz, run))
        yaw = math.degrees(math.atan2(dy, dx))
        cx, cy, cz = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, (p0[2] + p1[2]) / 2.0
        # Move the center down along the slab normal so the top surface goes through the points.
        cz -= thickness / 2.0 * math.cos(math.radians(pitch))
        return self.box(label, cx, cy, cz, length, width, thickness, yaw=yaw, pitch=pitch, mat=mat)

    def stairs(self, label, x, y, z_base, yaw, width, steps, rise, run, mat=None):
        """Stairs starting at (x, y) at height z_base and climbing along yaw. Each step is a solid block."""
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for i in range(steps):
            h = (i + 1) * rise
            d = (i + 0.5) * run
            self.box("%s_%d" % (label, i), x + c * d, y + s * d, z_base + h / 2.0, run, width, h, yaw=yaw, mat=mat)

    # --------------------------------------------------------------- others
    def spawn(self, cls, label, loc=(0, 0, 0), rot=(0, 0, 0)):
        actor = self.actor_lib.spawn_actor_from_class(
            cls, unreal.Vector(*loc), unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
        actor.set_actor_label(label)
        return actor

    def starts(self, points):
        """points: list of (x, y, z_ground, yaw)."""
        for i, (x, y, z, yaw) in enumerate(points):
            self.spawn(unreal.PlayerStart, "PlayerStart_%d" % i, (x, y, z + 110), (0, 0, yaw))
            self.start_count += 1

    def face_center_starts(self, points):
        """points: list of (x, y, z_ground). Players look at the middle of the map."""
        self.starts([(x, y, z, math.degrees(math.atan2(-y, -x))) for x, y, z in points])

    def point_light(self, label, loc, rgb, intensity, radius):
        light = self.spawn(unreal.PointLight, label, loc)
        comp = light.get_component_by_class(unreal.PointLightComponent)
        comp.set_editor_property("intensity", intensity)
        comp.set_editor_property("light_color", _color(rgb))
        comp.set_editor_property("attenuation_radius", radius)
        comp.set_editor_property("source_radius", 20.0)
        return light

    def sky(self, sun_pitch=-45.0, sun_yaw=35.0, sun_intensity=None, sun_rgb=None, sky_intensity=2.0, sky_rgb=None):
        sun = self.spawn(unreal.DirectionalLight, "Sun", (0, 0, 2000), (0, sun_pitch, sun_yaw))
        comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if sun_intensity is not None:
            comp.set_editor_property("intensity", sun_intensity)
        if sun_rgb is not None:
            comp.set_editor_property("light_color", _color(sun_rgb))
        self.spawn(unreal.SkyAtmosphere, "SkyAtmosphere")
        skylight = self.spawn(unreal.SkyLight, "SkyLight", (0, 0, 1500))
        sky_comp = skylight.get_component_by_class(unreal.SkyLightComponent)
        sky_comp.set_editor_property("real_time_capture", True)
        sky_comp.set_editor_property("intensity", sky_intensity)
        # The sky capture is very blue; a warm tint keeps shadows from turning navy.
        sky_comp.set_editor_property("light_color", _color(sky_rgb or (1.0, 0.886, 0.745)))

        # A weak second light from the opposite side, without shadows, so that the faces away
        # from the sun are readable instead of black.
        fill = self.spawn(unreal.DirectionalLight, "FillLight", (0, 0, 2100), (0, -28.0, sun_yaw + 180.0))
        fill_comp = fill.get_component_by_class(unreal.DirectionalLightComponent)
        fill_comp.set_editor_property("intensity", 1.6)
        fill_comp.set_editor_property("cast_shadows", False)
        fill_comp.set_editor_property("atmosphere_sun_light", False)
        fill_comp.set_editor_property("forward_shading_priority", 0)
        comp.set_editor_property("forward_shading_priority", 1)
        fill_comp.set_editor_property("light_color", _color((0.745, 0.824, 1.0)))

        self.spawn(unreal.ExponentialHeightFog, "Fog", (0, 0, 200))

    def finish(self, kill_z=None):
        world = self.editor_lib.get_editor_world()
        if kill_z is not None:
            world.get_world_settings().set_editor_property("kill_z", float(kill_z))
        self.level_lib.save_current_level()
        unreal.log("MAKEMAP_DONE %s boxes=%d starts=%d" % (self.map_path, self.box_count, self.start_count))


# =====================================================================================
# Extensions (MAPS): glowing materials, fog, ballistic jump pads, small prop helpers.
# =====================================================================================

GRAVITY = 980.0 * 1.15   # world gravity times the character's GravityScale


def launch_velocity(start, target, apex_extra=160.0):
    """Returns ((vx, vy, vz), flight_time) that carries a body from start to target on a ballistic arc.

    start / target are feet positions (x, y, z). The arc peaks apex_extra above the higher of the two.
    """
    dz = target[2] - start[2]
    apex = max(0.0, dz) + apex_extra
    vz = math.sqrt(2.0 * GRAVITY * apex)
    t_up = vz / GRAVITY
    t_down = math.sqrt(2.0 * GRAVITY * max(1.0, apex - dz)) / GRAVITY
    total = t_up + t_down
    return ((target[0] - start[0]) / total, (target[1] - start[1]) / total, vz), total


def _glow_material(self, name, rgb, glow=6.0):
    """A material that emits light: instance of M_IABody (parameters Color and Glow)."""
    if name in self.mats:
        return self.mats[name]
    full = "/Game/Materials/%s" % name
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        mic = unreal.EditorAssetLibrary.load_asset(full)
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mic = tools.create_asset(name, "/Game/Materials", unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
    lib = unreal.MaterialEditingLibrary
    lib.set_material_instance_parent(mic, unreal.EditorAssetLibrary.load_asset("/Game/Characters/M_IABody"))
    lib.set_material_instance_vector_parameter_value(mic, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    lib.set_material_instance_scalar_parameter_value(mic, "Roughness", 0.4)
    lib.set_material_instance_scalar_parameter_value(mic, "Metallic", 0.0)
    lib.set_material_instance_scalar_parameter_value(mic, "Glow", glow)
    lib.update_material_instance(mic)
    unreal.EditorAssetLibrary.save_asset(full)
    self.mats[name] = mic
    return mic


def _fog(self, rgb=None, density=None, falloff=None, start=None, max_opacity=None):
    """Adjusts (or creates) the level's exponential height fog."""
    fog = getattr(self, "fog_actor", None)
    if fog is None:
        for a in self.actor_lib.get_all_level_actors():
            if isinstance(a, unreal.ExponentialHeightFog):
                fog = a
        if fog is None:
            fog = self.spawn(unreal.ExponentialHeightFog, "Fog", (0, 0, 200))
        self.fog_actor = fog
    comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    if rgb is not None:
        for name in ("fog_inscattering_luminance", "fog_inscattering_color"):
            try:
                comp.set_editor_property(name, unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
                break
            except Exception:
                continue
    if density is not None:
        comp.set_editor_property("fog_density", density)
    if falloff is not None:
        comp.set_editor_property("fog_height_falloff", falloff)
    if start is not None:
        comp.set_editor_property("start_distance", start)
    if max_opacity is not None:
        comp.set_editor_property("fog_max_opacity", max_opacity)
    return fog


def _jump_pad(self, label, x, y, z, target, color=(0.0, 0.8, 1.0), apex_extra=160.0):
    """Places an AIAJumpPad at ground point (x, y, z) that lands the player on target=(x, y, z_ground).

    Returns the flight time in seconds and logs the launch data.
    """
    vel, total = launch_velocity((x, y, z), target, apex_extra)
    pad = self.spawn(unreal.IAJumpPad, label, (x, y, z), (0, 0, math.degrees(math.atan2(vel[1], vel[0]))))
    pad.set_editor_property("launch_velocity", unreal.Vector(*vel))
    pad.set_editor_property("pad_color", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    self.pad_count = getattr(self, "pad_count", 0) + 1
    unreal.log("JUMPPAD %s at (%.0f, %.0f, %.0f) -> (%.0f, %.0f, %.0f) v=(%.0f, %.0f, %.0f) t=%.2fs" % (
        (label, x, y, z) + tuple(target) + vel + (total,)))
    return total


def _light_strip(self, label, cx, cy, cz, sx, sy, sz, mat, rgb=None, light_every=0.0, intensity=1500.0,
                 radius=600.0):
    """A glowing bar (no collision), optionally with point lights spaced along its long axis."""
    self.box(label, cx, cy, cz, sx, sy, sz, mat=mat, solid=False)
    if rgb is not None and light_every > 0:
        along_x = sx >= sy
        length = sx if along_x else sy
        n = max(1, int(length // light_every))
        for i in range(n):
            f = ((i + 0.5) / n - 0.5) * length
            self.point_light("%s_L%d" % (label, i), (cx + (f if along_x else 0.0), cy + (0.0 if along_x else f), cz),
                             rgb, intensity, radius)


def _frame(self, label, cx, cy, z_bottom, width, height, thick, depth, yaw, mat, solid=True):
    """A rectangular frame (two posts and a lintel) in the plane given by yaw (door, gate, sign frame)."""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for side in (-1, 1):
        px, py = cx + c * side * (width / 2 - thick / 2), cy + s * side * (width / 2 - thick / 2)
        self.box(label + "_post", px, py, z_bottom + height / 2, thick, depth, height, yaw=yaw, mat=mat, solid=solid)
    self.box(label + "_lintel", cx, cy, z_bottom + height - thick / 2, width, depth, thick, yaw=yaw, mat=mat,
             solid=solid)


def _check_starts(self, min_distance=0.0):
    """Logs every pair of PlayerStarts that can see each other (eye-height line trace against the geometry)."""
    world = self.editor_lib.get_editor_world()
    starts = [a for a in self.actor_lib.get_all_level_actors() if isinstance(a, unreal.PlayerStart)]
    seen = 0
    for i in range(len(starts)):
        for j in range(i + 1, len(starts)):
            a = starts[i].get_actor_location() + unreal.Vector(0, 0, 60)
            b = starts[j].get_actor_location() + unreal.Vector(0, 0, 60)
            hit, _ = self._trace((a.x, a.y, a.z), (b.x, b.y, b.z))
            if not hit:
                seen += 1
                unreal.log("START_LOS %s <-> %s" % (starts[i].get_actor_label(), starts[j].get_actor_label()))
    unreal.log("START_CHECK starts=%d pairs_in_sight=%d" % (len(starts), seen))
    return seen


def _trace(self, a, b):
    """Line trace against the level geometry. Returns (hit, impact_point or None)."""
    world = self.editor_lib.get_editor_world()
    ignore = [x for x in self.actor_lib.get_all_level_actors() if isinstance(x, (unreal.IAJumpPad, unreal.PlayerStart))] \
        if getattr(self, "_ignore", None) is None else self._ignore
    self._ignore = ignore
    res = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(*a), unreal.Vector(*b), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore,
        unreal.DrawDebugTrace.NONE, True)
    if res is None:             # no hit
        return False, None
    t = res.to_tuple()          # (blocking_hit, initial_overlap, time, distance, location, impact_point, ...)
    hit = bool(t[0])
    return hit, ((t[5].x, t[5].y, t[5].z) if hit else None)


def _auto_starts(self, count, x_range, y_range, levels, step=150.0, seed=1, min_sep=600.0, margin=70.0,
                 face=(0.0, 0.0)):
    """Chooses PlayerStart positions automatically: standing room, no start in sight of another, spread over
    the given ground heights (levels). Places them and returns the list. Logs a warning when fewer than count fit."""
    rng = random.Random(seed)
    per_level = {}
    for z in levels:
        cands = []
        x = x_range[0]
        while x <= x_range[1]:
            y = y_range[0]
            while y <= y_range[1]:
                hit, p = self._trace((x, y, z + 40), (x, y, z - 40))
                if hit and p is not None and abs(p[2] - z) < 25:
                    up, _ = self._trace((x, y, z + 5), (x, y, z + 230))
                    walls = any(self._trace((x, y, z + 60), (x + dx * margin, y + dy * margin, z + 60))[0]
                                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if not up and not walls:
                        cands.append((x, y, z))
                y += step
            x += step
        rng.shuffle(cands)
        per_level[z] = cands
    chosen = []
    los_cache = {}

    def blocked(c, o):
        key = (c, o)
        if key not in los_cache:
            los_cache[key] = los_cache[(o, c)] = self._trace((c[0], c[1], c[2] + 170), (o[0], o[1], o[2] + 170))[0]
        return los_cache[key]

    for attempt in range(40):                          # keep the best of several random greedy passes
        pools = {z: list(v) for z, v in per_level.items()}
        for v in pools.values():
            rng.shuffle(v)
        order = []
        while any(pools.values()):                       # round robin over the levels
            for z in levels:
                if pools[z]:
                    order.append(pools[z].pop())
        trial = []
        for c in order:
            if len(trial) >= count:
                break
            if all(math.hypot(c[0] - o[0], c[1] - o[1]) >= min_sep or abs(c[2] - o[2]) >= 200 for o in trial) \
                    and all(blocked(c, o) for o in trial):
                trial.append(c)
        if len(trial) > len(chosen):
            chosen = trial
        if len(chosen) >= count:
            break
    if len(chosen) < count:
        unreal.log_warning("AUTO_STARTS only %d of %d fit" % (len(chosen), count))
    self.starts([(x, y, z, math.degrees(math.atan2(face[1] - y, face[0] - x))) for x, y, z in chosen])
    unreal.log("AUTO_STARTS chose %d: %s" % (len(chosen), chosen))
    return chosen


def _post(self, exposure_bias=None, min_brightness=None, max_brightness=None, bloom=None, saturation=None):
    """An unbound post process volume: exposure bias (EV), eye adaptation range, bloom, saturation."""
    ppv = self.spawn(unreal.PostProcessVolume, "PostProcess", (0, 0, 0))
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    if exposure_bias is not None:
        s.set_editor_property("override_auto_exposure_bias", True)
        s.set_editor_property("auto_exposure_bias", exposure_bias)
    if min_brightness is not None:
        s.set_editor_property("override_auto_exposure_min_brightness", True)
        s.set_editor_property("auto_exposure_min_brightness", min_brightness)
    if max_brightness is not None:
        s.set_editor_property("override_auto_exposure_max_brightness", True)
        s.set_editor_property("auto_exposure_max_brightness", max_brightness)
    if bloom is not None:
        s.set_editor_property("override_bloom_intensity", True)
        s.set_editor_property("bloom_intensity", bloom)
    if saturation is not None:
        s.set_editor_property("override_color_saturation", True)
        s.set_editor_property("color_saturation", unreal.Vector4(saturation, saturation, saturation, 1.0))
    ppv.set_editor_property("settings", s)
    return ppv


def _cone(self, label, cx, cy, z_bottom, z_top, diameter, mat=None, solid=True, yaw=0.0):
    """A cone (base at z_bottom, tip at z_top) from the engine's basic shapes: spires, pines, mountains."""
    if getattr(self, "cone_mesh", None) is None:
        self.cone_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cone.Cone")
    h = z_top - z_bottom
    return self._place(label, self.cone_mesh, (cx, cy, z_bottom + h / 2.0),
                       (diameter / 100.0, diameter / 100.0, h / 100.0), yaw, 0.0, mat, solid)


MapBuilder.cone = _cone
MapBuilder.post = _post
MapBuilder._trace = _trace
MapBuilder.auto_starts = _auto_starts
MapBuilder.check_starts = _check_starts
MapBuilder.glow = _glow_material
MapBuilder.fog = _fog
MapBuilder.jump_pad = _jump_pad
MapBuilder.light_strip = _light_strip
MapBuilder.frame = _frame
