from pathlib import Path
import shutil
W=Path('work');O=Path('outputs');B=W/'revisions/pre-limited-arc-test6';B.mkdir(parents=True,exist_ok=True)
for p in [W/'build_package.py',W/'UTAT_script.lua',W/'validate_three_gun_aim.py',O/'zz_SC2_CloneWars_UTAT_Model.scd',O/'Package-validation.json',O/'Pose-validation.json']:shutil.copy2(p,B/p.name)
p=W/'build_package.py';s=p.read_text(encoding='utf-8').replace("'RackBones':{}}","'RackBones':{},'TurretYawRange':20,'TurretPitch':15,'TurretPitchRange':20}")
s=s.replace("'Weapons.1.TurretBoneMuzzle'}","'Weapons.1.TurretBoneMuzzle','Weapons.1.TurretYawRange','Weapons.1.TurretPitch','Weapons.1.TurretPitchRange'}")
s=s.replace('three-gun-aim-test-5-size170','limited-arc-test-6-size170').replace("'only_weapon_bone_bindings_change':True","'only_weapon_bone_bindings_and_three_arc_fields_change':True")
s=s.replace('No damage/range/rate/beam timing changes.','User-authorized tank-like gun limits: yaw +/-20 degrees, elevation -5 to +35. No damage/range/rate/beam timing changes.')
s=s.replace("'installed':False", "'mechanical_limits':{'yaw_degrees':[-20,20],'elevation_degrees':[-5,35],'hull_facing':'Limited native forward arc requires hull facing; existing RotateOnSpot and AI.Attacker.RelocateToFire retained; no forced move orders or teleports','future_home':'User will select a separate tank slot; current uul0203 staging only; target categories unchanged'},'installed':False")
p.write_text(s,encoding='utf-8')
p=W/'UTAT_script.lua';s=p.read_text(encoding='utf-8').replace('three-gun-aim-test-5: native yaw/pitch and tip muzzle controllers ready','limited-arc-test-6: three tip muzzles, yaw +/-20, elevation -5 to 35 ready').replace('CloneWars UTAT aim5 first fire','CloneWars UTAT arc6 first fire');p.write_text(s,encoding='utf-8')
