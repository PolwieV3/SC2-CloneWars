import zipfile,json,sys
from pathlib import Path
sys.path.insert(0,r'C:/Users/gavad/OneDrive/Documents/ChatGPT/SC2/model-work/atrt/tools');from poc_unit import LiteralTable
G=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars/local/dev-game/gamedata');d=json.loads(Path('work/tank-conversion/tx130-effective.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(G/'zz_SC2_CloneWars_UTAT_Model.scd') as z:u=LiteralTable(z.read('units/zz_clonewars_utat_model_unit.bp').decode()).blueprint()
for k in ['AI','Categories','General','Physics','Navigation','StrategicIconName','SelectionMeshScaleX']:
 print(k,'TX130',d.get(k),'UTAT',u.get(k))
