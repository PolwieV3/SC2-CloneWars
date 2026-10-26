import bpy
from pathlib import Path
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/outputs/SPHA-T');bpy.ops.wm.open_mainfile(filepath=str(r/'SPHA-T-animated-source.blend'))
m=bpy.data.materials.new('SPHA_Diffuse_Preview');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85;tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/spha/SPHT.png',check_existing=True);tex.image.pack();m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
for ob in bpy.data.objects:
 if ob.type=='MESH':ob.data.materials.clear();ob.data.materials.append(m)
bpy.ops.wm.save_as_mainfile(filepath=str(r/'SPHA-T-animated-source.blend'));bpy.context.scene.render.filepath=str(r/'SPHA-T-preview.png');bpy.ops.render.render(write_still=True)

