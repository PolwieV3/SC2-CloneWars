import bpy,sys,json
from pathlib import Path
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/rtt';sys.path.insert(0,str(r/'work/archanist/tools/Blender-ALAMO-Plugin-for-4.0-master'));import io_alamo_tools as addon;addon.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_mesh.alo(filepath=str(r/'outputs/Approved-Models/RTT/RM-09 Shuttle/RV_RM-09.ALO'),importAnimations=False)
report=[]
for o in bpy.data.objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None}
 if o.type=='MESH':d.update({'vertices':len(o.data.vertices),'bounds':[list(c) for c in o.bound_box],'materials':[m.name if m else None for m in o.data.materials]})
 report.append(d)
(w/'source-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(w/'source.blend'))
