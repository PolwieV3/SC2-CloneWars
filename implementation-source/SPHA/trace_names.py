import zipfile,re
from pathlib import Path
p=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata')
effective={}
for a in sorted(p.glob('*.scd'),key=lambda p:p.name.lower()):
 with zipfile.ZipFile(a) as z:
  for n in z.namelist():
   if n.lower().endswith(('.lua','.bp')) and not n.lower().startswith('uncompiled/'):
    b=z.read(n)
    if b'Jackhammer' in b or 'research' in n.lower() or '/loc/' in n.lower() or n.lower().startswith('loc/'):effective[n.lower()]=(a.name,n,b)
for a,n,b in effective.values():
 if re.search(rb'Jackhammer',b,re.I):print(a,n,len(b))
