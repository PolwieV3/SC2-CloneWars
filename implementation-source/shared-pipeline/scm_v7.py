"""Read/write SC2 v7 geometry while retaining a reference skeleton byte for byte.

Layout checked against the installed UUL0101 meshes. This is a constrained v7
writer, not a general SCM exporter. It deliberately preserves unknown rig fields.
"""
import hashlib
import math
import struct

HEADER = struct.Struct('<4s13I')
VERTEX = struct.Struct('<16f4B')
BONE = struct.Struct('<16f3f4f4i')
MATERIAL = struct.Struct('<5I')


def cstring(raw, offset):
    return raw[offset:raw.index(b'\0', offset)].decode('ascii')


def read(raw):
    h = HEADER.unpack_from(raw)
    if h[0] != b'MODL' or h[1] != 7:
        raise ValueError('Expected an SC2 MODL version 7 mesh')
    if not (h[2] < h[4] < h[7] < h[5] < h[9] < h[12] <= len(raw)):
        raise ValueError('Unexpected SC2 section ordering')
    for offset, marker in [(h[2], b'SKEL'), (h[4], b'VTXL'), (h[7], b'TRIS'), (h[5], b'XTRA'), (h[9], b'INFO'), (h[12], b'MATS')]:
        if raw[offset-4:offset] != marker or offset % 32:
            raise ValueError(f'Invalid or unaligned section {marker!r}')
    bones = [BONE.unpack_from(raw, h[2] + i * BONE.size) for i in range(h[11])]
    vertices = [VERTEX.unpack_from(raw, h[4] + i * VERTEX.size) for i in range(h[6])]
    indices = struct.unpack_from(f'<{h[8]}H', raw, h[7])
    materials = [MATERIAL.unpack_from(raw, h[12] + i * MATERIAL.size) for i in range(h[13])]
    if h[8] % 3 or any(i >= h[6] for i in indices):
        raise ValueError('Invalid triangle index')
    if any(not math.isfinite(v) for row in vertices for v in row[:16]):
        raise ValueError('Non-finite vertex value')
    if any(row[16] >= h[3] for row in vertices):
        raise ValueError('Vertex references a non-skinning bone')
    if sum(m[1] * 3 for m in materials) != h[8]:
        raise ValueError('Material triangle ranges do not cover the mesh')
    for m in materials:
        if m[2] + m[1] * 3 > h[8] or m[3] + m[4] > h[6]:
            raise ValueError('Material draw range exceeds mesh')
        cstring(raw, m[0])
    return {'header': h, 'bones': bones, 'names': [cstring(raw, b[23]) for b in bones],
            'vertices': vertices, 'indices': indices, 'materials': materials,
            'material_names': [cstring(raw, m[0]) for m in materials],
            'extra': raw[h[5]:h[5] + h[6] * 4],
            'info': raw[h[9]:h[9] + h[10]]}


def section(buffer, tag):
    padding = (-len(buffer)) % 32
    if padding <= 4:
        padding += 32
    buffer.extend(b'\xbb' * (padding - 4) + tag)
    return len(buffer)


def write(reference, vertices, indices, materials, extra=None):
    ref = read(reference)
    h = list(ref['header'])
    if not vertices or len(vertices) > 65535:
        raise ValueError('Mesh must have 1..65535 vertices')
    if len(materials) != h[13]:
        raise ValueError('Preserve reference material slot count')
    buffer = bytearray(reference[:h[4]])
    for row in vertices:
        buffer.extend(VERTEX.pack(*row))
    h[6] = len(vertices)
    h[7] = section(buffer, b'TRIS')
    buffer.extend(struct.pack(f'<{len(indices)}H', *indices))
    h[8] = len(indices)
    h[5] = section(buffer, b'XTRA')
    weights = extra if extra is not None else b'\xff\0\0\0' * len(vertices)
    if len(weights) != len(vertices) * 4:
        raise ValueError('Unexpected extra vertex stream length')
    buffer.extend(weights)
    h[9] = section(buffer, b'INFO')
    buffer.extend(ref['info'])
    h[10] = len(ref['info'])
    section(buffer, b'MNAM')
    offsets = []
    for name in ref['material_names']:
        offsets.append(len(buffer)); buffer.extend(name.encode('ascii') + b'\0')
    h[12] = section(buffer, b'MATS')
    for offset, draw in zip(offsets, materials):
        buffer.extend(MATERIAL.pack(offset, *draw))
    HEADER.pack_into(buffer, 0, *h)
    result = bytes(buffer)
    parsed = read(result)
    if parsed['names'] != ref['names'] or parsed['bones'] != ref['bones']:
        raise ValueError('Skeleton changed')
    if result[h[2]:h[4]] != reference[h[2]:ref['header'][4]]:
        raise ValueError('Rig bytes changed')
    return result


def summary(raw):
    m = read(raw)
    return {'version': 7, 'vertices': len(m['vertices']), 'triangles': len(m['indices']) // 3,
            'bones': len(m['bones']), 'skin_bones': m['header'][3], 'material_names': m['material_names'],
            'bounds': [[min(v[k] for v in m['vertices']), max(v[k] for v in m['vertices'])] for k in range(3)],
            'sha256': hashlib.sha256(raw).hexdigest()}
