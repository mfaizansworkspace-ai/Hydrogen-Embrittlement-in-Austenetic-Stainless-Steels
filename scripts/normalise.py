"""Derived quantities and validation helpers for HE-Austenite."""
import json, sys, math
from jsonschema import Draft202012Validator  # pip install jsonschema

def ni_equivalent_hirayama(c):
    """Hirayama-Ogirima Ni equivalent (wt%), six elements, no nitrogen term.

    Nieq = Ni + 0.65 Cr + 0.98 Mo + 1.05 Mn + 0.35 Si + 12.6 C

    This is the form used in the hydrogen embrittlement literature this dataset
    draws on. It reproduces the published Nieq of Nakamura et al. (2018) Table 1
    (heat P, 29.88) and of Fukunaga (2024) Table 1 (SUS316CW, 28.5) exactly.
    Some authors use a nitrogen-bearing variant; where a source printed its own
    value it is kept in ni_equivalent_reported rather than mixed into this column.
    Returns None if any input is missing.
    """
    need = ("Ni","Cr","Mo","Si","Mn","C")
    if any(c.get(k) is None for k in need):
        return None
    return (c["Ni"] + 0.65*c["Cr"] + 0.98*c["Mo"] + 1.05*c["Mn"]
            + 0.35*c["Si"] + 12.6*c["C"])

# Angel fitted Md30 on Fe-Cr-Ni steels of roughly 300-series composition. Outside
# that range the linear form extrapolates wildly: applied to the nitrogen- and
# manganese-strengthened grades it returns temperatures below absolute zero, which
# is a sign the expression does not apply rather than a measure of stability.
MD30_DOMAIN = {"Mn": 2.5, "N": 0.12, "Cr": 21.0, "Mo": 3.0, "C": 0.15}


def md30_applies(c):
    """True when the composition sits inside the range Angel's expression was fitted on."""
    for el, limit in MD30_DOMAIN.items():
        if (c.get(el) or 0.0) > limit:
            return False
    return True


def md30(c):
    """Angel Md30 (degC): temperature for 50% martensite at 30% strain.

    Returns None outside the composition range the expression was fitted on.
    """
    need = ("C","Si","Mn","Cr","Ni","Mo")
    if any(c.get(k) is None for k in need):
        return None
    if not md30_applies(c):
        return None
    n = c.get("N") or 0.0
    return (413 - 462*(c["C"] + n) - 9.2*c["Si"] - 8.1*c["Mn"]
            - 13.7*c["Cr"] - 9.5*c["Ni"] - 18.5*c["Mo"])

def relative_ratio(rec):
    a, h = rec.get("property_reference"), rec.get("property_h2")
    if a in (None, 0) or h is None:
        return None
    return round(h / a, 3)

def validate(records, schema_path="scripts/schema.json"):
    schema = json.load(open(schema_path))
    v = Draft202012Validator(schema)
    errs = []
    for r in records:
        for e in v.iter_errors(r):
            errs.append((r.get("record_id"), e.message))
    return errs

if __name__ == "__main__":
    recs = json.load(open(sys.argv[1]))
    # Ni equivalent and Md30 are NOT computed here. They are computed in
    # apply_compositions.py, which knows from data/compositions.csv which
    # expressions apply to which material; computing them here as well would
    # quietly give duplex and precipitation-strengthened alloys values that do
    # not mean anything.
    for r in recs:
        derived = r.setdefault("derived_fields", [])
        if r.get("relative_ratio") is None:
            rr = relative_ratio(r)
            if rr is not None:
                r["relative_ratio"] = rr; derived.append("relative_ratio")
    errs = validate(recs)
    print(f"{len(recs)} records, {len(errs)} schema errors")
    for rid, m in errs[:20]:
        print(" ", rid, m)
    json.dump(recs, open(sys.argv[1], "w"), indent=1)
