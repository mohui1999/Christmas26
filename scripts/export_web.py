"""Export a web-friendly GLB from the finished Christmas town scene."""
import bpy, os, sys, time, math
from mathutils import Color

ROOT = '/Volumes/External/Project/ClawProject/Christmas26'
OUT = os.path.join(ROOT, 'web', 'models', 'christmas_town.glb')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

t0 = time.time()
print('OPEN', flush=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'christmas_town.blend'))

# ---------------------------------------------------------------------------
# 1. drop objects that are only useful for the Cycles render
# ---------------------------------------------------------------------------
drop_names = {'mist_volume', 'sky_backdrop', 'stars', 'snowflakes'}
for o in list(bpy.data.objects):
    if o.name in drop_names or o.type in {'LIGHT', 'CAMERA'}:
        if o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)

for o in bpy.data.objects:
    o.hide_set(False)
    o.hide_render = False
    o.hide_viewport = False

# ---------------------------------------------------------------------------
# 2. decimate the needle meshes (by far the heaviest part)
# ---------------------------------------------------------------------------
needle_targets = []
for o in bpy.data.objects:
    if o.type == 'MESH' and any(m and m.name == 'needles' for m in o.data.materials):
        if len(o.data.vertices) > 60000:
            needle_targets.append(o)
print('NEEDLE_MESHES', len(needle_targets), flush=True)
for o in needle_targets:
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception as e:
            print('modifier err', o.name, e, flush=True)
    mod = o.modifiers.new('web_decimate', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = 0.16
    mod.use_collapse_triangulate = True
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as e:
        print('decimate err', o.name, e, flush=True)
print('DECIMATED', round(time.time() - t0, 1), 'verts',
      sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'), flush=True)

# ---------------------------------------------------------------------------
# 3. simplify materials for glTF (flat PBR colours + emission)
# ---------------------------------------------------------------------------
def color_nodes(node, out, seen):
    if node in seen:
        return
    seen.add(node)
    if node.type == 'VALTORGB':
        for el in node.color_ramp.elements:
            out.append(tuple(el.color))
    for inp in node.inputs:
        try:
            if inp.type == 'RGBA':
                c = tuple(inp.default_value)
                if max(c[:3]) > 0.02 and (max(c[:3]) - min(c[:3])) > 0.02:
                    out.append(c)
        except Exception:
            pass
        if getattr(inp, 'is_linked', False):
            color_nodes(inp.links[0].from_node, out, seen)


def average_color(colors):
    if not colors:
        return None
    # discard almost-black colours
    cols = [c for c in colors if max(c[:3]) > 0.04] or colors
    r = sum(c[0] for c in cols) / len(cols)
    g = sum(c[1] for c in cols) / len(cols)
    b = sum(c[2] for c in cols) / len(cols)
    return (min(1, r), min(1, g), min(1, b), 1.0)


def emission_of(nodes):
    vals = []
    for n in nodes:
        if n.type == 'EMISSION':
            vals.append((tuple(n.inputs['Color'].default_value),
                         n.inputs['Strength'].default_value))
    return vals


def to_principled(mat, color, emit=None, strength=0.0, alpha=1.0, rough=0.55, metal=0.0):
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.location = (0, 0)
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Alpha'].default_value = alpha
    if emit:
        b.inputs['Emission Color'].default_value = emit
        b.inputs['Emission Strength'].default_value = strength
    mat.diffuse_color = color


for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    nodes = list(nt.nodes)
    pr = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    ems = emission_of(nodes)
    if pr is None:
        if ems:
            c, s = ems[0]
            to_principled(m, (c[0] * .25, c[1] * .25, c[2] * .25, 1), c, min(float(s), 3.0),
                          rough=0.35)
        continue
    # name based overrides
    name = m.name
    if name == 'needles':
        to_principled(m, (0.075, 0.155, 0.095, 1), rough=0.62)
        continue
    if name.startswith('bark'):
        to_principled(m, (0.075, 0.048, 0.03, 1), rough=0.82)
        continue
    # glass / alpha
    alpha = 1.0
    try:
        alpha = float(pr.inputs['Alpha'].default_value)
    except Exception:
        pass
    # emission (windows, bulbs, signs)
    ecol = tuple(pr.inputs['Emission Color'].default_value)
    estr = float(pr.inputs['Emission Strength'].default_value)
    if name.startswith('em_') or name.startswith('wg_') or name.startswith('sign_gold') or estr > 0.01:
        emit = ems[0][0] if ems else ecol
        strength = ems[0][1] if ems else estr
        if strength < 0.05:
            strength = 1.0
        base = (emit[0] * .22, emit[1] * .22, emit[2] * .22, 1)
        to_principled(m, base, emit, min(float(strength), 3.2), alpha=alpha,
                      rough=0.25 if name.startswith('gs_') else 0.4,
                      metal=0.0)
        continue
    if name.startswith('gs_'):
        tint = tuple(pr.inputs['Base Color'].default_value)
        to_principled(m, tint, alpha=min(alpha, 0.35), rough=0.08, metal=0.0)
        continue
    if name.startswith('mt_'):
        c = tuple(pr.inputs['Base Color'].default_value)
        rough = float(pr.inputs['Roughness'].default_value)
        to_principled(m, c, rough=rough, metal=1.0)
        continue
    # general: collect colours upstream of Base Color
    bc = pr.inputs['Base Color']
    colors = []
    if bc.is_linked:
        color_nodes(bc.links[0].from_node, colors, set())
    else:
        colors.append(tuple(bc.default_value))
    c = average_color(colors)
    if c is None:
        c = tuple(bc.default_value)
    if max(c[:3]) < 0.035:
        c = (0.16, 0.16, 0.16, 1)
    rough = 0.58
    try:
        rough = float(pr.inputs['Roughness'].default_value)
        if not (0 <= rough <= 1):
            rough = 0.58
    except Exception:
        pass
    metal = 0.0
    try:
        metal = float(pr.inputs['Metallic'].default_value)
    except Exception:
        pass
    to_principled(m, c, rough=rough, metal=metal, alpha=alpha)

# ---------------------------------------------------------------------------
# 4. apply modifiers, convert curves/text, flatten hierarchy
# ---------------------------------------------------------------------------
print('CONVERT', flush=True)
for o in bpy.data.objects:
    o.select_set(o.type in {'MESH', 'CURVE', 'FONT'})
sel = [o for o in bpy.data.objects if o.type in {'MESH', 'CURVE', 'FONT'}]
if sel:
    bpy.context.view_layer.objects.active = sel[0]
    bpy.ops.object.convert(target='MESH')
print('CONVERTED', len(sel), round(time.time() - t0, 1), flush=True)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o.type == 'MESH')
if meshes:
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
# now the empty groups can safely be removed
for o in list(bpy.data.objects):
    if o.type not in {'MESH'}:
        bpy.data.objects.remove(o, do_unlink=True)
print('TRANSFORMS', round(time.time() - t0, 1), flush=True)

# ---------------------------------------------------------------------------
# 5. join everything into a single multi-material mesh
# ---------------------------------------------------------------------------
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o.type == 'MESH')
if meshes:
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = 'ChristmasTown'
print('JOINED', len(obj.data.vertices), 'verts', len(obj.data.polygons), 'faces',
      len(obj.data.materials), 'materials', round(time.time() - t0, 1), flush=True)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

# ---------------------------------------------------------------------------
# 6. export
# ---------------------------------------------------------------------------
for p in bpy.context.scene.objects:
    p.select_set(p == obj)
print('EXPORT', flush=True)
kwargs = dict(
    filepath=OUT,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_texcoords=False,
    export_normals=True,
    export_materials='EXPORT',
    export_cameras=False,
    export_lights=False,
    export_animations=False,
)
try:
    bpy.ops.export_scene.gltf(export_draco_mesh_compression_enable=True,
                              export_draco_mesh_compression_level=6, **kwargs)
except Exception as e:
    print('DRACO FAILED', e, flush=True)
    bpy.ops.export_scene.gltf(**kwargs)

print('DONE', round(time.time() - t0, 1), 'size_mb', round(os.path.getsize(OUT) / 1e6, 2), flush=True)
