"""Gear of the Legion characters (looks 21-24): Praetor, Auxilia, Signifer, Tribune. Each function takes the Body and returns a gear_parts.Kit."""

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_b import kneepad, elbow_pad, pouch
from gear_chars_c import ring_strips
from gear_chars_d import diag_band
from gear_parts import Kit, back_x, front_x
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT


def _cape(B, z, length, role, half=140.0, bulge=1.0, ripple=0.8, taper=1.1, stripes=()):
    return gp.hang(B.tpt(z, -half, 1.8), B.tpt(z, half, 1.8), (-0.14, 0.0, -1.0), length, role, out=(-1, 0, 0), taper=taper, bulge=bulge, ripple=ripple, waves=1.5,
                   nu=8, nv=9, thick=0.6, stripes=list(stripes))


# ------------------------------------------------------------------------------------------------ 21 Praetor
def praetor(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.9, jaw=0.94)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=1.9, slit_w=11.0, slit_h=1.8, jaw=0.94, brow=True, vents=False))
    ztop = zc + 10.5
    # a transverse crest across the top, from ear to ear
    k.add("head", gp.box_at((H.cx - 0.5, 0.0, ztop + 3.6), (3.0, H.side(zc + 6.0) * 2.0 + 4.0, 7.5), R_TEAM, ch=1.0, taper=0.9))
    k.add("head", gp.box_at((H.cx - 0.5, 0.0, ztop + 0.6), (4.6, 3.0, 3.0), R_ACCENT, ch=0.6))
    z0, z1, span = 117.0, 151.0, 68.0
    k.add("spine_05", gp.cuirass(B, off_=2.0, thick=2.0, span=span, bulge=2.8, vneck=7, z0=z0, z1=z1))
    for j, z in enumerate((101.0, 107.0, 113.0)):
        k.add("pelvis" if j == 0 else "spine_05", gp.torso_plate(B, z, z + 5.2, -34 + j * 3, 34 - j * 3, 1.4, 1.3, R_PLATE, nu=7, nv=2, w=0.3))
    k.add("spine_05", gp.torso_plate(B, 128.0, 131.0, -50, 50, 4.2, 1.0, R_ACCENT, nu=11, nv=2, w=0.3))
    k.add("spine_05", _cape(B, 148.0, 105.0, R_TEAM, stripes=[(0.0, 0.08, R_ACCENT)]))
    k.pair("upperarm", gp.pauldron(B, big=1.3, layers=3, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.5, ridge=1.0, alpha=46))
    k.pair("lowerarm", gp.bracer(B, flare=1.3, accent=R_ACCENT, thick=1.3, s0=3, s1=23, rings=True))
    k.add("pelvis", belt(B, z0=95.0, z1=102.0, role=R_ACCENT, buckle=R_TEAM))
    k.add("pelvis", ring_strips(B, 95.0, 14, 24.0, R_TEAM, rad_off=1.8, flare=0.22, bands=[(0.82, 1.0, R_ACCENT)]))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.5, s1=37.0))
    return k


