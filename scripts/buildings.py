"""Procedural European Christmas village architecture."""
import bpy, math, random
from mathutils import Vector, Matrix
from lib import (box, cylinder, cone, sphere, ico, empty, join, curve_tube,
                 text_obj, mesh_obj, gable_roof, plaster, stone, wood, roofmat,
                 metal, gloss, fabric, emission, window_glow, glass, snowmat,
                 tile, PI, TAU, RNG, lin, parent_all)
import props
from vegetation import conifer

SNOW = snowmat()
IRON = metal('iron_black', '#14171c', 0.34)
GOLD = metal('gold', '#e8b25c', 0.22)
GOLD_DARK = metal('gold_dark', '#b8863f', 0.3)
WOOD_DARK = wood('wood_dark', '#3a2a1e', 0.62)
WOOD_MID = wood('wood_mid', '#6b4a30', 0.6)
WOOD_WARM = wood('wood_warm', '#8a5a34', 0.55)
STONE_TRIM = stone('stone_trim', '#b7ad9c', 0.55)
STONE_DARK = stone('stone_dark', '#6f675b', 0.62)
STONE_LIGHT = stone('stone_light', '#c9c0ae', 0.5)
IVORY = plaster('ivory', '#efe5d2', 0.82)
CREAM = plaster('cream', '#e6dcc8', 0.84)
SIGN_BOARD = wood('sign_board', '#243b2c', 0.6)
SIGN_GOLD = emission('sign_gold', '#ffd28a', 1.8)
WIN_GREEN = wood('win_green', '#33472f', 0.55)
WIN_BROWN = wood('win_brown', '#5a3d28', 0.55)
WIN_PALE = gloss('win_pale', '#d9d2c2', 0.42, 0.0, 0.3)
WIN_BLUE = gloss('win_bluegrey', '#7f919c', 0.45, 0.0, 0.3)


def brickmat(name, hexcol):
    key = 'brick_' + name
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
    br = nt.nodes.new('ShaderNodeTexBrick'); br.location = (-480, 60)
    br.inputs['Scale'].default_value = 8.0
    br.inputs['Mortar Size'].default_value = 0.02
    br.inputs['Brick Width'].default_value = 0.45
    br.inputs['Row Height'].default_value = 0.22
    br.inputs['Color1'].default_value = lin(hexcol)
    br.inputs['Color2'].default_value = lin('#b6a08e')
    br.inputs['Mortar'].default_value = lin('#d8cdb8')
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.82
    bump = nt.nodes.new('ShaderNodeBump'); bump.location = (100, -180)
    bump.inputs['Strength'].default_value = 0.5
    nt.links.new(br.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
# facade elements
# --------------------------------------------------------------------------- #
def _panel(name, pts, y, thick, mat, parent):
    """Extruded 2D polygon (x,z) along y."""
    n = len(pts)
    V = []
    for yy in (y - thick / 2, y + thick / 2):
        for (x, z) in pts:
            V.append((x, yy, z))
    F = []
    F.append(tuple(range(n - 1, -1, -1)))
    F.append(tuple(range(n, 2 * n)))
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    ob = mesh_obj(name, V, F, mat, bevel=0.0)
    ob.parent = parent
    return ob


def arch_pts(w, h_rect, segs=14):
    z0 = -(h_rect + w / 2) / 2
    pts = [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h_rect)]
    for i in range(1, segs + 1):
        a = PI * i / segs
        pts.append((math.cos(a) * w / 2, z0 + h_rect + math.sin(a) * w / 2))
    return pts


def pointed_pts(w, h_base, apex, segs=10):
    H = h_base + apex
    z0 = -H / 2
    pts = [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h_base)]
    for i in range(1, segs + 1):
        t = i / segs
        x = w / 2 * (1 - t)
        z = z0 + h_base + apex * (1 - (1 - t) ** 1.8)
        pts.append((x, z))
    for i in range(1, segs):
        t = 1 - i / segs
        x = -w / 2 * (1 - t)
        z = z0 + h_base + apex * (1 - (1 - t) ** 1.8)
        pts.append((x, z))
    return pts


def add_window(parent, pos, yaw=0.0, w=1.1, h=1.4, depth=0.08, lit=True,
               arch=False, pointed=False, shutters=None, flowerbox=False,
               sill_mat=None, name='window', dark_frame=None, frame_mat=None):
    e = empty(name, pos, (0, 0, yaw))
    e.parent = parent
    trim = stone('window_trim', '#d6cbb6', 0.55) if dark_frame is None else dark_frame
    if frame_mat is not None:
        trim = frame_mat
    if sill_mat is None:
        sill_mat = trim
    warm = window_glow('window_warm', '#ffa348', 1.55)
    warm2 = window_glow('window_warm2', '#ffb35e', 1.2)
    darkglass = glass('glass_dark', '#16202c', 0.55)
    clear = glass('window_glass', '#b8d2e4', 0.22)
    curtain_m = fabric('curtain_warm', '#5b3a26', 0.92, 0.2)
    if arch:
        h_rect = h - w / 2
        pts = arch_pts(w, h_rect)
        H = h
    elif pointed:
        h_rect = h * 0.6
        apex = h * 0.4
        pts = pointed_pts(w, h_rect, apex)
        H = h
    else:
        pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        H = h
    # glow backing (just proud of wall)
    _panel(name + '_glow', pts, -0.005, 0.012, warm if lit else darkglass, e)
    # bay reveal
    rev = -depth / 2
    box(name + '_revl', 0.07, depth, H, (-w / 2 + 0.035, rev, 0), WOOD_DARK, 0.005, parent=e)
    box(name + '_revr', 0.07, depth, H, (w / 2 - 0.035, rev, 0), WOOD_DARK, 0.005, parent=e)
    box(name + '_revt', w, depth, 0.07, (0, rev, H / 2 - 0.035), WOOD_DARK, 0.005, parent=e)
    # shelf / lower reveal
    box(name + '_shelf', w - 0.02, depth, 0.07, (0, rev, -H / 2 + 0.035), WOOD_DARK, 0.005, parent=e)
    # glass
    _panel(name + '_glass', pts, -depth - 0.004, 0.004, clear, e)
    # outer frame
    fw = 0.1
    box(name + '_fl', fw, 0.16, H + fw * 2, (-w / 2 - fw / 2, -depth - 0.03, 0), trim, 0.012, parent=e)
    box(name + '_fr', fw, 0.16, H + fw * 2, (w / 2 + fw / 2, -depth - 0.03, 0), trim, 0.012, parent=e)
    if not arch and not pointed:
        box(name + '_fb', w + fw * 2, 0.16, fw, (0, -depth - 0.03, -H / 2 - fw / 2), trim, 0.012, parent=e)
        box(name + '_ft', w + fw * 2, 0.16, fw, (0, -depth - 0.03, H / 2 + fw / 2), trim, 0.012, parent=e)
    else:
        if arch:
            radio = w / 2 + 0.05
            ptsa = [(math.cos(a) * radio, H / 2 - w / 2 + math.sin(a) * radio)
                    for a in [PI * i / 16 for i in range(17)]]
        else:
            ptsa = [(x, z + (0.04 if z > 0 else 0)) for (x, z) in pts[4:]]
            # remove base points
        curve_tube(name + '_arch', [(x, -depth - 0.03, z) for (x, z) in ptsa],
                   0.055, trim, parent=e)
        box(name + '_fb', w + fw * 2, 0.16, fw, (0, -depth - 0.03, -H / 2 - fw / 2), trim, 0.012, parent=e)
    # curtains inside the reveal
    for side in (-1, 1):
        box(name + '_curtain', 0.17, 0.02, H * 0.8,
            (side * (w / 2 - 0.11), -depth + 0.02, 0), curtain_m, 0.004, parent=e)
    # mullions
    box(name + '_mv', 0.04, 0.05, H - 0.08, (0, -depth - 0.02, 0), WOOD_DARK, 0.004, parent=e)
    box(name + '_mh', w - 0.08, 0.05, 0.04, (0, -depth - 0.02, -H / 2 + h * 0.42), WOOD_DARK, 0.004, parent=e)
    if not arch and not pointed and w > 0.8:
        # little pendant lamp silhouette
        cylinder(name + '_cord', 0.006, 0.28, (0, -depth + 0.07, H / 2 - 0.2), WOOD_DARK, 5, parent=e)
        cone(name + '_shade', 0.13, 0.03, 0.14, (0, -depth + 0.07, H / 2 - 0.37), WOOD_DARK, 10, parent=e)
        sphere(name + '_bulb', 0.045, (0, -depth + 0.07, H / 2 - 0.45),
               emission('pendant_bulb', '#ffc27a', 3.0), 8, 6, parent=e)
    # sill
    sill = box(name + '_sill', w + 0.32, depth + 0.3, 0.09,
               (0, -depth / 2 - 0.06, -H / 2 - fw - 0.03), sill_mat, 0.012, parent=e)
    # snow on sill and top frame
    for i in range(3):
        ico(name + '_snow', RNG.uniform(0.1, 0.19),
            (-w * 0.3 + i * w * 0.3, -depth / 2 - 0.08, -H / 2 - fw + 0.02),
            SNOW, 1, (1.4, 0.8, 0.25), parent=e, jitter=0.25)
    if not arch and not pointed:
        ico(name + '_snowtop', 0.15, (0, -depth - 0.04, H / 2 + fw + 0.02), SNOW, 1,
            (max(1.0, w / 0.32), 0.7, 0.22), parent=e, jitter=0.2)
    if shutters:
        for side in (-1, 1):
            sh = box(name + '_shutter', 0.38, 0.05, H + 0.06,
                     (side * (w / 2 + 0.26), -0.05, 0), shutters, 0.012, parent=e)
            box(name + '_shin', 0.28, 0.02, H * 0.4, (side * (w / 2 + 0.26), -0.085, H * 0.2),
                shutters, 0.004, parent=e)
            box(name + '_shin', 0.28, 0.02, H * 0.4, (side * (w / 2 + 0.26), -0.085, -H * 0.2),
                shutters, 0.004, parent=e)
            for i in range(2):
                ico(name + '_shsnow', 0.12, (side * (w / 2 + 0.26) + RNG.uniform(-0.1, 0.1),
                                             -0.05, H / 2 + 0.03), SNOW, 1, (1.2, 0.7, 0.25),
                    parent=e, jitter=0.25)
    if flowerbox:
        box(name + '_fbox', w * 0.95, 0.26, 0.22, (0, -depth - 0.2, -H / 2 - 0.2),
            WOOD_WARM, 0.015, parent=e)
        for i in range(4):
            ico(name + '_flw', 0.1, (-w * 0.35 + i * w * 0.23, -depth - 0.2, -H / 2 - 0.1),
                plaster('flower_green', '#2c4430', 0.8, 0.3), 1, (1, 1, 1), parent=e, jitter=0.2)
        ico(name + '_fbsnow', 0.14, (0, -depth - 0.2, -H / 2 - 0.06), SNOW, 1, (2.4, 0.8, 0.2),
            parent=e, jitter=0.2)
    return e


