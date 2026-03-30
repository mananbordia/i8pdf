"""Vercel serverless entry point — exposes the Flask app as a handler."""

import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
