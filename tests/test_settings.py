"""Settings: reading 0.2.x files, saving safely, never over a broken file.
Every test works in a temporary folder. Run: python -m unittest discover tests"""

import tempfile
import unittest
from pathlib import Path

from bitlaforge import backups, pools
from bitlaforge.settings import CORES, GENTLE, NORMAL, Config, typed

WALLET = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"
OLD = f'''# my notes about mining
pool = "stratum+tcp://stratum.ckpool.org:3333"
wallet = "{WALLET}"
algorithm = "sha256d"
threads = "8"
miner_name = "tphome02"
niceness = "0"
'''


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "config.toml"

    def load(self, text=None):
        if text is not None:
            self.path.write_text(text)
        return Config.load(self.path)


class ReadingOldFiles(Base):
    def test_0_2_x_text_values(self):
        c = self.load(OLD)
        self.assertTrue(c.readable)
        self.assertEqual(c.value("threads"), min(8, CORES))
        self.assertEqual(c.value("niceness"), NORMAL)
        self.assertEqual(c.value("pool"), "stratum+tcp://stratum.ckpool.org:3333")
        self.assertEqual(c.value("miner_name"), "tphome02")
        self.assertTrue(c.value("heat_pause"))            # new settings: their defaults
        self.assertEqual(c.value("heat_limit"), 85)

    def test_zero_threads_meant_every_core(self):
        self.assertEqual(typed("threads", "0"), CORES)
        self.assertEqual(typed("threads", "abc"), max(1, CORES - 1))
        self.assertEqual(typed("niceness", "5"), GENTLE)
        self.assertEqual(typed("heat_limit", 200), 95)

    def test_no_file_yet(self):
        c = self.load()
        self.assertTrue(c.readable)
        self.assertEqual(c.value("pool"), pools.DEFAULT)
        self.assertEqual(c.not_ready(), ["No wallet yet: add yours in Settings."])


class Saving(Base):
    def test_only_changes_are_written_notes_stay(self):
        c = self.load(OLD)
        n = 1 if min(8, CORES) != 1 else 2               # a real change on any computer (VMs have 2 cores)
        c.set("threads", n)
        c.set("heat_limit", 80)
        self.assertEqual(c.changes(), [("Cores to use", f"{min(8, CORES)} of {CORES} cores", f"{n} of {CORES} cores"),
                                       ("Pause at", "85 °C", "80 °C")])
        c.save()
        text = self.path.read_text()
        self.assertIn("# my notes about mining", text)
        self.assertIn('algorithm = "sha256d"', text)       # a setting 1.0 doesn't use stays
        self.assertIn(f"threads = {n}", text)
        self.assertIn("heat_limit = 80", text)
        self.assertIn('niceness = "0"', text)              # untouched settings keep their form
        self.assertEqual(c.change_count, 0)
        self.assertEqual(Config.load(self.path).value("threads"), n)

    def test_one_backup_per_save(self):
        c = self.load(OLD)
        c.set("threads", 2)
        c.set("niceness", GENTLE)
        c.set("odds", False)
        made = c.save()
        all_ = backups.list_all(path=self.path)
        self.assertEqual(len(all_), 1)
        self.assertEqual(all_[0].path, made)
        self.assertEqual(made.read_text(), OLD)           # the backup is the file before the save

    def test_setting_it_back_is_no_change(self):
        c = self.load(OLD)
        c.set("threads", 2)
        c.set("threads", min(8, CORES))
        self.assertEqual(c.change_count, 0)

    def test_a_new_file_is_private(self):
        c = self.load()
        c.set("wallet", WALLET)
        self.assertIsNone(c.save())                       # nothing to back up yet
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(Config.load(self.path).value("wallet"), WALLET)

    def test_a_link_stays_a_link(self):
        real = self.dir / "dotfiles" / "bitla.toml"
        real.parent.mkdir()
        real.write_text(OLD)
        self.path.symlink_to(real)
        c = self.load()
        c.set("threads", 1)
        c.save()
        self.assertTrue(self.path.is_symlink())
        self.assertIn("threads = 1", real.read_text())


class BrokenFile(Base):
    def test_never_saved_over(self):
        # F-5 (#8): 0.2.1 read a broken file as blank settings and the next save replaced it
        broken = OLD.replace('threads = "8"', 'threads = "8')
        c = self.load(broken)
        self.assertFalse(c.readable)
        self.assertIn("Line", c.error)
        self.assertEqual(c.not_ready(), ["The settings file can't be read."])
        c.set("threads", 2)
        with self.assertRaises(ValueError):
            c.save()
        self.assertEqual(self.path.read_text(), broken)

    def test_restore_brings_it_back(self):
        c = self.load(OLD)
        c.set("threads", 2)
        c.save()
        self.path.write_text("not = = toml")
        newest = backups.list_all(path=self.path)[0]
        backups.restore(newest, path=self.path)
        self.assertEqual(self.path.read_text(), OLD)
        self.assertEqual(backups.list_all(path=self.path)[0].note, "Before restoring a backup")


class Checks(Base):
    def test_a_bad_wallet_stops_the_save(self):
        c = self.load(OLD)
        c.set("wallet", WALLET[:-1] + "q")
        self.assertEqual(len(c.problems()), 1)
        self.assertIn("check digits", c.problems()[0])

    def test_pool_addresses(self):
        c = self.load(OLD)
        c.set("pool", "eusolo.ckpool.org:3333")
        self.assertEqual(c.value("pool"), "stratum+tcp://eusolo.ckpool.org:3333")
        self.assertEqual(c.problems(), [])
        for bad, words in (("solo.ckpool.org", "port"), ("", "No pool"), ("solo ckpool:3333", "isn't a pool")):
            self.assertIn(words, pools.problem(bad), bad)
        self.assertEqual(pools.label("stratum+tcp://solo.ckpool.org:3333"), "solo.ckpool.org · worldwide")
        self.assertEqual(pools.label("stratum+tcp://stratum.ckpool.org:3333"), "stratum.ckpool.org:3333")


if __name__ == "__main__":
    unittest.main()
