"""Gear of the campaign characters (looks 15-36). Each function takes the Body and returns a gear_parts.Kit.
15 Kestrel, 16 Sovereign | Rustborn 17-20 | Legion 21-24 | Syndicate 25-28 | Void Corps 29-32 | Hollow Court 33-36."""

import math

import gear_parts as gp
import mesh_char as mc
from gear_chars_a import belt, band_head, _sweep
from gear_chars_b import kneepad, elbow_pad, pouch
from gear_parts import Kit, back_x, front_x, rad, SIN, COS
from mesh_char import GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT, fr


def diag_band(B, z_top, z_bot, ang_top, ang_bot, role, off_=1.3, thick=1.0, steps=9, width=14.0):
    """A strap across the chest running from angle ang_top at z_top down to ang_bot at z_bot (angles on the torso: 0 front, +90 right)."""
    m = GM()
    dz = (z_top - z_bot) / steps
    for i in range(steps):
        t = (i + 0.5) / steps
        a = ang_top + (ang_bot - ang_top) * t
        z1 = z_top - i * dz
        m.append(gp.torso_plate(B, z1 - dz - 0.4, z1, a - width / 2, a + width / 2, off_, thick, role, nu=3, nv=2, w=0.25))
    return m


def spikes_ring(H, z, count, a0, a1, length, r, role, off=0.5, droop=0.0):
    m = GM()
    for i in range(count):
        a = a0 + (a1 - a0) * i / max(1, count - 1)
        base = H.pt(z, a, off)
        tip = H.pt(z, a, off + length)
        tip = (tip[0], tip[1], tip[2] - droop)
        m.append(gp.spike(base, tip, r, role))
    return m


# ------------------------------------------------------------------------------------------------ 17 Scrapjaw
def scrapjaw(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.4, jaw=0.95)
    k.add("head", gp.helm_full(B, role=R_PLATE, margin=2.4, slit_w=13.0, jaw=0.95, accent=R_ACCENT))
    k.add("head", spikes_ring(H, zc - 6.5, 7, -75, 75, 3.6, 0.9, R_ACCENT, off=1.0, droop=1.2))
    for a in (-40.0, 40.0):
        k.add("head", gp.horn(H.pt(zc + 6, a, 1.0), H.pt(zc + 9, a * 1.5, 4.0), H.pt(zc + 15, a * 1.8, 6.5), 1.4, R_TRIM))
    z0, z1, span = 118.0, 150.0, 72.0
    k.add("spine_05", gp.cuirass(B, off_=2.2, thick=2.4, span=span, bulge=2.2, vneck=6, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 125.0, 139.0, 18, 62, 4.2, 1.2, R_ACCENT, nu=5, nv=3, w=0.3))  # a welded rust patch
    k.add("spine_05", gp.box_at((front_x(B, 134.0, 4.0), -9.0, 134.0), (1.6, 10.0, 7.0), R_TRIM, ch=0.5, yaw=-4, roll=8))
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 4.0, 0.0, 130.0), (9.0, 28.0, 30.0), R_PLATE, ch=1.2, yaw=3))
    k.add("spine_05", gp.box_at((bx - 9.0, -6.0, 134.0), (2.0, 15.0, 18.0), R_ACCENT, ch=0.6, roll=6))
    for s in (-1, 1):
        k.add("spine_05", gp.cyl((bx - 9.0, s * 11.0, 112.0), (bx - 12.0, s * 12.0, 150.0), 2.4, R_TRIM, sides=9))
    k.pair("upperarm", gp.pauldron(B, big=1.6, layers=2, top_role=R_ACCENT, lame_role=R_PLATE, thick=1.8, ridge=1.6, spike=1.1, alpha=44))
    k.pair("lowerarm", gp.bracer(B, flare=1.5, accent=R_ACCENT, thick=1.5, s0=3, s1=24, rings=True))
    k.add("pelvis", belt(B, z0=94.0, z1=102.0, role=R_ACCENT, thick=1.6))
    cx = B.torso(92.0)[0]
    for s in (-1, 1):
        k.add("pelvis", gp.box_at((cx + 1.0, s * 18.0, 88.0), (10.0, 3.4, 18.0), R_PLATE, ch=0.9, roll=s * 6))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 8.0, 33.0, 11.2, 9.4, -70, 70, 1.6, R_PLATE, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.7, s1=37.0))
    kn = GM()
    kn.append(kneepad(B, R_TRIM, R_PLATE, 1.25))
    f = mc.frame_z(B.bone("calf_l"), B.bone("foot_l"))
    kn.append(gp.spike(f.pt((10.5, 0.0, -0.5)), f.pt((17.0, 0.0, -0.5)), 1.5, R_ACCENT))
    k.pair("calf", kn)
    return k


