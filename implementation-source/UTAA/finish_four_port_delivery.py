from pathlib import Path
import json,shutil,zipfile,hashlib
R=Path(__file__).resolve().parents[2];W=R/'work/archanist';O=R/'outputs/UT-AA'
pkg=json.loads((O/'Package-validation.json').read_text(encoding='utf-8'))
motion=json.loads((O/'Native-motion-validation.json').read_text(encoding='utf-8'))
assert pkg['installed'] and pkg['sha256']==motion['archive_sha256']
checkpoint={
 'date':'2026-10-21','unit_id':'uul0105','identity':'UT-AA','revision':'four-port-test-2',
 'status':'Installed in isolated test game; asset checks passed; runtime acceptance pending',
 'package_sha256':pkg['sha256'],'installed_path':pkg['installed_path'],
 'source':'User supplied FotR14.zip; UT-AA hull/turret credited to Philloraptor',
 'provenance_note':'Existing recorded provenance retained; no new public-release rights determination',
 'launcher':'Original 940-triangle source assembly restored once, uniform scale .42, original four 2x2 openings',
 'mount':'Main support narrowed to .33 original width; entire main mount raised 1.5 model units after clearance checks',
 'muzzles':'Four new pitch-rack helper bones; both original four-entry banks reference those same four helpers in native order',
 'native_animation':'AOpen and Aland decoded as sparse float keys. Same timing, rotations and other tracks; two Turret01 Y keys per clip raised 1.5. Blender actions provided and deformation checked.',
 'unchanged':'Chassis and secondary-gun geometry, texture/material bytes, damage/range/rate/projectiles/targeting/reload/bank settings, movement, abilities and research settings',
 'validation':{'asset':'passed across all 3 LODs','native_motion_samples':motion['sample_count'],'housing_chassis_surface_intersections':0,'maximum_muzzle_error':motion['maximum_muzzle_center_error'],'blender_actions':'6 sampled poses passed','runtime_tested':False},
 'runtime_remaining':['Check actual projectile origins and flashes against aircraft','Confirm aim-controller blending, pack/unpack and movement in engine','Check researched secondary gun and distance transitions','User visual acceptance'],
 'known_limits':['Full-detail geometry at all LODs','Existing neutral normal map and disabled team tint','Final roster sizing deferred as requested'],
 'rollback_package':pkg['rollback_package'],
 'prior_revision':'native-fit-test-1 eight-port conversion superseded; backups/2026-10-20-four-port-restore retains its files',
 'reports':['Package-validation.json','Four-port-validation.json','Native-motion-validation.json','Blender-animation-validation.json','Installation.json']}
for p in [O/'Integration-checkpoint.json',W/'integration-checkpoint.json']:
 p.write_text(json.dumps(checkpoint,indent=2),encoding='utf-8')
