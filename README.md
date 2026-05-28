# ⚡ BitlaForge

> A terminal UI for running solo Bitcoin mining as what it really is — a *lottery*. Wraps `minerd`, watches it work, doesn't pretend the odds are anything other than astronomical.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)
![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)
![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-purple.svg)

---

## Why BitlaForge?

Solo Bitcoin mining at today's network difficulty is, statistically, **a lottery**. The chance of finding a block on a single CPU in any given minute is so small it's barely a number. But unlike a pool, if you *do* hit, you take the entire block reward — no per-share split. That's the wager: tiny odds, maximum payout, and a long-running process turning electricity into hashes while you wait.

BitlaForge is the dashboard you watch while your machine buys lottery tickets in compute cycles. It launches `minerd`, parses what it says, and shows you the pool, wallet, threads, hashrate, uptime, and shares without you having to keep a terminal window staring at raw output. It also runs cleanly over SSH, which is what you actually want for a headless rig.

It is the fourth tool in the **Forge suite** for KognogOS — alongside [grubForge](https://github.com/jetomev/grubforge), [alacrittyForge](https://github.com/jetomev/alacrittyforge), and nogForge. Same Catppuccin Mocha aesthetic, same release discipline, same human + AI co-authorship.

---

## Project state

**v0.1.0 alpha — Forge-style TUI skeleton.** The app launches, all three screens compose and render, the help modal toggles, the confirm dialog accepts Esc/Enter, the M key flips a state flag.

**There is no real `minerd` integration yet.** Dashboard fields show placeholders, the log buffer is empty, the M toggle just notifies. Wiring `asyncio.create_subprocess_exec` to spawn `minerd`, parse its stdout, and stream into the Log screen is the headline work for the next cycle (v0.1.1).

> This repo used to be `BitLA`, a Qt6/Widgets desktop scaffold that landed in November 2025 with simulation-driven UI and no real miner integration either. On 2026-05-28 it pivoted to a Textual TUI under the Forge-suite umbrella. The Qt prototype is preserved permanently as the `v0.1.0-qt-archived` git tag; `main` is the TUI from day one.

---

## Features (v0.1.0 skeleton)

- 🏠 **Dashboard** — read-only overview: miner state, pool + port, wallet, CPU load, threads, uptime, hashrate, shares (accepted / rejected), log line count. (Placeholders today; wired in v0.1.1.)
- 📜 **Log** — streaming view of minerd stdout with a 5,000-line bounded buffer, search filter, and auto-scroll. (Empty today; piped in v0.1.1.)
- ⚙ **Config** — pool URL, wallet, algorithm, thread count. In-memory today; persisted to `~/.config/bitlaforge/config.toml` in v0.1.2.
- ❓ **Help modal** — toggleable; Esc / q / ? all dismiss. Lists every binding in the app.
- 💬 **Unified feedback** — `StatusMixin` from the Forge suite: status-line + toast popup, `popup=False` for passive mount hints so launch is quiet.
- 🎯 **Focus-on-show** — screen bindings fire on the first keypress without a panel click.

---

## Requirements

- Linux
- Python 3.11+
- `python-textual`, `python-rich`
- `minerd` (cpuminer or compatible) — required once v0.1.1 lands; **not used by v0.1.0**

---

## Installation

### From source (Arch, v0.1.0)
```bash
sudo pacman -S python-textual python-rich
git clone https://github.com/jetomev/bitlaforge.git
cd bitlaforge
python main.py
```

### Other distributions
```bash
pip install textual rich
git clone https://github.com/jetomev/bitlaforge.git
cd bitlaforge
python main.py
```

AUR submission lands with v0.1.3 — once there's real mining behavior to verify, the Forge release machinery (testing/, man page, hardened-`check()` PKGBUILD) goes up.

---

## Keybindings

### Global
| Key | Action |
|-----|--------|
| `1` | Dashboard |
| `2` | Log |
| `3` | Config |
| `M` | Start / Stop miner |
| `R` | Refresh current screen |
| `?` | Toggle help overlay |
| `q` | Quit |

### Log screen
| Key | Action |
|-----|--------|
| `/` | Focus the search filter |
| `C` | Clear the log buffer |

### Config screen
| Key | Action |
|-----|--------|
| `E` | Focus the first input (begin editing) |
| `S` | Save the current values |

---

## Project Structure

```
bitlaforge/
├── main.py                                # Entry point
├── bitlaforge/
│   ├── app.py                             # BitlaForgeApp shell + nav
│   ├── bitlaforge.css                     # Catppuccin Mocha stylesheet
│   ├── screens/
│   │   ├── dashboard.py                   # Miner overview (placeholder fields)
│   │   ├── log.py                         # Bounded streaming buffer + filter
│   │   └── config.py                      # Pool / wallet / algorithm / threads
│   └── widgets/
│       ├── status.py                      # StatusMixin (line + toast)
│       ├── help_screen.py                 # Toggleable modal help
│       └── confirm_dialog.py              # Esc-cancel / Enter-confirm modal
```

---

## Safety philosophy

Mining is **opt-in**. Real CPU load, real electricity, real heat. BitlaForge will never:

- Auto-start `minerd` on launch. The miner only runs after you explicitly press **M** (and, eventually, only if a pool + wallet are configured).
- Hide the active state. The Dashboard always shows whether the miner is running.
- Make the Stop path more than one keystroke away. **M** toggles. Always.

---

## Roadmap

### v0.1.0 — May 28, 2026 (current)
- [x] Pivot from Qt6/Widgets `BitLA` to Textual TUI under the Forge suite
- [x] Sidebar navigation + 3 screens (Dashboard, Log, Config)
- [x] `StatusMixin`, `HelpScreen`, `ConfirmDialog` ported from the Forge baseline
- [x] Catppuccin Mocha styling

### v0.1.1 — Planned (next cycle)
- [ ] Wire `minerd` via `asyncio.create_subprocess_exec`: spawn, parse stdout, stop cleanly
- [ ] Real Dashboard fields driven by parsed minerd output
- [ ] Stream minerd stdout into the Log screen's bounded buffer

### v0.1.2 — Planned
- [ ] Persist Config to `~/.config/bitlaforge/config.toml`
- [ ] Start-miner pre-flight (require pool + wallet)
- [ ] Error handling: minerd not installed, pool unreachable, bad wallet

### v0.1.3 — Planned (Forge release machinery + AUR)
- [ ] `testing/` (RELEASE-CHECKLIST + Test Matrix + dogfood Test Results)
- [ ] Man page `bitlaforge.1`
- [ ] PKGBUILD with hardened headless-mount `check()`
- [ ] First AUR submission

### Future
- [ ] Hashrate graph (Textual chart widget)
- [ ] Persistent log archive (rotating files)
- [ ] Pool tester (TCP probe before saving)

---

## Changelog

### v0.1.0 — May 28, 2026
**Pivot from Qt to TUI; first Forge-era release.**

Repo was originally `BitLA` — a Qt6/Widgets desktop scaffold pushed in November 2025 with simulation-driven UI and no real `minerd` integration. Untouched for ~6 months. Pivoted to a Textual TUI on 2026-05-28 because solo mining is fundamentally a streaming-stdout activity on long-running headless rigs, which a TUI fits better. The Qt code (~700 LOC of mostly scaffolding) is preserved permanently as the `v0.1.0-qt-archived` git tag.

Inaugural v0.1.0 ships the Forge-suite skeleton:

- Three screens (Dashboard, Log, Config) under sidebar navigation via `ContentSwitcher`.
- `StatusMixin` for unified status-line + toast feedback, with `popup=False` for passive mount-time hints (so the app launches quietly).
- Toggleable `HelpScreen` modal (Esc / q / ? dismiss; q shadows app-quit while help is up).
- `ConfirmDialog` with `escape` → cancel, `enter` → confirm.
- `DEFAULT_FOCUS` per screen so bindings fire on entry without a panel click.

`minerd` subprocess wiring is the v0.1.1 headline work.

---

## Authors

**Javier ([@jetomev](https://github.com/jetomev))** — idea, direction, testing

**Claude (Anthropic)** — co-developer, architecture, implementation

BitlaForge is built as a real collaboration between a human with an idea and an AI that helps bring it to life — one commit at a time. The co-authorship is preserved in the [Forge-suite recognition thesis](https://github.com/jetomev/grubforge): public projects that demonstrate AI as a serious software collaborator, not a black-box code generator. Co-author credit appears in commits, README, man pages, PKGBUILD, and release notes.

---

## License

GPL v3. See [LICENSE](LICENSE).

---

## Contributing

This is alpha software — UI feedback, bug reports, and ideas welcome via GitHub Issues. If you find BitlaForge useful, consider starring the repo. The Forge-suite recognition thesis only works if these projects are visible.
