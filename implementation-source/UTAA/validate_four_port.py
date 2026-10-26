"""Independent checks of exported four-port SCMs and effective blueprint changes.

Run with Blender --background --python this_file. Only validation reports are
written. Source geometry and prior package are independent comparison inputs.
This is asset validation, not an observed game or native-animation playback test.
"""
from pathlib import Path
import collections
import copy
import hashlib
import itertools
import json
import math
import struct
import sys
import zipfile
from mathutils import Matrix, Quaternion, Vector, kdtree

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/archanist"
OUT = ROOT / "outputs/UT-AA"
sys.path.insert(0, str(WORK / "pipeline"))
import scm_v7
import sca101
from bp_literals import LiteralTable, merge, differences

ARCHIVE = OUT / "zz_SC2_CloneWars_UTAA_Model.scd"
BEFORE = OUT / "backups/2026-10-20-four-port-restore/zz_SC2_CloneWars_UTAA_Model.scd"
NATIVE = WORK / "native/units.scd/units/UEF/UUL0105/UUL0105_LOD0.win.scm"
SOURCE = json.loads((WORK / "Rep_UTAA_Turret.json").read_text())["meshes"][0]
MEASURED = json.loads((WORK / "four-port-source-measurements.json").read_text())
HELPERS = [f"UTAA_Muzzle{i:02d}" for i in range(1, 5)]
PORT_IDS = ["negative_x_upper", "positive_x_upper", "negative_x_lower", "positive_x_lower"]
SCALE = .42
EPS = 0.00002
native = scm_v7.read(NATIVE.read_bytes())
report = {
    "revision": "four-port-test-2",
    "validation_type": "Independent exported asset and literal blueprint validation",
    "archive": str(ARCHIVE),
    "runtime_tested": False,
    "native_opening_and_landing_playback_tested": False,
    "limitations": [
        "No observed in-game firing, muzzle effects, projectile clearance, timing, movement, or research operation.",
        "Yaw/pitch checks use deterministic skeletal pose math, not the native engine aim controller.",
        "Synthetic inherited arm motion exercises attachment inheritance; it is not decoded ANIM101 playback.",
        "Identical gameplay settings and original code are static compatibility evidence, not runtime behavior certification.",
    ],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def bind_matrices(model):
    return [Matrix([b[k:k+4] for k in range(0, 16, 4)]).transposed().inverted()
            for b in model["bones"]]


def local_matrices(model):
    return [Matrix.Translation(Vector(b[16:19])) @ Quaternion(b[19:23]).to_matrix().to_4x4()
            for b in model["bones"]]


def poses(model, locals_, yaw=0, pitch=0, arm_synthetic=False):
    result = []
    for name, bone, base_local in zip(model["names"], model["bones"], locals_):
        local = base_local.copy()
        if name == "Turret01":
            local = local @ Matrix.Rotation(math.radians(yaw), 4, "Y")
        elif name == "T01_Rack01":
            local = local @ Matrix.Rotation(math.radians(-pitch), 4, "X")
        elif name == "T01_Arm01" and arm_synthetic:
            local = (local @ Matrix.Translation((0, .45, -.2))
                     @ Matrix.Rotation(math.radians(-25), 4, "X"))
        parent = bone[24]
        require(parent < len(result), "Non-topological bone parent")
        result.append(result[parent] @ local if parent >= 0 else local)
    return result


def triangle_rows(model):
    return [[model["vertices"][j] for j in model["indices"][i:i+3]]
            for i in range(0, len(model["indices"]), 3)]


def triangle_bytes(triangle):
    # Ignore vertex-list offsets and cyclic order; keep every actual attribute.
    return tuple(sorted(scm_v7.VERTEX.pack(*v) for v in triangle))


def counter(triangles):
    return collections.Counter(triangle_bytes(t) for t in triangles)


def both_sides(triangles):
    for t in triangles:
        yield t
        reverse = []
        for row in (t[0], t[2], t[1]):
            r = list(row)
            r[3:6] = [-v for v in r[3:6]]
            r[9:12] = [-v for v in r[9:12]]
            reverse.append(r)
        yield reverse


def source_positions(rack):
    rot = Matrix.Rotation(math.radians(10), 3, "X")
    hinge = Vector((0, 0, 1.9876500368118286))
    result = []
    for v in SOURCE["vertices"]:
        if v["bone"] == 2:
            p = rot @ (Vector(v["p"]) - hinge)
            result.append(rack @ Vector((p.x*SCALE, p.z*SCALE, -p.y*SCALE)))
        else:
            p = Vector(v["p"]) - hinge
            result.append(rack.translation + Vector((p.x, p.z, -p.y))*SCALE)
    return result


def geometry_checks(model, old, bind):
    tris = triangle_rows(model)
    old_tris = triangle_rows(old)
    stable = {0, 13, 14}
    stable_tris = [t for t in tris if all(v[16] in stable for v in t)]
    old_stable = [t for t in old_tris if all(v[16] in stable for v in t)]
    require(counter(stable_tris) == counter(old_stable),
            "Chassis or secondary weapon attributes changed")
    require(not any(v[16] in set(range(5, 13)) for v in model["vertices"]),
            "Obsolete eight-port barrel geometry retained")
    expected = source_positions(bind[4])
    source_indices = [SOURCE["indices"][k:k+3] for k in range(0, len(SOURCE["indices"]), 3)]
    mesh_counts = {}
    source_base_ids = set()
    actual_ring_points = {}
    maximum_position_error = 0.0
    for source_bone, target_bone in [(2, 4), (1, 3)]:
        ids = [i for i, v in enumerate(SOURCE["vertices"]) if v["bone"] == source_bone]
        unique, representatives = {}, {}
        for i in ids:
            key = tuple(round(v, 6) for v in SOURCE["vertices"][i]["p"])
            representatives[i] = unique.setdefault(key, i)
        tree = kdtree.KDTree(len(ids))
        for i in ids:
            tree.insert(expected[i], i)
        tree.balance()
        actual = []
        actual_triangle_ids = []
        for ti, tri in enumerate(tris):
            if not all(v[16] == target_bone for v in tri):
                continue
            mapped = []
            for v in tri:
                _co, index, distance = tree.find(Vector(v[:3]))
                if distance > EPS:
                    break
                mapped.append(representatives[index])
                maximum_position_error = max(maximum_position_error, distance)
            if len(mapped) == 3:
                actual.append(tuple(sorted(mapped)))
                actual_triangle_ids.append(ti)
        expected_tris = [
            tuple(sorted(representatives[i] for i in tri))
            for tri in source_indices
            if all(SOURCE["vertices"][i]["bone"] == source_bone for i in tri)
        ]
        expected_counter = collections.Counter(expected_tris)
        expected_counter.update(expected_tris)  # Existing two-sided export policy.
        require(collections.Counter(actual) == expected_counter,
                f"Source bone {source_bone} topology is missing, altered, or duplicated")
        if source_bone == 2:
            require(sum(all(v[16] == 4 for v in t) for t in tris) == len(expected_tris)*2,
                    "Unexpected additional pitch-housing geometry")
        else:
            source_base_ids.update(actual_triangle_ids)
        mesh_counts[str(source_bone)] = {
            "original_triangles": len(expected_tris),
            "exported_triangles_including_backfaces": len(actual),
            "original_topology_preserved": True,
        }

    # Validate the sole allowed change to native mounting geometry independently.
    old_mount = [t for t in old_tris if all(v[16] in {1, 2, 3} for v in t)]
    expected_mount = []
    for triangle in old_mount:
        transformed = []
        for row in triangle:
            v = list(row)
            v[0] *= .33
            v[1] += 1.5
            v[3:6] = Vector((row[3]/.33, row[4], row[5])).normalized()
            v[6:9] = Vector((row[6]*.33, row[7], row[8])).normalized()
            v[9:12] = Vector((row[9]*.33, row[10], row[11])).normalized()
            transformed.append(v)
        expected_mount.append(transformed)
    actual_mount = [t for i, t in enumerate(tris)
                    if i not in source_base_ids and all(v[16] in {1, 2, 3} for v in t)]
    require(counter(actual_mount) == counter(expected_mount),
            "Mount changes exceed authorized .33 width scale and basis correction")
    require(len(tris) == len(stable_tris) + len(actual_mount) + 940*2,
            "Unaccounted or duplicated geometry in export")

    # Sample actual exported vertices at every measured source bore lip position.
    exported = kdtree.KDTree(sum(v[16] == 4 for v in model["vertices"]))
    for i, v in enumerate(model["vertices"]):
        if v[16] == 4:
            exported.insert(Vector(v[:3]), i)
    exported.balance()
    source_ports = {p["id"]: p for p in MEASURED["ports"]}
    for helper, port_id in zip(HELPERS, PORT_IDS):
        ids = source_ports[port_id]["rings"]["bore_lip"]["representative_vertex_indices"]
        points = []
        for index in ids:
            _co, vi, distance = exported.find(expected[index])
            require(distance < EPS, f"Missing bore lip vertex {helper}")
            points.append(Vector(model["vertices"][vi][:3]))
        center = sum(points, Vector()) / len(points)
        radius = sum((p-center).length for p in points)/len(points)
        normal = (points[1]-points[0]).cross(points[2]-points[0]).normalized()
        forward = (bind[4].to_3x3() @ Vector((0, 0, 1))).normalized()
        if normal.dot(forward) < 0:
            normal.negate()
        require(abs(normal.dot(forward)-1) < 0.00001, "Bore plane direction incorrect")
        require(abs(radius - source_ports[port_id]["rings"]["bore_lip"]["mean_radius"]*SCALE)
                < EPS, "Bore radius changed nonuniformly")
        actual_ring_points[helper] = {"center": center, "normal": normal, "radius": radius}
    return {
        "source_shape": mesh_counts,
        "maximum_source_position_error": maximum_position_error,
        "chassis_and_secondary_geometry_bytes_unchanged": True,
        "stable_triangles_including_backfaces": len(stable_tris),
        "mount_triangles_including_backfaces": len(actual_mount),
        "mount_width_scale": .33,
        "obsolete_barrel_geometry_absent": True,
        "all_exported_triangles_accounted_for": True,
    }, actual_ring_points


def skeleton_and_pose_checks(model, rings):
    require(model["header"][3] == native["header"][3] == 16, "Skin bone count changed")
    require(len(model["bones"]) == 30, "Expected exactly 26 original + four helper bones")
    require(model["names"][:26] == native["names"], "Original bone order/names changed")
    require(model["names"][26:] == HELPERS, "Helper names/order incorrect")
    require(len(set(model["names"])) == 30, "Duplicate skeleton names")
    for i in range(26):
        a, b = model["bones"][i], native["bones"][i]
        expected=list(b)
        if i in set(range(1,13))|set(range(16,24)):
            for axis in range(3):expected[12+axis]-=expected[4+axis]*1.5
        if i==1:expected[17]+=1.5
        expected=scm_v7.BONE.unpack(scm_v7.BONE.pack(*expected))
        require(a[:23]+a[24:] == expected[:23]+expected[24:], f"Bone {i} change exceeds mount translation")
    for i in range(26, 30):
        require(model["bones"][i][24] == 4, "Helper does not inherit pitch rack")
    bind = bind_matrices(model)
    locals_ = local_matrices(model)
    rest = poses(model, locals_)
    rest_error = max(max(abs(bind[i][j][k]-rest[i][j][k]) for j in range(4) for k in range(4))
                     for i in range(30))
    require(rest_error < 0.00002, "SCM local fields disagree with inverse bind matrices")
    ring_details = []
    for j, helper in enumerate(HELPERS, 26):
        ring = rings[helper]
        error = (bind[j].translation-ring["center"]).length
        direction = (bind[j].to_3x3() @ Vector((0, 0, 1))).normalized()
        require(error < EPS, f"{helper} misses actual exported bore center")
        require(direction.dot(ring["normal"]) > .99999, f"{helper} forward direction incorrect")
        ring_details.append({"name": helper, "bone_index": j, "parent_index": 4,
                             "actual_bore_center": list(ring["center"]),
                             "helper_bind_center": list(bind[j].translation),
                             "center_error": error, "bore_radius": ring["radius"],
                             "forward_direction": list(direction)})
    samples = []
    # Every actual export vertex must stay finite throughout every sample.
    positions = {(tuple(v[:3]), v[16]) for v in model["vertices"]}
    for yaw, pitch, synthetic in itertools.product([-180, -90, 0, 90, 180], [0, 20, 40, 80], [False, True]):
        pose = poses(model, locals_, yaw, pitch, synthetic)
        skin = [pose[i] @ bind[i].inverted() for i in range(16)]
        errors, direction_errors = [], []
        for j, helper in enumerate(HELPERS, 26):
            center = skin[4] @ rings[helper]["center"]
            errors.append((center-pose[j].translation).length)
            normal = (skin[4].to_3x3() @ rings[helper]["normal"]).normalized()
            direction = (pose[j].to_3x3() @ Vector((0, 0, 1))).normalized()
            direction_errors.append(1-normal.dot(direction))
        require(max(errors) < EPS, "Pose moves helper away from visual bore")
        require(max(direction_errors) < 0.00001, "Pose changes bore/helper forward alignment")
        require(all(math.isfinite(x) for p, bi in positions for x in skin[bi] @ Vector(p)),
                "Nonfinite posed vertex")
        samples.append({"yaw": yaw, "pitch": pitch,
                        "inherited_arm": "synthetic translation + -25 degree rotation" if synthetic else "native rest",
                        "maximum_bore_helper_error": max(errors),
                        "maximum_forward_dot_error": max(direction_errors),
                        "finite_geometry": True})
    return {
        "original_26_names_parents_rotations_unchanged": True,
        "only_main_mount_translation_and_matching_inverse_binds_changed":1.5,
        "original_16_skin_bones_unchanged": True,
        "helper_count": 4,
        "bind_local_reconstruction_maximum_error": rest_error,
        "helpers": ring_details,
        "pose_samples": samples,
        "pose_sample_count": len(samples),
        "maximum_pose_center_error": max(s["maximum_bore_helper_error"] for s in samples),
    }


def blueprint_checks(current, previous):
    base_path = WORK / "native/uncompiled_lua.scd/uncompiled/Units/UEF/UUL0105/UUL0105_unit.bp"
    dlc_path = WORK / "native/z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUL0105/UUL0105_unit.bp"
    base = LiteralTable(base_path.read_text(encoding="utf-8")).blueprint()
    dlc = LiteralTable(dlc_path.read_text(encoding="utf-8")).blueprint()
    expected = {"Weapons.1.TurretBoneMuzzle"}
    expected |= {f"Weapons.1.RackBones.{bank}.MuzzleBones.{slot}"
                 for bank in [1, 2] for slot in range(1, 5)}
    results = []
    for prefix, original in [("", base), ("mods/DLC1/base/", dlc), ("mods/DLC1/shadow/", dlc)]:
        path = prefix + "units/zz_clonewars_utaa_model_unit.bp"
        old_patch = LiteralTable(previous.read(path).decode()).blueprint()
        new_patch = LiteralTable(current.read(path).decode()).blueprint()
        before, after = copy.deepcopy(original), copy.deepcopy(original)
        merge(before, old_patch)
        merge(after, new_patch)
        changed = set(differences(before, after))
        require(changed == expected, f"Unexpected effective changes for {prefix}: {changed}")
        require(after["Weapons"][1]["TurretBoneMuzzle"] == HELPERS[0], "Aim muzzle wrong")
        for bank in [1, 2]:
            names = after["Weapons"][1]["RackBones"][bank]["MuzzleBones"]
            require(names == {i+1: n for i, n in enumerate(HELPERS)}, "Firing bank remapping wrong")
        require(after["Weapons"][2] == before["Weapons"][2], "Secondary weapon behavior changed")
        require("Weapon" not in after, "Incorrect singular Weapon table introduced")
        results.append({"variant": prefix or "base",
                        "effective_changes": sorted(changed),
                        "attachment_reference_change_count": 9,
                        "both_banks_reference_same_four_ports_in_order": True,
                        "all_other_effective_fields_unchanged": True})
    stable = [n for n in previous.namelist() if n.lower().endswith((".dds", "utaa_mesh.bp"))]
    hashes = []
    for path in stable:
        require(current.read(path) == previous.read(path), f"Material/texture changed: {path}")
        hashes.append({"path": path, "sha256": sha(current.read(path))})
    require(not any(n.lower().endswith('.lua') for n in current.namelist()),
            "Unexpected native script replacement")
    clips=[]
    for filename in ('UUL0105_AOpen01.win.sca','UUL0105_Aland01.win.sca'):
        original=(NATIVE.parent/filename).read_bytes()
        updated=current.read('units/UEF/UUL0105/'+filename)
        require(updated==current.read('units/UEF/UUL0105/'+filename.replace('.win.sca','.sca')), 'Animation alias differs')
        a,b=sca101.read(original),sca101.read(updated)
        require(a['names']==b['names'] and a['parents']==b['parents'] and a['frames']==b['frames'] and a['duration']==b['duration'], 'Animation header or skeleton changed')
        expected=bytearray(original)
        for j,key in enumerate(a['tracks'][1]['keys']):
            struct.pack_into('<f',expected,a['tracks'][1]['offset']+32*j+24,key[6]+1.5)
        require(bytes(expected)==updated, 'Animation changes exceed two main-mount position keys')
        clips.append({'name':filename,'only_change':'Two Turret01 local Y keys raised by 1.5; all other bytes identical','key_times_rotations_and_duration_unchanged':True})
    return {"variants": results, "identical_texture_and_mesh_blueprint_hashes": hashes,
            "native_scripts_not_overridden": True,'animation_checks':clips}


def main():
    report["archive_sha256"] = sha(ARCHIVE.read_bytes())
    report["baseline_archive_sha256"] = sha(BEFORE.read_bytes())
    with zipfile.ZipFile(ARCHIVE) as current, zipfile.ZipFile(BEFORE) as old:
        require(current.testzip() is None, "Archive CRC error")
        old_model = scm_v7.read(old.read("units/CloneWars/UTAA/UUL0105_LOD0.win.scm"))
        lods = []
        for lod in range(3):
            name = "UUL0105_LOD0" if lod == 0 else f"UUL0105_lod{lod}"
            path = f"units/CloneWars/UTAA/{name}.win.scm"
            raw = current.read(path)
            require(raw == current.read(f"units/CloneWars/UTAA/{name}.scm"), "SCM alias differs")
            model = scm_v7.read(raw)
            geom, rings = geometry_checks(model, old_model, bind_matrices(model))
            skeleton = skeleton_and_pose_checks(model, rings)
            lods.append({"lod": lod, "path": path, "sha256": sha(raw),
                         "summary": scm_v7.summary(raw),
                         "geometry": geom, "skeleton_and_pose": skeleton})
        report["lods"] = lods
        report["blueprints_and_materials"] = blueprint_checks(current, old)
    report["status"] = "passed"


try:
    main()
except Exception as exc:
    report["status"] = "failed"
    report["error"] = f"{type(exc).__name__}: {exc}"
    raise
finally:
    text = json.dumps(report, indent=2)
    (WORK / "four-port-validation.json").write_text(text, encoding="utf-8")
    (OUT / "Four-port-validation.json").write_text(text, encoding="utf-8")
    print(json.dumps({"status": report.get("status"), "error": report.get("error"),
                      "archive_sha256": report.get("archive_sha256"),
                      "report": str(OUT / "Four-port-validation.json")}))
