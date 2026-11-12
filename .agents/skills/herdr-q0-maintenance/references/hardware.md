# Firmware, wire protocol, and hardware maintenance

Software-only changes do not require flashing. Hardware operations require authorization covering the operation; preserve authorization already given in the conversation. Build/test preparation should be complete before asking the user to enter bootloader mode.

## Protocol contract

Verify these details against `bridge.py`, `firmware/protocol.h`, and `firmware/keymap.c` when changing them.

- Q0 Plus USB runtime: VID `0x3434`, PID `0x0131`, raw HID usage page `0xFF60`, usage `0x61`.
- Custom report: 32 bytes; header `F0 48 51 01`; opcode at byte 4; uint32 little-endian revision at bytes 5–8. The Python HID write prepends the zero report-ID byte separately.
- Handshake: opcode `1`, response `0x81` with `Q0H1` at bytes 9–12. Handshake does not enable agent mode.
- State (`2`): enabled byte at 9 and nine state codes at 10–18. Codes: off 0, idle 1, working 2, unread/done 3, blocked 4, error 5, unavailable 6.
- Selection (`3`, device→host): slot 1–9 at byte 9; revision must match. Mode request (`5`): requested enabled value at byte 9. Disable (`4`) removes the live connection state.
- VIA owns raw HID reception. `via_command_kb` handles only the custom header; ordinary VIA commands must continue through unchanged. Do not replace VIA's raw HID receiver with an unrelated handler.

Changing framing/state codes requires matching bridge and firmware changes and cross-layer tests. New Herdr-only behavior usually needs neither a protocol change nor firmware rebuild.

## Build and inspect

`build.py` enforces the QMK commit recorded in source/manifest. Initialize the pinned ChibiOS, ChibiOS-Contrib, printf, and LUFA submodules, provide the QMK CLI, Arm toolchain, and `dfu-suffix`, and follow README's rebuild command. `SKIP_GIT=yes` avoids automatic network submodule/version probes during compilation; it does not remove the requirement to prepare pinned dependencies.

Run the sanitizer host harness, then the ARM build. Refresh tracked BIN, ELF, and `build-manifest.json` together. Verify the artifact SHA-256 and DFU suffix before a flash. Do not use a historical `.local` status record as evidence for a newly built image.

`VIA_FIRMWARE_VERSION` in `firmware/config.h` identifies the source revision separately from the `Q0H1` protocol handshake. A successful handshake alone cannot distinguish compatible firmware builds. Coordinate identifier changes with the validation instructions when needed.

### Read the installed firmware build version

Pause panel management with `.venv/bin/python bridge_lifecycle.py pause`, wait for the bridge lock to be released, and stop any manual/service bridge and other HID clients first. The custom image implements VIA `get_keyboard_value` (`0x02`) / `firmware_version` (`0x04`); the response stores the uint32 value at bytes 2–5, big-endian:

```sh
.venv/bin/python - <<'PY_VERSION'
from bridge import open_keyboard
from via_config import request
h = open_keyboard()
try:
    reply = request(h, [0x02, 0x04])
    print(f"VIA firmware build: 0x{int.from_bytes(reply[2:6], 'big'):08X}")
finally:
    h.close()
PY_VERSION
```

Compare this value with `VIA_FIRMWARE_VERSION` in the source being evaluated; do not hardcode the currently bundled version into a diagnostic helper. This reads the build identifier, not the VIA protocol version. A factory image may not support this value; an absent/unexpected response is not proof that the bundled custom image is installed. Resume the bridge after the inspection if it was running.

## Key and lighting constraints

- Target is `keychron/q0/plus`; the Q0, Q0 Max, and other devices have different targets.
- Numeric LED indices (1→9) are `{19,20,21,15,16,17,10,11,12}` in the pinned Q0 Plus map. Verify any future board definition rather than reusing them for another model.
- Status rendering uses the complete-frame `rgb_matrix_indicators_user` pass: blank decoration, then draw slot colors. The advanced hook suppresses the board's Num Lock indicator while active. Test off/unassigned states against a non-black decorative frame.
- Agent mode temporarily selects a solid effect; leaving it restores the saved effect and on/off state without EEPROM writes.
- Guard synthetic/encoder positions before indexing the physical swallowed-key array. A swallowed key press must have its release swallowed even after disconnect or mode/layer changes.
- M1 requests a revisioned mode. Input passes through numerically until acknowledgement; a 1.5-second bounded reconciliation prevents a rejected concurrent request wedging M1. M5 uses the transparent number-bypass layer.

## Authorized flashing and rollback

1. Pause panel management with `bridge_lifecycle.py pause` and confirm its bridge has exited. Stop any manual/service bridge separately and close other USB configurators. Save current VIA configuration with the repository helper when appropriate. Keep personal backups local.
2. Verify the image against its manifest, and have the exact Q0 Plus recovery image/configuration available.
3. Tell the user when ready: **unplug, hold the circle key, reconnect USB, release**. This shortcut is confirmed on the project owner's pad. Hardware-reset access beneath `0` / `.` is an alternative in README.
4. Inspect `dfu-util -l`. Confirm the expected runtime device disappeared and the intended STM32 bootloader appeared. Multiple alternate interfaces can belong to one physical serial; multiple physical devices require explicit selection/identification. Never guess a serial.
5. Use the README's command against internal flash, alternate `0`, address `0x08000000`, and the verified Q0 Plus image. Include `-S` for the identified serial when appropriate. Do not write option bytes, OTP, or other alternates.
6. Wait for completion/exit status before allowing unplugging. Verify the runtime handshake and actual firmware version after restart. Read back VIA layers/M1/M5 before physical checks.
7. Resume the previous bridge setup. Confirm normal numbers with bridge off, agent selection/status lights, M1 without focus stealing, held M5, timeout/reconnect, and real VIA configuration with bridge paused. Ask for physical observations where the computer cannot establish the result.

VIA protocol versions and raw keycode ranges can differ from factory firmware. A configuration backup is not a flash dump. `via_config.py --restore ... --yes` checks protocol/capacity, saves a safety backup, writes settings, and verifies them; it never flashes. Use it on matching firmware, not as a cross-version migration shortcut.

Report software verification and user-observed hardware results separately. If an update fails, inspect actual device state and use a verified recovery path; do not repeat arbitrary flashes or reset the user's Herdr Core.
