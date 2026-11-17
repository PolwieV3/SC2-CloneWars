"""Refine the standing rifle grip, range and aim point on the live squad package."""
import re
from zipfile import ZIP_DEFLATED, ZipFile

from patch_baked_standing_aim import bake
from patch_forward_walk_and_attack import MODEL, UNIT, WORK
from patch_shouldered_rifle import aim_pose, decode, encode, soldier_pose
from probe_squad_playback import paths, PROBE_SCRIPT, replace_once

OLD_TARGET = b"""        local targetY = targetPosition[2]
        if target then
            local baseY = target:GetPosition()[2]
            local height = target:GetBlueprint().SizeY or 0.5
            if targetY < baseY + 0.10 then targetY = baseY + math.max(0.13, height * 0.32) end
        end"""

TARGET = b"""        local targetY = targetPosition[2]
        if target and not target:IsInCategory('AIR') then
            local center = target:GetPosition()
            local bp = target:GetBlueprint()
            local height = bp.SizeY or 0.5
            -- Aim inside the target's vertical extent instead of imposing a
            -- fixed minimum lift that can overshoot short targets.
            targetPosition = center
            targetY = center[2] + height * 0.38
        end
        if not self.unit.SquadWalking then
            self.unit:SetSquadAimMesh(true)
        end"""


def main():
    base, _ = paths()
    backup = WORK / "backup-before-grip-and-range" / base.name
    stage = base.with_suffix(".grip-stage")
    with ZipFile(base) as source:
        idle_aim = source.read(f"{MODEL}_aim.sca")
        clip, keys = decode(idle_aim)
        for soldier in range(1, 6):
            muzzle = f"Muzzle{soldier:02}"
            for i in range(clip["frames"]):
                aim_pose(soldier_pose(keys, soldier, i), keys[muzzle][i], level_grip=True)
        aim = bake(source.read(f"{MODEL}_lod0.win.scm"), encode(idle_aim, clip, keys))
        mesh = f"{MODEL}_baked_aim_lod0"
        blueprint = source.read(UNIT)
        blueprint, count = re.subn(rb"MaxRadius = 15,", b"MaxRadius = 17.25,", blueprint)
        assert count == 1
        script = replace_once(source.read(PROBE_SCRIPT), OLD_TARGET, TARGET)
        script = replace_once(script, b"not target:IsInCategory('AIR')",
                              b"not EntityCategoryContains(categories.AIR, target)")
        updates = {UNIT: blueprint, PROBE_SCRIPT: script,
                   mesh+".scm": aim, mesh+".win.scm": aim}
        with ZipFile(stage, "w", ZIP_DEFLATED) as out:
            assert updates.keys() <= set(source.namelist())
            for name in source.namelist():
                out.writestr(name, updates[name] if name in updates else source.read(name))
        with ZipFile(stage) as check:
            assert check.testzip() is None
            assert all(check.read(name) == data for name, data in updates.items())
            assert all(check.read(name) == source.read(name) for name in source.namelist() if name not in updates)
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open("xb") as saved:
        saved.write(base.read_bytes())
    assert backup.read_bytes() == base.read_bytes()
    stage.replace(base)
    print("Installed level rifle grip, proportional target aim and range 17.25.")


if __name__ == "__main__":
    main()
