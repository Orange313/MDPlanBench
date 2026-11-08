from style import *
rr=rows('AA_equivalence_intervals.csv');fig,ax=plt.subplots(figsize=(3.5,2.65));fig.subplots_adjust(left=.33,right=.97,bottom=.20,top=.87);ax.axvspan(.9,1.1,color=P['Good']);ax.axvline(1,color='#B0B0B0',ls='--',lw=.7);labels=[];ys=[]
for i,(batch,dom,qps) in enumerate((b,d,q) for b in ['Initial','Repeat'] for d in ['HR','Pharma'] for q in [2,5]):
 if batch=='Repeat':ax.axhspan(i-.45,i+.45,color=P['Band'],zorder=0)
 labels.append(('First' if batch=='Initial' else 'Repeat')+' '+dom+f' {qps}');ys.append(i)
 for metric,dy,m,col in [('Service',-.12,'o',P['R100']),('Response',.12,'s',P['FullV'])]:
  r=next(z for z in rr if z['batch']==batch and z['domain']==dom and int(z['QPS'])==qps and z['metric']==metric);x,lo,hi=v(r,'ratio'),v(r,'low'),v(r,'high');ax.hlines(i+dy,lo,hi,color=col,lw=.8);ax.plot(x,i+dy,m,ms=3.4,color=col)
ax.set(yticks=ys,yticklabels=labels,ylim=(7.6,-.6),xlabel='B / A latency ratio (98.75% intervals)',xlim=(min(.6,min(v(r,'low') for r in rr)-.05),max(1.45,max(v(r,'high') for r in rr)+.05)));axes(ax,True,False);fig.legend(handles=[Line2D([],[],marker='o',color=P['R100'],ls='',ms=4,label='Service'),Line2D([],[],marker='s',color=P['FullV'],ls='',ms=4,label='Total response')],loc='upper center',bbox_to_anchor=(.59,1.0),ncol=2,frameon=False,handletextpad=.3);fig.text(.5,.025,'QPS per row; target band [0.9, 1.1].',ha='center',fontsize=6.5)
save(fig,'fig6_aa_equivalence')
