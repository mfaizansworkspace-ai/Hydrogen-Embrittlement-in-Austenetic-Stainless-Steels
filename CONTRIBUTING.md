# Contributing to HE-Austenite

Thanks for considering a contribution. This dataset is a literature compilation, so a
contribution is almost always one of three things: new records, missing fields on
existing records, or an independent re-check of records someone else extracted. All
three are welcome. This file says how to do each so the pull request can be merged
without a long back-and-forth.

Maintainer and lead author: Muhammad Faizan (`<your email>`, ORCID `<your ORCID>`).

---

## 1. Before you write any code

**Work against the current release.** v0.2 is the baseline. The untagged snapshot that
was downloadable from 23 September 2026, which some users cite as v0.1, differs: the
Sandia records are renamed from `SAND-2101-…` to `SAND2012-ch2101-…`, because the report
number and the chapter number were confusable, three electron-beam welds are recoded
from `laser` to `EBW`, and several values are corrected. v0.2 added composition on top
of that and changed no mechanical property, ratio or identifier, so analysis code
written against the renamed identifiers still runs.

**Open an issue first.** Say which papers or fields you intend to work on. This avoids
two people extracting the same tables, and it lets me tell you if a source is already
logged as excluded. The extraction log in `docs/` records every source that was
considered and why it was kept or dropped.

**Scope.** The dataset covers hydrogen **gas** exposure only: in-situ slow strain rate
testing in H₂ gas, and specimens thermally precharged in H₂ gas and then tested.
Electrochemically or cathodically charged studies are out of the main table and belong
in `data/excluded_electrochemical.csv`, because hydrogen fugacity from cathodic charging
cannot be converted to an equivalent gas pressure without assumptions. One record = one
reported test condition.

---

## 2. Provenance rules

These are the rules the dataset's credibility rests on. A pull request that breaks one
will be asked to change before anything else is reviewed.

1. **Every value is traceable to a published source.** Give the DOI, and the table or
   page the number came from.
2. **Numbers come from tables and text, not from figures.** If a value exists only in a
   plot, it is either left empty or recorded with `source_type = figure_read` and a note
   saying how it was read. Figure-read values are never mixed silently with tabulated
   ones.
3. **No PDFs in the repository.** Extract the numbers; leave the papers where they are.
4. **Missing is empty.** An unreported value is an empty cell. Never `0`, never `N/A`,
   never a guess, never a value carried over from a different heat or condition.
5. **Reported and derived are separate.** Anything computed from other columns is
   produced by a script, never typed in by hand (see §4).

---

## 3. Composition columns (the current gap)

Composition arrived in v0.2 and covers 102 of 113 records. What is still open is the
eleven records whose source names no heat, any heat whose published analysis is partial,
and nitrogen, which only 55 records carry.

Compositions live in `data/compositions.csv`, one row per heat, weld deposit or filler,
and `data/record_composition_map.csv` says which record uses which. Add a composition by
adding a row to the first and a mapping to the second; never type values into the records
or into the exported CSV. Element columns are in **weight percent**:

| Column | Notes |
|---|---|
| `C` | as printed, e.g. `0.024` |
| `Si`, `Mn`, `Cr`, `Ni`, `Mo` | as printed; leave empty where the grade carries none |
| `N` | as printed |
| `Cu`, `Nb`, `Ti` | only where reported; `Ti` and `Nb` matter for 321 and 347 |

And these alongside them:

| Column | Allowed values | Why |
|---|---|---|
| `composition_basis` | `heat_analysis`, `nominal`, `spec_midpoint` | A specification midpoint is not a measurement. Mixing the two silently is the main way a compilation like this goes wrong. |
| `composition_source` | free text, e.g. `Yamabe 2017, Table 1, steel D` | Points to the exact table so the number can be re-checked in under a minute. |
| `derive_nieq`, `derive_md30` | `yes` / `no` | Whether the two expressions apply to this material. Both are `no` for duplex; Md30 is `no` for precipitation-strengthened alloys. |

