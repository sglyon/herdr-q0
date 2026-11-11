import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bridge',Path(__file__).parents[1]/'bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def state():
    return {'version':1,'revision':123,'timestamp':100000,'enabled':True,'slots':[
        {'slot':i,'address':f'remote/t{i}','state':'working'} for i in range(1,10)]}

class BridgeTests(unittest.TestCase):
    def test_all_slots_and_revision(self):
        s=state()
        for i in range(1,10):
            self.assertEqual(b.selection_command(b.packet(3,123,bytes([i])),s),f'q0-agents.select-123-{i}')
        for i in [0,10,255]:self.assertIsNone(b.selection_command(b.packet(3,123,bytes([i])),s))
        self.assertIsNone(b.selection_command(b.packet(3,122,b'\x01'),s))
        self.assertIsNone(b.selection_command(b.packet(3,123,b'\x01')[:20],s))
    def test_offline_mode_and_toggle(self):
        s=state();s['slots'][0]['state']='unavailable'
        self.assertIsNone(b.selection_command(b.packet(3,123,b'\x01'),s))
        s['enabled']=False
        self.assertIsNone(b.selection_command(b.packet(3,123,b'\x02'),s))
        self.assertEqual(b.selection_command(b.packet(5,123),s),'q0-agents.mode-123-0')
        self.assertEqual(b.selection_command(b.packet(5,123,b'\x01'),s),'q0-agents.mode-123-1')
        self.assertIsNone(b.selection_command(b.packet(5,123,b'\x02'),s))
    def test_wire_encoding(self):
        s=state();s['revision']=0x78563412
        p=b.state_packet(s)
        self.assertEqual(len(p),32);self.assertEqual(p[5:9],bytes.fromhex('12345678'))
        self.assertEqual(p[9:19],bytes([1]+[2]*9))
    def test_freshness_and_malformed_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s.json';s=state();p.write_text(json.dumps(s))
            self.assertEqual(b.read_snapshot(p,101)['revision'],123)
            for now in [104,99]:
                with self.assertRaises(ValueError):b.read_snapshot(p,now)
            s['slots'][0]['slot']=9;p.write_text(json.dumps(s))
            with self.assertRaises(ValueError):b.read_snapshot(p,101)
    def test_handshake_does_not_activate_or_write_via_settings(self):
        class Fake:
            def __init__(self):self.writes=[]
            def write(self,p):self.writes.append(p)
            def read(self,n,timeout):return b.packet(0x81,0,b'Q0H1')
        h=Fake();b.handshake(h)
        self.assertEqual(h.writes,[b'\0'+b.packet(1)])
    def test_bridge_loop_dispatches_one_press_then_disables_when_mod_stops(self):
        class FakeHID:
            def __init__(self):self.writes=[];self.reads=0;self.closed=False
            def write(self,p):self.writes.append(p)
            def read(self,n,timeout):
                self.reads+=1
                if self.reads==1:return b.packet(0x81,0,b'Q0H1')
                if self.reads==2:return b.packet(3,123,b'\x01')
                return b''
            def close(self):self.closed=True
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.state.json').write_text(json.dumps(state()))
            device=FakeHID();clock=[0];calls=[]
            def sleep(dt):
                clock[0]+=dt
                if clock[0]>0.2:(root/'.state.json').unlink(missing_ok=True)
                if clock[0]>1.1:raise KeyboardInterrupt()
            def command(args,**kwargs):
                calls.append(args)
                return type('Result',(),{'returncode':0})()
            with patch.object(b,'open_keyboard',return_value=device),patch.object(b.time,'monotonic',lambda:clock[0]),patch.object(b.time,'time',lambda:100+clock[0]),patch.object(b.time,'sleep',sleep),patch.object(b.subprocess,'run',side_effect=command):
                with self.assertRaises(KeyboardInterrupt):b.run(root,'herdr-app','Herdr.app')
            self.assertEqual(calls[0],['herdr-app','do','q0-agents.select-123-1'])
            self.assertEqual(calls[1],['/usr/bin/open','-a','Herdr.app'])
            self.assertEqual(len(calls),2)
            self.assertTrue(device.closed)
            self.assertTrue(any(p[5]==2 for p in device.writes))
            self.assertEqual(device.writes[-1],b'\0'+b.packet(4))
    def test_physical_mode_press_dispatches_without_activating_herdr(self):
        class FakeHID:
            def __init__(self):self.reads=0
            def write(self,p):pass
            def read(self,n,timeout):
                self.reads+=1
                if self.reads==1:return b.packet(0x81,0,b'Q0H1')
                if self.reads==2:return b.packet(5,123,b'\x00')
                return b''
            def close(self):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.state.json').write_text(json.dumps(state()))
            clock=[0];calls=[]
            def sleep(dt):
                clock[0]+=dt
                if clock[0]>0.1:raise KeyboardInterrupt()
            def command(args,**kwargs):
                calls.append(args)
                return type('Result',(),{'returncode':0})()
            with patch.object(b,'open_keyboard',return_value=FakeHID()),patch.object(b.time,'monotonic',lambda:clock[0]),patch.object(b.time,'time',lambda:100+clock[0]),patch.object(b.time,'sleep',sleep),patch.object(b.subprocess,'run',side_effect=command):
                with self.assertRaises(KeyboardInterrupt):b.run(root,'herdr-app','Herdr.app')
            self.assertEqual(calls,[['herdr-app','do','q0-agents.mode-123-0']])

    def test_failed_foreground_activation_remains_visible(self):
        class FakeHID:
            def __init__(self):self.reads=0
            def write(self,p):pass
            def read(self,n,timeout):
                self.reads+=1
                if self.reads==1:return b.packet(0x81,0,b'Q0H1')
                if self.reads==2:return b.packet(3,123,b'\x01')
                return b''
            def close(self):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.state.json').write_text(json.dumps(state()))
            clock=[0];calls=[]
            def sleep(dt):
                clock[0]+=dt
                if clock[0]>0.3:raise KeyboardInterrupt()
            def command(args,**kwargs):
                calls.append(args)
                return type('Result',(),{'returncode':int(args[0]=='/usr/bin/open')})()
            with patch.object(b,'open_keyboard',return_value=FakeHID()),patch.object(b.time,'monotonic',lambda:clock[0]),patch.object(b.time,'time',lambda:100+clock[0]),patch.object(b.time,'sleep',sleep),patch.object(b.subprocess,'run',side_effect=command):
                with self.assertRaises(KeyboardInterrupt):b.run(root,'herdr-app','/custom/Herdr.app')
            self.assertEqual(calls[1],['/usr/bin/open','-a','/custom/Herdr.app'])
            self.assertIn('Check --app-path',json.loads((root/'.bridge-status.json').read_text())['message'])

if __name__=='__main__':unittest.main()
