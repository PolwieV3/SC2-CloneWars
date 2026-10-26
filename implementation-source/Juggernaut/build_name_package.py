from pathlib import Path
import zipfile,struct,re,json,hashlib
r=Path(__file__).parent;out=r.parents[1]/'outputs/Juggernaut';live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata')
def rename(value):
 value=re.sub(rb'\bFatboys\b',b'Juggernauts',value,flags=re.I)
 value=re.sub(rb'\bFatboy\s+(?:II|ll|2)\b',b'HAVw A6 Juggernaut',value,flags=re.I)
 return re.sub(rb'\bFatboy\b',b'Juggernaut',value,flags=re.I)
def rewrite(blob):
 assert blob[:12]==bytes.fromhex('1b4c75615100010404040400')
 offset=12;output=[blob[:12]];shape=[blob[:12]];changes=[]
 def take(n):
  nonlocal offset
  b=blob[offset:offset+n];assert len(b)==n;offset+=n;output.append(b);shape.append(b);return b
 def integer():return struct.unpack('<I',take(4))[0]
 def string(change=False):
  nonlocal offset
  size=struct.unpack_from('<I',blob,offset)[0];offset+=4;b=blob[offset:offset+size];assert len(b)==size;offset+=size
  if size:assert b[-1:]==b'\0'
  new=rename(b) if change else b
  if new!=b:changes.append({'before':b[:-1].decode('utf-8',errors='replace'),'after':new[:-1].decode('utf-8',errors='replace')})
  output.append(struct.pack('<I',len(new))+new);shape.append(b'<string>')
 def function():
  string();take(8);take(4);take(integer()*4)
  for _ in range(integer()):
   tag=take(1)[0]
   if tag==0:pass
   elif tag==1:take(1)
   elif tag==3:take(4)
   elif tag==4:string(True)
   else:raise ValueError(tag)
  for _ in range(integer()):function()
  take(integer()*4)
  for _ in range(integer()):string();take(8)
  for _ in range(integer()):string()
 function();assert offset==len(blob),(offset,len(blob))
 return b''.join(output),changes,hashlib.sha256(b''.join(shape)).hexdigest()
# Begin with effective installed files so previous unit-name edits survive.
effective={};stock=Path(r'B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata')
for p in [stock/'loc_US.scd',stock/'lua.scd',stock/'z_lua_dlc1.scd',*sorted(live.glob('*CloneWars*.scd'))]:
 if p.name=='zzzzz_SC2_CloneWars_Juggernaut_Name.scd':continue
 with zipfile.ZipFile(p) as z:
  for n in z.namelist():
   if n.lower().endswith(('/strings_db.lua','/research.lua','/achievements.lua')):effective[n]=(z.read(n),str(p))
payload={};reports=[]
for n,(before,origin) in effective.items():
 if not before.startswith(b'\x1bLua'):continue
 after,changes,shape=rewrite(before)
 if not changes:continue
 checked,pending,newshape=rewrite(after);assert checked==after and not pending and shape==newshape
 assert b'Fatboy' not in after and b'fatboy' not in after
 payload[n]=after;reports.append({'path':n,'base_archive':origin,'changed_constants':changes,'instruction_and_structure_hash_unchanged':shape})
namebp="UnitBlueprint { Merge = true, BlueprintId = 'uux0101', Display = { DisplayName = 'HAVw A6 Juggernaut' }, General = { UnitName = 'HAVw A6 Juggernaut' } }\n"
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:payload[prefix+'units/zz_clonewars_juggernaut_name_unit.bp']=namebp.encode()
archive=out/'zzzzz_SC2_CloneWars_Juggernaut_Name.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
d={'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'display_name':'HAVw A6 Juggernaut','changed_files':reports,'scope':'Player-facing English name/research/achievement/caption constants only; internal IDs/categories preserved. Existing localization edits retained. Original game archives untouched.','installed':False}
(r/'name-validation.json').write_text(json.dumps(d,indent=2),encoding='utf-8');print(json.dumps({'files':len(reports),'constant_replacements':sum(len(x['changed_constants']) for x in reports),'sha256':d['sha256']}))
