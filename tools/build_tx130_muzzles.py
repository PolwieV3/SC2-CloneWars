"""Build and stage a reversible muzzle-position patch for the current TX-130."""
from pathlib import Path
import re
import struct
from zipfile import ZIP_DEFLATED, ZipFile

import scm_v7

ROOT = Path(__file__).resolve().parents[1]
GAME_DATA = ROOT / "local/dev-game/gamedata"
MODEL = GAME_DATA / "zz_SC2_CloneWars_TX130_Model.scd"
PATCH = "z" * 80 + "_SC2_CloneWars_TX130_Muzzles_R1.scd"
MESH_DIR = "units/CloneWars/TX130"
MESH_ID = "/units/clonewars/tx130/tx130_muzzles_r1_mesh"
# Keep the stock two- and three-slot racks. The third upgraded slot
# repeats the right muzzle because the visible tank has two barrels.
MUZZLES = {
    "T01_B02_Muzzle01": 1,
    "T01_B02_Muzzle02": -1,
    "T01_B03_Muzzle01": -1,  # Upgraded weapon's aim reference.
    "T01_B04_Muzzle01": -1,
    "T01_B04_Muzzle02": 1,
    "T01_B04_Muzzle03": 1,
}


def transform_point(matrix, point):
    return tuple(
        matrix[12 + axis] + sum(matrix[4 * i + axis] * point[i] for i in range(3))
        for axis in range(3)
    )


def move_muzzles(raw):
    mesh = scm_v7.read(raw)
    barrel = mesh["names"].index("T01_Barrel01")
    vertices = [v for v in mesh["vertices"] if v[16] == barrel]
    front = max(v[2] for v in vertices)
    tips = {}
    for side in (-1, 1):
        rim = [v for v in vertices if side * v[0] > 0 and v[2] >= front - 0.02]
        x, y = [(min(v[i] for v in rim) + max(v[i] for v in rim)) / 2 for i in range(2)]
        if not (7.2 < side * x < 7.5 and 6.5 < y < 6.9 and 8.3 < front < 8.4):
            raise ValueError("Barrel geometry differs from the current TX-130 model")
        tips[side] = (x, y, front + 0.05)

    patched = bytearray(raw)
    for name, side in MUZZLES.items():
        index = mesh["names"].index(name)
        row = mesh["bones"][index]
        if index < mesh["header"][3] or any(b[24] == index for b in mesh["bones"]):
            raise ValueError(f"{name} must be an unskinned leaf bone")
        parent = mesh["bones"][row[24]]
        # Recover the original world origin from the inverse bind transform.
        world_origin = tuple(
            -sum(row[4 * i + axis] * row[12 + axis] for axis in range(3))
            for i in range(3)
        )
        original_local = transform_point(parent, world_origin)
        if max(abs(a - b) for a, b in zip(original_local, row[16:19])) > 0.002:
            raise ValueError(f"Unexpected bind transform for {name}")
        tip = tips[side]
        offset = mesh["header"][2] + index * scm_v7.BONE.size
        inverse_translation = tuple(
            -sum(row[4 * i + axis] * tip[i] for i in range(3)) for axis in range(3)
        )
        struct.pack_into("<3f", patched, offset + 48, *inverse_translation)
        struct.pack_into("<3f", patched, offset + 64, *transform_point(parent, tip))

    result = scm_v7.read(patched)
    for index, name in enumerate(mesh["names"]):
        before, after = mesh["bones"][index], result["bones"][index]
        if name in MUZZLES:
            tip = tips[MUZZLES[name]]
            if max(map(abs, transform_point(after, tip))) > 1e-5:
                raise ValueError(f"Incorrect inverse bind for {name}")
            parent = result["bones"][after[24]]
            if max(abs(a - b) for a, b in zip(transform_point(parent, tip), after[16:19])) > 1e-5:
                raise ValueError(f"Incorrect local position for {name}")
        elif before != after:
            raise ValueError(f"Unexpected bone change for {name}")
    if patched[mesh["header"][4]:] != raw[mesh["header"][4]:]:
        raise ValueError("Mesh geometry changed")
    return bytes(patched)


def main():
    payload = {}
    with ZipFile(MODEL) as source:
        blueprint = source.read(f"{MESH_DIR}/TX130_mesh.bp").decode()
        blueprint = blueprint.replace("/units/clonewars/tx130/tx130_mesh", MESH_ID)
        for lod in range(3):
            filename = f"UUL0101_lod{lod}"
            path = f"{MESH_DIR}/{filename}_muzzles_r1"
            original = next(
                name for name in source.namelist()
                if name.lower() == f"{MESH_DIR}/{filename}.win.scm".lower()
            )
            fixed = move_muzzles(source.read(original))
            payload[path + ".win.scm"] = fixed
            payload[path + ".scm"] = fixed
            blueprint, count = re.subn(
                re.escape(f"/{MESH_DIR}/{filename}.scm"),
                f"/{path}.scm", blueprint, flags=re.IGNORECASE,
            )
            if count != 1:
                raise ValueError(f"Expected exactly one mesh reference for LOD {lod}")

    payload[f"{MESH_DIR}/TX130_Muzzles_R1_mesh.bp"] = blueprint.encode()
    merge = f"""UnitBlueprint {{
    Merge = true,
    BlueprintId = 'uul0101',
    Display = {{ MeshBlueprint = '{MESH_ID}' }},
}}
""".encode()
    for prefix in ("", "mods/DLC1/base/", "mods/DLC1/shadow/"):
        payload[prefix + "units/" + "z" * 80 + "_tx130_muzzles_r1_unit.bp"] = merge

    target = GAME_DATA / PATCH
    temporary = target.with_suffix(".tmp")
    with ZipFile(temporary, "w", ZIP_DEFLATED) as package:
        for name, contents in sorted(payload.items()):
            package.writestr(name, contents)
    with ZipFile(temporary) as package:
        if package.testzip() or any(package.read(n) != data for n, data in payload.items()):
            raise ValueError("TX-130 muzzle archive failed verification")
    temporary.replace(target)
    print(f"Installed {target.name} ({len(payload)} entries)")


if __name__ == "__main__":
    main()
