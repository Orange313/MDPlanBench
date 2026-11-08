from style import *
fig=plt.figure(figsize=(7.16,3.9));gs=fig.add_gridspec(1,4,width_ratios=[2.3,1,1,1],left=.128,right=.985,bottom=.25,top=.81,wspace=.54);a,b,c,d=[fig.add_subplot(gs[0,i]) for i in range(4)];panel(a,'(a) Saving at matched risk');panel(b,'(b) Probe trade-off');panel(c,"(c) QP-risk cost");panel(d,'(d) QP actions')
domains=['HR','Finance','Industrial','Pharma','Biomedical','Economics'];ys=[];yl=[]
for i,dom in enumerate(domains):
 base=4*i
 if i>=4:a.axhspan(base-.45,base+2.5,color=P['Band'],zorder=0)
 for j,m in enumerate(['Q','QP','RR-hard','RR-soft']):
  y=base+(j if j<2 else 2+(-.12 if j==2 else .12));r=point(dom,m);xx=v(r,'gain_pp');lo=v(r,'gain_low');hi=v(r,'gain_high');col=P[m];a.hlines(y,lo,hi,color=col,lw=.7,ls='--' if dom=='Economics' else '-');a.plot(xx,y,marker=M[m],ms=4.2 if m!='QP' else 6,mfc='white' if m=='RR-soft' else col,mec=col,mew=.7)
  if j<2:a.text(xx+1.6,y-.18,f'{xx:+.1f}',color=col,fontsize=6.5,va='bottom');oo=subset('oracle_at_router_risk.csv',domain=dom,policy=m)[0];a.plot(v(oo,'headroom_vs4_pp'),y,marker='|',color=P['Oracle'],ms=8,mew=1.2)
 ys.extend([base,base+1,base+2]);yl.extend([dom+'  Q','QP','RR h/s'])
a.axvline(0,color='#B0B0B0',ls='--',lw=.8);a.set(yticks=ys,yticklabels=yl,xlim=(-48,68),ylim=(22.8,-.7),xticks=[-40,-20,0,20,40,60],xlabel='Saving (pp of FullV)\nMore costly  |  Cheaper');axes(a,True,False);a.tick_params(axis='y',labelsize=6.5)
b.axhline(0,color='#B0B0B0',ls='--',lw=.6);b.axvline(0,color='#B0B0B0',ls='--',lw=.6);xmin,xmax=-14,9;ymin,ymax=-.07,.045;b.fill_between([xmin,0],ymin,0,color=P['Good']);b.text(.05,.03,'QP lower risk\nand cheaper',transform=b.transAxes,fontsize=6.5,color=P['Oracle'])
for r in rows('paired_contrasts.csv'):
 col=P[r['control']];x,y=v(r,'delta_ms'),v(r,'delta_r');eb=b.errorbar(x,y,xerr=[[x-v(r,'ms_low')],[v(r,'ms_high')-x]],yerr=[[y-v(r,'r_low')],[v(r,'r_high')-y]],fmt='o' if r['domain']=='Biomedical' else 's',ms=3.8,mfc=col if r['domain']=='Biomedical' else 'white',mec=col,color=col,elinewidth=.65,capsize=1)
 for colls in eb.lines[2]:colls.set_linestyle({'Q':'--','R100':'-','R50':':'}[r['control']])
b.set(xlim=(xmin,xmax),ylim=(ymin,ymax),xlabel='QP - control (ms)',ylabel='QP - control regret',xticks=[-10,0],yticks=[-.05,0]);axes(b);b.legend(handles=[Line2D([],[],ls={'Q':'--','R100':'-','R50':':'}[m],marker='o',color=P[m],ms=4,label=NAMES[m]) for m in ['Q','R100','R50']],loc='upper right',frameon=False,handletextpad=.2,borderpad=.1,labelspacing=.2)
for i,dom in enumerate(['Biomedical','Economics']):
 z=subset('QP_cost_decomposition_corrected.csv',domain=dom)[0];hh=subset('oracle_at_router_risk.csv',domain=dom,policy='QP')[0];full=v(z,'FullV_ms');env=100*v(hh,'envelope_3_ms')/full;oq=100*v(hh,'oracle_3_ms')/full;act=100*v(z,'measured_intrinsic_action_ms')/full;over=100*v(z,'measured_nonaction_and_residual_ms')/full;y=i*4
 for yy,val,col in [(y,env,P['Env']),(y+1,act,P['QP']),(y+2,oq,P['Oracle'])]:c.barh(yy,val,height=.65,color=col)
 c.barh(y+1,over,left=act,height=.65,facecolor='white',edgecolor=P['QP'],hatch='////',lw=.6)
 for yy,val in [(y,env),(y+1,act+over),(y+2,oq)]:c.text(val+2,yy,f'{val:.1f}',va='center',fontsize=6.5)
 c.text(.0,y-.9,'Bio' if i==0 else 'Eco',ha='left',va='center',fontsize=7,transform=c.get_yaxis_transform())
c.axvline(100,color='#B0B0B0',ls='--',lw=.7);c.set(xlim=(0,132),ylim=(7,-1.3),yticks=[0,1,2,4,5,6],yticklabels=['Env.','QP','Oracle']*2,xlabel='Warm E2E (% FullV)',xticks=[0,50,100]);axes(c,True,False)
for i,dom in enumerate(['Biomedical','Economics']):
 rr=subset('QP_action_counts.csv',domain=dom);n=sum(v(r,'n') for r in rr);left=0
 for m in ['FullV','R100','BM25']:
  r=next(z for z in rr if z['action']==m);cnt=v(r,'n');wide=100*cnt/n;d.barh(i,wide,left=left,color=P[m],height=.42,edgecolor='white',lw=.4);sev=v(r,'fast_r_gt_005');d.barh(i,100*sev/n,left=left,height=.42,facecolor='none',edgecolor=P['QP'],hatch='////',lw=.6)
  d.text(left+wide/2,i+(0 if wide>=12 else .31),str(int(cnt)),ha='center',va='center',color='white' if wide>=12 else '#252525',fontsize=6.5);left+=wide
 d.text(.02,i-.41,('Bio' if i==0 else 'Eco')+f' (n={int(n)})',transform=d.get_yaxis_transform(),fontsize=7)
d.set(ylim=(1.8,-.8),xlim=(0,100),yticks=[],xticks=[0,50,100],xlabel='Queries (%)');axes(d,True,False)
fig.legend(handles=[handle('Q'),handle('QP'),handle('RR-hard'),handle('RR-soft'),Line2D([],[],marker='|',ls='',color=P['Oracle'],ms=8,label='Offline oracle at router risk')]+[handle(m) for m in ['FullV','R100','BM25']],ncol=5,loc='upper center',bbox_to_anchor=(.53,1.0),frameon=False,columnspacing=1,handlelength=1.1,handletextpad=.3)
fig.text(.54,.025,'Pointwise paired 95% CIs. Eco: conditional on 1 source component. Dev RR: composite cost.',ha='center',fontsize=6.5)
save(fig,'fig4_decision_information')
