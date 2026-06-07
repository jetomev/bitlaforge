# BitlaForge — v0.1.3 release test matrix

First-AUR-submission verification matrix. Covers the full v0.1.0 → v0.1.3 user-facing surface, since this is the version that hits public install paths via AUR. Each check confirms a feature still works after the install-via-pacman path.

## How to run

1. Test against a **clean install of bitlaforge v0.1.3-1 from the AUR** (`yay -S bitlaforge` post-AUR-push) on an Arch host with `python-textual ≥ 8.2.7` and `cpuminer` (or compatible) installed.
2. Tick each `[ ]` box as verified.
3. If anything fails, stop and log it in the v0.1.3 Test Results before continuing.

Skeleton + features came from earlier cycles (commits): v0.1.0 pivot `998e018`, v0.1.0 hotfix `bb39efd`, v0.1.1 G1 `181dbf1`, v0.1.1 G2 `02efe65`, v0.1.1 G3 `7107a05`, v0.1.1 G4 `f6cb46a`, v0.1.2 G1 `a028084`, v0.1.2 G2 `b7f0c40`, v0.1.2 G3 `50d3695`, v0.1.2 G4 `05072a0`, v0.1.2 G5 `7389714`, v0.1.2 hotfix `cfe1010` + `e3e3091`.

---

## 1. Install + launch

- [ ] **1.1** `yay -S bitlaforge` resolves the package from AUR, builds clean (check() prints `bitlaforge headless mount OK`), installs. The optdep prompt mentions `cpuminer / cpuminer-multi / cpuminer-opt` for actually mining.
- [ ] **1.2** Installed paths exist: `/usr/bin/bitlaforge` is executable; `/usr/lib/bitlaforge/main.py` present; `man bitlaforge` opens the man page.
- [ ] **1.3** `bitlaforge` from any shell launches the TUI without traceback.
- [ ] **1.4** Built package has zero `__pycache__/*.pyc` files (`tar tf` clean — the grubForge v1.0.2 packaging class stays closed).

## 2. Navigation + bindings (v0.1.0 + v0.1.0 hotfix)

- [ ] **2.1** Keyboard nav 1 / 2 / 3 / 4 switches screens. Works from a fresh launch (the v0.1.0 hotfix focus-on-mount fix holds).
- [ ] **2.2** Sidebar nav-item labels are clickable; clicking switches screens (the v0.1.0 hotfix on_click handler).
- [ ] **2.3** `?` opens HelpScreen; `?` again toggles closed; Esc / q close. `q` while help is open does NOT quit the app.
- [ ] **2.4** ConfirmDialog: any save dialog accepts Esc (cancel) and Enter (confirm).
- [ ] **2.5** No startup popup spray on launch.

## 3. Config persistence (v0.1.1 G1 + v0.1.2 G2)

- [ ] **3.1** Press 3 (Config). All six fields present: miner_name, pool, wallet, algorithm (select), threads, niceness.
- [ ] **3.2** miner_name defaults to `hostname`; niceness defaults to `19`; algorithm defaults to `sha256d`.
- [ ] **3.3** Threads label dynamically shows "of N available" matching `os.cpu_count()`.
- [ ] **3.4** Edit fields, press S, confirm. File at `~/.config/bitlaforge/config.toml` exists with the typed values.
- [ ] **3.5** Quit app (`q`) and relaunch. Config screen shows the saved values.

## 4. Setup screen (v0.1.1 G4 + v0.1.2 G1)

- [ ] **4.1** Press 4. System info block at the top shows host / CPU model / "N logical (M physical)" cores / memory / load avg color-graded.
- [ ] **4.2** Below: minerd status block (✓ installed at `<path>` if cpuminer was installed; ✗ not installed otherwise). Three AUR providers listed with `yay -S` commands. Paths section shows config + binary location.
- [ ] **4.3** Press T (Test minerd). Either runs `minerd --version` and surfaces output OR (if not installed) warns "not on PATH".
- [ ] **4.4** Press R. Re-renders without crash; load avg numbers may shift slightly.

