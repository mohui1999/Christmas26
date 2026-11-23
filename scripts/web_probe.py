
import bpy, collections
bpy.ops.wm.open_mainfile(filepath='/Volumes/External/Project/ClawProject/Christmas26/christmas_town.blend')
c=collections.Counter(o.type for o in bpy.data.objects)
print('TYPES', dict(c))
print('CURVES', [o.name for o in bpy.data.objects if o.type in {'FONT','CURVE'}][:10], len([o for o in bpy.data.objects if o.type in {'FONT','CURVE'}]))
print('VOLUMES', [o.name for o in bpy.data.objects if o.type=='MESH' and any(m and m.name=='mist_mat' for m in o.data.materials)])
print('BACKDROP', [(o.name, [m.name if m else None for m in o.data.materials]) for o in bpy.data.objects if 'backdrop' in o.name.lower()])
print('STARS', [o.name for o in bpy.data.objects if 'star' in o.name.lower()][:10], len([o for o in bpy.data.objects if 'star' in o.name.lower()]))
print('MATS', len(bpy.data.materials))
print('MESH_OBJECTS', len([o for o in bpy.data.objects if o.type=='MESH']))
print('VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'))
print('MODIFIERS', sum(len(o.modifiers) for o in bpy.data.objects if o.type=='MESH'))
print('PARENTS', len([o for o in bpy.data.objects if o.parent]))
