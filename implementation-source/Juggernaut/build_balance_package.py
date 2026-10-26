from pathlib import Path
import sys,json,zipfile,copy,hashlib
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools')
from poc_unit import LiteralTable,merge,differences
r=Path(__file__).parent;out=r.parents[1]/'outputs/Juggernaut';live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
model=live/'local/dev-game/gamedata/zz_SC2_CloneWars_Juggernaut_Model.scd'
with zipfile.ZipFile(model) as z:existing=LiteralTable(z.read('units/zz_clonewars_juggernaut_model_unit.bp').decode()).blueprint()
def lua(v):
 if isinstance(v,dict):return '{'+','.join((f'[{k}]' if isinstance(k,int) else k)+'='+lua(x) for k,x in v.items())+'}'
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,str):return repr(v)
 return str(v)
payload={};checks=[]
variants=[('',r/'native/uncompiled_lua.scd/uncompiled/Units/UEF/UUX0101/UUX0101_unit.bp'),('mods/DLC1/base/',r/'native/uncompiled_lua.scd/uncompiled/Units/UEF/UUX0101/UUX0101_unit.bp'),('mods/DLC1/shadow/',r/'native/z_uncompiled_lua_dlc1.scd/uncompiled/mods/DLC1/shadow/Units/UEF/UUX0101/UUX0101_unit.bp')]
for prefix,source in variants:
 before=LiteralTable(source.read_text(encoding='utf-8')).blueprint();merge(before,{k:v for k,v in existing.items() if k not in ['Merge','BlueprintId']})
 physics={k:before['Physics'][k]*1.15 for k in ['MaxSpeed','MaxSpeedReverse']}
 ranges={i:{'MaxRadius':w['MaxRadius']*.85} for i,w in before['Weapons'].items()}
 patch={'Merge':True,'BlueprintId':'uux0101','Physics':physics,'Weapons':ranges};after=copy.deepcopy(before);merge(after,{'Physics':physics,'Weapons':ranges})
 delta=differences(before,after);allowed={'Physics.MaxSpeed','Physics.MaxSpeedReverse',*(f'Weapons.{i}.MaxRadius' for i in range(1,7))};assert set(delta)==allowed,delta
 checks.append({'variant':prefix or 'base','speeds':{k:{'before':before['Physics'][k],'after':v} for k,v in physics.items()},'ranges':{i:{'before':before['Weapons'][i]['MaxRadius'],'after':v['MaxRadius']} for i,v in ranges.items()},'only_requested_fields_changed':delta})
 payload[prefix+'units/zzzz_clonewars_juggernaut_balance_unit.bp']=('UnitBlueprint '+lua(patch)+'\n').encode()
archive=out/'zzzzzz_SC2_CloneWars_Juggernaut_Balance.scd'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in payload.items():z.writestr(n,b)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for n in z.namelist():LiteralTable(z.read(n).decode()).blueprint()
d={'date':'2026-10-25','archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'authorized_change':'Movement speed +15%, maximum weapon range -15% across artillery, missiles and AA. Reverse speed included.','model_package_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'checks':checks,'installed':False,'runtime':'Blueprint checks passed; movement/range changes await user in-game test.'}
(r/'balance-validation.json').write_text(json.dumps(d,indent=2),encoding='utf-8');print(json.dumps(checks[0]))