# Keep familiar report filenames pointing to the completed revision.
shutil.copy2(O/'Four-port-validation.json',O/'Pose-validation.json')
shutil.copy2(O/'Native-motion-validation.json',O/'Clearance-validation.json')
(O/'Status.txt').write_text('UT-AA four-port-test-2 installed — October 21, 2026\n\nOriginal four-port launcher restored. Asset and native animation checks passed. In-game firing/effects and visual acceptance remain untested.\n\nRestart the isolated game using Launch-Skirmish-Test.cmd and build UEF UT-AA / Archanist.\n\nSee Four-port-readme.md for modifications, evidence, files and rollback.\n',encoding='utf-8')
readme='''# UT-AA four-port correction — October 21, 2026

Revision `four-port-test-2` is installed in the isolated test game. Restart its existing `Launch-Skirmish-Test.cmd` and build UEF UT-AA / Archanist.

## What changed

- Restored the complete original narrow UT-AA launcher: four octagonal openings in a centered 2×2 pattern, with the source armor, panel seams and texture layout. Removed the eight generated ports, enlarged front armor, bridge and skirts. The duplicated source draw mesh is omitted.
- Narrowed the main mounting brackets. Raised the main mount by 1.5 model units after the original mounting height produced chassis intersections. The housing proportions remain uniformly scaled from the source.
- Added four muzzle helpers at the measured bore centers. Both existing SC2 banks retain four entries in the original order and now reference these four positions. The aiming muzzle uses the same first helper.
- Matched the main rig translation in the opening and landing clips. Each clip changes only the two existing main-yaw Y-position keys. Duration, key times, rotations and every other track remain byte-identical. Bone names, parent links and the original 16 skinning indices are retained; the mount's inverse-bind positions are updated consistently.
- Preserved chassis and secondary-gun geometry attributes, all texture/material bytes, and all weapon fields except nine attachment-name strings. Damage, rate, range, projectiles, targeting, reload timing, bank structure, movement and abilities are unchanged in the base and DLC source comparisons. No gameplay Lua was added.

## Validation and its limits

All three exported LODs pass mesh, skeleton, topology, attachment and blueprint checks. Exactly one original four-port assembly remains. All non-assembly geometry is accounted for against the previous package.

The local reader consumes both complete ANIM101 clips, checks their skeleton links, key times and unit quaternions, and confirms first-frame transforms against the rig. Across 168 decoded-animation/deployed-aim samples, no main-housing/chassis triangle-surface intersections were detected. Maximum helper-to-visible-bore-center error is below 0.000002 model units. Six sampled Blender animation poses agree with the packaged motion within 0.000006 model units.

These are asset and Blender checks. **The game was not launched for this revision.** Actual muzzle effects, projectile emergence, aim-controller blending, moving fire, research operation and full engine animation/visual acceptance still require in-game observation. Surface sampling does not prove exhaustive collision-free motion between every component.

Native opening has 30 frames over 0.966667 seconds; landing has 16 frames over 0.5 seconds. No UT-AA-named source ALA clips were present in the supplied FotR archive; the delivered animations use the native SC2 motions.

Existing limitations remain: full-detail geometry at all LODs (8,316 exported triangles including backfaces), neutral normals, disabled team tint, and provisional roster scale.

## Deliverables

- [Animated editable model](UTAA-four-port-animated.blend) — packed textures, native rig, four helpers, opening and landing actions.
- [Static editable model](UTAA-four-port.blend).
- [Installed package](zz_SC2_CloneWars_UTAA_Model.scd).
- [Source bundle](UTAA-four-port-sources.zip) — scripts, required intermediate inputs, native references, and reproduction instructions.
- [Front](UTAA-four-port-front.png), [side](UTAA-four-port-side.png), [three-quarter](UTAA-four-port-three-quarter.png), and [deployed](UTAA-four-port-deployed.png) renders.
- Compare [original source](UTAA-source-preview.png) and [superseded eight-port model](UTAA-native-fit.png).
- [Attachment locations](Four-port-attachments.json), [package checks](Package-validation.json), [independent asset checks](Four-port-validation.json), [motion/clearance checks](Native-motion-validation.json), and [Blender motion checks](Blender-animation-validation.json).

## Installation and rollback

Only `zz_SC2_CloneWars_UTAA_Model.scd` was replaced in the existing isolated development game's `gamedata` directory. All seven other CloneWars package hashes were verified unchanged. Original Steam archives were not edited.

To restore the previous eight-port revision, close the test game and replace its UT-AA package with `backups/2026-10-21-before-final-install/zz_SC2_CloneWars_UTAA_Model.scd`. The wider source/model backup is in `backups/2026-10-20-four-port-restore`.

Source model: Philloraptor, Fall of the Republic 1.4, supplied by the user. Existing provenance records are retained.
'''
(O/'Four-port-readme.md').write_text(readme,encoding='utf-8')
audit=(W/'four-port-weapon-audit.md').read_text(encoding='utf-8')
(O/'Original-weapon-audit.md').write_text('Historical source audit. The initial recommendation to keep all original rest positions was superseded by the measured +1.5 mount correction; see Four-port-readme.md and current validation reports.\n\n'+audit,encoding='utf-8')
files=[]
for name in ['restore_four_port.py','build_four_port_package.py','validate_four_port.py','validate_native_motion.py','check_blender_motion.py','install_four_port.py','four-port-source-inspect.py','four-port-source-measurements.json','four-port-geometry.json','Rep_UTAA_Turret.json','atlas.png','native/rig.json']:
 files.append(W/name)
files+=list((W/'pipeline').glob('*.py'))
files += [W/'native/units.scd/units/UEF/UUL0105'/name for name in ['UUL0105_LOD0.win.scm','UUL0105_AOpen01.win.sca','UUL0105_Aland01.win.sca']]
files += [W/'native/uncompiled_lua.scd/uncompiled/Units/UEF/UUL0105/UUL0105_unit.bp',W/'native/z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUL0105/UUL0105_unit.bp']
files += [O/'backups/2026-10-20-four-port-restore'/name for name in ['state/geometry.json','zz_SC2_CloneWars_UTAA_Model.scd']]
files += [O/name for name in ['Four-port-readme.md','Original-weapon-audit.md','Package-validation.json','Four-port-validation.json','Native-motion-validation.json','Blender-animation-validation.json','Four-port-attachments.json']]
instructions='''UT-AA four-port source bundle

Extract into a dedicated folder and keep the work/ and outputs/ paths intact.
Requires Blender 5.2 and Python 3. Native binary and previous-revision references are included for this local project.

From the extracted root, run in order (replace blender with your executable path):
blender -b -t 6 -P work/archanist/restore_four_port.py
python work/archanist/build_four_port_package.py
blender -b -t 6 -P work/archanist/validate_four_port.py
blender -b -t 6 -P work/archanist/validate_native_motion.py
blender -b -t 6 -P work/archanist/check_blender_motion.py

Model outputs, renders and reports appear in outputs/UT-AA. Do not run install_four_port.py on another machine without updating its explicit isolated-game destination. It is supplied as an installation record/script, not an automatic setup step.

The install package uses original sparse-float-key ANIM101 files with a narrowly checked position offset. Blender actions are a preview/editing conversion. No game-runtime certification is implied.
'''
dest=O/'UTAA-four-port-sources.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('REBUILD.txt',instructions)
 for p in files:
  assert p.is_file(),p
  z.write(p,p.relative_to(R).as_posix())
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(json.dumps({'source_bundle':str(dest),'file_count':len(files)+1,'bytes':dest.stat().st_size,'package_sha256':pkg['sha256'],'installed':pkg['installed']}))
