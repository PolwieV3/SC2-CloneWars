import bpy,json,math,re
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[2]; W=R/'work/atte'; O=R/'outputs/AT-TE'
bpy.ops.wm.open_mainfile(filepath=str(O/'AT-TE-source.blend'))
scene=bpy.context.scene
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.data.objects if o.type=='MESH' and len(o.vertex_groups)]
S=6.0
C=Matrix(((S,0,0,0),(0,0,S,0),(0,-S,0,0),(0,0,0,1)))
def clean(m):
 return Matrix.Translation(m.translation)@m.to_quaternion().to_matrix().to_4x4()
source=list(arm.data.bones)
names=['ATTE_Root']+[b.name for b in source]
parents=[-1]+[names.index(b.parent.name) if b.parent else 0 for b in source]
scene.frame_set(1)
rest=[Matrix.Identity(4)]+[clean(C@arm.matrix_world@arm.pose.bones[b.name].matrix) for b in source]
# Rebase bind geometry onto the supplied first pose. Its original bind pose uses
# a different orientation from the standing animation and cannot be used as idle.
baked={}
dg=bpy.context.evaluated_depsgraph_get()
for ob in meshes:
 ev=ob.evaluated_get(dg);baked[ob.name]=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg)
controllers=[]; remap={};helper_hosts={}
guns=[('Main','Turret_Base_Pivot_13','Turret_Barrel_11',['Turret_Base_Pivot_13','Turret_12','Turret_Barrel_11'],0,180),
 ('FrontLeftTop','Left_Front_Top_BallTurret_10','Left_Front_Top_BallTurret_End_9',['Left_Front_Top_BallTurret_10','Left_Front_Top_BallTurret_End_9'],-30,65),
 ('FrontLeftBottom','Left_Front_Bottom_BallTurret_8','Left_Front_Bottom_BallTurret_End_7',['Left_Front_Bottom_BallTurret_8','Left_Front_Bottom_BallTurret_End_7'],-30,65),
 ('FrontRightTop','Right_Front_Top_BallTurret_15','Right_Front_Top_BallTurret_End_14',['Right_Front_Top_BallTurret_15','Right_Front_Top_BallTurret_End_14'],30,65),
 ('FrontRightBottom','Right_Front_Bottom_BallTurret_17','Right_Front_Bottom_BallTurret_End_16',['Right_Front_Bottom_BallTurret_17','Right_Front_Bottom_BallTurret_End_16'],30,65),
 ('RearLeft','Left_Back_BallTurret_28','Left_Back_BallTurret_End_27',['Left_Back_BallTurret_28','Left_Back_BallTurret_End_27'],-150,65),
 ('RearRight','Right_Back_BallTurret_35','Right_Back_BallTurret_End_34',['Right_Back_BallTurret_35','Right_Back_BallTurret_End_34'],150,65)]
scene.frame_set(1)
for label,pivot,tip,groups,yaw,arc in guns:
 p=rest[names.index(pivot)].translation; t=rest[names.index(tip)].translation
 # Project source tip to the actual barrel end using the weapon's skinned vertices.
 candidates=[]
 for ob in meshes:
  ids={g.index for g in ob.vertex_groups if g.name in groups}
  for v in baked[ob.name].vertices:
   if any(g.group in ids and g.weight>.4 for g in v.groups):candidates.append(C@ob.matrix_world@v.co)
 direction=Vector((math.sin(math.radians(yaw)),0,math.cos(math.radians(yaw))))
 if candidates:t=max(candidates,key=lambda v:(v-p).dot(direction))
 # Orient each muzzle down its visible barrel, including rear-facing lasers.
 direction=(t-p).normalized();heading=math.atan2(direction.x,direction.z)
 elevation=math.atan2(direction.y,math.hypot(direction.x,direction.z))
 y=Matrix.Translation(p)@Matrix.Rotation(heading,4,'Y')
 q=y@Matrix.Rotation(-elevation,4,'X');muzzle=q.copy();muzzle.translation=t
 host='Butt_36' if label.startswith('Rear') else 'Head_21'
 for suffix,world,parent in [('Yaw',y,names.index(host)),('Pitch',q,len(names)),('Muzzle',muzzle,len(names)+1)]:
  names.append('ATTE_'+label+'_'+suffix);rest.append(world);parents.append(parent)
  helper_hosts[names[-1]]=host
 for group in groups:remap[group]=names.index('ATTE_'+label+('_Yaw' if label=='Main' and group==pivot else '_Pitch'))
 controllers.append({'label':label,'yaw':'ATTE_'+label+'_Yaw','pitch':'ATTE_'+label+'_Pitch','muzzle':'ATTE_'+label+'_Muzzle','arc':arc,'heading':math.degrees(heading),'position':list(t),'direction':list(direction)})
bones=[]
for i,n in enumerate(names):
 local=rest[parents[i]].inverted()@rest[i] if parents[i]>=0 else rest[i]
 inv=rest[i].inverted();bones.append({'name':n,'parent':parents[i],'inverse':[inv[a][b] for b in range(4) for a in range(4)],'position':list(local.translation),'quaternion':list(local.to_quaternion())})
