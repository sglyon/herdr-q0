#!/usr/bin/env python3
"""Install only our personal mod; validate before cloning a layout. Never flashes."""
import json
import os
from pathlib import Path
import shutil
import subprocess

root=Path(__file__).resolve().parent
home=Path(os.environ.get('HERDR_APP_HOME',str(Path.home()/'.config/herdr-app'))).expanduser()
(root/'backups').mkdir(exist_ok=True)
dest=home/'mods/q0-agents'
if dest.exists() and not (dest/'q0-owner.json').exists():
    raise SystemExit('Refusing to replace an existing unrelated q0-agents mod')
dest.mkdir(parents=True,exist_ok=True)
for name in ['main.js','model.js','mod.json']:
    shutil.copy2(root/'mod'/name,dest/name)
runtime=dest/'.state.json'
runtime.touch(mode=0o600,exist_ok=True)
runtime.chmod(0o600)
(dest/'q0-owner.json').write_text(json.dumps({'source':str(root),'version':1}))
subprocess.run(['herdr-app','check',str(dest)],check=True)
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
print('Installed q0-agents mod and personal layout. Shipped files unchanged. No firmware flashed.')
