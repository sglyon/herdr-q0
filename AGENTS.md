# Herdr Q0 agent guidance

This repository connects the **Herdr desktop app** to a **Keychron Q0 Plus**. It contains a native Herdr mod, a macOS USB bridge, and VIA-compatible QMK firmware. The `herdr` TUI is a different product; use `herdr-app` for desktop actions and `hc` for core terminal facts.

Read [README.md](README.md) for installation and controls, and use the repo-local [herdr-q0-maintenance skill](.agents/skills/herdr-q0-maintenance/SKILL.md) when extending, diagnosing, deploying, or managing this controller. Skills remain in the repository; installing them globally is not part of ordinary project maintenance.

## Sources of truth

- Source in this checkout is authoritative. `install_mod.py` deploys copies into Herdr; editing those installed copies alone will be lost on the next installation.
- Before changing a Herdr integration, read the installed `$HERDR_APP_HOME/AGENTS.md` and `herdr.d.ts`; the default home is `~/.config/herdr-app`. Read `gpui-kit.d.ts` for native UI methods. These files match the installed app and are generated: do not edit them.
- Herdr's shipped mods/layouts are also generated. Maintain our personal `q0-agents` mod/layout instead. Do not alter shared Herdr settings or unrelated layouts to fix this controller.
- Firmware is built against the QMK commit in `build.py` / `build-manifest.json`. Inspect that pinned source and prefer Context7 for current external-library documentation. Do not silently upgrade QMK while implementing an unrelated feature.
- The manifest describes bundled artifacts, not the firmware actually installed on a connected keyboard. Verify hardware separately when needed.

## Code map

| Area | Files |
| --- | --- |
| Agent discovery, slot allocation, revisions | `mod/model.js` |
| Native panel, shared persistence, state export, commands | `mod/main.js`, `mod/mod.json` |
| USB framing, freshness, focus, bridge lifecycle | `bridge.py`, `bridge_lifecycle.py` |
| Keys, final-frame LEDs, mode acknowledgement | `firmware/keymap.c`, `firmware/protocol.h`, `firmware/config.h` |
| VIA layout/key labels and build options | `firmware/via-definition.json`, `firmware/rules.mk` |
| Personal mod/layout installation | `install_mod.py` |
| Optional launch agent generation/install/start/stop | `configure_service.py` |
| Read-only VIA backup / explicitly requested restore | `via_config.py` |
| Pinned build and artifact hashes; never flashes | `build.py`, `build-manifest.json` |
| Observable behavior and fixtures | `tests/`, `TESTING.md` |

## Behavior to preserve

- Fill empty keys 1–9 automatically once agents report status. Existing agents retain their keys despite list reordering or status changes. Overflow agents wait for a vacancy or a panel replacement.
- A completed turn is still a live agent. Release a slot when the agent closes, exits, or returns to a non-agent shell. Absence is conclusive only when the relevant machine is ready; retain reservations during remote outages/loading. Explicit terminal exit is conclusive independently of connectivity.
- Reconciliation is idempotent. Status/title changes alone must not churn assignment revisions. Manual replacement must survive the next reconciliation.
- Assignments and modes share a revision. Reject obsolete selection commands. M1 leaves the current app focused; selecting an assigned number brings Herdr forward. M5 is a momentary number-entry bypass.
- Number entry remains available while a mode change is pending. Keep the bounded reconciliation for rejected concurrent mode requests and pair swallowed key-down/key-up events across mode changes or disconnects.
- Herdr supplies unread/seen completion; raw terminal reports preserve errors. Do not infer agent state from terminal text or a decorative LED effect.
- State export is reactive; only transport has a heartbeat. Use Herdr's atomic `readTextFile` / `writeTextFile` APIs and hidden runtime filenames. Visible files under the mod directory trigger source hot reloads. The native `fs/promises` shim is not full Node.js (`rename` is unavailable).
- Agent mode uses a solid rendering pass, clears decorative LEDs at the final-frame indicator, draws slot colors, and suppresses the board's Num Lock decoration. Number mode restores the prior effect/on-off state without EEPROM writes. Do not move this back to a chunk-only overlay without physical validation.
- Preserve standard VIA command handling and four dynamic layers. Bridge-only and mod-only changes do not require flashing.

## Verification by change

Run commands from the checkout root. Use the existing `.venv`, or create it using the README. Choose checks relevant to the change; documentation-only edits do not need a hardware session.

| Change | Checks |
| --- | --- |
| Slot model or mod | `node --experimental-vm-modules --test tests/*.test.js` |
| Bridge, service, VIA helper | `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` |
| Firmware | Native C harness below, real pinned ARM build, refreshed manifest |
| Native panel or installation | Native validator, `herdr-app status`, then `herdr-app shot` and inspect the image |
| Skill/guidance | Skill frontmatter validation, relative links, commands against current source |

Firmware host harness:

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -I tests tests/firmware_test.c -o /tmp/herdr-q0-test
/tmp/herdr-q0-test
```

The harness compiles the actual keymap with hardware shims. It does not replace an ARM build or physical checks. When firmware changes, keep the shipped BIN, ELF, source, and manifest consistent. Do not regenerate unrelated artifacts for mod/bridge/docs changes.

For a deployed mod, run `herdr-app check` on its installed folder, then check the running app. A successful validator alone does not prove later asynchronous updates or rendered layout work. Screenshot paths may include private terminal content: keep them local and inspect before sharing.

## Runtime and hardware boundaries

The default bridge is now panel-managed: the installed hidden `.bridge-config.json` supplies absolute local paths, the panel invokes a short launcher every five seconds, and `bridge.py --managed` exits on an expired snapshot or `.bridge-paused`. Pause with `bridge_lifecycle.py pause` before taking USB for VIA/probes/flashing; resume afterward. Do not assume a killed managed bridge will stay stopped while supervision is active.

Inspect current state before stopping anything. The bridge may be running manually or under launchd; stop/restart only the identified bridge, preserving its custom paths. Avoid simultaneous HID clients: pause the bridge during VIA configuration, backup, probe, or restore, and resume it afterward if it was running.

Reading code, building, or installing a mod does not imply authorization to flash or restore configuration. Use existing explicit user authorization when it covers the requested operation; do not ask for the same permission repeatedly. For actual flashing, verify the exact Q0 Plus and intended DFU device/serial. Do not guess between multiple devices. The confirmed bootloader shortcut is **unplug, hold the circle key, reconnect USB, release**. Detailed flash/recovery guidance is in the skill's hardware reference and README.

Controller work must not send messages to, interrupt, or terminate the user's agents, nor restart/stop Herdr Core. If a lifecycle check needs a plain status fixture, use `tests/support/status_fixture.py`, record the terminal ID created for that test, and clean up only that fixture. Do not launch an AI agent for a status-light test.

The optional login service is separate from manually starting the bridge. Do not enable it or change login behavior merely because a code edit needs a restart. Generate service paths from the actual checkout and preserve custom app locations.

## Repository hygiene

Personal backups, macro contents, live bindings/status snapshots, screenshots, virtual environments, tools, and machine-specific service files stay ignored under `backups/`, `.local/`, etc. Do not stage them. Tests must work from tracked files without personal backups or a connected keypad.

Firmware is GPL-2.0-or-later; preserve its notices and `firmware/COPYING`. The remaining project is MIT licensed. Keep operational instructions in README and agent-specific decisions here/the skill instead of copying whole manuals into multiple files. Do not sign commits or add Signed-off-by trailers.
