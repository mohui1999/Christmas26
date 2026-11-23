"""Build the dreamy Christmas town and render a hero shot."""
import bpy, bmesh, math, os, sys, random, time
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from lib import (box, cylinder, cone, sphere, ico, empty, join, curve_tube,
                 mesh_obj, plaster, stone, wood, roofmat, metal, gloss, fabric,
                 emission, snowmat, tile, text_obj, gable_roof, PI, TAU, RNG,
                 lin, parent_all)

PREVIEW = '--preview' in sys.argv
DRAFT = '--draft' in sys.argv
if DRAFT:
    RES_X, RES_Y, SAMPLES = 640, 400, 12
elif PREVIEW:
    RES_X, RES_Y, SAMPLES = 900, 560, 24
else:
    RES_X, RES_Y, SAMPLES = 1920, 1200, 80


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.015
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 6
    sc.cycles.volume_bounces = 2
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.sample_clamp_indirect = 4.0
    sc.render.resolution_x = RES_X
    sc.render.resolution_y = RES_Y
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = 0.85
    return sc


def world(sc):
    w = bpy.data.worlds.new('ChristmasSky')
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); out.location = (700, 0)
    mix = nt.nodes.new('ShaderNodeMixShader'); mix.location = (500, 0)
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    # visible sky (camera rays only)
    bg_sky = nt.nodes.new('ShaderNodeBackground'); bg_sky.location = (300, 120)
    bg_sky.inputs['Strength'].default_value = 1.25
    # dim ambient for lighting
    bg_amb = nt.nodes.new('ShaderNodeBackground'); bg_amb.location = (300, -140)
    bg_amb.inputs['Strength'].default_value = 0.22
    bg_amb.inputs['Color'].default_value = lin('#243451')
    lp = nt.nodes.new('ShaderNodeLightPath'); lp.location = (100, 260)
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    nt.links.new(bg_amb.outputs[0], mix.inputs[1])
    nt.links.new(bg_sky.outputs[0], mix.inputs[2])
    tc = nt.nodes.new('ShaderNodeTexCoord'); tc.location = (-900, 0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-700, 0)
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-450, 0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = lin('#070c16')
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = lin('#16233a')
    e = ramp.color_ramp.elements.new(0.6)
    e.color = lin('#2a3d5c')
    e2 = ramp.color_ramp.elements.new(0.5)
    e2.color = lin('#7586a2')
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg_sky.inputs['Color'])
    sc.world = w
    return w


