from pathlib import Path
import json,csv,math
OUT=Path(__file__).resolve().parents[1]/'outputs'
audit=json.loads((OUT/'installed-unit-measurements.json').read_text())
rows=audit['rows'];byid={r['id']:r for r in rows}
sources={
 'ISP':('ISP / Legends dimensions','https://starwars.fandom.com/wiki/Infantry_Support_Platform/Legends','Secondary; references licensed RPG material'),
 'TX':('TX-130 / Legends dimensions','https://starwars.fandom.com/wiki/TX-130_Saber-class_fighter_tank/Legends','Secondary; attributes length to Wizards Republic Fighter Tank entry'),
 'AP':('AT-AP historical reference dimensions','https://www.swx.it/databank/index.php?mobileaction=toggle_view_mobile&title=All_Terrain_Attack_Pod','Secondary historical/Legends-style reference; provisional'),
 'RT':('Official AT-RT Databank','https://www.starwars.com/databank/at-rt-walker','Primary official; height 3.45 m'),
 'RX':('A5-RX vehicle description','https://starwars.fandom.com/wiki/A5-RX_battle_tank','Secondary; dimensions not supplied in retrieved entry'),
 'AA':('UT-AA model author and mod release notes','https://www.moddb.com/mods/star-wars-thrawns-revenge-iii/images/bringing-down-the-skies-pt1-ut-aa-render','Primary model author; no metre dimensions supplied'),
 'RTT':('Republic Troop Transport in D6 conversion','https://www.rancorpit.com/forums/downloads/Rancor%20Pit%20WotC%20Saga%20Stat%20Conversions/The%20Clone%20Wars%20-%20D6%20Conversion.pdf','Fan conversion of licensed RPG material; 18 m provisional, primary dimension not independently checked'),
 'UTAT':('UT-AT reference dimensions','https://swrpggm.com/unstable-terrain-artillery-transport-ut-at/','Secondary fan RPG compilation; 23.8 m provisional'),
 'JUG':('HAVw A6 Juggernaut dimensions','https://starwars.fandom.com/wiki/HAVw_A6_Juggernaut?file=Rescue_on_Felucia.jpg','Secondary canon entry; length 49.4 m, width 19.6 m, overall height 30.4 m'),
 'TE':('Official AT-TE Databank','https://www.starwars.com/databank/at-te-walker','Primary official; length 22.02 m, height 9.57 m'),
 'SPHA':('Official SPHA-T Databank','https://www.starwars.com/databank/self-propelled-heavy-artillery-turbolaser-spha-t','Primary official; length 140.2 m'),
}
# Length / width / height in metres, None means unverified or unavailable.
lore={
 'uul0002':([5,None,None],'ISP','Base ISP reference; engineering variant is custom. Arm and tools have no official dimensions.'),
 'uul0003d1':([5,None,None],'ISP','Same base ISP reference; custom beacon and engineering arm. Do not assign the beacon a lore height.'),
 'uul0101':([8.2,None,None],'TX','Legends length. Common 3.05 m width and 2.3 m height are omitted: reliable attribution was not established; width has a documented sourcing dispute.'),
 'uul0102':([None,None,10.97],'AP','Provisional historical height. Resize by height; length and width are inferred from this mesh, not verified lore.'),
 'uul0103':([None,None,3.45],'RT','Official height. Vehicle-only model: verify reference measurement endpoints (rider/antenna) and idle stance before applying.'),
 'uul0104':([None,None,None],'RX','No published metre dimensions located. Smaller-than-A5 description is insufficient to calculate a precise size. Do not borrow A5/A6 dimensions.'),
 'uul0105':([None,None,None],'AA','Author identifies Republic Galactic Battlegrounds anti-air vehicle/concept art. No published metre dimensions located; do not assume UT-AT dimensions from the name.'),
 'uul0201':([18,None,None],'RTT','Provisional RPG transport length; confirm the exact RTT design and primary RPG entry. Shield equipment is a custom adaptation.'),
 'uul0203':([23.8,None,None],'UTAT','Provisional reference length, corroborated in several secondary sources. Gun-inclusive versus hull-only endpoints not established.'),
 'uux0101':([49.4,19.6,30.4],'JUG','Full-size A6 reference. Retain tower. Smaller animated-series version and body-only heights must not be mixed with this target.'),
 'uux0111':([22.02,None,9.57],'TE','Current official Databank reference. Older 13.2 m and fan hull estimates are not interchangeable with this overall reference.'),
 'uux0113d1':([140.2,None,None],'SPHA','Official overall length. Any smaller gameplay target must be explicitly called a readability compromise.'),
}
anchor=byid['uul0101'];metres_per_unit=8.2/anchor['displayed_lwh'][0]
comparison=[]
for r in rows:
 if r['id'] not in lore:continue
 dims,key,note=lore[r['id']];idx=next((i for i,v in enumerate(dims) if v is not None),None)
 old=r['displayed_lwh'];factor=None if idx is None else dims[idx]/(metres_per_unit*old[idx])
 comparison.append({**r,'lore_lwh_m':dims,'source_key':key,'note':note,'reference_axis':None if idx is None else ['length','width','height'][idx], 'current_equivalent_lwh_m':[x*metres_per_unit for x in old], 'target_multiplier':factor, 'candidate_uniform_scale':None if factor is None else factor*r['uniform_scale'], 'target_displayed_lwh':None if factor is None else [x*factor for x in old]})
