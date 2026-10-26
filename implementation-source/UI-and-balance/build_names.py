from pathlib import Path
import importlib.util,zipfile,re,json,hashlib,shutil
R=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');L=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars');G=L/'local/dev-game/gamedata';O=R/'outputs/Unit-Names';O.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('rename',L/'tools/rename_unit_text.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
mapping={'uul0101':'TX-130 Saber Tank','uul0102':'AT-AP','uul0103':'AT-RT','uul0104':'A5-RX','uul0105':'UT-AA','uul0201':'RTT Shield Transport','uul0203':'UT-AT','uux0101':'HAVw A6 Juggernaut','uux0111':'AT-TE'}
rules=[(rb'\bFatboy\s+(?:II|ll|2)\b',b'HAVw A6 Juggernaut'),(rb'\bFatboys\b',b'HAVw A6 Juggernauts'),(rb'\bFatboy\b',b'HAVw A6 Juggernaut'),(rb'\bSharp[ -]?Shooter\b',b'UT-AT'),(rb'\bKing Kriptor\b',b'AT-TE'),(rb'\bP[ -]?Shield\b',b'RTT Shield Transport'),(rb'\bRock Head Tanks\b',b'TX-130 Saber Tanks'),(rb'\bRock Head Tank\b',b'TX-130 Saber Tank'),(rb'\bRock Heads\b',b'TX-130 Saber Tanks'),(rb'\bRock Head\b',b'TX-130 Saber Tank'),(rb'\bMeteor Missile Trucks\b',b'A5-RXs'),(rb'\bMeteor Missile Truck\b',b'A5-RX'),(rb'\bMeteor\b',b'A5-RX'),(rb'\bArchanist\b',b'UT-AA'),(rb"'?Titan'? Assault Bots\b",b'AT-RTs'),(rb"'?Titan'? Assault Bot\b",b'AT-RT'),(rb'\bTitan\b',b'AT-RT'),(rb'\bDemolishers\b',b'AT-APs'),(rb'\bDemolisher\b',b'AT-AP')]
pattern=re.compile(rb'(?i)\b(?:fatboy|sharp[ -]?shooter|king kriptor|p[ -]?shield|rock head|meteor|archanist|titan|demolisher)\b')
def rename(v):
 for p,r in rules:v=re.sub(p,r,v,flags=re.I)
 if b'AT-TE' in v:v=v.replace(b'Experimental Assault Bot',b'Experimental Assault Walker')
 return v
# Resolve the installed archives in normal alphabetical override order. Only
# localized visible string constants are changed; keys and instructions are retained.
resolved={};sources={};before_hash={a.name:hashlib.sha256(a.read_bytes()).hexdigest() for a in G.glob('*.scd')}
package='zzzzzzzzzz_SC2_CloneWars_UnitNames.scd'
for a in sorted(G.glob('*.scd'),key=lambda p:p.name.lower()):
 if a.name==package:continue
 with zipfile.ZipFile(a) as z:
  for n in z.namelist():
   if n.lower().endswith(('.lua','.bp')):
    b=z.read(n)
    if pattern.search(b):resolved[n.lower()]=(n,b);sources[n.lower()]=a.name
payload={};changes=[]
for key,(n,b) in resolved.items():
 if not b.startswith(b'\x1bLua'):continue
 isloc=n.lower()=='loc/us/strings_db.lua';prev=[b'']
 def transform(v):
  previous=prev[0];prev[0]=v
  if b'ACHIEVEMENT' in v.upper() or previous.startswith(b'SC2_ACHIEVEMENTS_'):return v
  eligible=(v.startswith(b'<LOC ') or (isloc and re.match(rb'^(?:UNIT_|RESEARCH_|SC2_|SCENARIO_|DEVTEST_)',previous)))
  if not eligible or not pattern.search(v):return v
  updated=rename(v)
  if updated!=v:changes.append({'entry':n,'source_archive':sources[key],'before':v.decode(errors='replace'),'after':updated.decode(errors='replace')})
  return updated
 assert m.Chunk(b,lambda v:v).result()==b
 patched=m.Chunk(b,transform).result()
 assert m.Chunk(patched,lambda v:v).result()==patched
 if patched!=b:payload[n]=patched
# Ensure all factory/selection names agree, including campaign and DLC contexts.
for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:
 text='-- Unified visible unit names; no simulation fields changed.\n'
 for uid,name in mapping.items():text+="UnitBlueprint { Merge = true, BlueprintId = '%s', Display = { DisplayName = '%s' }, General = { UnitName = '%s' } }\n"%(uid,name,name)
 payload[prefix+'units/zzzzzzzzzz_clonewars_unit_names_unit.bp']=text.encode('utf-8')
output=O/package
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(output) as z:assert z.testzip() is None
# Verify the effective localization's unit and research values by key.
loc=next(b for n,b in payload.items() if n.lower()=='loc/us/strings_db.lua');vals=[];m.Chunk(loc,lambda v:vals.append(v) or v).result();strings={vals[i].decode():vals[i+1].decode() for i in range(len(vals)-1) if re.match(rb'^(?:UNIT_NAME_|RESEARCH_NAME_|SC2_RESEARCH_INFO_)\d+$',vals[i])}
expected={'RESEARCH_NAME_0274':'UT-AT','RESEARCH_NAME_0277':'HAVw A6 Juggernaut','RESEARCH_NAME_0278':'AT-TE','RESEARCH_NAME_0279':'RTT Shield Transport','UNIT_NAME_0210':'TX-130 Saber Tank','UNIT_NAME_0216':'A5-RX','UNIT_NAME_0218':'UT-AA'}
for key,value in expected.items():assert strings[key]==value,(key,strings.get(key),value)
backup=O/'backups';backup.mkdir(exist_ok=True)
if (G/package).exists():shutil.copy2(G/package,backup/(hashlib.sha256((G/package).read_bytes()).hexdigest()[:12]+'-'+package))
shutil.copy2(output,G/package)
for n,h in before_hash.items():
 if n!=package:assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h,n
report={'date':'2026-10-24','game':str(G.parent),'package':package,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'names':mapping,'changed_visible_strings':len(changes),'entries':list(payload),'verified_localized_values':expected,'changes':changes,'other_archives_unchanged':True,'lua_instructions_and_numeric_constants_preserved':True,'runtime_ui_verified':False,'language':'English (loc/us); translated language databases not changed','rollback':'Remove only '+str(G/package)+' and restart the isolated game.'}
(O/'Verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(L/'planning/unit-names-2026-10-24.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(O/'README.md').write_text('Unified installed replacement names for English UI. Research labels/descriptions and localized unit references updated, plus factory/selection display-name merges for base, DLC and campaign. Existing archives are unchanged. Restart the isolated game to reload. See Verification.json for exact changes and rollback.\n',encoding='utf-8')
print(json.dumps({'strings':len(changes),'entries':len(payload),'verified':expected,'installed':str(G/package)},indent=2))
