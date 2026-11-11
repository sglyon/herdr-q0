# Runtime diagnostics and deployment

Commands run from the checkout root. The Herdr configuration home is `${HERDR_APP_HOME:-$HOME/.config/herdr-app}`. Its generated AGENTS/API files are authoritative for the installed version.

## Read before restarting

1. Inspect `herdr-app status`: active layout, focus, and errors. The `q0-agents` block must be mounted; a layout without it stops the mod heartbeat.
2. Read `mods/q0-agents/.state.json` under that configuration home. Compare `timestamp` to current milliseconds, inspect `enabled`, `revision`, and slot addresses/states. This file is diagnostic state, not the persistence API.
3. Read `.bridge-status.json` beside it and verify its timestamp too. A stale "ready" message does not prove a process is alive.
4. Identify the actual bridge: inspect its command line, the PID holding `.bridge.lock` (for example `lsof`), and `launchctl print gui/$(id -u)/dev.sglyon.herdr-q0` if a service might be installed. Do not kill processes by a broad Python/Herdr name match.

Bindings live in Herdr shared state (`q0-agents.assignments.v1`), not in the bridge or firmware. Mode is `q0-agents.enabled`. Do not patch Herdr's `shared.json` directly; it is written by the app. Shared state survives hot reloads and reinstalls.

## Diagnose at the boundary

| Symptom | Check |
| --- | --- |
| Slots do not fill/release | Reactive `candidates`/`reconcile`, terminal status versus ordinary shell, machine readiness, nine-key capacity |
| Assigned remote agent disappears | Distinguish a confirmed exit from remote loading/unavailable; retain outage reservations |
| Keys type digits instead of selecting | Fresh mod snapshot, enabled mode, bridge status/handshake, M5/other layer held, VIA key remap |
| M1 switches apps | Bridge must activate Herdr for selection packets only |
| Agent selected but Herdr stays behind | Actual `--app-path`, `open` error in status, service's saved arguments |
| Lighting differs from state | Pause other USB configurators; compare actual firmware version with source, then inspect final-frame rendering |
| Mod reloads repeatedly | Visible runtime files under the mod trigger source watching; use hidden files and atomic Herdr writes |
| Patch has no effect | Installed mod copy or running bridge process still uses old code |

Normal cadence is 750 ms for the mod export and 500 ms for bridge state. The host rejects snapshots older than 3 seconds; firmware expires after 2.5 seconds without a valid update. Diagnose persistent failure after these bounds rather than treating a normal transition as a defect.

## Mod update

Run relevant JS tests, then:

```sh
.venv/bin/python install_mod.py
herdr-app status
```

The installer runs the native validator. Check the installed mod's owner marker/source path if multiple checkouts exist. Capture `herdr-app shot` to an ignored `.local/` file and actually inspect it after UI changes. Do not commit terminal screenshots or copied runtime bindings.

Source uses `agents()` for Herdr's unread/seen state and raw terminal status for errors/sub-agents. `agents()` does not include every background terminal; do not accidentally drop raw status-reporting children when changing discovery. A new agent becomes eligible once it reports status.

## Bridge or service update

Run the Python suite before restarting. Preserve custom arguments and whether the process was manual or a service. Ctrl-C/SIGINT lets a manual bridge send disable/close its handle; only signal the positively identified process. A single-instance lock prevents duplicate bridges.

`configure_service.py generate` and `install` prepare files but do not start a service; `start` and `stop` change the running service. Generation supports `--app-path` and `HERDR_APP_HOME`. Reinstall an updated plist after changing paths, and use service management rather than fighting launchd's KeepAlive restart.

Do not run VIA/backup/probe helpers alongside the bridge. Restore the prior running state after a requested maintenance operation. Ordinary bridge restarts must not change app focus or restart the user's agents.

## Native lifecycle fixture

When a live lifecycle check is warranted, `tests/support/status_fixture.py` emits a plain OSC 7501 idle report and waits. It is not an AI agent. Use `hc --skill` / CLI help for current launch flags; give it a distinct test name, no parent, and no notifications. Record the returned terminal address. Verify it acquires a free slot, close/remove only that fixture, and verify the slot is released without moving existing assignments. If all nine slots are occupied, use isolated tests instead of evicting a user's agent just to make a test slot.
