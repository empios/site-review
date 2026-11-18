import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers import SCRIPTS

FAKE_NPX = """#!/bin/bash
# fake npx: find --output-path=... and write a minimal report there
for a in "$@"; do case "$a" in --output-path=*) out="${a#--output-path=}";; esac; done
echo '{"fake": true}' > "$out"
"""


class LighthouseRunsTest(unittest.TestCase):
    def run_script(self, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp, "bin")
            bin_dir.mkdir()
            npx = bin_dir / "npx"
            npx.write_text(FAKE_NPX)
            npx.chmod(0o755)
            chrome = bin_dir / "chrome"
            chrome.write_text("#!/bin/bash\nexit 0\n")
            chrome.chmod(0o755)
            out = Path(tmp, "out")
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", CHROME_PATH=str(chrome))
            r = subprocess.run(["bash", str(SCRIPTS / "lighthouse_runs.sh"), "https://e.com/", str(out), *extra],
                               capture_output=True, text=True, env=env, timeout=60)
            return r, sorted(p.name for p in out.glob("lh-*.json"))

    def test_default_three_mobile_three_desktop(self):
        r, files = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(files, [f"lh-desktop-{i}.json" for i in (1, 2, 3)] + [f"lh-mobile-{i}.json" for i in (1, 2, 3)])

    def test_subpage_mode_one_mobile_run(self):
        r, files = self.run_script("1", "0")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(files, ["lh-mobile-1.json"])
