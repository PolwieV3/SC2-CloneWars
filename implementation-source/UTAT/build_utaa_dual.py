from pathlib import Path
import sys,json,copy,hashlib,zipfile
W=Path(__file__).resolve().parent;C=W/'tank-conversion';O=W.parent/'outputs';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable,merge,differences
# Read serialization without importing a build script with side effects.
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
with zipfile.ZipFile(C/'backups/zz_SC2_CloneWars_UTAA_Model.scd') as z:
 payload={n:z.read(n) for n in z.namelist()};current_patch=LiteralTable(z.read('units/zz_clonewars_utaa_model_unit.bp').decode('utf-8-sig')).blueprint()
old=payload.copy();am_native=LiteralTable((W/'native/uncompiled_lua.scd/uncompiled/Units/UEF/UUL0203/UUL0203_unit.bp').read_text(encoding='utf-8')).blueprint()['Weapons'][1];intercept=copy.deepcopy(am_native)
intercept.update({'Label':'Turret02','DisplayName':'UT-AA Anti-Missile Interceptor','TurretBoneYaw':'Turret02','TurretBonePitch':'T02_Barrel01','TurretBoneMuzzle':'T02_B01_Muzzle01','RackBones':{1:{'RackBone':'T02_Barrel01','MuzzleBones':{1:'T02_B01_Muzzle01'}},2:{'RackBone':'T02_Barrel01','MuzzleBones':{1:'T02_B01_Muzzle02'}}},'NeedPrep':False,'InitiallyDisabled':False,'ScriptClass':'UTAAInterceptor','ScriptModule':'/units/CloneWars/UTAA/UTAA_script.lua'})
variants=[('',C/'native/uncompiled/Units/UEF/UUL0105/UUL0105_unit.bp'),('mods/DLC1/base/',C/'native/uncompiled/Units/UEF/UUL0105/UUL0105_unit.bp'),('mods/DLC1/shadow/',C/'native/uncompiled/mods/DLC1/shadow/Units/UEF/UUL0105/UUL0105_unit.bp')];reports=[]
for mount,p in variants:
 original=LiteralTable(p.read_text(encoding='utf-8')).blueprint();before=copy.deepcopy(original);merge(before,{k:v for k,v in current_patch.items() if k not in ['Merge','BlueprintId']});bp=copy.deepcopy(before);bp['BlueprintId']='uul0105';bp['Weapons'][2]=copy.deepcopy(intercept);bp['Description']='Mobile Anti-Air / Anti-Missile Defense';bp['ScriptModule']='/units/CloneWars/UTAA/UTAA_script.lua';bp['ScriptClass']='UTAA';bp['Display'].pop('Mesh',None);bp['Display'].pop('DisabledMeshBones',None)
 assert bp['Weapons'][1]==before['Weapons'][1]
 for k in ['Defense','Physics','Economy','Transport','Intel','Navigation']:assert bp[k]==before[k]
 assert bp.get('Abilities')==before.get('Abilities');assert bp['Weapons'][2]['Damage']==2 and bp['Weapons'][2]['RateOfFire']==3 and bp['Weapons'][2]['TargetRestrictOnlyAllow']=='TACTICAL MISSILE'
 assert bp['Weapons'][2]['TargetType']=='RULEWTT_Projectile';assert len(bp['Weapons'])==2
 text='UnitBlueprint '+lua(bp)+'\n';assert LiteralTable(text).blueprint()['Weapons']==bp['Weapons'];payload[mount+'units/zz_clonewars_utaa_model_unit.bp']=text.encode('utf-8');reports.append({'mount':mount,'changes':differences(before,bp),'primary_AA_weapon_exact':True,'health_cost_movement_transport_research_abilities_unchanged':True})
payload['units/CloneWars/UTAA/UTAA_script.lua']=(C/'UTAA_script.lua').read_bytes();assets=[n for n in old if n.endswith(('.scm','.dds','.sca')) or n.endswith('_mesh.bp')];assert all(payload[n]==old[n] for n in assets)
archive=O/'zz_SC2_CloneWars_UTAA_Model.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'revision':'dual-role-test-1','unit_id':'uul0105','identity':'UT-AA anti-air and anti-missile','archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'primary_anti_air':'Existing AntiAir01 blueprint and class inherited unchanged, including damage/rate/range/projectile/four-port aiming and pack/unpack','secondary_interceptor':{'mount':'Original researched ground gun, now visible and enabled from construction for user-requested first test','damage':2,'rate':3,'minimum_range':5,'maximum_range':32,'target':'TACTICAL MISSILE projectiles only','beam':'Native Sharp Shooter ZapperCollisionBeam02','muzzles':['T02_B01_Muzzle01','T02_B01_Muzzle02'],'shot_order':'One shot per native rack salvo, alternating the two existing ports; no extra concurrent shots'},'old_ground_upgrade':'Replaced by always-active interceptor. Label Turret02 preserved so existing research enable calls remain valid; previous ground-gun research is redundant in this first-test configuration and UI/balance cleanup remains.','model_textures_rig_animations_exactly_unchanged':True,'blueprint_checks':reports,'installed':False,'runtime_tested':False,'limits':['Test concurrent aircraft and tactical-missile targets to confirm independent mounts and no controller interference','Secondary mount original native geometry may be visually plain; user requested in-game trial','Public release rights and final balance/upgrade UI remain unresolved']}
(O/'UTAA-dual-role-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(C/'utaa-dual-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ['revision','sha256','primary_anti_air','model_textures_rig_animations_exactly_unchanged']}))
