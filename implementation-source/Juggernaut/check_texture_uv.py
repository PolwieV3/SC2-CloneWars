from PIL import Image
from pathlib import Path
from io import BytesIO
import zipfile,sys,json,collections
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
r=Path('work/juggernaut');out=Path('outputs/Juggernaut');reports=[]
for label,p in [('before',r/'revisions/pre-roof-side-weapons-2/zz_SC2_CloneWars_Juggernaut_Model.scd'),('after',out/'zz_SC2_CloneWars_Juggernaut_Model.scd')]:
 with zipfile.ZipFile(p) as z:
  m=scm_v7.read(z.read('units/CloneWars/Juggernaut/UUX0101_lod0.scm'));im=Image.open(BytesIO(z.read('units/CloneWars/Juggernaut/UUX0101_Diffuse.dds'))).convert('RGB');vs=[v for v in m['vertices'] if v[16]==0];colors=[im.getpixel((min(im.width-1,int((v[12]%1)*im.width)),min(im.height-1,int((v[13]%1)*im.height)))) for v in vs];distinct=len(set(colors));uniform=collections.Counter(colors).most_common(1)[0][1]/len(colors);reports.append({'revision':label,'distinct_hull_texture_samples':distinct,'largest_single_color_fraction':uniform})
assert reports[0]['largest_single_color_fraction']>.95;assert reports[1]['distinct_hull_texture_samples']>100
(r/'texture-uv-validation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');(out/'Texture-UV-validation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');print(json.dumps(reports))
