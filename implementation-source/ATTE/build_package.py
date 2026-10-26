from pathlib import Path
import sys,json,struct,zipfile,copy,hashlib,re,math
from PIL import Image
R=Path(__file__).resolve().parents[2];W=R/'work/atte';O=R/'outputs/AT-TE'
sys.path.insert(0,str(R/'work/archanist/pipeline'));import scm_v7
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable,differences
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atap');import native_animation
fit=json.loads((W/'rig-animation.json').read_text());bones=fit['bones'];names=[b['name'] for b in bones]
assert len(bones)<=71,'Exceeds shipped shader matrix palette'
ref=scm_v7.read((W/'template.scm').read_bytes());h=list(ref['header']);buf=bytearray(56)
scm_v7.section(buf,b'NAME');offsets=[]
for n in names:offsets.append(len(buf));buf.extend(n.encode()+b'\0')
h[2]=scm_v7.section(buf,b'SKEL');h[3]=h[11]=len(bones)
for b,off in zip(bones,offsets):buf.extend(scm_v7.BONE.pack(*(b['inverse']+b['position']+b['quaternion']+[off,b['parent'],0,0])))
h[4]=scm_v7.section(buf,b'VTXL');buf.extend(scm_v7.VERTEX.pack(*([0.]*16+[0]*4)));h[6]=1
h[7]=scm_v7.section(buf,b'TRIS');buf.extend(struct.pack('<3H',0,0,0));h[8]=3
h[5]=scm_v7.section(buf,b'XTRA');buf.extend(bytes([255,0,0,0]));h[9]=scm_v7.section(buf,b'INFO');buf.extend(ref['info']);h[10]=len(ref['info']);scm_v7.section(buf,b'MNAM');moff=[]
for n in ref['material_names']:moff.append(len(buf));buf.extend(n.encode()+b'\0')
h[12]=scm_v7.section(buf,b'MATS')
for i,off in enumerate(moff):buf.extend(scm_v7.MATERIAL.pack(off,1 if i==0 else 0,0 if i==0 else 3,0,1 if i==0 else 0))
scm_v7.HEADER.pack_into(buf,0,*h);reference=bytes(buf);scm_v7.read(reference)
payload={};folder='units/CloneWars/ATTE/';reports=[]
for lod in range(3):
 triangles=json.loads((W/f'geometry-lod{lod}.json').read_text());verts=[];indices=[];extra=bytearray();look={}
 for tri in triangles:
  for row in tri:
   v=row['v'];weights=[round(x*255) for x in row['w']];weights[0]+=255-sum(weights);key=tuple(round(x,6) for x in v)+tuple(weights)
   if key not in look:look[key]=len(verts);verts.append(v);extra.extend(weights)
   indices.append(look[key])
 assert len(verts)<65536,(lod,len(verts))
 indices += [j for k in range(0,len(indices),3) for j in (indices[k],indices[k+2],indices[k+1])]
 mats=[(len(indices)//3,0,0,len(verts))]+[(0,len(indices),len(verts),0)]*(len(moff)-1)
 raw=scm_v7.write(reference,verts,indices,mats,bytes(extra));reports.append(scm_v7.summary(raw))
 for ext in ['.scm','.win.scm']:payload[folder+f'ATTE_lod{lod}'+ext]=raw
def sca(frames,duration):
 b=bytearray(36);no=scm_v7.section(b,b'NAME')
 for n in names:b.extend(n.encode()+b'\0')
 lo=scm_v7.section(b,b'LINK');b.extend(struct.pack(f'<{len(bones)}i',*[x['parent'] for x in bones]));ao=scm_v7.section(b,b'ANIM');b.extend(struct.pack('<7f',0,0,0,1,0,0,0));fs=8+28*len(bones)
 for f in frames:
  b.extend(struct.pack('<fI',f['time'],0))
  for row in f['bones']:b.extend(struct.pack('<7f',*row))
 scm_v7.section(b,b'INFO');b.extend(b'AT-TE source gait conversion\0');struct.pack_into('<4sII f 5I',b,0,b'ANIM',7,len(frames),duration,len(bones),no,lo,ao,fs)
 raw=bytes(b);p=native_animation.read_sca(raw);assert p['names']==names;return raw
walk=sca(fit['frames'],fit['duration']);idle=sca([{'time':t,'bones':fit['frames'][0]['bones']} for t in [0.,1.]],1.)
for n,raw in [('Walk',walk),('Idle',idle)]:
 for ext in ['.sca','.win.sca']:payload[folder+'ATTE_'+n+ext]=raw
def dds(im):
 im=im.convert('RGBA');w,h=im.size;data=[]
 while True:
  data.append(im.tobytes('raw','BGRA'))
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
 vals=[124,0x2100f,h,w,w*4,0,len(data)]+[0]*11+[32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000]+[0x401008,0,0,0,0]
 return b'DDS '+struct.pack('<31I',*vals)+b''.join(data)
diffuse=Image.open(W/'diffuse.png').convert('RGBA');diffuse.thumbnail((2048,2048))
for kind,im in [('Diffuse',diffuse),('Normal',Image.new('RGBA',diffuse.size,(128,128,255,128))),('Mask',Image.new('RGBA',diffuse.size,(8,0,10,230))),('Team',Image.new('RGBA',diffuse.size,(0,0,0,0)))]:
 for ext in ['.dds','.win.dds']:payload[folder+'ATTE_'+kind+ext]=dds(im)
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
original=LiteralTable((W/'UUX0111_unit.bp').read_text(encoding='utf-8')).blueprint();bp=copy.deepcopy(original)
front_interval=0.75/1.6
rear_interval=1.5/1.6
bp.update({'BlueprintId':'uux0111','ScriptModule':'/units/CloneWars/ATTE/ATTE_script.lua','ScriptClass':'ATTE','Description':'Heavy Assault Walker','SizeX':7.4,'SizeY':5.3,'SizeZ':11.5,'CollisionOffsetY':2.4,'CollisionOffsetZ':0,'SelectionSizeX':7.4,'SelectionSizeZ':11.5,'SelectionCenterOffsetZ':0,'LifeBarOffset':5.4,'LifeBarSize':7.4})
bp['General']['UnitName']='AT-TE';bp['Defense'].update({'Health':30000,'MaxHealth':30000,'RegenRate':60});bp['Physics'].update({'MaxSpeed':1.8,'MaxSpeedReverse':.5,'MaxAcceleration':.8,'TurnRate':25,'MeshExtentsX':3.7,'MeshExtentsY':5.3,'MeshExtentsZ':5.75,'MotionType':'RULEUMT_Land','LayerChangeOffsetHeight':0,'RotateOnSpot':True});bp['Navigation'].update({'Radius':4.5,'IgnoreNeighbors':False});bp['AI']['TargetBones']={1:'Head_21',2:'Butt_36',3:'Hips_56'}
bp['Death']={'DebrisPieces':False,'ExplosionEffect':'UEFStructureDestroyEffectsExtraLarge02'}
mesh=copy.deepcopy(original['Display']['Mesh']);mid='/units/clonewars/atte/atte_mesh';mesh['BlueprintId']=mid
for i,t in mesh['LODs'].items():
 t['MeshName']=f'/units/CloneWars/ATTE/ATTE_lod{i-1}.scm'
 for ms in t['MaterialSets'].values():
  for mat in ms['Materials'].values():
   for field,kind in [('DiffuseName','Diffuse'),('NormalName','Normal'),('MaskName','Mask'),('TeamName','Team')]:mat[field]=f'/units/CloneWars/ATTE/ATTE_{kind}.dds'
   mat['ShaderMacros']='ambient_lighting, diffuse_lighting, specular_lighting, ambient_occlusion, team_color, environment_mapping, point_cloud'
bp['Display']={'DisplayName':'AT-TE','MeshBlueprint':mid,'UniformScale':.1,'AnimationWalk':'/units/CloneWars/ATTE/ATTE_Walk.sca','AnimationWalkRate':2.5,'AnimationIdle':'/units/CloneWars/ATTE/ATTE_Idle.sca','AnimationOnStartBuild':'/units/CloneWars/ATTE/ATTE_Idle.sca','AnimationDeploy':'/units/CloneWars/ATTE/ATTE_Idle.sca','EffectGroupClassification':'Large','SimulationBones':{i+1:c['muzzle'] for i,c in enumerate(fit['controllers'])}}
# A clean weapon list removes all Kriptor-specific controllers and weapon behavior.
template=copy.deepcopy(original['Weapons'][2]);bp['Weapons']={}
for i,c in enumerate(fit['controllers'],1):
 weapon=copy.deepcopy(template)
 for k in list(weapon):
  if k.startswith('MuzzleCharge') or k.startswith('CameraShake'):weapon.pop(k)
 main=i==1
 weapon.update({'Label':c['label'],'DisplayName':'Heavy Mass Driver' if main else 'Defensive Laser Cannon','Damage':1500 if main else 70,'DamageRadius':2.5 if main else 0,'RateOfFire':1/3 if main else 1/rear_interval,'MaxRadius':68.75 if main else 33.6,'MuzzleVelocity':85 if main else 65,'ProjectileId':'/projectiles/CloneWars/'+('ATTEHeavyBolt' if main else 'ATTELightBolt')+'/'+('ATTEHeavyBolt' if main else 'ATTELightBolt')+'_proj.bp','MuzzleFlashEffect':'','BallisticArc':'RULEUBA_None','RackRecoilDistance':0,'RackSalvoChargeTime':0,'RackSalvoReloadTime':3 if main else rear_interval,'RackSalvoSize':1,'RackSlavedToTurret':True,'RackBones':{1:{'RackBone':c['pitch'],'MuzzleBones':{1:c['muzzle']}}},'TurretBoneYaw':c['yaw'],'TurretBonePitch':c['pitch'],'TurretBoneMuzzle':c['muzzle'],'TurretPitch':0,'TurretPitchRange':35 if main else 40,'TurretPitchSpeed':25 if main else 80,'TurretYaw':0,'TurretYawRange':180 if main else (45 if c['label'].startswith('Front') else 65),'TurretYawSpeed':25 if main else 80,'TurretDualManipulators':False,'Turreted':True,'FireTargetLayerCaps':{'Land':'Land'},'TargetRestrictDisallow':'UNTARGETABLE','NotExclusive':True})
 weapon['Audio']=copy.deepcopy(original['Weapons'][2]['Audio']) if main else {'Fire':'SC2/SC2/Units/UEF/UUL0103/snd_UUL0103_AssBot_Plasma_Cannon'}
 weapon['Audio'].pop('MuzzleChargeStart',None)
 bp['Weapons'][i]=weapon
# Four front muzzles share one target and firing clock, in one native rack volley.
controllers={c['label']:c for c in fit['controllers']}
front=copy.deepcopy(bp['Weapons'][2]);front['Label']='FrontVolley';front['DisplayName']='Forward Laser Battery';front['RackFireTogether']=True;front['RackSalvoSize']=4;front['RackSlavedToTurret']=False
front['RackBones']={i:{'RackBone':controllers[label]['pitch'],'MuzzleBones':{1:controllers[label]['muzzle']}} for i,label in enumerate(['FrontLeftTop','FrontLeftBottom','FrontRightTop','FrontRightBottom'],1)}
front.pop('TargetRestrictOnlyAllow',None);front['FireTargetLayerCaps']={'Land':'Land'};front['RateOfFire']=1/front_interval;front['RackSalvoReloadTime']=front_interval
left=bp['Weapons'][6];right=bp['Weapons'][7]
for weapon in [left,right]:
 weapon.pop('TargetRestrictOnlyAllow',None);weapon['FireTargetLayerCaps']={'Land':'Land'};weapon['TurretYawRange']=35;weapon['TurretPitch']=12.5;weapon['TurretPitchRange']=22.5
bp['Weapons']={1:bp['Weapons'][1],2:front,3:left,4:right}
# The game's range overlay groups weapons by category. Keep every AT-TE gun
# in one category so its largest radius is the displayed artillery range.
for index in [1,2,3,4]:bp['Weapons'][index]['RangeCategory']='UWRC_IndirectFire'
bp['Categories']={i:('OVERLAYINDIRECTFIRE' if value=='OVERLAYDIRECTFIRE' else value) for i,value in bp['Categories'].items()}
# Use the AT-TE skeleton for pose-copying wreckage, never the custom Kriptor wreck.
bp['Wreckage']['UseCustomMesh']=False
bp['Wreckage']['Blueprint']='/props/CloneWars/ATTE/ATTE_wreck_prop.bp'
wreckmesh=copy.deepcopy(mesh);wreckmesh['BlueprintId']=mid+'_wreck'
for lod in wreckmesh['LODs'].values():
 for ms in lod['MaterialSets'].values():
  for mat in ms['Materials'].values():mat['ShaderMacros']+=', wreckage, wreckage_edge_highlight';mat['EffectName']='/textures/Units/Shared/Wreckage.dds'
bp['Display']['MeshBlueprintWrecked']=mid+'_wreck'
payload[folder+'ATTE_wreck_mesh.bp']=('MeshBlueprint '+lua(wreckmesh)+'\n').encode()
prop={'BlueprintId':'/props/clonewars/atte/atte_wreck_prop','Categories':{1:'RECLAIMABLE'},'Display':{'MeshBlueprint':mid+'_wreck','UniformScale':.1},'Interface':{'HelpText':'AT-TE Wreckage'},'Physics':{'BlockPath':False},'ScriptClass':'Wreckage','ScriptModule':'/lua/sim/wreckage.lua','SizeX':7.4,'SizeY':5.3,'SizeZ':11.5}
payload['props/CloneWars/ATTE/ATTE_wreck_prop.bp']=('PropBlueprint '+lua(prop)+'\n').encode()
bp.pop('Merge',None)
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:payload[prefix+'units/zzzz_clonewars_atte_unit.bp']=('UnitBlueprint '+lua(bp)+'\n').encode()
payload[folder+'ATTE_mesh.bp']=('MeshBlueprint '+lua(mesh)+'\n').encode()
core=Path(r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/shared/republic-blue-blaster');sys.path.insert(0,str(core));import build_core
for kind,scale in [('Heavy',1.8),('Light',1.0)]:
 for path,raw in build_core.payload().items():
  path=path.replace('lua/CloneWars/RepublicBlueBlaster.lua','lua/CloneWars/ATTE'+kind+'Blaster.lua').replace('effects/clonewars/republic/blueblaster/','effects/clonewars/atte/'+kind.lower()+'/')
  raw=raw.replace(b'/effects/clonewars/republic/blueblaster/',('/effects/clonewars/atte/'+kind.lower()+'/').encode())
  if path.endswith('.lua'):
   raw=raw.replace(b"Root .. 'blue_impact_flash_emit.bp')",("Root .. 'blue_impact_flash_emit.bp'):ScaleEmitter("+str(scale*.35)+")").encode())
  else:
   raw=re.sub(rb'(Size\s*=\s*)([0-9.]+)',lambda m:m[1]+str(float(m[2])*scale).encode(),raw)
  payload[path]=raw

g=Path(r'B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata')
with zipfile.ZipFile(g/'uncompiled_lua.scd') as z:
 original_proj=LiteralTable(z.read('uncompiled/projectiles/UEF/UCannon02/UCannon02_proj.bp').decode().replace('ProjectileBlueprint','UnitBlueprint',1)).blueprint()
for kind in ['Heavy','Light']:
 name='ATTE'+kind+'Bolt';proj=copy.deepcopy(original_proj)
 proj['BlueprintId']='/projectiles/clonewars/'+name.lower()+'/'+name.lower()+'_proj'
 proj['Display']={};proj['Effects']={};proj['General']['Weapon']=kind+' blue blaster'
 proj['Physics'].update({'InitialSpeed':85 if kind=='Heavy' else 65,'MaxSpeed':85 if kind=='Heavy' else 65,'Acceleration':0,'TrackTarget':False,'TrackTargetGround':False,'TurnRate':0,'Lifetime':4})
 payload['projectiles/CloneWars/'+name+'/'+name+'_proj.bp']=('ProjectileBlueprint '+lua(proj)+'\n').encode()
 code="local Projectile = import('/lua/sim/Projectile.lua').Projectile\nlocal Blue = import('/lua/CloneWars/ATTEKIND Бlaster.lua')\nNAME = Class(Projectile) { OnCreate = function(self) Projectile.OnCreate(self) Blue.AttachBolt(self) end, OnImpact = function(self,targetType,targetEntity) Blue.ImpactFlash(self) Projectile.OnImpact(self,targetType,targetEntity) end }\nTypeClass = NAME\n"
 code=code.replace('KIND Бlaster',kind+'Blaster').replace('NAME',name)
 payload['projectiles/CloneWars/'+name+'/'+name+'_script.lua']=code.encode()
payload[folder+'ATTE_script.lua']=(W/'ATTE_script.lua').read_bytes()
# Patch visible name occurrences using the effective installed localization overlay.
live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata');effective={}
installed_atte=live/'zzzzzz_SC2_CloneWars_ATTE.scd'
if installed_atte.exists():
 with zipfile.ZipFile(installed_atte) as previous:
  for n in previous.namelist():
   if n.lower().endswith(('/strings_db.lua','/research.lua','/achievements.lua')):payload[n]=previous.read(n)
for archive in sorted(live.glob('*.scd'),key=lambda p:p.name.lower()):
 if archive.name=='zzzzzz_SC2_CloneWars_ATTE.scd':continue
 with zipfile.ZipFile(archive) as z:
  for n in z.namelist():
   if n.lower().endswith(('/strings_db.lua','/research.lua','/achievements.lua')):effective[n]=z.read(n)
localizations=[]
import lua_constants
for n,raw in effective.items():
 if n in payload:continue
 if re.search(rb'King\s+Kriptor',raw,re.I):
  if raw.startswith(b'\x1bLua'):
   after,changes,shape=lua_constants.rewrite(raw);checked,pending,newshape=lua_constants.rewrite(after);assert checked==after and not pending and shape==newshape
  else:after=re.sub(rb'King\s+Kriptor',b'AT-TE',raw,flags=re.I)
  assert not re.search(rb'King\s+Kriptor',after,re.I)
  payload[n]=after;localizations.append(n)
payload['ATTE_ATTRIBUTION.txt']=b'AT-TE Walker (Animated) by R3negadeAidan. CC BY 4.0. https://sketchfab.com/3d-models/at-te-walker-animated-81ef81cf6c554055b741b43a1a08d69f\nModifications: six-leg native rig and animation conversion, weapon helpers, LODs, DDS materials, gameplay redesign.\n'
archive=O/'zzzzzz_SC2_CloneWars_ATTE.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,raw in sorted(payload.items()):z.writestr(n,raw)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'revision':'mount-test-6','archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'meshes':reports,'walk':{'frames':len(fit['frames']),'duration':fit['duration'],'version':7,'runtime_verified':False},'weapons':fit['controllers'],'localization_files':localizations,'gameplay':{'health':30000,'regen':60,'speed':1.8,'main_damage':1500,'main_rate':1/3,'main_range':68.75,'laser_damage':70,'front_rate':1/front_interval,'rear_rate':1/rear_interval,'front_interval':front_interval,'rear_interval':rear_interval,'laser_range':33.6,'land_only':True,'economy_and_research':'Original experimental slot cost/build time/research retained for first test'},'installed':False,'runtime':'unverified','blueprint_diff':differences(original,bp)}
(W/'unit-blueprint.json').write_text(json.dumps(bp,indent=2),encoding='utf8');(O/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ['blueprint_diff','weapons']},indent=2))
