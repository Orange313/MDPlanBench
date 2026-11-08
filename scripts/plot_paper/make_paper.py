"""Re-render the 018 candidate from verified CSVs with the 019 terminology."""
import os
import runpy
import subprocess
import sys
from pathlib import Path

from setup017 import *
from style import *

DISPLAY = list(SCENARIOS)[:3]
PALETTE = [("#252525", "-", "Exclusive"), (P["R100"], "--", "50% shared"),
           (P["QP"], ":", "Prepaid")]
GRID = sorted(set(np.geomspace(10, 100000, 161)) | set(VOLUMES) |
              {v for model in MODELS for sc in DISPLAY for v in crossing(model, sc)})
CURVES = []
for model in MODELS:
    for sc in DISPLAY:
        for n in GRID:
            mean, low, high = observed([ratio(model, r, sc, n) for r in (1, 2, 3)])
            CURVES.append(dict(model=model, scenario=sc, N=n, mean_ratio=mean,
                               observed_min=low, observed_max=high))
csv_write(OUT / "qa" / "fig1b_fig5_curve_points_017.csv", CURVES)
csv_write(OUT / "qa" / "fig5_setup_points_017.csv", [
    dict(model=model, repeat=repeat, component=label, wall_s=row[field], cohort="017")
    for (model, repeat), row in SETUP.items()
    for label, field in [("Load", "model_load_wall_s"), ("Page index", "index_wall_s")]
] + [dict(model="Shared", repeat=1, component="OCR", wall_s=OCR, cohort="Historical fixed")])


