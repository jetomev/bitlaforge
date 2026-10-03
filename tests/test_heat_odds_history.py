"""Heat, the lottery odds, and History — with a fake sensor folder, the
network's real numbers from 2 Oct 2026, and a temporary History file.
Run: python -m unittest discover tests"""

import tempfile
import time
import unittest
from pathlib import Path

from bitlaforge import heat, history, odds


def sensor(root: Path, n: int, name: str, temps: dict[str, int]) -> None:
    h = root / f"hwmon{n}"
    h.mkdir(parents=True)
    (h / "name").write_text(name + "\n")
    for i, (label, milli) in enumerate(temps.items(), 1):
        (h / f"temp{i}_input").write_text(f"{milli}\n")
        if label:
            (h / f"temp{i}_label").write_text(label + "\n")


class Heat(unittest.TestCase):
    def test_amd_uses_tctl(self):
        root = Path(tempfile.mkdtemp())
        sensor(root, 0, "acpitz", {"": 99000})           # a motherboard sensor: ignored
        sensor(root, 1, "nvme", {"Composite": 70000})     # a drive: ignored
        sensor(root, 2, "k10temp", {"Tctl": 72375, "Tccd1": 65000})
        self.assertEqual(heat.processor_temp(root), 72.375)

    def test_intel_package(self):
        root = Path(tempfile.mkdtemp())
        sensor(root, 0, "coretemp", {"Package id 0": 81000, "Core 0": 79000, "Core 1": 83000})
        self.assertEqual(heat.processor_temp(root), 81.0)

    def test_no_sensor(self):
        root = Path(tempfile.mkdtemp())
        sensor(root, 0, "nvme", {"Composite": 40000})
        self.assertIsNone(heat.processor_temp(root))
        self.assertIsNone(heat.processor_temp(root / "missing"))

    def test_this_computer_has_one(self):
        t = heat.processor_temp()
        if t is None:
            self.skipTest("no processor sensor on this computer")
        self.assertTrue(10 < t < 110, t)

    def test_pause_and_resume_with_a_margin(self):
        self.assertEqual(heat.decide(84.9, 85, False, True), "")
        self.assertEqual(heat.decide(85.0, 85, False, True), "pause")
        self.assertEqual(heat.decide(82.0, 85, True, True), "")       # still too warm
        self.assertEqual(heat.decide(80.0, 85, True, True), "resume")
        self.assertEqual(heat.decide(99.0, 85, False, False), "")     # switched off
        self.assertEqual(heat.decide(99.0, 85, True, False), "resume")  # switched off while paused
        self.assertEqual(heat.decide(None, 85, True, True), "resume")   # sensor gone


class Odds(unittest.TestCase):
    DIFFICULTY = 1.33e14          # mempool.space, 2 Oct 2026, 22:55

    def test_the_numbers_on_the_design_page(self):
        day = odds.one_in(184_300, self.DIFFICULTY, 86_400)
        year = odds.one_in(184_300, self.DIFFICULTY, 365 * 86_400)
        self.assertEqual(odds.words(day), "1 in 36 billion")
        self.assertEqual(odds.words(year), "1 in 98 million")

    def test_words(self):
        self.assertEqual(odds.words(2_400_000), "1 in 2.4 million")
        self.assertEqual(odds.words(1_000_000), "1 in 1 million")
        self.assertEqual(odds.words(512), "1 in 512")
        self.assertEqual(odds.words(odds.one_in(0, self.DIFFICULTY, 60)), "none while stopped")
        self.assertEqual(odds.eh(975e18), "975 EH/s")

    def test_kept_between_runs_and_asked_hourly(self):
        p = Path(tempfile.mkdtemp()) / "network.json"
        n = odds.Network(self.DIFFICULTY, 975e18, 3.156, time.time() - 120)
        odds.save(n, p)
        back = odds.load(p)
        self.assertEqual(back, n)
        self.assertFalse(odds.due(back))
        self.assertTrue(odds.due(back, back.checked + 3600))
        self.assertTrue(odds.due(None))
        self.assertEqual(odds.checked_words(back), "2 min ago")
        p.write_text("{broken")
        self.assertIsNone(odds.load(p))


class History(unittest.TestCase):
    def setUp(self):
        self.p = Path(tempfile.mkdtemp()) / "history.json"

    def test_recorded_and_updated(self):
        s = history.Session(started=1_759_400_000.0)
        history.record(s, self.p)
        s.seconds, s.accepted, s.why = 3600, 5, "you stopped it"
        history.record(s, self.p)
        rows = history.load(self.p)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].seconds, rows[0].why), (3600, "you stopped it"))

    def test_a_session_cut_short_says_so(self):
        history.record(history.Session(started=1_759_400_000.0, seconds=60), self.p)
        self.assertEqual(history.close_unfinished(self.p), 1)
        self.assertEqual(history.load(self.p)[0].why, "bitlaForge closed unexpectedly")
        self.assertEqual(history.close_unfinished(self.p), 0)

    def test_totals_and_newest_first(self):
        base = 1_759_400_000.0
        for i, (secs, acc) in enumerate(((600, 1), (7200, 9), (60, 0))):
            history.record(history.Session(base + i * 90_000, secs, 100.0, acc, 0, "you stopped it"), self.p)
        rows = history.load(self.p)
        self.assertEqual([r.started for r in rows], sorted((r.started for r in rows), reverse=True))
        t = history.totals(rows)
        self.assertEqual((t.seconds, t.accepted, t.sessions), (7860, 10, 3))
        self.assertEqual(t.best_day, rows[1].when.strftime("%b %-d"))

    def test_a_broken_file_is_an_empty_history(self):
        self.p.write_text("not json")
        self.assertEqual(history.load(self.p), [])

    def test_duration_words(self):
        self.assertEqual(history.duration(12_240), "3 h 24 min")
        self.assertEqual(history.duration(720), "12 min")
        self.assertEqual(history.duration(42), "42 s")


if __name__ == "__main__":
    unittest.main()
