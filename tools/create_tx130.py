"""Blender background authoring for the original TX-130 prototype.

Run with Blender --background --factory-startup --python tools/create_tx130.py.
Authored geometry stays editable in the saved .blend. The native writer uses the
installed tank's unchanged rig and maps vertex bindings by bone name per LOD.
"""
import bpy
import json
import math
import pathlib
import sys
from mathutils import Matrix, Vector

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import scm_v7

OUT=ROOT/'assets/Republic/Models'
BUILD=ROOT/'local/build/tx130'
REFERENCE=ROOT/'local/reference/UUL0101/units/units/UEF/UUL0101'
OUT.mkdir(parents=True,exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
PALETTE=[('Ivory',(159,164,163)),('Republic crimson',(111,43,48)),('Graphite',(29,34,38)),
         ('Gunmetal',(77,86,91)),('Cockpit',(29,66,84)),('Ion blue',(33,160,207)),
         ('Deep crimson',(101,37,42)),('Team markings',(204,204,192)),('Warm steel',(119,122,116)),
         ('Black',(13,18,22)),('Pale armor',(181,186,182)),('Red rim',(145,66,67)),
         ('GAR yellow',(224,207,107)),('Lamp',(221,233,210)),('Engine',(21,53,66)),('White',(227,228,218))]

def linear(v):
    c=v/255
    return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
materials=[]
for name,color in PALETTE:
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=tuple(linear(c) for c in color)+(1,)
    shader.inputs['Metallic'].default_value=0.3 if name not in {'Cockpit','Ion blue','Lamp'} else 0.5
    shader.inputs['Roughness'].default_value=0.4
    if name in {'Ion blue','Lamp'}:
        shader.inputs['Emission Color'].default_value=tuple(linear(c) for c in color)+(1,)
        shader.inputs['Emission Strength'].default_value=0.7
    materials.append(mat)

def cv(p): return Vector((p[0],-p[2],p[1]))
def inv(p): return (p[0],p[2],-p[1])

parts=[]
def part(name,verts,faces,color=0,bone='UUL0101',detail=0,bevel=0,slot=0):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([cv(v) for v in verts],[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    mesh.materials.append(materials[color]);obj['sc2_bone']=bone;obj['palette']=color
    obj['detail_level']=detail;obj['sc2_material_slot']=slot
    if bevel:
        modifier=obj.modifiers.new('Armor edge bevel','BEVEL');modifier.width=bevel;modifier.segments=1
        modifier.affect='EDGES'
    parts.append(obj);return obj

def prism(name,footprint,bottom,top,color=0,bone='UUL0101',detail=0,inset=0,bevel=0,slot=0):
    n=len(footprint);cx=sum(v[0] for v in footprint)/n;cz=sum(v[1] for v in footprint)/n
    verts=[(x,bottom,z) for x,z in footprint]+[(cx+(x-cx)*(1-inset),top,cz+(z-cz)*(1-inset)) for x,z in footprint]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    return part(name,verts,faces,color,bone,detail,bevel,slot)

def box(name,center,size,color=0,bone='UUL0101',detail=0,bevel=0,slot=0):
    x,y,z=center;a,b,c=[v/2 for v in size]
    return prism(name,[(x-a,z-c),(x+a,z-c),(x+a,z+c),(x-a,z+c)],y-b,y+b,color,bone,detail,bevel=bevel,slot=slot)

def tube(name,start,end,radius,color=3,bone='UUL0101',detail=0,sides=12):
    start,end=Vector(start),Vector(end);axis=(end-start).normalized()
    t=axis.cross(Vector((0,1,0)))
    if t.length<0.01:t=Vector((1,0,0))
    t.normalize();v=axis.cross(t).normalized()
    verts=[tuple(p+radius*(math.cos(i*math.tau/sides)*t+math.sin(i*math.tau/sides)*v)) for p in (start,end) for i in range(sides)]
    # Rings are counter-clockwise looking along their axis; reverse start cap.
    faces=[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    return part(name,verts,faces,color,bone,detail)

# Reference-led revision: broad low nose ramp, swept pointed outriggers,
# rear raised cockpit and cheek-mounted long guns rather than a central turret.
def wedge(name,outline,bottom,heights,color=0,bone='UUL0101',detail=0):
    n=len(outline)
    verts=[(x,bottom,z) for x,z in outline]+[(x,y,z) for (x,z),y in zip(outline,heights)]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    return part(name,verts,faces,color,bone,detail,bevel=.10)

wedge('Central floating lower chassis',[(-3.9,-8.8),(3.9,-8.8),(4.4,-3),(3.4,4.8),(2.0,6.8),(-2.0,6.8),(-3.4,4.8),(-4.4,-3)],.7,[1.44]*8,2)
wedge('Broad swept central nose',[(-3.6,-8),(3.6,-8),(3.9,-2.8),(2.4,4.8),(1.8,6.65),(-1.8,6.65),(-2.4,4.8),(-3.9,-2.8)],1.45,[3.8,3.8,4.35,2.5,1.75,1.75,2.5,4.35],0)
for sign,side in [(-1,'Port'),(1,'Starboard')]:
    outline=[(sign*x,z) for x,z in [(3.4,-8.5),(6.2,-7.9),(6.7,-3.0),(6.3,4.3),(5.6,8.65),(4.5,8.65),(3.65,6.7),(3.2,1.0)]]
    if sign<0:outline.reverse()
    heights=[2.4 if z>4 else 3.4 for x,z in outline]
    wedge(side+' pointed repulsor sled',outline,.95,[1.49]*len(outline),2)
    top=[(x,z) for x,z in outline]
    armor=wedge(side+' angular armored outrigger',top,1.5,[2.30 if z>8 else 2.65 if z>4 else 3.6 for x,z in top],0)
    # Paint the actual top face, instead of intersecting armor/decal solids.
    armor.data.materials.append(materials[1])
    armor.data.polygons[1].material_index=1
    box(side+' rear machinery block',(sign*5.25,3.62,-6),(2.25,.9,3.2),8,detail=1,bevel=.13)
    cap=box(side+' rear crimson armor cap',(sign*5.25,4.12,-6),(1.7,.12,2.7),1,detail=0)
    cap['paint_tile']=14;cap['paint_center_x']=sign*5.25;cap['paint_center_z']=-6.0;cap['paint_width']=1.7;cap['paint_depth']=2.7
    box(side+' outboard dark vent',(sign*6.35,2.4,-1.5),(.22,.75,5.2),9,detail=1)
    for j in range(6):box(side+' armor louver '+str(j),(sign*6.48,2.4,-3.7+j*.8),(.16,.65,.16),8,detail=2)
    box(side+' belly cooling fin',(sign*4.7,1.15,-1.4),(1.5,.15,3.0),3,slot=1)
    box(side+' team panel',(sign*6.38,2.5,1.0),(.1,.4,1.3),7,detail=1)
    tube(side+' rear repulsor',(sign*5.15,2,-8),(sign*5.15,2,-8.7),.64,3,detail=1)
    tube(side+' engine glow',(sign*5.15,2,-8.71),(sign*5.15,2,-8.76),.45,5,detail=1)

# Continuous cockpit: raised rear roof slopes down into a long central glacis.
wedge('Sloped rear command cabin',[(-2.9,-7.3),(2.9,-7.3),(2.65,-2.5),(1.7,1.3),(-1.7,1.3),(-2.65,-2.5)],3.0,[5.25,5.25,5.5,3.1,3.1,5.5],0,'UUL0101')
wedge('Cabin red dorsal stripe',[(-.65,-7.1),(.65,-7.1),(.65,-2.5),(.35,1.25),(-.35,1.25),(-.65,-2.5)],3.1,[5.28,5.28,5.54,3.16,3.16,5.54],6,'UUL0101')
box('Wide dark observation slit',(0,5.1,-1.95),(3.7,.5,.15),9,'UUL0101',detail=1)
box('Observation slit armor brow',(0,5.5,-2.02),(4.1,.17,.45),8,'UUL0101',detail=1)
# Nose panel ridges follow the long slope seen in both supplied references.
for sign in [-1,1]:
    wedge('Raised forward panel '+str(sign),[(sign*.65,-1.8),(sign*1.18,-1.8),(sign*.9,5.4),(sign*.55,5.4)],1.8,[4.95,4.95,2.25,2.25],10)
    box('Cheek gun armored pivot '+str(sign),(sign*3.0,4.75,-2.35),(1.35,1.25,2.2),8,'T01_Housing01',bevel=.12)
    tube('Long lateral cannon '+str(sign),(sign*3.0,4.85,-1.5),(sign*3.0,4.85,5.68),.18,3,'T01_Barrel01')
    tube('Cannon root sleeve '+str(sign),(sign*3.0,4.85,-1.45),(sign*3.0,4.85,.1),.3,2,'T01_Barrel01')
    tube('Cannon muzzle '+str(sign),(sign*3.0,4.85,5.15),(sign*3.0,4.85,5.685),.22,9,'T01_Barrel01')
    tube('Research cannon extension '+str(sign),(sign*3.0,4.85,5.7),(sign*3.0,4.85,7.2),.19,3,'T01_Barrel02',detail=1)
    tube('Research parallel cannon '+str(sign),(sign*3.5,4.85,-1.0),(sign*3.5,4.85,5.68),.15,3,'T01_Barrel03',detail=1)
tube('Rear circular commander hatch',(0,5.27,-5.35),(0,5.45,-5.35),1.15,3,'UUL0101',detail=1,sides=16)
hatch=tube('Commander hatch armor',(0,5.45,-5.35),(0,5.55,-5.35),.95,0,'UUL0101',detail=0,sides=16)
hatch['paint_tile']=12;hatch['paint_center_x']=0.;hatch['paint_center_z']=-5.35;hatch['paint_width']=1.9;hatch['paint_depth']=1.9
# Republic insignia are baked onto these armor surfaces, not stacked meshes.
for sign,side in [(-1,'Port'),(1,'Starboard')]:
    for j in range(4):
        box(side+' aft radiator slot '+str(j),(sign*(.7+j*.35),5.27,-6.9),(.16,.055,.55),2,detail=2)
    for j in range(3):
        box(side+' side service seam '+str(j),(sign*6.53,2.64,-3.3+j*1.0),(.03,.52,.05),2,detail=1)
    box(side+' rear access-panel inset',(sign*5.1,3.9,-7.7),(1.1,.07,.3),2,detail=1)
    tube(side+' maintenance handle',(sign*2.35,5.22,-4.8),(sign*2.35,5.22,-4.1),.07,3,detail=2,sides=6)

for sign in [-1,1]:
    tube('Tall communications aerial '+str(sign),(sign*2.0,5.2,-6.7),(sign*2.0,8.8,-6.7),.055,2,detail=2,sides=6)
box('Rear service panel',(0,3.5,-8.04),(3.0,.8,.12),3,detail=1)
box('Research anti-air dorsal module',(0,6.1,-5.3),(1.2,.7,1.8),0,'Turret02',detail=1)

# Editable armature; native exports retain reference bind matrices exactly.
rig_data=bpy.data.armatures.new('UUL0101 preserved rig');rig=bpy.data.objects.new('UUL0101',rig_data)
bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
ref=scm_v7.read((REFERENCE/'UUL0101_LOD0.win.scm').read_bytes())
transform=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
for name,row in zip(ref['names'],ref['bones']):
    matrix=Matrix([row[i:i+4] for i in range(0,16,4)]).transposed().inverted()
    bone=rig_data.edit_bones.new(name);bone.matrix=transform@matrix;bone.length=.65
for i,row in enumerate(ref['bones']):
    if row[24]>=0:rig_data.edit_bones[ref['names'][i]].parent=rig_data.edit_bones[ref['names'][row[24]]]
bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False);rig.show_in_front=True
for obj in parts:
    obj.parent=rig;group=obj.vertex_groups.new(name=obj['sc2_bone']);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    modifier=obj.modifiers.new('Preserved SC2 rig','ARMATURE');modifier.object=rig

def export_geometry(lod):
    groups=[[],[]]
    depsgraph=bpy.context.evaluated_depsgraph_get()
    for obj in parts:
        if obj['detail_level']>2-lod:continue
        if lod==2 and obj['sc2_bone'] in {'T01_Barrel02','T01_Barrel03','T01_Barrel04','Turret02'}:continue
        evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
        color=obj['palette']
        for tri in mesh.loop_triangles:
            face_color=1 if mesh.polygons[tri.polygon_index].material_index==1 else color
            uv=((face_color%4+.5)/4,(face_color//4+.5)/4)
            points=[inv(evaluated.matrix_world@mesh.vertices[i].co) for i in tri.vertices]
            a,b,c=map(Vector,points);normal=(b-a).cross(c-a)
            if normal.length<1e-7:continue
            normal.normalize();tangent=Vector((0,1,0)).cross(normal)
            if tangent.length<.01:tangent=Vector((1,0,0))
            tangent.normalize();binormal=normal.cross(tangent).normalized()
            uvs=None
            if 'paint_tile' in obj and normal.y>.5:
                tile=int(obj['paint_tile']);uvs=[]
                for x,y,z in points:
                    u=(x-obj['paint_center_x'])/obj['paint_width']+.5;v=(z-obj['paint_center_z'])/obj['paint_depth']+.5
                    uvs.append(((tile%4+u)/4,(tile//4+v)/4))
            groups[obj['sc2_material_slot']].append({'uvs':uvs,'positions':points,'normal':list(normal),'tangent':list(tangent),'binormal':list(binormal),'uv':uv,'bone':obj['sc2_bone']})
        evaluated.to_mesh_clear()
    return {'lod':lod,'groups':groups}

for lod in range(3):
    geometry=export_geometry(lod)
    (BUILD/f'geometry-lod{lod}.json').write_text(json.dumps(geometry,separators=(',',':')),encoding='utf-8')
    print('TX130 LOD',lod,'triangles',sum(len(g) for g in geometry['groups']))
(BUILD/'palette.json').write_text(json.dumps(PALETTE,indent=2))

# Use the same authored atlas for the editable Blender preview.
from build_tx130_model import dds
atlas_path=BUILD/'preview-diffuse.dds';atlas_path.write_bytes(dds('Diffuse',PALETTE))
atlas=bpy.data.images.load(str(atlas_path),check_existing=False)
atlas.pack()
for obj in parts:
    if 'paint_tile' not in obj:continue
    mat=bpy.data.materials.new(obj.name+' baked paint');mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=atlas
    mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);shader.inputs['Roughness'].default_value=.65
    obj.data.materials.clear();obj.data.materials.append(mat)
    uv_layer=obj.data.uv_layers.new(name='Armor paint atlas')
    for poly in obj.data.polygons:
        for loop_index in poly.loop_indices:
            position=inv(obj.data.vertices[obj.data.loops[loop_index].vertex_index].co)
            if poly.normal.z>.5:
                tile=int(obj['paint_tile']);u=(position[0]-obj['paint_center_x'])/obj['paint_width']+.5;v=(position[2]-obj['paint_center_z'])/obj['paint_depth']+.5
                uv=((tile%4+u)/4,1-(tile//4+v)/4)
            else:
                color=obj['palette'];uv=((color%4+.5)/4,1-(color//4+.5)/4)
            uv_layer.data[loop_index].uv=uv

# In the presentation, omit parts which the vanilla blueprint hides before research.
disabled={'T01_Barrel02','T01_Barrel03','T01_Barrel04','Turret02'}
for obj in parts:
    if obj['sc2_bone'] in disabled:obj.hide_render=True;obj.hide_set(True)

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48
scene.cycles.use_denoising=True;scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.25));ground=bpy.context.object;ground.name='Preview ground'
ground_mat=bpy.data.materials.new('Preview ground material');ground_mat.diffuse_color=(.16,.17,.18,1);ground.data.materials.append(ground_mat)
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size in [('Key',(12,-12,25),4000,14),('Fill',(-14,-5,15),2600,12),('Rim',(8,15,20),4500,10)]:
    bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.name=name;light.data.energy=power;light.data.shape='DISK';light.data.size=size;aim(light,(0,0,2.5))
bpy.ops.object.camera_add(location=(22,-27,24));camera=bpy.context.object;camera.name='Prototype camera';camera.data.type='ORTHO';camera.data.ortho_scale=29;aim(camera,(0,0,3.2));scene.camera=camera
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'TX130_Prototype-preview.png')
scene['asset_stage']='Model Changed — original TX-130 prototype awaiting in-game test'
scene['source_notes']='Project-authored geometry; preserves the installed SC2 UUL0101 rig. No downloaded Star Wars mesh.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TX130_Prototype.blend'))
bpy.ops.render.render(write_still=True)
print('TX130 original model source and preview saved')
