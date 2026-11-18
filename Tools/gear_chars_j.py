"""Gear of the reward characters (looks 37-43): the four Obsidian Crown fighters (Regent, Sentinel, Harrier, Oracle), Director Voss,
the Wildcard and Gino Gasket. Each function takes the Body and returns a gear_parts.Kit.

Palette notes (the roster entries in IACharacterRoster.h override some gear roles with FIAGearRole):
- Obsidian Crown: plate = glossy obsidian (roughness 0.3), trim = glossy black, accent = gold metal, glow = red. Shared crown badge on the chest.
- Voss: plate = white suit, cloth = black, light = bright white, accent / glow = cold blue-white.
- Wildcard: plate = grey-green, cloth = darker cloak, trim = worn tan scarf and straps, light = the blank mask, accent = the one orange line.
- Gino Gasket: plate = blue overalls, cloth = skin, accent = red cap, trim = brass, glow = dark brown (no glow: moustache, boots, belt),
  light = white gloves, team = the stripes of the shirt and the neckerchief.
"""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_b import kneepad, pouch
from gear_chars_c import ring_strips
from gear_parts import Kit, back_x, front_x, COS, SIN, rad
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT, fr

# approximate colours of the role overrides for the software preview (gear_preview.py)
_RED = (1.0, 0.06, 0.04)
_CROWN = {R_TRIM: (0.02, 0.02, 0.025), R_GLOW: _RED}
PREVIEW_ROLES = {
    37: _CROWN, 38: _CROWN, 39: _CROWN, 40: _CROWN,
    41: {R_CLOTH: (0.03, 0.03, 0.035), R_LIGHT: (0.85, 0.86, 0.9)},
    42: {R_CLOTH: (0.1, 0.13, 0.1), R_TRIM: (0.36, 0.28, 0.17), R_LIGHT: (0.72, 0.72, 0.68)},
    43: {R_CLOTH: (0.85, 0.6, 0.45), R_TRIM: (0.85, 0.62, 0.22), R_GLOW: (0.2, 0.1, 0.05), R_LIGHT: (0.95, 0.95, 0.93)},
}


# ------------------------------------------------------------------------------------------------ helpers
def crown_badge(B, z, off, s=1.0):
    """The Obsidian Crown team badge: a gold five-pointed crown with a red gem on a glossy black shield, centred on the chest."""
    m = GM()
    x = B.tpt(z, 0.0, off)[0]
    m.append(gp.box_at((x + 0.5, 0.0, z + 0.4 * s), (1.2, 11.0 * s, 9.6 * s), R_TRIM, ch=0.5, taper=0.92))
    m.append(gp.box_at((x + 1.4, 0.0, z - 2.4 * s), (1.0, 8.6 * s, 2.2 * s), R_ACCENT, ch=0.35))
    for (y, h) in ((-3.7, 3.4), (-1.85, 4.6), (0.0, 6.0), (1.85, 4.6), (3.7, 3.4)):
        base = (x + 1.4, y * s, z - 1.6 * s)
        tip = (x + 1.4, y * s * 1.12, z - 1.6 * s + h * s)
        m.append(gp.spike(base, tip, 0.9 * s, R_ACCENT, sides=4))
        m.append(gp.ball(tip, 0.55 * s, R_ACCENT, nu=6, nv=4))
    m.append(gp.ball((x + 2.0, 0.0, z - 2.4 * s), 0.85 * s, R_GLOW, nu=8, nv=5))
    return m


def body_line(B, z_top, z_bot, a_top, a_bot, role, off_, thick=0.7, steps=8, width=2.6, bulge=None):
    """A thin strip on the torso from (z_top, a_top) to (z_bot, a_bot), `width` degrees wide, that follows a plate with the given bulge
    (glow and gold lines, straps)."""
    m = GM()

    def surf(u, v):
        z = z_top + (z_bot - z_top) * v
        a = a_top + (a_bot - a_top) * v + (u - 0.5) * width
        return B.tpt(z, a, off_ + (bulge(a, z) if bulge else 0.0))
    m.plate(surf, gp.samples(2), gp.samples(steps + 1), lambda u, v: thick, role, B.inside((z_top + z_bot) / 2))
    return m


def band_arc(H, z, h, a0, a1, role, off=0.3, depth=0.6, sides=6):
    """A short raised band on a helmet between the angles a0..a1 (degrees, 0 = front, +90 = right)."""
    m = GM()
    r = H.r(z) + off
    m.lathe([(r, z - h / 2), (r + depth, z - h / 2), (r + depth, z + h / 2), (r, z + h / 2)], role, sides=sides, f=fr((H.cx, 0.0, 0.0)), sy=H.sy,
            arc=(a0, a1), creases=(1, 2), caps=(False, False))
    return m


def limb_line(P0, P1, s0, s1, r0, r1, ang, role, width=9.0, thick=0.5):
    """A thin straight line along a limb (gold piping on a suit)."""
    return gp.tube_plate(P0, P1, s0, s1, r0, r1, ang - width / 2, ang + width / 2, thick, role, nu=2, nv=3, w=0.3, lo=0.6)


def torus(c, R, r, role, tilt=90.0, sides=28, rings=6):
    """A smooth ring; with tilt 90 it stands upright and faces forward (+x)."""
    return gp.blob_ring(c, R, r, role, lumps=1, amp=0.0, sides=sides, rings=rings, tilt=tilt)


def ragged(n=7, depth=0.14, seed=0.0):
    """A torn hem: hem(u) for gear_parts.hang."""
    return lambda u: 1.0 - depth * (0.5 + 0.5 * SIN(u * n * math.pi * 2 + seed)) * (0.6 + 0.4 * SIN(u * 13.0 + seed * 2.0))


def full_wrap(P0, P1, s0, s1, r0, r1, role, thick=1.0, nv=5, nu=14, sy=1.0, bulge=None):
    """A closed sleeve around a limb (trousers, sleeves)."""
    return gp.tube_plate(P0, P1, s0, s1, r0, r1, 0.0, 360.0, thick, role, nv=nv, nu=nu, w=0.12, lo=0.5, sy=sy, bulge=bulge)


def calf_bulge(amount=1.8):
    """Room for the calf muscle at the back of a trouser leg (bulge(u, v) for full_wrap on calf -> foot)."""
    return lambda u, v: amount * max(0.0, -COS(rad(360.0 * u))) ** 1.5 * SIN(math.pi * min(1.0, v * 1.7))


def crown_tassets(k, B, z0=101.0, span=34.0, off_=1.6, thick=1.5):
    for j, z in enumerate((z0, z0 + 6.0, z0 + 12.0)):
        k.add("pelvis" if j == 0 else "spine_05", gp.torso_plate(B, z, z + 5.4, -span + j * 3, span - j * 3, off_, thick, R_PLATE, nu=7, nv=2, w=0.3))
        k.add("pelvis" if j == 0 else "spine_05", gp.torso_plate(B, z - 0.2, z + 1.0, -span + j * 3 + 2, span - j * 3 - 2, off_ + thick * 0.8, 0.6, R_ACCENT, nu=7, nv=2, w=0.3))


