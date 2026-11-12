import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from bridge import packet
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("lifecycle", ROOT / "bridge_lifecycle.py")
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)


def snapshot(directory):
    (directory / ".state.json").write_text(json.dumps({
        "version": 1, "revision": 1, "timestamp": time.time()*1000, "enabled": True,
        "slots": [{"slot": i, "address": None, "state": "off"} for i in range(1, 10)]}))


class LifecycleTests(unittest.TestCase):
    def test_paused_or_stale_panel_cannot_launch(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            (directory / ".bridge-paused").touch()
            with patch.object(lifecycle.subprocess, "Popen") as launch:
                self.assertEqual(lifecycle.ensure(directory), "paused")
                (directory / ".bridge-paused").unlink()
                with self.assertRaises(OSError): lifecycle.ensure(directory)
                launch.assert_not_called()

    def test_real_managed_child_stops_on_pause_and_heartbeat_loss_and_can_restart(self):
        # Actual bridge loop and subprocess/lock lifecycle, with only the USB device replaced.
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            bootstrap = directory / "fixture.py"
            bootstrap.write_text("""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import bridge
class HID:
    def write(self, packet):
        with (Path(sys.argv[2])/'writes').open('ab') as f: f.write(packet)
    def read(self, n, timeout):
        if not getattr(self,'verified',False):
            self.verified=True
            return bridge.packet(0x81,0,b'Q0H1')
        return b''
    def close(self): (Path(sys.argv[2])/'closed').touch()
bridge.open_keyboard=lambda: HID()
bridge.run(Path(sys.argv[2]),'unused','unused',managed=True)
""")
            config = {"arguments": [sys.executable, str(bootstrap), str(ROOT), str(directory)]}
            (directory / ".bridge-config.json").write_text(json.dumps(config))
            children = []
            original = subprocess.Popen
            def launch(*args, **kwargs):
                child = original(*args, **kwargs)
                children.append(child)
                return child
            def wait_for(predicate):
                deadline = time.monotonic()+5
                while not predicate():
                    if time.monotonic() > deadline: self.fail("Timed out waiting for managed child")
                    time.sleep(.02)
            try:
                with patch.object(lifecycle.subprocess, "Popen", side_effect=launch):
                    snapshot(directory)
                    self.assertEqual(lifecycle.ensure(directory), "started")
                    wait_for(lambda: (directory / "writes").exists())
                    self.assertEqual(lifecycle.ensure(directory), "running")
                    self.assertEqual(len(children), 1)
                    (directory / ".bridge-paused").touch()
                    self.assertEqual(children[0].wait(timeout=5), 0)
                    self.assertTrue((directory / "closed").exists())
                    self.assertEqual((directory / "writes").read_bytes()[-33:], b'\0'+packet(4))
                    self.assertEqual(lifecycle.ensure(directory), "paused")
                    (directory / ".bridge-paused").unlink()
                    (directory / "closed").unlink()
                    snapshot(directory)
                    self.assertEqual(lifecycle.ensure(directory), "started")
                    self.assertNotEqual(children[0].pid, children[1].pid)
                    wait_for(lambda: children[1].poll() is not None)
                    self.assertEqual(children[1].returncode, 0)
                    self.assertTrue((directory / "closed").exists())
                    self.assertEqual(len(children), 2)
            finally:
                for child in children:
                    if child.poll() is None: child.terminate()
                    child.wait(timeout=5)
