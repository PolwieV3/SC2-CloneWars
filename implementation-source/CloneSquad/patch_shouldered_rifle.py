"""Rebuild the installed clone squad's rifle stance and upright gait."""
import math
import struct
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np

from patch_forward_walk_and_attack import MODEL, UNIT, WORK, sca101
from probe_squad_playback import paths, PROBE_SCRIPT, replace_once

UPPER = ("Spine2", "Head", "LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "LeftHand", "RightHand")


def unit(vector):
    return vector / np.linalg.norm(vector)


def mul(q, r):
    return np.r_[q[0]*r[0] - np.dot(q[1:], r[1:]),
                 q[0]*r[1:] + r[0]*q[1:] + np.cross(q[1:], r[1:])]


def rotate(q, v):
    return v + 2*np.cross(q[1:], np.cross(q[1:], v) + q[0]*v)


def rotation(a, b):
    a, b = unit(a), unit(b)
    return unit(np.r_[1 + np.dot(a, b), np.cross(a, b)])


def chain(pose, names, start, end):
    """Move two rigid segments, retaining the original elbow or knee plane."""
    upper, lower, tip = (pose[name] for name in names)
    a, b, c = (key[4:].copy() for key in (upper, lower, tip))
    first, second = np.linalg.norm(b-a), np.linalg.norm(c-b)
    direction = unit(end-start)
    distance = np.clip(np.linalg.norm(end-start), abs(first-second)+1e-5, first+second-1e-5)
    end = start + direction*distance
    along = (first*first + distance*distance - second*second)/(2*distance)
    plane = b-a - direction*np.dot(b-a, direction)
    mid = start + direction*along + unit(plane)*math.sqrt(max(0, first*first-along*along))
    upper[:4] = mul(rotation(b-a, mid-start), upper[:4])
    lower[:4] = mul(rotation(c-b, end-mid), lower[:4])
    upper[4:], lower[4:], tip[4:] = start, mid, end


def aim_pose(pose, muzzle, *, level_grip=False):
    right, left = (pose[name] for name in ("RightHand", "LeftHand"))
    # The mesh's boots point along +Z. Swing the held rifle and both grips
    # together so the barrel faces +Z and is nearly horizontal.
    barrel = rotate(right[:4], muzzle[4:])
    forward = unit(np.array([0., .025, 1.]))
    turn = rotation(barrel, forward)
    if level_grip:
        # Keep the rifle upright around its barrel axis as the two grips swing forward.
        up = np.array([0., 1., 0.])
        current_up = rotate(mul(turn, right[:4]), up)
        current_up = unit(current_up - forward*np.dot(current_up, forward))
        desired_up = unit(up - forward*np.dot(up, forward))
        angle = math.atan2(np.dot(forward, np.cross(current_up, desired_up)),
                           np.dot(current_up, desired_up))
        turn = mul(np.r_[math.cos(angle/2), forward*math.sin(angle/2)], turn)
    spacing = rotate(turn, left[4:]-right[4:])
    shoulder = pose["RightArm"][4:]
    head = pose["Head"][4:]
    anchor = np.array([shoulder[0]+.025, head[1]-.055, shoulder[2]+.105])
    if level_grip:
        anchor[1:] += [-.018, -.025]
    arms = {(side): (side+"Arm", side+"ForeArm", side+"Hand") for side in ("Right", "Left")}
    # Find the nearest pair of reachable grips without changing their spacing.
    for _ in range(14):
        for side, offset in (("Right", np.zeros(3)), ("Left", spacing)):
            a,b,c = (pose[name][4:] for name in arms[side])
            limit = .97*(np.linalg.norm(b-a) + np.linalg.norm(c-b))
            delta = anchor+offset-a
            if np.linalg.norm(delta) > limit:
                anchor += unit(delta)*limit-delta
    for side, hand, end in (("Right",right,anchor), ("Left",left,anchor+spacing)):
        names = arms[side]
        chain(pose, names, pose[names[0]][4:].copy(), end)
        assert np.linalg.norm(hand[4:]-end) < .008, "Both hands must reach the rifle"
        hand[:4] = mul(turn, hand[:4])
    assert rotate(right[:4], muzzle[4:])[2] > .95*np.linalg.norm(barrel)


def upright(pose):
    lift = np.array([0., .018, 0.])
    for side in ("Left", "Right"):
        names = (side+"UpLeg", side+"Leg", side+"Foot")
        chain(pose, names, pose[names[0]][4:] + lift, pose[names[2]][4:].copy())
    for name in UPPER:
        pose[name][4:] += lift


def decode(raw):
    clip = sca101.read(raw)
    return clip, {t["name"]: np.array(t["keys"])[:,1:] for t in clip["tracks"]}


def encode(raw, clip, keys):
    data = bytearray(raw)
    for track in clip["tracks"]:
        rows = keys[track["name"]]
        for i,row in enumerate(rows):
            row[:4] = unit(row[:4])
            if i and np.dot(row[:4], rows[i-1,:4]) < 0:
                row[:4] *= -1
            struct.pack_into("<7f", data, track["offset"]+32*i+4, *row)
    assert sca101.read(data)["names"] == clip["names"]
    return bytes(data)


def soldier_pose(keys, soldier, frame):
    prefix = f"C{soldier:02}_"
    return {name[len(prefix):]: rows[frame] for name, rows in keys.items() if name.startswith(prefix)}


def main():
    base, _ = paths()
    backup = WORK / "backup-before-shouldered-rifle" / base.name
    stage = base.with_suffix(".shoulder-stage")
    with ZipFile(base) as src:
        names = ["walk_steady","armed_walk_steady","idle","aim","raise","lower"] + [f"fire{i:02}" for i in range(1,6)]
        raw = {name:src.read(f"{MODEL}_{name}.sca") for name in names}
        decoded = {name:decode(data) for name,data in raw.items()}
        for soldier in range(1,6):
            muzzle = f"Muzzle{soldier:02}"
            for action in ("aim", "armed_walk_steady", *(f"fire{i:02}" for i in range(1,6))):
                clip, keys = decoded[action]
                for i in range(clip["frames"]):
                    aim_pose(soldier_pose(keys,soldier,i), keys[muzzle][i])
            for action in ("walk_steady", "armed_walk_steady"):
                clip, keys = decoded[action]
                for i in range(clip["frames"]):
                    upright(soldier_pose(keys,soldier,i))
        for action, a, b in (("raise","idle","aim"),("lower","aim","idle")):
            clip, keys = decoded[action]
            for bone, rows in keys.items():
                start, end = decoded[a][1][bone][0].copy(), decoded[b][1][bone][0].copy()
                if np.dot(start[:4],end[:4]) < 0:
                    end[:4] *= -1
                for i,row in enumerate(rows):
                    t = i/(len(rows)-1)
                    t = t*t*(3-2*t)
                    row[:] = (1-t)*start+t*end
        bp = src.read(UNIT)
        updates = {}
        for name in names:
            if name == "idle":
                continue
            fixed = encode(raw[name], *decoded[name])
            original = f"{MODEL}_{name}"
            new = original + "_r2"
            bp = replace_once(bp,(original+".sca").encode(),(new+".sca").encode())
            for ext in (".sca",".win.sca"):
                updates[new+ext] = fixed
        updates[UNIT] = bp
        script = src.read(PROBE_SCRIPT)
        updates[PROBE_SCRIPT] = replace_once(script,b"steady gait and aim revision loaded",b"shouldered rifle and upright gait revision loaded")
        with ZipFile(stage,"w",ZIP_DEFLATED) as out:
            for name in src.namelist():
                if name not in updates:
                    out.writestr(name,src.read(name))
            for name,data in updates.items():
                out.writestr(name,data)
        with ZipFile(stage) as check:
            assert check.testzip() is None
            assert all(check.read(name)==src.read(name) for name in src.namelist() if name not in updates)
            assert all(check.read(name)==data for name,data in updates.items())
    backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open("xb") as saved:
        saved.write(base.read_bytes())
    assert backup.read_bytes() == base.read_bytes()
    stage.replace(base)
    print("Installed upright gait and forward-facing rifle clips")


if __name__ == "__main__":
    main()
