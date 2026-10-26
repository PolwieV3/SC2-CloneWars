"""Prepare reviewed source/data snapshot; never stage native game/model assets."""
from pathlib import Path
import json,shutil,hashlib,datetime,zipfile
R=Path(__file__).resolve().parents[2];O=R/'outputs/Project-Sync-2026-10-25'
L=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
state=json.loads((O/'project-state.json').read_text(encoding='utf-8'))
S=L/'project-registry';S.mkdir(exist_ok=True)
for name in ['project-state.json','roster.csv','balance-metrics.csv','weapons.csv','gameplay-differences.csv','installed-packages.csv','CHAT-MODE-FULL-PROMPT.md','workbook-validation.json']:
    if (O/name).exists():shutil.copy2(O/name,S/name)
shutil.copytree(O/'Obsidian-SC2',S/'Obsidian',dirs_exist_ok=True)
decisions={'as_of':'2026-10-25','authority':'Latest explicit user decisions; preserve superseded history. Numeric data is generated from installed archives, not edited here.','factions':{'UEF':'GAR','Cybran':'CIS','Illuminate':'Frozen'},'structures':'Deferred','units':[{'id':u['id'],'original':u['original'],'replacement':u['replacement'],'faction':u['faction'],'domain':u['domain'],'installed_prototype':u['installed'],'notes':u['notes']} for u in state['units']],'superseded':[{'unit':'uul0201','old':'UT-AT shield/support variant','current':'RTT Shield Transport'},{'unit':'uul0203','old':'A5-RX precision variant; later UT-AT anti-missile','current':'UT-AT tank; old anti-missile slot retained'},{'unit':'uul0105','old':'AA with optional ground gun','current':'UT-AA with AA + tactical missile interception'},{'unit':'uux0113d1','old':'AV-7 Antivehicle Cannon','current':'SPHA-T; AV-7 only a future artillery-structure candidate'}]}
(S/'decisions.json').write_text(json.dumps(decisions,indent=2),encoding='utf-8')
# Preserve active authoring/validation code. No vendor plugins, native Lua,
# extracted blueprints, meshes, textures, models, audio or download archives.
groups={
 'ATTE':(R/'work/atte',['build_package.py','export_native.py','extract_clips.py','install_package.py','inspect_source.py','inspect_motion.py','lua_constants.py']),
 'Juggernaut':(R/'work/juggernaut',['build_package.py','fit_native.py','import_model.py','atlas.py','check_poses.py','check_texture_uv.py','build_balance_package.py','build_name_package.py','install_balance_package.py','install_package.py']),
 'UTAA':(R/'work/archanist',['build_four_port_package.py','fit_native.py','import_verified.py','validate_native_motion.py','validate_four_port.py','atlas.py','four-port-source-inspect.py','finish_four_port_delivery.py']),
 'RTT':(R/'work/rtt',None),
 'UTAT':(Path(r'C:/Users/gavad/Documents/Codex/2026-10-24/sc2-ut-at/work'),['build_package.py','build_rockhead_foundation.py','build_utat_tank.py','build_utaa_dual.py','check_role_packages.py','install_role_pair.py','increase_attack_speed.py']),
 'SPHA':(Path(r'C:/Users/gavad/Documents/Codex/2026-10-25/spha-t-jackhammer-handoff-user-chose/work/spha'),['build_package.py','export_native.py','install_package.py','validate_native.py','inspect.py','fix_names.py']),
 'UI-and-balance':(R/'work/names',['build_names.py','fix_research_range.py','build_movement_speed.py']),
 'SPHA-source-import':(R/'work/spha',['old_ala.py','inspect_animated.py','fix_preview.py','verify_walk.py']),
}
code=L/'implementation-source';code.mkdir(exist_ok=True);records=[]
for group,(folder,names) in groups.items():
    candidates=[folder/n for n in names] if names is not None else list(folder.glob('*.py'))
    # UT-AT's latest role builders live in work root or subfolders depending revision.
    if group=='UTAT':candidates=list({p for p in folder.rglob('*.py') if p.name in set(names) and not any(s in p.parts for s in ['revisions','tools','native'])})
    for src in candidates:
        if not src.exists():continue
        dest=code/group/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
        records.append({'group':group,'file':dest.relative_to(L).as_posix(),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'local_source':str(src),'scope':'Authored conversion/inspection script snapshot; local inputs and external pipeline dependencies may still be required.'})
