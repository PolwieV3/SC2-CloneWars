import bpy,json,sys,math,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
r=Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let');w=r/'work/juggernaut';out=r/'outputs/Juggernaut';S=32.0
# Record material image inputs before replacing preview material.
mats=[m for m in bpy.data.materials if m.name.endswith('Default1')];mats=sorted(mats,key=lambda m:m.name);mi={m.name:i for i,m in enumerate(mats)}
for i,m in enumerate(mats):
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');links=bs.inputs['Base Color'].links;tex=links[0].from_node if links else None
 if tex and tex.type=='TEX_IMAGE':
  im=tex.image;im.filepath_raw=str(w/f'material-{i}.png');im.file_format='PNG';im.save()
(w/'materials.json').write_text(json.dumps([m.name for m in mats]),encoding='utf-8')
# Native bones retain identities and weapon hierarchy; only approved gun chains move.
d=json.loads((w/'native/rig.json').read_text());names=d['names'];old=[Matrix([b[k:k+4] for k in range(0,16,4)]).transposed().inverted() for b in d['bones']];world=[m.copy() for m in old];targets=[(.006,.535,.556),(.121,-.321,.62),(.265,-.325,.539),(-.119,-.326,.62),(-.26,-.327,.538)];tips=[]
for j,c in enumerate(targets,1):
 yi=names.index('Turret%02d'%j);pi=names.index('T%02d_Barrel01'%j);base=Vector((c[0]*S,c[2]*S,-c[1]*S));angle=0;world[yi]=Matrix.Rotation(math.radians(angle),4,'Y');world[yi].translation=base;world[pi]=world[yi].copy();world[pi].translation=base+Vector((.085 if j==1 else 0,1.012 if j==1 else .48,0))
 for k,x in enumerate(([-.07,0,.07] if j==1 else ([-.30,.30,-.30] if j in [2,4] else [-.52,0,.52])),1):
  n='T%02d_B01_Muzzle%02d'%(j,k);bi=names.index(n);world[bi]=world[pi].copy();world[bi].translation=world[pi]@Vector((x,0,4.14464 if j==1 else (2.9 if j in [2,4] else 1.65)));tips.append({'name':n,'barrel':('UUX0101' if j in [3,5] else 'T%02d_Barrel01'%j),'position':list(world[bi].translation)})
# New per-wheel visual bones, separate from original turning tread controllers.
wc=json.loads((w/'wheel-components.json').read_text());centers=[Vector(tuple((a+b)/2 for a,b in zip(c['min'],c['max']))) for c in wc];wheel_names=[]
for i,c in enumerate(centers,1):
 n='JUG_Wheel%02d'%i;wheel_names.append(n);names.append(n);bm=Matrix.Identity(4);bm.translation=Vector((c.x*S,c.z*S,-c.y*S));world.append(bm)
# Three visual AA joints added to the existing unused source gun, no new meshes.
aa_world=[Vector((.004*S,.619*S,.018*S)),Vector((.004*S,.664*S,.025*S)),Vector((.004*S,.664*S,.103142*S))]
for name,point in zip(['JUG_AA_Yaw','JUG_AA_Pitch','JUG_AA_Muzzle'],aa_world):
 names.append(name);matrix=Matrix.Identity(4);matrix.translation=point;world.append(matrix)
tips.append({'name':'JUG_AA_Muzzle','barrel':'JUG_AA_Pitch','position':list(aa_world[2])})
rows=[]
for i,n in enumerate(names):
 parent=d['bones'][i][24] if i<len(d['bones']) else 0
 if n.startswith(('T03_B01_Muzzle','T05_B01_Muzzle')):parent=0
 if n=='JUG_AA_Pitch':parent=names.index('JUG_AA_Yaw')
 if n=='JUG_AA_Muzzle':parent=names.index('JUG_AA_Pitch')
 local=world[parent].inverted()@world[i] if parent>=0 else world[i];q=local.to_quaternion();inv=world[i].inverted();rows.append({'name':n,'parent':parent,'inverse':[inv[a][b] for b in range(4) for a in range(4)],'position':list(local.translation),'quaternion':list(q),'world':[list(v) for v in world[i]]})
(w/'fitted-rig.json').write_text(json.dumps({'bones':rows,'tips':tips,'scale':S,'wheel_radius_world':.1315*S*.18},indent=2),encoding='utf-8')
parts=[]
def register(ob,bone,material_index=None,reduce=True):
 ob['bone']=bone;ob['reduce']=reduce
 if material_index is not None:ob['material_index']=material_index
 parts.append(ob)
