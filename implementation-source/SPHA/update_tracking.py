from pathlib import Path
import json,copy,hashlib
W=Path(__file__).resolve().parent;R=W.parents[1];O=R/'outputs/SPHA-T'
hub=Path(r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2')
live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
report=json.loads((O/'Package-validation.json').read_text(encoding='utf8'));assert report['installed']
evidence=str(live/'planning/spha-beam-test-1-installation.json')
backup=W/'tracking-backup';backup.mkdir(exist_ok=True)
def update(path,fn):
 before=path.read_bytes();text=before.decode('utf-8-sig');after=fn(text)
 if after==text:return
 saved=backup/(path.parent.name+'-'+path.name)
 if not saved.exists():saved.write_bytes(before)
 assert path.read_bytes()==before,'Concurrent tracking edit: '+str(path)
 path.write_text(after,encoding='utf8')
def roster(text):
 data=json.loads(text);old=copy.deepcopy(data)
 unit=next(u for u in data['units'] if u['unit_id']=='uux0113d1')
 if unit.get('current_identity')!='SPHA-T':unit.setdefault('superseded_identity_history',[]).append({'identity':unit.get('current_identity'),'decision_source':unit.get('decision_source'),'superseded_on':'2026-10-25','reason':'User selects SPHA-T for Jackhammer; AV-7 only a possible future structure; buildings deferred.'})
 unit.update({'current_identity':'SPHA-T','replacement_name':'SPHA-T','creative_approval':'selected_design','decision_status':'selected_design','decision_source':'Explicit user handoff and first-test authorization, October 25, 2026','evidence':evidence,'mechanics':'User-authorized direct beam and range95 first test; native Deploy button retained','model_status':'Nomada_Firefox animated model converted; source deformation checked','model_feasibility':'62-bone SCM export passes offline checks','animation_status':'Twelve-leg walk and deploy/pack SCA converted; engine playback unverified','integration_status':'beam-test-1 installed in isolated development copy','implementation_status':'First test package installed; runtime unverified','asset_license_status':'Source/credits recorded; standalone reuse license unestablished','runtime_acceptance':'not_tested','gameplay_parity_status':'Intentional beam/range exceptions; total nominal beam budget 3750; native simulation fields checked; runtime pending','last_tested_build':None,'test_package_sha256':report['sha256'],'special_constraints':['Keep existing Deploy/Pack button and planted-only firing','Maximum range95 for test','Two-second beam has3750 total nominal damage budget','AV-7 mapping superseded; structures deferred','Do not change other unit packages'],'source_references':[str(Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/outputs/SPHA-T/Selection-and-provenance.json')),evidence]})
 assert [u for u in old['units'] if u['unit_id']!='uux0113d1']==[u for u in data['units'] if u['unit_id']!='uux0113d1']
 data['updated_on']='2026-10-25'
 return json.dumps(data,indent=2,ensure_ascii=False)+'\n'
update(hub/'planning/roster.json',roster)
def manifest(text):
 data=json.loads(text);data['spha_test']={'unit_id':'uux0113d1','identity':'SPHA-T','supersedes':'AV-7 for Jackhammer only; buildings still deferred','revision':'beam-test-1','stage':'Installed for first user test; offline checks passed; runtime unverified','package_sha256':report['sha256'],'evidence':evidence,'native_deploy_button':True,'range':95,'beam_duration':2,'nominal_damage_per_full_beam':3750,'nominal_cycle_seconds':5,'minimum_range_retained':30,'next':'Launch isolated game, build fresh SPHA-T, verify walk/deploy/direct beam/pack and damage installments'}
 return json.dumps(data,indent=2,ensure_ascii=False)+'\n'
update(hub/'planning/project-manifest.json',manifest)
def rosterdoc(text):
 lines=text.splitlines()
 for i,line in enumerate(lines):
  if line.startswith('- Jackhammer (DLC experimental)'):
   lines[i]='- Jackhammer (DLC experimental) → **SPHA-T**. User supersedes AV-7 on October 25. Beam-test-1 installed: native Deploy/Pack button, twelve-leg source motion, direct two-second beam with 3,750 total nominal damage budget and range95. Offline checks pass; in-game acceptance pending. AV-7 is only a possible future structure; buildings remain deferred.'
 return '\n'.join(lines)+'\n'
update(hub/'docs/ROSTER.md',rosterdoc)
heading='## October 25, 2026 — SPHA-T beam-test-1'
body=f'''\n\n{heading}

User selects SPHA-T for Jackhammer/UUX0113D1, superseding AV-7. User authorizes the first in-game test with direct laser fire, maximum range95, existing Load/Unload (native Deploy/Pack) button, and one artillery round's total damage spread over the beam. Buildings remain deferred. No other unit change is authorized by this work.

Installed beam-test-1 SHA256: {report['sha256']}. Evidence: {evidence}. Package and test instructions: {O}.

Native Deploy ability resources are untouched: immobilization, attack command switching, animation wait, packing, and JackhammerUnpacked defense buff remain. Replaced Display.AnimationOpen/Close with source-motion SCA. Unit-local stop-event guard preserves the planted animator, and packing terminates any active beam.

DefaultBeamWeapon/ZapperCollisionBeam02 supplies direct native collision beam behavior. Two-second duration,0.2-second collision interval,375 per installment, and3750 per-discharge nominal cap. Original damage3750 shell becomes a3750 full-beam budget. Range90 becomes95. Nominal five-second cycle, minimum range30, splash radius7, target layers/priorities, health/economy/movement/collision/transport/ability fields remain. Fixed test damage budget, actual collision callbacks and research/critical interactions require runtime validation; no full gameplay parity claim.

Nomada_Firefox source converted to62 bones and3276 source triangles (6552 including both windings), within the72-matrix shader limit. All twelve visible feet deform; source-to-export mesh error below0.00001 model units. Walk closure, deploy-to-pack continuity, packaged SCM/SCA hierarchy and gun-axis checks pass. Deployed bore is level; turret retains native aiming envelope. Visual length is provisionally12 game units with native simulation footprint. LODs share first-test geometry; scale/clearance, provisional blue UEF effects/sound, research naming, and native playback need user review. No standalone source firing/death clips claimed.

Installed only the SPHA archive in isolated development game. All37 other SCD archive hashes match before/after; file rollback tested. Vanilla, AT-TE, UT-AT and other unit packages untouched. Full restart and fresh build required. Test walk, unpack, fire at open-ground targets between30 and95, health change across full beam, pack during firing, and redeploy. Log markers contain SPHA-T beam-test-1. Runtime acceptance remains untested. Rollback: close game and remove only zzzzzz_SC2_CloneWars_SPHA.scd.
'''
for p in [hub/'docs/DECISIONS.md',hub/'docs/TECHNICAL-DISCOVERY.md',live/'docs/test-results.md']:
 update(p,lambda text:text if heading in text else text+body)
risk='\n\n'+heading+' risks\n\nRuntime playback, deployment/packing during target loss, direct collision aiming, full-beam tick count and interruption damage remain unverified. The nominal full-beam budget is3750, not3750 per tick. Source rights are unestablished for public release. Visual footprint12-unit length is larger than preserved simulation footprint; clearance requires test. LOD optimization, legacy research text and final beam presentation remain provisional. No other package was changed. Evidence: '+evidence+'\n'
update(hub/'docs/RISKS.md',lambda text:text if heading in text else text+risk)
(live/'planning/spha-beam-test-1-decision.md').write_text(body,encoding='utf8')
print('Updated only SPHA roster entry, added manifest test record, preserved historical AV-7 decision, and recorded installation/risks/testing.')
