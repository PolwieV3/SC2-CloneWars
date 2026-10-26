import bpy,sys,json,struct,math
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parent.parent
project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(project/'tools'));import scm_v7
bpy.ops.wm.open_mainfile(filepath=str(root/'work/isp-warehouse/isp-native-arm-texture-r4.blend'))
out=root/'outputs/Field-Engineer-ISP-Test';out.mkdir(exist_ok=True)
ref=(root/'work/engineer-native/z_dlc1.scd/mods/DLC1/base/Units/UEF/UUL0003D1/UUL0003D1_lod0.win.scm').read_bytes();m=scm_v7.read(ref)
eng=scm_v7.read((root/'outputs/Engineer-ISP-Test/EngineerISP_lod0.win.scm').read_bytes())
bind=lambda model:[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed().inverted() for b in model['bones']]
oldworld=bind(m);ew=bind(eng);bn={n:i for i,n in enumerate(m['names'])}
world=[]
for name,old in zip(m['names'],oldworld):
    equivalent=name.replace('UUL0003D1','UUL0002')
    if equivalent in eng['names']:new=ew[eng['names'].index(equivalent)].copy()
    else:new=old.copy()
    world.append(new)
world[0]=Matrix.Identity(4)
convert=lambda p:Vector((p.x,p.z,-p.y))*4
gunmap={};muzzles={}
for label,prefix,ids,tips,center in [('Left','T02',[34,44,54,64,279,289,299,589,599,609,619],[34,54],(-.77,-1.57,.44)),('Right','T03',[74,84,94,104,309,319,329,629,639,649,659],[74,94],(.70,-1.57,.44))]:
    yaw=prefix;pitch=prefix+'_Barrel0'+('2' if prefix=='T02' else '3')
    world[bn[yaw]]=Matrix.Translation(convert(Vector(center)));world[bn[pitch]]=world[bn[yaw]].copy()
    for ident in ids:gunmap['NV_SwampSp_ID'+str(ident)]=bn[pitch]
    muzzles[label]=[]
    for j,ident in enumerate(tips,1):
        ob=bpy.data.objects['NV_SwampSp_ID'+str(ident)]
        points=[ob.matrix_world@v.co for v in ob.data.vertices];front=min(p.y for p in points)
        near=[p for p in points if abs(p.y-front)<.0001];tip=sum(near,Vector())/len(near)
        rear=max(p.y for p in points);backpoints=[p for p in points if abs(p.y-rear)<.0001];back=sum(backpoints,Vector())/len(backpoints)
        direction=(convert(tip)-convert(back)).normalized()
        heading=math.atan2(direction.x,direction.z);elevation=math.atan2(direction.y,math.hypot(direction.x,direction.z))
        name=prefix+'_muzzle_0'+str(j);world[bn[name]]=Matrix.Translation(convert(tip))@Matrix.Rotation(heading,4,'Y')@Matrix.Rotation(-elevation,4,'X')
        muzzles[label].append({'bone':name,'native_position':list(convert(tip)),'barrel_direction':list(direction)})
# Fit the native antenna to the same transformed arm mount as the working Engineer.
arm_old=oldworld[bn['Turret01']].translation;arm_new=world[bn['Turret01']].translation
pole_offset=arm_new-.64*arm_old
vs=[];inds=[];matdraw=[];lookups=[{},{}]
def append(row,slot):
    key=struct.pack('<16f4B',*row);lookup=lookups[slot]
    if key not in lookup:lookup[key]=len(vs);vs.append(row)
    inds.append(lookup[key])
conv=lambda p:(p.x,p.z,-p.y)
for arm in [False,True]:
    starti=len(inds);startv=len(vs)
    for ob in sorted(bpy.data.objects,key=lambda x:x.name):
        if ob.type!='MESH' or ob.hide_render or ob.name.startswith('SC2 original ')!=arm:continue
        mesh=ob.data;mesh.calc_loop_triangles();mesh.calc_tangents()
        name=ob.name.removeprefix('SC2 original ').replace('UUL0002','UUL0003D1')
        bone=bn[name] if arm else gunmap.get(ob.name,0)
        for tri in mesh.loop_triangles:
            for li in tri.loops:
                loop=mesh.loops[li];p=ob.matrix_world@mesh.vertices[loop.vertex_index].co;uv=list(mesh.uv_layers.active.data[li].uv)
                row=list(Vector(conv(p))*4)+list(conv(mesh.corner_normals[li].vector))+list(conv(loop.tangent))+list(conv(loop.bitangent))+uv+uv+[bone,0,0,0]
                append(row,int(arm))
    if arm:
        pole=[]
        for k in range(0,len(m['indices']),3):
            rows=[m['vertices'][j] for j in m['indices'][k:k+3]]
            if not all(r[16]==bn['Turret01'] for r in rows) or max(r[1] for r in rows)<19.05:continue
            for row in rows:
                row=list(row);p=Vector(row[:3])*.64+pole_offset;row[:3]=list(p);row[16]=0;append(row,1);pole.append(p)
        assert pole
        tip=max(pole,key=lambda p:p.y).copy();tip.x=sum(p.x for p in pole if abs(p.y-tip.y)<.0001)/sum(abs(p.y-tip.y)<.0001 for p in pole)
    matdraw.append(((len(inds)-starti)//3,starti,startv,len(vs)-startv))
world[bn['Tread02']]=Matrix.Translation(tip)
rig=bytearray(ref)
for i,bone in enumerate(m['bones']):
    parent=bone[24];local=world[i] if parent<0 else world[parent].inverted()@world[i];inv=world[i].inverted()
    # Native quaternion ordering is w,x,y,z (verified against source joints).
    q=local.to_quaternion();row=[inv[a][b] for b in range(4) for a in range(4)]+list(local.translation)+list(q)+list(bone[23:])
    scm_v7.BONE.pack_into(rig,m['header'][2]+i*scm_v7.BONE.size,*row)
raw=scm_v7.write(bytes(rig),vs,inds,matdraw);(out/'FieldEngineerISP_lod0.win.scm').write_bytes(raw)
(out/'rig-validation.json').write_text(json.dumps({'mesh':scm_v7.summary(raw),'native_names':m['names'],'muzzles':muzzles,'gun_object_skin_mapping':gunmap,'beacon_tip_native':list(tip),'beacon_offset_world_units':list(tip*.1),'beacon_triangles':len(pole)//3,'regular_engineer_mesh_hash':scm_v7.summary((root/'outputs/Engineer-ISP-Test/EngineerISP_lod0.win.scm').read_bytes())['sha256']},indent=2))
print('Exported Field Engineer',len(vs),len(inds)//3,'beacon',list(tip*.1))
