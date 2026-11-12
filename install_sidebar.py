#!/usr/bin/env python3
"""Decorate a personal copy of Herdr's Agents mod; never edit the shipped mod."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

NAME = "q0-agents-sidebar"


def patch_sidebar(source):
    """Require known extension points; fail before deploying on incompatible Herdr."""
    def replace(old, new):
        nonlocal source
        if source.count(old) != 1:
            raise ValueError(f"Herdr Agents mod changed; review Q0 sidebar patch at {old[:70]!r}")
        source = source.replace(old, new, 1)

    replace('import { v_flex, h_flex } from "gpui-base";',
            'import { v_flex, h_flex } from "gpui-base";\nimport { assignedKeys, keyBadge } from "./badges.js";')
    replace('    const collapsed = narrow();',
            '    this.q0Keys = assignedKeys(shared("q0-agents.assignments.v1"));\n'
            '    this.q0Enabled = shared("q0-agents.enabled") !== false;\n'
            '    const collapsed = narrow();')
    replace('      const pic = icon(a.program, 16, t.foreground);',
            '      const badge = keyBadge(t, a.address, this.q0Keys, this.q0Enabled);\n'
            '      const pic = icon(a.program, 16, t.foreground);')
    replace('.child(div().flex_1().min_w(0).whitespace_nowrap().text_right().text_color(t.muted).child(String(i + 1)))',
            '.child(div().flex_1().min_w(0).flex().justify_end().child(badge || pic || ""))')
    replace('        .when(Boolean(pic), el => el.child(div().id(`agent-fold-${a.address}`)',
            '        .when(Boolean(badge), el => el.child(badge))\n'
            '        .when(Boolean(pic), el => el.child(div().id(`agent-fold-${a.address}`)')
    replace('    const pic = icon(k.program, 14, t.foreground);',
            '    const badge = keyBadge(t, k.address, this.q0Keys, this.q0Enabled);\n'
            '    const pic = icon(k.program, 14, t.foreground);')
    replace('      .when(Boolean(pic), el => el.child(div().mr(8).child(pic)))',
            '      .when(Boolean(badge), el => el.child(div().mr(6).child(badge)))\n'
            '      .when(Boolean(pic), el => el.child(div().mr(8).child(pic)))')
    replace('openOverlay({ mod: "agents",', f'openOverlay({{ mod: "{NAME}",')
    return '// Personal Q0 badges added to the installed Herdr Agents mod.\n' + source


def sidebar_layout(layout):
    result = copy.deepcopy(layout)

    def visit(node):
        content = node.get("content", {})
        if content.get("mod") == "agents":
            content["mod"] = NAME
        for child in node.get("children", []):
            visit(child)

    visit(result)
    return result


def install_sidebar(root: Path, home: Path, cli="herdr-app"):
    source = (home / "mods/agents/main.js").read_text()
    patched = patch_sidebar(source)  # Validate every anchor before any installation writes.
    dest = home / "mods" / NAME
    if dest.exists() and not (dest / "q0-owner.json").exists():
        raise SystemExit(f"Refusing to replace an unrelated {NAME} mod")
    if not dest.exists():
        subprocess.run([cli, "do", "mod.clone", json.dumps({"name": "agents", "as": NAME})], check=True)
    shutil.copy2(root / "sidebar/badges.js", dest / "badges.js")
    shutil.copy2(root / "mod/model.js", dest / "model.js")
    (dest / "main.js").write_text(patched)
    (dest / "q0-owner.json").write_text(json.dumps({
        "source": str(root), "upstream_sha256": hashlib.sha256(source.encode()).hexdigest(), "version": 1}))
    subprocess.run([cli, "check", str(dest)], check=True)