# ------------------------------------------------------------------------------------------------ 18 Rivet
def rivet(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 1.7, z_bot=zc + 3.0, jaw=1.0)
    k.add("head", H.shell(R_CLOTH, sides=18, z_bot=zc + 2.5, caps=(False, True)))
    k.add("head", band_head(H, zc + 4.2, 2.2, R_ACCENT, off=0.4))
    knot = (H.cx - H.rx * 0.95, 4.0, zc + 5.0)
    for s, (dy, dz) in enumerate(((-3.0, -9.0), (2.0, -13.0))):
        k.add("head", gp.hang((H.cx - H.rx * 0.9, -1.5, zc + 5.0), (H.cx - H.rx * 0.9, 1.5, zc + 5.0), (-0.4, dy * 0.2, dz * 0.1 - 1.0), 12.0 - s * 3, R_ACCENT,
                              out=(-1, 0, 0), taper=0.8, ripple=1.0, waves=1.2, nu=2, nv=5, thick=0.4))
    k.add("head", gp.goggles(B, z=zc + 7.8, H=H, x_off=H.front(zc + 7.8) - 0.8, role_lens=R_LIGHT, role_rim=R_TRIM, r=2.8, rim_r=3.5, spread=4.7, tilt=20, strap_role=R_TRIM,
                             strap=False))
    # a bandolier of bolts and a second strap, light chest plate, tool pouches
    k.add("spine_05", diag_band(B, 150.0, 106.0, 55.0, -55.0, R_PLATE, thick=1.2))
    k.add("spine_05", diag_band(B, 146.0, 112.0, 40.0, -40.0, R_CLOTH, off_=1.0, thick=0.8, width=10.0))
    for i in range(7):
        t = i / 6.0
        z = 144.0 - t * 34.0
        ang = 52.0 - t * 104.0
        k.add("spine_05", gp.ball(B.tpt(z, ang, 2.6), 1.15, R_ACCENT, nu=6, nv=4))
    k.add("spine_05", gp.torso_plate(B, 118.0, 140.0, -42, 42, 1.0, 1.0, R_CLOTH, nu=9, nv=4, w=0.2))
    cx = B.torso(96.0)[0]
    k.add("pelvis", belt(B, z0=96.0, z1=102.0, role=R_CLOTH, buckle=R_ACCENT))
    for s in (-1, 1):
        k.add("pelvis", pouch((cx + 5.0, s * 14.0, 97.0), (4.5, 6.0, 8.0), R_PLATE, R_TRIM, yaw=-s * 20))
    k.add("pelvis", pouch((cx - 7.5, 0.0, 99.0), (4.0, 12.0, 8.0), R_CLOTH, R_ACCENT))
    # one big pauldron on the left only
    k.add("upperarm_l", gp.pauldron(B, big=1.1, layers=2, top_role=R_PLATE, lame_role=R_CLOTH, thick=1.2, ridge=0.8, alpha=46))
    fa = GM()
    fa.append(gp.bracer(B, flare=1.0, accent=R_ACCENT, thick=1.0, s0=4, s1=22, rings=True))
    fa.append(elbow_pad(B, R_ACCENT, 0.9))
    k.pair("lowerarm", fa)
    k.pair("calf", kneepad(B, R_ACCENT, R_TRIM, 1.0))
    k.pair("calf", gp.greave(B, thick=1.0, knee=False, s1=34.0, arc=(-100, 100), accent=R_ACCENT))
    return k


