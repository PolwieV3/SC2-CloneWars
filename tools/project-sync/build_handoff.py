from pathlib import Path
import json, re, shutil, hashlib, zipfile

R=Path(__file__).resolve().parents[2];O=R/'outputs/Project-Sync-2026-10-25'
L=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
D=json.loads((O/'project-state.json').read_text(encoding='utf-8'));U={u['id']:u for u in D['units']}

def fmt(v):
    if v is None:return 'not specified / not applicable'
    if isinstance(v,float):return f'{v:.8g}'
    return str(v)

def primary(u,mode):return next((w for w in u['weapons_'+mode] if isinstance(w['damage'],(int,float)) and w['damage']>0),{})

def profile(u,mode):
    w=primary(u,mode);s=u['stats_'+mode]
    return f"A={fmt(w.get('damage'))}, R={fmt(w.get('range'))}, S={fmt(s['speed'])}, HP={fmt(s['health'])}, ROF={fmt(w.get('rate'))}; selected weapon={w.get('label','none')}"

intro='''# SC2: The Clone Wars — complete Chat Mode handoff

Use this as a project-state handoff, not as instructions to restart the project. Read it fully before proposing changes. This snapshot was reconciled against local installed files on October 25, 2026. You may have older context that stops at TX-130 and AT-RT: that context is obsolete. We have ten GAR ground replacement prototypes installed, including ground experimentals. We are not at a two-unit prototype stage anymore, but installed does not mean finished, balanced, or fully tested.

## 1. What the project is

We are converting Supreme Commander 2 into a Clone Wars-themed project. UEF becomes the Galactic Republic / Grand Army of the Republic (GAR). Cybran becomes the Confederacy of Independent Systems (CIS / Separatists). The original Steam installation is read-only; changes are installed in an isolated development copy with reversible archives. Illuminate is frozen, with no approved conversion identity. Structures are deferred until the buildings phase unless separately authorized. Campaign-specific conversion is not the active production scope, although some visible text has been updated for consistency.

The original default was visual replacement with preserved gameplay. This remains the default for future work, but it is no longer correct to say every current conversion preserves vanilla gameplay. Explicit user-approved exceptions exist: AT-AP projectile behavior, UT-AT tank-role conversion, UT-AA dual defense, Juggernaut weapons and balance, AT-TE heavy assault redesign, and SPHA-T direct beam test. Do not undo those exceptions or impose the old reskin-only interpretation on them. Equally, do not treat approval of one redesigned unit as permission to rebalance everything.

The user wants believable model placement, actual textures, correctly aligned weapon tips, functional aiming, animation conversion, and clear research/build names. A sloppy static replacement is not the goal. All land-unit proportions and polish will be revisited after the ground roster is completed. Avoid presenting current provisional scale as a final acceptance decision.

## 2. Current progress and installed replacements

Ten distinct GAR ground slots now have installed replacement archives: TX-130, AT-AP, AT-RT, A5-RX, UT-AA, RTT Shield Transport, UT-AT, HAVw A6 Juggernaut, AT-TE, and SPHA-T. This count includes imperfect or deferred test assets. It does not include duplicate name/audio/range/speed archives as extra units. No CIS, GAR air, or GAR naval replacement packages were found in the installed CloneWars archive set. Those roster mappings below are design decisions, not completed conversions.

Use these evidence categories separately: design approved; source model located; provenance/license recorded; rig and animation inspected; native export built; static checks passed; archive installed; in-game loading observed; movement/firing observed; visual acceptance; gameplay acceptance. Never collapse them into a single 'done' label.

### TX-130 Saber Tank — Rock Head / UUL0101

Imported TX-130 model and Republic styling, projectiles and audio are installed. User feedback on an earlier current-stage appearance was positive ('TX-130 is looking good'), with historical earlier revisions also accepted. This is not proof that every subsequent revision or every research state passed gameplay parity. The hull/turret appearance was adapted to native aiming without changing basic movement controls. Final scale, team colors, upgraded visual configurations, LOD behavior and comparative gameplay still need review. Main projectile damage remains 60 and range 20; two main muzzle launches at rate 0.5 yield approximately 60 main-gun DPS when both hit, before mitigation/research. This is not a one-projectile 30-DPS tank.

### AT-AP — Demolisher / UUL0102

Installed artillery-walker conversion. Main gun visuals, alignment, direct-flight behavior and impact timing were iterated. User authorized that projectile behavior exception; it is not a blanket damage/range/rate change. Size/body surfaces and visual polish still need a final review. Native weapon/upgrade profiles remain separately recorded. Important: UUL0102 is AT-AP, not AT-RT.

### AT-RT — Titan / UUL0103

Installed walker conversion, with native movement/weapon integration carried through earlier work. It remains a prototype requiring final scale, animation transitions, firing alignment, research behavior and crowd/LOD checks. Do not describe it as the only completed unit beside TX-130. Important: UUL0103 is AT-RT, not AT-AP.

### A5-RX — Meteor / UUL0104

An A5-RX spread-missile test archive is installed. The user previously said the model needs a rework and deferred it. Presence in the game is not acceptance. Source came from A5-RX_Battle_Tank.7z; original creator/license were not established by inspection. The user said it was free and permitted use, but do not invent a verified third-party redistribution license. Preserve that provenance limitation for public-release planning. Rework visuals, launcher/muzzle mapping and final proportions before calling it finished.

### UT-AA — Archanist / UUL0105

Philloraptor/Fall of the Republic ALO model was imported using an ALAMO Blender plugin. A four-port visible main AA launcher was adapted to native aiming/unpack behavior. The latest authorized role is anti-air plus tactical missile defense. The existing smaller side weapon was repurposed as the missile interceptor, with its own aim chain. The AA weapon and interceptor should work independently. Interceptor damage 2, RateOfFire 3, range 5–32, tactical-missile targeting; enabled from construction for the first trial. The optional ground-gun role was removed. Its former ground-weapon research is now redundant and needs a user-directed tooltip/balance cleanup. Do not describe UT-AA as only AA or assume UT-AT still supplies missile defense. Verify real aircraft/missile interception, unpack/pack, muzzle placement, upgrades and absence of script errors. Public reuse permission for the source is not independently established.

### RTT Shield Transport — P-Shield / UUL0201

The earlier UT-AT shield concept was superseded by a custom Republic Troop Transport shield-generator variant. An RTT shield model archive is installed. The shield role remains; native shield health/regen/recharge, movement, selection, construction/research and team effects need full review. The RTT came from the RM-09 Alliance Shuttle / Republic Troop Transport model release, credited to Pandemic Studios (model/textures) and Sly442 (rig), uploaded by kubli. The site labels it Public Domain, but that label is not independent verification of the underlying game-IP rights. The custom shield variant is our adaptation, not an established GAR mobile shield vehicle from canon.

### UT-AT — Sharp Shooter / UUL0203

Important latest correction: UT-AT occupies the Sharp Shooter slot but is now a surface-combat tank, not mobile anti-missile. The user explicitly authorized that role change. The model source is DooFi's UT-AT, converted for EaW/FoC by Darth_Windu, obtained through Clone Wars 3.0. Cincorax's attractive Sketchfab/GMod model was not available for direct download; do not claim it was used. Public redistribution rights for the downloaded legacy source still require provenance review.

UT-AT's tank mechanics were rebuilt on native Rock Head-style firing behavior after aim/arc/firing problems. Roof and side weapon origins match visible tips, with limited physical arcs rather than arbitrary full rotation. Main roof damage is 75, exactly 25% above TX-130's 60 damage per projectile. Left/right side guns are 30 each. User then requested 45% faster attack speed: all three RateOfFire values changed from 0.5 to 0.725, approximately 1.37931 seconds between shots. Range is 20. If all three guns hit continuously, nominal combined damage rate is 97.875 before mitigation/research. Health remains 875, so it is considerably more fragile than TX-130's 1500 despite greater multi-gun output. Movement speed is 4. Appearance feedback ('it looks good') is retained, but current-rate gameplay and every targeting state remain unverified.

### HAVw A6 Juggernaut — Fatboy II / UUX0101

This is a substantial weapon-layout adaptation, not a small texture replacement. Keep its observation tower: the user reversed an earlier removal request after checking references. Roof heavy gun, roof repeaters, side missile pods and a roof air-defense gun are in the current installed package. Rotating wheel visuals were added. All weapons need to line up with physical mounts; firing effects should originate at visible tips. Source is bruhepic925's Clone Turbo Tank HAVw A6 Juggernaut, embedded CC BY 4.0 attribution. Earlier texture failure produced a flat gray-green model; a flipped UV V coordinate during native export fixed atlas sampling. Do not reintroduce the old flat-material issue.

The current balance archive reduced five ground weapon maximum ranges from 100 to 85 and AA range from 32 to 27.2, following a 15% reduction request recorded in the balance evidence. Speed increases stack: vanilla 2.5 -> 2.875 (+15%), then -> 3.30625 (+15% on the changed baseline). That is +32.25% over vanilla, not +15% total. Reverse speed similarly reaches 2.314375. Confirm the intended cumulative value in the balance review; do not silently normalize it. Current main damage/rate are 300 and 0.3; smaller roof guns and side rockets have their own profiles. Health is 10000. Side-rocket visual guidance/physics and weapon revisions must be read from the current package rather than an old description. Final firing behavior, visual scale, animation/collision and balance need user testing.

### AT-TE — King Kriptor / UUX0111

AT-TE replaces King Kriptor; it is not an additional experimental slot. The user explicitly approved gameplay redesign because a six-legged AT-TE should not keep Kriptor's body/guns/function. Chosen role: heavy assault walker with a powerful top cannon, smaller laser turrets, durable and slow. Source: R3negadeAidan's AT-TE Walker (Animated), embedded CC BY 4.0. Native conversion and a test archive are installed; this is beyond the old Blender-only checkpoint.

Current health is 30000 vs King Kriptor's 50625; regen 60 vs 143. Main gun: 1500 damage, range 68.75 after a +25% increase from its custom baseline of 55, RateOfFire 1/3. Four forward laser muzzles share one volley controller; two rear lasers fire independently. Smaller laser damage is 70 and range 33.6. Movement changed from custom 1.8 to 1.98 (+10%); reverse 0.5 -> 0.55. Against vanilla Kriptor speed 2.6 it is still slower overall. The user reported frozen legs, then retested and thought animation worked; the latest request was speed changes only, with no animation edits. Do not treat the animation as conclusively broken or fully accepted. Test fresh builds, walking/stopping/turning, aim, all six small muzzles, wrecks, research and collision before declaring complete.

### SPHA-T — Jackhammer / UUX0113D1

Latest choice replaces the older AV-7 mapping. AV-7 is only a possible future artillery structure in the deferred buildings phase. We selected Nomada_Firefox's animated model from Return of the Clones v7.2 because it includes twelve-leg movement and deployment clips. The archive checksum was verified. The old ALA animation format required a local decoder; later work in a separate chat completed native SCM/SCA prototype conversion. Source rig was reduced to 62 bones, within the 72-matrix shader limit; prototype geometry has 3276 source triangles / 6552 including both windings. Source and packaged pose checks passed, with all twelve visible feet deforming. No standalone source firing/death clip was found in that archive; do not claim those clips were verified simply because an older showcase mentions them.

SPHA-T beam-test-1 is now installed. Latest explicit user authorization, recorded in the newer chat's decision file: direct laser fire, max range 95, native Load/Unload button as deploy/pack, and one native artillery shell's damage spread over a beam. Original shell damage 3750 becomes a nominal 3750 full-discharge budget over 2 seconds: 375 per installment at 0.2-second intervals, ten-installment cap. Nominal cycle 5 seconds, minimum range 30, splash radius 7. Original max range was 90. Native deployment immobilization, ability wait/attack enabling and JackhammerUnpacked defense buff are retained. Packing cancels an active beam. Basic health 30000 and speed 3.1 remain. Actual collision tick count, interrupted damage, research/critical effects and real target hits require runtime validation. Do not read Damage=375 as a 90% reduction: it is a beam installment, not the whole attack. Current visuals use provisional blue UEF beam/sound; all LODs share first-test geometry. Clearance/scale, native playback, balance and naming need fresh user acceptance. Source model public redistribution rights are not yet established.

## 3. Full conversion roster

Every list below contains unique mobile slots. Experimentals are grouped by their movement domain, not counted twice. Names marked provisional or unselected are not final model approvals. Standard engineers and ACUs are included. The mobile plan is 25 GAR slots and 21 CIS slots.
'''

