from pathlib import Path
import sys,json,struct,zipfile,hashlib,copy,math
from PIL import Image
W=Path(__file__).resolve().parent;O=W.parent/'outputs';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
from poc_unit import LiteralTable,merge,differences
B=W/'native';bp=LiteralTable((B/'uncompiled_lua.scd/uncompiled/Units/UEF/UUL0203/UUL0203_unit.bp').read_text(encoding='utf-8')).blueprint();dlc=LiteralTable((B/'z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUL0203/UUL0203_unit.bp').read_text(encoding='utf-8')).blueprint()
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
ref=(B/'units.scd/units/UEF/UUL0203/UUL0203_lod0.win.scm').read_bytes();m=scm_v7.read(ref);assert scm_v7.write(ref,m['vertices'],m['indices'],[a[1:] for a in m['materials']],m['extra'])==ref
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atap');import native_animation
original_m=m;ref=native_animation.extend(ref,json.loads((W/'added-bones.json').read_text(encoding='utf-8')));m=scm_v7.read(ref)
geo=json.loads((W/'geometry.json').read_text(encoding='utf-8'));vs=[];inds=[];lookup={}
for tri in geo['triangles']:
 for row in tri:
  key=struct.pack('<16f4B',*row)
  if key not in lookup:lookup[key]=len(vs);vs.append(row)
  inds.append(lookup[key])
