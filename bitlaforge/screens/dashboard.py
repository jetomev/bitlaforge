"""BitlaForge — Dashboard screen.

Read-only overview of miner state. v0.1.0 is a stub: every field renders
its label and a placeholder value (— / stopped). The Phase B / v0.1.1
cycle replaces the placeholders with real values pulled from the minerd
subprocess.

Field surface carried forward from the Qt scaffold (it functioned as a
design doc):
    pool name + port, wallet, CPU load, threads, uptime, hashrate,
    shares (accepted/rejected), log line count.
"""

from textual.app import ComposeResult
from textual.widgets import Label, Static
from textual.containers import Container, Vertical

from ..widgets.status import StatusMixin


class DashboardScreen(StatusMixin, Container):
    """Miner overview — populated by the minerd subprocess once wired."""

    # No in-screen status line; action_refresh feedback goes to a toast
    # (mirrors alacrittyForge / grubForge's Dashboard pattern).
    STATUS_WIDGET_ID = None

    # Focusable so the app can place initial focus here at startup —
    # otherwise Textual auto-focuses the first focusable widget across
    # the whole DOM, which is Log's search Input, and 1/2/3/M get typed
    # into the input instead of triggering app bindings.
    can_focus = True
    DEFAULT_FOCUS = "#dashboard"

    def compose(self) -> ComposeResult:
        with Vertical(classes="main-area"):
            yield Label("⚡  BitlaForge — Miner Overview", classes="section-title")
            yield Static(id="dashboard-content")

    def on_mount(self) -> None:
        self._reload_view()

    def on_show(self) -> None:
        # G1 lesson from alacrittyForge — on_show is the silent path. The
        # real refresh wiring lands once minerd subprocess state exists.
        self._reload_view()

    def _reload_view(self) -> None:
        """Render the dashboard content. v0.1.0 stub — placeholder fields."""
        # Read miner_running off the app so the header reflects the M toggle.
        running = getattr(self.app, "miner_running", False)
        state_str = "[#a6e3a1]● running[/]" if running else "[#6c7086]○ stopped[/]"

        content = (
            "\n"
            f"  [#89b4fa]Miner state[/]   {state_str}\n"
            "\n"
            "[bold #cba6f7]── Pool & Wallet ────────────────────────────────[/]\n"
            "\n"
            "  [#89b4fa]Pool          [/]  [#6c7086]— (configure on Config screen)[/]\n"
            "  [#89b4fa]Port          [/]  [#6c7086]—[/]\n"
            "  [#89b4fa]Wallet        [/]  [#6c7086]—[/]\n"
            "\n"
            "[bold #cba6f7]── Performance ──────────────────────────────────[/]\n"
            "\n"
            "  [#89b4fa]CPU load      [/]  [#6c7086]—[/]\n"
            "  [#89b4fa]Threads       [/]  [#6c7086]—[/]\n"
            "  [#89b4fa]Hashrate      [/]  [#6c7086]—[/]\n"
            "\n"
            "[bold #cba6f7]── Session ──────────────────────────────────────[/]\n"
            "\n"
            "  [#89b4fa]Uptime        [/]  [#6c7086]—[/]\n"
            "  [#89b4fa]Shares        [/]  [#6c7086]— accepted / — rejected[/]\n"
            "  [#89b4fa]Log lines     [/]  [#6c7086]0[/]\n"
            "\n"
            "[bold #cba6f7]── Quick Actions ────────────────────────────────[/]\n"
            "\n"
            "  Press [bold #b4befe]M[/]  to start/stop the miner\n"
            "  Press [bold #b4befe]3[/]  to edit miner configuration\n"
            "  Press [bold #b4befe]2[/]  to watch the log stream\n"
            "  Press [bold #b4befe]?[/]  for help\n"
            "\n"
            "[dim italic]  ↳ v0.1.0 alpha: all fields are placeholders;\n"
            "    real minerd integration lands in v0.1.1.[/]\n"
        )
        self.query_one("#dashboard-content", Static).update(content)

    def action_refresh(self) -> None:
        self._reload_view()
        self._set_status("Dashboard refreshed.", "info")