# ------------------------------------------------------------------------------------------------ 37 Regent
def regent(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.0, jaw=0.92)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.0, slit_w=13.0, slit_h=1.8, jaw=0.92, brow=True, vents=False,
                               cheek=True, chin=True))
    # the crown crest: a gold band round the helmet and five points over the brow, a red gem in the middle
    zb = zc + 6.2
    k.add("head", band_head(H, zb, 2.6, R_ACCENT, off=0.3))
    for (a, h) in ((-62, 5.0), (-31, 7.5), (0, 11.0), (31, 7.5), (62, 5.0)):
        r = H.r(zb) + 0.9
        base = (H.cx + r * COS(rad(a)), r * H.sy * SIN(rad(a)), zb + 0.6)
        tip = (base[0] + 0.12 * h * COS(rad(a)), base[1] + 0.12 * h * SIN(rad(a)), zb + 0.6 + h)
        k.add("head", gp.spike(base, tip, 1.5, R_ACCENT, sides=6))
        k.add("head", gp.ball(tip, 0.75, R_ACCENT, nu=6, nv=4))
    k.add("head", gp.ball(H.pt(zb, 0.0, 1.5), 1.2, R_GLOW, nu=8, nv=5))
    # red glow lines on the cheeks
    for s in (-1, 1):
        k.add("head", band_arc(H, zc - 1.5, 0.8, s * 40 - 18, s * 40 + 18, R_GLOW, off=0.5))
    z0, z1, span = 117.0, 151.0, 68.0
    bul = gp.pec_bulge(2.6, z0, z1, span)
    k.add("spine_05", gp.collar_ring(B, z=151.0, r=9.6, h=5.2, role=R_ACCENT, thick=1.4))
    k.add("spine_05", gp.cuirass(B, off_=2.0, thick=2.0, span=span, bulge=2.6, vneck=8, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 122.0, 125.0, -62, 62, 4.1, 0.9, R_ACCENT, nu=13, nv=2, w=0.3, bulge=bul))
    for s in (-1, 1):
        k.add("spine_05", body_line(B, 147.0, 126.0, s * 46, s * 12, R_GLOW, 4.0, thick=0.8, width=4.5, bulge=bul))
    k.add("spine_05", crown_badge(B, 136.5, 6.6, 1.15))
    crown_tassets(k, B)
    # a short cape: obsidian red-black cloth with gold edges and a glowing hem
    k.add("spine_05", gp.hang(B.tpt(149.0, -124, 3.0), B.tpt(149.0, 124, 3.0), (-0.15, 0.0, -1.0), 60.0, R_CLOTH, out=(-1, 0, 0), taper=1.22, bulge=2.6, ripple=1.0,
                              waves=2.0, nu=9, nv=8, thick=0.7, hem=lambda u: 1.0 - 0.18 * abs(2 * u - 1) ** 2,
                              stripes=[(0.0, 0.05, R_ACCENT), (0.95, 1.0, R_ACCENT), (0.05, 0.95, R_GLOW, 0.93, 1.0)]))
    k.pair("upperarm", gp.pauldron(B, big=1.45, layers=3, top_role=R_PLATE, lame_role=R_PLATE, trim_role=R_ACCENT, thick=1.5, ridge=1.1, alpha=46))
    g = GM()
    g.append(gp.bracer(B, flare=1.4, accent=R_ACCENT, thick=1.3, s0=3, s1=23, rings=True))
    g.append(gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 17.5, 5.6, 1.0, R_GLOW, thick=0.6))
    k.pair("lowerarm", g)
    k.add("pelvis", belt(B, z0=94.5, z1=101.0, role=R_ACCENT, buckle=R_GLOW, thick=1.4))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 8.0, 34.0, 10.8, 9.2, -72, 72, 1.4, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    gr_ = GM()
    gr_.append(gp.greave(B, accent=R_ACCENT, thick=1.5, s1=37.0))
    gr_.append(limb_line(B.bone("calf_l"), B.bone("foot_l"), 6.0, 30.0, 8.6, 7.0, 0.0, R_GLOW, width=7.0, thick=0.4))
    k.pair("calf", gr_)
    return k


# ------------------------------------------------------------------------------------------------ 38 Sentinel
def _tower(B):
    """The tower shoulder guard over the left shoulder: an eight-sided turret with gold battlements and a red arrow slit."""
    m = GM()
    J = B.bone("upperarm_l")
    c = (J[0] - 1.5, J[1] - 6.5, 146.0)
    f = fr(c, roll=-10.0)
    m.lathe([(9.2, 0.0), (10.0, 23.0), (11.6, 25.0), (11.6, 30.0), (10.0, 30.0), (10.0, 28.4), (0.0, 28.4)], R_PLATE, sides=8, f=f, rot=math.pi / 8,
            creases=(1, 2, 3, 4, 5), caps=(True, False))
    m.lathe([(10.15, 22.4), (11.5, 23.9), (11.5, 25.3), (10.15, 24.6), (10.15, 22.4)], R_ACCENT, sides=8, f=f, rot=math.pi / 8, creases=(1, 2, 3), caps=(False, False))
    m.lathe([(9.2, 0.0), (9.9, 0.0), (9.9, 1.8), (9.25, 1.8), (9.2, 0.0)], R_ACCENT, sides=8, f=f, rot=math.pi / 8, creases=(1, 2, 3), caps=(False, False))
    for i in range(4):
        a = 45.0 + i * 90.0
        p = f.pt((10.8 * COS(rad(a)), 10.8 * SIN(rad(a)), 32.2))
        m.append(gp.box_at(p, (4.0, 4.4, 4.4), R_ACCENT, ch=0.5, yaw=a))
    # arrow slits: outside, front and back
    m.append(gp.box_at(f.pt((0.0, -10.0, 13.0)), (1.6, 1.2, 10.0), R_GLOW, ch=0.2))
    m.append(gp.box_at(f.pt((9.4, -3.8, 13.0)), (1.2, 1.6, 10.0), R_GLOW, ch=0.2, yaw=22.5))
    m.append(gp.box_at(f.pt((-9.4, -3.8, 13.0)), (1.2, 1.6, 10.0), R_GLOW, ch=0.2, yaw=-22.5))
    return m


