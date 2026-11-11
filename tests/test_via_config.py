import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
root=Path(__file__).parents[1];sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('via_config',root/'via_config.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class Keyboard:
    def __init__(self):
        self.config={'device':'Keychron Q0 Plus','vid':0x3434,'pid':0x131,'protocol':12,'layers':4,
                     'matrix_rows':6,'matrix_cols':5,'keymaps':[[[0 for _ in range(5)] for _ in range(6)] for _ in range(4)],
                     'encoders':[[[0xaa,0xa9]] for _ in range(4)],'macro_buffer_hex':'00'*84,
                     'macro_count':16,'layout_options_hex':'00000000'}
        self.reply=None;self.writes=[]
        self.macros=bytearray.fromhex(self.config['macro_buffer_hex'])
    def read(self,n,timeout):
        reply=self.reply;self.reply=None
        return reply or b''
    def write(self,report):
        p=bytearray(report[1:]);self.writes.append(p[0]);c=self.config;op=p[0]
        def word(i,value):p[i:i+2]=value.to_bytes(2,'big')
        if op==1:word(1,c['protocol'])
        elif op==0x11:p[1]=c['layers']
        elif op==4:word(4,c['keymaps'][p[1]][p[2]][p[3]])
        elif op==5:c['keymaps'][p[1]][p[2]][p[3]]=int.from_bytes(p[4:6],'big')
        elif op==0x14:word(4,c['encoders'][p[1]][0][p[3]])
        elif op==0x15:c['encoders'][p[1]][0][p[3]]=int.from_bytes(p[4:6],'big')
        elif op==0x0d:word(1,len(self.macros))
        elif op==0x0c:p[1]=c['macro_count']
        elif op in (0x0e,0x0f):
            offset=int.from_bytes(p[1:3],'big');n=p[3]
            if op==0x0e:p[4:4+n]=self.macros[offset:offset+n]
            else:self.macros[offset:offset+n]=p[4:4+n]
        elif op==2:p[2:6]=bytes.fromhex(c['layout_options_hex'])
        elif op==3:c['layout_options_hex']=p[2:6].hex()
        else:raise AssertionError(f'Unexpected opcode {op}')
        self.reply=bytes(p)

class ViaTests(unittest.TestCase):
    def test_backup_is_read_only_and_restore_round_trips(self):
        h=Keyboard();original=copy.deepcopy(h.config);current=v.capture(h)
        self.assertTrue(set(h.writes)<={1,2,4,0x0c,0x0d,0x0e,0x11,0x14})
        for k in ['keymaps','encoders','macro_buffer_hex','layout_options_hex']:self.assertEqual(current[k],original[k])
        saved=copy.deepcopy(current);saved['keymaps'][0][4][1]=0x7e00
        saved['encoders'][0][0]=[0x50,0x4f]
        saved['macro_buffer_hex']='1234'+saved['macro_buffer_hex'][4:]
        saved['layout_options_hex']='00000001'
        v.restore(h,saved,current)
        actual=v.capture(h)
        for k in ['keymaps','encoders','macro_buffer_hex','layout_options_hex']:self.assertEqual(actual[k],saved[k])
    def test_cross_protocol_or_invalid_restore_writes_nothing(self):
        h=Keyboard();current=v.capture(h);h.writes.clear()
        for kind in ['protocol','matrix','macro']:
            saved=copy.deepcopy(current)
            if kind=='protocol':saved['protocol']+=1
            if kind=='matrix':saved['keymaps'][0][0][0]=-1
            if kind=='macro':saved['macro_buffer_hex']=''
            with self.assertRaises(ValueError):v.restore(h,saved,current)
        self.assertEqual(h.writes,[])

if __name__=='__main__':unittest.main()
