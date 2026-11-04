#!/usr/bin/env python3
"""Runs the tools' own tests (tools/tests/test_*.py)."""
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(TOOLS / "tests"), top_level_dir=str(TOOLS / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
