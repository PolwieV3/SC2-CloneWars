"""Read-only SC2 roster/stat snapshot. Does not execute Lua or modify the game."""
from pathlib import Path
import sys, json, re, copy, zipfile, hashlib, csv

ROOT=Path(__file__).resolve().parents[2]
LIVE=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
HUB=Path(r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2')
VAN=Path(r'B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata')
GAME=LIVE/'local/dev-game/gamedata'
OUT=ROOT/'local/project-sync/2026-10-26'
sys.path.insert(0,str(LIVE/'tools'))
from poc_unit import LiteralTable, merge, differences

UEF='uul0001 uul0002 uul0003d1 uul0101 uul0102 uul0103 uul0104 uul0105 uul0201 uul0203 uux0101 uux0111 uux0113d1 uua0101 uua0102 uua0103 uua0901 uux0102 uux0103 uux0112 uus0102 uus0104 uus0105 uux0104 uux0105d1'.split()
CIS='ucl0001 ucl0002 ucl0102 ucl0103 ucl0104 ucl0204 ucx0101 ucx0103 ucx0111 ucx0117d1 ucx0104d1 uca0104 uca0103 uca0901 uca0105d1 ucx0112 ucx0102 ucs0103 ucs0105 ucs0901 ucx0113'.split()
IDS=set(UEF+CIS)
AIR=set('uua0101 uua0102 uua0103 uua0901 uux0102 uux0103 uux0112 uca0104 uca0103 uca0901 uca0105d1 ucx0112 ucx0102'.split())
SEA=set('uus0102 uus0104 uus0105 uux0104 uux0105d1 ucs0103 ucs0105 ucs0901 ucx0113'.split())
CHANGES={'uul0201':'RTT Shield Transport','uux0113d1':'SPHA-T','uux0112':'Pelta / Acclamator / Venator test candidates; final choice open','uux0104':'Unselected; Atlantis II deferred','uul0002':'ISP Engineer','uul0003d1':'ISP Field Engineer'}
PACKAGES={'uul0002':'EngineerISP_Test','uul0003d1':'FieldEngineerISP_Test','uul0101':'TX130_Model','uul0102':'ATAP_Model','uul0103':'ATRT_Model','uul0104':'A5RX_Test','uul0105':'UTAA_Model','uul0201':'RTTShield_Model','uul0203':'UTAT_Model','uux0101':'Juggernaut_Model','uux0111':'ATTE.scd','uux0113d1':'SPHA.scd'}

def parsed(src):
    p=LiteralTable(src.replace('\r',''));out=[]
    while p.i<len(p.tokens):
        p.take('UnitBlueprint');out.append(p.value())
    return out

def native():
    base={};dlc={};refs={}
    for archive in ['uncompiled_lua.scd','z_uncompiled_lua_dlc1.scd']:
        with zipfile.ZipFile(VAN/archive) as z:
            for n in z.namelist():
                low=n.lower();m=re.search(r'/units/(?:uef|cybran)/([^/]+)/\1_unit.bp$',low)
                if not m or m[1] not in IDS or '/campaignbranch/' in low:continue
                isdlc='/mods/dlc1/' in low
                if archive=='uncompiled_lua.scd' and isdlc:continue
                b=z.read(n);d=parsed(b.decode('utf-8'))[0];uid=m[1]
                if isdlc:
                    if d.get('Merge'):merge(dlc.setdefault(uid,copy.deepcopy(base.get(uid,{}))),d)
                    else:dlc[uid]=d
                else:base[uid]=d
                refs[uid]={'archive':archive,'entry':n,'sha256':hashlib.sha256(b).hexdigest()}
    for uid in IDS:
        if uid not in dlc:dlc[uid]=copy.deepcopy(base[uid])
    return base,dlc,refs

def clean_name(s):return re.sub(r'^<LOC [^>]+>','',str(s or ''))

def get(d,path):
    for p in path.split('.'):
        if not isinstance(d,dict):return None
        d=d.get(int(p) if p.isdigit() else p)
    return d

def table_values(d):return [d[k] for k in sorted(d,key=lambda k:(not isinstance(k,int),str(k)))] if isinstance(d,dict) else []

def weapons(d):
    out=[]
    for idx,w in d.get('Weapons',{}).items():
        if not isinstance(w,dict):continue
        racks=table_values(w.get('RackBones',{}));muzzles=sum(len(x.get('MuzzleBones',{})) for x in racks)
        out.append({'index':idx,'label':w.get('Label'),'name':clean_name(w.get('DisplayName')),'damage':w.get('Damage'),'range':w.get('MaxRadius'),'min_range':w.get('MinRadius'),'rate':w.get('RateOfFire'),'splash':w.get('DamageRadius'),'projectile':w.get('ProjectileId'),'muzzle_salvo':w.get('MuzzleSalvoSize'),'rack_salvo':w.get('RackSalvoSize'),'muzzle_delay':w.get('MuzzleSalvoDelay'),'rack_reload':w.get('RackSalvoReloadTime'),'charge_delay':w.get('MuzzleChargeDelay'),'muzzle_count':muzzles,'rack_count':len(racks),'rack_together':w.get('RackFireTogether'),'beam_lifetime':w.get('BeamLifetime'),'collision_delay':w.get('BeamCollisionDelay'),'enabled_by_script':w.get('EnabledByScript'),'target_allow':w.get('TargetRestrictOnlyAllow'),'target_disallow':w.get('TargetRestrictDisallow'),'layers':json.dumps(w.get('FireTargetLayerCaps',{}),sort_keys=True),'category':w.get('WeaponCategory'),'range_category':w.get('RangeCategory')})
    return sorted(out,key=lambda w:w['index'])

METRICS={'health':'Defense.MaxHealth','regen':'Defense.RegenRate','speed':'Physics.MaxSpeed','reverse_speed':'Physics.MaxSpeedReverse','acceleration':'Physics.MaxAcceleration','turn_rate':'Physics.TurnRate','vision':'Intel.VisionRadius','mass_value':'Economy.MassValue','energy_value':'Economy.EnergyValue','build_time':'Economy.BuildTime','build_rate':'Economy.BuildRate','shield_health':'Defense.Shield.ShieldMaxHealth','shield_radius':'Defense.Shield.ShieldSize','transport_storage_size':'Transport.StorageSize','shield_regen':'Defense.Shield.ShieldRegenRate','shield_recharge_time':'Defense.Shield.ShieldRechargeTime','size_x':'SizeX','size_y':'SizeY','size_z':'SizeZ','visual_scale':'Display.UniformScale','health_bar_size':'LifeBarSize','health_bar_offset':'LifeBarOffset'}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    base,original,refs=native();current=copy.deepcopy(original)
    files={};sources={};manifest=[];errors=[]
    for a in sorted(GAME.glob('*CloneWars*.scd'),key=lambda p:p.name.lower()):
        raw=a.read_bytes();manifest.append({'file':a.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        with zipfile.ZipFile(a) as z:
            for n in z.namelist():
                low=n.lower()
                if low.endswith('_unit.bp') and not low.startswith(('uncompiled/','mods/campaignbranch/')):
                    b=z.read(n)
                    if b.startswith(b'\x1bLua'):continue
                    files[low]=b.decode('utf-8');sources[low]=a.name
    applied={uid:[] for uid in IDS}
    for phase in ['base','dlcbase','dlcshadow']:
        for n in sorted(files):
            scope='dlcshadow' if n.startswith('mods/dlc1/shadow/') else 'dlcbase' if n.startswith('mods/dlc1/base/') else 'base'
            if scope!=phase:continue
            try:blocks=parsed(files[n])
            except Exception as e:errors.append({'file':n,'error':str(e)});continue
            for patch in blocks:
                uid=str(patch.get('BlueprintId','')).lower()
                if not uid:
                    match=re.search(r'/units/(?:uef|cybran)/([^/]+)/', '/'+n)
                    if match:uid=match[1]
                if uid not in IDS:continue
                data={k:v for k,v in patch.items() if k not in ['BlueprintId','Merge']}
                if patch.get('Merge'):merge(current[uid],data)
                else:current[uid]=copy.deepcopy(data)
                applied[uid].append({'archive':sources[n],'entry':n,'merge':bool(patch.get('Merge'))})
    oldroster={u['unit_id'].lower():u for u in json.loads((HUB/'planning/roster.json').read_text(encoding='utf-8'))['units']}
    rows=[];metrics=[];weapon_rows=[];delta_rows=[]
    for uid in UEF+CIS:
        old=oldroster[uid];before=original[uid];after=current[uid];name=CHANGES.get(uid,old.get('replacement_name','TBD'))
        installed=any(PACKAGES.get(uid,'NOT_FOUND') in a['file'] for a in manifest)
        domain='Air' if uid in AIR else 'Naval' if uid in SEA else 'Ground'
        status='Working ground conversion; current lineup/sizing user accepted 2026-10-26; edge-case and balance checks remain' if installed else 'Design only; no installed replacement package found'
        note=''
        if uid=='uul0203':note='Tank role now; three surface guns, 75/30/30 damage, RateOfFire 0.725 each; former anti-missile role superseded.'
        if uid=='uul0105':note='AA plus tactical missile interceptor; former researched ground gun replaced, research tooltip cleanup pending.'
        if uid=='uux0101':note='Two +15% speed patches stack: 2.5 -> 2.875 -> 3.30625 (+32.25% total). Weapon max ranges -15% from prior custom settings.'
        if uid=='uux0111':note='Heavy assault redesign; main range 55 -> 68.75, movement +10%. User retest suggests walk works; no new animation repair requested.'
        if uid=='uux0113d1':note='SPHA-T working ground attack/appearance accepted; test8 retained. Terrain-obstruction issue deferred. Research source13-point cost unverified; team paint reverted.'
        if uid=='uul0104':note='User reports A5-RX working; current ground lineup/sizing accepted.'
        if uid in ['uul0102','uul0103']:note='AT-AP/UUL0102 and AT-RT/UUL0103 identity/display mapping corrected and confirmed in current installed source.'
        row={'id':uid,'faction':'GAR' if uid in UEF else 'CIS','domain':domain,'original':old['source_name'],'replacement':name,'status':status,'installed':installed,'selection_status':old.get('decision_status'),'visible_name_reconstructed':clean_name(get(after,'Display.DisplayName')),'notes':note,'baseline_source':refs[uid],'patches':applied[uid],'stats_before':{k:get(before,p) for k,p in METRICS.items()},'stats_after':{k:get(after,p) for k,p in METRICS.items()},'weapons_before':weapons(before),'weapons_after':weapons(after)}
        rows.append(row)
        for k,path in METRICS.items():
            b=get(before,path);a=get(after,path)
            metrics.append({'id':uid,'faction':row['faction'],'domain':domain,'original':row['original'],'replacement':name,'metric':k,'vanilla':b,'current':a,'delta':a-b if isinstance(a,(float,int)) and isinstance(b,(float,int)) else None,'delta_percent':a/b-1 if isinstance(a,(float,int)) and isinstance(b,(float,int)) and b!=0 else None,'source':refs[uid]['archive']+'!'+refs[uid]['entry'],'status':status})
        for mode,d in [('Vanilla',before),('Current',after)]:
            for w in weapons(d):weapon_rows.append({'id':uid,'faction':row['faction'],'domain':domain,'original':row['original'],'replacement':name,'version':mode,**w})
        for path in differences(before,after):
            if path.startswith(('Weapons.','Physics.','Defense.','Economy.','Intel.','Abilities.','CommandCaps.','Categories.','Research')):
                b=get(before,path);a=get(after,path)
                if isinstance(b,dict) or isinstance(a,dict):continue
                delta_rows.append({'id':uid,'original':row['original'],'replacement':name,'field':path,'vanilla':b,'current':a})
    result={'as_of':'2026-10-26','method':'Static DLC-enabled skirmish reconstruction: vanilla literal source definitions + base/DLC installed full definitions and merge patches; native engine effective values not queried. Research upgrades, buffs, veterancy and difficulty are excluded. Does not execute Lua.','scope':{'GAR':25,'CIS':21},'units':rows,'metrics':metrics,'weapons':weapon_rows,'gameplay_field_differences':delta_rows,'installed_packages':manifest,'parse_errors':errors,'limitations':['Displayed names may be supplied by localization or runtime hooks; name reconstruction is not UI acceptance.','Script-controlled weapon enabling, volley/beam damage, upgrades, armor and target availability prevent one universal attack/DPS statistic.','Patch precedence is reconstructed from virtual filenames and base/DLC phase, not an engine interrogation.','Unit baseline uses DLC definitions when present, base otherwise. Multiple weapon roles must be compared separately.']}
    (OUT/'project-state.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for stem,data in [('roster',rows),('balance-metrics',metrics),('weapons',weapon_rows),('gameplay-differences',delta_rows),('installed-packages',manifest)]:
        if stem=='roster':data=[{k:v for k,v in d.items() if k not in ['baseline_source','patches','stats_before','stats_after','weapons_before','weapons_after']} for d in data]
        with (OUT/(stem+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    print(json.dumps({'units':len(rows),'installed':sum(r['installed'] for r in rows),'weapons':len(weapon_rows),'metrics':len(metrics),'parse_errors':errors},indent=2))
    for r in rows:
        if r['installed']:print(r['id'],r['replacement'],'speed',r['stats_before']['speed'],'->',r['stats_after']['speed'],'weapons',len(r['weapons_before']),len(r['weapons_after']))

if __name__=='__main__':main()
