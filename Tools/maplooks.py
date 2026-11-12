"""The global light and shading look of Instagib Arena: sun, sky, fog and post process presets for the maps.

Every map picks one of the presets below with one line, from a map script that uses mapkit:

    m.look("day_clear")                       # a preset
    m.look("dusk", sun_yaw=250)               # a preset with the sun turned
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

Units: sun and sky intensity are the engine's unitless lux-like numbers (UE default sun = 10). Exposure is EV100
(needs r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True, set in Config/DefaultEngine.ini).
"""

import unreal

# ---------------------------------------------------------------------------------------------------------
# The presets. Every key can be overridden with keyword arguments of look(): sun_lux, sun_pitch, sun_yaw,
# sun_rgb, sun_angle, sky_intensity, sky_rgb, ground_rgb, fog_rgb, fog_density, fog_falloff, fog_start,
# fog_max_opacity, ev, bloom, saturation, contrast, ssr, ao, atmosphere.
# ---------------------------------------------------------------------------------------------------------
LOOKS = {
    # Clear day: warm sun high in the sky, cool sky light, a thin haze in the distance.
    "day_clear": dict(
        sun_lux=10.0, sun_pitch=-48.0, sun_yaw=35.0, sun_rgb=(1.0, 0.97, 0.91), sun_angle=0.5,
        sky_intensity=3.2, sky_rgb=(0.86, 0.92, 1.0), ground_rgb=(0.22, 0.20, 0.18),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0012, fog_falloff=0.3, fog_start=0.0, fog_max_opacity=0.5,
        ev=1.6, bloom=0.2, saturation=1.0, contrast=1.06, ssr=35.0, ao=0.6),
    # Heavy clouds: soft light, hardly any shadows, cool and grey. The sun is weak and the sky does the lighting.
    "overcast": dict(
        sun_lux=4.0, sun_pitch=-55.0, sun_yaw=20.0, sun_rgb=(0.92, 0.95, 1.0), sun_angle=3.0,
        sky_intensity=3.5, sky_rgb=(0.88, 0.92, 0.98), ground_rgb=(0.20, 0.20, 0.20),
        atmosphere=True,
        fog_rgb=(0.50, 0.54, 0.60), fog_density=0.0020, fog_falloff=0.3, fog_start=400.0, fog_max_opacity=0.55,
        ev=1.3, bloom=0.18, saturation=0.92, contrast=1.05, ssr=25.0, ao=0.6),
    # Low warm sun, long shadows, orange horizon, cool blue shadows.
    "dusk": dict(
        sun_lux=8.0, sun_pitch=-14.0, sun_yaw=250.0, sun_rgb=(1.0, 0.66, 0.38), sun_angle=0.6,
        sky_intensity=6.0, sky_rgb=(0.72, 0.80, 1.0), ground_rgb=(0.20, 0.14, 0.11),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0018, fog_falloff=0.3, fog_start=300.0, fog_max_opacity=0.6,
        ev=0.8, bloom=0.22, saturation=1.02, contrast=1.08, ssr=30.0, ao=0.6),
    # A night in the city: a cool moon, a dark blue sky. The map brings its own coloured accent lights.
    "night_city": dict(
        sun_lux=1.5, sun_pitch=-38.0, sun_yaw=210.0, sun_rgb=(0.86, 0.90, 1.0), sun_angle=0.8,
        sky_intensity=1.2, sky_rgb=(0.86, 0.89, 1.0), ground_rgb=(0.10, 0.09, 0.12),
        atmosphere=True,
        fog_rgb=(0.050, 0.055, 0.085), fog_density=0.0025, fog_falloff=0.25, fog_start=500.0, fog_max_opacity=0.65,
        ev=-0.6, bloom=0.28, saturation=0.7, contrast=1.1, ssr=30.0, ao=0.7),
    # A cave or a forge: no sun, a dull red sky light, red-orange fog. Lit by lava and fire (accent lights).
    "volcanic": dict(
        sun_lux=3.0, sun_pitch=-60.0, sun_yaw=60.0, sun_rgb=(1.0, 0.72, 0.52), sun_angle=1.5,
        sky_intensity=2.2, sky_rgb=(0.95, 0.68, 0.52), ground_rgb=(0.26, 0.14, 0.10),
        atmosphere=True,
        fog_rgb=(0.10, 0.035, 0.018), fog_density=0.0030, fog_falloff=0.2, fog_start=300.0, fog_max_opacity=0.7,
        ev=0.0, bloom=0.25, saturation=1.0, contrast=1.1, ssr=25.0, ao=0.7),
    # Bright, cold, hard light, white ground that bounces a lot of light up.
    "arctic": dict(
        sun_lux=11.0, sun_pitch=-26.0, sun_yaw=60.0, sun_rgb=(0.92, 0.96, 1.0), sun_angle=0.5,
        sky_intensity=3.2, sky_rgb=(0.78, 0.88, 1.0), ground_rgb=(0.55, 0.60, 0.66),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0018, fog_falloff=0.25, fog_start=300.0, fog_max_opacity=0.55,
        ev=1.9, bloom=0.2, saturation=0.95, contrast=1.05, ssr=30.0, ao=0.6),
    # Strong warm sun, sand-coloured bounce, a dry haze.
    "desert": dict(
        sun_lux=11.0, sun_pitch=-40.0, sun_yaw=215.0, sun_rgb=(1.0, 0.88, 0.70), sun_angle=0.5,
        sky_intensity=4.5, sky_rgb=(0.90, 0.92, 1.0), ground_rgb=(0.42, 0.30, 0.18),
        atmosphere=True,
        fog_rgb=None, fog_density=0.0016, fog_falloff=0.3, fog_start=300.0, fog_max_opacity=0.5,
        ev=1.8, bloom=0.2, saturation=1.0, contrast=1.06, ssr=30.0, ao=0.6),
    # A hall with a roof: no sun, a weak neutral sky light as ambient and the map's own lamps (accent_light).
    "indoor": dict(
        sun_lux=1.0, sun_pitch=-75.0, sun_yaw=0.0, sun_rgb=(1.0, 1.0, 1.0), sun_angle=1.0,
        sky_intensity=3.0, sky_rgb=(0.80, 0.84, 0.92), ground_rgb=(0.14, 0.14, 0.15),
        atmosphere=True,
        fog_rgb=(0.04, 0.045, 0.055), fog_density=0.0015, fog_falloff=0.3, fog_start=500.0, fog_max_opacity=0.5,
        ev=-0.2, bloom=0.2, saturation=1.0, contrast=1.08, ssr=25.0, ao=0.7),
}