def draw_lifecycle(ax, model, scenarios, preview=False):
    for sc in scenarios:
        color, line, label = PALETTE[DISPLAY.index(sc)]
        rr = [r for r in CURVES if r["model"] == model and r["scenario"] == sc]
        x = [r["N"] for r in rr]
        ax.fill_between(x, [r["observed_min"] for r in rr], [r["observed_max"] for r in rr],
                        color=color, alpha=.13, linewidth=0)
        ax.plot(x, [r["mean_ratio"] for r in rr], color=color, ls=line, label=label)
        ax.plot(VOLUMES, [observed([ratio(model, r, sc, n) for r in (1, 2, 3)])[0]
                          for n in VOLUMES], ls="", marker="o", ms=2, color=color)
        if not preview:
            low, high = crossing(model, sc)
            ax.plot([low, high], [1, 1], color=color, lw=2, marker="|", ms=4, zorder=5)
    ax.axhline(1, color="#8C8C8C", ls="--", lw=.6, zorder=0)
    ax.set(xscale="log", xlim=(80 if preview else 10, 125000),
           ylim=(.8, 3.4 if preview else 3.8), xlabel="Query volume $N$")
    ax.set_xticks([100, 10000, 100000] if preview else [10, 1000, 100000])
    axes(ax)


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def clean_source(name, source):
    if name == 1:
        source = source.replace("figsize=(3.5,2.35)", "figsize=(3.5,2.15)")
        source = source.replace("bottom=.33,top=.73,wspace=.55", "bottom=.25,top=.73,wspace=.42")
        source = source.replace("f\"Q: {v(q,'gain_pp'):+.1f} pp\"", "f\"ΔC(Q) = {v(q,'gain_pp'):.1f}\".replace('-', '−')")
        source = source.replace("Oracle gap\\n{v(h,'headroom_vs4_pp'):.1f} pp", "Oracle headroom\\n{v(h,'headroom_vs4_pp'):.1f}")
        source = source.replace("ylabel='Warm E2E (% FullV)'", "ylabel='Warm cost (% of FullV)'")
        source = source.replace("[handle(m) for m in methods]", "[handle(m) for m in methods if m!='Mix-QP']")
        source = source.replace("columnspacing=.6,handlelength=1.0", "columnspacing=.42,handlelength=.85")
        source = source.replace("'Biomedical, ColQwen2',transform=b.transAxes,ha='right',va='top'", "'Biomedical, ColQwen2',transform=b.transAxes,ha='right',va='top'")
        source = source.replace("fig.set_size_inches(2.05,2.18)", "fig.set_size_inches(3.5,2.10)")
        source = source.replace("ax.set_position([bounds[0]*3.5/2.05,1-(1-bounds[1])*2.35/2.18,bounds[2]*3.5/2.05,bounds[3]*2.35/2.18])", "ax.set_position([.15,.26,.80,.47])")
    elif name == 2:
        for old,new in [
            ('ONLINE: frozen decision rules, complete measured request path','Online request path'),
            ('I0: query features\\nQuery-only Q','Query features (I0)'),
            ('BM25 probe (I1)\\nScores / page stats','BM25 probe (I1)'),
            ('Frozen Ridge\\nAction decision','Router (Eq. 7)'),
            ('Visual branches only\\nQuery encoding\\n+ exact MaxSim\\nShared score; stable ties','Shared visual scorer (Eq. 6)'),
            ('Stable Top-10\\nRetrieval output','Top-10 pages'),
            ('Reuse paid probe on fast actions; extra work on FullV fallback','Probe candidates reused by BM-K'),
            ('OFFLINE ASSETS AND EVIDENCE BOUNDARIES','Offline assets (setup cost)'),
            ('Text acquisition + BM25 index\\nOfficial markdown or OCR\\nPaid once by asset owner','Lexical plans: extracted text\\n(V3 markdown / V2 OCR), BM25 index'),
            ('Visual model +\\npage-embedding index\\nLoad / build costs separate','Visual plans: loaded model,\\npage embeddings'),
            ('setup: ownership and amortization','setup cost attributed by ownership (Eq. 5)'),
            ("cost(1.42,3.30,'features');cost(3.66,2.58,'planning');cost(7.59,2.14,'encoding / scoring');cost(10.24,2.83,'outer E2E')", "cost(1.42,3.30,'');cost(3.66,2.58,'');cost(7.59,2.14,'');cost(10.24,2.83,'');ax.text(11.75,4.35,'▲ cost measured',ha='right',fontsize=6.5,color=P['QP'])"),
            ("box('fit',5.79,.26,2.60,.70,'Frozen supervised routers\\nFit81; exposed Dev164\\nBiomedical160 / Economics58','#F3EFF7',P['Q'])", ''),
            ("box('seal',8.75,.26,2.98,.70,'Cal / Eval + old tests SEALED\\nNew K1: NOT_CERTIFIED\\nNo Serving speedup claim','#FAFAFA','#888888',True)", ''),
            ("cost(5.92,.08,'offline diagnostics are not certification')", ''),
            ("box('text',.17,.26,2.50,.70", "box('text',.17,.26,5.10,.70"),
            ("box('emb',3.03,.26,2.40,.70", "box('emb',5.70,.26,5.98,.70"),
            ("OUT/'fig2_testbed_editable.drawio'", "BASE.parent/'fig2_testbed_editable_019.drawio'"),
        ]:
            assert old in source, (name,old)
            source = source.replace(old,new)
        source = source.replace("figsize=(7.16,2.6)", "figsize=(7.16,2.32)")
        source = source.replace("assert not path.exists();E.ElementTree(mx).write", "E.ElementTree(mx).write")
        source = source.replace("path=BASE.parent/'fig2_testbed_editable_019.drawio';", """
def drawio_label(id,x,y,w,h,tx,color='#222222',size=13,bold=False):
 cell=E.SubElement(root,'mxCell',id=id,value=tx,style=f'text;html=1;whiteSpace=wrap;fillColor=none;strokeColor=none;fontColor={color};fontSize={size};fontStyle={int(bold)};align=left;verticalAlign=middle;',vertex='1',parent='1')
 E.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
drawio_label('online_title',13,7,390,31,'Online request path',size=17,bold=True)
drawio_label('cost_legend',1030,7,170,28,'▲ cost measured',color='#D62728',size=13)
drawio_label('reuse_note',21,273,480,30,'Probe candidates reused by BM-K',color='#EF8500',size=13)
drawio_label('offline_title',13,315,460,31,'Offline assets (setup cost)',size=17,bold=True)
drawio_label('setup_note',15,426,580,28,'▲ setup cost attributed by ownership (Eq. 5)',color='#D62728',size=13)
for i,x,y in [(1,142,125),(2,366,197),(3,759,241),(4,1024,172)]:
 drawio_label('cost_marker_'+str(i),x-8,y-8,20,20,'▲',color='#D62728',size=17)
path=BASE.parent/'fig2_testbed_editable_019.drawio';""")
    elif name == 3:
        source = source.replace("figsize=(7.16,4.0)", "figsize=(7.16,3.48)")
        source = source.replace("bottom=.22,top=.84,wspace=.36,hspace=.85", "bottom=.20,top=.84,wspace=.30,hspace=.62")
        source = source.replace("panel(ax,f'({letter}) {domain}')", "panel(ax,f'({letter}) '+('Pharmaceuticals' if domain=='Pharma' else domain))")
        source = source.replace("Off static envelope", "BM-100 above envelope")
        source = source.replace("if domain=='Economics':ax.text(.97,.69,'ColPali: NOT_RUN\\n1 source component',transform=ax.transAxes,ha='right',va='top',fontsize=6.5,color='#555555')", "")
        source = source.replace("if domain=='Biomedical':ax.text(.97,.51,'ColPali: post-hoc',transform=ax.transAxes,ha='right',va='top',fontsize=6.5,color='#555555')", "")
        source = source.replace("labels=['HR','Fin','Ind','Pha','Pali-Dev','Bio','Eco']", "labels=['HR','Fin.','Ind.','Pharm.','Dev (ColPali)','Bio.','Eco.']")
        source = source.replace("g,h=aa[1,2:];panel(g,'(g) Containment')", "g,h=aa[1,2:];hp=h.get_position();h.set_position([hp.x0+.045,hp.y0,hp.width-.045,hp.height]);panel(g,'(g) Containment')")
        source = source.replace("h.invert_yaxis();axes(h)", "h.invert_yaxis();axes(h);h.tick_params(axis='y',labelsize=6.5)")
        source = source.replace("'Complete / r=0'", "'Top-10 contained'").replace("'Miss / r=0'", "'Missed, no loss'").replace("'Miss / r>0'", "'Missed, loss'")
        source = source.replace("bbox_to_anchor=(.5,.93)", "bbox_to_anchor=(.5,.94)")
    elif name == 4:
        source = source.replace("from style import *", "from style import *\ndef panel(ax,txt):return ax.annotate(txt,xy=(.5,0),xycoords='axes fraction',xytext=(0,-46),textcoords='offset points',fontsize=8,ha='center',va='top')")
        source = source.replace("figsize=(7.16,3.9)", "figsize=(7.16,3.42)")
        source = source.replace("left=.128,right=.985,bottom=.25,top=.81,wspace=.54", "left=.16,right=.985,bottom=.16,top=.84,wspace=.42")
        source = source.replace("a,b,c,d=[fig.add_subplot(gs[0,i]) for i in range(4)]", "a,b,c,d=[fig.add_subplot(gs[0,i]) for i in range(4)];[ax.set_position(pos) for ax,pos in zip((a,b,c,d),[(.16,.25,.28,.59),(.50,.25,.11,.59),(.70,.25,.105,.59),(.88,.25,.105,.59)])]")
        source = source.replace("(c) QP-risk cost", "(c) Cost at QP's risk")
        source = source.replace("yl.extend([dom+'  Q','QP','RR h/s'])", "yl.extend([('Pharmaceuticals' if dom=='Pharma' else dom)+'  Q','QP','RR hard / soft'])")
        source = source.replace("f'{xx:+.1f}'", "f'{xx:+.1f}'.replace('-', '−')")
        source = source.replace("Saving (pp of FullV)\\nMore costly  |  Cheaper", "ΔC (pp of FullV)")
        source = source.replace("QP - control (ms)", "QP − control\\n(ms)")
        source = source.replace("QP - control regret", "Δ regret")
        source = source.replace("'Env.'", "'Envelope'")
        source = source.replace("xlabel='Warm E2E (% FullV)'", "xlabel='Warm cost\\n(% of FullV)'")
        source = source.replace("c.set(xlim=(0,132)", "c.tick_params(axis='y',labelsize=6.5);c.set(xlim=(0,132)")
        source = source.replace("label='Offline oracle at router risk'", "label=\"Oracle at router's risk\"")
        source = source.replace("fig.text(.54,.025,'Pointwise paired 95% CIs. Eco: conditional on 1 source component. Dev RR: composite cost.',ha='center',fontsize=6.5)", "")
    elif name == 6:
        source = source.replace("figsize=(3.5,2.65)", "figsize=(3.5,2.8)")
        source = source.replace("left=.33,right=.97,bottom=.20,top=.87", "left=.56,right=.97,bottom=.18,top=.82")
        source = source.replace("xlabel='B / A latency ratio (98.75% intervals)'", "xlabel='B / A latency ratio\\n(98.75% intervals)'")
        source = source.replace("axes(ax,True,False);fig.legend", "axes(ax,True,False);ax.tick_params(axis='y',labelsize=6.5);fig.legend")
        source = source.replace("('First' if batch=='Initial' else 'Repeat')+' '+dom+f' {qps}'", "('Cohort 1' if batch=='Initial' else 'Cohort 2')+', '+('Pharmaceuticals' if dom=='Pharma' else dom)+f', {qps} QPS'")
        source = source.replace("fig.text(.5,.025,'QPS per row; target band [0.9, 1.1].',ha='center',fontsize=6.5)", "")
        source = source.replace("from style import *", "from style import *\nfrom matplotlib.patches import Patch")
        source = source.replace("Line2D([],[],marker='s',color=P['FullV'],ls='',ms=4,label='Total response')", "Line2D([],[],marker='s',color=P['FullV'],ls='',ms=4,label='Total response'),Patch(facecolor=P['Good'],label='Equivalence band [0.9, 1.1]')")
        source = source.replace("ncol=2,frameon=False", "ncol=2,frameon=False")
    return source


