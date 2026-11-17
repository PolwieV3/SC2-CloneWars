"""Build the DLC Cybran Land research prototype in the local development copy."""
from copy import copy, deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
import sys
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'implementation-source/shared-pipeline'))
from bp_literals import LiteralTable
import scm_v7

GAME = ROOT / 'local/dev-game/gamedata'
BASE = ROOT / 'local/installed-snapshot/gamedata'
DLC = 'mods/DLC1/shadow/'
UNIT = 'ucl0107'
NODE = 'CLU_AAT'
ICON = 'textures/ui/common/icons/hud/units/ucl0107.dds'
NAME = 'Armored Assault Tank'
WORK = ROOT / 'local/build/aat'
MODEL = 'units/CloneWars/AAT/'
RESEARCH = DLC + 'lua/sim/Research.lua'
RESTRICTIONS = DLC + 'lua/sim/DefaultBuildRestrictions.lua'
LAYOUT = DLC + 'lua/ui/game/research/research_layout.lua'
ARCHIVE = 'z' * 80 + '_SC2_CloneWars_AAT_Research_Test.scd'
ATTE_BOLT = 'projectiles/CloneWars/ATTEHeavyBolt/ATTEHeavyBolt_proj.bp'
ATTE_EFFECTS = 'lua/CloneWars/ATTEHeavyBlaster.lua'
AAT_BOLT = ATTE_BOLT.replace('ATTEHeavyBolt', 'AATHeavyBolt')
AAT_EFFECTS = ATTE_EFFECTS.replace('ATTEHeavyBlaster', 'AATHeavyBlaster')
# Match the 9.19:8.2 lore length ratio using the installed TX-130's 3.672-unit mesh.
LORE_SCALE = .24845

def lua(value):
    if isinstance(value, dict):
        return '{\n' + ''.join(
            (f'[{key}]' if isinstance(key, int) else key) + ' = ' + lua(item) + ',\n'
            for key, item in value.items()
        ) + '}'
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    return 'nil' if value is None else str(value)

def insert_before(source, anchor, addition):
    assert source.count(anchor) == 1, anchor
    return source.replace(anchor, addition + anchor)

def text(raw):
    return raw.decode('latin1').replace('\r\n', '\n').replace('\r', '')

def dds(rgba, mipmaps=False):
    size = len(rgba)
    levels = [rgba[:, :, [2, 1, 0, 3]].tobytes()]
    while mipmaps and len(rgba) > 1:
        half = len(rgba) // 2
        rgba = rgba.reshape(half, 2, half, 2, 4).mean(axis=(1, 3)).astype(np.uint8)
        levels.append(rgba[:, :, [2, 1, 0, 3]].tobytes())
    header = [124, 0x2100f if mipmaps else 0x100f, size, size, size * 4, 0,
              len(levels) if mipmaps else 0] + [0] * 11
    header += [32, 0x41, 0, 32, 0xff0000, 0xff00, 0xff, 0xff000000,
               0x401008 if mipmaps else 0x1000, 0, 0, 0, 0]
    return b'DDS ' + struct.pack('<31I', *header) + b''.join(levels)

def tank_icon():
    render = np.fromfile(WORK / 'icon.rgba', dtype=np.uint8).reshape(256, 256, 4)
    y, x = np.nonzero(render[:, :, 3])
    side = max(np.ptp(x), np.ptp(y)) + 24
    center = (int((y.min() + y.max()) / 2), int((x.min() + x.max()) / 2))
    padded = np.pad(render, ((128, 128), (128, 128), (0, 0)))
    offsets = 128 + np.linspace(-side / 2, side / 2, 256).astype(int)
    sample = padded[np.ix_(center[0] + offsets, center[1] + offsets)]
    alpha = sample[:, :, 3].astype(np.float32) / 255
    shade = sample[:, :, :3].mean(axis=2) / 255
    depth = np.clip(shade * 1.5 + .33, 0, 1)
    rgb = np.array([104, 181, 255]) * depth[:, :, None]
    rgb[1::4] *= .72
    pixels = np.concatenate((rgb * alpha[:, :, None], alpha[:, :, None] * 255), axis=2)
    pixels = pixels.reshape(64, 4, 64, 4, 4).mean(axis=(1, 3))
    pixels[:, :, :3] *= 255 / np.maximum(pixels[:, :, 3:4], 1)
    return dds(pixels.clip(0, 255).astype(np.uint8))