def sentinel(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.4, jaw=0.98)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.4, slit_w=15.0, slit_h=1.5, jaw=0.98, brow=True, vents=True,
                               cheek=True, chin=True))
    # a gold band with square teeth round the top of the helmet: a small crown of battlements
    zb = zc + 7.5
    k.add("head", band_head(H, zb, 2.2, R_ACCENT, off=0.3))
    for i in range(8):
        a = 22.5 + i * 45.0
        r = H.r(zb) - 0.2
        k.add("head", gp.box_at((H.cx + r * COS(rad(a)), r * H.sy * SIN(rad(a)), zb + 2.4), (2.6, 3.0, 3.0), R_ACCENT, ch=0.45, yaw=a))
    z0, z1, span = 115.0, 152.0, 78.0
    bul = gp.pec_bulge(3.4, z0, z1, span)
    k.add("spine_05", gp.collar_ring(B, z=150.5, r=10.6, h=6.5, role=R_PLATE, thick=2.0))
    k.add("spine_05", gp.collar_ring(B, z=156.5, r=11.0, h=1.2, role=R_ACCENT, thick=1.2))
    k.add("spine_05", gp.cuirass(B, off_=3.0, thick=2.8, span=span, bulge=3.4, vneck=5, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 127.0, 130.5, -66, 66, 6.0, 1.0, R_ACCENT, nu=15, nv=2, w=0.3, lo=0.8, bulge=bul))
    k.add("spine_05", gp.torso_plate(B, 114.5, 116.5, -70, 70, 5.0, 0.8, R_ACCENT, nu=13, nv=2, w=0.3))
    k.add("spine_05", crown_badge(B, 140.5, 8.8, 1.25))
    crown_tassets(k, B, span=38.0, off_=2.0, thick=1.8)
    # a power pack on the back with red vents
    bx = back_x(B, 133.0)
    k.add("spine_05", gp.box_at((bx - 5.0, 0.0, 133.0), (8.0, 24.0, 28.0), R_PLATE, ch=1.6))
    k.add("spine_05", gp.box_at((bx - 9.2, 0.0, 145.5), (2.0, 20.0, 2.0), R_ACCENT, ch=0.5))
    for y in (-6.0, 0.0, 6.0):
        k.add("spine_05", gp.box_at((bx - 9.1, y, 131.0), (1.0, 2.2, 15.0), R_GLOW, ch=0.3))
    # the tower over the left shoulder, a plain heavy pauldron on the right
    k.add("spine_05", _tower(B))
    k.add("upperarm_l", gp.pauldron(B, big=1.25, layers=3, dome=False, lame_role=R_PLATE, thick=1.6, alpha=46))
    k.add("upperarm_r", gp.pauldron(B, big=1.8, layers=3, top_role=R_PLATE, lame_role=R_PLATE, trim_role=R_ACCENT, thick=1.8, ridge=1.4, alpha=44).mirrored())
    k.pair("lowerarm", gp.bracer(B, flare=2.1, accent=R_ACCENT, thick=1.9, s0=2, s1=24, rings=True))
    k.add("pelvis", belt(B, z0=93.5, z1=101.5, role=R_ACCENT, buckle=R_GLOW, thick=1.8, buckle_w=9.0))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 6.0, 36.0, 11.4, 9.6, -80, 80, 1.9, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=2.1, s1=38.0, arc=(-110, 110)))
    return k


# ------------------------------------------------------------------------------------------------ 39 Harrier
def harrier(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.5, jaw=0.88)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=1.5, slit_w=15.0, slit_h=1.6, jaw=0.88, brow=False, vents=False,
                               cheek=False, chin=False))
    # the swept-back crest: a tall gold blade over the middle and two thin ones at the temples
    fz = zc + 6.0
    m = GM()
    m.sweep([(H.front(fz) - 0.6, 0.0, fz), (H.cx + 4.0, 0.0, H.z_top + 1.0), (H.cx - 5.0, 0.0, H.z_top + 3.4), (H.cx - 15.0, 0.0, H.z_top + 3.0),
             (H.cx - 24.0, 0.0, H.z_top + 0.5)], [1.0, 2.4, 2.8, 2.0, 0.25], R_ACCENT, sides=8, flat=(0.33, 1.0))
    k.add("head", m)
    for s in (-1, 1):
        m = GM()
        p0 = H.pt(zc + 3.0, s * 62.0, -0.2)
        m.sweep([p0, (H.cx - 6.0, s * (H.side(zc + 4.0) + 1.0), zc + 6.0), (H.cx - 16.0, s * (H.side(zc + 4.0) + 1.6), zc + 9.5)], [1.3, 1.1, 0.2], R_ACCENT, sides=6,
                flat=(0.4, 1.0))
        k.add("head", m)
    k.add("head", band_arc(H, zc - 2.5, 0.7, -50, 50, R_ACCENT, off=0.2, depth=0.4, sides=8))
    # a slim chest plate with gold lines and the crown
    z0, z1, span = 120.0, 149.0, 52.0
    bul = gp.pec_bulge(1.4, z0, z1, span)
    k.add("spine_05", gp.collar_ring(B, z=149.5, r=8.0, h=4.0, role=R_PLATE, thick=1.1))
    k.add("spine_05", gp.cuirass(B, off_=1.1, thick=1.1, span=span, bulge=1.4, vneck=7, z0=z0, z1=z1, panel=False))
    for s in (-1, 1):
        k.add("spine_05", body_line(B, 147.0, 106.0, s * 58, s * 9, R_ACCENT, 0.9, thick=0.9, width=4.0, steps=10))
        k.add("spine_05", body_line(B, 147.0, 112.0, 180 + s * 50, 180 + s * 10, R_ACCENT, 1.4, thick=0.8, width=4.0, steps=9))
    k.add("spine_05", crown_badge(B, 137.0, 3.6, 0.9))
    # small wings behind the shoulders: four gold and obsidian feathers each, fanned up and back
    for s in (-1, 1):
        w = GM()
        root = (back_x(B, 143.0) - 1.0, s * 11.0, 144.0)
        for j in range(4):
            a = rad(28.0 + j * 17.0)                 # angle of the feather above the horizontal, seen from behind
            L = 19.0 - j * 2.6
            d = mc.norm((-0.55, s * COS(a), SIN(a)))
            p1 = mc.add(root, mc.mul(d, L * 0.5))
            p2 = mc.add(root, mc.mul(d, L))
            p2 = (p2[0] - 3.0, p2[1], p2[2])
            w.sweep([mc.add(root, mc.mul(d, 1.0)), p1, p2], [2.0, 2.4, 0.3], R_ACCENT if j % 2 == 0 else R_PLATE, sides=6, flat=(0.3, 1.0))
        w.append(gp.ball(root, 2.6, R_TRIM, nu=8, nv=5))
        w.append(gp.ball((root[0] - 1.2, root[1], root[2]), 1.0, R_GLOW, nu=6, nv=4))
        k.add("spine_05", w)
    k.pair("upperarm", gp.pauldron(B, big=0.8, layers=1, top_role=R_PLATE, lame_role=R_PLATE, trim_role=R_ACCENT, thick=1.0, ridge=0.7, alpha=50))
    J, E, Hd = B.bone("upperarm_l"), B.bone("lowerarm_l"), B.bone("hand_l")
    a = GM()
    a.append(limb_line(J, E, 9.0, 24.0, 6.4, 5.4, 90.0, R_ACCENT, width=10.0))
    k.add("upperarm_l", a)
    k.add("upperarm_r", a.mirrored())
    g = GM()
    g.append(gp.bracer(B, flare=0.95, accent=R_ACCENT, thick=0.9, s0=5, s1=22, rings=True))
    g.append(limb_line(E, Hd, 2.0, 6.0, 5.4, 5.2, 90.0, R_ACCENT, width=12.0))
    k.pair("lowerarm", g)
    k.add("pelvis", belt(B, z0=96.0, z1=100.0, role=R_ACCENT, buckle=R_GLOW, thick=0.9, buckle_w=5.0))
    T, C, F = B.bone("thigh_l"), B.bone("calf_l"), B.bone("foot_l")
    th = GM()
    th.append(gp.tube_plate(T, C, 12.0, 32.0, 10.6, 9.2, -48, 48, 1.0, R_PLATE, nv=4, nu=7, w=0.12, lo=0.4))
    th.append(limb_line(T, C, 4.0, 40.0, 10.8, 8.4, 90.0, R_ACCENT, width=9.0, thick=0.7))
    k.pair("thigh", th)
    cv = GM()
    cv.append(gp.greave(B, accent=R_ACCENT, thick=1.0, s0=5.0, s1=36.0, arc=(-70, 70)))
    cv.append(limb_line(C, F, 2.0, 34.0, 7.6, 5.8, 90.0, R_ACCENT, width=11.0, thick=0.7))
    k.pair("calf", cv)
    return k


