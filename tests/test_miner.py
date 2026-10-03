"""The miner: reading its lines, starting, stopping, pausing — with a stand-in
"minerd" (a small script printing cpuminer 2.5.1's real lines), so nothing is
ever mined. Run: python -m unittest discover tests"""

import asyncio
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from bitlaforge.miner import Miner, Stats, command, read_line, speed, worker_name

ROOT = Path(__file__).resolve().parents[1]
WALLET = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"
VALUES = {"pool": "stratum+tcp://solo.ckpool.org:3333", "wallet": WALLET, "miner_name": "Test Rig!",
          "threads": 2, "niceness": 19}

# cpuminer 2.5.1's lines, as printed on this desktop (the share lines from its
# own format: "accepted: %lu/%lu (%.2f%%), %s khash/s %s")
REAL = [
    "[2026-10-02 23:04:25] 1 miner threads started, using 'sha256d' algorithm.",
    "[2026-10-02 23:04:33] Starting Stratum on stratum+tcp://127.0.0.1:1",
    "[2026-10-02 23:04:33] Stratum connection failed: Failed to connect to 127.0.0.1:1 after 0 ms: "
    "Could not connect to server",
    "[2026-10-02 23:04:33] ...retry after 30 seconds",
    "[2026-10-02 23:04:25] thread 0: 2097152 hashes, 20929 khash/s",
    "[2026-10-02 23:04:25] Total: 20929 khash/s",
    "[2026-10-02 23:05:01] Stratum difficulty set to 10000",
    "[2026-10-02 23:41:17] accepted: 1/1 (100.00%), 20929 khash/s (yay!!!)",
    "[2026-10-02 23:58:40] accepted: 1/2 (50.00%), 20931 khash/s (booooo)",
]


def stand_in(tmp: Path, lines: list[str], then: str = "exec sleep 300") -> str:
    """A fake minerd that prints ``lines`` and then does ``then``."""
    p = tmp / "minerd"
    body = "\n".join(f"echo {l!r} >&2" for l in lines)
    p.write_text(f"#!/bin/sh\n{body}\n{then}\n")
    p.chmod(0o755)
    return str(p)


def alive(pid: int) -> bool:
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except (OSError, IndexError):
        return False
    return state != "Z"


class Reading(unittest.TestCase):
    def test_each_real_line(self):
        kinds = [read_line(l).kind for l in REAL]
        self.assertEqual(kinds, ["started", "info", "problem", "info", "thread", "total", "connected",
                                 "accepted", "rejected"])

    def test_rejected_shares_are_counted(self):
        # F-3 (#6): 0.2.1 looked for "rejected:", which cpuminer never prints
        s = Stats(running=True, started=time.time())
        for l in REAL:
            s.take(read_line(l))
        self.assertEqual((s.accepted, s.rejected), (1, 1))
        self.assertTrue(s.connected)
        self.assertEqual(s.problem, "")
        self.assertEqual(s.speed_khs, 20929)

    def test_a_problem_shows_until_connected(self):
        s = Stats(running=True)
        s.take(read_line(REAL[2]))
        self.assertIn("can't reach the pool", s.problem)
        self.assertFalse(s.connected)

    def test_speed_words(self):
        self.assertEqual(speed(20929), "20.9 Mh/s")
        self.assertEqual(speed(184300), "184.3 Mh/s")
        self.assertEqual(speed(0.5), "500 h/s")
        self.assertEqual(speed(0), "—")

    def test_minutes_for_the_chart(self):
        s = Stats(running=True)
        for khs in (100, 200):
            s.take(read_line(f"[2026-10-02 23:04:25] Total: {khs} khash/s"))
        s.tick_minute()
        self.assertEqual(list(s.minutes), [150])
        self.assertEqual(s.average_khs, 150)


