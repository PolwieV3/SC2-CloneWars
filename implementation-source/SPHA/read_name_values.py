import struct,zipfile
p=r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata/zzzzzzzzzz_SC2_CloneWars_UnitNames.scd'
b=zipfile.ZipFile(p).read('loc/us/strings_db.lua');o=12
n=struct.unpack_from('<I',b,o)[0];o+=4+n+12
n=struct.unpack_from('<I',b,o)[0];o+=4;code=struct.unpack_from('<%dI'%n,b,o);o+=4*n
n=struct.unpack_from('<I',b,o)[0];o+=4;constants=[]
for i in range(n):
 t=b[o];o+=1
 if t==4:
  l=struct.unpack_from('<I',b,o)[0];o+=4;v=b[o:o+l-1].decode('utf8',errors='replace');o+=l
 elif t==3:v=struct.unpack_from('<f',b,o)[0];o+=4
 elif t==1:v=b[o];o+=1
 else:v=None
 constants.append(v)
regs={}
for ins in code:
 op=ins&63;a=(ins>>6)&255;bx=ins>>14
 if op==1:regs[a]=constants[bx]
 if op==7 and constants[bx] in ['UNIT_NAME_0289','UNIT_NAME_0290','RESEARCH_NAME_0321','SC2_RESEARCH_INFO_0565']:print(constants[bx],regs.get(a))
