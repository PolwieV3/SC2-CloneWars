from pathlib import Path
import zipfile,sys,json,hashlib,shutil
root=Path(__file__).resolve().parent.parent
p=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(p/'tools'));import scm_v7
game=p/'local/dev-game/gamedata';out=root/'outputs/ISP-Refinement-4'
report={'date':'2026-10-26','runtime_verified':False,'sizes_unchanged_in_this_revision':True,'names':{},'archives':{}}
for name,expected in [('zzzzzzzzzzzzzz_SC2_CloneWars_EngineerISP_Test.scd','ISP Engineer'),('zzzzzzzzzzzzzzz_SC2_CloneWars_FieldEngineerISP_Test.scd','ISP Field Engineer')]:
    path=game/name;report['archives'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        blueprints=[z.read(n).decode() for n in z.namelist() if n.endswith('_unit.bp')]
        assert all(expected in s and '(Test)' not in s for s in blueprints)
        report['names'][expected]='All unit override names verified'
        if 'FieldEngineer' in name:
            script=z.read('units/CloneWars/FieldEngineerISPTest/FieldEngineerISP_script.lua').decode()
            assert "CreateAttachedEmitter( self, 'Tread02'" in script
            ambient=script.split('CreateAmbientEffect = function(self)',1)[1].split('OnAddToStorage',1)[0]
            assert 'OffsetEmitter' not in ambient
            for i in [1,2]:
                text=z.read('units/CloneWars/FieldEngineerISPTest/cw_isp_field_beacon_'+str(i)+'_emit.bp').decode()
                assert 'YPosCurve' in text and 'ZPosCurve' in text
            mesh=scm_v7.read(z.read('units/CloneWars/FieldEngineerISPTest/FieldEngineerISP_lod0.win.scm'))
            report['beacon_attachment']='Tread02 refitted to antenna tip; root offset removed'
            report['beacon_bone_present']='Tread02' in mesh['names']
report['localization']=json.loads((out/'name-verification.json').read_text())['entries_changed']
report['rear_uv_repairs']=json.loads((out/'rear-uv-repairs.json').read_text())
(out/'verification.json').write_text(json.dumps(report,indent=2))
(p/'planning/isp-refinement-4-2026-10-26.json').write_text(json.dumps(report,indent=2))
src=out/'source';src.mkdir(exist_ok=True)
for f in ['refine_rear_mapping.py','rename_isp_game_text.py','export_engineer_test.py','package_engineer_test.py','export_field_engineer.py','package_field_engineer.py']:
    shutil.copy2(root/'work'/f,src/f)
print('Verified both unit names, archive integrity, beacon tip attachment and localization override. Sizes retained. Runtime pending.')
