"""Build the Persuader replacement for Cobra in the local skirmish build."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
from zipfile import ZipFile, ZIP_DEFLATED

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / 'AAT'))
from build_research_test import AAT_BOLT, BASE, GAME, dds, heavy_blast, lua, model_reference
from bp_literals import LiteralTable
import scm_v7

RAW = ROOT / 'assets/CIS/NR-N99/raw'
MODEL = 'units/CloneWars/NRN99/'
MESH_ID = '/units/clonewars/nrn99/nrn99_mesh'
UNIT = 'Units/Cybran/UCL0104/UCL0104_unit.bp'
UNIT_OVERRIDE = 'units/zz_clonewars_nrn99_unit.bp'
NAME = 'Persuader'
ARCHIVE = 'zzzz_SC2_CloneWars_CIS_NRN99_Test.scd'
# Match the Databank length ratio (10.96 m / 9.19 m) against the installed AAT mesh.
SCALE = .1266


def mdx_geometry():
    raw = (RAW / 'NR-N99_V2.mdx').read_bytes()
    assert raw[:4] == b'MDLX'
    cursor = 4
    while cursor < len(raw):
        tag, size = struct.unpack_from('<4sI', raw, cursor)
        cursor += 8
        if tag == b'GEOS':
            geometries = raw[cursor:cursor + size]
            break
        cursor += size
    else:
        raise ValueError('MDX is missing geometry')

    cursor = 0
    while cursor < len(geometries):
        size, = struct.unpack_from('<I', geometries, cursor)
        end = cursor + size
        position = cursor + 4
        blocks = {}
        for tag, dtype, columns in (
            (b'VRTX', '<f4', 3), (b'NRMS', '<f4', 3), (b'PTYP', '<u4', 1),
            (b'PCNT', '<u4', 1), (b'PVTX', '<u2', 3), (b'GNDX', 'u1', 1),
            (b'MTGC', '<u4', 1), (b'MATS', '<u4', 1),
        ):
            actual, count = struct.unpack_from('<4sI', geometries, position)
            assert actual == tag
            entries = count if tag == b'PVTX' else count * columns
            array = np.frombuffer(geometries, dtype=dtype, count=entries, offset=position + 8)
            blocks[tag] = array.reshape(-1, columns)
            position += 8 + array.nbytes
        material, = struct.unpack_from('<I', geometries, position)
        uv_start = geometries.index(b'UVBS', position, end)
        uv_count, = struct.unpack_from('<I', geometries, uv_start + 4)
        uv = np.frombuffer(geometries, dtype='<f4', count=2 * uv_count, offset=uv_start + 8)
        assert uv_count == len(blocks[b'VRTX']) and set(blocks[b'PTYP'].flat) == {4}
        if material in (0, 6):
            yield material, blocks[b'VRTX'], blocks[b'NRMS'], blocks[b'PVTX'], uv.reshape(-1, 2)
        cursor = end


def components(points, triangles):
    parents = list(range(len(points)))
    welded = {}

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for index, point in enumerate(points):
        parents[index] = welded.setdefault(tuple(np.round(point, 3)), index)
    for first, second, third in triangles:
        parents[root(second)] = root(first)
        parents[root(third)] = root(first)
    islands = {}
    for index in range(len(points)):
        islands.setdefault(root(index), []).append(index)
    return list(islands.values())


def game_point(point):
    forward, side, up = point
    return (side * .12, (up - 3.95) * .12, forward * .12)


def build_model():
    geometry = sorted(mdx_geometry(), key=lambda item: item[0])
    assert [item[0] for item in geometry] == [0, 6]
    _, hull, _, hull_faces, _ = geometry[0]
    islands = components(hull, hull_faces)
    rig = [('NRN99_Root', -1, (0, 0, 0))]
    skin = np.zeros(len(hull), dtype=np.uint8)
    mounts = []
    for side, sign in (('Left', 1), ('Right', -1)):
        for name, center, tolerance, pivot, front in (
            ('Main', 44.65, 5.5, 40.94, 148.08),
            ('Aux', 58.26, 4, 43.185, 92.53),
        ):
            label = side + name
            pieces = []
            for island in islands:
                low = hull[island].min(axis=0)
                high = hull[island].max(axis=0)
                if (low[0] >= pivot and high[0] <= front + .01 and low[2] > 45
                        and np.all(np.abs(np.array([low[1], high[1]]) - sign * center) < tolerance)):
                    pieces.extend(island)
            assert len(pieces) == (230 if name == 'Main' else 80), (label, len(pieces))
            barrel = hull[pieces]
            cap = barrel[barrel[:, 0] >= barrel[:, 0].max() - .1]
            mid = (cap.min(axis=0) + cap.max(axis=0)) / 2
            assert abs(mid[0] - front) < .02
            yaw, pitch, muzzle = (f'NRN99_{label}{joint}' for joint in ('Yaw', 'Pitch', 'Muzzle'))
            mount_point = game_point((pivot, mid[1], mid[2]))
            muzzle_point = game_point((float(mid[0]) + .15, mid[1], mid[2]))
            base = len(rig)
            rig.extend(((yaw, 0, mount_point), (pitch, base, mount_point),
                        (muzzle, base + 1, muzzle_point)))
            assert not np.any(skin[pieces])
            skin[pieces] = base + 1
            mounts.append((label, yaw, pitch, muzzle))
    for index, (forward, side) in enumerate(((-95, -42), (-95, 42), (70, -42), (70, 42)), 1):
        rig.append((f'UCL0104_jumpjet0{index}', 0, game_point((forward, side, 4))))

    # Keep the repeating tread UVs in their own native material slot.
    reference = bytearray(model_reference(rig))
    header = list(scm_v7.HEADER.unpack_from(reference))
    name_offset = len(reference)
    reference.extend(b'Tread\0')
    first = scm_v7.MATERIAL.unpack_from(reference, header[12])
    header[12] = scm_v7.section(reference, b'MATS')
    header[13] = 2
    reference.extend(scm_v7.MATERIAL.pack(*first))
    reference.extend(scm_v7.MATERIAL.pack(name_offset, 0, 3, 0, 0))
    scm_v7.HEADER.pack_into(reference, 0, *header)

    vertices, indices, draws = [], [], []
    for material, points, normals, triangles, uv in geometry:
        start_vertex, start_index = len(vertices), len(indices)
        for index, (point, normal, texcoord) in enumerate(zip(points, normals, uv)):
            normal = normal[[1, 2, 0]].astype(float)
            normal /= np.linalg.norm(normal)
            axis = (1, 0, 0) if abs(normal[0]) < .9 else (0, 0, 1)
            tangent = np.cross(normal, axis)
            tangent /= np.linalg.norm(tangent)
            bitangent = np.cross(normal, tangent)
            bone = int(skin[index]) if material == 0 else 0
            vertices.append((*game_point(point), *normal, *tangent, *bitangent,
                             *texcoord, *texcoord, bone, 0, 0, 0))
        indices.extend(int(i) + start_vertex for i in triangles.flat)
        draws.append((len(triangles), start_index, start_vertex, len(points)))
    mesh = scm_v7.write(bytes(reference), vertices, indices, draws)
    assert scm_v7.read(mesh)['names'] == [name for name, _, _ in rig]
    return mesh, mounts


def assets(mesh):
    outputs = {}
    for name, source in [('Hull', 'NR-N99_512x512.png'), ('Tread', 'NR-N99_tread_64x64.png')]:
        pixels = cv2.imread(str(RAW / source), cv2.IMREAD_UNCHANGED)
        outputs[name] = dds(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGBA), mipmaps=True)
    for name, pixel in [('Normal', (128, 128, 255, 128)), ('Mask', (8, 0, 10, 230)),
                        ('Team', (0, 0, 0, 0))]:
        outputs[name] = dds(np.full((16, 16, 4), pixel, dtype=np.uint8), mipmaps=True)
    return {f'{MODEL}NRN99_{name}{platform}.{ext}': raw
            for ext, entries in [('scm', {'model': mesh}), ('dds', outputs)]
            for name, raw in entries.items() for platform in ('', '.win')}


def unit_blueprint(bp, template, mounts):
    stock = bp['Weapons'][1]
    detonate = bp['Weapons'][2]
    # Reduce the previous per-shot damage by 15% across all four guns.
    damage = stock['Damage'] * stock['ProjectilesPerOnFire'] * stock['RateOfFire'] / len(mounts) * .85
    firing_range = stock['MaxRadius'] * .8
    bp['Intel']['VisionRadius'] = firing_range
    weapons = {}
    for index, (label, yaw, pitch, muzzle) in enumerate(mounts, 1):
        gun = deepcopy(template)
        for key in ('MuzzleChargeDelay', 'PrefersPrimaryWeaponTarget', 'FiringRandomness',
                    'MuzzleFlashEffect', 'ValidateFiringTrajectory'):
            gun.pop(key, None)
        gun.update(Label=label, DisplayName='Persuader Blaster', Damage=damage, RateOfFire=.6,
                   FiringRandomness=0,
                   MinRadius=0, MaxRadius=firing_range, MuzzleVelocity=65, BallisticArc='RULEUBA_None',
                   ProjectileId='/' + AAT_BOLT, RackRecoilDistance=0, SlavedToBody=True,
                   # Small hull movements and the sideways muzzle offsets need
                   # more aiming tolerance than the Loyalist's swiveling laser.
                   FiringTolerance=20, RequireFiringTrajectory=False,
                   NotExclusive=True, TurretYaw=0, TurretYawRange=0, TurretPitch=17.5,
                   TurretPitchRange=17.5, TurretBoneYaw=yaw, TurretBonePitch=pitch,
                   TurretBoneMuzzle=muzzle, RackBones={1: {'RackBone': pitch, 'MuzzleBones': {1: muzzle}}})
        weapons[index] = gun
    bp['Weapons'] = {**weapons, len(weapons) + 1: detonate}
    bp['AI']['Attacker']['PrimaryWeapon'] = mounts[0][0]
    bp.update(BlueprintId='ucl0104', Description='Fixed-Forward Blaster Tank',
              ScriptModule=f'/{MODEL}NRN99_script.lua', ScriptClass='NRN99',
              StrategicIconName='icon_land_directfire')
    bp['General']['UnitName'] = NAME
    categories = [name for name in dict.fromkeys(bp['Categories'].values())
                  if name not in {'SILO', 'INDIRECTFIRE', 'OVERLAYINDIRECTFIRE'}]
    bp['Categories'] = dict(enumerate(categories + ['DIRECTFIRE', 'OVERLAYDIRECTFIRE'], 1))
    bp['Death'].pop('DestructionParts', None)
    display = bp['Display']
    for key in ('AnimationWalk', 'AnimationOpen', 'AnimationDeath'):
        display.pop(key, None)
    display.update(DisplayName=NAME, UniformScale=SCALE,
                   SimulationBones={i: mount[3] for i, mount in enumerate(mounts, 1)})
    mesh = display.pop('Mesh')
    mesh['BlueprintId'] = MESH_ID
    display['MeshBlueprint'] = MESH_ID
    for lod in mesh['LODs'].values():
        lod['MeshName'] = f'/{MODEL}NRN99_model.scm'
        for material_set in lod['MaterialSets'].values():
            first = material_set['Materials'][1]
            first['ShaderMacros'] = first['ShaderMacros'].replace('team_color, ', '')
            for index, name in enumerate(('Hull', 'Tread'), 1):
                material = deepcopy(first)
                for channel, image in [('Diffuse', name), ('Normal', 'Normal'),
                                       ('Mask', 'Mask'), ('Team', 'Team')]:
                    material[channel + 'Name'] = f'/{MODEL}NRN99_{image}.dds'
                material_set['Materials'][index] = material
    return bp, mesh


def build():
    mesh, mounts = build_model()
    _, red_effects = heavy_blast()
    payload = {**assets(mesh), **red_effects}
    # The installed AAT already provides these exact red effects. Use its bytes
    # so both packages resolve the same shared projectile even if load order changes.
    aat, = GAME.glob('*_SC2_CloneWars_AAT_Research_Test.scd')
    with ZipFile(aat) as red, ZipFile(BASE / 'uncompiled_lua.scd') as base, \
            ZipFile(BASE / 'z_uncompiled_lua_dlc1.scd') as dlc:
        for path in red_effects:
            payload[path] = red.read(path)
        root = 'uncompiled/'
        shadow = 'mods/DLC1/shadow/'
        loyalist = shadow + UNIT.replace('0104', '0103')
        template = LiteralTable(dlc.read(root + loyalist).decode('latin1')).blueprint()['Weapons'][2]
        for prefix, source, path in (('', base, UNIT), ('mods/DLC1/base/', base, UNIT),
                                     (shadow, dlc, shadow + UNIT)):
            original = LiteralTable(source.read(root + path).decode('latin1')).blueprint()
            bp, mesh_bp = unit_blueprint(original, template, mounts)
            encoded = 'UnitBlueprint ' + lua(bp) + '\n'
            assert LiteralTable(encoded).blueprint() == bp
            # Mirror the DSD1 layout. A distinct late-loading file avoids the
            # compiled stock blueprint at the original Cobra path.
            payload[prefix + UNIT_OVERRIDE] = encoded.encode()
        payload[f'{MODEL}NRN99_mesh.bp'] = ('MeshBlueprint ' + lua(mesh_bp) + '\n').encode()
    labels = ''.join(f'        {label} = Class(Blaster) {{}},\n' for label, *_ in mounts)
    payload[f'{MODEL}NRN99_script.lua'] = ("""local MobileUnit = import('/lua/sim/MobileUnit.lua').MobileUnit
