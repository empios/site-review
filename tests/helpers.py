import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "site-review"
SCRIPTS = SKILL / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