# ------------------------------------------------------------------------------------------------ 40 Oracle
def oracle(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.6, jaw=0.9)
    # a smooth obsidian head and a gold half-mask over the eyes and the nose, red eye slits
    k.add("head", H.shell(R_PLATE, sides=18, caps=(False, True)))
    mk = GM()
    za, zb_ = zc - 3.0, zc + 6.5

    def surf(u, v):
        z = za + (zb_ - za) * v
        a = -78.0 + 156.0 * u
        lo = 2.8 * (1.0 - abs(2 * u - 1)) ** 1.5         # the lower edge rises towards the middle (over the nose)
        z = max(z, za + lo * (1.0 - v))
        return H.pt(z, a, 0.15)
    mk.plate(surf, gp.samples(13), gp.samples(5), lambda u, v: 1.0 * gp.edge(u, v, 0.12, 0.4), R_ACCENT, H.c)
    k.add("head", mk)
    k.add("head", gp.box_at((H.front(zc + 1.0) + 1.2, 0.0, zc + 0.5), (2.4, 1.6, 6.0), R_ACCENT, ch=0.5, taper=0.7))
    for s in (-1, 1):
        k.add("head", gp.box_at(H.pt(zc + 2.6, s * 24.0, 1.2), (0.8, 4.2, 1.0), R_GLOW, ch=0.2, yaw=s * 24))
        k.add("head", band_arc(H, zc + 7.6, 0.9, s * 20, s * 85, R_ACCENT, off=0.1, depth=0.5))
    # the floating gold ring behind the head, with rays and a red inner ring
    rc = (H.cx - H.rx - 6.5, 0.0, zc + 4.0)
    k.add("head", torus(rc, 13.0, 0.95, R_ACCENT))
    k.add("head", torus(rc, 10.6, 0.45, R_GLOW, sides=24, rings=5))
    for i in range(12):
        a = rad(i * 30.0)
        p0 = (rc[0], 14.2 * COS(a), rc[2] + 14.2 * SIN(a))
        p1 = (rc[0], (17.5 + (1.6 if i % 2 == 0 else 0.0)) * COS(a), rc[2] + (17.5 + (1.6 if i % 2 == 0 else 0.0)) * SIN(a))
        k.add("head", gp.spike(p0, p1, 0.9, R_ACCENT, sides=4))
    # a high gold collar and the coat
    k.add("spine_05", gp.collar_ring(B, z=148.0, r=9.0, h=8.5, role=R_ACCENT, thick=1.0, cx_shift=-2.4))
    k.add("spine_05", gp.torso_plate(B, 108.0, 149.0, 8, 352, 1.6, 1.3, R_CLOTH, nu=22, nv=7, w=0.1, bulge=gp.pec_bulge(1.0, 108, 149, 60)))
    for s in (-1, 1):
        k.add("spine_05", body_line(B, 149.0, 104.0, s * 12, s * 9, R_ACCENT, 1.6, thick=1.2, width=3.6, steps=6))
        k.add("spine_05", body_line(B, 147.0, 106.0, s * 17, s * 14, R_GLOW, 1.8, thick=0.7, width=1.6, steps=6))
    k.add("spine_05", gp.torso_plate(B, 108.0, 149.0, -8, 8, 1.0, 1.0, R_PLATE, nu=3, nv=6, w=0.2))
    k.add("spine_05", crown_badge(B, 137.0, 3.6, 0.85))
    # the long coat: overlapping panels all round the hips, open at the front, gold hem with a red line
    k.add("pelvis", ring_strips(B, 100.0, 16, 78.0, R_CLOTH, rad_off=2.6, flare=0.14, width_deg=17.0, skip=((0, 1),), nv=7, taper=1.0,
                                bands=[(0.0, 1.0, R_ACCENT, 0.93, 1.0), (0.0, 1.0, R_GLOW, 0.88, 0.91)]))
    k.add("pelvis", belt(B, z0=97.0, z1=103.0, role=R_ACCENT, buckle=R_GLOW, thick=1.0))
    k.pair("upperarm", gp.pauldron(B, big=1.05, layers=2, top_role=R_CLOTH, lame_role=R_CLOTH, trim_role=R_ACCENT, thick=1.2, ridge=0.9, alpha=48))
    g = GM()
    E, Hd = B.bone("lowerarm_l"), B.bone("hand_l")
    g.append(full_wrap(E, Hd, 0.0, 20.0, 6.2, 9.6, R_CLOTH, thick=0.8, nv=5, nu=16))      # a wide sleeve, open towards the hand
    g.append(gp.ring_at(E, Hd, 18.4, 10.3, 1.8, R_ACCENT, thick=1.0, sides=16))
    g.append(gp.ring_at(E, Hd, 16.4, 9.9, 0.7, R_GLOW, thick=0.5, sides=16))
    g.append(gp.ring_at(E, Hd, 21.0, 5.0, 1.6, R_ACCENT, thick=0.9))
    k.pair("lowerarm", g)
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.2, s1=36.0, knee=False))
    return k


