"""Clean the extracted records and build the CSV + Excel deliverables."""
import json, re, csv, sys
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

SOURCES={
 "Caskey":dict(id="S1",cite="Caskey GR Jr. Hydrogen Compatibility Handbook for Stainless Steels. DP-1643, Savannah River Laboratory, June 1983.",link="https://www.osti.gov/biblio/5906050",access="open"),
 "San Marchi":dict(id="S2",cite="San Marchi C, Somerday BP (eds). Technical Reference on Hydrogen Compatibility of Materials. SAND2012-7321, Sandia National Laboratories, 2012.",link="https://h2tools.org/technical-reference",access="open"),
 "Balch":dict(id="S3",cite="Balch DK, San Marchi C, et al. Effect of hydrogen on tensile strength and ductility of multipass 304L/308L welds. PVP2015-45591, ASME, 2015.",link="",access="paywalled"),
 "Michler":dict(id="S4",cite="Michler T, Lee Y, Gangloff RP, Naumann J. Influence of macro segregation on hydrogen environment embrittlement of SUS 316L. Int J Hydrogen Energy 34(7) 2009: 3201-3209.",link="https://doi.org/10.1016/j.ijhydene.2009.02.015",access="paywalled"),
 "Nakamura":dict(id="S5",cite="Nakamura J, Okazaki S, Matsunaga H, Matsuoka S. SSRT and fatigue life properties of 317L weld metal in high-pressure hydrogen gas. Trans JSME 84(857) 2018 (Japanese).",link="https://doi.org/10.1299/transjsme.17-00437",access="open"),
 "Younes":dict(id="S6",cite="Younes CM, Steele AM, Nicholson JA, Barnett CJ. Influence of hydrogen content on the tensile properties and fracture of austenitic stainless steel welds. Int J Hydrogen Energy 38 2013: 4864-4876.",link="",access="paywalled"),
 "Iyer":dict(id="S7",cite="Iyer KJL. The influence of hydrogen on the mechanical properties and structure of a stable 304 stainless steel. Canadian Metallurgical Quarterly, 1989.",link="",access="paywalled"),
 "Fukunaga":dict(id="S8",cite="Fukunaga A. Hydrogen embrittlement behaviors during SSRT tests in gaseous hydrogen for cold-worked type 316 and A286 used in hydrogen refueling stations. Eng Failure Analysis 160 (2024) 108158.",link="https://doi.org/10.1016/j.engfailanal.2024.108158",access="paywalled"),
 "Matsuoka":dict(id="S9",cite="Matsuoka S, Yamabe J, Matsunaga H. Hydrogen-induced ductility loss of austenitic stainless steels for SSRT in high-pressure hydrogen gas. Solid State Phenomena 258 (2017) 259-264.",link="https://doi.org/10.4028/www.scientific.net/SSP.258.259",access="paywalled")}

FAM=[(r"^304",'300-series (304 type)'),(r"^316|^317",'300-series (316/317 type)'),
     (r"^321|^347",'300-series stabilised (321/347)'),(r"^310",'high-Ni austenitic (310)'),
     (r"21-6-9|Nitronic",'N-strengthened (21-6-9)'),(r"22-13-5",'N-strengthened (22-13-5)'),
     (r"2507|duplex",'duplex'),(r"A286",'precipitation-strengthened (A286)')]

def alloy_clean(a):
    a=(a.replace("Nitronic 40 (21-6-9)","21-6-9").replace(" (unspecified)","").replace(" (hi-Ni)"," hi-Ni")
        .replace("304L base / 308L filler weld","304L/308L weld")
        .replace("21-6-9 base / ER308L filler weld","21-6-9/308L weld")
        .replace("21-6-9 base / 21-6-9 filler weld","21-6-9/21-6-9 weld")
        .replace("SUS 316L","316L").replace("SUS316 hi-Ni","316 hi-Ni"))
    return re.sub(r"\s+heat\s+\S+","",a).strip()
def family(a):
    for p,f in FAM:
        if re.search(p,a,re.I): return f
    return "other"
