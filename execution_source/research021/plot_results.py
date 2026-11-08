"""Scientific review figures from generated tables only."""
import common as C
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"pdf.fonttype":42,
    "axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":300})
OUT=C.REPORT/"figures"
OUT.mkdir()
ROWS=C.load(C.REPORT/"EX1/router_capacity_results.csv")
QUERY_ROWS=C.load(C.REPORT/"EX1/actual_per_query.csv")
DECOMP=C.load(C.REPORT/"EX2/information_value_decomposition.csv")
MIX=C.load(C.REPORT/"EX3/static_mixture_prospective.csv")
DOM=["HR","Finance","Industrial","Pharma","Biomedical","Economics"]
METHODS=["Ridge_Q","Ridge_QP","LightGBM_Q","LightGBM_QP"]
COLORS=["#6A3D9A","#D62728","#1B7837","#2166AC"]
LABELS=["Ridge Q","Ridge QP","GBM Q","GBM QP"]


def save(fig,name):
    fig.tight_layout(rect=(0,.025,1,.94))
    fig.savefig(OUT/(name+".pdf"),metadata={"CreationDate":None})
    fig.savefig(OUT/(name+".png"))
    plt.close(fig)


fig,axes=plt.subplots(2,3,figsize=(9.2,5.8))
for ax,dom in zip(axes.flat,DOM):
    for i,(key,color) in enumerate(zip(METHODS,COLORS)):
        r=next(x for x in ROWS if x["domain"]==dom and x["method"]==key)
        val,lo,hi=map(float,[r["DeltaC_pp"],r["DeltaC_low_pp"],r["DeltaC_high_pp"]])
        ax.errorbar(val,i,xerr=[[max(0,val-lo)],[max(0,hi-val)]],
            fmt="o",color=color,capsize=2)
    ax.axvline(0,color=".5",lw=.7,ls="--")
    ax.set(yticks=range(4),yticklabels=LABELS,title=dom,xlabel="Matched-risk saving (pp FullV)")
    ax.invert_yaxis()
fig.suptitle("Selector capacity control | paired pointwise 95% intervals",fontsize=11)
save(fig,"router_capacity_figure")

fig,axes=plt.subplots(2,3,figsize=(9.2,5.8))
oracle_points=[]
for ax,dom in zip(axes.flat,DOM):
    for i,key in enumerate(["Ridge_QP","LightGBM_QP"]):
        r=next(x for x in DECOMP if x["domain"]==dom and x["method"]==key)
        actual=next(x for x in ROWS if x["domain"]==dom and x["method"]==key)
        ax.barh(i-.16,float(r["zero_signal_DeltaC_pp"]),height=.28,
                color="#A6BDDB",label="Intrinsic action, analysis only" if i==0 else None)
        ax.barh(i+.16,float(actual["DeltaC_pp"]),height=.28,
                color="#2166AC",label="Measured complete path" if i==0 else None)
        for yy,point,low,high in [
            (i-.16,float(r["zero_signal_DeltaC_pp"]),float(r["zero_signal_low_pp"]),float(r["zero_signal_high_pp"])),
            (i+.16,float(actual["DeltaC_pp"]),float(actual["DeltaC_low_pp"]),float(actual["DeltaC_high_pp"]))]:
            ax.errorbar(point,yy,xerr=[[max(0,point-low)],[max(0,high-point)]],
                        fmt="none",ecolor=".2",elinewidth=.6,capsize=1)
    ax.axvline(0,color=".5",lw=.7,ls="--")
    ax.set(yticks=[0,1],yticklabels=["Ridge QP","GBM QP"],title=dom,
           xlabel="Matched-risk saving (pp FullV)")
handles,labels=axes.flat[0].get_legend_handles_labels()
fig.legend(handles,labels,loc="upper center",ncol=2,frameon=False)
save(fig,"information_value_decomposition")