result={'as_of':'2026-10-26','status':'Read-only first comparison; source-reconstructed DLC bind pose, not runtime-verified dimensions','metres_per_game_unit':metres_per_unit,'calibration':'Provisional: keep current DLC TX-130 length and assign its Legends length of 8.2 metres. This is a mod convention, not a physical SC2 conversion.','sources':sources,'units':comparison,'planned_units':[r for r in rows if r['id'] not in lore]}
(OUT/'GAR-size-comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
fields=['id','replacement','current_length_game_units','current_width_game_units','current_height_game_units','current_length_equivalent_m','current_width_equivalent_m','current_height_equivalent_m','lore_length_m','lore_width_m','lore_height_m','reference_axis','candidate_multiplier','candidate_uniform_scale','source_url','notes']
with (OUT/'GAR-size-comparison.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in comparison:
  w.writerow(dict(zip(fields,[r['id'],r['replacement'],*r['displayed_lwh'],*r['current_equivalent_lwh_m'],*r['lore_lwh_m'],r['reference_axis'],r['target_multiplier'],r['candidate_uniform_scale'],sources[r['source_key']][1],r['note']])))
def trip(v):return ' × '.join('—' if x is None else f'{x:.2f}' for x in v)
lines=['# GAR unit sizing — first measured comparison','',
 '26 October 2026. ACU excluded. No game files changed.','',
 'This lists the 12 installed GAR ground replacements found in the development game. Dimensions are reconstructed from installed LOD0 geometry and source blueprint scales with DLC enabled; they are static bind-pose measurements, not measurements captured from a running match. All dimensions are **length × width × height**.','',
 '## Current visible sizes versus lore references','',
 'Game units (GU) are the engine coordinate scale. The metre equivalents below use a **provisional shared calibration** that keeps the TX-130 at its current length and treats that length as 8.2 m. These metre equivalents are calculated comparisons, not a claim about SC2’s real-world scale. A dash means no verified reference dimension was established.','',
 '| GAR replacement | Original UEF unit | Current L × W × H (GU) | Current equivalent L × W × H (m) | Lore reference L × W × H (m) | Evidence |',
 '|---|---|---:|---:|---:|---|']
for r in comparison:
 key=r['source_key'];label,url,status=sources[key]
 evidence='Official' if key in ['RT','TE','SPHA'] else 'Unknown size' if key in ['RX','AA'] else 'Base vehicle / custom variant' if key=='ISP' else 'Provisional secondary / RPG' if key in ['AP','RTT','UTAT'] else 'Secondary / canon' if key=='JUG' else 'Legends / secondary'
 lines.append(f"| {r['replacement']} | {r['original']} ({r['id'].upper()}) | {trip(r['displayed_lwh'])} | {trip(r['current_equivalent_lwh_m'])} | {trip(r['lore_lwh_m'])} | [{evidence}]({url}) |")
lines+=['','## Conversion math','',f"Current TX-130 length = {anchor['displayed_lwh'][0]:.8f} GU. Reference length = 8.2 m. Therefore **k = {metres_per_unit:.8f} metres per GU**.",'',
 'For a comparable dimension:',
 '- Current equivalent metres = current GU × k.',
 '- Desired GU = reference metres ÷ k.',
 '- Uniform resize multiplier = desired GU ÷ current GU.',
 '- Candidate display scale = existing UniformScale × resize multiplier.','',
 'Use the same k for every unit. A separate conversion per unit would conceal the mismatched proportions. An overall army-scale adjustment can later multiply every target GU dimension by the same value while preserving relative sizes.','',
 '## Conditional resize calculations — not applied','',
 'These are mathematical candidates under the TX-130 anchor, not approved final sizes. Length is the anchor where available; AT-AP and AT-RT use height. Only the chosen axis is matched. Other target dimensions follow the existing model proportions and must not be presented as independently verified lore dimensions.','',
 '| Unit | Matched reference | Target dimension (GU) | Multiply current size by | Candidate UniformScale |',
 '|---|---|---:|---:|---:|']
for r in comparison:
 factor=r['target_multiplier']
 if factor is None:lines.append(f"| {r['replacement']} | No defensible numeric target yet | — | — | — |")
 else:
  i=['length','width','height'].index(r['reference_axis']);d=r['lore_lwh_m'][i]
  lines.append(f"| {r['replacement']} | {r['reference_axis']} {d:g} m | {d/metres_per_unit:.3f} | {factor:.3f}× | {r['candidate_uniform_scale']:.6f} |")
lines+=['','## What the comparison shows','',
 '- **AT-TE versus SPHA-T is the largest mismatch.** Current length ratio is about 1.04:1, while their official reference ratio is about 6.37:1. This ratio mismatch exists regardless of the overall metres-per-GU convention.',
 '- **The two engineers use the same base hull geometry but different display scales.** The Field Engineer is currently 33.3% larger in length and width. A shared base ISP reference would give them the same hull size; the beacon would still make the Field Engineer taller.',
 '- **Uniform scale cannot guarantee every lore dimension.** With AT-TE length matched to 22.02 m, this mesh would stand about 10.02 m high versus the official 9.57 m, roughly 4.7% taller. Stance, turret pose and measurement endpoints need checking before changing proportions.',
 '- **Juggernaut proportions also need inspection.** At 49.4 m long, its mesh implies about 24.51 m width and 31.53 m height, compared with secondary reference values of 19.6 m and 30.4 m. Width can include custom side weapons, so this is an envelope discrepancy to inspect, not proof the hull must be narrowed.',
 '- **A5-RX and UT-AA need an estimated design target.** No usable metre dimensions were located. For a future estimate, use a known-height crew figure or a vehicle shown in the same shot, record perspective/variant uncertainty, and label the result as an estimate.',
 '- **Strict SPHA-T scale will be visually demanding.** Under this calibration it would be about 39.0 GU long, compared with 6.13 GU for the AT-TE. A compact gameplay version may be preferable, but that decision should be separate from the lore baseline.','',
 '## Per-unit reference notes','']
for r in comparison:
 title,url,status=sources[r['source_key']]
 lines.append(f"- **{r['replacement']}:** {r['note']} [{title}]({url}). Source quality: {status}.")
lines+=['','## Measurement limits and verification','',
 '- The reconstruction uses the existing project’s literal Lua parser and merge approach: native base/DLC sources, virtual-path deduplication, then base, DLC base and DLC shadow patch phases. All selected unit patches parsed without errors. The game log confirms the development archives are mounted, but it does not prove each effective blueprint value at runtime.',
 '- X is width, Y is vertical and Z is longitudinal in these exports. Exporter inspection shows vertices written in model-space rest coordinates, so bind-pose dimensions use the indexed geometry directly; applying each inverse-bind transform again would be incorrect.',
 '- The bounds include visible weapons, antennae, arms and the tower where present. Part-only hull bounds have not been separated. Idle, walking, aiming and deployed animations can alter the envelope; this first pass does not compute their maxima.',
 '- Custom package scripts were scanned for SetScale, SetMesh and SetBoneScale calls; none were found. This scan does not prove that every inherited engine behavior is scale-free.',
 '- Displayed dimensions multiply mesh bounds by UniformScale once. This is the source-model convention; a running-game debug measurement is still needed before installing changes.',
 '- These numbers assume the inspected DLC shadow configuration. Several native non-DLC scales differ, including TX-130 0.09 versus DLC 0.0675. The raw snapshot retains base and DLC scale values so this assumption can be revisited.',
 '- Collision SizeX/Y/Z and movement footprint are retained separately in installed-unit-measurements.json. Neither defines visible size. Enlarging a model alone does not enlarge pathfinding clearance or selection/hit volumes; those require a later, separately reviewed pass.',
 '- Avoid using map size or weapon range alone to infer physical metres: those gameplay conventions have not been calibrated to the GAR models.',
 '- Printed precision is for reproducible arithmetic, not a claim of centimetre-level lore or runtime accuracy.','',
 '## Air and naval entries still marked planned','',
 'The inspected installation contains no GAR mesh override for the following registry entries. Their current visuals remain native UEF in the inspected packages; no GAR mesh size is claimed here. They are listed separately so “all UEF replacements” does not silently omit the broader roster.','']
for r in result['planned_units']:lines.append(f"- {r['id'].upper()} — {r['original']} → {r['replacement']}.")
lines+=['','## Next checkpoint','',
 'The initial listing and conditional conversion math are complete for installed ground replacements, with unknowns explicitly recorded. Before changing sizes: confirm runtime effective scales and idle/deployed geometry, choose the army-wide calibration, estimate A5-RX/UT-AA, and decide whether SPHA-T gets a deliberate readability exception. No changes have been applied.','']
(OUT/'GAR-UNIT-SIZING.md').write_text('\n'.join(lines),encoding='utf-8')
print('Saved report, CSV, and comparison JSON. k =',metres_per_unit)
for r in comparison:print(r['id'],r['target_multiplier'])
