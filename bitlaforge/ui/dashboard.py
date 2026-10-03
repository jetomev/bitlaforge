"""Dashboard — is it mining, how fast, is it safe, what are my chances? (v1.0.0)

Four boxes, like grubForge's Overview: Mining · Speed · The lottery · Heat &
load. Anything stopping mining shows in the Mining box with the button that
fixes it. The miner only ever starts when you press M.
"""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static

from forgekit import glyph
from forgekit.console import is_console

from .. import history, odds, pools
from ..heat import RESUME_BELOW
from ..miner import speed
from ..settings import CORES, GENTLE, words

FINE = "▁▂▃▄▅▆▇█"
CONSOLE = "░▒▓█"


def bars(values: list[float], width: int, floor: float = 0.0) -> str:
    """A small chart: one character per value, the highest one full. ``floor``
    is the share of the top the chart starts from: 0 for an honest bar per core,
    0.5 for speed over time, so a pause or a slowdown stays visible."""
    steps = CONSOLE if is_console() else FINE
    vals = values[-width:]
    top = max(vals, default=0)
    if top <= 0:
        return ""
    low = top * floor
    out = []
    for v in vals:
        frac = max(0.0, (v - low) / (top - low))
        out.append(steps[min(len(steps) - 1, int(frac * (len(steps) - 1) + 0.5))])
    return "".join(out)


def ago(seconds: float) -> str:
    return history.duration(int(seconds))


