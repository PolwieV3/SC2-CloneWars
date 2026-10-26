from pathlib import Path
import hashlib,json,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[2];O=R/'outputs/AT-TE';W=R/'work/atte'
live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
src=O/'zzzzzz_SC2_CloneWars_ATTE.scd';dst=live/'local/dev-game/gamedata'/src.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with zipfile.ZipFile(src) as z:assert z.testzip() is None
report=json.loads((O/'Package-validation.json').read_text(encoding='utf8'));assert report['sha256']==sha(src)
pose=json.loads((O/'Native-pose-validation.json').read_text(encoding='utf8'));assert pose['bone_and_muzzle_references']=='pass'
others={p.name:sha(p) for p in dst.parent.glob('*CloneWars*.scd') if p!=dst}
previous=None
if dst.exists():
 previous=sha(dst);backup=W/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True);shutil.copy2(dst,backup/dst.name)
shutil.copy2(src,dst);assert sha(src)==sha(dst)
for n,h in others.items():assert sha(dst.parent/n)==h,('Other package changed during installation',n)
report.update({'installed':True,'installed_path':str(dst),'installed_sha256_verified':True,'previous_sha256':previous,'other_packages_unchanged':others,'pose_validation':pose,'runtime':'Installed; in-game loading, walk, aiming, firing and balance not yet verified','rollback':'Remove only '+str(dst)+' to restore the prior King Kriptor; restore backup first if previous_sha256 is populated.'})
(O/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(live/'planning/atte-mount-test-6-installation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
checkpoint=json.loads((O/'Implementation-checkpoint.json').read_text(encoding='utf8'));checkpoint['integration']='mount-test-6 installed in isolated dev game; runtime unverified';checkpoint['package']=report['installed_path'];checkpoint['package_sha256']=report['sha256'];checkpoint['next_steps']=['Restart isolated dev game and build a fresh AT-TE from existing King Kriptor research/build slot','Verify range overlay, firing and aiming on a newly built AT-TE','Tune gameplay balance and size from user feedback'];(O/'Implementation-checkpoint.json').write_text(json.dumps(checkpoint,indent=2),encoding='utf8')
print('Installed AT-TE mount-test-6:',sha(dst));print('Other CloneWars archives unchanged:',len(others))
