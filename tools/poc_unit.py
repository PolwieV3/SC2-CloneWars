"""Inspect actual POC source tables and extract a private model-work reference pack.

The parser accepts only literal Lua tables. It never executes game code. A source
merge comparison is useful evidence but does not simulate the engine or load order.
"""
import ast
import copy
import csv
import hashlib
import json
import pathlib
import re
import zipfile

from snapshot import ROOT

TOKEN = re.compile(r'''\s+|--\[\[.*?\]\]|--[^\n]*|\[\[.*?\]\]|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z_]\w*|[{}\[\]=,;]''', re.S)


class LiteralTable:
    def __init__(self, source):
        self.tokens = []
        pos = 0
        for m in TOKEN.finditer(source):
            if m.start() != pos:
                raise ValueError(f'Unsupported Lua syntax at offset {pos}')
            pos = m.end()
            text = m.group()
            if text.isspace() or text.startswith('--'):
                continue
            self.tokens.append(text)
        if pos != len(source):
            raise ValueError(f'Unsupported Lua syntax at offset {pos}')
        self.i = 0

    def take(self, expected=None):
        token = self.tokens[self.i]
        self.i += 1
        if expected is not None and token != expected:
            raise ValueError(f'Expected {expected}, found {token}')
        return token

    def value(self):
        token = self.take()
        if token == '{':
            result = {}
            index = 1
            while self.tokens[self.i] != '}':
                if self.tokens[self.i] == '[':
                    self.take('['); key = self.value(); self.take(']'); self.take('=')
                    value = self.value()
                elif self.i + 1 < len(self.tokens) and self.tokens[self.i + 1] == '=':
                    key = self.take(); self.take('='); value = self.value()
                else:
                    key = index; index += 1; value = self.value()
                if key in result:
                    raise ValueError(f'Duplicate table key: {key}')
                result[key] = value
                if self.tokens[self.i] in {',', ';'}:
                    self.take()
                elif self.tokens[self.i] != '}':
                    raise ValueError('Missing table field separator')
            self.take('}')
            return result
        if token.startswith(('\'', '"')):
            return ast.literal_eval(token)
        if token.startswith('[['):
            return token[2:-2]
        if token in {'true', 'false', 'nil'}:
            return {'true': True, 'false': False, 'nil': None}[token]
        if re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', token):
            return float(token) if any(c in token for c in '.eE') else int(token)
        raise ValueError(f'Unsupported literal: {token}')

    def blueprint(self):
        self.take('UnitBlueprint')
        result = self.value()
        if self.i != len(self.tokens):
            raise ValueError('Trailing Lua source after blueprint')
        return result


def merge(dest, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(dest.get(key), dict):
            merge(dest[key], value)
        else:
            dest[key] = copy.deepcopy(value)


def differences(before, after, path=''):
    changes = []
    for key in before.keys() | after.keys():
        here = f'{path}.{key}' if path else str(key)
        if key not in before or key not in after:
            changes.append(here)
        elif isinstance(before[key], dict) and isinstance(after[key], dict):
            changes.extend(differences(before[key], after[key], here))
        elif before[key] != after[key]:
            changes.append(here)
    return sorted(changes)


def values(table):
    for value in table.values():
        if isinstance(value, dict):
            yield from values(value)
        elif isinstance(value, str):
            yield value


def main():
    data = ROOT / 'local/installed-snapshot/gamedata'
    packet = ROOT / 'local/reference/UUL0101'
    patch = LiteralTable((ROOT / 'src/units/zz_clonewars_rename_unit.bp').read_text()).blueprint()
    if set(patch) != {'Merge', 'BlueprintId', 'Display', 'General'} or patch['Merge'] is not True or patch['BlueprintId'] != 'uul0101':
        raise ValueError('Unexpected POC patch metadata')
    name_patch = {key: value for key, value in patch.items() if key not in {'Merge', 'BlueprintId'}}
    variants = []
    sources = [('base', 'uncompiled_lua.scd', 'uncompiled/Units/UEF/UUL0101/UUL0101_unit.bp'),
               ('dlc', 'z_uncompiled_lua_dlc1.scd', 'uncompiled/mods/DLC1/shadow/Units/UEF/UUL0101/UUL0101_unit.bp')]
    for scope, archive, path in sources:
        with zipfile.ZipFile(data / archive) as z:
            raw = z.read(path)
        original = LiteralTable(raw.decode('utf-8').replace('\r', '')).blueprint()
        overridden = copy.deepcopy(original)
        merge(overridden, name_patch)
        changed = differences(original, overridden)
        if changed != ['Display.DisplayName', 'General.UnitName']:
            raise ValueError(f'Unexpected source changes in {scope}: {changed}')
        weapons = [{k: weapon[k] for k in ('Label', 'Damage', 'RateOfFire', 'MaxRadius', 'ProjectileId', 'MuzzleSalvoSize') if k in weapon}
                   for weapon in original['Weapons'].values()]
        refs = sorted(set(values(original)))
        variants.append({'scope': scope, 'archive': archive, 'path': path,
                         'source_sha256': hashlib.sha256(raw).hexdigest(),
                         'original_display_name': original['Display']['DisplayName'],
                         'health': original['Defense']['MaxHealth'],
                         'economy': original['Economy'],
                         'speed': original['Physics']['MaxSpeed'],
                         'weapons': weapons,
                         'research_upgrade_ids': sorted(original.get('ResearchUpgrades', {})),
                         'audio_events': [v for v in refs if v.startswith('SC2/')],
                         'texture_references': [v for v in refs if v.lower().endswith('.dds')],
                         'changed_source_fields': changed,
                         'all_other_source_fields_equal': True})
    assets = []
    # Keep game-derived assets private and out of the distributable archive and Git.
    for archive in sorted(data.glob('*.scd')):
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                path = item.filename
                if item.is_dir() or not ('/uul0101/' in '/' + path.lower() or 'uul0101_icon' in path.lower()):
                    continue
                rel = pathlib.PurePosixPath(path)
                if rel.is_absolute() or '..' in rel.parts or ':' in path:
                    raise ValueError(f'Unsafe archive path: {path}')
                dest = packet / archive.stem / pathlib.Path(*rel.parts)
                raw = z.read(item)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(raw)
                assets.append({'archive': archive.name, 'path': path, 'bytes': len(raw),
                               'sha256': hashlib.sha256(raw).hexdigest(),
                               'reference_path': dest.relative_to(ROOT).as_posix()})
    with (ROOT / 'inventory/poc-assets.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['archive', 'path', 'bytes', 'sha256', 'reference_path'])
        w.writeheader(); w.writerows(assets)
    manifest = json.loads((ROOT / 'inventory/snapshot-manifest.json').read_text())
    report = {'unit_id': 'uul0101', 'baseline': manifest['baseline'],
              'reference_files': len(assets), 'variants': variants,
              'validation': 'PASS: literal source table merge changes only both name fields for base and DLC',
              'limitation': 'Source-table comparison does not verify compiled blueprint/source equivalence, engine preprocessing, load order or gameplay.'}
    (ROOT / 'inventory/poc-unit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'unit_id': 'uul0101', 'reference_files': len(assets), 'validation': report['validation']}))


if __name__ == '__main__':
    main()
