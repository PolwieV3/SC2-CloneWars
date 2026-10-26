import bpy,json,sys,math,zipfile
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/juggernaut';out=r/'outputs/Juggernaut';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
with zipfile.ZipFile(out/'zz_SC2_CloneWars_Juggernaut_Model.scd') as z:m=scm_v7.read(z.read('units/CloneWars/Juggernaut/UUX0101_lod0.scm'))
names=m['names'];idx={n:i for i,n in enumerate(names)};bind=[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed().inverted() for b in m['bones']];fit=json.loads((w/'fitted-rig.json').read_text());checks=[]
def pose(yaw,pitch,wheel):
 world=[]
 for i,(name,b) in enumerate(zip(names,m['bones'])):
  par=b[24];local=bind[par].inverted()@bind[i] if par>=0 else bind[i].copy()
  if name.startswith('Turret') or name=='JUG_AA_Yaw':local=local@Matrix.Rotation(math.radians(yaw),4,'Y')
  if (name.startswith('T') and '_Barrel' in name) or name=='JUG_AA_Pitch':local=local@Matrix.Rotation(math.radians(-pitch),4,'X')
  if name.startswith('JUG_Wheel'):local=local@Matrix.Rotation(math.radians(wheel),4,'X')
  world.append(world[par]@local if par>=0 else local)
 return world
for yaw,pitch,roll in [(0,0,0),(45,20,90),(-60,40,180),(90,60,270)]:
 world=pose(yaw,pitch,roll);errors=[];dist=[]
 for tip in fit['tips']:
  pi=idx[tip['barrel']];mi=idx[tip['name']];visual=world[pi]@bind[pi].inverted()@Vector(tip['position']);errors.append((visual-world[mi].translation).length)
 assert max(errors)<1e-4,errors
 points=[]
 for v in m['vertices']:
  bi=v[16];p=world[bi]@bind[bi].inverted()@Vector(v[:3]);assert all(math.isfinite(x) for x in p);points.append(p)
  if names[bi].startswith('JUG_Wheel'):dist.append(abs((p-world[bi].translation).length-(Vector(v[:3])-bind[bi].translation).length))
 assert max(dist)<1e-4
 checks.append({'yaw':yaw,'pitch':pitch,'wheel_rotation':roll,'muzzle_position_error':max(errors),'wheel_shape_error':max(dist)})
# Render the actual archive geometry/UVs in a posed view to validate exported bindings.
for ob in list(bpy.data.objects):
 if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
world=pose(45,20,90);vs=[]
for v in m['vertices']:
 bi=v[16];p=world[bi]@bind[bi].inverted()@Vector(v[:3]);vs.append((p.x,-p.z,p.y))
faces=[m['indices'][i:i+3] for i in range(0,len(m['indices']),3)];me=bpy.data.meshes.new('Packaged Juggernaut posed');me.from_pydata(vs,[],faces);me.update();ob=bpy.data.objects.new('Packaged Juggernaut posed',me);bpy.context.collection.objects.link(ob);uv=me.uv_layers.new()
for li,loop in enumerate(me.loops):uv.data[li].uv=(m['vertices'][loop.vertex_index][12],1-m['vertices'][loop.vertex_index][13])
me.materials.append(bpy.data.materials.get('Juggernaut game atlas'));bpy.context.scene.render.filepath=str(out/'Juggernaut-aim-wheel-check.png');bpy.ops.render.render(write_still=True)
report={'sampled_poses':checks,'bone_count':len(names),'muzzles_checked':len(fit['tips']),'wheel_bones':10,'checks':'Actual archive skeleton, vertex skin indices and muzzle transforms checked; no source animation clips involved','runtime':'Not tested. Engine weapon aim, muzzle orientation, original weapon class lifecycle and cosmetic wheel script still require live test.'};(w/'pose-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(out/'Pose-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
