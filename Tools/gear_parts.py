"""Gear pieces (helmets, plates, pauldrons, guards, belts, packs, cloth ...) built with mesh_char.GM in character space (reference pose,
absolute coordinates of the Mannequin). Every builder takes the Body (gear_body.body(quinn)) and returns a GM. Left side pieces are built
at y < 0; mirrored() makes the right side. The pieces are cut per bone and shifted to the bone origin by make_gear_assets.py.
"""

import math

import gear_body as gb
import mesh_char as mc
from mesh_char import (GM, R_PLATE, R_CLOTH, R_ACCENT, R_TEAM, R_TRIM, R_GLOW, R_LIGHT, fr, lerp, clamp)

SIN, COS = math.sin, math.cos


def rad(a):
    return math.radians(a)


def edge(u, v, w=0.1, lo=0.3):
    """Thickness factor of a plate: `lo` at its border rising to 1 inside (a soft bevel)."""
    d = min(u, 1.0 - u, v, 1.0 - v)
    k = clamp(d / w, 0.0, 1.0)
    return lo + (1.0 - lo) * k * k * (3 - 2 * k)


def samples(n, wrap=False):
    return [i / float(n if wrap else n - 1) for i in range(n)]


# ------------------------------------------------------------------------------------------------ torso
def torso_plate(B, z0, z1, a0, a1, off_=1.2, thick=1.4, role=R_PLATE, top_fn=None, bot_fn=None, bulge=None, nu=13, nv=6, w=0.1, lo=0.3, wrap=False,
                inner=False):
    """A plate wrapped around the torso between the heights z0..z1 and the angles a0..a1 (degrees, 0 = front, 90 = right, 180 = back).
    top_fn(u) / bot_fn(u) lower the top edge / raise the bottom edge (V necks, curved hems); bulge(angle, z) adds standoff (pecs)."""
    m = GM()

    def surf(u, v):
        ang = lerp(a0, a1, u)
        lo_ = z0 + (bot_fn(u) if bot_fn else 0.0)
        hi_ = z1 - (top_fn(u) if top_fn else 0.0)
        z = lerp(lo_, hi_, v)
        return B.tpt(z, ang, off_ + (bulge(ang, z) if bulge else 0.0))

    us = samples(nu, wrap)
    m.plate(surf, us, samples(nv), lambda u, v: thick * (edge(u, v, w, lo) if not wrap else edge(0.5, v, w, lo)), role, B.inside((z0 + z1) / 2), wrap_u=wrap,
            inner=inner)
    return m


def pec_bulge(amount=1.6, z0=119.0, z1=149.0, span=62.0):
    """Standoff of a chest plate as a function of (angle, z): a soft double pec shape, 0 at the plate edges."""
    def f(ang, z):
        a = clamp(1.0 - abs(ang) / max(1.0, span), 0.0, 1.0)
        v = clamp((z - z0) / max(1.0, z1 - z0), 0.0, 1.0)
        return amount * (SIN(math.pi * a * 0.5) ** 0.8) * (SIN(math.pi * v) ** 0.7)
    return f


def cuirass(B, role=R_PLATE, trim=R_TRIM, z0=119.0, z1=149.0, back=True, off_=1.4, vneck=8.0, bulge=1.8, panel=True, thick=1.5, span=62.0):
    """Chest plate (front, optionally back) with a central ridge and a trim line along the lower edge."""
    m = GM()
    m.append(torso_plate(B, z0, z1, -span, span, off_, thick, role, top_fn=(lambda u: vneck * (1 - abs(2 * u - 1)) ** 2) if vneck else None,
                         bot_fn=lambda u: 5.0 * (1 - SIN(math.pi * u)) * 0.8, bulge=pec_bulge(bulge, z0, z1, span)))
    if panel:
        m.append(torso_plate(B, z0 + 1.5, z1 - 3.0, -3.0, 3.0, off_ + thick * 0.85, 0.9, trim, nu=3, nv=4, w=0.2, bulge=pec_bulge(bulge, z0, z1, span)))
        m.append(torso_plate(B, z0 - 0.5, z0 + 2.5, -span + 6, span - 6, off_ + thick * 0.6, 0.8, trim, nu=11, nv=2, bot_fn=lambda u: 3.0 * (1 - SIN(math.pi * u)) * 0.8,
                             w=0.25))
    if back:
        m.append(torso_plate(B, z0 + 2, z1 - 1, 180 - span * 0.85, 180 + span * 0.85, off_, thick * 0.9, role, nu=11, nv=5,
                             top_fn=lambda u: 2.0 * (1 - abs(2 * u - 1))))
    return m


