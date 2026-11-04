#!/bin/sh
# Runs every content check in tools/ (each tools/check_*.py). CI calls this.
set -e
cd "$(dirname "$0")/.."
status=0
for check in tools/check_*.py; do
  [ -e "$check" ] || continue
  python3 "$check" || status=1
done
exit $status
