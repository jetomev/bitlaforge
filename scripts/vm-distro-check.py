#!/usr/bin/env python3
"""Run inside a distro test VM: does bitlaForge work with this distribution's
miner? (v1.0.0, the same check alacrittyForge 1.0 had for Alacritty)

1. bitlaForge's tests, here.
2. The real ``minerd`` on PATH, driven through the app (headless):
   - Test the miner (10 s on one core, no pool) must report a speed;
   - mining is started against a pool address where nothing listens
     (127.0.0.1:1), so nothing is mined and nothing leaves the machine; the
     Dashboard must say the pool can't be reached;
   - quitting must ask, then leave no miner running.

Usage, with forgekit beside the repo:  PYTHONPATH=../forgekit python3 scripts/vm-distro-check.py
Prints a summary; the last line is PASS or FAIL.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

WALLET = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"


def miners_running() -> int:
    out = subprocess.run(["ps", "-C", "minerd", "-o", "pid", "--no-headers"], capture_output=True, text=True)
    return len(out.stdout.split())


async def drive() -> list[str]:
    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp())
    cfg = tmp / "config.toml"
    cfg.write_text(f'pool = "stratum+tcp://127.0.0.1:1"\nwallet = "{WALLET}"\nthreads = 1\n')
    from bitlaforge.app import BitlaForgeApp
    from bitlaforge.settings import Config
    notes: list[str] = []
    app = BitlaForgeApp(config=Config.load(cfg), history_path=tmp / "h.json", network_cache=tmp / "n.json")
    real_notify = app.notify
    app.notify = lambda msg, **kw: (notes.append(str(msg)), real_notify(msg, **kw))
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause(1)
        print(f"miner: {app.minerd}")
        await pilot.press("t")
        await pilot.pause(12)
        passed = [n for n in notes if n.startswith("The miner works")]
        print("test:", passed[0] if passed else f"no result ({notes[-1:] or 'nothing said'})")
        if not passed:
            problems.append("Test the miner gave no speed")
        await pilot.press("m")
        end = time.time() + 15
        while time.time() < end and not app.miner.stats.problem:
            await pilot.pause(0.3)
        await pilot.pause(1.2)
        mining = str(app.query_one("#db-mining").render())
        said = "can't reach the pool" in mining
        print("unreachable pool shown on the Dashboard:", said)
        if not said:
            problems.append(f"the Dashboard didn't say the pool can't be reached: {mining!r}")
        pid = app.miner.pid
        await pilot.press("q")
        await pilot.pause(0.5)
        asked = type(app.screen).__name__ == "QuitDialog"
        print("quitting asked first:", asked)
        if not asked:
            problems.append("quitting didn't ask")
        await pilot.press("enter")
        await pilot.pause(1)
    await asyncio.sleep(1)
    gone = pid is not None and not Path(f"/proc/{pid}").exists()
    print("miner stopped after quitting:", gone)
    if not gone:
        problems.append("the miner outlived bitlaForge")
    shutil.rmtree(tmp, ignore_errors=True)
    return problems


def main() -> int:
    ok = True
    v = subprocess.run(["minerd", "--version"], capture_output=True, text=True) if shutil.which("minerd") else None
    print(f"{(v.stdout or v.stderr).splitlines()[0] if v else 'no minerd'} · Python {sys.version.split()[0]}")
    r = subprocess.run([sys.executable, "-W", "default", "-m", "unittest", "discover", "tests"], cwd=HERE,
                       capture_output=True, text=True, env=dict(os.environ))
    summary = [l for l in r.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
    print("tests:", " · ".join(summary))
    ok = ok and r.returncode == 0
    if not shutil.which("minerd"):
        print("FAIL: no minerd on PATH")
        return 1
    problems = asyncio.run(drive())
    left = miners_running()
    if left:
        problems.append(f"{left} miner(s) still running at the end")
    for p in problems:
        print(" -", p)
    ok = ok and not problems
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
