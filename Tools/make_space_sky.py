"""Makes the three space skies of the campaign arenas (pure python, no downloads, no libraries):

  python -I Tools/make_space_sky.py [orbital derelict nexus]
  -> <AssetCache>/hdri/space_<name>.hdr   2048 x 1024 long-lat Radiance file, the same layout as the Poly Haven skies
     <AssetCache>/hdri/space_<name>.png   a small preview
Then Tools/import_space_skies.py (editor) imports them as /Game/Sky/T_Sky_space_<name> and maplooks.py has the looks.

  orbital  a banded gas giant filling a quarter of the sky, a hard white sun, dense stars (the station ring)
  derelict a purple and teal nebula, a cratered grey moon, a dim sun (the dead ship)
  nexus    a black hole with a glowing accretion ring, a blue-white star (the oldest arena)

Direction convention (like Tools/fetch_hdri.py): u = 0.5 looks along +x, u grows towards +y; v = 0.5 is the horizon, v = 0 the zenith.
Values are linear and absolute: stars up to about 8, a lit planet about 1, the sun disc about 14, nebula 0.02 to 0.4.
"""

import math
import os
import random
import struct
import sys
import zlib

_TOOLS = os.path.dirname(os.path.abspath(__file__))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import fetch_hdri as fh  # noqa: E402

W, H = 2048, 1024


def direction(az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))


def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    n = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def pix_dir(x, y):
    az = ((x + 0.5) / W - 0.5) * 2.0 * math.pi
    el = (0.5 - (y + 0.5) / H) * math.pi
    ce = math.cos(el)
    return (ce * math.cos(az), ce * math.sin(az), math.sin(el))


def dir_pix(d):
    az = math.atan2(d[1], d[0])
    el = math.asin(max(-1.0, min(1.0, d[2])))
    return (az / (2.0 * math.pi) + 0.5) * W, (0.5 - el / math.pi) * H


# ------------------------------------------------------------------------------------------------ noise
def _h(ix, iy, seed):
    n = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, y, seed=0):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _h(ix, iy, seed), _h(ix + 1, iy, seed)
    c, d = _h(ix, iy + 1, seed), _h(ix + 1, iy + 1, seed)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def fbm(x, y, seed=0, octaves=4):
    v, amp, f = 0.0, 0.5, 1.0
    for o in range(octaves):
        v += amp * vnoise(x * f, y * f, seed + o * 17)
        amp *= 0.5
        f *= 2.03
    return v


def fbm3(d, scale, seed=0, octaves=4):
    """3D-ish noise on a direction: no seam at the +-180 degree edge of the panorama."""
    return 0.5 * (fbm(d[0] * scale + 11.0, d[1] * scale + d[2] * scale * 0.7, seed, octaves) +
                  fbm(d[2] * scale + 3.0, d[0] * scale * 0.6 + d[1] * scale, seed + 5, octaves))


