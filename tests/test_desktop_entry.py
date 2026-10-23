"""#12 (next release): the package ships bitlaforge.desktop, so the app shows in every app menu and launcher —
not only in hypeForge, which carries its own copy until then. Same pattern as nogForge's #16."""

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopEntry(unittest.TestCase):
    def test_the_entry_is_there_and_valid(self):
        p = ROOT / "bitlaforge.desktop"
        self.assertTrue(p.is_file(), "bitlaforge.desktop at the repository root (the recipe installs it)")
        text = p.read_text()
        for line in ("[Desktop Entry]", "Type=Application", "Name=bitlaForge", "Exec=bitlaforge", "TryExec=bitlaforge",
                     "Terminal=true", "Icon=utilities-system-monitor", "Categories=System;Monitor;"):
            self.assertIn(line, text, f"{line} in the entry")
        validate = shutil.which("desktop-file-validate")
        if not validate:
            self.skipTest("desktop-file-validate isn't installed here")
        r = subprocess.run([validate, str(p)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.strip(), "", "no hints either: " + r.stdout)


if __name__ == "__main__":
    unittest.main()
