"""Install or remove the reversible Clone Squad playback diagnostic."""
from pathlib import Path
from shutil import copy2
import math
import struct
import sys
from zipfile import ZIP_DEFLATED, ZipFile

from patch_forward_walk_and_attack import MODEL, ROOT, UNIT, WORK, sca101

GAME = ROOT / "local/dev-game/gamedata"
PROBE = GAME / ("z" * 83 + "_SC2_CloneWars_CloneSquad_PlaybackProbe.scd")
CLIP = MODEL + "_probe_idle"
SCRIPT = MODEL + "_script.lua"
PROBE_SCRIPT = MODEL + "_probe_script.lua"

SAMPLE = b"""        -- Read bone transforms from the sim, independent of camera angle.
        for sample = 1, 10 do
            if self:IsDead() then return end
            local a = self:GetPosition('C01_Head')
            local b = self:GetPosition('C02_Head')
            local dx, dy, dz = a[1]-b[1], a[2]-b[2], a[3]-b[3]
            LOG('Clone Squad probe: head separation squared='..tostring(dx*dx+dy*dy+dz*dz))
            WaitTicks(4)
        end
"""


def probe_animation(raw):
    before = sca101.read(raw)
    changed = bytearray(raw)
    for track in before["tracks"]:
        if track["name"].startswith("C01_"):
            for i, key in enumerate(track["keys"]):
                # Translate all skinned parts of trooper 1 together. Its muzzle
                # is parented to the hand and picks up the offset from it.
                shift = 0.65 * (1 - math.cos(math.tau * i / (len(track["keys"]) - 1)))
                struct.pack_into("<f", changed, track["offset"] + 32*i + 20, key[5] - shift)
    after = sca101.read(changed)
    assert after["names"] == before["names"] and after["parents"] == before["parents"]
    for a, b in zip(before["tracks"], after["tracks"], strict=True):
        if a["name"].startswith("C01_"):
            assert min(y[5] - x[5] for x, y in zip(a["keys"], b["keys"], strict=True)) < -1.25
        else:
            assert a == b
    return bytes(changed)


def replace_once(raw, old, new):
    if raw.count(old) != 1:
        raise ValueError(f"Unexpected current squad source around {old!r}")
    return raw.replace(old, new)


def paths():
    base, = GAME.glob("*_CloneSquad_Test.scd")
    return base, WORK / "backup-before-playback-probe" / base.name


def install():
    base, backup = paths()
    stage = base.with_suffix(".probe-stage")
    with ZipFile(base) as source:
        idle = probe_animation(source.read(MODEL + "_idle.sca"))
        script = replace_once(
            source.read(SCRIPT),
            b"        self:ForkThread(self.UpdateSquadPose)",
            b"""        self:ForkThread(self.UpdateSquadPose)
        if not SquadProbeSampled and self:GetArmy() == 1 then
            SquadProbeSampled = true
            LOG('Clone Squad probe: sampling first army 1 squad')
            self:ForkThread(self.SampleSquadBones)
        end""",
        )
        script = replace_once(script, b"CloneSquad = Class(MobileUnit) {",
                              b"local SquadProbeSampled = false\nlocal poseReports = 0\nCloneSquad = Class(MobileUnit) {\n    SampleSquadBones = function(self)\n" + SAMPLE + b"    end,")
        script = replace_once(script, b"            self.SquadPose = pose", b"""            self.SquadPose = pose
            if poseReports < 30 then
                poseReports = poseReports + 1
                LOG('Clone Squad probe: pose='..pose..' clip='..clip)
            end""")
        script = b"LOG('Clone Squad probe: unique script loaded')\n" + script
        blueprint = replace_once(source.read(UNIT), (MODEL + "_idle.sca").encode(), (CLIP + ".sca").encode())
        blueprint = replace_once(blueprint, SCRIPT.encode(), PROBE_SCRIPT.encode())

        payload = {PROBE_SCRIPT: script, UNIT: blueprint, CLIP + ".sca": idle, CLIP + ".win.sca": idle}
        with ZipFile(stage, "w", ZIP_DEFLATED) as out:
            for path in source.namelist():
                if path not in payload:
                    out.writestr(path, source.read(path))
            for path, raw in payload.items():
                out.writestr(path, raw)
        with ZipFile(stage) as check:
            assert check.testzip() is None
            assert all(check.read(path) == raw for path, raw in payload.items())
            assert all(check.read(path) == source.read(path) for path in source.namelist() if path not in payload)
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open("xb") as saved:
        saved.write(base.read_bytes())
    assert backup.read_bytes() == base.read_bytes()
    stage.replace(base)
    PROBE.unlink(missing_ok=True)
    print("Installed playback probe directly in the Clone Squad test archive")


def remove():
    base, backup = paths()
    if backup.is_file():
        with ZipFile(base) as current:
            if PROBE_SCRIPT not in current.namelist():
                raise ValueError("Current squad archive does not contain the probe")
        stage = base.with_suffix(".restore-stage")
        copy2(backup, stage)
        stage.replace(base)
        backup.unlink()
    PROBE.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--remove"]:
        remove()
    else:
        install()
