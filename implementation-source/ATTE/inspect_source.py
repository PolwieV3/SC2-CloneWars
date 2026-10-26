import bpy,json,math
from pathlib import Path
from mathutils import Vector
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/atte';o=r/'outputs/AT-TE'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'C:/Users/gavad/Downloads/UEF/Ground/at-te_walker_animated.glb')
meshes=[a for a in bpy.data.objects if a.type=='MESH'];arms=[a for a in bpy.data.objects if a.type=='ARMATURE']
report={'objects':[],'armatures':[],'actions':[],'images':[]}
for a in meshes:report['objects'].append({'name':a.name,'vertices':len(a.data.vertices),'triangles':sum(len(p.vertices)-2 for p in a.data.polygons),'groups':[g.name for g in a.vertex_groups]})
for a in arms:report['armatures'].append({'name':a.name,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local)} for b in a.data.bones]})
for a in bpy.data.actions:report['actions'].append({'name':a.name,'frames':list(a.frame_range)})
for i in bpy.data.images:
 if i.has_data:
  report['images'].append({'name':i.name,'size':list(i.size)});i.pack()
s=bpy.context.scene;s.frame_set(1)
points=[a.matrix_world@Vector(c) for a in meshes for c in a.bound_box];lo=Vector([min(p[k] for p in points) for k in range(3)]);hi=Vector([max(p[k] for p in points) for k in range(3)]);center=(lo+hi)*.5;size=max(hi-lo);report['bounds']={'min':list(lo),'max':list(hi),'size':list(hi-lo)}
# Evaluate the imported deformation at several points in the source clip.
samples=[]
for f in [1,8,16,24,32]:
 s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();vs=[]
 for ob in meshes:
  ev=ob.evaluated_get(dg);m=ev.to_mesh();vs.extend([tuple(ev.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear()
 samples.append({'frame':f,'vertices':len(vs),'first_vertex':vs[0] if vs else None,'bounds_min':[min(v[k] for v in vs) for k in range(3)],'bounds_max':[max(v[k] for v in vs) for k in range(3)]})
report['animation_samples']=samples;s.frame_set(1)
s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.24,.28,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
bpy.ops.object.camera_add(location=center+Vector((1.2,-1.7,1.0))*size);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.45;s.camera=cam
for delta,power in [((1,-1,2),1800),((-1,-.2,1),1200),((0,1,1.5),1600)]:
 bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*size);a=bpy.context.object;a.data.energy=power*size*size/30;a.data.shape='DISK';a.data.size=size;a.rotation_euler=(center-a.location).to_track_quat('-Z','Y').to_euler()
(o/'Source-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(o/'AT-TE-source.blend'));s.render.filepath=str(o/'AT-TE-source.png');bpy.ops.render.render(write_still=True)
