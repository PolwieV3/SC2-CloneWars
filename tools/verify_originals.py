"""Read-only verification of source installation against the initial snapshot."""
import json,pathlib
from snapshot import ROOT,digest
m=json.loads((ROOT/'inventory/snapshot-manifest.json').read_text()); source=pathlib.Path(m['source'])
changed=[r['path'] for r in m['files'] if not (source/r['path']).is_file() or digest(source/r['path'])!=r['sha256']]
result={'checked_files':len(m['files']),'changed_files':changed,'passed':not changed}
(ROOT/'inventory/originals-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if changed:raise SystemExit(1)