# ------------------------------------------------------------------------------------------------ 41 Voss
def voss(B):
    k = Kit(B)
    zc = B.head_c[2]
    # slicked-back black hair (no helmet): a cap over the top and a longer part over the back of the head
    # the hairline is high at the forehead and low at the nape; the hair thins out at its edge
    Hh = gp.Helm(B, 1.1, z_bot=zc - 9.0, jaw=0.98, cx_shift=-0.6)
    hair = GM()

    def hsurf(u, v):
        a = 360.0 * u
        z_lo = zc - 0.9 + 6.6 * COS(rad(a))
        z = z_lo + (Hh.z_top - z_lo) * SIN(rad(90.0 * v))
        return Hh.pt(z, a, 0.0)
    hair.plate(hsurf, gp.samples(24, True), gp.samples(8), lambda u, v: 1.3 * gp.edge(0.5, v, 0.25, 0.25) * (1.0 + 0.5 * max(0.0, -COS(rad(360.0 * u))) * v),
               R_TRIM, Hh.c, wrap_u=True)
    k.add("head", hair)
    for s in (-1, 1):
        k.add("head", gp.box_at((Hh.cx + 3.0, s * (Hh.side(zc + 1.0) + 0.1), zc + 1.0), (2.6, 0.9, 5.0), R_TRIM, ch=0.35))
    # a monocle over the right eye and a thin earpiece with a microphone on the left
    H = gp.Helm(B, 0.0)
    ex, ey, ez = H.front(zc + 2.0) - 0.4, 3.7, zc + 2.0
    k.add("head", gp.cyl((ex, ey, ez), (ex + 0.8, ey, ez), 2.7, R_TRIM, sides=16))
    k.add("head", gp.cyl((ex + 0.5, ey, ez), (ex + 1.0, ey, ez), 2.1, R_GLOW, sides=16))
    k.add("head", _sweep([(ex + 0.2, ey + 2.4, ez - 1.0), (ex - 1.0, ey + 4.2, ez - 6.0), (ex - 3.5, ey + 4.6, ez - 12.0)], [0.22, 0.22, 0.22], R_ACCENT, sides=4))
    ear = (H.cx - 0.5, -(H.side(zc) + 0.6), zc)
    k.add("head", gp.box_at(ear, (3.2, 1.6, 4.2), R_TRIM, ch=0.5))
    k.add("head", gp.box_at((ear[0], ear[1] - 0.9, ear[2]), (2.0, 0.4, 2.8), R_GLOW, ch=0.15))
    k.add("head", _sweep([(ear[0] + 1.0, ear[1] - 0.6, ear[2] - 1.5), (ear[0] + 6.0, ear[1] + 1.2, zc - 6.0), (H.front(zc - 6.0) - 2.0, -3.5, zc - 7.5)],
                         [0.25, 0.25, 0.25], R_TRIM, sides=4))
    # the high collar, open at the front, with a cold blue edge
    c = (B.torso(149.0)[0] - 2.0, 0.0, 147.0)
    col = GM()
    col.lathe([(9.2, 0.0), (10.6, 12.0)], R_CLOTH, sides=20, f=fr(c), sy=1.08, arc=(48.0, 312.0), caps=(False, False), double=True)
    col.lathe([(10.55, 11.6), (10.8, 12.6), (10.2, 12.6), (10.0, 11.6)], R_ACCENT, sides=20, f=fr(c), sy=1.08, arc=(48.0, 312.0), caps=(False, False), creases=(1, 2))
    k.add("spine_05", col)
    # the white jacket open over a black waistcoat, lapels with a blue-white edge, a glowing tie line
    k.add("spine_05", gp.torso_plate(B, 106.0, 149.0, 14, 346, 1.6, 1.3, R_PLATE, nu=22, nv=7, w=0.08, bulge=gp.pec_bulge(1.2, 106, 149, 60)))
    k.add("spine_05", gp.torso_plate(B, 108.0, 147.0, -16, 16, 1.0, 1.1, R_CLOTH, nu=5, nv=6, w=0.2))
    for s in (-1, 1):
        k.add("spine_05", body_line(B, 148.5, 118.0, s * 30, s * 14, R_LIGHT, 2.4, thick=0.8, width=9.0, steps=7))
        k.add("spine_05", body_line(B, 148.5, 118.0, s * 25.5, s * 9.6, R_ACCENT, 3.0, thick=0.6, width=1.6, steps=7))
    k.add("spine_05", body_line(B, 146.0, 114.0, 0.0, 0.0, R_GLOW, 1.9, thick=0.5, width=2.2, steps=4))
    for i in range(3):
        k.add("spine_05", gp.ball(B.tpt(112.0 + i * 5.0, 0.0, 2.3), 0.7, R_LIGHT, nu=6, nv=4))
    # a white pocket square and the League pin on the lapel
    k.add("spine_05", gp.torso_plate(B, 137.0, 140.0, -40, -28, 3.0, 0.8, R_LIGHT, nu=3, nv=2, w=0.3, top_fn=lambda u: 1.6 * abs(2 * u - 1)))
    pin = B.tpt(141.5, 24.0, 4.2)
    k.add("spine_05", gp.box_at(pin, (0.8, 1.8, 1.8), R_GLOW, ch=0.2, roll=45))
    # tailored shoulders and long coat tails
    k.pair("upperarm", gp.pauldron(B, big=0.9, layers=1, top_role=R_PLATE, lame_role=R_PLATE, trim_role=R_PLATE, thick=1.0, ridge=0.0, alpha=50))
    for (a0, a1) in ((128.0, 179.0), (181.0, 232.0)):
        k.add("pelvis", gp.hang(B.tpt(106.0, a0, 2.4), B.tpt(106.0, a1, 2.4), (-0.06, 0.0, -1.0), 68.0, R_PLATE, out=(-1, 0, 0), taper=0.62, bulge=1.0, ripple=0.4,
                                waves=1.0, nu=5, nv=9, thick=0.6, hem=lambda u: 1.0 - 0.12 * u if a0 < 180 else 0.88 + 0.12 * u,
                                stripes=[(0.0, 0.08, R_CLOTH), (0.92, 1.0, R_CLOTH)]))
    k.add("pelvis", gp.hang(B.tpt(104.0, -44, 2.2), B.tpt(104.0, -12, 2.2), (0.1, 0.0, -1.0), 14.0, R_PLATE, out=(1, 0, 0), taper=0.8, nu=4, nv=3, thick=0.6))
    k.add("pelvis", gp.hang(B.tpt(104.0, 12, 2.2), B.tpt(104.0, 44, 2.2), (0.1, 0.0, -1.0), 14.0, R_PLATE, out=(1, 0, 0), taper=0.8, nu=4, nv=3, thick=0.6))
    k.add("pelvis", belt(B, z0=100.5, z1=104.5, role=R_CLOTH, buckle=R_ACCENT, thick=0.9, buckle_w=4.0))
    # sleeves: white cuffs with a blue cufflink, black gloves
    E, Hd = B.bone("lowerarm_l"), B.bone("hand_l")
    g = GM()
    g.append(gp.ring_at(E, Hd, 19.5, 5.2, 3.2, R_LIGHT, thick=0.9))
    g.append(gp.ring_at(E, Hd, 16.0, 5.6, 3.6, R_PLATE, thick=0.9))
    f = mc.frame_z(E, Hd)
    g.append(gp.ball(f.pt((0.0, 5.4, 21.0)), 0.8, R_ACCENT, nu=6, nv=4))
    k.pair("lowerarm", g)
    # thin black gloves
    gl = GM()
    fh = mc.frame_z(Hd, mc.add(Hd, mc.sub(Hd, E)))
    gl.ellipsoid((0.3, 0.0, 4.2), 3.0, 4.3, 6.0, R_CLOTH, nu=12, nv=7, f=fh)
    k.add("hand_l", gl)
    k.add("hand_r", gl.mirrored())
    # black trousers and shoes
    T, C, F = B.bone("thigh_l"), B.bone("calf_l"), B.bone("foot_l")
    k.pair("thigh", full_wrap(T, C, 2.0, 42.0, 12.2, 8.9, R_CLOTH, thick=0.7))
    k.pair("calf", full_wrap(C, F, 0.0, 39.0, 9.2, 6.6, R_CLOTH, thick=0.7, nv=7, bulge=calf_bulge(3.4)))
    sh = GM()
    sh.append(gp.box_at((F[0] + 7.5, F[1] - 0.6, F[2] - 3.6), (27.0, 10.6, 10.0), R_TRIM, ch=2.6, taper=0.72))
    k.add("foot_l", sh)
    k.add("foot_r", sh.mirrored())
    return k