def heat_of(a):
    m=re.search(r"heat\s+(\S+)",a,re.I); return m.group(1) if m else None

def clean(recs):
    rows=[]
    for r in recs:
        alloy=alloy_clean(r["alloy_grade"]); rr=r["relative_ratio"]
        rows.append(dict(record_id=r["record_id"],source_id=SOURCES[r["first_author"]]["id"],
          source_short=f'{r["first_author"]} {r["year"]}',alloy=alloy,heat=heat_of(r["alloy_grade"]),
          material_family=family(alloy),product_form=r["product_form"],
          is_weld="yes" if r["zone"]!="base metal" else "no",zone=r["zone"],
          weld_process=None if r["weld_process"]=="none" else r["weld_process"],
          filler_metal=r["filler_metal"],ferrite_number=r["delta_ferrite_pct"],
          hydrogen_exposure=r["hydrogen_exposure"],h2_pressure_MPa=r["h2_pressure_MPa"],
          hydrogen_content_wppm=r["hydrogen_content_wt_ppm"],charging_time_h=r["charging_time_h"],
          test_temperature_K=r["test_temperature_K"],
          test_temperature_C=None if r["test_temperature_K"] is None else round(r["test_temperature_K"]-273.15,1),
          strain_rate_per_s=r["strain_rate_per_s"],test_type=r["test_type"],property_name=r["property_name"],
          reference_environment=r["reference_environment"],property_reference=r["property_reference"],
          property_h2=r["property_h2"],relative_ratio=None if rr is None else round(rr,3),
          embrittlement_flag=(None if rr is None else ("no measurable loss" if rr>=0.95 else "moderate loss" if rr>=0.8 else "significant loss")),
          C_wt_pct=(r.get("composition_wt_pct") or {}).get("C"),
          Si_wt_pct=(r.get("composition_wt_pct") or {}).get("Si"),
          Mn_wt_pct=(r.get("composition_wt_pct") or {}).get("Mn"),
          Cr_wt_pct=(r.get("composition_wt_pct") or {}).get("Cr"),
          Ni_wt_pct=(r.get("composition_wt_pct") or {}).get("Ni"),
          Mo_wt_pct=(r.get("composition_wt_pct") or {}).get("Mo"),
          N_wt_pct=(r.get("composition_wt_pct") or {}).get("N"),
          Cu_wt_pct=(r.get("composition_wt_pct") or {}).get("Cu"),
          Nb_wt_pct=(r.get("composition_wt_pct") or {}).get("Nb"),
          Ti_wt_pct=(r.get("composition_wt_pct") or {}).get("Ti"),
          composition_basis=r.get("composition_basis"),composition_source=r.get("composition_source"),
          ni_equivalent=r["ni_equivalent"],ni_equivalent_reported=r.get("ni_equivalent_reported"),
          md30_calculated=r.get("md30_calculated"),
          derived_assumptions=r.get("derived_assumptions"),
          derived=";".join(dict.fromkeys(r["derived_fields"])) or None,
          verified="yes" if r["human_verified"] else "no",notes=re.sub(r"\s+"," ",r["notes"]).strip()))
    order={f:i for i,f in enumerate(["300-series (304 type)","300-series (316/317 type)",
      "300-series stabilised (321/347)","N-strengthened (21-6-9)","N-strengthened (22-13-5)",
      "high-Ni austenitic (310)","duplex","precipitation-strengthened (A286)","other"])}
    rows.sort(key=lambda x:(order[x["material_family"]],x["alloy"],x["is_weld"],x["record_id"]))
    return rows

if __name__=="__main__":
    import os
    src = next((p for p in ("data/records_raw.json", "data/records.json") if os.path.exists(p)), None)
    if src is None:
        raise SystemExit("No extraction records found. Expected data/records_raw.json (as released) "
                         "or data/records.json. Run this from the repository root.")
    recs=json.load(open(src))
    rows=clean(recs)
    cols=list(rows[0].keys())
    with open("data/he_austenite_v0.3.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
    json.dump({"rows":rows,"sources":SOURCES},open("data/clean.json","w"),indent=1)
    print(len(rows),"rows written")
