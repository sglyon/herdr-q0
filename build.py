#!/usr/bin/env python3
"""Rebuild only. This script has no flashing operation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

PIN='d194c077ed964195ec16d255c7a4b89a794cf03b'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--qmk-tree',type=Path,required=True)
p.add_argument('--toolchain',type=Path,required=True,help='Directory containing bin/arm-none-eabi-gcc')
p.add_argument('--dfu-tools',type=Path,required=True,help='Directory containing dfu-suffix')
a=p.parse_args();root=Path(__file__).resolve().parent;qmk=a.qmk_tree.resolve()
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=qmk,text=True).strip()
if revision!=PIN:raise SystemExit(f'Expected QMK {PIN}; found {revision}')
dest=qmk/'keyboards/keychron/q0/plus/keymaps/herdr';dest.mkdir(exist_ok=True)
for name in ['keymap.c','protocol.h','config.h','rules.mk']:shutil.copy2(root/'firmware'/name,dest/name)
env=dict(os.environ)
env['PATH']=os.pathsep.join([str(a.toolchain.resolve()/'bin'),str(a.dfu_tools.resolve()),env['PATH']])
subprocess.run(['make','keychron/q0/plus:herdr','-j4','SKIP_GIT=yes'],cwd=qmk,env=env,check=True)
for source,target in [(qmk/'keychron_q0_plus_herdr.bin',root/'firmware/keychron_q0_plus_herdr.bin'),(qmk/'.build/keychron_q0_plus_herdr.elf',root/'firmware/keychron_q0_plus_herdr.elf')]:
    shutil.copy2(source,target)
manifest={'qmk_commit':PIN,'target':'keychron/q0/plus:herdr','compiler':subprocess.check_output(['arm-none-eabi-gcc','--version'],env=env,text=True).splitlines()[0],
          'files':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((root/'firmware').iterdir()) if f.is_file()}}
(root/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Build and hashes saved. No device was flashed.')