# ------------------------------------------------------------------------------------------------ 42 Wildcard
def wildcard(B):
    k = Kit(B)
    zc = B.head_c[2]
    hd, H = gp.hood(B, role=R_CLOTH, margin=3.0, open_deg=50.0, back=0.42, z_bot=zc - 12.0, jaw=1.04)
    k.add("head", hd)
    # the blank mask: smooth and featureless
    Hm = gp.Helm(B, 0.0)
    m = GM()
    m.ellipsoid((Hm.front(zc) - 3.0, 0.0, zc + 0.3), 3.9, 7.4, 10.6, R_LIGHT, nu=16, nv=9, cut=(0.04, 0.96))
    k.add("head", m)
    # the worn scarf: a thick wrap round the neck, one end over the chest and one blowing behind
    k.add("spine_05", gp.collar_ring(B, z=146.5, r=10.4, h=8.0, role=R_TRIM, thick=2.6, cx_shift=-1.0))
    k.add("spine_05", gp.collar_ring(B, z=149.0, r=11.2, h=3.0, role=R_TRIM, thick=1.4, cx_shift=-1.0, tilt=8.0))
    k.add("spine_05", gp.hang(B.tpt(147.0, -36, 6.4), B.tpt(147.0, -14, 6.4), (0.12, 0.04, -1.0), 34.0, R_TRIM, out=(1, 0, 0), taper=0.8, bulge=1.0, ripple=0.3,
                              nu=4, nv=6, thick=0.8, hem=ragged(4, 0.18, 1.0)))
    k.add("spine_05", gp.hang(B.tpt(149.0, 160, 5.6), B.tpt(149.0, 186, 5.6), (-0.12, 0.06, -1.0), 44.0, R_TRIM, out=(-1, 0, 0), taper=0.75, ripple=1.0, waves=1.5,
                              nu=4, nv=7, thick=0.8, hem=ragged(4, 0.2, 2.0), sway=(-1.5, 1.5, 0.0)))
    # a capelet over the shoulders (ragged lower edge) and a long ragged cloak
    k.add("spine_05", gp.torso_plate(B, 133.0, 151.0, 0.0, 360.0, 3.4, 1.0, R_CLOTH, nu=24, nv=4, wrap=True, bot_fn=lambda u: 3.0 * (0.5 + 0.5 * SIN(u * 2 * math.pi * 7))))
    k.add("spine_05", gp.hang(B.tpt(149.0, -136, 3.4), B.tpt(149.0, 136, 3.4), (-0.18, 0.0, -1.0), 96.0, R_CLOTH, out=(-1, 0, 0), taper=1.3, bulge=2.6, ripple=1.8,
                              waves=2.0, nu=9, nv=10, thick=0.7, hem=ragged(6, 0.16, 0.5)))
    # a padded grey-green jacket and the one orange line, across the chest from the right shoulder to the left hip
    bul = gp.pec_bulge(1.0, 108, 136, 62)
    k.add("spine_05", gp.torso_plate(B, 104.0, 137.0, -62, 62, 1.5, 1.6, R_PLATE, nu=11, nv=6, w=0.12, bulge=bul))
    for z in (114.0, 122.0, 130.0):
        k.add("spine_05", gp.torso_plate(B, z - 0.5, z + 0.5, -56, 56, 2.6, 0.5, R_CLOTH, nu=9, nv=2, w=0.3, bulge=bul))
    k.add("spine_05", body_line(B, 131.0, 104.0, 40.0, -42.0, R_ACCENT, 2.9, thick=0.7, width=7.0, steps=12, bulge=bul))
    k.add("spine_05", gp.torso_plate(B, 104.0, 135.0, 120, 240, 1.4, 1.4, R_PLATE, nu=9, nv=5, w=0.15))
    # belt, straps and pouches in worn leather, a satchel on the left hip
    k.add("pelvis", belt(B, z0=95.0, z1=100.0, role=R_TRIM, buckle=R_PLATE, thick=1.1, buckle_w=5.0))
    cx = B.torso(98.0)[0]
    for s, yaw in ((-1, 14), (1, -14)):
        k.add("pelvis", pouch((cx + 4.0, s * 15.5, 95.0), (4.0, 6.0, 7.0), R_PLATE, R_TRIM, yaw=yaw))
    k.add("pelvis", pouch((cx - 6.0, -20.0, 89.0), (4.6, 12.0, 11.0), R_TRIM, R_PLATE, yaw=-90))
    T, C = B.bone("thigh_l"), B.bone("calf_l")
    tw = GM()
    tw.append(gp.ring_at(T, C, 12.0, 10.4, 2.0, R_TRIM, thick=0.8))
    tw.append(gp.tube_plate(T, C, 18.0, 30.0, 10.2, 9.4, 40, 130, 1.0, R_CLOTH, nu=5, nv=3, w=0.2, lo=0.5))
    k.pair("thigh", tw)
    # arm wraps and boots
    E, Hd = B.bone("lowerarm_l"), B.bone("hand_l")
    g = GM()
    g.append(gp.bracer(B, flare=1.15, thick=0.9, s0=6, s1=23, rings=False, role=R_CLOTH))
    for j in range(4):
        g.append(gp.ring_at(E, Hd, 8.0 + j * 4.2, 5.7 - j * 0.25, 1.3, R_TRIM, thick=0.6, grow=0.3))
    k.pair("lowerarm", g)
    k.pair("upperarm", gp.pauldron(B, big=0.95, layers=1, dome=False, lame_role=R_PLATE, thick=1.0, alpha=48))
    k.pair("calf", gp.merge(kneepad(B, role=R_PLATE, strap=R_TRIM, size=1.0),
                            gp.greave(B, role=R_CLOTH, trim_role=R_TRIM, thick=1.0, s0=18.0, s1=37.0, knee=False, arc=(-150, 150)),
                            gp.ring_at(B.bone("calf_l"), B.bone("foot_l"), 24.0, 7.0, 1.4, R_TRIM, thick=0.6)))
    return k