class Command(unittest.TestCase):
    def test_bitcoin_pool_wallet_worker(self):
        cmd = command(VALUES, "/usr/bin/minerd")
        i = cmd.index("/usr/bin/minerd")
        self.assertEqual(cmd[i:], ["/usr/bin/minerd", "-a", "sha256d", "-o", "stratum+tcp://solo.ckpool.org:3333",
                                   "-u", f"{WALLET}.testrig", "-p", "x", "-t", "2"])

    def test_gentle_priority_and_the_safety_net(self):
        cmd = command(VALUES, "minerd")
        self.assertEqual(cmd[:3], ["nice", "-n", "19"])
        self.assertEqual(cmd[3:6], ["setpriv", "--pdeathsig", "TERM"])
        self.assertNotIn("nice", command({**VALUES, "niceness": 0}, "minerd"))

    def test_host_port_gets_stratum(self):
        # F-4 (#7): without a scheme the miner contacts the pool as a web server
        cmd = command({**VALUES, "pool": "eusolo.ckpool.org:3333"}, "minerd")
        self.assertIn("stratum+tcp://eusolo.ckpool.org:3333", cmd)

    def test_worker_name(self):
        self.assertEqual(worker_name("Javier's Desktop_01"), "javiersdesktop_01")


class Lifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.events, self.changes = [], 0
        self.m = Miner(self.events.append, self._changed)

    def _changed(self):
        self.changes += 1

    async def asyncTearDown(self):
        self.m.stop_now()

    async def _wait(self, cond, seconds=5.0):
        end = time.time() + seconds
        while not cond() and time.time() < end:
            await asyncio.sleep(0.05)
        return cond()

    async def test_start_read_stop(self):
        self.assertEqual(await self.m.start(VALUES, stand_in(self.tmp, REAL)), "")
        pid = self.m.pid
        self.assertTrue(await self._wait(lambda: self.m.stats.submitted == 2))
        self.assertEqual(self.m.stats.rejected, 1)
        self.assertNotIn(WALLET, self.events[0].text)        # the Log never shows the wallet
        await self.m.stop()
        self.assertFalse(alive(pid))
        self.assertFalse(self.m.stats.running)
        self.assertEqual(self.m.stats.why_stopped, "you stopped it")

    async def test_pause_freezes_and_resume_continues(self):
        await self.m.start(VALUES, stand_in(self.tmp, REAL[:1]))
        pid = self.m.pid
        await asyncio.sleep(0.2)
        self.assertTrue(self.m.pause())
        await asyncio.sleep(0.1)
        state = lambda: Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
        self.assertEqual(state(), "T")                     # stopped by a signal
        self.assertTrue(self.m.resume())
        await asyncio.sleep(0.1)
        self.assertIn(state(), "SR")
        self.m.pause()
        await self.m.stop()                                # a frozen miner still stops
        self.assertFalse(alive(pid))

    async def test_a_miner_that_ends_by_itself(self):
        await self.m.start(VALUES, stand_in(self.tmp, ["minerd: unknown algorithm -- 'x'"], "exit 1"))
        self.assertTrue(await self._wait(lambda: not self.m.stats.running))
        self.assertEqual(self.m.stats.why_stopped, "it stopped by itself")
        self.assertEqual(self.m.stats.exit_code, 1)

    async def test_missing_miner(self):
        why = await self.m.start(VALUES, str(self.tmp / "nothing-here"))
        self.assertIn("couldn't start", why)
        self.assertFalse(self.m.running)


class SafetyNet(unittest.TestCase):
    def test_miner_stops_when_bitlaforge_dies(self):
        """F-2 (#5): bitlaForge killed outright (no chance to clean up) must not
        leave the miner running. The system stops it (parent-death signal)."""
        tmp = Path(tempfile.mkdtemp())
        fake = stand_in(tmp, REAL[:1])
        pidfile = tmp / "pid"
        script = textwrap.dedent(f"""
            import asyncio, os, sys
            sys.path.insert(0, {str(ROOT)!r})
            from bitlaforge.miner import Miner
            async def main():
                m = Miner(lambda e: None, lambda: None)
                await m.start({VALUES!r}, {fake!r})
                open({str(pidfile)!r}, "w").write(str(m.pid))
                await asyncio.sleep(0.3)
                os._exit(9)            # dies without stopping anything
            asyncio.run(main())
        """)
        subprocess.run([sys.executable, "-c", script], timeout=20)
        pid = int(pidfile.read_text())
        end = time.time() + 5
        while alive(pid) and time.time() < end:
            time.sleep(0.05)
        still = alive(pid)
        if still:
            os.kill(pid, 9)
        self.assertFalse(still, "the miner kept running after bitlaForge died")


if __name__ == "__main__":
    unittest.main()
