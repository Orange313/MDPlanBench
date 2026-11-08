"""Layout-only rendering. Assert every scientific array against the frozen ledger/raw costs."""
from pathlib import Path
import csv, json, sys, math, statistics, hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
root=Path(sys.argv[1])
def read(n):return list(csv.DictReader((root/'data'/n).open(encoding='utf-8-sig',newline='')))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7.5,'axes.labelsize':7.5,'axes.titlesize':8,
    'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'figure.facecolor':'white','savefig.dpi':350,
    'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.6,'lines.linewidth':1.1})
def save(fig,name):
    fig.canvas.draw()
    fig.savefig(root/'figures'/(name+'.pdf'),metadata={'CreationDate':None,'ModDate':None,'Title':name})
    fig.savefig(root/'figures'/(name+'.png'),dpi=350)
    plt.close(fig)
capacity=read('capacity_plot.csv');selection=read('selection_plot.csv');ledger={z['metric_key']:z for z in read('metric_ledger.csv')}
checks=[]
for z in capacity:
    l=ledger[z['metric_key']]
    assert float(z['DeltaC_pp'])==float(l['value'])
    assert float(z['DeltaC_low_pp'])==float(l['CI_low']) and float(z['DeltaC_high_pp'])==float(l['CI_high'])
    assert z['plan_catalog']=='FullV|R100|BM25'
for z in selection:
    for k in ['oracle_headroom_pp','selector_loss_pp','realized_minus_standalone_execution_pp','DeltaC_pp']:
        key=('021.EX1.' if k=='DeltaC_pp' else '021.EX2.')+z['domain']+'.LightGBM_QP.'+k
        assert float(z[k])==float(ledger[key]['value']),key
    assert abs(float(z['oracle_headroom_pp'])-float(z['selector_loss_pp'])-float(z['realized_minus_standalone_execution_pp'])-float(z['DeltaC_pp']))<1e-12
names=['HR','Finance','Industrial','Pharma','Biomedical','Economics'];labels=['HR','Finance','Industrial','Pharma.','Biomed.','Econ.']
models=['Ridge_Q','Ridge_QP','LightGBM_Q','LightGBM_QP'];colors=['#2B6CB0','#D46A1F','#288B68','#884A9E'];markers=['o','s','^','D']
fig,axs=plt.subplots(1,2,figsize=(7.16,2.65));fig.subplots_adjust(left=.105,right=.985,top=.91,bottom=.265,wspace=.39)
for j,method in enumerate(models):
    for k,d in enumerate(names):
        z=next(z for z in capacity if z['domain']==d and z['method']==method);y=k+(j-1.5)*.16
        axs[0].plot([float(z['DeltaC_low_pp']),float(z['DeltaC_high_pp'])],[y,y],color=colors[j],lw=1.1,ls='--' if d=='Economics' else '-')
        axs[0].scatter(float(z['DeltaC_pp']),y,color=colors[j],marker=markers[j],s=15,edgecolor='white',linewidth=.3,zorder=3,label=method.replace('_',' ') if k==0 else None)
axs[0].axvline(0,color='#444',lw=.75);axs[0].set_xlim(-48,42);axs[0].set_xticks([-40,-20,0,20,40]);axs[0].set_xlabel('Matched-risk saving '+r'$\Delta C$'+' (pp of FullV)');axs[0].set_title('(a) Capacity controls',loc='left',fontweight='bold')
series=[('oracle_headroom_pp','#2F8A72','H: headroom'),('selector_loss_pp','#C47529','S: selection loss'),('realized_minus_standalone_execution_pp','#9563A4','O: path difference')]
for j,(key,c,label) in enumerate(series):
    vals=[float(next(z for z in selection if z['domain']==d)[key]) for d in names]
    axs[1].barh(np.arange(6)+(j-1)*.21,vals,height=.18,color=c,label=label,zorder=3)
