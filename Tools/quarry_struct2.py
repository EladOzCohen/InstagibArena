"""More Quarry structures: excavator, drilling rig, water tank, scaffolding tower (see quarry_struct.py for the basics)."""

import math

import mesh_b as mb
from quarry_struct import Struct, wheel


def copy_into(st, tmp, x, y, z, yaw):
    c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for (mat, solid), mesh in tmp.g.items():
        dst = st.k(mat, solid)
        base = len(dst.verts)
        for v, n in zip(mesh.verts, mesh.norms):
            dst.verts.append((x + v[0] * c - v[1] * sn, y + v[0] * sn + v[1] * c, z + v[2]))
            dst.norms.append((n[0] * c - n[1] * sn, n[0] * sn + n[1] * c, n[2]))
        for (a, b_, c_) in mesh.tris:
            dst.tris.append((a + base, b_ + base, c_ + base))


def excavator(st, x, y, z, yaw, paint="paint_y", steel="steel", dark="dark", rust="rustc"):
    """A hydraulic excavator about 900 long: tracks, house, cab, boom, stick and bucket."""
    t = Struct("tmp")
    for sy in (-1, 1):
        t.k(dark, True).bx(0, sy * 150.0, 0.0, 560.0, 100.0, 95.0)
        for i in range(-5, 6):
            t.k(steel, False).bx(i * 50.0, sy * 150.0, 0.0, 22.0, 108.0, 100.0)
        for sx in (-1, 1):
            wheel(t, dark, steel, sx * 240.0, sy * 150.0, 50.0, 55.0, 100.0)
    t.k(steel, True).bx(0, 0, 90.0, 420.0, 260.0, 30.0)
    h = t.k(paint, True)
    h.bx(-30.0, 0, 120.0, 400.0, 290.0, 150.0)
    h.bx(-210.0, 0, 120.0, 90.0, 280.0, 190.0)
    h.bx(120.0, -100.0, 270.0, 120.0, 100.0, 120.0)
    t.k(dark, False).bx(180.0, -100.0, 300.0, 4.0, 90.0, 70.0)
    t.k(steel, False).cyl(-200.0, 90.0, 270.0, 400.0, 9.0, sides=8)
    pb = [(110.0, 0.0, 200.0), (320.0, 0.0, 520.0), (600.0, 0.0, 300.0)]
    pk = t.k(paint, True)
    pk.beam(pb[0], pb[1], 55.0, 50.0)
    pk.beam(pb[1], pb[2], 40.0, 36.0)
    t.k(steel, False).beam((150.0, 30.0, 150.0), (290.0, 30.0, 440.0), 14.0, 14.0)
    t.k(steel, False).beam((330.0, 30.0, 500.0), (470.0, 30.0, 250.0), 12.0, 12.0)
    t.k(rust, True).bx(640.0, 0.0, 150.0, 120.0, 170.0, 110.0, pitch=-25.0)
    for i in range(5):
        t.k(steel, False).bx(690.0, -64.0 + i * 32.0, 150.0, 22.0, 8.0, 16.0)
    copy_into(st, t, x, y, z, yaw)


def drill_rig(st, x, y, z, yaw, steel="steel", rust="rustc", paint="paint_y", dark="dark"):
    """A drilling rig: tracked carrier, a 1100 cm lattice mast with a head, rod racks, compressor."""
    t = Struct("tmp")
    for sy in (-1, 1):
        t.k(dark, True).bx(0, sy * 130.0, 0.0, 520.0, 90.0, 90.0)
    t.k(steel, True).bx(0, 0, 90.0, 480.0, 300.0, 40.0)
    t.k(paint, True).bx(-120.0, 0, 130.0, 220.0, 250.0, 170.0)
    t.k(paint, True).bx(-210.0, 0, 130.0, 90.0, 250.0, 260.0)
    t.k(dark, False).bx(-120.0, 126.0, 220.0, 100.0, 4.0, 60.0)
    t.k(steel, False).lattice_tower(150.0, 0.0, 130.0, 1150.0, 110.0, 80.0, levels=7, leg=9.0)
    t.k(rust, False).bx(150.0, 0.0, 1150.0, 100.0, 100.0, 40.0)
    t.k(steel, False).cyl(150.0, 0.0, 130.0, 1100.0, 8.0, sides=8)
    for i in range(4):
        t.k(steel, False).pipe((-100.0 + i * 20.0, -150.0, 150.0), (250.0, -150.0, 380.0 + i * 12.0), 7.0, sides=6)
    t.k(rust, True).bx(-250.0, 200.0, 0.0, 200.0, 140.0, 150.0)
    t.k(dark, False).cyl(-250.0, 200.0, 150.0, 190.0, 40.0, sides=10)
    copy_into(st, t, x, y, z, yaw)


def water_tank(st, x, y, z, r=210.0, h=480.0, stilt=300.0, steel="steel", rust="rustc"):
    st.k(rust, True).cyl(x, y, z + stilt, z + stilt + h, r, sides=24, cap_top=True, cap_bottom=True)
    st.k(steel, False).frustum(x, y, z + stilt + h, z + stilt + h + 60.0, r, r * 0.3, sides=24, cap_top=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            st.k(steel, True).bx(x + sx * r * 0.7, y + sy * r * 0.7, z, 22.0, 22.0, stilt + 10.0)
    for i in range(2):
        for sa, sb in (((-1, -1), (1, 1)), ((1, -1), (-1, 1))):
            st.k(steel, False).beam((x + sa[0] * r * 0.7, y + sa[1] * r * 0.7, z + 20.0 + i * 120.0),
                                    (x + sb[0] * r * 0.7, y + sb[1] * r * 0.7, z + 140.0 + i * 120.0), 8.0, 8.0)
    for zz in range(int(z + stilt + 80), int(z + stilt + h), 120):
        st.k(steel, False).cyl(x, y, zz, zz + 8.0, r + 4.0, sides=24, cap_top=False, cap_bottom=False)
    st.k(steel, False).pipe((x + r + 20.0, y, z), (x + r + 20.0, y, z + stilt + h * 0.6), 7.0, sides=6)


def scaffold(st, x, y, z, w, h, steel="steel", plank="plate"):
    k = st.k(steel, False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.bx(x + sx * w / 2.0, y + sy * w / 2.0, z, 6.0, 6.0, h)
    n = int(h / 220.0)
    for i in range(n + 1):
        zz = z + i * 220.0
        for sa, sb in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            k.beam((x + sa[0] * w / 2.0, y + sa[1] * w / 2.0, zz + 100.0), (x + sb[0] * w / 2.0, y + sb[1] * w / 2.0, zz + 100.0), 5.0, 5.0)
        if i < n:
            for sa, sb in (((-1, -1), (1, -1)), ((1, 1), (-1, 1))):
                k.beam((x + sa[0] * w / 2.0, y + sa[1] * w / 2.0, zz), (x + sb[0] * w / 2.0, y + sb[1] * w / 2.0, zz + 220.0), 4.0, 4.0)
        if i > 0 and i % 2 == 0:
            st.k(plank, False).bx(x, y, zz + 98.0, w, w, 4.0)
