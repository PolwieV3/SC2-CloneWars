"""Package project-authored TX-130 geometry and palette textures as an asset overlay."""
import math
import copy
import hashlib
import json
import pathlib
import struct
import zipfile

from snapshot import ROOT
import scm_v7
from poc_unit import LiteralTable, merge, differences

NAME='zz_SC2_CloneWars_TX130_Model.scd'
BASE=ROOT/'local/reference/UUL0101/units/units/UEF/UUL0101'
BUILD=ROOT/'local/build/tx130'


def dds(kind, palette, size=512):
    levels=[];width=size
    while width:
        pixels=bytearray()
        for y in range(width):
            for x in range(width):
                color_index=min(y*4//width,3)*4+min(x*4//width,3)
                if kind=='Diffuse':
                    r,g,b=palette[color_index][1]
                    # Subtle procedural paint finish; no external texture image used.
                    variation=((x*17+y*31)%7-3) if width>=16 else 0
                    r,g,b=[max(0,min(255,c+variation)) for c in (r,g,b)];a=255
                elif kind=='Normal':r,g,b,a=128,128,255,255
                elif kind=='Mask':r,g,b,a=12,0,24,220
                elif kind=='Team':r,g,b,a=0,0,0,225 if color_index==7 else 0
                else:raise ValueError(kind)
                if kind=='Diffuse' and color_index in {12,14}:
                    u=(x*4/width)%1;v=(y*4/width)%1
                    if color_index==14:
                        dx=(u-.5)*1.7;dz=(v-.5)*2.7;radius=math.hypot(dx,dz);angle=math.atan2(dz,dx)
                        r,g,b=palette[1][1]
                        if radius<.70:
                            r,g,b=palette[15][1]
                            spoke=abs((angle+math.pi/8)%(math.pi/4)-math.pi/8)
                            if radius<.14 or (.14<radius<.53 and spoke<.115) or (.57<radius<.68 and spoke<.31):r,g,b=palette[9][1]
                    else:
                        dx=(u-.5)*1.9;dz=(v-.5)*1.9;radius=math.hypot(dx,dz)
                        r,g,b=palette[0][1]
                        if radius<.79:
                            r,g,b=palette[12][1]
                            if radius>.59 and abs(dz)>.12:r,g,b=palette[1][1]
                pixels.extend(bytes((b,g,r,a)))
        levels.append(pixels);width//=2
    values=[124,0x2100f,size,size,size*4,0,len(levels)]+[0]*11
    values += [32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000]
    values += [0x401008,0,0,0,0]
    assert len(values)==31
    return b'DDS '+struct.pack('<31I',*values)+b''.join(levels)


def skin_index(name, reference, full_reference):
    names=reference['names']
    while name not in names or names.index(name)>=reference['header'][3]:
        node=full_reference['names'].index(name);parent=full_reference['bones'][node][24]
        if parent<0:raise ValueError(f'No skinning ancestor for {name}')
        name=full_reference['names'][parent]
    return names.index(name)


def main():
    if not (BUILD/'geometry-lod0.json').is_file():
        raise SystemExit('Generate the authored geometry with Blender first.')
    full=scm_v7.read((BASE/'UUL0101_LOD0.win.scm').read_bytes())
    payload={};meshes=[]
    for lod,filename in enumerate(['UUL0101_LOD0.win.scm','UUL0101_lod1.win.scm','UUL0101_lod2.win.scm']):
        original=(BASE/filename).read_bytes();reference=scm_v7.read(original)
        roundtrip=scm_v7.write(original,reference['vertices'],reference['indices'],[m[1:] for m in reference['materials']],reference['extra'])
        if roundtrip!=original:raise ValueError(f'Native reference round trip failed: {filename}')
        data=json.loads((BUILD/f'geometry-lod{lod}.json').read_text())
        vertices=[];indices=[];draws=[]
        for group in data['groups']:
            start_index=len(indices);start_vertex=len(vertices)
            for triangle in group:
                bone=skin_index(triangle['bone'],reference,full)
                for vertex_index,position in enumerate(triangle['positions']):
                    row=tuple(position+triangle['normal']+triangle['tangent']+triangle['binormal']+list(triangle['uvs'][vertex_index] if triangle.get('uvs') else triangle['uv'])*2+[bone,0,0,0])
                    indices.append(len(vertices));vertices.append(row)
            draws.append((len(group),start_index,start_vertex,len(vertices)-start_vertex))
        raw=scm_v7.write(original,vertices,indices,draws)
        native=scm_v7.read(raw)
        h=reference['header'];rig=original[h[2]:h[4]]
        if raw[h[2]:h[4]]!=rig:raise ValueError('Rig block changed')
        path='units/CloneWars/TX130/'+filename;payload[path]=raw
        payload[path.replace('.win.scm','.scm')]=raw
        meshes.append({'path':path,**scm_v7.summary(raw),'original_round_trip_byte_exact':True,
                       'native_skeleton_byte_exact':True,'rig_sha256':hashlib.sha256(rig).hexdigest()})
    palette=json.loads((BUILD/'palette.json').read_text())
    for kind in ['Diffuse','Normal','Mask','Team']:
        payload[f'units/CloneWars/TX130/UUL0101_{kind}.win.dds']=dds(kind,palette)
        payload[f'units/CloneWars/TX130/UUL0101_{kind}.dds']=dds(kind,palette)
    # Use unique paths and an explicit mesh reference instead of replacing
    # duplicate vanilla filenames whose mount priority proved ineffective.
    original_bp=LiteralTable((ROOT/'local/reference/UUL0101/uncompiled_lua/uncompiled/Units/UEF/UUL0101/UUL0101_unit.bp').read_text()).blueprint()
    mesh=copy.deepcopy(original_bp['Display']['Mesh'])
    mesh_id='/units/clonewars/tx130/tx130_mesh'
    mesh['BlueprintId']=mesh_id
    for lod,table in mesh['LODs'].items():
        table['MeshName']=f'/units/CloneWars/TX130/UUL0101_lod{lod-1}.scm'
        for material_set in table['MaterialSets'].values():
            for material in material_set['Materials'].values():
                for field,kind in [('DiffuseName','Diffuse'),('NormalName','Normal'),('MaskName','Mask'),('TeamName','Team')]:
                    material[field]=f'/units/CloneWars/TX130/UUL0101_{kind}.dds'
                material['ShaderMacros']=material['ShaderMacros'].replace(', anim_uvr','')
    def lua(value,indent=0):
        if isinstance(value,dict):
            rows=[]
            for key,item in value.items():
                k=f'[{key}]' if isinstance(key,int) else key
                rows.append(' '*(indent+4)+k+' = '+lua(item,indent+4)+',')
            return '{\n'+'\n'.join(rows)+'\n'+' '*indent+'}'
        if isinstance(value,str):return "'"+value.replace("'","\\'")+"'"
        if isinstance(value,bool):return 'true' if value else 'false'
        return str(value)
    patch={'Merge':True,'BlueprintId':'uul0101','Display':{'MeshBlueprint':mesh_id}}
    changed=copy.deepcopy(original_bp);merge(changed,{'Display':patch['Display']})
    if differences(original_bp,changed)!=['Display.MeshBlueprint']:raise ValueError('Unexpected gameplay change')
    with zipfile.ZipFile(ROOT/'local/installed-snapshot/gamedata/z_uncompiled_lua_dlc1.scd') as source:
        dlc=LiteralTable(source.read('uncompiled/mods/DLC1/shadow/Units/UEF/UUL0101/UUL0101_unit.bp').decode()).blueprint()
    dlc_changed=copy.deepcopy(dlc);merge(dlc_changed,{'Display':patch['Display']})
    if differences(dlc,dlc_changed)!=['Display.MeshBlueprint']:raise ValueError('Unexpected DLC gameplay change')
    unit_data=('UnitBlueprint '+lua(patch)+'\n').encode()
    for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/']:
        payload[prefix+'units/zz_clonewars_model_unit.bp']=unit_data
    payload['units/CloneWars/TX130/TX130_mesh.bp']=('MeshBlueprint '+lua(mesh)+'\n').encode()
    (ROOT/'src/units/zz_clonewars_model_unit.bp').write_bytes(unit_data)
    (ROOT/'src/units/TX130_mesh.bp').write_bytes(payload['units/CloneWars/TX130/TX130_mesh.bp'])
    dist=ROOT/'dist';dist.mkdir(exist_ok=True);target=dist/NAME
    with zipfile.ZipFile(target,'w') as z:
        for path,raw in sorted(payload.items()):
            info=zipfile.ZipInfo(path,(2026,10,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,raw)
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None or any(z.read(path)!=raw for path,raw in payload.items()):raise ValueError('Package round trip failed')
        if any(path.lower().endswith(('.lua','.sca')) for path in z.namelist()):raise ValueError('Visual package must not change scripts or animation')
    sha=hashlib.sha256(target.read_bytes()).hexdigest();(dist/(NAME+'.sha256')).write_text(sha+'  '+NAME+'\n')
    report={'archive':NAME,'sha256':sha,'bytes':target.stat().st_size,'asset_stage':'Model Changed — candidate awaiting in-game acceptance',
            'asset_origin':'Original procedural TX-130 prototype authored in this project; no downloaded Star Wars mesh',
            'mesh_validation':meshes,'textures':'Four authored 512x512 RGBA DDS atlases with complete mip chains',
            'paths':sorted(payload),'blueprint_changes':['Display.MeshBlueprint (visual reference only)'],'simulation_changes':[],'animation_changes':[],
            'previous_runtime_result':'User reported original Rock Head model remained; log confirms archive mounted. Revision uses unique mesh paths and explicit visual blueprint reference.','runtime_validation':'revised candidate not yet tested','known_limits':['Prototype silhouette and materials need user review.','SC2 shader channel behavior, team accents and native rendering still need in-game observation.','No new sound assets; sound milestone follows model acceptance.']}
    report['revision']=7
    report['palette_refinement']='Reference-led neutral off-white/light gray and muted crimson; eight-spoked Republic crests on both side armor tops and military roundel on hatch.'
    report['shape_polish']='Baked insignia without stacked decal geometry; darker gray/crimson and additional radiator, service-panel and handle details.'
    report['visual_fixes']=['Separated side-shell height ranges; paint assigned directly to armor faces.','Fixed command cabin and hatch to hull instead of rotating turret.']
    runtime_path=ROOT/'inventory/model-runtime-validation.json'
    if runtime_path.exists():
        report['previous_runtime_result']=json.loads(runtime_path.read_text())['result']
        report['previous_runtime_evidence']='inventory/model-runtime-validation.json'
    (ROOT/'inventory/model-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
