"""A shared detail layer for the campaign characters (looks 17-40): wrist and ankle cuffs, elbow joints and a faction emblem on the chest.
apply(i, B, kit) adds the pieces to the kit of character i (called by gear_roster.build)."""

import gear_parts as gp
import mesh_char as mc
from gear_parts import Kit
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT

FACTION = {}
for _i in range(17, 21):
    FACTION[_i] = "rust"
for _i in range(21, 25):
    FACTION[_i] = "legion"
for _i in range(25, 29):
    FACTION[_i] = "syndicate"
for _i in range(29, 33):
    FACTION[_i] = "void"
for _i in range(33, 37):
    FACTION[_i] = "court"
for _i in range(37, 41):
    FACTION[_i] = "crown"          # Obsidian Crown: cuffs and straps only, their crown badge is part of gear_chars_j
# 41 Voss, 42 Wildcard and 43 Gino Gasket have no detail layer: cuffs, straps and a spine ridge do not fit a suit, a cloak or overalls

# characters whose chest is hidden by a coat, a cape or a hologram: no emblem
NO_EMBLEM = {28, 37, 38, 39, 40}
# characters with a cape or a long coat over the back: no spine ridge
NO_RIDGE = {37, 40}


def _x(p, dx):
    return (p[0] + dx, p[1], p[2])


def emblem(B, kind, accent_role=R_ACCENT):
    """A small badge on the left chest, standing 0.8-1.4 cm out of the armour."""
    m = GM()
    p = B.tpt(141.0, -27.0, 5.4)
    if kind == "rust":
        m.append(gp.cyl(_x(p, 0.0), _x(p, 1.2), 3.6, R_ACCENT, sides=6))
        m.append(gp.cyl(_x(p, 1.1), _x(p, 1.7), 2.2, R_TRIM, sides=6))
        for dy, dz in ((-3.9, 0.0), (3.9, 0.0)):
            m.append(gp.ball((p[0] + 1.4, p[1] + dy, p[2] + dz), 0.9, R_LIGHT, nu=6, nv=4))
    elif kind == "legion":
        m.append(gp.cyl(_x(p, 0.0), _x(p, 1.1), 3.6, R_ACCENT, sides=22))
        m.append(gp.cyl(_x(p, 1.0), _x(p, 1.5), 2.5, R_TRIM, sides=22))
        m.append(gp.ball((p[0] + 1.6, p[1], p[2]), 1.3, R_ACCENT, nu=8, nv=5))
        for s in (-1, 1):
            m.append(gp.box_at((p[0] + 0.6, p[1] + s * 5.0, p[2] - 0.5), (1.0, 1.4, 5.2), R_ACCENT, ch=0.3, roll=s * 28))
    elif kind == "syndicate":
        m.append(gp.box_at((p[0] + 0.5, p[1], p[2]), (1.0, 6.8, 6.8), R_TRIM, ch=0.3, roll=45))
        m.append(gp.box_at((p[0] + 1.1, p[1], p[2]), (0.8, 4.6, 4.6), R_GLOW, ch=0.2, roll=45))
    elif kind == "void":
        m.append(gp.box_at((p[0] + 0.5, p[1], p[2]), (1.0, 8.4, 5.0), R_TRIM, ch=0.3))
        m.append(gp.box_at((p[0] + 1.0, p[1], p[2] + 0.9), (0.8, 7.0, 1.2), R_ACCENT, ch=0.2))
        m.append(gp.box_at((p[0] + 1.0, p[1] - 2.4, p[2] - 1.1), (0.8, 2.4, 1.0), R_LIGHT, ch=0.2))
    elif kind == "court":
        m.append(gp.cyl(_x(p, 0.0), _x(p, 1.0), 4.0, R_TRIM, sides=3))
        m.append(gp.cyl(_x(p, 0.9), _x(p, 1.4), 2.4, R_GLOW, sides=3))
    return m


def cuffs(B):
    """Wrist and ankle cuffs for the LEFT side (use Kit.pair)."""
    arm, leg = GM(), GM()
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    arm.append(gp.ring_at(P0, P1, 22.4, 5.0, 2.2, R_TRIM, thick=1.0))
    arm.append(gp.ring_at(P0, P1, 24.2, 4.7, 0.9, R_ACCENT, thick=0.5))
    Q0, Q1 = B.bone("calf_l"), B.bone("foot_l")
    leg.append(gp.ring_at(Q0, Q1, 36.2, 6.2, 2.4, R_TRIM, thick=1.1))
    leg.append(gp.ring_at(Q0, Q1, 33.4, 6.0, 0.9, R_ACCENT, thick=0.5))
    return arm, leg


def elbow(B):
    m = GM()
    P = B.bone("lowerarm_l")
    m.append(gp.ball(P, 3.9, R_TRIM, nu=10, nv=6))
    return m


def spine_ridge(B):
    """A segmented ridge of small plates down the back, seen by everyone who chases the character."""
    m = GM()
    k = 0
    for z in (122.0, 127.5, 133.0, 138.5, 144.0):
        bx = gp.back_x(B, z, 0.0)
        m.append(gp.box_at((bx - 1.3, 0.0, z), (2.2, 4.4 - k * 0.3, 3.8), R_TRIM, ch=0.5))
        m.append(gp.box_at((bx - 2.5, 0.0, z), (0.6, 1.6, 2.2), R_ACCENT, ch=0.2))
        k += 1
    return m


def thigh_strap(B):
    m = GM()
    P0, P1 = B.bone("thigh_l"), B.bone("calf_l")
    m.append(gp.ring_at(P0, P1, 21.0, 8.6, 2.6, R_TRIM, thick=1.0))
    m.append(gp.ring_at(P0, P1, 23.9, 8.4, 0.8, R_ACCENT, thick=0.5))
    return m


def apply(i, B, kit):
    kind = FACTION.get(i)
    if not kind:
        return kit
    arm, leg = cuffs(B)
    kit.pair("lowerarm", arm)
    kit.pair("calf", leg)
    if i not in NO_RIDGE:
        kit.add("spine_05", spine_ridge(B))
    kit.pair("thigh", thigh_strap(B))
    if i not in NO_EMBLEM:
        kit.add("spine_05", emblem(B, kind))
    return kit
