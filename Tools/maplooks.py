"""The global light and shading look of Instagib Arena: sun, sky, fog and post process presets for the maps.

Every map picks one of the presets below with one line, from a map script that uses mapkit:

    m.look("day_clear")                       # a preset
    m.look("dusk", sun_yaw=250)               # a preset with the sun (and the sky with it) turned to azimuth 250 - 180
    m.look("desert", sky_hdri=None)           # the old look: engine SkyAtmosphere instead of a photographic sky
    m.accent_light("Lamp_1", (x, y, z), (1.0, 0.5, 0.2), candela=40)   # a small coloured light

Why this file exists (measured on the first screenshots, see docs/DEVELOPMENT.md section 13):
  * The project has NO global illumination and NO Lumen (r.DynamicGlobalIlluminationMethod=0), reflections are
    screen space only. The sky light was the only ambient light, and its colour/intensity was set per map.
  * Auto exposure re-normalised every map and pumped when a bright emissive wall filled the screen, so a sun of
    0.9 and a sun of 6.0 looked equally bright and everything was either blown out or black.
  * Default fog density 0.02 (a blue wall of haze), default bloom 0.675, vignette 0.4, lens flare 1.0.
  * Emissive "light strips" with Glow 6 on whole walls, and a fill light of a different colour from the opposite side.
Everything here is therefore physically scaled: a clear-day sun is 10 lux, exposure is FIXED per look (no pumping),
the ambient comes from one sky light, bloom is low and fog is thin.

THE SKY (docs/DEVELOPMENT.md section 18). Every look except "indoor" shows a photographic sky: a CC0 panorama from Poly Haven
(Tools/fetch_hdri.py, Tools/import_skies.py) as a cube map /Game/Sky/T_Sky_<look>, drawn by a huge unlit dome (`SkyDome`, material
M_IASky, one instance per map: /Game/Sky/MI_Sky_<map>). The same cube map lights the world (sky light "specified cubemap"), the
fog takes its colour from the horizon of the panorama, and THE SUN IS ALIGNED WITH THE PICTURE: the directional light shines from
where the sun is in the panorama (elevation from the picture, azimuth = picture azimuth + sky_yaw). There is no SkyAtmosphere any more
(look(..., sky_hdri=None) brings the old atmosphere back).

Units: sun and sky intensity are the engine's unitless lux-like numbers (UE default sun = 10). Exposure is EV100
(needs r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True, set in Config/DefaultEngine.ini).
Sky brightness is the brightness the sky has ON SCREEN (linear, mean of the upper hemisphere; 0.45 = a normal day sky), independent
of `ev`: the dome multiplies by 1.2 * 2^ev, so a map that changes `ev` to light its floor does not change its sky.
"""

import unreal

