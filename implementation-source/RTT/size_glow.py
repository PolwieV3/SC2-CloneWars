from pathlib import Path
p=Path('work/rtt/fit.py');s=p.read_text(encoding='utf-8').replace('v.co *= 2.0','v.co *= 4.0').replace('location=(26,-36,26)','location=(52,-72,52)').replace('target=Vector((0,0,5))','target=Vector((0,0,10))').replace('cam.data.ortho_scale=30','cam.data.ortho_scale=60');p.write_text(s,encoding='utf-8')
p=Path('work/rtt/build.py');s=p.read_text(encoding='utf-8').replace('rtt-double-size-test-3','rtt-size-glow-test-4');at=s.index("archive=out/");s=s[:at]+'''# P-Shield-specific emitter visuals only; shield coverage and simulation stay unchanged.
import re
effect_checks=[]
with zipfile.ZipFile('B:/SteamLibrary/steamapps/common/Supreme Commander 2/gamedata/uncompiled_lua.scd') as sourcezip:
 for name in sourcezip.namelist():
  if 'uul0201_s_' not in name.lower() or not name.endswith('.bp'):continue
  original=sourcezip.read(name).decode('utf-8');text=original
  for field in ['SizeCurve','StartSizeCurve','EndSizeCurve','VelocityCurve']:
   pattern=r'(?<![A-Za-z])'+field+r'\\s*=\\s*\\{.*?\\n\\s*\\},\\s*\\n\\s*\\},'
   def shrink(match):
    return re.sub(r'([yz]\\s*=\\s*)(-?[0-9]+(?:\\.[0-9]+)?)',lambda m:m[1]+format(float(m[2])*.85,'.6f'),match[0])
   text,count=re.subn(pattern,shrink,text,flags=re.S);assert count==1,(name,field,count)
  payload[name.removeprefix('uncompiled/')]=text.encode('utf-8');effect_checks.append({'file':name,'particle_size_and_travel_scale':.85})
assert len(effect_checks)==3
''' + s[at:];s=s.replace("'simulation_changes':[]","'simulation_changes':[],'glow_effects':effect_checks,'visual_scale_relative_to_test_3':2.0");p.write_text(s,encoding='utf-8')