def base_and_plaza():
    # stone plinth / diorama base
    base = cylinder('diorama_base', 25.4, 1.6, (0, 0, -0.8), stone('base_rock', '#4b4a45', 0.75), 96)
    for p in base.data.polygons:
        p.use_smooth = True
    rim = cylinder('diorama_rim', 25.55, 0.32, (0, 0, 0.12), stone('base_rim', '#77705f', 0.62), 96)
    # snow cap of the base ring, with a gentle wave
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=120, radius=25.45)
    for v in bm.verts:
        r = math.hypot(v.co.x, v.co.y)
        if r > 24:
            v.co.z = 0.22 + 0.04 * math.sin(math.atan2(v.co.y, v.co.x) * 7)
        else:
            v.co.z = 0.28
    me = bpy.data.meshes.new('ground_snow')
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('ground_snow', me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(snowmat())
    # continuous snow cornice around the rim
    n = 140
    rows = [(23.1, 0.30), (23.9, 0.33), (24.7, 0.33), (25.28, 0.26)]
    V = []
    for (rr, zz) in rows:
        for i in range(n):
            a = i / n * TAU
            z = zz + 0.035 * math.sin(a * 5.0 + 0.7) + 0.022 * math.sin(a * 11.0)
            V.append((math.cos(a) * rr, math.sin(a) * rr, z))
    F = []
    for jrow in range(len(rows) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            a = jrow * n + i; b = jrow * n + i2
            c = (jrow + 1) * n + i2; d = (jrow + 1) * n + i
            F.append((a, b, c, d))
    # hanging outer lip
    base_i = len(V)
    for i in range(n):
        a = i / n * TAU
        V.append((math.cos(a) * 25.32, math.sin(a) * 25.32, 0.09 + 0.03 * math.sin(a * 9)))
    for i in range(n):
        i2 = (i + 1) % n
        F.append(((len(rows) - 1) * n + i, (len(rows) - 1) * n + i2,
                  base_i + i2, base_i + i))
    me2 = bpy.data.meshes.new('rim_snow')
    me2.from_pydata(V, [], F); me2.update()
    obs = bpy.data.objects.new('rim_snow', me2)
    bpy.context.scene.collection.objects.link(obs)
    me2.materials.append(snowmat())
    # larger drifts on the snow ring
    drifts = []
    for i in range(34):
        a = RNG.uniform(0, TAU)
        r = RNG.uniform(21.2, 24.7)
        drifts.append(ico('drift', RNG.uniform(0.45, 1.1), (math.cos(a) * r, math.sin(a) * r, 0.34),
                          snowmat(), 2, (1.3, 0.9, 0.24), jitter=0.28))
    j = join(drifts, 'rim_drifts')
    # paving tiles
    mats = [tile('pave1', '#b7ab97', 0.42), tile('pave2', '#a89d8b', 0.38),
            tile('pave3', '#c6b9a3', 0.46), tile('pave4', '#9b9182', 0.4),
            tile('pave5', '#b0a48f', 0.36), tile('pave6', '#8d8478', 0.44)]
    tiles = []
    r = 3.1
    ring = 0
    while r < 20.6:
        dr = RNG.uniform(0.82, 1.12)
        r1 = min(r + dr, 20.6)
        n = max(12, int((r1 + r) * PI / 1.15))
        phase = RNG.uniform(0, TAU) if ring % 2 == 0 else RNG.uniform(0.4, 1.2)
        for i in range(n):
            a0 = phase + i / n * TAU + RNG.uniform(-0.004, 0.004)
            a1 = phase + (i + 1) / n * TAU - RNG.uniform(0.006, 0.02)
            gap = 0.025
            rr0 = r + gap
            rr1 = r1 - gap
            ztop = 0.285 + RNG.uniform(-0.008, 0.012)
            zbot = ztop - 0.12
            V = [(math.cos(a0) * rr0, math.sin(a0) * rr0, ztop),
                 (math.cos(a0) * rr1, math.sin(a0) * rr1, ztop),
                 (math.cos(a1) * rr1, math.sin(a1) * rr1, ztop),
                 (math.cos(a1) * rr0, math.sin(a1) * rr0, ztop),
                 (math.cos(a0) * rr0, math.sin(a0) * rr0, zbot),
                 (math.cos(a0) * rr1, math.sin(a0) * rr1, zbot),
                 (math.cos(a1) * rr1, math.sin(a1) * rr1, zbot),
                 (math.cos(a1) * rr0, math.sin(a1) * rr0, zbot)]
            F = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
                 (2, 6, 7, 3), (3, 7, 4, 0)]
            ob = mesh_obj('pave_tile', V, F, RNG.choice(mats), bevel=0.012)
            tiles.append(ob)
        r = r1
        ring += 1
    jt = join(tiles, 'plaza_paving')
    # radial border ring
    for rr in (20.55, 3.05):
        ring_objs = []
        n = 96 if rr > 10 else 40
        for i in range(n):
            a0 = i / n * TAU; a1 = (i + 1) / n * TAU
            V = [(math.cos(a0) * (rr - 0.16), math.sin(a0) * (rr - 0.16), 0.30),
                 (math.cos(a0) * (rr + 0.16), math.sin(a0) * (rr + 0.16), 0.30),
                 (math.cos(a1) * (rr + 0.16), math.sin(a1) * (rr + 0.16), 0.30),
                 (math.cos(a1) * (rr - 0.16), math.sin(a1) * (rr - 0.16), 0.30),
                 (math.cos(a0) * (rr - 0.16), math.sin(a0) * (rr - 0.16), 0.16),
                 (math.cos(a0) * (rr + 0.16), math.sin(a0) * (rr + 0.16), 0.16),
                 (math.cos(a1) * (rr + 0.16), math.sin(a1) * (rr + 0.16), 0.16),
                 (math.cos(a1) * (rr - 0.16), math.sin(a1) * (rr - 0.16), 0.16)]
            F = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
            ring_objs.append(mesh_obj('border', V, F, tile('border_stone', '#8f8574', 0.45), bevel=0.008))
        join(ring_objs, 'border_ring')
    # central tree platform
    for i, (rr, zz, hh) in enumerate([(3.15, 0.30, 0.16), (2.8, 0.34, 0.20), (2.45, 0.40, 0.24)]):
        cylinder('tree_platform%d' % i, rr, hh, (0, 0, zz + hh / 2), stone('platform%d' % i, '#9a9081', 0.55), 64)
        for k in range(14):
            a = k / 14 * TAU
            ico('platform_snow', 0.28, (math.cos(a) * rr * 0.98, math.sin(a) * rr * 0.98, zz + hh + 0.02),
                snowmat(), 1, (1.4, 0.8, 0.25), jitter=0.3)
    # puddles and wet patches
    for i, (x, y, sx, sy, rot) in enumerate([(-6.2, -5.4, 0.8, 0.35, 0.4), (7.5, -3.0, 0.5, 0.3, -0.3),
                                            (-2.0, 6.5, 0.6, 0.3, 1.2), (4.0, 2.0, 0.45, 0.25, 0.8)]):
        props.puddle((x, y, 0.30), sx, sy, rot)
    return jt


def place_buildings():
    buildings.chapel((15.2, 14.6), -4)
    buildings.market_shop((-4.4, 14.6), -3)
    buildings.bakery((5.0, 15.3), 4)
    buildings.coffee_shop((-15.3, 8.0), 25)
    buildings.pizzeria((17.8, 4.0), -58)
    buildings.cake_shop((18.4, -4.5), -48)
    buildings.fruit_shop((-20.3, -1.5), 40)


def street_life():
    # lamps around the plaza
    lamp_pos = [(-9.2, -7.2, 0.0), (9.4, -6.5, 0.0), (-7.8, 8.6, 0.0),
                (8.2, 9.2, 0.0), (-14.6, -1.0, 0.0), (14.0, -1.5, 0.0)]
    for i, (x, y, yaw) in enumerate(lamp_pos):
        props.lamp_post((x, y, 0.28), yaw)
    # light strings between the front lamps, framing the tree
    for p0, p1 in [((-9.2, -7.2, 4.5), (9.4, -6.5, 4.5)),
                   ((-7.8, 8.6, 4.5), (8.2, 9.2, 4.5)),
                   ((-14.6, -1.0, 4.5), (-9.2, -7.2, 4.5))]:
        props.string_lights('plaza_lights', p0, p1, sag=0.65, bulbs=22)
    # benches
    for x, y in [(-5.8, -8.6), (6.4, -8.0), (-10.5, 3.0), (10.0, 3.8)]:
        yaw = math.atan2(-x, y)
        props.bench((x, y, 0.3), yaw)
    # gifts around the hero tree
    paper = ['#8c1f2e', '#f0e6d6', '#24482f', '#7a1f2b', '#d8cbb4', '#2e4f4a']
    ribbon = ['#d8b36a', '#b01824', '#e6d7b6', '#8c1f2e']
    for i in range(20):
        a = i / 20 * TAU + RNG.uniform(-0.1, 0.1)
        r = RNG.uniform(2.35, 3.4)
        s = RNG.uniform(0.35, 0.8)
        props.gift_box((math.cos(a) * r, math.sin(a) * r, 0.54 if r < 3.1 else 0.3),
                       (s, s * RNG.uniform(0.8, 1.1), s * RNG.uniform(0.6, 1.0)),
                       RNG.uniform(0, TAU), RNG.choice(paper), RNG.choice(ribbon))
    # a few gifts at the plaza edge
    for i, (x, y) in enumerate([(-4.6, -5.0), (5.2, -4.4), (-12.0, 1.2)]):
        props.gift_box((x, y, 0.3), (RNG.uniform(0.4, 0.65), RNG.uniform(0.4, 0.6), RNG.uniform(0.3, 0.5)),
                       RNG.uniform(0, TAU), RNG.choice(paper), RNG.choice(ribbon))
    # planters
    for x, y in [(-2.0, -11.0), (2.8, -10.2), (-13.6, 2.5), (13.0, -3.0)]:
        props.planter((x, y, 0.28), RNG.uniform(0, TAU), 0.55, 0.5)
        t = vegetation.conifer('planter_fir', (x, y, 0.7), RNG.uniform(1.2, 1.8), 0.35, seed=int(x * 7 + 3),
                               detail=0.35, sprig_len=0.22)
    props.signpost((-11.2, -4.6), 0.7)
    props.market_stall((-11.5, -11.5, 0.3), 20)
    # scattered snow drifts in the plaza corners
    for i in range(10):
        a = RNG.uniform(0, TAU); r = RNG.uniform(11.0, 19.0)
        ico('plaza_snow', RNG.uniform(0.4, 0.9), (math.cos(a) * r, math.sin(a) * r, 0.3),
            snowmat(), 2, (1.4, 0.8, 0.2), jitter=0.3)


def vegetation_around():
    # background conifers
    spots = [(-21.5, 9.0, 6.5, 1.8, 11), (21.0, 11.0, 7.5, 2.1, 12),
             (-20.5, -7.5, 5.2, 1.5, 13), (20.5, -8.5, 5.8, 1.6, 14),
             (-9.5, 20.0, 6.2, 1.8, 15), (13.5, 20.5, 6.8, 1.9, 16),
             (-19.0, 17.0, 5.5, 1.6, 17), (17.5, 18.0, 5.0, 1.5, 18),
             (-15.0, -13.5, 4.6, 1.3, 19), (15.0, -12.0, 4.8, 1.4, 20),
             (-21.2, -10.5, 7.4, 1.9, 21), (21.0, -10.0, 8.2, 2.1, 22)]
    for (x, y, h, r, sd) in spots:
        vegetation.conifer('village_fir', (x, y, 0.28), h, r, seed=sd, detail=0.55, sprig_len=0.42)
    # bare trees
    vegetation.deciduous('bare_tree1', (-22.0, 1.4, 0.28), 7.0, seed=41)
    vegetation.deciduous('bare_tree2', (22.0, -1.5, 0.28), 6.0, seed=42)
    # shrubs at the shop fronts
    for x, y in [(-6.0, 11.3), (-1.8, 12.6), (2.0, 12.7), (7.0, 12.4),
                 (15.6, 2.6), (15.0, -7.4), (-14.4, 1.0), (-14.6, -9.0)]:
        vegetation.shrub('shrub', (x, y, 0.3), RNG.uniform(0.45, 0.7), seed=int(x * 3 + y))


def hero_tree():
    vegetation.big_christmas_tree((0, 0, 0.6), 15.2, 4.65)
    # extra snow on the tree base
    for i in range(16):
        a = i / 16 * TAU
        ico('treebase_snow', RNG.uniform(0.25, 0.45), (math.cos(a) * 2.9, math.sin(a) * 2.9, 0.7),
            snowmat(), 2, (1.3, 0.9, 0.25), jitter=0.3)


def backdrop():
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 65, 34))
    ob = bpy.context.active_object
    ob.name = 'sky_backdrop'
    ob.scale = (420, 240, 1)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    m = bpy.data.materials.new('sky_backdrop_mat')
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    mix = nt.nodes.new('ShaderNodeMixShader'); mix.location = (500, 0)
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    trans = nt.nodes.new('ShaderNodeBsdfTransparent'); trans.location = (300, -120)
    nt.links.new(trans.outputs[0], mix.inputs[1])
    em = nt.nodes.new('ShaderNodeEmission'); em.location = (300, 120)
    em.inputs['Strength'].default_value = 0.9
    nt.links.new(em.outputs[0], mix.inputs[2])
    lp = nt.nodes.new('ShaderNodeLightPath'); lp.location = (100, 300)
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    tc = nt.nodes.new('ShaderNodeTexCoord'); tc.location = (-900, 0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-700, 0)
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-450, 0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = lin('#6b5a52')
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = lin('#070c16')
    e = ramp.color_ramp.elements.new(0.28)
    e.color = lin('#3f5372')
    e2 = ramp.color_ramp.elements.new(0.48)
    e2.color = lin('#23344f')
    e3 = ramp.color_ramp.elements.new(0.62)
    e3.color = lin('#121e32')
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    return ob


