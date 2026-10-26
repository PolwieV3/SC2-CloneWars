"""Read-only measurements of the four source UT-AA bore rings.

Run with Python; writes only four-port-source-measurements.json beside this file.
Coordinates are the imported ALO bind-world positions, with a documented optional
10 degree X rotation. No model, skeleton, or package is changed.
"""
from pathlib import Path
import collections
import json
import math

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Rep_UTAA_Turret.json"
doc = json.loads(SOURCE.read_text())
mesh = doc["meshes"][0]
verts = mesh["vertices"]
triangles = [mesh["indices"][i:i+3] for i in range(0, len(mesh["indices"]), 3)]
angle = math.radians(10)
c, s = math.cos(angle), math.sin(angle)


def rotate(p):
    x, y, z = p
    return [x, c*y-s*z, s*y+c*z]


def unrotate(p):
    x, y, z = p
    return [x, c*y+s*z, -s*y+c*z]


def bounds(points):
    return [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]


positions = [rotate(v["p"]) for v in verts]
hinge = [0, 0, doc["bones"][2]["matrix"][11]]
rotated_hinge = rotate(hinge)

# These planes are derived from repeated transformed Y coordinates. Each
# identified bore has a complete regular octagon at all four depths.
planes = {
    "outer_flange_rear": -13.969515,
    "bore_back": -14.142744,
    "outer_flange": -14.310098,
    "bore_lip": -14.431011,
}
ports = []
for sign, side in [(-1, "negative_x"), (1, "positive_x")]:
    for upper, row in [(False, "lower"), (True, "upper")]:
        rings = {}
        for name, depth in planes.items():
            ids = [
                i for i, p in enumerate(positions)
                if abs(p[1]-depth) < 0.00003
                and p[0]*sign > 0
                and (p[2] > 4.03) == upper
            ]
            unique = {}
            for i in ids:
                # Duplicate vertex records are UV seams/hard normal edges.
                unique.setdefault(tuple(round(k, 5) for k in positions[i]), i)
            ring_ids = sorted(unique.values())
            ring = [positions[i] for i in ring_ids]
            assert len(ring) == 8, (side, row, name, len(ring))
            center = [sum(p[k] for p in ring)/8 for k in range(3)]
            radii = [math.hypot(p[0]-center[0], p[2]-center[2]) for p in ring]
            mean_radius = sum(radii)/8
            error = max(abs(r-mean_radius) for r in radii)
            assert error < 0.00001, (side, row, name, error)
            rings[name] = {
                "center_rotated": center,
                "center_raw": unrotate(center),
                "center_rotated_hinge_relative": [
                    center[k]-rotated_hinge[k] for k in range(3)
                ],
                "mean_radius": mean_radius,
                "maximum_radius_error": error,
                "depth_max_minus_min": max(p[1] for p in ring)-min(p[1] for p in ring),
                "representative_vertex_indices": ring_ids,
                "all_vertex_indices": ids,
                "unique_positions_rotated": ring,
            }
        ports.append({"id": f"{side}_{row}", "rings": rings})

bone_geometry = []
for bone in (1, 2):
    points = [v["p"] for v in verts if v["bone"] == bone]
    own_triangles = [t for t in triangles if all(verts[i]["bone"] == bone for i in t)]
    bone_geometry.append({
        "bone_index": bone,
        "name": doc["bones"][bone]["name"],
        "vertex_records": len(points),
        "triangles": len(own_triangles),
        "unique_positions": len(set(tuple(round(x, 5) for x in p) for p in points)),
        "bounds_raw": bounds(points),
        "bounds_rotated": bounds([rotate(p) for p in points]),
        "description": (
            "Upright decagonal yaw-base cylinder, 10 perimeter points at each of 2 Z levels."
            if bone == 1 else "Complete pitchable launcher body, all four bore/flange assemblies, and side pivot."
        ),
    })

result = {
    "source": str(SOURCE),
    "source_mesh_count": len(doc["meshes"]),
    "duplicate_mesh_geometry_identical": doc["meshes"][0] == doc["meshes"][1],
    "coordinate_convention": {
        "raw": "ALO imported bind-world: X lateral, -Y forward, Z up.",
        "rotated": "R_x(+10 degrees) * raw around origin; all four ring planes then have constant Y.",
        "front_normal_raw": unrotate([0, -1, 0]),
        "front_normal_rotated": [0, -1, 0],
        "hinge_raw": hinge,
        "hinge_rotated": rotated_hinge,
        "hinge_caution": "To level only the pitch body while retaining the upright yaw base, use hinge + R_x(+10 degrees)*(p-hinge) on bone 2, not a global rotation of bone 1.",
    },
    "mixed_bone_triangles": sum(len({verts[i]["bone"] for i in t}) > 1 for t in triangles),
    "bone_geometry": bone_geometry,
    "ports": ports,
    "interpretation": [
        "Each port is evidenced by four complete concentric octagonal rings.",
        "The bore_lip is the forward inner bore ring; bore_back is the inset closed dark backing.",
        "Source casing has vertices ahead of bore lips: minimum rotated Y is -14.5787367.",
        "Each muzzle may be placed at bore_lip center, with a small forward offset only if the game effect requires it.",
        "All four rings for all four ports are rigidly weighted to source Barrel_00 (bone 2).",
    ],
}
target = HERE / "four-port-source-measurements.json"
target.write_text(json.dumps(result, indent=2))
print(json.dumps({
    "output": str(target),
    "ports": [{
        "id": p["id"],
        "lip_center": p["rings"]["bore_lip"]["center_rotated"],
        "radius": p["rings"]["bore_lip"]["mean_radius"],
        "hinge_relative": p["rings"]["bore_lip"]["center_rotated_hinge_relative"],
    } for p in ports],
    "hinge": rotated_hinge,
    "bone_geometry": bone_geometry,
}, indent=2))
