"""Patch the installed Clone Squad test archive, preserving a rollback copy."""
from copy import copy
from pathlib import Path
import shutil
import struct
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "implementation-source/shared-pipeline"))
import sca101

WORK = ROOT / "local/infantry-prototype"
MODEL = "units/CloneWars/CloneSquad/CloneSquad"
UNIT = "mods/DLC1/base/Units/UEF/UUL0198/UUL0198_unit.bp"
UPPER = {
    "Spine2", "Head", "LeftArm", "RightArm", "LeftForeArm",
    "RightForeArm", "LeftHand", "RightHand",
}

ANIMATION_SCRIPT = b"""    OnStopBeingBuilt = function(self, builder, layer)
        self.MoveAnimDisabled = true
        MobileUnit.OnStopBeingBuilt(self, builder, layer)
        self:ForkThread(self.UpdateSquadPose)
    end,

    OnMotionHorzEventChange = function(self, new, old)
        MobileUnit.OnMotionHorzEventChange(self, new, old)
        if new == 'Stopped' then
            -- MobileUnit just restored its idle animation.
            self.SquadPose = nil
        end
    end,

    SetSquadPose = function(self, pose, clip, loop, walking)
        if self.Animator and self.SquadPose ~= pose then
            self.Animator:PlayAnim(clip, loop, walking)
            self.Animator:SetRate(1)
            self.SquadPose = pose
        end
    end,

    PlaySquadRecoil = function(self, shooter)
        local now = GetGameTimeSeconds()
        self.SquadCombatUntil = now + 0.9
        if not self.SquadWalking and self.Animator then
            self.SquadRecoilUntil = now + 0.26
            self.SquadPose = nil
            self:SetSquadPose('fire', self:GetBlueprint().Display.AnimationSquadFire[shooter], false, false)
        end
    end,

    UpdateSquadPose = function(self)
        local weapon = self:GetWeapon(1)
        local display = self:GetBlueprint().Display
        local position = self:GetPosition()
        local lastX, lastZ = position[1], position[3]
        local transitionUntil = 0
        while not self:IsDead() do
            position = self:GetPosition()
            local dx, dz = position[1] - lastX, position[3] - lastZ
            lastX, lastZ = position[1], position[3]
            self.SquadWalking = dx*dx + dz*dz > 0.000025
            local now = GetGameTimeSeconds()
            local aiming = (weapon and weapon:GetCurrentTargetPos()) or now < (self.SquadCombatUntil or 0)
            local pose = self.SquadPose
            if self.SquadWalking then
                self:SetSquadPose(aiming and 'armed walk' or 'walk',
                    aiming and display.AnimationSquadArmedWalk or display.AnimationWalk, true, true)
            elseif not (pose == 'fire' and now < (self.SquadRecoilUntil or 0)) then
                if aiming then
                    if pose == 'fire' or pose == 'armed walk' or (pose == 'raise' and now >= transitionUntil) then
                        self:SetSquadPose('aim', display.AnimationSquadAim, true, false)
                    elseif pose ~= 'aim' and pose ~= 'raise' then
                        self:SetSquadPose('raise', display.AnimationSquadRaise, false, false)
                        transitionUntil = now + 0.28
                    end
                elseif pose == 'aim' or pose == 'fire' or pose == 'raise' or pose == 'armed walk' then
                    self:SetSquadPose('lower', display.AnimationSquadLower, false, false)
                    transitionUntil = now + 0.35
                elseif pose ~= 'lower' or now >= transitionUntil then
                    self:SetSquadPose('idle', display.AnimationIdle, true, false)
                end
            end
            WaitTicks(1)
        end
    end,
}
TypeClass = CloneSquad
"""


