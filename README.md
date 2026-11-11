# Herdr × Keychron Q0 Plus

Turn a Keychron Q0 Plus into a nine-agent control surface for the **Herdr desktop app**. Keys 1–9 select agents; their RGB LEDs show live status. Empty keys fill automatically, while each existing agent keeps its number. VIA configuration and ordinary number entry remain available.

This uses Herdr desktop mods and `herdr-app` commands, backed by Herdr Core. It does not use the older `herdr` TUI.

## Requirements

- A **Keychron Q0 Plus**, connected by USB. This firmware targets `keychron/q0/plus`, not Q0, Q0 Max, or another keyboard.
- macOS, Python 3.10+, and the Herdr desktop app with `herdr-app` on your PATH.
- Herdr's mod APIs described in `~/.config/herdr-app/AGENTS.md` and `herdr.d.ts`, including `agents`, `terminals`, `machines`, `shared`, `setShared`, `readTextFile`, and `writeTextFile`.
- `dfu-util` and `dfu-suffix` for flashing/inspection, or QMK Toolbox. For Homebrew: `brew install dfu-util`.

The bridge targets the Q0 Plus raw HID interface: VID `3434`, PID `0131`, usage page `FF60`, usage `61`. It does not capture global keyboard input.

## Install

```sh
git clone https://github.com/sglyon/herdr-q0.git
cd herdr-q0
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Open Herdr, then install the personal mod and layout:

```sh
.venv/bin/python install_mod.py
```

This copies `mod/` into `~/.config/herdr-app/mods/q0-agents`, runs Herdr's native validator, and creates/switches to a personal `q0-agents` layout cloned from `main`. It preserves the shipped layouts and mods. Re-running the installer updates only this project's mod. `HERDR_APP_HOME` is supported for a non-default Herdr configuration directory.

Installation alone does not flash the keyboard or start the USB bridge. The panel can populate assignments before flashing.

## Back up your current configuration

Close VIA/Keychron Launcher and stop any running bridge before configuration operations:

```sh
mkdir -p backups
.venv/bin/python via_config.py --backup backups/original-via.json
```

This sends only VIA read commands and saves all four layers, encoder mappings, macro contents, and layout options. It is a configuration backup, not a firmware dump. The utility refuses to overwrite an existing backup. Keep it local: macro contents can be personal. `backups/` is ignored by Git.

Download the official **Q0 Plus** recovery firmware and factory VIA definition from [Keychron's firmware page](https://www.keychron.com/pages/firmware-and-json-files-of-the-keychron-qmk-keyboards) before flashing.

## Flash the firmware

The repository includes a compiled image in `firmware/keychron_q0_plus_herdr.bin`, its ELF, corresponding source, and `build-manifest.json`. Verify the binary before use:

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path
name = 'firmware/keychron_q0_plus_herdr.bin'
expected = json.loads(Path('build-manifest.json').read_text())['files'][name]
assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected
print('Firmware checksum matches')
PY
```

Enter bootloader mode on the Q0 Plus:

1. Unplug its USB cable.
2. Hold the **circle key** and reconnect USB.
3. Release the circle key. This bootloader shortcut is confirmed on the project owner's Q0 Plus.

