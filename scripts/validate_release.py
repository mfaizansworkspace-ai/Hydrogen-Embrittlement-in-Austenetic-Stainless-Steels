"""Validate a release before it is deposited.

Everything here is recomputed from the released CSV and the source tables that feed
it, never from the intermediate JSON, so a bug in the pipeline cannot validate
itself. Exit code 0 means the release is publishable.

    python scripts/validate_release.py

Checks, in order:
  1  structure      row count, unique identifiers, expected columns
  2  schema         records_raw.json validates against scripts/schema.json
  3  composition    every element value matches compositions.csv through the record map
  4  ni_equivalent  recomputed independently from the CSV's own element columns
  5  reported       ni_equivalent_reported appears only where a source printed one
  6  md30           recomputed, and only inside the fitted composition range
  7  ratios         relative_ratio equals property_h2 / property_reference where both exist
  8  ranges         physical plausibility of every numeric field
  9  duplicates     identical measurements across sources are flagged in notes
 10  dictionary     completeness figures match the data
 11  statistics     every figure quoted in README.md is reproduced
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

DATA = Path("data")
CSV = DATA / "he_austenite_v0.3.csv"
ELEMENTS = ["C", "Si", "Mn", "Cr", "Ni", "Mo", "N", "Cu", "Nb", "Ti"]
fails: list[str] = []
notes: list[str] = []


def fail(check: str, msg: str) -> None:
    fails.append(f"[{check}] {msg}")


def num(v):
    v = (v or "").strip()
    return float(v) if v else None


def main() -> int:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    comps = {r["comp_key"]: r for r in csv.DictReader((DATA / "compositions.csv").open(encoding="utf-8"))}
    cmap = {r["record_id"]: r["comp_key"]
            for r in csv.DictReader((DATA / "record_composition_map.csv").open(encoding="utf-8"))}

    # 1 structure
    if len(rows) != 113:
        fail("structure", f"{len(rows)} rows, expected 113")
    ids = [r["record_id"] for r in rows]
    if len(set(ids)) != len(ids):
        fail("structure", "record_id is not unique")
    if len(rows[0]) != 45:
        fail("structure", f"{len(rows[0])} columns, expected 45")

    # 2 schema
    sys.path.insert(0, "scripts")
    from normalise import md30, md30_applies, ni_equivalent_hirayama, validate
    errs = validate(json.load((DATA / "records_raw.json").open(encoding="utf-8")))
    if errs:
        fail("schema", f"{len(errs)} schema errors, first is {errs[0]}")

    for r in rows:
        rid = r["record_id"]
        key = cmap.get(rid)
        comp = {e: num(r[f"{e}_wt_pct"]) for e in ELEMENTS}
        have = {e: v for e, v in comp.items() if v is not None}

        # 3 composition matches its declared source
        if key:
            src = comps[key]
            for e in ELEMENTS:
                want, got = num(src.get(e)), comp[e]
                if want != got:
                    fail("composition", f"{rid} {e} is {got}, compositions.csv says {want}")
            if r["composition_basis"] != src["composition_basis"]:
                fail("composition", f"{rid} basis is {r['composition_basis']}, expected {src['composition_basis']}")
            if r["composition_source"] != src["composition_source"]:
                fail("composition", f"{rid} composition_source does not match compositions.csv")
        elif have:
            fail("composition", f"{rid} carries a composition but no entry in the record map")

        derive_nieq = key and comps[key]["derive_nieq"] == "yes"
        derive_md30 = key and comps[key]["derive_md30"] == "yes"
        work = dict(have)
        for e in ("Mo", "N"):
            if e not in work:
                work[e] = 0.0

        # 4 ni_equivalent recomputed from the CSV's own columns
        want = ni_equivalent_hirayama(work) if derive_nieq else None
        got = num(r["ni_equivalent"])
        if want is None and got is not None:
            fail("ni_equivalent", f"{rid} has {got} but should have none")
        elif want is not None and (got is None or abs(round(want, 2) - got) > 0.005):
            fail("ni_equivalent", f"{rid} is {got}, recomputes to {None if want is None else round(want,2)}")

        # 5 reported values only where a source printed one
        declared = num(comps[key].get("ni_equivalent_reported")) if key else None
        rep = num(r["ni_equivalent_reported"])
        if declared != rep:
            fail("reported", f"{rid} ni_equivalent_reported is {rep}, compositions.csv declares {declared}")

        # 6 md30 recomputed, inside its fitted range only
        want = md30(work) if derive_md30 else None
        got = num(r["md30_calculated"])
        if want is None and got is not None:
            fail("md30", f"{rid} has {got} but the expression does not apply")
        elif want is not None and (got is None or abs(round(want, 1) - got) > 0.05):
            fail("md30", f"{rid} is {got}, recomputes to {round(want,1)}")
        if got is not None:
            if got < -273.15:
                fail("md30", f"{rid} Md30 {got} C is below absolute zero")
            if not md30_applies(work):
                fail("md30", f"{rid} Md30 computed outside the fitted composition range")

        # 7 ratios
        a, h, rr = num(r["property_reference"]), num(r["property_h2"]), num(r["relative_ratio"])
        if a and h is not None and rr is not None and abs(round(h / a, 3) - rr) > 0.0015:
            fail("ratios", f"{rid} ratio {rr} does not equal {h}/{a}")
        if rr is None:
            fail("ratios", f"{rid} has no relative_ratio")

        # 8 ranges
        p, tK, tC = num(r["h2_pressure_MPa"]), num(r["test_temperature_K"]), num(r["test_temperature_C"])
        if rr is not None and not 0 < rr < 2:
            fail("ranges", f"{rid} relative_ratio {rr} is outside 0 to 2")
        if p is not None and not 0 < p <= 200:
            fail("ranges", f"{rid} pressure {p} MPa is implausible")
        if tK is not None and not 77 <= tK <= 900:
            fail("ranges", f"{rid} temperature {tK} K is implausible")
        if tK is not None and tC is not None and abs((tK - 273.15) - tC) > 0.051:
            fail("ranges", f"{rid} {tK} K and {tC} C disagree")
        for e, v in have.items():
            if not 0 <= v <= 60:
                fail("ranges", f"{rid} {e} {v} wt% is implausible")
        if r["is_weld"] not in ("yes", "no"):
            fail("ranges", f"{rid} is_weld is {r['is_weld']}")
        if (r["zone"] == "base metal") != (r["is_weld"] == "no"):
            fail("ranges", f"{rid} zone {r['zone']} disagrees with is_weld {r['is_weld']}")

    # 9 duplicated measurements across sources
    seen: dict[tuple, str] = {}
    for r in rows:
        k = (r["alloy"], r["property_name"], r["property_reference"], r["property_h2"], r["relative_ratio"])
        if not r["property_reference"]:
            continue
        if k in seen:
            first, second = seen[k], r["record_id"]
            flagged = any(w in (x["notes"] or "").lower() for x in rows
                          if x["record_id"] in (first, second) for w in ("duplicat", "matches caskey", "same measurement"))
            if r["source_short"] != next(x["source_short"] for x in rows if x["record_id"] == first):
                if flagged:
                    notes.append(f"duplicate across sources, flagged in notes: {first} and {second}")
                else:
                    fail("duplicates", f"{first} and {second} report the same measurement and neither says so")
        else:
            seen[k] = r["record_id"]

    # 10 dictionary
    import subprocess
    out = subprocess.run([sys.executable, "scripts/check_dictionary.py"], capture_output=True, text=True)
    if out.returncode:
        fail("dictionary", out.stdout.strip().replace("\n", " | "))

    # 11 statistics quoted in the README
    import numpy as np
    import pandas as pd
    from scipy import stats as st
    d = pd.read_csv(CSV)
    d["comp_key"] = d.record_id.map(cmap)
    ra = d[(d.property_name == "reduction of area") & d.relative_ratio.notna() & d.ni_equivalent.notna()
           & (d.material_family != "precipitation-strengthened (A286)")
           & (d.record_id != "SAND2012-ch2101-T3111-5")]
    mat = ra.groupby("comp_key").agg(rra=("relative_ratio", "median"), nieq=("ni_equivalent", "first"),
                                     md=("md30_calculated", "first"), weld=("is_weld", "first"))
    claims = {
        "54 analysis records": (len(ra), 54),
        "24 materials": (len(mat), 24),
        "rho Nieq": (round(st.spearmanr(mat.nieq, mat.rra).statistic, 2), 0.60),
        "p Nieq": (round(st.spearmanr(mat.nieq, mat.rra).pvalue, 3), 0.002),
        "materials below 26.3": (int((mat.nieq < 26.3).sum()), 10),
        "materials at or above": (int((mat.nieq >= 26.3).sum()), 14),
        "median below": (round(mat[mat.nieq < 26.3].rra.median(), 2), 0.64),
        "median at or above": (round(mat[mat.nieq >= 26.3].rra.median(), 2), 0.95),
        "records below": (int((ra.ni_equivalent < 26.3).sum()), 27),
        "records at or above": (int((ra.ni_equivalent >= 26.3).sum()), 27),
        "record median below": (round(ra[ra.ni_equivalent < 26.3].relative_ratio.median(), 2), 0.52),
        "record median at or above": (round(ra[ra.ni_equivalent >= 26.3].relative_ratio.median(), 2), 0.93),
    }
    m2 = mat.dropna(subset=["md"])
    claims["rho Md30"] = (round(st.spearmanr(m2.md, m2.rra).statistic, 2), -0.43)
    claims["Md30 materials"] = (len(m2), 14)
    f304 = ra[ra.material_family == "300-series (304 type)"].groupby("comp_key").agg(
        rra=("relative_ratio", "median"), nieq=("ni_equivalent", "first"))
    claims["rho within 304"] = (round(st.spearmanr(f304.nieq, f304.rra).statistic, 2), -0.12)
    claims["304 materials"] = (len(f304), 9)
    g = ra[ra.reference_environment.isin(["air", "helium"])].groupby("comp_key").agg(
        rra=("relative_ratio", "median"), nieq=("ni_equivalent", "first"))
    claims["rho air and helium"] = (round(st.spearmanr(g.nieq, g.rra).statistic, 2), 0.63)
    for band, weld, want in (("lo", "no", 0.71), ("lo", "yes", 0.47), ("hi", "no", 0.99), ("hi", "yes", 0.86)):
        sub = mat[(mat.nieq < 26.3) if band == "lo" else (mat.nieq >= 26.3)]
        claims[f"median {band} {weld}"] = (round(sub[sub.weld == weld].rra.median(), 2), want)
    for name, (got, want) in claims.items():
        if got != want:
            fail("statistics", f"{name} is {got}, README says {want}")

    for n in notes:
        print(f"  note  {n}")
    for f in fails:
        print(f"  FAIL  {f}")
    print(f"\n{len(rows)} records, {len(fails)} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
