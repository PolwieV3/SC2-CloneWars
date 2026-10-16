"""First TX-130 audio-routing checkpoint using installed FMOD events."""
import copy, hashlib, json, zipfile
from snapshot import ROOT
from poc_unit import LiteralTable, merge, differences
NAME='zz_SC2_CloneWars_TX130_Audio.scd'
MOVE='SC2/SC2/Units/illuminate/UIL0101/snd_UIL0101_Tank_Move_Loop'
FIRE='SC2/SC2/Units/illuminate/UIL0101/snd_UIL0101_Tank_Cannon_Tau'
PATCH="""UnitBlueprint {
    Merge = true,
    BlueprintId = 'uul0101',
    Audio = { AmbientMove = '%s', },
    Weapons = {
        [1] = { Audio = { RackSalvoBeginFire = '%s', }, },
        [2] = { Audio = { RackSalvoBeginFire = '%s', }, },
    },
}
""" % (MOVE,FIRE,FIRE)

def main():
    patch=LiteralTable(PATCH).blueprint()
    allowed=['Audio.AmbientMove','Weapons.1.Audio.RackSalvoBeginFire','Weapons.2.Audio.RackSalvoBeginFire']
    checks=[]
    for archive,path in [('uncompiled_lua.scd','uncompiled/Units/UEF/UUL0101/UUL0101_unit.bp'),('z_uncompiled_lua_dlc1.scd','uncompiled/mods/DLC1/shadow/Units/UEF/UUL0101/UUL0101_unit.bp')]:
        with zipfile.ZipFile(ROOT/'local/installed-snapshot/gamedata'/archive) as z:before=LiteralTable(z.read(path).decode()).blueprint()
        assert before['Weapons'][1]['Label']=='Turret01' and before['Weapons'][2]['Label']=='Turret01ExtraBarrel'
        after=copy.deepcopy(before);merge(after,{k:v for k,v in patch.items() if k not in {'Merge','BlueprintId'}})
        changed=differences(before,after)
        if changed!=allowed:raise ValueError(changed)
        checks.append({'archive':archive,'changed_fields':changed,'all_other_fields_equal':True})
    # Validate complete paths against source blueprint and event names in FEV.
    with zipfile.ZipFile(ROOT/'local/installed-snapshot/gamedata/uncompiled_lua.scd') as z:
        donor=LiteralTable(z.read('uncompiled/Units/Illuminate/UIL0101/UIL0101_unit.bp').decode()).blueprint()
    assert donor['Audio']['AmbientMoveLand']==MOVE
    assert donor['Weapons'][1]['Audio']['Fire']==FIRE
    fev=(ROOT/'local/installed-snapshot/sounds/win/fmod/SC2.fev').read_bytes()
    assert all(event.rsplit('/',1)[1].encode()+b'\0' in fev for event in [MOVE,FIRE])
    source=ROOT/'src/units/zz_clonewars_audio_unit.bp';source.write_text(PATCH,encoding='utf-8')
    entries=[prefix+'units/zz_clonewars_audio_unit.bp' for prefix in ['', 'mods/DLC1/base/','mods/DLC1/shadow/']]
    target=ROOT/'dist'/NAME
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
        for path in entries:z.writestr(path,PATCH.encode())
    with zipfile.ZipFile(target) as z:assert z.testzip() is None and all(z.read(p)==PATCH.encode() for p in entries)
    sha=hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT/'dist'/(NAME+'.sha256')).write_text(sha+'  '+NAME+'\n')
    report={'stage':'Audio routing POC, temporary stock energy/hover events; not final Star Wars audio','archive':NAME,'sha256':sha,'source_checks':checks,'events':[MOVE,FIRE],'event_names_found_in_native_fev':True,'runtime_validation':'not tested','custom_bank_status':'Native FSB files do not have plain FSB headers; custom bank loading/export remains to be established.','simulation_changes':[]}
    (ROOT/'inventory/audio-validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