def collar_ring(B, z=151.5, r=7.2, h=3.4, role=R_TRIM, thick=1.2, sy=0.95, cx_shift=-1.6, tilt=0.0):
    m = GM()
    f = fr((B.torso(z)[0] + cx_shift, 0.0, z), pitch=tilt)
    m.lathe([(r - thick, 0.0), (r, 0.0), (r + 0.4, h), (r - thick + 0.4, h), (r - thick, 0.0)], role, sides=16, f=f, sy=sy, creases=(1, 2, 3), caps=(False, False))
    return m


# ------------------------------------------------------------------------------------------------ limbs
def tube_plate(P0, P1, s0, s1, r0, r1, a0, a1, thick, role, sy=1.0, bulge=None, nu=None, nv=4, w=0.12, lo=0.3, lip=0.0):
    """A plate on an (elliptic) cylinder around the axis P0 -> P1: s0..s1 along it (cm from P0), radius r0 -> r1, angles a0..a1 degrees
    (0 = local x = the forward-ish side, 90 = local y = the outer-up side for left limbs). A full 360 turn wraps closed."""
    f = mc.frame_z(P0, P1)
    full = abs((a1 - a0)) >= 359.0
    nu = nu or (14 if full else 9)
    m = GM()

    def surf(u, v):
        s = lerp(s0, s1, v)
        r = lerp(r0, r1, v) + (bulge(u, v) if bulge else 0.0) + lip * (v ** 6)
        ang = rad(lerp(a0, a1, u))
        return f.pt((r * COS(ang), r * sy * SIN(ang), s))

    mid = f.pt((0.0, 0.0, (s0 + s1) / 2))
    m.plate(surf, samples(nu, full), samples(nv), (lambda u, v: thick * edge(0.5, v, w, lo)) if full else (lambda u, v: thick * edge(u, v, w, lo)), role, mid,
            wrap_u=full)
    return m


def ring_at(P0, P1, s, r, h, role, sy=1.0, thick=0.9, sides=14, grow=0.0):
    """A thin band (ring) around the axis P0 -> P1 at s cm from P0."""
    f = mc.frame_z(P0, P1)
    m = GM()
    m.lathe([(r - thick, s), (r, s), (r + grow, s + h), (r - thick + grow, s + h), (r - thick, s)], role, sides=sides, f=f, sy=sy, creases=(1, 2, 3), caps=(False, False))
    return m


def axis_pt(P0, P1, s):
    d = mc.norm(mc.sub(P1, P0))
    return mc.add(P0, mc.mul(d, s))


