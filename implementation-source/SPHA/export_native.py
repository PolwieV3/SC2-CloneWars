import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
W=Path(__file__).resolve().parent; R=W.parents[1]; O=R/'outputs/SPHA-T'
source=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/outputs/SPHA-T')
bpy.ops.wm.open_mainfile(filepath=str(source/'SPHA-T-animated-source.blend'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE'); scene=bpy.context.scene
# Decode every source frame, with linear interpolation, rather than the old four-frame sampling.
decoder=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/spha/old_ala.py').read_text(encoding='utf8').replace('range(0,frames,4)','range(0,frames,1)')
ns={};exec(compile(decoder,'old_ala_full.py','exec'),ns)
actions={}
for short,src in [('Walk','move'),('Deploy','deploy'),('Pack','undeploy')]:
 before=set(bpy.data.actions); ns['load'](source/'Animated-source'/('Cv_SPHT_'+src+'_00.ala'),arm)
 actions[short]=next(a for a in bpy.data.actions if a not in before)
 for layer in actions[short].layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for p in fc.keyframe_points:p.interpolation='LINEAR'
def select(action,f):
 arm.animation_data.action=action
 if action.slots:arm.animation_data.action_slot=action.slots[0]
 scene.frame_set(f);bpy.context.view_layer.update()
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(('Box','CollMesh','Subshadow'))]
hosts={o.name:next(c.subtarget for c in o.constraints if c.type=='CHILD_OF' and c.target==arm) for o in meshes}
# Fit the source's proportions to a 12-unit visual length. Simulation footprint remains native.
S=120/155.2757; C=Matrix(((S,0,0,0),(0,0,S,0),(0,-S,0,0),(0,0,0,1)))
def rigid(m):return Matrix.Translation(m.translation)@m.to_quaternion().to_matrix().to_4x4()
select(actions['Deploy'],40)
endbar=C@arm.matrix_world@arm.pose.bones['Barrel_00'].matrix
endtip=C@arm.matrix_world@arm.pose.bones['MuzzleA_00'].matrix
enddir=(endtip.translation-endbar.translation).normalized()
flatten=Matrix.Rotation(math.atan2(enddir.y,math.hypot(enddir.x,enddir.z)),4,'X')
select(actions['Walk'],0)
visiblehosts=set(hosts.values())-{'Turret_00','Barrel_00'}
ordered=[b.name for b in arm.data.bones if b.name in visiblehosts]
names=['SPHA_Root']+ordered+['SPHA_Yaw','SPHA_Pitch','SPHA_Muzzle']
assert len(names)<72,len(names)
parents=[-1]+[0]*len(ordered)+[0,len(names)-3,len(names)-2]
def worlds():
 world=[Matrix.Identity(4)]+[rigid(C@arm.matrix_world@arm.pose.bones[n].matrix) for n in ordered]
 yaw=Matrix.Translation((C@arm.matrix_world@arm.pose.bones['Turret_00'].matrix).translation)
 bp=(C@arm.matrix_world@arm.pose.bones['Barrel_00'].matrix).translation
 tip=(C@arm.matrix_world@arm.pose.bones['MuzzleA_00'].matrix).translation
 direction=flatten@(tip-bp);heading=math.atan2(direction.x,direction.z);elev=math.atan2(direction.y,math.hypot(direction.x,direction.z))
 pitch=Matrix.Translation(bp)@Matrix.Rotation(heading,4,'Y')@Matrix.Rotation(-elev,4,'X')
 # Keep the bore length; the correction levels the deployed firing pose.
 muzzle=pitch.copy();muzzle.translation=bp+direction
 return world+[yaw,pitch,muzzle]
rest=worlds();source_rest={n:rigid(C@arm.matrix_world@arm.pose.bones[n].matrix) for n in ['Turret_00','Barrel_00']}
# Transform the barrel from its imported orientation onto a level deployed bore.
bar0=source_rest['Barrel_00'];d0=(C@arm.matrix_world@arm.pose.bones['MuzzleA_00'].matrix).translation-bar0.translation
heading0=math.atan2(d0.x,d0.z);elev0=math.atan2(d0.y,math.hypot(d0.x,d0.z))
sourceaxis=Matrix.Translation(bar0.translation)@Matrix.Rotation(heading0,4,'Y')@Matrix.Rotation(-elev0,4,'X')
barfix=rest[names.index('SPHA_Pitch')]@sourceaxis.inverted()
bind_objects={o.name:o.matrix_world.copy() for o in meshes}
triangles=[];vertices_by_mesh={};max_skin_error=0.;foot_ranges={n:[] for n in ordered if n.startswith('Main_foot')}
for ob in meshes:
 ob.data.calc_loop_triangles();ob.data.calc_tangents(uvmap=ob.data.uv_layers.active.name)
 host=hosts[ob.name];mapped='SPHA_Yaw' if host=='Turret_00' else 'SPHA_Pitch' if host=='Barrel_00' else host
 bi=names.index(mapped);transform=C@ob.matrix_world
 if host=='Barrel_00':transform=barfix@transform
 localverts=[]
 for tri in ob.data.loop_triangles:
  rows=[]
  for li in tri.loops:
   loop=ob.data.loops[li];v=ob.data.vertices[loop.vertex_index];p=transform@v.co
   n=(transform.to_3x3()@loop.normal).normalized();t=(transform.to_3x3()@loop.tangent).normalized();bt=n.cross(t)*loop.bitangent_sign
   uv=ob.data.uv_layers.active.data[li].uv
   rows.append({'v':list(p)+list(n)+list(t)+list(bt)+[uv.x,1-uv.y,uv.x,1-uv.y]+[bi,0,0,0],'w':[1,0,0,0]})
  triangles.append(rows)
 vertices_by_mesh[ob.name]=[(transform@v.co) for v in ob.data.vertices]
bones=[]
for i,n in enumerate(names):
 local=rest[parents[i]].inverted()@rest[i] if parents[i]>=0 else rest[i];inv=rest[i].inverted()
 bones.append({'name':n,'parent':parents[i],'inverse':[inv[a][b] for b in range(4) for a in range(4)],'position':list(local.translation),'quaternion':list(local.to_quaternion())})
clips={};mesh_motion={n:0. for n in vertices_by_mesh}
for short,action in actions.items():
 frames=[]
 for f in range(int(action.frame_range[1])+1):
  select(action,f);world=worlds();rows=[]
  for i,m in enumerate(world):
   local=world[parents[i]].inverted()@m if parents[i]>=0 else m
   rows.append(list(local.translation)+list(local.to_quaternion()))
  frames.append({'time':f/30,'bones':rows})
  if short=='Walk':
   for n in foot_ranges:foot_ranges[n].append(list(world[names.index(n)].translation))
   for ob in meshes:
    host=hosts[ob.name]
    if host in ['Turret_00','Barrel_00']:continue
    skin=world[names.index(host)]@rest[names.index(host)].inverted()
    actual=C@ob.matrix_world
    # Independent constraint-driven Blender mesh vs exported rigid skin transform.
    for vi in range(0,len(ob.data.vertices),max(1,len(ob.data.vertices)//8)):
     expected=actual@ob.data.vertices[vi].co;got=skin@vertices_by_mesh[ob.name][vi]
     max_skin_error=max(max_skin_error,(expected-got).length)
     mesh_motion[ob.name]=max(mesh_motion[ob.name],(got-vertices_by_mesh[ob.name][vi]).length)
 # Close the gait smoothly over the last quarter second, preserving all earlier motion.
 if short=='Walk':
  for j in range(len(frames)-8,len(frames)):
   a=(j-(len(frames)-9))/8
   for k,row in enumerate(frames[j]['bones']):
    target=frames[0]['bones'][k];p=Vector(row[:3]).lerp(Vector(target[:3]),a);q=Quaternion(row[3:]).slerp(Quaternion(target[3:]),a)
    frames[j]['bones'][k]=list(p)+list(q)
 clips[short]={'duration':frames[-1]['time'],'frames':frames}
clips['Idle']={'duration':1.,'frames':[{'time':t,'bones':clips['Walk']['frames'][0]['bones']} for t in [0.,1.]]}
# Endpoint poses are held by the native Deploy ability animator.
assert max_skin_error<.001,max_skin_error
assert len(foot_ranges)==12 and all(mesh_motion[n]>.1 for n in foot_ranges)
report={'bones':len(names),'triangles':len(triangles),'visual_length_target':12,'source_to_native_scale':S,'mesh_skin_max_error':max_skin_error,'mesh_motion_ranges':mesh_motion,'foot_count':len(foot_ranges),'excluded_meshes':[o.name for o in bpy.data.objects if o.type=='MESH' and o not in meshes],'loop_endpoint':'exact after 0.267 second closure blend','deployed_bore_elevation_degrees':0,'scope':'Offline source constraint deformation and native skin mathematics; engine playback pending'}
(W/'rig-animation.json').write_text(json.dumps({'bones':bones,'clips':clips},separators=(',',':')),encoding='utf8')
(W/'geometry.json').write_text(json.dumps(triangles,separators=(',',':')),encoding='utf8')
(O/'Source-motion-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
for im in bpy.data.images:
 if im.has_data and im.size[0]>64:im.filepath_raw=str(W/'diffuse.png');im.file_format='PNG';im.save();break
print(json.dumps(report,indent=2))
