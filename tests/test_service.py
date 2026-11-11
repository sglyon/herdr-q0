import importlib.util
from pathlib import Path
import plistlib
import unittest

spec=importlib.util.spec_from_file_location('service',Path(__file__).parents[1]/'configure_service.py')
service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)

class ServiceTests(unittest.TestCase):
    def test_custom_app_location_survives_plist_round_trip(self):
        root=Path('/checkout with spaces/herdr-q0');mod=Path('/config/mods/q0-agents')
        app=Path('/Applications/Custom Apps/Herdr.app')
        data=plistlib.loads(plistlib.dumps(service.service_definition(root,mod,'/tools/herdr-app',app)))
        args=data['ProgramArguments']
        self.assertEqual(args[args.index('--app-path')+1],str(app))
        self.assertEqual(args[0],str(root/'.venv/bin/python'))
        self.assertEqual(args[args.index('--directory')+1],str(mod))
        self.assertEqual(data['StandardErrorPath'],str(mod/'.bridge-error.log'))

if __name__=='__main__':unittest.main()
