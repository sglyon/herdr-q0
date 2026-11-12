#!/usr/bin/env python3
"""Local-only Q0 USB bridge. No network, agent messages, or firmware writes."""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import struct
import subprocess
import time

PREFIX = bytes([0xF0, 0x48, 0x51, 1])
STATES = {"off": 0, "idle": 1, "working": 2, "done": 3, "blocked": 4, "error": 5, "unavailable": 6}
VID, PID, PAGE, USAGE = 0x3434, 0x0131, 0xFF60, 0x61

def packet(op: int, revision: int = 0, payload: bytes = b"") -> bytes:
    return (PREFIX + bytes([op]) + struct.pack("<I", revision) + payload).ljust(32, b"\0")

def read_snapshot(path: Path, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    s = json.loads(path.read_text())
    if s.get("version") != 1 or not isinstance(s.get("revision"), int) or not 0 <= s["revision"] <= 0xFFFFFFFF:
        raise ValueError("Invalid state version/revision")
    if not 0 <= now * 1000 - s["timestamp"] < 3000:
        raise ValueError("Herdr state is stale")
    slots = s["slots"]
    if len(slots) != 9 or [v["slot"] for v in slots] != list(range(1, 10)):
        raise ValueError("Invalid slot list")
    for v in slots:
        if v["state"] not in STATES or (v["address"] is not None and not isinstance(v["address"], str)):
            raise ValueError("Invalid slot")
    if not isinstance(s.get("enabled"), bool): raise ValueError("Invalid mode")
    return s

def state_packet(s: dict) -> bytes:
    return packet(2, s["revision"], bytes([s["enabled"]]) + bytes(STATES[v["state"]] for v in s["slots"]))

def selection_command(data: bytes, s: dict) -> str | None:
    if len(data) != 32 or data[:4] != PREFIX:
        return None
    revision = struct.unpack_from("<I", data, 5)[0]
    if revision != s["revision"]: return None
    if data[4] == 5 and data[9] in (0, 1): return f"q0-agents.mode-{revision}-{data[9]}"
    if data[4] != 3 or not s["enabled"]: return None
    slot = data[9]
    if not 1 <= slot <= 9: return None
    target = s["slots"][slot - 1]
    if not target["address"] or target["state"] in ("off", "unavailable"): return None
    return f"q0-agents.select-{revision}-{slot}"

def open_keyboard():
    import hid
    matches = [d for d in hid.enumerate(VID, PID) if d["usage_page"] == PAGE and d["usage"] == USAGE]
    if len(matches) != 1: raise OSError(f"Expected one Q0 Plus, found {len(matches)}")
    h = hid.device()
    h.open_path(matches[0]["path"])
    return h

def handshake(h):
    h.write(b"\0" + packet(1))
    until = time.monotonic() + 1
    while time.monotonic() < until:
        r = bytes(h.read(32, 100))
        if r[:5] == PREFIX + b"\x81" and len(r) == 32 and r[9:13] == b"Q0H1": return
    raise OSError("Q0 Plus connected; custom firmware not installed")

def atomic_json(path: Path, value: dict):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value))
    os.chmod(temp, 0o600)
    temp.replace(path)

def run(directory: Path, app_cli: str, app_path: str, managed: bool = False):
    lock = (directory / ".bridge.lock").open("a")
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise SystemExit("Another Q0 bridge is already running")
    h, next_attempt, next_send, next_status = None, 0.0, 0.0, 0.0
    message, old_message, action_error = "Connecting to Q0 Plus", "", ""
    try:
        while True:
            now = time.monotonic()
            if h is None and now >= next_attempt:
                candidate = None
                try:
                    candidate = open_keyboard(); handshake(candidate); h = candidate
                except (OSError, ImportError) as e:
                    if candidate: candidate.close()
                    message = str(e); next_attempt = now + 3
            try:
                s = read_snapshot(directory / ".state.json")
            except (OSError, ValueError, TypeError, KeyError):
                s = None
            if managed and (s is None or (directory / ".bridge-paused").exists()):
                break
            if h:
                try:
                    if now >= next_send:
                        h.write(b"\0" + (state_packet(s) if s else packet(4)))
                        next_send = now + 0.5
                    message = "Keyboard ready · " + ("Herdr unavailable" if s is None else "agent mode" if s["enabled"] else "number mode")
                    if action_error: message += " · " + action_error
                    data = bytes(h.read(32, 50))
                    command = selection_command(data, s) if data and s else None
                    if command:
                        # Slot resolves in Herdr too, so a concurrent reassignment is rejected there.
                        result = subprocess.run([app_cli, "do", command], capture_output=True, timeout=3)
                        action_error = ""
                        if result.returncode: action_error = "Herdr command failed"
                        elif data[4] == 3:
                            activated = subprocess.run(["/usr/bin/open", "-a", app_path], capture_output=True, timeout=3)
                            if activated.returncode:
                                action_error = "Agent selected; cannot activate Herdr. Check --app-path"
                        if action_error: message = action_error
                except (OSError, subprocess.TimeoutExpired) as e:
                    h.close(); h = None; next_attempt = now + 1; message = str(e)
            if now >= next_status or old_message != message:
                atomic_json(directory / ".bridge-status.json", {"timestamp": int(time.time()*1000), "message": message})
                next_status = now + 1; old_message = message
            time.sleep(0.025 if h else 0.15)
    finally:
        try:
            if h:
                try: h.write(b"\0" + packet(4))
                finally: h.close()
        finally:
            if managed:
                atomic_json(directory / ".bridge-status.json", {"timestamp": int(time.time()*1000), "message": "Bridge stopped · panel inactive or paused"})
            lock.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory", type=Path, default=Path(os.environ.get('HERDR_APP_HOME',str(Path.home()/'.config/herdr-app'))).expanduser()/"mods/q0-agents")
    p.add_argument("--app-cli", default="herdr-app")
    p.add_argument("--app-path", default=str(Path.home()/"Applications/Herdr.app"))
    p.add_argument("--managed", action="store_true", help="Exit when the panel heartbeat expires or management is paused")
    p.add_argument("--probe", action="store_true", help="Only check for custom firmware; never change settings")
    a = p.parse_args()
    if a.probe:
        h = open_keyboard()
        try:
            handshake(h); print("Q0H1 firmware verified")
        except OSError as e: raise SystemExit(str(e))
        finally: h.close()
    else:
        try: run(a.directory, a.app_cli, a.app_path, managed=a.managed)
        except KeyboardInterrupt: pass
