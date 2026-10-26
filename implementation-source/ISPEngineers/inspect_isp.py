import bpy, xml.etree.ElementTree as E, json
from pathlib import Path
from mathutils import Matrix, Vector
base=Path(__file__).resolve().parent/'isp-warehouse'
root=E.parse(base/'model.dae').getroot(); ns={'c':'http://www.collada.org/2005/11/COLLADASchema'}
find=lambda e,p:e.find(p,ns)
all=lambda e,p:e.findall(p,ns)
ids={e.get('id'):e for e in root.iter() if e.get('id')}
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
mats={}
for mat in all(root,'.//c:library_materials/c:material'):
    effect=ids[find(mat,'c:instance_effect').get('url')[1:]]
    bm=bpy.data.materials.new(mat.get('id')); bm.use_nodes=True
    shader=bm.node_tree.nodes.get('Principled BSDF'); shader.inputs['Roughness'].default_value=.7
    geo_node=bm.node_tree.nodes.new('ShaderNodeNewGeometry')
    transparent=bm.node_tree.nodes.new('ShaderNodeBsdfTransparent')
    mix=bm.node_tree.nodes.new('ShaderNodeMixShader')
    bm.node_tree.links.new(geo_node.outputs['Backfacing'],mix.inputs[0])
    bm.node_tree.links.new(shader.outputs[0],mix.inputs[1])
    bm.node_tree.links.new(transparent.outputs[0],mix.inputs[2])
    bm.node_tree.links.new(mix.outputs[0],bm.node_tree.nodes.get('Material Output').inputs['Surface'])
    tex=find(effect,'.//c:diffuse/c:texture')
    if tex is not None:
        params={p.get('sid'):p for p in all(effect,'.//c:newparam')}
        surface=find(params[tex.get('texture')],'c:sampler2D/c:source').text
        image_id=find(params[surface],'c:surface/c:init_from').text
        imagepath=base/find(ids[image_id],'c:init_from').text
        im=bpy.data.images.load(str(imagepath),check_existing=True)
        node=bm.node_tree.nodes.new('ShaderNodeTexImage'); node.image=im
        bm.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
    else:
        color=find(effect,'.//c:diffuse/c:color')
        if color is not None: shader.inputs['Base Color'].default_value=tuple(map(float,color.text.split()))
    mats[mat.get('id')]=bm
objects=[]
def walk(node,parent=Matrix.Identity(4)):
    matrix=find(node,'c:matrix'); world=parent
    if matrix is not None:
        vals=list(map(float,matrix.text.split())); world=parent@Matrix([vals[i:i+4] for i in range(0,16,4)])
    for inst in all(node,'c:instance_geometry'):
        geo=ids[inst.get('url')[1:]]; mesh=find(geo,'c:mesh')
        sources={}
        for source in all(mesh,'c:source'):
            if find(source,'c:float_array') is None: continue
            vals=list(map(float,find(source,'c:float_array').text.split())); stride=int(find(source,'c:technique_common/c:accessor').get('stride'))
            sources[source.get('id')]=[vals[i:i+stride] for i in range(0,len(vals),stride)]
        vertsmap={v.get('id'):find(v,'c:input').get('source')[1:] for v in all(mesh,'c:vertices')}
        bindings={m.get('symbol'):mats[m.get('target')[1:]] for m in all(inst,'.//c:instance_material')}
        positions=[]; faces=[]; uvs=[]; slots=[]
        for tri in all(mesh,'c:triangles'):
            inp={x.get('semantic'):(int(x.get('offset')),x.get('source')[1:]) for x in all(tri,'c:input')}
            stride=max(x[0] for x in inp.values())+1; vals=list(map(int,find(tri,'c:p').text.split()))
            offset,src=inp['VERTEX']; src=vertsmap[src]
            for start in range(0,len(vals),stride*3):
                face=[]
                for k in range(3):
                    idx=start+k*stride; face.append(len(positions)); positions.append(sources[src][vals[idx+offset]][:3])
                    if 'TEXCOORD' in inp:
                        uo,us=inp['TEXCOORD']; uvs.append(sources[us][vals[idx+uo]][:2])
                    else:uvs.append([0,0])
                faces.append(face); slots.append(tri.get('material'))
        bm=bpy.data.meshes.new(geo.get('id')); bm.from_pydata(positions,[],faces); bm.update()
        obj=bpy.data.objects.new(node.get('name','part')+'_'+geo.get('id'),bm); bpy.context.collection.objects.link(obj); obj.matrix_world=world
        for material in bindings.values(): bm.materials.append(material)
        keys=list(bindings)
        for poly,slot in zip(bm.polygons,slots):poly.material_index=keys.index(slot) if slot in keys else 0
        uv=bm.uv_layers.new()
        for poly in bm.polygons:
            for li in poly.loop_indices:uv.data[li].uv=uvs[bm.loops[li].vertex_index]
        objects.append(obj)
    for child in all(node,'c:node'):walk(child,world)
    for inst in all(node,'c:instance_node'):walk(ids[inst.get('url')[1:]],world)
walk(find(root,'.//c:visual_scene'))
points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
lo=Vector([min(p[i] for p in points) for i in range(3)]); hi=Vector([max(p[i] for p in points) for i in range(3)])
center=(lo+hi)/2; span=max(hi-lo)
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.world.color=(.3,.3,.3)
bpy.ops.object.camera_add(location=center+Vector((1,-1,.8))*span*1.35)
camera=bpy.context.object; camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.type='ORTHO'; camera.data.ortho_scale=span*1.5; scene.camera=camera
for pos,power,size in [((0,-1,2),1800,8),((1,1,1),1100,6)]:
    bpy.ops.object.light_add(type='AREA',location=center+Vector(pos)*span); light=bpy.context.object; light.data.energy=power; light.data.shape='DISK'; light.data.size=size; light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'
output=Path(__file__).resolve().parent.parent/'outputs/ISP-Inspection'; output.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(output/'isp-source-preview.png'); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(base/'isp-inspection.blend'))
(base/'geometry-inspection.json').write_text(json.dumps({'mesh_objects':len(objects),'triangles_including_backfaces':sum(len(o.data.polygons) for o in objects),'bounds_source_units':list(hi-lo),'skinned':False,'source_groups':[n.get('name') for n in all(root,'.//c:library_nodes//c:node')],'objects':[{'name':o.name,'triangles':len(o.data.polygons)} for o in objects]},indent=2))
