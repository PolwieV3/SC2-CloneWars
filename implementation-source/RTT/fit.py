import bpy,json,sys,math,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/rtt';out=r/'outputs/RTT';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
rig=json.loads((w/'rig.json').read_text());bn={n:i for i,n in enumerate(rig['names'])};parts=[]
mat=bpy.data.materials.new('RTT shield atlas');mat.use_nodes=True;im=bpy.data.images.load(str(w/'atlas.png'));im.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.75;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
for ob in list(bpy.data.objects):
 if ob.type!='MESH' or ob.name in ['Collision','Barrel_00','Barrel_L','Barrel_R','Base_00','LandGear_L','LandGear_R','Line01']:
  bpy.data.objects.remove(ob,do_unlink=True);continue
 # Bake the imported rest pose before converting to native coordinates.
 dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev);old=ob.data;ob.data=me;ob.modifiers.clear();ob.parent=None
 for v in me.vertices:
  p=ob.matrix_world@v.co;v.co=(p.x*.43,p.z*.33+.35,-p.y*.33)
 ob.matrix_world=Matrix.Identity(4);me.materials.clear();me.materials.append(mat)
 for u in me.uv_layers.active.data:u.uv.y=.5+.5*(u.uv.y%1)
 ob['bone']=0;parts.append(ob)
native=scm_v7.read((w/'native/units.scd/units/UEF/UUL0201/UUL0201_lod0.win.scm').read_bytes())
verts=[];faces=[];uvs=[];ids=[]
for k in range(0,len(native['indices']),3):
 rows=[native['vertices'][i] for i in native['indices'][k:k+3]]
 if not all(v[16]!=0 for v in rows):continue
 start=len(verts);verts.extend([v[:3] for v in rows]);faces.append((start,start+1,start+2));uvs.extend([(v[12],.5*(1-v[13])) for v in rows]);ids.extend([v[16] for v in rows])
me=bpy.data.meshes.new('Native shield mechanism');me.from_pydata(verts,[],faces);me.update();layer=me.uv_layers.new()
for loop in me.loops:layer.data[loop.index].uv=uvs[loop.vertex_index]
ob=bpy.data.objects.new('Deploying shield mechanism',me);bpy.context.collection.objects.link(ob);me.materials.append(mat);bpy.data.objects.remove(ob,do_unlink=True)
for i,b in enumerate([]):
 group=ob.vertex_groups.get(str(b)) or ob.vertex_groups.new(name=str(b));group.add([i],1,'REPLACE')
# Double the plain hull visual dimensions; simulation and shield size stay unchanged.
for ob in parts:
 for v in ob.data.vertices:v.co *= 4.0
# Export native Y-up coordinates and UVs, plus editable preview in Blender Z-up.
geo=[]
for ob in parts:
 me=ob.data;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();me.calc_loop_triangles();me.calc_tangents();groups={g.index:int(g.name) if g.name.isdigit() else 0 for g in ob.vertex_groups}
 for tri in me.loop_triangles:
  rows=[]
  for li in tri.loops:
   loop=me.loops[li];v=me.vertices[loop.vertex_index];uv=list(me.uv_layers.active.data[li].uv);bone=ob.get('bone',groups[max(v.groups,key=lambda g:g.weight).group] if v.groups else 0);rows.append(list(v.co)+list(me.corner_normals[li].vector)+list(loop.tangent)+list(loop.bitangent)+uv+uv+[bone,0,0,0])
  geo.append(rows)
(w/'geometry.json').write_text(json.dumps({'triangles':geo},separators=(',',':')),encoding='utf-8')
for ob in parts:
 for v in ob.data.vertices:p=v.co.copy();v.co=(p.x,-p.z,p.y)
bpy.ops.object.camera_add(location=(52,-72,52));cam=bpy.context.object;target=Vector((0,0,10));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=60;bpy.context.scene.camera=cam
for loc,power in [((6,-8,12),1800),((-7,-3,8),1300),((2,8,10),1800)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=8;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1100;s.render.resolution_y=850;s.render.resolution_percentage=100;s.world.color=(.18,.18,.18);s.view_settings.view_transform='Standard';s.render.filepath=str(out/'RTT-shield-preview.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/'RTT-shield.blend'));bpy.ops.render.render(write_still=True)


