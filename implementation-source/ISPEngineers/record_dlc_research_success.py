from pathlib import Path
import json
root=Path.cwd();project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
f=root/'outputs/DLC-Research-Direct-Test/installation.json';data=json.loads(f.read_text());data['runtime_verified']=True;data['runtime_verification']={'date':'2026-10-26','method':'User confirmation plus two supplied in-game screenshots','scope':'Both DLC research titles and unlock descriptions: SPHA-T and ISP Field Engineer','evidence':['evidence/SPHA-T-research-verified.png','evidence/ISP-Field-Engineer-research-verified.png']};data['stop_condition']='Satisfied: user confirmed the names and descriptions fixed. Research rename no longer on hold.';f.write_text(json.dumps(data,indent=2));(project/'planning/dlc-research-direct-test-2026-10-26.json').write_text(json.dumps(data,indent=2))
state=project/'CURRENT-STATE.md';text=state.read_text(encoding='utf-8');note='- DLC research naming is verified in game October 26: SPHA-T and ISP Field Engineer titles and unlock descriptions are correct. Preserve the [verified DLC research renaming procedure](docs/DLC-RESEARCH-RENAMING.md); it handles native DLC shadow files, competing source/bytecode copies and localization tags.\n';
if note not in text:text=text.replace('This is the current reading entry point.',note+'\nThis is the current reading entry point.',1)
state.write_text(text,encoding='utf-8')
for h in [root/'outputs/ISP-Continuation-Handoff-2026-10-26.md',project/'planning/ISP-Continuation-Handoff-2026-10-26.md']:
 if h.exists():
  text=h.read_text(encoding='utf-8');update='> Update October 26: DLC research title and description renaming is now VERIFIED FIXED for both ISP Field Engineer and SPHA-T by user screenshots. The earlier research issue below is historical; follow docs/DLC-RESEARCH-RENAMING.md in the project. Rear motor/see-through geometry and pylon glow remain unresolved unless separately verified.\n\n';
  if update not in text:h.write_text(update+text,encoding='utf-8')
print('Verified procedure, screenshots, installation status and project entry point saved. Game files unchanged.')
