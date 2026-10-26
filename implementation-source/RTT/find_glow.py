import zipfile
from pathlib import Path
for p in Path('B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata').glob('*uncompiled*.scd'):
 with zipfile.ZipFile(p) as z:
  for n in z.namelist():
   if 'uul0201_s_' in n.lower():
    print(p.name,n);print(z.read(n).decode('utf-8',errors='replace').encode('ascii','replace').decode())
