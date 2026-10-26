from pathlib import Path
import zipfile,sys,json,hashlib,shutil
sys.path.insert(0,r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/atte');import lua_constants as lc
live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars');p=live/'local/dev-game/gamedata/zzzzzzzzzz_SC2_CloneWars_UnitNames.scd';out=Path('outputs/SPHA-T');backup=Path('work/spha/name-fix-localization');backup.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
oldsha=sha(p);others={a.name:sha(a) for a in p.parent.glob('*CloneWars*.scd') if a!=p};shutil.copy2(p,backup/p.name)
with zipfile.ZipFile(p) as z:infos=z.infolist();original={i.filename:z.read(i.filename) for i in infos}
fixes={b'<LOC RESEARCH_NAME_0321>SPHA-T\0':b'SPHA-T\0',b"<LOC SC2_RESEARCH_INFO_0565>Unlock the 'SPHA-T' Experimental Unpacking Cannon.\0":b"Unlock the 'SPHA-T' Experimental Unpacking Cannon.\0"}
lc.rename=lambda value:fixes.get(value,value)
payload=dict(original);edits={}
for n,b in original.items():
 if n.lower().endswith('/research.lua'):
  after,changes,shape=lc.rewrite(b)
  if changes:
   again,pending,shape2=lc.rewrite(after);assert not pending and again==after and shape==shape2
   payload[n]=after;edits[n]=changes
assert len(edits)==1 and sum(len(x) for x in edits.values())==2,edits
staged=out/p.name
with zipfile.ZipFile(staged,'w') as z:
 for info in infos:z.writestr(info,payload[info.filename])
with zipfile.ZipFile(staged) as z:assert z.testzip() is None
assert sha(p)==oldsha;shutil.copy2(staged,p);assert sha(staged)==sha(p)
assert all(sha(p.parent/n)==h for n,h in others.items())
report={'revision':'research-literal-name-fix-2','reason':'User screenshot after restart still showed Jackhammer although patched strings/fallbacks contained SPHA-T. Remove the two native LOC tags from the DLC research NAME/INFO so localization cannot resolve the old text.','changed_constants':edits,'before_sha256':oldsha,'installed_sha256':sha(p),'other_mod_archives_unchanged':len(others),'gameplay':'No research costs, prerequisites, unlock IDs or simulation fields changed. Bytecode instruction structure unchanged.','runtime':'Installed; current running process requires full restart. Tooltip not yet verified live.'}
(out/'Research-tooltip-fix-2.json').write_text(json.dumps(report,indent=2),encoding='utf8');(live/'planning/spha-research-tooltip-fix-2.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(edits,indent=2));print('Installed;18 other mod archives unchanged')
