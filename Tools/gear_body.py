"""Measurements of the two Mannequins (reference pose, character space, cm, mesh scale 1) for the gear builders.
The bone table comes from Tools/probe_mannequin.py. The torso is described by ellipses per height (centre x, half depth, half width)
measured on the mesh, so that plates can wrap around it with a margin.

    B = gear_body.body(quinn=False)
    B.bone("upperarm_l") -> (x, y, z);  B.torso(z) -> (cx, ax, ay);  B.tpt(z, ang_deg, off) -> point on the torso surface (+off)
"""

import math

import mesh_char as mc

BONES = {
    "manny": {
        "pelvis": (2.3, 0.0, 95.9), "spine_03": (4.3, 0.0, 113.4), "spine_04": (3.7, 0.0, 121.9), "spine_05": (0.5, 0.0, 141.1),
        "neck_01": (-1.6, 0.0, 152.8), "head": (0.7, 0.0, 162.6), "clavicle_l": (-1.7, -1.4, 146.3), "upperarm_l": (-2.6, -19.0, 143.6),
        "lowerarm_l": (-1.9, -35.0, 120.9), "hand_l": (15.7, -47.8, 104.5), "thigh_l": (2.5, -10.0, 93.5), "calf_l": (2.6, -12.3, 50.3),
        "foot_l": (-1.0, -14.1, 8.2), "ball_l": (13.9, -15.8, 0.8),
    },
    "quinn": {
        "pelvis": (2.4, 0.0, 98.7), "spine_03": (4.3, 0.0, 113.6), "spine_04": (3.8, 0.0, 122.4), "spine_05": (0.1, 0.0, 139.5),
        "neck_01": (-2.4, 0.0, 151.2), "head": (0.1, 0.0, 162.5), "clavicle_l": (-2.1, -0.9, 145.0), "upperarm_l": (-2.5, -16.1, 142.8),
        "lowerarm_l": (-1.8, -32.4, 121.2), "hand_l": (14.4, -45.5, 105.4), "thigh_l": (2.7, -11.2, 95.5), "calf_l": (1.7, -13.1, 49.8),
        "foot_l": (0.0, -14.7, 8.1), "ball_l": (13.9, -15.8, 0.8),
    },
}

# (z, centre x, half depth, half width) of the torso
TORSO = {
    "manny": [(88, 0.8, 12.0, 17.8), (96, 1.2, 12.4, 16.8), (104, 2.9, 11.0, 15.4), (110, 3.65, 10.7, 14.1), (116, 3.8, 11.1, 14.2), (122, 2.75, 12.9, 15.8),
              (128, 1.8, 14.6, 18.0), (134, 0.85, 15.2, 19.8), (140, 0.45, 14.0, 19.8), (146, -0.6, 11.8, 18.8), (150, -1.6, 9.5, 14.0), (154, -1.3, 8.0, 8.5)],
    "quinn": [(88, 1.8, 12.0, 18.9), (96, 1.9, 12.1, 17.8), (104, 2.55, 11.45, 16.0), (110, 3.7, 10.1, 13.8), (116, 4.55, 8.85, 11.6), (122, 4.05, 9.75, 12.4),
              (128, 2.9, 12.0, 15.0), (134, 1.8, 12.9, 16.6), (140, 0.45, 11.65, 17.0), (146, -1.25, 8.95, 15.8), (150, -2.0, 7.4, 12.0), (154, -2.3, 6.0, 7.0)],
}

# head: centre, half sizes (x depth, y width, z height) of the skull incl. the face
HEAD = {
    "manny": ((2.7, 0.0, 167.2), 11.4, 8.9, 12.8),
    "quinn": ((2.0, 0.0, 167.0), 10.4, 8.2, 12.6),
}


class Body:
    def __init__(self, quinn):
        self.quinn = quinn
        self.key = "quinn" if quinn else "manny"
        self.head_c, self.head_rx, self.head_ry, self.head_rz = HEAD[self.key]

    def bone(self, name):
        if name.endswith("_r"):
            x, y, z = BONES[self.key][name[:-2] + "_l"]
            return (x, -y, z)
        return BONES[self.key][name]

    def torso(self, z):
        t = TORSO[self.key]
        if z <= t[0][0]:
            return t[0][1:]
        for k in range(len(t) - 1):
            if t[k][0] <= z <= t[k + 1][0]:
                f = (z - t[k][0]) / (t[k + 1][0] - t[k][0])
                return tuple(mc.lerp(t[k][i], t[k + 1][i], f) for i in (1, 2, 3))
        return t[-1][1:]

    def tpt(self, z, ang, off=0.0):
        """Point on the torso at height z; ang in degrees, 0 = front, +90 = right side (+y), 180 = back. off = margin in cm."""
        cx, ax, ay = self.torso(z)
        a = math.radians(ang)
        return (cx + (ax + off) * math.cos(a), (ay + off) * math.sin(a), z)

    def inside(self, z=135.0):
        cx, _, _ = self.torso(z)
        return (cx, 0.0, z)


_cache = {}


def body(quinn=False):
    if quinn not in _cache:
        _cache[quinn] = Body(quinn)
    return _cache[quinn]