parts=[intro]
for faction in ['GAR','CIS']:
    for domain in ['Ground','Air','Naval']:
        parts.append(f'### {faction}: {domain}\n')
        for u in D['units']:
            if u['faction']==faction and u['domain']==domain:
                status='installed prototype' if u['installed'] else 'not implemented'
                parts.append(f"- **{u['original']} -> {u['replacement']}** — `{u['id'].upper()}`; {status}. Planning status: {u['selection_status']}.")
        parts.append('')

parts.append('''### Roster constraints and superseded ideas

- GAR Broadsword is the LAAT family; exact variant remains open. Do not lock it to LAAT/i by assumption.
- GAR Mega/Air Fortress is one slot. Pelta, Acclamator and Venator are test candidates, not three approved units.
- GAR Atlantis II has no selected model. “Roj Magic” was an internal historical codename, not a selected vehicle.
- GAR naval mappings are provisional and require a separate visual/feasibility review, including Super Triton custom hull direction.
- CIS Cobra is NR-N99 Persuader; IG-227 Hailfire was rejected for that slot due to size.
- CIS Brackman is HAG-M; J-1 Proton Cannon is a reserved alternative, not selected replacement.
- CIS Renegade is MAF; Soul Ripper II is HMP. Do not duplicate HMP into the Renegade slot.
- No Renegade walking mechanic was established. Do not invent a LEGS upgrade for it. Preserve actual walking-leg transformations on the Cybran naval units where native files support them.
- CIS Engineer uses LM-432 engineering direction conditionally; fallback is a custom engineering droid on original functional chassis if infeasible.
- CIS ACU “Super Mega Battle Droid” is a custom project label with B2 and Super Tactical Droid inspiration, not an established canonical vehicle name.
- CIS Salem remains a choice between Confederate Destroyer and CIS-style Salem remodel. Do not silently select one.
- CIS Executioner and Command Class retain original functional hull rigs. Preserve Command Class aircraft production/launching and all naval transformations.
- CIS Kraken's Trident concept must preserve native underwater/surface/combat functions.
- Monkeylord is a custom Separatist spiderbot with Admiral Trench-inspired emblem/decals; retain original rotating weapons and gameplay.
- Cicada retains mobile cloaking, energy/recharge and activation behavior. It does not become a communications jammer.
- C-9979 Giant Transport preserves loading, unloading, capacity and production/combat interactions.

## 4. Actual numeric comparison: vanilla vs current

These are extracted source/configuration values, not illustrative estimates. The user's earlier example 'Rock Head 30A,20R,5S' was a format example only; do not repeat those numbers as facts.

Definitions: A = Damage field on the selected first damaging weapon; R = that weapon's MaxRadius; S = Physics.MaxSpeed; HP = Defense.MaxHealth; ROF = RateOfFire. A is per projectile or beam installment, not DPS or automatically the full volley. Source selected weapon labels are given to reveal when a redesign changes the comparison. Multiple weapon systems, muzzle/rack salvos, targeting, upgrades and beam ticks must be reviewed in the full weapon profiles. For a unit with no damaging weapon, A/R are not applicable, not zero.

Baseline is vanilla with DLC definitions where present. Current is a static reconstruction from installed full definitions and merge patches for DLC-enabled skirmish. Research, veterancy, difficulty, temporary buffs and script-driven changes are not applied. Native engine effective values were not queried. For design-only replacements, Current equals vanilla because no replacement archive was found; this does not mean the future design has been implemented or balanced.
''')
for faction in ['GAR','CIS']:
    parts.append(f'### {faction} A/R/S/HP overview\n')
    for u in D['units']:
        if u['faction']==faction:parts.append(f"- **{u['original']} -> {u['replacement']}** ({u['id'].upper()}): vanilla [{profile(u,'before')}] -> current [{profile(u,'after')}]. {'Installed prototype.' if u['installed'] else 'Planned identity only; current mechanics remain native.'}")
    parts.append('')