delta_labels=[]
for k,d in enumerate(names):
    z=next(z for z in selection if z['domain']==d);txt=format(float(z['DeltaC_pp']),'+.1f');delta_labels.append(txt)
    axs[1].text(75,k,txt,ha='right',va='center',fontsize=7,bbox={'facecolor':'white','alpha':.85,'edgecolor':'none','pad':.2})
assert delta_labels==['-10.8','+3.3','+0.7','-8.6','-21.8','-3.2']
axs[1].set_xlim(0,76);axs[1].set_xticks([0,20,40,60]);axs[1].set_xlabel('pp of same-batch FullV; '+r'$\Delta C=H-S-O$');axs[1].set_title('(b) LightGBM-QP decomposition',loc='left',fontweight='bold')
for ax in axs:
    ax.set_yticks(range(6),labels);ax.set_ylim(5.65,-.65);ax.grid(axis='x',color='#e7ebef',lw=.5);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)
handles=[];ll=[]
for ax in axs:
    h,l=ax.get_legend_handles_labels();handles+=h;ll+=l
fig.legend(handles,ll,ncol=7,loc='lower center',bbox_to_anchor=(.5,.015),fontsize=7,frameon=False,columnspacing=.8,handlelength=1.1,handletextpad=.4)
assert min(t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text())>=7
save(fig,'posthoc_diagnostic')
# Lifecycle arrays are copied from the exact prior 019 figure source and checked against 017.
setup=read('G2_setup_repeats.csv');warm=read('G2_same_cohort_warm.csv');cross=read('G2_break_even_ranges.csv');curves=read('fig1b_fig5_curve_points_017.csv');OCR=407.725
scenarios=['OCR_EXCLUSIVE_NEW_INDEX','OCR_SHARED_HALF_NEW_INDEX','OCR_PREPAID_NEW_INDEX'];fractions=[1,.5,0]
def values(model,rep,sc):
    s=next(z for z in setup if z['model']==model and int(z['repeat'])==rep)
    f,r=[float(next(z['warm_E2E_s'] for z in warm if z['model']==model and int(z['repeat'])==rep and z['plan']==p)) for p in ['Full-Visual','BM25-R100']]
    base=float(s['base_process_startup_wall_s'])+float(s['index_wall_s']);extra=float(s['BM25_build_wall_s'])+fractions[scenarios.index(sc)]*OCR
    return base,extra,f,r
for z in curves:
    ratios=[]
    for rep in [1,2,3]:
        b,e,f,r=values(z['model'],rep,z['scenario']);n=float(z['N']);ratios.append((b+e+n*r)/(b+n*f))
    assert all(math.isclose(float(z[k]),v,rel_tol=1e-12,abs_tol=1e-12) for k,v in zip(['mean_ratio','observed_min','observed_max'],[statistics.mean(ratios),min(ratios),max(ratios)]))
for z in cross:
    if z['scenario'] in scenarios:
        b,e,f,r=values(z['model'],int(z['repeat']),z['scenario']);assert math.ceil(e/(f-r))==int(z['conditional_break_even_N'])
fig=plt.figure(figsize=(3.5,3.35));top=fig.add_axes([.205,.69,.765,.20]);axes=[fig.add_axes([.18,.17,.34,.31]),fig.add_axes([.62,.17,.34,.31])]
for i,(label,key) in enumerate([('Load','model_load_wall_s'),('Index build','index_wall_s')]):
    for model,shift,marker,c in [('ColQwen2',-.22,'o','#2166AC'),('ColPali',.22,'s','#1B7837')]:
        vals=[float(z[key]) for z in setup if z['model']==model]
        top.plot([min(vals),max(vals)],[i+shift]*2,color=c,lw=.8);top.plot(vals,[i+shift]*3,ls='',marker=marker,color=c,mfc='white' if model=='ColPali' else c,ms=3.4)
        if label=='Index build':top.text(105,i+shift,f'{min(vals):.1f}–{max(vals):.1f}',ha='right',va='center',fontsize=6.5,color=c)