# ---------------------------------------------------------------------------------------------------------
# The presets. Every key can be overridden with keyword arguments of look(): sun_lux, sun_pitch, sun_yaw,
# sun_rgb, sun_angle, sky_intensity, sky_rgb, ground_rgb, fog_rgb, fog_density, fog_falloff, fog_start,
# fog_max_opacity, ev, bloom, saturation, contrast, ssr, ao, atmosphere.
# Sky keys: hdri (a name of HDRI below or None = engine atmosphere; override name: sky_hdri), sky_yaw, sky_brightness, sky_tint,
# sky_rgb_hdri (colour of the sky light with a panorama: the panorama has the colour already, so about white), ambient_gain
# (multiplies sky_intensity with a panorama: calibrates the cube map against the old atmosphere capture),
# sun_override (True: keep sun_pitch / sun_yaw although the panorama has a sun elsewhere; the visible sun then does not match the shadows).
# With a panorama, `sun_yaw=` (old map scripts) is understood as "the sun is at azimuth sun_yaw + 180" and turns the sky to put the
# picture's sun there; `sun_pitch=` is ignored (the elevation comes from the picture) unless sun_override=True.
# ---------------------------------------------------------------------------------------------------------
LOOKS = {
    # Clear day: warm sun high in the sky, cool sky light, a thin haze in the distance.
    "day_clear": dict(
        sun_lux=10.0, sun_pitch=-48.0, sun_yaw=35.0, sun_rgb=(1.0, 0.97, 0.91), sun_angle=0.5,
        sky_intensity=3.2, sky_rgb=(0.86, 0.92, 1.0), ground_rgb=(0.22, 0.20, 0.18),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0012, fog_falloff=0.3, fog_start=0.0, fog_max_opacity=0.5,
        ev=1.6, bloom=0.2, saturation=1.0, contrast=1.06, ssr=35.0, ao=0.6,
        hdri="day_clear", sky_yaw=0.0, sky_brightness=0.45, sky_tint=(1.0, 1.0, 1.0), sky_rgb_hdri=(1.0, 1.0, 1.0),
        ambient_gain=1.0, sun_override=False),
    # Heavy clouds: soft light, hardly any shadows, cool and grey. The sun is weak and the sky does the lighting.
    "overcast": dict(
        sun_lux=4.0, sun_pitch=-55.0, sun_yaw=20.0, sun_rgb=(0.92, 0.95, 1.0), sun_angle=3.0,
        sky_intensity=3.5, sky_rgb=(0.88, 0.92, 0.98), ground_rgb=(0.20, 0.20, 0.20),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0020, fog_falloff=0.3, fog_start=400.0, fog_max_opacity=0.55,
        ev=1.3, bloom=0.18, saturation=0.92, contrast=1.05, ssr=25.0, ao=0.6,
        hdri="overcast", sky_yaw=0.0, sky_brightness=0.55, sky_tint=(1.0, 1.0, 1.0), sky_rgb_hdri=(1.0, 1.0, 1.0),
        ambient_gain=1.0, sun_override=False),
    # Low warm sun, long shadows, orange horizon, cool blue shadows.
    "dusk": dict(
        sun_lux=8.0, sun_pitch=-14.0, sun_yaw=250.0, sun_rgb=(1.0, 0.66, 0.38), sun_angle=0.6,
        sky_intensity=6.0, sky_rgb=(0.72, 0.80, 1.0), ground_rgb=(0.20, 0.14, 0.11),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0018, fog_falloff=0.3, fog_start=300.0, fog_max_opacity=0.6,
        ev=0.8, bloom=0.22, saturation=1.02, contrast=1.08, ssr=30.0, ao=0.6,
        hdri="dusk", sky_yaw=0.0, sky_brightness=0.5, sky_tint=(1.0, 1.0, 1.0), sky_rgb_hdri=(1.0, 1.0, 1.0),
        ambient_gain=1.0, sun_override=False),
    # A night in the city: a cool moon, a dark blue sky. The map brings its own coloured accent lights.
    "night_city": dict(
        sun_lux=1.5, sun_pitch=-38.0, sun_yaw=210.0, sun_rgb=(0.86, 0.90, 1.0), sun_angle=0.8,
        sky_intensity=1.2, sky_rgb=(0.86, 0.89, 1.0), ground_rgb=(0.10, 0.09, 0.12),
        atmosphere=True,
        fog_rgb=(0.050, 0.055, 0.085), fog_density=0.0025, fog_falloff=0.25, fog_start=500.0, fog_max_opacity=0.65,
        ev=-0.6, bloom=0.28, saturation=0.7, contrast=1.1, ssr=30.0, ao=0.7,
        hdri="night_city", sky_yaw=0.0, sky_brightness=0.06, sky_tint=(0.75, 0.85, 1.0), sky_rgb_hdri=(0.86, 0.89, 1.0),
        ambient_gain=1.0, sun_override=False),
    # A cave or a forge: no sun, a dull red sky light, red-orange fog. Lit by lava and fire (accent lights).
    # The smoky sky hides the sun, so the old sun direction stays (sun_override).
    "volcanic": dict(
        sun_lux=3.0, sun_pitch=-60.0, sun_yaw=60.0, sun_rgb=(1.0, 0.72, 0.52), sun_angle=1.5,
        sky_intensity=2.2, sky_rgb=(0.95, 0.68, 0.52), ground_rgb=(0.26, 0.14, 0.10),
        atmosphere=True,
        fog_rgb=(0.10, 0.035, 0.018), fog_density=0.0030, fog_falloff=0.2, fog_start=300.0, fog_max_opacity=0.7,
        ev=0.0, bloom=0.25, saturation=1.0, contrast=1.1, ssr=25.0, ao=0.7,
        hdri="volcanic", sky_yaw=0.0, sky_brightness=0.22, sky_tint=(1.0, 0.36, 0.17), sky_rgb_hdri=(0.95, 0.68, 0.52),
        ambient_gain=1.0, sun_override=True),
    # Bright, cold, hard light, white ground that bounces a lot of light up.
    "arctic": dict(
        sun_lux=11.0, sun_pitch=-26.0, sun_yaw=60.0, sun_rgb=(0.92, 0.96, 1.0), sun_angle=0.5,
        sky_intensity=3.2, sky_rgb=(0.78, 0.88, 1.0), ground_rgb=(0.55, 0.60, 0.66),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0018, fog_falloff=0.25, fog_start=300.0, fog_max_opacity=0.55,
        ev=1.9, bloom=0.2, saturation=0.95, contrast=1.05, ssr=30.0, ao=0.6,
        hdri="arctic", sky_yaw=0.0, sky_brightness=0.45, sky_tint=(1.0, 1.0, 1.0), sky_rgb_hdri=(1.0, 1.0, 1.0),
        ambient_gain=1.0, sun_override=False),
    # Strong warm sun, sand-coloured bounce, a dry haze.
    "desert": dict(
        sun_lux=11.0, sun_pitch=-40.0, sun_yaw=215.0, sun_rgb=(1.0, 0.88, 0.70), sun_angle=0.5,
        sky_intensity=4.5, sky_rgb=(0.90, 0.92, 1.0), ground_rgb=(0.42, 0.30, 0.18),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0016, fog_falloff=0.3, fog_start=300.0, fog_max_opacity=0.5,
        ev=1.8, bloom=0.2, saturation=1.0, contrast=1.06, ssr=30.0, ao=0.6,
        hdri="desert", sky_yaw=0.0, sky_brightness=0.5, sky_tint=(1.0, 0.97, 0.92), sky_rgb_hdri=(1.0, 1.0, 1.0),
        ambient_gain=1.0, sun_override=False),
    # A hall with a roof: no sun, a weak neutral sky light as ambient and the map's own lamps (accent_light). No sky to see.
    "indoor": dict(
        sun_lux=1.0, sun_pitch=-75.0, sun_yaw=0.0, sun_rgb=(1.0, 1.0, 1.0), sun_angle=1.0,
        sky_intensity=3.0, sky_rgb=(0.80, 0.84, 0.92), ground_rgb=(0.14, 0.14, 0.15),
        atmosphere=True,
        fog_rgb=(0.04, 0.045, 0.055), fog_density=0.0015, fog_falloff=0.3, fog_start=500.0, fog_max_opacity=0.5,
        ev=-0.2, bloom=0.2, saturation=1.0, contrast=1.08, ssr=25.0, ao=0.7,
        hdri=None, sky_yaw=0.0, sky_brightness=0.45, sky_tint=(1.0, 1.0, 1.0), sky_rgb_hdri=(1.0, 1.0, 1.0),
        ambient_gain=1.0, sun_override=False),
}

