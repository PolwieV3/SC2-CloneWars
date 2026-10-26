from pathlib import Path
import hashlib
import json
import shutil
import sys
import zipfile

root=Path(__file__).resolve().parents[2]
live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
gamedata=live/'local/dev-game/gamedata'
source=root/'work/spha/Deploy_Ability_override.lua'
target=root/'outputs/SPHA-T/a0_SC2_CloneWars_SPHA_Deploy.scd'
installed=gamedata/target.name
payload=source.read_bytes()
paths=['abilities/Deploy_Ability.lua','mods/DLC1/shadow/abilities/Deploy_Ability.lua','uncompiled/mods/DLC1/shadow/abilities/Deploy_Ability.lua']
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for name in paths:z.writestr(name,payload)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert all(z.read(name)==payload for name in paths)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if '--stage-only' in sys.argv:
    print(json.dumps({'staged':str(target),'sha256':sha(target),'runtime':'Installation waits for the isolated game to close.'},indent=2))
    raise SystemExit(0)
before={p.name:sha(p) for p in gamedata.glob('*.scd') if p!=installed}
if installed.exists() and sha(installed)!=sha(target):
    backup=root/'work/spha/backups'/('pre-deploy-priority-'+sha(installed)[:12])
    backup.mkdir(parents=True,exist_ok=True)
    shutil.copy2(installed,backup/installed.name)
shutil.copy2(target,installed)
assert sha(installed)==sha(target)
assert before=={p.name:sha(p) for p in gamedata.glob('*.scd') if p!=installed}
report={'revision':'beam-test-6-dlc-deploy-enable','archive':str(installed),'sha256':sha(installed),'paths':paths,'other_archives_unchanged':True,'runtime':'Full restart required; planted target acquisition and firing need in-game verification.'}
(root/'outputs/SPHA-T/Deploy-priority-installation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(live/'planning/spha-deploy-priority-installation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
