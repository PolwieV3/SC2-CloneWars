from pathlib import Path
import hashlib,json,shutil,zipfile,datetime,subprocess
W=Path(__file__).resolve().parent;R=W.parents[1];O=R/'outputs/SPHA-T'
live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
src=O/'zzzzzz_SC2_CloneWars_SPHA.scd';dst=live/'local/dev-game/gamedata'/src.name
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for data in iter(lambda:f.read(4*1024*1024),b''):h.update(data)
 return h.hexdigest()
running=subprocess.run(['tasklist','/FI','IMAGENAME eq SupremeCommander2.exe','/FO','CSV','/NH'],capture_output=True,text=True).stdout
assert 'SupremeCommander2.exe' not in running,'Close the running game before installing.'
report=json.loads((O/'Package-validation.json').read_text(encoding='utf8'))
checks=json.loads((O/'Native-pose-validation.json').read_text(encoding='utf8'))
assert report['sha256']==checks['package_sha256']==sha(src) and checks['checks']=='passed'
with zipfile.ZipFile(src) as z:assert z.testzip() is None
before={p.name:sha(p) for p in dst.parent.glob('*.scd') if p!=dst}
backup=W/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
previous=sha(dst) if dst.exists() else None
oldrecord=live/'planning/spha-beam-test-1-installation.json'
original_previous=previous
if oldrecord.exists():
 old=json.loads(oldrecord.read_text(encoding='utf8'))
 if old.get('sha256')==previous:original_previous=old.get('original_pretest_sha256',old.get('previous_sha256'))
if previous:shutil.copy2(dst,backup/dst.name)
# Exercise rollback only on this package's own path, then install the validated bytes.
shutil.copy2(src,dst);assert sha(dst)==sha(src)
if previous:shutil.copy2(backup/dst.name,dst);assert sha(dst)==previous
else:dst.unlink();assert not dst.exists()
shutil.copy2(src,dst);assert sha(dst)==sha(src)
after={p.name:sha(p) for p in dst.parent.glob('*.scd') if p!=dst};assert before==after,'Concurrent archive changes detected; inspect separately.'
report.update({'installed':True,'installed_path':str(dst),'installed_sha256_verified':True,'previous_sha256':previous,'backup':str(backup) if previous else None,'other_archives_unchanged':before,'rollback_file_test':'passed','runtime':'Installed for first user test; no in-game loading or gameplay acceptance claimed.','rollback':'Close the game and remove only '+str(dst) if previous is None else 'Close the game and restore '+str(backup/dst.name)})
report['original_pretest_sha256']=original_previous
if original_previous is None:report['rollback']='Close the game and remove only '+str(dst)+'; no SPHA package existed before this task.'
(O/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(live/'planning/spha-beam-test-1-installation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(live/'planning/spha-beam-test-1-source-validation.json').write_bytes((O/'Source-motion-validation.json').read_bytes())
(live/'planning/spha-beam-test-1-native-validation.json').write_bytes((O/'Native-pose-validation.json').read_bytes())
print('Installed',dst,'SHA256',sha(dst),'Other archives unchanged:',len(before),'Rollback passed')
