"""Starting bitlaForge from the terminal (v1.0.0).

``--version`` and ``--help`` answer and exit without opening the app.
Otherwise the app runs full-screen, and when it closes the terminal gets the
record of the session: the start banner, then a closing note saying what was
mined and saved, where the run was logged, and a thank-you (the same start
and end as grubForge, alacrittyForge and nog). However the app ends, the
miner is stopped before this returns.
"""

from __future__ import annotations

import datetime as dt
import os
import sys

from . import __version__

USAGE = f"""bitlaForge {__version__} — solo Bitcoin mining, honestly framed

Usage:
  bitlaforge             open bitlaForge
  bitlaforge --version   print the version
  bitlaforge --help      print this

Inside: M starts and stops mining (never on its own), T tests the miner,
1-4 change screens, F10 saves settings (with a review first), F1 explains,
? lists every key. Closing bitlaForge stops the miner.
Manual: https://github.com/jetomev/bitlaforge/tree/main/bitlaforge/manual
"""

LOG_DIR = "~/.local/share/bitlaforge/logs"


def summary(app) -> tuple[str, list[str], str]:
    from . import history
    from .miner import speed
    lines: list[str] = []
    if app.mined:
        secs = sum(s.seconds for s in app.mined)
        acc = sum(s.accepted for s in app.mined)
        rej = sum(s.rejected for s in app.mined)
        heading = f"Mined for {history.duration(secs)}"
        avg = [s.average_khs for s in app.mined if s.average_khs]
        lines.append(f"{len(app.mined)} session{'s' if len(app.mined) != 1 else ''}, "
                     f"{acc} share{'s' if acc != 1 else ''} accepted, {rej} rejected"
                     + (f", about {speed(sum(avg) / len(avg))}." if avg else "."))
        lines.append("The miner is stopped.")
    else:
        heading = "Didn't mine this time"
    if app.saves:
        lines.append(f"Settings saved {app.saves} time{'s' if app.saves != 1 else ''}, with a backup first.")
    elif app.config.change_count:
        lines.append("Settings changes were not saved.")
    return f"bitlaForge · {heading}", lines, "ok"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("--version", "-V", "version"):
        print(f"bitlaForge {__version__}")
        return 0
    if args and args[0] in ("--help", "-h", "help"):
        print(USAGE)
        return 0
    if args:
        print(f"bitlaforge: unknown option {args[0]!r}\n\n{USAGE}", file=sys.stderr)
        return 2

    from forgekit import closing_notice, runs_log_row, session_banner
    from .app import BitlaForgeApp

    app = BitlaForgeApp()
    try:
        app.run()
    finally:
        app.miner.stop_now()          # never left running, whatever happened
    ended = dt.datetime.now()
    heading, lines, level = summary(app)
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown"
    logs = []
    try:
        logs.append(runs_log_row(LOG_DIR, "bitlaforge",
                                 [f"{app.started:%m/%d/%Y}", f"{app.started:%I:%M %p}", user, "bitlaforge",
                                  heading.split("·", 1)[-1].strip(), " ".join(lines)]))
    except OSError as e:
        lines = lines + [f"(This run could not be logged: {e})"]
    print(session_banner("bitlaForge", __version__, "bitlaforge", app.started, ended, user))
    print(closing_notice(heading, lines, level=level, logs=logs, thanks="Thank you for using bitlaForge!"))
    return 0