def execute_original(name, transform):
    path = BASE / f"make_fig{name}_016.py"
    evidence = json.loads((BASE.parent / "INPUT_SHA256.json").read_text(encoding="utf8"))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence[f"figures/make_fig{name}.py"]
    source = clean_source(name, transform(path.read_text(encoding="utf8")))
    READ.clear()
    exec(compile(source, str(path), "exec"), dict(globals(), __file__=str(path)))


def overview(source, compact):
    start = source.index(" for sc,co,ls")
    end = source.index(" hs=", start)
    preview = """ draw_lifecycle(b,'ColQwen2',[DISPLAY[0],DISPLAY[2]],preview=True)
 b.set_ylabel('Total-cost ratio\\n(BM-100 / FullV)',fontsize=6.5,labelpad=0)
 b.set_title('Biomedical, ColQwen2',loc='right',fontsize=6.5,pad=2,color='#555555')
"""
    if compact:
        preview = """ b.remove()
 bounds=ax.get_position().bounds
 fig.set_size_inches(3.5,2.10)
 ax.set_position([.15,.26,.80,.47])
"""
    source = source[:start] + preview + source[end:]
    if compact:
        source = replace_once(source, "fig.legend(handles=hs,ncol=4,loc='upper center',bbox_to_anchor=(.51,1.0)",
                              "fig.legend(handles=hs[:-2],ncol=3,labelspacing=.30,loc='upper center',bbox_to_anchor=(.51,1.0)")
    suffix = "_compact" if compact else "_ab"
    return replace_once(source, "save(fig,'fig1_overview_'+domain.lower())",
                        f"save(fig,'fig1_'+domain.lower()+'{suffix}')")


