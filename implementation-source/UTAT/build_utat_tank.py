from pathlib import Path
import sys,json,zipfile,copy,hashlib
W=Path(__file__).resolve().parent;C=W/'tank-conversion';O=W.parent/'outputs';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable,differences
G=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata')
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 if v is None:return 'nil'
 return str(v)
tank=LiteralTable((C/'native/uncompiled/Units/UEF/UUL0101/UUL0101_unit.bp').read_text(encoding='utf-8')).blueprint();effective=json.loads((C/'tx130-effective.json').read_text(encoding='utf-8'));assert effective['Weapons']['1']['Damage']==60
with zipfile.ZipFile(C/'backups/zz_SC2_CloneWars_UTAT_Model.scd') as z:payload={n:z.read(n) for n in z.namelist()}
old_payload=payload.copy();payload['units/CloneWars/UTAT/UTAT_script.lua']=(C/'UTAT_script.lua').read_bytes()
with zipfile.ZipFile(G/'zz_SC2_CloneWars_TX130_Blaster.scd') as z:
 projectile=LiteralTable(z.read('projectiles/CloneWars/TX130/UCannonShell01_proj.bp').decode('utf-8').replace('ProjectileBlueprint','UnitBlueprint',1)).blueprint()
projectile.update({'BlueprintId':'/projectiles/clonewars/utat/utattankshot_proj','ScriptModule':'/projectiles/CloneWars/UTAT/UTATTankShot_script.lua','ScriptClass':'UTATTankShot'})
payload['projectiles/CloneWars/UTAT/UTATTankShot_proj.bp']=('ProjectileBlueprint '+lua(projectile)+'\n').encode('utf-8');payload['projectiles/CloneWars/UTAT/UTATTankShot_script.lua']=b"local Projectile = import('/lua/sim/Projectile.lua').Projectile\nUTATTankShot = Class(Projectile) { OnCreate = function(self,inWater) Projectile.OnCreate(self,inWater); self:SetBallisticAcceleration(0) end }\nTypeClass = UTATTankShot\n"
weapons={}
for i,(label,prefix,damage) in enumerate([('UTATMainGun','Roof',75),('UTATSideLeft','Left',30),('UTATSideRight','Right',30)],1):
 w=copy.deepcopy(tank['Weapons'][1]);w.update({'Label':label,'DisplayName':'UT-AT Main Cannon' if i==1 else 'UT-AT Side Cannon','Damage':damage,'BallisticArc':'RULEUBA_None','ProjectileId':'/projectiles/clonewars/utat/utattankshot_proj.bp','ProjectilesPerOnFire':1,'RackBones':{1:{'RackBone':'UTAT_'+prefix+'Pitch','MuzzleBones':{1:'UTAT_'+prefix+'Muzzle'}}},'RackFireTogether':False,'RackSlavedToTurret':False,'RackRecoilDistance':0,'TurretBoneYaw':'UTAT_'+prefix+'Yaw','TurretBonePitch':'UTAT_'+prefix+'Pitch','TurretBoneMuzzle':'UTAT_'+prefix+'Muzzle','TurretYawRange':20,'TurretPitch':15,'TurretPitchRange':20,'ScriptModule':'/units/CloneWars/UTAT/UTAT_script.lua','ScriptClass':'UTATTankGun'})
 weapons[i]=w
variants=[('',W/'native/uncompiled_lua.scd/uncompiled/Units/UEF/UUL0203/UUL0203_unit.bp'),('mods/DLC1/base/',W/'native/uncompiled_lua.scd/uncompiled/Units/UEF/UUL0203/UUL0203_unit.bp'),('mods/DLC1/shadow/',W/'native/z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUL0203/UUL0203_unit.bp')];reports=[]
for mount,p in variants:
 original=LiteralTable(p.read_text(encoding='utf-8')).blueprint();bp=copy.deepcopy(original);bp['BlueprintId']='uul0203';bp['Weapons']=copy.deepcopy(weapons);bp['Description']='Medium Tank';bp['Display'].update({'MeshBlueprint':'/units/clonewars/utat/utat_mesh','DisplayName':'UT-AT','UniformScale':.204});bp['Display'].pop('Mesh',None);bp['Display'].pop('AnimationOpen',None);bp['General']['UnitName']='UT-AT';bp['General']['CommandCaps'].update({'RULEUCC_Attack':True,'RULEUCC_RetaliateToggle':True});bp['StrategicIconName']=tank['StrategicIconName'];bp['ScriptModule']='/units/CloneWars/UTAT/UTAT_script.lua';bp['ScriptClass']='UTAT'
 cats=[x for x in original['Categories'].values() if x not in ['DEFENSE','OVERLAYINDIRECTFIRE']];cats+=['DIRECTFIRE','OVERLAYDIRECTFIRE'];bp['Categories']={i:v for i,v in enumerate(cats,1)}
 for key in ['Defense','Economy','Physics','Transport','Intel','Navigation']:assert bp[key]==original[key]
 assert bp.get('Abilities')==original.get('Abilities')
 assert not any('AntiMissile' in str(x) for x in bp['Weapons'].values());assert all('BeamLifetime' not in w and 'TargetType' not in w and 'TargetRestrictOnlyAllow' not in w for w in bp['Weapons'].values())
 text='UnitBlueprint '+lua(bp)+'\n';parsed=LiteralTable(text).blueprint();assert parsed['Weapons']==weapons
 payload[mount+'units/zz_clonewars_utat_model_unit.bp']=text.encode('utf-8');reports.append({'mount':mount,'changed_fields':differences(original,bp),'health_cost_speed_transport_research_abilities_unchanged':True,'complete_blueprint_replaces_old_beam_fields':True})
assert weapons[1]['Damage']/tank['Weapons'][1]['Damage']==1.25
asset_names=[n for n in old_payload if n.endswith(('.scm','.dds')) or n.endswith('_mesh.bp')]
assert all(payload[n]==old_payload[n] for n in asset_names)
archive=O/'zz_SC2_CloneWars_UTAT_Model.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'revision':'firing-fix-8-size170','unit_id':'uul0203','identity':'UT-AT tank','archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'damage':{'TX130_main_per_projectile':60,'UTAT_roof':75,'roof_ratio':1.25,'UTAT_side_each':30},'rate_each':.5,'range_each':20,'theoretical_unresearched_total_DPS':{'TX130':60,'UTAT':67.5,'assumptions':'All guns on target; one roof and two side projectiles each 2 seconds; TX130 two 60-damage muzzles each 2 seconds. Alignment/repositioning can reduce output.'},'model_texture_rig_mesh_payload_byte_unchanged':True,'visual_scale_multiplier':1.7,'mechanical_limits':{'yaw':[-20,20],'pitch':[-5,35]},'role':'Surface-target direct-fire tank; no missile interception or air-target weapon','projectile':'Private copy of the installed TX130 blaster projectile; same visual effects and native projectile settings, with gravity explicitly zero and weapon BallisticArc None for straight direct firing','weapon_classes':'Three separate native DefaultProjectileWeapon subclasses; native single-gun aim controllers. Native aiming/firing checks authoritative; custom probe-angle veto removed. No native beam class imported.','blueprint_checks':reports,'retained_current_health':875,'note':'Stronger gun/firepower, not an armor increase; prior health/cost/movement/research slot retained','installed':False,'runtime_tested':False,'UTAA':'Unchanged pending user choice after secondary-gun preview'}
(O/'Tank-conversion-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(O/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(C/'tank-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ['revision','sha256','damage','rate_each','range_each','model_texture_rig_mesh_payload_byte_unchanged']}))