def stars():
    m1 = emission('star_cool', '#cfe0ff', 2.2)
    m2 = emission('star_warm', '#ffe5bd', 2.6)
    objs = []
    for i in range(170):
        x = RNG.uniform(-70, 70)
        y = RNG.uniform(22, 54)
        z = RNG.uniform(18, 80)
        r = RNG.uniform(0.03, 0.09)
        objs.append(sphere('star', r, (x, y, z), m1 if i % 5 else m2, 6, 4))
    for i in range(12):
        objs.append(sphere('star', RNG.uniform(0.12, 0.19),
                           (RNG.uniform(-50, 50), RNG.uniform(25, 52), RNG.uniform(24, 68)),
                           m1 if i % 3 else m2, 8, 6))
    j = join(objs, 'stars')
    return j


def snowflakes():
    objs = []
    for i in range(420):
        x = RNG.uniform(-24, 24)
        y = RNG.uniform(-24, 24)
        z = RNG.uniform(1.0, 19.0)
        r = RNG.uniform(0.018, 0.055)
        objs.append(sphere('flake', r, (x, y, z), snowmat('flake_snow', '#f4f8ff'), 6, 4))
    j = join(objs, 'snowflakes')
    j.data.materials[0] = emission('flakeglow', '#dfeaff', 0.35)


