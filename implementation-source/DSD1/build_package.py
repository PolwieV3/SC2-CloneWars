"""Build and stage the Dwarf Spider Droid skirmish test package."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'implementation-source/shared-pipeline'))
from bp_literals import LiteralTable
import scm_v7

WORK = ROOT / 'local/build/dsd1'
BASE = ROOT / 'local/installed-snapshot/gamedata'
FOLDER = 'units/CloneWars/DSD1/'
MESH_ID = '/units/clonewars/dsd1/dsd1_mesh'
UNIT_PATH = 'Units/Cybran/UCL0103/UCL0103_unit.bp'
NAME = 'Dwarf Spider Droid'
rig = json.loads((WORK / 'rig.json').read_text())
bones = rig['bones']
names = [bone['name'] for bone in bones]
parents = [bone['parent'] for bone in bones]
payload = {}

def add_asset(stem, extension, data):
    for suffix in (extension, '.win' + extension):
        payload[FOLDER + stem + suffix] = data

def lua(value):
    if isinstance(value, dict):
        return '{' + ''.join(
            (f'[{key}]' if isinstance(key, int) else key) + ' = ' + lua(item) + ',\n'
            for key, item in value.items()
        ) + '}'
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    return 'nil' if value is None else str(value)

with ZipFile(BASE / 'units.scd') as units:
    original = scm_v7.read(units.read('units/Cybran/UCL0103/UCL0103_lod0.win.scm'))
header = list(original['header'])
buffer = bytearray(scm_v7.HEADER.size)
scm_v7.section(buffer, b'NAME')
offsets = []
for name in names:
    offsets.append(len(buffer))
    buffer.extend(name.encode('ascii') + b'\0')
header[2] = scm_v7.section(buffer, b'SKEL')
header[3] = header[11] = len(bones)
for bone, offset in zip(bones, offsets):
    buffer.extend(scm_v7.BONE.pack(*bone['inverse'], *bone['position'], *bone['quaternion'],
                                   offset, bone['parent'], 0, 0))
header[4] = scm_v7.section(buffer, b'VTXL')
header[6] = 1
buffer.extend(bytes(scm_v7.VERTEX.size))
header[7] = scm_v7.section(buffer, b'TRIS')
header[8] = 3
buffer.extend(bytes(6))
header[5] = scm_v7.section(buffer, b'XTRA')
buffer.extend(b'\xff\0\0\0')
header[9] = scm_v7.section(buffer, b'INFO')
buffer.extend(original['info'])
header[10] = len(original['info'])
material = scm_v7.section(buffer, b'MNAM')
buffer.extend(b'Diffuse\0')
header[12] = scm_v7.section(buffer, b'MATS')
buffer.extend(scm_v7.MATERIAL.pack(material, 1, 0, 0, 1))
scm_v7.HEADER.pack_into(buffer, 0, *header)
reference = bytes(buffer)
for lod in range(3):
    vertices, indices, weights = json.loads((WORK / f'lod{lod}.json').read_text())
    assert all(sum(weights[i:i+4]) == 255 for i in range(0, len(weights), 4))
    data = scm_v7.write(reference, vertices, indices, [(len(indices)//3, 0, 0, len(vertices))], bytes(weights))
    assert scm_v7.read(data)['names'] == names
    add_asset(f'DSD1_lod{lod}', '.scm', data)

def animation(frames):
    data = bytearray(36)
    name_offset = scm_v7.section(data, b'NAME')
    data.extend(b''.join(name.encode('ascii') + b'\0' for name in names))
    link_offset = scm_v7.section(data, b'LINK')
    data.extend(struct.pack(f'<{len(parents)}i', *parents))
    anim_offset = scm_v7.section(data, b'ANIM')
    data.extend(struct.pack('<7f', 0, 0, 0, 1, 0, 0, 0))
    frame_size = 8 + 28 * len(bones)
    for index, frame in enumerate(frames):
        assert len(frame) == len(bones)
        data.extend(struct.pack('<fI', index / (len(frames) - 1), 0))
        for row in frame:
            assert abs(sum(v*v for v in row[3:]) - 1) < 1e-4
            data.extend(struct.pack('<7f', *row))
    assert len(data) == anim_offset + 28 + len(frames) * frame_size
    scm_v7.section(data, b'INFO')
    data.extend(b'DSD1 skirmish test\0')
    struct.pack_into('<4sIIf5I', data, 0, b'ANIM', 7, len(frames), 1, len(bones),
                     name_offset, link_offset, anim_offset, frame_size)
    return bytes(data)

assert rig['frames'][0] == rig['frames'][-1]
for prefix in ('bone_l_f_', 'bone_r_b_', 'bone_r_f_', 'bone_l_b_'):
    index = names.index(prefix + 'hip')
    assert len({tuple(frame[index]) for frame in rig['frames']}) > 2
add_asset('DSD1_Walk', '.sca', animation(rig['frames']))
add_asset('DSD1_Idle', '.sca', animation([rig['idle']] * 2))

def dds(rgba):
    size = len(rgba)
    levels = []
    while True:
        levels.append(rgba[:, :, [2, 1, 0, 3]].tobytes())
        if len(rgba) == 1:
            break
        half = len(rgba) // 2
        rgba = rgba.reshape(half, 2, half, 2, 4).mean(axis=(1, 3)).astype(np.uint8)
    header = [124, 0x2100f, size, size, size*4, 0, len(levels)] + [0]*11
    header += [32, 0x41, 0, 32, 0xff0000, 0xff00, 0xff, 0xff000000, 0x401008, 0, 0, 0, 0]
    return b'DDS ' + struct.pack('<31I', *header) + b''.join(levels)

atlas = np.fromfile(WORK / 'atlas.rgba', dtype=np.uint8).reshape(2048, 2048, 4)
add_asset('DSD1_Diffuse', '.dds', dds(atlas))
for channel, rgba in [('Normal', (128, 128, 255, 128)), ('Mask', (8, 0, 10, 230)), ('Team', (0, 0, 0, 0))]:
    add_asset('DSD1_' + channel, '.dds', dds(np.full((16, 16, 4), rgba, dtype=np.uint8)))

with ZipFile(BASE / 'uncompiled_lua.scd') as source, ZipFile(BASE / 'z_uncompiled_lua_dlc1.scd') as dlc:
    scopes = [
        ('', source, 'uncompiled/' + UNIT_PATH),
        ('mods/DLC1/base/', source, 'uncompiled/' + UNIT_PATH),
        ('mods/DLC1/shadow/', dlc, 'uncompiled/mods/DLC1/shadow/' + UNIT_PATH),
    ]
    for prefix, archive, path in scopes:
        bp = LiteralTable(archive.read(path).decode()).blueprint()
        display = bp['Display']
        mesh = deepcopy(display.pop('Mesh'))
        mesh['BlueprintId'] = MESH_ID
        for lod, level in mesh['LODs'].items():
            level['MeshName'] = f'/{FOLDER}DSD1_lod{lod-1}.scm'
            material = level['MaterialSets'][1]['Materials'][1]
            for channel in ('Diffuse', 'Normal', 'Mask', 'Team'):
                material[channel + 'Name'] = f'/{FOLDER}DSD1_{channel}.dds'
            material['ShaderMacros'] = 'ambient_lighting, diffuse_lighting, specular_lighting, ambient_occlusion, environment_mapping, point_cloud'
        payload[FOLDER + 'DSD1_mesh.bp'] = ('MeshBlueprint ' + lua(mesh)).encode()
        walk = f'/{FOLDER}DSD1_Walk.sca'
        idle = f'/{FOLDER}DSD1_Idle.sca'
        display.update(DisplayName=NAME, MeshBlueprint=MESH_ID, AnimationWalk=walk, AnimationIdle=idle,
                       UniformScale=round(display['UniformScale'] * 1.8 * 1.15, 6),
                       SimulationBones={1: 'DSD1_Muzzle', 2: 'bonehead'},
                       TransportAnimation={1: {'Animation': idle, 'Weight': 100}})
        display.pop('AnimationDeath', None)
        bp['Death'].pop('DestructionParts', None)
        bp['General']['UnitName'] = NAME
        bp['Physics']['MaxSpeed'] = round(bp['Physics']['MaxSpeed'] * .8 * .95, 6)
        bp.update(BlueprintId='ucl0103', ScriptModule=f'/{FOLDER}DSD1_script.lua', ScriptClass='DSD1')
        weapons = bp['Weapons']
        controller, first, second, detonate = (weapons[i] for i in range(1, 5))
        assert controller['ProjectilesPerOnFire'] == 0
        assert first['ProjectilesPerOnFire'] == second['ProjectilesPerOnFire'] == 1
        dps = sum(weapon['Damage'] * weapon['RateOfFire'] for weapon in (first, second))
        first.pop('MuzzleChargeDelay', None)
        first.pop('PrefersPrimaryWeaponTarget', None)
        first.update(Damage=dps / 2 + 10, RateOfFire=2, TurretYawRange=180,
                     TurretBoneYaw='DSD1_Yaw', TurretBonePitch='DSD1_Pitch', TurretBoneMuzzle='DSD1_Muzzle',
                     RackRecoilDistance=0, RackBones={1: {'RackBone': 'DSD1_Pitch', 'MuzzleBones': {1: 'DSD1_Muzzle'}}})
        bp['Weapons'] = {1: first, 2: detonate}
        # Keep native gameplay, upgrades and jumpjet hooks. Redirect old visual anchors.
        text = lua(bp).replace('UCL0103_T01_B01_Muzzle01', 'DSD1_Muzzle')
        raw = 'UnitBlueprint ' + text
        verified = LiteralTable(raw).blueprint()
        assert verified['Weapons'][1]['Damage'] * verified['Weapons'][1]['RateOfFire'] == dps + 20
        payload[prefix + 'units/zz_clonewars_dsd1_unit.bp'] = raw.encode()

payload[FOLDER + 'DSD1_script.lua'] = b"""local MobileUnit = import('/lua/sim/MobileUnit.lua').MobileUnit
local DefaultProjectileWeapon = import('/lua/sim/DefaultWeapons.lua').DefaultProjectileWeapon

DSD1 = Class(MobileUnit) {
    DestructionExplosionWaitDelayMin = 0.6,
    DestructionExplosionWaitDelayMax = 0.8,
    Weapons = {
        Laser02 = Class(DefaultProjectileWeapon) {},
    },
}
TypeClass = DSD1
"""
payload['DSD1_ATTRIBUTION.txt'] = b"""Dwarf Spider Droid by Mind Mulch for the Masses, CC BY 4.0.
https://sketchfab.com/3d-models/dwarf-spider-droid-4f5d54b98b744c439a14fd897b946a4e
https://creativecommons.org/licenses/by/4.0/
Adapted with new animation, aim controls, LODs, texture atlas and SC2 export.
"""
archive = ROOT / 'dist/zzzz_SC2_CloneWars_CIS_DSD1_Test.scd'
archive.parent.mkdir(exist_ok=True)
with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
    for path, data in sorted(payload.items()):
        output.writestr(path, data)
with ZipFile(archive) as output:
    assert output.testzip() is None
    assert all(output.read(path) == data for path, data in payload.items())
print(f'{archive}: {len(payload)} verified entries, {dps + 20:g} nominal DPS')
