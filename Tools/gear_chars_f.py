"""Gear of the Neon Syndicate characters (looks 25-28): Cipher, Chrome, Broker, Glitch. Each function takes the Body and returns a gear_parts.Kit."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_b import kneepad, elbow_pad, pouch
from gear_chars_c import ring_strips
from gear_chars_d import diag_band
from gear_parts import Kit, back_x, front_x, COS, SIN, rad
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT


def glow_lines(B, z0, z1, angles, role=R_GLOW, off_=1.5, w=2.2):
    m = GM()
    for a in angles:
        m.append(gp.torso_plate(B, z0, z1, a - w / 2, a + w / 2, off_, 0.7, role, nu=2, nv=4, w=0.3))
    return m


# ------------------------------------------------------------------------------------------------ 25 Cipher
def cipher(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.7, jaw=0.9)
    k.add("head", gp.helm_full(B, role=R_TRIM, trim=R_TRIM, accent=R_GLOW, glow=R_GLOW, margin=1.7, slit_w=14.0, slit_h=3.8, jaw=0.9, brow=False, vents=False, cheek=False, chin=False))
    k.add("head", gp.box_at((H.cx - 1.0, 0.0, zc + 11.5), (7.0, 2.4, 2.6), R_GLOW, ch=0.5))
    for s in (-1, 1):
        k.add("head", gp.box_at((H.cx - 0.5, s * (H.side(zc + 1.0) + 1.2), zc + 1.0), (6.0, 1.6, 4.0), R_ACCENT, ch=0.4))
    z0, z1, span = 118.0, 150.0, 56.0
    k.add("spine_05", gp.collar_ring(B, z=151.0, r=8.6, h=5.8, role=R_TRIM, thick=1.2))
    k.add("spine_05", gp.cuirass(B, role=R_PLATE, trim=R_TRIM, off_=1.3, thick=1.2, span=span, bulge=1.2, vneck=10, z0=z0, z1=z1))
    k.add("spine_05", glow_lines(B, 121.0, 148.0, (-22, -9, 9, 22), off_=2.5))
    k.add("spine_05", glow_lines(B, 121.0, 148.0, (158, 172, 188, 202), off_=2.5))
    bx = back_x(B, 135.0)
    k.add("spine_05", gp.box_at((bx - 3.0, 0.0, 135.0), (6.0, 18.0, 26.0), R_TRIM, ch=1.0))
    # a floating data cube and two small ones beside the left shoulder
    for j, (y, z, s) in enumerate(((-27.0, 158.0, 6.5), (-34.0, 148.0, 3.4), (-24.0, 170.0, 3.0))):
        k.add("spine_05", gp.box_at((bx + 12.0, y, z), (s, s, s), R_GLOW if j == 0 else R_ACCENT, ch=0.4, yaw=30 + j * 20, roll=25))
    k.pair("upperarm", gp.pauldron(B, big=0.9, layers=2, top_role=R_PLATE, lame_role=R_TRIM, thick=0.9, ridge=0.4, alpha=50))
    g = GM()
    g.append(gp.bracer(B, flare=1.0, accent=R_GLOW, thick=0.9, s0=4, s1=22, rings=True))
    g.append(gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 12.0, 4.6, 1.6, R_GLOW, thick=0.8))
    k.pair("lowerarm", g)
    k.add("pelvis", belt(B, z0=95.0, z1=101.0, role=R_TRIM, buckle=R_GLOW))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 10.0, 30.0, 10.0, 8.4, -50, 50, 0.9, R_TRIM, nv=4, nu=7, w=0.12, lo=0.4))
    kn = GM()
    kn.append(gp.greave(B, accent=R_GLOW, thick=1.0, s1=36.0))
    kn.append(gp.ring_at(B.bone("calf_l"), B.bone("foot_l"), 20.0, 6.6, 1.6, R_GLOW, thick=0.7))
    k.pair("calf", kn)
    return k


# ------------------------------------------------------------------------------------------------ 26 Chrome
def chrome(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.8, jaw=0.92)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_ACCENT, margin=1.8, slit_w=17.0, slit_h=2.6, jaw=0.92, brow=False, vents=False, cheek=False))
    k.add("head", gp.box_at((H.cx - 1.0, 0.0, zc + 10.8), (H.rx * 1.8, 1.6, 4.0), R_PLATE, ch=0.6, pitch=4, taper=0.5))
    z0, z1, span = 117.0, 151.0, 64.0
    k.add("spine_05", gp.collar_ring(B, z=151.0, r=8.2, h=5.0, role=R_PLATE, thick=1.2))
    k.add("spine_05", gp.cuirass(B, role=R_PLATE, trim=R_TRIM, off_=1.7, thick=1.5, span=span, bulge=2.0, vneck=9, z0=z0, z1=z1))
    k.add("spine_05", glow_lines(B, 120.0, 149.0, (-30, 0, 30), role=R_ACCENT, off_=3.2, w=2.0))
    k.add("spine_05", gp.box_at((back_x(B, 135.0) - 4.0, 0.0, 135.0), (8.0, 20.0, 26.0), R_PLATE, ch=1.4))
    for j, z in enumerate((101.0, 107.0, 113.0)):
        k.add("pelvis" if j == 0 else "spine_05", gp.torso_plate(B, z, z + 5.2, -34 + j * 3, 34 - j * 3, 1.3, 1.1, R_PLATE, nu=7, nv=2, w=0.3))
    k.pair("upperarm", gp.pauldron(B, big=1.05, layers=2, top_role=R_PLATE, lame_role=R_PLATE, thick=1.2, ridge=0.5, alpha=48))
    k.pair("lowerarm", gp.bracer(B, flare=1.1, accent=R_ACCENT, thick=1.1, s0=3, s1=23, rings=True))
    k.add("pelvis", belt(B, z0=95.0, z1=102.0, role=R_TRIM, buckle=R_ACCENT))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 9.0, 34.0, 10.6, 9.0, -70, 70, 1.2, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.2, s1=37.0))
    return k


# ------------------------------------------------------------------------------------------------ 27 Broker
def broker(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.8, z_bot=zc + 3.0, jaw=1.0)
    # a flat-topped hat with a wide brim
    k.add("head", H.shell(R_PLATE, sides=18, z_bot=zc + 3.0, caps=(False, True)))
    k.add("head", gp.cyl((H.cx, 0.0, zc + 2.6), (H.cx, 0.0, zc + 4.2), H.rx * 1.9 + 3.6, R_PLATE, sides=24))
    k.add("head", band_head(H, zc + 5.0, 2.0, R_ACCENT, off=0.4))
    # a gold monocle over the right eye, with a chain
    ex, ey, ez = H.front(zc + 1.0) + 1.0, 3.6, zc + 1.2
    k.add("head", gp.cyl((ex, ey, ez), (ex + 1.0, ey, ez), 3.6, R_ACCENT, sides=16))
    k.add("head", gp.cyl((ex + 0.6, ey, ez), (ex + 1.3, ey, ez), 2.7, R_GLOW, sides=16))
    k.add("head", _sweep([(ex, ey + 3.0, ez - 3.0), (ex - 1.0, ey + 5.0, ez - 9.0), (ex - 3.0, ey + 6.0, ez - 15.0)], [0.4, 0.4, 0.4], R_ACCENT, sides=5))
    z0, z1, span = 117.0, 150.0, 58.0
    k.add("spine_05", gp.collar_ring(B, z=150.0, r=8.0, h=4.6, role=R_CLOTH, thick=1.2))
    k.add("spine_05", gp.torso_plate(B, 112.0, 148.0, -50, 50, 1.4, 1.4, R_PLATE, nu=11, nv=7, w=0.15, bulge=gp.pec_bulge(1.0, 112, 148, 50)))
    k.add("spine_05", gp.torso_plate(B, 120.0, 148.0, -9, 9, 2.8, 0.7, R_ACCENT, nu=3, nv=5, w=0.3))
    for i in range(4):
        k.add("spine_05", gp.ball(B.tpt(138.0 - i * 6.0, 0, 3.6), 1.2, R_ACCENT, nu=6, nv=4))
    # a long coat: tails behind, a short front
    k.add("pelvis", gp.hang(B.tpt(100.0, 70, 1.8), B.tpt(100.0, 290, 1.8), (0.0, 0.0, -1.0), 70.0, R_CLOTH, out=(-1, 0, 0), taper=1.18, bulge=1.5, ripple=1.4, waves=1.5,
                            nu=10, nv=9, thick=0.6, stripes=[(0.0, 0.03, R_ACCENT), (0.97, 1.0, R_ACCENT)]))
    k.add("pelvis", belt(B, z0=96.0, z1=102.0, role=R_ACCENT, buckle=R_GLOW, thick=1.0))
    k.pair("upperarm", gp.pauldron(B, big=0.8, layers=2, top_role=R_CLOTH, lame_role=R_CLOTH, thick=0.9, ridge=0.3, alpha=50))
    g = GM()
    g.append(gp.bracer(B, flare=1.0, accent=R_ACCENT, thick=1.0, s0=4, s1=23, rings=True, role=R_CLOTH))
    g.append(gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 20.0, 5.0, 2.0, R_ACCENT, thick=0.8))
    k.pair("lowerarm", g)
    k.pair("calf", gp.greave(B, role=R_CLOTH, accent=R_ACCENT, thick=1.0, s1=36.0, knee=False))
    return k


# ------------------------------------------------------------------------------------------------ 28 Glitch
def glitch(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.8, jaw=0.9)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_GLOW, glow=R_GLOW, margin=1.8, slit_w=13.0, slit_h=3.0, jaw=0.9, brow=False, vents=False, cheek=False))
    # the shell is cut and shifted: a slab of it floats off to the side
    k.add("head", gp.box_at((H.cx + 0.5, 6.0, zc + 6.0), (H.rx * 1.2, 5.0, 7.0), R_ACCENT, ch=0.5, yaw=14, roll=10))
    k.add("head", gp.box_at((H.cx - 3.0, -9.0, zc + 12.0), (3.0, 3.0, 3.0), R_GLOW, ch=0.3, yaw=40, roll=30))
    z0, z1, span = 118.0, 150.0, 60.0
    # chest plates split in broken, shifted panels
    k.add("spine_05", gp.torso_plate(B, 126.0, 150.0, -60, -4, 1.6, 1.5, R_PLATE, nu=7, nv=4, w=0.2))
    k.add("spine_05", gp.torso_plate(B, 120.0, 142.0, 6, 60, 3.4, 1.5, R_PLATE, nu=7, nv=4, w=0.2))
    k.add("spine_05", gp.torso_plate(B, 118.0, 126.0, -52, 52, 2.4, 0.9, R_GLOW, nu=9, nv=2, w=0.3))
    k.add("spine_05", glow_lines(B, 122.0, 148.0, (-66, 66), role=R_GLOW, off_=2.0, w=3.0))
    k.add("spine_05", gp.torso_plate(B, 126.0, 150.0, 150, 210, 2.0, 1.4, R_PLATE, nu=7, nv=4, w=0.2))
    for j, (y, z) in enumerate(((22.0, 150.0), (-26.0, 138.0), (30.0, 122.0))):
        k.add("spine_05", gp.box_at((front_x(B, z, 6.0 + j * 2.0), y, z), (1.4, 6.0, 5.0), R_GLOW if j != 1 else R_ACCENT, ch=0.3, yaw=j * 15, roll=j * 20))
    k.add("pelvis", ring_strips(B, 96.0, 9, 34.0, R_CLOTH, rad_off=1.6, flare=0.25, wave=0.35, bands=[(0.86, 1.0, R_GLOW)], skip=((100, 150),)))
    k.add("pelvis", belt(B, z0=95.0, z1=100.0, role=R_TRIM, buckle=R_GLOW, thick=1.0))
    # one big pauldron on the right and nothing on the left
    k.add("upperarm_r", gp.pauldron(B, big=1.25, layers=3, top_role=R_PLATE, lame_role=R_ACCENT, thick=1.4, ridge=0.8, alpha=46).mirrored())
    k.add("lowerarm_l", gp.bracer(B, flare=1.5, accent=R_GLOW, thick=1.0, s0=3, s1=23, rings=True))
    k.add("calf_r", gp.greave(B, accent=R_GLOW, thick=1.1, s1=36.0).mirrored())
    k.add("calf_l", gp.ring_at(B.bone("calf_l"), B.bone("foot_l"), 20.0, 6.4, 1.6, R_GLOW, thick=0.7))
    return k
