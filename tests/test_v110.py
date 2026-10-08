"""bitlaForge 1.1.0 (#13, Javier 8 Oct 2026): the menu keys come from forgekit 0.10.0
(1-5 and Ctrl + the underlined letter, Help included), the bottom bar says "1-5 menu",
--hypeforge makes bitlaForge a page of hypeForge Settings (no Quit of its own; Settings
asks it to close), and buttons read "Words in Title Case (k)".

Headless, with the same stand-in miner as test_screens.py: nothing is ever mined."""

from __future__ import annotations

import contextlib
import io
import os
import re
import signal
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_screens import Base, alive  # noqa: E402

from forgekit import HintBar, menu_key_clashes  # noqa: E402
from forgekit.menu import MenuDropdown, accel  # noqa: E402
from textual.widgets import Button  # noqa: E402

SECTIONS = ["dashboard", "settings", "log", "history"]
SMALL = {"a", "an", "and", "the", "to", "of", "for", "in", "on", "or", "with", "at", "by"}
LABEL = re.compile(r"^(?P<words>[A-Za-z' ]+?)(?: \((?P<key>[a-z0-9]|F\d{1,2}|Esc|Enter)\))?$")


def title_case(words: str) -> bool:
    """Every word starts with a capital, except the small joining words (never the first)."""
    parts = words.split()
    return bool(parts) and all(w[0].isupper() or (i and w in SMALL) for i, w in enumerate(parts))


class Labels(unittest.TestCase):
    def test_the_label_checker(self):
        for good in ("Start Mining (m)", "Test the Miner (t)", "Add Your Wallet", "Stay (Esc)", "Save (F10)"):
            m = LABEL.match(good)
            self.assertTrue(m and title_case(m["words"]), good)
        for bad in ("Start mining", "Save…  F10", "the Miner (t)", "Save (S)", "Clear(c)"):
            m = LABEL.match(bad)
            self.assertFalse(m and title_case(m["words"]), bad)


