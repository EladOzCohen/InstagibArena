"""Pure python geometry for DM-Citadel (builds on mesh_b.Mesh; no unreal import, so it can be tested with any python).

Local frames: walls run along +x with y = 0 the OUTER face and y = thick the inner face, z up. Everything is in cm.
  xform           rotate / mirror / move a mesh (mirror flips the triangle order)
  wall            masonry wall with arched or square openings, battlements, corbel course, plinth
  drum_tower      round tower with flared foot, corbelled top, flat platform, merlons, optional conical roof
  gable_roof      steep two-sided roof (solid prism, too steep to walk on), hip_roof (4 sides)
  building        enterable shell: four walls with doors and windows, floor, ceiling -> dict of meshes by material role
  arch_ring       voussoir ring around an opening
  vault_corridor  stone tunnel with a barrel vault (floor at z = 0, runs along +x)
  terrain_tile    a tile of the ground as one mesh per material slot (analytic normals, holes)
  ribbon, patch   thin overlays that follow the terrain (roads, dirt patches)
"""

import math
import random

from mesh_b import Mesh, clamp, fbm, lerp, ridged, smoothstep, rot_z, cross, sub, norm


# ------------------------------------------------------------------------------------------------ transforms
def xform(mesh, yaw=0.0, mirror=False, offset=(0.0, 0.0, 0.0), scale=1.0, pitch=0.0):
    """Returns a copy: scale, rotate about z by yaw (degrees), mirror x (after the rotation), then move."""
    out = Mesh()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def f(v, pos):
        x, y, z = v[0] * scale, v[1] * scale, v[2] * scale
        if pitch:
            x, z = x * cp - z * sp, x * sp + z * cp
        x, y = x * c - y * s, x * s + y * c
        if mirror:
            x = -x
        return (x + offset[0], y + offset[1], z + offset[2]) if pos else (x, y, z)

    def fn(n):
        x, y, z = n
        if pitch:
            x, z = x * cp - z * sp, x * sp + z * cp
        x, y = x * c - y * s, x * s + y * c
        if mirror:
            x = -x
        return (x, y, z)
    out.verts = [f(v, True) for v in mesh.verts]
    out.norms = [fn(n) for n in mesh.norms]
    out.tris = [(a, c_, b) if mirror else (a, b, c_) for (a, b, c_) in mesh.tris]
    return out


def merged(*meshes):
    m = Mesh()
    for k in meshes:
        if k is not None and k.verts:
            m.append(k)
    return m


def uv_free(m):
    return m


