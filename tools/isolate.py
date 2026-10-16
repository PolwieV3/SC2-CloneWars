"""Omit shared personal mods/maps mounts only in the development loader."""
from pathlib import Path
from snapshot import ROOT
source=ROOT/'local/installed-snapshot/bin/GameDataPath.lua'
dest=ROOT/'local/dev-game/bin/GameDataPath.lua'
raw=source.read_bytes()
lines=raw.splitlines(keepends=True)
removed=[line for line in lines if b"mount_contents(SHGetFolderPath('PERSONAL')" in line]
if len(removed)!=2:raise SystemExit('Unexpected loader layout; inspect before editing.')
result=b''.join(line for line in lines if line not in removed)
if dest.read_bytes() not in (raw,result):raise SystemExit('Development loader already customized; refusing to overwrite.')
dest.write_bytes(result)
print('Development copy now omits shared personal mods/maps mounts. Original and snapshot untouched.')
