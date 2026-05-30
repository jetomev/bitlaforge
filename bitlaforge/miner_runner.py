"""BitlaForge — minerd subprocess runner.

Owns the lifecycle of an external ``minerd`` process: build the command-line
args from the saved config, spawn via ``asyncio.create_subprocess_exec``,
stream stdout line-by-line into two callbacks (one raw, one stats-parsed),
and shut down cleanly on stop.

The parser is intentionally pragmatic — pooler's cpuminer (and most forks)
emit lines like:

    [2024-01-01 12:00:05] thread 0: 4096 hashes, 4.20 khash/s
    [2024-01-01 12:00:30] accepted: 1/1 (100.00%), 4.20 khash/s yes!
    [2024-01-01 12:00:40] rejected: 0/2 (0.00%), …

We grab the most recent ``khash/s`` number for the live hashrate, count
``accepted: N/M`` / ``rejected: N/M`` pairs as the share totals, and use
the max ``thread N:`` index seen as the running-thread count. Good enough
to feed the Dashboard; later cycles can refine if the user wants pickier
state machines.

Tests inject a binary path via the ``binary`` kwarg so a fake "minerd"
shell script can drive the lifecycle without an actual miner being
installed.
"""

from __future__ import annotations

import asyncio
import re
import shutil
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional


def find_minerd(binary: str = "minerd") -> Optional[str]:
    """Return the absolute path of the minerd binary on PATH, or None.

    Used at app launch to decide whether to show the install-guidance
    banner, and again on each M press so installing mid-session works
    without a relaunch.
    """
    return shutil.which(binary)


def sanitize_worker_name(name: str) -> str:
    """Strip a name down to the pool-safe character set.

    Stratum worker names are usually accepted as alphanumeric + ``-`` /
    ``_``. Lowercase isn't required but normalising avoids quietly
    splitting one rig into two on the pool dashboard if the user types
    "Laptop" once and "laptop" the next time.
    """
    return "".join(
        c.lower() if (c.isalnum() or c in "-_") else ""
        for c in name.strip()
    )


# Catalogue of AUR providers, used in install-guidance toasts and the
# Dashboard banner. Order matters — top entry is the recommended default.
MINERD_AUR_PROVIDERS: tuple[tuple[str, str], ...] = (
    ("cpuminer",       "pooler's original (recommended)"),
    ("cpuminer-multi", "multi-algorithm fork"),
    ("cpuminer-opt",   "heavily optimized variant"),
)


# ── Stats model ───────────────────────────────────────────────────────────


@dataclass
class MinerStats:
    """Snapshot of miner state. Read by the Dashboard, written by the runner."""

    running: bool = False
    hashrate_khs: float = 0.0          # latest khash/s value observed
    accepted: int = 0                  # accepted shares (from "accepted: N/M")
    rejected: int = 0                  # rejected shares
    threads: int = 0                   # 1 + max(thread index) seen so far
    started_at: Optional[float] = None  # time.time() when the process started

    # Per-process readouts (G5 v0.1.2). Updated by the App's 1-second tick
    # from /proc/<pid>/stat + /proc/<pid>/status — not by the parser.
    cpu_pct: float = 0.0               # 100% = one logical core fully used
    mem_mb: int = 0                    # resident set size in MiB

    # Config the miner was started with (echoed for the dashboard).
    pool: str = ""
    wallet: str = ""
    algorithm: str = ""

    @property
    def uptime_seconds(self) -> int:
        if self.started_at is None:
            return 0
        return int(time.time() - self.started_at)


# ── Output parsing ────────────────────────────────────────────────────────


_RE_HASHRATE = re.compile(r"(\d+\.\d+)\s*khash/s", re.IGNORECASE)
_RE_ACCEPTED = re.compile(r"accepted:\s*(\d+)/(\d+)", re.IGNORECASE)
_RE_REJECTED = re.compile(r"rejected:\s*(\d+)/(\d+)", re.IGNORECASE)
_RE_THREAD   = re.compile(r"thread\s+(\d+):", re.IGNORECASE)


def parse_line(line: str, stats: MinerStats) -> bool:
    """Update ``stats`` in place from one minerd output line. Returns True
    if any field actually changed (so the caller knows whether to repaint)."""
    updated = False

    m = _RE_HASHRATE.search(line)
    if m:
        new = float(m.group(1))
        if new != stats.hashrate_khs:
            stats.hashrate_khs = new
            updated = True

    m = _RE_ACCEPTED.search(line)
    if m:
        new = int(m.group(1))
        if new != stats.accepted:
            stats.accepted = new
            updated = True

    m = _RE_REJECTED.search(line)
    if m:
        new = int(m.group(1))
        if new != stats.rejected:
            stats.rejected = new
            updated = True

    m = _RE_THREAD.search(line)
    if m:
        new = int(m.group(1)) + 1
        if new > stats.threads:
            stats.threads = new
            updated = True

    return updated


# ── Runner ────────────────────────────────────────────────────────────────


LineCallback = Callable[[str], None]
StatsCallback = Callable[[MinerStats], None]


