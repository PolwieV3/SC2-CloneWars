"""Validate actual packaged clips and geometry; bake native motion into Blender.

This samples the decoded asset transforms, not the game's animation controller.
"""
from pathlib import Path
import json,sys,math,itertools,zipfile,hashlib
import bpy
from mathutils import Matrix,Quaternion,Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parent;R=W.parents[1];O=R/'outputs/UT-AA'
sys.path.insert(0,str(W/'pipeline'));import scm_v7,sca101
archive=O/'zz_SC2_CloneWars_UTAA_Model.scd'
with zipfile.ZipFile(archive) as z:
 m=scm_v7.read(z.read('units/CloneWars/UTAA/UUL0105_LOD0.win.scm'))
 clips={name:sca101.read(z.read('units/UEF/UUL0105/'+name)) for name in ('UUL0105_AOpen01.win.sca','UUL0105_Aland01.win.sca')}
bind=[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed().inverted() for b in m['bones']]
locals_=[Matrix.Translation(Vector(b[16:19]))@Quaternion(b[19:23]).to_matrix().to_4x4() for b in m['bones']]
tris=[[m['vertices'][j] for j in m['indices'][i:i+3]] for i in range(0,len(m['indices'])//2,3)]
hull=[t for t in tris if all(v[16]==0 for v in t)];housing=[t for t in tris if all(v[16]==4 for v in t)]
ports=json.loads((O/'Four-port-validation.json').read_text(encoding='utf-8'))['lods'][0]['skeleton_and_pose']['helpers']
def local_at(keys,time):
 for a,b in zip(keys,keys[1:]):
  if a[0]-1e-7<=time<=b[0]+1e-7:
   f=max(0,min(1,(time-a[0])/(b[0]-a[0])));q=Quaternion(a[1:5]).slerp(Quaternion(b[1:5]),f);p=Vector(a[5:]).lerp(Vector(b[5:]),f)
   return Matrix.Translation(p)@q.to_matrix().to_4x4()
 raise ValueError(time)
def pose_at(clip,time,yaw=0,pitch=None):
 pose=[]
 for i,(name,b) in enumerate(zip(m['names'],m['bones'])):
  l=local_at(clip['tracks'][i]['keys'],time) if i<26 else locals_[i].copy()
  if name=='Turret01':l=l@Matrix.Rotation(math.radians(yaw),4,'Y')
  if name=='T01_Rack01' and pitch is not None:l=Matrix.Translation(l.translation)@Matrix.Rotation(math.radians(-pitch),4,'X')
  pose.append(pose[b[24]]@l if b[24]>=0 else l)
 return pose
def tree(ts,skin):
 vs=[skin@Vector(v[:3]) for t in ts for v in t]
 return BVHTree.FromPolygons(vs,[(i,i+1,i+2) for i in range(0,len(vs),3)],all_triangles=True)
samples=[];records=[];max_error=0
for name,clip in clips.items():
 assert clip['names']==m['names'][:26] and list(clip['parents'])==[b[24] for b in m['bones'][:26]]
 first=max(abs(x-y) for t,b in zip(clip['tracks'],m['bones']) for x,y in zip(t['keys'][0][1:],b[19:23]+b[16:19]))
 assert first<2e-6
 records.append({'file':name,'frames':clip['frames'],'duration':clip['duration'],'first_key_bind_error':first,'all_bytes_parsed':clip['parsed_bytes']})
 # Stored frame intervals plus midpoints; reverse packing follows this same path.
 for j in range(2*clip['frames']-1):
  tm=clip['duration']*j/(2*clip['frames']-2)
  samples.append((name,tm,0,None,pose_at(clip,tm)))
 if 'Open' in name:
  for yaw,pitch in itertools.product(range(-180,181,30),(0,10,20,40,60,80)):
   samples.append(('deployed_aim',clip['duration'],yaw,pitch,pose_at(clip,clip['duration'],yaw,pitch)))
results=[]
for label,time,yaw,pitch,pose in samples:
 skin=[pose[i]@bind[i].inverted() for i in range(16)]
 errors=[((skin[4]@Vector(port['actual_bore_center']))-pose[j].translation).length for j,port in enumerate(ports,26)]
 max_error=max(max_error,max(errors));assert max(errors)<2e-5
 pairs=tree(hull,skin[0]).overlap(tree(housing,skin[4]))
 results.append({'clip_or_mode':label,'time':time,'yaw':yaw,'pitch':pitch,'housing_chassis_surface_intersections':len(pairs),'maximum_muzzle_error':max(errors)})
report={'status':'passed' if not any(s['housing_chassis_surface_intersections'] for s in results) else 'clearance_failed',
 'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'decoded_clips':records,'sample_count':len(results),
 'samples_with_housing_chassis_surface_intersections':sum(bool(s['housing_chassis_surface_intersections']) for s in results),
 'maximum_muzzle_center_error':max_error,'runtime_tested':False,
 'limits':['Decoded-asset sampling, not engine playback or observed projectile/effect rendering','BVH checks triangle-surface intersections between main housing and chassis; not exhaustive component collision or containment testing','Aim samples use deployed parent transforms and requested pitch; actual engine controller blending still needs runtime observation'],
 'samples':results}
(O/'Native-motion-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert report['status']=='passed',report['samples_with_housing_chassis_surface_intersections']

# Include both native motions as editable Blender actions. Geometry export is untouched.
bpy.ops.wm.open_mainfile(filepath=str(O/'UTAA-four-port.blend'))
arm=bpy.data.objects.get('UT-AA native animation rig');arm.animation_data_create()
conv=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
for name,clip in clips.items():
 action=bpy.data.actions.new('Native opening - raised mount' if 'Open' in name else 'Native landing - raised mount')
 action.use_fake_user=True;arm.animation_data.action=action
 for j in range(clip['frames']):
  bpy.context.scene.frame_set(j+1)
  pose=pose_at(clip,clip['duration']*j/(clip['frames']-1))
  for i,bone in enumerate(arm.pose.bones):
   if bone.name not in clip['names']:continue
   index=m['names'].index(bone.name);bone.rotation_mode='QUATERNION';bone.matrix=conv@pose[index]
   bpy.context.view_layer.update()
   bone.keyframe_insert('location',frame=j+1,group=bone.name)
   bone.keyframe_insert('rotation_quaternion',frame=j+1,group=bone.name)
   bone.keyframe_insert('scale',frame=j+1,group=bone.name)
 arm.animation_data.action=None
 for bone in arm.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
arm.animation_data.action=bpy.data.actions['Native opening - raised mount']
bpy.context.scene.render.fps=30;bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=30
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'UTAA-four-port-animated.blend'))
bpy.context.scene.frame_set(30)
bpy.context.scene.camera.location=(25,-32,23)
target=Vector((0,0,7))
bpy.context.scene.camera.rotation_euler=(target-bpy.context.scene.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera.data.ortho_scale=22
bpy.context.scene.render.filepath=str(O/'UTAA-four-port-deployed.png')
bpy.ops.render.render(write_still=True)
print(json.dumps({k:v for k,v in report.items() if k!='samples'}))
