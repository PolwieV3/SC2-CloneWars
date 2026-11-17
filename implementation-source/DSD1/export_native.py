"""Export the rigged DSD1 from Blender to the SC2 package builder."""
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'local/build/dsd1'
WORK.mkdir(parents=True, exist_ok=True)
arm = next(obj for obj in bpy.data.objects if obj.type == 'ARMATURE')
meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.vertex_groups]
source = list(arm.data.bones)
names = ['DSD1_Root'] + [bone.name for bone in source]
parents = [-1] + [names.index(bone.parent.name) if bone.parent else 0 for bone in source]
world = arm.matrix_world
origin = world @ arm.data.bones['bone_pelvis'].head_local
forward = world @ arm.data.bones['bone_gun'].head_local - origin
forward.z = 0
forward.normalize()
up = Vector((0, 0, 1))
right = forward.cross(up)
points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
floor = min(point.z for point in points)
origin.z = floor
width = max((point - origin).dot(right) for point in points) - min((point - origin).dot(right) for point in points)
basis = Matrix((right, up, forward)).to_4x4()
convert = Matrix.Scale(17 / width, 4) @ basis @ Matrix.Translation(-origin)

def rigid(matrix):
    return Matrix.Translation(matrix.translation) @ matrix.to_quaternion().to_matrix().to_4x4()

rest = [Matrix.Identity(4)] + [rigid(convert @ world @ bone.matrix_local) for bone in source]
# Use separate aim axes so native turret control does not fight the gait.
gun = names.index('bone_gun')
head = names.index('bonehead')
pivot = rest[gun].translation
muzzle = max(
    (convert @ point for point in points
     if abs((point - origin).dot(right)) < width * .07
     and abs(point.z - (world @ arm.data.bones['bone_gun'].head_local).z) < width * .09),
    key=lambda point: point.z,
)
helpers = [
    ('DSD1_Yaw', head, pivot),
    ('DSD1_Pitch', len(names), pivot),
    ('DSD1_Muzzle', len(names) + 1, muzzle),
    ('UCL0103_jumpjet01', 0, Vector((-3, 4, -2))),
    ('UCL0103_jumpjet02', 0, Vector((3, 4, -2))),
]
for name, parent, position in helpers:
    names.append(name)
    parents.append(parent)
    rest.append(Matrix.Translation(position))
assert len(names) <= 71

def local_rows(matrices):
    return [
        matrices[parent].inverted() @ matrix if parent >= 0 else matrix
        for matrix, parent in zip(matrices, parents)
    ]

bones = []
for name, parent, matrix, local in zip(names, parents, rest, local_rows(rest)):
    inverse = matrix.inverted()
    bones.append(dict(name=name, parent=parent, inverse=[inverse[r][c] for c in range(4) for r in range(4)],
                      position=list(local.translation), quaternion=list(local.to_quaternion())))

# Animate diagonal pairs in opposition. Each knee flexes during its swing phase.
scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 25
for frame in range(1, 26):
    phase = math.tau * (frame - 1) / 24
    for side, leg, offset in [('l', 'f', 0), ('r', 'b', 0), ('r', 'f', math.pi), ('l', 'b', math.pi)]:
        angle = phase + offset
        swing = math.sin(angle)
        lift = max(0, math.cos(angle))
        for joint, axis, value in [
            ('hip', up, (.22 if side == 'l' else -.22) * swing),
            ('thigh', right, (.16 if leg == 'f' else -.16) * lift),
            ('knee', right, (-.27 if leg == 'f' else .27) * lift),
        ]:
            pose = arm.pose.bones[f'bone_{side}_{leg}_{joint}']
            local_axis = (world @ pose.bone.matrix_local).to_quaternion().inverted() @ axis
            pose.rotation_mode = 'QUATERNION'
            pose.rotation_quaternion = Quaternion(local_axis, value)
            pose.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=pose.name)

frames = []
for frame in range(1, 26):
    scene.frame_set(frame)
    matrices = [Matrix.Identity(4)] + [rigid(convert @ world @ arm.pose.bones[bone.name].matrix) for bone in source]
    for index in range(len(matrices), len(rest)):
        parent = parents[index]
        matrices.append(matrices[parent] @ rest[parent].inverted() @ rest[index])
    frames.append([list(row.translation) + list(row.to_quaternion()) for row in local_rows(matrices)])
