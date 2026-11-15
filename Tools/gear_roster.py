"""The character roster as the gear tools see it: parsed from Source/InstagibArena/IACharacterRoster.h (single source of truth for names,
body type and colours) plus the table of gear builders. build(i) returns the gear_parts.Kit of character i."""

import os
import re
import sys

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import gear_body as gb  # noqa: E402

HEADER = os.path.join(os.path.dirname(_TOOLS), "Source", "InstagibArena", "IACharacterRoster.h")


def _floats(text):
    return tuple(float(x.strip().rstrip("f")) for x in text.split(","))


def parse():
    src = open(HEADER, encoding="utf-8").read()
    pat = re.compile(r'\{\s*TEXT\("([\w-]+)"\),\s*TEXT\("([\w ]+)"\),\s*(true|false),\s*([\d.]+)f,\s*FLinearColor\(([^)]*)\),\s*FLinearColor\(([^)]*)\),\s*'
                     r'([\d.]+)f,\s*([\d.]+)f')
    looks = []
    for m in pat.finditer(src):
        looks.append({"name": m.group(1), "title": m.group(2), "quinn": m.group(3) == "true", "scale": float(m.group(4)),
                      "body": _floats(m.group(5)), "accent": _floats(m.group(6)), "rough": float(m.group(7)), "metal": float(m.group(8))})
    return looks


LOOKS = parse()


def build(i):
    import gear_chars_a
    look = LOOKS[i]
    B = gb.body(look["quinn"])
    fn = {0: "bulwark", 1: "vesper", 2: "khet", 3: "razorclaw", 4: "cinder"}.get(i)
    if fn:
        return getattr(gear_chars_a, fn)(B)
    try:
        import gear_chars_b
        fn = {5: "marlowe", 6: "nyx", 7: "oddjob", 8: "sable", 9: "gearhead"}.get(i)
        if fn:
            return getattr(gear_chars_b, fn)(B)
    except ImportError:
        pass
    try:
        import gear_chars_c
        fn = {10: "aurelia", 11: "tundra", 12: "mosscap", 13: "specter", 14: "brimstone"}.get(i)
        if fn:
            return getattr(gear_chars_c, fn)(B)
    except ImportError:
        pass
    raise KeyError("no gear for look %d" % i)
