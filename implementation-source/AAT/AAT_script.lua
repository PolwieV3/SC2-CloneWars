local MobileUnit = import('/lua/sim/MobileUnit.lua').MobileUnit
local DefaultProjectileWeapon = import('/lua/sim/DefaultWeapons.lua').DefaultProjectileWeapon
local HeavyBlaster = import('/lua/CloneWars/AATHeavyBlaster.lua')

local SideRange = 16

local function SideTargetInRange(weapon)
    local target = weapon:GetCurrentTargetPos()
    if not target then
        return false
    end
    local origin = weapon.unit:GetPosition()
    local x = target[1] - origin[1]
    local z = target[3] - origin[3]
    return x * x + z * z <= SideRange * SideRange
end

local SideBlaster = Class(DefaultProjectileWeapon) {
    PlayFxMuzzleSequence = function(self, muzzle)
        if SideTargetInRange(self) then
            DefaultProjectileWeapon.PlayFxMuzzleSequence(self, muzzle)
        end
    end,

    CreateProjectileAtMuzzle = function(self, muzzle)
        if SideTargetInRange(self) then
            return DefaultProjectileWeapon.CreateProjectileAtMuzzle(self, muzzle)
        end
    end,
}

AAT = Class(MobileUnit) {
    Weapons = {
        Main = Class(DefaultProjectileWeapon) {
            PlayFxMuzzleSequence = function(self, muzzle)
                HeavyBlaster.MuzzleFlash(self.unit, muzzle)
            end,
        },
        Left = Class(SideBlaster) {},
        Right = Class(SideBlaster) {},
    },
}

TypeClass = AAT
