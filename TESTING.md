# Validation

## Automated checks

Run the commands in README.md from a fresh checkout. The current suite includes 13 JavaScript and 15 Python tests, plus the sanitizer firmware harness. No personal backup, running agent, or connected keyboard is required for the JavaScript/Python/firmware host tests. VIA fixtures are synthetic.

- JavaScript: stable auto-fill, new agents, closure/shell return, completed turns, overflow/manual replacements, offline/loading reservations, stale revisions, the actual native mod lifecycle with host mocks, and sidebar badge rendering across assignment swaps, closures, duplicate titles, full machine-qualified addresses, and number mode.
- Python: protocol packets, freshness, physical mode/focus behavior, bridge-loop dispatch and shutdown, a real managed child with synthetic HID (singleton lock, pause, heartbeat expiry, and restart), personal-layout sidebar replacement/idempotence, incompatible upstream rejection, and read-only backup / validated restore against an emulated VIA device.
- Firmware host harness: actual keymap code compiled with AddressSanitizer and UndefinedBehaviorSanitizer; all nine slots, malformed packets, VIA passthrough, paired releases, timeout, mode acknowledgement/reconciliation, LED output, and RGB restoration.
- ARM build: pinned upstream QMK target keychron/q0/plus:herdr. Binary and source hashes are in build-manifest.json.

## Native validation

After installation, run herdr-app check on the installed mod, inspect herdr-app status for errors, and inspect a herdr-app shot capture. Verify that the exported hidden .state.json stays fresh, all available agents up to capacity have keys, existing assignments do not move, and removing a test agent releases its key. Test remote outages separately from confirmed closure.

## Hardware validation

On the project owner's Q0 Plus, normal digit entry, volume knob, physical agent selection, assigned-status lighting, M1 transitions, and M5 temporary number entry were confirmed. M1 focus activation was corrected in the bridge and confirmed afterward. The final lighting firmware uses VIA version 0x51304802.

Remaining first-use checks on each installation: verify all desired slot mappings, working/done/blocked/error color changes, USB reconnect, stopping the bridge, and real VIA remapping with the bridge paused. Software emulation does not prove those physical results.

The circle-key bootloader method (unplug, hold circle, reconnect) was confirmed on the project owner's pad.

Live auto-fill validation also created a short-lived status-reporting fixture, observed its automatic assignment, destroyed only that fixture, and confirmed its slot was released while existing assignments remained unchanged. No user agent was interrupted. App-managed bridge supervision is the default; launcher errors and recovery are covered in the mod test. The service plist preserves custom app paths, and bridge tests verify activation failures remain visible.

Live app-managed validation terminated only the identified controller bridge and observed a new PID reconnecting to the Q0 automatically. Maintenance pause kept it stopped through a full supervision interval; resume reconnected with assignments and mode preserved. Herdr reported no errors. App-quit heartbeat expiry is covered with a real companion process using synthetic HID; the user's desktop app and agents were not stopped.

Sidebar badges passed native validation and rendered beside all eight current assigned agents in the personal layout. The shipped Agents source hash, Q0 assignments, and mode were unchanged; the bridge remained connected. The user confirmed the badges were visible. The sidebar is refreshed from installed Herdr source by rerunning the installer after an app update.