def pauldron(B, big=1.0, layers=3, role=R_PLATE, top_role=None, lame_role=None, trim_role=R_TRIM, alpha=48.0, dome=True, lift=1.5, thick=1.1, spike=0.0,
             spike_role=R_ACCENT, hang_=1.0, dome_cut=118.0, ridge=0.0):
    """A shoulder guard for the LEFT arm: a domed spaulder with `layers` overlapping lames cascading down the upper arm."""
    J = B.bone("upperarm_l")
    E = B.bone("lowerarm_l")
    top_role = role if top_role is None else top_role
    lame_role = role if lame_role is None else lame_role
    m = GM()
    if dome:
        c = mc.add(J, (0.0, -SIN(rad(alpha)) * lift, COS(rad(alpha)) * lift))
        f = fr(c, roll=alpha)
        R = 10.0 * big
        rx, ry, rz = R * 1.05, R * 1.0, R * 0.78

        def surf(u, v):
            phi = rad(360.0 * u)
            th = rad(dome_cut * v)
            g = 1.0 - 0.34 * max(0.0, SIN(phi)) * (th / rad(dome_cut))      # smaller toward the neck
            return f.pt((rx * g * SIN(th) * COS(phi), ry * g * SIN(th) * SIN(phi), rz * COS(th)))

        m.plate(surf, samples(16, True), samples(7), lambda u, v: thick * 1.2 * edge(0.5, v, 0.12, 0.4), top_role, c, wrap_u=True)
        if ridge > 0:
            # a raised rib running over the dome from front to back
            def surf2(u, v):
                th = rad(dome_cut * 0.92 * (u * 2 - 1) * 0.5 + 0.0)
                th = rad((u - 0.5) * 2 * 75.0)
                return f.pt((rx * 1.02 * SIN(th), (v - 0.5) * 2.0, rz * 1.02 * COS(th) + 0.2))
            m.plate(surf2, samples(9), samples(2), lambda u, v: ridge * edge(u, 0.5, 0.2, 0.3), trim_role, c)
    if spike > 0:
        c2 = mc.add(J, (0.0, -SIN(rad(alpha)) * (lift + 7.8 * big), COS(rad(alpha)) * (lift + 7.8 * big)))
        tip = mc.add(c2, (0.0, -SIN(rad(alpha)) * spike, COS(rad(alpha)) * spike))
        m.cone(c2, tip, 2.3 * big, spike_role, sides=7)
    # lames along the upper arm
    for k in range(layers):
        s0 = (4.0 + 5.0 * k * hang_) * big
        s1 = s0 + 7.0 * big
        r_out = (8.6 + 0.6 * (layers - 1 - k)) * big - 0.5 * k * hang_
        m.append(tube_plate(J, E, s0, s1, r_out, r_out - 0.6, -35.0, 215.0, thick * 0.9, lame_role, nu=10, nv=3, w=0.2, lo=0.45))
    return m


def bracer(B, s0=5.0, s1=22.0, role=R_PLATE, trim_role=R_TRIM, accent=None, flare=1.0, thick=0.9, arc=(-70.0, 250.0), rings=True, spike=0.0):
    """Forearm guard for the LEFT arm."""
    P0, P1 = B.bone("lowerarm_l"), B.bone("hand_l")
    m = GM()
    m.append(tube_plate(P0, P1, s0, s1, 5.8 * flare, 4.6, arc[0], arc[1], thick, role, nv=4, nu=9, w=0.14, lo=0.45))
    if rings:
        m.append(ring_at(P0, P1, s0 - 0.5, 6.0 * flare, 1.8, trim_role, thick=0.9))
        m.append(ring_at(P0, P1, s1 - 1.0, 4.9, 1.8, trim_role, thick=0.9))
    if accent is not None:
        m.append(ring_at(P0, P1, (s0 + s1) / 2 - 1, 5.6, 2.2, accent, thick=0.8))
    if spike > 0:
        f = mc.frame_z(P0, P1)
        base = f.pt((0.0, 4.2, s0 + 4.0))
        tip = f.pt((0.0, 4.2, s0 - spike))
        m.cone(base, tip, 1.8, R_ACCENT, sides=6)
    return m


def greave(B, role=R_PLATE, trim_role=R_TRIM, s0=3.0, s1=36.0, thick=1.0, arc=(-95.0, 95.0), knee=True, accent=None):
    """Shin guard (+ knee cap) for the LEFT leg, attached to calf_l."""
    P0, P1 = B.bone("calf_l"), B.bone("foot_l")
    m = GM()
    m.append(tube_plate(P0, P1, s0, s1, 7.2, 5.6, arc[0], arc[1], thick, role, nv=5, nu=9, w=0.1, lo=0.4))
    m.append(ring_at(P0, P1, s1 - 1.5, 5.9, 2.0, trim_role, thick=0.9))
    if knee:
        f = mc.frame_z(P0, P1)
        c = f.pt((8.6, 0.0, -1.5))
        m.ellipsoid(c, 4.2, 5.4, 5.2, trim_role if accent is None else accent, nu=10, nv=6, cut=(0.0, 0.62))
    if accent is not None:
        m.append(ring_at(P0, P1, s0 + 14, 6.6, 1.6, accent, thick=0.7))
    return m