class MenuKeys(Base):
    def test_each_underlined_letter_is_unique(self):
        from bitlaforge.app import BitlaForgeApp
        self.assertEqual(menu_key_clashes(BitlaForgeApp.MENU), [])

    def test_no_hand_written_menu_keys_and_no_ctrl_clash(self):
        # forgekit makes 1-5 and Ctrl+letter from MENU; a copy in the app would shadow it, and
        # any other Ctrl key of bitlaForge's on an underlined letter would be a dead key
        from bitlaforge.app import BitlaForgeApp, QuitDialog
        from bitlaforge.ui.log import LogScreen
        ctrl = {f"ctrl+{accel(m)}" for m in BitlaForgeApp.MENU}
        own = [b for cls in (BitlaForgeApp, LogScreen, QuitDialog) for b in cls.__dict__.get("BINDINGS", [])]
        for b in own:
            for key in b.key.split(","):
                self.assertNotIn(key, ctrl, f"{key} is an underlined letter's Ctrl key")
                self.assertFalse(key.isdigit(), f"{key} is forgekit's to give")

    async def test_numbers_reach_every_entry_help_included(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            self.assertEqual(app._menu_count, 5)
            # pressed as a person would: from wherever the last screen left the focus
            for key, sec in zip("2341", ["settings", "log", "history", "dashboard"]):
                await pilot.press(key)
                await pilot.pause(0.3)
                self.assertEqual(app.query_one("#forge-work").current, f"sec-{sec}", key)
            await pilot.press("5")
            await pilot.pause(0.3)
            self.assertIsInstance(app.screen, MenuDropdown, "5 opens Help")
            self.assertEqual(app.screen.menu_id, "help")
            await pilot.press("escape")
            await pilot.pause(0.2)
            app.set_focus(None)
            await pilot.press("6")
            await pilot.pause(0.2)
            self.assertEqual(len(app.screen_stack), 1, "Quit has no number")

    async def test_ctrl_letters_reach_every_entry_even_from_a_field(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("ctrl+e")
            await pilot.pause(0.3)
            self.assertEqual(app.query_one("#forge-work").current, "sec-settings")
            app.query_one("#row-miner_name").control.focus()
            await pilot.pause(0.2)
            for key, sec in (("ctrl+l", "log"), ("ctrl+y", "history"), ("ctrl+d", "dashboard"),
                             ("ctrl+e", "settings")):
                await pilot.press(key)
                await pilot.pause(0.3)
                self.assertEqual(app.query_one("#forge-work").current, f"sec-{sec}", key)
            await pilot.press("ctrl+h")
            await pilot.pause(0.3)
            self.assertEqual(getattr(app.screen, "menu_id", None), "help")
            self.assertEqual(app.config.change_count, 0, "nothing was typed into the field")

    async def test_the_bottom_bar_says_1_to_5_menu(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            for key in "134":
                await pilot.press(key)
                await pilot.pause(0.4)
                text = str(app.query_one(HintBar).render())
                self.assertIn("1-5", text, f"screen {key}")
                self.assertIn("menu", text, f"screen {key}")
                self.assertNotIn("screens", text, f"screen {key}")
                self.assertNotIn("{menu}", text, f"screen {key}")


class InsideHypeForgeSettings(Base):
    def app(self, text=None, hypeforge=True):
        from bitlaforge.app import BitlaForgeApp
        from bitlaforge.settings import Config
        if text is not None:
            self.cfg.write_text(text)
        return BitlaForgeApp(config=Config.load(self.cfg), history_path=self.dir / "history.json",
                             network_cache=self.dir / "network.json", hwmon=self.hwmon, hypeforge=hypeforge)

    @contextlib.contextmanager
    def watch_exit(self, app, really: bool = False):
        """Record every exit() call; ``really`` lets it close the app too (a quit that only
        records leaves Textual half-closed). The real one is put back whatever happens."""
        calls, real = [], app.exit

        def exit_(*a, **k):
            calls.append(1)
            if really:
                real(*a, **k)
        app.exit = exit_
        try:
            yield calls
        finally:
            del app.exit

    async def test_no_quit_and_q_does_nothing(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            with self.watch_exit(app) as calls:
                self.assertEqual(len(app.query("#menu-quit")), 0, "no Quit in the bar")
                for key in ("q", "ctrl+q"):
                    await pilot.press(key)
                    await pilot.pause(0.3)
                app.action_act("quit")
                await pilot.pause(0.2)
                self.assertEqual(calls, [], "Q, Ctrl+Q and the Quit action do nothing")
                self.assertEqual(len(app.screen_stack), 1, "and ask nothing")
                self.assertEqual(app._menu_count, 5, "Help keeps its number")

    async def test_without_the_flag_q_still_quits(self):
        app = self.app(hypeforge=False)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            with self.watch_exit(app, really=True) as calls:
                self.assertEqual(len(app.query("#menu-quit")), 1)
                await pilot.press("q")
                await pilot.pause(0.3)
                self.assertEqual(calls, [1])

    async def test_settings_closing_it_while_mining_asks_first(self):
        # the miner must never outlive bitlaForge, however the close is asked for
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            pid = await self.start_mining(app, pilot)
            with self.watch_exit(app, really=True) as calls:
                # what hypeForge Settings sends; without a listener it would end the whole test run
                self.assertNotIn(signal.getsignal(signal.SIGUSR1), (signal.SIG_DFL, None))
                os.kill(os.getpid(), signal.SIGUSR1)
                await pilot.pause(0.4)
                self.assertEqual(type(app.screen).__name__, "QuitDialog", "it asks first")
                self.assertEqual(calls, [], "and doesn't close yet")
                self.assertTrue(alive(pid) and app.miner.running)
                app.host_quit()                              # asked again: still one question
                await pilot.pause(0.3)
                self.assertEqual(sum(type(s).__name__ == "QuitDialog" for s in app.screen_stack), 1)
                await pilot.press("enter")                   # Stop Mining and Quit
                await self.until(pilot, lambda: not alive(pid))
        self.assertFalse(alive(pid), "the miner outlived bitlaForge")
        self.assertEqual(calls, [1])
        self.assertEqual(app.mined[0].why, "bitlaForge closed")

    async def test_settings_closing_it_with_nothing_running_closes_at_once(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            with self.watch_exit(app, really=True) as calls:
                app.host_quit()
                await pilot.pause(0.2)
                self.assertEqual(calls, [1])

    async def test_settings_closing_it_with_unsaved_changes_asks(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            app.query_one("#row-threads").control.set_value(1)
            await pilot.pause(0.3)
            with self.watch_exit(app) as calls:
                app.host_quit()
                await pilot.pause(0.3)
                self.assertEqual(type(app.screen).__name__, "QuitDialog")
                self.assertEqual(calls, [])


class ButtonLabels(Base):
    def check(self, buttons, where: str, keys: set[str] | None = None) -> list[str]:
        seen = []
        for b in buttons:
            if (b.id or "").startswith("preset-"):        # a number's presets: values, not actions
                continue
            label = str(b.label)
            m = LABEL.match(label)
            self.assertTrue(m and title_case(m["words"]), f"{where}: {label!r}")
            if keys is not None and m["key"]:
                key = m["key"].lower() if len(m["key"]) > 1 else m["key"]
                self.assertIn({"esc": "escape"}.get(key, key), keys, f"{where}: {label!r} promises a key")
            seen.append(label)
        return seen

    def fits(self, app, where: str) -> None:
        """The Mining box's two buttons inside their row at 100 columns, label not cut."""
        for bid in ("db-toggle", "db-test"):
            b = app.query_one(f"#{bid}", Button)
            self.assertIn(str(b.label), b.render_line(0).text, f"{where}: {b.label!r} cut off")
            self.assertLessEqual(b.region.right, b.parent.region.right, f"{where}: {b.label!r} runs past its row")

    def app_keys(self, app) -> set[str]:
        keys = {k for k, _ in app._bindings}
        for node in app.query("*"):
            keys |= {k for k, _ in node._bindings}
        return keys

    async def test_every_button_on_every_screen(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            keys = self.app_keys(app)
            seen = self.check(app.screen.query(Button), "main", keys)
            for label in ("Start Mining (m)", "Test Miner (t)", "Add Your Wallet", "Restore the Newest Backup",
                          "How to Install the Miner", "Copy the Log", "Clear (c)"):
                self.assertIn(label, seen)
            app.query_one("#row-threads").control.set_value(1)
            await pilot.pause(0.3)
            bar = [b for b in app.screen.query(Button) if b.id in ("bf-save", "bf-discard")]
            self.assertEqual([str(b.label) for b in bar], ["Save Changes (s)", "Discard Changes"])
            self.check(bar, "changes bar", keys)
            await pilot.press("f10")
            await pilot.pause(0.4)
            self.assertEqual(type(app.screen).__name__, "ReviewDialog")
            self.assertIn("Save (s)", self.check(app.screen.query(Button), "review"))
            await pilot.press("escape")
            await pilot.pause(0.3)
            await pilot.press("q")
            await pilot.pause(0.3)
            self.assertEqual([str(b.label) for b in app.screen.query(Button)],
                             ["Save First", "Quit Without Saving", "Stay (Esc)"])
            self.check(app.screen.query(Button), "quit")
            await pilot.press("escape")
            await pilot.pause(0.2)
            app.config.discard()

    async def test_start_and_stop_say_their_key(self):
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            toggle = app.query_one("#db-toggle", Button)
            self.assertEqual(str(toggle.label), "Start Mining (m)")
            self.fits(app, "stopped")
            pid = await self.start_mining(app, pilot)
            await pilot.pause(0.2)
            self.assertEqual(str(toggle.label), "Stop Mining (m)")
            self.fits(app, "mining")
            await pilot.press("q")
            await pilot.pause(0.4)
            self.assertEqual([str(b.label) for b in app.screen.query(Button)],
                             ["Stop Mining and Quit", "Stay (Esc)"])
            await pilot.press("escape")
            await pilot.pause(0.2)
            await pilot.press("m")
            await self.until(pilot, lambda: not alive(pid))
            self.assertEqual(str(toggle.label), "Start Mining (m)")

    async def test_s_in_the_review_saves_once(self):
        # "Save (s)" promises the key s inside the review (forgekit presses a bracketed letter)
        from bitlaforge import backups
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            app.query_one("#row-threads").control.set_value(1)
            await pilot.pause(0.3)
            await pilot.press("f10")
            await pilot.pause(0.4)
            self.assertEqual(type(app.screen).__name__, "ReviewDialog")
            await pilot.press("s")
            await pilot.pause(0.5)
            self.assertEqual(len(app.screen_stack), 1, "the review closed, no second one")
        self.assertEqual(app.saves, 1)
        self.assertIn("threads = 1", self.cfg.read_text())
        self.assertEqual(len(backups.list_all(path=self.cfg)), 1)


class Closing(Base):
    async def test_a_timer_while_closing_does_no_harm(self):
        # found by the 1.1.0 tests: the 1-second refresh could fire while bitlaForge was
        # closing and its screens were half gone, and end the run with an error
        from bitlaforge.ui.dashboard import DashboardScreen
        app = self.app()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await app.query_one(DashboardScreen).remove_children()
            app._tick()
            app._odds_done(None, "")


class CommandLine(unittest.TestCase):
    def test_hypeforge_in_any_case_and_hidden(self):
        from bitlaforge.cli import main, parser
        for flag in ("--hypeforge", "--hypeForge"):
            args, unknown = parser().parse_known_args([flag])
            self.assertTrue(args.hypeforge, flag)
            self.assertEqual(unknown, [])
        self.assertFalse(parser().parse_known_args([])[0].hypeforge)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["--help"]), 0)
        self.assertNotIn("hypeforge", out.getvalue().lower())
        page = (Path(__file__).resolve().parent.parent / "bitlaforge.1").read_text()
        self.assertNotIn("hypeforge", page.lower(), "the man page leaves it out too")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--hype"]), 2, "no shortened spellings")

    def test_the_flag_reaches_the_app(self):
        import bitlaforge.app as app_mod
        import bitlaforge.cli as cli
        made = []

        class Stand:
            def __init__(self, **kw):
                made.append(kw)
                self.mined, self.saves, self.started = [], 0, __import__("datetime").datetime.now()
                self.config = type("C", (), {"change_count": 0})()
                self.miner = type("M", (), {"stop_now": lambda self: None})()

            def run(self):
                pass
        real, log_dir = app_mod.BitlaForgeApp, cli.LOG_DIR
        app_mod.BitlaForgeApp, cli.LOG_DIR = Stand, tempfile.mkdtemp()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["--hypeForge"]), 0)
                self.assertEqual(cli.main([]), 0)
        finally:
            app_mod.BitlaForgeApp, cli.LOG_DIR = real, log_dir
        self.assertEqual([m.get("hypeforge") for m in made], [True, False])


if __name__ == "__main__":
    unittest.main()
