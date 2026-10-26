import bpy,json,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/archanist';out=r/'outputs/UT-AA';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
rig=json.loads((w/'native/rig.json').read_text());bind=[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed().inverted() for b in rig['bones']];bn={n:i for i,n in enumerate(rig['names'])};rack=bind[bn['T01_Rack01']];source=json.loads((w/'Rep_UTAA_Turret.json').read_text())['meshes'][0]
# Keep source inspection lighting and rebuild deliberate native-fit geometry.
for o in list(bpy.data.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
mat=bpy.data.materials.get('UT-AA source diffuse');parts=[]
def obj(name,vs,fs,uvs,bones,kind='source'):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();uv=me.uv_layers.new(name='UVMap');ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 for f,coords in zip(me.polygons,uvs):
  for li,c in zip(f.loop_indices,coords):uv.data[li].uv=c
 for i,n in enumerate(bones):
  g=ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n);g.add([i],1,'REPLACE')
 ob['texture_kind']=kind;parts.append(ob);return ob
body=json.loads((w/'Rep_UTAA.json').read_text())['meshes'][0];vs=[(v['p'][0]*.42,v['p'][2]*.42,-v['p'][1]*.42) for v in body['vertices']];fs=[body['indices'][i:i+3] for i in range(0,len(body['indices']),3)];uvs=[[(body['vertices'][i]['uv'][0],1-body['vertices'][i]['uv'][1]) for i in f] for f in fs];obj('UT-AA hull',vs,fs,uvs,['UUL0105']*len(vs))
# Source turret housing is reshaped around native eight-port face, not around a new firing origin.
rot=Matrix.Rotation(math.radians(10),3,'X');vs=[]
for v in source['vertices']:
 p=rot@Vector(v['p']);x,up,forward=p.x,p.z,-p.y;t=max(0,min(1,forward/14.43));sx=.65+1.47*t;sy=.42+.61*t
 q=Vector((x*sx,(up-1.957)*sy-2.45*t,forward*.3965));vs.append(tuple(rack@q))
fs=[];uvs=[]
for k in range(0,len(source['indices']),3):
 f=source['indices'][k:k+3];front=sum(source['vertices'][i]['p'][1] for i in f)/3
 if front< -12.65:continue
 fs.append(f);uvs.append([(source['vertices'][i]['uv'][0],1-source['vertices'][i]['uv'][1]) for i in f])
obj('UT-AA adapted launcher housing',vs,fs,uvs,['T01_Rack01']*len(vs))
# Native aim/opening base and optional research gun keep their exact vertices and skin bindings.
refpath=w/'native/units.scd/units/UEF/UUL0105/UUL0105_LOD0.win.scm';native=scm_v7.read(refpath.read_bytes());vs=[];fs=[];uvs=[];bones=[]
for k in range(0,len(native['indices']),3):
 rows=[native['vertices'][i] for i in native['indices'][k:k+3]]
 if not all(rig['names'][v[16]] in ['Turret01','Brace01','T01_Arm01','Turret02','T02_Barrel01'] for v in rows):continue
 start=len(vs);vs.extend([v[:3] for v in rows]);fs.append((start,start+1,start+2));uvs.append([v[12:14] for v in rows]);bones.extend([rig['names'][v[16]] for v in rows])
