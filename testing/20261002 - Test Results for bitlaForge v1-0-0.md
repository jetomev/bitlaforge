# bitlaForge v1.0.0 — Test Results

Matrix: `20261002 - Test Matrix for bitlaForge v1-0-0.md`. Sections 1–5 are recorded in the matrix (Claude, 2 Oct 2026): 64 tests, 0 warnings, four distributions PASS.

## 6 · Javier's run (this desktop, 2 Oct 2026, 23:42–23:47, real mining)

Javier: *"done! so much better!"* Read afterwards from the machine (not from memory):

| ID | Result | Evidence |
|---|---|---|
| 6.1 | **PASS** | `pacman -Q`: bitlaforge 1.0.0rc1-1 (upgraded from 0.2.1 with nog); `bitlaforge --version`: bitlaForge 1.0.0 |
| 6.4–6.6 | **PASS** | two saves, one backup each ("Before a save"); the first backup is the 0.2.1-era file byte for byte; the file changed only in what he chose: pool → `solo.ckpool.org` (picked from the list), `heat_limit = 90` added; wallet, worker name, cores, priority and the layout untouched |
| 6.7 | **PASS** | History: 46 s at 161.2 Mh/s ("you stopped it"), 127 s at 159.6 Mh/s; 8 of 16 cores as saved |
| 6.10–6.11 | **PASS** | the second session ended "bitlaForge closed" while mining; afterwards `ps -C minerd`: none running; the run log line: "Mined for 2 min · 2 sessions, 0 shares accepted, 0 rejected, about 160.4 Mh/s. The miner is stopped. Settings saved 2 times, with a backup first." |
| 6.3, 6.8, 6.12, 6.14 | not in the evidence | Test the miner, the Log screen, reopening History and the text console leave no record on disk; they were checked headless and in the VMs (sections 1–5), not confirmed here |
| 6.9 | not reached | Pause at was set to 90 °C; the processor didn't get there in 3 minutes. The pause itself is proven on a fake sensor (`test_heat_pauses_and_resumes`) |

Mining ran about 3 minutes in all, not the 10 the matrix asked for; no shares in that time, which is expected at the pool's minimum work size.

**Answered by the run:** the open question about `stratum.ckpool.org` (not on ckpool's solo list) — Javier switched to `solo.ckpool.org` himself.

**Findings:** none new.
