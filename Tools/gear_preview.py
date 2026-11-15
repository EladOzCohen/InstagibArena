"""Renders the gear of the characters with the software renderer (no engine): python -I Tools/gear_preview.py 0 3 5
Writes <AssetCache>/char_probe/g<idx>_<name>.png (front, side, back, 3/4) and prints the triangle count per character."""

import os
import sys

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import gear_body as gb  # noqa: E402
import gear_roster as gr  # noqa: E402
import mesh_char as mc  # noqa: E402
import preview_char as pv  # noqa: E402


def palette(look):
    """Approximate in-game colours of a roster entry for the preview."""
    def tone(c, k=1.0):
        return tuple(min(1.0, max(0.0, x * k)) for x in c[:3])
    body, accent = look["body"], look["accent"]
    return {
        mc.R_PLATE: tone(body, 1.0), mc.R_CLOTH: tone(body, 0.55), mc.R_ACCENT: tone(accent, 0.9), mc.R_TEAM: (0.85, 0.08, 0.08),
        mc.R_TRIM: (0.05, 0.055, 0.065), mc.R_GLOW: tone(accent, 1.0), mc.R_LIGHT: (0.8, 0.8, 0.76),
    }


def main(argv):
    idxs = [int(a) for a in argv] or list(range(15))
    for i in idxs:
        look = gr.LOOKS[i]
        B = gb.body(look["quinn"])
        kit = gr.build(i)
        pal = palette(look)
        pal.update(look.get("preview_roles", {}))
        # brighten very dark bodies for the preview so that the shapes can be read
        pieces = [g for g in kit.parts.values()]
        out = os.path.join(pv.PROBE, "g%02d_%s.png" % (i, look["name"]))
        pv.sheet(pieces, pal, out, quinn=look["quinn"], bodypal=(0.55, 0.57, 0.62))
        bad = sum(g.check() for g in pieces)
        print("%2d %-10s tris=%5d bones=%s bad=%d -> %s" % (i, look["name"], kit.tri_count(), ",".join(sorted(kit.parts)), bad, out))


if __name__ == "__main__":
    main(sys.argv[1:])
