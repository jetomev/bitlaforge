"""bitlaForge's settings: what they are, and saving them safely (v1.0.0).

One file, ``~/.config/bitlaforge/config.toml``. The names are 0.2.x's, so an
older file reads as it is (0.2.x stored every value as text: ``"8"``,
``"19"``). New in 1.0 (F-5, bitlaforge#8):

* a file that can't be read is **never saved over**; the app says why and
  offers the newest backup;
* every save is reviewed, backed up first, and written in one step; only the
  settings you changed are touched, everything else in the file stays.
"""

from __future__ import annotations

import os
import socket
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.exceptions import TOMLKitError

from . import pools
from .wallet import check as check_wallet, short as short_wallet

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "bitlaforge"
CONFIG_PATH = CONFIG_DIR / "config.toml"
CORES = os.cpu_count() or 1
GENTLE, NORMAL = 19, 0


def default_worker() -> str:
    from .miner import worker_name
    return worker_name(socket.gethostname()) or "bitlaforge"


@dataclass(frozen=True)
class Setting:
    key: str
    group: str
    label: str
    control: str                 # pool, wallet, text, number, priority, switch
    help: str
    default: Any = None
    presets: tuple = ()
    lo: int | None = None
    hi: int | None = None
    unit: str = ""
    note: str = ""


GROUPS = (
    ("pool", "Pool & wallet", "where your mining goes, and who gets paid"),
    ("miner", "Miner", "how hard this computer works"),
    ("safety", "Safety", "heat, and what bitlaForge asks the internet"),
)


