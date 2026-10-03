"""bitlaForge v1.0.0 — the app frame, on forgekit.

The frame is forgekit's (title bar, menu bar, changes bar, hint bar); the
screens are bitlaForge's. Javier's rulings for 1.0.0 (2 Oct 2026,
docs/design/v1.0.0-screens.html): four screens (Dashboard, Settings, Log,
History); Bitcoin only; pause when hot; honest odds from mempool.space; and
closing bitlaForge always stops the miner, after asking.
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import time

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.widgets import Button, Static

from forgekit import (
    FORGE_CSS, GPL3_NOTICE, ChangeGroup, ForgeApp, ForgeModal, ManualScreen, Notice, ReviewDialog,
    SettingRow, load_pages,
)

from . import __version__, backups, heat, history, odds
from .miner import ALGORITHM, Event, Miner, find_minerd, read_line, speed
from .process_stats import compute_cpu_pct, read_process_sample
from .settings import BY_KEY, Config
from .ui.dashboard import DashboardScreen
from .ui.history import HistoryScreen
from .ui.log import LogScreen
from .ui.settings import SettingsScreen

MANUAL_DIR = os.path.join(os.path.dirname(__file__), "manual")

BF_CSS = FORGE_CSS + """
/* bitlaForge's own sections, coloured only through forgekit's roles */
#bf-dash { grid-size: 2 2; grid-columns: 1fr 1fr; grid-rows: auto auto; grid-gutter: 1 2; height: auto; padding: 0 2 0 0; }
.bf-box { height: auto; border: round $forge-border; border-title-color: $forge-accent; border-title-style: bold; padding: 0 1; }
.bf-box-buttons { padding: 1 0 0 0; align-horizontal: left; height: auto; }
.bf-box-buttons Button { margin: 0 2 0 0; width: auto; min-width: 0; padding: 0 2; }
#db-fixes { padding: 0; }
#bf-groups { width: 20; height: 1fr; border: none; border-right: solid $forge-border; background: $forge-bg; padding: 1 1 0 0; }
#bf-settings-right { width: 1fr; height: 1fr; padding: 0 0 0 2; }
#bf-groupforms { height: 1fr; }
.bf-group { height: 1fr; padding: 0 1 0 0; }
.bf-group-title { height: auto; margin: 0 0 1 0; }
#bf-wallet-check { height: auto; padding: 0 0 0 18; }
#bf-about { height: auto; min-height: 4; max-height: 7; padding: 1 0 0 0; color: $forge-text; }
#sec-log { padding: 0 2 0 0; }
#lg-bar { height: 3; }
.lg-label { width: auto; height: 3; content-align: left middle; color: $forge-muted; padding: 0 1 0 0; }
#lg-show { width: 18; }
#lg-find { width: 1fr; margin: 0 2 0 0; }
#lg-follow { width: auto; height: 3; content-align: left middle; }
#lg-lines { height: 1fr; border: solid $forge-field-border; background: $forge-bg; }
#lg-lines:focus { border: solid $forge-accent; }
.lg-actions { padding: 1 0 0 0; align-horizontal: left; height: auto; }
.lg-actions Button { margin: 0 2 0 0; }
#sec-history { padding: 0 2 0 0; }
#hs-table { height: auto; max-height: 16; border: solid $forge-field-border; background: $forge-bg; }
#hs-table:focus { border: solid $forge-accent; }
#hs-totals { height: auto; padding: 1 0 0 0; }
#bf-quit-msg { height: auto; padding: 0 0 1 0; }
"""


class QuitDialog(ForgeModal[str | None]):
    """Before you go: the miner is running, or something isn't saved."""

    BINDINGS = [Binding("escape", "stay", "", show=False)]

    def __init__(self, heading: str, lines: list[str], buttons: list[tuple[str, str, bool]]) -> None:
        super().__init__()
        self._heading, self._lines, self._buttons = heading, lines, buttons

    def compose(self) -> ComposeResult:
        with Vertical(classes="forge-panel"):
            yield Static("Before you go", classes="forge-panel-title")
            yield Notice(self._heading, self._lines, level="warn", id="bf-quit-msg")
            with Horizontal(classes="forge-buttons forge-panel-footer"):
                for label, bid, primary in self._buttons:
                    yield Button(label, id=bid, variant="primary" if primary else "default")
                yield Button("Stay", id="stay")

    def on_mount(self) -> None:
        self.query_one(f"#{self._buttons[0][1]}", Button).focus()

    def on_button_pressed(self, e: Button.Pressed) -> None:
        e.stop()
        self.dismiss(None if e.button.id == "stay" else e.button.id)

    def action_stay(self) -> None:
        self.dismiss(None)