# Preserve only original hull/chassis/tower; weapon pieces are replaced explicitly.
remove={'Object_14','Object_16','Object_18','Object_22','Object_24','Object_38','Object_40','Object_42','Object_46','Object_48','Object_50','Object_52','Object_54','Object_56','Object_58'}
main_ps=[bpy.data.objects['Object_20'].matrix_world@v.co for v in bpy.data.objects['Object_20'].data.vertices];small_ps=[bpy.data.objects['Object_16'].matrix_world@v.co for v in bpy.data.objects['Object_16'].data.vertices]
housing_main=bpy.data.objects['Object_20'].copy();housing_main.data=bpy.data.objects['Object_20'].data.copy();housing_small=bpy.data.objects['Object_16'].copy();housing_small.data=bpy.data.objects['Object_16'].data.copy()
# The central narrow rear components are the existing gun/sight; base stays on hull.
rear=bpy.data.objects['Object_20'];adj={};keys={}
for v in rear.data.vertices:
 key=tuple(round(x,5) for x in v.co);keys[v.index]=key;adj.setdefault(key,set())
for edge in rear.data.edges:
 a,b=[keys[k] for k in edge.vertices];adj[a].add(b);adj[b].add(a)
groups={};seen=set()
for key in adj:
 if key in seen:continue
 stack=[key];seen.add(key);component=[]
 while stack:
  q=stack.pop();component.append(q)
  for other in adj[q]:
   if other not in seen:seen.add(other);stack.append(other)
 ps=[rear.matrix_world@Vector(q) for q in component];lo=[min(p[k] for p in ps) for k in range(3)];hi=[max(p[k] for p in ps) for k in range(3)]
 bone='DROP' if lo[0]>-.02 and hi[0]<.02 and lo[2]>.57 else ('UUX0101' if hi[2]<.56 else 'Turret01')
 for q in component:groups[q]=bone
rear_weights={i:groups[key] for i,key in keys.items()}
# Classify complete connected gun/stem components to avoid mixed bone triangles.
aa_source=bpy.data.objects['Object_6'];aa_adj={};aa_keys={}
for v in aa_source.data.vertices:
 key=tuple(round(x,5) for x in v.co);aa_keys[v.index]=key;aa_adj.setdefault(key,set())
for e in aa_source.data.edges:
 a,b=[aa_keys[i] for i in e.vertices];aa_adj[a].add(b);aa_adj[b].add(a)
aa_seen=set();aa_groups={}
for key in aa_adj:
 if key in aa_seen:continue
 stack=[key];aa_seen.add(key);component=[]
 while stack:
  q=stack.pop();component.append(q)
  for other in aa_adj[q]:
   if other not in aa_seen:aa_seen.add(other);stack.append(other)
 ps=[aa_source.matrix_world@Vector(q) for q in component];lo=[min(v[k] for v in ps) for k in range(3)];hi=[max(v[k] for v in ps) for k in range(3)]
 bone=None
 if lo[1]>-.12 and hi[1]<.02 and lo[0]>-.04 and hi[0]<.04:
  if lo[2]>.64:bone='JUG_AA_Pitch'
  elif lo[2]>.61 and hi[2]<.66:bone='JUG_AA_Yaw'
 if bone:
  for q in component:aa_groups[q]=bone
aa_weights={i:aa_groups.get(key) for i,key in aa_keys.items()}
for ob in list(bpy.data.objects):
 if ob.type!='MESH' or ob in [housing_main,housing_small]:continue
 if ob.name in remove or (ob.parent and ob.parent.name.startswith('C-')):bpy.data.objects.remove(ob,do_unlink=True);continue
 matrix=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=Matrix.Identity(4)
 for v in ob.data.vertices:
  p=matrix@v.co;v.co=(p.x*S,p.z*S,-p.y*S)
 if ob.name=='Object_36':
  for i in range(10):ob.vertex_groups.new(name=wheel_names[i])
  for v in ob.data.vertices:
   original=Vector((v.co.x/S,-v.co.z/S,v.co.y/S));i=min(range(10),key=lambda k:(original-centers[k]).length_squared);ob.vertex_groups[i].add([v.index],1,'REPLACE')
  register(ob,'WHEELS',reduce=False)
 elif ob.name=='Object_20':
  # Source pod points toward the rear; turn its upper swivel/gun forward.
  pivot=world[names.index('Turret01')].translation
  for v in ob.data.vertices:
   if rear_weights[v.index]!='UUX0101':v.co=pivot+Matrix.Rotation(math.pi,3,'Y')@(v.co-pivot)
  for name in ['UUX0101','Turret01','T01_Barrel01','DROP']:ob.vertex_groups.new(name=name)
  for v in ob.data.vertices:ob.vertex_groups[rear_weights[v.index]].add([v.index],1,'REPLACE')
  bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i,bone in rear_weights.items() if bone=='DROP'],context='VERTS');bm.to_mesh(ob.data);bm.free()
  register(ob,'WEIGHTED',reduce=False)
 elif ob.name=='Object_6':
  for name in ['UUX0101','T01_Barrel01','JUG_AA_Yaw','JUG_AA_Pitch']:ob.vertex_groups.new(name=name)
  pivot=world[names.index('Turret01')].translation
  for v in ob.data.vertices:
   source=Vector((v.co.x/S,-v.co.z/S,v.co.y/S))
   gun=abs(source.x)<.035 and .55<source.y<.70 and .57<source.z<.62
   if gun:v.co=pivot+Matrix.Rotation(math.pi,3,'Y')@(v.co-pivot)
   bone=aa_weights[v.index] or ('T01_Barrel01' if gun else 'UUX0101');ob.vertex_groups[bone].add([v.index],1,'REPLACE')
  register(ob,'WEIGHTED',reduce=False)
 else:register(ob,'UUX0101')