# ------------------------------------------------------------------------------------------------ arches
def arch_ring(R, tk, y0, y1, segments=14, z_spring=0.0, x_center=0.0, jitter=0.4, seed=1, both=True):
    """A ring of voussoirs round a round-arched opening of radius R (inner), thickness tk, spanning y0..y1 (the wall plane runs along x)."""
    rng = random.Random(seed)
    m = Mesh()
    for k in range(segments):
        a0 = math.pi * k / segments
        a1 = math.pi * (k + 1) / segments
        ex = tk * (1.28 if k == segments // 2 or (segments % 2 == 0 and k == segments // 2 - 1) else 1.0)
        pts = [(x_center + R * math.cos(a0), z_spring + R * math.sin(a0)), (x_center + R * math.cos(a1), z_spring + R * math.sin(a1)),
               (x_center + (R + ex) * math.cos(a1), z_spring + (R + ex) * math.sin(a1)), (x_center + (R + ex) * math.cos(a0), z_spring + (R + ex) * math.sin(a0))]
        m.prism(pts, y0, y1, jitter=jitter, seed=seed * 7 + k)
    return m


# ------------------------------------------------------------------------------------------------ walls
def wall(length, height, thick, openings=(), seed=1, base_z=-60.0, jitter=0.5, crenel=None, plinth=0.0, ring=0.0, ring_depth=14.0, corbel=0.0):
    """Masonry wall along +x (0..length), y 0 (outer) .. thick (inner), from base_z to height. openings: dicts(u0, u1, z0=0, z1, arch=False).
    crenel: dict(outer=True, inner=True, parapet_h=100, parapet_t=48, merlon_w=100, gap=86, merlon_h=75).
    plinth: height of a slightly proud foot course; ring: thickness of an arch ring round arched openings; corbel: height of a projecting top course."""
    rng = random.Random(seed)
    m = Mesh()
    ops = sorted(openings, key=lambda o: o["u0"])

    def solid(u0, u1, z0, z1, top_flush=True):
        if u1 - u0 < 0.5 or z1 - z0 < 0.5:
            return
        m.box((u0 + u1) / 2.0, thick / 2.0, z0, u1 - u0 + 0.2, thick + rng.uniform(-1.0, 1.0), z1 - z0, base=True, jitter=jitter, top_jitter=0.0 if top_flush else jitter,
              seed=rng.randint(0, 10 ** 6))
    cur = 0.0
    for o in ops:
        u0, u1 = o["u0"], o["u1"]
        z0, z1 = o.get("z0", 0.0), o["z1"]
        arch = o.get("arch", False)
        solid(cur, u0, base_z, height)
        if z0 > base_z + 1.0:
            solid(u0, u1, base_z, z0)
        solid(u0, u1, z1, height)
        if arch:
            R = (u1 - u0) / 2.0
            zs = z1 - R
            uc = (u0 + u1) / 2.0
            N = 14
            for k in range(N):
                xa = u0 + (u1 - u0) * k / N
                xb = u0 + (u1 - u0) * (k + 1) / N
                za = zs + math.sqrt(max(0.0, R * R - (xa - uc) ** 2))
                zb = zs + math.sqrt(max(0.0, R * R - (xb - uc) ** 2))
                m.prism([(xa, za), (xb, zb), (xb, z1 + 0.3), (xa, z1 + 0.3)], 0.0, thick, jitter=0.0)
            if ring > 0.0:
                for face in (0, 1):
                    y0_, y1_ = (-ring_depth, 0.0) if face == 0 else (thick, thick + ring_depth)
                    m.append(arch_ring(R, ring, y0_, y1_, segments=14, z_spring=zs, x_center=uc, seed=seed + int(u0)))
                    for sgn in (-1, 1):                       # jambs under the ring
                        jx = uc + sgn * (R + ring / 2.0)
                        m.box(jx, (y0_ + y1_) / 2.0, z0, ring, ring_depth, zs - z0 + 1.0, base=True, jitter=0.4, seed=seed + sgn + int(u0))
        elif ring > 0.0:
            for face in (0, 1):
                y0_, y1_ = (-ring_depth, 0.0) if face == 0 else (thick, thick + ring_depth)
                m.box((u0 + u1) / 2.0, (y0_ + y1_) / 2.0, z1 - 1.0, u1 - u0 + ring * 2.0, ring_depth, ring * 1.1, base=True, jitter=0.4, seed=seed + int(u0))
                for sgn in (-1, 1):
                    m.box((u0 if sgn < 0 else u1) + sgn * ring / 2.0, (y0_ + y1_) / 2.0, z0, ring, ring_depth, z1 - z0, base=True, jitter=0.4, seed=seed + sgn)
        cur = u1
    solid(cur, length, base_z, height)
    if plinth > 0.0:
        cur_p = 0.0
        spans = [(o["u0"] - (ring + 4.0 if ring else 0.0), o["u1"] + (ring + 4.0 if ring else 0.0)) for o in ops if o.get("z0", 0.0) < plinth]
        for a_, b_ in spans + [(length, length)]:
            if a_ - cur_p > 1.0:
                m.box((cur_p + a_) / 2.0, -11.0, base_z, a_ - cur_p, 22.0, plinth - base_z, base=True, jitter=0.5, seed=seed + 5 + int(cur_p))
            cur_p = max(cur_p, b_)
    if corbel > 0.0:
        m.box(length / 2.0, -9.0, height - corbel, length, 18.0, corbel, base=True, jitter=0.4, top_jitter=0.0, seed=seed + 6)
    if crenel:
        c = dict(outer=True, inner=True, parapet_h=100.0, parapet_t=48.0, merlon_w=100.0, gap=86.0, merlon_h=75.0)
        c.update(crenel)
        pt, ph = c["parapet_t"], c["parapet_h"]
        if c["outer"]:
            m.box(length / 2.0, pt / 2.0, height, length, pt, ph, base=True, jitter=0.3, top_jitter=0.0, seed=seed + 8)
            pitch = c["merlon_w"] + c["gap"]
            n = max(1, int((length - c["gap"]) // pitch))
            start = (length - (n * pitch - c["gap"])) / 2.0
            for i in range(n):
                x = start + c["merlon_w"] / 2.0 + i * pitch
                m.box(x, pt / 2.0, height + ph, c["merlon_w"], pt, c["merlon_h"], base=True, jitter=0.35, top_jitter=0.3, seed=seed * 3 + i)
        if c["inner"]:
            m.box(length / 2.0, thick - 14.0, height, length, 28.0, 60.0, base=True, jitter=0.3, top_jitter=0.0, seed=seed + 9)
    return m


# ------------------------------------------------------------------------------------------------ towers
def drum_tower(radius, height, sides=26, flare=1.12, top_k=1.2, merlons=True, roof=0.0, roof_over=1.28, seed=1, parapet=100.0, merlon_h=75.0, base_z=-90.0, gaps=()):
    """A round tower: shaft from base_z to height - corbel, corbelled ring, flat platform at z = height, merlons around its edge.
    roof > 0 adds a conical roof of that height instead of merlons. Origin on the axis."""
    rng = random.Random(seed)
    m = Mesh()
    cor_h = 62.0
    zc = height - cor_h
    total = zc - base_z
    m.lathe(0, 0, base_z, zc, radius, radius, sides=sides, segments=8, profile=[(0.0, flare), (0.16, 1.0), (1.0, 1.0)], cap_bottom=False, cap_top=False, jitter=0.6, seed=seed)
    m.lathe(0, 0, zc, height, radius, radius * top_k, sides=sides, segments=4, profile=[(0.0, 1.0), (0.3, 1.03), (0.55, 1.08), (0.8, 1.14), (1.0, 1.0)], cap_bottom=False, cap_top=True)
    if roof <= 0.0 and merlons:
        R = radius * top_k - 24.0
        n_par = sides
        chord = 2.0 * R * math.sin(math.pi / n_par) + 1.0
        for i in range(n_par):
            a = 2.0 * math.pi * (i + 0.5) / n_par
            if any(abs(((math.degrees(a) - g0 + 180.0) % 360.0) - 180.0) < gh for g0, gh in gaps):
                continue
            m.box(math.cos(a) * R, math.sin(a) * R, height, 46.0, chord, parapet, yaw=math.degrees(a) + 90.0 - 90.0, base=True, jitter=0.3, top_jitter=0.0, seed=seed + i)
            if i % 2 == 0:
                m.box(math.cos(a) * R, math.sin(a) * R, height + parapet, 46.0, chord * 0.95, merlon_h, yaw=math.degrees(a), base=True, jitter=0.35, top_jitter=0.3, seed=seed + 50 + i)
    if roof > 0.0:
        rr = radius * roof_over
        m.lathe(0, 0, height, height + 18.0, rr, rr, sides=sides, segments=1, cap_bottom=True, cap_top=False)
        m.lathe(0, 0, height + 18.0, height + roof, rr, 1.0, sides=sides, segments=10, profile=[(0.0, 1.0), (0.12, 0.93), (0.5, 0.52), (1.0, 0.0)], cap_bottom=False, cap_top=True)
    return m


def square_tower(w, d, height, seed=1, merlons=True, roof=0.0, base_z=-90.0, taper=0.04):
    """A square tower: shaft, a projecting top course, a platform with merlons or a pyramid roof. Centred on the origin."""
    rng = random.Random(seed)
    m = Mesh()
    zc = height - 56.0
    m.box(0, 0, base_z, w * 1.08, d * 1.08, 140.0 - base_z, base=True, jitter=0.5, seed=seed)
    m.box(0, 0, base_z + 100.0, w, d, zc - base_z - 100.0, base=True, jitter=0.5, top_jitter=0.0, seed=seed + 1, taper=taper)
    m.box(0, 0, zc, w * 1.12, d * 1.12, 56.0, base=True, jitter=0.4, top_jitter=0.0, seed=seed + 2)
    if roof <= 0.0 and merlons:
        W, D = w * 1.12, d * 1.12
        for sx_ in (-1, 1):
            m.box(sx_ * (W / 2.0 - 24.0), 0, height, 48.0, D, 100.0, base=True, jitter=0.3, top_jitter=0.0, seed=seed + 5 + sx_)
            m.box(0, sx_ * (D / 2.0 - 24.0), height, W, 48.0, 100.0, base=True, jitter=0.3, top_jitter=0.0, seed=seed + 8 + sx_)
        for sx_ in (-1, 1):
            n = max(2, int(D // 190))
            for i in range(n):
                y = -D / 2.0 + (i + 0.5) * D / n
                m.box(sx_ * (W / 2.0 - 24.0), y, height + 100.0, 48.0, 100.0, 75.0, base=True, jitter=0.35, top_jitter=0.3, seed=seed + 20 + i + sx_)
            for i in range(max(2, int(W // 190))):
                x = -W / 2.0 + (i + 0.5) * W / max(2, int(W // 190))
                m.box(x, sx_ * (D / 2.0 - 24.0), height + 100.0, 100.0, 48.0, 75.0, base=True, jitter=0.35, top_jitter=0.3, seed=seed + 40 + i + sx_)
    if roof > 0.0:
        W, D = w * 1.12, d * 1.12
        ov = 30.0
        pts = [(-W / 2 - ov, -D / 2 - ov), (W / 2 + ov, -D / 2 - ov), (W / 2 + ov, D / 2 + ov), (-W / 2 - ov, D / 2 + ov)]
        tip = (0.0, 0.0, height + roof)
        base_ring = [(p[0], p[1], height) for p in pts]
        m.poly(base_ring, (0, 0, -1))
        for i in range(4):
            a, b = base_ring[i], base_ring[(i + 1) % 4]
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, height + roof * 0.35)
            m.poly([a, b, tip], (mid[0], mid[1], mid[2] - height))
    return m


# ------------------------------------------------------------------------------------------------ roofs
def gable_roof(w, d, rise, overhang=40.0, seed=1, ridge_along_x=True, thick=26.0, with_ridge=True):
    """A gable roof as one closed solid. Ridge along x (span in y) by default. The origin is the centre of the eaves line at z = 0."""
    m = Mesh()
    if ridge_along_x:
        span, length = d, w
    else:
        span, length = w, d
    hs = span / 2.0 + overhang
    hl = length / 2.0 + overhang * 0.7
    rz = rise * (1.0 + overhang / (span / 2.0))
    # outer envelope with an underside offset, so the roof has a visible thickness at the eaves (a lip)
    prof = [(-hs, -thick * 0.2), (hs, -thick * 0.2), (hs, 0.0), (0.0, rz), (-hs, 0.0)]
    m.prism(prof, -hl, hl, jitter=0.0)
    if with_ridge:
        m.box(0, 0, rz - 6.0, 26.0, length + overhang * 1.4, 22.0, base=True, jitter=0.5, seed=seed)
    if not ridge_along_x:
        out = Mesh()
        out.verts = [(v[1], v[0], v[2]) for v in m.verts]
        out.norms = [(n[1], n[0], n[2]) for n in m.norms]
        out.tris = [(a, c, b) for (a, b, c) in m.tris]        # swapping x and y mirrors: flip the winding
        return out
    return m


def hip_roof(w, d, rise, overhang=40.0):
    """A four-sided pyramid-like roof with a short ridge, closed solid, centre of the eaves at z = 0."""
    m = Mesh()
    hw, hd = w / 2.0 + overhang, d / 2.0 + overhang
    rl = max(0.0, (max(w, d) - min(w, d)) / 2.0)
    if w >= d:
        r0, r1 = (-rl, 0.0), (rl, 0.0)
    else:
        r0, r1 = (0.0, -rl), (0.0, rl)
    top0 = (r0[0], r0[1], rise)
    top1 = (r1[0], r1[1], rise)
    c0, c1, c2, c3 = (-hw, -hd, 0.0), (hw, -hd, 0.0), (hw, hd, 0.0), (-hw, hd, 0.0)
    m.poly([c0, c1, c2, c3], (0, 0, -1))
    m.convex([c0, c1, c2, c3, top0, top1], [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)], center=(0, 0, rise * 0.3))
    return m


# ------------------------------------------------------------------------------------------------ buildings
def building(w, d, h, thick=36.0, doors=(), windows=(), seed=1, floor=True, ceiling=True, jitter=0.5, ring=0.0, base_z=-50.0, crenel=None, plinth=0.0):
    """An enterable shell centred on the origin (floor top at z = 0). doors / windows: (side, u_centre, width, height[, sill, arch]) with
    side 0 = -y (front), 1 = +x, 2 = +y, 3 = -x and u measured along the wall from its left end as seen from outside.
    Returns dict(walls=Mesh, floor=Mesh, ceil=Mesh, trim=Mesh)."""
    walls = Mesh()
    trim = Mesh()
    lengths = [w, d, w, d]
    frames = [((-w / 2.0, -d / 2.0), 0.0), ((w / 2.0, -d / 2.0), 90.0), ((w / 2.0, d / 2.0), 180.0), ((-w / 2.0, d / 2.0), 270.0)]
    for side in range(4):
        ops = []
        for dd in doors:
            if dd[0] == side:
                _, uc, ww, hh = dd[:4]
                arch = dd[5] if len(dd) > 5 else True
                ops.append(dict(u0=uc - ww / 2.0, u1=uc + ww / 2.0, z0=0.0, z1=hh, arch=arch))
        for ww_ in windows:
            if ww_[0] == side:
                _, uc, ww, hh = ww_[:4]
                sill = ww_[4] if len(ww_) > 4 else 110.0
                arch = ww_[5] if len(ww_) > 5 else False
                ops.append(dict(u0=uc - ww / 2.0, u1=uc + ww / 2.0, z0=sill, z1=sill + hh, arch=arch))
        wm = wall(lengths[side], h, thick, ops, seed=seed * 5 + side, base_z=base_z, jitter=jitter, ring=ring, ring_depth=10.0, plinth=plinth, crenel=crenel)
        org, yaw = frames[side]
        walls.append(xform(wm, yaw=yaw, offset=(org[0], org[1], 0.0)))
    out = dict(walls=walls, trim=trim)
    if floor:
        f = Mesh()
        f.box(0, 0, -22.0, w - 2.0, d - 2.0, 22.0, base=True, jitter=0.0)
        out["floor"] = f
    if ceiling:
        c = Mesh()
        c.box(0, 0, h, w + 2.0, d + 2.0, 20.0, base=True, jitter=0.0, top_jitter=0.0)
        out["ceil"] = c
    return out


# ------------------------------------------------------------------------------------------------ tunnels
def vault_corridor(length, width, wall_h, rise, seed=1, ribs_every=330.0, slab=40.0, floor_slab=40.0, openings_n=(), openings_s=()):
    """A stone corridor along +x from 0 to length. Floor top at z = 0, straight side walls to wall_h, a segmental barrel vault above rising
    `rise` more. The structure has an outside shell of `slab` thickness. Returns dict(floor, walls, vault, ribs) as separate meshes."""
    rng = random.Random(seed)
    hw = width / 2.0
    floor = Mesh()
    floor.box(length / 2.0, 0, -floor_slab, length, width + 2 * slab, floor_slab, base=True, jitter=0.0)
    walls = Mesh()
    for sgn in (-1, 1):
        ops = openings_n if sgn > 0 else openings_s
        wm = wall(length, wall_h, slab, ops, seed=seed + sgn, base_z=-floor_slab, jitter=0.0)
        if sgn > 0:
            walls.append(xform(wm, yaw=180.0, offset=(length, hw + slab, 0.0)))
        else:
            walls.append(xform(wm, yaw=0.0, offset=(0.0, -hw - slab, 0.0)))
    vault = Mesh()
    N = 8
    R = (hw * hw + rise * rise) / (2.0 * rise)          # circle through the spring points (+-hw, wall_h) and the crown (0, wall_h + rise)
    zc = wall_h + rise - R
    prev = (-hw, wall_h)
    for k in range(1, N + 1):
        a = -hw + 2.0 * hw * k / N
        cur = (a, zc + math.sqrt(max(0.0, R * R - a * a)))
        # slab between prev and cur: thickness `slab` outwards
        mid = ((prev[0] + cur[0]) / 2.0, (prev[1] + cur[1]) / 2.0)
        ang = math.degrees(math.atan2(cur[1] - prev[1], cur[0] - prev[0]))
        seg = math.hypot(cur[0] - prev[0], cur[1] - prev[1])
        nx_, nz_ = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
        vault.box(length / 2.0, mid[0] + nx_ * slab / 2.0, mid[1] + nz_ * slab / 2.0 - slab / 2.0 * 0.0, length, seg + 1.5, slab, roll=ang, jitter=0.0, seed=k)
        prev = cur
    ribs = Mesh()
    n_r = max(1, int(length // ribs_every))
    for i in range(n_r + 1):
        x = i * length / n_r
        pts = []
        for k in range(N + 1):
            a = -hw + 2.0 * hw * k / N
            pts.append((a, zc + math.sqrt(max(0.0, R * R - a * a))))
        # arch rib: small boxes along the vault curve, protruding 12 cm below it
        for k in range(N):
            p0, p1 = pts[k], pts[k + 1]
            mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
            ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
            seg = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            nx_, nz_ = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
            ribs.box(x, mid[0] - nx_ * 7.0, mid[1] - nz_ * 7.0, 34.0, seg + 1.0, 14.0, roll=ang, jitter=0.0, seed=k + i)
        for sgn in (-1, 1):
            ribs.box(x, sgn * (hw - 9.0), 0, 36.0, 18.0, wall_h, base=True, jitter=0.0)
    return dict(floor=floor, walls=walls, vault=vault, ribs=ribs)


# ------------------------------------------------------------------------------------------------ terrain
def terrain_tile(x0, y0, x1, y1, cell, G, slot_fn, holes=()):
    """Ground mesh for the rectangle, one Mesh per material slot {slot: Mesh}. Normals come from the height function itself, so tiles
    meet without a shading seam. holes: rectangles (x0, y0, x1, y1) whose cells are left out."""
    nx = int(round((x1 - x0) / cell))
    ny = int(round((y1 - y0) / cell))
    Z = {}
    for i in range(-1, nx + 2):
        for j in range(-1, ny + 2):
            Z[(i, j)] = G(x0 + i * cell, y0 + j * cell)

    def vert(i, j):
        dzx = (Z[(i + 1, j)] - Z[(i - 1, j)]) / (2.0 * cell)
        dzy = (Z[(i, j + 1)] - Z[(i, j - 1)]) / (2.0 * cell)
        n = norm((-dzx, -dzy, 1.0))
        return (x0 + i * cell, y0 + j * cell, Z[(i, j)]), n
    cache = {}

    def V(i, j):
        v = cache.get((i, j))
        if v is None:
            v = cache[(i, j)] = vert(i, j)
        return v
    out = {}
    for i in range(nx):
        for j in range(ny):
            cx, cy = x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell
            if any(h[0] <= cx <= h[2] and h[1] <= cy <= h[3] for h in holes):
                continue
            za, zb, zc, zd = Z[(i, j)], Z[(i + 1, j)], Z[(i + 1, j + 1)], Z[(i, j + 1)]
            if abs(za - zc) <= abs(zb - zd):
                tris = [((i, j), (i + 1, j), (i + 1, j + 1)), ((i, j), (i + 1, j + 1), (i, j + 1))]
            else:
                tris = [((i, j), (i + 1, j), (i, j + 1)), ((i + 1, j), (i + 1, j + 1), (i, j + 1))]
            for t in tris:
                p = [V(*q) for q in t]
                n = cross(sub(p[1][0], p[0][0]), sub(p[2][0], p[0][0]))
                n = norm(n)
                zc_ = (p[0][0][2] + p[1][0][2] + p[2][0][2]) / 3.0
                xc_ = (p[0][0][0] + p[1][0][0] + p[2][0][0]) / 3.0
                yc_ = (p[0][0][1] + p[1][0][1] + p[2][0][1]) / 3.0
                slot = slot_fn(n[2], zc_, xc_, yc_)
                m = out.get(slot)
                if m is None:
                    m = out[slot] = Mesh()
                b = len(m.verts)
                for q in p:
                    m.verts.append(q[0])
                    m.norms.append(q[1])
                m.tris.append((b, b + 1, b + 2))
    return out


def ribbon(points, width_fn, G, lift=5.0, edge=-5.0, cross_n=5, step=70.0, wobble=0.18, seed=1, closed_ends=True, z_add=0.0):
    """A strip that follows the ground along a polyline [(x, y)...]: lift at the middle, `edge` (below the ground) at the borders, so the
    visible outline is where it meets the ground, irregular thanks to `wobble`. width_fn(s) with s = distance along the path (cm)."""
    res = [points[0]]
    for a, b in zip(points[:-1], points[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d // step))
        for k in range(1, n + 1):
            f = k / float(n)
            res.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    m = Mesh()
    nn_ = len(res)
    s_acc = 0.0
    rows = []
    for i, p in enumerate(res):
        if i:
            s_acc += math.hypot(p[0] - res[i - 1][0], p[1] - res[i - 1][1])
        a = res[max(i - 1, 0)]
        b = res[min(i + 1, nn_ - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1.0
        tx, ty = tx / l, ty / l
        px, py = -ty, tx
        w = width_fn(s_acc) * (1.0 + wobble * fbm(s_acc / 260.0, seed * 3.1, 0.0, 2, seed))
        row = []
        for k in range(cross_n):
            t = (k / float(cross_n - 1)) * 2.0 - 1.0
            x, y = p[0] + px * t * w / 2.0, p[1] + py * t * w / 2.0
            e = abs(t)
            e2 = e * e * e
            if closed_ends and (i == 0 or i == nn_ - 1):
                e2 = 1.0
            z = G(x, y) + lift + (edge - lift) * (e2 if k not in (0, cross_n - 1) else 1.0) + z_add
            row.append((x, y, z))
        rows.append(row)

    def pt(i, k):
        return rows[i][k]
    base = 0
    for i in range(nn_):
        for k in range(cross_n):
            i0, i1 = max(i - 1, 0), min(i + 1, nn_ - 1)
            k0, k1 = max(k - 1, 0), min(k + 1, cross_n - 1)
            du = sub(rows[i1][k], rows[i0][k])
            dv = sub(rows[i][k1], rows[i][k0])
            n = norm(cross(du, dv))
            if n[2] < 0.0:
                n = (-n[0], -n[1], -n[2])
            m.verts.append(rows[i][k])
            m.norms.append(n)
    idx = lambda i, k: i * cross_n + k
    for i in range(nn_ - 1):
        for k in range(cross_n - 1):
            a, b, c, d = idx(i, k), idx(i + 1, k), idx(i + 1, k + 1), idx(i, k + 1)
            # make the winding face up
            va, vb, vc = m.verts[a], m.verts[b], m.verts[c]
            nz = cross(sub(vb, va), sub(vc, va))[2]
            if nz >= 0:
                m.tris.append((a, b, c))
                m.tris.append((a, c, d))
            else:
                m.tris.append((a, c, b))
                m.tris.append((a, d, c))
    return m


def patch(cx, cy, rx, ry, G, seed=1, cell=60.0, lift=5.0, under=-5.0, wobble=0.55, yaw=0.0):
    """An organic ground overlay (dirt, moss, gravel) following the terrain: a heightfield above the ground whose outline is where it dips below it."""
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    ext = max(rx, ry) * 1.15
    nx = max(3, int(2 * ext / cell) + 1)
    m = Mesh()
    zs = {}

    def height(i, j):
        key = (i, j)
        v = zs.get(key)
        if v is None:
            lx, ly = -ext + 2 * ext * i / (nx - 1), -ext + 2 * ext * j / (nx - 1)
            wx, wy = cx + lx * ca - ly * sa, cy + lx * sa + ly * ca
            r = math.hypot(lx / rx, ly / ry)
            n = fbm(lx / 130.0 + seed, ly / 130.0, 0.0, 3, seed)
            e = 1.0 - r + wobble * n
            top = under + (lift - under) * smoothstep(0.0, 0.45, e)
            v = zs[key] = (wx, wy, G(wx, wy) + top, e)
        return v
    for i in range(nx):
        for j in range(nx):
            v = height(i, j)
            m.verts.append((v[0], v[1], v[2]))
            i0, i1, j0, j1 = max(i - 1, 0), min(i + 1, nx - 1), max(j - 1, 0), min(j + 1, nx - 1)
            a, b = height(i1, j), height(i0, j)
            c, d = height(i, j1), height(i, j0)
            nrm = norm(cross(sub((a[0], a[1], a[2]), (b[0], b[1], b[2])), sub((c[0], c[1], c[2]), (d[0], d[1], d[2]))))
            if nrm[2] < 0:
                nrm = (-nrm[0], -nrm[1], -nrm[2])
            m.norms.append(nrm)
    for i in range(nx - 1):
        for j in range(nx - 1):
            es = [height(i, j)[3], height(i + 1, j)[3], height(i + 1, j + 1)[3], height(i, j + 1)[3]]
            if max(es) <= 0.0:
                continue                      # entirely under the ground: skip
            a, b, c, d = i * nx + j, (i + 1) * nx + j, (i + 1) * nx + j + 1, i * nx + j + 1
            va, vb, vc = m.verts[a], m.verts[b], m.verts[c]
            if cross(sub(vb, va), sub(vc, va))[2] >= 0:
                m.tris.append((a, b, c))
                m.tris.append((a, c, d))
            else:
                m.tris.append((a, c, b))
                m.tris.append((a, d, c))
    return m
