local MobileUnit = import('/lua/sim/MobileUnit.lua').MobileUnit
local NativeTankGun = import('/lua/sim/DefaultWeapons.lua').DefaultProjectileWeapon
UTATTankGun = Class(NativeTankGun) {
    SetupTurret = function(self)
        NativeTankGun.SetupTurret(self)
        self.AimControl:SetResetPoseTime(0)
    end,
    CreateProjectileAtMuzzle = function(self,muzzle)
        -- Native aim/firing-arc checks are authoritative. Do not veto a native shot
        -- by comparing an instantaneous target point to an auxiliary visual probe.
        local projectile = NativeTankGun.CreateProjectileAtMuzzle(self,muzzle)
        if not self.UTATFirstShotResult then
            self.UTATFirstShotResult = true
            LOG('CloneWars UTAT firing-fix-8 '..muzzle..' projectile_created='..tostring(projectile != nil)..' damage='..tostring(self:GetBlueprint().Damage))
        end
        return projectile
    end,
}
UTAT = Class(MobileUnit) {
    Weapons = {
        UTATMainGun = Class(UTATTankGun) {},
        UTATSideLeft = Class(UTATTankGun) {},
        UTATSideRight = Class(UTATTankGun) {},
    },
    OnStopBeingBuilt = function(self,builder,layer)
        MobileUnit.OnStopBeingBuilt(self,builder,layer)
        LOG('CloneWars UTAT firing-fix-8: native projectile firing, roof75/sides30, limited arcs retained')
    end,
}
TypeClass = UTAT
