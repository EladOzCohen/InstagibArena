"""Small colour tweaks applied AFTER MapBuilder.look() (the NATURE pass). They do not touch the look preset or the sky choice:
they only warm / cool what is already placed, so a new sky (HDRI) keeps working.

    import looktweak_n as lt
    m.look(...)                                       # as before
    lt.tint_sky(m, color=(1.0, 0.92, 0.80))           # multiply the sky light colour (removes a cyan cast in the shade)
    lt.tint_ground(m, (0.5, 0.38, 0.24))              # colour of the light bounced up from the ground
    lt.grade(m, tint=(1.0, 0.97, 0.92), saturation=0.95)
"""

import unreal


def _color8(rgb):
    return unreal.Color(r=int(max(0.0, min(1.0, rgb[0])) * 255 + 0.5), g=int(max(0.0, min(1.0, rgb[1])) * 255 + 0.5),
                        b=int(max(0.0, min(1.0, rgb[2])) * 255 + 0.5), a=255)


def _sky_comp(m):
    for a in m.actor_lib.get_all_level_actors():
        if isinstance(a, unreal.SkyLight):
            return a.get_component_by_class(unreal.SkyLightComponent)
    return None


def tint_sky(m, color=None, intensity_mul=None):
    """Multiplies the sky light's colour by `color` (0..1 per channel) and its intensity by intensity_mul."""
    c = _sky_comp(m)
    if c is None:
        unreal.log_warning("LOOKTWEAK no sky light")
        return
    if color is not None:
        old = c.get_editor_property("light_color")
        c.set_editor_property("light_color", unreal.Color(r=int(old.r * color[0]), g=int(old.g * color[1]), b=int(old.b * color[2]), a=255))
    if intensity_mul is not None:
        c.set_editor_property("intensity", float(c.get_editor_property("intensity")) * intensity_mul)


def tint_ground(m, rgb):
    c = _sky_comp(m)
    if c is not None:
        c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))


def tint_sun(m, rgb=None, intensity_mul=None):
    for a in m.actor_lib.get_all_level_actors():
        if isinstance(a, unreal.DirectionalLight):
            c = a.get_component_by_class(unreal.DirectionalLightComponent)
            if rgb is not None:
                c.set_editor_property("light_color", _color8(rgb))
            if intensity_mul is not None:
                c.set_editor_property("intensity", float(c.get_editor_property("intensity")) * intensity_mul)


def grade(m, tint=None, saturation=None, contrast=None):
    """Post process colour grade on the map's volume: scene colour tint, saturation, contrast."""
    ppv = None
    for a in m.actor_lib.get_all_level_actors():
        if isinstance(a, unreal.PostProcessVolume):
            ppv = a
    if ppv is None:
        return
    s = ppv.get_editor_property("settings")
    try:
        if tint is not None:
            s.set_editor_property("override_scene_color_tint", True)
            s.set_editor_property("scene_color_tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
        if saturation is not None:
            s.set_editor_property("override_color_saturation", True)
            s.set_editor_property("color_saturation", unreal.Vector4(saturation, saturation, saturation, 1.0))
        if contrast is not None:
            s.set_editor_property("override_color_contrast", True)
            s.set_editor_property("color_contrast", unreal.Vector4(contrast, contrast, contrast, 1.0))
    except Exception as exc:                                     # noqa: BLE001
        unreal.log_warning("LOOKTWEAK grade: %s" % exc)
    ppv.set_editor_property("settings", s)
