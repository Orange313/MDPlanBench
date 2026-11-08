"""Shared print-first scientific plot style; data-only standalone renderer."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np,csv,json,hashlib,os
BASE=Path(__file__).resolve().parent;DATA=BASE/'data';OUT=Path(os.environ.get('MDROUTER_FIG_OUT',str(BASE/'output')));OUT.mkdir(parents=True,exist_ok=True)
P={'FullV':'#252525','R100':'#2166AC','R50':'#A6BDDB','BM25':'#E08214','Q':'#6A3D9A','QP':'#D62728','RR-hard':'#8C564B','RR-soft':'#8C564B','Mix-Q':'#888888','Mix-QP':'#888888','FixedMix':'#888888','Env':'#555555','Oracle':'#1B7837','Good':'#E5EDDE','Band':'#F4F4F4'}
M={'FullV':'s','R100':'o','R50':'o','BM25':'^','Q':'D','QP':'*','RR-hard':'v','RR-soft':'v','Mix-Q':'s','Mix-QP':'x','FixedMix':'s'}
NAMES={'FullV':'FullV','R100':'BM-100','R50':'BM-50','BM25':'BM25','Q':'Q','QP':'QP','RR-hard':'RR hard','RR-soft':'RR soft','Mix-Q':'Executed mix','Mix-QP':'Executed mix','FixedMix':'Executed mix'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7.5,'axes.labelsize':7.5,'axes.titlesize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'figure.dpi':150,'savefig.dpi':300,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'MDRouter019','axes.linewidth':.6,'lines.linewidth':1.1,'xtick.direction':'in','ytick.direction':'in','xtick.major.size':2.3,'ytick.major.size':2.3,'grid.linewidth':.4,'grid.linestyle':':','grid.color':'#D0D0D0','axes.unicode_minus':True,'hatch.linewidth':.6})
MAN=json.loads((DATA/'MANIFEST.json').read_text());USED={};READ={}
def rows(name):
 p=DATA/name;h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==MAN['files'][name]['sha256'],('INPUT_HASH_CHANGED',name);READ[name]=h
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def v(r,k):
 z=float(r[k]);assert np.isfinite(z);return z
def point(d,m,model='ColQwen2'):return next(r for r in rows(MAN.get('plot_points_file','plan_points.csv')) if r['domain']==d and r['method']==m and r['model']==model)
def subset(name,**keys):return [r for r in rows(name) if all(r[k]==str(x) for k,x in keys.items())]
def axes(ax,xgrid=False,ygrid=True):
 ax.set_axisbelow(True);ax.grid(ygrid,axis='y');ax.grid(xgrid,axis='x')
def panel(ax,txt):ax.annotate(txt,xy=(.5,0),xycoords='axes fraction',xytext=(0,-27),textcoords='offset points',fontsize=8,ha='center',va='top')
def handle(m,open=False,label=None):return Line2D([],[],color=P[m],marker=M[m],ls='none',ms=4 if m=='R50' else (5 if m!='QP' else 7),mfc='white' if open or m in ['RR-soft','Mix-Q','FixedMix'] else P[m],mec=P['R100'] if m=='R50' else P[m],label=label or NAMES[m])
def mark(ax,r,open=False,err=True,ms=4):
 m=r['method'];x,y=v(r,'risk'),v(r,'cost_pct_FullV');col=P['R100'] if m=='R50' else P[m]
 a=ax.errorbar(x,y,xerr=[[max(0,x-v(r,'r_low'))],[max(0,v(r,'r_high')-x)] ] if err else None,yerr=[[max(0,y-v(r,'cost_low_pct'))],[max(0,v(r,'cost_high_pct')-y)]] if err else None,fmt=M[m],ms=3.2 if m=='R50' else (4 if m!='QP' else 5.5),mfc='white' if open or m in ['Mix-Q','FixedMix','RR-soft'] else P[m],mec=col,mew=.75,color=col,elinewidth=.6,capsize=1.1,zorder=4)
 assert abs(a.lines[0].get_xdata()[0]-x)<1e-6 and abs(a.lines[0].get_ydata()[0]-y)<1e-6
 return a
def legend(fig,methods,**kw):fig.legend(handles=[handle(m) for m in methods],frameon=False,**kw)
def save(fig,name):
 fig.canvas.draw();texts=[t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()];minfont=min([t.get_fontsize() for t in texts] or [100]);assert minfont>=6.5,(name,minfont)
 renderer=fig.canvas.get_renderer();bounds=fig.bbox;outside=[];undrawn_tick_labels=set()
 for ax in fig.axes:
  for axis in [ax.xaxis,ax.yaxis]:
   lo,hi=sorted(axis.get_view_interval())
   for tick in axis.get_major_ticks()+axis.get_minor_ticks():
    if tick.get_loc()<lo-1e-9 or tick.get_loc()>hi+1e-9:undrawn_tick_labels.update([id(tick.label1),id(tick.label2)])
 for t in texts:
  if id(t) in undrawn_tick_labels:continue
  bb=t.get_window_extent(renderer)
  if bb.x0<-.75 or bb.y0<-.75 or bb.x1>bounds.width+.75 or bb.y1>bounds.height+.75:outside.append(t.get_text())
 assert not outside,('TEXT_CLIPPED',name,outside)
 path=OUT/(name+'_019.png');assert not path.exists(),('REFUSE_OVERWRITE',path)
 fig.savefig(path,format='png',dpi=300,bbox_inches='tight',pad_inches=.01,metadata={'Software':'MDRouter019'})
 receipt={'figure':name+'_019','size_inches':list(fig.get_size_inches()),'font_min_pt':minfont,'inputs':dict(READ),'text_values':[t.get_text() for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()],'GPU_jobs':0,'new_statistics':False};(OUT/'qa'/(name+'_019_receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n');plt.close(fig)
