"""Read-only installed-source reconstruction and bind-pose mesh measurements."""
from pathlib import Path
import sys,json,re,zipfile,copy,hashlib,csv
ROOT=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
GAME=ROOT/'local/dev-game/gamedata'
OUT=Path(__file__).resolve().parents[1]/'outputs'
sys.path.insert(0,str(ROOT/'tools'))
from poc_unit import LiteralTable,merge
import scm_v7
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
roster=[u for u in json.loads((ROOT/'project-registry/decisions.json').read_text())['units'] if u['faction']=='GAR' and u['id']!='uul0001']
IDS={u['id'] for u in roster}
def parse(raw):
 s=raw.decode('utf-8-sig').replace('\r','')
 s=re.sub(r'\bMeshBlueprint\s*\{','UnitBlueprint {',s)
 p=LiteralTable(s);out=[]
 while p.i<len(p.tokens):p.take('UnitBlueprint');out.append(p.value())
 return out
base={};dlc={};native_refs={}
for filename in ['uncompiled_lua.scd','z_uncompiled_lua_dlc1.scd']:
 with zipfile.ZipFile(GAME/filename) as z:
  for n in z.namelist():
   low=n.lower();m=re.search(r'/units/uef/([^/]+)/\1_unit.bp$',low)
   if not m or m[1] not in IDS or '/campaignbranch/' in low:continue
   isdlc='/mods/dlc1/' in low
   if filename=='uncompiled_lua.scd' and isdlc:continue
   uid=m[1];d=parse(z.read(n))[0];dest=dlc if isdlc else base
   if d.get('Merge'):merge(dest.setdefault(uid,copy.deepcopy(base.get(uid,{}))),d)
   else:dest[uid]=d
   native_refs.setdefault(uid,{})['dlc' if isdlc else 'base']=filename+'!'+n
native={uid:copy.deepcopy(dlc.get(uid,base.get(uid,{}))) for uid in IDS}
current=copy.deepcopy(native);resources={};files={};errors=[];applied={uid:[] for uid in IDS};scale_calls=[]
for a in sorted(GAME.glob('*CloneWars*.scd'),key=lambda a:a.name.lower()):
 with zipfile.ZipFile(a) as z:
  for n in z.namelist():
   low=n.lower();resources[low]=(a.name,n)
   if low.endswith('_unit.bp') and not low.startswith(('uncompiled/','mods/campaignbranch/')):
    b=z.read(n)
    if not b.startswith(b'\x1bLua'):files[low]=(a.name,n,b)
   if low.endswith('.lua'):
    s=z.read(n).decode(errors='replace')
    hits=[l.strip() for l in s.splitlines() if re.search(r'\b(?:SetScale|SetMesh|SetBoneScale)\s*\(',l)]
    if hits:scale_calls.append({'archive':a.name,'member':n,'lines':hits})
for phase in ['base','dlcbase','dlcshadow']:
 for low,(a,n,b) in sorted(files.items()):
  scope='dlcshadow' if low.startswith('mods/dlc1/shadow/') else 'dlcbase' if low.startswith('mods/dlc1/base/') else 'base'
  if scope!=phase:continue
  try:blocks=parse(b)
  except Exception as e:errors.append({'archive':a,'member':n,'error':str(e)});continue
  for patch in blocks:
   uid=str(patch.get('BlueprintId','')).lower()
   if not uid:
    m=re.search(r'/units/uef/([^/]+)/','/'+low)
    if m:uid=m[1]
   if uid not in IDS:continue
   if patch.get('Merge'):merge(current[uid],patch)
   else:current[uid]=copy.deepcopy(patch)
   applied[uid].append({'archive':a,'member':n,'display':patch.get('Display',{})})
def resource(path):
 key=path.lower().lstrip('/')
 if key not in resources and key.endswith('.scm'):key=key[:-4]+'.win.scm'
 if key not in resources:raise KeyError(path)
 a,n=resources[key]
 with zipfile.ZipFile(GAME/a) as z:return z.read(n),a+'!'+n
rows=[]
for u in roster:
 uid=u['id'];d=current[uid];display=d.get('Display',{});mesh=display.get('MeshBlueprint','')
 row={'id':uid,'original':u['original'],'replacement':u['replacement'],'uniform_scale':display.get('UniformScale'), 'base_scale':base.get(uid,{}).get('Display',{}).get('UniformScale'),'native_dlc_scale':native[uid].get('Display',{}).get('UniformScale'),'collision_xyz':[d.get('Size'+k) for k in 'XYZ'],'footprint':d.get('Footprint'),'native_sources':native_refs.get(uid),'patches':applied[uid]}
 if uid=='uul0002':row['replacement']='ISP Engineer (custom engineering variant)'
 if uid=='uul0003d1':row['replacement']='ISP Field Engineer (custom engineering variant)'
 if '/clonewars/' not in mesh.lower():row['status']='Planned GAR replacement; native UEF visual remains in inspected packages';rows.append(row);continue
 try:
  raw,mesh_ref=resource(mesh+'.bp');bp=parse(raw)[0];lods=bp['LODs'];lod=lods[min(lods)];path=lod['MeshName']
  raw,scm_ref=resource(path);m=scm_v7.read(raw);v=[m['vertices'][i] for i in sorted(set(m['indices']))]
  bounds=[[min(p[k] for p in v),max(p[k] for p in v)] for k in range(3)];scale=row['uniform_scale'];dims=[(hi-lo)*scale for lo,hi in bounds]
  row.update(status='Installed GAR mesh; static source reconstruction',mesh_blueprint_source=mesh_ref,scm_source=scm_ref,mesh_sha256=hashlib.sha256(raw).hexdigest(),raw_bounds_xyz=bounds,displayed_lwh=[dims[2],dims[0],dims[1]],vertices=len(v),bones=len(m['bones']))
 except Exception as e:row.update(status='Measurement error',error=str(e))
 rows.append(row)
result={'method':'DLC source baseline plus literal merge patches in base / DLC base / DLC shadow phases; lexical within phase, duplicate virtual paths resolved by archive filename. Source reconstruction, not runtime load-order proof. LOD0 indexed vertices in exported model-space bind pose; X=width,Y=height,Z=length; bounds include weapons and accessories. UniformScale applied once.','rows':rows,'parse_errors':errors,'script_scale_calls':scale_calls}
(OUT/'installed-unit-measurements.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for r in rows:print(r['id'],r['replacement'],r['uniform_scale'],[round(x,4) for x in r.get('displayed_lwh',[])],r.get('error',''))
print('PARSE ERRORS',errors);print('SCRIPT SCALE CALLS',json.dumps(scale_calls))
