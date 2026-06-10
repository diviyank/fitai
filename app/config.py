import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("FITAI_DB_PATH", REPO_ROOT / "data" / "fitai.db"))
APP_TITLE = "fitai"
