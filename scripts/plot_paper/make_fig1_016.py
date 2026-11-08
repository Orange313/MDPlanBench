from style import *
for domain in ['Industrial','Biomedical']:
 fig,axs=plt.subplots(1,2,figsize=(3.5,2.35),gridspec_kw={'width_ratios':[1.18,1]});fig.subplots_adjust(left=.145,right=.965,bottom=.33,top=.73,wspace=.55)
 ax,b=axs;panel(ax,'(a) '+domain);panel(b,'(b) Lifecycle')
 curve=rows(('industrial' if domain=='Industrial' else 'biomedical')+'_oracle_curve.csv');x=[v(r,'risk_budget') for r in curve];ax.fill_between(x,[v(r,'envelope4_pct') for r in curve],105,color='#EFEFEF',zorder=0);ax.plot(x,[v(r,'envelope4_pct') for r in curve],color=P['Env'],label='Static envelope');ax.plot(x,[v(r,'oracle3_pct') for r in curve],color=P['Oracle'],ls='-.',label='Offline oracle')
 methods=['FullV','R50','R100','BM25','Q','QP']+(['Mix-Q','Mix-QP'] if domain=='Industrial' else ['FixedMix'])
 for m in methods:mark(ax,point(domain,m),err=m in ['Q','QP'],ms=3.4)
 q=point(domain,'Q');h=subset('oracle_at_router_risk.csv',domain=domain,policy='Q')[0];ax.annotate(f"Q: {v(q,'gain_pp'):+.1f} pp",(v(q,'risk'),v(q,'cost_pct_FullV')),xytext=(.04,.11),textcoords='axes fraction',fontsize=6.5,color=P['Q'],arrowprops={'arrowstyle':'-','color':P['Q'],'lw':.6});ax.text(.97,.90,f"Oracle gap\n{v(h,'headroom_vs4_pp'):.1f} pp",transform=ax.transAxes,ha='right',va='top',color=P['Oracle'],fontsize=6.5)
 ex=v(h,'envelope_4_ms')/v(point(domain,'FullV'),'warm_ms')*100;ox=v(h,'oracle_3_ms')/v(point(domain,'FullV'),'warm_ms')*100;ax.annotate('',(v(q,'risk'),ex),(v(q,'risk'),ox),arrowprops={'arrowstyle':'<->','color':P['Oracle'],'lw':.65})
 ax.set(ylim=(-1,108),xlabel='Mean positive regret',ylabel='Warm E2E (% FullV)');ax.set_xticks([0,.05,.1] if domain=='Industrial' else [0,.15,.3]);ax.set_xlim(-.004,.105 if domain=='Industrial' else .31);axes(ax)
 for sc,co,ls in [('OCR_EXCLUSIVE_NEW_INDEX',P['FullV'],'-'),('OCR_PREPAID_NEW_INDEX',P['QP'],':')]:
  rr=subset('lifecycle_curves.csv',model='ColQwen2',scenario=sc);b.plot([v(r,'N') for r in rr],[v(r,'ratio') for r in rr],color=co,ls=ls,label='OCR exclusive' if ls=='-' else 'OCR prepaid')
 b.axhline(1,color='#B0B0B0',ls='--',lw=.7);b.set(xscale='log',xlim=(10,1e6),ylim=(.8,3.4),xlabel='Query volume N',ylabel='BM-100 / FullV');b.set_xticks([1e2,1e4,1e6]);b.text(.96,.96,'Biomedical\n009 cohort\nConditional model',transform=b.transAxes,ha='right',va='top',fontsize=6.5,color='#555555');axes(b)
 hs=[handle(m) for m in methods]+[Line2D([],[],color=P['Env'],label='Envelope'),Line2D([],[],color=P['Oracle'],ls='-.',label='Offline oracle'),Line2D([],[],color=P['FullV'],label='OCR exclusive'),Line2D([],[],color=P['QP'],ls=':',label='OCR prepaid')];fig.legend(handles=hs,ncol=4,loc='upper center',bbox_to_anchor=(.51,1.0),frameon=False,columnspacing=.6,handlelength=1.0,handletextpad=.25)
 save(fig,'fig1_overview_'+domain.lower())