top.plot(OCR,2,marker='D',color='#E08214',ms=4);top.text(OCR*.9,2,'407.725 s',ha='right',va='center',fontsize=6.5)
top.set(xscale='log',xlim=(2,650),ylim=(2.45,-.45),yticks=[0,1,2],yticklabels=['Load','Index build','OCR'],xlabel='Setup wall time (s)');top.set_xticks([10,100]);top.grid(axis='x',ls=':',lw=.4)
top.annotate('(a) Setup cost',xy=(.5,0),xycoords='axes fraction',xytext=(0,-35),textcoords='offset points',fontsize=8,ha='center',va='top')
palette=[('#252525','-','Exclusive'),('#2166AC','--','50% shared'),('#D62728',':','Prepaid')]
for ax,model,tag in zip(axes,['ColQwen2','ColPali'],['(b) ColQwen2','(c) ColPali']):
    for sc,(c,ls,label) in zip(scenarios,palette):
        rr=[z for z in curves if z['model']==model and z['scenario']==sc];x=[float(z['N']) for z in rr]
        ax.fill_between(x,[float(z['observed_min']) for z in rr],[float(z['observed_max']) for z in rr],color=c,alpha=.13,linewidth=0)
        ax.plot(x,[float(z['mean_ratio']) for z in rr],color=c,ls=ls)
        ns=[100,1000,10000,100000];ys=[]
        for n in ns:
            vals=[]
            for rep in [1,2,3]:
                b,e,f,r=values(model,rep,sc);vals.append((b+e+n*r)/(b+n*f))
            ys.append(statistics.mean(vals))
        ax.plot(ns,ys,ls='',marker='o',ms=2,color=c)
        xx=[int(z['conditional_break_even_N']) for z in cross if z['model']==model and z['scenario']==sc]
        ax.plot([min(xx),max(xx)],[1,1],color=c,lw=2,marker='|',ms=4,zorder=5)
    ax.axhline(1,color='#8C8C8C',ls='--',lw=.6,zorder=0);ax.set(xscale='log',xlim=(10,125000),ylim=(.8,3.8),xlabel='Query volume $N$',yticks=[1,2,3]);ax.set_xticks([10,1000,100000]);ax.grid(axis='y',ls=':',lw=.4)
    ax.annotate(tag,xy=(.5,0),xycoords='axes fraction',xytext=(0,-31),textcoords='offset points',fontsize=8,ha='center',va='top')
axes[0].set_ylabel('Total-cost ratio\n(BM-100 / FullV)',fontsize=6.5,labelpad=0);axes[1].tick_params(labelleft=False)
fig.legend(handles=[Line2D([],[],marker='o',color='#2166AC',ls='',label='ColQwen2'),Line2D([],[],marker='s',mfc='white',color='#1B7837',ls='',label='ColPali'),Line2D([],[],marker='D',color='#E08214',ls='',label='OCR'),*[Line2D([],[],color=c,ls=ls,label=l) for c,ls,l in palette]],loc='upper center',bbox_to_anchor=(.51,1.005),frameon=False,ncol=3,columnspacing=.7,handletextpad=.3,handlelength=1.2,fontsize=7)
save(fig,'fig5_lifecycle')
checks=dict(status='PASS',fig5_capacity_points=24,fig5_capacity_CIs=24,fig5_decomposition_values=18,fig5_delta_labels=delta_labels,fig5_height_reduction_pct=100*(1-2.65/3.65),fig5_min_font_pt=7,lifecycle_curve_points=len(curves),lifecycle_arrays_recomputed_from_017=True,lifecycle_observed_bands_unchanged=True,lifecycle_crossings_unchanged=True,lifecycle_height_reduction_pct=100*(1-3.35/4.5),OCR_s=OCR,scientific_values_changed=0)
(root/'scientific_array_checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks))