# ------------------------------------------------------------------------------------------------ 22 Auxilia
def auxilia(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.6, z_bot=zc + 3.0, jaw=1.0)
    k.add("head", gp.helm_open(B, role=R_PLATE, trim=R_TRIM, cloth=R_CLOTH, margin=1.6, brim=2.6))
    k.add("head", gp.box_at((H.cx - 0.5, 0.0, zc + 12.5), (2.0, 2.4, 6.0), R_TEAM, ch=0.5))   # a short plume stub
    # a boiled-leather cuirass with metal bands and a team sash
    k.add("spine_05", gp.torso_plate(B, 118.0, 148.0, -50, 50, 1.5, 1.4, R_CLOTH, nu=11, nv=7, w=0.15, bulge=gp.pec_bulge(1.2, 118, 148, 50)))
    for z in (123.0, 130.0, 137.0, 144.0):
        k.add("spine_05", gp.torso_plate(B, z, z + 1.4, -50, 50, 2.9, 0.8, R_ACCENT, nu=11, nv=2, w=0.3))
    k.add("spine_05", diag_band(B, 150.0, 108.0, -50.0, 50.0, R_TEAM, off_=2.4, thick=1.0, steps=10, width=12.0))
    k.add("pelvis", belt(B, z0=95.0, z1=101.0, role=R_CLOTH, buckle=R_ACCENT))
    k.add("pelvis", ring_strips(B, 95.0, 12, 20.0, R_CLOTH, rad_off=1.6, flare=0.18, bands=[(0.8, 1.0, R_ACCENT)]))
    # the round shield, strapped over the left forearm
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    c = ((P0[0] + P1[0]) / 2 + 3.0, (P0[1] + P1[1]) / 2 - 5.2, (P0[2] + P1[2]) / 2 + 0.5)
    sh = GM()
    sh.append(gp.cyl((c[0], c[1] - 1.4, c[2]), (c[0], c[1] + 1.4, c[2]), 13.5, R_PLATE, sides=24))
    sh.append(gp.cyl((c[0], c[1] - 1.6, c[2]), (c[0], c[1] + 1.2, c[2]), 14.4, R_ACCENT, sides=24, caps=(True, False)))
    sh.append(gp.ball((c[0], c[1] - 2.2, c[2]), 3.6, R_ACCENT, nu=10, nv=5))
    sh.append(gp.cyl((c[0], c[1] - 1.7, c[2]), (c[0], c[1] - 2.0, c[2]), 8.0, R_TEAM, sides=24))
    k.add("lowerarm_l", sh)
    k.pair("upperarm", gp.pauldron(B, big=0.9, layers=3, top_role=R_CLOTH, lame_role=R_CLOTH, thick=1.0, ridge=0.5, alpha=50))
    k.add("lowerarm_r", gp.bracer(B, flare=1.0, accent=R_ACCENT, thick=1.0, s0=4, s1=22).mirrored())
    k.pair("calf", gp.greave(B, thick=1.1, knee=False, s1=35.0, arc=(-100, 100), accent=R_ACCENT))
    return k


# ------------------------------------------------------------------------------------------------ 23 Signifer
def signifer(B):
    k = Kit(B)
    zc = B.head_c[2]
    hd, H = gp.hood(B, role=R_CLOTH, margin=3.0, open_deg=58.0, back=0.4)
    k.add("head", hd)
    for s in (-1, 1):
        k.add("head", gp.spike((H.cx + 0.5, s * 6.0, zc + 9.0), (H.cx - 0.5, s * 7.5, zc + 16.0), 2.2, R_CLOTH))
    z0, z1, span = 118.0, 150.0, 64.0
    k.add("spine_05", gp.cuirass(B, off_=1.7, thick=1.7, span=span, bulge=2.2, vneck=8, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 126.0, 129.0, -48, 48, 3.5, 1.0, R_ACCENT, nu=11, nv=2, w=0.3))
    # the wolf pelt over the shoulders
    k.add("spine_05", gp.hang(B.tpt(149.0, -70, 3.0), B.tpt(149.0, 70, 3.0), (0.0, 0.0, -1.0), 20.0, R_CLOTH, out=(1, 0, 0), taper=0.7, bulge=3.0, ripple=1.5, waves=3.0,
                              nu=10, nv=4, thick=1.0))
    k.add("spine_05", gp.hang(B.tpt(149.0, -130, 2.6), B.tpt(149.0, 130, 2.6), (-0.1, 0.0, -1.0), 42.0, R_CLOTH, out=(-1, 0, 0), taper=0.8, bulge=2.5, ripple=1.8, waves=3.0,
                              nu=10, nv=6, thick=1.0))
    # the standard: a pole on the back, a crossbar, a banner and a gilded spear head
    bx = back_x(B, 130.0)
    px = bx - 9.0
    k.add("spine_05", gp.cyl((px, 10.0, 70.0), (px, 10.0, 214.0), 1.5, R_TRIM, sides=8))
    k.add("spine_05", gp.spike((px, 10.0, 214.0), (px, 10.0, 226.0), 3.0, R_ACCENT))
    k.add("spine_05", gp.cyl((px, -6.0, 202.0), (px, 26.0, 202.0), 1.0, R_ACCENT, sides=8))
    k.add("spine_05", gp.hang((px, -5.0, 201.0), (px, 25.0, 201.0), (0.0, 0.0, -1.0), 34.0, R_TEAM, out=(-1, 0, 0), taper=0.9, ripple=0.8, waves=1.5, nu=5, nv=7, thick=0.5,
                              stripes=[(0.1, 0.9, R_TEAM)]))
    k.add("spine_05", gp.ball((px, 10.0, 208.0), 2.4, R_ACCENT, nu=8, nv=5))
    k.add("spine_05", gp.box_at((px - 1.0, 10.0, 160.0), (2.0, 5.0, 3.0), R_ACCENT, ch=0.4))
    k.pair("upperarm", gp.pauldron(B, big=1.1, layers=3, top_role=R_PLATE, lame_role=R_CLOTH, thick=1.3, ridge=0.8, alpha=46))
    k.pair("lowerarm", gp.bracer(B, flare=1.1, accent=R_ACCENT, thick=1.1, s0=3, s1=23, rings=True))
    k.add("pelvis", belt(B, z0=95.0, z1=102.0, role=R_ACCENT, buckle=R_TEAM))
    k.add("pelvis", ring_strips(B, 95.0, 12, 22.0, R_CLOTH, rad_off=1.6, flare=0.2, bands=[(0.8, 1.0, R_ACCENT)]))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.2, s1=36.0))
    return k