class MinerRunner:
    """Async wrapper around an external ``minerd`` process.

    Single-instance: holding more than one ``MinerRunner`` simultaneously
    is fine but they'd race on the same minerd binary; in BitlaForge there's
    exactly one runner per App.
    """

    def __init__(
        self,
        on_line: LineCallback,
        on_stats: StatsCallback,
    ) -> None:
        self._on_line = on_line
        self._on_stats = on_stats
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._stats = MinerStats()

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    @property
    def stats(self) -> MinerStats:
        return self._stats

    @property
    def pid(self) -> Optional[int]:
        """The minerd process pid, or None if no process is running.

        Used by the App's 1-second tick to read /proc/<pid>/stat for the
        CPU% / mem readouts on the Dashboard. Note: when niceness > 0 the
        spawned process is `nice`, not minerd directly — but `nice` exec's
        minerd in place, so the pid is the minerd pid either way.
        """
        if self._proc is None or self._proc.returncode is not None:
            return None
        return self._proc.pid

    async def start(
        self,
        config: dict,
        *,
        binary: str = "minerd",
    ) -> tuple[bool, str]:
        """Spawn minerd with args derived from ``config``.

        Returns ``(ok, message)``. ``ok=False`` covers binary-not-found,
        already-running, and OS-level spawn failure.

        When ``config["niceness"]`` is a positive integer, the binary is
        wrapped with ``nice -n N`` so the spawned process runs at a lower
        scheduler priority. Anything ≤ 0 (the default for "normal") runs
        the binary directly.
        """
        if self.is_running:
            return False, "miner already running"

        args = self._build_args(config)

        # G3 (v0.1.2): nice wrapper.
        try:
            niceness = int(config.get("niceness", "0"))
        except (TypeError, ValueError):
            niceness = 0
        if niceness > 0:
            cmd = ["nice", "-n", str(niceness), binary, *args]
        else:
            cmd = [binary, *args]

        try:
            self._proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                # Merge stderr into stdout so a single reader catches both —
                # cpuminer logs status to stderr and worker output to stdout.
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            # If niceness is set, FileNotFoundError most likely points at
            # `nice` itself (which lives in coreutils — essentially always
            # present), but we keep the message agnostic.
            return False, f"binary not found: {cmd[0]}"
        except OSError as e:
            return False, f"failed to start {cmd[0]}: {e}"

        # Reset stats with the config the miner was started against.
        self._stats = MinerStats(
            running=True,
            started_at=time.time(),
            pool=config.get("pool", ""),
            wallet=config.get("wallet", ""),
            algorithm=config.get("algorithm", ""),
        )
        self._on_stats(self._stats)

        # Kick off the line reader as a background task.
        self._reader_task = asyncio.create_task(self._read_stdout())

        return True, f"started {binary} (pid {self._proc.pid})"

    async def stop(self) -> None:
        """Terminate the process gracefully; SIGKILL fallback after 3s."""
        if not self.is_running or self._proc is None:
            return

        try:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                # Process didn't honour SIGTERM in time — escalate.
                self._proc.kill()
                await self._proc.wait()
        except ProcessLookupError:
            # Process already gone — fine.
            pass

        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()

        self._stats = MinerStats(running=False)
        self._on_stats(self._stats)

    def _build_args(self, config: dict) -> list[str]:
        """Translate the saved config into pooler-cpuminer-compatible args.

        Appends ``.workername`` to the wallet when ``config["miner_name"]``
        is set, so the pool side sees per-rig stats via Stratum's standard
        ``WALLET.WORKER`` convention. The worker name is sanitized down to
        the pool-safe character set (alphanumeric + ``-`` / ``_``) — see
        ``sanitize_worker_name``.
        """
        args: list[str] = []
        algo = config.get("algorithm", "").strip()
        if algo:
            args += ["-a", algo]

        pool = config.get("pool", "").strip()
        if pool:
            args += ["-o", pool]

        wallet = config.get("wallet", "").strip()
        if wallet:
            worker = sanitize_worker_name(config.get("miner_name", ""))
            user = f"{wallet}.{worker}" if worker else wallet
            args += ["-u", user]
            # Most pools want *some* password — "x" is the de-facto placeholder.
            args += ["-p", "x"]

        threads = config.get("threads", "0").strip()
        if threads and threads != "0":
            args += ["-t", threads]

        return args

    async def _read_stdout(self) -> None:
        """Stream the subprocess's merged stdout/stderr line-by-line.

        Each line is forwarded to ``on_line`` (the Log screen) and run
        through ``parse_line``; if parsing updates any stat, ``on_stats``
        fires so the Dashboard can repaint.
        """
        if self._proc is None or self._proc.stdout is None:
            return

        while True:
            try:
                line_bytes = await self._proc.stdout.readline()
            except (asyncio.CancelledError, BrokenPipeError):
                break
            if not line_bytes:
                break  # EOF — process is done.

            line = line_bytes.decode("utf-8", errors="replace").rstrip()
            if not line:
                continue

            try:
                self._on_line(line)
            except Exception:
                # A callback raising shouldn't kill the reader loop.
                pass

            if parse_line(line, self._stats):
                try:
                    self._on_stats(self._stats)
                except Exception:
                    pass

        # Process ended on its own — flip the running flag and notify.
        if self._stats.running:
            self._stats.running = False
            try:
                self._on_stats(self._stats)
            except Exception:
                pass
