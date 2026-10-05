"""Check every 'N of 113' completeness figure in docs/data_dictionary.md against the CSV.

Those figures were typed by hand once and two of them were wrong. This script makes
that failure loud instead of silent.

    python scripts/check_dictionary.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

DICT = Path("docs/data_dictionary.md")
CSV = Path("data/he_austenite_v0.3.csv")


def main() -> int:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    total = len(rows)
    filled = {c: sum(1 for r in rows if (r.get(c) or "").strip()) for c in rows[0]}

    bad = []
    for line in DICT.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        claim = re.search(rf"(\d+)\s+of\s+{total}\b", cols[-1]) if cols else None
        if not claim:
            continue
        for name in re.findall(r"`([^`]+)`", cols[0]):
            if name in filled and filled[name] != int(claim.group(1)):
                bad.append((name, int(claim.group(1)), filled[name]))

    for name, claimed, actual in bad:
        print(f"  {name}: dictionary says {claimed} of {total}, data has {actual}")
    print(f"{len(bad)} mismatch(es) in {DICT}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
