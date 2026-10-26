from pathlib import Path
import zipfile,sys,json
p=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(p/'tools'));from rename_unit_text import Chunk
result=[]
for a in (p/'local/dev-game/gamedata').glob('*.scd'):
 if 'uncompiled' in a.name.lower():continue
 with zipfile.ZipFile(a) as z:
  for n in z.namelist():
   if n.lower()!='mods/dlc1/shadow/lua/sim/research.lua':continue
   data=z.read(n)
   if data.startswith(b'\x1bLua'):
    vals=[];Chunk(data,lambda s:vals.append(s) or s).result()
   else:
    import re
    vals=[token[1:-1] for token in re.findall(rb"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"",data)]
   for k in [b'RESEARCH_NAME_0321',b'RESEARCH_NAME_0322',b'SC2_RESEARCH_INFO_0565',b'SC2_RESEARCH_INFO_0566']:
    assert not any(s.startswith(b'<LOC '+k+b'>') for s in vals),(a.name,k)
   assert b'SPHA-T' in vals and b'ISP Field Engineer' in vals,a.name
   result.append(a.name)
print('Verified direct literal titles in all installed DLC Research.lua copies:',result)
