import zipfile,json,sys
from pathlib import Path
r=Path.cwd(); w=r/'work/rtt';sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');import scm_v7
for arc in ['uncompiled_lua.scd','units.scd','z_uncompiled_lua_dlc1.scd']:
 with zipfile.ZipFile(Path('B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata')/arc) as z:
  for n in z.namelist():
   if '/uul0201/' in n.lower():
    p=w/'native'/arc/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    if n.lower().endswith('lod0.win.scm'):
     m=scm_v7.read(z.read(n));(w/'rig.json').write_text(json.dumps({'names':m['names'],'bones':m['bones'],'bounds':[[min(v[i] for v in m['vertices']),max(v[i] for v in m['vertices'])] for i in range(3)]},indent=2),encoding='utf-8');print(m['names'])
