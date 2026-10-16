"""Install/remove only this project's POC in its isolated development copy."""
import argparse, hashlib, pathlib, shutil
from build import ROOT, NAME
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['install','remove']);ap.add_argument('--package',choices=['rename','model','audio','blaster'],default='rename');args=ap.parse_args()
    name={'rename':NAME,'model':'zz_SC2_CloneWars_TX130_Model.scd','audio':'zz_SC2_CloneWars_TX130_Audio.scd','blaster':'zz_SC2_CloneWars_TX130_Blaster.scd'}[args.package]
    dev=(ROOT/'local/dev-game').resolve(); p=dev/'gamedata'/name;built=ROOT/'dist'/name
    if not dev.is_relative_to(ROOT.resolve()) or not (dev/'bin/SupremeCommander2.exe').is_file():raise SystemExit('Development copy is missing or outside project.')
    if p.exists() and (not built.exists() or p.read_bytes()!=built.read_bytes()):raise SystemExit('Existing archive differs; inspect it before replacing or removing.')
    if args.action=='install':shutil.copy2(built,p);print('Staged only in '+str(p))
    elif p.exists():p.unlink();print('Removed '+name+' from development copy.')
if __name__=='__main__':main()