# ------------------------------------------------------------------------------------------------ head
class Helm:
    """A skull shell: ellipsoid dome above the equator, a skirt below it. r(z) gives the radius of the shell at a height, front(z) the
    x of its front surface (to place visors, brows and vents on it)."""

    def __init__(self, B, margin=1.6, z_eq=None, z_bot=None, jaw=0.88, cx_shift=-0.8, top=None):
        self.B = B
        c = B.head_c
        self.c = c
        self.rx = B.head_rx + margin
        self.ry = B.head_ry + margin
        self.rz = B.head_rz + margin * 0.5
        self.margin = margin
        self.z_eq = c[2] + 1.0 if z_eq is None else z_eq
        self.z_bot = c[2] - 9.0 if z_bot is None else z_bot
        self.jaw = jaw
        self.cx = c[0] + cx_shift
        self.z_top = c[2] + self.rz if top is None else top
        self.sy = self.ry / self.rx

    def r(self, z):
        if z >= self.z_eq:
            t = (z - self.z_eq) / max(1e-6, self.z_top - self.z_eq)
            return self.rx * math.sqrt(max(0.0, 1.0 - t * t))
        t = (self.z_eq - z) / max(1e-6, self.z_eq - self.z_bot)
        return self.rx * (1.0 - (1.0 - self.jaw) * t)

    def front(self, z):
        return self.cx + self.r(z)

    def side(self, z):
        return self.r(z) * self.sy

    def profile(self, n_up=7, n_low=3, z_bot=None):
        zb = self.z_bot if z_bot is None else z_bot
        prof = [(self.r(zb), zb)]
        for k in range(1, n_low):
            z = zb + (self.z_eq - zb) * k / float(n_low)
            prof.append((self.r(z), z))
        for k in range(0, n_up):
            t = k / float(n_up - 1) * 88.0
            z = self.z_eq + (self.z_top - self.z_eq) * SIN(rad(t))
            prof.append((self.rx * COS(rad(t)), z))
        prof[-1] = (0.0, self.z_top)
        return prof

    def shell(self, role, sides=18, z_bot=None, caps=(False, False), arc=None, extra=0.0, rfn=None):
        prof = self.profile(z_bot=z_bot)
        if extra:
            prof = [(r + extra if r > 0 else 0.0, z) for (r, z) in prof]
        m = GM()
        m.lathe(prof, role, sides=sides, f=fr((self.cx, 0.0, 0.0)), sy=self.sy, caps=caps, arc=arc, rfn=rfn)
        return m

    def pt(self, z, ang, off=0.0):
        """Point on the shell at height z, angle ang (0 = front, +90 = right side, 180 = back), pushed out by off cm."""
        r = self.r(z) + off
        a = rad(ang)
        return (self.cx + r * COS(a), r * self.sy * SIN(a), z)


def helm_full(B, role=R_PLATE, trim=R_TRIM, accent=R_ACCENT, glow=R_GLOW, margin=1.7, slit_w=12.0, fin=0.0, cheek=True, brow=True, chin=True, vents=True,
              slit_h=1.7, jaw=0.9):
    H = Helm(B, margin, jaw=jaw)
    c = H.c
    m = GM()
    m.append(H.shell(role, caps=(False, True)))
    zc = c[2]
    if brow:
        m.append(box_at((H.front(zc + 4.7) + 0.2, 0.0, zc + 4.7), (3.4, H.side(zc + 4.7) * 2.1, 2.0), accent, ch=0.7, pitch=-6, taper=0.9))
    zs = zc + 2.1
    m.box((H.front(zs) + 0.1, 0.0, zs), (1.2, slit_w, slit_h), glow, ch=0.25)
    m.box((H.front(zs) - 0.2, 0.0, zs), (1.0, slit_w + 3.2, slit_h + 2.2), trim, ch=0.35)
    if vents:
        for k in range(3):
            z = zc - 3.2 - k * 1.9
            m.box((H.front(z) + 0.2, 0.0, z), (1.2, 6.8 - 1.2 * k, 0.9), trim, ch=0.25)
    if chin:
        z = zc - 7.8
        m.box((H.front(z) - 0.5, 0.0, z), (4.2, H.side(z) * 1.55, 3.4), role, ch=0.8, taper=0.8)
    if cheek:
        for sgn in (-1, 1):
            m.box((H.cx + 0.5, sgn * (H.side(zc - 3.0) + 0.3), zc - 3.0), (H.rx * 1.1, 1.3, 8.2), trim, ch=0.45)
    if fin:
        m.append(box_at((H.cx - 0.5, 0.0, H.z_top - 0.6 + fin * 0.3), (H.rx * 1.7, 1.5, fin), accent, ch=0.5, pitch=4, taper=0.55))
    return m


