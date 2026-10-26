from pathlib import Path
import sys,json,struct,zipfile,copy,hashlib
W=Path(__file__).resolve().parent;R=W.parents[1];O=R/'outputs/SPHA-T'
sys.path.insert(0,r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/archanist/pipeline');import scm_v7
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable,differences
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atap');import native_animation
from PIL import Image
fit=json.loads((W/'rig-animation.json').read_text(encoding='utf8'));bones=fit['bones'];names=[b['name'] for b in bones]
assert len(bones)<72
ref=scm_v7.read(Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/atte/template.scm').read_bytes());h=list(ref['header']);buf=bytearray(56)
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
scm_v7.HEADER.pack_into(buf,0,*h);reference=bytes(buf)
triangles=json.loads((W/'geometry.json').read_text(encoding='utf8'));verts=[];indices=[];extra=bytearray();look={}
for tri in triangles:
 for row in tri:
  v=row['v'];key=tuple(round(x,6) for x in v)
  if key not in look:look[key]=len(verts);verts.append(v);extra.extend([255,0,0,0])
  indices.append(look[key])
# Both windings retain the existing working pipeline's renderer behavior.
indices += [j for k in range(0,len(indices),3) for j in (indices[k],indices[k+2],indices[k+1])]
mats=[(len(indices)//3,0,0,len(verts))]+[(0,len(indices),len(verts),0)]*(len(moff)-1)
raw=scm_v7.write(reference,verts,indices,mats,bytes(extra));scm_v7.read(raw)
folder='units/CloneWars/SPHA/';payload={}
for lod in range(3):
 for ext in ['.scm','.win.scm']:payload[folder+f'SPHA_lod{lod}'+ext]=raw
def sca(clip):
 b=bytearray(36);no=scm_v7.section(b,b'NAME')
 for n in names:b.extend(n.encode()+b'\0')
 lo=scm_v7.section(b,b'LINK');b.extend(struct.pack(f'<{len(bones)}i',*[x['parent'] for x in bones]));ao=scm_v7.section(b,b'ANIM');b.extend(struct.pack('<7f',0,0,0,1,0,0,0));fs=8+28*len(bones)
 for f in clip['frames']:
  b.extend(struct.pack('<fI',f['time'],0))
  for row in f['bones']:b.extend(struct.pack('<7f',*row))
 scm_v7.section(b,b'INFO');b.extend(b'SPHA-T source motion; prototype\0');struct.pack_into('<4sII f 5I',b,0,b'ANIM',7,len(clip['frames']),clip['duration'],len(bones),no,lo,ao,fs)
 raw=bytes(b);p=native_animation.read_sca(raw);assert p['names']==names;return raw
for n,clip in fit['clips'].items():
 for ext in ['.sca','.win.sca']:payload[folder+'SPHA_'+n+ext]=sca(clip)
def dds(im):
 im=im.convert('RGBA');w,h=im.size;data=[]
 while True:
  data.append(im.tobytes('raw','BGRA'))
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
 vals=[124,0x2100f,h,w,w*4,0,len(data)]+[0]*11+[32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000]+[0x401008,0,0,0,0]
 return b'DDS '+struct.pack('<31I',*vals)+b''.join(data)
diffuse=Image.open(Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/spha/SPHT.png')).convert('RGBA')
for kind,im in [('Diffuse',diffuse),('Normal',Image.new('RGBA',diffuse.size,(128,128,255,128))),('Mask',Image.new('RGBA',diffuse.size,(8,0,10,230))),('Team',Image.new('RGBA',diffuse.size,(0,0,0,0)))]:
 for ext in ['.dds','.win.dds']:payload[folder+'SPHA_'+kind+ext]=dds(im)
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
original=LiteralTable((R/'work/native-jackhammer/z_uncompiled_lua_dlc1_UUX0113D1_unit.bp').read_text(encoding='utf8')).blueprint();bp=copy.deepcopy(original)
bp.update({'BlueprintId':'uux0113d1','ScriptModule':'/units/CloneWars/SPHA/SPHA_script.lua','ScriptClass':'SPHA','Description':'SPHA-T Deployable Laser Cannon (30-95 range; cannot target inside 30)'})
bp['General']['UnitName']='SPHA-T'
mesh=copy.deepcopy(original['Display']['Mesh']);mid='/units/clonewars/spha/spha_mesh';mesh['BlueprintId']=mid
for i,lod in mesh['LODs'].items():
 lod['MeshName']=f'/units/CloneWars/SPHA/SPHA_lod{i-1}.scm'
 for ms in lod['MaterialSets'].values():
  for mat in ms['Materials'].values():
   for field,kind in [('DiffuseName','Diffuse'),('NormalName','Normal'),('MaskName','Mask'),('TeamName','Team')]:mat[field]=f'/units/CloneWars/SPHA/SPHA_{kind}.dds'
   mat['ShaderMacros']='ambient_lighting, diffuse_lighting, specular_lighting, ambient_occlusion, team_color, environment_mapping, point_cloud'
bp['Display']={'DisplayName':'SPHA-T','MeshBlueprint':mid,'UniformScale':.1,'AnimationWalk':'/'+folder+'SPHA_Walk.sca','AnimationWalkRate':.4,'AnimationIdle':'/'+folder+'SPHA_Idle.sca','AnimationOpen':'/'+folder+'SPHA_Deploy.sca','AnimationClose':'/'+folder+'SPHA_Pack.sca','EffectGroupClassification':'Large','SimulationBones':{1:'SPHA_Muzzle'}}
bp['Display']['AnimationWalk']='/'+folder+'SPHA_Walk.sca'
bp['Physics']['MaxSpeed']=1.24
# Keep the experimental slot and Deploy ability, but classify its combat role the
# same way as Rock Head so ordinary surface targets are handled by the same AI/UI paths.
category_values=list(bp['Categories'].values())
for old,new in [('ARTILLERY','TANK'),('INDIRECTFIRE','DIRECTFIRE'),('OVERLAYINDIRECTFIRE','OVERLAYDIRECTFIRE')]:
 for key,value in bp['Categories'].items():
  if value==old:bp['Categories'][key]=new
weapon=bp['Weapons'][1]
for k in ['ProjectileId','ProjectileLifetime','MuzzleVelocity','FiringRandomness','UseFiringSolutionInsteadOfAimBone']:weapon.pop(k,None)
weapon.update({'DisplayName':'Heavy Laser Cannon','BallisticArc':'RULEUBA_None','BeamCollisionDelay':.2,'BeamLifetime':2.,'Damage':375.,'MaxRadius':95,'RackRecoilDistance':0,'RackBones':{1:{'RackBone':'SPHA_Pitch','MuzzleBones':{1:'SPHA_Muzzle'}}},'TurretBoneYaw':'SPHA_Yaw','TurretBonePitch':'SPHA_Pitch','TurretBoneMuzzle':'SPHA_Muzzle','RackSlavedToTurret':True,'MuzzleFlashEffect':'','FiringTolerance':.2})
weapon.update({'AboveWaterTargetsOnly':True,'AlwaysRecheckTarget':True,'AutoInitiateAttackOnPatrol':True,'FireTargetLayerCaps':{'Land':'Land|Water|Seabed'},'TargetCheckInterval':.2,'TargetPriorities':{1:'LAND MOBILE',2:'ALLUNITS'},'TargetRestrictDisallow':'UNTARGETABLE','RangeCategory':'UWRC_DirectFire','WeaponCategory':'Direct Fire'})
for key in ['CannotAttackGround','AutoInitiateAttackCommand','NeedPrep']:
 weapon.pop(key,None)
weapon['MinRadius']=30
weapon['Audio']={'Fire':'SC2/SC2/Units/UEF/UUL0203/snd_UUL0203_AntiMissile_AntiMissile'}
weapon['MuzzleFlashEffect']='UEF_AntiMissile01_Launch02'
bp['Weapons'][2]['MaxRadius']=95
bp['Weapons'][2]['MinRadius']=30
bp['Death']['DebrisPieces']=False;bp['Death'].pop('DestructionParts',None)
bp['Wreckage']['UseCustomMesh']=False
bp['Wreckage']['Blueprint']='/props/CloneWars/SPHA/SPHA_wreck_prop.bp'
bp['LifeBarOffset']=5.8
bp['Display']['MeshBlueprintWrecked']=mid+'_wreck'
wreckmesh=copy.deepcopy(mesh);wreckmesh['BlueprintId']=mid+'_wreck'
for lod in wreckmesh['LODs'].values():
 for ms in lod['MaterialSets'].values():
  for mat in ms['Materials'].values():mat['ShaderMacros']+=', wreckage, wreckage_edge_highlight';mat['EffectName']='/textures/Units/Shared/Wreckage.dds'
payload[folder+'SPHA_wreck_mesh.bp']=('MeshBlueprint '+lua(wreckmesh)+'\n').encode()
prop={'BlueprintId':'/props/clonewars/spha/spha_wreck_prop','Categories':{1:'RECLAIMABLE'},'Display':{'MeshBlueprint':mid+'_wreck','UniformScale':.1},'Interface':{'HelpText':'SPHA-T Wreckage'},'Physics':{'BlockPath':False},'ScriptClass':'Wreckage','ScriptModule':'/lua/sim/wreckage.lua','SizeX':original['SizeX'],'SizeY':original['SizeY'],'SizeZ':original['SizeZ']}
payload['props/CloneWars/SPHA/SPHA_wreck_prop.bp']=('PropBlueprint '+lua(prop)+'\n').encode()
# Native footprint, health, economy, movement, research slot, categories, ability,
# The native Deploy ability controls the gun. The requested 30-unit artillery
# dead zone is retained for both the main weapon and its range helper.
bp.pop('Merge',None)
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:payload[prefix+'units/zzzz_clonewars_spha_unit.bp']=('UnitBlueprint '+lua(bp)+'\n').encode()
payload[folder+'SPHA_mesh.bp']=('MeshBlueprint '+lua(mesh)+'\n').encode()
payload[folder+'SPHA_script.lua']=(W/'SPHA_script.lua').read_bytes()
payload['SPHA_ATTRIBUTION.txt']=b'SPHA-T model/textures by Nomada_Firefox; Return of the Clones v7.2 compilation by Darth_Windu. Reuse license not established; private conversion test only. Source: https://www.moddb.com/mods/return-of-the-clones1/downloads/return-of-the-clones-v72\n'
archive=O/'zzzzzz_SC2_CloneWars_SPHA.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,raw in sorted(payload.items()):z.writestr(n,raw)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'revision':'beam-test-3-close-range-research-fix','archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'mesh':scm_v7.summary(raw if False else payload[folder+'SPHA_lod0.scm']),'animation':{n:{'duration':c['duration'],'frames':len(c['frames'])} for n,c in fit['clips'].items()},'movement':{'max_speed_before':3.1,'max_speed_after':1.24,'reduction_percent':60,'walk_rate_before':1.0,'walk_rate_after':0.4},'targeting':{'surface_permissions':'Rock Head main-gun parity: Land|Water|Seabed','priorities':['LAND MOBILE','ALLUNITS'],'weapon_category':'Direct Fire','range_category':'UWRC_DirectFire','deploy_required':True,'minimum_range':0},'beam':{'duration':2,'pulse_damage':375,'pulse_interval':.2,'maximum_installments':10,'total_budget':3750,'cycle':5,'maximum_range':95,'minimum_range':0,'blast_radius':7,'damage_parity':'Nominal full-beam budget equals one native shell. Actual hits, collision tick count, mitigation and interrupted damage require runtime verification.'},'deployment':'Exact native Deploy ability and its existing button; native enabling after animation completion, disabling and immobilization retained. Source deploy/pack SCA paths substituted.','limitations':['All three LODs share prototype geometry','Native footprint preserved despite 12-unit visual length; clearance needs user review','No source firing/death animation','Provisional native blue UEF beam effect and sound','Runtime unverified'],'blueprint_diff':differences(original,bp),'installed':False}
report['revision']='beam-test-8-target-recheck'
report['targeting']['minimum_range']=30
report['beam']['minimum_range']=30
report['deployment']='Original DLC Deploy ability blueprint and Load/Unload button retained. The verified-loaded SPHA-T unit script detects the native Immobile planted state and enables MainGun after 1.5 seconds; it disables MainGun when mobile.'
report['targeting']['recheck']='MainGun AlwaysRecheckTarget=true and TargetCheckInterval=0.2; blocked-terrain behavior requires runtime test.'
(W/'unit-blueprint.json').write_text(json.dumps(bp,indent=2),encoding='utf8');(O/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('Built',archive,report['sha256'],len(bones),'bones',len(verts),'vertices')
