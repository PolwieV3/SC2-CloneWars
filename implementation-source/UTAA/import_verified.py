import bpy,sys,json
from pathlib import Path
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/archanist';sys.path.insert(0,str(w/'tools/Blender-ALAMO-Plugin-for-4.0-master'))
import io_alamo_tools as addon
addon.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for stem in ['Rep_UTAA','Rep_UTAA_Turret']:
 bpy.ops.import_mesh.alo(filepath=str(w/'source'/(stem+'.alo')),importAnimations=False)
report=[]
for o in bpy.data.objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None}
 if o.type=='MESH':o.data.calc_loop_triangles();d.update({'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'groups':[v.name for v in o.vertex_groups],'materials':[m.name for m in o.data.materials]})
 if o.type=='ARMATURE':d['bones']=[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in o.data.bones]
 report.append(d)
(w/'verified-import-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(w/'UTAA-rigged-import.blend'));print(json.dumps(report))