frames[-1] = frames[0]
idle = [list(row.translation) + list(row.to_quaternion()) for row in local_rows(rest)]
(WORK / 'rig.json').write_text(json.dumps(dict(bones=bones, frames=frames, idle=idle)))

materials = sorted({obj.data.materials[0].name for obj in meshes})
tile_size = 512
material_size = 2 * tile_size
atlas = np.zeros((2 * material_size, 2 * material_size, 4), dtype=np.uint8)
for tile, material in enumerate(materials):
    nodes = bpy.data.materials[material].node_tree.nodes
    shader = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
    image = shader.inputs['Base Color'].links[0].from_node.image
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    width, height = image.size
    pixels = pixels.reshape(height, width, 4)
    xy = np.arange(tile_size)
    rgb = pixels[np.ix_(xy * height // tile_size, xy * width // tile_size)]
    x, y = tile % 2, tile // 2
    # The source uses a repeating sampler and UVs span two repeats per axis.
    # Bake those repeats into the atlas so triangles can cross a seam intact.
    tile_pixels = (rgb.clip(0, 1) * 255 + .5).astype(np.uint8)
    atlas[y * material_size:(y + 1) * material_size,
          x * material_size:(x + 1) * material_size] = np.tile(tile_pixels, (2, 2, 1))
(WORK / 'atlas.rgba').write_bytes(atlas[::-1].tobytes())

for lod, ratio in enumerate((1, .55, .28)):
    vertices, weights, indices, lookup = [], [], [], {}
    for original in meshes:
        obj = original.copy()
        obj.data = original.data.copy()
        bpy.context.collection.objects.link(obj)
        for modifier in list(obj.modifiers):
            obj.modifiers.remove(modifier)
        if ratio < 1:
            decimate = obj.modifiers.new('DSD1 LOD', 'DECIMATE')
            decimate.ratio = ratio
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=decimate.name)
        mesh = obj.data
        mesh.calc_loop_triangles()
        mesh.calc_tangents()
        transform = convert @ obj.matrix_world
        normal_transform = transform.to_3x3().inverted().transposed()
        tile = materials.index(mesh.materials[0].name)
        for triangle in mesh.loop_triangles:
            for loop_index in reversed(triangle.loops):
                loop = mesh.loops[loop_index]
                vertex = mesh.vertices[loop.vertex_index]
                position = transform @ vertex.co
                normal = (normal_transform @ loop.normal).normalized()
                tangent = (transform.to_3x3() @ loop.tangent).normalized()
                bitangent = -normal.cross(tangent) * loop.bitangent_sign
                uv = mesh.uv_layers.active.data[loop_index].uv
                assert -1e-4 <= uv.x <= 2.0001 and -1e-4 <= uv.y <= 2.0001, tuple(uv)
                u = (tile % 2 * 2 + uv.x) / 4
                v = 1 - (tile // 2 * 2 + uv.y) / 4
                groups = {}
                for group in vertex.groups:
                    name = obj.vertex_groups[group.group].name
                    index = names.index('DSD1_Pitch' if name == 'bone_gun' else name)
                    groups[index] = groups.get(index, 0) + group.weight
                ranked = sorted(groups.items(), key=lambda item: -item[1])[:4] or [(0, 1)]
                total = sum(weight for _, weight in ranked)
                ranked += [(0, 0)] * (4 - len(ranked))
                influence = [round(255 * weight / total) for _, weight in ranked]
                influence[0] += 255 - sum(influence)
                row = (*position, *normal, *tangent, *bitangent, u, v, u, v, *(index for index, _ in ranked))
                key = (row, tuple(influence))
                if key not in lookup:
                    lookup[key] = len(vertices)
                    vertices.append(row)
                    weights.extend(influence)
                indices.append(lookup[key])
        bpy.data.objects.remove(obj, do_unlink=True)
    assert len(vertices) < 65536
    (WORK / f'lod{lod}.json').write_text(json.dumps([vertices, indices, weights]))
    print(f'DSD1 LOD{lod}: {len(vertices)} vertices, {len(indices)//3} triangles')
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(WORK / 'DSD1-walk.blend'))