class DashboardScreen(VerticalScroll, can_focus=False):
    FORGE_HINTS = [("M", "start / stop"), ("T", "test"), ("1-4", "screens"), ("F1", "help"), ("?", "all keys")]

    def compose(self) -> ComposeResult:
        with Grid(id="bf-dash"):
            with Vertical(classes="bf-box", id="box-mining"):
                yield Static("", id="db-mining")
                with Horizontal(classes="forge-buttons bf-box-buttons"):
                    yield Button("Start mining", id="db-toggle", variant="primary")
                    yield Button("Test the miner", id="db-test")
                with Horizontal(classes="forge-buttons bf-box-buttons", id="db-fixes"):
                    yield Button("Add your wallet", id="db-wallet", variant="primary")
                    yield Button("Restore the newest backup", id="db-restore", variant="primary")
                    yield Button("How to install the miner", id="db-install", variant="primary")
            with Vertical(classes="bf-box", id="box-speed"):
                yield Static("", id="db-speed")
            with Vertical(classes="bf-box", id="box-odds"):
                yield Static("", id="db-odds")
            with Vertical(classes="bf-box", id="box-heat"):
                yield Static("", id="db-heat")

    def on_mount(self) -> None:
        for box, title in (("box-mining", "Mining"), ("box-speed", "Speed"), ("box-odds", "The lottery"),
                           ("box-heat", "Heat & load")):
            self.query_one(f"#{box}").border_title = title
        self.refresh_view()

    # ── the four boxes ───────────────────────────────────────────────────────
    def refresh_view(self) -> None:
        app = self.app
        st, cfg = app.miner.stats, app.config
        m = "$forge-muted"
        lines: list[str] = []
        problems = app.not_ready()
        if app.miner.running and st.paused:
            lines.append(f"[b $forge-warn]{glyph('warn')} Paused: the processor is hot[/]")
            lines.append(f"[{m}]Goes on by itself at {cfg.original('heat_limit') - RESUME_BELOW} °C.[/]")
        elif app.miner.running:
            lines.append(f"[b $forge-ok]{glyph('on')}[/] [b]Mining[/]  [{m}]for {ago(st.seconds)}[/]")
            if st.problem:
                lines.append(f"[$forge-warn]{glyph('warn')} {escape(st.problem)}[/]")
                lines.append(f"[{m}]The miner keeps trying every 30 seconds.[/]")
            elif not st.connected:
                lines.append(f"[{m}]Connecting to {escape(pools.label(cfg.original('pool')))}{glyph('ellipsis')}[/]")
            else:
                lines.append(f"[{m}]Pool[/]  {escape(pools.label(cfg.original('pool')))}")
        else:
            lines.append(f"[{m}]{glyph('off')}[/] [b]Not mining[/]")
            if st.why_stopped:
                lines.append(f"[{m}]Last session: {ago(st.seconds)}, {escape(st.why_stopped)}.[/]")
            if problems:
                for p in problems:
                    lines.append(f"[$forge-warn]{glyph('warn')}[/] {escape(p)}")
            else:
                lines.append(f"[{m}]Ready: {escape(pools.label(cfg.original('pool')))}, "
                             f"{cfg.original('threads')} of {CORES} cores.[/]")
        lines.append("")
        lines.append(f"[{m}]bitlaForge never starts mining on its own, and stops it when it closes.[/]")
        self.query_one("#db-mining", Static).update("\n".join(lines))

        toggle = self.query_one("#db-toggle", Button)
        toggle.label = "Stop mining" if app.miner.running else "Start mining"
        toggle.variant = "error" if app.miner.running else "primary"
        toggle.disabled = not app.miner.running and bool(problems)
        self.query_one("#db-test", Button).disabled = app.miner.running or app.testing
        no_wallet = cfg.readable and not cfg.original("wallet")
        fixes = {"db-wallet": no_wallet, "db-restore": not cfg.readable and app.has_backups(),
                 "db-install": app.minerd is None}
        for bid, show in fixes.items():
            self.query_one(f"#{bid}").display = show
        self.query_one("#db-fixes").display = any(fixes.values())

        self._speed(st, m)
        self._odds(st, m)
        self._heat(st, m)

    def _speed(self, st, m) -> None:
        if not st.running and not st.minutes:
            self.query_one("#db-speed", Static).update(
                f"[{m}]Shows while mining: the speed now and over the last 30 minutes, and how each "
                f"core is doing.[/]")
            return
        now = speed(st.speed_khs) if st.running and not st.paused else "paused" if st.paused else "stopped"
        chart = bars(list(st.minutes), 36, floor=0.5)
        n = len(st.minutes)
        out = [f"[b]{now}[/]  [{m}]now {glyph('dash')} average {speed(st.average_khs)}[/]"]
        if chart:
            out += [f"[$forge-accent]{chart}[/]", f"[{m}]the last {n} minute{'s' if n != 1 else ''}[/]", ""]
        else:
            out += [f"[{m}]The chart starts after the first minute.[/]", ""]
        if st.cores:
            vals = [st.cores[k] for k in sorted(st.cores)]
            out.append(f"[{m}]Cores[/] [$forge-accent]{bars(vals, 32)}[/] [{m}]{len(vals)} busy[/]")
            out.append(f"[{m}]slowest {speed(min(vals))} {glyph('dash')} fastest {speed(max(vals))}[/]")
        self.query_one("#db-speed", Static).update("\n".join(out))

    def _odds(self, st, m) -> None:
        app = self.app
        if not app.config.original("odds"):
            self.query_one("#db-odds", Static).update(
                f"[{m}]Lottery odds are off: no internet is used for them. Turn them on in "
                f"Settings {glyph('pointer')} Safety.[/]")
            return
        n = app.network
        if n is None:
            self.query_one("#db-odds", Static).update(
                f"[{m}]Asking mempool.space how big the Bitcoin network is{glyph('ellipsis')}[/]"
                + (f"\n[$forge-warn]{escape(app.network_error)}[/]" if app.network_error else ""))
            return
        khs = st.speed_khs if st.running and not st.paused else st.average_khs or app.last_average()
        if khs:
            when = "" if st.running and not st.paused else f" [{m}](at {speed(khs)})[/]"
            day, year = odds.one_in(khs, n.difficulty, 86_400), odds.one_in(khs, n.difficulty, 365 * 86_400)
            out = [f"[{m}]A block today    [/] [b]{odds.words(day)}[/]{when}",
                   f"[{m}]A block this year[/] [b]{odds.words(year)}[/]"]
        else:
            out = [f"[{m}]Your chance of a block shows once you've mined: it depends on your speed.[/]"]
        out += [f"[{m}]Bitcoin network  [/] {odds.eh(n.hashrate)} [{m}]{glyph('dash')} {odds.checked_words(n)}[/]",
               f"[{m}]A block pays about {n.reward_btc:.2f} BTC. Almost no solo miner ever finds one: "
               f"that's the lottery.[/]"]
        if app.network_error:
            out.append(f"[$forge-warn]{escape(app.network_error)}[/]")
        self.query_one("#db-odds", Static).update("\n".join(out))

    def _heat(self, st, m) -> None:
        app, cfg = self.app, self.app.config
        t = app.temp
        limit = cfg.original("heat_limit")
        if t is None:
            temp = f"[{m}]no sensor found: not watched[/]"
        elif cfg.original("heat_pause"):
            temp = f"{t:.0f} °C [{m}]{glyph('dash')} pauses at {limit} °C[/]"
        else:
            temp = f"{t:.0f} °C [{m}]{glyph('dash')} pausing is off[/]"
        use = f"{app.cpu_cores:.1f} of {CORES} cores" if app.miner.running and not st.paused else (
            "nothing (paused)" if st.paused else "nothing (not mining)")
        prio = cfg.original("niceness")
        tot = app.totals()
        rows = [f"[{m}]Processor  [/] {temp}",
                f"[{m}]Miner uses [/] {use}",
                f"[{m}]Priority   [/] {words('niceness', prio)} [{m}]{glyph('dash')} "
                f"{'other programs first' if prio == GENTLE else 'equal to your programs'}[/]"]
        if st.running or st.submitted:
            bad = f"[$forge-warn]{st.rejected} rejected[/]" if st.rejected else "0 rejected"
            rows.append(f"[{m}]Shares     [/] [$forge-ok]{st.accepted} accepted[/] {glyph('dash')} {bad}")
        rows.append(f"[{m}]All time   [/] " + (f"{history.duration(tot.seconds)} mining {glyph('dash')} "
                                                f"{tot.accepted} share{'s' if tot.accepted != 1 else ''}" if tot.sessions
                                                else "no mining yet"))
        self.query_one("#db-heat", Static).update("\n".join(rows))
