import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-texture-r3.blend'))
changes={}
for ob in bpy.data.objects:
    if ob.type!='MESH' or ob.hide_render or ob.name.startswith('SC2 original '):continue
    uv=ob.data.uv_layers.active.data; repaired=0
    for face in ob.data.polygons:
        coords=[uv[li].uv for li in face.loop_indices]
        if not any(c.x<-.001 or c.x>1.001 or c.y<-.001 or c.y>1.001 for c in coords):continue
        # Residual SketchUp back/edge faces have object-space planar coordinates
        # instead of atlas UVs. Map those faces to the atlas's existing steel panel.
        positions=[ob.data.vertices[ob.data.loops[li].vertex_index].co for li in face.loop_indices]
        normal=face.normal; axes=sorted(range(3),key=lambda i:abs(normal[i]))[:2]
        mins=[min(p[a] for p in positions) for a in axes];maxs=[max(p[a] for p in positions) for a in axes]
        for li,p in zip(face.loop_indices,positions):
            s=(p[axes[0]]-mins[0])/max(maxs[0]-mins[0],.00001)
            t=(p[axes[1]]-mins[1])/max(maxs[1]-mins[1],.00001)
            uv[li].uv=(.81+.16*s,.925+.055*t)
        repaired+=1
    if repaired:changes[ob.name]=repaired
out=root/'outputs/ISP-Refinement-4';out.mkdir(exist_ok=True)
(out/'rear-uv-repairs.json').write_text(json.dumps(changes,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-texture-r4.blend'))
print(json.dumps(changes))
