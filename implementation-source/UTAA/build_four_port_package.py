"""Build the reversible UT-AA four-port revision; does not install or edit inputs."""
from pathlib import Path
import copy
import hashlib
import json
import math
import struct
import sys
import zipfile

W = Path(__file__).resolve().parent
ROOT = W.parents[1]
OUT = ROOT / "outputs/UT-AA"
sys.path.insert(0, str(W / "pipeline"))
import scm_v7
import sca101
from bp_literals import LiteralTable, merge, differences

BACKUP = OUT / "backups/2026-10-20-four-port-restore/zz_SC2_CloneWars_UTAA_Model.scd"
REFERENCE = W / "native/units.scd/units/UEF/UUL0105/UUL0105_LOD0.win.scm"
GEOMETRY = W / "four-port-geometry.json"
BASE_BP = W / "native/uncompiled_lua.scd/uncompiled/Units/UEF/UUL0105/UUL0105_unit.bp"
DLC_BP = W / "native/z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUL0105/UUL0105_unit.bp"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def lua(value, indent=0):
    if isinstance(value, dict):
        return "{\n" + "".join(
            " " * (indent + 4)
            + (f"[{key}]" if isinstance(key, int) else key)
            + " = " + lua(item, indent + 4) + ",\n"
            for key, item in value.items()
        ) + " " * indent + "}"
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "nil"
    return str(value)


def serialize_extended_reference(original, helpers):
    """Append non-skinned helpers while preserving all original bone semantics."""
    model = scm_v7.read(original)
    h = list(model["header"])
    names = list(model["names"])
    bones = [list(row) for row in model["bones"]]
    affected = set(range(1,13)) | set(range(16,24))
    for index in affected:
        row = bones[index]
        for axis in range(3):
            row[12+axis] -= row[4+axis]*1.5
    bones[1][17] += 1.5
    expected_bones = copy.deepcopy(bones)
    assert len(names) == 26 and h[3] == 16
    rack = names.index("T01_Rack01")
    template = list(bones[names.index("T01_B01_Muzzle01")])
    for helper in helpers:
        assert helper["name"] not in names
        row = template.copy()
        position = helper["world"]
        # Inverse bind is column-major: preserve native muzzle inverse rotation.
        for axis in range(3):
            row[12 + axis] = -sum(row[column * 4 + axis] * position[column] for column in range(3))
        row[16:19] = helper["rack_local"]
        row[19:23] = template[19:23]
        row[24] = rack
        names.append(helper["name"])
        bones.append(row)
    assert len(set(names)) == 30
    h[11] = len(bones)
    buffer = bytearray(original[:scm_v7.HEADER.size])
    scm_v7.section(buffer, b"NAME")
    for name, row in zip(names, bones):
        row[23] = len(buffer)
        buffer.extend(name.encode("ascii") + b"\0")
    h[2] = scm_v7.section(buffer, b"SKEL")
    for row in bones:
        buffer.extend(scm_v7.BONE.pack(*row))
    h[4] = scm_v7.section(buffer, b"VTXL")
    for row in model["vertices"]:
        buffer.extend(scm_v7.VERTEX.pack(*row))
    h[7] = scm_v7.section(buffer, b"TRIS")
    buffer.extend(struct.pack(f"<{len(model['indices'])}H", *model["indices"]))
    h[5] = scm_v7.section(buffer, b"XTRA")
    buffer.extend(model["extra"])
    h[9] = scm_v7.section(buffer, b"INFO")
    buffer.extend(model["info"])
    scm_v7.section(buffer, b"MNAM")
    material_offsets = []
    for name in model["material_names"]:
        material_offsets.append(len(buffer))
        buffer.extend(name.encode("ascii") + b"\0")
    h[12] = scm_v7.section(buffer, b"MATS")
    for offset, material in zip(material_offsets, model["materials"]):
        buffer.extend(scm_v7.MATERIAL.pack(offset, *material[1:]))
    scm_v7.HEADER.pack_into(buffer, 0, *h)
    raw = bytes(buffer)
    check = scm_v7.read(raw)
    assert check["names"][:26] == model["names"]
    assert check["header"][3] == 16 and check["header"][11] == 30
    for expected, new in zip(expected_bones, check["bones"][:26]):
        rounded = scm_v7.BONE.unpack(scm_v7.BONE.pack(*expected))
        assert rounded[:23] == new[:23] and rounded[24:] == new[24:]
    assert check["vertices"] == model["vertices"]
    assert check["indices"] == model["indices"]
    assert check["extra"] == model["extra"]
    assert check["info"] == model["info"]
    assert scm_v7.write(raw, check["vertices"], check["indices"],
                        [m[1:] for m in check["materials"]], check["extra"]) == raw
    return raw


