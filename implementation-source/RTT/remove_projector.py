from pathlib import Path
p=Path('work/rtt/fit.py');s=p.read_text(encoding='utf-8');a=s.index('def cylinder(');b=s.index('# Export native',a);s=s[:a]+s[b:];p.write_text(s,encoding='utf-8')
p=Path('work/rtt/build.py');s=p.read_text(encoding='utf-8').replace('rtt-shield-test-1','rtt-plain-hull-test-2').replace('Custom emitter bound to rotating Turret01; opening arm geometry omitted.','No added projector or native unfolding arm geometry. Plain rigid RTT hull.');p.write_text(s,encoding='utf-8')
