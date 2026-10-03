"""The screens, headless, with a stand-in miner (a small script printing
cpuminer 2.5.1's line format), so nothing is ever mined. Every test works in a
temporary folder. Run: python -m unittest discover tests"""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
import time
import unittest
from pathlib import Path

from bitlaforge import backups, history, odds
from bitlaforge.settings import Config

WALLET = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"
CONFIG = f'''# my notes
pool = "stratum+tcp://solo.ckpool.org:3333"
wallet = "{WALLET}"
threads = "2"
miner_name = "testrig"
niceness = "19"
'''
STAND_IN = r'''#!/usr/bin/env python3
import sys, time
if "--version" in sys.argv:
    print("cpuminer 2.5.1 (stand-in)"); sys.exit(0)
w = lambda s: (sys.stderr.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + s + "\n"), sys.stderr.flush())
w("2 miner threads started, using 'sha256d' algorithm.")
w("Stratum difficulty set to 10000")
n = 0
while True:
    w("thread 0: 104857 hashes, 20900 khash/s"); w("thread 1: 104857 hashes, 21100 khash/s")
    w("Total: 42000 khash/s")
    n += 1
    if n == 2: w("accepted: 1/1 (100.00%), 42000 khash/s (yay!!!)")
    if n == 3: w("accepted: 1/2 (50.00%), 42000 khash/s (booooo)")
    time.sleep(0.2)
'''


def alive(pid: int) -> bool:
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return False


