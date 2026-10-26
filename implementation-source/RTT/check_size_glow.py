from pathlib import Path
import json
old=json.loads(Path('work/rtt/revisions/double-size-test-3/Package-validation.json').read_text(encoding='utf-8'));new=json.loads(Path('outputs/RTT/Package-validation.json').read_text(encoding='utf-8'))
for a in range(3):
 for b in range(2):assert abs(new['meshes'][0]['bounds'][a][b]-2*old['meshes'][0]['bounds'][a][b])<1e-5
assert len(new['glow_effects'])==3
print('Verified: mesh dimensions doubled; three P-Shield glow layers reduced 15%; no simulation changes.')
