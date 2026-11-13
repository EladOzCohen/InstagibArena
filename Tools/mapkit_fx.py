"""Effect helpers for map scripts (monkey-patch style, like mapkit_b): flames.

    import mapkit, mapkit_fx          # (props.py already imports it, so maps that `import props` have it)
    b.flame("Torch_1", x, y, z, scale=1.0, colour=(1.0, 0.30, 0.05))     # z = where the fire starts (the rim of the bowl)
    b.prop("Drum_1", "barrel_fire", x, y, 0)                              # barrel_fire and fire_pit get a flame automatically

Flame = an AIAFlame actor (Source/InstagibArena/IAFlame.*): three crossed quads with the animated procedural flame material
M_IAFlame, two quads of drifting embers (M_IAEmbers), and a small flickering shadowless point light. The materials come from
Tools/build_fx.py (committed in /Game/Materials/FX). scale 1 = fire about 75 cm tall; scale 0.6 = a candle-sized torch tip.

    flame(label, x, y, z, scale=1.0, colour=None, glow=None, light=None, radius=None, embers=True)
        colour  outer colour of the fire (rgb 0..1); default orange (1.0, 0.30, 0.05). Blue-white: (0.25, 0.5, 1.0)
        glow    emissive multiplier of the flame (default 1.6; the look has low bloom and fixed exposure, so 1-2.5)
        light   candela of the flicker light (default 10 * scale^1.5 + 6); 0 = no light (the map already lights the spot)
        radius  light radius in cm (default 380 * scale^0.5)
        embers  False = no drifting sparks (candles, small torches)
"""

import inspect

import unreal

import mapkit

DEFAULT_COLOUR = (1.0, 0.30, 0.05)

# Catalogue props that burn: name -> (flame height as a fraction of the prop's height, flame scale per prop scale,
#                                     light in candela, radius). The flame stands in the opening of the barrel / pit.
FIRE_PROPS = {
    "barrel_fire": (0.93, 0.80, 7.0, 360.0),
    "fire_pit": (0.62, 1.05, 14.0, 480.0),
}


def _flame(self, label, x, y, z, scale=1.0, colour=None, glow=None, light=None, radius=None, embers=True):
    """Places an AIAFlame with its origin (bottom centre of the fire) at (x, y, z). Returns the actor."""
    actor = self.spawn(unreal.IAFlame, label, (x, y, z))
    col = colour if colour is not None else DEFAULT_COLOUR
    actor.set_editor_property("flame_scale", float(scale))
    actor.set_editor_property("flame_color", unreal.LinearColor(col[0], col[1], col[2], 1.0))
    if glow is not None:
        actor.set_editor_property("glow", float(glow))
    cd = light if light is not None else 10.0 * scale ** 1.5 + 6.0
    actor.set_editor_property("light_candela", float(cd))
    actor.set_editor_property("light_radius", float(radius if radius is not None else 380.0 * scale ** 0.5))
    actor.set_editor_property("embers", bool(embers))
    try:
        actor.set_folder_path("FX")
    except Exception:                            # noqa: BLE001
        pass
    self.flame_count = getattr(self, "flame_count", 0) + 1
    return actor


def _install_prop_flames():
    """Wraps MapBuilder.prop (from props.py) so that burning catalogue props get their flame. Pass flame=False to skip."""
    orig = getattr(mapkit.MapBuilder, "prop", None)
    if orig is None or getattr(orig, "_ia_fx", False):
        return
    sig = inspect.signature(orig)

    def prop(self, label, name, *args, flame=True, **kwargs):
        actor = orig(self, label, name, *args, **kwargs)
        if flame and name in FIRE_PROPS:
            bound = sig.bind(self, label, name, *args, **kwargs)
            bound.apply_defaults()
            a = bound.arguments
            try:
                import props
                height = props.size_of(name, a["scale"])[2]
            except Exception:                    # noqa: BLE001
                height = 80.0 * a["scale"]
            frac, fscale, cd, rad = FIRE_PROPS[name]
            self.flame(label + "_Fire", a["x"], a["y"], a["z"] + height * frac, scale=fscale * a["scale"], light=cd, radius=rad)
        return actor

    prop._ia_fx = True
    prop.__doc__ = orig.__doc__
    mapkit.MapBuilder.prop = prop


mapkit.MapBuilder.flame = _flame
_install_prop_flames()
