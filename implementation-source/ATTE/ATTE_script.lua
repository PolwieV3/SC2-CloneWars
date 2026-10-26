local ExperimentalMobileUnit = import('/lua/sim/ExperimentalMobileUnit.lua').ExperimentalMobileUnit
local DefaultProjectileWeapon = import('/lua/sim/DefaultWeapons.lua').DefaultProjectileWeapon
local HeavyBlue = import('/lua/CloneWars/ATTEHeavyBlaster.lua')
local LightBlue = import('/lua/CloneWars/ATTELightBlaster.lua')

local Gun = Class(DefaultProjectileWeapon) {
    SetupTurret = function(self)
        DefaultProjectileWeapon.SetupTurret(self)
        if self.AimControl then self.AimControl:SetResetPoseTime(0) end
    end,
    ATTEAllowed = function(self)
        local label = self:GetBlueprint().Label
        if label == 'Main' then return true end
        local target = self:GetCurrentTargetPos()
        if not target then return false end
        local center = self.unit:GetPosition()
        local head = self.unit:GetBonePosition('Head_21')
        local back = self.unit:GetBonePosition('Butt_36')
        local fx,fz = head[1]-back[1],head[3]-back[3]
        local dx,dz = target[1]-center[1],target[3]-center[3]
        local length = math.sqrt((fx*fx+fz*fz)*(dx*dx+dz*dz))
        if length < 0.0001 then return false end
        local dot = (fx*dx+fz*dz)/length
        -- Final shot gate is independent of target acquisition and turret state.
        if label == 'FrontVolley' then return dot >= math.cos(45*math.pi/180) end
        return dot <= -math.cos(35*math.pi/180)
    end,
    PlayFxMuzzleSequence = function(self,muzzle)
        if self:ATTEAllowed() then
            if self:GetBlueprint().Label == 'Main' then HeavyBlue.MuzzleFlash(self.unit,muzzle)
            else LightBlue.MuzzleFlash(self.unit,muzzle) end
        end
    end,
    CreateProjectileAtMuzzle = function(self,muzzle)
        if self.ATTEChannels then self:SetFireControl(self.ATTEChannels[muzzle]) end
        if not self:ATTEAllowed() then return nil end
        local projectile = DefaultProjectileWeapon.CreateProjectileAtMuzzle(self,muzzle)
        if projectile then
            LOG(string.format('ATTE mount-test-6 shot %s %s time=%.3f',self:GetBlueprint().Label,muzzle,GetGameTimeSeconds()))
        end
        return projectile
    end,
}

local FrontVolley = Class(Gun) {
    SetupTurret = function(self)
        Gun.SetupTurret(self)
        self.ATTEControllers={self.AimControl}
        self.ATTEChannels={ATTE_FrontLeftTop_Muzzle='Default'}
        -- Every gun aims from its own hull-mounted pivot. Native fire channels
        -- share the weapon's target and clock without copying mount positions.
        for k,pair in {{'Right','ATTE_FrontLeftBottom'},{'Left','ATTE_FrontRightTop'},{'Torso','ATTE_FrontRightBottom'}} do
            local channel,prefix=pair[1],pair[2]
            local aim=CreateAimController(self,channel,prefix..'_Yaw',prefix..'_Pitch',prefix..'_Muzzle')
            aim:SetEnabled(self:IsEnabled())
            aim:SetPrecedence(10)
            aim:SetResetPoseTime(0)
            local ymin,ymax=self:GetTurretYawMinMax()
            local pmin,pmax=self:GetTurretPitchMinMax()
            aim:SetFiringArc(ymin,ymax,self:GetTurretYawSpeed(),pmin,pmax,self:GetTurretPitchSpeed())
            self.unit.Trash:Add(aim)
            table.insert(self.ATTEControllers,aim)
            self.ATTEChannels[prefix..'_Muzzle']=channel
        end
    end,
    AimManipulatorSetEnabled = function(self,enabled)
        Gun.AimManipulatorSetEnabled(self,enabled)
        for k,aim in self.ATTEControllers or {} do aim:SetEnabled(enabled) end
    end,
}

ATTE = Class(ExperimentalMobileUnit) {
    Weapons = {
        Main = Class(Gun) {},
        FrontVolley = Class(FrontVolley) {},
        RearLeft = Class(Gun) {},
        RearRight = Class(Gun) {},
    },
    OnStopBeingBuilt = function(self,builder,layer)
        ExperimentalMobileUnit.OnStopBeingBuilt(self,builder,layer)
        LOG('CloneWars AT-TE mount-test-6: heavy 3s / front four-barrel volley 0.46875s / independent rear 0.9375s')
    end,
}
TypeClass = ATTE
