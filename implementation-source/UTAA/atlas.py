from PIL import Image
from pathlib import Path
r=Path('work/archanist');src=Image.open(r/'source/Rep_UTAA.dds').convert('RGB').resize((1024,1024));nat=Image.open(r/'native/units.scd/units/UEF/UUL0105/UUL0105_Diffuse.win.dds').convert('RGB').resize((1024,1024));atlas=Image.new('RGBA',(1024,2048),(255,255,255,255));atlas.paste(src,(0,0));atlas.paste(nat,(0,1024));atlas.paste((100,105,104,255),(0,1008,16,1024));atlas.save(r/'atlas.png')
