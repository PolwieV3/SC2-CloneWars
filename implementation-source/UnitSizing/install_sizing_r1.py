"""Install one removable visual-size overlay; preserve gameplay configuration."""
from pathlib import Path
import runpy,io,contextlib,json,zipfile,hashlib,copy,math,shutil
W=Path(__file__).resolve().parents[1]
OUT=W/'outputs'/'Sizing-R1'
OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
GAME=ROOT/'local/dev-game/gamedata'
NAME='zzzzzzzzzzzzzzzzzzzz_SC2_CloneWars_UnitSizing_R1.scd'
TARGET=GAME/NAME
if TARGET.exists():raise SystemExit('Sizing R1 already installed; refusing to multiply scales twice.')
factors={'uul0002':.9,'uul0003d1':.675,'uul0101':1.,'uul0102':.9,'uul0103':.6,'uul0104':1.5,'uul0105':1.25,'uul0201':1.8,'uul0203':2.,'uux0101':1.6,'uux0111':.65,'uux0113d1':2.}
reasons={'uul0002':'Slightly smaller support hull','uul0003d1':'Match regular engineer hull size; retain tall beacon','uul0101':'Retain reference tank size','uul0102':'Slightly smaller artillery walker','uul0103':'Compact scout walker with readable silhouette','uul0104':'Larger missile tank, below heavy transports','uul0105':'Larger dedicated AA platform','uul0201':'Medium shield transport','uul0203':'Heavy transport near AT-TE length','uux0101':'User requested +60% linear size','uux0111':'Heavy walker below Juggernaut size','uux0113d1':'User requested +100% linear size'}
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
  payload[prefix+'units/zzzzzzzzzzzzzzzzzzzz_sizing_r1_'+uid+'_unit.bp']=raw
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
manifest={'revision':'Sizing R1','date':'2026-10-26','installed_path':str(TARGET),'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'changes':changes,'effective_changed_fields':delta,'validation':'All 24 roster entries reconstructed and compared to expected blueprints. 12 GAR meshes unchanged; all 12 resulting dimensions match requested factors. Existing package SHA256 values unchanged. Archive CRC and installed copy match passed. Runtime not tested.','scope':'Visual UniformScale, existing selection sizes/offsets and health-bar vertical offsets only. Collision boxes, navigation, physics, weapons, abilities, research, costs and all other fields unchanged.','rollback':'Close/restart development game after removing only '+NAME+' from its gamedata folder. Original packages were not edited.'}
(OUT/'installation-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
lines=['# GAR sizing — installed first pass','', '26 October 2026. Restart the development game to load this overlay. Runtime visuals are not yet verified.','', 'Percentages below refer to linear size in all three dimensions. +100% means twice as long, wide and tall; +60% means 1.6 times each dimension.','', '| Unit | Size change | Old L × W × H (game units) | New L × W × H (game units) |','|---|---:|---:|---:|']
for c in changes:
 fmt=lambda v:' × '.join(f'{x:.2f}' for x in v)
 lines.append(f"| {c['name']} | {(c['factor']-1)*100:+g}% | {fmt(c['old_lwh'])} | {fmt(c['new_lwh'])} |")
lines+=['','The engineers now have equal hull length and width. The Field Engineer retains its extra height from the beacon. SPHA-T is the longest and tallest ground model in this pass, followed by the Juggernaut. AT-TE and UT-AT form the heavy-vehicle tier. TX-130 remains the reference tank.','', 'This is a visual/readability pass rather than strict lore scaling. The chosen sizes preserve each mesh’s proportions. Selection outlines and health-bar offsets follow the visual size changes.','', '## Verification','',manifest['validation'],'', '## In-game check','', 'Build fresh units after restarting. Check the SPHA-T packed/deployed poses, Juggernaut wheel motion and tower, walker ground contact, engineer arms/beacon, muzzle positions, selection outlines and health bars. Collision boxes and navigation clearance retain their previous values, so inspect overlap, factory exits and movement through groups before treating these as final sizes.','', '## Reversal','',manifest['rollback'],'', 'Installed package: '+str(TARGET),'', 'The package copy, pre-change blueprints/measurements, package hashes, post-change measurements and exact field differences are saved beside this note.']
(OUT/'SIZING-R1.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Installed',TARGET)
print(manifest['validation'])
for c in changes:print(c['id'],f"{(c['factor']-1)*100:+g}%",'scale',c['new_scale'])
