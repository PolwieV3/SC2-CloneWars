from PIL import Image
from pathlib import Path
r=Path('work/juggernaut');im=Image.new('RGBA',(2048,2048),(59,61,56,255))
for i in range(4):
 p=r/f'material-{i}.png';src=Image.open(p).convert('RGBA');src.putalpha(255);src=src.resize((512,512),Image.Resampling.LANCZOS);im.paste(src,(i*512,0))
# Private gun-metal swatches in the unused lower atlas band.
from PIL import ImageDraw
draw=ImageDraw.Draw(im)
for x,color in [(0,(62,68,72,255)),(512,(106,114,118,255)),(1024,(12,16,19,255))]:draw.rectangle((x,1536,x+511,2047),fill=color)
from PIL import ImageOps
wear=ImageOps.grayscale(Image.open(r/'material-0.png').convert('RGB').crop((64,64,320,320))).resize((512,512),Image.Resampling.LANCZOS)
for x,black,white in [(0,(36,39,40),(137,143,140)),(512,(48,51,52),(164,170,166)),(1536,(74,71,65),(197,195,184))]:
 patch=ImageOps.colorize(wear,black,white).convert('RGBA');im.paste(patch,(x,1536))
im.save(r/'atlas.png')
