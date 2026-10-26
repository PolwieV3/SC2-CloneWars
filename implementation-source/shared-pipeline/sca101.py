"""Constrained reader for the two UUL0105 sparse float-key ANIM101 clips.

Layout inferred and checked against complete local files: 7-float DATA preamble,
then one uint32 count and count*(time, quaternion WXYZ, position XYZ) per bone.
No engine playback claim. Original clips are retained unless explicitly patched.
"""
import struct,math
def read(raw):
 h=struct.unpack_from('<4sII f 5I',raw)
 assert h[0:2]==(b'ANIM',101)
 frames,duration,bone_count,name_off,link_off,data_off,frame_size=h[2:]
 names=raw[name_off:link_off-4].split(b'\0')[:bone_count]
 names=[n.decode('ascii') for n in names]
 parents=struct.unpack_from(f'<{bone_count}i',raw,link_off)
 preamble=struct.unpack_from('<7f',raw,data_off)
 offset=data_off+28;tracks=[]
 for name in names:
  count=struct.unpack_from('<I',raw,offset)[0];offset+=4
  assert 0<count<=frames
  keys=[struct.unpack_from('<8f',raw,offset+32*j) for j in range(count)]
  assert all(all(math.isfinite(v) for v in k) for k in keys)
  assert keys[0][0]==0 and abs(keys[-1][0]-duration)<1e-6
  assert all(a[0]<b[0] for a,b in zip(keys,keys[1:]))
  assert all(abs(sum(v*v for v in k[1:5])-1)<1e-5 for k in keys)
  tracks.append({'name':name,'offset':offset,'keys':keys});offset+=count*32
 assert offset==len(raw)
 return {'frames':frames,'duration':duration,'names':names,'parents':parents,'preamble':preamble,'tracks':tracks,'parsed_bytes':offset}