parts.append('''### Expanded current gun profiles for installed replacements

Profiles include native upgrade/control weapons where still defined. A weapon's presence in a blueprint does not prove it is enabled from construction. Never sum every listed profile into unit DPS without checking research/script gates and firing logic. In particular, interceptor damage applies to projectiles and is not comparable to surface-unit damage.
''')
for u in D['units']:
    if not u['installed']:continue
    parts.append(f"#### {u['replacement']} / {u['id'].upper()}\n")
    for w in u['weapons_after']:
        parts.append(f"- {w['label']}: Damage {fmt(w['damage'])}; range {fmt(w['min_range'])} to {fmt(w['range'])}; RateOfFire {fmt(w['rate'])}; muzzle salvo {fmt(w['muzzle_salvo'])}; rack salvo {fmt(w['rack_salvo'])}; total muzzle bones {w['muzzle_count']}; splash {fmt(w['splash'])}; layers {w['layers']}." )
    if not u['weapons_after']:parts.append('- No damaging weapon profiles; compare shield/support metrics instead.')
    parts.append('')

parts.append('''## 5. Balance interpretation and findings to carry forward

1. **UT-AT role change is a deliberate redesign.** A direct-fire tank vs an anti-missile unit is not meaningfully compared by damage ratio. Compare its armor/cost/role against TX-130 and other tanks while ensuring missile-defense coverage has moved to UT-AA.
2. **UT-AT firepower versus survivability:** nominal three-gun damage rate 97.875 vs approximately 60 for unresearched TX-130 main guns; UT-AT has 875 HP vs TX-130 1500, and speed 4 vs 3.1. This suggests a faster, fragile fire-support tank rather than a straight replacement upgrade. Actual arcs/hit probability and simultaneous side-gun coverage matter.
3. **Juggernaut speed stacks.** 3.30625 is +32.25% over native 2.5. The last requested increment was +15% on an already changed speed. This is a review flag, not permission to silently reduce it.
4. **AT-TE uses two baselines.** Its +10% speed is relative to custom 1.8, so current 1.98 is still about 23.85% slower than native Kriptor 2.6. Its +25% range is relative to custom 55, producing 68.75; native Kriptor's selected arm gun range was 50. Explicitly state which baseline each percentage references.
5. **AT-TE weapon count and volley behavior changed.** Four forward muzzles share FrontVolley; rear guns remain independent. A Damage field alone is insufficient to rank it against the thirteen native Kriptor weapon/controller entries.
6. **SPHA-T beam must be compared by full discharge and exposure.** Full budget 3750 over two seconds, nominal five-second cycle (~750 budget/second averaged over a complete uninterrupted cycle), with real collision/interrupt behavior unresolved. The immediate burst, target motion, splash and deployment vulnerability differ from a 3750 artillery shell.
7. **UT-AA research is a known cleanup need.** Always-on first-test interceptor supersedes an optional ground gun, leaving a formerly meaningful ground-weapon unlock potentially redundant or misleading.
8. **Naming defect found during this audit:** the unified naming overlay currently assigns AT-RT to UUL0102 and AT-AP to UUL0103. Correct identities are AT-AP/UUL0102 and AT-RT/UUL0103. Other current merge/model packages use the correct slots. The snapshot records the defect; no game files were modified by this documentation task. Do not propagate the reversed display labels into the design roster.
9. **Build/economy values:** MassValue and EnergyValue are raw blueprint resource values, not researched runtime costs. BuildTime is blueprint work, not necessarily literal seconds under all builders. BuildRate, regen, shield data and transport storage are in the metric sheet. Missing fields are not zero.
10. **No blanket parity claim:** numeric fields can match while projectile physics, targeting, scripts, arcs, deployment, collision and research behavior differ. Separate configuration parity from observed performance.

## 6. What still needs to be done

### Remaining GAR ground implementation

- Field Engineer -> ISP / Swamp Speeder engineering variant. Preserve construction, repairs, selection, build effects and relevant DLC mechanics.
- Standard Engineer -> custom GAR engineering vehicle. Functional construction/repair behavior and build attachments take priority over superficial model similarity.
- ACU -> custom GAR command walker/vehicle. Preserve commander build systems and all approved weapon/upgrade/death/escape dependencies unless separately redesigned.
- A5-RX visual/model rework remains outstanding even though its test archive exists.
- SPHA-T needs runtime deployment/beam/movement/packing tests; it is no longer just a model-search task.

### Ground-wide acceptance and polish

Perform a coordinated size pass using common reference units, not isolated arbitrary edits. Check world/selection/collision footprint, gantry/build clearance, formation movement, turning, reverse, terrain, crowd performance, LODs, textures/team colors, normals, transparency, muzzle tips, turret yaw/pitch/recoil, idle/walk/deploy/pack continuity, death/wreckage, transport and save/load. Test research unlocks, upgrades and enabled/disabled weapons from fresh units in a restarted game. Confirm the correct development executable path. Review names in factory queues, selection panels, research headings, prerequisite text and unlock descriptions, not just the unit's name field. Recheck AT-AP/AT-RT overlay IDs. Keep final sound choices distinct from temporary native effects. Each acceptance result should name the exact archive hash/revision.

### Broader production

GAR air and naval implementation still lies ahead, including unresolved model choices noted above. CIS design mappings are extensive but no CIS conversion package was found in this installed set; implementation, asset procurement/provenance and native compatibility remain. Buildings are deferred, including Noah Unit Cannon, Disruptor Station, Aegis Shield Generator, Research Converter, Proto-Brain Complex/dependency, Magnetron, Recycler and Boomerang. Keep Illuminate untouched. AV-7 is a candidate for a later artillery structure, not an approved completed building.

## 7. Tools, files, source-of-truth and GitHub

The local desktop is the authoritative asset/runtime environment; ordinary Chat Mode cannot inspect local files unless they are attached or connected. Do not pretend this prompt grants file access. Ask for an updated snapshot when facts cannot be checked, rather than reverting to old memory.

- Current generated snapshot: project-state.json; all 46 mobile slots, baseline/current scalar stats, all weapon profiles, field differences, installed package checksums and patch provenance.
- Workbook: SC2-Conversion-and-Balance.xlsx. Tabs: Unit comparison, Metric deltas, Weapon profiles, Conversion roster, Read me. Numeric deltas and percentage differences are formulas, with unavailable fields exposed.
- Exchange files: roster.csv, balance-metrics.csv, weapons.csv, gameplay-differences.csv, installed-packages.csv. These can be imported into other tools.
- Obsidian starter: a plain Markdown vault with one note per stable native unit ID, current progress and remaining work, linked index, known issues and decision rules. No plugin dependency or fake live synchronization.
- Machine-readable identity/decisions and regenerated numeric stats should be the authority. Prompt/workbook/Obsidian are generated reading views. Do not hand-edit three contradictory copies of stats.
- Keep identity (native ID), chosen model, gameplay role, current installed revision, model availability, provenance, rig conversion, installation and acceptance as separate fields. Unit display names can change; native IDs are stable keys.
- The GitHub repository is https://github.com/norvek-forge/SC2-CloneWars. Before this sync, its main branch had only the initial setup commit, while substantial newer files were local. The repo's older README and planning files were stale. The current sync adds a coherent snapshot and authored implementation source collection; it must not be described as a complete portable redistributable game build.
- Game archives, vanilla assets, downloaded model packs, external plugin source, private runtime copies and unverified-rights assets must not be swept into GitHub. Record paths/checksums/licenses and authored code instead. A manifest proves which files were inspected; it does not make local binaries available to another device.
- Repo update status, commit and any upload limitation are reported in GitHub-sync-status.md. Do not assume a push succeeded from the existence of a local commit.

Primary working locations for desktop implementation:

- Tracking/spec hub: C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2
- Active Git/game workspace: C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars
- Development game: active workspace + /local/dev-game
- Read-only Steam reference: B:/SteamLibrary/steamapps/common/Supreme Commander 2
- Main authoring work from this conversation: C:/Users/gavad/Documents/Codex/2026-10-18/let/work and /outputs
- UT-AT chat workspace: C:/Users/gavad/Documents/Codex/2026-10-24/sc2-ut-at
- SPHA-T newer native conversion workspace: C:/Users/gavad/Documents/Codex/2026-10-25/spha-t-jackhammer-handoff-user-chose
- Blender: B:/SteamLibrary/steamapps/common/Blender/blender.exe

Technical notes: SCD archives are ZIP containers. Native mesh is SCM MODL version 7; animations use SCA ANIM 101 in current pipeline. These exporters are constrained project tools, not universal game importers. Keep hierarchy, bone indices, inverse bind transforms and material definitions coherent. Respect the observed 72-matrix shader limit by consolidating unused helper bones. Flip UV V as needed when converting Blender UVs to DDS/D3D native layout; initial Juggernaut texture failure was a real example. Use Weapons plural in blueprint checks. Partial merge tables can leak old weapon fields if used incorrectly; role redesigns need intentionally complete tables or explicit validated logic. Treat native engine load order/cached Lua and localization separately from filename-based reconstruction.

## 8. How Chat Mode should help next

First acknowledge the project has moved beyond TX-130/AT-RT and summarize current installed ground roster, authorized role changes, remaining ground work and unresolved decisions. Use this prompt's numbers as snapshot data, preserving the stated method/limitations. Keep a compact current-state summary for future chats.

Help review balance by role, resource cost, health/shield, damage per complete discharge, practical sustained output, range/minimum range, target layers, movement/turn/acceleration, deployment vulnerability and research stage. Start by identifying asymmetric strengths/weaknesses and the explicit open flags, not by proposing arbitrary universal stat multipliers. Never invent missing stats. Do not compare anti-missile projectile damage to tank damage, or a beam installment to an artillery shell. Distinguish design intent from actual implementation evidence.

Help maintain the central registry and Obsidian/database structure. Suggest small, reviewable updates with stable IDs, dated user decisions, superseded history, exact artifact hashes, test outcomes, blockers and next action. Keep one authority for numeric snapshots and generate the views from it. Do not declare cross-device access, automatic Obsidian-Git synchronization or complete GitHub reproducibility unless those have actually been configured and tested.

Do not start from scratch, undo decisions because old context disagrees, invent a new experimental slot for AT-TE, restore UT-AT's superseded anti-missile role, remove the Juggernaut tower, put HMP into the Renegade slot, treat AV-7 as Jackhammer's current selection, begin deferred buildings/Illuminate, or call all prototypes finished. Ask only for decisions that materially affect the next work and are genuinely unresolved.
''')

