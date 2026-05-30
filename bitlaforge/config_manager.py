"""BitlaForge — persistent config layer.

Reads and writes the miner config to ``~/.config/bitlaforge/config.toml``.
v0.1.0 held everything in-memory only; v0.1.1 persists across launches so
the user can configure pool / wallet / algorithm / threads once and just
press M to mine on every subsequent session.

Schema is intentionally flat for now — when later cycles add (e.g.) UI
preferences or log archive settings they can live under separate TOML
table headers (``[ui]``, ``[log]``) without breaking the miner section.

Read uses ``tomllib`` (Python 3.11+ stdlib). Write uses ``tomli_w``
(third-party, same dep alacrittyForge already pulls in).
"""

from __future__ import annotations

import socket
import tomllib
from pathlib import Path

import tomli_w


CONFIG_DIR = Path.home() / ".config" / "bitlaforge"
CONFIG_PATH = CONFIG_DIR / "config.toml"


def _default_miner_name() -> str:
    """Hostname makes a decent default — already meaningful when SSH-ing
    into a rig, and users with multiple BitlaForge instances will typically
    have distinct hostnames anyway."""
    try:
        return socket.gethostname() or ""
    except OSError:
        return ""


DEFAULT_CONFIG: dict[str, str] = {
    "pool":       "",
    "wallet":     "",
    "algorithm":  "sha256d",
    "threads":    "0",     # 0 = let minerd auto-detect
    "miner_name": _default_miner_name(),  # local label + pool worker name
    "niceness":   "19",    # 0 = normal; 19 = lowest priority (mining default)
}


def load_config() -> dict[str, str]:
    """Load config from disk; return defaults if the file doesn't exist.

    A corrupted or partially-written TOML file falls back to defaults
    rather than crashing — the user can fix and re-save through the UI.
    """
    if not CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)

    try:
        with CONFIG_PATH.open("rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return dict(DEFAULT_CONFIG)

    # Merge over defaults so missing keys get sane fallbacks and unknown
    # keys are tolerated (forward-compatible with future schema additions).
    merged = dict(DEFAULT_CONFIG)
    for k in DEFAULT_CONFIG:
        if k in data and isinstance(data[k], str):
            merged[k] = data[k]
    return merged


def save_config(config: dict[str, str]) -> bool:
    """Write the config to disk. Returns True on success, False on failure.

    Creates the config directory if it doesn't exist; only known keys are
    written so a careless caller can't bloat the file with junk.
    """
    payload = {k: str(config.get(k, DEFAULT_CONFIG[k])) for k in DEFAULT_CONFIG}

    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("wb") as f:
            tomli_w.dump(payload, f)
        return True
    except OSError:
        return False
