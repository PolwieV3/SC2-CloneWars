local ExperimentalMobileUnit = import('/lua/sim/ExperimentalMobileUnit.lua').ExperimentalMobileUnit
local DefaultBeamWeapon = import('/lua/sim/DefaultWeapons.lua').DefaultBeamWeapon
local NativeBeam = import('/lua/sim/defaultcollisionbeams.lua').ZapperCollisionBeam02
local CollisionBeam = import('/lua/sim/CollisionBeam.lua').CollisionBeam

-- Native collision checks deliver ten 375-damage installments. The per-discharge
-- budget also prevents an extra endpoint collision from exceeding one artillery round.
local SPHABeam = Class(NativeBeam) {
    OnEnable = function(self)
        self.RemainingDamage = 3750
        self.Installments = 0
        NativeBeam.OnEnable(self)
    end,
    DoDamage = function(self, instigator, damageData, targetEntity)
        if self.RemainingDamage <= 0 then return end
        local amount = math.min(damageData.DamageAmount or 0, self.RemainingDamage)
        if amount <= 0 then return end
        local pulse = {}
        for k,v in damageData do pulse[k] = v end
        pulse.DamageAmount = amount
        pulse.CriticalChance = pulse.CriticalChance or 0
        pulse.StunChance = pulse.StunChance or 0
        self.RemainingDamage = self.RemainingDamage - amount
        self.Installments = self.Installments + 1
        CollisionBeam.DoDamage(self, instigator, pulse, targetEntity)
        if self.Installments == 1 or self.RemainingDamage == 0 then
            LOG(string.format('SPHA-T beam-test-1 damage pulse=%d nominal=%.1f remaining=%.1f', self.Installments, amount, self.RemainingDamage))
        end
    end,
}
local Laser = Class(DefaultBeamWeapon) {
    BeamType = SPHABeam,
    SetupTurret = function(self)
        DefaultBeamWeapon.SetupTurret(self)
        if self.AimControl then self.AimControl:SetResetPoseTime(0) end
    end,
    PlayFxBeamStart = function(self, muzzle)
        DefaultBeamWeapon.PlayFxBeamStart(self, muzzle)
        LOG('SPHA-T beam-test-1 firing: two-second beam, total budget 3750, range95')
    end,
}
SPHA = Class(ExperimentalMobileUnit) {
    Weapons = { MainGun = Class(Laser) {} },
    OnStopBeingBuilt = function(self, builder, layer)
        ExperimentalMobileUnit.OnStopBeingBuilt(self, builder, layer)
        LOG('CloneWars SPHA-T beam-test-7: unit-local deployment watcher started')
        self:SetWeaponEnabledByLabel('MainGun', false)
        self:ForkThread(self.WatchDeployment)
    end,
    WatchDeployment = function(self)
        local plantedTicks = 0
        local gunEnabled = false
        while not self:IsDead() do
            if self:IsUnitState('Immobile') then
                plantedTicks = plantedTicks + 1
                if plantedTicks >= 15 and not gunEnabled then
                    self:SetWeaponEnabledByLabel('MainGun', true)
                    gunEnabled = true
                    LOG('SPHA-T beam-test-7: planted MainGun enabled')
                end
            else
                plantedTicks = 0
                if gunEnabled then
                    self:SetWeaponEnabledByLabel('MainGun', false)
                    gunEnabled = false
                    LOG('SPHA-T beam-test-7: mobile MainGun disabled')
                end
            end
            WaitSeconds(0.1)
        end
    end,
    OnMotionHorzEventChange = function(self, new, old)
        -- Native Deploy waits for unit.Animator. While planted, leave that
        -- animator untouched so movement idle cannot restart its animation.
        if self:IsUnitState('Immobile') then
            LOG('SPHA-T beam-test-7 planted motion event; deploy animator preserved')
            return
        end
        ExperimentalMobileUnit.OnMotionHorzEventChange(self, new, old)
    end,
}
TypeClass = SPHA
