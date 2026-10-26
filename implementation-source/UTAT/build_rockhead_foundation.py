from pathlib import Path
import sys,json,zipfile,copy,hashlib
W=Path(__file__).resolve().parent;R=W/'rockhead-foundation-fix';O=W.parent/'outputs';G=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata');sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable,differences
# JSON evidence retains numeric-table semantics after integer-key restoration.
def restore(v):
 if isinstance(v,dict):return {int(k) if k.isdigit() else k:restore(x) for k,x in v.items()}
 return v
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
with zipfile.ZipFile(R/'zz_SC2_CloneWars_UTAT_Model.scd') as z:payload={n:z.read(n) for n in z.namelist()}
old=payload.copy();del payload['units/CloneWars/UTAT/UTAT_script.lua']
with zipfile.ZipFile(G/'zz_SC2_CloneWars_TX130_Blaster.scd') as z:
 txproj=LiteralTable(z.read('projectiles/CloneWars/TX130/UCannonShell01_proj.bp').decode('utf-8').replace('ProjectileBlueprint','UnitBlueprint',1)).blueprint();txscript=z.read('projectiles/CloneWars/TX130/UCannonShell01_script.lua')
projectile=copy.deepcopy(txproj);projectile.update({'BlueprintId':'/projectiles/clonewars/utat/utattankshot_proj','ScriptModule':'/projectiles/CloneWars/UTAT/UTATTankShot_script.lua','ScriptClass':'UTATTankShot'})
payload['projectiles/CloneWars/UTAT/UTATTankShot_proj.bp']=('ProjectileBlueprint '+lua(projectile)+'\n').encode('utf-8')
# Identical native Projectile inheritance to the installed TX-130: no gravity or velocity override.
payload['projectiles/CloneWars/UTAT/UTATTankShot_script.lua']=txscript.replace(b'UCannonShell01',b'UTATTankShot')
reports=[]
for mount,baselinefile in [('',R/'tx130-base-effective.json'),('mods/DLC1/base/',R/'tx130-base-effective.json'),('mods/DLC1/shadow/',R/'tx130-dlc-effective.json')]:
 tank=restore(json.loads(baselinefile.read_text(encoding='utf-8')));path=mount+'units/zz_clonewars_utat_model_unit.bp';current=LiteralTable(old[path].decode('utf-8-sig')).blueprint();bp=copy.deepcopy(current)
 bp['AI']=copy.deepcopy(tank['AI']);bp['AI']['TargetBones']={1:'UTAT_RoofYaw'}
 bp['Categories']={i:('UUL0203' if c=='UUL0101' else c) for i,c in tank['Categories'].items()}
 general=copy.deepcopy(tank['General'])
 for k in ['BuildIconIndex','BuildIconPage','BuildIconSortPriority','UnitName']:general[k]=current['General'][k]
 bp['General']=general;bp['ScriptModule']='/units/UEF/UUL0101/UUL0101_script.lua';bp['ScriptClass']='UUL0101'
 weapons={};weapon_reports=[]
 for i,(label,prefix,damage) in enumerate([('UTATMainGun','Roof',75),('UTATSideLeft','Left',30),('UTATSideRight','Right',30)],1):
  native=tank['Weapons'][1];w=copy.deepcopy(native);w.update({'Label':label,'DisplayName':'UT-AT Main Cannon' if i==1 else 'UT-AT Side Cannon','Damage':damage,'ProjectileId':'/projectiles/clonewars/utat/utattankshot_proj.bp','ProjectilesPerOnFire':1,'RackBones':{1:{'RackBone':'UTAT_'+prefix+'Pitch','MuzzleBones':{1:'UTAT_'+prefix+'Muzzle'}}},'RackRecoilDistance':0,'TurretBoneYaw':'UTAT_'+prefix+'Yaw','TurretBonePitch':'UTAT_'+prefix+'Pitch','TurretBoneMuzzle':'UTAT_'+prefix+'Muzzle','TurretYawRange':20,'TurretPitch':12.5,'TurretPitchRange':22.5})
  assert w['BallisticArc']=='RULEUBA_LowArc' and w['ScriptModule']=='/lua/sim/DefaultWeapons.lua' and w['ScriptClass']=='DefaultProjectileWeapon'
  allowed={'Label','DisplayName','Damage','ProjectileId','ProjectilesPerOnFire','RackRecoilDistance','TurretBoneYaw','TurretBonePitch','TurretBoneMuzzle','TurretYawRange','TurretPitch','TurretPitchRange','RackBones.1.MuzzleBones.1'}
  delta=differences(native,w);assert set(delta)<=allowed|{'RackBones.1.RackBone','RackBones.1.MuzzleBones.2'},delta
  assert w['Damage']/native['Damage']==1.25 if i==1 else w['Damage']==30
  weapon_reports.append({'gun':label,'native_weapon_differences':delta,'native_ballistic_range_rate_targeting_projectile_class_exact':True});weapons[i]=w
 bp['Weapons']=weapons
 assert bp['General']['CommandCaps']==tank['General']['CommandCaps'] and 'RULEUCC_FormAttack' not in bp['General']['CommandCaps']
 assert {'TANK','ANTISURFACE','DIRECTFIRE'}<=set(bp['Categories'].values());assert bp['General']['ExperienceTable']=='TANK'
 for k in ['Defense','Economy','Physics','Transport','Navigation','Display']:assert bp[k]==current[k]
 assert bp.get('Abilities')==current.get('Abilities');text='UnitBlueprint '+lua(bp)+'\n';assert LiteralTable(text).blueprint()['Weapons']==weapons;payload[path]=text.encode('utf-8');reports.append({'mount':mount,'unit_changes_from_prior':differences(current,bp),'native_command_caps_and_tank_classification':True,'preserved_UTAT_model_size_health_cost_speed':True,'weapons':weapon_reports})
