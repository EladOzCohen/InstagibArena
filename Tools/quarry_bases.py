"""The two team bases of DM-Quarry as Structs (local frame: u toward the pit, v north, origin = flag centre, z = ground).

  red_plant()   crushing plant: flag hall with a crusher deck, silos, conveyors, containers
  blue_dock()   loading dock: flag hall with dock doors, platform, gantry crane, office, trucks

Both share the gameplay skeleton (hall u -800..700, v -650..650; gates: east v=0, north u=430, south u=430; stairs to a deck along the
west wall at z=430). Positions that the map script needs (starts, lights, props) are in BASE_INFO.
"""

import math
import random

import mesh_b as mb
from quarry_struct import Struct, wall, box, hcolumn, gable_roof, silo, conveyor, container, haul_truck, plate, wheel

HU0, HU1, HV0, HV1 = -800.0, 700.0, -650.0, 650.0
HH = 700.0          # wall height
DECK_Z = 430.0
GATES_E = [(650.0, 520.0, 0.0, 430.0)]            # (s along wall from its start, width, zb, zt)


def _hall(st, style):
    """Walls with three gates, clerestory slits, roof, columns, mezzanine deck and stairs, flag plinth."""
    t = 40.0
    lo_h = 260.0
    # south wall (v = HV0) runs west -> east: s measured from u = HU0
    slits = [(s, 190.0, 520.0, 610.0) for s in (160.0, 420.0, 680.0, 940.0)]
    wall(st, (HU0, HV0), (HU1, HV0), t, HH, openings=[(430.0 - HU0, 380.0, 0.0, 420.0)] + slits, lo_h=lo_h)
    # north wall (v = HV1)
    wall(st, (HU0, HV1), (HU1, HV1), t, HH, openings=[(430.0 - HU0, 380.0, 0.0, 420.0)] + slits, lo_h=lo_h)
    # west wall (u = HU0), closed, with two high slits
    wall(st, (HU0, HV0), (HU0, HV1), t, HH, openings=[(325.0, 160.0, 520.0, 610.0), (975.0, 160.0, 520.0, 610.0)], lo_h=lo_h)
    # east wall (u = HU1) with the main gate
    wall(st, (HU1, HV0), (HU1, HV1), t, HH, openings=[(650.0, 520.0, 0.0, 430.0)], lo_h=lo_h)
    # floor slab inside, plinth for the flag
    box(st, "floor", (HU0 + HU1) / 2.0, 0.0, -2.0, HU1 - HU0, HV1 - HV0, 8.0)
    k = st.k("conc", False)
    k.cyl(0, 0, 6.0, 12.0, 130.0, sides=24)
    st.k("steel", False).cyl(0, 0, 12.0, 14.0, 112.0, sides=24)
    st.k("team", False).bx(HU1 + 22.0, 0.0, 470.0, 4.0, 1100.0, 60.0)
    st.k("team", False).bx(0.0, HV1 + 22.0, 470.0, 1100.0, 4.0, 60.0)
    st.k("team", False).bx(0.0, HV0 - 22.0, 470.0, 1100.0, 4.0, 60.0)
    for i in range(12):
        a = 2 * math.pi * i / 12.0
        st.k("yellow", False).bx(math.cos(a) * 138.0, math.sin(a) * 138.0, 6.0, 20.0, 8.0, 20.0, yaw=math.degrees(a))
    # roof
    gable_roof(st, "roof", "steel", (HU0 + HU1) / 2.0, 0.0, HH, HU1 - HU0, HV1 - HV0, 230.0, ridge_along_x=True, trusses=7)
    # columns inside along the long walls
    for u in (-560.0, -200.0, 160.0, 520.0):
        for v in (-585.0, 585.0):
            hcolumn(st, "steel", u, v, 0.0, HH, solid=False)
    # crane runway beam below the trusses
    for v in (-585.0, 585.0):
        st.k("steel", False).beam((HU0, v, HH - 90.0), (HU1, v, HH - 90.0), 30.0, 40.0)
    # mezzanine deck along the west wall
    dk = st.k("plate", True)
    dk.box((HU0 + 20.0 + -470.0) / 2.0, 0.0, DECK_Z - 14.0, 300.0, 1240.0, 14.0, base=True) if False else None
    dk.box(-620.0, 0.0, DECK_Z - 14.0, 300.0, 1240.0, 14.0, base=True)
    sk = st.k("steel", False)
    for u in (-760.0, -480.0):
        for v in (-600.0, -300.0, 0.0, 300.0, 600.0):
            sk.bx(u, v, 0.0, 14.0, 14.0, DECK_Z - 14.0)
    for v in (-600.0, -300.0, 0.0, 300.0, 600.0):
        sk.beam((-770.0, v, DECK_Z - 30.0), (-470.0, v, DECK_Z - 30.0), 8.0, 24.0)
    for u in (-760.0, -620.0, -480.0):
        sk.beam((u, -620.0, DECK_Z - 30.0), (u, 620.0, DECK_Z - 30.0), 8.0, 24.0)
    # rail on the east edge of the deck, gaps where the stairs arrive
    yk = st.k("yellow", False)
    yk.rail((-470.0, -620.0, DECK_Z), (-470.0, -450.0, DECK_Z), every=170.0)
    yk.rail((-470.0, -350.0, DECK_Z), (-470.0, 350.0, DECK_Z), every=230.0)
    yk.rail((-470.0, 450.0, DECK_Z), (-470.0, 620.0, DECK_Z), every=170.0)
    # stairs up to the deck from the south and from the north (run along u)
    for sv in (-1, 1):
        v = sv * 400.0
        k2 = st.k("plate", True)
        k2.stairs(200.0, v, 0.0, -470.0, v, DECK_Z, 130.0, stringers=True, riser_closed=False)
        yk.rail((200.0, v + 70.0, 0.0), (-470.0, v + 70.0, DECK_Z), every=170.0, mid=True)
        yk.rail((200.0, v - 70.0, 0.0), (-470.0, v - 70.0, DECK_Z), every=170.0, mid=True)
    # low concrete cover blocks inside
    for (u, v, sx, sy) in ((-200.0, 260.0, 170.0, 70.0), (-200.0, -260.0, 170.0, 70.0), (330.0, 220.0, 90.0, 130.0), (330.0, -220.0, 90.0, 130.0)):
        box(st, "conc_dark", u, v, 0.0, sx, sy, 105.0)
        box(st, "yellow", u, v, 105.0, sx + 6.0, sy + 6.0, 6.0, solid=False)
    # service block behind the west wall: blocks the sight along the back of the base
    box(st, "conc", -1030.0, 0.0, -30.0, 190.0, 760.0, 360.0)
    box(st, "corr", -1030.0, 0.0, 330.0, 220.0, 790.0, 24.0, solid=False)
    for v in (-250.0, 0.0, 250.0):
        st.k("steel", False).bx(-1130.0, v, 0.0, 10.0, 90.0, 220.0)
    # clerestory glow strips are done by lights in the map script