def minerd_version(binary: str | None) -> str:
    if not binary:
        return ""
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=5)
        first = (out.stdout or out.stderr).splitlines()[0].strip()
        return first if first else "minerd"
    except (OSError, subprocess.SubprocessError, IndexError):
        return "minerd"


class BitlaForgeApp(ForgeApp):
    APP_NAME = f"bitlaForge {__version__} · solo Bitcoin mining"
    SHOW_HINT_BAR = True
    SHOW_CHANGES_BAR = True
    CSS = BF_CSS
    LICENSE_NOTICE = GPL3_NOTICE
    MENU = [
        {"id": "dashboard", "title": "Dashboard", "kind": "section"},
        {"id": "settings", "title": "Settings", "kind": "section", "acc": "e"},
        {"id": "log", "title": "Log", "kind": "section"},
        {"id": "history", "title": "History", "kind": "section", "acc": "y"},
        {"id": "help", "title": "Help", "kind": "menu", "items": [
            ("Manual", "m", "manual"), ("Keys", "k", "shortcuts"),
            ("License", "l", "license"), ("About", "a", "about")]},
        {"id": "quit", "title": "Quit", "kind": "action", "action": "quit"},
    ]
    SHORTCUTS = [
        ("M", "start or stop mining"),
        ("T", "test the miner (10 seconds, one core, nothing sent)"),
        ("Tab / Shift+Tab", "next / previous field or button"),
        ("Enter", "open a list, press a button, confirm"),
        ("Space", "flip a switch"),
        ("↑↓ in a number", "step through its presets"),
        ("Esc", "close a window, or leave a field"),
        ("1-4, Ctrl+letter", "go to a screen (the underlined letter)"),
        ("F10 or S", "save settings, with a review first"),
        ("R", "read the settings file again"),
        ("F1", "help on what is selected"),
        ("/  F  C", "in the Log: find, follow, clear"),
        ("?", "this list"),
        ("Q or Ctrl+Q", "quit (stops the miner, after asking)"),
    ]
    HINTS = [("M", "start / stop"), ("1-4", "screens"), ("F10", "save"), ("F1", "help"), ("?", "all keys")]
    BINDINGS = [
        Binding("1", "go('dashboard')", show=False), Binding("2", "go('settings')", show=False),
        Binding("3", "go('log')", show=False), Binding("4", "go('history')", show=False),
        Binding("ctrl+d", "go('dashboard')", show=False), Binding("ctrl+e", "go('settings')", show=False),
        Binding("ctrl+l", "go('log')", show=False), Binding("ctrl+y", "go('history')", show=False),
        Binding("m", "toggle_mining", show=False), Binding("t", "test_miner", show=False),
        Binding("f10", "save", show=False, priority=True), Binding("s", "save", show=False),
        Binding("r", "reload", show=False),
        Binding("f1", "field_help", show=False, priority=True),
        Binding("question_mark", "act('shortcuts')", show=False),
        Binding("q", "act('quit')", show=False),
    ]

    def __init__(self, config: Config | None = None, *, history_path=None, network_cache=None,
                 hwmon=None, **kw) -> None:
        self.config = config or Config.load()
        self.history_path = history_path or history.PATH
        self.network_cache = network_cache or odds.CACHE
        self.hwmon = hwmon or heat.HWMON
        self.miner = Miner(self._on_event, self._on_miner_change)
        self.minerd = find_minerd()
        self.testing = False
        self.network = odds.load(self.network_cache)
        self.network_error = ""
        self.temp = heat.processor_temp(self.hwmon)
        self.cpu_cores = 0.0
        self.saves = 0
        self.mined: list[history.Session] = []          # sessions this run, for the closing note
        self.started = __import__("datetime").datetime.now()
        self._session: history.Session | None = None
        self._sample = None
        self._sessions = None
        self._fetching = False
        self.closed_unexpectedly = history.close_unfinished(self.history_path)
        self.ABOUT = {
            "name": "bitlaForge", "version": __version__,
            "tagline": "Solo Bitcoin mining, honestly framed",
            "description": "Part of the Forge Suite for KognogOS. Runs cpuminer's minerd; never starts it on "
                           "its own.",
            "authors": "jetomev (Javier) · Claude (Anthropic), co-developer",
            "license": "GPL-3.0-or-later",
            "links": [("Code", "https://github.com/jetomev/bitlaforge")],
        }
        super().__init__(**kw)

    def compose_sections(self) -> ComposeResult:
        yield DashboardScreen(id="sec-dashboard")
        yield SettingsScreen(id="sec-settings")
        yield LogScreen(id="sec-log")
        yield HistoryScreen(id="sec-history")

    def on_mount(self) -> None:
        super().on_mount()
        if self.closed_unexpectedly:
            self.notify("The last mining session ended without bitlaForge (the computer was switched off, or "
                        "bitlaForge was stopped). It's in History.", timeout=8)
        version = minerd_version(self.minerd)
        self.set_title_status(f"{socket.gethostname()} · {version or 'the miner is not installed'}")
        self.set_interval(1, self._tick)
        self.set_interval(5, self._heat_tick)
        self.set_interval(60, self._minute)
        self.set_interval(300, self.fetch_odds)
        self.fetch_odds()
        self.refresh_state()

    # ── what the screens ask ─────────────────────────────────────────────────
    def not_ready(self) -> list[str]:
        out = self.config.not_ready()
        if self.minerd is None:
            out.append("The miner (minerd) isn't installed.")
        return out

    def has_backups(self) -> bool:
        return bool(backups.list_all(path=self.config.path, backup_dir=self.config.backup_dir))

    def sessions(self) -> list[history.Session]:
        if self._sessions is None:
            self._sessions = history.load(self.history_path)
        return self._sessions

    def totals(self) -> history.Totals:
        """Since you started, the session being mined included as it is now."""
        rows = self.sessions()
        if self._session is not None:
            st = self.miner.stats
            live = history.Session(self._session.started, st.seconds, st.average_khs, st.accepted, st.rejected)
            rows = [r for r in rows if r.started != live.started] + [live]
        return history.totals(rows)

    def last_average(self) -> float:
        return next((s.average_khs for s in self.sessions() if s.average_khs), 0.0)

    def _record(self, s: history.Session) -> None:
        history.record(s, self.history_path)
        self._sessions = None

    # ── navigation ───────────────────────────────────────────────────────────
    def action_go(self, section: str) -> None:
        self._switch_section(section)

    def on_section_shown(self, section_id: str) -> None:
        if section_id == "dashboard":
            self.query_one(DashboardScreen).refresh_view()
        elif section_id == "settings":
            self.query_one("#bf-groups").focus()
        elif section_id == "log":
            self.query_one("#lg-lines").focus()
        elif section_id == "history":
            self.query_one(HistoryScreen).refresh_view()
            self.query_one("#hs-table").focus()

    def on_action(self, action_id: str) -> None:
        if action_id == "manual":
            self.open_manual()

    def open_manual(self, page: str | None = None) -> None:
        pages = load_pages(MANUAL_DIR) if os.path.isdir(MANUAL_DIR) else []
        if not pages:
            self.notify("The manual isn't there.", severity="warning")
            return
        self.push_screen(ManualScreen("bitlaForge manual", pages, start=page))

    def action_field_help(self) -> None:
        w = self.focused
        row = next((a for a in (w.ancestors_with_self if w else []) if isinstance(a, SettingRow)), None)
        if row is not None:
            self.open_manual(BY_KEY[row.setting].group)
        elif w is not None and any(a.id == "sec-log" for a in w.ancestors_with_self):
            self.open_manual("log")
        elif w is not None and any(a.id == "sec-history" for a in w.ancestors_with_self):
            self.open_manual("log")
        else:
            self.open_manual("dashboard")

    # ── the changes bar ──────────────────────────────────────────────────────
    def refresh_state(self) -> None:
        n, bar = self.config.change_count, self.changes_bar
        if n:
            bar.show(f"{n} change{'s' if n != 1 else ''} not saved yet", "changed",
                     [("Save…  F10", "bf-save", True), ("Discard", "bf-discard", False)])
        else:
            bar.hide()
        self.query_one(DashboardScreen).refresh_view()

    def on_button_pressed(self, e: Button.Pressed) -> None:
        bid = e.button.id or ""
        if bid == "bf-save":
            self.action_save()
        elif bid == "bf-discard":
            self.config.discard()
            self.query_one(SettingsScreen).sync()
            self.refresh_state()
            self.notify("Changes discarded. Nothing was written.")
        elif bid == "db-toggle":
            self.action_toggle_mining()
        elif bid == "db-test":
            self.action_test_miner()
        elif bid == "db-wallet":
            self._switch_section("settings")
            self.query_one(SettingsScreen).focus_setting("wallet")
        elif bid == "db-restore":
            self.restore_newest()
        elif bid == "db-install":
            self.open_manual("install")

    # ── mining ───────────────────────────────────────────────────────────────
    @work(exclusive=True, group="bf-mining")
    async def action_toggle_mining(self) -> None:
        if self.miner.running:
            await self.miner.stop("you stopped it")
            return
        self.minerd = find_minerd()
        problems = self.not_ready()
        if problems:
            self.notify("\n".join(problems), title="Can't start mining yet", severity="warning", timeout=10)
            self.query_one(DashboardScreen).refresh_view()
            return
        if self.testing:
            self.notify("The miner test is still running; try again in a few seconds.")
            return
        values = {s: self.config.original(s) for s in ("pool", "wallet", "miner_name", "threads", "niceness")}
        why = await self.miner.start(values, self.minerd)
        if why:
            self.notify(why, title="Mining didn't start", severity="error", timeout=10)
            return
        self._session = history.Session(started=self.miner.stats.started)
        self._record(self._session)
        self._sample = None
        if self.config.change_count:
            self.notify("Mining with the saved settings; your unsaved changes apply after you save and "
                        "start again.", timeout=8)
        self.fetch_odds()

    def _on_event(self, e: Event) -> None:
        try:
            self.query_one(LogScreen).add(e)
        except NoMatches:              # bitlaForge is closing: the screens are gone
            pass

    def _note(self, kind: str, text: str) -> None:
        self._on_event(Event(time.strftime("%H:%M:%S"), kind, text, text))

    def _on_miner_change(self) -> None:
        st = self.miner.stats
        if not st.running and self._session is not None:
            self._finish_session()
            self._note("info", f"stopped: {st.why_stopped}")
            if st.why_stopped.startswith("the miner stopped by itself"):
                self.notify("The miner stopped by itself. The Log shows its last words.",
                            title="Mining stopped", severity="warning", timeout=10)
        try:
            self.query_one(DashboardScreen).refresh_view()
        except NoMatches:
            pass

    def _update_session(self) -> None:
        s, st = self._session, self.miner.stats
        if s is None:
            return
        s.seconds, s.accepted, s.rejected = st.seconds, st.accepted, st.rejected
        s.average_khs = round(st.average_khs, 1)

    def _finish_session(self) -> None:
        self._update_session()
        s = self._session
        s.why = self.miner.stats.why_stopped or "stopped"
        self._record(s)
        self.mined.append(s)
        self._session = None
        try:
            self.query_one(HistoryScreen).refresh_view()
        except NoMatches:
            pass

    # ── timers ───────────────────────────────────────────────────────────────
    def _tick(self) -> None:
        pid = self.miner.pid
        if pid and not self.miner.stats.paused:
            now = read_process_sample(pid)
            if now and self._sample:
                self.cpu_cores = compute_cpu_pct(self._sample, now) / 100
            self._sample = now
        else:
            self.cpu_cores, self._sample = 0.0, None
        if self.query_one("#forge-work").current == "sec-dashboard":
            self.query_one(DashboardScreen).refresh_view()

    def _heat_tick(self) -> None:
        self.temp = heat.processor_temp(self.hwmon)
        if not self.miner.running:
            return
        limit = self.config.original("heat_limit")
        do = heat.decide(self.temp, limit, self.miner.stats.paused, self.config.original("heat_pause"))
        if do == "pause" and self.miner.pause():
            self._note("paused", f"paused: the processor reached {self.temp:.0f} °C; goes on at "
                                 f"{limit - heat.RESUME_BELOW} °C")
            self.notify(f"The processor reached {self.temp:.0f} °C, so mining is paused until it cools.",
                        title="Paused for heat", severity="warning", timeout=10)
        elif do == "resume" and self.miner.resume():
            self._note("resumed", "going on: the processor has cooled" if self.temp is not None else
                       "going on: heat is no longer watched")

    def _minute(self) -> None:
        if self.miner.running:
            self.miner.stats.tick_minute()
            self._update_session()
            if self._session:
                self._record(self._session)

    def fetch_odds(self) -> None:
        if self.config.original("odds") and odds.due(self.network) and not self._fetching:
            self._fetching = True
            self._fetch_odds()

    @work(thread=True, exclusive=True, group="bf-odds")
    def _fetch_odds(self) -> None:
        try:
            n = odds.fetch()
        except (OSError, ValueError, KeyError, IndexError) as e:
            why = getattr(e, "reason", None) or e
            self.call_from_thread(self._odds_done, None,
                                  f"mempool.space can't be reached right now ({why}); trying again later.")
            return
        self.call_from_thread(self._odds_done, n, "")

    def _odds_done(self, n, error: str) -> None:
        self._fetching = False
        self.network_error = error
        if n is not None:
            self.network = n
            odds.save(n, self.network_cache)
        self.query_one(DashboardScreen).refresh_view()

    # ── the miner test: 10 seconds on one core, nothing sent anywhere ────────
    @work(exclusive=True, group="bf-test")
    async def action_test_miner(self) -> None:
        if self.miner.running or self.testing:
            return
        self.minerd = find_minerd()
        if not self.minerd:
            self.notify("The miner (minerd) isn't installed: Help ▸ Manual ▸ Installing the miner.",
                        title="No miner", severity="warning", timeout=10)
            self.query_one(DashboardScreen).refresh_view()
            return
        self.testing = True
        self.query_one(DashboardScreen).refresh_view()
        self.notify("Testing the miner: 10 seconds on one core, without a pool. Nothing is sent anywhere.")
        best = 0.0
        try:
            proc = await asyncio.create_subprocess_exec(
                self.minerd, "--benchmark", "-a", ALGORITHM, "-t", "1", stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            end = time.time() + 10
            while time.time() < end:
                try:
                    raw = await asyncio.wait_for(proc.stdout.readline(), max(0.1, end - time.time()))
                except asyncio.TimeoutError:
                    break
                if not raw:
                    break
                e = read_line(raw.decode("utf-8", "replace").rstrip())
                if e.kind == "thread":
                    best = float(e.raw.rsplit(",", 1)[1].split()[0])
            if proc.returncode is None:
                proc.terminate()
                await proc.wait()
        except OSError as e:
            self.notify(f"The miner couldn't run: {e.strerror or e}.", title="Test failed", severity="error")
            best = -1
        finally:
            self.testing = False
            self.query_one(DashboardScreen).refresh_view()
        if best > 0:
            # only what was measured: cores that share a physical core don't double the speed
            self.notify(f"The miner works: one core does {speed(best)}. Mining shows the speed of all the "
                        "cores you use.", title="Test passed", timeout=10)
        elif best == 0:
            self.notify("The miner started but reported no speed in 10 seconds.", title="Test inconclusive",
                        severity="warning", timeout=10)

    # ── save, reload, restore ────────────────────────────────────────────────
    @work(exclusive=True, group="bf-write")
    async def action_save(self) -> None:
        c = self.config
        if not c.readable:
            self.notify("Your settings file can't be read, so it isn't saved over. Restore the newest "
                        "backup from the Dashboard, or fix the file and press R.", title="Can't save",
                        severity="warning", timeout=10)
            return
        if not c.change_count:
            self.notify("Nothing to save: no changes.")
            return
        problems = c.problems()
        if problems:
            self.notify("\n".join(problems), title="Can't save yet", severity="error", timeout=10)
            return
        path = str(c.path).replace(os.path.expanduser("~"), "~")
        steps = ["A backup of your settings is made" if c.exists else "Your settings file is created",
                 "The changes are written; everything else in the file stays"]
        if self.miner.running:
            steps.append("The miner keeps running with the old settings; stop and start it to use these")
        choice = await self.push_screen_wait(ReviewDialog(
            "Review before saving", [ChangeGroup("Settings", path, c.changes())], steps=steps,
            buttons=[("Save", "save", True)]))
        if choice is None:
            return
        try:
            c.save()
        except (ValueError, OSError) as e:
            self.notify(f"{getattr(e, 'strerror', None) or e}. Nothing was changed.", title="Not saved",
                        severity="error", timeout=10)
            return
        self.saves += 1
        self.query_one(SettingsScreen).sync()
        self.refresh_state()
        self.fetch_odds()
        self.notify("Saved." + (" Stop and start mining to use them." if self.miner.running else ""),
                    title="Saved", timeout=6)

    def action_reload(self) -> None:
        self.config.reload()
        self.query_one(SettingsScreen).sync()
        self.refresh_state()
        self.notify("Read the settings file again. Your unsaved changes are kept.")

    def restore_newest(self) -> None:
        made = backups.list_all(path=self.config.path, backup_dir=self.config.backup_dir)
        if not made:
            return
        backups.restore(made[0], path=self.config.path, backup_dir=self.config.backup_dir)
        self.config.reload()
        self.query_one(SettingsScreen).sync()
        self.refresh_state()
        self.notify(f"Restored the backup from {made[0].made:%b %-d %H:%M}. The file that couldn't be read "
                    "was backed up first.", title="Restored", timeout=8)

    # ── quitting: the miner always stops ─────────────────────────────────────
    def before_quit(self) -> bool:
        n = self.config.change_count
        unsaved = [f"{n} settings change{'s are' if n != 1 else ' is'} not saved: quitting loses "
                   f"{'them' if n != 1 else 'it'}."] if n else []
        if self.miner.running:
            self.push_screen(QuitDialog(
                "The miner is running",
                ["Closing bitlaForge stops it, so your computer doesn't keep mining with nothing on screen."]
                + unsaved, [("Stop mining and quit", "stopquit", True)]), self._after_quit_choice)
            return False
        if n:
            self.push_screen(QuitDialog(f"{n} change{'s are' if n != 1 else ' is'} not saved",
                                        ["Quitting now loses them."],
                                        [("Save first", "save", True), ("Quit without saving", "quit", False)]),
                             self._after_quit_choice)
            return False
        return True

    def _after_quit_choice(self, choice: str | None) -> None:
        if choice == "quit":
            self.exit()
        elif choice == "save":
            self.action_save()
        elif choice == "stopquit":
            self._stop_and_quit()

    @work(exclusive=True, group="bf-mining")
    async def _stop_and_quit(self) -> None:
        await self.miner.stop("bitlaForge closed")
        self.exit()

    def on_unmount(self) -> None:
        # however the app ends, the miner doesn't outlive it
        if self.miner.running:
            self.miner.stop_now()
            self.miner._finish("bitlaForge closed")
