"""The wallet check, against the examples in Bitcoin's own specifications
(BIP173, BIP350) and the best-known addresses. Run: python -m unittest discover tests"""

import unittest

from bitlaforge.wallet import check, short

GENESIS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"           # the very first block's address
P2SH = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"              # BIP13's example
SEGWIT = "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4"    # BIP173, valid
SEGWIT32 = "bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3"  # BIP173, 32 bytes
TAPROOT = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"  # BIP350, valid


class Valid(unittest.TestCase):
    def test_every_kind(self):
        for addr, kind in ((GENESIS, "legacy"), (P2SH, "script"), (SEGWIT, "SegWit"),
                           (SEGWIT.lower(), "SegWit"), (SEGWIT32, "SegWit"), (TAPROOT, "Taproot")):
            with self.subTest(addr=addr):
                c = check(addr)
                self.assertTrue(c.ok, c.problem)
                self.assertEqual(c.kind, kind)

    def test_spaces_around_are_ignored(self):
        self.assertTrue(check(f"  {TAPROOT}\n").ok)


class Invalid(unittest.TestCase):
    def assertBad(self, addr, words):
        c = check(addr)
        self.assertFalse(c.ok, addr)
        self.assertIn(words, c.problem)

    def test_one_character_mistyped(self):
        for good in (GENESIS, P2SH, SEGWIT.lower(), TAPROOT):
            i = len(good) // 2
            swap = "q" if good[i] != "q" else "p"
            if good[0] in "13":
                swap = "2" if good[i] != "2" else "3"
            with self.subTest(addr=good):
                self.assertBad(good[:i] + swap + good[i + 1:], "check digits")

    def test_one_character_missing(self):
        self.assertBad(TAPROOT[:-1], "check digits")
        self.assertFalse(check(GENESIS[:-1]).ok)

    def test_wrong_checksum_kind(self):
        # BIP350: a version-0 address with the newer (bech32m) checksum, and the reverse
        self.assertBad("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kemeawh", "check digits")
        self.assertBad("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqh2y7hd", "check digits")

    def test_mixed_case(self):
        self.assertBad("bc1qW508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", "capital")

    def test_test_network(self):
        self.assertBad("tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx", "test-network")
        self.assertBad("mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn", "test-network")

    def test_not_an_address(self):
        self.assertBad("", "No wallet address")
        self.assertBad("hello", "start with bc1, 1 or 3")
        self.assertBad("bc1q w508", "space")
        self.assertBad("1A1zP1eP5QGefi2DMPTfTL5SLmv7Div0Na", "'0'")      # 0 is never used
        self.assertBad("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3tb", "'b'")


class Short(unittest.TestCase):
    def test_keeps_both_ends(self):
        s = short(TAPROOT, 24)
        self.assertEqual(len(s), 24)
        self.assertTrue(s.startswith("bc1p0xlxvl") and s.endswith(TAPROOT[-12:]))
        self.assertEqual(short(GENESIS, 40), GENESIS)


if __name__ == "__main__":
    unittest.main()
