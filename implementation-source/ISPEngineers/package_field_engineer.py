from pathlib import Path
import sys,json,zipfile,hashlib,copy,re,shutil
root=Path(__file__).resolve().parent.parent
project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(project/'tools'));import scm_v7
from poc_unit import LiteralTable,merge,differences
out=root/'outputs/Field-Engineer-ISP-Test';game=project/'local/dev-game/gamedata'
def lua(v):
    if isinstance(v,dict):return '{\n'+''.join((f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x)+',\n' for k,x in v.items())+'}'
    if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
    if isinstance(v,bool):return 'true' if v else 'false'
    return str(v)
folder='units/CloneWars/FieldEngineerISPTest/';payload={}
source=game/'zzzzzzzzzzzzzz_SC2_CloneWars_EngineerISP_Test.scd'
engineerhash=hashlib.sha256(source.read_bytes()).hexdigest()
with zipfile.ZipFile(source) as z:
    for n in z.namelist():
        if n.lower().endswith('.dds'):payload[folder+n.rsplit('/',1)[-1]]=z.read(n)
    source_mesh=next(z.read(n).decode() for n in z.namelist() if n.endswith('_mesh.bp'))
meshtext=source_mesh.replace('EngineerISPTest','FieldEngineerISPTest').replace('engineerisptest','fieldengineerisptest').replace('EngineerISP_lod','FieldEngineerISP_lod')
payload[folder+'FieldEngineerISPTest_mesh.bp']=meshtext.encode()
raw=(out/'FieldEngineerISP_lod0.win.scm').read_bytes();m=scm_v7.read(raw)
for i in range(3):
    for ext in ['.scm','.win.scm']:payload[folder+f'FieldEngineerISP_lod{i}'+ext]=raw
rig=json.loads((out/'rig-validation.json').read_text());offset=rig['beacon_offset_world_units']
script=(root/'work/field-engineer-native/UUL0003D1_script.lua').read_text(encoding='utf-8',errors='replace')
with zipfile.ZipFile(game/'z_uncompiled_lua_dlc1.scd') as z:
    for i,old in enumerate(['uef_uul0003d1_01_spinlight','uef_uul0003d1_02_glowlight'],1):
        n=next(n for n in z.namelist() if n.lower().endswith(old+'_emit.bp'))
        text=z.read(n).decode();new=f'cw_isp_field_beacon_{i}'
        text=text.replace(old,new)
        for axis in ['Y','Z']:
            text=re.sub(r'('+axis+r'PosCurve\s*=\s*\{.*?Keys\s*=\s*\{.*?y=)[-\d.]+',r'\g<1>0.0000',text,count=1,flags=re.S)
        payload[folder+new+'_emit.bp']=text.encode()
        script=script.replace('/effects/emitters/units/uef/uul0003d1/ambient/'+old+'_emit.bp','/'+folder+new+'_emit.bp')
needle="CreateAttachedEmitter( self, 'Turret01', self:GetArmy(), v )"
replacement="CreateAttachedEmitter( self, 'Tread02', self:GetArmy(), v ):ScaleEmitter(0.8)"
assert script.count(needle)==1;script=script.replace(needle,replacement)
payload[folder+'FieldEngineerISP_script.lua']=script.encode()
patch={'Merge':True,'BlueprintId':'uul0003d1','Display':{'MeshBlueprint':'/units/clonewars/fieldengineerisptest/fieldengineerisptest_mesh','DisplayName':'ISP Field Engineer','UniformScale':.1,'MovementEffects':{'Land':{'Treads':{'ScrollTreads':False}}}},'General':{'UnitName':'ISP Field Engineer'},'ScriptModule':'/'+folder+'FieldEngineerISP_script.lua','ScriptClass':'UUL0003D1'}
bp=LiteralTable((root/'work/field-engineer-native/UUL0003D1_unit.bp').read_text(encoding='utf-8')).blueprint();new=copy.deepcopy(bp);merge(new,{k:v for k,v in patch.items() if k not in ['Merge','BlueprintId']});diff=differences(bp,new)
allowed={'Display.MeshBlueprint','Display.DisplayName','Display.UniformScale','Display.MovementEffects.Land.Treads.ScrollTreads','General.UnitName','ScriptModule','ScriptClass'}
assert set(diff)<=allowed,diff
for key in ['Weapons','Build','Economy','Defense','Physics','Abilities','Intel','Transport','Categories']:
    assert new.get(key)==bp.get(key),key