assert len(vs)<65536
assert all(len(set(inds[k:k+3]))==3 for k in range(0,len(inds),3))
materials=[(len(inds)//3,0,0,len(vs))]+[(0,len(inds),len(vs),0)]*(len(m['materials'])-1)
raw=scm_v7.write(ref,vs,inds,materials);parsed=scm_v7.read(raw);assert parsed['bones']==m['bones'] and parsed['names']==m['names']
payload={};folder='units/CloneWars/UTAT/';meshes=[]
for i in range(3):
 native=(B/f'units.scd/units/UEF/UUL0203/UUL0203_lod{i}.win.scm').read_bytes();n=scm_v7.read(native);assert scm_v7.write(native,n['vertices'],n['indices'],[a[1:] for a in n['materials']],n['extra'])==native
 for suffix in ['.win.scm','.scm']:payload[folder+f'UTAT_lod{i}'+suffix]=raw
 meshes.append({'lod':i,**scm_v7.summary(raw),'native_roundtrip':True,'native_bone_transforms_unchanged':True,'added_visual_bones':12})
def dds(im):
 im=im.convert('RGBA');width,height=im.size;levels=[]
 while True:
  levels.append(im.tobytes('raw','BGRA'))
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
 vals=[124,0x2100f,height,width,width*4,0,len(levels)]+[0]*11+[32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000]+[0x401008,0,0,0,0]
 return b'DDS '+struct.pack('<31I',*vals)+b''.join(levels)
for name,im in [('Diffuse',Image.open(W/'atlas.png')),('Normal',Image.new('RGBA',(2048,2048),(128,128,255,128))),('Mask',Image.new('RGBA',(2048,2048),(0,0,0,255))),('Team',Image.new('RGBA',(2048,2048),(0,0,0,0)))]:
 data=dds(im)
 for suffix in ['.dds','.win.dds']:payload[folder+'UTAT_'+name+suffix]=data
mesh=copy.deepcopy(bp['Display']['Mesh']);meshid='/units/clonewars/utat/utat_mesh';mesh['BlueprintId']=meshid
for i,t in mesh['LODs'].items():
 t['MeshName']=f'/units/CloneWars/UTAT/UTAT_lod{i-1}.scm'
 for ms in t['MaterialSets'].values():
  for material in ms['Materials'].values():
   material.clear()
   for f,n in [('DiffuseName','Diffuse'),('NormalName','Normal'),('MaskName','Mask'),('TeamName','Team')]:material[f]=f'/units/CloneWars/UTAT/UTAT_{n}.dds'
   material['ShaderMacros']='ambient_lighting, diffuse_lighting, point_cloud'
bones_patch={'TurretBoneYaw':'UTAT_LeftYaw','TurretBonePitch':'UTAT_LeftPitch','TurretBoneMuzzle':'UTAT_LeftMuzzle','RackBones':{},'TurretYawRange':20,'TurretPitch':15,'TurretPitchRange':20}
for j,label in enumerate(['Left','Right','Roof'],1):bones_patch['RackBones'][j]={'RackBone':'UTAT_'+label+'Pitch','MuzzleBones':{1:'UTAT_'+label+'Muzzle'}}
patch={'Merge':True,'BlueprintId':'uul0203','Display':{'MeshBlueprint':meshid,'DisplayName':'UT-AT','UniformScale':bp['Display']['UniformScale']*1.7},'General':{'UnitName':'UT-AT'},'ScriptModule':'/units/CloneWars/UTAT/UTAT_script.lua','ScriptClass':'UTAT','Weapons':{1:bones_patch}};checks=[]
allowed_weapon_paths={'Weapons.1.TurretBoneYaw','Weapons.1.TurretBonePitch','Weapons.1.TurretBoneMuzzle','Weapons.1.TurretYawRange','Weapons.1.TurretPitch','Weapons.1.TurretPitchRange'}
for j in range(1,4):allowed_weapon_paths.update({f'Weapons.1.RackBones.{j}.RackBone',f'Weapons.1.RackBones.{j}.MuzzleBones.1'})
for label,original in [('base',bp),('DLC',dlc)]:
 assert original.get('Weapons') and len(original['Weapons'])==1
 changed=copy.deepcopy(original);merge(changed,{k:v for k,v in patch.items() if k not in ('Merge','BlueprintId')});diff=differences(original,changed)
 allowed=set(['Display.MeshBlueprint','Display.DisplayName','Display.UniformScale','General.UnitName','ScriptModule','ScriptClass'])|allowed_weapon_paths
 assert set(diff)==allowed,diff
 original_weapon=copy.deepcopy(original['Weapons']);merge(original_weapon,{1:bones_patch});assert changed['Weapons']==original_weapon
 assert len(changed['Weapons'][1]['RackBones'])==3
 assert 'T01_' not in lua(changed['Weapons']) and 'Turret01' not in lua(changed['Weapons'])
 checks.append({'variant':label,'changes':diff,'only_weapon_bone_bindings_and_three_arc_fields_change':True,'native_damage_range_rate_targeting_beam_timing_and_all_other_fields_unchanged':True,'three_visible_muzzles_only':True})
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/']:payload[prefix+'units/zz_clonewars_utat_model_unit.bp']=('UnitBlueprint '+lua(patch)+'\n').encode('utf-8')
payload[folder+'UTAT_script.lua']=(W/'UTAT_script.lua').read_bytes()
payload[folder+'UTAT_mesh.bp']=('MeshBlueprint '+lua(mesh)+'\n').encode('utf-8')
payload['CloneWars_UTAT_CREDITS.txt']=b'UT-AT model/textures: Doofi (DooFi); EaW/FoC tweaks: Darth_Windu; rigging: Jake Green; compilation: nett40, Star Wars Clone Wars v3.0. Downloaded ModDB archive MD5 0e06551f9cb18c1ef3f729490531aeaa. Local conversion/testing only. Readme requests contacting original authors for another public mod release; permission is not established. Native Sharp Shooter rig/game resources: Gas Powered Games. Project adaptation: native-rig fit and three visual intercept emitters.\n'
archive=O/'zz_SC2_CloneWars_UTAT_Model.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;assert [n for n in z.namelist() if n.endswith('.lua')]==[folder+'UTAT_script.lua'];assert not any(n.endswith('.sca') for n in z.namelist())
 paths={n.lower() for n in z.namelist()}
 for lod in mesh['LODs'].values():
  assert lod['MeshName'].lstrip('/').lower() in paths
  for ms in lod['MaterialSets'].values():
   for mat in ms['Materials'].values():
    for k,v in mat.items():
     if k.endswith('Name'):assert v.lstrip('/').lower() in paths
report={'revision':'limited-arc-test-6-size170','unit_id':'uul0203','identity':'UT-AT','user_size_request':'Increase whole model 70 percent, October 24, 2026','visual_scale_multiplier':1.7,'Display.UniformScale':bp['Display']['UniformScale']*1.7,'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'meshes':meshes,'blueprint_checks':checks,'simulation_changes':['User-authorized firing origins moved from hidden native muzzles to the three visible tips; native aim bone bindings retargeted to visible guns. User-authorized tank-like gun limits: yaw +/-20 degrees, elevation -5 to +35. No damage/range/rate/beam timing changes.'],'weapon':'Native ZapperCollisionBeam02; same three-rack cycle, damage, ranges, rates, targets and beam timing. Muzzle/rack/yaw/pitch bindings now use the three visible guns. Native aim controllers Default/Right/Left target each mount independently.', 'native_script_and_animation_overrides':'Native weapon logic inherited; SetupTurret adds two native aim controllers, forward-reset and fire-channel routing. Original firing and flash methods forwarded once; no custom firing schedule or beam class.','texture':'Three source 1024 DDS textures combined into 2048 atlas; explicit export V flip; full mip chains; neutral normal map; team tint deferred','geometry':geo['parts'],'removed':'Artificial tall center mount and three-emitter array; original low central housing restored','visual_animation':'Each visible gun now has independent native yaw/pitch/muzzle chain and native aim control; no-target pose resets forward','firing_origins':'All three RackBones and muzzle flashes bind only to LeftMuzzle/RightMuzzle/RoofMuzzle at actual visible tube ends; no hidden mount firing references remain','native_animation_issue':'Original Aactivate asset header bone names are UEL0307/Spinner/B01/B02/B03/B04/Exhaust_Right/Exhaust_Left; mismatches original UUL0203 rig. Native file/reference preserved; activation playback requires runtime evidence. Constrained UUL0105 decoder does not decode this file.','mechanical_limits':{'yaw_degrees':[-20,20],'elevation_degrees':[-5,35],'hull_facing':'Limited native forward arc requires hull facing; existing RotateOnSpot and AI.Attacker.RelocateToFire retained; no forced move orders or teleports','future_home':'User will select a separate tank slot; current uul0203 staging only; target categories unchanged'},'installed':False,'runtime':'Not tested','limits':['All LODs use identical full-detail geometry to preserve mount/UV alignment in first test; crowd performance unmeasured','Activation, aiming, beam visibility, side-gun clearance, transport, researched ability, destruction and rollback require runtime observation','Native wreckage remains; no custom destruction model','User explicitly authorizes visible-tip interception origins and aiming. Beam/interception class retained; no artillery/anti-air conversion','Final scale/team tint/normal-map polish deferred']}
(W/'package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(O/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'sha256':report['sha256'],'triangles':len(inds)//3,'vertices':len(vs),'checks':checks}))
