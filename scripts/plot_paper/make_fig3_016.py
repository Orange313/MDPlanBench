from style import *
from matplotlib.patches import Patch
fig,aa=plt.subplots(2,4,figsize=(7.16,4.0));fig.subplots_adjust(left=.066,right=.987,bottom=.22,top=.84,wspace=.36,hspace=.85)
for ax,domain,letter in zip(aa.ravel(),['HR','Finance','Industrial','Pharma','Biomedical','Economics'],'abcdef'):
 panel(ax,f'({letter}) {domain}');axes(ax)
 for model,op,ls in [('ColQwen2',False,'-'),('ColPali',True,'--')]:
  rr=subset('envelope_vertices.csv',domain=domain,model=model)
  if not rr:continue
  rr=sorted(rr,key=lambda r:v(r,'order'));ax.plot([v(r,'risk') for r in rr],[v(r,'cost_pct_FullV') for r in rr],color=P['Env'],ls=ls,lw=.9,zorder=2)
  for m in ['FullV','R50','R100','BM25']:mark(ax,point(domain,m,model),open=op,ms=3.5)
 r=point(domain,'R100');ax.text(.97,.94,f"BM-100 saving\n{100-v(r,'cost_pct_FullV'):.1f}%"+('\nOff static envelope' if domain=='Biomedical' else ''),transform=ax.transAxes,ha='right',va='top',fontsize=6.5,color=P['R100'])
 xmax=max(v(point(domain,m,mo),'r_high') for mo in (['ColQwen2'] if domain=='Economics' else ['ColQwen2','ColPali']) for m in ['FullV','R50','R100','BM25']);ax.set(xlim=(-.007,max(.11,xmax*1.03)),ylim=(-3,110),xlabel='Mean positive regret');ax.set_ylabel('Warm E2E (% FullV)' if domain in ['HR','Biomedical'] else '')
 if domain=='Economics':ax.text(.97,.69,'ColPali: NOT_RUN\n1 source component',transform=ax.transAxes,ha='right',va='top',fontsize=6.5,color='#555555')
 if domain=='Biomedical':ax.text(.97,.51,'ColPali: post-hoc',transform=ax.transAxes,ha='right',va='top',fontsize=6.5,color='#555555')
g,h=aa[1,2:];panel(g,'(g) Containment');cr=rows('containment_groups.csv');cats=[('complete_no_harm','#C8C8C8','Complete / no harm'),('incomplete_no_harm',P['R100'],'Incomplete / no harm'),('incomplete_harm',P['QP'],'Incomplete / harm')]
for i,r in enumerate(cr):
 left=0
 for k,c,label in cats:
  z=v(r,k)/v(r,'n')*100;g.barh(i,z,left=left,color=c,height=.5,edgecolor='white',hatch='///' if k=='incomplete_harm' else None,lw=.4)
  if z>5:g.text(left+z/2,i,str(int(v(r,k))),ha='center',va='center',fontsize=6.5,color='white' if k!='complete_no_harm' else '#252525')
  left+=z
g.set(yticks=[0,1],yticklabels=['Bio','Eco'],xlim=(0,100),xlabel='Queries (%)',ylim=(-.7,1.7));g.invert_yaxis();axes(g)
panel(h,'(h) Recovery');rr=rows('repair_counts.csv');order=[('ColQwen2',d) for d in ['HR','Finance','Industrial','Pharma']]+[('ColPali','ALL_DEV'),('ColQwen2','Biomedical'),('ColQwen2','Economics')];labels=['HR','Fin','Ind','Pha','Pali-Dev','Bio','Eco']
for i,(mo,d) in enumerate(order):
 z=[r for r in rr if r['model']==mo and (r['domain']==d or d=='ALL_DEV' and r['domain'] in ['HR','Finance','Industrial','Pharma'])];a=sum(v(r,'fully_repaired') for r in z);b=sum(v(r,'still_harmed') for r in z);c=sum(v(r,'newly_harmed') for r in z);h.barh(i,a,color=P['Oracle'],height=.62);h.barh(i,b,left=a,color=P['QP'],height=.62,hatch='///',edgecolor='white',lw=.3);h.barh(i,c,left=a+b,color='white',edgecolor=P['QP'],hatch='xxx',height=.62,lw=.6)
 if a>=3:h.text(a/2,i,str(int(a)),color='white',va='center',ha='center',fontsize=6.5)
 if 0<a<3:h.text(a+b+c+1,i,f'repair {int(a)}',color=P['Oracle'],va='center',fontsize=6.5)
 if b:h.text(a+b/2,i,str(int(b)),color='white',va='center',ha='center',fontsize=6.5)
 if c:h.text(a+b+c+.6,i,'+'+str(int(c)),va='center',fontsize=6.5,color=P['QP'])
h.set(yticks=range(len(labels)),yticklabels=labels,xlabel='Query count',xlim=(0,53));h.invert_yaxis();axes(h)
fig.legend(handles=[handle(m) for m in ['FullV','R100','R50','BM25']]+[Line2D([],[],color=P['Env'],ls='-',label='ColQwen2 / filled'),Line2D([],[],color=P['Env'],ls='--',marker='o',mfc='white',ms=3,label='ColPali / open')],loc='upper center',bbox_to_anchor=(.5,.99),frameon=False,ncol=6,columnspacing=1.0,handlelength=1.5,handletextpad=.4)
fig.legend(handles=[Patch(facecolor=co,edgecolor='white' if hatch=='///' else P['QP'] if hatch=='xxx' else co,hatch=hatch,label=la) for co,hatch,la in [('#C8C8C8',None,'Complete / r=0'),(P['R100'],None,'Miss / r=0'),(P['QP'],'///','Miss / r>0'),(P['Oracle'],None,'Repaired'),(P['QP'],'///','Still harmed'),('white','xxx','New harm')]],loc='upper center',bbox_to_anchor=(.5,.93),frameon=False,ncol=6,columnspacing=.8,handletextpad=.3)
save(fig,'fig3_static_frontiers')
