exec(open('work/spha/inspect.py',encoding='utf8').read().split("out={'arm_world'")[0])
for n in ['Main_body','Main_foot_L1','Barrel_00','Turret_00','Subtorreta']:
 ob=bpy.data.objects[n];print(n,'parent',ob.parent.name if ob.parent else None,ob.parent_type,ob.parent_bone,'local',list(ob.location),'world',list(ob.matrix_world.translation),'bbox',[list(v) for v in ob.bound_box])
