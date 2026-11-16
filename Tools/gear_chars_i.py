"""Gear of the two story characters: Kestrel (look 15) and Sovereign (look 16). Each function takes the Body and returns a gear_parts.Kit."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_b import kneepad, elbow_pad, pouch
from gear_chars_c import ring_strips
from gear_chars_d import diag_band
from gear_parts import Kit, back_x, front_x, COS, SIN, rad
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT


# ------------------------------------------------------------------------------------------------ 15 Kestrel
def kestrel(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.7, z_bot=zc + 3.0, jaw=1.0)
    # a worn flat cap
    k.add("head", H.shell(R_CLOTH, sides=18, z_bot=zc + 2.8, caps=(False, True)))
    k.add("head", gp.box_at((H.front(zc + 4.0) + 2.2, 0.0, zc + 3.4), (6.0, H.side(zc + 4.0) * 1.7, 0.9), R_CLOTH, ch=0.35, pitch=-8, taper=0.8))
    # a scarf with a long tail
    k.add("spine_05", gp.collar_ring(B, z=148.5, r=9.4, h=6.0, role=R_ACCENT, thick=1.6))
    k.add("spine_05", gp.hang(B.tpt(147.0, 128, 2.6), B.tpt(147.0, 150, 2.6), (-0.2, 0.2, -1.0), 62.0, R_ACCENT, out=(-1, 0, 0), taper=0.8, ripple=1.0, waves=1.5, nu=3, nv=8, thick=0.6))
    # the coat: chest panel, a skirt to the knees, a belt
    k.add("spine_05", gp.torso_plate(B, 112.0, 148.0, -56, 56, 1.5, 1.6, R_CLOTH, nu=11, nv=7, w=0.15, bulge=gp.pec_bulge(1.0, 112, 148, 56)))
    k.add("spine_05", gp.torso_plate(B, 112.0, 148.0, -6, 6, 3.0, 0.8, R_TRIM, nu=2, nv=6, w=0.3))
    k.add("pelvis", ring_strips(B, 100.0, 14, 76.0, R_CLOTH, rad_off=2.0, flare=0.12, wave=0.1, bands=[(0.94, 1.0, R_TRIM)], nv=6, skip=((-18, 18),)))
    k.add("pelvis", belt(B, z0=95.0, z1=100.0, role=R_TRIM, buckle=R_ACCENT, thick=1.0))
    # a worn plate on the left shoulder only
    k.add("upperarm_l", gp.pauldron(B, big=1.1, layers=2, top_role=R_PLATE, lame_role=R_CLOTH, thick=1.4, ridge=0.5, alpha=46))
    k.pair("lowerarm", gp.bracer(B, flare=1.0, accent=R_ACCENT, thick=1.1, s0=4, s1=22, rings=True, role=R_CLOTH))
    cx = B.torso(98.0)[0]
    for s in (-1, 1):
        k.add("pelvis", pouch((cx + 5.0, s * 14.5, 97.0), (4.5, 6.0, 8.0), R_PLATE, R_TRIM, yaw=-s * 14))
    k.pair("calf", gp.greave(B, role=R_CLOTH, accent=R_ACCENT, thick=1.1, s1=35.0, knee=False, arc=(-100, 100)))
    return k


# ------------------------------------------------------------------------------------------------ 16 Sovereign
def sovereign(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.0, jaw=0.94)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.0, slit_w=12.0, slit_h=2.0, jaw=0.94, brow=True, vents=False))
    # a crown of spikes around the top
    ztop = zc + 10.0
    for i in range(7):
        a = -90.0 + i * 30.0
        base = (H.cx + (H.rx * 0.9) * COS(rad(a + 90.0)) * 0.0 + (H.rx * 0.85) * COS(rad(a)), (H.ry * 0.85) * SIN(rad(a)), ztop - 1.6)
        tip = (base[0] + (0.0 if i != 3 else 0.0), base[1], ztop + 6.0 + (4.0 if i % 2 == 0 else 0.0))
        k.add("head", gp.spike(base, tip, 1.6, R_ACCENT))
    k.add("head", band_head(H, ztop - 1.8, 2.0, R_ACCENT, off=0.4))
    k.add("spine_05", gp.collar_ring(B, z=151.0, r=9.6, h=5.0, role=R_ACCENT, thick=1.5))
    z0, z1, span = 116.0, 151.0, 72.0
    k.add("spine_05", gp.cuirass(B, off_=2.4, thick=2.4, span=span, bulge=3.0, vneck=7, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 127.0, 131.0, -58, 58, 4.9, 1.0, R_ACCENT, nu=11, nv=2, w=0.3))
    k.add("spine_05", gp.torso_plate(B, 120.0, 148.0, -9, 9, 5.0, 0.8, R_GLOW, nu=3, nv=5, w=0.3))
    for j, z in enumerate((101.0, 107.0, 113.0)):
        k.add("pelvis" if j == 0 else "spine_05", gp.torso_plate(B, z, z + 5.2, -34 + j * 3, 34 - j * 3, 1.5, 1.4, R_PLATE, nu=7, nv=2, w=0.3))
    # a very long cape, black with a gold edge
    k.add("spine_05", gp.hang(B.tpt(150.0, -145, 2.0), B.tpt(150.0, 145, 2.0), (-0.1, 0.0, -1.0), 140.0, R_CLOTH, out=(-1, 0, 0), taper=1.3, bulge=2.0, ripple=1.4, waves=2.0,
                              nu=9, nv=10, thick=0.7, stripes=[(0.0, 0.04, R_ACCENT), (0.96, 1.0, R_ACCENT)]))
    # a tabard hanging in front
    k.add("pelvis", gp.hang(B.tpt(100.0, -22, 2.4), B.tpt(100.0, 22, 2.4), (0.1, 0.0, -1.0), 52.0, R_ACCENT, out=(1, 0, 0), taper=0.8, ripple=0.4, waves=1.0, nu=4, nv=7, thick=0.6,
                            stripes=[(0.42, 0.58, R_GLOW)]))
    k.pair("upperarm", gp.pauldron(B, big=1.7, layers=4, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.7, ridge=1.3, spike=1.0, alpha=44))
    k.pair("lowerarm", gp.bracer(B, flare=1.6, accent=R_ACCENT, thick=1.5, s0=3, s1=24, rings=True))
    k.add("pelvis", belt(B, z0=94.0, z1=102.0, role=R_ACCENT, buckle=R_GLOW, thick=1.6))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 8.0, 34.0, 10.9, 9.2, -72, 72, 1.5, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.6, s1=37.0))
    return k
