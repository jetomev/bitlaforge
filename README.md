# ⚡ BitlaForge

> A terminal UI for running solo Bitcoin mining as what it really is — a *lottery*. Wraps `minerd`, watches it work, doesn't pretend the odds are anything other than astronomical.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)
![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)
![Version: 0.1.2](https://img.shields.io/badge/Version-0.1.2-purple.svg)

---

## Why BitlaForge?

Solo Bitcoin mining at today's network difficulty is, statistically, **a lottery**. The chance of finding a block on a single CPU in any given minute is so small it's barely a number. But unlike a pool, if you *do* hit, you take the entire block reward — no per-share split. That's the wager: tiny odds, maximum payout, and a long-running process turning electricity into hashes while you wait.

BitlaForge is the dashboard you watch while your machine buys lottery tickets in compute cycles. It launches `minerd`, parses what it says, and shows you the pool, wallet, threads, hashrate, uptime, and shares without you having to keep a terminal window staring at raw output. It also runs cleanly over SSH, which is what you actually want for a headless rig.

It is the fourth tool in the **Forge suite** for KognogOS — alongside [grubForge](https://github.com/jetomev/grubforge), [alacrittyForge](https://github.com/jetomev/alacrittyforge), and nogForge. Same Catppuccin Mocha aesthetic, same release discipline, same human + AI co-authorship.

---

## Project state

**v0.1.1 alpha — it actually mines now.** v0.1.0 was the Forge-style skeleton (screens, nav, help, confirm); v0.1.1 wires the four pieces that turn the skeleton into a usable tool:

- **Persistence.** Pool / wallet / algorithm / thread count are saved to `~/.config/bitlaforge/config.toml` and reload at launch.
- **Real `minerd` subprocess.** Pressing **M** spawns `minerd` via `asyncio.create_subprocess_exec`, streams its stdout line-by-line into the Log screen, and parses hashrate / accepted / rejected / threads into reactive Dashboard fields. Pressing **M** again terminates cleanly (SIGTERM with a 3-second grace period, SIGKILL fallback).
- **`minerd` runtime detection.** `shutil.which("minerd")` runs at launch and on every **M** press. When the binary is missing, the Dashboard shows a persistent banner and **M** surfaces friendly install guidance instead of a raw "binary not found" error.
- **Setup screen.** A new fourth screen (**4**) lists the three AUR providers (`cpuminer`, `cpuminer-multi`, `cpuminer-opt`) with copy-pasteable `yay -S` commands and a **T** action that runs `minerd --version` to verify the install actually works.

> This repo used to be `BitLA`, a Qt6/Widgets desktop scaffold that landed in November 2025 with simulation-driven UI and no real miner integration. On 2026-05-28 it pivoted to a Textual TUI under the Forge-suite umbrella. The Qt prototype is preserved permanently as the `v0.1.0-qt-archived` git tag; `main` is the TUI from day one.

---

## Features (v0.1.1)

- 🏠 **Dashboard** — read-only overview driven live by parsed minerd output: pool / port / wallet / algorithm / threads / hashrate / accepted / rejected shares / uptime. Persistent **⚠ minerd not detected** banner when the binary isn't on PATH.
- 📜 **Log** — streaming view of minerd's stdout/stderr line-by-line, with a 5,000-line bounded buffer, **/** to focus search, **C** to clear.
- ⚙ **Config** — pool URL, wallet, algorithm (sha256d / scrypt / yescrypt / x11 / x13 / x15 / x17 / groestl), thread count. **Persisted** to `~/.config/bitlaforge/config.toml`; loads at every launch.
- 🛠 **Setup** — install guide for `minerd` (AUR-only) with one-liner commands for each provider, and a **T** action that runs `minerd --version` to verify the install.
- ❓ **Help modal** — toggleable; Esc / q / ? all dismiss; lists every binding.
- 💬 **Unified feedback** — `StatusMixin` from the Forge suite: status-line + toast popup, `popup=False` for passive mount hints so launch is quiet.
- 🎯 **Focus-on-show** — screen bindings fire on the first keypress without a panel click; clickable sidebar nav as an alternative path.

---

## Requirements

- Linux
- Python 3.11+
- `python-textual`, `python-rich`, `python-tomli-w`
- `minerd` — optional but required to actually mine. AUR-only; install via one of `cpuminer` (recommended, pooler's original), `cpuminer-multi`, or `cpuminer-opt`. The Setup screen (press **4**) has the install commands and a self-test.

---

## Installation

### From source (Arch)
```bash
sudo pacman -S python-textual python-rich python-tomli-w
git clone https://github.com/jetomev/bitlaforge.git
cd bitlaforge
python main.py
```

### Other distributions
```bash
pip install textual rich tomli-w
git clone https://github.com/jetomev/bitlaforge.git
cd bitlaforge
python main.py
```

To actually mine, also install `minerd` via the AUR (see the Setup screen):
```bash
yay -S cpuminer
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
| `4` | Setup |
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

### Setup screen
| Key | Action |
|-----|--------|
| `T` | Test minerd binary (`minerd --version`) |

---

## Project Structure

```
bitlaforge/
├── main.py                                # Entry point
├── bitlaforge/
│   ├── app.py                             # BitlaForgeApp shell + nav + M lifecycle + live tick
│   ├── bitlaforge.css                     # Catppuccin Mocha stylesheet
│   ├── config_manager.py                  # TOML read/write at ~/.config/bitlaforge/
│   ├── miner_runner.py                    # Async minerd subprocess + stdout parsing
│   ├── process_stats.py                   # /proc/<pid>/ CPU% + RAM readouts
│   ├── system_info.py                     # /proc/cpuinfo + /proc/meminfo + load avg
│   ├── screens/
│   │   ├── dashboard.py                   # Live miner overview + missing-minerd banner
│   │   ├── log.py                         # 5,000-line bounded buffer + filter
│   │   ├── config.py                      # Pool / wallet / algorithm / threads / name / niceness
│   │   └── setup.py                       # System info + AUR install guide + minerd self-test
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

### v0.1.0 — May 28, 2026
- [x] Pivot from Qt6/Widgets `BitLA` to Textual TUI under the Forge suite
- [x] Sidebar navigation + 3 screens (Dashboard, Log, Config)
- [x] `StatusMixin`, `HelpScreen`, `ConfirmDialog` ported from the Forge baseline
- [x] Catppuccin Mocha styling

### v0.1.1 — May 28, 2026
- [x] Persist config to `~/.config/bitlaforge/config.toml` (TOML)
- [x] Wire `minerd` via `asyncio.create_subprocess_exec`: spawn, parse stdout, stop cleanly
- [x] Real Dashboard fields driven by parsed minerd output (hashrate / threads / accepted / rejected / uptime)
- [x] Stream minerd stdout into the Log screen's bounded buffer
- [x] Runtime `which("minerd")` check + Dashboard banner + friendly install guidance
- [x] Setup screen with AUR provider list + `minerd --version` self-test

### v0.1.2 — May 29, 2026 (current)
- [x] System info on Setup screen (CPU model + logical/physical cores + load avg + memory) from stdlib
- [x] Config gains **miner name** (default hostname; also used as Stratum worker name) and **niceness** (0–19, default 19)
- [x] Threads input shows "of N available" hint from `os.cpu_count()`
- [x] `miner_runner` appends `wallet.workername` and wraps with `nice -n N`
- [x] Dashboard live tick (1s `set_interval` while mining) — uptime advances smoothly between hashmeter lines
- [x] Miner name surfaced in the Dashboard title
- [x] Live `minerd` CPU% / RAM from `/proc/<pid>/stat` + `/proc/<pid>/status` — makes the niceness setting observable

### v0.1.3 — Planned
- [ ] Start-miner pre-flight beyond pool+wallet (validate wallet format, optionally TCP-probe the pool)
- [ ] Persistent log archive (rotating files in `~/.local/share/bitlaforge/`)
- [ ] Per-session uptime / share totals across restarts

### v0.1.4 — Planned (Forge release machinery + AUR)
- [ ] `testing/` (RELEASE-CHECKLIST + Test Matrix + dogfood Test Results)
- [ ] Man page `bitlaforge.1`
- [ ] PKGBUILD with hardened headless-mount `check()` + `optdepends` listing the cpuminer variants
- [ ] First AUR submission

### Future
- [ ] Hashrate graph (Textual chart widget)
- [ ] Pool tester (TCP probe before saving)
- [ ] Multi-config profiles (switch between pools / wallets / algorithms)

---

## Changelog

### v0.1.2 — May 29, 2026
**Resource awareness + live Dashboard.**

v0.1.1 made BitlaForge mine; v0.1.2 makes it feel alive while doing it. Five per-group commits, all stdlib (no new deps):

- **G1 — System info on Setup.** New `bitlaforge/system_info.py` reads `/proc/cpuinfo`, `/proc/meminfo`, `os.getloadavg()`, and `os.cpu_count()` into a `SystemInfo` dataclass. The Setup screen gains a block above the minerd status showing **CPU model**, **logical/physical cores**, **memory total/available with % used**, and **1/5/15-minute load averages** color-graded against your core count (green when comfortably idle, yellow as load approaches your ceiling, red over it). Refreshes on **R**.
- **G2 — Config gains miner name + niceness + threads hint.** Two new fields in `~/.config/bitlaforge/config.toml`: `miner_name` (defaults to `socket.gethostname()`) and `niceness` (0–19, default 19). The Thread count label dynamically shows "of N available" sourced from the same `os.cpu_count()`. Forward-compatible: a v0.1.1 TOML loads cleanly with new defaults silently applied.
- **G3 — `miner_runner` worker name + nice wrapper.** `_build_args` now joins the sanitized `miner_name` to the wallet as `wallet.workername` (standard Stratum convention — pools show per-rig stats on their dashboards). `start()` wraps the spawn with `nice -n N` when niceness > 0; niceness ≤ 0 spawns directly with no overhead.
- **G4 — Dashboard live tick + name in header.** App installs a 1-second `set_interval` timer when the miner starts, cancels on stop (and when the parser sees the process end on its own). Each tick re-renders the Dashboard so **uptime advances smoothly** between minerd hashmeter dumps. The Dashboard title now shows the miner name in mauve: `⚡ BitlaForge — Miner Overview — workstation-rig`.
- **G5 — Live `minerd` CPU% / RAM from `/proc/<pid>/`.** New `process_stats.py` parses `/proc/<pid>/stat` (utime + stime ticks) and `/proc/<pid>/status` (VmRSS) — stdlib only, no `psutil`. The App tick captures a baseline at start, computes deltas on each tick, and writes `cpu_pct` (htop-style: 100% = one logical core) + `mem_mb` into `MinerStats`. Dashboard shows them under Performance. Makes the **niceness setting observable**: with niceness=19, you'll see minerd's CPU% drop the moment any other process needs cycles.

No dependency changes. Same `python`, `python-textual`, `python-rich`, `python-tomli-w`.

### v0.1.1 — May 28, 2026
**Make it actually mine.**

v0.1.0 shipped the Forge-style TUI skeleton with sidebar nav, three screens, the help modal, and a confirm dialog — but `minerd` integration was a stub: pressing M just flipped a state flag and notified. v0.1.1 turns the skeleton into a working tool. Four per-group commits:

- **G1 — Config persistence.** New `config_manager.py` (tomllib for read + tomli_w for write) saves pool / wallet / algorithm / threads to `~/.config/bitlaforge/config.toml`. The values survive launches; the Config screen loads them on `__init__`. Schema is intentionally flat so future cycles can add `[ui]` / `[log]` sections without breaking the miner section.
- **G2 — Real minerd subprocess.** New `miner_runner.py` with a `MinerRunner` class that uses `asyncio.create_subprocess_exec`, streams stdout line-by-line via a background `asyncio.Task`, and parses hashrate / accepted / rejected / threads out of pooler-cpuminer-format lines via regex. Each line is forwarded to the Log screen's bounded buffer; each parsed stat update repaints the Dashboard. Stop is `SIGTERM` with a 3-second grace, `SIGKILL` fallback. App's `M` binding is now async and wraps it all.
- **G3 — Runtime check + Dashboard banner + friendly guards.** `shutil.which("minerd")` runs at launch and on every M press. When the binary is missing, the Dashboard shows a persistent red "⚠ minerd not detected" banner with install hint; pressing M produces "install one of: cpuminer / cpuminer-multi / cpuminer-opt from AUR (`yay -S cpuminer`)" instead of the bare "binary not found" error.
- **G4 — Setup screen (4th nav).** New screen at **4** with the minerd status block (path if installed, or ✗ not installed), an "about minerd" explainer, the three AUR providers with copy-pasteable `yay -S` commands, the config file path, and a **T** action that runs `minerd --version` to verify the install actually works.

Dependency note: `python-tomli-w` is now required (same dep alacrittyForge already pulled in).

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
