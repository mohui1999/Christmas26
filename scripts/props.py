"""Street furniture, decorations and small props."""
import bpy, math, random
from mathutils import Vector, Euler
from lib import (box, cylinder, cone, sphere, ico, empty, join, curve_tube,
                 text_obj, mesh_obj, metal, gloss, wood, fabric, emission,
                 snowmat, stone, plaster, PI, TAU, RNG, lin)

WARM = '#ffb35c'
BULB = emission('fairy_bulb', '#ffc27a', 9.0)
BULB_SOFT = emission('fairy_bulb_soft', '#ffe0b0', 4.0)
IRON = metal('iron_black', '#14171c', 0.34)
IRON_SOFT = metal('iron_dark', '#22262c', 0.42)
SNOW = snowmat()
GOLD = metal('gold', '#e8b25c', 0.22)
GLASS_WARM = emission('lamp_glass', '#ffb264', 7.0)


def lamp_post(loc, yaw=0.0, power=320.0):
    e = empty('lamp', loc, (0, 0, yaw))
    objs = []
    objs.append(cylinder('lamp_base1', 0.34, 0.12, (0, 0, 0.06), IRON, 24, parent=e))
    objs.append(cylinder('lamp_base2', 0.23, 0.2, (0, 0, 0.22), IRON, 20, parent=e))
    objs.append(cylinder('lamp_base3', 0.13, 0.45, (0, 0, 0.53), IRON, 20, parent=e))
    objs.append(cylinder('lamp_pole', 0.052, 2.9, (0, 0, 2.15), IRON, 12, parent=e))
    objs.append(cone('lamp_collar', 0.15, 0.075, 0.18, (0, 0, 3.52), IRON, 8, parent=e))
    objs.append(box('lamp_plate', 0.36, 0.36, 0.05, (0, 0, 3.64), IRON, 0.01, parent=e))
    # lantern glass + frame
    objs.append(box('lamp_glass', 0.3, 0.3, 0.42, (0, 0, 3.88), GLASS_WARM, 0.02, parent=e))
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(box('lamp_bar', 0.028, 0.028, 0.48, (sx * 0.155, sy * 0.155, 3.88), IRON, 0.004, parent=e))
    objs.append(box('lamp_top', 0.42, 0.42, 0.05, (0, 0, 4.12), IRON, 0.01, parent=e))
    objs.append(cone('lamp_roof', 0.28, 0.02, 0.26, (0, 0, 4.28), IRON, 4, parent=e))
    objs.append(sphere('lamp_finial', 0.055, (0, 0, 4.44), GOLD, 12, 8, parent=e))
    # snow cap
    objs.append(ico('lamp_snow', 0.24, (0, 0.02, 4.36), SNOW, 2, (1.0, 1.0, 0.28), parent=e, jitter=0.18))
    objs.append(ico('lamp_snowbase', 0.34, (0.02, -0.02, 0.14), SNOW, 2, (1.0, 1.0, 0.22), parent=e, jitter=0.2))
    # little hanging garland on the collar
    for i in range(6):
        a = i / 6 * TAU
        objs.append(cone('lamp_pine', 0.09, 0.0, 0.3, (math.cos(a) * 0.17, math.sin(a) * 0.17, 3.5),
                         foliage(), 7, rot=(0.9 * math.sin(a), 0.9 * -math.cos(a), 0), parent=e))
    ld = bpy.data.lights.new('lamp_light', 'POINT')
    ld.energy = power
    ld.color = (1.0, 0.62, 0.3)
    ld.shadow_soft_size = 0.22
    ld.use_soft_falloff = True
    lo = bpy.data.objects.new('lamp_light', ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (0, 0, 3.88)
    lo.parent = e
    return e


def foliage():
    key = 'foliage_green'
    m = bpy.data.materials.get(key)
    if m:
        return m
    return plaster('foliage_green', '#1d3a28', 0.82, 0.35)


def bench(loc, yaw=0.0):
    e = empty('bench', loc, (0, 0, yaw))
    W = wood('bench_wood', '#6a4a30', 0.6)
    objs = []
    for side in (-1, 1):
        objs.append(box('bench_leg', 0.09, 0.55, 0.46, (side * 0.8, 0.02, 0.23), IRON, 0.012, parent=e))
        objs.append(box('bench_arm', 0.09, 0.06, 0.38, (side * 0.8, -0.28, 0.6), IRON, 0.01, parent=e))
        objs.append(box('bench_arm2', 0.09, 0.55, 0.06, (side * 0.8, 0.0, 0.78), IRON, 0.01, parent=e))
    for i in range(4):
        y = -0.2 + i * 0.148
        objs.append(box('bench_slat', 1.78, 0.12, 0.055, (0, y, 0.49 + 0.006 * i), W, 0.012, parent=e))
    for i in range(3):
        objs.append(box('bench_back', 1.78, 0.05, 0.13, (0, 0.29, 0.66 + i * 0.16), W, 0.01,
                        rot=(0.1, 0, 0), parent=e))
    for i in range(6):
        objs.append(ico('bench_snow', 0.17 + RNG.random() * 0.1,
                        (-0.65 + i * 0.26, -0.03 + RNG.random() * 0.06, 0.53),
                        SNOW, 1, (1.4, 0.9, 0.2), parent=e, jitter=0.25))
    return e


def gift_box(loc, size=(0.6, 0.55, 0.5), rot=0.0, paper='#8c1f2e',
             ribbon='#d8b36a', bow=True):
    e = empty('gift', loc, (0, 0, rot))
    sx, sy, sz = size
    pm = gloss('paper_' + paper, paper, 0.48, 0.0, 0.25)
    rm = fabric('ribbon_' + ribbon, ribbon, 0.45, 0.55)
    objs = [box('gift_box', sx, sy, sz, (0, 0, sz / 2), pm, 0.018, parent=e)]
    # ribbons crossing
    objs.append(box('gift_r1', 0.1, sy + 0.012, sz + 0.012, (0, 0, sz / 2), rm, 0.006, parent=e))
    objs.append(box('gift_r2', sx + 0.012, 0.1, sz + 0.012, (0, 0, sz / 2), rm, 0.006, parent=e))
    if bow:
        for a in (-0.55, 0.55):
            objs.append(sphere('bow_loop', 0.13, (a * sx * 0.5, 0, sz + 0.07), rm, 16, 10,
                               (0.8, 0.35, 0.6), parent=e))
        objs.append(sphere('bow_knot', 0.06, (0, 0, sz + 0.06), rm, 12, 8, (1, 1, 1), parent=e))
    return e


def wreath(loc, radius=0.32, rot=(math.pi / 2, 0, 0), parent=None, berries=7):
    mats = foliage()
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=radius * 0.24,
                                     major_segments=28, minor_segments=9,
                                     location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = 'wreath'
    ob.rotation_euler = rot
    ob.location = loc
    if parent:
        ob.parent = parent
    me = ob.data
    me.materials.append(mats)
    for v in me.vertices:
        d = Vector((v.co.x, v.co.y, 0)).normalized()
        v.co += d * 0.02 * random.random()
    # berries in torus local plane
    for i in range(berries):
        a = i / berries * TAU + 0.2
        s = sphere('wreath_berry', radius * 0.11,
                   (math.cos(a) * radius * 1.05, math.sin(a) * radius * 1.05, 0.02),
                   gloss('holly_berry', '#a5121b', 0.22), 10, 6)
        s.parent = ob
    bowm = fabric('bow_red', '#a5121b', 0.5, 0.4)
    b = sphere('wreath_bow', radius * 0.3, (0, -radius * 1.0, -0.02), bowm, 14, 8,
               (1.4, 0.5, 0.8))
    b.parent = ob
    return ob


def planter(loc, yaw=0.0, r=0.5, h=0.5):
    e = empty('planter', loc, (0, 0, yaw))
    objs = [cylinder('pot', r, h, (0, 0, h / 2), stone('pot_stone', '#8d8578', 0.7), 20, parent=e)]
    objs.append(cylinder('pot_rim', r * 1.08, 0.09, (0, 0, h - 0.03), stone('pot_stone2', '#a49a8a', 0.65), 20, parent=e))
    objs.append(ico('pot_snow', r * 0.98, (0, 0, h - 0.02), SNOW, 2, (1, 1, 0.28), parent=e, jitter=0.2))
    return e


def candy_cane(loc, scale=1.0):
    pts = []
    for i in range(16):
        t = i / 15
        a = -PI / 2 + t * PI * 0.85
        if i < 10:
            pts.append((0, 0, (0.02 + t * 0.55) * scale))
        else:
            pass
    # simpler L: vertical + hook
    pts = [(0, 0, 0.02 * scale), (0, 0, 0.45 * scale)]
    for i in range(9):
        a = PI * i / 8
        pts.append((0.12 * (1 - math.cos(a)) * scale, 0, (0.45 + 0.12 * math.sin(a)) * scale))
    ob = curve_tube('candy_cane', pts, 0.028 * scale, gloss('candy_red', '#c81f2c', 0.35))
    ob.location = loc
    return ob


def string_lights(name, p0, p1, sag=0.35, bulbs=18, bulb=BULB, parent=None):
    p0 = Vector(p0); p1 = Vector(p1)
    pts = []
    for i in range(21):
        t = i / 20
        p = p0.lerp(p1, t)
        p.z -= math.sin(math.pi * t) * sag
        pts.append(p)
    wire = curve_tube(name + '_wire', pts, 0.007, IRON)
    if parent:
        wire.parent = parent
    bulbs_objs = []
    for i in range(bulbs):
        t = (i + 0.5) / bulbs
        p = p0.lerp(p1, t)
        p.z -= math.sin(math.pi * t) * sag + 0.04
        o = sphere(name + '_b', 0.019, p, bulb, 6, 4)
        if parent:
            o.parent = parent
        bulbs_objs.append(o)
    b = join(bulbs_objs, name + '_bulbs')
    if parent:
        b.parent = parent
    return wire, b


def signpost(loc, yaw=0.0):
    e = empty('signpost', loc, (0, 0, yaw))
    W = wood('sign_wood', '#4d3524', 0.65)
    objs = [cylinder('sign_post', 0.075, 2.6, (0, 0, 1.3), W, 10, parent=e)]
    objs.append(cone('sign_top', 0.09, 0.0, 0.28, (0, 0, 2.74), wood('sign_wood2', '#5a3e2a', 0.65), 8, parent=e))
    for i, (z, a) in enumerate([(2.2, 0.0), (1.75, 2.3)]):
        objs.append(box('sign_board', 0.9, 0.06, 0.22, (0.28, 0, z), W, 0.012, rot=(0, 0, a), parent=e))
        objs.append(sphere('sign_star', 0.06, (0.55, -0.04, z), GOLD, 10, 6, (1, 1, 1), parent=e))
    objs.append(ico('sign_snow', 0.1, (0.28, 0, 2.08), SNOW, 1, (1.6, 0.3, 0.25), parent=e, jitter=0.2))
    return e


def puddle(loc, sx=0.7, sy=0.35, rot=0.0):
    bmverts = []
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=20, radius=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy
    for v in bm.verts:
        v.co.z = 0.0
    me = bpy.data.meshes.new('puddle')
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('puddle', me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.get('puddle_mat')
    if not m:
        m, nt, b = __import__('lib')._base('puddle_mat')
        b.inputs['Base Color'].default_value = lin('#0a0d12')
        b.inputs['Roughness'].default_value = 0.04
        b.inputs['Metallic'].default_value = 0.1
    me.materials.append(m)
    ob.location = (loc[0], loc[1], loc[2])
    ob.rotation_euler = (0, 0, rot)
    return ob


def market_stall(loc, yaw=0.0):
    e = empty('stall', loc, (0, 0, yaw))
    W = wood('stall_wood', '#6a4a30', 0.6)
    WD = wood('stall_wood_dark', '#3a2a1e', 0.65)
    red = fabric('stall_red', '#a8322f', 0.85, 0.5)
    cream = fabric('stall_cream', '#f0e4d2', 0.85, 0.5)
    objs = []
    objs.append(box('stall_counter', 2.8, 0.8, 0.95, (0, 0.1, 0.55), W, 0.02, parent=e))
    objs.append(box('stall_top', 2.9, 0.9, 0.08, (0, 0.1, 1.04), WD, 0.01, parent=e))
    objs.append(box('stall_back', 2.8, 0.18, 2.1, (0, 0.58, 1.25), W, 0.015, parent=e))
    for i, z in enumerate((1.2, 1.65, 2.1)):
        objs.append(box('stall_shelf', 2.6, 0.45, 0.06, (0, 0.42, z), WD, 0.008, parent=e))
    for sx in (-1.36, 1.36):
        for sy in (-0.45, 0.6):
            objs.append(box('stall_post', 0.09, 0.09, 2.7, (sx, sy, 1.35), WD, 0.005, parent=e))
    # striped canopy, a simple shallow gable of coloured planks
    for i in range(9):
        x = -1.36 + (i + 0.5) * 2.72 / 9
        m = red if i % 2 == 0 else cream
        objs.append(box('stall_canopy', 2.72 / 9 + 0.002, 1.5, 0.05,
                        (x, 0.05, 2.72), m, 0.004, rot=(0.12, 0, 0), parent=e))
    objs.append(box('stall_valance', 2.8, 0.05, 0.2, (0, -0.7, 2.58), red, 0.004, parent=e))
    # snow on the canopy
    for i in range(4):
        objs.append(ico('stall_snow', 0.16, (-1.0 + i * 0.68, 0.05, 2.79), SNOW, 1,
                        (1.6, 1.0, 0.25), parent=e, jitter=0.25))
    # goods on the counter
    for i in range(5):
        objs.append(cylinder('stall_jar', 0.08, 0.22, (-1.0 + i * 0.5, 0.05, 1.2),
                             gloss('stall_glass', '#c98b45', 0.25), 10, parent=e))
    for i in range(4):
        objs.append(box('stall_gift', 0.24, 0.2, 0.18, (-1.1 + i * 0.7, 0.1, 1.1),
                        red if i % 2 else cream, 0.01, parent=e))
    # hanging lanterns
    for sx in (-0.9, 0.9):
        objs.append(box('stall_lantern', 0.16, 0.16, 0.24, (sx, -0.25, 2.2), GLASS_WARM, 0.01, parent=e))
        objs.append(box('stall_lantop', 0.22, 0.22, 0.04, (sx, -0.25, 2.33), IRON, 0.004, parent=e))
    # pine garland + bulbs across the front
    for i in range(7):
        x = -1.2 + i * 0.4
        objs.append(ico('stall_pine', 0.12, (x, -0.68, 2.45 + 0.04 * math.sin(i)), foliage(), 1,
                        (1.2, 0.7, 0.8), parent=e, jitter=0.2))
        objs.append(sphere('stall_bulb', 0.025, (x + 0.1, -0.72, 2.36), BULB, 6, 4, parent=e))
    g = join(objs, 'stall_parts')
    g.parent = e
    # warm lantern light
    ld = bpy.data.lights.new('stall_light', 'POINT')
    ld.energy = 120; ld.color = (1.0, 0.62, 0.3); ld.shadow_soft_size = 0.4
    lo = bpy.data.objects.new('stall_light', ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (0, -0.2, 2.2)
    lo.parent = e
    # a star on the roof
    star = cone('stall_star', 0.16, 0.0, 0.28, (0, -0.72, 2.72), GOLD, 5, rot=(0, 0, 0), parent=e)
    return e


def icicle(loc, length=0.35, r=0.035, parent=None):
    return cone('icicle', r, 0.002, length, loc, glass_ice(), 6, rot=(PI, 0, 0), parent=parent)


def glass_ice():
    m = bpy.data.materials.get('ice')
    if m:
        return m
    m, nt, b = __import__('lib')._base('ice')
    b.inputs['Base Color'].default_value = lin('#bfe2f2')
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Transmission Weight'].default_value = 0.85
    b.inputs['IOR'].default_value = 1.31
    return m
