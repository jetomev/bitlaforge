"""BitlaForge — system info helpers.

Stdlib-only readouts for the Setup screen's diagnostics block (G1 in
v0.1.2). No psutil dep; everything comes from os.cpu_count, os.getloadavg,
and parsing /proc/cpuinfo + /proc/meminfo on Linux.

All accessors degrade gracefully if their source is missing or
unparseable — the caller gets a SystemInfo with default values rather
than an exception.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SystemInfo:
    """Snapshot of host resources at the time it was constructed."""

    hostname:        str
    cpu_model:       str
    logical_cores:   int
    physical_cores:  int
    mem_total_mb:    int
    mem_available_mb: int
    load_1:          float
    load_5:          float
    load_15:         float


# ── /proc/cpuinfo ─────────────────────────────────────────────────────────


def _read_cpuinfo() -> tuple[str, int]:
    """Return (cpu_model_name, physical_core_count) from /proc/cpuinfo.

    Logical cores come from ``os.cpu_count`` (matches multiprocessing /
    scheduler reality). Physical cores are derived by counting unique
    ``(physical id, core id)`` pairs across processor stanzas — that's
    what works on Intel/AMD with hyperthreading and on Apple Silicon
    with cluster topology.
    """
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists():
        return ("unknown CPU", os.cpu_count() or 1)

    try:
        text = cpuinfo.read_text(errors="replace")
    except OSError:
        return ("unknown CPU", os.cpu_count() or 1)

    cpu_model = "unknown CPU"
    pairs: set[tuple[str, str]] = set()
    current_phys: Optional[str] = None
    current_core: Optional[str] = None

    for line in text.splitlines():
        if ":" not in line:
            # blank line between processor stanzas — commit the pair.
            if current_phys is not None and current_core is not None:
                pairs.add((current_phys, current_core))
            current_phys = None
            current_core = None
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        if cpu_model == "unknown CPU" and key == "model name":
            cpu_model = val
        elif key == "physical id":
            current_phys = val
        elif key == "core id":
            current_core = val

    # Don't miss the last stanza if the file doesn't end with a blank line.
    if current_phys is not None and current_core is not None:
        pairs.add((current_phys, current_core))

    physical = len(pairs) if pairs else (os.cpu_count() or 1)
    return (cpu_model, physical)


# ── /proc/meminfo ─────────────────────────────────────────────────────────


def _read_meminfo() -> tuple[int, int]:
    """Return (mem_total_mb, mem_available_mb) from /proc/meminfo.

    Both are reported in mebibytes (1024 * 1024 bytes). Available falls
    back to ``MemFree + Buffers + Cached`` on older kernels that don't
    expose ``MemAvailable`` directly.
    """
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return (0, 0)

    try:
        text = meminfo.read_text(errors="replace")
    except OSError:
        return (0, 0)

    values_kb: dict[str, int] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip().split()
        if not val:
            continue
        try:
            values_kb[key.strip()] = int(val[0])
        except ValueError:
            continue

    total = values_kb.get("MemTotal", 0)
    available = values_kb.get("MemAvailable")
    if available is None:
        # Pre-3.14 kernel fallback.
        available = (
            values_kb.get("MemFree", 0)
            + values_kb.get("Buffers", 0)
            + values_kb.get("Cached", 0)
        )

    return (total // 1024, available // 1024)


# ── Load average ─────────────────────────────────────────────────────────


def _read_load_avg() -> tuple[float, float, float]:
    """Return the (1, 5, 15)-minute load averages; falls back to zeros."""
    try:
        load = os.getloadavg()
    except (OSError, AttributeError):
        return (0.0, 0.0, 0.0)
    return load


# ── Public ────────────────────────────────────────────────────────────────


def get_system_info() -> SystemInfo:
    """Build a fresh SystemInfo snapshot — cheap, safe to call on each render."""
    cpu_model, physical_cores = _read_cpuinfo()
    mem_total, mem_avail = _read_meminfo()
    load_1, load_5, load_15 = _read_load_avg()

    return SystemInfo(
        hostname=socket.gethostname(),
        cpu_model=cpu_model,
        logical_cores=os.cpu_count() or 1,
        physical_cores=physical_cores,
        mem_total_mb=mem_total,
        mem_available_mb=mem_avail,
        load_1=load_1,
        load_5=load_5,
        load_15=load_15,
    )