def add_door(parent, x, y, z0, w=1.2, h=2.3, door_mat=None, frame_mat=None,
             arched=False, double=False, wreath_on=True, lamps=True, name='door'):
    if door_mat is None:
        door_mat = WOOD_DARK
    if frame_mat is None:
        frame_mat = STONE_TRIM
    e = empty(name, (x, y, z0 + h / 2), (0, 0, 0))
    e.parent = parent
    # recess / dark reveal
    box(name + '_rec', w + 0.12, 0.12, h + 0.1, (0, 0.03, 0), wood('door_rec', '#211810', 0.8), 0.005, parent=e)
    # panel
    box(name + '_leaf', w, 0.09, h, (0, -0.02, 0), door_mat, 0.012, parent=e)
    for i in range(2):
        box(name + '_panel', w * 0.34, 0.025, h * 0.3,
            (-w * 0.2 + i * w * 0.4, -0.075, h * 0.16), door_mat, 0.006, parent=e)
        box(name + '_panel', w * 0.34, 0.025, h * 0.25,
            (-w * 0.2 + i * w * 0.4, -0.075, -h * 0.2), door_mat, 0.006, parent=e)
    # frame
    box(name + '_frame_l', 0.14, 0.18, h + 0.2, (-w / 2 - 0.07, -0.06, 0), frame_mat, 0.012, parent=e)
    box(name + '_frame_r', 0.14, 0.18, h + 0.2, (w / 2 + 0.07, -0.06, 0), frame_mat, 0.012, parent=e)
    box(name + '_frame_t', w + 0.28, 0.18, 0.16, (0, -0.06, h / 2 + 0.08), frame_mat, 0.012, parent=e)
    # transom
    box(name + '_trans', w * 0.7, 0.05, 0.32, (0, -0.075, h / 2 - 0.2),
        window_glow('door_glow', '#ffb35e', 1.5), 0.006, parent=e)
    # handle
    cylinder(name + '_handle', 0.033, 0.05, (w * 0.33, -0.12, -0.05), GOLD_DARK, 10,
             rot=(PI / 2, 0, 0), parent=e)
    # steps descending to the pavement
    for i in range(3):
        box(name + '_step', w + 0.8 + i * 0.32, 0.55, 0.16,
            (0, -0.3 - i * 0.2, -h / 2 - 0.1 - i * 0.15), STONE_LIGHT, 0.015, parent=e)
        for k in range(3):
            ico(name + '_stepsnow', 0.12, (-w * 0.35 + k * w * 0.35, -0.3 - i * 0.2,
                                           -h / 2 + 0.0 - i * 0.15), SNOW, 1, (1.5, 0.7, 0.2),
                parent=e, jitter=0.2)
    if wreath_on:
        props.wreath((0, -0.14, 0.15), 0.3, rot=(PI / 2, 0, 0), parent=e)
    if lamps:
        for side in (-1, 1):
            add_wall_lamp(e, side * (w / 2 + 0.32), -0.02, 0.15)
    return e


def add_wall_lamp(parent, x, y, z):
    e = empty('wall_lamp', (x, y, z), (0, 0, 0))
    e.parent = parent
    box('wl_arm', 0.05, 0.3, 0.05, (0, -0.15, 0), IRON, 0.005, parent=e)
    box('wl_body', 0.15, 0.15, 0.22, (0, -0.3, -0.14), emission('wall_glow', '#ffb35e', 2.2), 0.01, parent=e)
    box('wl_top', 0.2, 0.2, 0.03, (0, -0.3, -0.01), IRON, 0.004, parent=e)
    cone('wl_roof', 0.13, 0.0, 0.12, (0, -0.3, 0.06), IRON, 4, parent=e)
    return e


def add_sign(parent, text, x, z, y, width=3.0, height=0.5, board_mat=None,
             letter_mat=None, name='sign'):
    if board_mat is None:
        board_mat = SIGN_BOARD
    if letter_mat is None:
        letter_mat = SIGN_GOLD
    e = empty(name, (x, y, z), (0, 0, 0))
    e.parent = parent
    box(name + '_board', width, 0.08, height, (0, 0, 0), board_mat, 0.02, parent=e)
    for sx in (-1, 1):
        box(name + '_trim', 0.045, 0.1, height + 0.05, (sx * (width / 2), -0.005, 0), GOLD_DARK, 0.006, parent=e)
    for sz in (-1, 1):
        box(name + '_trim', width + 0.05, 0.1, 0.045, (0, -0.005, sz * height / 2), GOLD_DARK, 0.006, parent=e)
    size = min(0.4, width * 0.8 / max(4, len(text)) * 1.55)
    t = text_obj(name + '_text', text, size, (0, -0.07, 0.005), (PI / 2, 0, 0),
                 letter_mat, 0.012, 0.002, parent=e)
    # tiny snow on top
    for i in range(4):
        ico(name + '_snow', RNG.uniform(0.07, 0.15), (-width * 0.35 + i * width * 0.23, 0, height / 2 + 0.02),
            SNOW, 1, (1.5, 0.6, 0.2), parent=e, jitter=0.25)
    return e