Rules:

- A composition applies to the record only if it is the **same heat or the same filler
  and weld pass** as the mechanical test. If the paper reports a base-metal analysis and
  a weld-metal analysis, do not apply the base-metal row to a weld-metal record.
- Where only a specification range is published, either leave composition empty or record
  the midpoint with `composition_basis = spec_midpoint`. Do not treat it as measured.
- Do not edit the composition of a record that already has one without saying why in the
  pull request.

---

## 4. Derived columns

`ni_equivalent` and `md30_calculated` are computed by `scripts/apply_compositions.py`
and are flagged as derived. Do not type them in, and do not introduce a second formula.

The nickel equivalent uses Hirayama's six-element form,
`Ni + 0.65Cr + 0.98Mo + 1.05Mn + 0.35Si + 12.6C`, with no nitrogen term. That choice is
not arbitrary: it reproduces the values printed by Nakamura et al. (2018) and Fukunaga
(2024) exactly. Md₃₀ follows Angel,
`Md30 (°C) = 413 − 462(C+N) − 9.2Si − 8.1Mn − 13.7Cr − 9.5Ni − 18.5Mo`. Where a source
prints its own nickel equivalent on a different expression, it goes in
`ni_equivalent_reported` and is not mixed into the recomputed column. If you think a
different expression is the better choice, open an issue and argue it there; changing it
is a release-level decision, because it moves every derived value.

A record only gets a derived value when every element the formula needs is present.
Partial composition means an empty derived cell, not a partial calculation.

---

## 5. Verification and re-checks

An independent re-extraction is a real contribution and is tracked as one.

- Work from the original source, not from the dataset. Record what you read, then compare.
- Where you agree, set the verification field for that record and name yourself.
- Where you disagree, do not overwrite the existing value. Add a row to the extraction
  log with both values, the source location for each, and your reasoning. Disagreements
  are resolved in the pull request, and the resolution is logged.
- Agreement rates between independent extractors are reported in the dataset
  documentation, so a disagreement found is a useful result, not a problem.

---

## 6. Pull request checklist

- [ ] Branched from v0.2 or later
- [ ] The validation script passes
- [ ] The build runs end to end from a fresh clone (`normalise` → `apply_compositions` → `build_outputs` → `build_workbook` → `make_figures`) and reproduces the CSV byte for byte
- [ ] No existing `record_id` changed or removed
- [ ] Every new or changed value has its source location recorded
- [ ] The extraction log is updated, including anything you considered and rejected
- [ ] Derived columns regenerated by the script, not edited
- [ ] The pull request says in one paragraph what was added and from which sources

---

## 7. Credit

Credit is agreed before work starts, in the issue, so nobody is guessing later.

- **Every contributor** is listed in `CONTRIBUTORS.md` with what they contributed, in
  CRediT terms (data curation, validation, software, and so on).
- **A substantial data or validation contribution** earns authorship on the Zenodo
  deposit for the release that contains it. "Substantial" means something like a new
  source family, a field populated across a meaningful share of records, or an
  independent re-check of a large block of rows. The maintainer remains first author and
  corresponding author.
- **Co-authorship on a manuscript** follows the usual standard: it needs a contribution
  to the written work, not only to the data — typically drafting or substantially
  revising a section, such as a technical validation or an analysis the paper reports.
  Data-only contributions are acknowledged by name in the paper and credited on the
  deposit. If you want to move from one to the other, say so early and we will agree the
  section.
- **Analyses you build on the dataset are yours.** Publish them under your own name. The
  only ask is that you cite the dataset by its DOI and state which version you used.

## 8. Licences

Data is CC BY 4.0; code is MIT. By opening a pull request you confirm that you are
entitled to contribute the material and that it may be released under those licences.
Extracted numerical values are facts from the literature, cited to their sources; do not
contribute copied text, tables as images, or figures from publications.
