from pathlib import Path
import zipfile
from PIL import Image,ImageEnhance
r=Path.cwd();w=r/'work/rtt';src=r/'outputs/Approved-Models/RTT/RM-09 Shuttle'
im=Image.open(src/'rep_fly_command.dds').convert('RGB').convert('RGBA').resize((1024,1024));atlas=Image.new('RGBA',(1024,2048),(150,155,162,255));atlas.paste(im,(0,0))
with zipfile.ZipFile('B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata/units.scd') as z:
 n=next(n for n in z.namelist() if '/uul0201/' in n.lower() and '_diffuse.' in n.lower());p=w/'native-diffuse.dds';p.write_bytes(z.read(n));tex=Image.open(p).convert('RGB').resize((1024,1024));tex=ImageEnhance.Color(tex).enhance(.15);tex=ImageEnhance.Brightness(tex).enhance(1.5);atlas.paste(tex,(0,1024))
# Palette swatches reserved in bottom edge for custom machinery.
from PIL import ImageDraw
d=ImageDraw.Draw(atlas);d.rectangle((0,2016,255,2047),fill=(195,202,210,255));d.rectangle((256,2016,511,2047),fill=(40,47,56,255));d.rectangle((512,2016,767,2047),fill=(34,154,230,255));d.rectangle((768,2016,1023,2047),fill=(135,35,35,255));atlas.save(w/'atlas.png')
