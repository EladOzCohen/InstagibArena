"""Small toolkit for building blockout maps from engine shapes with Python.

Used by make_map_temple.py, make_map_dock.py and make_map_skyline.py.
Units are Unreal units (1 uu = 1 cm). Boxes are given by their center and full size.
"""

import math
import os
import sys

import unreal

PROJECT_TOOLS = os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools")
if PROJECT_TOOLS not in sys.path:
    sys.path.insert(0, PROJECT_TOOLS)


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
        comp.set_editor_property("light_color", unreal.Color(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255))
        comp.set_editor_property("attenuation_radius", radius)
        comp.set_editor_property("source_radius", 20.0)
        return light

    def sky(self, sun_pitch=-45.0, sun_yaw=35.0, sun_intensity=None, sun_rgb=None, sky_intensity=2.0):
        sun = self.spawn(unreal.DirectionalLight, "Sun", (0, 0, 2000), (0, sun_pitch, sun_yaw))
        comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if sun_intensity is not None:
            comp.set_editor_property("intensity", sun_intensity)
        if sun_rgb is not None:
            comp.set_editor_property("light_color", unreal.Color(
                int(sun_rgb[0] * 255), int(sun_rgb[1] * 255), int(sun_rgb[2] * 255), 255))
        self.spawn(unreal.SkyAtmosphere, "SkyAtmosphere")
        skylight = self.spawn(unreal.SkyLight, "SkyLight", (0, 0, 1500))
        sky_comp = skylight.get_component_by_class(unreal.SkyLightComponent)
        sky_comp.set_editor_property("real_time_capture", True)
        sky_comp.set_editor_property("intensity", sky_intensity)
        # The sky capture is very blue; a warm tint keeps shadows from turning navy.
        sky_comp.set_editor_property("light_color", unreal.Color(255, 226, 190, 255))

        # A weak second light from the opposite side, without shadows, so that the faces away
        # from the sun are readable instead of black.
        fill = self.spawn(unreal.DirectionalLight, "FillLight", (0, 0, 2100), (0, -28.0, sun_yaw + 180.0))
        fill_comp = fill.get_component_by_class(unreal.DirectionalLightComponent)
        fill_comp.set_editor_property("intensity", 1.6)
        fill_comp.set_editor_property("cast_shadows", False)
        fill_comp.set_editor_property("atmosphere_sun_light", False)
        fill_comp.set_editor_property("forward_shading_priority", 0)
        comp.set_editor_property("forward_shading_priority", 1)
        fill_comp.set_editor_property("light_color", unreal.Color(190, 210, 255, 255))

        self.spawn(unreal.ExponentialHeightFog, "Fog", (0, 0, 200))

    def finish(self, kill_z=None):
        world = self.editor_lib.get_editor_world()
        if kill_z is not None:
            world.get_world_settings().set_editor_property("kill_z", float(kill_z))
        self.level_lib.save_current_level()
        unreal.log("MAKEMAP_DONE %s boxes=%d starts=%d" % (self.map_path, self.box_count, self.start_count))
