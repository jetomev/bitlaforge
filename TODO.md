# bitlaForge — TODO

*The live work list and the handoff between sessions. Newest work first. Updated after every step.*

## Next — the grubForge 2.0 look (Javier, 2026-10-02)
After alacrittyForge. Rework bitlaForge onto forgekit 0.5.0 to match grubForge 2.0 ("so far the best of the 3"), with the same method: research, a screen-by-screen design Javier approves before code, build, tests (incl. 100 columns), his own run, release. Fold in the open items below (F-1 #3, #2 console) and the v0.3.0 dashboard ideas.

## Now
- [x] Project kit completed: `CLAUDE.md` and this `TODO.md` (Javier, 2026-10-01: mandatory for every project). GitHub (README, About, topics, releases) and the AUR were already complete; the Vault folder exists
- [ ] **F-1 · bitlaforge#3** · Esc does not take the cursor out of a Config field, so the next shortcut key is typed into it (found 2026-10-01 in forgekit's console-mode test; same in a normal terminal). Also: `E` focuses Pool URL while the Shortcuts window says "first field"
- [ ] **bitlaforge#2 · console mode, the app's own part** (forgekit 0.4.1 already gives the shell console mode; bitlaForge runs on it unchanged and passed the console test):
  - drop bitlaForge's own copy of the form colours (`Input` / `Select` / `#log-view-container` in `app.py`), which duplicates forgekit since 0.3.0 (**K-1**: on a terminal that draws bright backgrounds, those frames vanish; not on a real console)
  - move the remaining fixed hex colours to the `$forge-*` roles, and the nav marks (`⚡`, `○`…) to `glyph()`
  - add a console run to the test matrix
- [ ] `Ctrl+H` opens Shortcuts in bitlaForge, but a text console can never send it; there `F1` opens forgekit's Help menu instead. Decide whether Shortcuts needs a console key of its own (`?` already toggles it)

## Next — v0.3.0: make it worth watching (Javier's ruling, 2026-08-09)
- [ ] A sparkline of hashrate over time, under the number
- [ ] Per-thread bars, so a lagging core shows
- [ ] Proper time-series charts, the way system monitors do it
- [ ] A committed `tests/` folder (the August headless Pilot smoke suite, rebuilt), so the test count can be reported at every release

## Also planned (from the README)
- [ ] Check the wallet address is valid before mining to it for a week
- [ ] Test whether the pool is reachable on save, not only on start
- [ ] Keep session logs across restarts
- [ ] Lifetime totals across restarts (uptime, shares)
- [ ] Switch between saved setups with one key
- [ ] Optional restart if the miner crashes
- [ ] Announce an accepted share loudly

## Housekeeping
- [ ] Naming drift: files and docs still say `BitlaForge`; the house name is `bitlaForge`. Fix as files are touched; a full rename (GitHub repo name is already lowercase `bitlaforge`) is Javier's call
- [ ] Vault: entries for v0.2.0 and v0.2.1 (August) are missing (only Part 1, June). Part of the Vault-review initiative

## Done (the two newest releases; full history in `docs/CHANGELOG.md`)
- [x] v0.2.1 (2026-08-09): Shortcuts window shows both ways to trigger each action; `T` restored; windows hug their content with a fixed button footer
- [x] v0.2.0 (2026-08-08): the first Forge app on forgekit