def _crusher(st):
    """Primary jaw crusher on the deck, feed hopper, motors and a flywheel under the deck, output chute."""
    d = st.k("dark", True)
    d.bx(-660.0, 0.0, DECK_Z, 230.0, 300.0, 170.0)
    st.k("steel", True).bx(-690.0, 0.0, DECK_Z + 170.0, 160.0, 220.0, 40.0)
    # feed hopper (a four sided frustum made of plates)
    hk = st.k("rustc", True)
    a = [(-760.0, -170.0, DECK_Z + 210.0), (-560.0, -170.0, DECK_Z + 210.0), (-560.0, 170.0, DECK_Z + 210.0), (-760.0, 170.0, DECK_Z + 210.0)]
    b = [(-710.0, -75.0, DECK_Z + 20.0), (-610.0, -75.0, DECK_Z + 20.0), (-610.0, 75.0, DECK_Z + 20.0), (-710.0, 75.0, DECK_Z + 20.0)]
    pts = a + b
    hk.convex(pts, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    st.k("yellow", False).beam((-760.0, -170.0, DECK_Z + 214.0), (-560.0, -170.0, DECK_Z + 214.0), 8.0, 8.0)
    st.k("yellow", False).beam((-760.0, 170.0, DECK_Z + 214.0), (-560.0, 170.0, DECK_Z + 214.0), 8.0, 8.0)
    # under the deck: motors, flywheel guard, gearbox
    for v in (-420.0, 0.0, 420.0):
        st.k("dark", True).bx(-700.0, v, 0.0, 140.0, 150.0, 190.0)
        st.k("steel", False).cyl(-700.0, v, 190.0, 215.0, 55.0, sides=14)
        st.k("steel", False).bx(-640.0, v, 0.0, 12.0, 70.0, 150.0)
    # output chute and a belt leaving through the west wall
    st.k("steel", False).beam((-560.0, 0.0, DECK_Z + 120.0), (-820.0, 0.0, DECK_Z + 40.0), 80.0, 10.0)


def red_plant():
    st = Struct("RedPlant")
    _hall(st, "crush")
    _crusher(st)
    # silos in the north yard
    for i, u in enumerate((-680.0, 0.0, 680.0)):
        silo(st, u, 1230.0, 0.0, 255.0, 1250.0 - 80.0 * (i == 1), mat="conc", legs=True)
    silo(st, 1250.0, 1050.0, 0.0, 150.0, 760.0, mat="conc", legs=True, hopper=False, roof=True)
    # high gallery over the silos with a conveyor to the crusher
    gk = st.k("plate", False)
    gk.box(0.0, 1230.0, 1405.0, 1500.0, 70.0, 10.0, base=True)
    yk = st.k("yellow", False)
    yk.rail((-750.0, 1195.0, 1415.0), (750.0, 1195.0, 1415.0), h=100.0, every=250.0)
    yk.rail((-750.0, 1265.0, 1415.0), (750.0, 1265.0, 1415.0), h=100.0, every=250.0)
    conveyor(st, (-900.0, 1230.0, 1470.0), (900.0, 1230.0, 1470.0), w=60.0, hood=True, supports=False)
    conveyor(st, (-830.0, 210.0, 520.0), (-900.0, 1210.0, 1450.0), w=70.0, hood=True, supports=True, every=420.0)
    # a transfer tower at the north-west corner
    tk = st.k("steel", True)
    tk.lattice_tower(-950.0, 1210.0, 0.0, 1480.0, 190.0, 150.0, leg=18.0)
    # containers in the south yard (red and rust)
    container(st, "cont_r", -520.0, -1300.0, 0.0, 0.0, doors=0)
    container(st, "cont_r", -520.0, -1300.0, 250.0, 0.0, doors=0, solid=False) if False else None
    container(st, "cont_g", -380.0, -1560.0, 0.0, 90.0, doors=1)
    container(st, "cont_r", 540.0, -1150.0, 0.0, 90.0, doors=-1)
    container(st, "cont_y", 700.0, -1500.0, 0.0, 0.0, doors=1)
    container(st, "cont_r", -120.0, -1400.0, 0.0, 0.0, length=600.0, doors=1)
    container(st, "cont_r", -120.0, -1400.0, 250.0, 10.0, doors=1)
    # pipe rack along the hall's north wall
    for u in range(-700, 700, 340):
        st.k("steel", False).bx(u, 760.0, 0.0, 14.0, 14.0, 300.0)
    st.k("steel", False).pipe((-740.0, 760.0, 300.0), (700.0, 760.0, 300.0), 14.0)
    st.k("rustc", False).pipe((-740.0, 790.0, 300.0), (700.0, 790.0, 300.0), 22.0)
    st.k("steel", False).pipe((-740.0, 760.0, 340.0), (700.0, 760.0, 340.0), 10.0)
    # concrete push walls (cover) on the apron
    for (u, v, a_) in ((1000.0, 330.0, 90.0), (1000.0, -330.0, 90.0), (1250.0, 0.0, 0.0)):
        k = st.k("conc", True)
        k.box(u, v, 0.0, 260.0 if a_ == 0 else 40.0, 40.0 if a_ == 0 else 260.0, 150.0, base=True)
    # decline portal frame at the top of the red decline (local u -140..340, v -1950)
    for u in (-170.0, 370.0):
        box(st, "conc", u, -1960.0, -300.0, 60.0, 360.0, 380.0)
    st.k("steel", False).bx(100.0, -1960.0, 80.0, 540.0, 24.0, 20.0)
    return st


def blue_dock():
    st = Struct("BlueDock")
    _hall(st, "dock")
    # dock platform east of the hall with a ramp down at the gate
    box(st, "conc", 840.0, -400.0, -20.0, 280.0, 500.0, 150.0)
    box(st, "conc", 840.0, 400.0, -20.0, 280.0, 500.0, 150.0)
    # ramps from the gate (v -150..150) down to the yard: a wedge each side is part of the platform; the gate lane stays level
    for sv in (-1, 1):
        st.k("steel", False).bx(990.0, sv * 255.0, 130.0, 8.0, 500.0, 4.0)
    # roller doors (closed, decorative) on the east face of the platform side
    for v in (-420.0, 420.0):
        st.k("corr", False).bx(704.0, v, 0.0, 10.0, 300.0, 330.0)
        st.k("yellow", False).bx(706.0, v, 330.0, 8.0, 330.0, 16.0)
        st.k("rubber", False).bx(990.0, v - 130.0, 90.0, 24.0, 40.0, 70.0)
        st.k("rubber", False).bx(990.0, v + 130.0, 90.0, 24.0, 40.0, 70.0)
    # gantry crane over the north yard: two runways, a bridge beam and a trolley
    for u in (-300.0, 520.0):
        for v in (820.0, 1700.0):
            lk = st.k("steel", True)
            lk.bx(u, v, 0.0, 44.0, 44.0, 980.0)
            st.k("steel", False).beam((u, v, 180.0), (u + (80.0 if u < 0 else -80.0), v, 20.0), 20.0, 20.0)
        st.k("yellow", False).beam((u, 820.0, 990.0), (u, 1700.0, 990.0), 46.0, 56.0)
    st.k("steel", False).beam((-300.0, 1260.0, 1030.0), (520.0, 1260.0, 1030.0), 60.0, 60.0)
    st.k("yellow", False).bx(110.0, 1260.0, 1090.0, 120.0, 90.0, 70.0)
    st.k("steel", False).bx(110.0, 1260.0, 600.0, 4.0, 4.0, 490.0)
    st.k("yellow", False).bx(110.0, 1260.0, 560.0, 34.0, 26.0, 50.0)
    st.k("rubber", False).bx(110.0, 1260.0, 620.0, 4.0, 4.0, 0.1) if False else None
    # office block at the north-east corner with an outside steel stair to the roof
    ob = st.k("conc_clean", True)
    ob.box(1000.0, 900.0, 0.0, 420.0, 360.0, 330.0, base=True)
    st.k("corr", False).bx(1000.0, 900.0, 330.0, 440.0, 380.0, 30.0)
    for i in range(3):
        st.k("glass_dark", False).bx(1000.0 - 120.0 + i * 120.0, 719.0, 150.0, 80.0, 4.0, 100.0)
    st.k("steel", False).bx(1000.0, 719.0, 0.0, 70.0, 6.0, 210.0)
    st.k("plate", True).stairs(1250.0, 1000.0, 0.0, 1250.0, 820.0, 360.0, 110.0, stringers=True) if False else None
    st.k("plate", True).stairs(1260.0, 1150.0, 0.0, 1260.0, 760.0, 360.0, 110.0, stringers=True)
    st.k("yellow", False).rail((1210.0, 760.0, 360.0), (1210.0, 1150.0, 0.0), every=180.0)
    st.k("yellow", False).rail((1310.0, 760.0, 360.0), (1310.0, 1150.0, 0.0), every=180.0)
    st.k("plate", True).box(1050.0, 900.0, 358.0, 300.0, 340.0, 8.0, base=True) if False else None
    # containers (blue) and a weighbridge
    container(st, "cont_b", -520.0, -1300.0, 0.0, 0.0, doors=0)
    container(st, "cont_b", -380.0, -1560.0, 0.0, 90.0, doors=1)
    container(st, "cont_w", 540.0, -1150.0, 0.0, 90.0, doors=-1)
    container(st, "cont_b", 700.0, -1500.0, 0.0, 0.0, doors=1)
    container(st, "cont_b", -120.0, -1400.0, 0.0, 0.0, doors=1)
    container(st, "cont_w", -120.0, -1400.0, 250.0, 10.0, doors=1)
    box(st, "plate", 1100.0, -300.0, -2.0, 700.0, 260.0, 10.0)
    for v in (-420.0, -180.0):
        box(st, "steel", 1100.0, v, 4.0, 700.0, 10.0, 6.0, solid=False)
    # truck parked at the platform
    haul_truck(st, paint="paint_b", x=1360.0, y=-1100.0, yaw=90.0, scale=0.9)
    # pipe run on the hall's north wall and covered conveyor out of the dock
    st.k("steel", False).pipe((-740.0, 700.0, 340.0), (700.0, 700.0, 340.0), 12.0)
    for u in range(-700, 700, 340):
        st.k("steel", False).bx(u, 700.0, 0.0, 14.0, 14.0, 340.0)
    for (u, v, a_) in ((1050.0, 330.0, 90.0), (1300.0, 0.0, 0.0)):
        k = st.k("conc_clean", True)
        k.box(u, v, 0.0, 260.0 if a_ == 0 else 40.0, 40.0 if a_ == 0 else 260.0, 150.0, base=True)
    for u in (-170.0, 370.0):
        box(st, "conc_clean", u, -1960.0, -300.0, 60.0, 360.0, 380.0)
    st.k("steel", False).bx(100.0, -1960.0, 80.0, 540.0, 24.0, 20.0)
    return st
