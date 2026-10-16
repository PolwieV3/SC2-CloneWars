"""Build a deterministic, minimal name-only blueprint merge archive."""
import hashlib, json, pathlib, re, shutil, zipfile
import copy
from poc_unit import LiteralTable, differences, merge
ROOT=pathlib.Path(__file__).resolve().parents[1]
NAME='zz_SC2_CloneWars_POC.scd'
def main():
    source=ROOT/'src/units/zz_clonewars_rename_unit.bp'
    raw=source.read_text(encoding='utf-8').replace('\r\n','\n')
    stripped=re.sub(r'--[^\n]*','',raw)
    # Full grammar for this deliberately narrow POC; no other fields can slip in.
    pattern=r"\s*UnitBlueprint\s*\{\s*Merge\s*=\s*true\s*,\s*BlueprintId\s*=\s*'uul0101'\s*,\s*Display\s*=\s*\{\s*DisplayName\s*=\s*'TX-130 Saber Tank'\s*,\s*\}\s*,\s*General\s*=\s*\{\s*UnitName\s*=\s*'TX-130 Saber Tank'\s*,\s*\}\s*,\s*\}\s*"
    if not re.fullmatch(pattern,stripped): raise SystemExit('POC validation failed: only the two approved name fields are allowed.')
    manifest=json.loads((ROOT/'inventory/snapshot-manifest.json').read_text())
    patch=LiteralTable(raw).blueprint()
    source_checks=[]
    for scope, archive, path in [('base','uncompiled_lua.scd','uncompiled/Units/UEF/UUL0101/UUL0101_unit.bp'),('dlc','z_uncompiled_lua_dlc1.scd','uncompiled/mods/DLC1/shadow/Units/UEF/UUL0101/UUL0101_unit.bp')]:
        with zipfile.ZipFile(ROOT/'local/installed-snapshot/gamedata'/archive) as z: original_raw=z.read(path)
        original=LiteralTable(original_raw.decode('utf-8').replace('\r','')).blueprint()
        changed=copy.deepcopy(original)
        merge(changed,{k:v for k,v in patch.items() if k not in {'BlueprintId','Merge'}})
        changed_fields=differences(original,changed)
        if changed_fields!=['Display.DisplayName','General.UnitName']:raise SystemExit(f'Unexpected source changes for {scope}: {changed_fields}')
        source_checks.append({'scope':scope,'archive':archive,'path':path,'source_sha256':hashlib.sha256(original_raw).hexdigest(),'changed_fields':changed_fields,'all_other_source_fields_equal':True})
    data=raw.encode('utf-8');dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    target=dist/NAME
    paths=['units/zz_clonewars_rename_unit.bp','mods/DLC1/base/units/zz_clonewars_rename_unit.bp','mods/DLC1/shadow/units/zz_clonewars_rename_unit.bp']
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
        for path in paths:
            info=zipfile.ZipInfo(path,(2026,10,3,0,0,0));info.external_attr=0o644<<16;z.writestr(info,data)
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None or z.namelist()!=paths or any(z.read(p)!=data for p in paths):raise RuntimeError('Archive validation failed')
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (dist/(NAME+'.sha256')).write_text(digest+'  '+NAME+'\n')
    report={'archive':NAME,'sha256':digest,'bytes':target.stat().st_size,'baseline':manifest['baseline'],'entries':paths,'target':'uul0101','changed_fields':['Display.DisplayName','General.UnitName'],'source_checks':source_checks,'static_validation':'passed: exact name-only merge schema, real base/DLC source comparisons and archive round-trip','runtime_validation':'not performed','dlc_validation':'packaged base and shadow merges; runtime order remains to be verified'}
    runtime_path=ROOT/'inventory/runtime-validation.json'
    if runtime_path.exists():
        runtime=json.loads(runtime_path.read_text())
        if runtime.get('archive_sha256')==digest:
            report['runtime_validation']=runtime['result']
            report['runtime_evidence']='inventory/runtime-validation.json'
            if runtime.get('dlc_location_observed'):
                report['dlc_validation']='Selected-unit rename observed in a DLC-active development-copy session; base-only test remains pending'
    (ROOT/'inventory'/'build-validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