def _core_presets() -> tuple:
    return tuple(sorted({1, max(1, CORES // 4), max(1, CORES // 2), max(1, CORES - 1), CORES}))


SETTINGS = (
    Setting("pool", "pool", "Pool", "pool",
            "The solo pool your computer mines through. If your computer finds a block, the pool "
            "pays it to your wallet, minus its fee. Pick one near you; 'Other' takes any pool's "
            "address (name:port).", pools.DEFAULT),
    Setting("wallet", "pool", "Wallet", "wallet",
            "Your Bitcoin address: where a block's reward is paid. It is checked here, on your "
            "computer: a mistyped address is caught before it is ever used. Nothing is sent "
            "anywhere to check it.", ""),
    Setting("miner_name", "pool", "Worker name", "text",
            "A name for this computer, shown on the pool's page, so two computers mining to the same "
            "wallet can be told apart. Letters, digits, - and _.", None,
            note="shown on the pool's page"),
    Setting("threads", "miner", "Cores to use", "number",
            "How many processor cores mine. Leaving one free keeps the computer responsive for "
            "everything else. The change applies the next time mining starts.", max(1, CORES - 1),
            presets=_core_presets(), lo=1, hi=CORES, unit=f"of {CORES}"),
    Setting("niceness", "miner", "Priority", "priority",
            "Gentle lets every other program go first, so the computer feels the same while "
            "mining; the miner gets whatever is left. Normal competes equally with your programs.",
            GENTLE),
    Setting("heat_pause", "safety", "Pause when hot", "switch",
            "Pauses the miner when the processor reaches the temperature below, and resumes it "
            "when the processor has cooled 5 °C. Mining is long, full work for a processor.", True),
    Setting("heat_limit", "safety", "Pause at", "number",
            "The processor temperature that pauses mining. Most processors are built to run up to "
            "about 95 °C; 85 °C keeps a margin.", 85, presets=(75, 80, 85, 90), lo=60, hi=95,
            unit="°C"),
    Setting("odds", "safety", "Lottery odds", "switch",
            "Once an hour, asks mempool.space (a public Bitcoin website) how big the Bitcoin network "
            "is, to show your real chance of finding a block. Nothing about you is sent. Off: no "
            "internet is used for this, and the odds aren't shown.", True),
)
BY_KEY = {s.key: s for s in SETTINGS}


# ── reading values (0.2.x wrote everything as text) ──────────────────────────
def _as_int(v: Any, fallback: int) -> int:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return fallback


def _as_bool(v: Any, fallback: bool) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.strip().lower() in ("true", "yes", "on", "1"):
        return True
    if isinstance(v, str) and v.strip().lower() in ("false", "no", "off", "0"):
        return False
    return fallback


def typed(key: str, raw: Any) -> Any:
    """A value from the file as the app uses it; the default when absent or unusable."""
    s = BY_KEY[key]
    default = default_worker() if key == "miner_name" else s.default
    if raw is None:
        return default
    if key == "threads":
        n = _as_int(raw, default)
        return CORES if n <= 0 else min(n, CORES)        # 0.2.x: "0" meant every core
    if key == "niceness":
        return GENTLE if _as_int(raw, GENTLE) > 0 else NORMAL
    if key == "heat_limit":
        return min(max(_as_int(raw, default), s.lo), s.hi)
    if s.control == "switch":
        return _as_bool(raw, default)
    text = str(raw).strip()
    if key == "pool":
        return pools.normalise(text) if text else default
    if key == "miner_name":
        return text or default
    return text


def words(key: str, value: Any) -> str:
    """A value in plain words, for the review and the Dashboard."""
    if key == "pool":
        return pools.label(value)
    if key == "wallet":
        return short_wallet(value, 26) if value else "none"
    if key == "threads":
        return f"{value} of {CORES} cores"
    if key == "niceness":
        return "Gentle" if value == GENTLE else "Normal"
    if key == "heat_limit":
        return f"{value} °C"
    if BY_KEY[key].control == "switch":
        return "On" if value else "Off"
    return str(value)


# ── writing ──────────────────────────────────────────────────────────────────
def write_atomic(path: Path, text: str, *, mode: int = 0o600) -> Path:
    """Write ``text`` to ``path`` (following a link) in one step, so the file is
    never half-written. An existing file keeps its permissions."""
    target = Path(os.path.realpath(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        mode = target.stat().st_mode & 0o7777
    fd, tmp = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".new", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return target


@dataclass
class Config:
    """The settings file, what is changed but not saved yet, and saving it."""

    path: Path = CONFIG_PATH
    backup_dir: Path | None = None
    doc: Any = None
    error: str = ""                          # why the file can't be read
    exists: bool = False
    pending: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None, backup_dir: Path | None = None) -> "Config":
        c = cls(path=Path(path or CONFIG_PATH), backup_dir=backup_dir)
        c.reload()
        return c

    def reload(self) -> None:
        """Read the file again. Unsaved changes stay."""
        self.doc, self.error, self.exists = tomlkit.document(), "", self.path.exists()
        if not self.exists:
            return
        try:
            self.doc = tomlkit.parse(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as e:
            self.error = f"It can't be opened: {getattr(e, 'strerror', None) or e}."
        except TOMLKitError as e:
            self.error = f"Line {getattr(e, 'line', '?')} isn't valid: {str(e).split(' at line')[0]}."

    @property
    def readable(self) -> bool:
        return not self.error

    def original(self, key: str) -> Any:
        raw = self.doc.get(key) if self.readable else None
        return typed(key, raw.unwrap() if hasattr(raw, "unwrap") else raw)

    def value(self, key: str) -> Any:
        return self.pending[key] if key in self.pending else self.original(key)

    def values(self) -> dict[str, Any]:
        return {s.key: self.value(s.key) for s in SETTINGS}

    def set(self, key: str, value: Any) -> None:
        if key == "pool":
            value = pools.normalise(value)
        elif isinstance(value, str):
            value = value.strip()
        if value == self.original(key):
            self.pending.pop(key, None)
        else:
            self.pending[key] = value

    def discard(self) -> None:
        self.pending.clear()

    @property
    def change_count(self) -> int:
        return len(self.pending)

    def changes(self) -> list[tuple[str, str, str]]:
        """(setting, old, new) in plain words, in the form's order."""
        return [(s.label, words(s.key, self.original(s.key)), words(s.key, self.pending[s.key]))
                for s in SETTINGS if s.key in self.pending]

    def problems(self) -> list[str]:
        """What stops a save: values that can't work."""
        out = []
        w = self.value("wallet")
        if w and not check_wallet(w).ok:
            out.append(f"Wallet: {check_wallet(w).problem}")
        p = pools.problem(self.value("pool"))
        if p:
            out.append(f"Pool: {p}")
        return out

    def not_ready(self) -> list[str]:
        """Why mining can't start with the saved settings (empty when it can)."""
        if not self.readable:
            return ["The settings file can't be read."]
        out = []
        w = self.original("wallet")
        if not w:
            out.append("No wallet yet: add yours in Settings.")
        elif not check_wallet(w).ok:
            out.append(f"The saved wallet isn't valid: {check_wallet(w).problem}")
        p = pools.problem(self.original("pool"))
        if p:
            out.append(p)
        return out

    def save(self, note: str = "Before a save") -> Path | None:
        """Back up, then write only the changed settings. Returns the backup made.
        Raises ``ValueError`` for a file that can't be read: it is never saved over."""
        if not self.readable:
            raise ValueError(self.error)
        from . import backups
        made = backups.create(note, path=self.path, backup_dir=self.backup_dir) if self.exists else None
        doc = self.doc
        if not self.exists:
            doc.add(tomlkit.comment("bitlaForge settings. Edited by bitlaForge; your own notes stay."))
        for s in SETTINGS:
            if s.key in self.pending:
                doc[s.key] = self.pending[s.key]
        write_atomic(self.path, tomlkit.dumps(doc))
        self.pending.clear()
        self.reload()
        return made
