# bitlaForge — TODO

*The live work list and the handoff between sessions. Newest work first. Updated after every step.*


- [x] **1.0 design approved (2 Oct, 23:03)**: all six answers yes ("Love it!", "Wow! I like it!") — https://claude.ai/artifact/Rtcb5HuMzYntERx5JoWxLj, issue #4. Findings opened: F-2 #5 quit leaves the miner running · F-3 #6 rejected never counted · F-4 #7 host:port never connects · F-5 #8 broken config replaced silently.
- [ ] **1.0 build** (#4), in order, each with tests:
  1. ✅ **Safe core (2 Oct, 23:12), 48 tests**: `wallet.py` (offline check, BIP173/350 vectors; Javier's saved wallet passes), `pools.py` (ckpool's 3 verified solo servers + Other; host:port → stratum+tcp://), `settings.py` + `backups.py` (reads 0.2.x text values; review/backup/one-step write; never over a broken file — 0.2.1 shown to erase the wallet), `miner.py` (real cpuminer 2.5.1 lines; rejected = T − A; stops on quit; `setpriv --pdeathsig TERM` stops it if bitlaForge dies — tested by killing a parent; heat pause = SIGSTOP/SIGCONT; a missing binary refused before spawning), `heat.py` (k10temp Tctl / coretemp package), `odds.py` (mempool.space hourly, cached), `history.py`. Old code still in place until step 2 replaces it.
  - To ask Javier: his saved pool `stratum.ckpool.org` isn't one ckpool's solo page names (it names solo/eusolo/ausolo); unverified whether it's solo. Shows as "Other".
  2. ✅ **Screens (2 Oct, 23:28), 64 tests, 0 warnings**: Dashboard (4 boxes; speed chart floor 50 %, core bars from zero), Settings (3 groups; pool list + Other; wallet checked as typed; Esc leaves a field — F-1 #3), Log (Important/Everything/Problems/Shares, Find, Following works; wallet never shown), History (sessions cut short closed before any screen reads them), quit dialog (stops the miner; any other close stops it too), manual (9 pages; install page Arch-only until step 4 proves the others), `--version`/`--help`, closing note + run log. Console preview clean on all 4 screens (no undrawable/invisible characters). Real `minerd` Test: one core 21.0 Mh/s (the "all 16 would do" estimate was dropped: SMT doesn't double). 0.2.1's screens/, widgets/, config_manager, miner_runner, setup_info, system_info removed.
  3. ✅ Heat pause, lottery odds, History: built inside steps 1 and 2.
  4. ✅ **Every distribution (2 Oct, 23:37)**: `scripts/vm-distro-check.py` PASS in Debian 13, Ubuntu 24.04, Fedora 44, openSUSE Tumbleweed (64 tests; real minerd: Test ~20.7 Mh/s/core, unreachable pool shown, quit asks, no miner left). The miner: openSUSE packages `cpuminer`; **Debian, Ubuntu, Fedora don't** — the cpuminer project's ready-made linux-x86_64 program (v2.5.1) runs on all three (curl built in, no missing libraries); manual page 08 has both recipes. A test assumed ≥4 cores (VMs have 2) — fixed. VMs have no temperature sensor: "not watched" shown, 1 test skipped.
  5. ✅ **Javier's run (2 Oct 23:42–23:47): "done! so much better!"** — real mining 2 sessions (~160 Mh/s), quit while mining stopped it, 2 saves = 2 backups, pool switched to solo.ckpool.org himself, heat_limit 90. Results: `testing/20261002 - Test Results for bitlaForge v1-0-0.md` (Test/Log/console not in the on-disk evidence; ~3 min mined, not 10). Next: release, when Javier says go — README, man page rewrite, CHANGELOG/ROADMAP, RELEASE-CHECKLIST fix, version surfaces, tag, GitHub release, AUR, close #2–#8.
  6. ⏳ **Release v1.0.0 (Javier: "go", 2 Oct)**: docs commit (README, man page, manual, CHANGELOG/ROADMAP with 0.2.0 moved out, RELEASE-CHECKLIST for 1.0, CLAUDE.md, 8 new pictures), signed tag, GitHub release, AUR, badge, issues #2–#8, About/topics, nog install.
  - ~~Ask Javier about stratum.ckpool.org~~ — he switched to solo.ckpool.org in his run.
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
- [ ] **Naming drift (Javier, 2026-10-02: "the name bitlaForge needs fixing")**. GitHub done 10-02: the four old release titles and five release notes now say bitlaForge; forgekit's example app too (forgekit `3b647ec`). README, About and the repo name were already right. **Left, in the rework release:** what the app itself shows — dashboard title "⚡ BitlaForge — Miner Overview" (`screens/dashboard.py`), About name (`app.py`), the Install & Setup text (`setup_info.py`), module docstrings; and the AUR recipe's comment. Internal names (`BitlaForgeApp`) stay. The Vault folder is still `BitlaForge/`.
- [ ] Vault: entries for v0.2.0 and v0.2.1 (August) are missing (only Part 1, June). Part of the Vault-review initiative

## Done (the two newest releases; full history in `docs/CHANGELOG.md`)
- [x] v0.2.1 (2026-08-09): Shortcuts window shows both ways to trigger each action; `T` restored; windows hug their content with a fixed button footer
- [x] v0.2.0 (2026-08-08): the first Forge app on forgekit
