import json
from pathlib import Path
r=Path.cwd();old=json.loads((r/'work/rtt/revisions/plain-hull-test-2/Package-validation.json').read_text(encoding='utf-8'));p=r/'outputs/RTT/Package-validation.json';new=json.loads(p.read_text(encoding='utf-8'))
for axis in range(3):
 for end in range(2):assert abs(new['meshes'][0]['bounds'][axis][end]-old['meshes'][0]['bounds'][axis][end]*2)<1e-5
new['visual_scale_relative_to_test_2']=2;new['size_check']='All three mesh dimensions exactly doubled';p.write_text(json.dumps(new,indent=2),encoding='utf-8');print(new['size_check'])
