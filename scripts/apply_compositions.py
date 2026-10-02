"""Join per-heat compositions onto the extracted records.

Reads  data/compositions.csv            one row per heat, with its source table
       data/record_composition_map.csv  which record uses which heat
       data/records_raw.json            the extracted records

Writes data/records_raw.json in place, filling composition_wt_pct,
composition_basis and composition_source, then recomputing ni_equivalent and
md30_calculated from the composition.

Rules, applied here and nowhere else:
  - A composition is attached to a record only when the source reports it for
    the same heat, weld deposit or filler as the mechanical test.
  - Values already present on a record are never overwritten.
  - Derived values are computed only where the expression applies, set per heat
    by derive_nieq and derive_md30 in compositions.csv. Md30 is not computed for
    duplex or precipitation-strengthened alloys; the Ni equivalent is not
    computed for duplex.
  - A Ni equivalent printed by the source is moved to ni_equivalent_reported and
    the ni_equivalent column is recomputed for every record from one expression,
    so the column is comparable across sources.
  - Mo and N that a source does not report are taken as zero ONLY for grades
    whose specification does not call for them; the assumption is recorded in
    the record's derived_assumptions field.

    python scripts/apply_compositions.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from normalise import md30, ni_equivalent_hirayama

DATA = Path("data")
ELEMENTS = ["C", "Si", "Mn", "Cr", "Ni", "Mo", "N", "Cu", "Nb", "Ti"]
# Grades whose specification carries no deliberate Mo or N addition: an unreported
# value is a true absence rather than an unmeasured one.
NO_MO = ("304", "304L", "321", "347", "21-6-9", "310")
NO_N = ("304", "304L", "316", "316L", "317L", "321", "347", "310")


def load_compositions() -> dict[str, dict]:
    out = {}
    for row in csv.DictReader((DATA / "compositions.csv").open(encoding="utf-8")):
        comp = {el: float(row[el]) for el in ELEMENTS if row.get(el, "").strip()}
        out[row["comp_key"]] = {
            "composition": comp,
            "basis": row["composition_basis"],
            "source": row["composition_source"],
            "derive_nieq": row["derive_nieq"] == "yes",
            "derive_md30": row["derive_md30"] == "yes",
            "label": row["material_label"],
        }
    return out


def assumed_zeros(alloy: str, comp: dict) -> list[str]:
    """Elements we treat as zero for the derived values, with the grade's consent."""
    out = []
    if "Mo" not in comp and any(g in alloy for g in NO_MO):
        out.append("Mo")
    if "N" not in comp and any(g in alloy for g in NO_N):
        out.append("N")
    return out


def main() -> None:
    comps = load_compositions()
    mapping = {r["record_id"]: r["comp_key"]
               for r in csv.DictReader((DATA / "record_composition_map.csv").open(encoding="utf-8"))}
    recs = json.load((DATA / "records_raw.json").open(encoding="utf-8"))

    filled = derived_nieq = derived_md30 = 0
    for r in recs:
        key = mapping.get(r["record_id"])
        if not key:
            continue
        entry = comps[key]
        comp = dict(entry["composition"])
        if not r.get("composition_wt_pct"):
            r["composition_wt_pct"] = comp
            filled += 1
        else:
            comp = {**comp, **r["composition_wt_pct"]}  # keep what was already extracted
            r["composition_wt_pct"] = comp
        r["composition_basis"] = entry["basis"]
        r["composition_source"] = entry["source"]

        if not (entry["derive_nieq"] or entry["derive_md30"]):
            continue
        work = dict(comp)
        assumed = assumed_zeros(r["alloy_grade"], comp)
        for el in assumed:
            work[el] = 0.0
        if assumed:
            r["derived_assumptions"] = f"{', '.join(assumed)} taken as 0 for the derived values"

        derived = r.setdefault("derived_fields", [])
        if entry["derive_nieq"]:
            if r.get("ni_equivalent") is not None and r.get("ni_equivalent_reported") is None:
                # the value carried before v0.2 was the one the source printed
                r["ni_equivalent_reported"] = r["ni_equivalent"]
            v = ni_equivalent_hirayama(work)
            if v is not None:
                r["ni_equivalent"] = round(v, 2)
                if "ni_equivalent" not in derived:
                    derived.append("ni_equivalent")
                derived_nieq += 1
        if entry["derive_md30"] and r.get("md30_calculated") is None:
            v = md30(work)
            if v is not None:
                r["md30_calculated"] = round(v, 1)
                derived.append("md30_calculated")
                derived_md30 += 1

    json.dump(recs, (DATA / "records_raw.json").open("w", encoding="utf-8"), indent=1)
    have = sum(1 for r in recs if r.get("composition_wt_pct"))
    print(f"{len(recs)} records")
    print(f"  composition present   {have}")
    print(f"    newly filled        {filled}")
    print(f"  ni_equivalent derived {derived_nieq}")
    print(f"  md30 derived          {derived_md30}")
    missing = [r["record_id"] for r in recs if not r.get("composition_wt_pct")]
    print(f"  still without         {len(missing)}: {', '.join(missing)}")


if __name__ == "__main__":
    main()