fig,axes=plt.subplots(2,3,figsize=(9.2,5.8))
for ax,dom in zip(axes.flat,DOM):
    full=float(next(r["E2E_ms"] for r in ROWS if r["domain"]==dom and r["method"]=="Full-Visual"))
    stat=[next(r for r in ROWS if r["domain"]==dom and r["method"]==p) for p in C.PLANS]
    for r in stat:
        ax.plot(float(r["mean_r"]),100*float(r["E2E_ms"])/full,"s",color=".25",ms=4)
    # Recorded envelope vertices are recomputed from this cohort for plotting.
    from scipy.optimize import linprog
    risk=np.array([float(x["mean_r"]) for x in stat])[C.CAT]
    cost=np.array([float(x["E2E_ms"]) for x in stat])[C.CAT]
    largest=max(float(x["mean_r"]) for x in ROWS if x["domain"]==dom)
    grid=np.linspace(0,max(risk.max(),largest,.10),101)
    y=[]
    for b in grid:
        lp=linprog(cost,A_ub=[risk],b_ub=[b+1e-12],A_eq=[np.ones(3)],b_eq=[1],
                    bounds=(0,1),method="highs")
        assert lp.success
        y.append(100*lp.fun/full)
    ax.plot(grid,y,color=".5",lw=.8)
    from scipy.sparse import csr_matrix,kron,eye
    qrows=[r for r in QUERY_ROWS if r["domain"]==dom and r["method"] in C.PLANS]
    qids=sorted({int(r["query_id"]) for r in qrows})
    lookup={(int(r["query_id"]),r["method"]):r for r in qrows}
    loss=np.array([[float(lookup[q,C.PLANS[j]]["r"]) for j in C.CAT] for q in qids])
    price=np.array([[float(lookup[q,C.PLANS[j]]["E2E_ms"]) for j in C.CAT] for q in qids])
    nn=len(qids)
    ox,oy=[],[]
    for budget in (.02,.05,.10):
        lp=linprog(price.ravel()/nn,A_ub=csr_matrix(loss.ravel()[None,:]/nn),b_ub=[budget+1e-12],
            A_eq=kron(eye(nn),np.ones((1,3)),format="csr"),b_eq=np.ones(nn),
            bounds=(0,1),method="highs")
        assert lp.success
        achieved=float(lp.x @ loss.ravel()/nn)
        ox.append(achieved);oy.append(100*lp.fun/full)
        oracle_points.append(dict(domain=dom,budget=budget,achieved_r=achieved,
            oracle_E2E_ms=lp.fun,scope="OFFLINE_LABEL_DEPENDENT_FRACTIONAL_ORACLE"))
    ax.plot(ox,oy,"--",marker="|",color="#1B7837",lw=.8)
    for key,color in zip(METHODS,COLORS):
        r=next(x for x in ROWS if x["domain"]==dom and x["method"]==key)
        ax.plot(float(r["mean_r"]),100*float(r["E2E_ms"])/full,"o",color=color,ms=4)
    for m in [x for x in MIX if x["domain"]==dom]:
        ax.plot(float(m["achieved_expected_r"]),100*float(m["expected_E2E_ms"])/full,
                marker="D",mfc="white",mec="#E08214",ms=4)
    actual=next(x for x in ROWS if x["domain"]==dom and x["method"]=="FitFrozenMix_0.05")
    ax.plot(float(actual["mean_r"]),100*float(actual["E2E_ms"])/full,"*",color="#E08214",ms=8)
    ax.set(title=dom,xlabel="Mean positive regret",ylabel="Warm cost (% FullV)")
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([],[],color=c,marker="o",ls="",label=label)
                    for c,label in zip(COLORS,LABELS)]+
    [Line2D([],[],color=".5",label="Post-hoc envelope"),
    Line2D([],[],color="#1B7837",ls="--",label="Offline fractional oracle"),
    Line2D([],[],color="#E08214",marker="D",mfc="white",ls="",label="Fit-only mix expectation"),
    Line2D([],[],color="#E08214",marker="*",ls="",label="Executed mix (.05)")],
    loc="upper center",ncol=4,frameon=False)
save(fig,"risk_cost_comparison")
C.table(OUT/"oracle_plot_points.csv",oracle_points)
C.write(OUT/"plot_inputs.json",dict(sources={
    str(p.relative_to(C.ROOT)):C.sha(p) for p in [
        C.REPORT/"EX1/router_capacity_results.csv",
        C.REPORT/"EX1/actual_per_query.csv",
        C.REPORT/"EX2/information_value_decomposition.csv",
        C.REPORT/"EX3/static_mixture_prospective.csv"]},
    script_sha256=C.sha(__file__),uncertainty="paired pointwise 95% source/family and process",
    new_plots_are_manuscript_review_candidates=True))
