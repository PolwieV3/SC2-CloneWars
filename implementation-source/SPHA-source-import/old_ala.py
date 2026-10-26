import struct
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
import bpy

def chunks(b):
 p=0
 while p<len(b):
  typ,n=struct.unpack_from('<II',b,p);n&=0x7fffffff
  assert p+8+n<=len(b)
  yield typ,b[p+8:p+8+n];p+=8+n
 assert p==len(b)
def minis(b):
 p=0;out={}
 while p<len(b):
  t,n=b[p:p+2];out[t]=b[p+2:p+2+n];p+=2+n
 assert p==len(b)
 return out

def load(path,arm):
 root=list(chunks(path.read_bytes()));assert len(root)==1 and root[0][0]==0x1000
 cs=list(chunks(root[0][1]));h=minis(cs[0][1]);frames=struct.unpack('<I',h[1])[0];fps=struct.unpack('<f',h[2])[0];count=struct.unpack('<I',h[3])[0];tracks=[]
 for typ,data in cs[1:]:
  assert typ==0x1002
  parts=list(chunks(data));info=minis(parts[0][1]);name=info[4].rstrip(b'\0').decode();track={'name':name,'offset':Vector(struct.unpack('<3f',info[6])),'scale':Vector(struct.unpack('<3f',info[7]))}
  for t,v in parts[1:]:
   if t==0x1004:track['pos']=[struct.unpack_from('<3H',v,i) for i in range(0,len(v),6)]
   elif t==0x1006:track['rot']=[Quaternion((q[3]/32767,q[0]/32767,q[1]/32767,q[2]/32767)).normalized() for q in [struct.unpack_from('<4h',v,i) for i in range(0,len(v),8)]]
   elif t!=0x1007:raise ValueError(hex(t))
  assert len(track['rot']) in (1,frames)
  if 'pos' in track:assert len(track['pos']) in (1,frames)
  assert name in arm.pose.bones,name
  tracks.append(track)
 assert len(tracks)==count
 arm.animation_data_create();action=bpy.data.actions.new(path.stem);action.use_fake_user=True;arm.animation_data.action=action
 sampled=sorted(set([0,frames-1]+list(range(0,frames,4))))
 for frame in sampled:
  for t in tracks:
   bone=arm.pose.bones[t['name']];bone.rotation_mode='QUATERNION';p=t['offset'].copy()
   if 'pos' in t:p+=Vector([t['pos'][min(frame,len(t['pos'])-1)][i]*t['scale'][i] for i in range(3)])
   q=t['rot'][min(frame,len(t['rot'])-1)];local=Matrix.Translation(p)@q.to_matrix().to_4x4();rest=bone.bone.matrix_local
   if bone.parent:rest=bone.parent.bone.matrix_local.inverted()@rest
   bone.matrix_basis=rest.inverted()@local
   bone.keyframe_insert(data_path='location',frame=frame);bone.keyframe_insert(data_path='rotation_quaternion',frame=frame)
 return {'name':path.stem,'frames':frames,'fps':fps,'bones':count,'sampled_frames':len(sampled),'duration':(frames-1)/fps}