frames=[]
for frame in range(1,481,2):
 scene.frame_set(frame)
 world=[Matrix.Identity(4)]+[clean(C@arm.matrix_world@arm.pose.bones[b.name].matrix) for b in source]
 for i in range(len(world),len(rest)):
  host=names.index(helper_hosts[names[i]])
  world.append(world[host]@rest[host].inverted()@rest[i])
 rows=[]
 for i,m in enumerate(world):
  local=world[parents[i]].inverted()@m if parents[i]>=0 else m
  rows.append(list(local.translation)+list(local.to_quaternion()))
 frames.append({'time':(frame-1)/24,'bones':rows})
# Close the source walk at an explicit repeat boundary; retain the original sequence.
frames.append({'time':20.,'bones':frames[0]['bones']})
# The shipped unit shader has 72 matrices; keep root, 44 mechanical joints,
# and 21 gun helpers. Bake retained world transforms before changing parents.
oldnames=names[:];oldparents=parents[:];oldrest=rest[:]
keep=[i for i,n in enumerate(oldnames) if n.startswith('ATTE_') or not re.search(r'Toe|Suction|FootBottom|\.IK|Target|Orient|BallTurret|Turret|rootJoint',n)]
assert len(keep)<=71,len(keep)
old_to_new={old:i for i,old in enumerate(keep)}
def retained(i):
 while i not in old_to_new:i=oldparents[i]
 return old_to_new[i]
names=[oldnames[i] for i in keep];rest=[oldrest[i] for i in keep]
parents=[retained(oldparents[i]) if oldparents[i]>=0 else -1 for i in keep]
skinmap={n:retained(i) for i,n in enumerate(oldnames)}
remap={n:old_to_new[i] for n,i in remap.items()}
from mathutils import Quaternion
for f in frames:
 world=[]
 for i,row in enumerate(f['bones']):
  local=Matrix.Translation(Vector(row[:3]))@Quaternion(row[3:]).to_matrix().to_4x4()
  world.append(world[oldparents[i]]@local if oldparents[i]>=0 else local)
 rows=[]
 for i,newparent in zip(keep,parents):
  local=world[keep[newparent]].inverted()@world[i] if newparent>=0 else world[i]
  rows.append(list(local.translation)+list(local.to_quaternion()))
 f['bones']=rows
bones=[]
for i,n in enumerate(names):
 local=rest[parents[i]].inverted()@rest[i] if parents[i]>=0 else rest[i]
 inv=rest[i].inverted();bones.append({'name':n,'parent':parents[i],'inverse':[inv[a][b] for b in range(4) for a in range(4)],'position':list(local.translation),'quaternion':list(local.to_quaternion())})
(W/'rig-animation.json').write_text(json.dumps({'bones':bones,'controllers':controllers,'frames':frames,'duration':20.},separators=(',',':')),encoding='utf-8')
scene.frame_set(1)
for im in bpy.data.images:
 if im.has_data and im.size[0]>64:
  im.filepath_raw=str(W/('diffuse.png' if 'base' in im.name.lower() or '0'==im.name else 'image-'+im.name.replace('/','_')+'.png'));im.file_format='PNG';im.save()
mat=meshes[0].data.materials[0];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=bs.inputs['Base Color'].links[0].from_node.image;tex.filepath_raw=str(W/'diffuse.png');tex.file_format='PNG';tex.save()
for lod,ratio in enumerate([.42,.20,.09]):
 triangles=[]
 for original in meshes:
  for preserve_guns in [False,True]:
   ob=original.copy();ob.data=baked[original.name].copy();bpy.context.collection.objects.link(ob)
   for m in list(ob.modifiers):ob.modifiers.remove(m)
   if not preserve_guns:
    dec=ob.modifiers.new('Native LOD','DECIMATE');dec.ratio=ratio;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=dec.name)
   ob.data.calc_loop_triangles();ob.data.calc_tangents(uvmap=ob.data.uv_layers.active.name)
   normal_matrix=C.to_3x3()@ob.matrix_world.to_3x3()
   for tri in ob.data.loop_triangles:
    is_gun=any(ob.vertex_groups[g.group].name in remap and g.weight>.25 for vi in tri.vertices for g in ob.data.vertices[vi].groups)
    if is_gun != preserve_guns:continue
    rows=[]
    for li in tri.loops:
     loop=ob.data.loops[li];v=ob.data.vertices[loop.vertex_index];p=C@ob.matrix_world@v.co;n=(normal_matrix@loop.normal).normalized();t=(normal_matrix@loop.tangent).normalized();bt=n.cross(t)*loop.bitangent_sign;uv=ob.data.uv_layers.active.data[li].uv
     weights={}
     for g in v.groups:
      name=ob.vertex_groups[g.group].name;bi=remap.get(name,skinmap.get(name,0));weights[bi]=weights.get(bi,0)+g.weight
     ws=sorted(weights.items(),key=lambda x:-x[1])[:4] or [(0,1.)];total=sum(x[1] for x in ws);ws=[(b,w/total) for b,w in ws];ws+=[(0,0)]*(4-len(ws))
     rows.append({'v':list(p)+list(n)+list(t)+list(bt)+[uv.x,1-uv.y,uv.x,1-uv.y]+[x[0] for x in ws],'w':[x[1] for x in ws]})
    triangles.append(rows)
   bpy.data.objects.remove(ob,do_unlink=True)
 (W/f'geometry-lod{lod}.json').write_text(json.dumps(triangles,separators=(',',':')),encoding='utf-8');print('LOD',lod,len(triangles))
print('ATTE export complete',len(names),'bones',len(frames),'frames')
