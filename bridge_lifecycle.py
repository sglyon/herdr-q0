#!/usr/bin/env python3
"""Short-lived launcher for a panel-owned bridge; never touches agents or firmware."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess

from bridge import read_snapshot


def ensure(directory):
    if (directory / ".bridge-paused").exists():
        return "paused"
    # Do not launch from an obsolete panel, nor contend with a manual/service bridge.
    read_snapshot(directory / ".state.json")
    with (directory / ".bridge.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "running"
    config = json.loads((directory / ".bridge-config.json").read_text())
    with (directory / ".bridge.log").open("ab") as out, (directory / ".bridge-error.log").open("ab") as err:
        subprocess.Popen(config["arguments"] + ["--managed"], stdin=subprocess.DEVNULL,
                         stdout=out, stderr=err, start_new_session=True, close_fds=True)
    return "started"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["ensure", "pause", "resume"])
    p.add_argument("--directory", type=Path, default=Path(os.environ.get("HERDR_APP_HOME", str(Path.home()/".config/herdr-app")))/"mods/q0-agents")
    a = p.parse_args()
    paused = a.directory / ".bridge-paused"
    if a.action == "pause":
        paused.touch(mode=0o600)
        print("Paused. Managed bridge will exit; stop manual/service bridges separately.")
    elif a.action == "resume":
        paused.unlink(missing_ok=True)
        print("Resumed. The active panel will start its bridge.")
    else:
        print(ensure(a.directory))


if __name__ == "__main__":
    main()
