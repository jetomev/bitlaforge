"""The processor's temperature, from its own sensor (v1.0.0).

Linux shows every sensor in ``/sys/class/hwmon``. The processor's is
``k10temp`` or ``zenpower`` on AMD (``Tctl``, the one the processor itself
throttles by), ``coretemp`` on Intel (``Package id 0``), and ``cpu_thermal``
on a Raspberry Pi. When none is found, heat isn't shown and mining is never
paused for it: the Dashboard says so.
"""

from __future__ import annotations

from pathlib import Path

HWMON = Path("/sys/class/hwmon")
CPU_SENSORS = ("k10temp", "zenpower", "coretemp", "cpu_thermal")
PREFERRED_LABELS = ("Tctl", "Tdie", "Package id 0")
RESUME_BELOW = 5          # °C under the limit before mining goes on


def _read(p: Path) -> str:
    try:
        return p.read_text().strip()
    except OSError:
        return ""


def processor_temp(root: Path = HWMON) -> float | None:
    """The processor's temperature in °C, or None when there is no sensor."""
    found: list[float] = []
    if not root.is_dir():
        return None
    for h in sorted(root.iterdir()):
        if _read(h / "name") not in CPU_SENSORS:
            continue
        temps = {}
        for t in sorted(h.glob("temp*_input")):
            raw = _read(t)
            if raw.lstrip("-").isdigit():
                temps[_read(t.with_name(t.name.replace("_input", "_label")))] = int(raw) / 1000
        if not temps:
            continue
        preferred = [v for k, v in temps.items() if k in PREFERRED_LABELS]
        found.append(max(preferred or temps.values()))
    return max(found) if found else None


def decide(temp: float | None, limit: int, paused: bool, on: bool) -> str:
    """What to do now: "pause", "resume" or "" (nothing)."""
    if temp is None or not on:
        return "resume" if paused else ""
    if not paused and temp >= limit:
        return "pause"
    if paused and temp <= limit - RESUME_BELOW:
        return "resume"
    return ""
