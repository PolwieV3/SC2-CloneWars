from pathlib import Path
import zipfile,sys,hashlib,json
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable,differences
W=Path('work');O=Path('outputs');G=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata');name='zz_SC2_CloneWars_UTAT_Model.scd';B=W/'revisions/pre-attack-speed145-2026-10-25';B.mkdir(parents=True,exist_ok=True);src=G/name;raw=src.read_bytes();(B/name).write_bytes(raw)
def lua(v,ind=0):
 if isinstance(v,dict):return '{\n'+''.join(' '*(ind+4)+(f'[{k}]' if isinstance(k,int) else k)+' = '+lua(x,ind+4)+',\n' for k,x in v.items())+' '*ind+'}'
 if isinstance(v,str):return "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
 if isinstance(v,bool):return 'true' if v else 'false'
 return str(v)
with zipfile.ZipFile(src) as z:payload={n:z.read(n) for n in z.namelist()}
old=payload.copy();checks=[]
for n in payload:
 if not n.endswith('_unit.bp'):continue
 before=LiteralTable(payload[n].decode('utf-8-sig')).blueprint();assert before['BlueprintId']=='uul0203' and len(before['Weapons'])==3;after=__import__('copy').deepcopy(before);rates=[]
 for i,w in after['Weapons'].items():
  rate=w['RateOfFire'];w['RateOfFire']=round(rate*1.45,9);rates.append({'gun':w['Label'],'before':rate,'after':w['RateOfFire'],'damage_unchanged':w['Damage']})
 delta=differences(before,after);assert set(delta)=={f'Weapons.{i}.RateOfFire' for i in (1,2,3)},delta
 payload[n]=('UnitBlueprint '+lua(after)+'\n').encode('utf-8');assert LiteralTable(payload[n].decode()).blueprint()==after;checks.append({'file':n,'changes':delta,'rates':rates})
assert len(checks)==3
for n in old:
 if not n.endswith('_unit.bp'):assert payload[n]==old[n]
out=O/name
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
report={'date':'2026-10-25','revision':'rockhead-test-10-attack-speed145','unit_id':'uul0203','request':'Increase attack speed by 45 percent','multiplier':1.45,'rate_before':.5,'rate_after':.725,'seconds_between_shots_before':2,'seconds_between_shots_after':1/.725,'damage':{'roof':75,'left':30,'right':30},'changes_only_three_RateOfFire_fields_per_variant':checks,'all_other_payload_bytes_unchanged':True,'previous_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'archive':str(out.resolve()),'backup':str((B/name).resolve()),'installed':False,'runtime_tested':False}
(O/'Attack-speed145-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['revision','rate_before','rate_after','seconds_between_shots_after','sha256']}))
