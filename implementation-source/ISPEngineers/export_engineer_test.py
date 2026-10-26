import bpy,sys,json,struct
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parent.parent
project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(project/'tools'));import scm_v7
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-texture-r4.blend'))
refpath=root/'work/engineer-native/units.scd/units/UEF/UUL0002/UUL0002_lod0.win.scm'
ref=refpath.read_bytes();m=scm_v7.read(ref)
bind=[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed().inverted() for b in m['bones']]
pivot=bind[m['names'].index('Turret01')].translation
anchor=Vector((-.04,.65,.32));native_anchor=Vector((anchor.x,anchor.z,-anchor.y))*4
offset=native_anchor-.64*pivot
world=[]
for i,mat in enumerate(bind):
    new=mat.copy()
    if i:new.translation=mat.translation*.64+offset
    world.append(new)
rig=bytearray(ref)
for i,bone in enumerate(m['bones']):
    inv=world[i].inverted();parent=bone[24]
    local=world[i] if parent<0 else world[parent].inverted()@world[i]
    row=[inv[a][b] for b in range(4) for a in range(4)]+list(local.translation)+list(bone[19:])
    scm_v7.BONE.pack_into(rig,m['header'][2]+i*scm_v7.BONE.size,*row)
rawref=bytes(rig);scm_v7.read(rawref)
vertices=[];indices=[];materials=[];counts={}
for arm in [False,True]:
    firstindex=len(indices);firstvertex=len(vertices);lookup={}
    for ob in sorted(bpy.data.objects,key=lambda o:o.name):
        if ob.type!='MESH' or ob.hide_render or ob.name.startswith('SC2 original ')!=arm:continue
        mesh=ob.data;mesh.calc_loop_triangles();mesh.calc_tangents()
        bone=m['names'].index(ob.name.removeprefix('SC2 original ')) if arm else 0
        for tri in mesh.loop_triangles:
            for li in tri.loops:
                loop=mesh.loops[li];v=ob.matrix_world@mesh.vertices[loop.vertex_index].co
                normal=mesh.corner_normals[li].vector;tangent=loop.tangent;bitangent=loop.bitangent
                conv=lambda v:(v.x,v.z,-v.y)
                uv=mesh.uv_layers.active.data[li].uv
                row=list(Vector(conv(v))*4)+list(conv(normal))+list(conv(tangent))+list(conv(bitangent))+list(uv)+list(uv)+[bone,0,0,0]
                key=struct.pack('<16f4B',*row)
                if key not in lookup:lookup[key]=len(vertices);vertices.append(row)
                indices.append(lookup[key])
        counts[ob.name]=len(mesh.loop_triangles)
    materials.append(((len(indices)-firstindex)//3,firstindex,firstvertex,len(vertices)-firstvertex))
out=root/'outputs/Engineer-ISP-Test';out.mkdir(exist_ok=True)
raw=scm_v7.write(rawref,vertices,indices,materials)
(out/'EngineerISP_lod0.win.scm').write_bytes(raw)
(out/'rig-validation.json').write_text(json.dumps({'names':m['names'],'native_joint_names_and_parents_preserved':True,'arm_bind_translation_scale':.64,'arm_world_translation_offset':list(offset),'new_bind_positions':{n:list(w.translation) for n,w in zip(m['names'],world)},'parts':counts,'mesh':scm_v7.summary(raw),'skin_assignments':{n:sum(v[16]==i for v in vertices) for i,n in enumerate(m['names'])}},indent=2))
print('Exported',len(vertices),'vertices',len(indices)//3,'triangles')
