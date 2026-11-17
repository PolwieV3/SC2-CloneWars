"""Export the AAT's textured geometry and render its research icon in Blender."""
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'local/build/aat'
WORK.mkdir(parents=True, exist_ok=True)
meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.data.materials]
for obj in meshes:
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj not in meshes:
        obj.hide_render = True

materials = sorted({obj.data.materials[0].name for obj in meshes})
atlas = np.zeros((2048, 2048, 4), dtype=np.uint8)
for tile, name in enumerate(materials):
    shader = next(node for node in bpy.data.materials[name].node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    image = shader.inputs['Base Color'].links[0].from_node.image
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    width, height = image.size
    xy = np.arange(1024)
    pixels = pixels.reshape(height, width, 4)[np.ix_(xy * height // 1024, xy * width // 1024)]
    x, y = (tile % 2) * 1024, (tile // 2) * 1024
    atlas[y:y+1024, x:x+1024] = (pixels.clip(0, 1) * 255 + .5).astype(np.uint8)
(WORK / 'diffuse.rgba').write_bytes(atlas[::-1].tobytes())

# The imported asset is already Y-up. Its main gun points toward positive Z.
def game_position(point):
    return (point - Vector((0, .74, .14))) * 6.4


arm = next(obj for obj in bpy.data.objects if obj.type == 'ARMATURE')
mounts = (
    ('Main', 'Head_01', 'Main Gun_02'),
    ('Left', 'Gun .L_03', 'Gun .L_03'),
    ('Right', 'Gun .R_04', 'Gun .R_04'),
)
rig = [('AAT_Root', -1, (0, 0, 0))]
skin = {}
for label, yaw_joint, pitch_joint in mounts:
    yaw = game_position(arm.matrix_world @ arm.data.bones[yaw_joint].head_local)
    pitch = game_position(arm.matrix_world @ arm.data.bones[pitch_joint].head_local)
    barrel = [
        game_position(obj.matrix_world @ vertex.co)
        for obj in meshes for vertex in obj.data.vertices
        if any(obj.vertex_groups[group.group].name == pitch_joint and group.weight > .5
               for group in vertex.groups)
    ]
    tip = max(point.z for point in barrel)
    cap = [point for point in barrel if point.z >= tip - .025]
    muzzle = Vector(((min(p.x for p in cap) + max(p.x for p in cap)) / 2,
                     (min(p.y for p in cap) + max(p.y for p in cap)) / 2,
                     tip + .03))
    base = len(rig)
    rig.extend(((f'AAT_{label}Yaw', 0, tuple(yaw)),
                (f'AAT_{label}Pitch', base, tuple(pitch)),
                (f'AAT_{label}Muzzle', base + 1, tuple(muzzle))))
    skin[yaw_joint] = base
    skin[pitch_joint] = base + 1
for number, (x, z) in enumerate(((-3, -3), (3, -3), (-3, 3), (3, 3)), 1):
    rig.append((f'UCL0104_jumpjet0{number}', 0, (x, .7, z)))
(WORK / 'rig.json').write_text(json.dumps(rig))

for lod, ratio in enumerate((1, .55, .28)):
    vertices, indices, lookup = [], [], {}
    for original in meshes:
        obj = original.copy()
        obj.data = original.data.copy()
        bpy.context.collection.objects.link(obj)
        if ratio < 1:
            modifier = obj.modifiers.new('AAT LOD', 'DECIMATE')
            modifier.ratio = ratio
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        mesh = obj.data
        mesh.calc_loop_triangles()
        mesh.calc_tangents()
        direction = obj.matrix_world.to_3x3()
        normal_matrix = direction.inverted().transposed()
        tile = materials.index(mesh.materials[0].name)
        for triangle in mesh.loop_triangles:
            for index in triangle.loops:
                loop = mesh.loops[index]
                vertex = mesh.vertices[loop.vertex_index]
                point = game_position(obj.matrix_world @ vertex.co)
                normal = (normal_matrix @ loop.normal).normalized()
                tangent = (direction @ loop.tangent).normalized()
                bitangent = normal.cross(tangent) * loop.bitangent_sign
                uv = mesh.uv_layers.active.data[index].uv
                assert all(-.005 <= value <= 1.005 for value in uv), tuple(uv)
                u = (tile % 2 + max(0, min(1, uv.x))) / 2
                v = 1 - (tile // 2 + max(0, min(1, uv.y))) / 2
                dominant = max(vertex.groups, key=lambda group: group.weight, default=None)
                bone = skin.get(obj.vertex_groups[dominant.group].name, 0) if dominant else 0
                row = (*point, *normal, *tangent, *bitangent, u, v, u, v, bone, 0, 0, 0)
                if row not in lookup:
                    lookup[row] = len(vertices)
                    vertices.append(row)
                indices.append(lookup[row])
        bpy.data.objects.remove(obj, do_unlink=True)
    (WORK / f'lod{lod}.json').write_text(json.dumps([vertices, indices]))

scene = bpy.context.scene
camera = bpy.data.objects.new('Research Icon Camera', bpy.data.cameras.new('Research Icon Camera'))
scene.collection.objects.link(camera)
camera.location = (3.4, 2.8, 4.5)
target = Vector((0, 1.24, .12))
back = (camera.location - target).normalized()
right = Vector((0, 1, 0)).cross(back).normalized()
camera.rotation_euler = Matrix((right, back.cross(right), back)).transposed().to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 3.15
scene.camera = camera
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.45, .65, .95)
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.show_shadows = True
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 256
scene.render.resolution_percentage = 100
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = str(WORK / 'aat-render.png')
bpy.ops.render.render(write_still=True)
image = bpy.data.images.load(scene.render.filepath)
pixels = np.empty(len(image.pixels), dtype=np.float32)
image.pixels.foreach_get(pixels)
pixels = pixels.reshape(256, 256, 4)[::-1]
(WORK / 'icon.rgba').write_bytes((pixels.clip(0, 1)*255+.5).astype(np.uint8).tobytes())
