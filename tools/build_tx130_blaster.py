"""TX-130-only projectile appearance clone; retain native shell physics/script."""
import copy,hashlib,json,zipfile
from snapshot import ROOT
from poc_unit import LiteralTable,merge,differences
NAME='zz_SC2_CloneWars_TX130_Blaster.scd'
BASE='uncompiled/projectiles/UEF/UCannonShell01/UCannonShell01'
ID='/projectiles/clonewars/tx130/ucannonshell01_proj'
def parse(raw):return LiteralTable(raw.decode('cp1252').replace('ProjectileBlueprint','UnitBlueprint',1)).blueprint()
def lua(v,n=0):
    if isinstance(v,dict):return '{\n'+'\n'.join(' '*(n+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,n+4)+',' for k,x in v.items())+'\n'+' '*n+'}'
    if isinstance(v,str):return "'"+v.replace("'","\\'")+"'"
    if isinstance(v,bool):return 'true' if v else 'false'
    return str(v)
def main():
    with zipfile.ZipFile(ROOT/'local/installed-snapshot/gamedata/uncompiled_lua.scd') as z:
        original=parse(z.read(BASE+'_proj.bp'));donor=parse(z.read('uncompiled/projectiles/Illuminate/ILaser01/ILaser01_proj.bp'))
        script=z.read(BASE+'_script.lua')
    clone=copy.deepcopy(original);clone['BlueprintId']=ID
    clone['Display'].pop('Mesh',None);clone['Effects']=copy.deepcopy(donor['Effects'])
    assert clone['Physics']==original['Physics'] and clone['Categories']==original['Categories'] and clone['General']==original['General']
    changed=differences(original,clone)
    if any(not (x=='BlueprintId' or x.startswith('Display.Mesh') or x.startswith('Effects.')) for x in changed):raise ValueError(changed)
    patch={'Merge':True,'BlueprintId':'uul0101','Weapons':{i:{'ProjectileId':ID+'.bp'} for i in [1,2]}}
    checks=[]
    for archive,path in [('uncompiled_lua.scd','uncompiled/Units/UEF/UUL0101/UUL0101_unit.bp'),('z_uncompiled_lua_dlc1.scd','uncompiled/mods/DLC1/shadow/Units/UEF/UUL0101/UUL0101_unit.bp')]:
        with zipfile.ZipFile(ROOT/'local/installed-snapshot/gamedata'/archive) as z:before=LiteralTable(z.read(path).decode()).blueprint()
        after=copy.deepcopy(before);merge(after,{'Weapons':patch['Weapons']})
        assert differences(before,after)==['Weapons.1.ProjectileId','Weapons.2.ProjectileId']
        checks.append({'archive':archive,'only_changed_fields':differences(before,after),'damage_rate_range_equal':True})
    payload={'projectiles/CloneWars/TX130/UCannonShell01_proj.bp':('ProjectileBlueprint '+lua(clone)).encode(),'projectiles/CloneWars/TX130/UCannonShell01_script.lua':script}
    unit=('UnitBlueprint '+lua(patch)).encode()
    for prefix in ['', 'mods/DLC1/base/','mods/DLC1/shadow/']:payload[prefix+'units/zz_clonewars_blaster_unit.bp']=unit
    for path,raw in payload.items():
        dest=ROOT/'src'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    target=ROOT/'dist'/NAME
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
        for path,raw in payload.items():z.writestr(path,raw)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None and all(z.read(p)==raw for p,raw in payload.items())
    report={'archive':NAME,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'projectile_physics_equal':True,'projectile_script_byte_identical':True,'projectile_changes':changed,'unit_checks':checks,'effects_source':'Native ILaser01 laser trail/impact effects; color needs in-game review','scope':'Only TX-130 main and researched extra cannon; other units keep original shells','runtime_validation':'not tested'}
    (ROOT/'inventory/blaster-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
