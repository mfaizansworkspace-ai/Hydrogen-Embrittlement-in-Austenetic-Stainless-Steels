import json, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BLUE,ORANGE,AQUA,YELLOW="#2a78d6","#eb6834","#1baf7a","#eda100"
SURF,INK,INK2,GRID="#fcfcfb","#0b0b0b","#52514e","#e4e3df"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.edgecolor":GRID,
 "axes.labelcolor":INK2,"text.color":INK,"xtick.color":INK2,"ytick.color":INK2,
 "figure.facecolor":SURF,"axes.facecolor":SURF,"axes.grid":True,"grid.color":GRID,
 "grid.linewidth":0.8,"axes.axisbelow":True})

rows=[r for r in json.load(open("data/clean.json"))["rows"]
      if r["property_name"]=="reduction of area" and r["relative_ratio"] is not None]

# ---- Figure 1: RRA by material family
fams=["300-series (304 type)","300-series stabilised (321/347)","300-series (316/317 type)",
      "N-strengthened (21-6-9)","N-strengthened (22-13-5)","high-Ni austenitic (310)","duplex"]
short={"300-series (304 type)":"304 type","300-series stabilised (321/347)":"321 / 347",
 "300-series (316/317 type)":"316 / 317","N-strengthened (21-6-9)":"21-6-9","N-strengthened (22-13-5)":"22-13-5",
 "high-Ni austenitic (310)":"310","duplex":"2507 duplex"}
fig,ax=plt.subplots(figsize=(8.4,4.6))
for i,f in enumerate(fams):
    vals=[r["relative_ratio"] for r in rows if r["material_family"]==f]
    if not vals: continue
    wel=[r["relative_ratio"] for r in rows if r["material_family"]==f and r["is_weld"]=="yes"]
    bas=[r["relative_ratio"] for r in rows if r["material_family"]==f and r["is_weld"]=="no"]
    ax.scatter([i-0.12]*len(bas),bas,s=46,color=BLUE,alpha=.75,edgecolor=SURF,linewidth=1.2,zorder=3)
    ax.scatter([i+0.12]*len(wel),wel,s=46,color=ORANGE,alpha=.75,marker="s",edgecolor=SURF,linewidth=1.2,zorder=3)
    m=st.median(vals); ax.plot([i-0.32,i+0.32],[m,m],color=INK,lw=2,zorder=4)
    ax.annotate(f"{m:.2f}",(i+0.34,m),fontsize=9,color=INK2,va="center")
ax.axhline(0.8,color=INK2,lw=1,ls="--",zorder=2)
ax.annotate("0.80 — Japanese acceptance threshold for hydrogen service",(0.45,0.815),
            ha="left",fontsize=8.5,color=INK2,
            bbox=dict(facecolor=SURF,edgecolor="none",pad=1.5))
ax.set_xticks(range(len(fams))); ax.set_xticklabels([short[f] for f in fams],fontsize=9.5)
ax.set_ylabel("Relative reduction of area  (H$_2$ / reference)"); ax.set_ylim(0,1.6)
ax.set_title("Ductility retained in gaseous hydrogen, by alloy family",fontsize=12.5,color=INK,pad=12,loc="left")
ax.legend(handles=[Line2D([],[],marker="o",ls="",color=BLUE,label="base metal (circles)",markersize=7),
                   Line2D([],[],marker="s",ls="",color=ORANGE,label="welds (squares)",markersize=7),
                   Line2D([],[],color=INK,lw=2,label="family median")],
          frameon=False,loc="upper left",fontsize=9)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("figures/fig1_family.png",dpi=200)

# ---- Figure 2: pressure dependence, 304-type only
fig,ax=plt.subplots(figsize=(7.6,4.4))
pts=[(r["h2_pressure_MPa"],r["relative_ratio"],r["is_weld"]) for r in rows
     if r["material_family"]=="300-series (304 type)" and r["h2_pressure_MPa"]]
for w,c,mk,lab in (("no",BLUE,"o","base metal"),("yes",ORANGE,"s","weld")):
    xs=[p for p,_,ww in pts if ww==w]; ys=[y for _,y,ww in pts if ww==w]
    ax.scatter(xs,ys,s=52,color=c,marker=mk,alpha=.75,edgecolor=SURF,linewidth=1.2,label=lab,zorder=3)
ax.axhline(0.8,color=INK2,lw=1,ls="--",zorder=2)
ax.set_xscale("log"); ax.set_xlabel("Hydrogen pressure (MPa, log scale)")
ax.set_ylabel("Relative reduction of area"); ax.set_ylim(0,1.3)
ax.set_title("304-type steels: ductility loss against hydrogen pressure",fontsize=12.5,color=INK,pad=12,loc="left")
ax.legend(frameon=False,fontsize=9,loc="lower left")
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("figures/fig2_pressure.png",dpi=200)