obj('Native articulation and research gun',vs,fs,uvs,bones,'native')
# Eight individually skinned ports terminate exactly at native muzzle locations.
portcenters=[]
for j in range(1,9):
 name='T01_B01_Muzzle%02d'%j;center=bind[bn[name]].translation;local=rack.inverted()@center;portcenters.append(list(center));verts=[];faces=[];coords=[];labels=[];angles=sorted(set([i*math.tau/16 for i in range(16)]+[math.atan2(y*1.14,x*.95)%math.tau for x,y in [(1,1),(-1,1),(-1,-1),(1,-1)]]));N=len(angles)
 # Each rectangular armored cell surrounds an open circular tube, with depth behind muzzle plane.
 for layer in range(3):
  for i in range(N):
   a=angles[i];c=math.cos(a);s=math.sin(a)
   if layer==0:
    den=max(abs(c)/.95,abs(s)/1.14);x,y=c/den,s/den;z=0
   else:x,y=c*(.49 if layer==1 else .39),s*(.49 if layer==1 else .39);z=0 if layer==1 else -.65
   verts.append(tuple(rack@Vector((local.x+x,local.y+y,local.z+z))));labels.append('T01_Barrel%02d'%j)
 for layer in range(2):
  for i in range(N):faces.append((layer*N+i,layer*N+(i+1)%N,(layer+1)*N+(i+1)%N,(layer+1)*N+i));coords.append([(.015,.015)]*4)
 ob=obj('AA port %02d'%j,verts,faces,coords,labels,'palette');ob['muzzle']=name
# Join the two firing banks with continuous armor; keep a recessed front face.
cs=[(-1.23,-2.60,5.70),(1.23,-2.60,5.70),(1.23,1.95,5.70),(-1.23,1.95,5.70)]
obj('Launcher central armor bridge',[tuple(rack@Vector(p)) for p in cs],[(0,1,2,3)],[[ (.004,.004)]*4],['T01_Rack01']*4,'palette')
# Close housing perimeter behind the muzzle plate with tapered skirts.
vs=[];fs=[]
for z,x,ylo,yhi in [(5.69,4.97,-2.60,1.95),(1.0,3.6,-1.4,1.95)]:
 vs.extend([tuple(rack@Vector(p)) for p in [(-x,ylo,z),(x,ylo,z),(x,yhi,z),(-x,yhi,z)]])
for i in range(4):fs.append((i,(i+1)%4,(i+1)%4+4,i+4))
obj('Launcher continuous armor skirt',vs,fs,[[ (.004,.004)]*4]*4,['T01_Rack01']*8,'palette')

# Export per-triangle attributes from exactly these objects; source shapes remain editable.
for ob in parts:
 me=ob.data;me.calc_loop_triangles()
 # Source UV mapped to upper half of the combined texture; native UV to lower half.
 for uv in me.uv_layers.active.data:
  if ob['texture_kind']=='source':uv.uv.y=.5+.5*(uv.uv.y%1)
  elif ob['texture_kind']=='native':uv.uv.y=.5*(uv.uv.y%1)
  else:uv.uv=(.004,.504)
geo=[]
for ob in parts:
 me=ob.data;me.calc_loop_triangles();me.calc_tangents();gn={g.index:g.name for g in ob.vertex_groups}
 for tri in me.loop_triangles:
  rows=[]
  for li in tri.loops:
   loop=me.loops[li];v=me.vertices[loop.vertex_index];n=me.corner_normals[li].vector;t=loop.tangent;b=loop.bitangent;uv=list(me.uv_layers.active.data[li].uv);bone=gn[max(v.groups,key=lambda g:g.weight).group];rows.append(list(v.co)+list(n)+list(t)+list(b)+uv+uv+[bn[bone],0,0,0])
  geo.append(rows)
(w/'geometry.json').write_text(json.dumps({'triangles':geo,'ports':portcenters},separators=(',',':')),encoding='utf-8')
# Preview native coordinates as Blender Z-up.
for ob in parts:
 for v in ob.data.vertices:p=v.co.copy();v.co=(p.x,-p.z,p.y)
# Give each source/native/palette object a correct preview material after atlas mapping.
# Combined atlas is created before this script is run.
im=bpy.data.images.load(str(w/'atlas.png'));im.pack();mat.node_tree.nodes.get('Image Texture').image=im
s=bpy.context.scene;cam=s.camera;cam.location=(20,-28,18);target=Vector((0,0,4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=19;s.render.filepath=str(out/'UTAA-native-fit.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/'UTAA-native-fit.blend'));bpy.ops.render.render(write_still=True)
print('Exported',len(geo),'triangles')
