from pathlib import Path
import json,hashlib,shutil,zipfile
W=Path(__file__).resolve().parent;C=W/'tank-conversion';O=W.parent/'outputs';L=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars');G=L/'local/dev-game/gamedata';assert G.resolve().is_relative_to((L/'local/dev-game').resolve())
check=json.loads((O/'Dual-role-package-checks.json').read_text(encoding='utf-8'));assert check['status']=='passed';filenames=[p['archive'] for p in check['packages']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p in check['packages']:assert sha(O/p['archive'])==p['sha256']
for name in filenames:assert sha(G/name)==sha(C/'backups'/name),'Installed package changed since role-conversion snapshot: '+name
others={p.name:sha(p) for p in G.glob('*.scd') if p.name not in filenames};old={n:sha(G/n) for n in filenames}
try:
 for n in filenames:shutil.copy2(O/n,G/n);assert sha(G/n)==sha(O/n)
 # File-level two-package rollback, then restore this exact test pair.
 for n in filenames:shutil.copy2(C/'backups'/n,G/n);assert sha(G/n)==old[n]
 for n in filenames:shutil.copy2(O/n,G/n);assert sha(G/n)==sha(O/n)
 assert others=={p.name:sha(p) for p in G.glob('*.scd') if p.name not in filenames}
except Exception:
 for n in filenames:shutil.copy2(C/'backups'/n,G/n)
 raise
for name,report_name in [('zz_SC2_CloneWars_UTAT_Model.scd','Tank-conversion-validation.json'),('zz_SC2_CloneWars_UTAA_Model.scd','UTAA-dual-role-validation.json')]:
 d=json.loads((O/report_name).read_text(encoding='utf-8'));d.update({'installed':True,'installed_path':str(G/name),'installed_hash_verified':True,'previous_sha256':old[name],'rollback_archive':str(C/'backups'/name),'unchanged_other_archive_hashes':others,'pair_file_level_rollback_test':'passed; original pair restored and verified, then new pair reinstalled','runtime_tested':False})
 (O/report_name).write_text(json.dumps(d,indent=2),encoding='utf-8')
 if name.startswith('zz_SC2_CloneWars_UTAT'):(O/'Package-validation.json').write_text(json.dumps(d,indent=2),encoding='utf-8')
 (L/'planning'/('utat-tank-conversion-2026-10-24.json' if 'UTAT' in name else 'utaa-dual-role-2026-10-24.json')).write_text(json.dumps(d,indent=2),encoding='utf-8')
check.update({'installed':True,'other_archives_unchanged':len(others),'other_archive_hashes':others,'previous_pair_hashes':old,'file_level_rollback_passed':True});(O/'Dual-role-package-checks.json').write_text(json.dumps(check,indent=2),encoding='utf-8');print('Installed both test packages; other archives unchanged:',len(others));print([(n,sha(G/n)) for n in filenames])
