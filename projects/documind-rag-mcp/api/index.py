"""Vercel ASGI entrypoint."""

from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402,F401