Alternatively, the hardware reset button is accessible beneath the `0` / `.` keycaps; hold it while reconnecting USB. See [Keychron's Q0 Plus flashing instructions](https://keychron.be/pages/how-to-factory-reset-or-flash-your-qmk-via-enabled-keychron-q0-plus-keyboard).

Inspect the bootloader and confirm it is the intended Q0 Plus:

```sh
dfu-util -l
```

Then flash its internal-flash alternate interface. If multiple matching devices are present, use `-S YOUR_SERIAL` to select the Q0 Plus explicitly.

```sh
dfu-util -d 0483:df11 -a 0 -s 0x08000000:leave -D firmware/keychron_q0_plus_herdr.bin
```

Keep it connected until the download completes. The updater leaves bootloader mode afterward. Before starting the bridge, verify ordinary numbers and the volume knob work.

## Start the bridge

```sh
.venv/bin/python bridge.py --probe
.venv/bin/python bridge.py
```

The probe must report `Q0H1 firmware verified`. The bridge then reads the native mod's local state and updates the keypad. Ctrl-C stops it. Only one bridge instance can run at a time.

If Herdr is installed outside `~/Applications/Herdr.app`, pass `--app-path /Applications/Herdr.app` (or the actual bundle path). `--app-cli` accepts an absolute path if `herdr-app` is not on the bridge's PATH.

### Optional login service

Generate a launch agent for the current checkout location, install it, then start it:

```sh
.venv/bin/python configure_service.py generate
.venv/bin/python configure_service.py install
.venv/bin/python configure_service.py start
```

Generation checks `~/Applications/Herdr.app` and `/Applications/Herdr.app`. For another location, pass `--app-path /path/to/Herdr.app` to both `generate` and `install`.

Stop a manually running bridge before starting the service. `install` does not start it. To stop the service:

```sh
.venv/bin/python configure_service.py stop
```

The generated plist lives under ignored `.local/`; logs are hidden files in the installed mod directory. A failed app activation stays visible in the panel status until a subsequent action succeeds. If the checkout moves, stop the service, regenerate/reinstall it, then start it again.

## Controls and lights

| Control | Behavior |
| --- | --- |
| 1–9 | Open the assigned agent and bring Herdr forward |
| M1 | Toggle agent/number mode without switching the foreground app |
| Hold M5 | Temporarily enter ordinary numbers while held |
| Existing circle/Fn key | Existing lighting/media layer |
| Knob | Volume |

| Light | Agent state |
| --- | --- |
| Off | Unassigned |
| Dim white | Idle |
| Pulsing blue | Working |
| Green | Finished, unread |
| Pulsing amber | Needs your input |
| Red | Error |
| Dim purple | Assigned but unavailable |

Agent mode clears decorative lighting so status colors stand out. Number mode restores the prior RGB effect and on/off state, without saving temporary settings to EEPROM. Opaque stock keycaps show mostly edge glow; translucent MX-compatible keycaps make the colors easier to see.

### Automatic assignments and overflow

- Agents receive a key when they appear in Herdr's status-reporting agent data. With fewer than nine available agents, every available agent gets a key.
- Existing assignments stay fixed as agents change status or the list changes order. Empty slots fill in Herdr's terminal-list order.
- Closing/removing an agent, or its terminal returning to an ordinary shell, releases its key. A waiting agent fills the vacancy if one exists.
- Completing a turn is not closing an agent: its key stays assigned.
- Remote outages/loading retain existing slot reservations until the machine supplies authoritative state again. This avoids reshuffling during a connection failure.
- With more than nine agents, select a number in the Q0 Agents panel and choose a **Waiting** agent to replace that key. **Next waiting** is a shortcut for this. Other live assignments stay put.
- Selecting an agent that already has a key moves it; automatic filling preserves coverage of displaced agents when capacity allows.

Assignments persist in Herdr shared state. A wiped/replaced core can reuse terminal addresses; review assignments after resetting a core.

## VIA

The firmware retains four dynamic layers, macros, lighting controls, and encoder mapping. Pause the bridge while configuring VIA, then import `firmware/via-definition.json` through VIA's Design tab if automatic detection is unavailable.

- M1 is custom keycode `0x7E00` (Herdr mode toggle).
- M5 is `MO(2)`; layer 2 is initially transparent so it bypasses agent interception.
- Layer 3 is also initially transparent.
- Remapping a number key to a different action in VIA removes its agent-selection behavior. The status light remains tied to the physical number position.

The included build uses VIA protocol 13. Older factory firmware can use protocol 12. Firmware changes may reset EEPROM, and raw keycodes can differ between QMK versions. Do not blindly import old raw keycodes into a different firmware version.

For a rollback to matching factory firmware, stop the bridge, enter bootloader mode, flash the saved official recovery image, and restore the matching configuration:

```sh
.venv/bin/python via_config.py --restore backups/original-via.json --yes
```

Restore requires explicit `--yes`, refuses protocol/capacity mismatches, saves a safety backup, and reads every value back for verification. It restores configuration; it does not flash firmware.

## How it works

The native GPUI mod reads Herdr's reactive agent/terminal/machine data, reconciles nine persistent slot addresses, and exports an atomic hidden `.state.json` snapshot every 750 ms. Only transport uses a timer; agent data follows Herdr's render updates. Raw errors remain distinct from desktop attention state; unread completion uses Herdr's seen/unseen behavior.

The Python bridge verifies the custom USB handshake, sends status every 500 ms, and routes physical slot presses back to the mod's `agent.focus` command. Only slot-selection events activate Herdr; mode changes leave focus alone. It opens no network port and sends no messages to agents.

Assignments and mode changes share a revision. A press against an obsolete revision is rejected. After M1, number entry stays available until the mode acknowledgement; a rejected concurrent request reconciles to Herdr's authoritative mode after 1.5 seconds. The host rejects snapshots older than 3 seconds. The firmware independently expires a missing bridge after 2.5 seconds and returns to numbers. A swallowed press always has its release swallowed, including across disconnects.

The mod must be mounted in the active layout. Switching to a layout without it eventually returns the pad to ordinary numbers. A single panel copy should be mounted at a time.

## Tests

```sh
node --experimental-vm-modules --test tests/*.test.js
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -I tests tests/firmware_test.c -o /tmp/herdr-q0-test
/tmp/herdr-q0-test
herdr-app check ~/.config/herdr-app/mods/q0-agents
```

Tests cover automatic allocation, overflow/manual replacement, destruction, offline reservations, revisions, mode/focus behavior, bridge shutdown, VIA backup/restore emulation, and the actual firmware's status/key/LED logic with a hardware shim. Use Herdr's own `shot` command for native visual checks. Physical verification should include all assigned keys, status visibility, M1, held M5, USB reconnect, bridge-stop fallback, and real VIA configuration.

## Rebuild

The build is pinned to QMK commit `d194c077ed964195ec16d255c7a4b89a794cf03b`, target `keychron/q0/plus:herdr`. Follow [QMK's environment setup](https://docs.qmk.fm/newbs_getting_started) for the QMK CLI and ARM GNU toolchain. Keep build dependencies separate from the lightweight bridge virtual environment.

```sh
git clone --filter=blob:none https://github.com/qmk/qmk_firmware.git ../qmk_firmware
git -C ../qmk_firmware checkout d194c077ed964195ec16d255c7a4b89a794cf03b
git -C ../qmk_firmware submodule update --init lib/chibios lib/chibios-contrib lib/printf lib/lufa
python3 build.py --qmk-tree ../qmk_firmware --toolchain /path/to/arm-toolchain --dfu-tools /path/to/dfu-tools
```

`--toolchain` names the directory containing `bin/arm-none-eabi-gcc`; `--dfu-tools` names the directory containing `dfu-suffix`. The `qmk` CLI must also be on PATH. `build.py` copies the keymap, builds offline against the pinned checkout/submodules, and refreshes the binary and manifest. It has no flashing operation.

## Remove

Stop the bridge/service and switch back to the standard layout:

```sh
herdr-app do layout.switch --name main
```

Remove only the personal `q0-agents` mod/layout when no longer needed. If a login service was installed, stop it and remove `~/Library/LaunchAgents/dev.sglyon.herdr-q0.plist`. Agent terminals remain running. To remove the custom firmware too, flash the official Q0 Plus recovery image.

## Agent maintenance

[AGENTS.md](AGENTS.md) maps the code, behavioral invariants, and validation/deployment boundaries. The repository-local [herdr-q0-maintenance skill](.agents/skills/herdr-q0-maintenance/SKILL.md) adds focused runtime and hardware procedures for future agents. Keep this guidance with the checkout; no global skill installation is required to read and use it.

## License

The bridge, mod, helpers, and tests are MIT licensed. The QMK-derived firmware is GPL-2.0-or-later; see `firmware/COPYING`. Its corresponding modified source and pinned upstream reference are included.
