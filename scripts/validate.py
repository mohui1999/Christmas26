
import bpy
sc=bpy.context.scene
print('OBJECTS', len(bpy.data.objects), 'MESHES', len(bpy.data.meshes), 'MATS', len(bpy.data.materials))
print('CAMERA', sc.camera.name if sc.camera else None, sc.camera.data.type if sc.camera else None, round(sc.camera.data.ortho_scale,2) if sc.camera else None)
print('RES', sc.render.resolution_x, sc.render.resolution_y, 'SAMPLES', sc.cycles.samples, 'ENGINE', sc.render.engine)
print('SIGNS', sorted([o.name for o in bpy.data.objects if o.type=='FONT' and o.name.endswith('_text')]))
print('TEXT_BODIES', sorted(set(o.data.body for o in bpy.data.objects if o.type=='FONT')))
print('LIGHTS', len([o for o in bpy.data.objects if o.type=='LIGHT']))
print('MISSING', [i.filepath for i in bpy.data.images if i.filepath and not i.packed_file][:5])
