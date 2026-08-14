from pathlib import Path
import sys
p=Path(__file__).resolve().parents[1]/'backend';sys.path.insert(0,str(p))
from app.main import app  # noqa:E402,F401
