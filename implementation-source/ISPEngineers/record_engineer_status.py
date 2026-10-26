from pathlib import Path
import json, shutil
root=Path.cwd()
p=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
event={'date':'2026-10-26','regular_engineer':{'unit':'uul0002','status':'User reports model looks great and works in game','scope':'Overall user report; individual test matrix not supplied'},'field_engineer':{'unit':'uul0003d1','status':'ISP copy with native illuminated pylon installed for testing; runtime pending'},'crew':'Clone troopers planned later; no crew added in this revision','next':'Validate Field Engineer in game, then ground-unit sizing; ACU remains paused'}
(p/'planning/engineer-user-acceptance-2026-10-26.json').write_text(json.dumps(event,indent=2))
f=p/'CURRENT-STATE.md';text=f.read_text(encoding='utf-8');backup=root/'outputs/Field-Engineer-ISP-Test/CURRENT-STATE-before.md'
if not backup.exists():shutil.copy2(f,backup)
text=text.replace('- Remaining unimplemented GAR ground slots: Field Engineer (ISP engineering variant), standard Engineer, ACU.', '- Engineer update October 26: ISP regular Engineer (`UUL0002`) is reported working in game by the user. The matching ISP Field Engineer (`UUL0003D1`) with native illuminated pylon is installed for testing; its runtime checks remain pending. Clone-trooper crew is deferred. ACU remains unimplemented and paused.')
text=text.replace('- Next sequence: Field Engineer, standard Engineer, then pause ACU and conduct a ground-unit sizing pass.', '- Next sequence: validate the installed Field Engineer, then conduct the ground-unit sizing pass with ACU paused.')
f.write_text(text,encoding='utf-8')
print('Recorded user acceptance and staged Field Engineer status.')
