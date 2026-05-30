"""BitlaForge — Setup screen.

The user-facing complement to the Dashboard banner: a permanent home for
the "you need to install minerd" guidance. Shows current minerd status,
lists every AUR provider with a copy-pasteable install command, links to
the config file path, and offers a "test minerd" button that runs
``minerd --version`` and shows the output.
"""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Label, Static, Button
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer

from ..config_manager import CONFIG_PATH
from ..widgets.status import StatusMixin
# Note: find_minerd is imported lazily inside the methods that use it so
# tests can monkey-patch bitlaforge.miner_runner.find_minerd and have the
# new value picked up on next call (binding at module-load time would
# cache the original reference and ignore the patch).


class SetupScreen(StatusMixin, Container):
    """Install + diagnostics screen for the external minerd dependency."""

    STATUS_WIDGET_ID = "setup-status"
    # Focus the scroll container, not a Button — same reason as Log / Config:
    # keeps digit keys (1/2/3/4) free to navigate.
    can_focus = True
    DEFAULT_FOCUS = "#setup"

    BINDINGS = [
        Binding("t", "test_minerd", "Test minerd", show=True),
        Binding("r", "refresh",     "Refresh",     show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="main-area"):
            yield Label("🛠   Setup — minerd install + diagnostics", classes="section-title")

            with ScrollableContainer(id="setup-scroll"):
                yield Static(id="setup-body")

            with Horizontal(classes="config-buttons"):
                yield Button("Test minerd binary", id="btn-test-minerd", classes="primary")
                yield Button("Refresh status",     id="btn-refresh-setup", classes="accent")

            yield Label("", id="setup-status")

    def on_mount(self) -> None:
        self._redraw()
        self._set_status(
            "Press T to test the installed minerd, R to re-check PATH.",
            "info", popup=False,
        )

    def on_show(self) -> None:
        self._redraw()

    def _redraw(self) -> None:
        """Re-paint the body — system info + minerd status + providers + paths.

        Named ``_redraw`` (not ``_render``) so it doesn't shadow Textual's
        internal ``Widget._render()`` — same lesson LogScreen caught in v0.1.0.
        """
        from ..miner_runner import find_minerd, MINERD_AUR_PROVIDERS
        from ..system_info import get_system_info
        info = get_system_info()
        minerd_path = find_minerd()

        # G1 (v0.1.2): system info block — what's available to mine with.
        # Refreshed on every R press so load averages stay current.
        if info.physical_cores != info.logical_cores:
            cores_str = (
                f"{info.logical_cores} logical "
                f"([dim]{info.physical_cores} physical[/])"
            )
        else:
            cores_str = f"{info.logical_cores}"

        mem_pct_used = (
            int(100 * (1 - info.mem_available_mb / info.mem_total_mb))
            if info.mem_total_mb > 0 else 0
        )
        load_color = (
            "#a6e3a1" if info.load_1 < info.logical_cores * 0.5
            else "#f9e2af" if info.load_1 < info.logical_cores * 0.9
            else "#f38ba8"
        )

        system_block = (
            f"  [#89b4fa]Host[/]         [#cdd6f4]{info.hostname}[/]\n"
            f"  [#89b4fa]CPU[/]          [#cdd6f4]{info.cpu_model}[/]\n"
            f"  [#89b4fa]Cores[/]        [#cdd6f4]{cores_str}[/]\n"
            f"  [#89b4fa]Memory[/]       "
            f"[#cdd6f4]{info.mem_available_mb / 1024:.1f} GB free "
            f"of {info.mem_total_mb / 1024:.1f} GB[/]  "
            f"[dim]({mem_pct_used}% used)[/]\n"
            f"  [#89b4fa]Load avg[/]     "
            f"[{load_color}]{info.load_1:.2f}[/]  "
            f"[dim]{info.load_5:.2f} (5m)  {info.load_15:.2f} (15m)[/]\n"
        )
        if minerd_path:
            status_block = (
                "[bold #a6e3a1]✓ minerd is installed[/]\n"
                f"  [#89b4fa]Path:[/]  [#cdd6f4]{minerd_path}[/]\n"
                "\n"
                "[#a6adc8]Press [bold #b4befe]T[/] to run `minerd --version` "
                "and verify the binary responds.[/]\n"
            )
        else:
            status_block = (
                "[bold #f38ba8]✗ minerd is not installed[/]\n"
                "  [#a6adc8]No `minerd` binary on PATH. BitlaForge can browse,\n"
                "  configure, and exercise its UI, but pressing M won't actually\n"
                "  start a miner until one of the AUR packages below is in.[/]\n"
            )

        providers_block = "\n".join(
            f"  [#cba6f7]{pkg:18s}[/]  [#a6adc8]{desc}[/]\n"
            f"    [#6c7086]install:[/]  [#cdd6f4]yay -S {pkg}[/]"
            for pkg, desc in MINERD_AUR_PROVIDERS
        )

        body = (
            "\n"
            "[bold #cba6f7]── System info ────────────────────────────────────[/]\n"
            "\n"
            f"{system_block}"
            "\n"
            "[bold #cba6f7]── minerd status ──────────────────────────────────[/]\n"
            "\n"
            f"{status_block}"
            "\n"
            "[bold #cba6f7]── About minerd ───────────────────────────────────[/]\n"
            "\n"
            "  [#cdd6f4]minerd[/] is the CPU mining binary BitlaForge wraps.\n"
            "  It is [bold]not[/] in the official Arch repos — only on the AUR,\n"
            "  with several variants. BitlaForge calls whichever one provides\n"
            "  /usr/bin/minerd, so any of these works.\n"
            "\n"
            "[bold #cba6f7]── AUR providers ─────────────────────────────────[/]\n"
            "\n"
            f"{providers_block}\n"
            "\n"
            "[bold #cba6f7]── Paths ─────────────────────────────────────────[/]\n"
            "\n"
            f"  [#89b4fa]Config[/]      [#cdd6f4]{CONFIG_PATH}[/]\n"
            "  [#89b4fa]minerd[/]      [#cdd6f4]/usr/bin/minerd[/]  "
            "[#6c7086](provided by whichever cpuminer package above)[/]\n"
            "\n"
            "[bold #cba6f7]── Safety ────────────────────────────────────────[/]\n"
            "\n"
            "  Mining draws real CPU and electricity. BitlaForge will never\n"
            "  start [bold]minerd[/] without an explicit [bold #b4befe]M[/] press,\n"
            "  and a second [bold #b4befe]M[/] always stops it cleanly.\n"
        )
        self.query_one("#setup-body", Static).update(body)

    # ── Actions ───────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-test-minerd":
            self.action_test_minerd()
        elif event.button.id == "btn-refresh-setup":
            self.action_refresh()

    async def action_test_minerd(self) -> None:
        """Run `minerd --version` and surface the result in the status line."""
        from ..miner_runner import find_minerd
        minerd_path = find_minerd()
        if minerd_path is None:
            self._set_status(
                "Can't test — minerd is not on PATH. Install one of the AUR "
                "providers above first.",
                "warn",
            )
            return

        try:
            proc = await asyncio.create_subprocess_exec(
                minerd_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            text = out.decode("utf-8", errors="replace").strip()
            # Show only the first line so the status line stays sane.
            first_line = text.splitlines()[0] if text else "(no output)"
            self._set_status(
                f"minerd {first_line[:120]}", "ok",
            )
        except asyncio.TimeoutError:
            self._set_status("minerd --version timed out after 5s.", "error")
        except OSError as e:
            self._set_status(f"Couldn't exec minerd: {e}", "error")

    def action_refresh(self) -> None:
        from ..miner_runner import find_minerd
        self._redraw()
        self._set_status(
            f"PATH re-checked — minerd {'detected' if find_minerd() else 'still missing'}.",
            "info",
        )