## 5. Mining lifecycle (v0.1.1 G2 + v0.1.2 G3 + hotfixes)

Requires `cpuminer` installed. Pool: any solo or pool that accepts your wallet.

- [ ] **5.1** With pool + wallet configured and `minerd` on PATH, press M from any screen. Toast: "Miner started — started minerd (pid N)". Dashboard miner_state header flips to "● running".
- [ ] **5.2** Within ~10s, Dashboard Performance section populates: Threads = N, Hashrate scales appropriately (e.g. "159.15 Mh/s" not "1590%" or "—"), minerd CPU = "X.Y / N cores (P%)", minerd RAM = real value.
- [ ] **5.3** Uptime ticks every second (live tick); doesn't freeze between minerd hashmeter lines.
- [ ] **5.4** Press 2 (Log screen). minerd stdout is streaming line-by-line; buffer fills.
- [ ] **5.5** Press M again. Toast: "Miner stopped." Dashboard state header flips back to "○ stopped". CPU%/RAM display reverts to "—".
- [ ] **5.6** Without configured pool+wallet, M produces "Configure pool, wallet first (press 3)." (not a crash).
- [ ] **5.7** With `minerd` NOT on PATH, M produces friendly install-guidance toast (not raw "binary not found"); Dashboard banner shows.

## 6. Pool-side worker name (v0.1.2 G3)

- [ ] **6.1** With `miner_name="workstation-rig"` and a Stratum pool that exposes per-worker stats, after mining for a few minutes the pool's dashboard shows a worker named `workstation-rig` under your wallet. (For solo.ckpool.org and most pools: visible in the workers table.)

## 7. Niceness behavior (v0.1.2 G3 + G5)

- [ ] **7.1** With niceness=19, start mining. minerd CPU% reads close to "N / N cores (≈99%)" on an idle system.
- [ ] **7.2** Launch a CPU-bound process in another terminal (e.g. `stress-ng --cpu 4 --timeout 30s` or `yes > /dev/null` in 4 shells). Within 1–2 seconds, BitlaForge's Dashboard shows minerd's CPU% DROP — visible proof that niceness is yielding.
- [ ] **7.3** With niceness=0, repeat 7.2. minerd's CPU% should drop LESS (or not at all), confirming niceness is the variable.

## 8. Regression — version sync + packaging

- [ ] **8.1** `bitlaforge` sidebar reads **v0.1.3** (or main.py header / __init__ shows 0.1.3 via `python -c "import bitlaforge; print(bitlaforge.__version__)"`).
- [ ] **8.2** Man page `.TH` line reads **v0.1.3**.
- [ ] **8.3** PKGBUILD `pkgver=0.1.3 pkgrel=1`.
- [ ] **8.4** Async-worker audit clean (`grep -rn "run_worker(self\.action_" bitlaforge/` empty).
- [ ] **8.5** `_render` shadowing audit clean (`grep -rn "def _render(self" bitlaforge/` empty).

---

## Pass criteria for v0.1.3 release

- All of section 1 (install) and section 2 (nav) must pass.
- Sections 3–5 (config, setup, mining) must pass — these are the core features.
- Section 7 (niceness behavior) is the differentiator the user can show others; passes are nice-to-have but the feature exists either way.
- Section 8 (regression / packaging) must pass before tag.

If section 1.4 fails (`.pyc` in package): the grubForge v1.0.2 packaging fix didn't propagate; check `PYTHONDONTWRITEBYTECODE=1` in `check()` and the `__pycache__` cleanup in `package()`.

If section 2 fails: the v0.1.0 hotfix isn't in this release. Cross-check that `bb39efd` (or its content) is in main.

If section 5.2 hashrate shows "—" with cpuminer running: the hotfix `e3e3091` (regex + aggregate + auto-scale) didn't make it. Check `miner_runner.py` parse_line for `_RE_THREAD_RATE`.

---

## Out of scope (deferred to v0.1.4)

- Pool reachability TCP probe before start.
- Wallet format validation.
- Persistent log archive across launches.
- Per-session lifetime totals.
- Hashrate sparkline / btop-style graphs (v0.2.0+).
