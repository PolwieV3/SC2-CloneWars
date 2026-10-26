from pathlib import Path
import json,sys,struct,zipfile,copy,hashlib,math,re
from io import BytesIO
from PIL import Image
r=Path(__file__).resolve().parents[2];w=r/'work/juggernaut';out=r/'outputs/Juggernaut';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atap');import scm_v7,native_animation
from poc_unit import LiteralTable,merge,differences
base=w/'native';native=(base/'units.scd/units/UEF/UUX0101/UUX0101_lod0.win.scm').read_bytes();original=scm_v7.read(native);fit=json.loads((w/'fitted-rig.json').read_text());bones=fit['bones'];added=[{'name':b['name'],'parent':'UUX0101','inverse':b['inverse'],'position':b['position'],'quaternion':b['quaternion']} for b in bones[len(original['bones']):]];ref=bytearray(native_animation.extend(native,added));parsed=scm_v7.read(ref)
for i,b in enumerate(bones):
 old=parsed['bones'][i];row=b['inverse']+b['position']+b['quaternion']+[old[23],b['parent'],old[25],old[26]];scm_v7.BONE.pack_into(ref,parsed['header'][2]+i*scm_v7.BONE.size,*row)
ref=bytes(ref);fitted=scm_v7.read(ref);assert fitted['names'][:len(original['names'])]==original['names'];assert fitted['header'][3]==43
payload={};reports=[];folder='units/CloneWars/Juggernaut/'
for lod in range(3):
 geo=json.loads((w/f'geometry-lod{lod}.json').read_text())['triangles'];verts=[];indices=[];lookup={}
 def push(v):
  key=tuple(round(x,6) if isinstance(x,float) else x for x in v)
  if key not in lookup:lookup[key]=len(verts);verts.append(v)
  indices.append(lookup[key])
 for tri in geo:
  for v in tri:
   row=list(v);row[13]=1-row[13];row[15]=1-row[15];row[9:12]=[-x for x in row[9:12]];push(row)
  # Explicit backfaces retain source double-sided armor, avoiding transparent panels.
  for v in [tri[0],tri[2],tri[1]]:
   row=list(v);row[13]=1-row[13];row[15]=1-row[15];row[3:6]=[-x for x in row[3:6]];push(row)
 assert len(verts)<65536,(lod,len(verts));assert all(v[16]<43 for v in verts)
 raw=scm_v7.write(ref,verts,indices,[(len(indices)//3,0,0,len(verts)),(0,len(indices),len(verts),0)]);check=scm_v7.read(raw);assert check['bones']==fitted['bones']
 for suffix in ['.scm','.win.scm']:payload[folder+f'UUX0101_lod{lod}'+suffix]=raw
 reports.append({'lod':lod,**scm_v7.summary(raw)})
def dds(im):
 im=im.convert('RGBA');width,height=im.size;levels=[]
 while True:
  levels.append(im.tobytes('raw','BGRA'))
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
 vals=[124,0x2100f,height,width,width*4,0,len(levels)]+[0]*11+[32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000]+[0x401008,0,0,0,0]
 return b'DDS '+struct.pack('<31I',*vals)+b''.join(levels)
for kind,im in [('Diffuse',Image.open(w/'atlas.png')),('Normal',Image.new('RGBA',(2048,2048),(128,128,255,128))),('Mask',Image.new('RGBA',(2048,2048),(12,0,24,220))),('Team',Image.new('RGBA',(2048,2048),(0,0,0,0)))]:
 raw=dds(im)
 for suffix in ['.dds','.win.dds']:payload[folder+'UUX0101_'+kind+suffix]=raw
bp=LiteralTable((base/'uncompiled_lua.scd/uncompiled/Units/UEF/UUX0101/UUX0101_unit.bp').read_text(encoding='utf-8')).blueprint();dlc=LiteralTable((base/'z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUX0101/UUX0101_unit.bp').read_text(encoding='utf-8')).blueprint()
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
mesh=copy.deepcopy(bp['Display']['Mesh']);mid='/units/clonewars/juggernaut/juggernaut_mesh';mesh['BlueprintId']=mid
for i,t in mesh['LODs'].items():
 t['MeshName']=f'/units/CloneWars/Juggernaut/UUX0101_lod{i-1}.scm'
 for ms in t['MaterialSets'].values():
  for material in ms['Materials'].values():
   for field,kind in [('DiffuseName','Diffuse'),('NormalName','Normal'),('MaskName','Mask'),('TeamName','Team')]:material[field]=f'/units/CloneWars/Juggernaut/UUX0101_{kind}.dds'
   material['ShaderMacros']=material.get('ShaderMacros','ambient_lighting, diffuse_lighting, specular_lighting, ambient_occlusion, team_color, environment_mapping, point_cloud').replace(', anim_uvr','')
# Per-unit effect core avoids changing AT-AP or other consumers.
shared=Path(r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/shared/republic-blue-blaster')
sys.path.insert(0,str(shared));import build_core
for path,data in build_core.payload().items():
 path=path.replace('lua/CloneWars/RepublicBlueBlaster.lua','lua/CloneWars/JuggernautBlueBlaster.lua').replace('effects/clonewars/republic/blueblaster/','effects/clonewars/juggernaut/blueblaster/')
 payload[path]=data.replace(b'/effects/clonewars/republic/blueblaster/',b'/effects/clonewars/juggernaut/blueblaster/')
# Saturated private ramp, with no white center or lingering glow particles.
ramp=Image.new('RGBA',(256,16))
ramp.putdata([(35,110,235,int(175*(1-x/255))) for y in range(16) for x in range(256)])
for ext in ['.dds','.win.dds']:payload['effects/clonewars/juggernaut/blueblaster/saturated_blue'+ext]=dds(ramp)
for key in list(payload):
 if key.endswith('_emit.bp'):
  text=payload[key].decode()
  text=re.sub(r'RampTexture\s*=\s*\[\[.*?\]\]', 'RampTexture = [[/effects/clonewars/juggernaut/blueblaster/saturated_blue.dds]]',text)
  text=text.replace('Size = 0.25','Size = 0.22').replace('TrailLength = 0.45','TrailLength = 0.38')
  if 'impact_flash' in key:text=text.replace('y=0.8000,z=0.2000','y=0.1200,z=0.0000').replace('y=1.8000,z=0.5000','y=0.5000,z=0.0000')
  payload[key]=text.encode()
key='lua/CloneWars/JuggernautBlueBlaster.lua'
payload[key]=payload[key].replace(b"    local glow = CreateEmittersOnEntity(projectile, projectile:GetArmy(), {Root .. 'blue_bolt_glow_emit.bp'}, true)",b'    local glow = false')
# A thin pale-blue core supplies shine within the wider blue envelope.
core=Image.new('RGBA',(256,16))
core.putdata([(140,210,255,int(145*(1-x/255))) for y in range(16) for x in range(256)])
for ext in ['.dds','.win.dds']:payload['effects/clonewars/juggernaut/blueblaster/bright_core'+ext]=dds(core)
trail='effects/clonewars/juggernaut/blueblaster/blue_bolt_trail_emit.bp'
payload['effects/clonewars/juggernaut/blueblaster/bright_core_emit.bp']=payload[trail].replace(b'saturated_blue.dds',b'bright_core.dds').replace(b'Size = 0.22',b'Size = 0.08').replace(b'TrailLength = 0.38',b'TrailLength = 0.30')
key='lua/CloneWars/JuggernautBlueBlaster.lua'
payload[key]=payload[key].replace(b'    local glow = false',b"    local glow = CreateTrail(projectile, -2, projectile:GetArmy(), Root .. 'bright_core_emit.bp')")
# Copy the exact installed AT-AP effect into a private roof-cannon namespace.
atap_archive=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata/zz_SC2_CloneWars_ATAP_Model.scd')
with zipfile.ZipFile(atap_archive) as atap:
 for key in atap.namelist():
  if key=='lua/CloneWars/RepublicBlueBlaster.lua' or key.startswith('effects/clonewars/republic/blueblaster/'):
   dest=key.replace('lua/CloneWars/RepublicBlueBlaster.lua','lua/CloneWars/JuggernautRoofBlaster.lua').replace('effects/clonewars/republic/blueblaster/','effects/clonewars/juggernaut/roofblaster/')
   payload[dest]=atap.read(key).replace(b'/effects/clonewars/republic/blueblaster/',b'/effects/clonewars/juggernaut/roofblaster/')
# Preserve the AT-AP ramp shape and alpha, but suppress its near-white RGB core.
with zipfile.ZipFile(r'B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata/textures.scd') as tex:
 names={n.lower():n for n in tex.namelist()}
 for filename in ['ramp_blue_02','ramp_blue_green']:
  source='textures/particles/'+filename+'.win.dds'
  if source not in names:source='textures/particles/'+filename+'.dds'
  im=Image.open(BytesIO(tex.read(names[source]))).convert('RGBA')
  im.putdata([(int(red*.32),int(green*.66),blue,alpha) for red,green,blue,alpha in im.getdata()])
  for ext in ['.dds','.win.dds']:payload['effects/clonewars/juggernaut/roofblaster/'+filename+ext]=dds(im)
 for key in list(payload):
  if key.startswith('effects/clonewars/juggernaut/roofblaster/') and key.endswith('_emit.bp'):
   payload[key]=payload[key].replace(b'/textures/particles/ramp_blue_02.dds',b'/effects/clonewars/juggernaut/roofblaster/ramp_blue_02.dds').replace(b'/textures/particles/ramp_blue_green.dds',b'/effects/clonewars/juggernaut/roofblaster/ramp_blue_green.dds')
projectile_checks=[]
for name,origin,rocket in [('JUGHeavyBolt','UCannonShell03',False),('JUGRepeaterBolt','UCannonShell02',False),('JUGSideRocket','UTacticalMissile01',True),('JUGAABolt','UAntiAir02',False)]:
 originalp=LiteralTable((w/'weapon-reference'/(origin+'_proj.bp')).read_text(encoding='utf-8').replace('ProjectileBlueprint','UnitBlueprint',1)).blueprint();proj=copy.deepcopy(originalp);proj['BlueprintId']='/projectiles/clonewars/'+name.lower()+'/'+name.lower()+'_proj'
 pf='projectiles/CloneWars/'+name+'/'
 if rocket:
  tactical=LiteralTable((w/'weapon-reference/UTacticalMissile01_proj.bp').read_text(encoding='utf-8').replace('ProjectileBlueprint','UnitBlueprint',1)).blueprint();msh=copy.deepcopy(tactical['Display']['Mesh']);msh['BlueprintId']='/projectiles/clonewars/jugsiderocket/jugrocket_mesh'
  for table in msh['LODs'].values():
   table['MeshName']='/projectiles/UEF/UTacticalMissile01/UTacticalMissile01_lod0.scm';table['DiffuseName']='/projectiles/CloneWars/JUGSideRocket/MissileBlue.dds'
  im=Image.open(w/'weapon-reference/missile-native.dds').convert('RGBA');pixels=[]
  for red,green,blue,alpha in im.getdata():
   light=max(red,green,blue);pixels.append((int(light*.40),int(light*.75),light,alpha))
  im.putdata(pixels)
  for suffix in ['.dds','.win.dds']:payload[pf+'MissileBlue'+suffix]=dds(im)
  payload[pf+'JugRocket_mesh.bp']=('MeshBlueprint '+lua(msh)+'\n').encode();proj['Display']['MeshBlueprint']=msh['BlueprintId'];proj['Display']['UniformScale']=.035
  proj['Effects']={}
  proj['Physics'].update({'Acceleration':12,'InitialSpeed':14,'MaxSpeed':32,'MaxZigZag':0,'ZigZagFrequency':0,'TurnRate':360,'TrackTarget':False,'TrackTargetGround':True,'VelocityAlign':True})
  code="""local Projectile = import('/lua/sim/Projectile.lua').Projectile
local Blue = import('/lua/CloneWars/JuggernautBlueBlaster.lua')
JUGSideRocket = Class(Projectile) {
    OnCreate = function(self)
        Projectile.OnCreate(self)
        Blue.AttachBolt(self)
        self:ForkThread(self.LaunchGuidance)
    end,
    LaunchGuidance = function(self)
        WaitSeconds(0.15)
        if self:BeenDestroyed() then return end
        self:SetTurnRate(360)
        self:SetVelocityAlign(true)
        self:TrackTarget(true)
    end,
    OnLostTarget = function(self)
        Projectile.OnLostTarget(self)
        self:Destroy()
    end,
    OnImpact = function(self, targetType, targetEntity)
        Blue.ImpactFlash(self)
        Projectile.OnImpact(self, targetType, targetEntity)
    end,
}
TypeClass = JUGSideRocket
"""
 else:
  proj['Display'].pop('MeshBlueprint',None);proj['Effects']={}
  code="local Projectile = import('/lua/sim/Projectile.lua').Projectile\nlocal Blue = import('/lua/CloneWars/JuggernautBlueBlaster.lua')\n"+name+" = Class(Projectile) {\n OnCreate = function(self) Projectile.OnCreate(self); Blue.AttachBolt(self) end,\n OnImpact = function(self, targetType, targetEntity) Blue.ImpactFlash(self); Projectile.OnImpact(self, targetType, targetEntity) end,\n}\nTypeClass = "+name+"\n"
 if not rocket:code=code.replace('JuggernautBlueBlaster.lua','JuggernautRoofBlaster.lua')
 payload[pf+name+'_proj.bp']=('ProjectileBlueprint '+lua(proj)+'\n').encode();payload[pf+name+'_script.lua']=code.encode();assert rocket or proj['Physics']==originalp['Physics'];projectile_checks.append({'projectile':name,'native_physics_source':origin,'native_physics_preserved':not rocket,'rocket_is_guided':rocket})
weaponpatch={}
for index,weapon in bp['Weapons'].items():
 name='JUGHeavyBolt' if index==1 else ('JUGSideRocket' if index in [3,5] else 'JUGRepeaterBolt');weaponpatch[index]={'ProjectileId':'/projectiles/CloneWars/'+name+'/'+name+'_proj.bp'}
 if index in [3,5]:
  weaponpatch[index].update({'Turreted':False,'RackSlavedToTurret':False,'RackRecoilDistance':0,'BallisticArc':'RULEUBA_None','RequireFiringTrajectory':False,'ValidateFiringTrajectory':False,'FiringRandomness':0,'SlavedToBody':False,'MuzzleVelocity':6,'ProjectileLifetime':25,'WeaponCategory':'Missile','RangeCategory':'UWRC_IndirectFire','FiringTolerance':180,'MuzzleFlashEffect':'','Audio':{'Fire':'SC2/SC2/Units/UEF/UUL0104/snd_UUL0104_MobileMissile_Missile_Cruise'}})

for i in [3,5]:
 weaponpatch[i].update({'RackFireTogether':True,'RackSalvoSize':1,'MuzzleSalvoSize':3,'MuzzleSalvoDelay':.1,'ProjectilesPerOnFire':9,'RackSalvoReloadTime':2.5,'RackReloadTimeout':0,'RateOfFire':1/3.4,'MuzzleVelocity':14,'MuzzleVelocityReduceDistance':100000,'ProjectileLifetime':6,'ProjectileLifetimeUsesMultiplier':1,'NotExclusive':True,'Audio':{'Fire':'','RackSalvoBeginFire':'SC2/SC2/Units/UEF/UUL0104/snd_UUL0104_MobileMissile_Missile_Cruise'}})

for i in [1,2,4]:weaponpatch[i]['MuzzleFlashEffect']=''

# Half the native mobile-AA sustained damage, with strict air-only target filters.
aa=LiteralTable((r/'work/archanist/native/uncompiled_lua.scd/uncompiled/Units/UEF/UUL0105/UUL0105_unit.bp').read_text(encoding='utf-8')).blueprint()['Weapons'][1]
aa=copy.deepcopy(aa)
for key in list(aa):
 if key.startswith('WeaponUnpack') or key.startswith('WeaponRepack'):del aa[key]
aa.update({'Label':'JUGAntiAir','DisplayName':'Roof Air Defense Blaster','Damage':8,'DamageRadius':0,'RateOfFire':2,'MaxRadius':32,'MuzzleVelocity':55,'MuzzleFlashEffect':'','WeaponUnpacks':False,'ProjectilesPerOnFire':1,'MuzzleSalvoSize':1,'MuzzleSalvoDelay':0,'RackFireTogether':False,'RackBones':{1:{'RackBone':'JUG_AA_Pitch','MuzzleBones':{1:'JUG_AA_Muzzle'}}},'TurretBoneYaw':'JUG_AA_Yaw','TurretBonePitch':'JUG_AA_Pitch','TurretBoneMuzzle':'JUG_AA_Muzzle','TurretPitch':40,'TurretPitchRange':45,'TurretPitchSpeed':180,'TurretYaw':0,'TurretYawRange':180,'TurretYawSpeed':180,'CannotAttackGround':True,'TargetRestrictOnlyAllow':'AIR','TargetRestrictDisallow':'UNTARGETABLE,LAND,STRUCTURE,NAVAL','TargetPriorities':{1:'AIR MOBILE',2:'AIR'},'FireTargetLayerCaps':{'Land':'Air','Water':'Air'},'NotExclusive':True,'ProjectileId':'/projectiles/CloneWars/JUGAABolt/JUGAABolt_proj.bp'})
weaponpatch[6]=aa

patch={'Merge':True,'BlueprintId':'uux0101','Display':{'MeshBlueprint':mid,'DisplayName':'HAVw A6 Juggernaut'},'General':{'UnitName':'HAVw A6 Juggernaut'},'ScriptModule':'/units/CloneWars/Juggernaut/JUG_script.lua','ScriptClass':'JUG','Weapons':weaponpatch};checks=[]
allowed={*(f'Weapons.{i}.MuzzleFlashEffect' for i in [1,2,4]),*(f'Weapons.{i}.ProjectileId' for i in range(1,6)),'Display.MeshBlueprint','Display.DisplayName','General.UnitName','ScriptModule','ScriptClass'}
allowed.add('Weapons.6')
for i in [3,5]:
 for key in weaponpatch[i]:allowed.add(f'Weapons.{i}.{key}')
 allowed.add(f'Weapons.{i}.Audio.Fire');allowed.add(f'Weapons.{i}.Audio.RackSalvoBeginFire')
for label,org in [('base',bp),('DLC',dlc)]:
 changed=copy.deepcopy(org);merge(changed,{k:v for k,v in patch.items() if k not in ['Merge','BlueprintId']});diff=differences(org,changed);assert all(key in allowed or any(key.startswith(f'Weapons.{i}.RackBones') for i in [3,5]) for key in diff),diff
 for f in ['Physics','Economy','Intel','Build','Transport','Defense','Categories','Air']:assert changed.get(f)==org.get(f),(label,f)
 for wi,weapon in org.get('Weapons',{}).items():
  after=changed['Weapons'][wi]
  if wi in [1,2,4]:assert {k:v for k,v in weapon.items() if k not in ['ProjectileId','MuzzleFlashEffect']}=={k:v for k,v in after.items() if k not in ['ProjectileId','MuzzleFlashEffect']}
  for field in ['Damage','DamageRadius','MaxRadius']:assert weapon.get(field)==after.get(field),(wi,field)
 checks.append({'variant':label,'diff':diff,'damage_range_and_nonweapon_stats_unchanged':True,'roof_weapon_fields_unchanged_except_projectile_and_flash_visuals':True})
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/']:payload[prefix+'units/zz_clonewars_juggernaut_model_unit.bp']=('UnitBlueprint '+lua(patch)+'\n').encode()
payload[folder+'Juggernaut_mesh.bp']=('MeshBlueprint '+lua(mesh)+'\n').encode()
radius=fit['wheel_radius_world']
script="""local Blue = import('/lua/CloneWars/JuggernautRoofBlaster.lua')
local RocketBlue = import('/lua/CloneWars/JuggernautBlueBlaster.lua')
local DefaultProjectileWeapon = import('/lua/sim/DefaultWeapons.lua').DefaultProjectileWeapon
local Base = import('/units/UEF/UUX0101/UUX0101_script.lua').UUX0101
JUG = Class(Base) {
    Weapons = {
        JUGAntiAir = Class(DefaultProjectileWeapon) { PlayFxMuzzleSequence = function(self, muzzle) Blue.MuzzleFlash(self.unit, muzzle) end },
        MainTurret01 = Class(Base.Weapons.MainTurret01) { CreateProjectileAtMuzzle = function(self, muzzle) return DefaultProjectileWeapon.CreateProjectileAtMuzzle(self, muzzle) end, PlayFxMuzzleSequence = function(self, muzzle) Blue.MuzzleFlash(self.unit, muzzle) end },
        RightTurret01 = Class(Base.Weapons.RightTurret01) { PlayFxMuzzleSequence = function(self, muzzle) Blue.MuzzleFlash(self.unit, muzzle) end },
        RightTurret02 = Class(Base.Weapons.RightTurret02) { PlayFxMuzzleSequence = function(self, muzzle) RocketBlue.MuzzleFlash(self.unit, muzzle) end },
        LeftTurret01 = Class(Base.Weapons.LeftTurret01) { PlayFxMuzzleSequence = function(self, muzzle) Blue.MuzzleFlash(self.unit, muzzle) end },
        LeftTurret02 = Class(Base.Weapons.LeftTurret02) { PlayFxMuzzleSequence = function(self, muzzle) RocketBlue.MuzzleFlash(self.unit, muzzle) end },
    },
    OnStopBeingBuilt = function(self, builder, layer)
        Base.OnStopBeingBuilt(self, builder, layer)
        self.JUGWheelRotators = {}
        for i = 1, 10 do
            local rot = CreateRotator(self, string.format('JUG_Wheel%02d', i), 'x', nil, 0, 1440, 0)
            rot:SetAccel(1440)
            self.Trash:Add(rot)
            table.insert(self.JUGWheelRotators, rot)
        end
        self:ForkThread(self.JUGWheelThread)
        LOG('CloneWars Juggernaut air-defense-12: wheel controllers ready, acceleration 1440')
    end,
    JUGWheelThread = function(self)
        local p = self:GetPosition()
        local lx, lz = p[1], p[3]
        while not self:IsDead() do
            WaitSeconds(0.1)
            if self:IsDead() then break end
            local now = self:GetPosition()
            local dx, dz = now[1] - lx, now[3] - lz
            local speed = math.sqrt(dx * dx + dz * dz) * 10
            local rate = speed / WHEEL_RADIUS * 57.295779513
            if rate > 720 then rate = 720 end
            for k, rot in self.JUGWheelRotators do
                rot:SetTargetSpeed(rate)
            end
            lx, lz = now[1], now[3]
        end
    end,
}
TypeClass = JUG
""".replace('WHEEL_RADIUS',str(radius))
payload[folder+'JUG_script.lua']=script.encode();(w/'JUG_script.lua').write_text(script,encoding='utf-8');payload['CloneWars_Juggernaut_ATTRIBUTION.txt']=(out/'ATTRIBUTION.txt').read_bytes()+b'\nProject modifications: five native-controller gun replacements, approved weapon-chain/muzzle repositioning, ten cosmetic wheel bones/controllers, texture atlas, distance LODs and two-sided native mesh conversion.\n'
archive=out/'zz_SC2_CloneWars_Juggernaut_Model.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'date':'2026-10-23','revision':'air-defense-12','archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'projectile_checks':projectile_checks,'texture_correction':'Blender UV V flipped into native DDS top-origin coordinates; native shader macros restored','weapon_roles':'rear heavy gun, two forward roof repeaters, two existing forward side launch-port panels; nine-shot volleys, 2.5 second reload, fast guidance without zigzag; original tower retained','meshes':reports,'blueprint_checks':checks,'authorized_exception':'User approves replacing guns and requests two fixed blue mobile-missile-launcher side weapons; roof three retained','source_animations':'None. Original static mesh bound to native weapon controllers; ten cosmetic wheel bones added','native_unit_class':'Original UUX0101 inherited; original Weapons table, tread controllers, build/transport lifecycle retained through base call','wheel_script':'Distance-based rotation with explicit nonzero acceleration; reverse direction is not yet distinguished; runtime test pending','limits':['Current aiming/shot clearance and wheel animation require runtime test','Visual scale32 provisional; source length about50 model units versus native42','No source animation conversion claimed','Original nonweapon detail may remain static','Normal maps and team tint deferred; matte diffuse atlas used','Original wreckage and build effects retained; new wreckage model not authored'],'installed':False}
(w/'package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(out/'Package-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'sha256':report['sha256'],'LODs':[(x['vertices'],x['triangles']) for x in reports],'checks':checks}))
