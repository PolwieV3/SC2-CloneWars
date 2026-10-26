import bpy,json,sys
from pathlib import Path
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');bpy.ops.wm.open_mainfile(filepath=str(r/'outputs/SPHA-T/SPHA-T-animated-source.blend'))
a=next(o for o in bpy.data.objects if o.type=='ARMATURE');s=bpy.context.scene
out={'arm_world':[list(x) for x in a.matrix_world],'bones':[],'objects':[],'poses':{}}
for b in a.data.bones:out['bones'].append({'name':b.name,'parent':b.parent.name if b.parent else None,'pos':list(b.matrix_local.translation)})
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 weights={}
 for v in ob.data.vertices:
  for g in v.groups:
   n=ob.vertex_groups[g.group].name;weights[n]=weights.get(n,0)+g.weight
 out['objects'].append({'name':ob.name,'pos':list(ob.matrix_world.translation),'weights':weights,'mods':[(m.type,m.object.name if m.type=='ARMATURE' and m.object else None) for m in ob.modifiers]})
for name in ['Cv_SPHT_idle_00','Cv_SPHT_deploy_00','Cv_SPHT_undeploy_00','Cv_SPHT_move_00']:
 act=bpy.data.actions[name];a.animation_data.action=act
 if act.slots:a.animation_data.action_slot=act.slots[0]
 out['poses'][name]={}
 for f in [0,int(act.frame_range[1])]:
  s.frame_set(f);out['poses'][name][f]={n:[list(row) for row in (a.matrix_world@a.pose.bones[n].matrix)] for n in ['Main_body','Subtorreta','Turret_00','Barrel_00','MuzzleA_00','Main_foot_L1']}
Path('work/spha/source-inspection.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out['poses'],indent=2))