# Source-style turret domes now follow native yaw joints at selected Juggernaut mounts.
for j in [2,4]:
 template=housing_main if j==1 else housing_small;ob=template.copy();ob.data=template.data.copy();bpy.context.collection.objects.link(ob);oldmatrix=template.matrix_world.copy();ps=main_ps if j==1 else small_ps;center=sum(ps,Vector())/len(ps);target=world[names.index('Turret%02d'%j)].translation;ob.parent=None;ob.matrix_world=Matrix.Identity(4)
 for v,p in zip(ob.data.vertices,ps):v.co=target+Vector(((p.x-center.x)*S,(p.z-center.z)*S,-(p.y-center.y)*S))
 register(ob,'Turret%02d'%j);ob.name='Juggernaut gun %02d housing'%j
# Three barrels per native weapon preserve the existing three-rack firing pattern.
palette=bpy.data.materials.new('Gun metal');palette.diffuse_color=(.23,.24,.22,1)
for j in [2,4]:
 pi=names.index('T%02d_Barrel01'%j);mat=world[pi];length=4.14464 if j==1 else (2.9 if j in [2,4] else 1.65)
 for k,x in enumerate(([0] if j==1 else ([-.30,.30] if j in [2,4] else [-.52,0,.52])),1):
  seg=16;verts=[];faces=[]
  profile=[(0,.29),(.45,.29),(.52,.22),(.72,.22),(.76,.255),(.88,.255),(.92,.18),(1.23,.18),(1.27,.23),(1.39,.23),(1.43,.17),(2.15,.17),(2.19,.23),(2.33,.23),(2.38,.16),(2.62,.16),(2.68,.22),(2.9,.22),(2.9,.105),(2.54,.105)]
  for z,radius in profile:
   for a in range(seg):
    ang=a*math.tau/seg;verts.append(tuple(mat@Vector((x+radius*math.cos(ang),radius*math.sin(ang),z))))
  for layer in range(len(profile)-1):
   for a in range(seg):faces.append((layer*seg+a,layer*seg+(a+1)%seg,(layer+1)*seg+(a+1)%seg,(layer+1)*seg+a))
  me=bpy.data.meshes.new('Barrel');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Gun %02d barrel %02d'%(j,k),me);bpy.context.collection.objects.link(ob);uv=me.uv_layers.new();me.materials.append(palette);me.materials.append(palette);me.materials.append(palette)
  for face in me.polygons:face.material_index=2 if face.index//seg==len(profile)-2 else (1 if face.index//seg in [3,7,11,16,17] else 0)
  ob['gun_shading']=True;register(ob,('UUX0101' if j in [3,5] else 'T%02d_Barrel01'%j),-1,False)
# Beveled armored receivers enclose both breeches and seat into the yaw bases.
for j in [2,4]:
 mat=world[names.index('Turret%02d'%j)];cross=[(-.72,-.32),(.72,-.32),(.98,-.08),(.98,.76),(.72,1.04),(-.72,1.04),(-.98,.76),(-.98,-.08)]
 vs=[tuple(mat@Vector((x,y,z))) for z in [-1.25,.35] for x,y in cross]
 fs=[tuple(range(7,-1,-1)),tuple(range(8,16))]+[(a,(a+1)%8,(a+1)%8+8,a+8) for a in range(8)]
 fs=[(face[0],face[k],face[k+1]) for face in fs for k in range(1,len(face)-1)]
 me=bpy.data.meshes.new('Armored receiver');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('Front gun %02d armored cradle'%j,me);bpy.context.collection.objects.link(ob);me.materials.append(palette);me.uv_layers.new();register(ob,'Turret%02d'%j,-2,False)