assert len(new['Weapons'])==2
for w in new['Weapons'].values():
    for k in ['TurretBoneYaw','TurretBonePitch','TurretBoneMuzzle']:assert w[k] in m['names']
    for rack in w['RackBones'].values():
        assert rack['RackBone'] in m['names']
        for name in rack['MuzzleBones'].values():assert name in m['names']
for arm in bp['Build']['BuildArmManipulators'].values():
    for name in arm.values():assert name in m['names']
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/']:
    payload[prefix+'units/zzzzzzzzzzzzzzz_field_engineer_isp_test_unit.bp']=('UnitBlueprint '+lua(patch)+'\n').encode()
payload['FieldEngineerISPTest-Credits.txt']=b'Local testing only. Hull source uploaded by abdyla, described as SW:EAW; redistribution rights not verified. Native arm, antenna and effects: Gas Powered Games. Hull texture revisions: built-in image generation. No crew added. Field Engineer gameplay preserved.\n'
archive=out/'zzzzzzzzzzzzzzz_SC2_CloneWars_FieldEngineerISP_Test.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None;paths={n.lower() for n in z.namelist()}
    for path in re.findall(r"'(\/[^']+\.(?:dds|scm))'",meshtext):assert path.lstrip('/').lower() in paths,path
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in game.glob('*.scd')}
target=game/archive.name
if target.exists():
    backups=out/'backups';backups.mkdir(exist_ok=True);shutil.copy2(target,backups/(before[target.name][:12]+'-'+target.name))
shutil.copy2(archive,target);digest=hashlib.sha256(archive.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
assert all(hashlib.sha256((game/n).read_bytes()).hexdigest()==h for n,h in before.items() if n!=target.name)
assert hashlib.sha256(source.read_bytes()).hexdigest()==engineerhash
report={'date':'2026-10-26','unit':'uul0003d1','name':'ISP Field Engineer (Test)','installed_path':str(target),'archive_sha256':digest,'regular_engineer_package_unchanged':True,'regular_engineer_runtime_status':'User reports looks great and works, October 26, 2026','field_engineer_runtime_verified':False,'crew':'Empty cockpits; clone troopers deferred by user','mesh':scm_v7.summary(raw),'blueprint_changes':diff,'native_gameplay_preserved':True,'weapon_damage_range_rates_and_arcs_unchanged':True,'two_weapons_four_visible_muzzles':rig['muzzles'],'beacon_tip_world_units':offset,'native_beacon_effects_reused':True,'native_arm_script_preserved_except_beacon_attachment':True,'other_archives_unchanged':True,'rollback':'Close dev game; remove only '+str(target)+'; restart.','pending_runtime_tests':['Spawn/name and beacon glow at pylon tip','Repair actual HP and arm unfold/aim/stow','Both gun pairs fire from visible muzzle tips and follow targets','SpeedOverdrive, guard/assist, capture if available','Movement, transport, water effects, death/wreckage and research tooltip']}
(out/'installation.json').write_text(json.dumps(report,indent=2));(project/'planning/field-engineer-isp-test-1-2026-10-26.json').write_text(json.dumps(report,indent=2))
(out/'TEST-INSTRUCTIONS.txt').write_text('ISP FIELD ENGINEER TEST 1\nRestart the development game. Unlock/build the DLC Field Engineer. Name: ISP Field Engineer (Test). Verify the small illuminated pylon, repair arm and actual repairs, both paired guns and their muzzle origins, SpeedOverdrive and transport. Cockpits intentionally empty. Regular Engineer package unchanged. This Field Engineer is staged, not yet runtime-verified.\n\nRollback: close game and remove only '+str(target)+'\n')
print(json.dumps(report,indent=2))
