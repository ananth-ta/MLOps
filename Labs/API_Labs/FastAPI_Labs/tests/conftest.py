import sys
from pathlib import Path

# The app imports its modules as plain names (uvicorn runs it with --app-dir src)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
