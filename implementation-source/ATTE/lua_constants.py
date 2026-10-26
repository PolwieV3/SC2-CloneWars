import re,struct,hashlib
def rename(value):
 return re.sub(rb"King\s+Kriptor",b"AT-TE",value,flags=re.I)
def rewrite(blob):
 assert blob[:12]==bytes.fromhex('1b4c75615100010404040400')
 offset=12;output=[blob[:12]];shape=[blob[:12]];changes=[]
 def take(n):
  nonlocal offset
  b=blob[offset:offset+n];assert len(b)==n;offset+=n;output.append(b);shape.append(b);return b
 def integer():return struct.unpack('<I',take(4))[0]
 def string(change=False):
  nonlocal offset
  size=struct.unpack_from('<I',blob,offset)[0];offset+=4;b=blob[offset:offset+size];assert len(b)==size;offset+=size
  if size:assert b[-1:]==b'\0'
  new=rename(b) if change else b
  if new!=b:changes.append({'before':b[:-1].decode('utf-8',errors='replace'),'after':new[:-1].decode('utf-8',errors='replace')})
  output.append(struct.pack('<I',len(new))+new);shape.append(b'<string>')
 def function():
  string();take(8);take(4);take(integer()*4)
  for _ in range(integer()):
   tag=take(1)[0]
   if tag==0:pass
   elif tag==1:take(1)
   elif tag==3:take(4)
   elif tag==4:string(True)
   else:raise ValueError(tag)
  for _ in range(integer()):function()
  take(integer()*4)
  for _ in range(integer()):string();take(8)
  for _ in range(integer()):string()
 function();assert offset==len(blob),(offset,len(blob))
 return b''.join(output),changes,hashlib.sha256(b''.join(shape)).hexdigest()