# Measurements of the panoramas (printed by Tools/import_skies.py as SKIES_TABLE; azimuth/elevation of the sun in the picture,
# azimuth 0 = the +x axis of the unrotated sky, growing towards +y; colours are linear, relative to the mean brightness of the upper hemisphere).
HDRI = {
    "day_clear": dict(slug="kloofendal_48d_partly_cloudy_puresky", sun_az=34.26, sun_el=47.89, horizon=(1.139, 1.272, 1.628)),
    "overcast": dict(slug="kloofendal_overcast_puresky", sun_az=29.68, sun_el=22.82, horizon=(0.666, 0.712, 0.805)),
    "dusk": dict(slug="evening_road_01_puresky", sun_az=35.59, sun_el=12.10, horizon=(1.092, 1.216, 1.193)),
    "night_city": dict(slug="kloppenheim_07_puresky", sun_az=36.04, sun_el=38.46, horizon=(1.046, 1.087, 1.170)),
    "volcanic": dict(slug="scythian_tombs_puresky", sun_az=35.64, sun_el=13.18, horizon=(1.016, 0.968, 0.889)),
    "arctic": dict(slug="syferfontein_18d_clear_puresky", sun_az=35.87, sun_el=18.37, horizon=(1.649, 2.108, 2.499)),
    "desert": dict(slug="kloofendal_43d_clear_puresky", sun_az=36.18, sun_el=42.93, horizon=(1.500, 1.773, 2.179)),
}