prompt='\n\n'.join(parts)
(O/'CHAT-MODE-FULL-PROMPT.md').write_text(prompt,encoding='utf-8')
(O/'CHAT-MODE-FULL-PROMPT.txt').write_text(prompt,encoding='utf-8')

vault=O/'Obsidian-SC2';(vault/'Units').mkdir(parents=True,exist_ok=True)
index=['# SC2: The Clone Wars\n','Snapshot: 2026-10-25. [[Current status]] · [[Known issues]] · [[Workflow]]\n']
for faction in ['GAR','CIS']:
    for domain in ['Ground','Air','Naval']:
        index.append(f'## {faction} — {domain}\n')
        for u in D['units']:
            if u['faction']==faction and u['domain']==domain:index.append(f"- [[Units/{u['id']}|{u['original']} → {u['replacement']}]]")
for u in D['units']:
    lines=['---',f"unit_id: {u['id']}",f"faction: {u['faction']}",f"domain: {u['domain']}",f"original: {json.dumps(u['original'])}",f"replacement: {json.dumps(u['replacement'])}",f"installed: {str(u['installed']).lower()}",'snapshot: 2026-10-25','---',f"# {u['replacement']}",f"[[Home]] · {u['original']} / {u['id'].upper()}",'## State',u['status'],u['notes'] or 'No detailed acceptance evidence included; review current files before implementation.','## Primary comparison',f"Vanilla: {profile(u,'before')}",f"Current: {profile(u,'after')}",'A is selected weapon projectile/tick damage, not total DPS. See workbook/full profiles.','## Next action','Runtime/visual/research acceptance and balance review.' if u['installed'] else 'Locate a suitable licensed model, inspect rig and establish a native prototype.','## Provenance',u['baseline_source']['archive']+'!'+u['baseline_source']['entry']]
    lines+=['- '+p['archive']+'!'+p['entry'] for p in u['patches']]
    (vault/'Units'/f"{u['id']}.md").write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
