#!/usr/bin/env python3
"""Regenerate the README screenshots (v1.0.0) — Textual SVGs at 100 columns.

Run from the repo root (forgekit on PYTHONPATH if not installed):
    python docs/screenshots/generate.py
Everything happens in a temporary folder: a stand-in "minerd" (a small script
printing cpuminer's line format), an example wallet from Bitcoin's own
specification (BIP350), example History sessions and network numbers; the miner's processor use on the
Dashboard is staged (the stand-in barely uses any). Nothing
is mined, nothing is sent anywhere, and none of your own files are read.
"""
import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp())
os.environ["HOME"] = str(TMP)            # paths show as ~/.config/…, as on a real computer
for k, d in (("XDG_CONFIG_HOME", ".config"), ("XDG_DATA_HOME", ".local/share"), ("XDG_CACHE_HOME", ".cache")):
    os.environ[k] = str(TMP / d)

from bitlaforge import app as app_module, history, odds  # noqa: E402
from bitlaforge.app import BitlaForgeApp  # noqa: E402
from bitlaforge.settings import Config  # noqa: E402

OUT = Path(__file__).resolve().parent
SIZE = (100, 30)
WALLET = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"   # BIP350's example
STAND_IN = r'''#!/usr/bin/env python3
import sys, time, random
if "--version" in sys.argv:
    print("cpuminer 2.5.1"); sys.exit(0)
t = int(sys.argv[sys.argv.index("-t") + 1])
w = lambda s: (sys.stderr.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + s + "\n"), sys.stderr.flush())
w(f"{t} miner threads started, using 'sha256d' algorithm.")
w("Starting Stratum on stratum+tcp://solo.ckpool.org:3333")
w("Stratum difficulty set to 10000")
n = 0
while True:
    tot = 0
    for i in range(t):
        r = 11500 + random.randint(-250, 250); tot += r
        w(f"thread {i}: {r * 5} hashes, {r} khash/s")
    w(f"Total: {tot} khash/s")
    n += 1
    if n in (2, 4, 7):
        w(f"accepted: {min(n, 3) - (n == 7)}/{min(n, 3)} (100.00%), {tot} khash/s (yay!!!)")
    time.sleep(0.4)
'''


def shot(app, name: str) -> None:
    app.save_screenshot(filename=f"{name}.svg", path=str(OUT))
    print(f"  {name}.svg")


async def main() -> None:
    bindir = TMP / "bin"
    bindir.mkdir()
    (bindir / "minerd").write_text(STAND_IN)
    (bindir / "minerd").chmod(0o755)
    os.environ["PATH"] = f"{bindir}:{os.environ['PATH']}"
    # the stand-in barely uses the processor; the picture shows a real miner's load (staged: 15.2 cores)
    app_module.compute_cpu_pct = lambda _a, _b: 1520.0
    cfg = TMP / ".config" / "bitlaforge" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(f'pool = "stratum+tcp://solo.ckpool.org:3333"\nwallet = "{WALLET}"\nthreads = 15\n'
                   f'miner_name = "desktop"\nniceness = 19\n')
    hist = TMP / "history.json"
    day = 86_400
    for ago, secs, khs, acc, why in ((1 * day + 7200, 32_520, 181_200, 3, "you stopped it"),
                                     (2 * day + 3600, 720, 184_000, 0, "bitlaForge closed"),
                                     (3 * day, 2460, 0, 0, "it stopped by itself")):
        history.record(history.Session(time.time() - ago, secs, khs, acc, 0, why), hist)
    net = TMP / "network.json"
    odds.save(odds.Network(1.33e14, 975e18, 3.15, time.time() - 120), net)
    app = BitlaForgeApp(config=Config.load(cfg), history_path=hist, network_cache=net)
    try:
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause(1.0)
            shot(app, "02-dashboard-stopped")
            await pilot.press("m")
            await pilot.pause(3.5)
            st = app.miner.stats
            for i, v in enumerate([170, 178, 182, 183, 181, 184, 183, 175, 184, 185, 183, 184, 182, 184]):
                st.minutes.append(v * 1000)
            st.started -= 14 * 60 + 23
            await pilot.pause(1.2)
            shot(app, "01-dashboard-mining")
            await pilot.press("2")
            await pilot.pause(0.5)
            shot(app, "03-settings")
            app.query_one("#bf-groups").highlighted = 2
            await pilot.pause(0.3)
            app.query_one("#row-heat_limit").control.set_value(80)
            await pilot.pause(0.3)
            shot(app, "04-safety")
            await pilot.press("f10")
            await pilot.pause(0.6)
            shot(app, "05-review")
            await pilot.press("escape")
            await pilot.pause(0.3)
            app.config.discard()
            app.query_one("#sec-settings").sync()
            app.refresh_state()
            await pilot.press("3")
            await pilot.pause(0.6)
            shot(app, "06-log")
            await pilot.press("4")
            await pilot.pause(0.5)
            shot(app, "07-history")
            await pilot.press("1")
            await pilot.pause(0.3)
            await pilot.press("q")
            await pilot.pause(0.5)
            shot(app, "08-quit")
            await pilot.press("enter")
            await pilot.pause(1)
    finally:
        app.miner.stop_now()
    print("bitlaForge screenshots done.")


asyncio.run(main())
