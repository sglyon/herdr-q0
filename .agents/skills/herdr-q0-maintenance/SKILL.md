---
name: herdr-q0-maintenance
description: Extend, troubleshoot, or manage this Herdr desktop mod, macOS USB bridge, and VIA-compatible Keychron Q0 Plus firmware. Use for agent-slot allocation, status LEDs, mode/focus behavior, deployment, service setup, builds, and requested hardware maintenance in herdr-q0.
---

# Herdr Q0 maintenance

Work from the checkout root (`git rev-parse --show-toplevel`). Read [AGENTS.md](../../../AGENTS.md) first. Keep changes in repository source and deploy deliberately; the running mod is a copy, and an edited bridge process keeps its old code until restarted.

## Choose the layer

| Request | Start here | Deployment consequence |
| --- | --- | --- |
| New/closed agents, stable keys, overflow | `mod/model.js`, model/lifecycle JS tests | Install mod; no flash |
| Panel controls, live status, unread completion | `mod/main.js`, installed Herdr API definitions | Install, native-check, inspect screenshot |
| M1 steals focus, agent activation, stale USB state | `bridge.py`, `bridge_lifecycle.py`, bridge-loop Python tests | Pause/resume management; no flash |
| Login behavior, custom app/checkout location | `configure_service.py`, service tests | Regenerate/install service only within requested scope |
| Key mapping, RGB output, pending-mode timing | `firmware/keymap.c`, firmware host harness | ARM build; flash only when authorized |
| VIA settings or recovery | `via_config.py`, matching firmware/definition | Separate configuration mutation from flashing |

For runtime diagnostics or deployment, read [runtime.md](references/runtime.md). For firmware/protocol changes or requested flash/recovery, read [hardware.md](references/hardware.md). Read only the branch needed; user installation instructions remain in [README.md](../../../README.md).

## Decisions that prevent regressions

- Preserve surviving assignments; fill gaps rather than recomputing a ranked top nine. Do not turn an idle/done state or a network outage into an agent deletion. Use machine readiness to judge missing agents.
- Share a revision across assignments and mode changes. Check authoritative shared mode when selecting, not only a cached render flag. A pending toggle must resolve after a rejected concurrent request.
- Route physical slot selection to `agent.focus` and activate Herdr; route mode changes without app activation. Retain custom `--app-path` / `--app-cli` arguments through restarts and service generation.
- Keep ordinary number entry and paired key releases safe across disconnects. Bridge stale-state handling and firmware timeout are independent fail-safes.
- Render slot LEDs after the complete RGB frame and clear background decoration in agent mode. Restore prior decorative lighting in number mode without persisting temporary state.
- Use native Herdr reactive reads and atomic text-file APIs. Only heartbeat I/O is periodic; hidden runtime files avoid a hot-reload loop. Do not assume Node's filesystem/DOM APIs exist.

## Validate and report

Use the AGENTS change/check matrix and [TESTING.md](../../../TESTING.md). Add regressions for actual behavior changes: allocation under capacity/overflow, closures versus disconnection, stale revisions, mode focus, final LED output, or service-path propagation as relevant. Use synthetic fixtures, not personal backups.

For a mod update, preserve the existing assignments while running `install_mod.py`; inspect the native validator/status and a screenshot. For a bridge update, restart the correct manual process or service and confirm fresh bridge status. A code change alone is not a deployed change.

For firmware, report host tests, ARM build/hash checks, and hardware observations separately. Compilation/emulation cannot establish actual key/LED/USB/VIA behavior. Do not label unperformed physical checks as passed or introduce a flash into a software-only request.

Conclude with the changed layer, how it was deployed, verification evidence, and any remaining user hardware action. Keep personal runtime files out of commits.