# ------------------------------------------------------------------------------------------------ 19 Flux
def flux(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.0, jaw=0.95)
    k.add("head", gp.helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.0, slit_w=15.0, slit_h=3.4, jaw=0.95, brow=False, vents=False))
    # a flip-up visor frame above the slit and cable clips on the sides
    k.add("head", gp.box_at((H.front(zc + 5.2) + 1.0, 0.0, zc + 5.2), (3.6, H.side(zc + 5.2) * 2.15, 4.0), R_TRIM, ch=0.9, pitch=-14, taper=0.9))
    for s in (-1, 1):
        k.add("head", gp.cyl((H.cx + 1.0, s * (H.side(zc) + 1.5), zc + 6.0), (H.cx + 1.0, s * (H.side(zc) + 1.5), zc - 4.0), 1.5, R_ACCENT, sides=8))
    z0, z1, span = 118.0, 150.0, 62.0
    k.add("spine_05", gp.cuirass(B, off_=1.6, thick=1.7, span=span, bulge=1.6, vneck=8, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 126.0, 128.2, -52, 52, 3.2, 0.9, R_GLOW, nu=9, nv=2, w=0.3))
    # welder's apron: cloth from the chest to the knees with an accent hem
    k.add("spine_05", gp.hang(B.tpt(128.0, -34, 3.4), B.tpt(128.0, 34, 3.4), (0.15, 0.0, -1.0), 66.0, R_CLOTH, out=(1, 0, 0), taper=1.05, bulge=1.2, ripple=0.4, waves=1.0,
                              nu=6, nv=8, thick=0.6, stripes=[(0.0, 1.0, R_CLOTH)]))
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 5.0, 0.0, 130.0), (11.0, 23.0, 28.0), R_TRIM, ch=1.4))
    for s in (-1, 1):
        k.add("spine_05", gp.cyl((bx - 6.0, s * 6.5, 119.0), (bx - 6.0, s * 6.5, 150.0), 3.6, R_ACCENT, sides=12))
        k.add("spine_05", gp.ball((bx - 6.0, s * 6.5, 150.5), 3.6, R_ACCENT, nu=10, nv=5))
    cable = ((bx - 10.0, 0.0, 138.0), (bx - 14.0, 14.0, 128.0), (bx - 6.0, 26.0, 110.0), (bx + 6.0, 26.0, 98.0))
    k.add("spine_05", _sweep(list(cable), [1.2, 1.2, 1.2, 1.2], R_TRIM, sides=7))
    k.pair("upperarm", gp.pauldron(B, big=1.1, layers=2, top_role=R_PLATE, lame_role=R_TRIM, thick=1.2, ridge=0.7, alpha=48))
    g = GM()
    g.append(gp.bracer(B, flare=1.9, accent=R_GLOW, thick=1.3, s0=2, s1=23, rings=True))
    g.append(gp.ring_at(B.bone("lowerarm_l"), B.bone("hand_l"), 21.0, 5.6, 2.2, R_GLOW, thick=1.0))
    k.pair("lowerarm", g)
    k.add("pelvis", belt(B, z0=94.0, z1=102.0, role=R_TRIM, buckle=R_GLOW))
    k.pair("calf", gp.greave(B, accent=R_ACCENT, thick=1.2, s1=36.0))
    return k


