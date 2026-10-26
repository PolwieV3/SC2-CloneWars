import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=r'C:/Users/gavad/Documents/Codex/2026-10-18/let/outputs/SPHA-T/SPHA-T-animated-source.blend')
ob=bpy.data.objects['Barrel_00'];m=ob.data
adj={i:set() for i in range(len(m.vertices))};bypos={}
for v in m.vertices:bypos.setdefault(tuple(round(x,3) for x in v.co),[]).append(v.index)
for vs in bypos.values():
 for i in vs:adj[i].update(vs)
for e in m.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();out=[]
for i in adj:
 if i in seen:continue
 stack=[i];ids=set()
 while stack:
  j=stack.pop()
  if j in ids:continue
  ids.add(j);stack.extend(adj[j]-ids)
 seen.update(ids);pts=[m.vertices[j].co for j in ids];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
 out.append({'vertices':len(ids),'ids':sorted(ids),'min':lo,'max':hi,'extent':[hi[k]-lo[k] for k in range(3)]})
Path('work/spha/barrel-components.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps([{k:v for k,v in c.items() if k!='ids'} for c in out],indent=2))
