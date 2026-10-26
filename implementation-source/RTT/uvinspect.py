import bpy
for o in bpy.data.objects:
 if o.type=='MESH' and o.name=='Hull':
  print('UV',[(l.name,min(u.uv.x for u in l.data),max(u.uv.x for u in l.data),min(u.uv.y for u in l.data),max(u.uv.y for u in l.data)) for l in o.data.uv_layers]);print('mats',[(m.name,len(m.node_tree.nodes) if m.use_nodes else 0) for m in o.data.materials]);print('sample',[list(u.uv) for u in o.data.uv_layers.active.data][:8])
