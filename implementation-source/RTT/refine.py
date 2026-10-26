from pathlib import Path
p=Path('work/rtt/fit.py');s=p.read_text(encoding='utf-8').replace('u.uv.y=.5+.5*u.uv.y','u.uv.y=.5+.5*(u.uv.y%1)');s=s.replace('parts.append(ob)\nfor i,b in enumerate(ids):','bpy.data.objects.remove(ob,do_unlink=True)\nfor i,b in enumerate([]):')
a=s.index("cylinder('Shield generator armored plinth'");b=s.index('# Export native',a)
s=s[:a]+'''cylinder('Shield generator armored plinth',(0,2.65,0),1.5,.45,0,0)
cylinder('Shield generator red band',(0,2.91,0),1.32,.12,0,3)
cylinder('Blue power core',(0,3.15,0),1.02,.35,1,2)
cylinder('Rotating emitter cap',(0,3.42,0),1.38,.2,1,0)
cylinder('Emitter inner face',(0,3.54,0),1.12,.06,1,1)
cylinder('Emitter blue lens',(0,3.58,0),.72,.04,1,2)
for x in [-1,1]:
 for z in [-.9,.9]:
  cylinder('Cooling column',(x,3.18,z),.15,.65,1,1)
  cylinder('Coil blue band',(x,3.2,z),.19,.12,1,2)
''' + s[b:];p.write_text(s,encoding='utf-8')