def helm_open(B, role=R_PLATE, trim=R_TRIM, cloth=R_CLOTH, margin=1.5, brim=3.2, strap=True):
    """An open helmet (soldier): dome with a brim all around, a chin strap."""
    H = Helm(B, margin, z_bot=B.head_c[2] + 3.0, jaw=1.0)
    c = H.c
    m = GM()
    m.append(H.shell(role, caps=(False, True), z_bot=c[2] + 2.0))
    f = fr((H.cx, 0.0, c[2] + 2.2))
    m.lathe([(H.rx - 0.4, 0.0), (H.rx + brim, -0.9), (H.rx + brim + 0.2, -0.2), (H.rx - 0.2, 0.7)], role, sides=20, f=f, sy=H.sy, caps=(False, False), creases=(1, 2))
    if strap:
        for sgn in (-1, 1):
            a0 = (H.cx + 0.5, sgn * (H.side(c[2]) - 0.1), c[2] + 1.0)
            a1 = (H.cx + 3.0, sgn * 5.2, c[2] - 10.5)
            m.sweep([a0, mc.lerp3(a0, a1, 0.5), a1], [0.45, 0.45, 0.45], cloth, sides=5, flat=(1.0, 0.4))
        m.sweep([(H.cx + 3.0, -5.2, c[2] - 10.5), (H.cx + 4.8, 0.0, c[2] - 11.4), (H.cx + 3.0, 5.2, c[2] - 10.5)], [0.5, 0.5, 0.5], cloth, sides=5, flat=(1.0, 0.5))
    return m


def goggles(B, z_off=3.0, role_rim=R_TRIM, role_lens=R_GLOW, strap_role=R_CLOTH, r=2.9, rim_r=3.6, spread=4.8, x_off=None, tilt=0.0, H=None, z=None, lens_depth=1.0,
            strap=True):
    """Two round lenses on a strap around the head. x_off = x of the lens plane (default: the face front)."""
    H = H or Helm(B, 1.0)
    c = H.c
    z = c[2] + z_off if z is None else z
    fx = H.front(z) - 1.2 if x_off is None else x_off
    m = GM()
    for sgn in (-1, 1):
        g = fr((fx, sgn * spread, z), pitch=-90 + tilt)           # local z points forward (+x)
        m.lathe([(0.0, 0.0), (rim_r, 0.0), (rim_r, 1.6), (r + 0.4, 2.0), (r, 2.0)], role_rim, sides=14, f=g, creases=(2,), caps=(False, False))
        m.lathe([(0.0, 1.9), (r, 1.9), (r - 0.3, 2.0 + lens_depth * 0.5), (0.0, 2.0 + lens_depth * 0.6)], role_lens, sides=14, f=g, caps=(False, False))
    m.box((fx + 0.6, 0.0, z), (1.4, spread * 2 - rim_r * 1.5, 1.3), role_rim, ch=0.3)
    if strap:
        rr_ = H.r(z) + 0.3
        m.lathe([(rr_, z - 0.9), (rr_ + 0.5, z - 0.9), (rr_ + 0.5, z + 0.9), (rr_, z + 0.9), (rr_, z - 0.9)], strap_role, sides=20, f=fr((H.cx, 0.0, 0.0)), sy=H.sy,
                creases=(1, 2, 3), caps=(False, False))
    return m


