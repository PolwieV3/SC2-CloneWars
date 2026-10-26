from pathlib import Path
import sys,zipfile,json,hashlib
W=Path(__file__).resolve().parent;C=W/'tank-conversion';O=W.parent/'outputs';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
from poc_unit import LiteralTable
reports=[]
for unit,prefix,filename in [('uul0203','UTAT','zz_SC2_CloneWars_UTAT_Model.scd'),('uul0105','UTAA','zz_SC2_CloneWars_UTAA_Model.scd')]:
 with zipfile.ZipFile(O/filename) as z:
  names=z.namelist();assert z.testzip() is None;models=[scm_v7.read(z.read(n)) for n in names if n.lower().endswith('.win.scm')];assert len(models)==3
  patches=[n for n in names if n.endswith('_unit.bp')];assert len(patches)==3
  for n in patches:
   d=LiteralTable(z.read(n).decode('utf-8-sig')).blueprint();assert d['BlueprintId']==unit and not d.get('Merge');bone_names=set(models[0]['names'])
   for m in models:assert set(m['names'])==bone_names
   for w in d['Weapons'].values():
    for key in ['TurretBoneYaw','TurretBonePitch','TurretBoneMuzzle']:assert w[key] in bone_names,(filename,key,w[key])
    for rack in w['RackBones'].values():
     assert rack['RackBone'] in bone_names
     for muzzle in rack['MuzzleBones'].values():assert muzzle in bone_names
   script=d['ScriptModule'].lstrip('/');assert script in names
   if prefix=='UTAT':
    assert len(d['Weapons'])==3 and d['Weapons'][1]['Damage']==75
    assert all(w['WeaponCategory']=='Direct Fire' and w['ScriptClass']=='UTATTankGun' and w['BallisticArc']=='RULEUBA_None' and w['ProjectilesPerOnFire']==1 for w in d['Weapons'].values())
    assert all(w['FireTargetLayerCaps']['Land']=='Land|Water|Seabed' and w['TurretYawRange']==20 and w['TurretPitchRange']==20 and w['TurretPitch']==15 for w in d['Weapons'].values())
    assert d['General']['CommandCaps']['RULEUCC_Attack'] and d['General']['CommandCaps']['RULEUCC_RetaliateToggle']
    assert all(w['ProjectileId'].lstrip('/') in {s.lower() for s in names} for w in d['Weapons'].values())
    code=z.read(script).decode('utf-8-sig');assert 'DefaultBeamWeapon' not in code and 'AntiMissile01' not in code;assert code.count('NativeTankGun.CreateProjectileAtMuzzle(self,muzzle)')==1
    assert b'SetBallisticAcceleration(0)' in z.read('projectiles/CloneWars/UTAT/UTATTankShot_script.lua')
   else:
    aa,am=d['Weapons'][1],d['Weapons'][2];assert aa['Label']=='AntiAir01' and am['Label']=='Turret02';assert am['TargetType']=='RULEWTT_Projectile' and am['TargetRestrictOnlyAllow']=='TACTICAL MISSILE';assert not am['InitiallyDisabled'] and not am['NeedPrep']
    assert aa['TurretBoneYaw']!=am['TurretBoneYaw'] and aa['TurretBonePitch']!=am['TurretBonePitch'];assert 'DisabledMeshBones' not in d['Display'];assert len(d['Weapons'])==2
    assert aa['WeaponUnpacks'] and aa['WeaponUnpackAnimation']=='/units/UEF/uul0105/uul0105_aopen01.sca'
    code=z.read(script).decode('utf-8-sig');assert 'Class(Base.Weapons.AntiAir01)' in code and 'ZapperCollisionBeam02' in code;assert code.count('return DefaultBeamWeapon.CreateProjectileAtMuzzle(self,muzzle)')==1
 reports.append({'unit':unit,'archive':filename,'crc':True,'base_and_DLC_role_bone_script_dependency_checks':True,'all_three_LODs_valid':True,'sha256':hashlib.sha256((O/filename).read_bytes()).hexdigest()})
result={'status':'passed','packages':reports,'runtime_tested':False,'scope':'UTAT surface-tank conversion with roof damage 75, UTAA retained aircraft weapon plus separate native secondary anti-missile beam; UTAT assets unchanged; UTAA original geometry retained plus connecting mount; rigs/textures/animations unchanged','research_limit':'UTAA secondary interceptor enabled from build for first test; former ground-gun research is redundant, label preserved for safe existing enable calls'}
(O/'Dual-role-package-checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