# ------------------------------------------------------------------------------------------------ 43 Gino Gasket
def _moustache(H, zc):
    """A big fan of rounded lobes under the nose."""
    m = GM()
    c = (H.front(zc - 4.0) + 1.4, 0.0, zc - 4.2)
    m.ellipsoid(c, 2.4, 3.6, 2.2, R_GLOW, nu=10, nv=6)
    n = 7
    for i in range(n):
        t = i / float(n - 1)
        a = rad(-82.0 + 164.0 * t)
        L = 7.6 + 1.6 * abs(2 * t - 1)
        d = (0.18, SIN(a), -COS(a) * 0.8)
        dn = mc.norm(d)
        p0 = mc.add(c, mc.mul(dn, 1.0))
        p1 = mc.add(c, mc.mul(dn, L * 0.55))
        tip = mc.add(c, mc.mul(dn, L))
        curl = abs(2 * t - 1)                       # the outer lobes curl up at the ends
        tip = (tip[0] - 0.6 * curl, tip[1], tip[2] + 2.6 * curl * curl)
        m.sweep([p0, p1, tip], [1.8, 2.2, 0.95], R_GLOW, sides=6)
    return m


def _wrench(c, s, role=R_TRIM, roll=0.0):
    """A pipe wrench seen from the front (in the y-z plane at x = c[0]): handle, hook jaw and the adjusting nut."""
    m = GM()
    f = fr(c, roll=roll)
    m.box((0.0, 0.0, -1.0 * s), (0.6 * s, 0.95 * s, 4.6 * s), role, ch=0.2 * s, f=f)
    m.box((0.0, 0.25 * s, 1.75 * s), (0.6 * s, 2.0 * s, 0.85 * s), role, ch=0.2 * s, f=f)
    m.box((0.0, 0.95 * s, 1.1 * s), (0.6 * s, 0.7 * s, 1.5 * s), role, ch=0.15 * s, f=f)
    m.box((0.0, -0.05 * s, 0.75 * s), (0.7 * s, 1.25 * s, 0.6 * s), role, ch=0.15 * s, f=f)
    return m


