#!/usr/bin/env python3
"""Generate a launch agent for this checkout. Install/start/stop are explicit."""
import argparse
import os
from pathlib import Path
import plistlib
import shutil
import subprocess

LABEL = 'dev.sglyon.herdr-q0'

def service_definition(root, mod, cli, app_path):
    return {'Label': LABEL, 'ProgramArguments': [str(root/'.venv/bin/python'), str(root/'bridge.py'),
            '--directory', str(mod), '--app-cli', str(cli), '--app-path', str(app_path)],
            'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 10,
            'StandardOutPath': str(mod/'.bridge.log'), 'StandardErrorPath': str(mod/'.bridge-error.log')}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['generate','install','start','stop'])
    p.add_argument('--app-path', type=Path, help='Herdr.app bundle; defaults to ~/Applications or /Applications')
    a = p.parse_args()
    root = Path(__file__).resolve().parent
    generated = root/'.local'/f'{LABEL}.plist'
    installed = Path.home()/'Library/LaunchAgents'/generated.name
    domain = f'gui/{os.getuid()}'
    if a.action in ('generate','install'):
        python = root/'.venv/bin/python'
        cli = shutil.which('herdr-app')
        if not python.exists() or not cli: raise SystemExit('Create .venv and install Herdr CLI first')
        choices = [Path.home()/'Applications/Herdr.app', Path('/Applications/Herdr.app')]
        app = a.app_path.expanduser().resolve() if a.app_path else next((v for v in choices if v.exists()), None)
        if app is None or not app.exists(): raise SystemExit('Herdr.app not found; supply --app-path /path/to/Herdr.app')
        home = Path(os.environ.get('HERDR_APP_HOME', str(Path.home()/'.config/herdr-app'))).expanduser()
        mod = home/'mods/q0-agents'
        if not mod.exists(): raise SystemExit('Install the Herdr mod first')
        value = service_definition(root, mod, cli, app)
        generated.parent.mkdir(exist_ok=True)
        generated.write_bytes(plistlib.dumps(value))
        print(generated)
        if a.action == 'install':
            installed.parent.mkdir(parents=True, exist_ok=True)
            if installed.exists() and plistlib.loads(installed.read_bytes()).get('Label') != LABEL:
                raise SystemExit('Refusing to replace an unrelated launch agent')
            shutil.copy2(generated, installed)
            print(f'Installed {installed}; not started')
    elif a.action == 'start':
        if not installed.exists(): raise SystemExit('Run configure_service.py install first')
        subprocess.run(['launchctl','bootstrap',domain,str(installed)], check=True)
    elif a.action == 'stop':
        subprocess.run(['launchctl','bootout',f'{domain}/{LABEL}'], check=True)

if __name__ == '__main__': main()
