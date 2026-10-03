# bitlaForge v1.0.0 — Test Matrix

Design: `docs/design/v1.0.0-screens.html` (Javier's rulings, 2 Oct 2026, issue #4). Each result was read from the run itself, not assumed.

## 1–4 · Built and checked by Claude (2 Oct 2026)

Automated: **64 tests**, all passing, 0 warnings (also inside the package build, and in four distribution VMs). Each finding's test was checked against 0.2.1, where it fails.

| ID | Area | Proven by | Result |
|---|---|---|---|
| 1 | Wallet checked offline: every mainnet kind (1…, 3…, bc1q…, bc1p…), one character mistyped or missing caught, wrong checksum kind (BIP350), test-network refused; Javier's saved wallet passes | `test_wallet.py` (vectors from BIP173/BIP350) | **PASS** |
| 2 | Settings: 0.2.x text values read; only changes written, notes kept; one backup per save; a link stays a link; a new file is private (600); **a broken file is never saved over** (0.2.1 erased the wallet, shown on a copy) | `test_settings.py`, `test_screens.py` | **PASS** |
| 3 | The miner: cpuminer 2.5.1's real lines read; **rejected shares counted** (0.2.1: always 0); host:port gets stratum+tcp:// (0.2.1: contacted as a website, shown with the real miner); pause freezes / resume continues; a missing program refused before starting | `test_miner.py` | **PASS** |
| 4 | **The miner never outlives bitlaForge**: quitting asks, then stops it; any other close stops it; bitlaForge killed outright → the system stops it (setpriv parent-death signal) | `test_miner.py` (a killed parent), `test_screens.py` | **PASS** |
| 5 | Screens: Dashboard (4 boxes), Settings (3 groups, wallet checked as typed, Esc leaves a field — F-1 #3), Log (filters, Find, Following, wallet never shown), History (sessions cut short closed), heat pause and resume on a fake sensor, the closing note | `test_screens.py` | **PASS** |
| 6 | Nothing cut off at 100 columns on any screen or group while mining; text console (100×30) on all four screens: console font only, nothing invisible | `test_every_screen_fits_100_columns_while_mining`; forgekit `console-preview.py` | **PASS** |
| 7 | Test the miner with this desktop's real minerd: one core 21.0 Mh/s; nothing left running | headless run | **PASS** |

## 5 · Every major distribution

`scripts/vm-distro-check.py` in the grubForge test VMs (snapshot `fresh`): the tests, then **that distribution's real miner** driven through the app: Test the miner, mining against a pool address where nothing listens (nothing mined, nothing sent), the Dashboard must say the pool can't be reached, quitting must ask and leave no miner running.

| ID | Distribution | The miner comes from | Python | Tests | Test the miner | Unreachable pool shown | Quit stops it | Result |
|---|---|---|---|---|---|---|---|---|
| 5.1 | Debian 13 | cpuminer's ready-made program (not packaged) | 3.13 | 64 pass, 1 skip¹ | 20.7 Mh/s per core | yes | yes | **PASS** |
| 5.2 | Ubuntu 24.04 | cpuminer's ready-made program (not packaged) | 3.12 | 64 pass, 1 skip¹ | 20.6 Mh/s | yes | yes | **PASS** |
| 5.3 | Fedora 44 | cpuminer's ready-made program (not packaged) | 3.14 | 64 pass, 1 skip¹ | 20.6 Mh/s | yes | yes | **PASS** |
| 5.4 | openSUSE Tumbleweed | `zypper install cpuminer` | 3.13 | 64 pass, 1 skip¹ | 20.9 Mh/s | yes | yes | **PASS** |
| 5.5 | Arch / KognogOS (this desktop) | `cpuminer` (AUR) | 3.14 | 64 pass | 21.0 Mh/s | yes | yes | **PASS** |

¹ "this computer has a temperature sensor": VMs have none; bitlaForge says heat is "not watched".

**Findings of the 1.0 cycle, as issues** (each opened with the explanation; closed with the release): F-1 #3 Esc didn't leave a field · F-2 #5 quitting left the miner running · F-3 #6 rejected shares never counted · F-4 #7 host:port never connects · F-5 #8 a broken settings file replaced silently.

## 6 · Javier's run (this desktop, real mining)

Setup by Claude: `scripts/make-rc-packages.sh` builds `dist-rc/bitlaforge-1.0.0rc1-1-any.pkg.tar.zst` from the current commit (the build runs all 64 tests). Your settings file is copied aside first (`~/.config/bitlaforge/config.toml.before-1.0`).

| ID | Do | Expect | Result |
|---|---|---|---|
| 6.1 | In `~/Programs/bitlaforge`: `nog install ./dist-rc/bitlaforge-1.0.0rc1-1-any.pkg.tar.zst` | an upgrade from 0.2.1; then `bitlaforge --version` says 1.0.0 | |
| 6.2 | Open `bitlaforge` | Dashboard: Not mining · Ready: your pool, 8 of 16 cores; the lottery box shows the network (975 EH/s or near); Heat & load shows the processor's temperature | |
| 6.3 | Press **T** | after 10 seconds: "The miner works: one core does about 21 Mh/s" | |
| 6.4 | Press **2**. Visit the three groups (↑↓). In Wallet, add one wrong character | a warning under the wallet ("check digits"); **Esc** leaves the field; the changes bar offers Discard: discard it | |
| 6.5 | Open the Pool list | ckpool's three solo servers, plus yours marked "(yours)", plus Other | |
| 6.6 | Safety ▸ **Pause at**: pick 75 (or type 60 for a quick pause test). **F10** | the review shows Pause at 85 °C → your value; Save; "Saved" | |
| 6.7 | Press **1**, then **M**: **real mining** for 10 minutes or more | Mining · Pool; speed near 160–190 Mh/s with every core; the Speed chart starts after a minute; Cores bars; Miner uses ~8 of 16 cores; the lottery shows *your* odds | |
| 6.8 | Press **3** (Log) while mining | "connected: the pool is sending work"; Show ▸ Everything adds the per-core lines; Find narrows; **F** stops/starts following. (Shares may not come at all in 10 minutes: the pool's minimum work size is large for a home computer) | |
| 6.9 | If you set 60 °C: watch the Dashboard | "Paused: the processor is hot", then going on by itself 5 °C lower; both in the Log | |
| 6.10 | Press **Q** while mining | "Before you go · The miner is running" → **Stop mining and quit** | |
| 6.11 | Look at the terminal | the banner and the closing note: "Mined for …", "The miner is stopped.", the log line, the thank-you | |
| 6.12 | Open `bitlaforge` again, press **4** | History: your session, with "bitlaForge closed" | |
| 6.13 | Set Pause at back to 85 (or keep yours) and quit | | |
| 6.14 *(optional)* | On a text console (Ctrl+Alt+F3, log in, `bitlaforge`) | everything readable; Ctrl+Alt+F1/F2 to come back | |

Tell Claude "done": the History file, the backups, the run log and the settings file are read from the machine, and the results are written in `testing/20261002 - Test Results for bitlaForge v1-0-0.md`.