for n in old:
 if n.endswith(('.scm','.dds','.sca')) or n.endswith('_mesh.bp'):assert payload[n]==old[n]
projcmp=copy.deepcopy(projectile)
for k in ['BlueprintId','ScriptModule','ScriptClass']:projcmp.pop(k,None)
txcmp=copy.deepcopy(txproj)
for k in ['BlueprintId','ScriptModule','ScriptClass']:txcmp.pop(k,None)
assert projcmp==txcmp and b'SetBallisticAcceleration' not in payload['projectiles/CloneWars/UTAT/UTATTankShot_script.lua']
archive=O/'zz_SC2_CloneWars_UTAT_Model.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'revision':'rockhead-foundation-test-9-size170','unit_id':'uul0203','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'diagnosis':'Prior revision created all three projectiles (live log true), but custom zero-gravity projectile and changed ballistic arc diverged from the working TX130 trajectory. Unit command foundation still lacked TANK/ANTISURFACE, retained FormAttack and lacked tank experience/AI metadata. These are candidate causes; clip does not contain the reported over-head misses.','native_baseline':'Current installed TX130/RockHead base and DLC with all root unit merge patches applied','changes':['Exact native Rock Head unit script/class and normal DefaultProjectileWeapon classes; no custom UTAT firing overrides','Exact native tank command-cap table, tank/antisurface categories and tank experience; AI target bone remapped to visible roof mount','LowArc and unchanged TX130 projectile physics/effects; native Projectile script, no acceleration/gravity override','One visible muzzle per gun, agreed damage 75/30/30, native range20/rate0.5','Yaw +/-20 and upper elevation35 retained; downward travel relaxed from5 to10 degrees for near ground targets'], 'blueprint_checks':reports,'projectile_semantics_exact_TX130_except_private_resource_identity':True,'all_UTAT_model_textures_rig_size_health_cost_speed_transport_bytes_preserved':True,'installed':False,'runtime_tested':False,'limits':['Manual attack, hit accuracy and hull-facing must be verified in a restarted live game','Existing UTAT unit slot/research and optional Rock Head upgrades are not duplicated; three approved guns replace the optional cannon/SAM variants','No UTAA or TX130 package edits']}
(R/'foundation-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(O/'RockHead-foundation-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ['revision','sha256','changes']}))
