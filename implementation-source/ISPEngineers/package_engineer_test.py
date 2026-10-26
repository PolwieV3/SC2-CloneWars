from pathlib import Path
import sys,json,zipfile,hashlib,struct,copy,shutil,datetime
from PIL import Image
root=Path(__file__).resolve().parent.parent
project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(project/'tools'));import scm_v7
from poc_unit import LiteralTable,merge,differences
out=root/'outputs/Engineer-ISP-Test';game=project/'local/dev-game/gamedata'
def lua(v):
    if isinstance(v,dict):return '{\n'+''.join((f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x)+',\n' for k,x in v.items())+'}'
    if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
    if isinstance(v,bool):return 'true' if v else 'false'
    return str(v)
def dds(im):
    im=im.convert('RGBA');w,h=im.size;levels=[]
    while True:
        levels.append(im.tobytes('raw','BGRA'))
        if im.size==(1,1):break
        im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
    values=[124,0x2100f,h,w,w*4,0,len(levels)]+[0]*11+[32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000]+[0x401008,0,0,0,0]
    return b'DDS '+struct.pack('<31I',*values)+b''.join(levels)
folder='units/CloneWars/EngineerISPTest/';payload={}
meshraw=(out/'EngineerISP_lod0.win.scm').read_bytes();parsed=scm_v7.read(meshraw)
native=root/'work/engineer-native/units.scd/units/UEF/UUL0002'
original=scm_v7.read((native/'UUL0002_lod0.win.scm').read_bytes())
assert parsed['names']==original['names'];assert [b[24] for b in parsed['bones']]==[b[24] for b in original['bones']]
assert len(parsed['materials'])==2
for lod in range(3):
    for ext in ['.scm','.win.scm']:payload[folder+f'EngineerISP_lod{lod}'+ext]=meshraw
for name,im in [('HullDiffuse',Image.open(root/'outputs/ISP-Texture-R3/hull-atlas-r3.png').resize((2048,2048),Image.Resampling.LANCZOS)),('HullNormal',Image.new('RGBA',(4,4),(128,128,255,128))),('HullMask',Image.new('RGBA',(4,4),(0,0,0,255)))]:
    for ext in ['.dds','.win.dds']:payload[folder+name+ext]=dds(im)
for name in ['Diffuse','Normal','Mask']:
    data=(native/f'UUL0002_{name}.win.dds').read_bytes()
    for ext in ['.dds','.win.dds']:payload[folder+'Arm'+name+ext]=data
meshid='/units/clonewars/engineerisptest/engineerisptest_mesh'
materials={}
for i,part in enumerate(['Hull','Arm'],1):
    materials[i]={key:'/units/CloneWars/EngineerISPTest/'+part+name+'.dds' for key,name in [('DiffuseName','Diffuse'),('NormalName','Normal'),('MaskName','Mask')]}
    materials[i]['ShaderMacros']='ambient_lighting, diffuse_lighting, specular_lighting, point_cloud'
mesh={'BlueprintId':meshid,'LODs':{i+1:{'LODCutoff':cutoff,'MeshName':f'/units/CloneWars/EngineerISPTest/EngineerISP_lod{i}.scm','MaterialSets':{1:{'Materials':materials}}} for i,cutoff in enumerate([50,130,500])}}
payload[folder+'EngineerISPTest_mesh.bp']=('MeshBlueprint '+lua(mesh)+'\n').encode()
patch={'Merge':True,'BlueprintId':'uul0002','Display':{'MeshBlueprint':meshid,'DisplayName':'ISP Engineer','MovementEffects':{'Land':{'Treads':{'ScrollTreads':False}}}},'General':{'UnitName':'ISP Engineer'}}
allowed={'Display.MeshBlueprint','Display.DisplayName','Display.MovementEffects.Land.Treads.ScrollTreads','General.UnitName'}
checks=[]
for a in ['uncompiled_lua.scd','z_uncompiled_lua_dlc1.scd']:
    base=root/'work/engineer-native'/a
    for src in base.rglob('UUL0002_unit.bp'):
        bp=LiteralTable(src.read_text(encoding='utf-8-sig')).blueprint();new=copy.deepcopy(bp);merge(new,{k:v for k,v in patch.items() if k not in ['Merge','BlueprintId']})
        diff=differences(bp,new)
        assert set(diff)<=allowed,(src,diff)
        checks.append({'source':str(src),'changes':diff})
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:
    payload[prefix+'units/zzzzzzzzzzzzzz_engineer_isp_test_unit.bp']=('UnitBlueprint '+lua(patch)+'\n').encode()
payload['EngineerISPTest-Credits.txt']=b'Local test only. ISP source uploaded by abdyla, described as SW:EAW; redistribution rights unverified. Native Engineer arm/materials: Gas Powered Games. Hull texture revisions made with built-in image generation. No source assets published. UUL0002 regular Engineer only; Field Engineer not modified.\n'
archive=out/'zzzzzzzzzzzzzz_SC2_CloneWars_EngineerISP_Test.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in sorted(payload.items()):z.writestr(name,data)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    paths={n.lower() for n in z.namelist()}
    for lod in mesh['LODs'].values():
        assert lod['MeshName'].lstrip('/').lower() in paths
        for material in lod['MaterialSets'][1]['Materials'].values():
            for k,v in material.items():
                if k.endswith('Name'):assert v.lstrip('/').lower() in paths
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in game.glob('*.scd')}
target=game/archive.name
if target.exists():
    backups=out/'backups';backups.mkdir(exist_ok=True);shutil.copy2(target,backups/(before[target.name][:12]+'-'+target.name))
shutil.copy2(archive,target)
digest=hashlib.sha256(archive.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
assert all(hashlib.sha256((game/n).read_bytes()).hexdigest()==h for n,h in before.items() if n!=target.name)
report={'date':'2026-10-26','unit':'uul0002','role':'Regular Engineer','archive':str(archive),'installed':str(target),'sha256':digest,'mesh':scm_v7.summary(meshraw),'blueprint_checks':checks,'other_archives_unchanged':True,'native_script_preserved':True,'native_joint_names_and_hierarchy_preserved':True,'arm_bind_positions_refitted':True,'gameplay_stats_unchanged':True,'weapons_added':False,'field_engineer_modified':False,'runtime_verified':False,'limitations':['Native arm bind positions refitted; build/repair/reclaim animation requires in-game validation','Native water animation, movement, transport, effects, death/wreckage need runtime tests','ISP guns decorative; regular Engineer has no added weapon','Shader appearance may differ from Blender; hull uses neutral normal map; native arm normal/mask retained','Final roster scale deferred'],'rollback':'Close the development game, remove only '+str(target)+', then relaunch.'}
(out/'installation.json').write_text(json.dumps(report,indent=2));(project/'planning/engineer-isp-test-1-2026-10-26.json').write_text(json.dumps(report,indent=2))
(out/'TEST-INSTRUCTIONS.txt').write_text('ISP ENGINEER TEST 1 — October 26, 2026\n\nInstalled only in the isolated development game, UUL0002 regular Engineer. Restart Launch-Skirmish-Test.cmd to load. Build a new Engineer from the ACU; selection name should be ISP Engineer (Test).\n\nCheck: spawn/name/icon; move/turn; construction arm unfold/aim/stow; build completion; repair actual HP; reclaim actual resources; capture/assist where available; water transition; transport; selection; death/wreckage. Confirm effects originate at the visible arm tip. ISP guns should not fire. Field Engineer remains unchanged.\n\nNo runtime test has been claimed. See installation.json for exact package hash and rollback.\n')
print(json.dumps(report,indent=2))
