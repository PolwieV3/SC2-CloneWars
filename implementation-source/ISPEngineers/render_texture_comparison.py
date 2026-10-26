import bpy, sys, hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
out=root/'outputs/ISP-Texture-Enhancement'; out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-inspection.blend'))
def geometry_hash():
    return hashlib.sha256(repr([(o.name,[tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(map(tuple,o.matrix_world)) ) for o in sorted(bpy.data.objects,key=lambda x:x.name) if o.type=='MESH']).encode()).hexdigest()
original_hash=geometry_hash()
# SketchUp exported opposite sides with different UVs. Preserve every vertex
# and face; transfer the explicitly mapped front-side UVs to coincident backs.
candidates={}
def cornerkey(o,vi):return tuple(round(x,5) for x in (o.matrix_world@o.data.vertices[vi].co))
for o in bpy.data.objects:
    if o.type!='MESH' or not o.data.uv_layers.active:continue
    uv=o.data.uv_layers.active.data
    for p in o.data.polygons:
        if o.data.materials[p.material_index].name!='ID125':continue
        key=tuple(sorted(cornerkey(o,vi) for vi in p.vertices))
        candidates[key]={cornerkey(o,o.data.loops[li].vertex_index):tuple(uv[li].uv) for li in p.loop_indices}
uv_fixed=0
for o in bpy.data.objects:
    if o.type!='MESH' or not o.data.uv_layers.active:continue
    for p in o.data.polygons:
        key=tuple(sorted(cornerkey(o,vi) for vi in p.vertices))
        if key not in candidates:continue
        uv=o.data.uv_layers.active.data
        for li in p.loop_indices:
            correct=candidates[key][cornerkey(o,o.data.loops[li].vertex_index)]
            if tuple(uv[li].uv)!=correct:uv_fixed+=1
            uv[li].uv=correct
assert geometry_hash()==original_hash
scene=bpy.context.scene; scene.view_settings.view_transform='AgX'; scene.world.color=(.3,.3,.3)
scene.render.resolution_x=1400; scene.render.resolution_y=1000; scene.cycles.samples=48
for o in bpy.data.objects:
    if o.type=='LIGHT':o.data.energy*=1.5
scene.render.filepath=str(out/'original-textures.png'); bpy.ops.render.render(write_still=True)
enhanced=bpy.data.images.load(str(out/'enhanced-atlas.png'),check_existing=True)
for m in bpy.data.materials:
    if m.use_nodes:
        for node in m.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:node.image=enhanced
assert geometry_hash()==original_hash
scene.render.filepath=str(out/'enhanced-textures.png'); bpy.ops.render.render(write_still=True)
assert geometry_hash()==original_hash
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/isp-warehouse/isp-open-enhanced-textures.blend'))
(out/'verification.json').write_text(json.dumps({'date':'2026-10-26','geometry_before_sha256':original_hash,'geometry_after_sha256':geometry_hash(),'geometry_unchanged':True,'uv_corners_corrected':uv_fixed,'cockpit':'Original open cockpit; no crew added','texture_sha256':hashlib.sha256((out/'enhanced-atlas.png').read_bytes()).hexdigest(),'installed':False,'runtime_tested':False},indent=2))
