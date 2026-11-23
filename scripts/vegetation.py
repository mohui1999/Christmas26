"""Stylised winter vegetation: detailed conifers, shrubs, bare trees."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from lib import (empty, box, cylinder, cone, sphere, ico, join, curve_tube,
                 mesh_obj, metal, gloss, snowmat, plaster, emission, fabric, PI, TAU,
                 RNG, lin, parent_all)

SNOW = snowmat()


# --------------------------------------------------------------------------- #
# shared materials
# --------------------------------------------------------------------------- #
def needle_material():
    m = bpy.data.materials.get('needles')
    if m:
        return m
    m = bpy.data.materials.new('needles')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (420, 0)
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.location = (-700, 160)
    attr.attribute_name = 'Col'
    nt.links.new(attr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.62
    b.inputs['Sheen Weight'].default_value = 0.35
    b.inputs['Sheen Tint'].default_value = lin('#dfe8ff')
    # snow dusting on upward facing needles
    geo = nt.nodes.new('ShaderNodeNewGeometry'); geo.location = (-900, -160)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-700, -160)
    nt.links.new(geo.outputs['Normal'], sep.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.location = (-500, -160)
    mr.inputs['From Min'].default_value = 0.15
    mr.inputs['From Max'].default_value = 0.85
    mr.inputs['To Min'].default_value = 0.0
    mr.inputs['To Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    n = nt.nodes.new('ShaderNodeTexNoise'); n.location = (-700, -380)
    n.inputs['Scale'].default_value = 9.0
    n.inputs['Detail'].default_value = 5.0
    n.inputs['Roughness'].default_value = 0.6
    nt.links.new(geo.outputs['Position'], n.inputs['Vector'])
    mr2 = nt.nodes.new('ShaderNodeMapRange'); mr2.location = (-480, -380)
    mr2.inputs['From Min'].default_value = 0.48
    mr2.inputs['From Max'].default_value = 0.72
    mr2.inputs['To Min'].default_value = 0.0
    mr2.inputs['To Max'].default_value = 1.0
    nt.links.new(n.outputs['Fac'], mr2.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.location = (-280, -260)
    nt.links.new(mr.outputs['Result'], mul.inputs[0])
    nt.links.new(mr2.outputs['Result'], mul.inputs[1])
    powr = nt.nodes.new('ShaderNodeMath'); powr.operation = 'POWER'; powr.location = (-120, -260)
    powr.inputs[1].default_value = 1.4
    nt.links.new(mul.outputs[0], powr.inputs[0])
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.location = (140, 40)
    mix.blend_type = 'MIX'
    nt.links.new(powr.outputs[0], mix.inputs[0])
    nt.links.new(attr.outputs['Color'], mix.inputs[1])
    mix.inputs[2].default_value = lin('#e8f0fb')
    nt.links.new(mix.outputs['Color'], b.inputs['Base Color'])
    return m


def bark_material(name='bark', hexcol='#4a3526'):
    key = 'bark_' + name
    m = bpy.data.materials.get(key)
    if m:
        return m
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (600, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (350, 0)
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    tc = nt.nodes.new('ShaderNodeTexCoord'); tc.location = (-700, 0)
    n = nt.nodes.new('ShaderNodeTexNoise'); n.location = (-500, 80)
    n.inputs['Scale'].default_value = 12.0
    n.inputs['Detail'].default_value = 6.0
    n.inputs['Distortion'].default_value = 2.5
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-260, 120)
    ramp.color_ramp.elements[0].color = lin('#2c1f16')
    ramp.color_ramp.elements[1].color = lin(hexcol)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    bump = nt.nodes.new('ShaderNodeBump'); bump.location = (100, -180)
    bump.inputs['Strength'].default_value = 0.6
    nt.links.new(n.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
# mesh accumulation helpers
# --------------------------------------------------------------------------- #
def _tube(V, F, points, radii, sides=4, close=False):
    """Append a low poly tube along points into V/F."""
    base = len(V)
    n = len(points)
    for i, p in enumerate(points):
        p = Vector(p)
        if i < n - 1:
            d = (Vector(points[i + 1]) - p)
        else:
            d = (p - Vector(points[i - 1]))
        if d.length < 1e-6:
            d = Vector((0, 0, 1))
        d.normalize()
        up = Vector((0, 0, 1))
        if abs(d.dot(up)) > 0.95:
            up = Vector((0, 1, 0))
        u = d.cross(up).normalized()
        v = d.cross(u).normalized()
        for k in range(sides):
            a = k / sides * TAU
            V.append(p + u * (math.cos(a) * radii[i]) + v * (math.sin(a) * radii[i]))
    for i in range(n - 1):
        for k in range(sides):
            a = base + i * sides + k
            b = base + i * sides + (k + 1) % sides
            c = base + (i + 1) * sides + (k + 1) % sides
            d = base + (i + 1) * sides + k
            F.append((a, b, c, d))


def _sprig_template(seed=1, length=0.55):
    """A tuft of needles in local space: stem along +X."""
    rng = random.Random(seed)
    V, F, C = [], [], []

    def needle(base, direction, length, width, thick, col):
        d = Vector(direction).normalized()
        up = Vector((0, 0, 1))
        if abs(d.dot(up)) > 0.95:
            up = Vector((0, 1, 0))
        u = d.cross(up).normalized()
        v = d.cross(u).normalized()
        b = Vector(base)
        idx = len(V)
        V.extend([b + u * (width * 0.5) + v * (thick * 0.5),
                  b - u * (width * 0.5) + v * (thick * 0.5),
                  b - u * (width * 0.5) - v * (thick * 0.5),
                  b + u * (width * 0.5) - v * (thick * 0.5),
                  b + d * length])
        F.extend([(idx, idx + 1, idx + 4), (idx + 1, idx + 2, idx + 4),
                  (idx + 2, idx + 3, idx + 4), (idx + 3, idx, idx + 4)])
        C.extend([col] * 5)

    # stem
    stem_pts = [(0, 0, 0), (length * 0.28, 0, 0.01), (length * 0.58, 0, 0.02), (length * 0.8, 0, 0.015)]
    tb = len(V)
    for p in stem_pts:
        V.append(p)
    for i in range(len(stem_pts) - 1):
        pass
    # needles along the stem
    n_st = 9
    for i in range(n_st):
        t = 0.12 + 0.82 * i / (n_st - 1)
        x = length * t
        spread = 0.7 + 0.35 * math.sin(t * PI)
        for side in (-1, 1):
            for updown in (1, -1):
                ang = rng.uniform(-0.25, 0.25)
                d = Vector((0.55 + 0.3 * rng.random(),
                            side * (0.45 + 0.35 * rng.random()) * spread,
                            updown * (0.18 + 0.38 * rng.random())))
                if updown > 0 and rng.random() < 0.35:
                    d.z += 0.35
                col = (0.12 + rng.uniform(-0.03, 0.04),
                       0.26 + rng.uniform(-0.06, 0.08),
                       0.16 + rng.uniform(-0.04, 0.05), 1)
                needle((x, 0, 0.01 * t), d, length * rng.uniform(0.18, 0.30),
                       length * 0.032, length * 0.011, col)
    return V, F, C


def _accumulate_sprigs(placements, seed=1, length=0.55):
    tv, tf, tc = _sprig_template(seed, length)
    V, F, C = [], [], []
    for M, sc in placements:
        base = len(V)
        for v in tv:
            V.append(M @ (Vector(v) * sc))
        for c in tc:
            C.append(c)
        for f in tf:
            F.append(tuple(i + base for i in f))
    me = bpy.data.meshes.new('needle_mesh')
    me.from_pydata(V, [], F)
    me.update()
    col = me.color_attributes.new(name='Col', type='FLOAT_COLOR', domain='POINT')
    for i, c in enumerate(C):
        col.data[i].color = c
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new('needles', me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(needle_material())
    return ob


# --------------------------------------------------------------------------- #
# conifer
# --------------------------------------------------------------------------- #
def conifer(name, loc=(0, 0, 0), height=7.0, radius=2.2, yaw=0.0, seed=1,
            detail=0.75, sprig_len=0.55, tint=None, snow=True):
    rng = random.Random(seed)
    e = empty(name, loc, (0, 0, yaw))
    Vb, Fb = [], []

    z0 = height * 0.06
    ztop = height * 0.97
    # trunk
    tps = []
    for i in range(7):
        t = i / 6
        z = z0 + (ztop - z0) * t
        tps.append((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), z))
    _tube(Vb, Fb, tps, [0.09 + radius * 0.032 * (1 - i / 6) ** 1.4 for i in range(7)], sides=6)
    # root flare
    _tube(Vb, Fb, [(0, 0, -0.1), (0, 0, 0.18), (0, 0, 0.55)],
          [radius * 0.075, radius * 0.06, radius * 0.045], sides=7)

    sprigs = []
    whorl_count = max(9, int(height / 0.34))
    for wi in range(whorl_count):
        t = wi / (whorl_count - 1)
        z = z0 + (ztop - z0) * t
        if wi >= whorl_count - 2:
            n_branch = 6
        else:
            n_branch = rng.randint(9, 12)
        Lbase = radius * (1 - t) ** 0.82 + 0.22
        Lbase *= rng.uniform(0.9, 1.08)
        phase = wi * 0.7 + rng.uniform(-0.3, 0.3)
        for bi in range(n_branch):
            a = phase + bi / n_branch * TAU + rng.uniform(-0.15, 0.15)
            L = Lbase * rng.uniform(0.82, 1.1)
            droop = (0.55 + 0.55 * (1 - t)) * (0.8 + rng.uniform(-0.2, 0.3))
            rad = Vector((math.cos(a), math.sin(a), 0))
            n_seg = 5
            pts = []
            droopf = 0.8 + 0.4 * rng.random()
            for s in range(n_seg):
                u = s / (n_seg - 1)
                p = rad * (0.12 + L * u)
                p.z = z + 0.16 * math.sin(u * PI) - droop * u * u * droopf
                pts.append(p)
            _tube(Vb, Fb, pts, [max(0.006, 0.032 * (1 - s / n_seg)) for s in range(n_seg)], sides=4)
            # sprig placements along branch
            n_sp = max(4, int(L / (0.15 if detail > 0.6 else 0.22)))
            for si in range(n_sp):
                u = 0.10 + 0.90 * (si / max(1, n_sp - 1))
                idx = min(n_seg - 1, int(u * (n_seg - 1)))
                f = u * (n_seg - 1) - idx
                p = Vector(pts[idx]).lerp(Vector(pts[min(idx + 1, n_seg - 1)]), f)
                if idx >= n_seg - 1:
                    tangent = (Vector(pts[n_seg - 1]) - Vector(pts[n_seg - 2])).normalized()
                else:
                    tangent = (Vector(pts[idx + 1]) - Vector(pts[idx])).normalized()
                if tangent.length < 1e-5:
                    tangent = rad
                roll = rng.uniform(0, TAU)
                # build frame with X along tangent
                x = tangent
                up = Vector((0, 0, 1))
                if abs(x.dot(up)) > 0.97:
                    up = Vector((0, 1, 0))
                y = x.cross(up).normalized()
                zax = x.cross(y).normalized()
                # roll around x
                y2 = y * math.cos(roll) + zax * math.sin(roll)
                z2 = x.cross(y2).normalized()
                M = Matrix((x, y2, z2)).transposed().to_4x4()
                M.translation = p + Vector((0, 0, rng.uniform(-0.02, 0.04)))
                sprigs.append((M, rng.uniform(0.6, 0.95) * (0.8 + 0.25 * (1 - t))))
            # secondary twigs
            if t < 0.9 and L > 0.55:
                for k in range(3):
                    u0 = rng.uniform(0.45, 0.8)
                    idx = min(n_seg - 1, int(u0 * (n_seg - 1)))
                    base = Vector(pts[idx])
                    side = Vector((-math.sin(a), math.cos(a), 0)) * rng.choice((-1, 1))
                    pts2 = [base]
                    for s in range(1, 4):
                        v = s / 3
                        p = base + rad * (L * 0.34 * v) + side * (L * 0.22 * v)
                        p.z -= (0.15 + 0.4 * v) * v
                        pts2.append(p)
                    _tube(Vb, Fb, pts2, [0.014, 0.011, 0.008, 0.005], sides=4)
                    for s in range(3):
                        v = 0.3 + 0.3 * s
                        p = Vector(pts2[1]).lerp(Vector(pts2[3]), v)
                        tang = (Vector(pts2[3]) - Vector(pts2[1])).normalized()
                        x = tang
                        up = Vector((0, 0, 1))
                        y = x.cross(up).normalized()
                        zax = x.cross(y).normalized()
                        M = Matrix((x, y, zax)).transposed().to_4x4()
                        M.translation = p
                        sprigs.append((M, rng.uniform(0.5, 0.8) * (0.75 + 0.25 * (1 - t))))

    bark = bark_material('bark', '#4b3627')
    if Vb:
        me = bpy.data.meshes.new(name + '_branches')
        me.from_pydata(Vb, [], Fb)
        me.update()
        ob = bpy.data.objects.new(name + '_branches', me)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(bark)
        ob.parent = e
        for p in me.polygons:
            p.use_smooth = True
    fol = _accumulate_sprigs(sprigs, seed=seed, length=sprig_len)
    fol.name = name + '_needles'
    fol.parent = e
    # snow clumps
    if snow:
        sn = []
        for i in range(min(180, len(sprigs) // 30)):
            M, sc = sprigs[rng.randrange(len(sprigs))]
            p = M.translation + Vector((rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0.1))
            sn.append(ico(name + '_snow', rng.uniform(0.09, 0.2), p, SNOW, 1,
                          (1.4, 1.1, 0.35), jitter=0.3))
        if sn:
            parent_all(sn, e)
            s = join(sn, name + '_snowcap')
            s.parent = e
    return e


def big_christmas_tree(loc=(0, 0, 0), height=10.6, radius=3.4):
    """The hero tree with ornaments, fairy lights and a star."""
    rng = random.Random(991)
    e = conifer('giant_tree_body', (0, 0, 0), height, radius, seed=77, detail=1.0,
                sprig_len=0.62)
    e.name = 'giant_tree'
    e.location = loc

    # fairy lights: spiral
    def surf_r(z):
        t = max(0.0, min(1.0, (z - height * 0.06) / (height * 0.91)))
        return radius * (1 - t) ** 0.82 + 0.25

    bulb_mat = emission('fairy_bulb', '#ffb45c', 6.5)
    bulbs = []
    n_bulbs = 640
    for i in range(n_bulbs):
        t = i / (n_bulbs - 1)
        z = 1.1 + t * (height - 1.5)
        a = t * TAU * 11.5 + 0.4
        r = surf_r(z) * rng.uniform(0.84, 1.0)
        p = (math.cos(a) * r, math.sin(a) * r, z + rng.uniform(-0.12, 0.12))
        b = sphere('treebulb', rng.uniform(0.021, 0.03), p, bulb_mat, 6, 4)
        b.parent = e
        bulbs.append(b)
    for i in range(130):
        z = rng.uniform(1.2, height - 0.6)
        a = rng.uniform(0, TAU)
        r = surf_r(z) * rng.uniform(0.75, 0.98)
        b = sphere('treebulb', rng.uniform(0.02, 0.028),
                   (math.cos(a) * r, math.sin(a) * r, z), bulb_mat, 6, 4)
        b.parent = e
        bulbs.append(b)
    ob = join(bulbs, 'tree_bulbs')
    ob.parent = e

    # ornaments
    red = gloss('orn_red', '#9d1420', 0.12, 0.35, 0.8)
    gold = metal('orn_gold', '#e3ac55', 0.16)
    silver = metal('orn_silver', '#c9d2da', 0.14)
    pearl = gloss('orn_pearl', '#f1e6d2', 0.24, 0.0, 0.9)
    blue = gloss('orn_blue', '#2a4f78', 0.1, 0.3, 0.9)
    orn_mats = [red, gold, silver, pearl, blue]
    orns = []
    for i in range(260):
        z = rng.uniform(1.4, height - 0.8)
        a = rng.uniform(0, TAU)
        r = surf_r(z) * rng.uniform(0.82, 1.0)
        p = (math.cos(a) * r, math.sin(a) * r, z - 0.12)
        rr = rng.choice([0.07, 0.08, 0.09, 0.1, 0.12, 0.14])
        s = sphere('orn', rr, p, rng.choice(orn_mats), 14, 10)
        s.parent = e
        orns.append(s)
        # hook
        h = cylinder('hook', 0.006, 0.1, (p[0], p[1], p[2] + rr + 0.04), metal('hook_m', '#6b5d48', 0.4), 5)
        h.parent = e
    # large feature baubles
    for i in range(14):
        z = rng.uniform(2.5, height - 2.0)
        a = rng.uniform(0, TAU)
        r = surf_r(z) * 0.98
        p = (math.cos(a) * r, math.sin(a) * r, z)
        s = sphere('big_orn', rng.uniform(0.16, 0.23), p, rng.choice([red, gold, blue]), 18, 12)
        s.parent = e

    # red velvet ribbon spiralling through the branches
    ribbon = fabric('tree_ribbon', '#8f1522', 0.45, 0.5)
    pts = []
    for i in range(120):
        t = i / 119
        z = 1.35 + t * (height - 2.2)
        a = t * TAU * 7.0 + 1.1
        r = surf_r(z) * rng.uniform(0.97, 1.02)
        pts.append((math.cos(a) * r, math.sin(a) * r, z))
    curve_tube('tree_ribbon', pts, 0.032, ribbon, parent=e)
    # bows at intervals
    for i in range(12):
        t = (i + 0.5) / 12
        z = 1.5 + t * (height - 2.6)
        a = t * TAU * 7.0 + 1.1
        r = surf_r(z) * 1.02
        p = (math.cos(a) * r, math.sin(a) * r, z)
        for side in (-1, 1):
            b = sphere('bowloop', 0.16, (p[0] + side * 0.12, p[1], p[2] + 0.03),
                       ribbon, 12, 8, (1.3, 0.5, 0.7))
            b.parent = e
        k = sphere('bowknot', 0.07, p, ribbon, 10, 8)
        k.parent = e
        for side in (-1, 1):
            tail = box('bowtail', 0.06, 0.02, 0.28, (p[0] + side * 0.06, p[1], p[2] - 0.15),
                       ribbon, 0.0, rot=(0.2, side * 0.2, 0))
            tail.parent = e
    # gold bead garland
    gold_beads = []
    for i in range(150):
        t = i / 149
        z = 1.3 + t * (height - 1.8)
        a = t * TAU * 9.0 + 2.3
        r = surf_r(z) * 0.99
        b = sphere('goldbead', 0.035, (math.cos(a) * r, math.sin(a) * r, z), gold, 8, 6)
        b.parent = e
        gold_beads.append(b)
    join(gold_beads, 'gold_chain').parent = e

    # star
    starm = metal('star_gold', '#f0c070', 0.18)
    sb = starm.node_tree.nodes['Principled BSDF']
    sb.inputs['Emission Color'].default_value = lin('#ffd27a')
    sb.inputs['Emission Strength'].default_value = 0.75
    star = make_star((0, 0, height + 0.72), 1.3, starm)
    star.parent = e
    # star glow light
    ld = bpy.data.lights.new('star_light', 'POINT')
    ld.energy = 90
    ld.color = (1.0, 0.72, 0.4)
    ld.shadow_soft_size = 0.4
    lo = bpy.data.objects.new('star_light', ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (0, 0, height + 0.3)
    lo.parent = e

    # warm light inside the foliage
    for i, (z, en) in enumerate([(3.0, 120), (6.2, 100), (9.4, 80)]):
        ld = bpy.data.lights.new('tree_glow%d' % i, 'POINT')
        ld.energy = en
        ld.color = (1.0, 0.58, 0.26)
        ld.shadow_soft_size = 1.8
        lo = bpy.data.objects.new('tree_glow%d' % i, ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = (0, 0, z)
        lo.parent = e
    # practical lights outside the foliage so the branches glow
    for i in range(3):
        a = i / 3 * TAU + 0.4
        ld = bpy.data.lights.new('tree_rim%d' % i, 'POINT')
        ld.energy = 450
        ld.color = (1.0, 0.62, 0.3)
        ld.shadow_soft_size = 1.4
        lo = bpy.data.objects.new('tree_rim%d' % i, ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = (math.cos(a) * 4.3, math.sin(a) * 4.3, 4.6 if i != 1 else 8.2)
        lo.parent = e
    # warm front fill so the front needles catch the light
    for (lx, ly, lz, en) in [(0, -4.8, 5.6, 300), (0, 0.5, 12.2, 200)]:
        ld = bpy.data.lights.new('tree_front', 'POINT')
        ld.energy = en; ld.color = (1.0, 0.6, 0.28); ld.shadow_soft_size = 2.2
        lo = bpy.data.objects.new('tree_front', ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = (lx, ly, lz)
        lo.parent = e

    return e


def make_star(loc, size, mat):
    """Flat extruded 5 point star facing -Y."""
    pts = []
    for i in range(10):
        a = PI / 2 + i * PI / 5
        r = size if i % 2 == 0 else size * 0.42
        pts.append((math.cos(a) * r, math.sin(a) * r))
    V, F = [], []
    d = 0.09
    n = len(pts)
    for y in (-d, d):
        for (x, z) in pts:
            V.append((x, y, z))
    for i in range(1, n - 1):
        F.append((0, i + 1, i))
        F.append((n, n + i, n + i + 1))
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    ob = mesh_obj('star', V, F, mat, loc=loc, bevel=0.0)
    mod = ob.modifiers.new('bev', 'BEVEL'); mod.width = 0.02; mod.segments = 2
    return ob


def deciduous(name, loc, height=6.0, seed=3):
    rng = random.Random(seed)
    e = empty(name, loc)
    V, F = [], []
    bark = bark_material('bark_bare', '#3e332b')

    def branch(p, d, length, thick, depth):
        seg = 5
        pts = [p]
        cur = Vector(p)
        dd = Vector(d).normalized()
        for i in range(seg):
            step = length / seg
            dd = (dd + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.12))).normalized()
            cur = cur + dd * step
            pts.append(cur.copy())
        _tube(V, F, pts, [thick * (1 - i / len(pts)) ** 0.8 for i in range(len(pts))], sides=4)
        if depth > 0:
            for k in range(2 if depth == 2 else 3):
                nd = (dd + Vector((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), rng.uniform(-0.2, 0.5)))).normalized()
                branch(cur, nd, length * rng.uniform(0.45, 0.65), thick * 0.55, depth - 1)

    branch((0, 0, 0), (0, 0, 1), height * 0.42, 0.16, 3)
    me = bpy.data.meshes.new(name + '_mesh')
    me.from_pydata(V, [], F); me.update()
    ob = bpy.data.objects.new(name + '_mesh', me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(bark)
    ob.parent = e
    for p in me.polygons:
        p.use_smooth = True
    # snow lines on the upper branches
    return e


def shrub(name, loc, r=0.5, seed=5):
    rng = random.Random(seed)
    e = empty(name, loc)
    green = plaster('shrub_green', '#2a3f2c', 0.9, 0.3)
    for i in range(4):
        p = (rng.uniform(-0.25, 0.25) * r, rng.uniform(-0.25, 0.25) * r, r * 0.4)
        ob = ico('shrub', r * rng.uniform(0.55, 0.8), p, green, 2,
                 (1.0, 1.0, 0.8), jitter=0.22)
        ob.parent = e
    ico('shrub_snow', r * 0.9, (0, 0, r * 0.8), SNOW, 2, (1.1, 1.0, 0.3),
        parent=e, jitter=0.3)
    return e
