import zipfile,re
from pathlib import Path
p=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata')
effective={}
for a in sorted(p.glob('*.scd'),key=lambda p:p.name.lower()):
 with zipfile.ZipFile(a) as z:
  for n in z.namelist():
   if n.lower().endswith(('/strings_db.lua','/research.lua','/achievements.lua')):effective[n.lower()]=(a.name,n,z.read(n))
for key,(a,n,b) in effective.items():
 for m in re.finditer(rb'Jack\s*hammer|AV-7',b,re.I):
  print(a,n,repr(b[max(0,m.start()-90):m.end()+140]))
