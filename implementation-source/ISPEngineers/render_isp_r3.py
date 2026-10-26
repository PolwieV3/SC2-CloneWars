import bpy,json,bmesh
from pathlib import Path
root=Path(__file__).resolve().parent.parent
out=root/'outputs/ISP-Texture-R3';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-texture-r2.blend'))
im=bpy.data.images.load(str(out/'hull-atlas-r3.png'))
for m in bpy.data.materials:
    if m.name not in ['ID8','ID125']:continue
    for n in m.node_tree.nodes:
        if n.type=='TEX_IMAGE':n.image=im
    shader=m.node_tree.nodes.get('Principled BSDF')
    texture=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
    curves=m.node_tree.nodes.new('ShaderNodeRGBCurve');curves.label='Recover dark painted surface detail'
    curve=curves.mapping.curves[3];curve.points[0].location=(0,.035);curve.points.new(.12,.18);curve.points.new(.4,.4);curves.mapping.update()
    m.node_tree.links.new(texture.outputs['Color'],curves.inputs['Color']);m.node_tree.links.new(curves.outputs['Color'],shader.inputs['Base Color'])
    m.node_tree.links.new(shader.outputs[0],m.node_tree.nodes.get('Material Output').inputs['Surface'])
# Remove coplanar opposite-side export duplicates while keeping the outward
# atlas mapping. These were self-shadowing the very thin platform surfaces.
for ob in bpy.data.objects:
    if ob.type!='MESH' or not ob.name.startswith(('NV_SwampSp','fan_')):continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.verts.index_update()
    groups={}
    for face in list(bm.faces):groups.setdefault(tuple(sorted(v.index for v in face.verts)),[]).append(face)
    for faces in groups.values():
        faces.sort(key=lambda f:ob.data.materials[f.material_index].name=='ID125',reverse=True)
        for face in faces[1:]:bm.faces.remove(face)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
scene=bpy.context.scene;scene.cycles.samples=64
scene.render.filepath=str(out/'isp-dark-area-refinement.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-texture-r3.blend'))
(out/'Notes.txt').write_text('Revision 3: built-in image generation edits dark seat, mechanism and platform regions while preserving UV registration. Prompt: raise near-black surfaces to readable charcoal/gunmetal, clarify existing details; keep gray armor and all island layouts unchanged. A preview material curve additionally lifts near-black albedo without changing geometry, lighting or the SC2 arm. No installation or runtime test.\n')
