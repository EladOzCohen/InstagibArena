"""Gear of characters 0-4: Bulwark, Vesper, Khet, Razorclaw, Cinder. Each function takes the Body and returns a gear_parts.Kit."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_parts import Kit, back_x, front_x, rad, SIN, COS
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT, fr


def belt(B, z0=96.5, z1=102.5, role=R_TRIM, off_=1.0, thick=1.2, buckle=R_ACCENT, buckle_w=7.0):
    m = GM()
    m.append(gp.torso_plate(B, z0, z1, 0.0, 360.0, off_, thick, role, nu=22, nv=3, wrap=True, w=0.25))
    if buckle is not None:
        x = front_x(B, (z0 + z1) / 2, off_ + thick)
        m.box((x + 0.2, 0.0, (z0 + z1) / 2), (1.6, buckle_w, z1 - z0 + 1.2), buckle, ch=0.5)
    return m


def hip_pods(B, role=R_PLATE, size=(12.0, 3.0, 15.0), z=91.0, y=17.2, tilt=14.0):
    m = GM()
    cx = B.torso(z)[0]
    m.box((cx, -y, z), size, role, ch=1.0, f=fr((0, 0, 0), roll=-tilt) if False else mc.IDENT)
    return m


def thigh_plate(B, role=R_PLATE, s0=9.0, s1=34.0, thick=1.2, arc=(-75.0, 75.0), r0=10.6, r1=9.0):
    P0, P1 = B.bone("thigh_l"), B.bone("calf_l")
    return gp.tube_plate(P0, P1, s0, s1, r0, r1, arc[0], arc[1], thick, role, nv=5, nu=9, w=0.12, lo=0.4)


# ------------------------------------------------------------------------------------------------ 0 Bulwark
def bulwark(B):
    k = Kit(B)
    zc = B.head_c[2]
    k.add("head", gp.helm_full(B, margin=2.0, slit_w=11.0, fin=3.8, jaw=0.92))
    k.add("spine_05", gp.collar_ring(B, z=149.5, r=8.8, h=4.4, thick=1.6))
    z0, z1, span = 118.0, 150.0, 68.0
    k.add("spine_05", gp.cuirass(B, off_=1.9, thick=2.1, span=span, bulge=2.6, vneck=7, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 132.5, 137.0, -52, 52, 1.9 + 1.9, 1.0, R_TEAM, bulge=gp.pec_bulge(2.6, z0, z1, span), nu=11, nv=2, w=0.3))
    bx = back_x(B, 132)
    k.add("spine_05", gp.box_at((bx - 5.0, 0, 132), (11, 25, 29), R_PLATE, ch=1.4))
    for s in (-1, 1):
        k.add("spine_05", gp.cyl((bx - 7.0, s * 8.5, 120), (bx - 7.0, s * 8.5, 142), 3.3, R_TRIM, sides=10))
    k.add("spine_05", gp.box_at((bx - 10.6, 0, 140), (2.0, 21, 3.6), R_ACCENT, ch=0.5))
    p = gp.pauldron(B, big=1.4, layers=3, top_role=R_TEAM, lame_role=R_PLATE, thick=1.5, ridge=1.3, alpha=46)
    k.pair("upperarm", p)
    k.pair("lowerarm", gp.bracer(B, flare=1.4, accent=R_ACCENT, thick=1.3, s0=3, s1=23, rings=True))
    k.add("pelvis", belt(B))
    cx = B.torso(92)[0]
    for s in (-1, 1):
        k.add("pelvis", gp.box_at((cx + 1.0, s * 17.8, 90.5), (11.0, 3.2, 16.0), R_PLATE, ch=1.0, roll=s * 8))
    k.add("pelvis", gp.torso_plate(B, 80.0, 96.5, -28, 28, 0.8, 1.4, R_PLATE, bot_fn=lambda u: 5.0 * (1 - math.sin(math.pi * u)) * 0.8 + 2.0, nu=7, nv=4))
    k.pair("thigh", thigh_plate(B, thick=1.5))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.5, s1=37.0))
    return k


# ------------------------------------------------------------------------------------------------ 1 Vesper
def vesper(B):
    k = Kit(B)
    H = gp.Helm(B, 1.5, jaw=0.9)
    zc = B.head_c[2]
    k.add("head", gp.helm_full(B, margin=1.5, slit_w=14.0, slit_h=2.7, brow=False, cheek=False, chin=False, vents=False, fin=6.5, jaw=0.9))
    # antenna on the right side of the helmet, leaning back
    p0 = (H.cx - 1.0, 7.4, zc + 7.0)
    k.add("head", gp.horn(p0, (H.cx - 7.0, 9.8, zc + 24.0), (H.cx - 17.0, 11.5, zc + 41.0), 0.75, R_ACCENT, n=8, sides=5, taper=0.25))
    k.add("head", gp.ball((H.cx - 17.0, 11.5, zc + 41.0), 1.1, R_GLOW, nu=6, nv=4))
    z0, z1, span = 120.0, 148.0, 48.0
    k.add("spine_05", gp.cuirass(B, off_=1.1, thick=1.2, span=span, bulge=1.1, vneck=13.0, z0=z0, z1=z1, panel=False, back=True))
    k.add("spine_05", gp.torso_plate(B, 123.0, 143.0, -4.5, 4.5, 1.1 + 1.0, 0.8, R_TEAM, bulge=gp.pec_bulge(1.1, z0, z1, span), nu=3, nv=5, w=0.3))
    k.add("spine_05", gp.collar_ring(B, z=149.5, r=6.8, h=3.0, thick=1.0))
    bx = back_x(B, 136)
    k.add("spine_05", gp.box_at((bx - 2.6, 0, 136), (2.2, 3.4, 30), R_ACCENT, ch=0.5, pitch=-6, taper=0.45))
    k.add("spine_05", gp.box_at((bx - 3.6, 0, 126), (5.0, 18, 10), R_TRIM, ch=1.0))
    left = gp.pauldron(B, big=1.2, layers=2, top_role=R_PLATE, lame_role=R_PLATE, alpha=54, thick=1.0, ridge=0.8)
    right = gp.pauldron(B, big=0.78, layers=1, top_role=R_PLATE, lame_role=R_PLATE, alpha=50, thick=0.9)
    k.add("upperarm_l", left)
    k.add("upperarm_r", right.mirrored())
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    br = gp.bracer(B, flare=0.88, accent=R_ACCENT, thick=0.8, s0=5, s1=21)
    f = mc.frame_x(P0, P1)
    blade = GM()
    blade.box((26.0, 0.0, 5.0), (40.0, 0.8, 3.6), R_ACCENT, ch=0.3, f=f, taper=0.12)
    br.append(blade)
    k.pair("lowerarm", br)
    # a long tail of cloth on the left hip and a short one at the back
    a, b = B.tpt(101, -92, 1.5), B.tpt(101, -140, 1.5)
    k.add("pelvis", gp.hang(a, b, (0.05, -0.1, -1.0), 40.0, R_CLOTH, out=(0, -1, 0), taper=0.55, ripple=1.6, waves=1.5, hem=lambda u: 0.75 + 0.25 * u, nu=6, nv=6))
    k.add("pelvis", belt(B, role=R_TRIM, buckle=R_TEAM, buckle_w=5.0, thick=1.0))
    k.pair("calf", gp.greave(B, thick=0.9, knee=False, s1=35.0, arc=(-80, 80)))
    return k


# ------------------------------------------------------------------------------------------------ 2 Khet
def khet(B):
    k = Kit(B)
    H = gp.Helm(B, 2.2, z_bot=B.head_c[2] - 3.0, jaw=1.0, cx_shift=-1.2)
    zc = B.head_c[2]
    # striped nemes: the dome in 8 wedges of alternating colours, the sides below the brow only at the back
    roles = [R_ACCENT, R_TEAM]
    zb = zc + 5.5
    for i in range(8):
        a0, a1 = i * 45.0, (i + 1) * 45.0
        k.add("head", H.shell(roles[i % 2], sides=3, z_bot=zb, arc=(a0, a1)))
    # lower cloth of the headdress: back and sides (open at the face)
    lo = GM()
    lo.lathe([(H.r(zc - 3.0), zc - 3.0), (H.r(zc + 1.0), zc + 1.0), (H.r(zb), zb)], R_PLATE, sides=14, f=fr((H.cx, 0, 0)), sy=H.sy,
             caps=(False, False), arc=(72.0, 288.0))
    k.add("head", lo)
    k.add("head", band_head(H, zc + 5.7, 1.8, R_ACCENT))
    k.add("head", gp.horn((H.front(zc + 8) + 0.2, 0, zc + 7.5), (H.front(zc + 8) + 3.0, 0, zc + 11.5), (H.front(zc + 8) + 1.0, 0, zc + 15.5), 1.3, R_ACCENT, n=6, sides=6))
    k.add("head", gp.box_at((H.front(zc - 9) - 0.5, 0, zc - 11.5), (3.0, 3.4, 8.0), R_ACCENT, ch=0.7, pitch=-8, taper=0.6))
    # lappets hanging in front of the shoulders
    for sgn in (-1, 1):
        for j, role in enumerate((R_ACCENT, R_TEAM, R_ACCENT)):
            a = (H.cx + 3.5 + j * 0.2, sgn * (H.side(zc) + 0.8 + j * 1.9), zc - 2.0)
            b = (H.cx + 3.5 + j * 0.2, sgn * (H.side(zc) + 2.6 + j * 1.9), zc - 2.0)
            k.add("head", gp.hang(a, b, (0.18, sgn * 0.12, -1.0), 24.0 - j * 0.0, role, out=(1, 0, 0), taper=0.9, nu=2, nv=5, thick=0.6))
    # broad collar: bands of gold, team colour and teal
    bands = [(7.5, 11.0, R_ACCENT), (11.0, 14.0, R_TEAM), (14.0, 17.0, R_ACCENT), (17.0, 19.6, R_PLATE), (19.6, 22.0, R_ACCENT)]
    for (r0, r1, role) in bands:
        z0_ = 152.0 - (r0 - 7.5) * 0.45
        z1_ = 152.0 - (r1 - 7.5) * 0.45 - 0.6
        m = GM()
        m.lathe([(r0 + 0.0, z0_), (r1, z1_)], role, sides=26, f=fr((B.torso(150)[0] - 1.2, 0, 0)), sy=1.3, caps=(False, False))
        k.add("spine_05", m)
    k.pair("upperarm", ring_pair(B, "upperarm_l", "lowerarm_l", 9.0, 7.4, 3.2, R_ACCENT, 2))
    k.pair("lowerarm", gp.bracer(B, flare=1.12, role=R_ACCENT, trim_role=R_TEAM, thick=1.0, s0=2, s1=24, arc=(0, 360), rings=True))
    k.add("pelvis", belt(B, role=R_ACCENT, buckle=R_TEAM, buckle_w=6.0))
    a, b = B.tpt(98, -38, 1.0), B.tpt(98, 38, 1.0)
    k.add("pelvis", gp.hang(a, b, (0.35, 0.0, -1.0), 38.0, R_LIGHT, out=(1, 0, 0), taper=1.4, bulge=1.0, ripple=0.7, waves=5.0, nu=15, nv=6))
    a2, b2 = B.tpt(98, -7, 2.2), B.tpt(98, 7, 2.2)
    k.add("pelvis", gp.hang(a2, b2, (0.35, 0.0, -1.0), 36.0, R_TEAM, out=(1, 0, 0), taper=1.6, bulge=1.0, nu=3, nv=5))
    k.pair("calf", gp.greave(B, role=R_ACCENT, trim_role=R_TEAM, knee=False, s0=18.0, s1=36.0, thick=0.9, arc=(-180, 180)) if False else ring_pair(B, "calf_l", "foot_l", 28.0, 6.4, 5.5, R_ACCENT, 1))
    return k


def band_head(H, z, h, role, off=0.6):
    m = GM()
    r = H.r(z) + off
    m.lathe([(r, z - h / 2), (r + 0.7, z - h / 2), (r + 0.7, z + h / 2), (r, z + h / 2), (r, z - h / 2)], role, sides=22, f=fr((H.cx, 0, 0)), sy=H.sy, creases=(1, 2, 3),
            caps=(False, False))
    return m


def ring_pair(B, bone0, bone1, s, r, h, role, n=1, gap=4.0, thick=1.0):
    """Ring(s) around a limb for the left side: n rings from s, spaced by gap."""
    P0, P1 = B.bone(bone0), B.bone(bone1)
    m = GM()
    for i in range(n):
        m.append(gp.ring_at(P0, P1, s + i * gap, r, h, role, thick=thick))
    return m


# ------------------------------------------------------------------------------------------------ 3 Razorclaw
def razorclaw(B):
    k = Kit(B)
    H = gp.Helm(B, 0.9, jaw=1.0)
    zc = B.head_c[2]
    # crest: spikes over the skull from the forehead to the back of the head
    lens = [5.0, 8.5, 12.0, 11.0, 8.5, 5.5]
    for i, L in enumerate(lens):
        ph = 62.0 + i * 17.0
        x = H.cx + H.rx * 0.96 * COS(rad(ph))
        z = H.z_eq + (H.z_top - H.z_eq) * SIN(rad(ph)) * 0.98
        n = (COS(rad(ph)), 0.0, SIN(rad(ph)))
        d = mc.norm((n[0] - 0.75, 0.0, n[2] + 0.1))
        base = (x, 0.0, z)
        k.add("head", gp.spike(mc.add(base, mc.mul(n, -0.6)), mc.add(base, mc.mul(d, L)), 1.5, R_ACCENT, sides=6))
    for s in (-1, 1):
        k.add("head", gp.box_at((H.front(zc + 4.5) - 1.0, s * 4.4, zc + 4.7), (4.0, 7.0, 1.8), R_TRIM, ch=0.6, yaw=s * 14, pitch=-10))
        k.add("head", gp.spike((H.cx - 1.0, s * (H.side(zc - 4) + 0.4), zc - 4), (H.cx - 7.0, s * (H.side(zc - 4) + 5.0), zc - 9.0), 1.4, R_ACCENT, sides=6))
        k.add("head", gp.spike((H.cx + 6.0, s * (H.side(zc - 6) + 0.2), zc - 7), (H.cx + 8.0, s * (H.side(zc - 6) + 4.8), zc - 12.0), 1.1, R_ACCENT, sides=5))
    # dorsal spines down the back
    for i in range(6):
        z = 150.0 - i * 6.2
        x = back_x(B, z, 0.5)
        L = 9.0 + 6.0 * math.sin(math.pi * (i + 0.5) / 6.0)
        k.add("spine_05", gp.spike((x + 0.5, 0, z), (x - L * 0.8, 0, z + L * 0.55), 2.0 + 0.5 * math.sin(math.pi * (i + 0.5) / 6.0), R_ACCENT, sides=6))
    # bone ribs on the chest
    for j, z in enumerate((125.0, 131.0, 137.0)):
        k.add("spine_05", gp.torso_plate(B, z - 1.2, z + 1.2, -44 + j * 3, 44 - j * 3, 1.3, 1.0, R_TRIM, nu=9, nv=2, w=0.35,
                                         bulge=gp.pec_bulge(1.2, 118, 148, 52)))
    k.add("spine_05", gp.torso_plate(B, 119, 148, 150, 210, 1.2, 1.2, R_TRIM, nu=7, nv=5, w=0.2))
    k.pair("upperarm", gp.pauldron(B, big=0.95, layers=2, top_role=R_TRIM, lame_role=R_TRIM, spike=10.0, spike_role=R_ACCENT, thick=1.1, alpha=44))
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    br = gp.bracer(B, flare=1.0, role=R_TRIM, trim_role=R_ACCENT, thick=0.9, s0=4, s1=19, rings=True)
    f = mc.frame_x(P0, P1)
    pts = [f.pt((12.0, 0.0, 4.6)), f.pt((30.0, 0.0, 9.0)), f.pt((46.0, 0.0, 3.0))]
    br.append(gp.horn(pts[0], pts[1], pts[2], 2.2, R_ACCENT, n=8, sides=5, sy=0.45))
    k.pair("lowerarm", br)
    # claws on the fingers
    for (fx, fy, fz) in ((26.5, -51.0, 93.5), (24.8, -52.8, 92.0), (19.0, -54.6, 92.2)):
        cl = gp.horn((fx, fy, fz), (fx + 2.5, fy - 0.2, fz - 3.5), (fx + 2.5, fy - 0.4, fz - 9.5), 1.0, R_ACCENT, n=5, sides=5)
        k.add("hand_l", cl)
        k.add("hand_r", cl.mirrored())
    # calf spurs and knee spikes
    c0 = B.bone("calf_l")
    sp = GM()
    sp.append(gp.horn((c0[0] - 4.5, c0[1] - 0.5, c0[2] - 14.0), (c0[0] - 10.0, c0[1] - 0.5, c0[2] - 17.0), (c0[0] - 16.0, c0[1] - 0.5, c0[2] - 15.0), 1.9, R_ACCENT, n=6, sides=6))
    sp.append(gp.spike((c0[0] + 8.0, c0[1] - 0.5, c0[2] + 1.0), (c0[0] + 14.0, c0[1] - 0.5, c0[2] + 5.0), 2.0, R_ACCENT, sides=6))
    k.pair("calf", sp)
    # tail
    pelv = B.bone("pelvis")
    path = [(pelv[0] - 8, 0, pelv[2] + 1), (pelv[0] - 17, 0, pelv[2] - 5), (pelv[0] - 30, 0, pelv[2] - 18), (pelv[0] - 43, 0, pelv[2] - 38), (pelv[0] - 49, 0, pelv[2] - 52)]
    k.add("pelvis", gp.merge(_sweep(path, [4.2, 3.6, 2.7, 1.6, 0.8], R_CLOTH, 8)))
    k.add("pelvis", gp.spike(path[-1], (path[-1][0] - 3, 0, path[-1][2] - 11.0), 1.7, R_ACCENT, sides=6))
    return k


def _sweep(path, radii, role, sides=8, sy=1.0):
    m = GM()
    m.sweep(path, radii, role, sides=sides, sy=sy)
    return m


# ------------------------------------------------------------------------------------------------ 4 Cinder
def cinder(B):
    k = Kit(B)
    H = gp.Helm(B, 1.6)
    zc = B.head_c[2]
    k.add("head", gp.box_at((H.cx + 0.5, 0, zc + 0.5), (H.rx * 2 + 1.0, H.ry * 2 + 2.6, H.rz * 2 - 2.0), R_PLATE, ch=2.4))
    fx = H.cx + H.rx + 0.5
    g = fr((fx, 0, zc + 1.8), pitch=-90)
    m = GM()
    m.lathe([(0.0, 0.0), (3.9, 0.0), (3.9, 1.6), (3.2, 1.9), (3.0, 1.9)], R_TRIM, sides=14, f=g, creases=(2,), caps=(False, False))
    m.lathe([(0.0, 1.8), (2.9, 1.8), (2.3, 2.3), (0.0, 2.5)], R_GLOW, sides=14, f=g, caps=(False, False))
    k.add("head", m)
    for sgn in (-1, 1):
        for j in range(3):
            k.add("head", gp.box_at((H.cx - 1.0, sgn * (H.ry + 1.6), zc - 2.5 + j * 2.4), (7.0, 0.9, 1.0), R_TRIM, ch=0.25))
    k.add("head", gp.cyl((H.cx - 3.0, 4.0, zc + H.rz - 1.0), (H.cx - 3.0, 4.0, zc + H.rz + 9.0), 0.7, R_TRIM, sides=6))
    k.add("head", gp.cyl((H.cx - 3.0, 4.0, zc + H.rz + 8.0), (H.cx - 3.0, 4.0, zc + H.rz + 10.2), 1.1, R_ACCENT, sides=6))
    k.add("head", gp.cyl((H.cx - 1.5, 0, zc - 11.0), (H.cx - 1.5, 0, zc - 2.0), 4.6, R_TRIM, sides=10))
    # chest block with a round reactor housing
    xf = front_x(B, 133.0, 0.5)
    k.add("spine_05", gp.box_at((xf + 3.0, 0, 134.5), (10.0, 31.0, 25.0), R_PLATE, ch=2.0))
    g2 = fr((xf + 8.1, 0, 135.0), pitch=-90)
    c = GM()
    c.lathe([(0.0, 0.0), (7.0, 0.0), (7.0, 1.8), (5.6, 2.4), (5.2, 2.4)], R_TRIM, sides=16, f=g2, creases=(2,), caps=(False, False))
    c.lathe([(0.0, 2.3), (4.6, 2.3), (3.6, 3.0), (0.0, 3.3)], R_GLOW, sides=16, f=g2, caps=(False, False))
    k.add("spine_05", c)
    k.add("spine_05", gp.box_at((xf + 3.0, 0, 120.5), (8.5, 28.0, 4.0), R_ACCENT, ch=1.0))
    k.add("spine_05", gp.box_at((back_x(B, 132, 0) - 4.0, 0, 134.0), (8.0, 28.0, 26.0), R_PLATE, ch=1.8))
    for s in (-1, 1):
        x = back_x(B, 130, 8.5)
        k.add("spine_05", gp.cyl((x, s * 9.5, 118), (x, s * 9.5, 150), 3.6, R_TRIM, sides=10))
        for z in (124.0, 136.0, 147.0):
            k.add("spine_05", gp.cyl((x, s * 9.5, z), (x, s * 9.5, z + 1.8), 4.2, R_ACCENT, sides=10))
    # shoulder joints, blocky pauldrons, pistons
    J, E = B.bone("upperarm_l"), B.bone("lowerarm_l")
    sh = GM()
    sh.append(gp.ball(J, 6.6, R_TRIM, nu=12, nv=7))
    sh.append(gp.box_at((J[0], J[1] - 3.8, J[2] + 5.4), (15.0, 15.0, 8.0), R_PLATE, ch=1.8, roll=48))
    sh.append(gp.box_at((J[0], J[1] - 5.2, J[2] + 6.4), (15.4, 4.0, 8.4), R_ACCENT, ch=1.0, roll=48))
    d = mc.norm(mc.sub(E, J))
    off = (6.6, 0, 0)
    sh.append(gp.cyl(mc.add(mc.add(J, off), (0, 0, -6)), mc.add(mc.add(E, off), (0, 0, 8)), 2.2, R_TRIM, sides=8))
    sh.append(gp.ring_at(mc.add(J, off), mc.add(E, off), 8, 3.0, 2.4, R_ACCENT, thick=0.7))
    k.pair("upperarm", sh)
    fa = gp.bracer(B, flare=1.18, role=R_PLATE, trim_role=R_TRIM, accent=R_ACCENT, thick=1.6, s0=3, s1=22, arc=(0, 360))
    k.pair("lowerarm", fa)
    k.add("pelvis", belt(B, role=R_PLATE, buckle=R_ACCENT, thick=1.8, z0=96.0, z1=104.0, buckle_w=9))
    cx = B.torso(92)[0]
    for s in (-1, 1):
        k.add("pelvis", gp.box_at((cx + 0.5, s * 17.0, 90.0), (13.0, 5.0, 16.0), R_TRIM, ch=1.4))
    P0, P1 = B.bone("thigh_l"), B.bone("calf_l")
    th = GM()
    th.append(gp.cyl(mc.add(P0, (9.0, 0, -8)), mc.add(P1, (9.0, 0, 6)), 2.5, R_TRIM, sides=8))
    th.append(gp.ring_at(mc.add(P0, (9.0, 0, 0)), mc.add(P1, (9.0, 0, 0)), 12, 3.4, 2.4, R_ACCENT, thick=0.8))
    th.append(gp.tube_plate(P0, P1, 12, 34, 10.0, 8.8, -70, 70, 1.4, R_PLATE, nv=4, nu=7))
    k.pair("thigh", th)
    k.pair("calf", gp.greave(B, thick=1.6, knee=True, arc=(-110, 110), s1=36.0, accent=R_ACCENT))
    return k