def horn(p0, p1, p2, r0, role, n=8, sides=7, taper=0.06, sy=1.0):
    """A horn / claw along a quadratic curve p0 -> p1 -> p2 whose radius shrinks from r0 to a point."""
    pts, rr_ = [], []
    for k in range(n):
        t = k / float(n - 1)
        a = mc.lerp3(p0, p1, t)
        b = mc.lerp3(p1, p2, t)
        pts.append(mc.lerp3(a, b, t))
        rr_.append(max(taper, r0 * (1.0 - t) ** 0.9))
    m = GM()
    m.sweep(pts, rr_, role, sides=sides, caps=(True, False), sy=sy)
    return m


def spike(base, tip, r, role, sides=7):
    m = GM()
    m.cone(base, tip, r, role, sides=sides)
    return m


def cyl(p0, p1, r, role, sides=10, caps=(True, True), smooth=True, sy=1.0):
    m = GM()
    m.tube(p0, p1, r, r, role, sides=sides, caps=caps, smooth=smooth, sy=sy)
    return m


def hang(a, b, down, length, role, out=(1.0, 0.0, 0.0), taper=1.0, bulge=0.0, ripple=0.0, waves=2.0, phase=0.0, hem=None, nu=7, nv=6, thick=0.5, inside=None,
         sway=(0.0, 0.0, 0.0), stripes=()):
    """A piece of cloth hanging from the edge a -> b along `down` for `length` cm. taper scales the width at the hem, bulge pushes the middle
    along `out`, ripple adds sideways waves growing downwards, hem(u) -> factor of the length (torn / pointed hems), sway moves the hem.
    stripes = [(u0, u1, role), ...] adds slightly thicker cloth patches over the same surface (bands, hem trims, central stripes)."""
    down = mc.norm(down)
    ctr = mc.lerp3(a, b, 0.5)

    def surf(u, v):
        top = mc.lerp3(a, b, u)
        L = length * (hem(u) if hem else 1.0)
        w = lerp(1.0, taper, v)
        p = mc.add(ctr, mc.mul(mc.sub(top, ctr), w))
        p = mc.add(p, mc.mul(down, L * v))
        p = mc.add(p, mc.mul(out, bulge * SIN(math.pi * min(1.0, v * 1.2)) + ripple * v * SIN(2 * math.pi * (waves * u) + phase)))
        return mc.add(p, mc.mul(sway, v * v))

    m = GM()
    P = [[surf(i / float(nu - 1), j / float(nv - 1)) for j in range(nv)] for i in range(nu)]
    m.cloth(P, role, thick=thick, inside=inside)
    for (u0, u1, r2, *rest) in stripes:
        v0, v1 = (rest[0], rest[1]) if len(rest) >= 2 else (0.0, 1.0)
        n_u = max(2, int(round((u1 - u0) * (nu - 1))) + 1)
        n_v = max(2, int(round((v1 - v0) * (nv - 1))) + 1)
        Q = [[surf(lerp(u0, u1, i / float(n_u - 1)), lerp(v0, v1, j / float(n_v - 1))) for j in range(n_v)] for i in range(n_u)]
        m.cloth(Q, r2, thick=thick + 0.5, inside=inside)
    return m


def pleat_band(P0, P1, s, r, h, role, pleats=12, depth=0.16, sides=36, sy=1.0, flare=0.0):
    """A frilled cuff around the axis P0 -> P1 (wrists, ankles)."""
    f = mc.frame_z(P0, P1)
    m = GM()
    m.lathe([(r, s), (r + flare, s + h)], role, sides=sides, f=f, sy=sy, caps=(False, False), rfn=lambda th, t: 1.0 + depth * COS(pleats * th), double=True)
    return m


def diamond(B, z0, z1, span, off_, thick, role, **kw):
    """A diamond shaped plate on the chest or the back (tabards, emblems)."""
    return torso_plate(B, z0, z1, -span, span, off_, thick, role, top_fn=lambda u: (z1 - z0) * 0.5 * abs(2 * u - 1), bot_fn=lambda u: (z1 - z0) * 0.5 * abs(2 * u - 1),
                       nu=kw.get("nu", 9), nv=kw.get("nv", 7), w=kw.get("w", 0.12), lo=kw.get("lo", 0.4))


