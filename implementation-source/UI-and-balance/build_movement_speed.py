from pathlib import Path
from decimal import Decimal
import zipfile,json,hashlib,shutil
R=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');L=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars');G=L/'local/dev-game/gamedata';O=R/'outputs/Movement-Speed';name='zzzzzzzzzzzz_SC2_CloneWars_MovementSpeed.scd'
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in G.glob('*.scd') if p.name!=name}
units=[('uux0111','AT-TE','1.8','0.5','1.10'),('uux0101','HAVw A6 Juggernaut','2.875','2.0125','1.15')];rows=[];text='-- User-approved movement speed changes; no animation or weapon fields.\n'
for uid,label,forward,reverse,mult in units:
 f=Decimal(forward)*Decimal(mult);r=Decimal(reverse)*Decimal(mult)
 text+=f"UnitBlueprint {{ Merge = true, BlueprintId = '{uid}', Physics = {{ MaxSpeed = {f}, MaxSpeedReverse = {r} }} }}\n"
 rows.append({'unit':label,'id':uid,'forward_before':float(forward),'forward_after':float(f),'reverse_before':float(reverse),'reverse_after':float(r),'increase_percent':int((Decimal(mult)-1)*100)})
with zipfile.ZipFile(O/name,'w',zipfile.ZIP_DEFLATED) as z:
 for prefix in ['','mods/DLC1/base/','mods/DLC1/shadow/','mods/CampaignBranch/shadow/']:z.writestr(prefix+'units/zzzzzzzzzzzz_clonewars_speed_unit.bp',text.encode())
with zipfile.ZipFile(O/name) as z:
 assert z.testzip() is None
 for n in z.namelist():
  b=z.read(n).decode();assert 'Weapons' not in b and 'Animation' not in b
if (G/name).exists():
 backup=O/'backups';backup.mkdir(exist_ok=True);shutil.copy2(G/name,backup/(hashlib.sha256((G/name).read_bytes()).hexdigest()[:12]+'-'+name))
shutil.copy2(O/name,G/name)
for n,h in before.items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h,n
report={'date':'2026-10-25','changes':rows,'installed':str(G/name),'sha256':hashlib.sha256((G/name).read_bytes()).hexdigest(),'other_archives_unchanged':True,'animation_changes':False,'user_animation_feedback':'User retested and thinks AT-TE animation works; animation repair not requested now.','verification':'Archive CRC and installed hash checked; gameplay speed not yet tested.','rollback':'Remove only '+str(G/name)+' and restart isolated game.'}
(O/'Verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(L/'planning/movement-speed-2026-10-25.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(rows,indent=2))
