"""BitlaForge — main TUI application.

A Catppuccin Mocha Textual TUI that wraps `minerd` for solo Bitcoin mining
("the lottery"). Sidebar navigation + ContentSwitcher screen routing,
ported from alacrittyForge v0.1.1's hardened App.

v0.1.0 is the skeleton — screens compose, nav works, help/confirm dialogs
work, but **`minerd` subprocess integration is NOT yet wired**. The M key
toggles a state flag (`miner_running`) so the UI surfaces the eventual
control loop; v0.1.1 replaces the stub with a real
`asyncio.create_subprocess_exec` lifecycle that streams stdout into the
Log screen and updates Dashboard fields.
"""

from pathlib import Path

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Label, ContentSwitcher
from textual.containers import Horizontal, Vertical

from .screens.dashboard import DashboardScreen
from .screens.log import LogScreen
from .screens.config import ConfigScreen
from .widgets.help_screen import HelpScreen


# Sidebar nav order: matches the digit-key bindings.
NAV_ITEMS = [
    ("1", "dashboard", "🏠  Dashboard"),
    ("2", "log",       "📜  Log"),
    ("3", "config",    "⚙   Config"),
]


class BitlaForgeApp(App):
    """BitlaForge — solo Bitcoin mining TUI."""

    TITLE = "BitlaForge"
    CSS_PATH = Path(__file__).parent / "bitlaforge.css"

    BINDINGS = [
        Binding("1", "show_screen('dashboard')", "Dashboard",  show=True),
        Binding("2", "show_screen('log')",       "Log",        show=True),
        Binding("3", "show_screen('config')",    "Config",     show=True),
        # M for Miner toggle (S is reserved for screen-level Save on Config,
        # mirroring the alacrittyForge / grubForge convention).
        Binding("m", "toggle_miner",             "Start/Stop", show=True),
        Binding("r", "refresh_active",           "Refresh",    show=False),
        Binding("q", "quit",                     "Quit",       show=True),
        Binding("question_mark", "show_help",    "Help",       show=True),
    ]

    # Reactive-ish: the M toggle flips this; screens read it to render state.
    miner_running: bool = False
    _current_screen: str = "dashboard"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal():
            with Vertical(classes="sidebar"):
                yield Label("⚡ BitlaForge", classes="sidebar-title")
                yield Label("[dim]Solo Bitcoin lottery[/]", classes="sidebar-subtitle")
                for key, sid, label in NAV_ITEMS:
                    active_cls = "nav-item --active" if sid == "dashboard" else "nav-item"
                    yield Label(f"{key}  {label}", id=f"nav-{sid}", classes=active_cls)
                yield Label("", classes="sidebar-spacer")
                yield Label(
                    "[dim]M start/stop  •  ? help  •  q quit[/]",
                    classes="sidebar-footer",
                )
            with ContentSwitcher(initial="dashboard", id="content"):
                yield DashboardScreen(id="dashboard")
                yield LogScreen(id="log")
                yield ConfigScreen(id="config")
        yield Footer()

    def on_mount(self) -> None:
        """Land initial focus on the Dashboard.

        Without this, Textual auto-focuses the first focusable widget in
        the DOM — which is Log's search Input — and every character key
        (1, 2, 3, m, …) gets typed into the input instead of firing the
        app-level bindings. Dashboard is set to ``can_focus = True`` so it
        accepts focus and bubbles character keys back up to the app.
        """
        try:
            self.query_one("#dashboard").focus()
        except Exception:
            pass

    def on_click(self, event: events.Click) -> None:
        """Route sidebar nav-item clicks to action_show_screen.

        Mirrors the grubForge sidebar click pattern. Catches the click on
        whichever Label has id ``nav-<screen>`` and switches to that screen.
        """
        wid = getattr(event.widget, "id", "") or ""
        if wid.startswith("nav-"):
            self.action_show_screen(wid[4:])

    # ── Screen switching ──────────────────────────────────────────────────

    def action_show_screen(self, screen_id: str) -> None:
        """Switch the visible screen, update sidebar highlight, refresh data."""
        self._current_screen = screen_id
        self.query_one("#content", ContentSwitcher).current = screen_id
        self._update_nav(screen_id)

        try:
            screen = self.query_one(f"#{screen_id}")
        except Exception:
            return

        # Refresh-on-show — silent path (alacrittyForge G1 lesson).
        if hasattr(screen, "on_show"):
            try:
                screen.on_show()
            except Exception:
                pass

        # Focus the screen's primary widget so its bindings fire on entry
        # without a panel click (alacrittyForge G4 / grubForge F15).
        focus_id = getattr(screen, "DEFAULT_FOCUS", None)
        if focus_id:
            try:
                self.query_one(focus_id).focus()
            except Exception:
                pass

    def _update_nav(self, active_id: str) -> None:
        for _, sid, _ in NAV_ITEMS:
            try:
                lbl = self.query_one(f"#nav-{sid}", Label)
                classes = set(lbl.classes)
                classes.discard("--active")
                if sid == active_id:
                    classes.add("--active")
                lbl.set_classes(" ".join(classes))
            except Exception:
                pass

    # ── Actions ───────────────────────────────────────────────────────────

    def action_toggle_miner(self) -> None:
        """Toggle the miner state.

        v0.1.0 stub — just flips `miner_running` and notifies. v0.1.1
        replaces this with a real `asyncio.create_subprocess_exec` lifecycle
        that spawns `minerd`, pipes stdout into the Log screen via
        `LogScreen.append_line`, and stops it cleanly on toggle-off.
        """
        self.miner_running = not self.miner_running
        if self.miner_running:
            self.notify(
                "Miner started (stub — minerd integration lands in v0.1.1).",
                severity="information", timeout=4,
            )
        else:
            self.notify("Miner stopped.", severity="information", timeout=4)

        # Re-render Dashboard so the state header updates.
        try:
            self.query_one("#dashboard")._reload_view()
        except Exception:
            pass

    def action_refresh_active(self) -> None:
        """R — dispatch refresh to the active screen if it has action_refresh."""
        try:
            screen = self.query_one(f"#{self._current_screen}")
            fn = getattr(screen, "action_refresh", None)
            if callable(fn):
                fn()
        except Exception:
            pass

    def action_show_help(self) -> None:
        """Toggle the help overlay (pops if open, pushes otherwise)."""
        if isinstance(self.screen, HelpScreen):
            self.pop_screen()
        else:
            self.push_screen(HelpScreen())
