from pathlib import Path
import zipfile,json
G=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata');W=Path('work/tank-conversion');W.mkdir(exist_ok=True)
for name in ['zz_SC2_CloneWars_TX130_Model.scd','zz_SC2_CloneWars_TX130_Blaster.scd','zz_SC2_CloneWars_UTAA_Model.scd','zz_SC2_CloneWars_UTAT_Model.scd']:
 p=G/name
 with zipfile.ZipFile(p) as z:
  print(name)
  for n in z.namelist():
   if n.endswith(('.lua','_unit.bp')):
    b=z.read(n);target=W/name/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);print(n)
with zipfile.ZipFile('B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata/uncompiled_lua.scd') as z:
 for n in z.namelist():
  if '/UUL0101/' in n and n.endswith(('.lua','.bp')):
   p=W/'native'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