# ------------------------------------------------------------------------------------------------ 20 Torch
def torch(B):
    k = Kit(B)
    zc = B.head_c[2]
    H = gp.Helm(B, 2.3, jaw=0.98)
    k.add("head", gp.helm_full(B, role=R_CLOTH, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=2.3, slit_w=11.0, slit_h=2.6, jaw=0.98, brow=True, vents=False, chin=False))
    # respirator: a snout with two round filters
    xf = H.front(zc - 5.0)
    k.add("head", gp.box_at((xf + 0.5, 0.0, zc - 5.0), (5.0, 8.0, 6.0), R_TRIM, ch=1.2, taper=0.8))
    for s in (-1, 1):
        k.add("head", gp.cyl((xf - 1.0, s * 5.0, zc - 5.5), (xf + 1.0, s * 6.4, zc - 5.5), 2.5, R_ACCENT, sides=12))
    z0, z1, span = 116.0, 151.0, 70.0
    k.add("spine_05", gp.cuirass(B, role=R_CLOTH, trim=R_TRIM, off_=2.4, thick=2.6, span=span, bulge=3.0, vneck=5, z0=z0, z1=z1))
    k.add("spine_05", gp.torso_plate(B, 138.0, 142.0, -58, 58, 4.8, 1.0, R_ACCENT, nu=9, nv=2, w=0.3))
    k.add("spine_05", gp.torso_plate(B, 126.0, 130.0, -58, 58, 4.8, 1.0, R_ACCENT, nu=9, nv=2, w=0.3))
    bx = back_x(B, 132.0)
    k.add("spine_05", gp.box_at((bx - 3.5, 0.0, 130.0), (7.0, 24.0, 22.0), R_TRIM, ch=1.2))
    for s in (-1, 1):
        k.add("spine_05", gp.cyl((bx - 9.0, s * 7.0, 108.0), (bx - 9.0, s * 7.0, 150.0), 4.6, R_ACCENT, sides=14))
        k.add("spine_05", gp.ball((bx - 9.0, s * 7.0, 150.5), 4.6, R_ACCENT, nu=10, nv=5))
        k.add("spine_05", gp.ring_at((bx - 9.0, s * 7.0, 100.0), (bx - 9.0, s * 7.0, 160.0), 22.0, 5.0, 2.0, R_TRIM, thick=0.8))
        k.add("spine_05", gp.ring_at((bx - 9.0, s * 7.0, 100.0), (bx - 9.0, s * 7.0, 160.0), 42.0, 5.0, 2.0, R_TRIM, thick=0.8))
    hose = ((bx - 9.0, -7.0, 148.0), (bx - 14.0, -16.0, 142.0), (bx - 4.0, -26.0, 122.0), (bx + 8.0, -24.0, 104.0), (bx + 20.0, -22.0, 92.0))
    k.add("spine_05", _sweep(list(hose), [1.3, 1.3, 1.3, 1.3, 1.3], R_TRIM, sides=7))
    k.pair("upperarm", gp.pauldron(B, big=1.3, layers=2, top_role=R_ACCENT, lame_role=R_CLOTH, thick=1.6, ridge=0.8, alpha=44))
    k.pair("lowerarm", gp.bracer(B, flare=2.0, accent=R_ACCENT, thick=1.6, s0=2, s1=24, rings=True, role=R_CLOTH))
    nozzle = B.bone("hand_l")
    k.add("lowerarm_l", gp.ball((nozzle[0] + 11.0, nozzle[1], nozzle[2] - 2.0), 2.0, R_GLOW, nu=8, nv=5))
    k.add("pelvis", belt(B, z0=94.0, z1=103.0, role=R_ACCENT, buckle=R_TRIM, thick=1.8))
    k.pair("thigh", gp.tube_plate(B.bone("thigh_l"), B.bone("calf_l"), 6.0, 34.0, 11.4, 9.6, -80, 80, 1.8, R_CLOTH, nv=5, nu=9, w=0.12, lo=0.4))
    k.pair("calf", gp.greave(B, role=R_CLOTH, accent=R_ACCENT, thick=1.8, s1=37.0))
    return k
