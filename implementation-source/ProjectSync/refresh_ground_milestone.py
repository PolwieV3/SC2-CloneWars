from pathlib import Path
import json,csv,shutil,hashlib,zipfile,ast
W=Path(__file__).resolve().parents[1]
P=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
R=P/'project-registry';S=W/'work/github-sync';state=json.loads((S/'project-state.json').read_text(encoding='utf-8'))
state['as_of']='2026-10-26'
notes={
 'uul0002':'ISP Engineer working in game; custom engineering arm. Clone crew deferred.',
 'uul0003d1':'ISP Field Engineer installed with illuminated pylon; same base hull size as Engineer. Earlier rear texture/pylon follow-up remains separate from general sizing acceptance.',
 'uul0102':'AT-AP native ID confirmed. R3 scale matches reference AT-AP/AT-TE height ratio; rest-pose and gun-inclusive endpoints limit exact lore claims.',
 'uul0103':'AT-RT native ID confirmed; compact scout enlarged for readability in R2.',
 'uul0104':'User reports A5-RX working in game October26; current sizing accepted. Earlier rework status superseded by working ground milestone.',
 'uul0105':'Anti-air plus tactical missile interception. Former optional ground-gun research cleanup remains pending.',
 'uul0201':'RTT shield transport; custom shield adaptation. Vehicle team-paint rollout deferred.',
 'uul0203':'Ground tank in old Sharp Shooter slot; three guns,75/30/30 damage,RateOfFire .725 each. No longer the anti-missile role.',
 'uux0101':'User accepted ground sizing; tower retained. Two15% speed changes still yield +32.25% vs vanilla. R1 visual size +60% retained.',
 'uux0111':'AT-TE heavy assault conversion; R3 adds5% to R2 size. User accepts current ground appearance. Reported terrain-obstruction firing issue remains deferred.',
 'uux0113d1':'SPHA-T working ground attack and appearance user accepted. Test8 beam/deploy behavior retained; terrain-obstruction targeting unresolved. R1 doubled visual size. Team-paint prototype removed after blue/yellow worked but purple appeared black; ownership indicators deferred. Research source cost13 requested, runtime spending not verified. DLC research NAME/INFO rename verified separately.',
}
acceptance='Working GAR ground conversion; user accepted current lineup/sizing on 2026-10-26. Final balance and individual edge-case tests remain open.'
for u in state['units']:
 if u['installed']:
  u['status']=acceptance
  u['notes']=notes.get(u['id'],'Current tank sizing accepted; further balance and effects checks remain.')
for m in state['metrics']:
 u=next(u for u in state['units'] if u['id']==m['id']);m['status']=u['status'];m['replacement']=u['replacement']
