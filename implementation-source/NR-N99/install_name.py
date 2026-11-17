"""Set the visible Cobra slot name in the dev game's unit and English UI data."""
import sys
from copy import copy
from hashlib import sha256
import shutil
from zipfile import ZIP_DEFLATED, ZipFile

from build_package import GAME, NAME, ROOT

sys.path.insert(0, str(ROOT / 'tools'))
from rename_unit_text import Chunk


LOC = 'loc/us/strings_db.lua'
TARGET = GAME / ('z' * 20 + '_SC2_CloneWars_Persuader_Name.scd')
RESEARCH_NAMES = {
    b'Cobra': NAME.encode(),
    b"Unlock the 'Cobra' Mobile Missile Launcher.": f"Unlock the {NAME}.".encode(),
}


def patch_research(data):
    replacements = {
        b'<LOC RESEARCH_NAME_0079>Cobra': RESEARCH_NAMES[b'Cobra'],
        b"<LOC SC2_RESEARCH_INFO_0078>Unlock the 'Cobra' Mobile Missile Launcher.":
            RESEARCH_NAMES[b"Unlock the 'Cobra' Mobile Missile Launcher."],
    }
    if data.startswith(b'\x1bLua'):
        return Chunk(data, lambda value: replacements.get(value, value)).result()
    for old, new in replacements.items():
        data = data.replace(old.replace(b"'", b"\\'"), new)
        data = data.replace(old, new)
    return data


def install_research():
    # The engine can read DLC research directly from the stock-named archives.
    backups = ROOT / 'local/history/Persuader-research-names'
    changed = 0
    for path in sorted(GAME.glob('*.scd')):
        staged = path.with_suffix('.research-stage')
        with ZipFile(path) as archive:
            edits = {}
            for name in archive.namelist():
                if name.lower().endswith('/research.lua'):
                    data = archive.read(name)
                    if b'<LOC RESEARCH_NAME_0079>Cobra' in data:
                        renamed = patch_research(data)
                        assert renamed != data and b'<LOC RESEARCH_NAME_0079>Cobra' not in renamed
                        edits[name] = renamed
            if not edits:
                continue
            with ZipFile(staged, 'w') as output:
                output.comment = archive.comment
                for item in archive.infolist():
                    output.writestr(copy(item), edits.get(item.filename, archive.read(item)))
            with ZipFile(staged) as output:
                assert output.testzip() is None
                assert output.namelist() == archive.namelist()
                for name in output.namelist():
                    assert output.read(name) == edits.get(name, archive.read(name))
        backups.mkdir(parents=True, exist_ok=True)
        digest = sha256(path.read_bytes()).hexdigest()[:12]
        backup = backups / f'{digest}_{path.name}'
        if not backup.exists():
            shutil.copy2(path, backup)
        staged.replace(path)
        changed += len(edits)
    print(f'Updated {changed} installed research scripts')


def install():
    localization = None
    for path in sorted(GAME.glob('*.scd'), key=lambda path: path.name.lower()):
        if path != TARGET:
            with ZipFile(path) as archive:
                if LOC in archive.namelist():
                    localization = archive.read(LOC)
    assert localization is not None
    assert Chunk(localization, lambda value: value).result() == localization
    renamed = Chunk(localization, lambda value: RESEARCH_NAMES.get(value, value)).result()
    assert all(value + b'\0' in renamed for value in RESEARCH_NAMES.values())

    unit = f"""UnitBlueprint {{
    Merge = true,
    BlueprintId = 'ucl0104',
    Display = {{ DisplayName = '{NAME}' }},
    General = {{ UnitName = '{NAME}' }},
}}
""".encode()
    payload = {LOC: renamed}
    for prefix in ('', 'mods/DLC1/base/', 'mods/DLC1/shadow/', 'mods/CampaignBranch/shadow/'):
        payload[prefix + 'units/zzzzzzzzzz_clonewars_persuader_name_unit.bp'] = unit

    staged = TARGET.with_suffix('.tmp')
    with ZipFile(staged, 'w', ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
    with ZipFile(staged) as archive:
        assert archive.testzip() is None
        assert all(archive.read(name) == data for name, data in payload.items())
    staged.replace(TARGET)
    install_research()
    print(f'Installed {NAME} display name in {TARGET.name}')


if __name__ == '__main__':
    install()