execute_original(1, lambda source: overview(source, False))
execute_original(1, lambda source: overview(source, True))


def architecture(source):
    source = replace_once(source, "Text acquisition + BM25 index\\nOfficial markdown or OCR\\nPaid once by asset owner",
                          "Official text or OCR\\nHistorical OCR timing reused\\nBM25 index: asset cost")
    source = replace_once(source, "Visual model +\\npage-embedding index\\nLoad / build costs separate",
                          "Visual model + page index\\n017 load / build\\n3 independent runs/model")
    return replace_once(source, "save(fig,'fig2_testbed')", """csv_write(OUT/'fig2_setup_sources.csv',[
 dict(component='OCR', source='Historical fixed', repeats='1 archived', wall_s=OCR),
 *[dict(component=field,source=f'017 {model}',repeats=rep,wall_s=row[field])
   for (model,rep),row in SETUP.items() for field in ['model_load_wall_s','index_wall_s']]])
save(fig,'fig2_testbed_017')""")


# Architectural diagram superseded by frozen editable draw.io.
# execute_original(2, lambda source: replace_once(source, "save(fig,'fig2_testbed')", "save(fig,'fig2_testbed_017')"))


def harm(source):
    return replace_once(source, "save(fig,'fig3_static_frontiers')", "save(fig,'fig3_static_frontiers_018')")