state['acceptance']={'date':'2026-10-26','ground_milestone':'User confirms working UEF/GAR ground units and approves current appearance after sizingR3.','installed_ground_replacements':12,'acu':'Deferred','team_paint':'SPHA prototype removed at user request; defer further vehicle paint/ownership work','research_cost':'SPHA DLC source requests13 research points (10+3); in-game cost/spending not confirmed','research_names':'SPHA-T and ISP Field Engineer DLC titles/descriptions verified in game by user, per docs/DLC-RESEARCH-RENAMING.md','limits':'Working milestone does not establish full balance, pathfinding, multiplayer, every animation or research upgrade acceptance.'}
assert len(state['units'])==46 and sum(u['installed'] for u in state['units'])==12 and not state['parse_errors']
(R/'project-state.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
for stem,data in [('roster',[{k:v for k,v in u.items() if k not in ['baseline_source','patches','stats_before','stats_after','weapons_before','weapons_after']} for u in state['units']]),('balance-metrics',state['metrics']),('weapons',state['weapons']),('gameplay-differences',state['gameplay_field_differences']),('installed-packages',state['installed_packages'])]:
 with (R/(stem+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
  writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
d=json.loads((R/'decisions.json').read_text(encoding='utf-8'));d['as_of']='2026-10-26'
for u in d['units']:
 current=next(x for x in state['units'] if x['id']==u['id']);u.update(replacement=current['replacement'],installed_prototype=current['installed'],notes=current['notes'])
d['ground_milestone']=state['acceptance'];d['sizing_authority']='User-approved SizingR3; per-axis mesh bounds and exact scales in ground-sizing/current-measurements.json.'
(R/'decisions.json').write_text(json.dumps(d,indent=2),encoding='utf-8')
# Preserve the accepted sizing history as authored patches and numeric manifests.
dest=P/'implementation-source/UnitSizing';dest.mkdir(exist_ok=True)
for name in ['measure_units.py','install_sizing_r1.py','install_sizing_r2.py','install_sizing_r3.py','build_sizing_report.py']:
 shutil.copy2(W/'work'/name,dest/name)
for rev in ['R1','R2','R3']:
 m=json.loads((W/f'outputs/Sizing-{rev}/installation-manifest.json').read_text(encoding='utf-8'))
 zpath=Path(m['installed_path'])
 with zipfile.ZipFile(zpath) as z:
  for n in z.namelist():
   assert n.endswith('_unit.bp')
   target=dest/'patches'/rev/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
 g=R/'ground-sizing';g.mkdir(exist_ok=True)
 (g/f'{rev}-installation.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
shutil.copy2(W/'outputs/installed-unit-measurements.json',R/'ground-sizing/current-measurements.json')
shutil.copy2(W/'outputs/Sizing-R3/SIZING-R3.md',R/'ground-sizing/SIZING-R3.md')
shutil.copy2(W/'outputs/SPHA-TeamColor-Removed/reversion-manifest.json',R/'ground-sizing/team-paint-decision.json')
# Refresh previously captured authored scripts at their recorded source locations.
manifest_path=P/'implementation-source/source-manifest.json';records=json.loads(manifest_path.read_text())
for entry in records:
 src=Path(entry['local_source']);target=P/entry['file']
 if src.exists() and src.resolve()!=target.resolve():shutil.copy2(src,target)
groups={
 'ISPEngineers':Path(r'C:/Users/gavad/Documents/Codex/2026-10-26/files-pasted-by-the-user-gar/work'),
 'SPHA':Path(r'C:/Users/gavad/Documents/Codex/2026-10-25/spha-t-jackhammer-handoff-user-chose/work/spha'),
}
skip={'extract_latest_video.py','extract_targeting_video.py','extract_video_frames.py','dlc_research_ui_probe.py'}
for group,folder in groups.items():
 for src in folder.glob('*.py'):
  if src.name in skip:continue
  target=P/'implementation-source'/group/src.name;target.parent.mkdir(exist_ok=True);shutil.copy2(src,target)
  key=target.relative_to(P).as_posix();record={'group':group,'file':key,'local_source':str(src),'scope':'Authored conversion/inspection code; local/private inputs required; not a clean-machine build.'}
  existing=next((x for x in records if x['file']==key),None)
  if existing:existing.update(record)
  else:records.append(record)
for src in dest.glob('*.py'):
 key=src.relative_to(P).as_posix()
 if not any(r['file']==key for r in records):records.append({'group':'UnitSizing','file':key,'local_source':str(W/'work'/src.name),'scope':'Accepted visual-sizing overlay build and validation; requires local model archives.'})
for entry in records:entry['sha256']=hashlib.sha256((P/entry['file']).read_bytes()).hexdigest()
manifest_path.write_text(json.dumps(records,indent=2),encoding='utf-8')
(P/'implementation-source/README.md').write_text('''# Authored implementation source snapshot — October26,2026

Current UEF/GAR ground conversion authoring and sizing scripts, including both ISP engineers and the current SPHA work. Source hashes and local provenance are recorded in source-manifest.json. Current installed package hashes are in project-registry/project-state.json.

This is a working local-game milestone, not a portable clean-machine release. Scripts retain desktop paths and need local/private native rigs, meshes, animations, source textures and other pipeline inputs. Review paths before running installation helpers. UnitSizing/patches contains the exact authored R1/R2/R3 merge overlays; apply in that order against the corresponding baseline, never by repeatedly multiplying an already resized installation.

Native game files, packaged SCD archives, downloaded mods, imported models/textures, external Blender plugins and assets with unresolved redistribution rights remain local. The rejected SPHA team-paint prototype is not part of the active source snapshot.
''',encoding='utf-8')
# Keep all46 per-unit notes generated from the same snapshot.
for u in state['units']:
 st=u['stats_after'];lines=['---',f"unit_id: {u['id']}",f"faction: {u['faction']}",f"domain: {u['domain']}",f"original: {json.dumps(u['original'])}",f"replacement: {json.dumps(u['replacement'])}",f"installed: {str(u['installed']).lower()}",'snapshot: 2026-10-26','---',f"# {u['replacement']}",'',f"{u['original']} / {u['id'].upper()}",'',u['status'],'',u['notes'],'',f"Current source snapshot: health {st['health']}, speed {st['speed']}, display scale {st['visual_scale']}. See project-state.json for full weapon and balance profiles; these are source-reconstructed values.",'','## Provenance','',u['baseline_source']['archive']+'!'+u['baseline_source']['entry']]
 lines+=['- '+p['archive']+'!'+p['entry'] for p in u['patches']]
 (R/'Obsidian/Units'/f"{u['id']}.md").write_text('\n'.join(lines)+'\n',encoding='utf-8')
summary='''# Working UEF/GAR ground milestone — October26,2026

Twelve UEF ground replacements are working locally; the user approved the current lineup and sizing after R3. ACU is deferred. GAR air/naval and CIS remain design plans; buildings are deferred and Illuminate is frozen.

Accepted sizing includes SPHA-T doubled and Juggernaut +60% from the pre-sizing baseline, followed by readability adjustments, AT-TE R3 +5%, TX-130 R3 +15%, and an AT-AP relative-height correction. See ground-sizing/current-measurements.json and R1/R2/R3 manifests for exact final scales; percentages are sequential, not additive.

The SPHA team-color trial worked in blue/yellow but appeared black in purple. The user rejected vehicle team paint for immersion. The prototype was removed; the original tan SPHA appearance is active. Ownership indicators are deferred. Other vehicles’ existing material behavior has not been removed.

SPHA research source requests13 points (10+3); engine UI/spending remains unverified. A separate later research NAME/INFO fix was verified for SPHA-T and ISP Field Engineer; preserve docs/DLC-RESEARCH-RENAMING.md. The old issue log’s tooltip-name failure is historical; its terrain-obstruction firing issue remains open.

Known limits: reported SPHA/AT-TE terrain-obstruction firing; collision/navigation clearance after visual resizing; final balance/AI/multiplayer and research-upgrade coverage; redundant former UT-AA ground-gun research; engineer-specific rear/pylon detail checks. General visual acceptance does not establish every edge case. Health bars were normalized in R3; no isolated final acceptance claim is made for every view.

Current numeric source is project-state.json, with regenerated CSVs and Obsidian unit notes. The existing SC2-Conversion-and-Balance.xlsx remains the historical October25 workbook; use current CSV/JSON for October26 values until it is regenerated. No game files were changed by this GitHub sync.
'''
(R/'GROUND-MILESTONE-2026-10-26.md').write_text(summary,encoding='utf-8')
(R/'Obsidian/Current status.md').write_text(summary+'\n[[Home]] · [[Known issues]] · [[Workflow]]\n',encoding='utf-8')
(R/'Obsidian/Known issues.md').write_text('# Known issues — October26,2026\n\n'+summary[summary.index('Known limits:'):]+'\n[[Home]]\n',encoding='utf-8')
index=['# SC2-TCW registry','',summary,'','## Ground roster','']
index+=['- [['+u['id']+']] — '+u['replacement'] for u in state['units'] if u['installed']]
(R/'Obsidian/Home.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
handoff=summary+'\n## All mobile design slots\n\n'+'\n'.join('- '+u['id'].upper()+' / '+u['original']+' → '+u['replacement']+' — '+('working ground conversion' if u['installed'] else 'design only') for u in state['units'])+'\n\nPreserve stable IDs, authorized role changes and accepted sizes. Consult the current installed archive snapshot before further edits. Working ground milestone is not a public release or complete reproducible build.\n'
(R/'CHAT-MODE-FULL-PROMPT.md').write_text(handoff,encoding='utf-8')
(R/'README.md').write_text('# Current project registry — October26,2026\n\nStart with [working ground milestone](GROUND-MILESTONE-2026-10-26.md), [handoff](CHAT-MODE-FULL-PROMPT.md) and project-state.json.\n\n12 working GAR ground replacements; user-approved sizingR3; ACU deferred.46 mobile design slots retained. CSV views and Obsidian unit notes regenerated from the installed source snapshot. Numeric configuration is source-reconstructed, not engine-interrogated.\n\nGround-sizing/ holds final geometry bounds, R1/R2/R3 decisions and the rejected team-paint decision. Installed packages and private model/game binaries are excluded. The October25 XLSX is historical; current numeric values are in CSV/JSON.\n\nThe user accepted the lineup in game. Research13-point spending and documented edge cases remain unverified. See GROUND-MILESTONE-2026-10-26.md and docs/DLC-RESEARCH-RENAMING.md.\n',encoding='utf-8')
(R/'sync-scope.json').write_text(json.dumps({'as_of':'2026-10-26','authored_script_files':len(records),'unit_notes':46,'installed_ground_replacements':12,'excluded':'Game/model binaries, imported asset textures, source archives and vendor plugins. Preexisting unrelated editor/worktree changes left intact.','workbook':'Historical October25 XLSX retained; current CSV/JSON regenerated.'},indent=2),encoding='utf-8')
# Main reading entry points replace stale two-unit/ten-prototype descriptions.
(P/'CURRENT-STATE.md').write_text(summary+'\nRead [full handoff](project-registry/CHAT-MODE-FULL-PROMPT.md), [registry](project-registry/README.md), [verified research-name procedure](docs/DLC-RESEARCH-RENAMING.md) and [authoring source](implementation-source/README.md).\n',encoding='utf-8')
(P/'README.md').write_text('''# SC2: The Clone Wars

Working local Supreme Commander2 conversion: UEF becomes the Galactic Republic. **All12 selected UEF/GAR ground replacements are working locally**, with current sizing approved by the user on October26,2026. The ACU is deferred.

Start with [current state](CURRENT-STATE.md), the [ground milestone](project-registry/GROUND-MILESTONE-2026-10-26.md), the [project registry](project-registry/README.md), and [authored implementation source](implementation-source/README.md).

## Ground roster

ISP Engineer, ISP Field Engineer, TX-130 Saber Tank, AT-AP, AT-RT, A5-RX, UT-AA, RTT Shield Transport, UT-AT, HAVw A6 Juggernaut, AT-TE and SPHA-T. Stable UEF IDs and original slots are retained in the registry.

UT-AA supplies anti-air plus tactical missile interception; UT-AT is a tank. AT-TE uses King Kriptor’s slot; SPHA-T uses Jackhammer’s. The working milestone includes custom authorized balance/role changes; it is not a blanket vanilla-stat parity claim.

## Current decisions

- User-approved visual sizing through R3; exact scales, dimensions and sequential changes are recorded under project-registry/ground-sizing/.
- Vehicle team-paint rollout deferred for immersion. The SPHA prototype was removed and its tan hull restored. Ownership indicators can be revisited later.
- SPHA research source cost requests13 points; actual engine UI/spending requires confirmation. Separate SPHA/ISP Field Engineer research-name fixes were verified in game.
- Terrain-obstruction firing, collision/navigation clearance, final balance and broader runtime tests remain open. See CURRENT-STATE.md.
- GAR air/naval and CIS are planned. Structures are deferred; Illuminate is frozen.

## Local testing

Use Launch-Skirmish-Test.cmd for the isolated development copy with F8 V3 Dev Mode, or Launch-Skirmish-Without-Dev.cmd without developer tools. Keep Steam running and verify the executable belongs to local/dev-game. Developer resource/research replenishment can invalidate research-cost spending tests.

The original Steam installation and installed-snapshot are reference inputs. Only local/dev-game receives private conversion packages. This sync does not modify game files.

## Repository scope

This repository contains authored code, merge configuration, source manifests, current balance/roster snapshots and project documentation. It is **not a downloadable game or a clean-machine rebuild**. Original game files, imported models/textures, private mod packages, downloaded archives and assets with unresolved redistribution rights remain local and ignored. Some scripts retain desktop paths and require local/private inputs; review them before running.

Current numeric views are project-registry/project-state.json and its CSVs. The existing October25 balance workbook is historical; it is not the current October26 snapshot. [Source-of-truth workflow](project-registry/Obsidian/Workflow.md) explains how to refresh and verify changes.
''',encoding='utf-8')
print('Refreshed46 unit notes,12 installed ground units,',len(records),'authored scripts.')
print('Visible labels:',[(u['id'],u['visible_name_reconstructed']) for u in state['units'] if u['id'] in ['uul0102','uul0103']])
