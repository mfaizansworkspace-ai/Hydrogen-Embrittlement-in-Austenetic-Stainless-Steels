# Data dictionary

One record is one reported test condition and one property. Version 0.3, 45 columns.

Composition columns are the analysis the source published for the heat, weld deposit or filler that was tested. `data/compositions.csv` holds one row per composition with the table it came from, and `data/record_composition_map.csv` says which record uses which. A composition is never carried across heats, and a specification range is never recorded as a measurement.

| Column | Meaning | Populated |
|---|---|---|
| `record_id` | Unique id: source, table, row | 113 of 113 |
| `source_id` | Key into the source list | 113 of 113 |
| `source_short` | Author and year | 113 of 113 |
| `alloy` | Alloy designation, standardised | 113 of 113 |
| `heat` | Heat or cast id where reported | 16 of 113 |
| `material_family` | Grouping used for analysis | 113 of 113 |
| `product_form` | plate, bar, sheet, tube, weld | 113 of 113 |
| `is_weld` | Gauge section contains weld metal (yes/no) | 113 of 113 |
| `zone` | base metal / weld metal / HAZ / fusion line / whole joint | 113 of 113 |
| `weld_process` | GTAW, GMAW, PAW, EBW, laser | 60 of 113 |
| `filler_metal` | Filler wire designation | 50 of 113 |
| `ferrite_number` | Ferrite number of the weld metal, FN, where reported | 2 of 113 |
| `hydrogen_exposure` | gaseous in-situ or gaseous precharge | 113 of 113 |
| `h2_pressure_MPa` | Hydrogen gas pressure, MPa |
| `hydrogen_content_wppm` | Hydrogen content, wt ppm | 52 of 113 |
| `charging_time_h` | Precharging duration, hours | 45 of 113 |
| `test_temperature_K` | Test temperature, K |
| `test_temperature_C` | Test temperature, degrees C |
| `strain_rate_per_s` | Nominal strain rate, 1/s | 64 of 113 |
| `test_type` | tensile or SSRT | 113 of 113 |
| `property_name` | reduction of area, elongation, tensile strength, plastic strain to failure, notched tensile strength | 113 of 113 |
| `reference_environment` | air, helium, nitrogen, argon or uncharged | 113 of 113 |
| `property_reference` | Value in the reference environment, % or MPa | 103 of 113 |
| `property_h2` | Value in or after hydrogen, % or MPa | 103 of 113 |
| `relative_ratio` | property_h2 / property_reference, or the ratio as the source printed it where absolute values were not given; RRA when the property is reduction of area | 113 of 113 |
| `embrittlement_flag` | no measurable loss >= 0.95, moderate 0.80-0.95, significant < 0.80 | 113 of 113 |
| `C_wt_pct` | Carbon, wt % | 99 of 113 |
| `Si_wt_pct` | Silicon, wt % | 98 of 113 |
| `Mn_wt_pct` | Manganese, wt % | 98 of 113 |
| `Cr_wt_pct` | Chromium, wt % | 102 of 113 |
| `Ni_wt_pct` | Nickel, wt % | 102 of 113 |
| `Mo_wt_pct` | Molybdenum, wt %, empty where the grade carries none | 48 of 113 |
| `N_wt_pct` | Nitrogen, wt % | 72 of 113 |
| `Cu_wt_pct`, `Nb_wt_pct`, `Ti_wt_pct` | Reported only for some grades | see the CSV |
| `composition_basis` | `heat_analysis` for a measured heat, weld deposit or filler analysis; `nominal` for a nominal composition. A specification midpoint is never recorded as a measurement. | 102 of 113 |
| `composition_source` | The table the composition was read from | 102 of 113 |
| `ni_equivalent` | Nickel equivalent, wt %, recomputed for every record from the composition using Hirayama's six-element expression: Ni + 0.65 Cr + 0.98 Mo + 1.05 Mn + 0.35 Si + 12.6 C. Derived, never reported. | 93 of 113 |
| `ni_equivalent_reported` | Nickel equivalent as the source printed it, which may use a different expression | 15 of 113 |
| `md30_calculated` | Angel Md30, degrees C: 413 − 462(C+N) − 9.2 Si − 8.1 Mn − 13.7 Cr − 9.5 Ni − 18.5 Mo. The temperature at which 30% strain produces 50% martensite. Computed only where the composition falls inside the range Angel's expression was fitted on (Mn ≤ 2.5, N ≤ 0.12, Cr ≤ 21.0, Mo ≤ 3.0, C ≤ 0.15); outside it the linear form returns values below absolute zero. Derived, never reported. | 55 of 113 |
| `derived_assumptions` | Elements taken as zero when computing the derived values, for grades whose specification carries none. Mo in 42 records, N in 18, both in 5. The nickel equivalent has no nitrogen term so is unaffected; Md30 is sensitive to it, and an unreported nitrogen of 0.05 wt% would move Md30 by about 23 °C. | see the CSV |
| `derived` | Fields computed rather than reported by the source | 113 of 113 |
| `verified` | Independently re-extracted and matched (yes/no) | 113 of 113 |
| `notes` | Source table, test conditions and caveats | 113 of 113 |

## Sources

| ID | Citation | Access |
|---|---|---|
| S1 | Caskey GR Jr. Hydrogen Compatibility Handbook for Stainless Steels. DP-1643, Savannah River Laboratory, June 1983. | open |
| S2 | San Marchi C, Somerday BP (eds). Technical Reference on Hydrogen Compatibility of Materials. SAND2012-7321, Sandia National Laboratories, 2012. | open |
| S3 | Balch DK, San Marchi C, et al. Effect of hydrogen on tensile strength and ductility of multipass 304L/308L welds. PVP2015-45591, ASME, 2015. | paywalled |
| S4 | Michler T, Lee Y, Gangloff RP, Naumann J. Influence of macro segregation on hydrogen environment embrittlement of SUS 316L. Int J Hydrogen Energy 34(7) 2009: 3201-3209. | paywalled |
| S5 | Nakamura J, Okazaki S, Matsunaga H, Matsuoka S. SSRT and fatigue life properties of 317L weld metal in high-pressure hydrogen gas. Trans JSME 84(857) 2018 (Japanese). | open |
| S6 | Younes CM, Steele AM, Nicholson JA, Barnett CJ. Influence of hydrogen content on the tensile properties and fracture of austenitic stainless steel welds. Int J Hydrogen Energy 38 2013: 4864-4876. | paywalled |
| S7 | Iyer KJL. The influence of hydrogen on the mechanical properties and structure of a stable 304 stainless steel. Canadian Metallurgical Quarterly, 1989. | paywalled |
| S8 | Fukunaga A. Hydrogen embrittlement behaviors during SSRT tests in gaseous hydrogen for cold-worked type 316 and A286 used in hydrogen refueling stations. Eng Failure Analysis 160 (2024) 108158. | paywalled |
| S9 | Matsuoka S, Yamabe J, Matsunaga H. Hydrogen-induced ductility loss of austenitic stainless steels for SSRT in high-pressure hydrogen gas. Solid State Phenomena 258 (2017) 259-264. | paywalled |