# ------------------------------------------------------------------------------------------------ painting
class Sky:
    def __init__(self, base=(0.0015, 0.0018, 0.0030)):
        self.buf = [0.0] * (W * H * 3)
        for i in range(W * H):
            self.buf[3 * i], self.buf[3 * i + 1], self.buf[3 * i + 2] = base

    def add(self, x, y, c):
        x %= W
        if 0 <= y < H:
            i = 3 * (int(y) * W + int(x))
            self.buf[i] += c[0]
            self.buf[i + 1] += c[1]
            self.buf[i + 2] += c[2]

    def stars(self, count, seed, bright=1.0, tint_spread=0.35):
        rnd = random.Random(seed)
        for _ in range(count):
            z = rnd.uniform(-1.0, 1.0)
            a = rnd.uniform(0.0, 2.0 * math.pi)
            r = math.sqrt(1.0 - z * z)
            d = (r * math.cos(a), r * math.sin(a), z)
            x, y = dir_pix(d)
            mag = rnd.random() ** 6                        # most are faint, a few are bright
            lum = (0.25 + 8.0 * mag) * bright
            t = rnd.uniform(-1.0, 1.0) * tint_spread       # blue .. orange
            col = (lum * (1.0 + 0.5 * t), lum, lum * (1.0 - 0.5 * t))
            stretch = 1.0 / max(0.25, math.sqrt(1.0 - z * z))     # equirect stretches the east-west direction near the poles
            kx = int(min(6, stretch))
            for dx in range(-kx, kx + 1):
                for dy in (-1, 0, 1):
                    w = math.exp(-((dx / stretch) ** 2 + dy * dy) * 1.1) * (1.0 / (1.0 + 0.0 * kx))
                    self.add(x + dx, y + dy, (col[0] * w * 0.5, col[1] * w * 0.5, col[2] * w * 0.5))

    def region(self, d, radius_deg, fn):
        """Calls fn(px, py, dir) for every pixel within radius_deg of direction d (a bounding box of the long-lat grid, exact test inside)."""
        x0, y0 = dir_pix(d)
        el = math.asin(max(-1.0, min(1.0, d[2])))
        dy = int(radius_deg / 180.0 * H) + 3
        wide = radius_deg / 360.0 * W / max(0.12, math.cos(min(math.radians(85.0), abs(el) + math.radians(radius_deg))))
        dx = int(min(W / 2.0, wide)) + 3
        cosr = math.cos(math.radians(radius_deg))
        for py in range(int(y0) - dy, int(y0) + dy + 1):
            if not 0 <= py < H:
                continue
            for px in range(int(x0) - dx, int(x0) + dx + 1):
                pd = pix_dir(px % W, py)
                if dot(pd, d) >= cosr:
                    fn(px % W, py, pd)

    def planet(self, c, radius_deg, sun_dir, bands, rim, seed, noise_scale=6.0, axis_tilt=0.35, crater=False, dark=0.015):
        c = norm(c)
        up = (0.0, 0.0, 1.0)
        e1 = norm(cross(up, c))
        e2 = cross(c, e1)
        e2 = (e2[0] * math.cos(axis_tilt) + e1[0] * math.sin(axis_tilt), e2[1] * math.cos(axis_tilt) + e1[1] * math.sin(axis_tilt), e2[2] * math.cos(axis_tilt) + e1[2] * math.sin(axis_tilt))
        sinr = math.sin(math.radians(radius_deg))
        sd = norm(sun_dir)

        def paint(px, py, d):
            p = (d[0] - c[0] * dot(d, c), d[1] - c[1] * dot(d, c), d[2] - c[2] * dot(d, c))
            ux, uy = dot(p, e1) / sinr, dot(p, e2) / sinr
            rr = ux * ux + uy * uy
            if rr >= 1.0:
                return
            nz = math.sqrt(1.0 - rr)
            n = (e1[0] * ux + e2[0] * uy - c[0] * nz, e1[1] * ux + e2[1] * uy - c[1] * nz, e1[2] * ux + e2[2] * uy - c[2] * nz)
            lit = max(0.0, dot(n, sd))
            lat = uy / max(0.05, math.sqrt(max(0.0, 1.0 - ux * ux * 0.0)))
            if crater:
                v = fbm(ux * noise_scale + 7.0, uy * noise_scale, seed, 5)
                cr = max(0.0, 1.0 - abs(fbm(ux * noise_scale * 2.2, uy * noise_scale * 2.2, seed + 9, 3) - 0.5) * 6.0)
                shade = 0.55 + 0.9 * v - 0.35 * cr
                col = tuple(max(0.0, bands[0][i] * shade) for i in range(3))
            else:
                t = 0.5 + 0.5 * math.sin(lat * 7.5 + 2.2 * fbm(ux * 2.0 + 3.0, uy * 9.0, seed, 3) + 0.6 * math.sin(lat * 19.0))
                t = min(0.999, max(0.0, t))
                f = t * (len(bands) - 1)
                i0 = int(f)
                fr = f - i0
                col = tuple(bands[i0][i] * (1 - fr) + bands[min(i0 + 1, len(bands) - 1)][i] * fr for i in range(3))
                swirl = 0.85 + 0.3 * fbm(ux * 5.0 + 1.0, uy * 16.0, seed + 3, 4)
                col = tuple(v * swirl for v in col)
            lum = dark + lit
            limb = (1.0 - nz) ** 3.0
            glow = rim[0] * limb * (0.12 + 1.6 * lit)
            self.add(px, py, (col[0] * lum * 1.1 + rim[1][0] * glow, col[1] * lum * 1.1 + rim[1][1] * glow, col[2] * lum * 1.1 + rim[1][2] * glow))
            # the sky behind the disc is replaced
            i = 3 * (py * W + px)
            # (the add above keeps the star field under the planet, which is dark enough to be invisible)

        self.region(c, radius_deg * 1.06, lambda px, py, d: self._planet_or_atmo(paint, px, py, d, c, radius_deg, sd, rim))

    def _planet_or_atmo(self, paint, px, py, d, c, radius_deg, sd, rim):
        t = math.degrees(math.acos(max(-1.0, min(1.0, dot(d, c)))))
        if t < radius_deg:
            i = 3 * (py * W + px)
            self.buf[i] = self.buf[i + 1] = self.buf[i + 2] = 0.0       # stars do not shine through the planet
            paint(px, py, d)
        else:
            # a thin atmosphere halo just outside the disc, brighter on the sunny side
            f = (t - radius_deg) / (radius_deg * 0.06)
            side = max(0.0, dot(norm((d[0] - c[0], d[1] - c[1], d[2] - c[2])), sd))
            g = math.exp(-f * f * 3.0) * (0.15 + 0.85 * side) * rim[0] * 0.5
            self.add(px, py, (rim[1][0] * g, rim[1][1] * g, rim[1][2] * g))

    def disc(self, d, radius_deg, color, halo=0.0, halo_deg=6.0):
        def paint(px, py, pd):
            t = math.degrees(math.acos(max(-1.0, min(1.0, dot(pd, d)))))
            core = 1.0 if t < radius_deg else math.exp(-((t - radius_deg) / (radius_deg * 0.25)) ** 2)
            glow = halo * math.exp(-(t / halo_deg) ** 2)
            v = core + glow
            self.add(px, py, (color[0] * v, color[1] * v, color[2] * v))
        self.region(d, max(radius_deg * 3.0, halo_deg * 2.2), paint)

    def nebula(self, seed, colors, strength, scale=2.6, clear=0.45, gw=256, gh=128):
        """A coarse noise field (cheap) sampled bilinearly over the whole sky."""
        rnd = random.Random(seed)
        grid = []
        for gy in range(gh):
            el = (0.5 - (gy + 0.5) / gh) * math.pi
            for gx in range(gw):
                az = ((gx + 0.5) / gw - 0.5) * 2.0 * math.pi
                d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
                a = fbm3(d, scale, seed, 5)
                b = fbm3(d, scale * 1.9, seed + 31, 4)
                m = max(0.0, (a - clear) / (1.0 - clear))
                m = m * m * (3.0 - 2.0 * m)
                lane = max(0.0, 1.0 - abs(fbm3(d, scale * 0.8, seed + 77, 3) - 0.5) * 7.0)
                grid.append((m, b, lane))
        c0, c1, c2 = colors
        for y in range(H):
            gy = min(gh - 1.001, (y + 0.5) / H * gh - 0.5)
            gy0 = max(0, int(gy))
            fy = gy - gy0
            for x in range(W):
                gx = (x + 0.5) / W * gw - 0.5
                gx0 = int(math.floor(gx))
                fx = gx - gx0
                i00 = grid[gy0 * gw + gx0 % gw]
                i10 = grid[gy0 * gw + (gx0 + 1) % gw]
                i01 = grid[min(gh - 1, gy0 + 1) * gw + gx0 % gw]
                i11 = grid[min(gh - 1, gy0 + 1) * gw + (gx0 + 1) % gw]
                m = (i00[0] * (1 - fx) + i10[0] * fx) * (1 - fy) + (i01[0] * (1 - fx) + i11[0] * fx) * fy
                if m < 0.002:
                    continue
                b = (i00[1] * (1 - fx) + i10[1] * fx) * (1 - fy) + (i01[1] * (1 - fx) + i11[1] * fx) * fy
                ln = (i00[2] * (1 - fx) + i10[2] * fx) * (1 - fy) + (i01[2] * (1 - fx) + i11[2] * fx) * fy
                k = m * strength * (0.6 + 0.8 * b)
                mix = min(1.0, max(0.0, b * 1.4 - 0.2))
                r = (c0[0] * (1 - mix) + c1[0] * mix) * k + c2[0] * ln * m * strength * 0.5
                g = (c0[1] * (1 - mix) + c1[1] * mix) * k + c2[1] * ln * m * strength * 0.5
                bl = (c0[2] * (1 - mix) + c1[2] * mix) * k + c2[2] * ln * m * strength * 0.5
                i = 3 * (y * W + x)
                self.buf[i] += r
                self.buf[i + 1] += g
                self.buf[i + 2] += bl

    def ring(self, c, radius_deg, width_deg, color, hole_deg, strength=1.0, seed=3, tilt=0.35):
        """A glowing accretion ring around a black centre (the black hole of Nexus), seen slightly from the side."""
        c = norm(c)
        e1 = norm(cross((0.0, 0.0, 1.0), c))
        e2 = cross(c, e1)

        def paint(px, py, d):
            p = (d[0] - c[0] * dot(d, c), d[1] - c[1] * dot(d, c), d[2] - c[2] * dot(d, c))
            ux, uy = math.degrees(math.asin(max(-1.0, min(1.0, dot(p, e1))))), math.degrees(math.asin(max(-1.0, min(1.0, dot(p, e2)))))
            uy /= max(0.12, tilt)                                       # the ring is an ellipse
            t = math.sqrt(ux * ux + uy * uy)
            ang = math.atan2(uy, ux)
            ring = math.exp(-((t - radius_deg) / width_deg) ** 2)
            doppler = 0.55 + 0.45 * math.cos(ang - 0.6)                 # one side brighter
            turb = 0.7 + 0.6 * fbm(ang * 6.0, t * 0.7, seed, 4)
            v = ring * doppler * turb * strength
            self.add(px, py, (color[0] * v, color[1] * v, color[2] * v))
            if t < hole_deg:
                i = 3 * (py * W + px)
                self.buf[i] = self.buf[i + 1] = self.buf[i + 2] = 0.0
        self.region(c, radius_deg * 1.6 + 8.0, paint)
        # a faint lensed halo around the hole
        def halo(px, py, d):
            t = math.degrees(math.acos(max(-1.0, min(1.0, dot(d, c)))))
            if t < hole_deg:
                return
            g = 0.1 * math.exp(-((t - hole_deg) / (hole_deg * 0.9)) ** 2)
            self.add(px, py, (color[0] * g, color[1] * g * 0.7, color[2] * g * 0.5))
        self.region(c, hole_deg * 3.2, halo)

    # ------------------------------------------------------------------------------------------ output
    def save(self, name, sun_az, sun_el, horizon):
        path = os.path.join(fh.cache_dir(), name + ".hdr")
        import array
        fh.write_hdr(path, W, H, array.array("f", self.buf))
        rows = []
        for oy in range(256):
            y = oy * H // 256
            row = bytearray()
            for ox in range(512):
                x = ox * W // 512
                i = 3 * (y * W + x)
                px = []
                for k in range(3):
                    v = self.buf[i + k] * 1.4
                    v = (v / (1.0 + v)) ** (1.0 / 2.2)
                    px.append(min(255, int(v * 255)))
                row += bytes(px)
            rows.append(bytes(row))
        fh._png(os.path.join(fh.cache_dir(), name + ".png"), 512, 256, rows)
        print("wrote", path, "sun az %.1f el %.1f horizon %s" % (sun_az, sun_el, horizon))