def gino(B):
    k = Kit(B)
    zc = B.head_c[2]
    # the face: a round skin head, ears, a big nose, eyes and bushy brows
    Hs = gp.Helm(B, 1.4, z_bot=zc - 12.0, jaw=0.95)
    k.add("head", Hs.shell(R_CLOTH, sides=16, caps=(False, True)))
    for s in (-1, 1):
        k.add("head", gp.ball((Hs.cx + 0.5, s * (Hs.side(zc) + 0.3), zc), 2.6, R_CLOTH, nu=8, nv=5, sy=0.5, sz=1.2))
    k.add("head", gp.ball((Hs.front(zc - 2.0) + 2.0, 0.0, zc - 2.0), 3.4, R_CLOTH, nu=12, nv=8, sy=0.95, sz=0.9))
    for s in (-1, 1):
        e = (Hs.front(zc + 3.4) - 0.5, s * 3.8, zc + 3.4)
        k.add("head", gp.ball(e, 1.35, R_LIGHT, nu=8, nv=6, sy=1.25, sz=1.75))
        k.add("head", gp.ball((e[0] + 1.1, e[1] - s * 0.2, e[2] - 0.3), 0.8, R_GLOW, nu=6, nv=4, sz=1.3))
        k.add("head", gp.box_at((Hs.front(zc + 6.6) + 0.2, s * 4.0, zc + 6.6), (1.6, 4.8, 1.5), R_GLOW, ch=0.55, roll=-s * 12))
    k.add("head", _moustache(Hs, zc - 0.8))
    # the neck
    nk = B.bone("neck_01")
    k.add("spine_05", gp.cyl((nk[0] + 0.6, 0.0, 146.0), (nk[0] + 1.2, 0.0, 158.0), 6.4, R_CLOTH, sides=12, caps=(False, False)))
    # hair below the cap at the back and the sides
    k.add("head", Hs.shell(R_GLOW, sides=10, z_bot=zc - 5.0, arc=(105.0, 255.0), extra=0.6))
    for s in (-1, 1):
        k.add("head", gp.box_at((Hs.cx + 1.6, s * (Hs.side(zc + 1.0) + 0.4), zc + 1.0), (3.0, 1.2, 5.5), R_GLOW, ch=0.4))
    # the red cap: a puffy crown, a band and a rounded brim; the badge is a white hex nut with a brass pipe wrench
    Hc = gp.Helm(B, 2.2, z_eq=zc + 7.5, z_bot=zc + 7.6, jaw=1.0, top=zc + 19.5)    # z_eq at the rim: the cap is a dome with no skirt
    k.add("head", Hc.shell(R_ACCENT, sides=16, z_bot=zc + 7.6, caps=(False, True), rfn=lambda th, t: 1.0 + 0.06 * t * (1.0 + COS(th))))
    k.add("head", band_head(Hc, zc + 8.6, 2.2, R_ACCENT, off=0.2))
    k.add("head", _brim(Hc, zc + 4.0))
    bp = (Hc.front(zc + 12.6) + 0.6, 0.0, zc + 12.6)
    k.add("head", gp.cyl((bp[0] - 0.6, 0.0, bp[2]), (bp[0] + 0.5, 0.0, bp[2]), 3.5, R_LIGHT, sides=6))
    k.add("head", _wrench((bp[0] + 0.7, 0.0, bp[2] + 0.2), 1.05, roll=-35.0))
    k.add("head", gp.ball((Hc.cx, 0.0, Hc.z_top + 0.3), 1.1, R_ACCENT, nu=8, nv=5, sz=0.5))
    # the neckerchief in the team colour
    k.add("spine_05", gp.collar_ring(B, z=148.5, r=8.6, h=3.0, role=R_TEAM, thick=1.4))
    k.add("spine_05", gp.hang(B.tpt(148.5, -22, 1.6), B.tpt(148.5, 22, 1.6), (0.3, 0.0, -1.0), 10.0, R_TEAM, out=(1, 0, 0), taper=0.08, nu=5, nv=4, thick=0.6))
    # stocky: a round belly under the overalls, the bib with a pocket, straps and big brass buttons
    def belly(ang, z):
        f = max(0.0, COS(rad(ang))) ** 1.4
        return 1.2 + 4.6 * f * max(0.0, SIN(math.pi * (z - 96.0) / 40.0)) ** 0.9
    k.add("spine_05", gp.torso_plate(B, 96.0, 136.0, 0.0, 360.0, 1.2, 1.2, R_PLATE, nu=22, nv=6, wrap=True, bulge=belly))
    k.add("spine_05", gp.torso_plate(B, 112.0, 141.0, -34, 34, 3.0, 1.0, R_PLATE, nu=9, nv=6, w=0.12,
                                     bulge=lambda a, z: belly(a, min(z, 136.0)) if z < 136.0 else belly(a, 136.0) * 0.6))
    k.add("spine_05", gp.torso_plate(B, 118.0, 128.0, -14, 14, 3.8, 0.8, R_PLATE, nu=5, nv=3, w=0.2, bulge=belly))
    k.add("spine_05", gp.torso_plate(B, 127.2, 128.4, -14, 14, 4.4, 0.5, R_TRIM, nu=5, nv=2, w=0.3, bulge=belly))
    strap = GM()
    strap.append(body_line(B, 151.0, 139.0, -50, -24, R_PLATE, 1.6, thick=1.2, width=9.0, steps=4))
    strap.append(gp.torso_plate(B, 148.0, 152.5, -132, -48, 1.6, 1.2, R_PLATE, nu=6, nv=2, w=0.25))
    strap.append(body_line(B, 151.0, 104.0, -134, -212, R_PLATE, 1.7, thick=1.2, width=9.0, steps=9))     # crosses the other strap on the back
    k.add("spine_05", strap)
    k.add("spine_05", strap.mirrored())
    for s in (-1, 1):
        p = B.tpt(139.5, s * 26.0, 4.6)
        k.add("spine_05", gp.cyl((p[0] - 0.4, p[1], p[2]), (p[0] + 1.3, p[1], p[2]), 2.3, R_TRIM, sides=14))
        k.add("spine_05", gp.cyl((p[0] + 1.2, p[1], p[2]), (p[0] + 1.6, p[1], p[2]), 1.3, R_PLATE, sides=10))
    # the tool belt: brown leather, brass buckle, pouches, a pipe wrench on the right, a hammer on the left, a plunger behind
    k.add("pelvis", belt(B, z0=94.0, z1=100.0, role=R_GLOW, buckle=R_TRIM, off_=2.2, thick=1.6, buckle_w=7.0))
    cx = B.torso(97.0)[0]
    for s, yaw in ((-1, 16), (1, -16)):
        k.add("pelvis", pouch((cx + 3.0, s * 17.5, 93.0), (4.6, 6.4, 8.0), R_GLOW, R_TRIM, yaw=yaw))
    wr = GM()
    wr.append(gp.cyl((cx - 4.0, 21.5, 96.0), (cx - 4.6, 22.6, 78.0), 1.0, R_TRIM, sides=8))
    wr.append(gp.box_at((cx - 4.0, 21.6, 98.5), (2.6, 2.2, 3.6), R_TRIM, ch=0.4))
    wr.append(gp.box_at((cx - 1.8, 21.6, 100.4), (3.4, 2.0, 1.4), R_TRIM, ch=0.3))
    k.add("pelvis", wr)
    hm = GM()
    hm.append(gp.cyl((cx - 3.0, -21.5, 97.0), (cx - 3.6, -22.6, 80.0), 0.9, R_GLOW, sides=8))
    hm.append(gp.box_at((cx - 3.0, -21.6, 98.0), (7.0, 2.4, 2.6), R_TRIM, ch=0.5))
    k.add("pelvis", hm)
    bx = back_x(B, 97.0)
    k.add("pelvis", gp.cyl((bx - 2.5, -9.0, 98.0), (bx - 5.5, -14.0, 124.0), 0.9, R_GLOW, sides=8))
    pl = GM()
    pl.lathe([(0.0, 0.0), (4.2, 0.0), (4.4, 1.5), (3.4, 4.6), (1.2, 6.0), (0.9, 6.0)], R_ACCENT, sides=16, f=mc.frame_z((bx - 2.0, -8.2, 92.0), (bx - 2.5, -9.0, 98.0)),
             caps=(False, True))
    k.add("pelvis", pl)
    # sleeves: a puffy striped shirt sleeve on the upper arm, rolled up; bare forearms and big white gloves
    J, E, Hd = B.bone("upperarm_l"), B.bone("lowerarm_l"), B.bone("hand_l")
    sl = GM()
    sl.append(gp.ball(mc.add(J, (0.0, -1.5, 2.5)), 7.6, R_TEAM, nu=10, nv=6))
    for j in range(5):
        sl.append(gp.ring_at(J, E, 2.0 + j * 3.6, 7.9 - 0.25 * j, 3.6, R_TEAM if j % 2 == 0 else R_LIGHT, thick=1.6, sides=12))
    sl.append(gp.ring_at(J, E, 19.6, 7.0, 2.6, R_LIGHT, thick=1.8, grow=0.4))
    sl.append(full_wrap(J, E, 20.0, 29.0, 6.0, 5.4, R_CLOTH, thick=0.5, nv=3, nu=12))
    k.pair("upperarm", sl)
    fa = GM()
    fa.append(full_wrap(E, Hd, -1.0, 21.0, 5.8, 4.6, R_CLOTH, thick=0.5, nv=4, nu=12))
    fa.append(gp.ring_at(E, Hd, 18.0, 5.0, 3.6, R_LIGHT, thick=1.0, grow=2.4))
    k.pair("lowerarm", fa)
    gl = GM()
    f = mc.frame_z(Hd, mc.add(Hd, mc.sub(Hd, E)))
    gl.ellipsoid((0.6, 0.0, 7.6), 5.0, 5.6, 9.6, R_LIGHT, nu=12, nv=7, f=f)
    gl.ellipsoid((3.4, -4.2, 3.2), 2.1, 2.1, 3.8, R_LIGHT, nu=8, nv=5, f=f)
    k.add("hand_l", gl)
    k.add("hand_r", gl.mirrored())
    # baggy overall trousers with rolled cuffs, a knee patch, big brown boots
    T, C, F = B.bone("thigh_l"), B.bone("calf_l"), B.bone("foot_l")
    k.pair("thigh", full_wrap(T, C, 0.0, 42.0, 11.4, 9.0, R_PLATE, thick=1.0))
    cv = GM()
    cv.append(full_wrap(C, F, -1.0, 34.0, 10.0, 8.4, R_PLATE, thick=1.0, nv=6, bulge=calf_bulge(1.8)))
    cv.append(gp.ring_at(C, F, 29.6, 9.6, 4.8, R_PLATE, thick=1.6, grow=0.3))
    cv.append(gp.ring_at(C, F, 32.2, 10.2, 0.8, R_LIGHT, thick=0.5))
    cv.append(gp.tube_plate(C, F, -1.0, 8.0, 11.0, 10.6, -32, 32, 0.6, R_GLOW, nu=4, nv=3, w=0.2, lo=0.5))
    k.pair("calf", cv)
    bt = GM()
    bt.append(gp.box_at((F[0] + 5.5, F[1] - 0.6, F[2] - 2.8), (27.0, 12.6, 11.0), R_GLOW, ch=3.2, taper=0.92))
    bt.ellipsoid((F[0] + 14.5, F[1] - 0.6, F[2] - 3.2), 7.2, 6.8, 5.6, R_GLOW, nu=10, nv=6)
    bt.append(gp.box_at((F[0] + 6.0, F[1] - 0.6, F[2] - 7.8), (29.0, 13.4, 1.8), R_TRIM, ch=0.6))
    bt.append(gp.ring_at(F, mc.add(F, (0.0, 0.0, 10.0)), 0.5, 7.2, 3.2, R_GLOW, thick=1.4))
    k.add("foot_l", bt)
    k.add("foot_r", bt.mirrored())
    return k


def _brim(Hc, zc):
    """A rounded duck-bill brim at the front of the cap."""
    m = GM()
    z = zc + 3.9
    c = (Hc.front(z) + 1.6, 0.0, z - 0.4)
    m.ellipsoid(c, 7.4, 9.6, 1.1, R_ACCENT, nu=16, nv=5)
    return m
