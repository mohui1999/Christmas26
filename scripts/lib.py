"""Helpers for the Christmas town scene (Blender 5.3)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
from mathutils import noise as mnoise

PI = math.pi
TAU = 2 * math.pi
RNG = random.Random(20261225)


# --------------------------------------------------------------------------- #
# colour + materials
# --------------------------------------------------------------------------- #
def lin(hexstr, a=1.0):
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], a)


def mixc(c, f):
    return (min(1, c[0] * f), min(1, c[1] * f), min(1, c[2] * f), 1.0)


def _base(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (800, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (480, 0)
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m, nt, b


def _texcoord(nt, loc=(-1000, 0)):
    tc = nt.nodes.new('ShaderNodeTexCoord'); tc.location = loc
    return tc


def _noise(nt, scale, detail=4.0, rough=0.55, distortion=0.0, loc=(-750, 0)):
    n = nt.nodes.new('ShaderNodeTexNoise'); n.location = loc
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = distortion
    return n


def _bump(nt, height_socket, strength=0.2, distance=0.02, loc=(250, -300)):
    b = nt.nodes.new('ShaderNodeBump'); b.location = loc
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = distance
    nt.links.new(height_socket, b.inputs['Height'])
    return b


def _mixrgb(nt, c1, c2, fac_socket=None, fac=0.5, blend='MIX', loc=(0, 0)):
    m = nt.nodes.new('ShaderNodeMixRGB'); m.location = loc
    m.blend_type = blend
    if isinstance(c1, tuple):
        m.inputs[1].default_value = c1
    else:
        nt.links.new(c1, m.inputs[1])
    if isinstance(c2, tuple):
        m.inputs[2].default_value = c2
    else:
        nt.links.new(c2, m.inputs[2])
    if fac_socket is not None:
        nt.links.new(fac_socket, m.inputs[0])
    else:
        m.inputs[0].default_value = fac
    return m


MATS = {}


def plaster(name, hexcol, rough=0.86, bump=0.12):
    key = 'pl_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    base = lin(hexcol)
    tc = _texcoord(nt)
    n = _noise(nt, 3.2, 5, 0.55, loc=(-780, 60))
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-500, 120)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = mixc(base, 0.88)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = mixc(base, 1.06)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    # darken the base of each wall a little
    gen = nt.nodes.new('ShaderNodeTexCoord'); gen.location = (-900, -520)
    gsep = nt.nodes.new('ShaderNodeSeparateXYZ'); gsep.location = (-720, -520)
    nt.links.new(gen.outputs['Generated'], gsep.inputs['Vector'])
    gramp = nt.nodes.new('ShaderNodeValToRGB'); gramp.location = (-540, -520)
    gramp.color_ramp.elements[0].position = 0.0
    gramp.color_ramp.elements[0].color = (0.42, 0.4, 0.38, 1)
    gramp.color_ramp.elements[1].position = 0.14
    gramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(gsep.outputs['Z'], gramp.inputs['Fac'])
    mixd = nt.nodes.new('ShaderNodeMixRGB'); mixd.location = (-300, 80)
    mixd.blend_type = 'MULTIPLY'; mixd.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], mixd.inputs[1])
    nt.links.new(gramp.outputs['Color'], mixd.inputs[2])
    nt.links.new(mixd.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    fine = _noise(nt, 55, 3, 0.5, loc=(-500, -260))
    nt.links.new(tc.outputs['Object'], fine.inputs['Vector'])
    bmp = _bump(nt, fine.outputs['Fac'], bump, 0.012)
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    MATS[key] = m
    return m


def stone(name, hexcol, rough=0.6, scale=1.2, bump=0.28):
    key = 'st_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    base = lin(hexcol)
    tc = _texcoord(nt)
    n = _noise(nt, 4.5, 6, 0.6, 1.1, loc=(-780, 60))
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-500, 120)
    ramp.color_ramp.elements[0].position = 0.32
    ramp.color_ramp.elements[0].color = mixc(base, 0.78)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = mixc(base, 1.12)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    gen = nt.nodes.new('ShaderNodeTexCoord'); gen.location = (-900, -520)
    gsep = nt.nodes.new('ShaderNodeSeparateXYZ'); gsep.location = (-720, -520)
    nt.links.new(gen.outputs['Generated'], gsep.inputs['Vector'])
    gramp = nt.nodes.new('ShaderNodeValToRGB'); gramp.location = (-540, -520)
    gramp.color_ramp.elements[0].position = 0.0
    gramp.color_ramp.elements[0].color = (0.48, 0.46, 0.44, 1)
    gramp.color_ramp.elements[1].position = 0.12
    gramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(gsep.outputs['Z'], gramp.inputs['Fac'])
    mixd = nt.nodes.new('ShaderNodeMixRGB'); mixd.location = (-300, 80)
    mixd.blend_type = 'MULTIPLY'; mixd.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], mixd.inputs[1])
    nt.links.new(gramp.outputs['Color'], mixd.inputs[2])
    nt.links.new(mixd.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    v = nt.nodes.new('ShaderNodeTexVoronoi'); v.location = (-780, -260)
    v.feature = 'DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value = 12.0
    nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
    bmp = _bump(nt, v.outputs['Distance'], bump, 0.05)
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    MATS[key] = m
    return m


def tile(name, hexcol, rough=0.42, scale=1.0):
    key = 'ti_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    base = lin(hexcol)
    tc = _texcoord(nt)
    n = _noise(nt, 6.0 * scale, 6, 0.62, 0.8, loc=(-780, 60))
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-500, 120)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = mixc(base, 0.8)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = mixc(base, 1.1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    # slightly wet / polished stone
    rn = _noise(nt, 2.2, 3, 0.5, loc=(-500, -420))
    nt.links.new(tc.outputs['Object'], rn.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.location = (-220, -380)
    mr.inputs['From Min'].default_value = 0.3
    mr.inputs['From Max'].default_value = 0.7
    mr.inputs['To Min'].default_value = rough - 0.12
    mr.inputs['To Max'].default_value = rough + 0.18
    nt.links.new(rn.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    v = nt.nodes.new('ShaderNodeTexVoronoi'); v.location = (-780, -300)
    v.feature = 'DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value = 22.0
    nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
    bmp = _bump(nt, v.outputs['Distance'], 0.12, 0.02)
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    MATS[key] = m
    return m


def wood(name, hexcol, rough=0.55, scale=1.5):
    key = 'wd_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    base = lin(hexcol)
    tc = _texcoord(nt)
    w = nt.nodes.new('ShaderNodeTexWave'); w.location = (-750, 80)
    w.wave_type = 'BANDS'; w.bands_direction = 'Z'
    w.inputs['Scale'].default_value = 2.4 * scale
    w.inputs['Distortion'].default_value = 9.0
    w.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-480, 120)
    ramp.color_ramp.elements[0].position = 0.2
    ramp.color_ramp.elements[0].color = mixc(base, 0.62)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = mixc(base, 1.18)
    nt.links.new(w.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    bmp = _bump(nt, w.outputs['Fac'], 0.3, 0.02)
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    MATS[key] = m
    return m


def roofmat(name, hexcol, scale=1.0):
    key = 'rf_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    base = lin(hexcol)
    tc = _texcoord(nt)
    br = nt.nodes.new('ShaderNodeTexBrick'); br.location = (-700, 90)
    br.inputs['Scale'].default_value = 7.0 * scale
    br.inputs['Mortar Size'].default_value = 0.035
    br.inputs['Mortar Smooth'].default_value = 0.2
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Brick Width'].default_value = 0.5
    br.inputs['Row Height'].default_value = 0.3
    br.inputs['Color1'].default_value = mixc(base, 0.82)
    br.inputs['Color2'].default_value = mixc(base, 1.12)
    br.inputs['Mortar'].default_value = mixc(base, 0.45)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    # patchy snow dusting on upward facing tiles
    geo = nt.nodes.new('ShaderNodeNewGeometry'); geo.location = (-700, -300)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-520, -300)
    nt.links.new(geo.outputs['Normal'], sep.inputs['Vector'])
    mrz = nt.nodes.new('ShaderNodeMapRange'); mrz.location = (-330, -300)
    mrz.inputs['From Min'].default_value = 0.5
    mrz.inputs['From Max'].default_value = 0.9
    mrz.inputs['To Min'].default_value = 0.0
    mrz.inputs['To Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], mrz.inputs['Value'])
    ns = nt.nodes.new('ShaderNodeTexNoise'); ns.location = (-700, -540)
    ns.inputs['Scale'].default_value = 2.6
    ns.inputs['Detail'].default_value = 5.0
    nt.links.new(tc.outputs['Object'], ns.inputs['Vector'])
    mrn = nt.nodes.new('ShaderNodeMapRange'); mrn.location = (-330, -540)
    mrn.inputs['From Min'].default_value = 0.44
    mrn.inputs['From Max'].default_value = 0.62
    mrn.inputs['To Min'].default_value = 0.0
    mrn.inputs['To Max'].default_value = 1.0
    nt.links.new(ns.outputs['Fac'], mrn.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.location = (-140, -400)
    nt.links.new(mrz.outputs['Result'], mul.inputs[0])
    nt.links.new(mrn.outputs['Result'], mul.inputs[1])
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.location = (60, 60)
    mix.blend_type = 'MIX'
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(br.outputs['Color'], mix.inputs[1])
    mix.inputs[2].default_value = lin('#e9f0fb')
    nt.links.new(mix.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.78
    bmp = _bump(nt, br.outputs['Fac'], 0.35, 0.03)
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    MATS[key] = m
    return m


def snowmat(name='snow', tint='#e7edf8'):
    key = 'sn_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    base = lin(tint)
    tc = _texcoord(nt)
    n = _noise(nt, 14.0, 6, 0.62, 0.6, loc=(-780, 60))
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-500, 120)
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = lin('#c9d7ea')
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = base
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.62
    b.inputs['Subsurface Weight'].default_value = 0.12
    b.inputs['Subsurface Radius'].default_value = (0.08, 0.1, 0.14)
    v = nt.nodes.new('ShaderNodeTexVoronoi'); v.location = (-780, -300)
    v.feature = 'F1'; v.inputs['Scale'].default_value = 45.0
    nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
    bmp = _bump(nt, v.outputs['Distance'], 0.35, 0.02)
    # suggest tile courses under the snow
    br = nt.nodes.new('ShaderNodeTexBrick'); br.location = (-780, -560)
    br.inputs['Scale'].default_value = 7.0
    br.inputs['Mortar Size'].default_value = 0.03
    br.inputs['Brick Width'].default_value = 0.5
    br.inputs['Row Height'].default_value = 0.28
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    bmp2 = nt.nodes.new('ShaderNodeBump'); bmp2.location = (60, -420)
    bmp2.inputs['Strength'].default_value = 0.18
    bmp2.inputs['Distance'].default_value = 0.02
    nt.links.new(br.outputs['Fac'], bmp2.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], bmp2.inputs['Normal'])
    nt.links.new(bmp2.outputs['Normal'], b.inputs['Normal'])
    MATS[key] = m
    return m


def metal(name, hexcol, rough=0.28):
    key = 'mt_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    b.inputs['Base Color'].default_value = lin(hexcol)
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = rough
    MATS[key] = m
    return m


def gloss(name, hexcol, rough=0.28, metalv=0.0, coat=0.4):
    key = 'gl_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    b.inputs['Base Color'].default_value = lin(hexcol)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metalv
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = 0.08
    MATS[key] = m
    return m


def emission(name, hexcol, strength=5.0):
    key = 'em_' + name
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (300, 0)
    e = nt.nodes.new('ShaderNodeEmission'); e.location = (60, 0)
    e.inputs['Color'].default_value = lin(hexcol)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], out.inputs['Surface'])
    MATS[key] = m
    return m


def window_glow(name, hexcol, strength=2.2):
    key = 'wg_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    b.inputs['Base Color'].default_value = lin('#20140c')
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Emission Color'].default_value = lin(hexcol)
    b.inputs['Emission Strength'].default_value = strength
    MATS[key] = m
    return m


def glass(name, tint='#b8d2e4', alpha=0.25, transmission=0.0):
    key = 'gs_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    b.inputs['Base Color'].default_value = lin(tint)
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Alpha'].default_value = alpha
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['IOR'].default_value = 1.45
    b.inputs['Coat Weight'].default_value = 0.6
    b.inputs['Coat Roughness'].default_value = 0.02
    m.use_backface_culling = False
    MATS[key] = m
    return m


def fabric(name, hexcol, rough=0.85, sheen=0.4):
    key = 'fb_' + name
    if key in MATS:
        return MATS[key]
    m, nt, b = _base(name)
    b.inputs['Base Color'].default_value = lin(hexcol)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Sheen Roughness'].default_value = 0.4
    MATS[key] = m
    return m


# --------------------------------------------------------------------------- #
# geometry helpers
# --------------------------------------------------------------------------- #
def _new_obj(name, me):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _finish(bm, name, mat, smooth=False, bevel=0.0):
    if bevel > 0:
        try:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel,
                            offset_type='OFFSET', segments=2, profile=0.5,
                            affect='EDGES', clamp_overlap=True)
        except Exception:
            pass
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = _new_obj(name, me)
    if mat:
        me.materials.append(mat)
    return ob


def box(name, sx, sy, sz, loc=(0, 0, 0), mat=None, bevel=0.0,
        rot=(0, 0, 0), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
    ob = _finish(bm, name, mat, bevel=min(bevel, min(sx, sy, sz) * 0.45))
    ob.location = loc
    ob.rotation_euler = rot
    if parent:
        ob.parent = parent
    return ob


def cylinder(name, r, depth, loc=(0, 0, 0), mat=None, segments=20,
             rot=(0, 0, 0), parent=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r, radius2=r, depth=depth)
    ob = _finish(bm, name, mat, bevel=bevel)
    ob.location = loc
    ob.rotation_euler = rot
    if parent:
        ob.parent = parent
    return ob


def cone(name, r1, r2, depth, loc=(0, 0, 0), mat=None, segments=16,
         rot=(0, 0, 0), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r1, radius2=r2, depth=depth)
    ob = _finish(bm, name, mat)
    ob.location = loc
    ob.rotation_euler = rot
    if parent:
        ob.parent = parent
    return ob


def sphere(name, r, loc=(0, 0, 0), mat=None, seg=20, ring=12,
           scale=(1, 1, 1), parent=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=r)
    for v in bm.verts:
        v.co.x *= scale[0]; v.co.y *= scale[1]; v.co.z *= scale[2]
    ob = _finish(bm, name, mat, smooth=smooth)
    ob.location = loc
    if parent:
        ob.parent = parent
    return ob


def ico(name, r, loc=(0, 0, 0), mat=None, subdiv=2, scale=(1, 1, 1),
        parent=None, jitter=0.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    for v in bm.verts:
        if jitter:
            n = mnoise.noise(v.co * 3.0 + Vector((13.2, 4.7, 8.1)))
            v.co *= 1.0 + n * jitter
        v.co.x *= scale[0]; v.co.y *= scale[1]; v.co.z *= scale[2]
    ob = _finish(bm, name, mat, smooth=True)
    ob.location = loc
    if parent:
        ob.parent = parent
    return ob


def mesh_obj(name, verts, faces, mat=None, loc=(0, 0, 0), rot=(0, 0, 0),
             parent=None, smooth=False, bevel=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = _new_obj(name, me)
    if mat:
        me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if bevel:
        mod = ob.modifiers.new('bev', 'BEVEL')
        mod.width = bevel; mod.segments = 2
    ob.location = loc; ob.rotation_euler = rot
    if parent:
        ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0)):
    if len(loc) == 2:
        loc = (loc[0], loc[1], 0)
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.5
    e.location = loc; e.rotation_euler = rot
    bpy.context.scene.collection.objects.link(e)
    return e


def parent_all(objs, par):
    for o in objs:
        o.parent = par
    return objs


def text_obj(name, body, size, loc=(0, 0, 0), rot=(math.pi / 2, 0, 0),
             mat=None, extrude=0.012, bevel=0.002, align='CENTER', parent=None,
             spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.space_character = spacing
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    if mat:
        cu.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def curve_tube(name, points, radius=0.02, mat=None, parent=None,
               resolution=2, cyclic=False, radii=None):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = resolution
    cu.resolution_u = 6
    cu.fill_mode = 'FULL'
    sp = cu.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (p[0], p[1], p[2], 1)
        if radii is not None:
            sp.points[i].radius = radii[i]
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        cu.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def join(objs, name='joined'):
    objs = [o for o in objs if o and o.name in bpy.data.objects]
    if not objs:
        return None
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    return ob


def gable_roof(name, w, d, h, over=0.45, thick=0.16, mat=None, parent=None):
    """Ridge runs along X. Base at z=0, ridge at z=h. Closed solid with thickness."""
    wx = w / 2 + over
    wy = d / 2 + over
    verts = [
        (-wx, -wy, 0), (wx, -wy, 0), (wx, wy, 0), (-wx, wy, 0),      # eaves top A B C D
        (-wx, 0, h), (wx, 0, h),                                       # ridge E F
        (-wx, -wy, -thick), (wx, -wy, -thick), (wx, wy, -thick),
        (-wx, wy, -thick),
        (-wx, 0, h - thick), (wx, 0, h - thick),
    ]
    faces = [
        (0, 1, 5, 4), (2, 3, 4, 5),                 # slopes
        (0, 4, 3), (1, 2, 5),                       # gable ends
        (0, 1, 7, 6), (2, 3, 9, 8),                 # eave faces
        (3, 0, 6, 9), (1, 2, 8, 7),                 # gable side faces
        (0, 4, 10, 6), (4, 3, 9, 10),               # left gable thickness
        (1, 7, 11, 5), (5, 11, 8, 2),               # right gable thickness
        (6, 10, 11, 7), (8, 9, 10, 11),             # underside
    ]
    ob = mesh_obj(name, verts, faces, mat, bevel=0.02)
    ob.parent = parent
    return ob


def bez(points, t):
    # simple polyline sampling / catenary-ish
    n = len(points) - 1
    x = t * n
    i = min(int(x), n - 1)
    f = x - i
    a = Vector(points[i]); b = Vector(points[i + 1])
    return a.lerp(b, f)