# ---- Figure 3: two sets of records in which weld condition is the variable.
# The two panels are NOT comparable with one another: they differ in alloy system,
# pressure, temperature, reference environment and specimen geometry. Panel conditions
# are stated in each subtitle so that no cross-panel reading is implied.
panelA=[("317L weld metal,\nas welded",0.552,ORANGE),
        ("317L weld metal,\npost-weld solution treated",0.905,AQUA),
        ("316 hi-Ni base metal,\nsame bar",1.024,BLUE)]
panelB=[("304L/308L weld,\nFN 4.7",0.350,ORANGE),
        ("304L/308L weld,\nFN 8.5",0.425,ORANGE)]
fig,axes=plt.subplots(1,2,figsize=(8.8,4.3),gridspec_kw={"width_ratios":[3,2]})
for ax,cases,sub in ((axes[0],panelA,"Nakamura 2018 [5]: one TIG-welded bar\n106 MPa H$_2$, 228 K, nitrogen reference, smooth"),
                     (axes[1],panelB,"Sandia 2012 [2]: composite welds\n69 MPa H$_2$, 295 K, air reference, notched")):
    xs=range(len(cases))
    ax.bar(xs,[c[1] for c in cases],color=[c[2] for c in cases],width=0.58,zorder=3,
           edgecolor=SURF,linewidth=2)
    for i,(lab,v,c) in enumerate(cases): ax.annotate(f"{v:.2f}",(i,v+0.03),ha="center",fontsize=10,color=INK)
    ax.axhline(0.8,color=INK2,lw=1,ls="--",zorder=2)
    ax.set_xticks(list(xs)); ax.set_xticklabels([c[0] for c in cases],fontsize=8.2)
    ax.set_ylim(0,1.2)
    ax.set_title(sub,fontsize=9,color=INK2,pad=10,loc="left")
    for s in ("top","right"): ax.spines[s].set_visible(False)
axes[0].set_ylabel("Relative reduction of area")
fig.suptitle("Records in which the weld condition is the only variable within a study",
             fontsize=12.5,color=INK,x=0.012,ha="left",y=0.99)
fig.tight_layout(rect=[0,0,1,0.93]); fig.savefig("figures/fig3_ferrite.png",dpi=200)

# ---- counts quoted in the paper, printed so they can be checked against the captions
n304=len([r for r in rows if r["material_family"]=="300-series (304 type)"])
n304p=len([r for r in rows if r["material_family"]=="300-series (304 type)" and r["h2_pressure_MPa"]])
print(f"figures written | Fig.1 n={len(rows)} | Fig.2 304-family plotted {n304p} of {n304}")

# ---- Figure 4: ductility retained against nickel equivalent
import csv as _csv
dat=[r for r in _csv.DictReader(open("data/he_austenite_v0.3.csv",encoding="utf-8"))
     if r["property_name"]=="reduction of area" and r["relative_ratio"] and r["ni_equivalent"]
     and r["material_family"] != "precipitation-strengthened (A286)"
     # reports the same measurement as a Caskey record already in the set
     and r["record_id"] != "SAND2012-ch2101-T3111-5"]
fig,ax=plt.subplots(figsize=(8.4,4.8))
for weld,colour,marker,label in (("no",BLUE,"o","base metal"),("yes",ORANGE,"s","weld")):
    xs=[float(r["ni_equivalent"]) for r in dat if r["is_weld"]==weld]
    ys=[float(r["relative_ratio"]) for r in dat if r["is_weld"]==weld]
    ax.scatter(xs,ys,s=52,color=colour,marker=marker,alpha=.78,edgecolor=SURF,linewidth=1.2,
               zorder=3,label=f"{label}  (n = {len(xs)})")
ax.axhline(0.8,color=INK2,lw=1,ls="--",zorder=2)
ax.axvline(26.3,color=INK2,lw=1,ls=":",zorder=2)
ax.annotate("RRA = 0.80",(ax.get_xlim()[0]+0.2,0.815),fontsize=8.5,color=INK2,
            bbox=dict(facecolor=SURF,edgecolor="none",pad=1.5))
ax.annotate("Ni$_{eq}$ = 26.3, the criterion proposed by Matsuoka et al. [9]",
            (26.6,0.06),fontsize=8.5,color=INK2)
ax.set_xlabel("Nickel equivalent (wt%), Hirayama expression, recomputed from composition")
ax.set_ylabel("Relative reduction of area  (H$_2$ / reference)")
ax.set_ylim(0,1.3)
ax.set_title("Ductility retained against austenite stability, austenitic grades only",fontsize=12.5,color=INK,pad=12,loc="left")
ax.legend(frameon=False,loc="lower right",fontsize=9)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("figures/fig4_nieq.png",dpi=200)
lo=[float(r["relative_ratio"]) for r in dat if float(r["ni_equivalent"])<26.3]
hi=[float(r["relative_ratio"]) for r in dat if float(r["ni_equivalent"])>=26.3]
print(f"Fig.4 n={len(dat)} | below 26.3: n={len(lo)} median {st.median(lo):.2f} | "
      f"at or above: n={len(hi)} median {st.median(hi):.2f}")
