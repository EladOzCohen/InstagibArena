"""Procedural conifers for DM-Citadel (pure python): dense ragged tiers on a trunk, cheap (about 700 triangles)."""

import math
import random

from mesh_b import Mesh, fbm


def fir_tree(height=700.0, radius=190.0, seed=1, tiers=9, sides=12):
    """Returns (foliage Mesh, trunk Mesh), origin at the foot of the trunk."""
    rng = random.Random(seed)
    fol = Mesh()
    trunk = Mesh()
    trunk.lathe(0, 0, -10.0, height * 0.9, 20.0, 7.0, sides=8, segments=4, jitter=0.8, seed=seed, profile=[(0, 1.25), (0.1, 1.0), (1.0, 1.0)])
    for i in range(tiers):
        t = i / float(max(1, tiers - 1))
        zb = height * (0.16 + 0.74 * t) - height * 0.05
        hi = height * (0.24 - 0.08 * t)
        r = radius * (1.0 - 0.86 * t) * rng.uniform(0.9, 1.1)

        def rfn(th, tt, i=i):
            return 1.0 + 0.18 * fbm(math.cos(th) * 2.0 + i * 3.1, math.sin(th) * 2.0, tt * 2.0, 2, seed + i) + 0.10 * math.sin(5.0 * th + i * 1.7) * (1.0 - tt)

        def zfn(th, tt, hi=hi):
            return -hi * 0.22 * (1.0 - tt) * (0.5 + 0.5 * math.sin(3.0 * th + 0.7))
        fol.lathe(0, 0, zb, zb + hi, r, r, sides=sides, segments=3, rfn=rfn, zfn=zfn, cap_bottom=True, cap_top=True, profile=[(0.0, 1.0), (0.4, 0.58), (1.0, 0.03)], seed=seed + i)
    return fol, trunk