def mist():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 4.5))
    ob = bpy.context.active_object
    ob.name = 'mist_volume'
    ob.scale = (72, 72, 9)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m = bpy.data.materials.new('mist_mat')
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    vol = nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.64, 0.74, 0.92, 1)
    vol.inputs['Density'].default_value = 0.0035
    vol.inputs['Anisotropy'].default_value = 0.35
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob


def lights():
    def area(name, loc, target, energy, color, size):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy; ld.color = color; ld.shape = 'DISK'; ld.size = size
        ob = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = loc
        d = Vector(target) - Vector(loc)
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        return ob
    # crisp cold moonlight
    ld = bpy.data.lights.new('moon_sun', 'SUN')
    ld.energy = 2.7; ld.angle = 0.08; ld.color = (0.5, 0.65, 1.0)
    sun = bpy.data.objects.new('moon_sun', ld)
    bpy.context.scene.collection.objects.link(sun)
    sun.location = (-34, 26, 44)
    d = Vector((0, 0, 4)) - sun.location
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    area('moon', (-30, 20, 38), (0, 0, 4), 500, (0.6, 0.72, 1.0), 24)
    area('sky_fill', (24, -30, 24), (0, 0, 5), 280, (0.55, 0.68, 1.0), 30)
    area('warm_fill', (-6, -24, 9), (0, 0, 4), 350, (1.0, 0.66, 0.38), 14)
    # warm rim behind the town
    area('back_glow', (0, 28, 12), (0, 0, 4), 900, (0.9, 0.55, 0.35), 22)


