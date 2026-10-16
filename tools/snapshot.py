"""Create isolated copies; never write to the source installation."""
import argparse, hashlib, json, pathlib, shutil
ROOT = pathlib.Path(__file__).resolve().parents[1]
EXTRAS = {'_modsupport_v7.scd','experimental_warp_pillars.scd','revamp_balance.scd','revamp_base.scd','revamp_content.scd','revamp_textures.scd','z_revamp_extras.scd','modoptions.scd'}
def digest(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('installation',type=pathlib.Path); args=ap.parse_args()
    src=args.installation.resolve(); local=ROOT/'local'; snapshot=local/'installed-snapshot'; dev=local/'dev-game'
    if snapshot.exists() or dev.exists(): raise SystemExit('Copies already exist; refusing to overwrite.')
    files=[p for p in src.rglob('*') if p.is_file() and p.suffix.lower() not in {'.rar','.mdmp'} and 'DirectX' not in p.relative_to(src).parts]
    size=sum(p.stat().st_size for p in files)
    if shutil.disk_usage(ROOT).free < size*2+1024**3: raise SystemExit('Insufficient disk space for independent copies.')
    rows=[]
    for p in files:
        rel=p.relative_to(src); q=snapshot/rel; q.parent.mkdir(parents=True,exist_ok=True)
        before=digest(p); shutil.copy2(p,q)
        if digest(q)!=before: raise RuntimeError(f'Copy hash mismatch: {rel}')
        excluded=rel.parts[0]=='gamedata' and rel.parts[1].lower() in EXTRAS
        if not excluded:
            d=dev/rel; d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(q,d)
            if digest(d)!=before: raise RuntimeError(f'Dev copy mismatch: {rel}')
        rows.append({'path':rel.as_posix(),'bytes':p.stat().st_size,'sha256':before,'in_dev_copy':not excluded})
    (ROOT/'inventory').mkdir(exist_ok=True)
    (ROOT/'inventory'/'snapshot-manifest.json').write_text(json.dumps({'source':str(src),'baseline':'Installed state; not Steam-verified vanilla','excluded_extras':sorted(EXTRAS),'files':rows},indent=2))
    print(json.dumps({'files':len(rows),'source_bytes':size,'snapshot':str(snapshot),'dev':str(dev)}))
if __name__=='__main__': main()