def model_reference(rig, source_mesh=None):
    if source_mesh is None:
        with ZipFile(BASE / 'units.scd') as units:
            source_mesh = units.read('units/Cybran/UCL0104/UCL0104_LOD0.win.scm')
    original = scm_v7.read(source_mesh)
    header = list(original['header'])
    raw = bytearray(scm_v7.HEADER.size)
    scm_v7.section(raw, b'NAME')
    offsets = []
    for name, _, _ in rig:
        offsets.append(len(raw))
        raw.extend(name.encode('ascii') + b'\0')
    header[2] = scm_v7.section(raw, b'SKEL')
    header[3] = header[11] = len(rig)
    for (_, parent, position), offset in zip(rig, offsets):
        x, y, z = position
        parent_position = rig[parent][2] if parent >= 0 else (0, 0, 0)
        local = [value - origin for value, origin in zip(position, parent_position)]
        inverse = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1]
        raw.extend(scm_v7.BONE.pack(*inverse, *local, 1, 0, 0, 0, offset, parent, 0, 0))
    header[4] = scm_v7.section(raw, b'VTXL')
    header[6] = 1
    raw.extend(bytes(scm_v7.VERTEX.size))
    header[7] = scm_v7.section(raw, b'TRIS')
    header[8] = 3
    raw.extend(bytes(6))
    header[5] = scm_v7.section(raw, b'XTRA')
    raw.extend(b'\xff\0\0\0')
    header[9] = scm_v7.section(raw, b'INFO')
    header[10] = len(original['info'])
    raw.extend(original['info'])
    material = scm_v7.section(raw, b'MNAM')
    raw.extend(b'Diffuse\0')
    header[12] = scm_v7.section(raw, b'MATS')
    raw.extend(scm_v7.MATERIAL.pack(material, 1, 0, 0, 1))
    scm_v7.HEADER.pack_into(raw, 0, *header)
    return bytes(raw)

