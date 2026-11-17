"""Revise the Clone Squad gait and keep combat pose active between shots."""
from pathlib import Path
import struct
from zipfile import ZIP_DEFLATED, ZipFile

from patch_forward_walk_and_attack import MODEL, UNIT, WORK, sca101
from probe_squad_playback import paths, PROBE_SCRIPT, replace_once

UPPER_PARTS = ("Spine2", "Head", "Arm", "ForeArm", "Hand")


def steady_gait(raw):
    clip = sca101.read(raw)
    tracks = {t["name"]: t for t in clip["tracks"]}
    result = bytearray(raw)
    for name, track in tracks.items():
        if not name.startswith("C0"):
            continue
        soldier, part = name.split("_", 1)
        chest = tracks[soldier + "_Spine2"]["keys"]
        center_x = sum(k[5] for k in chest[:-1]) / (len(chest) - 1)
        mean_x = sum(k[5] for k in track["keys"][:-1]) / (len(chest) - 1)
        for i, key in enumerate(track["keys"]):
            is_upper = part.endswith(UPPER_PARTS)
            # Move the upper body together to preserve the two-handed carry.
            x = key[5] - 0.8 * ((chest[i][5] - center_x) if is_upper else (key[5] - mean_x))
            struct.pack_into("<f", result, track["offset"] + 32*i + 20, x)
    checked = sca101.read(result)
    assert checked["names"] == clip["names"]
    return bytes(result)


def main():
    base, _ = paths()
    backup = WORK / "backup-before-steady-gait" / base.name
    stage = base.with_suffix(".gait-stage")
    with ZipFile(base) as source:
        script = source.read(PROBE_SCRIPT)
        # Preserve the last shot beyond the normal interval, including a skipped shot.
        script = replace_once(script, b"now + 0.9", b"now + 1.85")
        script = replace_once(script, b"        MobileUnit.OnMotionHorzEventChange(self, new, old)\n        if new == 'Stopped' then\n            -- MobileUnit just restored its idle animation.\n            self.SquadPose = nil\n        end",
            b"""        local previous = self.Animator
        -- MobileUnit resets its animator to idle on Stopped. The squad thread owns pose transitions.
        self.Animator = nil
        MobileUnit.OnMotionHorzEventChange(self, new, old)
        self.Animator = previous""")
        script = replace_once(script, b"            if poseReports < 30 then", b"            if pose ~= 'idle' and pose ~= 'walk' and poseReports < 30 then")
        script = replace_once(script, b"        self.SquadCombatUntil = now + 1.85", b"""        if not self.SquadLoggedShot then
            self.SquadLoggedShot = true
            LOG('Clone Squad pose revision: first shot, walking='..tostring(self.SquadWalking)..' pose='..tostring(self.SquadPose))
        end
        self.SquadCombatUntil = now + 1.85""")
        script = replace_once(script, b"        if not self.SquadWalking and self.Animator then",
            b"""        if self.SquadWalking then
            self:SetSquadPose('armed walk', self:GetBlueprint().Display.AnimationSquadArmedWalk, true, false)
        elseif self.Animator then""")
        script = replace_once(script, b"display.AnimationWalk, true, true)", b"display.AnimationWalk, true, false)")
        # Remove the test-only displaced clone and its sampling thread.
        start = script.index(b"        if not SquadProbeSampled")
        stop = script.index(b"    end,", start)
        script = script[:start] + script[stop:]
        start = script.index(b"    SampleSquadBones = function")
        stop = script.index(b"    Weapons =", start)
        script = script[:start] + script[stop:]
        script = replace_once(script, b"local SquadProbeSampled = false\n", b"")
        script = replace_once(script, b"unique script loaded", b"steady gait and aim revision loaded")

        bp = replace_once(source.read(UNIT), b"_probe_idle.sca", b"_idle.sca")
        updates = {PROBE_SCRIPT: script}
        for stance in ("walk", "armed_walk"):
            old = MODEL + "_" + stance
            new = old + "_steady"
            bp = replace_once(bp, (old + ".sca").encode(), (new + ".sca").encode())
            raw = steady_gait(source.read(old + ".sca"))
            for extension in (".sca", ".win.sca"):
                updates[new + extension] = raw
        updates[UNIT] = bp
        remainders = set(source.namelist()) - updates.keys()
        with ZipFile(stage, "w", ZIP_DEFLATED) as target:
            for name in sorted(remainders):
                target.writestr(name, source.read(name))
            for name, raw in updates.items():
                target.writestr(name, raw)
        with ZipFile(stage) as target:
            assert target.testzip() is None
            assert all(target.read(name) == source.read(name) for name in remainders)
            assert all(target.read(name) == raw for name, raw in updates.items())
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open("xb") as output:
        output.write(base.read_bytes())
    assert backup.read_bytes() == base.read_bytes()
    stage.replace(base)
    print("Installed steady gait and combat stance revision")


if __name__ == "__main__":
    main()