def orbital():
    sun_az, sun_el = 35.0, 32.0
    sd = direction(sun_az, sun_el)
    s = Sky()
    s.nebula(5, ((0.05, 0.07, 0.14), (0.10, 0.06, 0.12), (0.03, 0.05, 0.09)), 0.35, scale=2.2, clear=0.55)
    s.stars(6500, 11)
    # a banded gas giant, about 28 degrees across, low in the sky and lit from the sun's side
    s.planet(direction(95.0, 7.0), 23.0, sd, [(0.95, 0.74, 0.50), (0.72, 0.42, 0.24), (0.98, 0.86, 0.66), (0.55, 0.36, 0.30), (0.90, 0.70, 0.52)],
             (1.0, (1.0, 0.65, 0.35)), seed=21)
    # a small moon beside it
    s.planet(direction(190.0, 12.0), 2.6, sd, [(0.7, 0.7, 0.72)], (0.2, (0.8, 0.85, 1.0)), seed=5, crater=True, noise_scale=5.0)
    s.disc(sd, 0.55, (14.0, 13.6, 12.6), halo=0.5, halo_deg=4.5)
    s.save("space_orbital", sun_az, sun_el, (0.18, 0.15, 0.13))
    return sun_az, sun_el


def derelict():
    sun_az, sun_el = 215.0, 24.0
    sd = direction(sun_az, sun_el)
    s = Sky()
    s.nebula(9, ((0.30, 0.10, 0.45), (0.06, 0.40, 0.45), (0.5, 0.2, 0.3)), 2.2, scale=1.9, clear=0.34)
    s.stars(5000, 33, bright=0.8)
    s.planet(direction(300.0, 18.0), 7.0, sd, [(0.62, 0.62, 0.64)], (0.15, (0.8, 0.8, 1.0)), seed=8, crater=True, noise_scale=4.5)
    s.disc(sd, 0.4, (9.0, 8.4, 7.4), halo=0.25, halo_deg=3.0)
    s.save("space_derelict", sun_az, sun_el, (0.09, 0.06, 0.10))
    return sun_az, sun_el


def nexus():
    sun_az, sun_el = 250.0, 30.0
    sd = direction(sun_az, sun_el)
    s = Sky()
    s.nebula(14, ((0.30, 0.10, 0.04), (0.05, 0.10, 0.30), (0.4, 0.15, 0.05)), 0.5, scale=2.0, clear=0.5)
    s.stars(11000, 55)
    s.ring(direction(70.0, 14.0), 19.0, 2.6, (4.0, 1.6, 0.5), 8.0, strength=1.2, tilt=0.30)
    s.disc(sd, 0.45, (9.0, 11.0, 14.0), halo=0.4, halo_deg=4.0)
    s.save("space_nexus", sun_az, sun_el, (0.10, 0.07, 0.07))
    return sun_az, sun_el


if __name__ == "__main__":
    which = sys.argv[1:] or ["orbital", "derelict", "nexus"]
    for name in which:
        {"orbital": orbital, "derelict": derelict, "nexus": nexus}[name]()
