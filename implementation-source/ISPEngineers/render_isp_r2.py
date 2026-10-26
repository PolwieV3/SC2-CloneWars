import bpy,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
out=root/'outputs/ISP-Texture-R2';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-fit.blend'))
def meshhash():
    return hashlib.sha256(repr([(o.name,[tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]) for o in sorted(bpy.data.objects,key=lambda o:o.name) if o.type=='MESH']).encode()).hexdigest()
before=meshhash();scene=bpy.context.scene;scene.cycles.samples=64
scene.render.filepath=str(out/'before.png');bpy.ops.render.render(write_still=True)
image=bpy.data.images.load(str(out/'hull-atlas-r2.png'),check_existing=True)
for material in bpy.data.materials:
    if material.name not in ['ID8','ID125']:continue
    for node in material.node_tree.nodes:
        if node.type=='TEX_IMAGE':node.image=image
    shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.65;shader.inputs['Metallic'].default_value=.15
scene.render.filepath=str(out/'isp-native-arm-texture-r2.png');bpy.ops.render.render(write_still=True)
assert meshhash()==before
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-texture-r2.blend'))
(out/'verification.json').write_text(json.dumps({'geometry_unchanged':True,'geometry_sha256':before,'arm_texture_unchanged':True,'hull_atlas_sha256':hashlib.sha256((out/'hull-atlas-r2.png').read_bytes()).hexdigest(),'installed':False,'runtime_verified':False},indent=2))
