from pathlib import Path
import sys,zipfile,hashlib,json,re,shutil
w=Path('work/spha/name-fix');w.mkdir(parents=True,exist_ok=True)
o=Path('outputs/SPHA-T');live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
p=live/'local/dev-game/gamedata/zzzzzzzzzz_SC2_CloneWars_UnitNames.scd'
sys.path.insert(0,r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/atte');import lua_constants as lc
lc.rename=lambda value:re.sub(rb'Jack\s*hammer',b'SPHA-T',value,flags=re.I)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
others={a.name:sha(a) for a in p.parent.glob('*CloneWars*.scd') if a!=p}
oldsha=sha(p);backup=w/p.name
if not backup.exists():shutil.copy2(p,backup)
with zipfile.ZipFile(p) as z:infos=z.infolist();original={i.filename:z.read(i.filename) for i in infos}
payload=dict(original);changes={}
for name,raw in original.items():
 if name.lower().endswith(('/strings_db.lua','/research.lua','/achievements.lua')) and re.search(rb'Jack\s*hammer',raw,re.I):
  assert raw.startswith(b'\x1bLua')
  after,edits,shape=lc.rewrite(raw);again,pending,newshape=lc.rewrite(after)
  assert shape==newshape and again==after and not pending
  payload[name]=after;changes[name]=edits
assert set(changes)=={'loc/us/strings_db.lua','mods/DLC1/shadow/lua/sim/Research.lua'},changes.keys()
assert all(payload[n]==raw for n,raw in original.items() if n not in changes)
target=o/p.name
with zipfile.ZipFile(target,'w') as z:
 for info in infos:z.writestr(info,payload[info.filename])
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 assert set(z.namelist())==set(original)
 for n in changes:assert not re.search(rb'Jack\s*hammer',z.read(n),re.I)
assert sha(p)==oldsha,'Names package changed concurrently'
shutil.copy2(target,p);assert sha(p)==sha(target)
assert all(sha(p.parent/n)==h for n,h in others.items())
report={'change':'Jackhammer -> SPHA-T in unit localization and research tab title/tooltip/fallbacks','changed_files':changes,'bytecode_instructions_and_structure':'unchanged; only matching string constants rewritten','before_sha256':oldsha,'installed_sha256':sha(p),'installed_path':str(p),'backup':str(backup.resolve()),'other_mod_archives_unchanged':others,'runtime':'Requires restart to reload localization; no live UI verification claimed'}
(o/'Name-and-research-fix.json').write_text(json.dumps(report,indent=2),encoding='utf8');(live/'planning/spha-name-and-research-fix.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(changes,indent=2));print('Installed; other mod archives unchanged:',len(others))