execute_original(3, harm)
execute_original(4, lambda source: source)
execute_original(6, lambda source: source)
READ.clear()
fig = plt.figure(figsize=(3.5, 4.50))
gs = fig.add_gridspec(2, 2)
top = fig.add_subplot(gs[0, :])
top.set_position([.18,.71,.79,.18])
for i, (label, field) in enumerate([("Load", "model_load_wall_s"), ("Index build", "index_wall_s")]):
    for model, shift, marker, color in [("ColQwen2", -.22, "o", P["R100"]),
                                        ("ColPali", .22, "s", P["Oracle"])]:
        values = [float(SETUP[model, str(rep)][field]) for rep in (1, 2, 3)]
        top.plot([min(values), max(values)], [i + shift] * 2, color=color, lw=.8)
        top.plot(values, [i + shift] * 3, ls="", marker=marker, color=color,
                 mfc="white" if model == "ColPali" else color, ms=3.4)
        if label == "Index build":
            top.text(105, i + shift, f"{min(values):.1f}–{max(values):.1f}",
                     ha="right", va="center", fontsize=6.5, color=color)
top.plot(OCR, 2, marker="D", color=P["BM25"], ms=4)
top.text(OCR*.9, 2, "407.725 s", ha="right", va="center", fontsize=6.5)
top.set(xscale="log", xlim=(2, 650), ylim=(2.45, -.45), yticks=[0, 1, 2],
        yticklabels=["Load", "Index build", "OCR"], xlabel="Setup wall time (s)")
top.set_xticks([10, 100])
axes(top, True, False)
top.annotate("(a) Setup cost",xy=(.5,0),xycoords='axes fraction',xytext=(0,-23),textcoords='offset points',fontsize=8,ha='center',va='top')
fig.legend(handles=[
    Line2D([], [], marker="o", color=P["R100"], ls="", label="ColQwen2"),
    Line2D([], [], marker="s", mfc="white", color=P["Oracle"], ls="", label="ColPali"),
    Line2D([], [], marker="D", color=P["BM25"], ls="", label="OCR"),
    *[Line2D([], [], color=c, ls=ls, label=label) for c, ls, label in PALETTE],
], loc="upper center", bbox_to_anchor=(.51,.993), frameon=False, ncol=3,
   columnspacing=.85, handletextpad=.35, handlelength=1.3)
for i, (model, tag) in enumerate(zip(MODELS, ["(b) ColQwen2", "(c) ColPali"])):
    ax = fig.add_subplot(gs[1, i])
    ax.set_position([.18 if i==0 else .62,.33,.34,.25])
    draw_lifecycle(ax, model, DISPLAY)
    ax.set_yticks([1, 2, 3])
    ax.annotate(tag,xy=(.5,0),xycoords='axes fraction',xytext=(0,-34),textcoords='offset points',fontsize=8,ha='center',va='top')
    if i == 0:
        ax.set_ylabel("Total-cost ratio\n(BM-100 / FullV)",fontsize=6.5,labelpad=0)
    else:
        ax.tick_params(labelleft=False)
fig.text(.52,.15,"Crossing ranges (queries)",ha="center",fontsize=6.8,fontweight="bold")
fig.text(.02,.12,"OCR ownership",fontsize=6.5)
for model, x in zip(MODELS,[.52,.80]):
    fig.text(x,.12,model,ha="center",fontsize=6.5)
for sc, (_, _, label), y in zip(DISPLAY,PALETTE,[.095,.070,.045]):
    fig.text(.02,y,label,fontsize=6.5)
    for model, x in zip(MODELS,[.52,.80]):
        low, high = crossing(model, sc)
        fig.text(x,y,f"{low:,}–{high:,}",ha="center",fontsize=6.5)
save(fig,"fig5_lifecycle_017")
