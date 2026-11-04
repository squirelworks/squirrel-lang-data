#!/usr/bin/env python3
"""Generate the JavaScript copy of features.json that apps ship.

Apps run offline and from file://, where pages can't fetch JSON, so they load
features.json as a plain script that sets window.LSD_FEATURES.

    python3 tools/gen_features.py OUT.js            write it
    python3 tools/gen_features.py OUT.js --check    exit 1 if OUT.js is out of date
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def render():
    data = json.loads((ROOT / "features.json").read_text(encoding="utf-8"))
    try:
        sha = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h", "--", "features.json"],
                             check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = ""
    head = ("// Generated from squirrel-lang-data features.json"
            + (f" (last changed in {sha})" if sha else "")
            + " by tools/gen_features.py. Don't edit; change features.json and regenerate.\n")
    return head + "window.LSD_FEATURES = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__.strip()); return 2
    out = Path(args[0])
    want = render()
    if "--check" in sys.argv:
        have = out.read_text(encoding="utf-8") if out.exists() else ""
        if have != want:
            print(f"{out}: out of date; run tools/gen_features.py {out}")
            return 1
        print(f"{out}: up to date")
        return 0
    out.write_text(want, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
