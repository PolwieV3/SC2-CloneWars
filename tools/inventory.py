"""Index copied archives without executing their Lua. Source fields are lexical observations."""
import collections, csv, json, pathlib, re, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'local'/'installed-snapshot'/'gamedata'
OUT=ROOT/'inventory'
def save(name,rows,fields):
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def field(t,k):
    m=re.search(r'\b'+re.escape(k)+r'''\s*=\s*(['"])(.*?)\1''',t,re.S)
    return m.group(2) if m else ''
def clean(s): return re.sub(r'<LOC [^>]+>','',s)
def main():
    OUT.mkdir(exist_ok=True); archives=[]; entries=[]; units=[]; refs=[]; research=[]; factions=[]; blueprints=[]; research_nodes=[]
    for p in sorted(DATA.glob('*.scd')):
        if not p.is_file(): continue
        with zipfile.ZipFile(p) as z:
            infos=[i for i in z.infolist() if not i.is_dir()]
            archives.append({'archive':p.name,'bytes':p.stat().st_size,'entries':len(infos),'uncompressed_bytes':sum(i.file_size for i in infos)})
            for i in infos:
                n=i.filename; low=n.lower(); ext=pathlib.PurePosixPath(n).suffix.lower()
                kind=({'.scm':'model','.sca':'animation','.dds':'texture','.bp':'blueprint','.lua':'lua'}.get(ext,'other'))
                if '/projectiles/' in '/'+low: kind='projectile_'+kind
                entries.append({'archive':p.name,'path':n,'kind':kind,'bytes':i.file_size,'crc32':f'{i.CRC:08x}'})
                if ext not in {'.bp','.lua'}: continue
                b=z.read(i)
                compiled=b.startswith(b'\x1bLua')
                if ext=='.bp': blueprints.append({'archive':p.name,'path':n,'encoding':'lua-bytecode' if compiled else 'text'})
                if compiled: continue
                t=b.decode('utf-8',errors='replace').replace('\r','')
                if low.endswith('/lua/sim/research.lua'):
                    for m in re.finditer(r'^    ([A-Z][A-Z0-9_]+) = \{\n(.*?)^    \},',t,re.M|re.S):
                        body=m.group(2)
                        cost=re.search(r'\bCOST\s*=\s*(\d+)',body)
                        research_nodes.append({'archive':p.name,'path':n,'id':m.group(1),'name':clean(field(body,'NAME')),'cost':cost.group(1) if cost else '', 'categories':field(body,'CATS'),'prerequisites':field(body,'PREREQUISITES'),'buff_ids':';'.join(sorted(set(re.findall(r'RB_[A-Z0-9_]+',body))))})
                if 'research' in low:
                    research.append({'archive':p.name,'path':n,'blueprint_ids':';'.join(re.findall(r'''BlueprintId\s*=\s*['"]([^'"]+)''',t)),'status':'source file; dependencies not evaluated'})
                if low.endswith('/factions.lua'):
                    factions.append({'archive':p.name,'path':n})
                    dest=ROOT/'local'/'reference'/p.stem/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(t,encoding='utf-8')
                if low.endswith('_unit.bp') and 'UnitBlueprint' in t:
                    uid=pathlib.PurePosixPath(n).name[:-8].lower()
                    units.append({'archive':p.name,'path':n,'unit_id':uid,'faction':field(t,'FactionName'),'name':clean(field(t,'DisplayName') or field(t,'UnitName')),'role':clean(field(t,'Description')),'merge':bool(re.search(r'Merge\s*=\s*true',t)),'scope':'dlc' if '/dlc1/' in low else 'campaign' if '/campaignbranch/' in low else 'base' if low.startswith('uncompiled/units/') else 'other'})
                if ext=='.bp' or 'research' in low:
                    for m in re.finditer(r'''\b([A-Za-z_]\w*)\s*=\s*(['"])([^'"\r\n]*)\2''',t):
                        k,v=m.group(1),m.group(3);category=''
                        if 'SC2/' in v or 'snd_' in v: category='audio'
                        elif k in {'Projectile','ProjectileId'}:category='projectile'
                        elif k in {'WeaponBlueprint','WeaponCategory','WeaponName','Label'} and ('weapon' in low or '_unit.bp' in low):category='weapon'
                        elif v.lower().endswith(('.dds','.scm','.sca')) or k in {'Mesh','MeshName','MeshBlueprint'}:category='asset'
                        if category:refs.append({'archive':p.name,'path':n,'line':t[:m.start()].count('\n')+1,'kind':category,'field':k,'value':v})
    save('archives.csv',archives,['archive','bytes','entries','uncompressed_bytes'])
    save('entries.csv',entries,['archive','path','kind','bytes','crc32'])
    save('blueprints.csv',blueprints,['archive','path','encoding'])
    save('unit-variants.csv',units,['archive','path','unit_id','faction','name','role','merge','scope'])
    save('references.csv',refs,['archive','path','line','kind','field','value'])
    save('research-files.csv',research,['archive','path','blueprint_ids','status'])
    save('faction-files.csv',factions,['archive','path'])
    save('research-nodes.csv',research_nodes,['archive','path','id','name','cost','categories','prerequisites','buff_ids'])
    sounds=[{'path':p.relative_to(DATA.parent).as_posix(),'bytes':p.stat().st_size} for p in (DATA.parent/'sounds').rglob('*') if p.is_file()]
    save('audio-banks.csv',sounds,['path','bytes'])
    base=[u for u in units if u['scope']=='base' and u['archive']=='uncompiled_lua.scd']
    matrix=[]
    for u in base:
        if u['faction'].upper() not in {'UEF','CYBRAN'}:continue
        proposed={'uul0101':'TX-130 Saber Tank','uua0101':'V-19 Torrent','uua0102':'BTL-B Y-wing','uua0103':'LAAT/i (gunship role)','uua0901':'LAAT/c (transport role)','ucl0103':'B2 battle droid (single-unit representation)','ucl0102':'Hailfire droid (artillery role)','ucl0104':'Hailfire droid (missile role; choose one mapping)','uca0104':'Vulture droid (retain fighter/bomber role)','uca0103':'HMP droid gunship','uux0101':'AT-TE (experimental scale; provisional)'}.get(u['unit_id'],'TBD')
        matrix.append({'unit_id':u['unit_id'],'source_faction':u['faction'],'target_faction':'Galactic Republic' if u['faction'].upper()=='UEF' else 'CIS / Separatists','source_name':u['name'],'source_role':u['role'],'proposed_identity':proposed,'status':'POC name only' if u['unit_id']=='uul0101' else 'proposed' if proposed!='TBD' else 'unassigned','mechanics':'preserve','blueprint_path':u['path']})
    save('conversion-matrix.csv',matrix,['unit_id','source_faction','target_faction','source_name','source_role','proposed_identity','status','mechanics','blueprint_path'])
    manifest=json.loads((OUT/'snapshot-manifest.json').read_text())
    summary={'baseline':manifest['baseline'],'installation_files':len(manifest['files']),'archives':len(archives),'archive_entries':len(entries),'entry_types':dict(collections.Counter(e['kind'] for e in entries)),'unit_source_variants':len(units),'base_units_by_faction':dict(collections.Counter(u['faction'] for u in base)),'references':dict(collections.Counter(r['kind'] for r in refs)),'research_source_files':len(research),'research_node_variants':len(research_nodes),'audio_bank_files':len(sounds),'conversion_rows':len(matrix),'limitations':['Lexical source inventory, not evaluated runtime blueprints.','Archive duplicates, campaign and DLC variants retained.','Audio event references catalogued; bank event mapping not decoded.']}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
