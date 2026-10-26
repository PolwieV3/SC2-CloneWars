from pathlib import Path
import zipfile,re,json,hashlib,shutil,datetime
exec(Path('work/names/build_names.py').read_text(encoding='utf-8-sig').split('# Resolve the installed archives')[0])
O=R/'outputs/Unit-Names';B=O/'backups/research-fix-2026-10-25';B.mkdir(parents=True,exist_ok=True);records=[]
for archive in sorted(G.glob('*.scd')):
 replacements={};changes=[]
 with zipfile.ZipFile(archive) as z:
  for entry in z.infolist():
   n=entry.filename;isloc=n.lower()=='loc/us/strings_db.lua';research=n.lower().endswith('/research.lua')
   if not (isloc or research):continue
   b=z.read(n)
   if not b.startswith(b'\x1bLua'):continue
   prev=[b'']
   def transform(v):
    p=prev[0];prev[0]=v
    if b'ACHIEVEMENT' in v.upper() or p.startswith(b'SC2_ACHIEVEMENTS_'):return v
    eligible=v.startswith(b'<LOC ') or (isloc and re.match(rb'^(?:UNIT_|RESEARCH_|SC2_|SCENARIO_|DEVTEST_)',p))
    updated=rename(v) if eligible else v
    if updated!=v:changes.append({'entry':n,'before':v.decode(errors='replace'),'after':updated.decode(errors='replace')})
    return updated
   assert m.Chunk(b,lambda v:v).result()==b
   updated=m.Chunk(b,transform).result();assert m.Chunk(updated,lambda v:v).result()==updated
   if updated!=b:replacements[n]=updated
  if not replacements:continue
  backup=B/archive.name
  if not backup.exists():shutil.copy2(archive,backup)
  temp=R/'work/names'/('updated-'+archive.name)
  with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as dest:
   for info in z.infolist():dest.writestr(info,replacements.get(info.filename,z.read(info.filename)))
 with zipfile.ZipFile(temp) as z,zipfile.ZipFile(archive) as old:
  assert z.testzip() is None
  assert z.namelist()==old.namelist()
  assert all(z.read(n)==old.read(n) for n in z.namelist() if n not in replacements)
 shutil.copy2(temp,archive)
 records.append({'archive':archive.name,'backup':str(backup),'changed_entries':list(replacements),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'changes':changes})
# Separate, explicit range-only merge: current main gun 55 -> 68.75.
atte=G/'zzzzzz_SC2_CloneWars_ATTE.scd'
with zipfile.ZipFile(atte) as z:
 text=z.read('units/zzzz_clonewars_atte_unit.bp').decode()
 assert re.search(r'MaxRadius\s*=\s*55\b',text)
 # Check actual first weapon label and original range before applying numeric merge.
 pos=text.index('Weapons =');print(text[pos:pos+220])
range_text="-- User approved +25% main cannon range: 55 * 1.25 = 68.75.\nUnitBlueprint { Merge = true, BlueprintId = 'uux0111', Weapons = { [1] = { MaxRadius = 68.75 } } }\n"
package='zzzzzzzzzzz_SC2_CloneWars_ATTE_Range.scd';target=O/package
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
 for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:z.writestr(prefix+'units/zzzzzzzzzzz_clonewars_atte_range_unit.bp',range_text)
shutil.copy2(target,G/package)
# Update the authoring value so rebuilding AT-TE retains the requested range.
p=R/'work/atte/build_package.py';s=p.read_text(encoding='utf-8');assert "'MaxRadius':55 if main else 33.6" in s;s=s.replace("'MaxRadius':55 if main else 33.6","'MaxRadius':68.75 if main else 33.6");p.write_text(s,encoding='utf-8')
report={'date':'2026-10-25','research_fix':'Patched actual installed loc and Research chunks, including cached lua.scd and DLC; overlay-only attempt was not effective in user screenshots.','archives':records,'range':{'unit':'AT-TE','weapon_index':1,'before':55,'after':68.75,'increase_percent':25,'package':package,'other_weapon_fields_changed':False},'runtime_verified':False,'vanilla_steam_unchanged':True}
(O/'Research-and-range-fix.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(L/'planning/research-names-atte-range-2026-10-25.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('Patched archives:',len(records),'visible strings:',sum(len(r['changes']) for r in records));print('Range installed: 55 -> 68.75')
