#!/usr/bin/env python3
"""Install only our personal mod; validate before cloning a layout. Never flashes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from install_sidebar import install_sidebar, sidebar_layout

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--app-path', type=Path, help='Herdr.app bundle for foreground activation')
args=parser.parse_args()
root=Path(__file__).resolve().parent
python=root/'.venv/bin/python'
cli=shutil.which('herdr-app')
choices=[Path.home()/'Applications/Herdr.app',Path('/Applications/Herdr.app')]
app=args.app_path.expanduser().resolve() if args.app_path else next((p for p in choices if p.exists()),None)
if not python.exists() or not cli or app is None or not app.exists():
    raise SystemExit('Create .venv, install herdr-app, and supply --app-path if Herdr.app is not in an Applications folder')
home=Path(os.environ.get('HERDR_APP_HOME',str(Path.home()/'.config/herdr-app'))).expanduser()
(root/'backups').mkdir(exist_ok=True)
dest=home/'mods/q0-agents'
if dest.exists() and not (dest/'q0-owner.json').exists():
    raise SystemExit('Refusing to replace an existing unrelated q0-agents mod')
dest.mkdir(parents=True,exist_ok=True)
for name in ['main.js','model.js','mod.json']:
    shutil.copy2(root/'mod'/name,dest/name)
config={'python':str(python),'launcher':str(root/'bridge_lifecycle.py'),
        'arguments':[str(python),str(root/'bridge.py'),'--directory',str(dest),
                     '--app-cli',str(cli),'--app-path',str(app)]}
(dest/'.bridge-config.json').write_text(json.dumps(config))
(dest/'.bridge-config.json').chmod(0o600)
runtime=dest/'.state.json'
runtime.touch(mode=0o600,exist_ok=True)
runtime.chmod(0o600)
(dest/'q0-owner.json').write_text(json.dumps({'source':str(root),'version':1}))
subprocess.run(['herdr-app','check',str(dest)],check=True)
install_sidebar(root, home)
status=json.loads(subprocess.check_output(['herdr-app','status']))
name='q0-agents'
layout=home/'layouts'/f'{name}.json'
if layout.exists():
    existing=json.loads(layout.read_text())
    if not any(c.get('id')=='q0-control-panel' for c in existing.get('children',[])):
        raise SystemExit('Refusing to replace an unrelated q0-agents layout')
    subprocess.run(['herdr-app','do','layout.switch','--name',name],check=True)
else:
    (root/'backups'/'herdr-before-install.json').write_text(json.dumps(status,indent=2)+'\n')
    subprocess.run(['herdr-app','do','layout.clone',json.dumps({'name':'main','as':name})],check=True)
    data=json.loads(layout.read_text())
    data['children'].append({'id':'q0-control-panel','type':'block','size':{'px':380},'min':340,'max':560,
                             'content':{'mod':'q0-agents'}})
    layout.write_text(json.dumps(data,indent=2)+'\n')
    subprocess.run(['herdr-app','do','layout.set',json.dumps({'layout':data})],check=True)
    shutil.copy2(layout,root/'q0-agents-layout.json')
data=json.loads(layout.read_text())
decorated=sidebar_layout(data)
if decorated != data:
    subprocess.run(['herdr-app','do','layout.set',json.dumps({'layout':decorated})],check=True)
print('Installed Q0 controller and Agents sidebar badges. Shipped files unchanged. No firmware flashed.')