SKY_DIR = "/Game/Sky"
DOME_MESH = SKY_DIR + "/SM_SkyDome"
DOME_MATERIAL = SKY_DIR + "/M_IASky"
DOME_RADIUS = 120000.0         # uu. The maps are at most about 12000 wide; the dome only has to hold them all (the picture is
#                                drawn by view direction, not by position, so the size does not change how the sky looks).

LABELS = ("Sun", "SkyAtmosphere", "SkyLight", "FillLight", "Fog", "PostProcess", "SkyDome")


def _color8(rgb):
    return unreal.Color(r=int(max(0.0, min(1.0, rgb[0])) * 255 + 0.5), g=int(max(0.0, min(1.0, rgb[1])) * 255 + 0.5),
                        b=int(max(0.0, min(1.0, rgb[2])) * 255 + 0.5), a=255)


def _lin(rgb):
    return unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)


def _set(obj, name, value):
    """set_editor_property that logs instead of stopping the script when a property does not exist in this engine version."""
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception as exc:                       # noqa: BLE001
        unreal.log_warning("LOOK property %s not set: %s" % (name, exc))
        return False


def _clear_old(builder):
    """Removes lights, atmosphere, fog, post process volumes and the sky dome that an earlier sky()/look() call placed."""
    kinds = (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.ExponentialHeightFog,
             unreal.PostProcessVolume)
    for actor in builder.actor_lib.get_all_level_actors():
        old_dome = isinstance(actor, unreal.StaticMeshActor) and actor.get_actor_label() == "SkyDome"
        if isinstance(actor, kinds) or old_dome:
            try:
                builder.actor_lib.destroy_actor(actor)
            except Exception:                      # noqa: BLE001
                pass
    builder.fog_actor = None


def available():
    return sorted(LOOKS.keys())


def hdris():
    return sorted(HDRI.keys())


def _level_name():
    try:
        return unreal.EditorLevelLibrary.get_editor_world().get_name()
    except Exception:                              # noqa: BLE001
        return "Level"


def _sky_instance(level, hdri, yaw, brightness, tint):
    """The material instance /Game/Sky/MI_Sky_<level> (parent M_IASky) with the cube map and the parameters of this map."""
    eal = unreal.EditorAssetLibrary
    mlib = unreal.MaterialEditingLibrary
    path = "%s/MI_Sky_%s" % (SKY_DIR, level)
    if eal.does_asset_exist(path):
        mic = eal.load_asset(path)
    else:
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MI_Sky_" + level, SKY_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mlib.set_material_instance_parent(mic, eal.load_asset(DOME_MATERIAL))
    mlib.set_material_instance_texture_parameter_value(mic, "Cube", eal.load_asset("%s/T_Sky_%s" % (SKY_DIR, hdri)))
    mlib.set_material_instance_scalar_parameter_value(mic, "Rotation", float(yaw))
    mlib.set_material_instance_scalar_parameter_value(mic, "Brightness", float(brightness))
    mlib.set_material_instance_vector_parameter_value(mic, "Tint", _lin(tint))
    mlib.update_material_instance(mic)
    eal.save_asset(path)
    return mic


