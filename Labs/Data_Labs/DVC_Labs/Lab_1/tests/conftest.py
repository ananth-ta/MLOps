import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent.parent
# The stages import each other as plain modules (DVC runs them as `python src/<stage>.py`)
sys.path.insert(0, str(LAB_DIR / "src"))
sys.path.insert(0, str(LAB_DIR / "scripts"))