def awning(parent, x, y_wall, z, width, depth, mat_a, mat_b, name='awning', drop=0.42):
    e = empty(name, (x, y_wall, z), (0, 0, 0))
    e.parent = parent
    nx, ny = 16, 5
    V = []
    for j in range(ny + 1):
        v = j / ny
        for i in range(nx + 1):
            u = i / nx
            yy = -depth * v
            zz = -drop * v + 0.06 * math.sin(PI * u) * (1 - v * 0.6)
            V.append(((-0.5 + u) * width, yy, zz))
    F = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new(name + '_mesh')
    me.from_pydata(V, [], F); me.update()
    ob = bpy.data.objects.new(name + '_mesh', me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat_a); me.materials.append(mat_b)
    for p in me.polygons:
        p.material_index = int(round(((p.center.x / width) + 0.5) * 8)) % 2
    mod = ob.modifiers.new('sol', 'SOLIDIFY'); mod.thickness = 0.022
    ob.parent = e
    # front valance
    for i in range(8):
        xx = (-0.5 + (i + 0.5) / 8) * width
        m = mat_a if i % 2 == 0 else mat_b
        box(name + '_val', width / 8 + 0.005, 0.02, 0.18,
            (xx, -depth + 0.01, -drop - 0.09 + 0.02 * math.sin(PI * (i + 0.5) / 8)),
            m, 0.004, parent=e)
    # snow on top near wall
    for i in range(4):
        ico(name + '_snow', 0.13, (-width * 0.35 + i * width * 0.23, -0.12, 0.04),
            SNOW, 1, (1.6, 0.7, 0.2), parent=e, jitter=0.25)
    return e


