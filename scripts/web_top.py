
import bpy
bpy.ops.wm.open_mainfile(filepath='/Volumes/External/Project/ClawProject/Christmas26/christmas_town.blend')
items=sorted(((len(o.data.vertices), o.name, [m.name for m in o.data.materials if m]) for o in bpy.data.objects if o.type=='MESH'), reverse=True)
for n,name,mats in items[:25]:
    print(n, name, mats)
print('TOTAL', sum(n for n,_,_ in items))