# Existing source port panels remain; no added side housings or barrels.
for j in []:
 mat=world[names.index('Turret%02d'%j)];vs=[tuple(mat@Vector((x,y,z))) for x,y,z in [(-1.0,-.45,-.9),(1.0,-.45,-.9),(1.0,.90,-.9),(-1.0,.90,-.9),(-1.0,-.45,3.4),(1.0,-.45,3.4),(1.0,.90,3.4),(-1.0,.90,3.4)]]
 fs=[(0,3,2,1),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
 me=bpy.data.meshes.new('Missile pod armor');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('Side missile pod %02d'%j,me);bpy.context.collection.objects.link(ob);me.materials.append(palette);me.uv_layers.new();register(ob,'UUX0101',-1,False)

# Per-corner source UVs are remapped into the four texture atlas tiles.
for ob in parts:
 me=ob.data
 if not me.uv_layers:me.uv_layers.new()
 for poly in me.polygons:
  material=me.materials[poly.material_index] if me.materials else None;tile=mi.get(material.name,0) if material else 0
  for li in poly.loop_indices:
   uv=me.uv_layers.active.data[li].uv
   if ob.get('material_index')==-1:
    vi=me.loops[li].vertex_index;uv[:]=((poly.material_index*.25)+.005+(vi%16)/16*.24,.005+(vi//16)/19*.24) if ob.get('gun_shading') else (.125,.125)
   elif ob.get('material_index')==-2:
    p=world[names.index(ob['bone'])].inverted()@me.vertices[me.loops[li].vertex_index].co
    normal=poly.normal;axis=max(range(3),key=lambda k:abs(normal[k]))
    if axis==2:u,v=(p.x+.98)/1.96,(p.y+.32)/1.36
    elif axis==1:u,v=(p.x+.98)/1.96,(p.z+1.25)/1.60
    else:u,v=(p.z+1.25)/1.60,(p.y+.32)/1.36
    uv[:]=(.5+.25*(.4+u*.35),.75+.25*(.6+v*.25))
   else:uv[:]=((uv.x%1)*.25+tile*.25,(uv.y%1)*.25+.75)
# Requested uniform 10% visual enlargement, including skeleton and firing origins.
factor=1.1
for ob in parts:
 for v in ob.data.vertices:v.co*=factor
for bm in world:bm.translation*=factor
for row in rows:
 row['position']=[v*factor for v in row['position']]
 for k in [12,13,14]:row['inverse'][k]*=factor
 for k in range(3):row['world'][k][3]*=factor
for tip in tips:tip['position']=[v*factor for v in tip['position']]
(w/'fitted-rig.json').write_text(json.dumps({'bones':rows,'tips':tips,'scale':S*factor,'visual_enlargement':factor,'wheel_radius_world':.1315*S*.18*factor},indent=2),encoding='utf-8')
# Export exactly the fitted geometry with reduced hull LODs; wheels and tips retained.
for lod,ratio in enumerate([1,.6,.3]):
 triangles=[]
 for original in parts:
  ob=original.copy();ob.data=original.data.copy();bpy.context.collection.objects.link(ob)
  if ratio<1 and original['reduce'] and len(ob.data.polygons)>80:
   mod=ob.modifiers.new('Distance reduction','DECIMATE');mod.ratio=ratio;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
  me=ob.data;me.calc_loop_triangles();me.calc_tangents();gn={g.index:g.name for g in ob.vertex_groups}
  for tri in me.loop_triangles:
   rows=[]
   for li in tri.loops:
    loop=me.loops[li];v=me.vertices[loop.vertex_index];bone=ob['bone']
    if bone in ['WHEELS','WEIGHTED']:bone=gn[max(v.groups,key=lambda g:g.weight).group]
    uv=list(me.uv_layers.active.data[li].uv);rows.append(list(v.co)+list(me.corner_normals[li].vector)+list(loop.tangent)+list(loop.bitangent)+uv+uv+[names.index(bone),0,0,0])
   triangles.append(rows)
  bpy.data.objects.remove(ob,do_unlink=True)
 (w/f'geometry-lod{lod}.json').write_text(json.dumps({'triangles':triangles},separators=(',',':')),encoding='utf-8');print('LOD',lod,'triangles',len(triangles))
# Prepare preview in Z-up with the exact exported positions.
for ob in parts:
 for v in ob.data.vertices:p=v.co.copy();v.co=(p.x,-p.z,p.y)
 ob.data.update()
(w/'fit-parts.json').write_text(json.dumps({'scale':S,'weapon_positions':[list(world[names.index('Turret%02d'%j)].translation) for j in range(1,6)],'wheel_count':10,'parts':[ob.name for ob in parts]},indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Juggernaut-native-fit.blend'))