LABELS = ("Sun", "SkyAtmosphere", "SkyLight", "FillLight", "Fog", "PostProcess")


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
    """Removes lights, atmosphere, fog and post process volumes that an earlier sky()/look() call placed."""
    kinds = (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.ExponentialHeightFog,
             unreal.PostProcessVolume)
    for actor in builder.actor_lib.get_all_level_actors():
        if isinstance(actor, kinds):
            try:
                builder.actor_lib.destroy_actor(actor)
            except Exception:                      # noqa: BLE001
                pass
    builder.fog_actor = None


def available():
    return sorted(LOOKS.keys())


def apply_look(builder, name="day_clear", **over):
    """Spawns the sun, sky atmosphere, sky light, fog and one unbound post process volume of a look.

    builder: a mapkit.MapBuilder (anything with spawn() and actor_lib). Returns the resolved settings dict.
    Keyword overrides use the keys of the presets (sun_yaw=..., ev=..., fog_density=...).
    """
    if name not in LOOKS:
        raise ValueError("unknown look %r, choose one of %s" % (name, ", ".join(available())))
    cfg = dict(LOOKS[name])
    cfg.update(over)
    _clear_old(builder)
    movable = unreal.ComponentMobility.MOVABLE

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

    # --- atmosphere: the visible sky and its aerial perspective (distance haze that matches the sky)
    if cfg["atmosphere"]:
        builder.spawn(unreal.SkyAtmosphere, "SkyAtmosphere")

    # --- sky light: THE ambient light. Movable so that it works without baked lighting. The lower hemisphere
    # returns a little ground-coloured light, which stands in for the bounce light that Lumen would give us.
    sky = builder.spawn(unreal.SkyLight, "SkyLight", (0, 0, 1500))
    kc = sky.get_component_by_class(unreal.SkyLightComponent)
    _set(kc, "mobility", movable)
    _set(kc, "real_time_capture", bool(cfg["atmosphere"]))
    _set(kc, "intensity", float(cfg["sky_intensity"]))
    _set(kc, "light_color", _color8(cfg["sky_rgb"]))
    _set(kc, "lower_hemisphere_is_black", False)
    _set(kc, "lower_hemisphere_color", _lin(cfg["ground_rgb"]))
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
    ev = float(cfg["ev"])

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

    unreal.log("LOOK applied %s (sun %.1f lux, sky %.2f, EV %.1f, fog %.4f)" % (
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
