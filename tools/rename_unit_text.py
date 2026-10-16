"""Replace the two reskinned unit names in the development game's text constants."""
from pathlib import Path
import re, struct, hashlib, json, shutil, zipfile

PROJECT = Path(r'C:\Users\gavad\Documents\Codex\2026-10-03\referenced-chatgpt-conversation-this-is-an\outputs\SC2-CloneWars')
OUTPUT = Path(r'C:\Users\gavad\Documents\Codex\2026-10-14\referenced-chatgpt-conversation-this-is-an-2\outputs\Unit-Name-Replacements')
PATTERNS = [
    (rb"'Titan' Assault Bots\b", b"'AT-RTs'"),
    (rb"'Titan' Assault Bot\b", b"'AT-RT'"),
    (rb'\bTitan Assault Bots\b', b'AT-RTs'),
    (rb'\bTitan Assault Bot\b', b'AT-RT'),
    (rb'\bDemolishers\b', b'AT-APs'),
    (rb'\bDemolisher\b', b'AT-AP'),
    (rb'\bTitan\b', b'AT-RT'),
]

def rename(value):
    # Never rename asset paths or an embedded bytecode chunk.
    if value.startswith((b'/', b'\\', b'\x1bLua')): return value
    for pattern, replacement in PATTERNS:
        value = re.sub(pattern, replacement, value, flags=re.I)
    return value

class Chunk:
    def __init__(self, data, transform):
        assert data[:12] == bytes.fromhex('1b4c75615100010404040400')
        self.data = data; self.offset = 12; self.transform = transform; self.changes = []
    def read(self, count):
        value = self.data[self.offset:self.offset + count]
        assert len(value) == count
        self.offset += count
        return value
    def integer(self): return struct.unpack('<I', self.read(4))[0]
    def string(self, constant=False):
        length = self.integer(); value = self.read(length)
        if constant and length:
            assert value[-1:] == b'\0'
            updated = self.transform(value[:-1]) + b'\0'
            if updated != value:
                self.changes.append({'before': value[:-1].decode(errors='replace'), 'after': updated[:-1].decode(errors='replace')})
            value = updated
        return struct.pack('<I', len(value)) + value
    def function(self):
        out = bytearray(self.string()); out += self.read(12)
        count = self.integer(); out += struct.pack('<I', count) + self.read(count * 4)
        count = self.integer(); out += struct.pack('<I', count)
        for _ in range(count):
            kind = self.read(1); out += kind
            if kind == b'\0': pass
            elif kind == b'\1': out += self.read(1)
            elif kind == b'\3': out += self.read(4)
            elif kind == b'\4': out += self.string(True)
            else: raise ValueError('Unknown Lua constant type')
        count = self.integer(); out += struct.pack('<I', count)
        for _ in range(count): out += self.function()
        count = self.integer(); out += struct.pack('<I', count) + self.read(count * 4)
        count = self.integer(); out += struct.pack('<I', count)
        for _ in range(count): out += self.string() + self.read(8)
        count = self.integer(); out += struct.pack('<I', count)
        for _ in range(count): out += self.string()
        return bytes(out)
    def result(self):
        result = self.data[:12] + self.function()
        assert self.offset == len(self.data)
        return result

def patch_data(data):
    if data.startswith(b'\x1bLua'):
        original = Chunk(data, lambda value: value)
        assert original.result() == data, 'Native bytecode did not round-trip'
        patched = Chunk(data, rename); result = patched.result()
        # Independently reparse the changed lengths; code and numbers remain untouched.
        assert Chunk(result, lambda value: value).result() == result
        return result, patched.changes
    updated = rename(data)
    return updated, ([{'before': line.decode(errors='replace'), 'after': rename(line).decode(errors='replace')}
        for line in data.splitlines() if rename(line) != line] if updated != data else [])

def main():
    game = PROJECT / 'local/dev-game/gamedata'
    OUTPUT.mkdir(parents=True, exist_ok=True)
    changes = []; archive_report = []
    for archive in sorted(game.glob('*.scd')):
        replacements = {}
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                if not entry.filename.lower().endswith(('.lua', '.bp', '.txt', '.strings')): continue
                data = z.read(entry.filename)
                if not re.search(rb'\b(?:Demolisher|Demolishers|Titan)\b', data, re.I): continue
                updated, records = patch_data(data)
                if updated != data:
                    replacements[entry.filename] = updated
                    changes.extend({'archive': archive.name, 'entry': entry.filename, **record} for record in records)
        if not replacements: continue
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        backup = OUTPUT / 'backups' / (digest[:12] + '-' + archive.name)
        backup.parent.mkdir(exist_ok=True)
        if not backup.exists(): shutil.copy2(archive, backup)
        built = OUTPUT / archive.name
        with zipfile.ZipFile(backup) as z, zipfile.ZipFile(built, 'w') as updated_zip:
            for entry in z.infolist(): updated_zip.writestr(entry, replacements.get(entry.filename, z.read(entry.filename)))
        with zipfile.ZipFile(backup) as original, zipfile.ZipFile(built) as patched:
            assert patched.testzip() is None and original.namelist() == patched.namelist()
            assert [n for n in original.namelist() if original.read(n) != patched.read(n)] == [n for n in original.namelist() if n in replacements]
        shutil.copy2(built, archive)
        archive_report.append({'archive': archive.name, 'backup': str(backup), 'changed_entries': list(replacements),
                               'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()})
    # Keep GAR's ownership checks and future rebuild pipeline consistent with the text-only patch.
    manifest_path = OUTPUT.parent / 'GAR-Dev-Mode/evidence/install.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['patched_lua_sha256'] = hashlib.sha256((game / 'lua.scd').read_bytes()).hexdigest()
    manifest['unit_text_patch'] = str(OUTPUT / 'verification.json')
    manifest_path.write_text(json.dumps(manifest, indent=2))
    installed_tool = PROJECT / 'tools/rename_unit_text.py'
    if Path(__file__).resolve() != installed_tool.resolve(): shutil.copy2(__file__, installed_tool)
    report = {'replacements': {'Demolisher': 'AT-AP', 'Titan / Titan Assault Bot': 'AT-RT'},
              'game': str(game.parent), 'archives': archive_report, 'string_changes': changes,
              'bytecode_code_and_numeric_constants_preserved': True, 'steam_installation_untouched': True,
              'engine_text_verified': False}
    (OUTPUT / 'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'patched_archives': len(archive_report), 'changed_strings': len(changes),
                      'archive_entries': {a['archive']: len(a['changed_entries']) for a in archive_report}}, indent=2))

if __name__ == '__main__': main()
