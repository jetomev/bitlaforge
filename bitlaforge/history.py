"""History: every mining session, kept between runs (v1.0.0).

Javier, 2 Oct 2026: "Love it!" One small file,
``~/.local/share/bitlaforge/history.json``; nothing leaves the computer. A
session is written when it starts and brought up to date every minute, so a
session cut short (the computer switched off, bitlaForge killed) still shows,
as "bitlaForge closed unexpectedly". The newest 500 are kept.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

PATH = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "bitlaforge" / "history.json"
KEEP = 500
RUNNING = "running"


@dataclass
class Session:
    started: float
    seconds: int = 0
    average_khs: float = 0.0
    accepted: int = 0
    rejected: int = 0
    why: str = RUNNING

    @property
    def when(self) -> datetime:
        return datetime.fromtimestamp(self.started)


def load(path: Path = PATH) -> list[Session]:
    """Newest first. A session still marked running from an earlier run ended unexpectedly."""
    try:
        rows = json.loads(path.read_text())
    except (OSError, ValueError):
        return []
    out = []
    for r in rows if isinstance(rows, list) else []:
        try:
            out.append(Session(**r))
        except TypeError:
            continue
    return sorted(out, key=lambda s: s.started, reverse=True)


def record(s: Session, path: Path = PATH) -> None:
    """Add or bring up to date one session (matched by when it started)."""
    rows = [r for r in load(path) if r.started != s.started]
    rows = sorted(rows + [s], key=lambda r: r.started, reverse=True)[:KEEP]
    from .settings import write_atomic
    try:
        write_atomic(path, json.dumps([asdict(r) for r in rows], indent=0))
    except OSError:
        pass


def close_unfinished(path: Path = PATH) -> int:
    """At start-up: sessions left "running" by an earlier run ended unexpectedly."""
    rows = load(path)
    hit = [r for r in rows if r.why == RUNNING]
    for r in hit:
        r.why = "bitlaForge closed unexpectedly"
        record(r, path)
    return len(hit)


@dataclass
class Totals:
    seconds: int
    accepted: int
    rejected: int
    sessions: int
    best_day: str           # the day with the most mining time


def totals(rows: list[Session]) -> Totals:
    by_day: dict[str, int] = defaultdict(int)
    for r in rows:
        by_day[r.when.strftime("%b %-d")] += r.seconds
    best = max(by_day.items(), key=lambda kv: kv[1])[0] if by_day else ""
    return Totals(sum(r.seconds for r in rows), sum(r.accepted for r in rows),
                  sum(r.rejected for r in rows), len(rows), best)


def duration(seconds: int) -> str:
    h, rest = divmod(int(seconds), 3600)
    m = rest // 60
    if h:
        return f"{h} h {m:02d} min"
    if m:
        return f"{m} min"
    return f"{int(seconds)} s"
