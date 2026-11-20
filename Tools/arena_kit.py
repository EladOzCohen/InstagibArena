"""A small kit for building big arenas fast (boxes, columns, stairs, ramps, bases, starts, pads). Run inside the editor (python commandlet).

    import arena_kit as ak
    A = ak.Arena("/Game/Maps/DM-Colosseum", "day_clear", seed=7)
    sand = A.surf("Sand", (200, 170, 120), "ColFloor")
    A.box("Floor", -3000, 3000, -2000, 2000, -300, 0, sand)
    A.stairs("Seat", "x", 3000, 3600, -2000, 2000, 0, 300, sand)
    A.base(0, -2750, 0); A.base(1, 2750, 0); A.team_starts(...) ; A.finish(kill_z=-600)

Rules that keep the bots working: steps at most 40 cm high, ramps under 15 degrees, walkways at least 300 cm wide, flat floors where the fight is.
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
from mapkit import MapBuilder  # noqa: E402
from matlib import surface  # noqa: E402


class Arena:
    def __init__(self, path, look="day_clear", seed=1, **look_kw):
        self.path = path
        self.m = MapBuilder(path)
        self.m.look(look, **look_kw)
        self.rng = random.Random(seed)
        self.n = 0

    # ------------------------------------------------------------------ materials
    def surf(self, name, albedo, tag, **kw):
        return surface(name, albedo=albedo, tag=tag, **kw)

    def glow(self, name, rgb, k=3.0):
        return self.m.glow(name, rgb, k)

    # ------------------------------------------------------------------ solids
    def box(self, prefix, x0, x1, y0, y1, z0, z1, mat, solid=True, yaw=0.0):
        """An axis-aligned box by its extents (yaw turns it about its centre)."""
        self.n += 1
        return self.m.box("%s_%d" % (prefix, self.n), (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0),
                          yaw=yaw, mat=mat, solid=solid)

    def boxc(self, prefix, cx, cy, z0, z1, sx, sy, mat, solid=True, yaw=0.0):
        """A box by its centre and size (yaw turns it)."""
        self.n += 1
        return self.m.box("%s_%d" % (prefix, self.n), cx, cy, (z0 + z1) / 2.0, sx, sy, abs(z1 - z0), yaw=yaw, mat=mat, solid=solid)

    def col(self, prefix, x, y, z0, z1, d, mat, solid=True):
        self.n += 1
        return self.m.column("%s_%d" % (prefix, self.n), x, y, z0, z1, d, mat=mat, solid=solid)

    def ring_cols(self, prefix, cx, cy, r, count, z0, z1, d, mat, a0=0.0, solid=True):
        for k in range(count):
            a = math.radians(a0 + k * 360.0 / count)
            self.col(prefix, cx + math.cos(a) * r, cy + math.sin(a) * r, z0, z1, d, mat, solid)

    def stairs(self, prefix, axis, start, end, lo, hi, z0, z1, mat, step=30.0):
        """Solid steps rising from z0 to z1 along x (axis 'x') or y, from `start` to `end`; lo..hi is the width on the other axis. start may be > end (it climbs towards `end`)."""
        count = max(1, int(math.ceil((z1 - z0) / step)))
        h = (z1 - z0) / count
        run = (end - start) / float(count)
        for i in range(count):
            a, b = start + i * run, start + (i + 1) * run
            top = z0 + (i + 1) * h
            if axis == "x":
                self.box(prefix, min(a, b), max(a, b), lo, hi, z0 - 40.0, top, mat)
            else:
                self.box(prefix, lo, hi, min(a, b), max(a, b), z0 - 40.0, top, mat)

    def ramp(self, prefix, p0, p1, width, mat, thickness=40.0):
        self.n += 1
        return self.m.slope("%s_%d" % (prefix, self.n), p0, p1, width, thickness=thickness, mat=mat)

    # ------------------------------------------------------------------ gameplay
    def base(self, team, x, y, z=6.0):
        import unreal as u
        f = self.m.spawn(u.IAFlagBase, "FlagBase_%s" % ("Blue" if team else "Red"), (x, y, z))
        f.set_editor_property("flag_team", team)

    def pad(self, label, x, y, z, target, color=(1.0, 0.6, 0.2), apex_extra=160.0):
        self.m.jump_pad(label, x, y, z, target, color=color, apex_extra=apex_extra)

    def light(self, label, loc, rgb, candela=80.0, radius=1400.0):
        self.m.accent_light(label, loc, rgb, candela=candela, radius=radius)

    def start(self, label, x, y, yaw, tag=None, z=0.0):
        a = self.m.spawn(unreal.PlayerStart, label, (x, y, z + 110.0), (0, 0, yaw))
        if tag:
            a.set_editor_property("player_start_tag", tag)
        self.m.start_count += 1

    def team_starts(self, team, cx, cy, spread=700.0, along="y", z=0.0, count=8, yaw=None):
        """Eight starts of a team in two rows around (cx, cy); the team faces the other side (red looks +x, blue -x)."""
        tag = "Blue" if team else "Red"
        yaw = yaw if yaw is not None else (180.0 if team else 0.0)
        for i in range(count):
            row, col = i % 2, i // 2
            off = (col - (count / 4.0 - 0.5)) * spread / (count / 2.0)
            dx = (row * 260.0) * (1 if team else -1)  # the second row stands behind the first
            if along == "y":
                self.start("Start_%s_%d" % (tag, i), cx + dx, cy + off, yaw, tag, z)
            else:
                self.start("Start_%s_%d" % (tag, i), cx + off, cy + dx, yaw, tag, z)

    def mid_starts(self, points):
        for i, (x, y, z) in enumerate(points):
            self.start("Start_Mid_%d" % i, x, y, math.degrees(math.atan2(-y, -x)), None, z)

    def finish(self, kill_z=-800.0, scale=1.0):
        self.m.check_starts()
        self.m.finish(kill_z=kill_z, scale=scale)
