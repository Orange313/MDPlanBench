"""Inference parity from saved small router parameters and numerical features; no fit."""
from pathlib import Path
import argparse,csv,hashlib,json
import lightgbm as lgb
import numpy as np
G=Path(__file__).resolve().parents[1];S=G/'records/021_snapshot/artifacts/icde_eab_review_strengthening_021'
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);a=ap.parse_args();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
models=json.loads((G/'config/frozen_capacity_models.json').read_text());expected=json.loads((S/'EX1/predictions_and_allocations.json').read_text());meta=json.loads((S/'EX0/domains.json').read_text());checks=[]
blocks={'Q':[],'QP':list(range(13)),'Q_distribution':[0,1,2,3,4,5,9,10,12],'Q_gaps':[6,7,8],'Q_coverage':[11]}
for dom in meta:
 with np.load(S/('EX0/'+dom['domain']+'.npz'),allow_pickle=False) as z:Q=z['Q'];P=z['P']
 for name,m in models.items():
  pp=blocks[m['block']];X=np.c_[Q,P[:,pp]] if pp else Q
  if m['kind']=='Ridge':
   cols,median,mu,sd,w,bias=[np.array(v) for v in m['model']];v=X[:,cols.astype(bool)];mis=~np.isfinite(v);v=np.c_[np.where(mis,median,v),mis.astype(float)];pred=(v-mu)/sd@w+bias
  else:
   pre=m['preprocess'];v=X[:,np.array(pre['cols'],bool)];mis=~np.isfinite(v);v=np.c_[np.where(mis,np.array(pre['median']),v),mis];boosters=[lgb.Booster(model_str=t) for t in m['model']];pred=np.stack([b.predict(v,num_threads=1) for b in boosters],axis=1)
  ref=np.array(expected[dom['domain']][name]['prediction']);err=float(np.max(np.abs(pred-ref)));cost=np.array(dom['cvec'])[[0,2,3]];cost/=cost[0];act=np.array([0,2,3])[np.argmin(cost+20*np.maximum(pred,0),axis=1)];same=bool(np.array_equal(act,np.array(expected[dom['domain']][name]['actions'])))
  checks.append(dict(domain=dom['domain'],model=name,queries=len(Q),features=X.shape[1],max_prediction_abs_error=err,tolerance=1e-10,actions_exact=same,status='PASS' if err<=1e-10 and same else 'FAIL'))
with (O/'frozen_inference_checks.csv').open('x',newline='',encoding='utf8') as f:w=csv.DictWriter(f,list(checks[0]));w.writeheader();w.writerows(checks)
r=dict(status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',cells=len(checks),query_model_pairs=sum(x['queries'] for x in checks),max_error=max(x['max_prediction_abs_error'] for x in checks),models_sha256=hashlib.sha256((G/'config/frozen_capacity_models.json').read_bytes()).hexdigest(),lightgbm_version=lgb.__version__,new_models_trained=0,raw_labels_read=0,scope='Frozen numeric-feature inference parity only; no new effectiveness experiment or timing')
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(r['status']!='PASS')
