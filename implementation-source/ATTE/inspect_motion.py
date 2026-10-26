import bpy,json
from pathlib import Path
p=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');bpy.ops.wm.open_mainfile(filepath=str(p/'outputs/AT-TE/AT-TE-source.blend'));arm=next(a for a in bpy.data.objects if a.type=='ARMATURE');s=bpy.context.scene;names=['Hips_56','LeftFrontFoot_79','RightFrontFoot_90','LeftMiddleFoot_101','RightMiddleFoot_112','LeftBackFoot_57','RightBackFoot_68','Turret_Base_Pivot_13'];rows=[]
for frame in range(1,481,4):
 s.frame_set(frame);rows.append({'frame':frame,'bones':{n:list((arm.matrix_world@arm.pose.bones[n].matrix).translation) for n in names}})
r={'frames':480,'fps':s.render.fps,'duration':480/s.render.fps,'ranges':{n:[max(a['bones'][n][k] for a in rows)-min(a['bones'][n][k] for a in rows) for k in range(3)] for n in names},'samples':rows};(p/'outputs/AT-TE/Animation-inspection.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='samples'},indent=2))