def model_assets(rig):
    reference = model_reference(rig)
    atlas = np.fromfile(WORK / 'diffuse.rgba', dtype=np.uint8).reshape(2048, 2048, 4)
    atlas[:, :, :3] = np.rint(atlas[:, :, :3] * .88).astype(np.uint8)
    assets = {'AAT_Diffuse.dds': dds(atlas, mipmaps=True)}
    for kind, value in [('Normal', (128, 128, 255, 128)), ('Mask', (8, 0, 10, 230)),
                        ('Team', (0, 0, 0, 0))]:
        assets[f'AAT_{kind}.dds'] = dds(np.full((16, 16, 4), value, dtype=np.uint8), mipmaps=True)
    for lod in range(3):
        vertices, indices = json.loads((WORK / f'lod{lod}.json').read_text())
        assert {vertex[16] for vertex in vertices} == {0, 1, 2, 5, 8}
        assets[f'AAT_lod{lod}.scm'] = scm_v7.write(
            reference, vertices, indices, [(len(indices) // 3, 0, 0, len(vertices))]
        )
    payload = {}
    for name, raw in assets.items():
        stem, extension = name.rsplit('.', 1)
        payload[MODEL + name] = raw
        payload[f'{MODEL}{stem}.win.{extension}'] = raw
    return payload

def tank_weapons(template, heavy_cannon, heavy_audio):
    weapons = {}
    for index, (label, name, damage, period, radius, yaw, velocity) in enumerate((
        # Match the TX-130's baseline ground DPS across the AAT's three guns.
        ('Main', 'Main Blaster Cannon', 100, 2.5, 26, 180, 85),
        # The native ring can pick either side gun. Publish the main radius
        # for every gun and enforce side-gun reach in AAT_script.lua.
        ('Left', 'Left Side Blaster', 4, .4, 26, 35, 55),
        ('Right', 'Right Side Blaster', 4, .4, 26, 35, 55),
    ), 1):
        weapon = deepcopy(template)
        weapon.pop('MuzzleChargeDelay', None)
        weapon.pop('PrefersPrimaryWeaponTarget', None)
        mount = 'AAT_' + label
        weapon.update(Label=label, DisplayName=name, Damage=damage, RateOfFire=1 / period,
                      MaxRadius=radius, MuzzleVelocity=velocity, RackRecoilDistance=0,
                      NotExclusive=True, TurretYawRange=yaw, TurretPitchRange=25,
                      TurretBoneYaw=mount + 'Yaw', TurretBonePitch=mount + 'Pitch',
                      TurretBoneMuzzle=mount + 'Muzzle',
                      RackBones={1: {'RackBone': mount + 'Pitch',
                                    'MuzzleBones': {1: mount + 'Muzzle'}}})
        if label == 'Main':
            for key in ('BallisticArc', 'FiringTolerance', 'MuzzleFlashEffect',
                        'RackSlavedToTurret'):
                weapon[key] = deepcopy(heavy_cannon[key])
            weapon['RangeCategory'] = 'UWRC_DirectFire'
            weapon['ProjectileId'] = '/' + AAT_BOLT
            weapon['Audio'] = deepcopy(heavy_audio)
            weapon.pop('FiringRandomness', None)
            weapon.pop('ValidateFiringTrajectory', None)
        else:
            weapon['RangeCategory'] = 'UWRC_DirectFire'
        weapons[index] = weapon
    return weapons

def heavy_blast():
    atte_root = 'effects/clonewars/atte/heavy/'
    aat_root = 'effects/clonewars/aat/heavy/'
    payload = {}
    with ZipFile(GAME / 'zzzzzz_SC2_CloneWars_ATTE.scd') as archive:
        name = 'mods/DLC1/shadow/units/zzzz_clonewars_atte_unit.bp'
        cannon = LiteralTable(archive.read(name).decode()).blueprint()['Weapons'][1]
        module = archive.read(ATTE_EFFECTS)
        payload[AAT_EFFECTS] = module.replace(atte_root.encode(), aat_root.encode()).replace(b'blue_', b'red_')
        script_path = ATTE_BOLT.replace('_proj.bp', '_script.lua')
        payload[AAT_BOLT.replace('_proj.bp', '_script.lua')] = archive.read(script_path).replace(
            b'ATTEHeavy', b'AATHeavy'
        ).replace(b'local Blue', b'local Red').replace(b'Blue.', b'Red.')
        payload[AAT_BOLT] = archive.read(ATTE_BOLT).replace(
            b'/atteheavybolt/atteheavybolt_proj', b'/aatheavybolt/aatheavybolt_proj'
        ).replace(b'Heavy blue blaster', b'Heavy red blaster').replace(b"'UEF'", b"'CYBRAN'")
        for effect, blue_ramp, red_ramp in (
            ('bolt_trail', 'ramp_blue_02.dds', 'ramp/ra_0120_trail.dds'),
            ('bolt_glow', 'ramp_blue_green.dds', 'ramp_red_05.dds'),
            ('impact_flash', 'ramp_blue_green.dds', 'ramp_red_14.dds'),
        ):
            source = archive.read(f'{atte_root}blue_{effect}_emit.bp')
            assert blue_ramp.encode() in source
            payload[f'{aat_root}red_{effect}_emit.bp'] = source.replace(
                blue_ramp.encode(), red_ramp.encode()
            ).replace(b'rb_0030_33.dds', b'rb_0031_12.dds')
    assert cannon['RangeCategory'] == 'UWRC_IndirectFire'
    return cannon, payload

def build():
    # Use the current effective DLC research source so existing GAR edits survive.
    candidates = []
    for archive in sorted(GAME.glob('*.scd'), key=lambda p: p.name.lower()):
        if archive.name == ARCHIVE:
            continue
        with ZipFile(archive) as existing:
            assert not any(UNIT in name.lower() for name in existing.namelist()), archive
            if RESEARCH in existing.namelist():
                candidates.append(existing.read(RESEARCH))
    assert candidates and not candidates[-1].startswith(b'\x1bLua')
    current = text(candidates[-1])
    # Refresh the node already installed by this builder on subsequent runs.
    if NODE in current:
        current, count = re.subn(r'^    CLU_AAT = \{\n.*?^    \},\n', '', current,
                                 flags=re.MULTILINE | re.DOTALL)
        assert count == 1 and NODE not in current
    research = insert_before(current, '    CLU_MISSILETRUCK = {', f"""    {NODE} = {{
        NAME = '{NAME}',
        TIME = 0,
        COST = 5,
        ENERGY = 0,
        MASS = 0,
        INFO = 'Unlock the Armored Assault Tank, a medium battle tank with a long-range main cannon.',
        CATS = 'ucb0001',
        BuildRestrictionRemoval = {{ '{UNIT}' }},
        PREREQUISITES = 'CLB_REGENERATION',
        tip_affects = 'Built By: Land Factory',
        tip_type = 'Unit Unlock',
    }},
""")

    with ZipFile(BASE / 'z_uncompiled_lua_dlc1.scd') as source:
        restrictions = text(source.read('uncompiled/' + RESTRICTIONS))
        layout = text(source.read('uncompiled/' + LAYOUT))
        bp = LiteralTable(source.read('uncompiled/' + DLC + 'Units/Cybran/UCL0104/UCL0104_unit.bp').decode()).blueprint()
        blaster = LiteralTable(source.read('uncompiled/' + DLC + 'Units/Cybran/UCL0103/UCL0103_unit.bp').decode()).blueprint()['Weapons'][2]
        megalith = LiteralTable(source.read('uncompiled/' + DLC + 'Units/Cybran/UCX0101/UCX0101_unit.bp').decode()).blueprint()
    restrictions = insert_before(restrictions, '    categories.ucl0104,', f'    categories.{UNIT}, -- AAT\n')
    land = layout.split('    CYBRAN_LAND = {', 1)[1].split('    CYBRAN_NAVAL = {', 1)[0]
    assert ('1', '3') not in re.findall(r'col\s*=\s*(\d+),\s*row\s*=\s*(\d+)', land)
    layout = insert_before(layout, '        CLU_MISSILETRUCK = {', f"""        {NODE} = {{
            icon = '/{ICON}',
            col = 1,
            row = 3,
        }},
""")

    bp.update(BlueprintId=UNIT, Description='Medium Battle Tank',
              ScriptModule=f'/{MODEL}AAT_script.lua', ScriptClass='AAT',
              StrategicIconName='icon_land_directfire')
    bp['Display']['DisplayName'] = NAME
    bp['Display']['UniformScale'] = LORE_SCALE
    bp.update(SizeX=3.15, SizeY=1.82, SizeZ=3.64, SelectionSizeX=3.15,
              SelectionSizeZ=3.64, LifeBarOffset=2, LifeBarSize=2.48)
    bp['Navigation']['Radius'] = 1.57
    bp['Physics'].update(MaxSpeed=3.2, MaxSpeedReverse=.56, MaxAcceleration=3, MaxBrake=4, TurnRate=65)
    bp['Defense'].update(Health=1500, MaxHealth=1500, RegenRate=4)
    bp['Defense']['Shield'].update(ShieldMaxHealth=150, ShieldRegenRate=3,
                                   SizeX=3.15, SizeY=1.82, SizeZ=3.64)
    bp['Economy'].update(MassValue=85, EnergyValue=220, BuildTime=19)
    bp['General'].update(UnitName=NAME, BuildIconIndex=5, BuildIconPage=1,
                         BuildIconSortPriority=45, ExperienceTable='TANK', ExperienceValue=2500)
    categories = [value for value in dict.fromkeys(bp['Categories'].values())
                  if value not in {'SILO', 'INDIRECTFIRE', 'OVERLAYINDIRECTFIRE'}]
    bp['Categories'] = dict(enumerate(categories + [
        'TANK', 'DIRECTFIRE', 'OVERLAYDIRECTFIRE',
    ], 1))
    assert {'BUILTBYFACTORY', 'CYBRAN', 'LAND', 'TECH1'} <= set(bp['Categories'].values())
    # The engine uses the attacker's primary weapon for its primary range overlay.
    bp['AI']['Attacker']['PrimaryWeapon'] = 'Main'
    detonate = next(weapon for weapon in bp['Weapons'].values() if weapon['Label'] == 'PowerDetonate')
    heavy_audio = {'Fire': next(weapon['Audio']['Fire'] for weapon in megalith['Weapons'].values()
                                if 'Megabot_Proton_Cannon' in weapon.get('Audio', {}).get('Fire', ''))}
    cannon, effects = heavy_blast()
    bp['Weapons'] = tank_weapons(blaster, cannon, heavy_audio)
    bp['Weapons'][4] = detonate
    bp['Display']['SimulationBones'] = dict(enumerate(
        (weapon['TurretBoneMuzzle'] for weapon in list(bp['Weapons'].values())[:3]), 1
    ))
    for animation in ('AnimationWalk', 'AnimationOpen', 'AnimationDeath'):
        bp['Display'].pop(animation, None)
    bp['Death'].pop('DestructionParts', None)
    model = '/' + MODEL + 'AAT'
    for lod, level in bp['Display']['Mesh']['LODs'].items():
        level['MeshName'] = f'{model}_lod{lod-1}.scm'
        material = level['MaterialSets'][1]['Materials'][1]
        material['ShaderMacros'] = 'ambient_lighting, diffuse_lighting, ambient_occlusion, point_cloud'
        for channel in ('Diffuse', 'Normal', 'Mask', 'Team'):
            material[channel + 'Name'] = f'{model}_{channel}.dds'
    unit_path = f'mods/DLC1/base/Units/Cybran/{UNIT.upper()}/{UNIT.upper()}_unit.bp'
    blueprint = 'UnitBlueprint ' + lua(bp) + '\n'
    assert LiteralTable(blueprint).blueprint() == bp

    art = tank_icon()
    payload = {
        RESEARCH: research.encode('latin1'),
        RESTRICTIONS: restrictions.encode('latin1'),
        LAYOUT: layout.encode('latin1'),
        unit_path: blueprint.encode(),
        ICON: art,
        f'textures/ui/common/icons/hud/pc_units/{UNIT}.dds': art,
        f'textures/ui/common/icons/hud/units/{UNIT}_d.dds': art,
        f'textures/ui/common/icons/hud/units/{UNIT}_h.dds': art,
        f'textures/ui/common/icons/hud/units/large/{UNIT}.dds': art,
        f'textures/ui/common/icons/units/{UNIT}_icon.dds': art,
    }
    rig = json.loads((WORK / 'rig.json').read_text())
    payload.update(model_assets(rig))
    payload.update(effects)
    names = set(scm_v7.read(payload[MODEL + 'AAT_lod0.win.scm'])['names'])
    for weapon in list(bp['Weapons'].values())[:3]:
        assert {weapon[key] for key in ('TurretBoneYaw', 'TurretBonePitch', 'TurretBoneMuzzle')} <= names
    payload[MODEL + 'AAT_script.lua'] = Path(__file__).with_name('AAT_script.lua').read_bytes()
    payload['AAT_ATTRIBUTION.txt'] = b'''-Star Wars- AAT by ARKON MAREK (CC BY 4.0).
https://sketchfab.com/3d-models/star-wars-aat-9ed126f4616a482fabee52b0e0d46e52
https://creativecommons.org/licenses/by/4.0/
Adapted with new LODs, texture atlas, game conversion, and hologram render.
'''
    return payload

def install_dlc_resources(payload):
    # These resources can be loaded before normal overlays are applied.
    replacements = {path.lower(): payload[path] for path in (RESEARCH, RESTRICTIONS, LAYOUT)}
    backups = ROOT / 'local/history/AAT-research'
    backups.mkdir(parents=True, exist_ok=True)
    staged = []
    for path in GAME.glob('*.scd'):
        if path.name == ARCHIVE:
            continue
        with ZipFile(path) as source:
            changes = {
                name: replacements[name.lower()] for name in source.namelist()
                if name.lower() in replacements and source.read(name) != replacements[name.lower()]
            }
            if not changes:
                continue
            temporary = path.with_suffix('.aat-stage')
            with ZipFile(temporary, 'w') as target:
                target.comment = source.comment
                for item in source.infolist():
                    raw = changes[item.filename] if item.filename in changes else source.read(item)
                    target.writestr(copy(item), raw)
            with ZipFile(temporary) as target:
                assert target.testzip() is None and target.namelist() == source.namelist()
                for name in target.namelist():
                    assert target.read(name) == (changes[name] if name in changes else source.read(name))
        digest = sha256(path.read_bytes()).hexdigest()[:12]
        backup = backups / f'{digest}_{path.name}'
        if not backup.exists():
            shutil.copyfile(path, backup)
        staged.append((path, temporary))
    for path, temporary in staged:
        temporary.replace(path)
    print(f'Updated and verified the DLC resources in {len(staged)} existing archives.')

if __name__ == '__main__':
    payload = build()
    target = GAME / ARCHIVE
    temporary = target.with_suffix('.tmp')
    with ZipFile(temporary, 'w', ZIP_DEFLATED) as archive:
        for path, raw in sorted(payload.items()):
            archive.writestr(path, raw)
    with ZipFile(temporary) as archive:
        assert archive.testzip() is None
        assert all(archive.read(path) == raw for path, raw in payload.items())
    install_dlc_resources(payload)
    temporary.replace(target)
    print(f'Installed {NODE} with {len(payload)} verified entries in {target}')