(vault/'Home.md').write_text('\n\n'.join(index),encoding='utf-8')
(vault/'Current status.md').write_text('# Current status\n\n10 GAR ground prototypes installed; 3 remaining GAR ground engineer/ACU slots not implemented. A5-RX rework and all current-unit polish/testing remain. GAR air/naval and CIS conversions are design plans. SPHA-T beam-test-1 is installed in the newest evidence, not merely downloaded. See the full Chat Mode prompt and snapshot for details.\n\n[[Home]] · [[Known issues]] · [[Workflow]]\n',encoding='utf-8')
(vault/'Known issues.md').write_text('# Known issues\n\n- AT-AP/UUL0102 and AT-RT/UUL0103 display labels are reversed in unified naming overlay. Design roster remains correct.\n- Juggernaut two +15% speed increments stack to +32.25% vs native. Confirm intent.\n- UT-AA former optional ground-gun research is redundant after always-on interceptor trial.\n- SPHA-T beam damage timing, deployment, footprint and playback await runtime tests.\n- A5-RX rework deferred despite installed archive.\n- Current snapshots reconstruct configuration; they are not engine measurements or final balance acceptance.\n- Third-party public redistribution rights remain unresolved for some imported assets.\n\n[[Home]]\n',encoding='utf-8')
(vault/'Workflow.md').write_text('# Source-of-truth workflow\n\n1. Record human decisions in decisions.json with date, unit ID, scope and superseded choice.\n2. Inspect current installed archives and capture hashes, numeric fields and provenance in project-state.json.\n3. Regenerate workbook, CSV and Markdown notes from that snapshot.\n4. Review numeric differences and missing evidence before changing gameplay.\n5. Record fresh tests by exact archive hash/revision.\n6. Commit only reviewed documentation/data/authored code. Keep private game/model archives outside Git.\n7. Push, then verify the remote commit.\n\nOpen this folder as an Obsidian vault; no plugin is required. These are ordinary linked Markdown notes. Live synchronization is not configured.\n\n[[Home]]\n',encoding='utf-8')
print('Prompt words:',len(prompt.split()),'vault unit notes:',len(D['units']))
