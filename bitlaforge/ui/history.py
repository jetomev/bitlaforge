"""History — every mining session, kept between runs (v1.0.0).

A table of sessions (newest first) and the totals since you started. A found
block isn't something the miner can see: the pool shows it on its page for
your wallet, and the manual says where.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from forgekit import glyph

from .. import history
from ..miner import speed


class HistoryScreen(Vertical):
    FORGE_HINTS = [("↑↓", "move"), ("1-4", "screens"), ("F1", "help"), ("?", "all keys")]

    def compose(self) -> ComposeResult:
        yield Static("[b $forge-title-accent]History[/]   [$forge-muted]every mining session, kept between "
                     "runs; nothing leaves this computer[/]", classes="bf-group-title")
        table = DataTable(id="hs-table", cursor_type="row", zebra_stripes=False)
        table.FORGE_HINTS = self.FORGE_HINTS
        yield table
        yield Static("", id="hs-totals")

    def on_mount(self) -> None:
        t = self.query_one(DataTable)
        for label, width in (("Started", 14), ("Ran for", 13), ("Average speed", 14), ("Shares", 16),
                             ("Why it stopped", 24)):
            t.add_column(label, width=width)
        self.refresh_view()

    def refresh_view(self) -> None:
        rows = self.app.sessions()
        t = self.query_one(DataTable)
        t.clear()
        for r in rows:
            shares = f"{r.accepted}" + (f" {glyph('dash')} {r.rejected} rejected" if r.rejected else "")
            t.add_row(r.when.strftime("%b %-d  %H:%M"), history.duration(r.seconds),
                      speed(r.average_khs), shares, "mining now" if r.why == history.RUNNING else r.why)
        tot = history.totals(rows)
        m = "$forge-muted"
        if not rows:
            text = f"[{m}]No sessions yet. Each time you mine, the session is kept here.[/]"
        else:
            text = (f"[{m}]Since you started[/]  {history.duration(tot.seconds)} mining {glyph('dash')} "
                    f"[$forge-ok]{tot.accepted} shares accepted[/] {glyph('dash')} {tot.rejected} rejected\n"
                    f"[{m}]Sessions[/]           {tot.sessions}"
                    + (f" {glyph('dash')} most mining on {tot.best_day}" if tot.best_day else "") +
                    f"\n[{m}]Blocks found[/]       the pool's page for your wallet would show one "
                    f"[{m}](Help {glyph('pointer')} Manual {glyph('pointer')} The lottery)[/]")
        self.query_one("#hs-totals", Static).update(text)