local DefaultProjectileWeapon = import('/lua/sim/DefaultWeapons.lua').DefaultProjectileWeapon
local RedBlaster = import('/lua/CloneWars/AATHeavyBlaster.lua')

local Blaster = Class(DefaultProjectileWeapon) {
    CreateProjectileAtMuzzle = function(self, muzzle)
        local target = self:GetCurrentTargetPos()
        local projectile = DefaultProjectileWeapon.CreateProjectileAtMuzzle(self, muzzle)
        if projectile and target then
            local origin = projectile:GetPosition()
            local x = target[1] - origin[1]
            local y = target[2] - origin[2]
            local z = target[3] - origin[3]
            local distance = math.sqrt(x * x + y * y + z * z)
            if distance > 0 then
                local scale = self:GetBlueprint().MuzzleVelocity / distance
                projectile:SetBallisticAcceleration(0)
                projectile:SetVelocity(x * scale, y * scale, z * scale)
            end
        end
        return projectile
    end,

    PlayFxMuzzleSequence = function(self, muzzle)
        RedBlaster.MuzzleFlash(self.unit, muzzle)
    end,
}

NRN99 = Class(MobileUnit) {
    DestructionExplosionWaitDelayMin = 0.8,
    DestructionExplosionWaitDelayMax = 0.8,
    Weapons = {
""" + labels + """    },
}
TypeClass = NRN99
""").encode()
    return payload


if __name__ == '__main__':
    payload = build()
    target = GAME / ARCHIVE
    stage = target.with_suffix('.tmp')
    with ZipFile(stage, 'w', ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            archive.writestr(name, data)
    with ZipFile(stage) as archive:
        assert archive.testzip() is None
        assert all(archive.read(name) == data for name, data in payload.items())
    stage.replace(target)
    print(f'Installed {target.name} with {len(payload)} verified entries')
