#!/usr/bin/env python3
"""Every content file is formatted the way tools/fmt.py writes it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fmt  # noqa: E402

if __name__ == "__main__":
    status = fmt.main(["--check"])
    if not status:
        print("format: OK")
    sys.exit(status)