def _spawn_dome(builder, hdri, yaw, brightness, tint):
    """The sky: one huge sphere around the map with the unlit sky material. No shadows, no collision (not walkable, shots
    and bots pass through), no decals, no lighting contribution."""
    mic = _sky_instance(_level_name(), hdri, yaw, brightness, tint)
    mesh = unreal.EditorAssetLibrary.load_asset(DOME_MESH)
    radius = mesh.get_bounding_box().max.x                       # the copied engine sphere (about 50 uu)
    scale = DOME_RADIUS / max(1.0, radius)
    dome = builder.spawn(unreal.StaticMeshActor, "SkyDome", (0, 0, 0))
    dome.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    comp = dome.get_component_by_class(unreal.StaticMeshComponent)
    _set(comp, "static_mesh", mesh)
    comp.set_material(0, mic)
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception as exc:                       # noqa: BLE001
        unreal.log_warning("LOOK dome collision: %s" % exc)
    for prop, value in (("cast_shadow", False), ("cast_dynamic_shadow", False), ("cast_static_shadow", False),
                        ("cast_contact_shadow", False), ("cast_volumetric_translucent_shadow", False),
                        ("affect_dynamic_indirect_lighting", False), ("affect_distance_field_lighting", False),
                        ("receives_decals", False), ("use_as_occluder", False), ("generate_overlap_events", False),
                        ("visible_in_ray_tracing", False), ("can_ever_affect_navigation", False)):
        _set(comp, prop, value)
    return dome


def _norm_angle(a):
    return (a + 180.0) % 360.0 - 180.0