# --------------------------------------------------------------------------- #
# snow
# --------------------------------------------------------------------------- #
def snow_slope(parent, width, wy, rh, front=True, zbase=0.0):
    alpha = math.atan2(rh, wy)
    L = math.hypot(wy, rh)
    nx, ny = 14, 7
    V, F = [], []
    for side in (0, 1):  # top/bottom
        off = 0.0 if side == 0 else -0.11
        for j in range(ny + 1):
            v = j / ny
            for i in range(nx + 1):
                u = i / nx
                x = (u - 0.5) * (width + 0.06)
                y = (v - 0.5) * (L + 0.04)
                n = math.sin(u * 9.1 + 1.3) * math.cos(v * 6.2 + 0.7) * 0.018
                edge = math.sin(PI * u) * math.sin(PI * v)
                V.append((x, y, off + n * (0.4 + edge)))
    def idx(side, j, i):
        return side * (nx + 1) * (ny + 1) + j * (nx + 1) + i
    for j in range(ny):
        for i in range(nx):
            F.append((idx(0, j, i), idx(0, j, i + 1), idx(0, j + 1, i + 1), idx(0, j + 1, i)))
            F.append((idx(1, j, i), idx(1, j + 1, i), idx(1, j + 1, i + 1), idx(1, j, i + 1)))
    for i in range(nx):
        F.append((idx(0, 0, i), idx(1, 0, i), idx(1, 0, i + 1), idx(0, 0, i + 1)))
        F.append((idx(0, ny, i), idx(0, ny, i + 1), idx(1, ny, i + 1), idx(1, ny, i)))
    for j in range(ny):
        F.append((idx(0, j, 0), idx(0, j + 1, 0), idx(1, j + 1, 0), idx(1, j, 0)))
        F.append((idx(0, j, nx), idx(1, j, nx), idx(1, j + 1, nx), idx(0, j + 1, nx)))
    me = bpy.data.meshes.new('roofsnow')
    me.from_pydata(V, [], F); me.update()
    ob = bpy.data.objects.new('roofsnow', me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(SNOW)
    ob.parent = parent
    if front:
        ob.rotation_euler = (alpha, 0, 0)
        ob.location = (0, -wy / 2, zbase + rh / 2 + 0.09)
    else:
        ob.rotation_euler = (-alpha, 0, 0)
        ob.location = (0, wy / 2, zbase + rh / 2 + 0.09)
    return ob


def roof_snow(parent, w, d, rh, over=0.5, zbase=0.0):
    wy = d / 2 + over
    wx = w / 2 + over
    a = snow_slope(parent, wx * 2, wy, rh, True, zbase)
    b = snow_slope(parent, wx * 2, wy, rh, False, zbase)
    # icicles + eave snow lumps
    for sx in (-1, 1):
        for i in range(10):
            xx = -wx * 0.94 + i * wx * 1.88 / 9
            ico('eavesnow', RNG.uniform(0.11, 0.22), (xx, sx * (wy - 0.03), zbase + RNG.uniform(0.0, 0.1)),
                SNOW, 1, (RNG.uniform(1.4, 2.0), RNG.uniform(0.6, 0.9), RNG.uniform(0.22, 0.4)),
                parent=parent, jitter=0.3)
            if i % 2 == 0 and abs(xx) < w / 2:
                props.icicle((xx, sx * (wy + 0.02), zbase - 0.06), RNG.uniform(0.25, 0.6),
                             parent=parent)
    # fascia and gutter outline the roof, exposing a dark eave under the snow
    for sy in (-1, 1):
        box('fascia', wx * 2 + 0.05, 0.16, 0.28, (0, sy * (wy - 0.02), zbase - 0.1),
            WOOD_DARK, 0.01, parent=parent)
        box('gutter', wx * 2 + 0.05, 0.1, 0.1, (0, sy * (wy + 0.06), zbase + 0.02),
            IRON, 0.005, parent=parent)
    # ridge snow
    for i in range(7):
        xx = -wx * 0.8 + i * wx * 1.6 / 6
        ico('ridgesnow', RNG.uniform(0.14, 0.26), (xx, 0, zbase + rh + 0.06), SNOW, 1,
            (1.4, 1.1, 0.32), parent=parent, jitter=0.25)
    return a, b


def dormer(parent, x, y, z, wall, roofm, w=1.15, h=1.15, dd=1.05):
    e = empty('dormer', (x, y, z), (0, 0, 0))
    e.parent = parent
    box('dormer_body', w, dd, h, (0, 0, h / 2), wall, 0.02, parent=e)
    roof = gable_roof('dormer_roof', w, dd, 0.55, 0.16, 0.1, roofm)
    roof.location = (0, 0, h)
    roof.parent = e
    ico('dormer_snow', 0.42, (0, 0, h + 0.56), SNOW, 2, (1.15, 1.0, 0.28), parent=e, jitter=0.22)
    add_window(e, (0, -dd / 2 - 0.02, h * 0.54), 0, 0.52, 0.7, 0.04, True,
               name='dormer_win')
    box('dormer_ledge', w + 0.14, 0.16, 0.06, (0, -dd / 2 - 0.05, h * 0.54 - 0.4), STONE_TRIM, 0.008, parent=e)
    for i in range(2):
        ico('dormer_ic', 0.05, (-w * 0.3 + i * w * 0.55, -dd / 2 - 0.05, h * 0.54 - 0.47),
            SNOW, 1, (0.8, 0.8, 0.4), parent=e, jitter=0.2)
    return e


def chimney(parent, x, y, z, h=1.5, mat=None):
    if mat is None:
        mat = brickmat('chimney', '#8a5a4a')
    box('chimney', 0.48, 0.48, h, (x, y, z + h / 2), mat, 0.02, parent=parent)
    box('chimney_cap', 0.62, 0.62, 0.1, (x, y, z + h + 0.03), STONE_DARK, 0.015, parent=parent)
    ico('chimney_snow', 0.3, (x, y, z + h + 0.12), SNOW, 2, (1, 1, 0.4),
        parent=parent, jitter=0.25)


def garland(parent, p0, p1, sag=0.22, tufts=16, name='garland', berries=True,
            bulbs=True, scale=1.0):
    p0 = Vector(p0); p1 = Vector(p1)
    pts = []
    for i in range(17):
        t = i / 16
        p = p0.lerp(p1, t)
        p.z -= math.sin(PI * t) * sag
        pts.append(p)
    curve_tube(name + '_rope', pts, 0.035 * scale, plaster('garland_rope', '#223a2a', 0.9, 0.2),
               parent=parent)
    objs = []
    green = plaster('garland_green', '#2c4a33', 0.88, 0.35)
    for i in range(tufts):
        t = i / (tufts - 1)
        p = p0.lerp(p1, t)
        p.z -= math.sin(PI * t) * sag
        for k in range(3):
            a = RNG.uniform(0, TAU)
            L = RNG.uniform(0.16, 0.28) * scale
            objs.append(cone('tuft', 0.06 * scale, 0.0, L,
                             (p.x + math.cos(a) * 0.06, p.y - 0.05,
                              p.z - 0.02 - L * 0.35),
                             green, 5,
                             rot=(math.sin(a) * 1.1, -math.cos(a) * 1.1, RNG.uniform(0, TAU)),
                             parent=parent))
        if berries:
            for k in range(2):
                objs.append(sphere('berry', 0.028, (p.x + RNG.uniform(-0.1, 0.1),
                                                  p.y - 0.1, p.z - RNG.uniform(0, 0.1)),
                                   gloss('berry_red', '#b01824', 0.25), 8, 6, parent=parent))
        if i % 3 == 0:
            objs.append(sphere('gball', 0.035, (p.x, p.y - 0.11, p.z - 0.08), GOLD, 8, 6,
                               parent=parent))
    if bulbs:
        b = []
        nbulb = int(tufts * 1.5)
        for i in range(nbulb):
            t = (i + 0.5) / nbulb
            p = p0.lerp(p1, t)
            p.z -= math.sin(PI * t) * sag + 0.09
            b.append(sphere('gbulb', 0.017, p, emission('garland_bulb', '#ffc27a', 11.0), 6, 4))
        if b:
            for o in b:
                o.parent = parent
            join(b, name + '_bulbs')
    if objs:
        g = join(objs, name + '_tufts')
        g.parent = parent
    return


# --------------------------------------------------------------------------- #
# shop displays
# --------------------------------------------------------------------------- #
def cake_display(win):
    # win is window empty local coords
    plate = cylinder('cake_plate', 0.34, 0.05, (0.0, -0.13, -0.4), gloss('porcelain', '#f4efe4', 0.16, coat=0.6), 20, parent=win)
    cylinder('cake_stand', 0.06, 0.22, (0, -0.13, -0.26), GOLD, 10, parent=win)
    cylinder('cake_tier', 0.28, 0.12, (0, -0.13, -0.12), gloss('cake_cream', '#f6e3d2', 0.5), 24, parent=win)
    cylinder('cake_tier2', 0.2, 0.1, (0, -0.13, 0.0), gloss('cake_pink', '#efc3bf', 0.5), 24, parent=win)
    for i in range(7):
        a = i / 7 * TAU
        sphere('strawberry', 0.045, (math.cos(a) * 0.2, -0.13 + math.sin(a) * 0.2, 0.03),
               gloss('strawberry', '#c81f2c', 0.28), 8, 6, parent=win)
    for i in range(4):
        x = -0.45 + i * 0.3
        cylinder('cupcake', 0.09, 0.13, (x, -0.1, -0.42), gloss('cupcake_wrap', '#b0573c', 0.6), 12, parent=win)
        sphere('frosting', 0.1, (x, -0.1, -0.32), gloss('frosting', '#f3ddd0', 0.5), 10, 7, (1, 1, 0.7), parent=win)
    # gingerbread house
    box('ginger_house', 0.26, 0.2, 0.2, (0.55, -0.1, -0.34),
        gloss('ginger', '#8a4a22', 0.6), 0.01, parent=win)
    cone('ginger_roof', 0.19, 0.19, 0.1, (0.55, -0.1, -0.2),
         gloss('ginger_roof', '#a33b2a', 0.5), 4, rot=(0, 0, PI / 4), parent=win)


def bread_display(win):
    for i in range(4):
        x = -0.55 + i * 0.33
        sphere('loaf', 0.15, (x, -0.1, -0.42), gloss('bread', '#b9793f', 0.55), 14, 8,
               (1.4, 0.7, 0.65), parent=win)
        for k in range(3):
            sphere('loaf2', 0.08, (x - 0.1 + k * 0.1, -0.1, -0.28), gloss('bread2', '#c98c4d', 0.5),
                   10, 6, (1.6, 0.7, 0.6), parent=win)
    for i in range(3):
        cylinder('baguette', 0.035, 0.8, (-0.3 + i * 0.3, -0.08, -0.1),
                 gloss('baguette', '#c68b4e', 0.55), 8, rot=(0, 1.2, 0.3), parent=win)


def coffee_display(win):
    box('counter', 1.6, 0.18, 0.5, (0, -0.1, -0.45), WOOD_MID, 0.01, parent=win)
    box('machine', 0.38, 0.28, 0.42, (-0.25, -0.1, -0.2), gloss('espresso', '#2b3036', 0.25, 0.6, 0.4), 0.02, parent=win)
    cylinder('portafilter', 0.06, 0.12, (-0.25, -0.26, -0.38), metal('steel', '#aeb6bd', 0.2), 8, parent=win)
    for i in range(6):
        cylinder('cup', 0.055, 0.09, (0.35 + (i % 3) * 0.1, -0.12, -0.14 + (i // 3) * 0.14),
                 gloss('cup_white', '#efe9dd', 0.3), 10, parent=win)
    for i in range(3):
        cylinder('shelf_cup', 0.05, 0.08, (-0.5 + i * 0.15, -0.12, 0.1), gloss('cup2', '#d9c8b2', 0.4),
                 10, parent=win)


def fruit_crates(parent, y_front, x0, n=3):
    for i in range(n):
        x = x0 + i * 0.85
        box('crate', 0.55, 0.4, 0.26, (x, y_front - 0.55, 0.62), WOOD_MID, 0.015, parent=parent)
        box('crate2', 0.55, 0.4, 0.26, (x, y_front - 0.55, 0.95), WOOD_WARM, 0.015, parent=parent)
        for k in range(9):
            colors = ['#b31b26', '#e08a2b', '#e5c235', '#9db83a', '#7d2b3f']
            c = colors[(i + k) % len(colors)]
            sphere('fruit', 0.075, (x - 0.18 + (k % 3) * 0.18, y_front - 0.68 + (k // 3) * 0.13,
                                    0.78 + (i % 2) * 0.02),
                   gloss('fruit_' + c, c, 0.3), 10, 7, parent=parent)
    # basket
    cylinder('basket', 0.3, 0.22, (x0 + n * 0.85, y_front - 0.55, 0.6),
             plaster('wicker', '#8a663c', 0.8, 0.3), 16, parent=parent)
    for k in range(5):
        sphere('fruit2', 0.07, (x0 + n * 0.85 - 0.15 + (k % 3) * 0.14, y_front - 0.62 + (k // 3) * 0.12, 0.75),
               gloss('fruit_orange', '#d97a20', 0.3), 8, 6, parent=parent)


def market_shelves(win):
    for i in range(3):
        box('shelf', 1.7, 0.12, 0.05, (0, -0.12, -0.4 + i * 0.25), WOOD_WARM, 0.01, parent=win)
        for k in range(7):
            c = ['#c94b4b', '#4b7ac9', '#d9b44a', '#62a06a', '#c97a4b'][(i + k) % 5]
            box('product', 0.12, 0.08, 0.16, (-0.72 + k * 0.22, -0.12, -0.32 + i * 0.25),
                gloss('prod_' + c, c, 0.35), 0.008, parent=win)


def pizza_oven(win):
    base = cylinder('oven_base', 0.44, 0.55, (0, -0.13, -0.42), brickmat('oven_brick', '#7d4235'), 16, parent=win)
    base.scale = (1, 0.38, 1)
    dome = sphere('oven_dome', 0.45, (0, -0.13, -0.16), brickmat('oven_brick', '#7d4235'), 18, 10,
                  (1, 1, 0.72), parent=win)
    dome.scale = (1, 0.38, 0.72)
    box('oven_mouth', 0.3, 0.03, 0.24, (0, -0.27, -0.36), emission('oven_fire', '#ff7a24', 3.0), 0.01, parent=win)
    for i in range(3):
        box('pizza_peel', 0.5, 0.16, 0.02, (0.3 + i * 0.05, -0.18, -0.38 + i * 0.1), WOOD_WARM, 0.0, parent=win)


def table_chair(parent, x, y, yaw=0.0):
    e = empty('cafe_set', (x, y, 0), (0, 0, yaw))
    e.parent = parent
    cylinder('table_top', 0.4, 0.05, (0, 0, 0.78), WOOD_WARM, 20, parent=e)
    cylinder('table_leg', 0.05, 0.75, (0, 0, 0.4), IRON, 10, parent=e)
    cylinder('table_base', 0.25, 0.04, (0, 0, 0.03), IRON, 16, parent=e)
    for k in range(2):
        cx = -0.75 if k == 0 else 0.75
        chair = empty('chair', (cx, 0, 0), (0, 0, 0))
        chair.parent = e
        box('seat', 0.4, 0.4, 0.05, (0, 0, 0.5), WOOD_MID, 0.01, parent=chair)
        box('back', 0.4, 0.05, 0.45, (0, 0.19, 0.73), WOOD_MID, 0.01, parent=chair)
        for sx in (-1, 1):
            for sy in (-1, 1):
                box('leg', 0.035, 0.035, 0.5, (sx * 0.16, sy * 0.16, 0.25), IRON, 0.005, parent=chair)
    cylinder('cup', 0.05, 0.08, (0.1, 0.1, 0.84), gloss('cup_white', '#efe9dd', 0.3), 10, parent=e)
    return e


# --------------------------------------------------------------------------- #
# generic shop
# --------------------------------------------------------------------------- #
def shop(cfg):
    e = empty(cfg['name'], cfg['pos'], (0, 0, math.radians(cfg.get('yaw', 0))))
    w, d, h = cfg['w'], cfg['d'], cfg['h']
    wall = cfg['wall']
    trim = cfg.get('trim', IVORY)
    roofm = cfg['roof']
    shutters = cfg.get('shutters')
    win_frame = cfg.get('win_frame')
    rh = cfg.get('roof_h', 2.15)
    sign_z = cfg.get('sign_z', 3.2)
    # sidewalk + foundation
    box('walk', w + 1.2, 1.6, 0.12, (0, -d / 2 - 0.8, 0.06), tile('walk_stone', '#a8a091', 0.5), 0.015, parent=e)
    box('foundation', w + 0.22, d + 0.22, 0.5, (0, 0, 0.25), STONE_DARK, 0.02, parent=e)
    # body
    box('body', w, d, h, (0, 0, 0.5 + h / 2), wall, 0.04, parent=e)
    # corner quoins
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('quoin', 0.2, 0.2, h, (sx * w / 2, sy * d / 2, 0.5 + h / 2), STONE_LIGHT, 0.01, parent=e)
    # floor band + top cornice
    box('band', w + 0.16, d + 0.16, 0.14, (0, 0, 3.55), trim, 0.02, parent=e)
    box('cornice', w + 0.3, d + 0.3, 0.22, (0, 0, 0.5 + h - 0.11), trim, 0.025, parent=e)
    box('cornice2', w + 0.18, d + 0.18, 0.1, (0, 0, 0.5 + h - 0.3), trim, 0.015, parent=e)
    # roof
    roof = gable_roof('roof', w, d, rh, 0.5, 0.2, roofm)
    roof.location = (0, 0, 0.5 + h)
    roof.parent = e
    roof_snow(e, w, d, rh, over=0.5, zbase=0.5 + h)
    box('ridgecap', w + 1.0, 0.16, 0.1, (0, 0, 0.5 + h + rh + 0.04), roofm, 0.015, parent=e)
    chimney(e, w * 0.28, d * 0.16, 0.5 + h + rh * 0.4, cfg.get('chimney_h', 1.35))
    if cfg.get('dormer', True):
        dy = -(d * 0.24)
        dy_front = dy - 0.55
        zb = 0.5 + h + rh * (1 - abs(dy_front) / (d / 2 + 0.5)) - 0.18
        dormer(e, w * 0.18, dy, zb, wall, roofm)
    # upper windows
    n_up = cfg.get('upper', 3)
    z_up = 5.35
    xs = [(-w / 2 + (i + 1) * w / (n_up + 1)) for i in range(n_up)]
    for i, xx in enumerate(xs):
        add_window(e, (xx, -d / 2 - 0.02, z_up), 0, 1.0, 1.35, 0.07,
                   lit=(i % 3 != 1), shutters=shutters, flowerbox=(i % 2 == 0),
                   sill_mat=trim, name='upwin', frame_mat=win_frame)
    # ground floor
    door_x = cfg.get('door_x', 0)
    door_w = cfg.get('door_w', 1.2)
    door = add_door(e, door_x, -d / 2 - 0.02, 0.52, door_w, cfg.get('door_h', 2.3),
                    door_mat=cfg.get('door_mat', WOOD_DARK),
                    frame_mat=cfg.get('frame_mat', STONE_TRIM),
                    arched=cfg.get('arch_door', False),
                    wreath_on=cfg.get('wreath', True))
    disp = cfg.get('display')
    if disp:
        dx, dw, dh, arch = disp
        win = add_window(e, (dx, -d / 2 - 0.02, 2.05), 0, dw, dh, 0.3, True,
                         arch=arch, sill_mat=trim, name='displaywin', dark_frame=WOOD_DARK)
        cfg['display_win'] = win
    # sign
    add_sign(e, cfg['sign'], cfg.get('sign_x', door_x), sign_z, -d / 2 - 0.16,
             cfg.get('sign_w', 3.0), 0.5, cfg.get('sign_board'), cfg.get('sign_letter'))
    # side-mounted signs so the shop stays legible from the square
    for side in (-1, 1):
        se = empty('sidesign_pivot', (side * (w / 2 + 0.015), -d / 2 + 1.35, 3.18),
                   (0, 0, side * PI / 2))
        se.parent = e
        add_sign(se, cfg['sign'], 0, 0, 0, 2.3, 0.42,
                 cfg.get('sign_board'), cfg.get('sign_letter'), name='sidesign')
    # awning
    if cfg.get('awning'):
        aw = cfg['awning']
        awning(e, aw['x'], -d / 2 - 0.02, cfg.get('awning_z', 3.02), aw['w'], aw['d'],
               aw['mat_a'], aw['mat_b'])
    # garland / lights along the eave
    if cfg.get('garland', True):
        garland(e, (-w / 2 + 0.4, -d / 2 - 0.22, 0.5 + h - 0.28),
                (w / 2 - 0.4, -d / 2 - 0.22, 0.5 + h - 0.28), sag=0.18, tufts=cfg.get('garland_n', 14))
        props.string_lights('eavelights', (-w / 2 + 0.5, -d / 2 - 0.35, 0.5 + h - 0.45),
                            (w / 2 - 0.5, -d / 2 - 0.35, 0.5 + h - 0.45), sag=0.22, bulbs=16,
                            parent=e)
    # side windows for wings
    if cfg.get('side_windows'):
        for side in (-1, 1):
            if not cfg.get('side_windows') == 'both' and side != cfg['side_windows']:
                continue
            yaw = PI / 2 * side
            for k in range(2):
                yy = -d * 0.25 + k * d * 0.5
                add_window(e, (side * (w / 2 + 0.02), yy, 5.35), yaw, 0.9, 1.25, 0.07,
                           lit=(k == 0), shutters=shutters, name='sidewin', frame_mat=win_frame)
                add_window(e, (side * (w / 2 + 0.02), yy, 2.1), yaw, 0.9, 1.3, 0.07,
                           lit=False, name='sidewin2', frame_mat=win_frame)
    # sign wash light
    ld = bpy.data.lights.new(cfg['name'] + '_signlight', 'POINT')
    ld.energy = 90
    ld.color = (1.0, 0.66, 0.36)
    ld.shadow_soft_size = 0.35
    sl = bpy.data.objects.new(cfg['name'] + '_signlight', ld)
    bpy.context.scene.collection.objects.link(sl)
    sl.location = (cfg.get('sign_x', door_x), -d / 2 - 0.75, sign_z + 0.15)
    sl.parent = e
    # small spot washing the shopfront
    ld = bpy.data.lights.new(cfg['name'] + '_spot', 'SPOT')
    ld.energy = 55
    ld.color = (1.0, 0.7, 0.42)
    ld.spot_size = 1.15
    ld.spot_blend = 0.65
    ld.shadow_soft_size = 0.25
    sp = bpy.data.objects.new(cfg['name'] + '_spot', ld)
    bpy.context.scene.collection.objects.link(sp)
    sp.location = (cfg.get('sign_x', door_x), -d / 2 - 1.4, 3.9)
    dv = Vector((cfg.get('sign_x', door_x), -d / 2 - 0.1, 2.2)) - sp.location
    sp.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
    sp.parent = e
    # interior light
    ld = bpy.data.lights.new(cfg['name'] + '_light', 'POINT')
    ld.energy = 180
    ld.color = (1.0, 0.6, 0.28)
    ld.shadow_soft_size = 0.8
    lo = bpy.data.objects.new(cfg['name'] + '_light', ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (0, -d / 2 - 0.55, 2.2)
    lo.parent = e
    return e


def cake_shop(pos, yaw):
    e = shop(dict(
        name='cake_shop', pos=pos, yaw=yaw, w=7.2, d=6.8, h=7.3, roof_h=2.45, win_frame=IVORY,
        wall=plaster('wall_cake', '#e8c7c3', 0.86),
        trim=IVORY, roof=roofmat('roof_cake', '#3d4a55'),
        shutters=plaster('shutter_cake', '#d9b3af', 0.7),
        door_x=2.0, display=(-1.15, 3.2, 2.55, True),
        sign='CAKE SHOP', sign_w=3.1, sign_z=3.28, sign_x=2.0,
        awning=dict(x=-1.15, w=3.8, d=1.15,
                    mat_a=fabric('awning_pink', '#d98f92', 0.85),
                    mat_b=fabric('awning_cream', '#f2e6d6', 0.85)),
        side_windows='both', garland_n=16,
    ))
    cake_display(next(o for o in e.children if o.name.startswith('displaywin') and o.type == 'EMPTY'))
    for side in (-1, 1):
        tree = conifer('door_fir', (side * 1.1, -6.1, 0), 2.0, 0.5, seed=10 + side, detail=0.4, sprig_len=0.3)
        tree.parent = e
    return e


def coffee_shop(pos, yaw):
    e = shop(dict(
        name='coffee_shop', pos=pos, yaw=yaw, w=7.6, d=6.8, h=7.9, roof_h=2.55, win_frame=WIN_GREEN,
        wall=plaster('wall_coffee', '#e5dac4', 0.88),
        trim=CREAM, roof=roofmat('roof_coffee', '#3a3630'),
        shutters=plaster('shutter_coffee', '#33452f', 0.7),
        door_x=0, display=None,
        sign='COFFEE', sign_w=2.6, sign_z=3.3, sign_x=0,
        door_mat=WOOD_DARK, side_windows='both',
    ))
    # two ground windows
    for side in (-1, 1):
        win = add_window(e, (side * 2.3, -3.42, 2.05), 0, 1.9, 1.9, 0.28, True, sill_mat=CREAM,
                         name='coffee_win')
        coffee_display(win)
    table_chair(e, -3.2, -4.6, 0.3)
    table_chair(e, -1.8, -5.3, -0.2)
    # balcony
    box('balc', 4.2, 0.9, 0.12, (0, -3.9, 4.65), WOOD_MID, 0.02, parent=e)
    box('balc_rail', 4.2, 0.05, 0.05, (0, -4.3, 5.45), IRON, 0.005, parent=e)
    for i in range(13):
        box('balc_bar', 0.03, 0.03, 0.8, (-2.0 + i * 0.34, -4.3, 5.02), IRON, 0.003, parent=e)
    for i in range(3):
        ico('balc_snow', 0.16, (-1.4 + i * 1.4, -4.3, 5.52), SNOW, 1, (1.6, 0.6, 0.2), parent=e, jitter=0.25)
    # prominent sign on the balcony rail
    add_sign(e, 'COFFEE', 0, 5.12, -4.42, 2.5, 0.46, SIGN_BOARD, SIGN_GOLD, name='balcony_sign')
    # high wall sign, readable above the foreground roofs
    add_sign(e, 'COFFEE', 0, 6.68, -3.42, 2.6, 0.48, SIGN_BOARD, SIGN_GOLD, name='high_sign')
    return e


def fruit_shop(pos, yaw):
    e = shop(dict(
        name='fruit_shop', pos=pos, yaw=yaw, w=7.4, d=6.8, h=7.1, roof_h=2.05, win_frame=WIN_GREEN,
        wall=plaster('wall_fruit', '#d9d0a5', 0.87),
        trim=WOOD_WARM, roof=roofmat('roof_fruit', '#43352a'),
        shutters=plaster('shutter_fruit', '#4b5c35', 0.72),
        door_x=-1.9, display=(1.0, 2.7, 2.2, False),
        sign='FRESH FRUITS', sign_w=3.3, sign_z=3.48, sign_x=1.0,
        awning=dict(x=1.0, w=3.1, d=1.0, z=2.92,
                    mat_a=fabric('awning_green', '#3e5c3a', 0.85),
                    mat_b=fabric('awning_cream2', '#eee2cf', 0.85)),
        side_windows='both', garland_n=13,
    ))
    win = next(o for o in e.children if o.name.startswith('displaywin') and o.type == 'EMPTY')
    for i in range(3):
        cylinder('basket2', 0.22, 0.18, (-0.6 + i * 0.55, -0.12, -0.42), plaster('wicker2', '#8a663c', 0.8, 0.3), 14, parent=win)
        for k in range(5):
            sphere('f', 0.06, (-0.72 + i * 0.55 + (k % 3) * 0.11, -0.12 + (k // 3) * 0.1, -0.32),
                   gloss('fruit_mix' + str((i + k) % 3), ['#b31b26', '#d97a20', '#e5c235'][(i + k) % 3], 0.3),
                   8, 6, parent=win)
    fruit_crates(e, -3.5, -2.2, 2)
    return e


def market_shop(pos, yaw):
    e = shop(dict(
        name='market_shop', pos=pos, yaw=yaw, w=7.8, d=7.0, h=7.2, roof_h=2.35, win_frame=WIN_BLUE,
        wall=plaster('wall_market', '#ccd4d7', 0.86),
        trim=IVORY, roof=roofmat('roof_market', '#2e3a45'),
        shutters=plaster('shutter_market', '#7c8b93', 0.72),
        door_x=2.1, display=(-1.1, 3.6, 2.3, False),
        sign='MINI MARKET', sign_w=3.5, sign_z=3.3, sign_x=-2.0,
        garland_n=16, side_windows='both',
    ))
    win = next(o for o in e.children if o.name.startswith('displaywin') and o.type == 'EMPTY')
    market_shelves(win)
    # A frame board
    box('aframe', 0.8, 0.08, 1.0, (3.0, -4.6, 0.55), WOOD_MID, 0.015,
        rot=(0.2, 0, 0.5), parent=e)
    return e


def bakery(pos, yaw):
    e = shop(dict(
        name='bakery', pos=pos, yaw=yaw, w=7.5, d=6.9, h=7.5, roof_h=2.15, win_frame=WIN_BROWN,
        wall=plaster('wall_bakery', '#d7b184', 0.88),
        trim=CREAM, roof=roofmat('roof_bakery', '#3c2a22'),
        shutters=WOOD_MID,
        door_x=-2.0, display=(1.2, 3.0, 2.4, True),
        sign='BAKERY', sign_w=2.8, sign_z=3.3, sign_x=2.0,
        awning=None, side_windows='both', garland_n=15,
    ))
    win = next(o for o in e.children if o.name.startswith('displaywin') and o.type == 'EMPTY')
    bread_display(win)
    # wooden cart
    box('cart', 1.5, 0.7, 0.5, (2.6, -4.9, 0.55), WOOD_WARM, 0.02, parent=e)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cylinder('cartwheel', 0.26, 0.07, (2.6 + sx * 0.75, -4.9 + sy * 0.36, 0.3),
                     WOOD_DARK, 12, rot=(PI / 2, 0, 0), parent=e)
    for i in range(4):
        sphere('cartbread', 0.14, (2.3 + i * 0.2, -4.9, 0.85), gloss('bread3', '#c08044', 0.5),
               10, 6, (1.4, 0.7, 0.6), parent=e)
    # high sign on the right half of the facade, visible past the tree
    add_sign(e, 'BAKERY', 2.55, 6.55, -3.62, 2.1, 0.46, SIGN_BOARD, SIGN_GOLD, name='high_sign')
    return e


def pizzeria(pos, yaw):
    e = shop(dict(
        name='pizzeria', pos=pos, yaw=yaw, w=7.6, d=7.2, h=7.2, roof_h=2.2, win_frame=WIN_GREEN,
        wall=brickmat('wall_pizza', '#8f4b3e'),
        trim=CREAM, roof=roofmat('roof_pizza', '#3f2b24'),
        shutters=plaster('shutter_pizza', '#37472f', 0.72),
        door_x=0, display=None, arch_door=True,
        sign='PIZZERIA', sign_w=3.0, sign_z=3.35, sign_x=0,
        awning=dict(x=0, w=5.6, d=1.2,
                    mat_a=fabric('awning_red', '#a8322f', 0.85),
                    mat_b=fabric('awning_cream3', '#f0e4d2', 0.85)),
        awning_z=3.05, side_windows='both', garland_n=15,
    ))
    for side in (-1, 1):
        win = add_window(e, (side * 2.2, -3.62, 2.05), 0, 1.7, 1.8, 0.28, True,
                         sill_mat=CREAM, name='pizza_win')
        if side == 1:
            pizza_oven(win)
    # chimney smoke
    for i in range(3):
        ico('smoke', 0.25 + i * 0.12, (2.1, 1.2, 10.5 + i * 0.55),
            gloss('smoke_m', '#aeb5bd', 0.6), 2, (1, 1, 0.8), parent=e, jitter=0.3)
    return e


def chapel(pos, yaw):
    e = empty('chapel', pos, (0, 0, math.radians(yaw)))
    w, d, h = 8.8, 8.4, 6.2
    wall = plaster('wall_chapel', '#ded3bd', 0.87)
    roofm = roofmat('roof_chapel', '#33414f')
    stone_b = stone('chapel_base', '#8f897c', 0.6)
    box('walk', w + 2.0, 2.0, 0.12, (0, -d / 2 - 1.0, 0.06), tile('chapel_walk', '#a8a091', 0.5), 0.015, parent=e)
    box('foundation', w + 0.3, d + 0.3, 0.6, (0, 0, 0.3), stone_b, 0.02, parent=e)
    box('body', w, d, h, (0, 0, 0.6 + h / 2), wall, 0.04, parent=e)
    # corner buttresses / quoins
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('quoin', 0.3, 0.3, h, (sx * w / 2, sy * d / 2, 0.6 + h / 2), STONE_LIGHT, 0.012, parent=e)
            ico('quoin_snow', 0.16, (sx * w / 2, sy * d / 2, 0.6 + h + 0.02), SNOW, 1,
                (1.0, 1.0, 0.3), parent=e, jitter=0.25)
    box('cornice', w + 0.34, d + 0.34, 0.22, (0, 0, 0.6 + h - 0.11), STONE_TRIM, 0.02, parent=e)
    # roof, ridge running front-back
    rh = 3.6
    roof = gable_roof('roof', d, w, rh, 0.3, 0.2, roofm)
    roof.rotation_euler = (0, 0, PI / 2)
    roof.location = (0, 0, 0.6 + h)
    roof.parent = e
    # front gable wall and barge boards
    gy = -d / 2 - 0.32
    V = [(-w / 2, gy, 0.6 + h), (w / 2, gy, 0.6 + h), (0, gy, 0.6 + h + rh)]
    F = [(0, 1, 2)]
    gable = mesh_obj('gable_wall', V, F, wall)
    gable.parent = e
    # thickness band at gable base
    box('gable_band', w + 0.06, 0.26, 0.2, (0, gy + 0.06, 0.6 + h + 0.1), STONE_TRIM, 0.015, parent=e)
    for sx in (-1, 1):
        curve_tube('barge', [(sx * w / 2, gy - 0.02, 0.6 + h), (0, gy - 0.02, 0.6 + h + rh)],
                   0.1, WOOD_DARK, parent=e)
    # rose window in gable
    rz = 0.6 + h + 1.75
    cylinder('rose_trim', 0.78, 0.16, (0, gy - 0.06, rz), STONE_TRIM, 32, rot=(PI / 2, 0, 0), parent=e)
    cylinder('rose_glow', 0.64, 0.05, (0, gy - 0.15, rz), window_glow('rose_glow', '#ffbf7c', 2.4),
             32, rot=(PI / 2, 0, 0), parent=e)
    for i in range(8):
        ang = i * PI / 4
        box('rose_bar', 0.045, 0.04, 1.18, (0, gy - 0.19, rz), STONE_DARK, 0.0,
            rot=(0, ang, 0), parent=e)
    cylinder('rose_hub', 0.1, 0.08, (0, gy - 0.2, rz), STONE_TRIM, 12, rot=(PI / 2, 0, 0), parent=e)
    # tower at back-left
    tx, ty = -w / 2 + 1.25, d / 2 - 1.3
    th = 9.2
    box('tower', 1.95, 1.95, th, (tx, ty, 0.6 + th / 2), wall, 0.03, parent=e)
    for zz in (0.6 + 3.2, 0.6 + 7.4, 0.6 + th - 0.16):
        box('tower_band', 2.15, 2.15, 0.16, (tx, ty, zz), STONE_TRIM, 0.012, parent=e)
    # belfry openings on four faces
    for face in range(4):
        ang = face * PI / 2
        xx = tx + math.sin(ang) * 0.99
        yy = ty - math.cos(ang) * 0.99
        ob = box('belfry', 1.0, 0.08, 1.5, (0, 0, 0), wood('belfry_dark', '#1e1710', 0.82), 0.01)
        ob.location = (xx, yy, 0.6 + th - 1.05)
        ob.rotation_euler = (0, 0, ang)
        ob.parent = e
        for k in range(3):
            lv = box('louver', 1.0, 0.06, 0.08, (0, 0, 0), WOOD_DARK, 0.004)
            lv.location = (xx + math.sin(ang) * 0.06, yy - math.cos(ang) * 0.06, 0.6 + th - 1.55 + k * 0.42)
            lv.rotation_euler = (0, 0, ang)
            lv.parent = e
        bell = cone('bell', 0.22, 0.12, 0.32, (xx, yy, 0.6 + th - 1.55), GOLD, 12)
        bell.parent = e
    # clock on the front face of the tower
    cylinder('clock', 0.5, 0.08, (tx, ty - 1.02, 0.6 + th - 3.4), stone('clock_face', '#e9e1cd', 0.5), 28,
             rot=(PI / 2, 0, 0), parent=e)
    cylinder('clock_ring', 0.55, 0.06, (tx, ty - 1.0, 0.6 + th - 3.4), STONE_TRIM, 28,
             rot=(PI / 2, 0, 0), parent=e)
    box('hand', 0.035, 0.03, 0.32, (tx, ty - 1.08, 0.6 + th - 3.28), IRON, 0.0,
        rot=(0, 0.35, 0), parent=e)
    box('hand2', 0.03, 0.03, 0.22, (tx + 0.08, ty - 1.08, 0.6 + th - 3.4), IRON, 0.0,
        rot=(0, 1.4, 0), parent=e)
    # spire and pinnacles
    cone('spire', 1.55, 0.02, 3.6, (tx, ty, 0.6 + th + 1.8), roofm, 4, rot=(0, 0, PI / 4), parent=e)
    cone('spire_snow', 1.58, 0.35, 0.4, (tx, ty, 0.6 + th + 0.2), SNOW, 4, rot=(0, 0, PI / 4), parent=e)
    box('cross_v', 0.08, 0.08, 1.1, (tx, ty, 0.6 + th + 4.15), GOLD, 0.01, parent=e)
    box('cross_h', 0.62, 0.08, 0.08, (tx, ty, 0.6 + th + 4.3), GOLD, 0.01, parent=e)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cone('pin', 0.22, 0.0, 0.9, (tx + sx * 0.85, ty + sy * 0.85, 0.6 + th + 0.35),
                 roofm, 4, rot=(0, 0, PI / 4), parent=e)
    # facade pilasters
    for sx in (-1, 1):
        for px in (sx * w / 2, sx * 1.9):
            box('pilaster', 0.34, 0.24, h - 0.3, (px, -d / 2 - 0.1, 0.6 + (h - 0.3) / 2),
                STONE_LIGHT, 0.012, parent=e)
            box('pilaster_cap', 0.44, 0.34, 0.16, (px, -d / 2 - 0.12, 0.6 + h - 0.28), STONE_TRIM, 0.01, parent=e)
            ico('pilaster_snow', 0.14, (px, -d / 2 - 0.14, 0.6 + h - 0.18), SNOW, 1, (1.0, 0.7, 0.25),
                parent=e, jitter=0.2)
    # entrance
    door = add_door(e, 0, -d / 2 - 0.02, 0.62, 1.85, 2.75,
                    door_mat=WOOD_DARK, frame_mat=STONE_TRIM, arched=True,
                    wreath_on=True, lamps=True, name='chapel_door')
    # pointed arch above the door
    for sx in (-1, 1):
        pts = []
        for i in range(9):
            t = i / 8
            pts.append((sx * 1.25 * (1 - t) + 0.0, -d / 2 - 0.14, 0.62 + 2.9 + 1.1 * t ** 1.5))
        curve_tube('door_arch', pts, 0.08, STONE_TRIM, parent=e)
    # stained glass windows
    cols = [(emission('stain_blue', '#2e4f9a', 1.6)),
            (emission('stain_ruby', '#9a1f2e', 1.6)),
            (emission('stain_gold', '#c8922f', 1.5))]
    for sx in (-1, 1):
        win = add_window(e, (sx * 2.9, -d / 2 - 0.02, 2.45), 0, 1.25, 2.9, 0.14, True,
                         pointed=True, sill_mat=STONE_TRIM, name='chapel_win')
        for k, cmat in enumerate(cols):
            box('stain', 0.26, 0.01, 1.9, ((k - 1) * 0.3, -0.05, -0.1), cmat, 0.0, parent=win)
    for side in (-1, 1):
        for k in range(2):
            win = add_window(e, (side * (w / 2 + 0.02), -d * 0.23 + k * d * 0.46, 2.6),
                             PI / 2 * side, 1.0, 2.4, 0.1, True, pointed=True,
                             sill_mat=STONE_TRIM, name='chapel_side')
            for j, cmat in enumerate(cols):
                box('stain', 0.22, 0.01, 1.5, ((j - 1) * 0.25, -0.05, -0.05), cmat, 0.0, parent=win)
    # steps
    for i in range(4):
        box('step', 3.4 + i * 0.42, 0.55, 0.16, (0, -d / 2 - 0.45 - i * 0.22, 0.22 - i * 0.16),
            STONE_LIGHT, 0.015, parent=e)
        for k in range(3):
            ico('step_snow', 0.12, (-1.2 + k * 1.2, -d / 2 - 0.45 - i * 0.22, 0.31 - i * 0.16),
                SNOW, 1, (1.5, 0.7, 0.2), parent=e, jitter=0.2)
    # snow on the gable bargeboards
    for i in range(7):
        t = i / 6
        for sx in (-1, 1):
            ico('barge_snow', 0.13, (sx * (w / 2) * (1 - t), gy - 0.06, 0.6 + h + rh * t + 0.04),
                SNOW, 1, (1.3, 0.6, 0.25), parent=e, jitter=0.25)
    # roof snow
    roofgrp = empty('chapel_roofgrp', (0, 0, 0.6 + h), (0, 0, PI / 2))
    roofgrp.parent = e
    snow_slope(roofgrp, d + 0.6, w / 2 + 0.3, rh, True)
    snow_slope(roofgrp, d + 0.6, w / 2 + 0.3, rh, False)
    # warm skylights on the visible slope
    alpha = math.atan2(rh, w / 2 + 0.3)
    for i, yy in enumerate((-1.9, 0.0, 1.9)):
        xx = -2.45
        zz = 0.6 + h + rh * (1 - abs(xx) / (w / 2 + 0.3)) + 0.1
        sk = empty('skylight', (xx, yy, zz), (0, alpha, 0))
        sk.parent = e
        box('skylight_frame', 1.0, 1.35, 0.1, (0, 0, 0), IRON, 0.015, parent=sk)
        box('skylight_glass', 0.82, 1.15, 0.04, (0, 0, 0.06),
            window_glow('skylight_glow', '#ffb35e', 1.2), 0.01, parent=sk)
        for k in range(2):
            ico('skylight_snow', 0.18, (-0.45 + k * 0.9, 0, 0.08), SNOW, 1, (1.0, 1.6, 0.25),
                parent=sk, jitter=0.25)
    # stone cross at the gable apex
    box('gable_cross_v', 0.07, 0.07, 0.8, (0, gy - 0.12, 0.6 + h + rh + 0.3), STONE_TRIM, 0.01, parent=e)
    box('gable_cross_h', 0.5, 0.07, 0.07, (0, gy - 0.12, 0.6 + h + rh + 0.5), STONE_TRIM, 0.01, parent=e)
    # fir trees and lamps
    for side in (-1, 1):
        tree = conifer('chapel_fir', (side * 3.5, -d / 2 - 1.45, 0), 3.1, 0.75, seed=30 + side,
                       detail=0.5, sprig_len=0.4)
        tree.parent = e
        lp = props.lamp_post((side * 4.6, -d / 2 - 1.0, 0), 0)
        lp.parent = e
    # warm interior
    ld = bpy.data.lights.new('chapel_light', 'POINT')
    ld.energy = 70; ld.color = (1.0, 0.58, 0.26); ld.shadow_soft_size = 0.8
    lo = bpy.data.objects.new('chapel_light', ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (0, -d / 2 - 0.4, 2.3)
    lo.parent = e
    return e
