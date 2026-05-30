"""BitlaForge — per-process CPU/MEM readouts.

Reads ``/proc/<pid>/stat`` (for accumulated user/kernel ticks) and
``/proc/<pid>/status`` (for resident set size). Used by the App to
surface the running minerd's live CPU% and memory footprint on the
Dashboard alongside the parsed hashrate / shares — the main payoff is
making the niceness setting observable: when other workloads compete,
a niceness=19 minerd visibly drops CPU% while a niceness=0 minerd
doesn't.

CPU% is computed across two samples and follows the htop/top convention
where 100% = one logical core fully busy (so 8 fully-busy threads on a
16-core box reads 800%). Normalisation to "of all cores" would be a
single divide at the call site if we ever want it.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


_CLK_TCK = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100


@dataclass
class ProcessSample:
    """Snapshot of one process at a point in time."""

    timestamp: float    # time.time() when this sample was taken
    cpu_ticks: int      # utime + stime (clock ticks since process start)
    rss_mb:    int      # resident set size in mebibytes


def read_process_sample(pid: int) -> Optional[ProcessSample]:
    """Read ``/proc/<pid>/{stat,status}``. Return None if the process is gone."""
    stat_path = Path(f"/proc/{pid}/stat")
    status_path = Path(f"/proc/{pid}/status")
    if not stat_path.exists():
        return None

    try:
        stat_text = stat_path.read_text()
    except OSError:
        return None

    # ``stat`` format: pid (comm-with-possibly-spaces) state field4 field5 …
    # Parse from the rightmost ')' so commands with spaces/parens don't break
    # field counting.
    rparen = stat_text.rfind(")")
    if rparen == -1:
        return None
    fields = stat_text[rparen + 2:].split()
    if len(fields) < 16:
        return None
    try:
        # After stripping `pid (comm)` we lose the first two fields; the
        # remaining list starts at "state" (field 3). utime=14, stime=15
        # are at index 11 and 12 of the trimmed list.
        utime = int(fields[11])
        stime = int(fields[12])
    except (ValueError, IndexError):
        return None

    rss_kb = 0
    try:
        for line in status_path.read_text().splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        rss_kb = int(parts[1])
                    except ValueError:
                        pass
                break
    except OSError:
        # Status missing or unreadable — fall through with rss_kb = 0.
        pass

    return ProcessSample(
        timestamp=time.time(),
        cpu_ticks=utime + stime,
        rss_mb=rss_kb // 1024,
    )


def compute_cpu_pct(prev: ProcessSample, curr: ProcessSample) -> float:
    """Return CPU% across an interval. 100% = one logical core fully used."""
    dt = curr.timestamp - prev.timestamp
    if dt <= 0:
        return 0.0
    dticks = curr.cpu_ticks - prev.cpu_ticks
    if dticks < 0:
        return 0.0
    return (dticks / _CLK_TCK / dt) * 100.0