def camera(sc):
    cam_data = bpy.data.cameras.new('hero_cam')
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 58.0
    cam = bpy.data.objects.new('hero_cam', cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (-16.0, -45.0, 27.0)
    target = Vector((0.0, 0.0, 6.3))
    d = target - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    return cam


def compositor(sc):
    ng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
    sc.compositing_node_group = ng
    out = ng.nodes.new('NodeGroupOutput')
    out.location = (500, 0)
    ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new('CompositorNodeRLayers'); rl.location = (-400, 0)
    glare = ng.nodes.new('CompositorNodeGlare'); glare.location = (0, 0)
    try:
        glare.inputs['Type'].default_value = 'Fog Glow'
    except Exception:
        try:
            glare.inputs['Type'].default_value = 'FOG_GLOW'
        except Exception:
            pass
    for k, v in [('Quality', 'High'), ('Threshold', 0.72), ('Strength', 0.85),
                 ('Size', 0.78), ('Saturation', 1.0)]:
        try:
            glare.inputs[k].default_value = v
        except Exception:
            pass
    ng.links.new(rl.outputs['Image'], glare.inputs['Image'])
    ng.links.new(glare.outputs['Image'], out.inputs['Image'])


def main():
    global props, vegetation, buildings
    t0 = time.time()
    sc = reset()
    import props, vegetation, buildings
    world(sc)
    base_and_plaza()
    place_buildings()
    hero_tree()
    street_life()
    vegetation_around()
    snowflakes()
    backdrop()
    stars()
    mist()
    lights()
    camera(sc)
    compositor(sc)
    name = 'draft.png' if DRAFT else ('preview.png' if PREVIEW else 'christmas_town.png')
    sc.render.filepath = os.path.join(ROOT, 'renders', name)
    print('BUILD DONE', round(time.time() - t0, 1), 'objects', len(bpy.data.objects))
    if not ('--norender' in sys.argv):
        bpy.ops.render.render(write_still=True)
        print('RENDER DONE', round(time.time() - t0, 1))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'christmas_town.blend'))
    print('SAVED')


if __name__ == '__main__':
    main()
