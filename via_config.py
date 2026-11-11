#!/usr/bin/env python3
"""Read-only VIA backup by default; restoring requires --restore and --yes."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from bridge import open_keyboard

def request(h, data):
    while h.read(32, 1): pass
    h.write(b'\0' + bytes(data).ljust(32, b'\0'))
    r=bytes(h.read(32,1500))
    if len(r)!=32 or r[0]!=data[0]:raise RuntimeError(f'Unexpected VIA response to {data[0]:02x}')
    return r

def capture(h):
    ask=lambda d:request(h,d)
    protocol=int.from_bytes(ask([1])[1:3],'big');layers=ask([0x11])[1]
    if not 1<=layers<=16:raise RuntimeError('Invalid layer count')
    keymaps=[[[int.from_bytes(ask([4,l,r,c])[4:6],'big') for c in range(5)] for r in range(6)] for l in range(layers)]
    encoders=[[[int.from_bytes(ask([0x14,l,0,d])[4:6],'big') for d in range(2)]] for l in range(layers)]
    size=int.from_bytes(ask([0x0d])[1:3],'big')
    if size>32768:raise RuntimeError('Unexpected macro buffer size')
    macros=bytearray()
    for offset in range(0,size,28):
        n=min(28,size-offset);macros.extend(ask([0x0e,offset>>8,offset&255,n])[4:4+n])
    return {'device':'Keychron Q0 Plus','vid':0x3434,'pid':0x131,'protocol':protocol,'layers':layers,
            'matrix_rows':6,'matrix_cols':5,'keymaps':keymaps,'encoders':encoders,
            'macro_buffer_hex':macros.hex(),'macro_count':ask([0x0c])[1],
            'layout_options_hex':ask([2,2])[2:6].hex(),
            'captured_at':datetime.now(timezone.utc).isoformat(),
            'note':'Read-only VIA configuration backup; not a flash firmware dump.'}

def validate(saved,current):
    for k in ['device','vid','pid','protocol','layers','matrix_rows','matrix_cols','macro_count']:
        if saved[k]!=current[k]:raise ValueError(f'Configuration mismatch: {k}; raw restore across QMK versions is not supported')
    maps=saved['keymaps'];enc=saved['encoders']
    if len(maps)!=saved['layers'] or len(enc)!=saved['layers']:raise ValueError('Invalid layers')
    for layer in maps:
        if len(layer)!=6 or any(len(row)!=5 for row in layer):raise ValueError('Invalid matrix')
        if any(type(v) is not int or not 0<=v<=65535 for row in layer for v in row):raise ValueError('Invalid keycode')
    for layer in enc:
        if len(layer)!=1 or len(layer[0])!=2 or any(type(v)is not int or not 0<=v<=65535 for v in layer[0]):raise ValueError('Invalid encoder')
    if len(bytes.fromhex(saved['macro_buffer_hex']))!=len(bytes.fromhex(current['macro_buffer_hex'])):raise ValueError('Macro capacity differs')
    if len(bytes.fromhex(saved['layout_options_hex']))!=4:raise ValueError('Invalid layout options')

def restore(h,saved,current):
    validate(saved,current) # Everything is validated before the first write.
    for l,layer in enumerate(saved['keymaps']):
        for r,row in enumerate(layer):
            for c,v in enumerate(row):request(h,[5,l,r,c,v>>8,v&255])
    for l,layer in enumerate(saved['encoders']):
        for d,v in enumerate(layer[0]):request(h,[0x15,l,0,d,v>>8,v&255])
    macros=bytes.fromhex(saved['macro_buffer_hex'])
    for offset in range(0,len(macros),28):
        chunk=macros[offset:offset+28];request(h,[0x0f,offset>>8,offset&255,len(chunk),*chunk])
    request(h,[3,2,*bytes.fromhex(saved['layout_options_hex'])])
    actual=capture(h)
    for k in ['keymaps','encoders','macro_buffer_hex','layout_options_hex']:
        if actual[k]!=saved[k]:raise RuntimeError(f'Restore read-back failed: {k}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--backup',type=Path)
    g.add_argument('--restore',type=Path)
    p.add_argument('--yes',action='store_true',help='Explicitly permit VIA configuration writes')
    a=p.parse_args()
    if a.restore and not a.yes:p.error('Restore requires --yes; stop the bridge and VIA before restoring')
    if a.backup and a.backup.exists():p.error('Refusing to overwrite an existing backup')
    h=open_keyboard()
    try:
        current=capture(h)
        if a.backup:a.backup.write_text(json.dumps(current,indent=2)+'\n');print('Saved read-only VIA backup')
        else:
            saved=json.loads(a.restore.read_text());validate(saved,current)
            safety=a.restore.with_name(f'before-restore-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json')
            with safety.open('x') as f:json.dump(current,f,indent=2)
            restore(h,saved,current);print('Restored and verified VIA configuration')
    finally:h.close()
