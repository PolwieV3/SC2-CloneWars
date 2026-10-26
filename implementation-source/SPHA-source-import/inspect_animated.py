import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');o=r/'outputs/SPHA-T';w=r/'work/spha';src=o/'Animated-source'
sys.path.insert(0,str(r/'work/archanist/tools/Blender-ALAMO-Plugin-for-4.0-master'));import io_alamo_tools;io_alamo_tools.register();bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_mesh.alo(filepath=str(src/'Cv_SPHT.ALO').replace('/','\\'),importAnimations=False)
sys.path.insert(0,str(w));import old_ala
arm=next(a for a in bpy.data.objects if a.type=='ARMATURE');clips=[old_ala.load(src/name,arm) for name in ['Cv_SPHT_idle_00.ala','Cv_SPHT_deploy_00.ala','Cv_SPHT_undeploy_00.ala','Cv_SPHT_move_00.ala']]
meshes=[a for a in bpy.data.objects if a.type=='MESH'];arms=[a for a in bpy.data.objects if a.type=='ARMATURE'];report={'decoded_clips':clips,'meshes':[],'armatures':[],'actions':[],'images':[]}
for a in meshes:a.data.calc_loop_triangles();report['meshes'].append({'name':a.name,'vertices':len(a.data.vertices),'triangles':len(a.data.loop_triangles),'groups':len(a.vertex_groups),'materials':[m.name for m in a.data.materials]})
for a in arms:report['armatures'].append({'name':a.name,'bones':[b.name for b in a.data.bones]})
for a in bpy.data.actions:report['actions'].append({'name':a.name,'frames':list(a.frame_range)})
for i in bpy.data.images:
 report['images'].append({'name':i.name,'path':i.filepath,'size':list(i.size)})
 if i.has_data:i.pack()
s=bpy.context.scene
if arms and bpy.data.actions:
 arm=arms[0];walk=next((a for a in bpy.data.actions if 'move_00' in a.name),None)
 if walk:
  arm.animation_data.action=walk
  if hasattr(walk,'slots') and len(walk.slots):arm.animation_data.action_slot=walk.slots[0]
  states=[]
  for f in [walk.frame_range[0],sum(walk.frame_range)/2,walk.frame_range[1]]:
   s.frame_set(int(f));states.append({'frame':f,'positions':{b.name:list(b.matrix.translation) for b in arm.pose.bones}})
  report['walk_samples']=states
  report['walk_max_bone_translation_change']=max((Vector(states[0]['positions'][n])-Vector(states[1]['positions'][n])).length for n in states[0]['positions'])
  s.frame_set(int(walk.frame_range[0]))
for a in meshes:
 a.hide_render=a.name.startswith(('Box','CollMesh','Subshadow'));a.hide_set(a.hide_render)
points=[a.matrix_world@Vector(c) for a in meshes for c in a.bound_box];lo=Vector([min(p[k] for p in points) for k in range(3)]);hi=Vector([max(p[k] for p in points) for k in range(3)]);center=(lo+hi)/2;size=max(hi-lo);report['bounds']={'min':list(lo),'max':list(hi)}
# ALO materials use game-specific shaders: connect their diffuse texture for preview.
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 nodes=mat.node_tree.nodes;tex=next((n for n in nodes if n.type=='TEX_IMAGE' and n.image and n.image.has_data),None);bs=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
 if tex and bs:mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.8
s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1100;s.render.resolution_y=750;s.render.resolution_percentage=100;s.world.color=(.25,.25,.25)
bpy.ops.object.camera_add(location=center+Vector((1.2,-1.6,1.0))*size);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.35;s.camera=cam
for delta in [(1,-1,2),(-1,0,1),(0,1,2)]:
 bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*size);a=bpy.context.object;a.data.energy=60*size*size;a.data.size=size;a.rotation_euler=(center-a.location).to_track_quat('-Z','Y').to_euler()
(o/'Animated-model-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(o/'SPHA-T-animated-source.blend'));s.render.filepath=str(o/'SPHA-T-preview.png');bpy.ops.render.render(write_still=True)