# ------------------------------------------------------------------------------------------------ 24 Tribune
def tribune(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.8, jaw=0.94)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=1.8, slit_w=11.0, slit_h=1.6, jaw=0.94, brow=True, vents=False, fin=2.0))
    ztop = zc + 10.5
    plume = [(H.cx - 1.0, 0.0, ztop + 1.0), (H.cx - 1.0, 0.0, ztop + 10.0), (H.cx - 9.0, 0.0, ztop + 12.0), (H.cx - 17.0, 0.0, ztop + 5.0), (H.cx - 21.0, 0.0, ztop - 7.0)]
    k.add("head", _sweep(plume, [3.6, 4.4, 3.8, 3.0, 1.2], R_TEAM, sides=8, sy=0.5))
    z0, z1, span = 117.0, 151.0, 66.0
    k.add("spine_05", gp.cuirass(B, off_=1.8, thick=1.8, span=span, bulge=3.0, vneck=8, z0=z0, z1=z1))
    k.add("spine_05", diag_band(B, 150.0, 112.0, 52.0, -48.0, R_ACCENT, off_=3.5, thick=1.0, steps=10, width=12.0))
    for j, z in enumerate((101.0, 107.0, 113.0)):
        k.add("pelvis" if j == 0 else "spine_05", gp.torso_plate(B, z, z + 5.2, -34 + j * 3, 34 - j * 3, 1.4, 1.2, R_PLATE, nu=7, nv=2, w=0.3))
    # a short cape from the left shoulder only
    k.add("spine_05", gp.hang(B.tpt(149.0, -85, 2.0), B.tpt(149.0, -165, 2.0), (-0.1, -0.3, -1.0), 75.0, R_ACCENT, out=(0, -1, 0), taper=1.1, bulge=1.5, ripple=1.0, waves=1.5,
                              nu=6, nv=8, thick=0.6))
    k.pair("upperarm", gp.pauldron(B, big=1.2, layers=3, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.4, ridge=0.9, alpha=46))
    k.pair("lowerarm", gp.bracer(B, flare=1.3, accent=R_ACCENT, thick=1.2, s0=3, s1=23, rings=True))
    k.add("pelvis", belt(B, z0=95.0, z1=102.0, role=R_ACCENT, buckle=R_TEAM))
    k.add("pelvis", ring_strips(B, 95.0, 14, 22.0, R_PLATE, rad_off=1.8, flare=0.2, bands=[(0.82, 1.0, R_ACCENT)]))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 9.0, 34.0, 10.6, 9.0, -75, 75, 1.3, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.3, s1=37.0))
    return k
