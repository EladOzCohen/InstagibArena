"""Gear of characters 10-14: Aurelia, Tundra, Mosscap, Specter-9, Brimstone. Each function takes the Body and returns a gear_parts.Kit."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_b import kneepad, elbow_pad, pouch
from gear_parts import Kit, back_x, front_x, rad, SIN, COS
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT, fr


def ring_strips(B, z, count, length, role, rad_off=1.4, flare=0.2, width_deg=None, skip=(), nv=4, taper=0.85, bands=(), wave=0.0):
    """Strips hanging all round the hips (pteruges, leaf skirts)."""
    m = GM()
    step = 360.0 / count
    w = width_deg or step * 0.56
    for i in range(count):
        ang = i * step
        if any(lo <= ang <= hi for lo, hi in skip):
            continue
        a, b = B.tpt(z, ang - w, rad_off), B.tpt(z, ang + w, rad_off)
        d = (flare * COS(rad(ang)), flare * SIN(rad(ang)), -1.0)
        out = (COS(rad(ang)), SIN(rad(ang)), 0.0)
        L = length * (1.0 + wave * SIN(i * 2.3))
        m.append(gp.hang(a, b, d, L, role, out=out, taper=taper, bulge=0.4, nu=2, nv=nv, thick=0.5, stripes=list(bands)))
    return m


# ------------------------------------------------------------------------------------------------ 10 Aurelia
def aurelia(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.8, z_bot=zc - 7.0, jaw=0.96)
    zb = zc + 5.0
    k.add("head", H.shell(R_PLATE, sides=18, z_bot=zb, caps=(False, True)))
    k.add("head", H.shell(R_PLATE, sides=10, z_bot=zc - 7.0, arc=(52.0, 308.0)) if False else _lower_helm(H, zc, zb))
    k.add("head", band_head(H, zb - 0.2, 1.6, R_ACCENT, off=0.4))
    k.add("head", gp.box_at((H.front(zc - 1.0) + 0.1, 0.0, zc + 0.5), (1.1, 1.8, 11.0), R_PLATE, ch=0.4, pitch=-3))
    for s in (-1, 1):
        k.add("head", gp.box_at((H.cx + 1.5, s * (H.side(zc - 2.0) + 0.5), zc - 3.0), (9.0, 1.2, 11.0), R_PLATE, ch=0.5, yaw=s * -8, taper=0.9))
    k.add("head", gp.box_at((H.cx - H.rx * 0.95, 0.0, zc - 6.0), (3.0, H.ry * 1.9, 5.5), R_PLATE, ch=0.7, pitch=18, taper=0.8))
    # transverse crest: a fan of red plumes from the forehead to the neck
    def crest_pt(phi, h):
        x = H.cx + H.rx * COS(rad(phi))
        z = H.z_eq + (H.z_top - H.z_eq) * SIN(rad(phi))
        n = (COS(rad(phi)), 0.0, SIN(rad(phi)))
        return (x + n[0] * h, 0.0, z + n[2] * h)
    cr = GM()
    cr.plate(lambda u, v: crest_pt(lerp_(20.0, 160.0, u), v * 12.0 * (0.55 + 0.45 * SIN(math.pi * u)) + 0.2), [i / 12.0 for i in range(13)], [0.0, 0.5, 1.0],
             lambda u, v: 1.6 * (1.0 - 0.5 * v), R_ACCENT, (H.cx, 0.0, zc), ) if False else None
    for i in range(11):
        phi = 22.0 + i * 13.0
        h = 9.0 + 3.5 * SIN(math.pi * i / 10.0)
        p0 = crest_pt(phi, -0.5)
        p1 = crest_pt(phi, h)
        cr.append(gp.box_at(((p0[0] + p1[0]) / 2, 0.0, (p0[2] + p1[2]) / 2), (1.3, 2.4, h + 0.8), R_ACCENT, ch=0.35, pitch=90 - phi if True else 0, taper=0.8))
    k.add("head", cr)
    # muscle cuirass in gold
    z0, z1, span = 116.0, 148.0, 58.0
    k.add("spine_05", gp.cuirass(B, off_=1.0, thick=1.3, span=span, bulge=2.6, vneck=3.0, z0=z0, z1=z1, panel=False, back=True))
    for z in (123.0, 128.0):
        k.add("spine_05", gp.torso_plate(B, z - 0.6, z + 0.6, -26, 26, 1.6, 1.0, R_TRIM, nu=7, nv=2, w=0.3, bulge=gp.pec_bulge(2.6, z0, z1, span)))
    k.add("spine_05", gp.torso_plate(B, 137.0 - 0.5, 137.0 + 0.5, -5, 5, 1.0, 1.0, R_TRIM, nu=3, nv=2, w=0.3, bulge=gp.pec_bulge(2.6, z0, z1, span)) if False else GM())
    k.add("spine_05", gp.collar_ring(B, z=149.0, r=7.4, h=3.0, role=R_ACCENT, thick=1.2))
    bx = back_x(B, 146.0, 1.8)
    k.add("spine_05", gp.hang((bx, -16.0, 147.5), (bx, 16.0, 147.5), (-0.14, 0.0, -1.0), 66.0, R_TEAM, out=(-1, 0, 0), taper=1.2, bulge=2.0, ripple=2.4, waves=2.0, phase=0.4,
                              nu=12, nv=8, inside=(bx + 8.0, 0, 120.0), stripes=[(0.0, 1.0, R_ACCENT, 0.94, 1.0)]))
    k.pair("upperarm", gp.pauldron(B, big=1.05, layers=3, role=R_PLATE, top_role=R_PLATE, lame_role=R_PLATE, thick=1.1, alpha=46))
    k.pair("lowerarm", gp.bracer(B, flare=1.1, accent=R_ACCENT, thick=0.9, s0=2, s1=24, arc=(0, 360)))
    # belt and the strips of the skirt
    k.add("pelvis", belt(B, role=R_PLATE, buckle=R_ACCENT, buckle_w=6.0, thick=1.3))
    k.add("pelvis", ring_strips(B, 97.0, 16, 20.0, R_TEAM, flare=0.28, nv=3, bands=[(0.0, 1.0, R_PLATE, 0.88, 1.0)]))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.1, s1=36.0, arc=(-98, 98)))
    return k


def lerp_(a, b, t):
    return a + (b - a) * t


def _lower_helm(H, zc, zb):
    m = GM()
    prof = [(H.r(zc - 7.0), zc - 7.0), (H.r(zc - 2.0), zc - 2.0), (H.r(zb), zb)]
    m.lathe(prof, R_PLATE, sides=10, f=fr((H.cx, 0, 0)), sy=H.sy, caps=(False, False), arc=(52.0, 308.0))
    return m


# ------------------------------------------------------------------------------------------------ 11 Tundra
def tundra(B):
    k = Kit(B)
    zc = B.head_c[2]
    hd, H = gp.hood(B, role=R_PLATE, margin=3.4, open_deg=48.0, back=0.25, z_bot=zc - 12.0)
    k.add("head", hd)
    fx = H.cx + H.rx
    # fur trim round the face, goggles, fur collar
    k.add("head", gp.blob_ring((fx - 3.0, 0.0, zc + 0.5), 12.0, 3.2, R_LIGHT, lumps=11, amp=0.3, sy=0.80, sides=28, rings=6, seed=2) if False else _fur_face(H, zc))
    k.add("head", gp.goggles(B, z=zc + 2.4, H=gp.Helm(B, 0.6), x_off=B.head_c[0] + B.head_rx - 0.8, role_lens=R_GLOW, role_rim=R_TRIM, r=2.5, rim_r=3.1, spread=4.4,
                             strap_role=R_TRIM, strap=False))
    cx = B.torso(148)[0] - 0.6
    k.add("spine_05", gp.blob_ring((cx, 0.0, 147.5), 13.5, 4.6, R_LIGHT, lumps=12, amp=0.28, sy=1.32, sides=30, rings=7, seed=5))
    # harness, backpack with a sleeping mat and an ice axe
    k.add("spine_05", gp.torso_plate(B, 120.0, 144.0, -50, 50, 1.3, 1.1, R_PLATE, nu=9, nv=5, bulge=gp.pec_bulge(1.0, 120, 144, 50), top_fn=lambda u: 6 * (1 - abs(2 * u - 1)) ** 2))
    for sgn in (-1, 1):
        k.add("spine_05", gp.torso_plate(B, 120.0, 146.0, min(sgn * 6, sgn * 16), max(sgn * 6, sgn * 16), 2.6, 0.9, R_TRIM, nu=3, nv=6, w=0.25, bulge=gp.pec_bulge(1.0, 120, 144, 50)))
    k.add("spine_05", gp.box_at((front_x(B, 134.0, 3.0), 0.0, 133.0), (1.4, 8.0, 5.0), R_ACCENT, ch=0.5))
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 6.5, 0.0, 130.0), (13.0, 26.0, 32.0), R_PLATE, ch=2.5, taper=0.92))
    k.add("spine_05", gp.cyl((bx - 6.5, -14.5, 150.0), (bx - 6.5, 14.5, 150.0), 5.5, R_ACCENT, sides=12))
    k.add("spine_05", gp.cyl((bx - 13.5, -8.0, 108.0), (bx - 13.5, -8.0, 160.0), 1.1, R_TRIM, sides=6))
    k.add("spine_05", gp.horn((bx - 13.5, -8.0, 160.0), (bx - 13.5, -13.5, 163.0), (bx - 13.5, -17.0, 157.0), 1.6, R_ACCENT, n=6, sides=6))
    # fur shoulders with ice crystals
    sh = GM()
    J = B.bone("upperarm_l")
    sh.append(gp.ball((J[0], J[1] - 1.0, J[2] + 3.5), 9.4, R_LIGHT, nu=12, nv=7, sy=1.0, sz=0.72))
    for i, (dx, dy, h) in enumerate(((1.0, -4.0, 11.0), (-2.5, -6.5, 8.0), (4.0, -6.0, 7.0))):
        base = (J[0] + dx, J[1] + dy - 0.5, J[2] + 8.0)
        sh.append(gp.spike(base, (base[0] + dx * 0.3, base[1] - 2.0, base[2] + h), 2.1, R_ACCENT, sides=5))
    k.pair("upperarm", sh)
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    k.pair("lowerarm", gp.merge(gp.ring_at(P0, P1, 17.5, 6.0, 6.0, R_LIGHT, thick=2.2, grow=0.8), gp.ring_at(P0, P1, 3.0, 5.8, 2.0, R_TRIM, thick=1.0)))
    k.add("pelvis", belt(B, role=R_TRIM, buckle=R_TEAM, buckle_w=6.0))
    C0, C1 = B.bone("calf_l"), B.bone("foot_l")
    k.pair("calf", gp.merge(kneepad(B, R_PLATE, R_TRIM, 1.0), gp.ring_at(C0, C1, 24.0, 7.7, 8.0, R_LIGHT, thick=2.4, grow=0.8)))
    return k


def _fur_face(H, zc):
    return gp.blob_ring((H.cx + H.rx - 2.0, 0.0, zc - 1.5), 11.5, 3.3, R_LIGHT, lumps=11, amp=0.3, sy=0.78, sides=28, rings=6, seed=2, tilt=90.0)


# ------------------------------------------------------------------------------------------------ 12 Mosscap
def mosscap(B):
    k = Kit(B)
    zc = B.head_c[2]
    cx = B.head_c[0] - 0.4
    zr = zc + 6.5                                   # rim height of the cap
    R = 27.0
    wav = lambda th, t: 1.0 + 0.04 * COS(7 * th)
    cap = GM()
    prof = [(R, zr), (R * 0.97, zr + 4.0), (R * 0.82, zr + 9.5), (R * 0.58, zr + 14.0), (R * 0.28, zr + 17.0), (0.0, zr + 18.0)]
    cap.lathe(prof, R_ACCENT, sides=26, f=fr((cx, 0.0, 0.0)), caps=(False, False), rfn=wav)
    cap.lathe([(R * 1.02, zr - 1.6), (R * 1.02, zr - 0.2), (R, zr + 0.8)], R_TEAM, sides=26, f=fr((cx, 0.0, 0.0)), caps=(False, False), rfn=wav)
    # gills under the cap, a cream disc
    cap.lathe([(R * 0.99, zr - 1.5), (R * 0.2, zr - 4.5), (R * 0.2, zr - 0.6), (R * 0.97, zr - 1.5)][:2] + [(R * 0.2, zr - 2.8)], R_LIGHT, sides=26, f=fr((cx, 0.0, 0.0)), caps=(False, False),
              rfn=wav, flip=True) if False else None
    cap.lathe([(R * 0.2, zr - 3.6), (R * 0.99, zr - 1.4)], R_LIGHT, sides=26, f=fr((cx, 0.0, 0.0)), caps=(False, False), rfn=wav, flip=True)
    def dome_z(rr):
        for (r0, z0), (r1, z1) in zip(prof[:-1], prof[1:]):
            if r1 <= rr <= r0:
                return z0 + (z1 - z0) * (r0 - rr) / (r0 - r1)
        return zr + 18.0
    for i, (r_, a_, s_) in enumerate(((0.45, 20, 4.2), (0.62, 80, 3.4), (0.5, 150, 4.4), (0.72, 200, 3.2), (0.4, 260, 3.6), (0.7, 320, 4.0), (0.12, 40, 3.4))):
        rr_ = R * r_
        th = rad(a_)
        cap.ellipsoid((cx + rr_ * COS(th), rr_ * SIN(th), dome_z(rr_) - 0.3), s_, s_, 1.6, R_LIGHT, nu=8, nv=4, cut=(0.0, 0.5))
    k.add("head", cap)
    # shelf fungi on the back
    bx = back_x(B, 134.0)
    for (y, z, r_) in ((-6.0, 142.0, 12.5), (7.0, 130.0, 14.0), (-4.0, 118.0, 11.0)):
        sh = GM()
        sh.lathe([(r_, 0.0), (r_ * 0.92, 3.4), (r_ * 0.5, 5.6), (0.0, 6.2)], R_TEAM, sides=10, f=fr((bx + 1.0, y, z), pitch=0), caps=(False, False), arc=(90.0, 270.0))
        sh.lathe([(0.0, -0.6), (r_ * 0.97, 0.0)], R_LIGHT, sides=10, f=fr((bx + 1.0, y, z)), caps=(False, False), arc=(90.0, 270.0), flip=True)
        k.add("spine_05", sh)
    # moss pads on the shoulders, leaves on chest and hips
    J = B.bone("upperarm_l")
    k.pair("upperarm", gp.merge(gp.ball((J[0], J[1] - 1.0, J[2] + 3.0), 9.0, R_CLOTH, nu=10, nv=6, sy=1.05, sz=0.7),
                                gp.ball((J[0] + 2.5, J[1] - 3.5, J[2] + 6.0), 4.5, R_CLOTH, nu=8, nv=5)))
    leaf = lambda a, b, L: gp.hang(a, b, (0.0, 0.0, -1.0), L, R_CLOTH, out=(1.0, 0.0, 0.0), taper=0.12, bulge=0.8, nu=3, nv=4, thick=0.5)
    for row, (z, L, n) in enumerate(((147.0, 12.0, 9), (139.0, 12.0, 9), (131.0, 11.0, 7), (123.0, 10.0, 7))):
        span = 62.0 - row * 6.0
        for i in range(n):
            ang = -span + 2.0 * span * i / (n - 1)
            w = span / (n - 1) * 0.62
            k.add("spine_05", leaf(B.tpt(z, ang - w, 1.2 + row * 0.25), B.tpt(z, ang + w, 1.2 + row * 0.25), L))
    k.add("pelvis", belt(B, role=R_CLOTH, buckle=R_TEAM, buckle_w=5.0))
    k.add("pelvis", ring_strips(B, 97.0, 12, 18.0, R_CLOTH, flare=0.35, taper=0.15, nv=4, wave=0.2))
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    k.pair("lowerarm", gp.bracer(B, role=R_PLATE, trim_role=R_CLOTH, thick=1.2, s0=3, s1=21, rings=True, arc=(-60, 240)))
    C0, C1 = B.bone("calf_l"), B.bone("foot_l")
    k.pair("calf", gp.merge(kneepad(B, R_CLOTH, R_PLATE, 1.1), gp.tube_plate(C0, C1, 20, 35, 6.6, 5.4, -90, 90, 1.0, R_PLATE, nv=4, nu=7)))
    return k


# ------------------------------------------------------------------------------------------------ 13 Specter-9
def specter(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 0.9)
    k.add("head", gp.blob_ring((H.cx, 0.0, zc + 26.0), 16.5, 0.95, R_GLOW, lumps=3, amp=0.0, sy=1.0, sides=40, rings=5, seed=1))
    k.add("head", gp.blob_ring((H.cx, 0.0, zc + 24.0), 12.5, 0.7, R_LIGHT, lumps=3, amp=0.0, sy=1.0, sides=32, rings=5, seed=1))
    k.add("head", gp.box_at((H.front(zc + 2.2) + 0.2, 0.0, zc + 2.4), (1.0, 15.0, 2.8), R_GLOW, ch=0.3))
    k.add("head", gp.box_at((H.front(zc + 2.2) - 0.1, 0.0, zc + 2.4), (0.9, 17.5, 4.4), R_LIGHT, ch=0.5))
    for s in (-1, 1):
        k.add("head", gp.box_at((H.cx, s * (H.side(zc) + 1.0), zc + 1.5), (7.0, 1.2, 8.0), R_LIGHT, ch=0.4))
    # floating ribs and shoulder shards
    z0, z1 = 120.0, 148.0
    for i, z in enumerate((126.0, 132.0, 138.0, 144.0)):
        k.add("spine_05", gp.torso_plate(B, z - 1.3, z + 1.3, -56 + i * 3, 56 - i * 3, 3.6, 1.0, R_TEAM if i % 2 == 0 else R_LIGHT, nu=11, nv=2, w=0.3,
                                         bulge=gp.pec_bulge(1.4, z0, z1, 60)))
    bx = back_x(B, 138.0)
    k.add("spine_05", _back_ring(bx))
    k.add("spine_05", gp.box_at((bx - 3.0, 0.0, 135.0), (3.0, 3.0, 30.0), R_LIGHT, ch=0.8))
    shard = GM()
    J = B.bone("upperarm_l")
    for i, (dx, dy, dz, sz, role, rot) in enumerate(((2.0, -9.0, 14.0, 5.0, R_LIGHT, 25), (-4.0, -14.0, 9.0, 4.0, R_TEAM, 50), (6.0, -15.0, 4.0, 3.4, R_GLOW, 70))):
        shard.append(gp.box_at((J[0] + dx, J[1] + dy, J[2] + dz), (sz, sz, sz), role, ch=0.9, yaw=rot, pitch=rot * 0.7, roll=rot * 0.4))
    k.pair("upperarm", shard)
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    k.pair("lowerarm", gp.merge(gp.ring_at(P0, P1, 5.0, 6.2, 0.9, R_GLOW, thick=0.5), gp.ring_at(P0, P1, 13.0, 5.6, 1.3, R_LIGHT, thick=0.6), gp.ring_at(P0, P1, 20.0, 4.8, 0.9, R_GLOW, thick=0.5)))
    k.add("pelvis", belt(B, role=R_LIGHT, buckle=R_GLOW, buckle_w=4.0, thick=0.7))
    C0, C1 = B.bone("calf_l"), B.bone("foot_l")
    k.pair("calf", gp.merge(gp.ring_at(C0, C1, 8.0, 7.6, 1.0, R_GLOW, thick=0.5), gp.ring_at(C0, C1, 24.0, 6.4, 1.4, R_LIGHT, thick=0.6), gp.ring_at(C0, C1, 36.0, 5.8, 0.9, R_GLOW, thick=0.5)))
    return k


def _back_ring(bx):
    return gp.blob_ring((bx - 12.0, 0.0, 137.0), 27.0, 0.9, R_GLOW, lumps=3, amp=0.0, sy=1.0, sides=44, rings=5, seed=1, tilt=90.0)


# ------------------------------------------------------------------------------------------------ 14 Brimstone
def brimstone(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 0.8)
    for s in (-1, 1):
        k.add("head", gp.horn((H.cx + 3.0, s * 5.5, zc + 9.0), (H.cx - 5.0, s * 17.0, zc + 23.0), (H.cx - 14.0, s * 15.5, zc + 41.0), 3.4, R_TRIM, n=9, sides=7))
        k.add("head", gp.spike((H.cx + 2.0, s * (H.side(zc - 4) + 0.2), zc - 5.0), (H.cx + 4.0, s * (H.side(zc - 4) + 4.5), zc - 12.0), 1.6, R_TRIM, sides=6))
    k.add("head", gp.box_at((H.front(zc + 5.0) - 0.8, 0.0, zc + 5.2), (3.0, H.side(zc + 5.0) * 2.0, 1.8), R_TRIM, ch=0.7, pitch=-8))
    # charred chest plate with a glowing crack
    z0, z1, span = 120.0, 149.0, 56.0
    k.add("spine_05", gp.cuirass(B, role=R_TRIM, trim=R_PLATE, off_=1.2, thick=1.3, span=span, bulge=1.8, vneck=6.0, z0=z0, z1=z1, panel=False, back=True))
    zig = lambda u: 1.5 * math.sin(u * 23.0)
    k.add("spine_05", gp.torso_plate(B, 124.0, 146.0, -3.0, 3.0, 2.8, 0.7, R_GLOW, nu=3, nv=9, w=0.3, bulge=gp.pec_bulge(1.8, z0, z1, span)))
    for (a0, a1, za, zb_) in ((3.0, 22.0, 132.0, 138.0), (-22.0, -3.0, 126.0, 131.0)):
        k.add("spine_05", gp.torso_plate(B, za, zb_, a0, a1, 2.6, 0.6, R_GLOW, nu=4, nv=2, w=0.3, bulge=gp.pec_bulge(1.8, z0, z1, span)))
    # wings
    bx = back_x(B, 138.0)
    k.pair("spine_05_wings", GM()) if False else None
    wing = _wing(B, bx)
    k.add("spine_05", wing)
    k.add("spine_05", wing.mirrored())
    # tail
    pelv = B.bone("pelvis")
    path = [(pelv[0] - 8, 0, pelv[2] + 1), (pelv[0] - 16, 0, pelv[2] - 4), (pelv[0] - 28, 0, pelv[2] - 16), (pelv[0] - 38, 0, pelv[2] - 34), (pelv[0] - 36, 0, pelv[2] - 52),
            (pelv[0] - 28, 0, pelv[2] - 62)]
    k.add("pelvis", _sweep(path, [4.4, 3.8, 3.0, 2.2, 1.6, 1.2], R_PLATE, 8))
    tip = path[-1]
    spade = GM()
    spade.append(gp.box_at((tip[0] - 1.0, 0.0, tip[2] - 4.0), (1.2, 9.0, 11.0), R_ACCENT, ch=0.4, pitch=-10, taper=0.2))
    k.add("pelvis", spade)
    k.pair("upperarm", gp.pauldron(B, big=1.15, layers=2, role=R_TRIM, top_role=R_PLATE, lame_role=R_TRIM, spike=13.0, spike_role=R_ACCENT, thick=1.2, alpha=44))
    k.pair("lowerarm", gp.bracer(B, flare=1.15, role=R_TRIM, trim_role=R_ACCENT, thick=1.1, s0=3, s1=22, spike=11.0))
    k.add("pelvis", belt(B, role=R_TRIM, buckle=R_ACCENT, buckle_w=6.0))
    C0 = B.bone("calf_l")
    sp = GM()
    sp.append(gp.spike((C0[0] + 8.0, C0[1] - 0.5, C0[2] + 1.0), (C0[0] + 14.5, C0[1] - 0.5, C0[2] + 5.5), 2.3, R_TRIM, sides=6))
    sp.append(gp.tube_plate(C0, B.bone("foot_l"), 6, 32, 7.0, 5.7, -90, 90, 1.1, R_TRIM, nv=4, nu=7))
    k.pair("calf", sp)
    return k


def _wing(B, bx):
    """A bat wing for the left side: an arm bone, three fingers and two membranes. Built in the plane behind the shoulder blade."""
    root = (bx - 2.0, -7.0, 139.0)
    elbow = (bx - 14.0, -36.0, 164.0)
    fingers = [
        [root, (bx - 26.0, -52.0, 183.0), (bx - 36.0, -80.0, 190.0)],
        [elbow, (bx - 34.0, -66.0, 164.0), (bx - 52.0, -92.0, 150.0)],
        [elbow, (bx - 28.0, -60.0, 148.0), (bx - 46.0, -74.0, 118.0)],
        [root, (bx - 14.0, -34.0, 120.0), (bx - 28.0, -44.0, 98.0)],
    ]

    def curve(f, t):
        a = mc.lerp3(f[0], f[1], t)
        b = mc.lerp3(f[1], f[2], t)
        return mc.lerp3(a, b, t)

    m = GM()
    # arm bone: root -> elbow -> first finger tip
    arm = [root, mc.lerp3(root, elbow, 0.5), elbow, (bx - 20.0, -50.0, 176.0), (bx - 36.0, -80.0, 190.0)]
    m.sweep(arm, [2.0, 1.8, 1.7, 1.2, 0.5], R_TRIM, sides=6)
    for f in fingers[1:3]:
        pts = [curve(f, t / 6.0) for t in range(7)]
        m.sweep(pts, [1.3 - 0.9 * (t / 6.0) for t in range(7)], R_TRIM, sides=5)
    for (fa, fb) in ((fingers[0], fingers[1]), (fingers[1], fingers[2]), (fingers[2], fingers[3])):
        nv = 8
        P = []
        for i in range(5):
            u = i / 4.0
            col = []
            for j in range(nv):
                t = j / float(nv - 1)
                pa, pb = curve(fa, t), curve(fb, t)
                p = mc.lerp3(pa, pb, u)
                sag = 3.0 * SIN(math.pi * u) * t
                col.append((p[0] - sag, p[1], p[2]))
            P.append(col)
        m.cloth(P, R_CLOTH, thick=0.5)
    return m
