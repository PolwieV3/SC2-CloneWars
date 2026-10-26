import bpy, bmesh
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-inspection.blend'))
def material(name,color,metal=.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=.48
    return m
ivory=material('Republic warm armor',(.72,.74,.71),.25)
red=material('Republic crimson',(.35,.025,.035),.3)
dark=material('Gunmetal',(.085,.105,.12),.65)
glass=material('Dark armored vision panel',(.025,.09,.12),.55)
for o in list(bpy.data.objects):
    if o.type!='MESH':continue
    bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00005)
    # Collada contains reversed duplicates; merge and remove those before shading.
    seen={}
    for face in list(bm.faces):
        key=tuple(sorted(v.index for v in face.verts))
        if key in seen:bm.faces.remove(face)
        else:seen[key]=face
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(o.data); bm.free()
    o.data.materials.clear()
    sid=o.name.split('_')[-1]
    mat=ivory
    if o.name.startswith('fan') or sid in ['ID669','ID189','ID379']:mat=dark
    if sid=='ID124':mat=red
    if o.dimensions.y>.5 and o.dimensions.x<.3:mat=dark
    o.data.materials.append(mat)
    for p in o.data.polygons:p.material_index=0
def mesh(name,verts,faces,mat):
    m=bpy.data.meshes.new(name); m.from_pydata(verts,[],faces); m.update()
    o=bpy.data.objects.new(name,m); bpy.context.collection.objects.link(o); m.materials.append(mat)
    bevel=o.modifiers.new('Armor edge highlights','BEVEL'); bevel.width=.025; bevel.segments=2
    o.modifiers.new('Panel normals','WEIGHTED_NORMAL')
    return o
for x in [-1.06,.98]:
    # A broad base seals the entire former seat opening. The roof narrows inward.
    mesh('Enclosed engineering cabin',[(x-.77,.0,.57),(x+.77,.0,.57),(x+.77,1.78,.57),(x-.77,1.78,.57),(x-.56,.42,1.48),(x+.56,.42,1.48),(x+.56,1.55,1.48),(x-.56,1.55,1.48)],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7),(3,2,1,0)],ivory)
    mesh('Armored forward viewport',[(x-.46,.21,1.04),(x+.46,.21,1.04),(x+.46,.37,1.38),(x-.46,.37,1.38)],[(0,1,2,3)],glass)
    mesh('Crimson roof identification stripe',[(x-.13,.44,1.49),(x+.13,.44,1.49),(x+.13,1.53,1.49),(x-.13,1.53,1.49)],[(0,1,2,3)],red)
    for y in [.85,1.0,1.15]:
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x+.576,y,1.24)); o=bpy.context.object; o.name='Cabin side vent'; o.dimensions=(.025,.08,.17); o.data.materials.append(dark)
scene=bpy.context.scene; scene.world.color=(.25,.25,.25)
scene.view_settings.view_transform='AgX'
for o in bpy.data.objects:
    if o.type=='LIGHT':o.data.energy*=1.2
scene.render.resolution_x=1400; scene.render.resolution_y=1000; scene.cycles.samples=48
out=root/'outputs/ISP-Closed-Cockpit'; out.mkdir(exist_ok=True)
scene.render.filepath=str(out/'closed-cockpit-preview.png'); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/isp-warehouse/isp-closed-cockpit.blend'))
