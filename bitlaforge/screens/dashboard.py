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
        """Render the dashboard content from live MinerStats off the app."""
        from ..miner_runner import MinerStats  # local import to avoid cycle
        stats: MinerStats = getattr(self.app, "miner_stats", MinerStats())

        # State header.
        state_str = "[#a6e3a1]● running[/]" if stats.running else "[#6c7086]○ stopped[/]"

        # Pool: split off "stratum+tcp://" for readability and pull the port out.
        pool_raw = stats.pool or "—"
        if "://" in pool_raw:
            _, _, hostport = pool_raw.partition("://")
        else:
            hostport = pool_raw
        if ":" in hostport and hostport != "—":
            host, _, port = hostport.rpartition(":")
            pool_display = host or "—"
            port_display = port or "—"
        else:
            pool_display = hostport
            port_display = "—"

        wallet_display = stats.wallet if stats.wallet else "—"
        if len(wallet_display) > 42:  # truncate long Bitcoin addresses
            wallet_display = wallet_display[:18] + "…" + wallet_display[-10:]

        # Performance / session.
        hashrate_str = (
            f"{stats.hashrate_khs:.2f} kh/s" if stats.hashrate_khs > 0 else "—"
        )
        threads_str = str(stats.threads) if stats.threads > 0 else "—"
        uptime_secs = stats.uptime_seconds
        uptime_str = (
            f"{uptime_secs // 3600}h {(uptime_secs % 3600) // 60}m {uptime_secs % 60}s"
            if uptime_secs > 0 else "—"
        )
        shares_str = (
            f"{stats.accepted} accepted / {stats.rejected} rejected"
            if (stats.accepted or stats.rejected) else "— accepted / — rejected"
        )
        algo_str = stats.algorithm if stats.algorithm else "—"

        content = (
            "\n"
            f"  [#89b4fa]Miner state[/]   {state_str}\n"
            "\n"
            "[bold #cba6f7]── Pool & Wallet ────────────────────────────────[/]\n"
            "\n"
            f"  [#89b4fa]Pool          [/]  [#cdd6f4]{pool_display}[/]\n"
            f"  [#89b4fa]Port          [/]  [#cdd6f4]{port_display}[/]\n"
            f"  [#89b4fa]Wallet        [/]  [#cdd6f4]{wallet_display}[/]\n"
            f"  [#89b4fa]Algorithm     [/]  [#cdd6f4]{algo_str}[/]\n"
            "\n"
            "[bold #cba6f7]── Performance ──────────────────────────────────[/]\n"
            "\n"
            f"  [#89b4fa]Threads       [/]  [#cdd6f4]{threads_str}[/]\n"
            f"  [#89b4fa]Hashrate      [/]  [#cdd6f4]{hashrate_str}[/]\n"
            "\n"
            "[bold #cba6f7]── Session ──────────────────────────────────────[/]\n"
            "\n"
            f"  [#89b4fa]Uptime        [/]  [#cdd6f4]{uptime_str}[/]\n"
            f"  [#89b4fa]Shares        [/]  [#cdd6f4]{shares_str}[/]\n"
            "\n"
            "[bold #cba6f7]── Quick Actions ────────────────────────────────[/]\n"
            "\n"
            "  Press [bold #b4befe]M[/]  to start/stop the miner\n"
            "  Press [bold #b4befe]3[/]  to edit miner configuration\n"
            "  Press [bold #b4befe]2[/]  to watch the log stream\n"
            "  Press [bold #b4befe]?[/]  for help\n"
        )
        self.query_one("#dashboard-content", Static).update(content)

    def action_refresh(self) -> None:
        self._reload_view()
        self._set_status("Dashboard refreshed.", "info")
