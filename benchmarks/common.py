"""Shared helpers for the benchmark scripts."""
import csv
import gc
import os
import platform
import statistics
import sys
import time
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
RESULTS = os.path.join(ROOT, "results")
SIZES = (1_000, 10_000, 100_000, 1_000_000)

from caselaw import data  # noqa: E402


def corpus():
    return data.load_or_build()


def timed(fn, *args):
    """Run fn(*args) once after a garbage collection; return (seconds, result)."""
    gc.collect()
    t0 = time.perf_counter()
    result = fn(*args)
    return time.perf_counter() - t0, result


def summary(times):
    return min(times), statistics.median(times), max(times)


def write_csv(name, rows):
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", os.path.relpath(path, ROOT), flush=True)


def write_environment():
    mem_kb = 0
    try:
        with open("/proc/meminfo") as f:
            mem_kb = int(f.readline().split()[1])
    except OSError:
        pass
    lines = [f"date: {date.today().isoformat()}",
             f"python: {platform.python_version()} ({platform.python_implementation()})",
             f"platform: {platform.platform()}",
             f"machine: {platform.machine()}",
             f"cpu_count: {os.cpu_count()}",
             f"ram_gb: {mem_kb / 1e6:.1f}" if mem_kb else "ram_gb: unknown",
             "note: timings are wall-clock (time.perf_counter); one process at a time"]
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "environment.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
