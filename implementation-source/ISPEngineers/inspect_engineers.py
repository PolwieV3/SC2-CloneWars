from pathlib import Path
import zipfile,sys,json
root=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(root/'implementation-source/shared-pipeline')); import scm_v7
out=Path('work/engineer-native'); out.mkdir(exist_ok=True)
report={}
for archive in ['units.scd','z_dlc1.scd','uncompiled_lua.scd','z_uncompiled_lua_dlc1.scd']:
    with zipfile.ZipFile(root/'local/dev-game/gamedata'/archive) as z:
        for name in z.namelist():
            if not any('/'+uid+'/' in name.lower() for uid in ['uul0002','uul0003d1']):continue
            if not name.lower().endswith(('.scm','.dds','.bp','.lua')):continue
            p=out/archive/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(z.read(name))
            if name.lower().endswith('lod0.win.scm'):
                raw=z.read(name); m=scm_v7.read(raw)
                report[name]={**scm_v7.summary(raw),'names':m['names'],'bones':m['bones'],'bone_vertex_counts':{n:sum(v[16]==i for v in m['vertices']) for i,n in enumerate(m['names'])}}
(out/'rigs.json').write_text(json.dumps(report,indent=2))
print(json.dumps({n:{k:v for k,v in r.items() if k not in ['bones']} for n,r in report.items()},indent=2))