def main():
    source_package = BACKUP.read_bytes()
    backup_hash = sha(source_package)
    geometry_raw = GEOMETRY.read_bytes()
    geometry = json.loads(geometry_raw)
    assert geometry["revision"] == "four-port-test-2"
    helpers = geometry["ports"]
    assert len(helpers) == 4
    helper_names = [p["name"] for p in helpers]
    assert geometry["banks"] == [helper_names, helper_names]
    original = REFERENCE.read_bytes()
    reference = serialize_extended_reference(original, helpers)
    old = scm_v7.read(original)
    extended = scm_v7.read(reference)
    vertices = []
    indices = []
    # Retain previous package's two-sided policy for this bounded correction.
    for reverse in (False, True):
        for triangle in geometry["triangles"]:
            assert len(triangle) == 3
            order = (triangle[0], triangle[2], triangle[1]) if reverse else triangle
            for source_row in order:
                row = list(source_row)
                assert len(row) == 20 and 0 <= row[16] < 16
                if reverse:
                    row[3:6] = [-value for value in row[3:6]]
                    row[9:12] = [-value for value in row[9:12]]
                indices.append(len(vertices))
                vertices.append(row)
    assert len(vertices) <= 65535
    mesh_raw = scm_v7.write(reference, vertices, indices,
                            [(len(indices) // 3, 0, 0, len(vertices)),
                             (0, len(indices), len(vertices), 0)])
    model = scm_v7.read(mesh_raw)
    assert model["bones"] == extended["bones"]
    assert model["names"] == extended["names"]
    helper_checks = []
    for helper, row in zip(helpers, model["bones"][26:]):
        # The helper's inverse bind maps its authored world origin to zero.
        residual = [
            sum(row[column * 4 + axis] * helper["world"][column] for column in range(3))
            + row[12 + axis] for axis in range(3)
        ]
        error = max(abs(value) for value in residual)
        assert error < 2e-6
        assert row[24] == old["names"].index("T01_Rack01")
        assert max(abs(row[16 + axis] - helper["rack_local"][axis]) for axis in range(3)) < 1e-6
        assert row[19:23] == old["bones"][16][19:23]
        helper_checks.append({
            "name": helper["name"], "parent": "T01_Rack01",
            "rack_local": list(row[16:19]), "world": helper["world"],
            "inverse_bind_origin_error": error,
            "native_muzzle_local_rotation_preserved": True,
            "skinned": False,
        })
    with zipfile.ZipFile(BACKUP) as archive:
        assert archive.testzip() is None
        payload = {name: archive.read(name) for name in archive.namelist()}
    old_payload = dict(payload)
    animation_checks = []
    for filename in ('UUL0105_AOpen01.win.sca','UUL0105_Aland01.win.sca'):
        original_clip = (REFERENCE.parent / filename).read_bytes()
        clip = sca101.read(original_clip)
        assert clip['names'] == old['names']
        data = bytearray(original_clip)
        track = clip['tracks'][1]
        assert track['name'] == 'Turret01'
        for j,key in enumerate(track['keys']):
            struct.pack_into('<f',data,track['offset']+j*32+24,key[6]+1.5)
        converted = sca101.read(bytes(data))
        for index,(a,b) in enumerate(zip(clip['tracks'],converted['tracks'])):
            for ak,bk in zip(a['keys'],b['keys']):
                assert all(x==y for k,(x,y) in enumerate(zip(ak,bk)) if not(index==1 and k==6))
                if index==1: assert abs(bk[6]-ak[6]-1.5)<1e-6
        for name in (filename, filename.replace('.win.sca','.sca')):
            payload['units/UEF/UUL0105/'+name] = bytes(data)
        animation_checks.append({'file':filename,'frames':clip['frames'],'duration':clip['duration'],
            'only_change':'Turret01 local Y +1.5 at both existing keys; all times, rotations and other tracks byte-identical',
            'source_sha256':sha(original_clip),'adapted_sha256':sha(bytes(data))})
    mesh_paths = [name for name in payload if name.endswith((".scm", ".win.scm"))]
    assert len(mesh_paths) == 6
    for name in mesh_paths:
        payload[name] = mesh_raw
    patches = {}
    for prefix in ("", "mods/DLC1/base/", "mods/DLC1/shadow/"):
        path = prefix + "units/zz_clonewars_utaa_model_unit.bp"
        patch = LiteralTable(payload[path].decode("utf-8")).blueprint()
        assert patch["Merge"] is True and patch["BlueprintId"] == "uul0105"
        assert set(patch) == {"Merge", "BlueprintId", "Display", "General"}
        patch["Weapons"] = {
            1: {
                "RackBones": {
                    bank: {"MuzzleBones": {slot: name for slot, name in enumerate(names, 1)}}
                    for bank, names in enumerate(geometry["banks"], 1)
                },
                "TurretBoneMuzzle": helper_names[0],
            }
        }
        payload[path] = ("UnitBlueprint " + lua(patch) + "\n").encode("utf-8")
        assert LiteralTable(payload[path].decode("utf-8")).blueprint() == patch
        patches[path] = patch
    checks = []
    allowed_attachments = {
        f"Weapons.1.RackBones.{bank}.MuzzleBones.{slot}"
        for bank in (1, 2) for slot in range(1, 5)
    } | {"Weapons.1.TurretBoneMuzzle"}
    allowed_display = {"Display.MeshBlueprint", "Display.DisplayName", "General.UnitName"}
    for variant, path in (("base", BASE_BP), ("DLC shadow", DLC_BP)):
        original_bp = LiteralTable(path.read_text(encoding="utf-8")).blueprint()
        changed = copy.deepcopy(original_bp)
        patch = patches["units/zz_clonewars_utaa_model_unit.bp"]
        merge(changed, {key: value for key, value in patch.items() if key not in ("Merge", "BlueprintId")})
        actual = set(differences(original_bp, changed))
        assert actual == allowed_attachments | allowed_display, sorted(actual)
        assert changed["Weapons"][2] == original_bp["Weapons"][2]
        for bank in (1, 2):
            assert changed["Weapons"][1]["RackBones"][bank]["RackBone"] == original_bp["Weapons"][1]["RackBones"][bank]["RackBone"]
        revert = copy.deepcopy(changed["Weapons"][1])
        revert["RackBones"] = copy.deepcopy(original_bp["Weapons"][1]["RackBones"])
        revert["TurretBoneMuzzle"] = original_bp["Weapons"][1]["TurretBoneMuzzle"]
        assert revert == original_bp["Weapons"][1]
        checks.append({
            "variant": variant, "changes": sorted(actual),
            "attachment_string_changes": 9,
            "all_other_weapon_fields_unchanged": True,
            "secondary_research_weapon_unchanged": True,
            "native_bank_entry_count": [4, 4],
            "new_bank_entry_count": [4, 4],
            "sparse_numeric_table_merge": True,
        })
    payload["CloneWars_UTAA_CREDITS.txt"] = (
        "UT-AA hull and turret: Philloraptor, Fall of the Republic 1.4. "
        "Original archive supplied by user. Original author reuse permission not independently verified. "
        "Native rig/secondary visual geometry: Gas Powered Games, Supreme Commander 2. "
        "Project adaptation four-port-test-2: original four-port launcher restored, "
        "main visual mounting support narrowed, four muzzle helpers mapped to unchanged native two-bank logic. "
        "Not a public release authorization.\n"
    ).encode("utf-8")
    preserved_paths = [name for name in payload if name.lower().endswith((".dds", "_mesh.bp"))]
    assert len(preserved_paths) == 9
    assert all(payload[name] == old_payload[name] for name in preserved_paths)
    assert not any(name.lower().endswith('.lua') for name in payload)
    assert len([n for n in payload if n.lower().endswith('.sca')]) == 4
    archive_path = OUT / "zz_SC2_CloneWars_UTAA_Model.scd"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            archive.writestr(name, data)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert archive.namelist() == sorted(payload)
        assert all(archive.read(name) == data for name, data in payload.items())
    assert sha(BACKUP.read_bytes()) == backup_hash
    assert GEOMETRY.read_bytes() == geometry_raw, "Geometry changed during build; rebuild with stable input"
    report = {
        "revision": geometry["revision"], "archive": str(archive_path),
        "sha256": sha(archive_path.read_bytes()), "geometry_sha256": sha(geometry_raw),
        "previous_package_backup": str(BACKUP), "previous_package_sha256": backup_hash,
        "backup_unchanged": True, "archive_crc": "passed", "installed": False,
        "meshes": [dict(lod=i, **scm_v7.summary(mesh_raw)) for i in range(3)],
        "skeleton": {
            "original_bones": 26, "total_bones": 30, "skin_bones": 16,
            "original_names_order_parents_and_rotations_preserved": True,
            "main_mount_vertical_rise":1.5,
            "only_original_bone_row_changes": "Main yaw local Y +1.5; matching descendant inverse-bind translations; absolute name offsets",
            "new_helpers": helper_checks,
            "all_lods_use_identical_full_detail_geometry_and_rig": True,
        },
        "source_triangle_count": len(geometry["triangles"]),
        "backface_policy": "Same all-triangle reverse-face policy as previous installed revision",
        "blueprint_checks": checks,
        "materials_and_mesh_blueprint_byte_identical_to_previous_package": preserved_paths,
        "native_script_overrides": False,
        "adapted_native_animations":animation_checks,
        "gameplay_settings_changed": [],
        "firing_attachment_changes": "Nine attachment strings: eight bank entries plus aiming muzzle; four new rig helpers",
        "native_animations": "Original AOpen and Aland references, frame/key times, rotations and all non-mount tracks retained; main yaw Y raised 1.5 to match corrected mount",
        "runtime_tested": False,
        "limits": [
            "Static source-table, binary-format, helper-rest-placement and package checks only; no gameplay/runtime acceptance",
            "Changed firing origins require live muzzle-flash, trajectory clearance and aim-solution checks",
            "Opening/packing, landing, moving fire and research gun clearance still require in-game testing",
            "Full geometry at all LODs and all-triangle backfaces retain prior performance limitations",
            "Original test materials retained: neutral normals and disabled team tint",
        ],
    }
    (W / "four-port-package-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "Package-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "revision": report["revision"], "sha256": report["sha256"],
        "triangles": len(indices) // 3, "vertices": len(vertices),
        "bones": len(model["bones"]), "skin_bones": model["header"][3],
        "blueprint_variants_passed": len(checks), "installed": False,
    }))


if __name__ == "__main__":
    main()