class Base(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.cfg = self.dir / "config.toml"
        self.cfg.write_text(CONFIG)
        b = self.dir / "bin"
        b.mkdir()
        (b / "minerd").write_text(STAND_IN)
        (b / "minerd").chmod(0o755)
        self._path = os.environ["PATH"]
        os.environ["PATH"] = f"{b}:{self._path}"
        self.hwmon = self.dir / "hwmon"
        self.sensor(60)
        # a fresh answer from mempool.space, so no test asks the internet
        odds.save(odds.Network(1.33e14, 975e18, 3.15, time.time()), self.dir / "network.json")

    def tearDown(self):
        os.environ["PATH"] = self._path
        self._tmp.cleanup()

    def sensor(self, celsius: float) -> None:
        h = self.hwmon / "hwmon0"
        h.mkdir(parents=True, exist_ok=True)
        (h / "name").write_text("k10temp\n")
        (h / "temp1_label").write_text("Tctl\n")
        (h / "temp1_input").write_text(f"{int(celsius * 1000)}\n")

    def app(self, text: str | None = None):
        from bitlaforge.app import BitlaForgeApp
        if text is not None:
            self.cfg.write_text(text)
        return BitlaForgeApp(config=Config.load(self.cfg), history_path=self.dir / "history.json",
                             network_cache=self.dir / "network.json", hwmon=self.hwmon)

    async def until(self, pilot, cond, seconds: float = 5.0) -> bool:
        end = time.time() + seconds
        while not cond() and time.time() < end:
            await pilot.pause(0.1)
        return cond()

    async def start_mining(self, app, pilot):
        await pilot.press("m")
        self.assertTrue(await self.until(pilot, lambda: app.miner.running), "mining didn't start")
        return app.miner.pid


class Quitting(Base):
    async def test_quitting_while_mining_asks_then_stops_the_miner(self):
        # F-2 (#5): 0.2.1 closed and left the miner running
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            pid = await self.start_mining(app, pilot)
            await pilot.press("q")
            await pilot.pause(0.4)
            self.assertEqual(type(app.screen).__name__, "QuitDialog")
            self.assertTrue(alive(pid), "asking must not stop it yet")
            await pilot.press("escape")                      # Stay
            await pilot.pause(0.3)
            self.assertTrue(app.miner.running)
            await pilot.press("q")
            await pilot.pause(0.4)
            await pilot.press("enter")                       # Stop mining and quit
            await self.until(pilot, lambda: not alive(pid))
        self.assertFalse(alive(pid), "the miner outlived bitlaForge")
        self.assertEqual(app.mined[0].why, "bitlaForge closed")
        self.assertEqual(history.load(self.dir / "history.json")[0].why, "bitlaForge closed")

    async def test_closing_any_other_way_still_stops_it(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            pid = await self.start_mining(app, pilot)
            app.exit()                                       # no question asked
            await pilot.pause(0.3)
        await asyncio.sleep(0.3)
        self.assertFalse(alive(pid))

    async def test_closing_note(self):
        from bitlaforge.cli import summary
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await self.start_mining(app, pilot)
            await self.until(pilot, lambda: app.miner.stats.submitted == 2)
            await pilot.press("m")
            await self.until(pilot, lambda: not app.miner.running)
        heading, lines, _ = summary(app)
        self.assertTrue(heading.startswith("bitlaForge · Mined for"), heading)
        self.assertIn("1 share accepted, 1 rejected", lines[0])
        self.assertEqual(lines[1], "The miner is stopped.")


class Mining(Base):
    async def test_dashboard_shows_speed_shares_and_odds(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await self.start_mining(app, pilot)
            await self.until(pilot, lambda: app.miner.stats.submitted == 2)
            await pilot.pause(1.2)
            text = lambda wid: str(app.query_one(wid).render())
            self.assertIn("Mining", text("#db-mining"))
            self.assertIn("42.0 Mh/s", text("#db-speed"))
            self.assertIn("2 busy", text("#db-speed"))
            self.assertIn("1 accepted", text("#db-heat"))
            self.assertIn("1 rejected", text("#db-heat"))          # F-3 (#6)
            self.assertIn("A block today", text("#db-odds"))
            self.assertIn("975 EH/s", text("#db-odds"))
            self.assertIn("mining — 1 share", text("#db-heat"))   # all time includes this session
            await pilot.press("m")
            await self.until(pilot, lambda: not app.miner.running)

    async def test_no_wallet_no_mining(self):
        app = self.app(CONFIG.replace(f'wallet = "{WALLET}"\n', ""))
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            self.assertTrue(app.query_one("#db-toggle").disabled)
            self.assertTrue(app.query_one("#db-wallet").display)
            await pilot.press("m")
            await pilot.pause(0.4)
            self.assertFalse(app.miner.running)
            await pilot.click("#db-wallet")
            await pilot.pause(0.3)
            self.assertEqual(app.focused.setting_key, "wallet")

    async def test_heat_pauses_and_resumes(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            pid = await self.start_mining(app, pilot)
            self.sensor(86)
            app._heat_tick()
            await pilot.pause(0.3)
            self.assertTrue(app.miner.stats.paused)
            self.assertEqual(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0], "T")
            self.assertIn("Paused", str(app.query_one("#db-mining").render()))
            self.sensor(82)                                   # cooler, but not 5 °C under
            app._heat_tick()
            self.assertTrue(app.miner.stats.paused)
            self.sensor(79)
            app._heat_tick()
            await pilot.pause(0.2)
            self.assertFalse(app.miner.stats.paused)
            kinds = [e.kind for e in app.query_one("#sec-log").events]
            self.assertIn("paused", kinds)
            self.assertIn("resumed", kinds)
            await pilot.press("m")
            await self.until(pilot, lambda: not app.miner.running)

    async def test_a_session_cut_short_shows_in_history(self):
        history.record(history.Session(started=time.time() - 600, seconds=540), self.dir / "history.json")
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("4")
            await pilot.pause(0.4)
            self.assertEqual(app.sessions()[0].why, "bitlaForge closed unexpectedly")
            self.assertEqual(app.query_one("#hs-table").row_count, 1)

    async def test_log_filters(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await self.start_mining(app, pilot)
            await self.until(pilot, lambda: app.miner.stats.submitted == 2)
            await pilot.press("m")
            await self.until(pilot, lambda: not app.miner.running)
            log = app.query_one("#sec-log")
            log.query_one("#lg-show").value = "shares"
            await pilot.pause(0.2)
            shown = [e for e in log.events if log.wanted(e)]
            self.assertEqual([e.kind for e in shown], ["accepted", "rejected"])
            log.query_one("#lg-show").value = "important"
            await pilot.pause(0.2)
            self.assertFalse(any(e.kind == "thread" for e in log.events if log.wanted(e)))
            self.assertFalse(any(WALLET in e.text for e in log.events))


class Saving(Base):
    async def test_a_change_is_reviewed_and_saved_with_one_backup(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            await pilot.pause(0.3)
            app.query_one("#row-threads").control.set_value(1)
            app.query_one("#row-heat_limit").control.set_value(80)
            await pilot.pause(0.3)
            self.assertEqual(app.config.change_count, 2)
            self.assertTrue(app.query_one("#row-threads").changed)
            await pilot.press("f10")
            await pilot.pause(0.5)
            self.assertEqual(type(app.screen).__name__, "ReviewDialog")
            await pilot.click("#save")
            await pilot.pause(0.5)
        text = self.cfg.read_text()
        self.assertIn("# my notes", text)
        self.assertIn("threads = 1", text)
        self.assertIn("heat_limit = 80", text)
        self.assertEqual(len(backups.list_all(path=self.cfg)), 1)
        self.assertEqual(app.saves, 1)

    async def test_a_mistyped_wallet_is_said_and_cant_be_saved(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            await pilot.pause(0.3)
            inp = app.query_one("#row-wallet").control
            inp.value = WALLET[:-1] + "q"
            await pilot.pause(0.3)
            self.assertIn("check digits", str(app.query_one("#bf-wallet-check").render()))
            await pilot.press("f10")
            await pilot.pause(0.4)
            self.assertNotEqual(type(app.screen).__name__, "ReviewDialog")
        self.assertEqual(self.cfg.read_text(), CONFIG)

    async def test_typing_in_a_field_never_triggers_a_key_and_esc_leaves_it(self):
        # F-1 (#3): in 0.2.1 Esc didn't leave a field
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            await pilot.pause(0.3)
            app.query_one("#row-miner_name").control.focus()
            await pilot.pause(0.2)
            await pilot.press("m", "t", "q", "1")
            await pilot.pause(0.4)
            self.assertFalse(app.miner.running)
            self.assertEqual(app.query_one("#forge-work").current, "sec-settings")
            self.assertTrue(app.query_one("#row-miner_name").control.value.endswith("mtq1"))
            await pilot.press("escape")
            await pilot.pause(0.2)
            self.assertEqual(app.focused.id, "bf-groups")
            await pilot.press("1")                              # a key acts again
            await pilot.pause(0.3)
            self.assertEqual(app.query_one("#forge-work").current, "sec-dashboard")

    async def test_a_file_that_cant_be_read_is_never_saved_over(self):
        # F-5 (#8): 0.2.1 read it as blank settings and the next save erased the wallet
        c = Config.load(self.cfg)
        c.set("threads", 1)
        c.save()                                             # one good backup exists
        broken = CONFIG.replace('threads = "2"', 'threads = "2')
        app = self.app(broken)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            self.assertTrue(app.query_one("#db-toggle").disabled)
            self.assertTrue(app.query_one("#db-restore").display)
            await pilot.press("2")
            await pilot.pause(0.3)
            self.assertTrue(app.query_one("#row-threads").control.disabled)
            await pilot.press("f10")
            await pilot.pause(0.3)
            self.assertEqual(self.cfg.read_text(), broken)
            await pilot.press("1")
            await pilot.pause(0.3)
            await pilot.click("#db-restore")
            await pilot.pause(0.4)
            self.assertTrue(app.config.readable)
            self.assertFalse(app.query_one("#row-threads").control.disabled)
        self.assertEqual(self.cfg.read_text(), CONFIG)


class Fits(Base):
    async def test_every_screen_fits_100_columns_while_mining(self):
        from textual.widgets import Button, Input, OptionList
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await self.start_mining(app, pilot)
            await self.until(pilot, lambda: app.miner.stats.submitted == 2)
            for key in "1234":
                await pilot.press(key)
                await pilot.pause(0.5)
                groups = app.query_one("#bf-groups", OptionList) if key == "2" else None
                for gi in range(groups.option_count if groups else 1):
                    if groups:
                        groups.highlighted = gi
                        await pilot.pause(0.3)
                    where = f"screen {key}" + (f" group {gi}" if groups else "")
                    for b in app.screen.query(Button):
                        if not b.display or not b.region.width:
                            continue
                        self.assertIn(str(b.label), b.render_line(0).text, f"{where}: {b.label!r} cut off")
                        self.assertLessEqual(b.region.right, b.parent.region.right,
                                             f"{where}: {str(b.label)!r} runs past its row")
                    for row in app.screen.query(".forge-setting"):
                        if row.display and row.region.width:
                            line = row.query_one(".forge-setting-line")
                            self.assertLessEqual(row.control.region.right, line.region.right,
                                                 f"{where}: {row.setting} runs past its row")
                    for w in app.screen.query("*"):
                        if isinstance(w, Input):         # a field scrolls its own long text
                            continue
                        self.assertFalse(w.display and w.show_horizontal_scrollbar,
                                         f"{where}: {w!r} scrolls sideways")
            await pilot.press("1")
            await pilot.press("m")
            await self.until(pilot, lambda: not app.miner.running)


class Manual(unittest.TestCase):
    def test_every_page_help_opens_exists(self):
        from forgekit import load_pages
        from bitlaforge.app import MANUAL_DIR
        from bitlaforge.settings import GROUPS
        ids = {pid for pid, _t, _m in load_pages(MANUAL_DIR)}
        for needed in [g for g, _l, _d in GROUPS] + ["dashboard", "log", "install", "lottery", "keys"]:
            self.assertIn(needed, ids)

    def test_the_name_is_bitlaforge(self):
        from bitlaforge.app import MANUAL_DIR
        root = Path(MANUAL_DIR).parent
        for p in list(root.rglob("*.py")) + list(Path(MANUAL_DIR).glob("*.md")):
            # the class's code name (BitlaForgeApp) is code, not something anyone reads
            found = re.findall(r".{0,30}BitlaForge(?!App).{0,30}", p.read_text())
            self.assertEqual(found, [], p.name)


class CommandLine(unittest.TestCase):
    def test_version_help_unknown(self):
        import contextlib
        import io
        from bitlaforge import __version__
        from bitlaforge.cli import main
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["--version"]), 0)
            self.assertEqual(main(["--help"]), 0)
        self.assertIn(f"bitlaForge {__version__}", out.getvalue())
        self.assertIn("Closing bitlaForge stops the miner", out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--mine-forever"]), 2)


if __name__ == "__main__":
    unittest.main()
