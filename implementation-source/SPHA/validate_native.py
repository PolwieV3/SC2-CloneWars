import bpy,json,sys,zipfile,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
W=Path(__file__).resolve().parent;R=W.parents[1];O=R/'outputs/SPHA-T'
sys.path.insert(0,r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/archanist/pipeline');import scm_v7
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atap');import native_animation
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable
archive=O/'zzzzzz_SC2_CloneWars_SPHA.scd';folder='units/CloneWars/SPHA/'
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 model=scm_v7.read(z.read(folder+'SPHA_lod0.win.scm'));bones=model['bones'];names=model['names']
 clips={n:native_animation.read_sca(z.read(folder+'SPHA_'+n+'.win.sca')) for n in ['Walk','Idle','Deploy','Pack']}
 bp=LiteralTable(z.read('units/zzzz_clonewars_spha_unit.bp').decode('utf8')).blueprint()
 for prefix in ['mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:assert z.read(prefix+'units/zzzz_clonewars_spha_unit.bp')==z.read('units/zzzz_clonewars_spha_unit.bp')
 for i in range(3):assert z.read(folder+f'SPHA_lod{i}.scm')==z.read(folder+f'SPHA_lod{i}.win.scm')
 for n,c in clips.items():assert c['names']==names and list(c['links'])==[b[24] for b in bones]
 for key in ['AnimationWalk','AnimationIdle','AnimationOpen','AnimationClose']:assert bp['Display'][key].lstrip('/') in z.namelist()
 assert bp['Abilities']=={1:{'Blueprint':'Deploy'}}
 assert not any('SPHADeploy_Ability' in path for path in z.namelist())
 assert not any(n.endswith('Deploy_Ability.lua') for n in z.namelist())
 script=z.read(folder+'SPHA_script.lua')
 assert b"SetWeaponEnabledByLabel('MainGun', true)" in script
 assert b"SetWeaponEnabledByLabel('MainGun', false)" in script
 assert b"IsUnitState('Immobile')" in script and b'self:ForkThread(self.WatchDeployment)' in script
 gun=bp['Weapons'][1];assert gun['InitiallyDisabled'] and gun['MaxRadius']==95 and gun['MinRadius']==30
 assert bp['Weapons'][2]['MinRadius']==30
 assert gun['BallisticArc']=='RULEUBA_None' and 'ProjectileId' not in gun
 assert gun['Damage']*10==3750 and gun['BeamLifetime']==2 and gun['BeamCollisionDelay']==.2 and gun['RateOfFire']==.2
 for key in ['TurretBoneYaw','TurretBonePitch','TurretBoneMuzzle']:assert gun[key] in names
 assert gun['RackBones'][1]['MuzzleBones'][1]==gun['TurretBoneMuzzle']
 original=LiteralTable((R/'work/native-jackhammer/z_uncompiled_lua_dlc1_UUX0113D1_unit.bp').read_text(encoding='utf8')).blueprint()
 for key in ['Abilities','AI','Defense','Economy','Navigation','Transport']:assert bp[key]==original[key],key
 assert bp['General']['CommandCaps']==original['General']['CommandCaps']
 assert original['Physics']['MaxSpeed']==3.1 and bp['Physics']['MaxSpeed']==1.24
 for key,value in original['Physics'].items():
  if key!='MaxSpeed':assert bp['Physics'][key]==value,key
 assert bp['Display']['AnimationWalkRate']==.4
 assert 'TANK' in bp['Categories'].values() and 'DIRECTFIRE' in bp['Categories'].values() and 'OVERLAYDIRECTFIRE' in bp['Categories'].values()
 assert 'ARTILLERY' not in bp['Categories'].values() and 'INDIRECTFIRE' not in bp['Categories'].values()
 assert gun['FireTargetLayerCaps']=={'Land':'Land|Water|Seabed'}
 assert gun['TargetPriorities']=={1:'LAND MOBILE',2:'ALLUNITS'}
 assert gun['AutoInitiateAttackOnPatrol'] and gun['WeaponCategory']=='Direct Fire' and gun['RangeCategory']=='UWRC_DirectFire'
 assert gun['AlwaysRecheckTarget'] and gun['TargetCheckInterval']==.2
 assert 'CannotAttackGround' not in gun
 assert len(bones)<72 and all(-1<=b[24]<i for i,b in enumerate(bones))
 for j,v in enumerate(model['vertices']):assert sum(model['extra'][j*4:j*4+4])==255 and all(0<=n<len(bones) for n in v[16:])
 inverses=[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed() for b in bones]
 bind=[m.inverted() for m in inverses]
 def pose(rows,yaw=0,pitch=0):
  worlds=[]
  for i,row in enumerate(rows):
   local=Matrix.Translation(Vector(row[:3]))@Quaternion(row[3:]).to_matrix().to_4x4()
   if names[i]=='SPHA_Yaw':local=local@Matrix.Rotation(math.radians(yaw),4,'Y')
   if names[i]=='SPHA_Pitch':local=local@Matrix.Rotation(math.radians(-pitch),4,'X')
   worlds.append(worlds[bones[i][24]]@local if bones[i][24]>=0 else local)
  return worlds
 def vertices(world):
  skin=[m@inv for m,inv in zip(world,inverses)]
  return [skin[v[16]]@Vector(v[:3]) for v in model['vertices']]
 restworld=pose([b[16:23] for b in bones])
 binderror=max(max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4)) for a,b in zip(restworld,bind))
 assert binderror<.001
 w=clips['Walk'];a=vertices(pose(w['samples'][0][1]));b=vertices(pose(w['samples'][-1][1]));seam=max((x-y).length for x,y in zip(a,b));assert seam<1e-5
 frames={};footmotion={n:0 for n in names if n.startswith('Main_foot')}
 initial=pose(w['samples'][0][1]);initialv=vertices(initial)
 for t,rows in w['samples']:
  world=pose(rows)
  for n in footmotion:footmotion[n]=max(footmotion[n],(world[names.index(n)].translation-initial[names.index(n)].translation).length)
 assert len(footmotion)==12 and min(footmotion.values())>.1
 deploy=pose(clips['Deploy']['samples'][-1][1]);pack=pose(clips['Pack']['samples'][0][1])
 transition=max((x-y).length for x,y in zip(vertices(deploy),vertices(pack)));assert transition<.001
 muzzle=names.index('SPHA_Muzzle');pi=names.index('SPHA_Pitch')
 direction=(deploy[muzzle].translation-deploy[pi].translation).normalized();assert abs(direction.y)<.001
 aimerror=0
 for yaw in [-180,-90,0,90,180]:
  for elevation in [-40,0,40]:
   world=pose(clips['Deploy']['samples'][-1][1],yaw,elevation)
   direction=(world[muzzle].translation-world[pi].translation).normalized()
   axis=(world[pi].to_3x3()@Vector((0,0,1))).normalized();aimerror=max(aimerror,(axis-direction).length)
 assert aimerror<.001
 # Validate every packaged internal resource reference and all native scripts.
 native=set()
 game=Path('B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata')
 for path in game.glob('*.scd'):
  with zipfile.ZipFile(path) as nativezip:native.update('/'+n.lower() for n in nativezip.namelist())
 internal={'/'+n.lower() for n in z.namelist()}
 for p in ['/lua/sim/ExperimentalMobileUnit.lua','/lua/sim/DefaultWeapons.lua','/lua/sim/defaultcollisionbeams.lua','/lua/sim/CollisionBeam.lua']:assert p.lower() in native,p
 # Native mod-mounted Deploy resources are required and remain untouched.
 assert '/mods/dlc1/shadow/abilities/deploy_ability.lua' in native
 assert '/mods/dlc1/shadow/abilities/deploy_ability.bp' in native
 assert '/effects/emitters/weapons/uef/antimissile01/projectile/w_u_am01_p_02_polytrails_emit.bp' in native
