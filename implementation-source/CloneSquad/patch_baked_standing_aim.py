"""Install a baked standing aim pose using the engine's unit mesh switch."""
import struct
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np

from patch_forward_walk_and_attack import MODEL, UNIT, WORK
from patch_shouldered_rifle import decode, rotate
from probe_squad_playback import paths, PROBE_SCRIPT, replace_once
import scm_v7

AIM_ID = "/units/clonewars/clonesquad/clonesquad_baked_aim_mesh"
CARRY_ID = "/units/clonewars/clonesquad/clonesquad_baked_carry_mesh"

MESH_SWITCH = f"""    SetSquadAimMesh = function(self, aiming)
        if self.SquadAimMesh == aiming then return end
        self.SquadAimMesh = aiming
        if self.Animator then
            self.Animator:Destroy()
            self.Animator = nil
        end
        self:SetMesh(aiming and '{AIM_ID}' or '{CARRY_ID}')
        if not aiming then
            self.Animator = CreateAnimator(self)
            self.Trash:Add(self.Animator)
        end
        self.SquadPose = nil
    end,

""".encode()


def bake(mesh_raw, animation):
    mesh = scm_v7.read(mesh_raw)
    clip, tracks = decode(animation)
    assert mesh["names"] == clip["names"]
    assert [row[24] for row in mesh["bones"]] == list(clip["parents"])
    result = bytearray(mesh_raw)
    header = mesh["header"]
    positions = []
    for index, (name, bone) in enumerate(zip(mesh["names"], mesh["bones"], strict=True)):
        parent = bone[24]
        key = tracks[name][0]
        origin = key[4:]
        # Muzzle offsets are local to their animated hands.
        if parent >= 0:
            parent_key = tracks[mesh["names"][parent]][0]
            origin = positions[parent] + rotate(parent_key[:4], origin)
        positions.append(origin)
        local = origin if parent < 0 else origin - positions[parent]
        offset = header[2] + index*scm_v7.BONE.size
        struct.pack_into("<3f", result, offset+48, *(-origin))
        struct.pack_into("<3f", result, offset+64, *local)

    vertices = np.array(mesh["vertices"], dtype=float)
    for index, name in enumerate(mesh["names"][:header[3]]):
        mask = vertices[:,16] == index
        old = -np.array(mesh["bones"][index][12:15])
        q = tracks[name][0,:4]
        vertices[mask,:3] = rotate(q, vertices[mask,:3]-old)+positions[index]
        for axis in (3,6,9):
            vertices[mask,axis:axis+3] = rotate(q, vertices[mask,axis:axis+3])
    for index, row in enumerate(vertices):
        scm_v7.VERTEX.pack_into(result, header[4]+index*scm_v7.VERTEX.size,
                               *row[:16], *map(int,row[16:]))
    check = scm_v7.read(result)
    assert check["indices"] == mesh["indices"] and check["names"] == mesh["names"]
    for soldier in range(1,6):
        hand = mesh["names"].index(f"C{soldier:02}_RightHand")
        muzzle = mesh["names"].index(f"Muzzle{soldier:02}")
        assert positions[muzzle][2] - positions[hand][2] > .2
    return bytes(result)


def main():
    base, _ = paths()
    backup = WORK / "backup-before-baked-aim" / base.name
    stage = base.with_suffix(".baked-stage")
    with ZipFile(base) as source:
        bp = source.read(UNIT)
        start = bp.index(b"Mesh = {") + len(b"Mesh = ")
        end = bp.index(b"\n},\nAnimationWalk",start)+2
        mesh = bp[start:end]
        assert mesh.startswith(b"{") and mesh.endswith(b"}")
        carry_path = f"{MODEL}_lod0.scm".encode()
        aim_path = f"{MODEL}_baked_aim_lod0"
        aim = bake(source.read(f"{MODEL}_lod0.win.scm"),source.read(f"{MODEL}_aim_r2.sca"))
        script = source.read(PROBE_SCRIPT)
        script = replace_once(script,b"    SetSquadPose = function",MESH_SWITCH+b"    SetSquadPose = function")
        script = replace_once(script,b"        local now = GetGameTimeSeconds()\n        if not self.SquadLoggedShot",
            b"        local now = GetGameTimeSeconds()\n        if not self.SquadWalking then self:SetSquadAimMesh(true) end\n        if not self.SquadLoggedShot")
        script = replace_once(script,b"            local pose = self.SquadPose\n            if self.SquadWalking then",
            b"""            if aiming and not self.SquadWalking then
                self:SetSquadAimMesh(true)
            elseif self.SquadAimMesh then
                self:SetSquadAimMesh(false)
            end
            local pose = self.SquadPose
            if self.SquadAimMesh then
                -- The mesh supplies the standing pose while combat is active.
            elseif self.SquadWalking then""")
        script = replace_once(script,b"shouldered rifle and upright gait revision loaded",b"baked standing aim revision loaded")
        updates = {PROBE_SCRIPT:script}
        for suffix in (".scm",".win.scm"):
            updates[aim_path+suffix] = aim
        for mesh_id, definition in ((CARRY_ID,mesh),
                                   (AIM_ID,replace_once(mesh,carry_path,(aim_path+".scm").encode()))):
            updates[f"{MODEL}_{mesh_id.rsplit('_baked_',1)[1]}.bp"] = (
                b"MeshBlueprint "+definition[:-1]+f'BlueprintId = "{mesh_id}",\n}}\n'.encode())
        with ZipFile(stage,"w",ZIP_DEFLATED) as out:
            for name in source.namelist():
                if name not in updates:
                    out.writestr(name,source.read(name))
            for name,data in updates.items():
                out.writestr(name,data)
        with ZipFile(stage) as check:
            assert check.testzip() is None
            assert all(check.read(name)==source.read(name) for name in source.namelist() if name not in updates)
            assert all(check.read(name)==data for name,data in updates.items())
    backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open("xb") as saved:
        saved.write(base.read_bytes())
    assert backup.read_bytes()==base.read_bytes()
    stage.replace(base)
    print("Installed baked standing aim mesh")


if __name__ == "__main__":
    main()
