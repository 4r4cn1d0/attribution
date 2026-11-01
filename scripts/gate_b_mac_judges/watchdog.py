"""Memory and disk watchdog for a Mac judge run (stdlib only); a copy of tmp/family-probe-olmo2-1b/harmbench_watchdog.py
(SHA-256 8f89b3ab…) with the same limits and defaults; only the log path is an argument and the stop rule is a function.

    python3 watchdog.py --pid JUDGE_PID --log PATH [--swap-gb 8] [--disk-gb 40] [--tag watchdog]

Every 20 s it reads `sysctl vm.swapusage`, the free space of the home volume and the kernel memory pressure level
(`sysctl kern.memorystatus_vm_pressure_level`: 1 normal, 2 warn, 4 critical). It sends SIGTERM to the judge, and logs
why, if swap used exceeds --swap-gb, free disk drops below --disk-gb, or the level is critical; it sends SIGKILL if the
judge is still alive 60 s later. It logs swap and free disk every 5 min and exits when the judge exits. The judge stops
after its current item on SIGTERM; its per-item cache makes the run resumable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def swap_used_gb() -> float:
    out = subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used = ([\d.]+)M", out)
    return float(m.group(1)) / 1024 if m else float("nan")


def free_disk_gb() -> float:
    st = os.statvfs(os.path.expanduser("~"))
    return st.f_bavail * st.f_frsize / 1024 ** 3


def pressure_level() -> int | None:
    out = subprocess.run(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"], capture_output=True, text=True).stdout
    return int(out.strip()) if out.strip().isdigit() else None


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def stop_reason(swap: float, disk: float, level, swap_gb: float, disk_gb: float) -> str | None:
    """harmbench_watchdog's stop rule, unchanged."""
    if swap > swap_gb:
        return f"swap used {swap:.2f}GB > {swap_gb}GB"
    if disk < disk_gb:
        return f"free disk {disk:.1f}GB < {disk_gb}GB"
    if level == 4:
        return "memory pressure level critical (4)"
    return None


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--swap-gb", type=float, default=8.0)
    ap.add_argument("--disk-gb", type=float, default=40.0)
    ap.add_argument("--interval", type=float, default=20.0)
    ap.add_argument("--report-every", type=float, default=300.0)
    ap.add_argument("--log", type=pathlib.Path, required=True)
    ap.add_argument("--tag", default="watchdog")
    return ap


def main(argv=None) -> int:
    a = parser().parse_args(argv)

    def write(msg: str) -> None:
        with a.log.open("a") as fh:
            fh.write(f"{utc()} {a.tag} {msg}\n")

    peak_swap, min_disk = 0.0, float("inf")
    write(f"start pid={a.pid} limits swap>{a.swap_gb}GB disk<{a.disk_gb}GB pressure=critical(4); "
          f"swap={swap_used_gb():.2f}GB free_disk={free_disk_gb():.1f}GB level={pressure_level()}")
    last_report, killed_at = time.time(), None
    while alive(a.pid):
        swap, disk, level = swap_used_gb(), free_disk_gb(), pressure_level()
        peak_swap, min_disk = max(peak_swap, swap), min(min_disk, disk)
        reason = stop_reason(swap, disk, level, a.swap_gb, a.disk_gb)
        if reason and killed_at is None:
            write(f"SIGTERM judge pid={a.pid}: {reason}")
            os.kill(a.pid, signal.SIGTERM)
            killed_at = time.time()
        elif killed_at is not None and time.time() - killed_at > 60 and alive(a.pid):
            write(f"SIGKILL judge pid={a.pid}: still alive 60 s after SIGTERM")
            os.kill(a.pid, signal.SIGKILL)
        if time.time() - last_report >= a.report_every:
            write(f"status swap={swap:.2f}GB free_disk={disk:.1f}GB level={level}")
            last_report = time.time()
        time.sleep(a.interval if killed_at is None else 5)
    write(f"judge pid={a.pid} exited; peak_swap={peak_swap:.2f}GB min_free_disk={min_disk:.1f}GB "
          f"stopped_by_watchdog={killed_at is not None}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
