from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).parent;out=r.parents[1]/'outputs/Juggernaut';live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars');src=out/'zzzzzz_SC2_CloneWars_Juggernaut_Balance.scd';dest=live/'local/dev-game/gamedata'/src.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();others={p.name:sha(p) for p in dest.parent.glob('*CloneWars*.scd') if p!=dest}
if dest.exists():shutil.copy2(dest,r/'balance-package-before.scd')
shutil.copy2(src,dest);assert sha(dest)==sha(src)
for n,h in others.items():assert sha(dest.parent/n)==h
d=json.loads((r/'balance-validation.json').read_text(encoding='utf-8'));d.update({'installed':True,'installed_path':str(dest),'other_packages_unchanged':others,'rollback':d.get('rollback','Remove only '+str(dest))})
for p in [r/'balance-validation.json',out/'Balance-validation.json',live/'planning/juggernaut-balance-2026-10-25.json']:p.write_text(json.dumps(d,indent=2),encoding='utf-8')
print('Installed Juggernaut balance package '+sha(dest));print('Existing mod packages unchanged: '+str(len(others)))
