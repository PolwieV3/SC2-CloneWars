local Base = import('/units/UEF/UUL0105/UUL0105_script.lua').UUL0105
local DefaultBeamWeapon = import('/lua/sim/DefaultWeapons.lua').DefaultBeamWeapon
local Beams = import('/lua/sim/defaultcollisionbeams.lua')
UTAAInterceptor = Class(DefaultBeamWeapon) {
    BeamType = Beams.ZapperCollisionBeam02,
    CreateProjectileAtMuzzle = function(self,muzzle)
        if not self.UTAAFirstIntercept then
            self.UTAAFirstIntercept = true
            LOG('CloneWars UTAA dual-role-test-1: secondary interceptor fired from '..muzzle)
        end
        return DefaultBeamWeapon.CreateProjectileAtMuzzle(self,muzzle)
    end,
}
UTAA = Class(Base) {
    Weapons = {
        AntiAir01 = Class(Base.Weapons.AntiAir01) {},
        Turret02 = Class(UTAAInterceptor) {},
    },
    OnStopBeingBuilt = function(self,builder,layer)
        Base.OnStopBeingBuilt(self,builder,layer)
        self:ShowBone('Turret02',true)
        LOG('CloneWars UTAA dual-role-test-1: native AA retained; secondary anti-missile gun active')
    end,
}
TypeClass = UTAA
