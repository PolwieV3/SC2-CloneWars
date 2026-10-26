import bpy,json
from pathlib import Path
from mathutils import Vector
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/juggernaut';bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(next((w/'source').glob('*.glb'))));bpy.context.view_layer.update();report=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 o.data.calc_loop_triangles();ps=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[k] for p in ps) for k in range(3)];hi=[max(p[k] for p in ps) for k in range(3)];report.append({'name':o.name,'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'min':lo,'max':hi,'materials':[m.name for m in o.data.materials]})
(w/'import-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(w/'Juggernaut-import.blend'));print(json.dumps(report))