report={'package_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'checks':'passed','bones':len(bones),'shader_limit':72,'bind_matrix_max_error':binderror,'walk_loop_vertex_error':seam,'deploy_to_pack_vertex_error':transition,'twelve_feet_motion':footmotion,'aim_axis_max_error':aimerror,'native_ability_and_preserved_simulation_fields':'pass','native_resources':'pass','runtime':'Not executed in game; actual collision pulse count, aiming, animation playback and button sequencing still require live test.'}
(O/'Native-pose-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
if '--checks-only' in sys.argv:raise SystemExit(0)
# Render three poses decoded from the actual package. This is an offline preview.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('SPHA packaged diffuse');mat.use_nodes=True
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/spha/SPHT.png')
bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.85
for number,(clip,frame,yaw,pitch) in enumerate([('Walk',0,0,0),('Deploy',-1,0,0),('Deploy',-1,30,10)]):
 world=pose(clips[clip]['samples'][frame][1],yaw,pitch);vs=vertices(world)
 mesh=bpy.data.meshes.new('Packaged '+str(number));mesh.from_pydata([(p.x*.1+number*8,-p.z*.1,p.y*.1) for p in vs],[],[model['indices'][i:i+3] for i in range(0,len(model['indices'])//2,3)])
 ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(ob);uv=mesh.uv_layers.new()
 for poly in mesh.polygons:
  for li in poly.loop_indices:
   v=model['vertices'][mesh.loops[li].vertex_index];uv.data[li].uv=(v[12],1-v[13])
 mesh.materials.append(mat)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1440;scene.render.resolution_y=650;scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35);center=Vector((8,0,2.5))
bpy.ops.object.camera_add(location=(22,-27,18));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=31;scene.camera=cam
for location,energy in [((3,-8,18),5000),((18,4,16),4000),((-8,0,10),2500)]:
 bpy.ops.object.light_add(type='AREA',location=location);light=bpy.context.object;light.data.energy=energy;light.data.size=10;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(O/'Packaged-poses-preview.png');bpy.ops.render.render(write_still=True)
