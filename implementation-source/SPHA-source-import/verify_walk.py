import bpy,json
from pathlib import Path
from mathutils import Vector
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');o=r/'outputs/SPHA-T';bpy.ops.wm.open_mainfile(filepath=str(o/'SPHA-T-animated-source.blend'));s=bpy.context.scene;s.render.fps=30;arm=next(x for x in bpy.data.objects if x.type=='ARMATURE');a=bpy.data.actions['Cv_SPHT_move_00'];arm.animation_data.action=a
if len(a.slots):arm.animation_data.action_slot=a.slots[0]
feet=[b.name for b in arm.pose.bones if b.name.startswith('Main_foot')];samples=[]
for f in range(0,241,10):
 s.frame_set(f);samples.append({n:list(arm.pose.bones[n].matrix.translation) for n in feet})
report={'clip':a.name,'frames':241,'fps':30,'duration_seconds':8,'feet_count':len(feet),'foot_motion_ranges':{n:[max(row[n][k] for row in samples)-min(row[n][k] for row in samples) for k in range(3)] for n in feet},'loop_endpoint_position_error':max((Vector(samples[0][n])-Vector(samples[-1][n])).length for n in feet),'scope':'Decoded source pose movement in Blender; mesh deformation and native SC2 conversion not certified.'};(o/'Walk-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8');s.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(o/'SPHA-T-animated-source.blend'));print(json.dumps(report,indent=2))
