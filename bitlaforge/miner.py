"""The miner: starting it, stopping it, and reading what it says (v1.0.0).

bitlaForge runs ``minerd`` (cpuminer) and never starts it on its own. New in 1.0:

* **It stops when bitlaForge closes** (F-2, bitlaforge#5). Quitting asks first
  and stops it; and the miner is started with a *parent-death signal*
  (``setpriv --pdeathsig TERM``, util-linux), so the system itself stops it if
  bitlaForge ever ends without a chance to (a crash, a closed terminal).
* **Rejected shares are counted** (F-3, bitlaforge#6): cpuminer reports every
  share as ``accepted: A/T (…) (yay!!!|booooo)``; rejected = T − A.
* **Pausing for heat** freezes the miner (SIGSTOP) and lets it go on (SIGCONT),
  so no work or connection setup is thrown away.

The lines below are cpuminer 2.5.1's own, captured on 2 Oct 2026.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import signal
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

STOPPED_BY_ITSELF = "it stopped by itself"
ALGORITHM = "sha256d"          # Bitcoin's (Javier, 2 Oct: Bitcoin only)
PROVIDERS = ("cpuminer",)      # the package that provides minerd on Arch (AUR)


def find_minerd() -> str | None:
    return shutil.which("minerd")


def worker_name(name: str) -> str:
    """The pool-safe form of a name: small letters, digits, - and _."""
    return "".join(c.lower() for c in (name or "").strip() if c.isalnum() or c in "-_")[:32]


def command(values: dict, binary: str = "minerd") -> list[str]:
    """The full command that runs the miner with these settings."""
    from .pools import normalise
    worker = worker_name(values.get("miner_name", ""))
    user = values["wallet"] + (f".{worker}" if worker else "")
    cmd = [binary, "-a", ALGORITHM, "-o", normalise(values["pool"]), "-u", user, "-p", "x",
           "-t", str(int(values.get("threads") or 1))]
    if shutil.which("setpriv"):
        cmd = ["setpriv", "--pdeathsig", "TERM", *cmd]
    if int(values.get("niceness") or 0) > 0:
        cmd = ["nice", "-n", str(int(values["niceness"])), *cmd]
    return cmd


# ── reading the miner's lines ────────────────────────────────────────────────
_STAMP = re.compile(r"^\[\d{4}-\d\d-\d\d (\d\d:\d\d:\d\d)\]\s*")
_THREAD = re.compile(r"thread (\d+): (\d+) hashes, ([\d.]+) khash/s")
_TOTAL = re.compile(r"Total: ([\d.]+) khash/s")
_SHARE = re.compile(r"accepted: (\d+)/(\d+) \(([\d.]+)%\), ([\d.]+) khash/s(.*)")
_CONNECTED = ("Stratum difficulty set to", "Stratum requested work restart", "Stratum detected new block",
              "LONGPOLL pushed new work")
_FAILED = ("Stratum connection failed", "HTTP request failed", "json_rpc_call failed",
           "Stratum connection interrupted", "Stratum authentication failed", "...terminating workio thread")


@dataclass
class Event:
    """One line from the miner, read: what it means, in plain words."""
    time: str
    kind: str            # thread, total, accepted, rejected, connected, problem, started, info
    text: str            # plain words for the Log
    raw: str


def read_line(line: str) -> Event:
    m = _STAMP.match(line)
    when = m.group(1) if m else time.strftime("%H:%M:%S")
    body = line[m.end():] if m else line.strip()
    if (t := _THREAD.search(body)):
        return Event(when, "thread", f"core {int(t.group(1)) + 1}: {speed(float(t.group(3)))}", line)
    if (t := _TOTAL.search(body)):
        return Event(when, "total", f"total speed {speed(float(t.group(1)))}", line)
    if (s := _SHARE.search(body)):
        ok, total = int(s.group(1)), int(s.group(2))
        if "boo" in s.group(5):
            return Event(when, "rejected", f"share rejected ({ok} of {total} accepted): the pool said no, "
                                            "usually because the work was already out of date", line)
        return Event(when, "accepted", f"share accepted ({ok} of {total})", line)
    if body.startswith("Starting Stratum on"):
        return Event(when, "info", f"connecting to {body.split(' on ', 1)[1]}", line)
    if any(body.startswith(c) for c in _CONNECTED):
        return Event(when, "connected", "connected: the pool is sending work", line)
    if any(body.startswith(f) for f in _FAILED):
        why = body.split(": ", 1)[1] if ": " in body else body
        return Event(when, "problem", f"can't reach the pool: {why}", line)
    if "retry after" in body:
        return Event(when, "info", "trying again in 30 seconds", line)
    if "miner threads started" in body:
        return Event(when, "started", body.replace("miner threads", "cores").rstrip("."), line)
    return Event(when, "info", body, line)


def speed(khs: float) -> str:
    """cpuminer counts in khash/s; shown in the unit that reads best."""
    if khs <= 0:
        return "—"
    for unit, size in (("Th/s", 1e9), ("Gh/s", 1e6), ("Mh/s", 1e3), ("kh/s", 1)):
        if khs >= size:
            return f"{khs / size:.1f} {unit}"
    return f"{khs * 1000:.0f} h/s"


# ── what the Dashboard shows ─────────────────────────────────────────────────
@dataclass
class Stats:
    running: bool = False
    paused: bool = False             # frozen for heat
    started: float = 0.0
    ended: float = 0.0
    connected: bool = False
    problem: str = ""                # the latest trouble, in plain words
    cores: dict[int, float] = field(default_factory=dict)   # core → khash/s
    total_khs: float = 0.0
    accepted: int = 0
    submitted: int = 0
    why_stopped: str = ""
    exit_code: int | None = None     # when it stopped by itself
    minutes: deque = field(default_factory=lambda: deque(maxlen=30))  # speed, one per minute
    _sum: float = 0.0
    _n: int = 0
    _minute: list = field(default_factory=list)

    @property
    def rejected(self) -> int:
        return self.submitted - self.accepted

    @property
    def seconds(self) -> int:
        if not self.started:
            return 0
        return int((self.ended or time.time()) - self.started)

    @property
    def speed_khs(self) -> float:
        if self.total_khs:
            return self.total_khs
        return sum(self.cores.values())

    @property
    def average_khs(self) -> float:
        return self._sum / self._n if self._n else self.speed_khs

    def take(self, e: Event) -> None:
        """Update from one line."""
        if e.kind == "thread":
            t = _THREAD.search(e.raw)
            self.cores[int(t.group(1))] = float(t.group(3))
        elif e.kind == "total":
            self.total_khs = float(_TOTAL.search(e.raw).group(1))
            self._sum += self.total_khs
            self._n += 1
            self._minute.append(self.total_khs)
            self.connected = self.connected or bool(self.submitted)
        elif e.kind in ("accepted", "rejected"):
            s = _SHARE.search(e.raw)
            self.accepted, self.submitted = int(s.group(1)), int(s.group(2))
            self.connected, self.problem = True, ""
        elif e.kind == "connected":
            self.connected, self.problem = True, ""
        elif e.kind == "problem":
            self.connected, self.problem = False, e.text

    def tick_minute(self) -> None:
        """Called once a minute: the speed over that minute goes on the chart."""
        if self._minute:
            self.minutes.append(sum(self._minute) / len(self._minute))
            self._minute = []
        elif self.running and not self.paused:
            self.minutes.append(self.speed_khs)


# ── running it ───────────────────────────────────────────────────────────────
class Miner:
    """One miner at a time. ``on_event`` gets every line read; ``on_change``
    is called whenever running/stopped changes."""

    def __init__(self, on_event: Callable[[Event], None], on_change: Callable[[], None]) -> None:
        self.on_event, self.on_change = on_event, on_change
        self.proc: asyncio.subprocess.Process | None = None
        self.stats = Stats()
        self._reader: asyncio.Task | None = None
        self._stopping = False

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    @property
    def pid(self) -> int | None:
        return self.proc.pid if self.running else None

    async def start(self, values: dict, binary: str | None = None) -> str:
        """Start mining. Returns "" when started, or why it couldn't."""
        if self.running:
            return "The miner is already running."
        binary = binary or find_minerd()
        if not binary:
            return "The miner (minerd) isn't installed."
        # checked here: behind nice/setpriv a missing program would "start" and end at once
        if not (os.path.isfile(binary) and os.access(binary, os.X_OK)):
            return f"The miner couldn't start: {binary} isn't a program that can run."
        cmd = command(values, binary)
        try:
            self.proc = await asyncio.create_subprocess_exec(
                *cmd, stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT)
        except OSError as e:
            self.proc = None
            return f"The miner couldn't start: {e.strerror or e}."
        self.stats = Stats(running=True, started=time.time())
        self._stopping = False
        shown = " ".join("WALLET" if c.startswith(values["wallet"]) else
                         "minerd" if c == binary else c
                         for c in cmd if c not in ("setpriv", "--pdeathsig", "TERM"))
        self.on_event(Event(time.strftime("%H:%M:%S"), "info", f"started: {shown}", shown))
        self._reader = asyncio.create_task(self._read())
        self.on_change()
        return ""

    async def _read(self) -> None:
        proc = self.proc
        assert proc is not None and proc.stdout is not None
        while True:
            try:
                raw = await proc.stdout.readline()
            except (asyncio.CancelledError, ConnectionError):
                break
            if not raw:
                break
            line = raw.decode("utf-8", "replace").rstrip()
            if not line:
                continue
            e = read_line(line)
            self.stats.take(e)
            try:
                self.on_event(e)
            except Exception:       # a screen failing must not stop the reading
                pass
        code = await proc.wait()
        if not self._stopping:     # it ended by itself; the code goes to the Log, the reason stays short
            self.stats.exit_code = code
            self._finish(STOPPED_BY_ITSELF)

    def _finish(self, why: str) -> None:
        if not self.stats.running:
            return
        self.stats.tick_minute()
        self.stats.running, self.stats.paused = False, False
        self.stats.ended, self.stats.why_stopped = time.time(), why
        self.on_change()

    async def stop(self, why: str = "you stopped it") -> None:
        """Stop the miner: asked politely, then made to after 3 seconds."""
        if not self.running or self.proc is None:
            return
        self._stopping = True
        if self.stats.paused:
            self._signal(signal.SIGCONT)        # a frozen process can't hear "stop"
        try:
            self.proc.terminate()
            try:
                await asyncio.wait_for(self.proc.wait(), 3)
            except asyncio.TimeoutError:
                self.proc.kill()
                await self.proc.wait()
        except ProcessLookupError:
            pass
        if self._reader and not self._reader.done():
            self._reader.cancel()
        self._finish(why)

    def stop_now(self) -> None:
        """Last resort, without the event loop (bitlaForge is closing)."""
        if self.proc is not None and self.proc.returncode is None:
            for sig in (signal.SIGCONT, signal.SIGKILL):
                try:
                    os.kill(self.proc.pid, sig)
                except ProcessLookupError:
                    break

    def _signal(self, sig: int) -> bool:
        if not self.running:
            return False
        try:
            os.kill(self.proc.pid, sig)
            return True
        except ProcessLookupError:
            return False

    def pause(self) -> bool:
        if self.stats.paused or not self._signal(signal.SIGSTOP):
            return False
        self.stats.paused = True
        self.on_change()
        return True

    def resume(self) -> bool:
        if not self.stats.paused or not self._signal(signal.SIGCONT):
            return False
        self.stats.paused = False
        self.on_change()
        return True
