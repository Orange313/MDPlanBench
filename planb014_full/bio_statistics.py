"""Exact archived 008 L0 grouped bootstrap, IO isolated from private resource traces."""
from pathlib import Path
import numpy as np,csv,json,collections,sys,hashlib
ROOT=Path(sys.argv[1]);META=json.loads(Path(sys.argv[2]).read_text());METHODS=['Full-Visual','BM25-R50','BM25-R100','BM25','Q_regret','QP_regret','RandomMix','RR_hard','RR_soft'];ids=META['query_ids'];base=ROOT/'reports/icde_eab_independent_007/T2'
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
quality=read(base/'process_0_001/quality.csv');qm={(int(x['query_id']),x['method']):x for x in quality};bucket=collections.defaultdict(list)
for proc in range(3):
 for x in read(base/f'process_{proc}_001/requests.csv'):bucket[int(x['query_id']),int(x['process']),x['method']].append(x)
T=np.array([[[np.mean([float(x['E2E_s']) for x in bucket[q,p,m]])*1000 for m in METHODS] for p in range(3)] for q in ids]);R=np.array([[float(qm[q,m]['r']) for m in METHODS] for q in ids]);U=np.array([[float(qm[q,m]['nDCG10']) for m in METHODS] for q in ids]);qi=5;summary=[];B=2000
for grouping,offset in [('source_group',1),('family',0)]:
 groups=np.array([qm[q,'Full-Visual'][grouping] for q in ids]);rng=np.random.default_rng(META['seed']+offset);u=np.unique(groups);indices=[np.concatenate([np.flatnonzero(groups==h) for h in rng.choice(u,len(u),replace=True)]) for _ in range(B)];processes=np.random.default_rng(META['seed']+43).integers(0,3,(B,3));br=np.array([R[ix].mean(0) for ix in indices]);bu=np.array([U[ix].mean(0) for ix in indices]);bt=np.array([T[ix][:,pi].mean((0,1)) for ix,pi in zip(indices,processes)])
 for ctrl in ['BM25-R100','BM25-R50','Q_regret']:
  j=METHODS.index(ctrl);dr=br[:,qi]-br[:,j];du=bu[:,qi]-bu[:,j];dt=bt[:,qi]-bt[:,j]
  for metric,point,arr,direction in [('positive_regret_delta',R[:,qi].mean()-R[:,j].mean(),dr,'negative_better'),('nDCG10_delta',U[:,qi].mean()-U[:,j].mean(),du,'positive_better'),('complete_E2E_ms_delta',T[:,:,qi].mean()-T[:,:,j].mean(),dt,'negative_better')]:
   lo,hi=np.quantile(arr,[.025,.975]);blo,bhi=np.quantile(arr,[.0125,.9875]);summary.append({'contrast':'QP_minus_'+ctrl,'control':ctrl,'grouping':grouping,'queries':160,'groups':len(set(groups)),'metric':metric,'estimate':point,'low95':lo,'high95':hi,'low97p5_for_two_endpoint_sensitivity':blo,'high97p5_for_two_endpoint_sensitivity':bhi,'favorable_direction':direction,'bootstrap_draw_fraction_QP_lower_r_and_lower_E2E':float(np.mean((dr<0)&(dt<0))),'bootstrap_repetitions':B,'scope':'POST_HOC_PAIRED_DESCRIPTIVE_POINTWISE;97.5% percentile sensitivity only adjusts the two r/E2E endpoints per comparator, not all analyses; no delta-PAC claim'})
p=ROOT/'reports/icde_eab_lastmile_008/L0/paired_all_comparisons.csv';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('x',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
assert hashlib.sha256(p.read_bytes()).hexdigest()==META['paired_sha256'],'Biomedical grouped CI numerical replay changed'
print(json.dumps({'status':'PASS_BIOMEDICAL18_PAIRED_CELLS','rows':len(summary),'B':2000,'groupings':['27sources','157families'],'all_bytes_match':True}))
