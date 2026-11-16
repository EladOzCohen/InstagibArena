"""Gear of the Void Corps characters (looks 29-32): Apogee, Tether, Vanta, Perigee. Each function takes the Body and returns a gear_parts.Kit."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_b import kneepad, elbow_pad, pouch
from gear_chars_d import diag_band
from gear_chars_f import glow_lines
from gear_parts import Kit, back_x, front_x, COS, SIN, rad
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT


# ------------------------------------------------------------------------------------------------ 29 Apogee
def apogee(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 3.6, jaw=0.98)
    # a big domed helmet with a wide visor and a neck ring
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=3.6, slit_w=15.0, slit_h=7.0, jaw=0.98, brow=False, vents=False, cheek=False, chin=False))
    k.add("head", gp.ring_at((H.cx, 0.0, zc - 10.0), (H.cx, 0.0, zc + 10.0), 0.0, H.rx * 1.12 + 0.2, 1.8, R_ACCENT, sy=H.sy, thick=0.9))
    k.add("spine_05", gp.collar_ring(B, z=150.5, r=10.0, h=4.6, role=R_ACCENT, thick=1.4))
    z0, z1, span = 114.0, 151.0, 76.0
    k.add("spine_05", gp.cuirass(B, role=R_PLATE, trim=R_TRIM, off_=2.6, thick=2.8, span=span, bulge=3.0, vneck=3, z0=z0, z1=z1))
    k.add("spine_05", gp.box_at((front_x(B, 130.0, 5.0), 0.0, 130.0), (2.6, 14.0, 12.0), R_ACCENT, ch=0.9))
    for j in range(4):
        k.add("spine_05", gp.box_at((front_x(B, 130.0, 6.5), -4.5 + j * 3.0, 130.5 + (j % 2) * 3.0), (1.0, 1.8, 1.8), R_GLOW if j % 2 else R_TEAM, ch=0.2))
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 8.0, 0.0, 130.0), (16.0, 28.0, 36.0), R_PLATE, ch=2.0))
    for s in (-1, 1):
        k.add("spine_05", gp.cyl((bx - 12.0, s * 8.0, 112.0), (bx - 12.0, s * 8.0, 146.0), 4.0, R_ACCENT, sides=12))
        k.add("spine_05", gp.ball((bx - 12.0, s * 8.0, 146.0), 4.0, R_ACCENT, nu=10, nv=5))
    hose = [(bx - 4.0, -9.0, 150.0), (bx + 4.0, -15.0, 156.0), (bx + 12.0, -9.0, 152.0), (front_x(B, 146.0, 2.0), -7.0, 144.0)]
    k.add("spine_05", _sweep(hose, [1.3, 1.3, 1.3, 1.3], R_TRIM, sides=7))
    k.pair("upperarm", gp.pauldron(B, big=1.5, layers=3, top_role=R_PLATE, lame_role=R_PLATE, thick=1.8, ridge=1.0, alpha=44))
    k.pair("lowerarm", gp.bracer(B, flare=1.8, accent=R_ACCENT, thick=1.6, s0=2, s1=24, rings=True))
    k.add("pelvis", belt(B, z0=94.0, z1=102.0, role=R_ACCENT, buckle=R_TEAM, thick=1.6))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 6.0, 34.0, 11.6, 9.8, -80, 80, 1.8, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.8, s1=37.0))
    return k


# ------------------------------------------------------------------------------------------------ 30 Tether
def tether(B):
    k = Kit(B)
    zc = B.head_c[2]
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.2, slit_w=13.0, slit_h=3.0, jaw=0.92, brow=True, vents=False, fin=2.6))
    k.add("spine_05", gp.collar_ring(B, z=150.0, r=8.6, h=4.2, role=R_TRIM, thick=1.3))
    k.add("spine_05", gp.cuirass(B, role=R_PLATE, trim=R_TRIM, off_=1.6, thick=1.6, span=60.0, bulge=1.6, vneck=9, z0=118.0, z1=150.0))
    k.add("spine_05", diag_band(B, 150.0, 108.0, 52.0, -50.0, R_ACCENT, off_=3.2, thick=1.0, steps=9, width=12.0))
    k.add("spine_05", diag_band(B, 150.0, 108.0, -52.0, 50.0, R_ACCENT, off_=3.2, thick=1.0, steps=9, width=12.0))
    k.add("spine_05", gp.ball(B.tpt(130.0, 0, 3.4), 2.2, R_TRIM, nu=8, nv=5))
    bx = back_x(B, 132.0)
    # the grapple pack: a box, a spool and a launcher pointing up and back
    k.add("spine_05", gp.box_at((bx - 5.0, 0.0, 130.0), (10.0, 24.0, 28.0), R_TRIM, ch=1.4))
    k.add("spine_05", gp.cyl((bx - 11.0, -9.0, 124.0), (bx - 11.0, 9.0, 124.0), 7.0, R_ACCENT, sides=16))
    k.add("spine_05", gp.cyl((bx - 11.0, -9.5, 124.0), (bx - 11.0, 9.5, 124.0), 3.4, R_TRIM, sides=10))
    k.add("spine_05", gp.cyl((bx - 4.0, 0.0, 140.0), (bx - 14.0, 0.0, 168.0), 2.3, R_TRIM, sides=10))
    k.add("spine_05", gp.spike((bx - 14.0, 0.0, 168.0), (bx - 16.0, 0.0, 176.0), 2.0, R_ACCENT))
    cableA = [(bx - 11.0, 9.0, 124.0), (bx - 14.0, 22.0, 112.0), (bx - 6.0, 28.0, 96.0), (bx + 6.0, 24.0, 90.0)]
    k.add("spine_05", _sweep(cableA, [1.0, 1.0, 1.0, 1.0], R_ACCENT, sides=6))
    k.pair("upperarm", gp.pauldron(B, big=1.0, layers=2, top_role=R_PLATE, lame_role=R_TRIM, thick=1.2, ridge=0.6, alpha=48))
    g = GM()
    g.append(gp.bracer(B, flare=1.2, accent=R_ACCENT, thick=1.1, s0=3, s1=23, rings=True))
    g.append(gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 12.0, 4.8, 2.4, R_ACCENT, thick=0.8))
    k.pair("lowerarm", g)
    cx = B.torso(98.0)[0]
    k.add("pelvis", belt(B, z0=94.0, z1=102.0, role=R_TRIM, buckle=R_ACCENT))
    for s in (-1, 1):
        k.add("pelvis", gp.cyl((cx + 4.0, s * 14.0, 92.0), (cx + 4.0, s * 18.0, 92.0), 4.4, R_ACCENT, sides=12))
        k.add("pelvis", pouch((cx - 3.0, s * 16.0, 99.0), (4.5, 5.0, 8.0), R_PLATE, R_TRIM, yaw=s * 14))
    k.pair("calf", kneepad(B, R_ACCENT, R_TRIM, 1.0))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.2, s1=36.0, knee=False))
    return k


# ------------------------------------------------------------------------------------------------ 31 Vanta
def vanta(B):
    k = Kit(B)
    zc = B.head_c[2]
    hd, H = gp.hood(B, role=R_CLOTH, margin=2.0, open_deg=62.0, back=0.2, z_bot=zc - 9.5, jaw=0.92)
    k.add("head", hd)
    k.add("head", gp.box_at((H.front(zc + 1.8) + 0.2, 0.0, zc + 1.8), (1.0, 11.0, 1.6), R_GLOW, ch=0.3))
    k.add("head", gp.box_at((H.front(zc - 4.0) - 0.3, 0.0, zc - 4.0), (2.4, H.side(zc - 4.0) * 1.7, 7.0), R_TRIM, ch=0.7))
    k.add("spine_05", gp.collar_ring(B, z=150.0, r=8.0, h=5.0, role=R_CLOTH, thick=1.1))
    k.add("spine_05", gp.torso_plate(B, 117.0, 149.0, -52, 52, 1.1, 1.0, R_PLATE, nu=11, nv=6, w=0.15, bulge=gp.pec_bulge(1.0, 117, 149, 52)))
    k.add("spine_05", glow_lines(B, 119.0, 148.0, (-34, -14, 14, 34), off_=2.1, w=1.8))
    k.add("spine_05", glow_lines(B, 119.0, 148.0, (156, 168, 192, 204), off_=2.1, w=1.8))
    k.add("spine_05", gp.hang(B.tpt(148.0, 140, 1.6), B.tpt(148.0, 220, 1.6), (-0.15, 0.0, -1.0), 62.0, R_CLOTH, out=(-1, 0, 0), taper=1.2, ripple=1.0, waves=1.5, nu=5, nv=8, thick=0.5))
    k.pair("upperarm", gp.pauldron(B, big=0.85, layers=2, top_role=R_TRIM, lame_role=R_CLOTH, thick=0.8, ridge=0.3, alpha=52))
    g = GM()
    g.append(gp.bracer(B, flare=0.9, accent=R_GLOW, thick=0.8, s0=4, s1=22, rings=True, role=R_TRIM))
    g.append(gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 10.0, 4.3, 1.2, R_GLOW, thick=0.6))
    k.pair("lowerarm", g)
    k.add("pelvis", belt(B, z0=95.0, z1=100.0, role=R_TRIM, buckle=R_GLOW, thick=0.9))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 10.0, 30.0, 9.6, 8.2, -45, 45, 0.8, R_TRIM, nv=4, nu=7, w=0.12, lo=0.4))
    kn = GM()
    kn.append(gp.greave(B, role=R_TRIM, accent=R_GLOW, thick=0.9, s1=36.0, knee=False))
    kn.append(gp.ring_at(B.bone("calf_l"), B.bone("foot_l"), 20.0, 6.2, 1.2, R_GLOW, thick=0.6))
    k.pair("calf", kn)
    return k


# ------------------------------------------------------------------------------------------------ 32 Perigee
def perigee(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.0, jaw=0.94)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.0, slit_w=10.0, slit_h=2.0, jaw=0.94, brow=True, vents=False))
    # a long scope over the right eye
    sx, sy, sz = H.front(zc + 2.0) + 0.5, 5.2, zc + 2.8
    k.add("head", gp.cyl((sx - 1.5, sy, sz), (sx + 13.0, sy, sz), 2.0, R_TRIM, sides=10))
    k.add("head", gp.cyl((sx + 11.0, sy, sz), (sx + 14.0, sy, sz), 2.8, R_ACCENT, sides=10))
    k.add("head", gp.ball((sx + 14.2, sy, sz), 1.9, R_GLOW, nu=8, nv=5))
    k.add("head", gp.box_at((sx + 1.0, sy - 2.0, sz - 1.0), (3.0, 3.0, 1.6), R_TRIM, ch=0.4))
    k.add("spine_05", gp.collar_ring(B, z=150.0, r=8.6, h=4.6, role=R_TRIM, thick=1.3))
    k.add("spine_05", gp.cuirass(B, role=R_PLATE, trim=R_TRIM, off_=1.7, thick=1.7, span=60.0, bulge=1.8, vneck=8, z0=118.0, z1=150.0))
    k.add("spine_05", gp.torso_plate(B, 126.0, 129.0, -48, 48, 3.3, 1.0, R_ACCENT, nu=9, nv=2, w=0.3))
    # a scarf hanging down the back
    k.add("spine_05", gp.hang(B.tpt(150.0, 150, 2.4), B.tpt(150.0, 210, 2.4), (-0.2, 0.0, -1.0), 70.0, R_ACCENT, out=(-1, 0, 0), taper=0.9, ripple=1.4, waves=1.5, nu=4, nv=8, thick=0.5))
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 4.0, 0.0, 132.0), (8.0, 18.0, 24.0), R_TRIM, ch=1.2))
    # a rifle rack on the back: one long tube
    k.add("spine_05", gp.cyl((bx - 7.0, -4.0, 96.0), (bx - 9.0, 8.0, 166.0), 1.6, R_TRIM, sides=8))
    k.pair("upperarm", gp.pauldron(B, big=1.05, layers=2, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.3, ridge=0.6, alpha=48))
    k.pair("lowerarm", gp.bracer(B, flare=1.1, accent=R_ACCENT, thick=1.1, s0=3, s1=23, rings=True))
    cx = B.torso(98.0)[0]
    k.add("pelvis", belt(B, z0=94.0, z1=102.0, role=R_TRIM, buckle=R_ACCENT))
    for s in (-1, 1):
        for j in range(3):
            k.add("pelvis", gp.box_at((cx + 4.0, s * (13.0 + j * 2.8), 96.0), (2.4, 2.2, 8.0), R_ACCENT, ch=0.4))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 9.0, 34.0, 10.6, 9.0, -70, 70, 1.2, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.3, s1=37.0))
    return k