def hood(B, role=R_CLOTH, margin=2.8, open_deg=52.0, back=0.35, z_bot=None, rim=None, jaw=1.02):
    """A cloth hood: a shell around the head open at the face, longer and pointed at the back."""
    H = Helm(B, margin, z_bot=(B.head_c[2] - 11.0) if z_bot is None else z_bot, jaw=jaw, cx_shift=-1.2)
    m = GM()
    m.append(H.shell(role, sides=14, arc=(open_deg, 360.0 - open_deg), rfn=lambda th, t: 1.0 + back * max(0.0, -COS(th)) ** 2 * (t ** 1.2)))
    if rim is not None:
        zc = B.head_c[2]
        for sgn in (-1, 1):
            pts = [H.pt(zc + 14.0, sgn * (open_deg + 4.0), 0.3), H.pt(zc + 6.0, sgn * (open_deg - 1.0), 0.4), H.pt(zc - 3.0, sgn * (open_deg - 4.0), 0.4),
                   H.pt(zc - 9.0, sgn * (open_deg - 8.0), 0.4)]
            m.sweep(pts, [0.9, 0.9, 0.9, 0.7], rim, sides=5)
    return m, H


def pleated_ring(c, r0, r1, z0, z1, role, pleats=14, depth=0.14, sides=40, sy=1.0):
    """A ruff / frilled skirt: a flared lathe with sinusoidal pleats."""
    m = GM()
    m.lathe([(r1, z1), (r0, z0)] if z1 < z0 else [(r0, z0), (r1, z1)], role, sides=sides, f=fr(c), sy=sy, caps=(False, False),
            rfn=lambda th, t: 1.0 + depth * (0.4 + 0.6 * t) * COS(pleats * th), double=True)
    return m


def blob_ring(c, R, r, role, lumps=9, amp=0.28, sy=1.0, sides=22, rings=6, tilt=0.0, seed=1, roll=0.0):
    """A lumpy torus (fur trim): major radius R, minor radius r."""
    m = GM()
    f = fr(c, pitch=tilt, roll=roll)
    P = []
    for i in range(sides):
        th = 2 * math.pi * i / sides
        col = []
        for j in range(rings):
            ph = 2 * math.pi * j / rings
            k = 1.0 + amp * mc.fbm(th * lumps / (2 * math.pi) * 1.6, ph * 0.6, seed, 2)
            rr_ = R + r * k * COS(ph)
            col.append(f.pt((rr_ * COS(th), rr_ * sy * SIN(th), r * k * SIN(ph))))
        col.append(col[0])
        P.append(col)
    # torus: u around the ring (ccw), v around the tube; natural normal points inward, so flip
    m.grid(P, role, wrap_u=True, flip=True)
    return m


def box_at(c, size, role, ch=0.6, yaw=0.0, pitch=0.0, roll=0.0, taper=1.0):
    m = GM()
    m.box((0.0, 0.0, 0.0), size, role, ch=ch, f=fr(c, yaw=yaw, pitch=pitch, roll=roll), taper=taper)
    return m


def ball(c, r, role, nu=10, nv=6, sy=1.0, sz=1.0, f=None):
    m = GM()
    m.ellipsoid(c, r, r * sy, r * sz, role, nu=nu, nv=nv, f=f or mc.IDENT)
    return m


def merge(*ms):
    out = GM()
    for m in ms:
        if m is not None:
            out.append(m)
    return out


class Kit:
    """Collects the pieces of one character per bone (absolute reference-pose coordinates)."""

    def __init__(self, B):
        self.B = B
        self.parts = {}

    def add(self, bone, gm):
        if gm is None or not gm.t:
            return
        self.parts.setdefault(bone, GM()).append(gm)

    def pair(self, base, gm_left):
        self.add(base + "_l", gm_left)
        self.add(base + "_r", gm_left.mirrored())

    def tri_count(self):
        return sum(len(g.t) for g in self.parts.values())


def back_x(B, z, off=0.0):
    cx, ax, _ = B.torso(z)
    return cx - ax - off


def front_x(B, z, off=0.0):
    cx, ax, _ = B.torso(z)
    return cx + ax + off
