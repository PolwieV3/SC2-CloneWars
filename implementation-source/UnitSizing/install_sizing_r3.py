"""Install one removable visual-size overlay; preserve gameplay configuration."""
from pathlib import Path
import runpy,io,contextlib,json,zipfile,hashlib,copy,math,shutil
W=Path(__file__).resolve().parents[1]
OUT=W/'outputs'/'Sizing-R3'
OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
GAME=ROOT/'local/dev-game/gamedata'
NAME='zzzzzzzzzzzzzzzzzzzz_SC2_CloneWars_UnitSizing_R3.scd'
TARGET=GAME/NAME
if TARGET.exists():raise SystemExit('Sizing R3 already installed; refusing to multiply scales twice.')
factors={'uul0002':1.,'uul0003d1':1.,'uul0101':1.15,'uul0102':1.,'uul0103':1.,'uul0104':1.,'uul0105':1.,'uul0201':1.,'uul0203':1.,'uux0101':1.,'uux0111':1.05,'uux0113d1':1.}
reasons={uid:'Retain R2 visual size; normalize health bar' for uid in factors}
reasons.update({'uux0111':'User requested +5% from current R2 size','uul0101':'User accepted suggested +15% TX-130 increase','uul0102':'Match AT-AP/AT-TE reference height ratio (10.97/9.57), after AT-TE +5%; keep mesh proportions'})
with contextlib.redirect_stdout(io.StringIO()):before=runpy.run_path(str(W/'work/measure_units.py'))
if before['errors']:raise RuntimeError(before['errors'])
byid={r['id']:r for r in before['rows']}
factors['uul0102']=byid['uux0111']['displayed_lwh'][2]*1.05*(10.97/9.57)/byid['uul0102']['displayed_lwh'][2]
original=copy.deepcopy(before['current']);measurements=copy.deepcopy(before['rows'])
(OUT/'before-blueprints.json').write_text(json.dumps(original,indent=2),encoding='utf-8')
(OUT/'before-measurements.json').write_text(json.dumps(before['result'],indent=2),encoding='utf-8')
hashes={a.name:hashlib.sha256(a.read_bytes()).hexdigest() for a in GAME.glob('*CloneWars*.scd')}
(OUT/'before-package-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
visual_fields=['LifeBarSize','LifeBarHeight','LifeBarOffset','SelectionSizeX','SelectionSizeZ','SelectionCenterOffsetX','SelectionCenterOffsetZ','SelectionMeshOffsetX','SelectionMeshOffsetY','SelectionMeshOffsetZ']
patches={};changes=[]
for uid,factor in factors.items():
 d=original[uid];old=d['Display']['UniformScale'];new=round(old*factor,9)
 row=next(r for r in measurements if r['id']==uid)
 changes.append({'id':uid,'name':row['replacement'],'factor':factor,'old_scale':old,'new_scale':new,'old_lwh':row['displayed_lwh'],'new_lwh':[x*factor for x in row['displayed_lwh']],'reason':reasons[uid]})
 patch={'Merge':True,'BlueprintId':uid,'Display':{'UniformScale':new}}
 for key in visual_fields:
  if isinstance(d.get(key),(float,int)):patch[key]=round(d[key]*factor,9)
 # Use compact, bounded UI bars independent of experimental-unit legacy sizes.
 width=row['displayed_lwh'][1]*factor
 height=row['displayed_lwh'][2]*factor
 patch['LifeBarSize']=round(max(.8,min(2.8,width*.5)),4)
 patch['LifeBarHeight']=.16 if uid.startswith('uux') else .12
 patch['LifeBarOffset']=round(min(.45,.2+height*.02),4)
 patches[uid]=patch
def lua(d,indent=0):
 if isinstance(d,dict):
  return '{\n'+''.join(' '*(indent+4)+k+' = '+lua(v,indent+4)+',\n' for k,v in d.items())+' '*indent+'}'
 if isinstance(d,bool):return 'true' if d else 'false'
 if isinstance(d,str):return repr(d)
 return str(d)
payload={}
for uid,patch in patches.items():
 raw=('UnitBlueprint '+lua(patch)+'\n').encode('utf-8')
 for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/']:
  payload[prefix+'units/zzzzzzzzzzzzzzzzzzzz_sizing_r3_'+uid+'_unit.bp']=raw
PACKAGE=OUT/NAME
with zipfile.ZipFile(PACKAGE,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(PACKAGE) as z:
 assert z.testzip() is None
 for n in z.namelist():
  patch=before['parse'](z.read(n))[0]
  assert set(patch)<=set(visual_fields)|{'Merge','BlueprintId','Display'}
  assert set(patch['Display'])=={'UniformScale'}
shutil.copy2(PACKAGE,TARGET)
try:
 with contextlib.redirect_stdout(io.StringIO()):after=runpy.run_path(str(W/'work/measure_units.py'))
 assert not after['errors']
 delta={}
 from poc_unit import differences
 for uid,d in original.items():
  actual=after['current'][uid]
  expected=copy.deepcopy(d)
  if uid in patches:before['merge'](expected,patches[uid])
  assert actual==expected,uid+' unexpected effective blueprint change'
  delta[uid]=differences(d,actual)
 for r in after['rows']:
  if r['id'] not in factors:continue
  prev=next(v for v in measurements if v['id']==r['id'])
  assert r['mesh_sha256']==prev['mesh_sha256']
  assert all(math.isclose(b,a*factors[r['id']],rel_tol=1e-8) for a,b in zip(prev['displayed_lwh'],r['displayed_lwh']))
 for n,sha in hashes.items():assert hashlib.sha256((GAME/n).read_bytes()).hexdigest()==sha,n+' modified unexpectedly'
 assert TARGET.read_bytes()==PACKAGE.read_bytes()
except BaseException:
 # Remove only this newly created overlay on a verification failure.
 TARGET.unlink()
 raise
(OUT/'after-measurements.json').write_text(json.dumps(after['result'],indent=2),encoding='utf-8')
manifest={'revision':'Sizing R3','date':'2026-10-26','installed_path':str(TARGET),'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'changes':changes,'effective_changed_fields':delta,'validation':'All 24 roster entries reconstructed and compared to expected blueprints. 12 GAR meshes unchanged; all 12 resulting dimensions match requested factors. Existing package SHA256 values unchanged. Archive CRC and installed copy match passed. Runtime not tested.','scope':'Visual UniformScale, selection sizes/offsets, and LifeBarOffset/LifeBarSize/LifeBarHeight only. Collision boxes, navigation, physics, weapons, abilities, research, costs and all other fields unchanged.','rollback':'Close/restart development game after removing only '+NAME+' from its gamedata folder. Removing R3 restores R2; keep the R1 and R2 packages installed. Existing packages were not edited.'}
(OUT/'installation-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
lines=['# GAR sizing R3 — AT-TE, TX-130, AT-AP and health bars','', '26 October 2026. Restart the development game and build fresh units. File checks passed; runtime appearance is pending.','', 'Changes are relative to R2. AT-TE +5%; TX-130 +15%; AT-AP approximately +34.25% to match reference height proportions. Other model sizes retained.','', '| Unit | Size change | Old L × W × H (game units) | New L × W × H (game units) |','|---|---:|---:|---:|']
for c in changes:
 fmt=lambda v:' × '.join(f'{x:.2f}' for x in v)
 lines.append(f"| {c['name']} | {(c['factor']-1)*100:+.2f}% | {fmt(c['old_lwh'])} | {fmt(c['new_lwh'])} |")
lines+=['','## AT-AP reference check','', 'Reference AT-AP: 15.24 m length, 10.97 m height ([secondary reference](https://starwars.fandom.com/wiki/All_Terrain_Attack_Pod)). Reference AT-TE: 22.02 m length, 9.57 m height ([official Databank](https://www.starwars.com/databank/at-te-walker)).','', 'Using the newly enlarged AT-TE as the local reference gives desired AT-AP height = new AT-TE mesh height × 10.97/9.57. This matches the height ratio of about 1.1463. The AT-AP becomes about 6.862 × 4.383 × 4.698 game units; the AT-TE becomes about 9.010 × 5.756 × 4.098.','', 'A uniform resize cannot match both source length and height exactly. At the matched height, AT-AP length relative to AT-TE is about 0.7616 versus the listed 0.6921, roughly 10% longer proportionally. Gun-inclusive mesh bounds, rest stance and source measurement endpoints may explain some of that discrepancy. No hull stretching or gun shortening was performed. This is a relative height correction, not proof of exact lore dimensions for every axis or runtime pose.','', '## Health-bar cleanup','', 'For all 12 installed GAR ground replacements, set width from half the displayed mesh width, bounded to 0.8–2.8 game units; set thickness to 0.12 for standard units or 0.16 for experimentals; replace large legacy LifeBarOffset values with a small 0.2 + 0.02 × mesh-height offset, capped at 0.45. These are visual tuning candidates.','', 'The earlier passes multiplied existing LifeBarOffset values but retained large legacy widths. R3 replaces those values with bounded settings to address the oversized and distant bars in the screenshots. The engine placement behavior was not independently confirmed from source, so final alignment must be checked in game.','', '## Verification','',manifest['validation'],'', 'Combat, collision and movement fields remain unchanged. Mesh files remain unchanged.','', '## Rollback','',manifest['rollback'],'', 'Installed package: '+str(TARGET),'', 'Before/after snapshots, hashes and exact changed fields are saved alongside this report.']
(OUT/'SIZING-R3.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Installed',TARGET)
print(manifest['validation'])
for c in changes:print(c['id'],f"{(c['factor']-1)*100:+g}%",'scale',c['new_scale'])
