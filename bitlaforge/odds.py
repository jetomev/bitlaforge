"""The lottery, honestly: your real chance of finding a block (v1.0.0).

Javier, 2 Oct 2026: "Wow! I like it!" Once an hour (when the Lottery odds
switch is on) bitlaForge asks mempool.space, a public Bitcoin website, two
things: the network's difficulty and the last block's reward. Nothing about
you is sent: no wallet, no speed. The answer is kept, so the odds still show
offline, with when they were checked.

The maths: each hash finds a block with probability 1 / (difficulty × 2³²).
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

API = "https://mempool.space/api/v1"
EVERY = 3600                     # seconds between asks
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "bitlaforge" / "network.json"


@dataclass
class Network:
    difficulty: float
    hashrate: float               # hashes per second, the whole network
    reward_btc: float             # the last block's reward, fees included
    checked: float                # when mempool.space was asked


def fetch(timeout: float = 10) -> Network:
    """Ask mempool.space. Raises OSError/ValueError when it can't be reached."""
    def get(path: str):
        req = urllib.request.Request(f"{API}/{path}", headers={"User-Agent": "bitlaForge"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    rate = get("mining/hashrate/3d")
    blocks = get("blocks")
    return Network(float(rate["currentDifficulty"]), float(rate["currentHashrate"]),
                   blocks[0]["extras"]["reward"] / 1e8, time.time())


def load(path: Path = CACHE) -> Network | None:
    try:
        return Network(**json.loads(path.read_text()))
    except (OSError, ValueError, TypeError):
        return None


def save(n: Network, path: Path = CACHE) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(n)))
    except OSError:
        pass


def due(n: Network | None, now: float | None = None) -> bool:
    return n is None or (now or time.time()) - n.checked >= EVERY


def one_in(khs: float, difficulty: float, seconds: float) -> float:
    """"1 in N": the chance of at least one block in ``seconds`` at ``khs``."""
    per_hash = 1 / (difficulty * 2 ** 32)
    expected = khs * 1000 * seconds * per_hash
    return 1 / expected if expected > 0 else float("inf")


def words(n: float) -> str:
    """1 in 35,873,390,454 → "1 in 36 billion"."""
    if n == float("inf"):
        return "none while stopped"
    for name, size in (("trillion", 1e12), ("billion", 1e9), ("million", 1e6), ("thousand", 1e3)):
        if n >= size:
            v = n / size
            return f"1 in {v:.0f} {name}" if v >= 10 else f"1 in {v:.1f} {name}".replace(".0 ", " ")
    return f"1 in {n:.0f}"


def eh(hashrate: float) -> str:
    return f"{hashrate / 1e18:.0f} EH/s"


def checked_words(n: Network, now: float | None = None) -> str:
    mins = int(((now or time.time()) - n.checked) // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    if mins < 48 * 60:
        return f"{mins // 60} h ago"
    return f"{mins // 1440} days ago"