def reverse_walk(raw, aim_raw):
    walk = sca101.read(raw)
    aim = sca101.read(aim_raw)
    assert walk["names"] == aim["names"] and walk["parents"] == aim["parents"]
    forward = bytearray(raw)
    armed = bytearray(raw)
    tracks = {track["name"]: track["keys"] for track in walk["tracks"]}
    for track, aimed in zip(walk["tracks"], aim["tracks"], strict=True):
        name = track["name"]
        trooper, _, part = name.partition("_")
        keys = track["keys"]
        for i, (time, *_) in enumerate(keys):
            frame = len(keys) - 1 - i
            values = keys[frame][1:]
            offset = track["offset"] + 32 * i
            struct.pack_into("<8f", forward, offset, time, *values)
            if part in UPPER:
                chest = tracks[trooper + "_Spine2"]
                # Carry the aimed upper body with the walking chest's vertical motion.
                bob = chest[frame][6] - (max(k[6] for k in chest) + min(k[6] for k in chest)) / 2
                qw, qx, qy, qz, x, y, z = aimed["keys"][0][1:]
                values = (qw, qx, qy, qz, x, y + bob, z)
            struct.pack_into("<8f", armed, offset, time, *values)

    for data in (forward, armed):
        parsed = sca101.read(data)
        assert parsed["names"] == walk["names"] and parsed["parents"] == walk["parents"]
        for track in parsed["tracks"]:
            a, b = track["keys"][0][1:], track["keys"][-1][1:]
            assert max(abs(x - y) for x, y in zip(a, b)) < 1e-5
    forward_tracks = sca101.read(forward)["tracks"]
    armed_tracks = sca101.read(armed)["tracks"]
    for original, normal, combat in zip(walk["tracks"], forward_tracks, armed_tracks, strict=True):
        assert [k[1:] for k in normal["keys"]] == [k[1:] for k in reversed(original["keys"])]
        if original["name"].partition("_")[2] not in UPPER:
            assert normal["keys"] == combat["keys"]
    return bytes(forward), bytes(armed)


def main():
    package, = (ROOT / "local/dev-game/gamedata").glob("*_CloneSquad_Test.scd")
    backup = WORK / "backup-before-forward-walk-and-attack" / package.name
    if backup.exists():
        raise SystemExit(f"Rollback copy already exists at {backup}")
    stage = package.with_suffix(".pose-stage")
    with ZipFile(package) as source:
        updates = {}
        original = source.read(MODEL + "_script.lua")
        script = original[:original.index(b"    OnStopBeingBuilt = function")] + ANIMATION_SCRIPT
        script = script.replace(b"local recoilBones = " + original.split(b"local recoilBones = ", 1)[1].splitlines()[0] + b"\nlocal recoilReports = 0\n", b"")
        updates[MODEL + "_script.lua"] = script

        bp = source.read(UNIT)
        marker = b"AnimationWalkRate = 1,"
        assert bp.count(marker) == 1
        updates[UNIT] = bp.replace(marker, marker + f'\nAnimationSquadArmedWalk = "/{MODEL}_armed_walk.sca",'.encode())
        assert source.read(MODEL + "_walk.sca") == source.read(MODEL + "_walk.win.sca")
        forward, armed = reverse_walk(source.read(MODEL + "_walk.sca"), source.read(MODEL + "_aim.sca"))
        for suffix in ("sca", "win.sca"):
            updates[f"{MODEL}_walk.{suffix}"] = forward
            updates[f"{MODEL}_armed_walk.{suffix}"] = armed

        with ZipFile(stage, "w") as target:
            for entry in source.infolist():
                target.writestr(copy(entry), updates.get(entry.filename, source.read(entry)))
            for name in updates.keys() - set(source.namelist()):
                target.writestr(name, updates[name], compress_type=8)
        with ZipFile(stage) as target:
            assert target.testzip() is None
            assert set(target.namelist()) == set(source.namelist()) | updates.keys()
            assert all(target.read(name) == data for name, data in updates.items())
            assert all(target.read(name) == source.read(name) for name in source.namelist() if name not in updates)

    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(package, backup)
    assert backup.read_bytes() == package.read_bytes()
    stage.replace(package)
    print("Installed forward walk, armed walk and standing attack playback.")


if __name__ == "__main__":
    main()