for filename in ['bp_literals.py','sca101.py','scm_v7.py']:
    src=R/'work/archanist/pipeline'/filename
    if src.exists():
        dest=code/'shared-pipeline'/filename;dest.parent.mkdir(exist_ok=True);shutil.copy2(src,dest);records.append({'group':'shared-pipeline','file':dest.relative_to(L).as_posix(),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'local_source':str(src)})
# Capture newer UT-AT build/validation scripts explicitly if names differ.
utroot=Path(r'C:/Users/gavad/Documents/Codex/2026-10-24/sc2-ut-at/work')
for src in utroot.glob('*.py'):
    if any(s in src.name for s in ['tank','dual','attack_speed','role_pair','role_packages']):
        dest=code/'UTAT'/src.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(src,dest)
        if not any(d['file']==dest.relative_to(L).as_posix() for d in records):records.append({'group':'UTAT','file':dest.relative_to(L).as_posix(),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'local_source':str(src)})
(code/'source-manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(code/'README.md').write_text('''# Authored implementation source snapshot

Captured 2026-10-25 from current unit workspaces. These are project-authored builders, exporters, inspectors and validators, not a portable ready-to-run build or a distribution of the game. Paths currently reflect the original desktop environment. Consult source-manifest.json for hashes and original locations, and project-registry/project-state.json for the installed package hashes.

Native game blueprints, extracted rigs, original animations, source models/textures, external Blender plugins, downloaded mods, installed SCD packages, caches and Steam game files are intentionally excluded. Some scripts require those local/private inputs or other pipeline files; resolve and parameterize dependencies before claiming a clean-machine build. Do not automatically run installation scripts on another computer.

The active installed archive is the authority for this dated numeric snapshot; the source collection includes investigation helpers and is not evidence that every script represents the winning installed revision. Full reproducible packaging remains a separate task.
''',encoding='utf-8')
(S/'README.md').write_text('''# Current project registry

As of 2026-10-25. Start with CHAT-MODE-FULL-PROMPT.md for context and project-state.json for the numeric/provenance snapshot. This replaces stale assumptions that only TX-130 and AT-RT exist.

- decisions.json: chosen identities, roles and superseded decisions; update through explicit human decisions.
- project-state.json: generated installed-file reconstruction, vanilla/DLC comparison, all weapons and package hashes. Do not hand-edit numeric fields.
- CSV views: roster, scalar balance metrics, weapon profiles, gameplay differences, installed checksums.
- SC2-Conversion-and-Balance.xlsx: human balance review with formulas, if present.
- Obsidian/: plain Markdown vault, one stable-ID note per unit, plus index/status/issues/workflow. Open this folder as a vault. No sync plugin or automatic git sync is configured.
- ../implementation-source/: current authored conversion code snapshot with dependency limitations.

One authority per kind of fact: user decisions define intended design; installed file snapshots define observed configuration; dated tests define runtime acceptance. Generated views must not independently redefine these facts.

Known flags: AT-AP/AT-RT labels reversed by unified naming overlay; Juggernaut speed increments stack to +32.25% over vanilla; UT-AA research cleanup; SPHA beam/runtime testing; A5-RX rework. No game fields were changed by this documentation task.

Refresh by capturing a new dated snapshot, regenerating the prompt/workbook/notes, reviewing differences, committing only selected public-safe files, pushing and verifying the remote SHA. The extractor currently needs the recorded desktop inputs and existing tools/poc_unit.py; parameterizing these paths is a known portability task.
''',encoding='utf-8')
# Save extractor/build sources beside registry so the snapshot can be audited.
tools=L/'tools/project-sync';tools.mkdir(exist_ok=True)
for name in ['extract.py','build_handoff.py','build_workbook.mjs','stage_registry.py']:shutil.copy2(R/'work/project-sync'/name,tools/name)
(S/'sync-scope.json').write_text(json.dumps({'authored_script_files':len(records),'unit_notes':46,'numeric_snapshot':'Static configuration reconstruction, not engine measurement','excluded':'Native game/model binaries, source archives, unverified-rights assets and vendor plugin source','preexisting_worktree_changes':'Left intact; not swept into this commit'},indent=2),encoding='utf-8')
print('Prepared registry, vault and',len(records),'authored script files')
