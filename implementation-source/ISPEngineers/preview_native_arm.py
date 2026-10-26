import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parent.parent
project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(project/'implementation-source/shared-pipeline'));import scm_v7
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-open-enhanced-textures.blend'))
out=root/'outputs/ISP-Native-Arm';out.mkdir(exist_ok=True)
# Use original downloaded atlas, not the generated remaster.
original=bpy.data.images.load(str(root/'work/isp-warehouse/model/_02_-_Default1.PNG'),check_existing=True)
for m in bpy.data.materials:
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE':n.image=original
spine=bpy.data.objects.get('NV_SwampSp_ID124');spine.hide_render=True;spine.hide_viewport=True
native=root/'work/engineer-native/units.scd/units/UEF/UUL0002'
m=scm_v7.read((native/'UUL0002_lod0.win.scm').read_bytes());names=m['names']
bind=[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed().inverted() for b in m['bones']]
bn={n:i for i,n in enumerate(names)};pivot=bind[bn['Turret01']].translation
mat=bpy.data.materials.new('Original SC2 Engineer arm diffuse');mat.use_nodes=True
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(native/'UUL0002_Diffuse.win.dds'))
shader=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color']);shader.inputs['Roughness'].default_value=.65
keep={'Turret01','UUL0002_MidLever','UUL0002_Lever01','T01_Barrel01'}
scale=.16; anchor=Vector((-.04,.65,.32)); arm_parts=[]
def convert(p):
    q=(p-pivot)*scale
    return Vector((q.x,-q.z,q.y))+anchor
for bone in keep:
    vs=[];fs=[];uv=[]
    for i in range(0,len(m['indices']),3):
        rows=[m['vertices'][j] for j in m['indices'][i:i+3]]
        if not all(names[v[16]]==bone for v in rows):continue
        start=len(vs);vs.extend([tuple(convert(Vector(v[:3]))) for v in rows]);fs.append((start,start+1,start+2));uv.extend([v[12:14] for v in rows])
    mesh=bpy.data.meshes.new(bone);mesh.from_pydata(vs,[],fs);mesh.update();layer=mesh.uv_layers.new()
    for poly in mesh.polygons:
        for li in poly.loop_indices:layer.data[li].uv=uv[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new('SC2 original '+bone,mesh);bpy.context.collection.objects.link(ob);mesh.materials.append(mat);arm_parts.append(ob)
scene=bpy.context.scene;scene.view_settings.view_transform='AgX';scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.cycles.samples=48
scene.render.filepath=str(out/'native-arm-fit.png');bpy.ops.render.render(write_still=True)
# Offline pose study using native controller goals, not a runtime test.
posed=[];angles={'UUL0002_MidLever':30,'UUL0002_Lever01':-120,'T01_Barrel01':90}
for i,b in enumerate(m['bones']):
    parent=b[24]; local=bind[i] if parent<0 else bind[parent].inverted()@bind[i]
    rot=Matrix.Rotation(math.radians(angles.get(names[i],0)),4,'X')
    posed.append(local@rot if parent<0 else posed[parent]@local@rot)
for ob in arm_parts:
    bone=ob.name.removeprefix('SC2 original ');i=bn[bone];delta=posed[i]@bind[i].inverted()
    for v in ob.data.vertices:
        q=(v.co-anchor)/scale; native_pos=Vector((q.x,q.z,-q.y))+pivot
        v.co=convert(delta@native_pos)
scene.render.filepath=str(out/'native-arm-deployed-study.png');bpy.ops.render.render(write_still=True)
for ob in arm_parts:
    bone=ob.name.removeprefix('SC2 original ');i=bn[bone];delta=bind[i]@posed[i].inverted()
    for v in ob.data.vertices:
        q=(v.co-anchor)/scale; v.co=convert(delta@(Vector((q.x,q.z,-q.y))+pivot))
# Preserve rig reference and original material paths for later, without claiming animation validation.
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-fit.blend'))
(out/'fit-notes.json').write_text(json.dumps({'date':'2026-10-26','hull':'Downloaded ISP, original texture with export UV corrections','arm':'Native UUL0002 LOD0 triangles and original diffuse; Turret01, MidLever, Lever01, T01_Barrel01','layout':'Center spine hidden; arm in center lane','preview_only':True,'rig_animation_verified':False,'native_arm_scale_relative_to_source':scale,'field_engineer':'Retain separate native gameplay and mirrored weapon controllers; beacon not yet fitted','installed':False},indent=2))
print('Pivots',[(n,list(convert(bind[bn[n]].translation))) for n in keep])
