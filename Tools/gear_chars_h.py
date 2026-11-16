"""Gear of the Hollow Court characters (looks 33-36): Oni, Jackal, Gorgon, Wraith. Each function takes the Body and returns a gear_parts.Kit."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_c import ring_strips
from gear_chars_d import diag_band
from gear_parts import Kit, back_x, front_x, COS, SIN, rad
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT


# ------------------------------------------------------------------------------------------------ 33 Oni
def oni(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.2, jaw=0.95)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.2, slit_w=12.0, slit_h=2.4, jaw=0.95, brow=True, vents=False, chin=False))
    # two big horns and a fanged lower face
    for s in (-1, 1):
        k.add("head", gp.horn((H.cx + 1.0, s * 6.0, zc + 8.0), (H.cx + 2.0, s * 15.0, zc + 16.0), (H.cx + 6.0, s * 13.0, zc + 30.0), 2.6, R_LIGHT, n=9, sides=8))
        k.add("head", gp.spike((H.front(zc - 5.0) - 0.5, s * 3.6, zc - 5.0), (H.front(zc - 5.0) + 0.5, s * 3.0, zc - 10.5), 1.3, R_LIGHT))
    k.add("head", gp.box_at((H.front(zc - 6.5) + 0.3, 0.0, zc - 6.5), (2.0, 9.0, 3.6), R_TRIM, ch=0.6))
    z0, z1, span = 117.0, 151.0, 70.0
    k.add("spine_05", gp.cuirass(B, off_=2.2, thick=2.2, span=span, bulge=2.6, vneck=6, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 130.0, 133.0, -58, 58, 4.6, 1.0, R_ACCENT, nu=11, nv=2, w=0.3))
    # a heavy robe: panels front and back from the belt, wide sleeves of cloth at the shoulders
    k.add("pelvis", ring_strips(B, 97.0, 12, 55.0, R_CLOTH, rad_off=2.0, flare=0.3, bands=[(0.9, 1.0, R_ACCENT)], skip=((-30, 30),)))
    k.add("pelvis", gp.hang(B.tpt(98.0, -26, 2.2), B.tpt(98.0, 26, 2.2), (0.1, 0.0, -1.0), 62.0, R_TEAM, out=(1, 0, 0), taper=0.95, ripple=0.6, waves=1.0, nu=4, nv=8, thick=0.6,
                            stripes=[(0.0, 0.1, R_ACCENT), (0.9, 1.0, R_ACCENT)]))
    k.pair("upperarm", gp.pauldron(B, big=1.5, layers=3, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.6, ridge=1.2, spike=1.2, alpha=44))
    k.pair("lowerarm", gp.bracer(B, flare=2.0, accent=R_ACCENT, thick=1.5, s0=2, s1=24, rings=True, role=R_CLOTH))
    k.add("pelvis", belt(B, z0=94.0, z1=102.0, role=R_ACCENT, buckle=R_TRIM, thick=1.6))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.5, s1=37.0))
    return k


# ------------------------------------------------------------------------------------------------ 34 Jackal
def jackal(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.0, jaw=0.9)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.0, slit_w=8.0, slit_h=1.8, jaw=0.9, brow=True, vents=False, chin=False, cheek=False))
    # the jackal head: a long snout and two tall ears
    fx = H.front(zc - 1.0)
    k.add("head", gp.box_at((fx + 6.0, 0.0, zc - 2.6), (13.0, 6.4, 5.2), R_PLATE, ch=1.2, pitch=-6, taper=0.55))
    k.add("head", gp.box_at((fx + 13.0, 0.0, zc - 3.6), (3.0, 3.6, 3.0), R_TRIM, ch=0.8))
    k.add("head", gp.box_at((fx + 5.0, 0.0, zc - 6.4), (11.0, 5.2, 1.6), R_TRIM, ch=0.5, taper=0.6))
    for s in (-1, 1):
        k.add("head", gp.spike((H.cx - 1.0, s * 6.0, zc + 8.0), (H.cx - 3.0, s * 9.0, zc + 28.0), 3.4, R_PLATE))
        k.add("head", gp.spike((H.cx - 1.4, s * 6.0, zc + 9.0), (H.cx - 3.4, s * 8.6, zc + 24.0), 1.6, R_ACCENT))
    # the gold collar
    k.add("spine_05", gp.collar_ring(B, z=149.0, r=10.4, h=6.0, role=R_ACCENT, thick=1.6))
    z0, z1, span = 118.0, 150.0, 66.0
    k.add("spine_05", gp.cuirass(B, off_=1.9, thick=1.9, span=span, bulge=2.4, vneck=8, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 124.0, 128.0, -54, 54, 4.0, 1.0, R_ACCENT, nu=11, nv=2, w=0.3))
    k.add("spine_05", gp.hang(B.tpt(148.0, 120, 1.8), B.tpt(148.0, 240, 1.8), (-0.12, 0.0, -1.0), 85.0, R_CLOTH, out=(-1, 0, 0), taper=1.1, ripple=0.8, waves=1.5, nu=6, nv=8,
                              thick=0.6, stripes=[(0.0, 0.05, R_ACCENT), (0.95, 1.0, R_ACCENT)]))
    k.add("pelvis", ring_strips(B, 96.0, 12, 30.0, R_CLOTH, rad_off=1.8, flare=0.22, bands=[(0.82, 1.0, R_ACCENT)]))
    k.add("pelvis", belt(B, z0=95.0, z1=102.0, role=R_ACCENT, buckle=R_TRIM))
    k.pair("upperarm", gp.pauldron(B, big=1.25, layers=3, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.4, ridge=0.9, alpha=46))
    k.pair("lowerarm", gp.bracer(B, flare=1.3, accent=R_ACCENT, thick=1.2, s0=3, s1=23, rings=True))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.4, s1=37.0))
    return k


# ------------------------------------------------------------------------------------------------ 35 Gorgon
def gorgon(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.9, jaw=0.9)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=1.9, slit_w=11.0, slit_h=2.4, jaw=0.9, brow=True, vents=False, cheek=False))
    # nine serpents rising from the crown
    for i in range(9):
        a = -80.0 + i * 20.0
        base = H.pt(zc + 8.0, a * 1.1 + 180.0 * (1 if abs(a) > 60 else 0), 0.3) if False else (H.cx - 2.0 + 2.0 * COS(rad(a)), 6.0 * SIN(rad(a)), zc + 9.5)
        out = (-5.0 * abs(COS(rad(a))) - 3.0, 12.0 * SIN(rad(a)), zc + 18.0 + (i % 3) * 3.0)
        tip = (out[0] - 6.0 * (1 + (i % 2)), out[1] * 1.5, zc + 22.0 + (i % 3) * 4.0 - (i % 2) * 8.0)
        k.add("head", _sweep([base, out, tip], [1.7, 1.5, 0.5], R_ACCENT if i % 3 == 0 else R_PLATE, sides=7))
    z0, z1, span = 118.0, 150.0, 62.0
    k.add("spine_05", gp.collar_ring(B, z=150.0, r=8.4, h=4.4, role=R_ACCENT, thick=1.2))
    # scale armour: overlapping bands that alternate in colour
    for j in range(8):
        z = 121.0 + j * 3.8
        k.add("spine_05", gp.torso_plate(B, z, z + 4.6, -52, 52, 1.5 + (j % 2) * 0.5, 1.0, R_PLATE if j % 2 == 0 else R_ACCENT, nu=11, nv=2, w=0.25,
                                         bulge=gp.pec_bulge(1.2, 118, 150, 52)))
    for j in range(5):
        z = 103.0 + j * 3.4
        k.add("pelvis", gp.torso_plate(B, z, z + 4.2, -36, 36, 1.2, 1.0, R_PLATE if j % 2 == 0 else R_ACCENT, nu=9, nv=2, w=0.25))
    k.add("pelvis", ring_strips(B, 97.0, 12, 38.0, R_CLOTH, rad_off=1.8, flare=0.24, bands=[(0.78, 1.0, R_ACCENT)], taper=0.5))
    k.add("pelvis", belt(B, z0=95.0, z1=100.0, role=R_ACCENT, buckle=R_GLOW, thick=1.0))
    k.pair("upperarm", gp.pauldron(B, big=0.95, layers=3, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.1, ridge=0.6, alpha=50))
    k.pair("lowerarm", gp.bracer(B, flare=1.0, accent=R_ACCENT, thick=1.0, s0=3, s1=23, rings=True))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.1, s1=36.0))
    return k


# ------------------------------------------------------------------------------------------------ 36 Wraith
def wraith(B):
    k = Kit(B)
    zc = B.head_c[2]
    hd, H = gp.hood(B, role=R_CLOTH, margin=3.4, open_deg=48.0, back=0.5, z_bot=zc - 12.0, jaw=1.05)
    k.add("head", hd)
    # the pale mask inside the hood
    k.add("head", gp.box_at((H.front(zc + 0.5) + 0.2, 0.0, zc + 0.5), (1.6, 10.5, 15.0), R_LIGHT, ch=0.8, taper=0.85))
    for s in (-1, 1):
        k.add("head", gp.box_at((H.front(zc + 2.2) + 1.0, s * 2.8, zc + 2.2), (0.8, 2.2, 1.0), R_GLOW, ch=0.2))
    k.add("head", gp.box_at((H.front(zc - 4.0) + 1.0, 0.0, zc - 4.0), (0.8, 1.2, 4.0), R_TRIM, ch=0.2))
    k.add("spine_05", gp.torso_plate(B, 114.0, 150.0, -60, 60, 1.6, 1.4, R_CLOTH, nu=11, nv=5, w=0.2, bulge=gp.pec_bulge(1.0, 114, 150, 60)))
    # a robe all the way to the ankles, and a cloak
    k.add("pelvis", ring_strips(B, 100.0, 14, 92.0, R_CLOTH, rad_off=2.0, flare=0.12, wave=0.18, bands=[(0.92, 1.0, R_ACCENT)], nv=7))
    k.add("spine_05", gp.hang(B.tpt(150.0, -150, 2.4), B.tpt(150.0, 150, 2.4), (-0.15, 0.0, -1.0), 110.0, R_CLOTH, out=(-1, 0, 0), taper=1.2, bulge=2.0, ripple=1.8, waves=2.0,
                              nu=9, nv=10, thick=0.7, stripes=[(0.0, 0.05, R_ACCENT)]))
    k.pair("upperarm", gp.pauldron(B, big=1.1, layers=2, top_role=R_CLOTH, lame_role=R_CLOTH, thick=1.4, ridge=0.5, alpha=48))
    k.pair("lowerarm", gp.bracer(B, flare=3.0, accent=R_ACCENT, thick=1.1, s0=2, s1=25, rings=False, role=R_CLOTH))
    k.add("pelvis", belt(B, z0=95.0, z1=100.0, role=R_ACCENT, buckle=R_LIGHT, thick=1.0))
    k.pair("calf", gp.greave(B, role=R_CLOTH, accent=R_ACCENT, thick=1.0, s1=36.0, knee=False))
    return k
