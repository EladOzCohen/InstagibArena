"""Gear of characters 5-9: Marlowe, Nyx, Oddjob, Sable, Gearhead. Each function takes the Body and returns a gear_parts.Kit."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, ring_pair, band_head
from gear_parts import Kit, back_x, front_x, rad, SIN, COS
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT, fr


def kneepad(B, role=R_PLATE, strap=R_CLOTH, size=1.0):
    P0, P1 = B.bone("calf_l"), B.bone("foot_l")
    f = mc.frame_z(P0, P1)
    m = GM()
    m.ellipsoid(f.pt((8.4, 0.0, -0.5)), 4.6 * size, 5.8 * size, 5.6 * size, role, nu=12, nv=6, cut=(0.0, 0.66))
    m.append(gp.ring_at(P0, P1, -3.5, 7.4, 2.0, strap, thick=1.0))
    m.append(gp.ring_at(P0, P1, 3.5, 7.1, 1.6, strap, thick=1.0))
    return m


def elbow_pad(B, role=R_PLATE, size=1.0):
    P0, P1 = B.bone("upperarm_l"), B.bone("lowerarm_l")
    f = mc.frame_z(P1, B.bone("hand_l"))
    m = GM()
    m.ellipsoid(f.pt((-3.6, 1.2, 1.5)), 4.4 * size, 4.4 * size, 5.2 * size, role, nu=10, nv=6, cut=(0.0, 0.7), f=mc.IDENT)
    return m


def pouch(c, size, role, flap=R_TRIM, yaw=0.0, roll=0.0):
    m = GM()
    m.append(gp.box_at(c, size, role, ch=0.5, yaw=yaw, roll=roll))
    f = fr(c, yaw=yaw, roll=roll)
    m.box((size[0] / 2 + 0.1, 0.0, size[2] * 0.2), (0.5, size[1] * 0.9, size[2] * 0.55), flap, ch=0.2, f=f)
    return m


# ------------------------------------------------------------------------------------------------ 5 Marlowe
def marlowe(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.5, z_bot=zc + 3.0, jaw=1.0)
    k.add("head", gp.helm_open(B, role=R_PLATE, brim=3.4))
    k.add("head", gp.goggles(B, z=zc + 6.6, H=gp.Helm(B, 1.5), x_off=H.front(zc + 6.6) - 0.6, role_lens=R_GLOW, role_rim=R_TRIM, r=2.6, rim_r=3.2, spread=4.6, tilt=-6,
                             strap_role=R_CLOTH))
    z0, z1, span = 120.0, 146.0, 50.0
    k.add("spine_05", gp.torso_plate(B, z0, z1, -span, span, 1.2, 1.8, R_TEAM, nu=11, nv=5, top_fn=lambda u: 4.0 * (1 - abs(2 * u - 1)) ** 2,
                                     bulge=gp.pec_bulge(1.0, z0, z1, span)))
    k.add("spine_05", gp.torso_plate(B, z0 + 2.0, z1 - 2.0, 150.0, 210.0, 1.1, 1.6, R_PLATE, nu=7, nv=4))
    # shoulder straps and the pouches of the chest rig
    for sgn in (-1, 1):
        a0, a1 = (sgn * 18.0, sgn * 40.0)
        k.add("spine_05", gp.torso_plate(B, 126.0, 151.5, min(a0, a1), max(a0, a1), 1.0, 1.0, R_CLOTH, nu=3, nv=7, w=0.2))
        for j in range(3):
            ang = sgn * (8.0 + 11.0 * j)
            x = front_x(B, 128.0, 3.1)
            c = (x - 0.5, (11.0 - 0.0) * sgn * (0.35 + 0.65 * j), 125.5)
            k.add("spine_05", pouch((x - 0.8, sgn * (3.2 + 6.0 * j), 125.0), (3.0, 5.0, 7.0), R_CLOTH, R_TRIM))
    # rucksack with a bedroll
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 7.0, 0.0, 131.0), (15.0, 26.0, 34.0), R_CLOTH, ch=2.2, taper=0.92))
    k.add("spine_05", gp.box_at((bx - 8.0, 0.0, 149.0), (15.5, 26.5, 5.0), R_PLATE, ch=1.4))
    k.add("spine_05", gp.box_at((bx - 10.0, 0.0, 123.0), (8.0, 20.0, 11.0), R_PLATE, ch=1.2))
    k.add("spine_05", gp.cyl((bx - 6.0, -17.5, 122.0), (bx - 6.0, -17.5, 136.0), 3.6, R_TRIM, sides=10))
    k.add("spine_05", gp.cyl((bx - 6.0, -13.5, 150.0), (bx - 6.0, 13.5, 150.0), 5.2, R_ACCENT, sides=12))
    for s in (-1, 1):
        k.add("spine_05", gp.box_at((bx - 5.0, s * 14.0, 128.0), (7.0, 4.5, 14.0), R_TRIM, ch=0.9))
        k.add("spine_05", gp.cyl((bx - 6.0, s * 5.0, 143.0), (bx - 6.0, s * 5.0, 156.0), 1.2, R_ACCENT, sides=6)) if False else None
    k.pair("upperarm", gp.pauldron(B, big=0.78, layers=1, lame_role=R_PLATE, top_role=R_PLATE, thick=0.9, alpha=50))
    k.pair("lowerarm", gp.merge(elbow_pad(B), gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 20.5, 4.6, 3.0, R_CLOTH, thick=1.0)))
    k.add("pelvis", belt(B, role=R_CLOTH, buckle=R_ACCENT, buckle_w=5.0))
    cx = B.torso(98)[0]
    for s in (-1, 1):
        k.add("pelvis", pouch((cx + 5.5, s * 14.0, 96.0), (5.0, 6.0, 8.0), R_CLOTH, R_TRIM, yaw=s * -20))
    k.add("pelvis", pouch((cx - 8.0, 0.0, 97.0), (4.0, 8.0, 6.5), R_CLOTH, R_TRIM))
    k.pair("calf", kneepad(B))
    return k


def elbow_free(B):
    return GM()


# ------------------------------------------------------------------------------------------------ 6 Nyx
def nyx(B):
    k = Kit(B)
    zc = B.head_c[2]
    hd, H = gp.hood(B, role=R_CLOTH, margin=2.5, open_deg=50.0, back=0.45, rim=R_ACCENT, z_bot=zc - 8.5, jaw=0.86)
    k.add("head", hd)
    fx = B.head_c[0] + B.head_rx - 0.2
    for s in (-1, 1):
        k.add("head", gp.box_at((fx + 0.3, s * 3.6, zc + 2.3), (0.9, 3.3, 1.0), R_GLOW, ch=0.2, yaw=s * 8))
        k.add("head", gp.horn((H.cx + 2.0, s * 7.5, zc + 10.0), (H.cx + 0.0, s * 13.0, zc + 19.0), (H.cx - 3.0, s * 14.0, zc + 28.0), 1.9, R_ACCENT, n=7, sides=6))
    # mantle over the shoulders
    cx = B.torso(150)[0] - 1.2
    m = GM()
    m.lathe([(21.5, 140.5), (17.0, 146.0), (12.0, 150.0), (8.2, 152.6)], R_CLOTH, sides=26, f=fr((cx, 0, 0)), sy=1.28, caps=(False, False), double=True)
    m.lathe([(22.4, 138.6), (21.5, 140.5)], R_ACCENT, sides=26, f=fr((cx, 0, 0)), sy=1.28, caps=(False, False), double=True)
    k.add("spine_05", m)
    # cape with a torn hem and a team coloured stripe
    bx = back_x(B, 146.0, 1.8)
    a, b = (bx, -17.0, 147.5), (bx, 17.0, 147.5)
    k.add("spine_05", gp.hang(a, b, (-0.16, 0.0, -1.0), 112.0, R_CLOTH, out=(-1.0, 0.0, 0.0), taper=1.45, bulge=2.5, ripple=3.0, waves=2.5, phase=0.6,
                              hem=lambda u: 0.88 + 0.12 * abs(math.sin(u * 17.0)), nu=15, nv=9, thick=0.5, inside=(bx + 8.0, 0, 120.0),
                              stripes=[(0.45, 0.55, R_TEAM), (0.0, 1.0, R_ACCENT, 0.93, 1.0)]))
    # chest clasp and bracers
    x = front_x(B, 146.0, 2.0)
    k.add("spine_05", gp.box_at((x - 2.0, 0, 147.0), (2.0, 7.0, 2.2), R_TEAM, ch=0.5))
    k.pair("lowerarm", gp.bracer(B, flare=1.05, trim_role=R_ACCENT, thick=1.0, s0=3, s1=22, role=R_PLATE))
    k.add("pelvis", belt(B, role=R_PLATE, buckle=R_ACCENT, buckle_w=4.0, thick=1.0))
    k.pair("calf", gp.greave(B, thick=1.0, knee=False, s1=34.0, arc=(-100, 100), trim_role=R_ACCENT))
    return k


# ------------------------------------------------------------------------------------------------ 7 Oddjob
def oddjob(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.7, jaw=1.0)
    # two-coloured skull cap with a band and two curling horns ending in bells
    k.add("head", H.shell(R_ACCENT, sides=4, z_bot=zc + 5.0, arc=(90.0, 270.0)))
    k.add("head", H.shell(R_TEAM, sides=4, z_bot=zc + 5.0, arc=(-90.0, 90.0)))
    k.add("head", band_head(H, zc + 5.0, 2.0, R_PLATE))
    for s, role, bell in ((-1, R_ACCENT, R_LIGHT), (1, R_TEAM, R_GLOW)):
        p0 = (H.cx + 1.0, s * 5.5, zc + 10.0)
        p1 = (H.cx - 1.0, s * 20.0, zc + 22.0)
        p2 = (H.cx - 7.0, s * 26.0, zc + 11.0)
        k.add("head", gp.horn(p0, p1, p2, 3.4, role, n=10, sides=8))
        k.add("head", gp.ball((p2[0] - 0.5, p2[1] + s * 0.5, p2[2] - 1.5), 2.8, bell, nu=8, nv=5))
    cx = B.torso(150)[0] - 1.0
    k.add("spine_05", gp.pleated_ring((cx, 0, 0), 8.0, 15.5, 148.0, 144.0, R_LIGHT, pleats=15, depth=0.13, sides=44, sy=1.15) if False else ruff(cx))
    # diamond tabard and buttons
    k.add("spine_05", gp.diamond(B, 104.0, 147.0, 38.0, 1.3, 1.1, R_TEAM))
    k.add("spine_05", gp.diamond(B, 112.0, 138.0, 22.0, 1.3 + 1.0, 0.8, R_LIGHT))
    for z in (143.0, 135.0, 127.0):
        x = front_x(B, z, 3.6)
        k.add("spine_05", gp.ball((x, 0.0, z), 1.6, R_ACCENT, nu=7, nv=5))
    for sgn in (-1, 1):
        pass
    cuff = GM()
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    cuff.append(gp.pleat_band(P0, P1, 20.0, 5.0, 5.0, R_LIGHT, pleats=11, depth=0.15, flare=2.0))
    cuff.append(gp.ring_at(P0, P1, 6.0, 5.6, 1.6, R_ACCENT, thick=0.9))
    k.pair("lowerarm", cuff)
    # ruffled skirt and knee frills
    k.add("pelvis", belt(B, role=R_ACCENT, buckle=R_TEAM, buckle_w=5.0))
    k.add("pelvis", gp.pleated_ring((B.torso(98)[0], 0, 0), 15.5, 23.0, 98.0, 87.0, R_TEAM, pleats=14, depth=0.12, sides=44, sy=1.0))
    C0, C1 = B.bone("calf_l"), B.bone("foot_l")
    k.pair("calf", gp.merge(gp.pleat_band(C0, C1, 31.0, 5.2, 4.0, R_ACCENT, pleats=11, depth=0.15, flare=2.2), gp.pleat_band(C0, C1, 2.0, 6.5, 3.5, R_LIGHT, pleats=11, depth=0.15, flare=1.5)))
    return k


def ruff(cx):
    m = GM()
    # flared collar: bottom to top so that the outside faces out and up
    m.lathe([(15.5, 144.0), (8.0, 148.5)], R_LIGHT, sides=44, f=fr((cx, 0, 0)), sy=1.15, caps=(False, False), rfn=lambda th, t: 1.0 + 0.12 * (1.0 - t) * COS(16 * th), double=True)
    m.lathe([(13.0, 142.5), (15.5, 144.0)], R_ACCENT, sides=44, f=fr((cx, 0, 0)), sy=1.15, caps=(False, False), rfn=lambda th, t: 1.0 + 0.1 * COS(16 * th), double=True)
    return m


# ------------------------------------------------------------------------------------------------ 8 Sable
def sable(B):
    k = Kit(B)
    H = gp.Helm(B, 1.8, z_bot=B.head_c[2] - 9.5, jaw=0.78)
    zc = B.head_c[2]
    k.add("head", H.shell(R_CLOTH, sides=16, caps=(False, True)))
    # eye slit and headband with trailing tails
    k.add("head", gp.box_at((H.front(zc + 2.5) + 0.1, 0.0, zc + 2.5), (1.0, 12.0, 1.5), R_GLOW, ch=0.25))
    k.add("head", band_head(H, zc + 4.8, 2.6, R_ACCENT, off=0.4))
    for s, L in ((-1, 30.0), (1, 24.0)):
        a = (H.cx - H.rx * 0.95, s * 0.6, zc + 4.8)
        b = (H.cx - H.rx * 0.95, s * 3.6, zc + 4.8)
        k.add("head", gp.hang(a, b, (-0.45, 0.0, -1.0), L, R_ACCENT, out=(0, s, 0), taper=0.8, ripple=1.8, waves=1.0, phase=s, nu=3, nv=6, thick=0.3))
    # scarf: ring round the neck and a long tail
    k.add("spine_05", gp.blob_ring((B.torso(151)[0] - 1.8, 0, 152.0), 7.6, 2.9, R_ACCENT, lumps=7, amp=0.18, sy=1.0, sides=20, rings=6, seed=3))
    bx = back_x(B, 146.0, 1.0)
    k.add("spine_05", gp.hang((bx, -3.0, 150.0), (bx, 3.0, 150.0), (-0.32, 0.0, -1.0), 62.0, R_ACCENT, out=(-1, 0, 0), taper=0.9, ripple=3.0, waves=1.2, phase=0.8,
                              nu=3, nv=9, thick=0.4, inside=(bx + 6, 0, 130.0)))
    # two crossed swords on the back
    bk = back_x(B, 132.0, 1.0)
    for roll in (-36.0, 36.0):
        f = fr((bk - 3.4, 0.0, 130.0), roll=roll)
        s = GM()
        s.box((0.0, 0.0, 0.0), (0.9, 3.2, 74.0), R_TRIM, ch=0.3, f=f, taper=0.9)
        s.box((0.0, 0.0, 41.0), (1.9, 2.6, 16.0), R_ACCENT, ch=0.5, f=f)
        s.box((0.0, 0.0, 33.5), (1.5, 6.8, 1.4), R_TRIM, ch=0.4, f=f)
        k.add("spine_05", s)
    # chest wrap, light plates and an obi sash
    k.add("spine_05", gp.torso_plate(B, 124.0, 146.0, -40, 40, 1.2, 1.3, R_PLATE, nu=9, nv=5, top_fn=lambda u: 6.0 * (1 - abs(2 * u - 1)) ** 2, bulge=gp.pec_bulge(0.8, 124, 146, 40)))
    k.add("spine_05", gp.torso_plate(B, 123.0, 125.2, -42, 42, 2.4, 0.8, R_ACCENT, nu=9, nv=2, w=0.3))
    k.add("pelvis", gp.torso_plate(B, 95.0, 106.0, 0, 360, 1.0, 1.5, R_ACCENT, nu=22, nv=3, wrap=True, w=0.3))
    xk, yk = front_x(B, 100.0, 2.4), -15.0
    k.add("pelvis", gp.box_at((xk - 3.0, yk, 100.0), (3.0, 6.0, 6.0), R_ACCENT, ch=1.0))
    for t, L in ((-6.0, 36.0), (-1.5, 30.0)):
        a, b = (xk - 3.5, yk + t, 98.5), (xk - 3.5, yk + t + 3.6, 98.5)
        k.add("pelvis", gp.hang(a, b, (0.1, -0.15, -1.0), L, R_ACCENT, out=(1, 0, 0), taper=0.9, ripple=1.2, waves=1.0, nu=3, nv=6, thick=0.4))
    # arm wraps with a metal plate, shin guards
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    fa = GM()
    fa.append(gp.tube_plate(P0, P1, 4, 22, 5.5, 4.4, 0, 360, 0.9, R_CLOTH, nv=5, nu=12))
    fa.append(gp.tube_plate(P0, P1, 8, 20, 6.2, 5.2, 20, 160, 0.9, R_TRIM, nv=3, nu=6, w=0.2))
    fa.append(gp.ring_at(P0, P1, 4, 5.9, 1.4, R_ACCENT, thick=0.8))
    k.pair("lowerarm", fa)
    k.pair("calf", gp.greave(B, thick=1.0, knee=False, s1=35.0, arc=(-100, 100), accent=R_ACCENT))
    return k


# ------------------------------------------------------------------------------------------------ 9 Gearhead
def gearhead(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.9, z_bot=zc + 3.5, jaw=1.0)
    # flat cap with a short brim and goggles pushed up on it
    k.add("head", H.shell(R_CLOTH, sides=18, z_bot=zc + 3.0, caps=(False, True)))
    k.add("head", gp.box_at((H.front(zc + 4.0) + 2.4, 0.0, zc + 3.6), (6.5, H.side(zc + 4.0) * 1.7, 0.9), R_CLOTH, ch=0.35, pitch=-9, taper=0.8))
    k.add("head", band_head(H, zc + 4.2, 1.4, R_TRIM, off=0.3))
    k.add("head", gp.goggles(B, z=zc + 9.3, H=H, x_off=H.front(zc + 9.3) - 1.0, role_lens=R_LIGHT, role_rim=R_ACCENT, r=2.9, rim_r=3.7, spread=4.9, tilt=24, strap_role=R_TRIM,
                             strap=False))
    # overall straps, bib pocket
    for sgn in (-1, 1):
        k.add("spine_05", gp.torso_plate(B, 118.0, 151.0, min(sgn * 20.0, sgn * 33.0), max(sgn * 20.0, sgn * 33.0), 1.0, 1.0, R_CLOTH, nu=3, nv=7, w=0.2))
        k.add("spine_05", gp.ball((front_x(B, 126.0, 2.4), sgn * 10.0, 126.0), 1.3, R_ACCENT, nu=7, nv=5))
    k.add("spine_05", gp.torso_plate(B, 112.0, 126.0, -22, 22, 1.2, 1.0, R_CLOTH, nu=6, nv=4, w=0.18))
    # backpack with a big gear
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 5.0, 0.0, 130.0), (11.0, 22.0, 26.0), R_TRIM, ch=1.8))
    gear = GM()
    prof = [(3.4, 0.0), (13.0, 0.0), (13.0, 3.2), (3.4, 3.2), (3.4, 0.0)]
    teeth = lambda th, t: 1.0 + 0.11 * max(-1.0, min(1.0, 3.0 * COS(12 * th))) if t > 0.0 and t < 0.99 else 1.0
    gear.lathe(prof, R_ACCENT, sides=48, f=fr((bx - 12.0, 0.0, 134.0), pitch=90), creases=(1, 2, 3), caps=(False, False), rfn=lambda th, t: 1.0 + (0.1 * max(-1.0, min(1.0, 4.0 * COS(12 * th))) if t in (0.25, 0.5) else 0.0))
    gear.lathe([(0.0, -0.4), (3.4, -0.4), (3.4, 3.6), (0.0, 3.6)], R_TRIM, sides=12, f=fr((bx - 12.0, 0.0, 134.0), pitch=90))
    k.add("spine_05", gear)
    for s in (-1, 1):
        k.add("spine_05", gp.cyl((bx - 9.0, s * 6.5, 122.0), (bx - 9.0, s * 6.5, 144.0), 1.3, R_TRIM, sides=6))
    # wrench on the right hip: a long handle and an open jaw
    cx = B.torso(98)[0]
    wr = GM()
    wr.append(gp.cyl((cx - 4.0, 18.5, 102.0), (cx - 4.0, 18.5, 76.0), 1.2, R_ACCENT, sides=8))
    wr.append(gp.box_at((cx - 4.0, 18.5, 74.0), (3.4, 4.2, 7.0), R_ACCENT, ch=0.8))
    wr.append(gp.box_at((cx - 4.0, 18.5, 102.5), (3.0, 3.0, 2.0), R_TRIM, ch=0.5))
    k.add("pelvis", wr)
    # tool belt
    k.add("pelvis", gp.torso_plate(B, 94.0, 102.0, 0, 360, 1.0, 1.8, R_TEAM, nu=22, nv=3, wrap=True, w=0.3))
    for s in (-1, 1):
        k.add("pelvis", pouch((cx + 6.0, s * 13.5, 98.0), (4.5, 6.0, 8.0), R_CLOTH, R_TRIM, yaw=s * -22))
    k.add("pelvis", gp.box_at((front_x(B, 98.0, 3.2), 0.0, 98.0), (1.8, 7.0, 6.0), R_ACCENT, ch=0.6))
    # elbow and knee pads, gloves
    fl = GM()
    fl.append(elbow_pad(B, R_ACCENT, 1.05))
    fl.append(gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 19.0, 4.9, 4.5, R_TRIM, thick=1.2))
    k.pair("lowerarm", fl)
    k.pair("calf", kneepad(B, R_ACCENT, R_TRIM, 1.1))
    return k
