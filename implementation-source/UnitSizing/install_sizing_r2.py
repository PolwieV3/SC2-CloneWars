"""Install one removable visual-size overlay; preserve gameplay configuration."""
from pathlib import Path
import runpy,io,contextlib,json,zipfile,hashlib,copy,math,shutil
W=Path(__file__).resolve().parents[1]
OUT=W/'outputs'/'Sizing-R2'
OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
GAME=ROOT/'local/dev-game/gamedata'
NAME='zzzzzzzzzzzzzzzzzzzz_SC2_CloneWars_UnitSizing_R2.scd'
TARGET=GAME/NAME
if TARGET.exists():raise SystemExit('Sizing R2 already installed; refusing to multiply scales twice.')
factors={'uul0002':1.6,'uul0003d1':1.6,'uul0101':1.4,'uul0102':1.15,'uul0103':2.,'uul0104':1.25,'uul0105':1.2,'uul0201':1.1,'uul0203':1.,'uux0101':1.,'uux0111':1.15,'uux0113d1':1.}
reasons={uid:'Screenshot readability adjustment relative to R1' for uid in factors}
reasons.update({'uux0111':'User requested +15% from current R1 size','uul0103':'Double tiny scout for gameplay readability','uul0002':'Larger visible support hull','uul0003d1':'Keep shared engineer hull dimensions','uul0203':'Retain current heavy transport size','uux0101':'Retain user-selected R1 Juggernaut size','uux0113d1':'Retain user-selected R1 SPHA-T size'})
with contextlib.redirect_stdout(io.StringIO()):before=runpy.run_path(str(W/'work/measure_units.py'))
if before['errors']:raise RuntimeError(before['errors'])
original=copy.deepcopy(before['current']);measurements=copy.deepcopy(before['rows'])
(OUT/'before-blueprints.json').write_text(json.dumps(original,indent=2),encoding='utf-8')
(OUT/'before-measurements.json').write_text(json.dumps(before['result'],indent=2),encoding='utf-8')
hashes={a.name:hashlib.sha256(a.read_bytes()).hexdigest() for a in GAME.glob('*CloneWars*.scd')}
(OUT/'before-package-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
visual_fields=['LifeBarOffset','SelectionSizeX','SelectionSizeZ','SelectionCenterOffsetX','SelectionCenterOffsetZ','SelectionMeshOffsetX','SelectionMeshOffsetY','SelectionMeshOffsetZ']
patches={};changes=[]
for uid,factor in factors.items():
 d=original[uid];old=d['Display']['UniformScale'];new=round(old*factor,9)
 row=next(r for r in measurements if r['id']==uid)
 changes.append({'id':uid,'name':row['replacement'],'factor':factor,'old_scale':old,'new_scale':new,'old_lwh':row['displayed_lwh'],'new_lwh':[x*factor for x in row['displayed_lwh']],'reason':reasons[uid]})
 if factor==1:continue
 patch={'Merge':True,'BlueprintId':uid,'Display':{'UniformScale':new}}
 for key in visual_fields:
  if isinstance(d.get(key),(float,int)):patch[key]=round(d[key]*factor,9)
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
  payload[prefix+'units/zzzzzzzzzzzzzzzzzzzz_sizing_r2_'+uid+'_unit.bp']=raw
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
manifest={'revision':'Sizing R2','date':'2026-10-26','installed_path':str(TARGET),'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'changes':changes,'effective_changed_fields':delta,'validation':'All 24 roster entries reconstructed and compared to expected blueprints. 12 GAR meshes unchanged; all 12 resulting dimensions match requested factors. Existing package SHA256 values unchanged. Archive CRC and installed copy match passed. Runtime not tested.','scope':'Visual UniformScale, existing selection sizes/offsets and health-bar vertical offsets only. Collision boxes, navigation, physics, weapons, abilities, research, costs and all other fields unchanged.','rollback':'Close/restart development game after removing only '+NAME+' from its gamedata folder. Removing R2 restores R1; keep the R1 package installed. Existing packages were not edited.'}
(OUT/'installation-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
lines=['# GAR sizing — installed first pass','', '26 October 2026. Restart the development game to load this overlay. Runtime visuals are not yet verified.','', 'Percentages below are relative to the installed R1 sizes in the screenshot. +15% AT-TE means current R1 size multiplied by 1.15, not 15 percentage points added to the original size. All dimensions scale uniformly.','', '| Unit | Size change | Old L × W × H (game units) | New L × W × H (game units) |','|---|---:|---:|---:|']
for c in changes:
 fmt=lambda v:' × '.join(f'{x:.2f}' for x in v)
 lines.append(f"| {c['name']} | {(c['factor']-1)*100:+g}% | {fmt(c['old_lwh'])} | {fmt(c['new_lwh'])} |")
lines+=['','The engineers now have equal hull length and width. The Field Engineer retains its extra height from the beacon. SPHA-T, Juggernaut and UT-AT retain their R1 sizes. AT-TE is 15% larger than R1. The smaller units are enlarged for readability based on the supplied screenshot; this deliberately relaxes strict lore scaling.','', 'This is a visual/readability pass rather than strict lore scaling. The chosen sizes preserve each mesh’s proportions. Selection outlines and health-bar offsets follow the visual size changes.','', '## Verification','',manifest['validation'],'', '## In-game check','', 'Build fresh units after restarting. Check the SPHA-T packed/deployed poses, Juggernaut wheel motion and tower, walker ground contact, engineer arms/beacon, muzzle positions, selection outlines and health bars. Collision boxes and navigation clearance retain their previous values, so inspect overlap, factory exits and movement through groups before treating these as final sizes.','', '## Reversal','',manifest['rollback'],'', 'Installed package: '+str(TARGET),'', 'The package copy, pre-change blueprints/measurements, package hashes, post-change measurements and exact field differences are saved beside this note.']
(OUT/'SIZING-R2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Installed',TARGET)
print(manifest['validation'])
for c in changes:print(c['id'],f"{(c['factor']-1)*100:+g}%",'scale',c['new_scale'])
