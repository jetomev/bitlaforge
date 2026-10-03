"""Backups of bitlaForge's settings file (v1.0.0).

One backup before every save, in ``~/.config/bitlaforge/backups/``, the newest
20 kept: ``config_<date>_<time>_<n>.bak.toml`` with a ``.note`` beside it
saying why it was made. Dated from the name, never the file's own time.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MAX_BACKUPS = 20
_STAMP = re.compile(r"config_(\d{8})_(\d{6})_")


@dataclass
class Backup:
    path: Path
    made: datetime
    note: str


def _dir(path: Path, backup_dir: Path | None) -> Path:
    return backup_dir or Path(path).parent / "backups"


def _note(p: Path) -> Path:
    return p.with_suffix("").with_suffix(".note")


def create(note: str, *, path: Path, backup_dir: Path | None = None) -> Path | None:
    src = Path(os.path.realpath(path))
    if not src.exists():
        return None
    d = _dir(path, backup_dir)
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    dest = d / f"config_{now:%Y%m%d_%H%M%S}_{now:%f}.bak.toml"
    n = 0
    while dest.exists():
        n += 1
        dest = d / f"config_{now:%Y%m%d_%H%M%S}_{now:%f}{n}.bak.toml"
    shutil.copy2(src, dest)
    _note(dest).write_text(note, encoding="utf-8")
    for b in list_all(path=path, backup_dir=backup_dir)[MAX_BACKUPS:]:
        b.path.unlink(missing_ok=True)
        _note(b.path).unlink(missing_ok=True)
    return dest


def list_all(*, path: Path, backup_dir: Path | None = None) -> list[Backup]:
    """Newest first."""
    d = _dir(path, backup_dir)
    if not d.is_dir():
        return []
    out = []
    for p in d.glob("config_*.bak.toml"):
        m = _STAMP.match(p.name)
        if not m:
            continue
        try:
            made = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
            note = _note(p).read_text(encoding="utf-8").strip() if _note(p).exists() else ""
        except (ValueError, OSError):
            continue
        out.append(Backup(p, made, note))
    return sorted(out, key=lambda b: (b.made, b.path.name), reverse=True)


def restore(b: Backup, *, path: Path, backup_dir: Path | None = None) -> Path | None:
    """Put a backup back, after backing up what is there now (even a broken file)."""
    from .settings import write_atomic
    text = b.path.read_text(encoding="utf-8")
    made = create("Before restoring a backup", path=path, backup_dir=backup_dir)
    write_atomic(path, text)
    return made