def apply_look(builder, name="day_clear", **over):
    """Spawns the sun, sky (dome or atmosphere), sky light, fog and one unbound post process volume of a look.

    builder: a mapkit.MapBuilder (anything with spawn() and actor_lib). Returns the resolved settings dict.
    Keyword overrides use the keys of the presets (sun_yaw=..., ev=..., fog_density=...) plus
      sky_hdri=None | "<name>"   the panorama (None: the engine's SkyAtmosphere as before; default: the look's own),
      sky_yaw=<degrees>          turns the sky (sun included),
      sky_brightness=<linear>    brightness of the sky on screen (about 0.45 for a day sky),
      sun_override=True          keep sun_pitch / sun_yaw of the look or the overrides; the sun in the picture then does not match.
    """
    if name not in LOOKS:
        raise ValueError("unknown look %r, choose one of %s" % (name, ", ".join(available())))
    cfg = dict(LOOKS[name])
    over = dict(over)
    if "sky_hdri" in over:
        cfg["hdri"] = over.pop("sky_hdri")
        if isinstance(cfg["hdri"], str) and cfg["hdri"].lower() in ("", "none"):      # from an environment variable
            cfg["hdri"] = None
    if cfg["hdri"] is not None and cfg["hdri"] not in HDRI:
        raise ValueError("unknown sky %r, choose one of %s" % (cfg["hdri"], ", ".join(hdris())))
    hd = HDRI.get(cfg["hdri"]) if cfg["hdri"] else None
    explicit = set(over.keys())
    cfg.update(over)
    ev = float(cfg["ev"])
    movable = unreal.ComponentMobility.MOVABLE
    _clear_old(builder)

    if hd is not None:
        if "atmosphere" not in explicit:
            cfg["atmosphere"] = False                  # the picture replaces the atmosphere
        sky_yaw = float(cfg["sky_yaw"])
        if "sky_yaw" not in explicit and "sun_yaw" in explicit and not cfg["sun_override"]:
            sky_yaw = _norm_angle(float(cfg["sun_yaw"]) + 180.0 - hd["sun_az"])      # old scripts: put the sun where they wanted it
        cfg["sky_yaw"] = sky_yaw
        if not cfg["sun_override"]:
            cfg["sun_yaw"] = _norm_angle(hd["sun_az"] + sky_yaw + 180.0)             # the light travels away from the picture's sun
            cfg["sun_pitch"] = -hd["sun_el"]
        if "sky_rgb" not in explicit:
            cfg["sky_rgb"] = cfg["sky_rgb_hdri"]
        # on-screen brightness -> scene value of the dome (fixed exposure: scale = 1 / (1.2 * 2^EV))
        scene = float(cfg["sky_brightness"]) * 1.2 * (2.0 ** ev)
        cfg["sky_intensity"] = float(cfg["sky_intensity"]) * float(cfg["ambient_gain"])
        if cfg["fog_rgb"] is None:
            # the fog is the colour of the horizon of the picture (a little less saturated, a little darker)
            h = hd["horizon"]
            grey = 0.2126 * h[0] + 0.7152 * h[1] + 0.0722 * h[2]
            k = scene * 0.9
            cfg["fog_rgb"] = tuple(max(0.0, (grey + 0.6 * (c - grey)) * k) for c in h)

    # --- sun: crisp shadows (small source angle), real-time shadow maps, the one directional light of the map
    sun = builder.spawn(unreal.DirectionalLight, "Sun", (0, 0, 2000), (0, cfg["sun_pitch"], cfg["sun_yaw"]))
    sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    _set(sc, "mobility", movable)
    _set(sc, "intensity", float(cfg["sun_lux"]))
    _set(sc, "light_color", _color8(cfg["sun_rgb"]))
    _set(sc, "light_source_angle", float(cfg["sun_angle"]))
    _set(sc, "cast_shadows", cfg["sun_lux"] > 0.0)
    _set(sc, "atmosphere_sun_light", bool(cfg["atmosphere"]) and cfg["sun_lux"] > 0.0)
    _set(sc, "specular_scale", 0.6)               # the sun's highlight is the main source of a "plastic" shine

    # --- sky: the dome with the photographic panorama, or (sky_hdri=None) the atmosphere with its aerial perspective
    if hd is not None:
        _spawn_dome(builder, cfg["hdri"], cfg["sky_yaw"], scene, cfg["sky_tint"])
    if cfg["atmosphere"]:
        builder.spawn(unreal.SkyAtmosphere, "SkyAtmosphere")

    # --- sky light: THE ambient light. Movable so that it works without baked lighting. The lower hemisphere
    # returns a little ground-coloured light, which stands in for the bounce light that Lumen would give us.
    sky = builder.spawn(unreal.SkyLight, "SkyLight", (0, 0, 1500))
    kc = sky.get_component_by_class(unreal.SkyLightComponent)
    _set(kc, "mobility", movable)
    _set(kc, "intensity", float(cfg["sky_intensity"]))
    _set(kc, "light_color", _color8(cfg["sky_rgb"]))
    _set(kc, "lower_hemisphere_is_black", False)
    _set(kc, "lower_hemisphere_color", _lin(cfg["ground_rgb"]))
    if hd is not None:
        # the same cube map as the dome: ambient light and sky agree
        _set(kc, "real_time_capture", False)
        _set(kc, "source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
        _set(kc, "cubemap", unreal.EditorAssetLibrary.load_asset("%s/T_Sky_%s" % (SKY_DIR, cfg["hdri"])))
        _set(kc, "source_cubemap_angle", float(cfg["sky_yaw"]))
    else:
        _set(kc, "real_time_capture", bool(cfg["atmosphere"]))
        if not cfg["atmosphere"]:
            # No sky to capture: the light comes from a flat colour instead of a capture of the map.
            _set(kc, "source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)

    # --- fog: thin, with the inscattering taken from the atmosphere unless the look gives a colour
    fog = builder.spawn(unreal.ExponentialHeightFog, "Fog", (0, 0, 200))
    builder.fog_actor = fog
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    _set(fc, "fog_density", float(cfg["fog_density"]))
    _set(fc, "fog_height_falloff", float(cfg["fog_falloff"]))
    _set(fc, "start_distance", float(cfg["fog_start"]))
    _set(fc, "fog_max_opacity", float(cfg["fog_max_opacity"]))
    if cfg["fog_rgb"] is not None:
        _set(fc, "fog_inscattering_luminance", _lin(cfg["fog_rgb"]))

    # --- post process: fixed exposure (no pumping), low bloom, no vignette / lens flare, a little contrast
    ppv = builder.spawn(unreal.PostProcessVolume, "PostProcess", (0, 0, 0))
    _set(ppv, "unbound", True)
    s = ppv.get_editor_property("settings")

    def over_(prop, value):
        s.set_editor_property("override_" + prop, True)
        s.set_editor_property(prop, value)

    over_("auto_exposure_min_brightness", ev)
    over_("auto_exposure_max_brightness", ev)
    over_("auto_exposure_bias", 0.0)
    over_("auto_exposure_speed_up", 20.0)
    over_("auto_exposure_speed_down", 20.0)
    over_("bloom_intensity", float(cfg["bloom"]))
    over_("vignette_intensity", 0.0)
    over_("lens_flare_intensity", 0.0)
    over_("scene_fringe_intensity", 0.0)
    over_("ambient_occlusion_intensity", float(cfg["ao"]))
    over_("screen_space_reflection_intensity", float(cfg["ssr"]))
    over_("screen_space_reflection_max_roughness", 0.5)
    sat, con = float(cfg["saturation"]), float(cfg["contrast"])
    over_("color_saturation", unreal.Vector4(sat, sat, sat, 1.0))
    over_("color_contrast", unreal.Vector4(con, con, con, 1.0))
    ppv.set_editor_property("settings", s)

    if hd is not None:
        unreal.log("LOOK applied %s with sky %s (yaw %.0f, brightness %.2f; sun %.1f lux from az %.0f el %.0f%s; sky light %.2f; EV %.1f; fog %.4f)" % (
            name, cfg["hdri"], cfg["sky_yaw"], cfg["sky_brightness"], cfg["sun_lux"], _norm_angle(cfg["sun_yaw"] + 180.0),
            -cfg["sun_pitch"], " OVERRIDDEN" if cfg["sun_override"] else "", cfg["sky_intensity"], ev, cfg["fog_density"]))
    else:
        unreal.log("LOOK applied %s (atmosphere; sun %.1f lux, sky %.2f, EV %.1f, fog %.4f)" % (
            name, cfg["sun_lux"], cfg["sky_intensity"], ev, cfg["fog_density"]))
    return cfg


def accent_light(builder, label, loc, rgb, candela=30.0, radius=450.0, source_radius=8.0, shadows=False):
    """A small, physically sized coloured light (a lamp, a screen, a vent): candela instead of "intensity 1500".

    30 cd at 3 m is about 3 lux, a quarter of what the sun gives a surface; 100 cd is a bright lamp. The radius is
    short on purpose. Specular is reduced so that the light does not draw wet-looking streaks on the floor.
    """
    light = builder.spawn(unreal.PointLight, label, loc)
    comp = light.get_component_by_class(unreal.PointLightComponent)
    _set(comp, "mobility", unreal.ComponentMobility.MOVABLE)
    _set(comp, "intensity_units", unreal.LightUnits.CANDELAS)
    _set(comp, "intensity", float(candela))
    _set(comp, "light_color", _color8(rgb))
    _set(comp, "attenuation_radius", float(radius))
    _set(comp, "source_radius", float(source_radius))
    _set(comp, "use_inverse_squared_falloff", True)
    _set(comp, "cast_shadows", bool(shadows))
    _set(comp, "specular_scale", 0.4)
    return light
