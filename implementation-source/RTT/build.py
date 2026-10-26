from pathlib import Path
import sys,json,struct,zipfile,hashlib,copy,math
from PIL import Image
r=Path(__file__).resolve().parents[2];w=r/'work/rtt';out=r/'outputs/RTT';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
from poc_unit import LiteralTable,merge,differences
base=w/'native';bp=LiteralTable((base/'uncompiled_lua.scd/uncompiled/Units/UEF/UUL0201/UUL0201_unit.bp').read_text(encoding='utf-8')).blueprint();dlc=LiteralTable((base/'z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUL0201/UUL0201_unit.bp').read_text(encoding='utf-8')).blueprint()
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
ref=(base/'units.scd/units/UEF/UUL0201/UUL0201_LOD0.win.scm').read_bytes();m=scm_v7.read(ref);assert scm_v7.write(ref,m['vertices'],m['indices'],[a[1:] for a in m['materials']],m['extra'])==ref
geo=json.loads((w/'geometry.json').read_text());vs=[];inds=[]
for tri in geo['triangles']:
 for row in tri:
  row=list(row);row[13]=1-row[13];row[15]=1-row[15];row[9:12]=[-x for x in row[9:12]];inds.append(len(vs));vs.append(row)
# Interior backfaces preserve closed armor rendering during steep aiming.
for tri in geo['triangles']:
 for row in [tri[0],tri[2],tri[1]]:
  v=list(row);v[13]=1-v[13];v[15]=1-v[15];v[3:6]=[-x for x in v[3:6]];v[9:12]=[-x for x in v[9:12]];inds.append(len(vs));vs.append(v)
assert len(vs)<65536
raw=scm_v7.write(ref,vs,inds,[(len(inds)//3,0,0,len(vs)),(0,len(inds),len(vs),0)]);parsed=scm_v7.read(raw);assert parsed['bones']==m['bones'];assert parsed['names']==m['names']
payload={};folder='units/CloneWars/RTTShield/';meshes=[]
for i in range(3):
 filename='UUL0201_LOD0' if i==0 else f'UUL0201_lod{i}'
 for suffix in ['.win.scm','.scm']:payload[folder+filename+suffix]=raw
 meshes.append({'lod':i,**scm_v7.summary(raw),'full_native_LOD0_skeleton_retained':True,'geometry':'Full detail at all distances in first test; optimization pending'})
def dds(im):
 im=im.convert('RGBA');width,height=im.size;levels=[]
 while True:
  levels.append(im.tobytes('raw','BGRA'))
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
 vals=[124,0x2100f,height,width,width*4,0,len(levels)]+[0]*11+[32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000]+[0x401008,0,0,0,0]
 return b'DDS '+struct.pack('<31I',*vals)+b''.join(levels)
for name,im in [('Diffuse',Image.open(w/'atlas.png')),('Normal',Image.new('RGBA',(1024,2048),(128,128,255,128))),('Mask',Image.new('RGBA',(1024,2048),(0,0,0,255))),('Team',Image.new('RGBA',(1024,2048),(0,0,0,0)))]:
 data=dds(im)
 for suffix in ['.dds','.win.dds']:payload[folder+'UUL0201_'+name+suffix]=data
mesh=copy.deepcopy(bp['Display']['Mesh']);meshid='/units/clonewars/rttshield/rttshield_mesh';mesh['BlueprintId']=meshid
for i,t in mesh['LODs'].items():
 t['MeshName']=f'/units/CloneWars/RTTShield/UUL0201_lod{i-1}.scm'
 for ms in t['MaterialSets'].values():
  for material in ms['Materials'].values():
   for f,n in [('DiffuseName','Diffuse'),('NormalName','Normal'),('MaskName','Mask'),('TeamName','Team')]:material[f]=f'/units/CloneWars/RTTShield/UUL0201_{n}.dds'
   material['ShaderMacros']=material.get('ShaderMacros','ambient_lighting, diffuse_lighting').replace(', anim_uvr','')
patch={'Merge':True,'BlueprintId':'uul0201','Display':{'MeshBlueprint':meshid,'DisplayName':'RTT Shield Transport'},'General':{'UnitName':'RTT Shield Transport'}};checks=[]
for label,original in [('base',bp),('DLC',dlc)]:
 changed=copy.deepcopy(original);merge(changed,{'Display':patch['Display'],'General':patch['General']});diff=differences(original,changed);assert set(diff)<=set(['Display.MeshBlueprint','Display.DisplayName','General.UnitName']),diff;assert changed.get('Weapons')==original.get('Weapons');checks.append({'variant':label,'changes':diff,'weapon_tables_unchanged':True})
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/']:payload[prefix+'units/zz_clonewars_rttshield_model_unit.bp']=('UnitBlueprint '+lua(patch)+'\n').encode()
payload[folder+'RTTShield_mesh.bp']=('MeshBlueprint '+lua(mesh)+'\n').encode();payload['CloneWars_RTT_CREDITS.txt']=b'RTT model/textures: Pandemic Studios. ALO rig: Sly442. ModDB uploader kubli. Source RM-09_Shuttle.zip. ModDB lists Public Domain; underlying rights not independently verified. Shield mechanism: native Supreme Commander 2, Gas Powered Games. Custom adaptation: this project.\n'
# P-Shield-specific emitter visuals only; shield coverage and simulation stay unchanged.
import re
effect_checks=[]
with zipfile.ZipFile('B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata/uncompiled_lua.scd') as sourcezip:
 for name in sourcezip.namelist():
  if 'uul0201_s_' not in name.lower() or not name.endswith('.bp'):continue
  original=sourcezip.read(name).decode('utf-8');text=original
  for field in ['SizeCurve','StartSizeCurve','EndSizeCurve','VelocityCurve']:
   pattern=r'(?<![A-Za-z])'+field+r'\s*=\s*\{.*?\n\s*\},\s*\n\s*\},'
   def shrink(match):
    return re.sub(r'([yz]\s*=\s*)(-?[0-9]+(?:\.[0-9]+)?)',lambda m:m[1]+format(float(m[2])*.85,'.6f'),match[0])
   text,count=re.subn(pattern,shrink,text,flags=re.S);assert count==1,(name,field,count)
  payload[name.removeprefix('uncompiled/')]=text.encode('utf-8');effect_checks.append({'file':name,'particle_size_and_travel_scale':.85})
assert len(effect_checks)==3
archive=out/'zz_SC2_CloneWars_RTTShield_Model.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;assert not any(n.endswith(('.lua','.sca')) for n in z.namelist())
report={'revision':'rtt-size-glow-test-4','archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'meshes':meshes,'blueprint_checks':checks,'native_script_and_animation_overrides':False,'simulation_changes':[],'glow_effects':effect_checks,'visual_scale_relative_to_test_3':2.0,'source_animation':'ALA clips supplied; not converted. RTT hull is rigid and source guns removed.','native_animations':'Original P-Shield skeleton/scripts/clips retained. No added projector or native unfolding arm geometry. Plain rigid RTT hull. Runtime unverified.','limits':['In-game texture, clearance and shield toggle checks pending','Full-detail first-test LODs','Source ALA playback not verified'],'installed':False}
(w/'package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(out/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
