"""Recompute earlier seven-plan Dev audit means from original per-query/time records."""
from pathlib import Path
import argparse,csv,json
import numpy as np
G=Path(__file__).resolve().parents[1];D=G/'records/earlier_plan_audit'
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
def rows(n):return list(csv.DictReader((D/n).open(encoding='utf-8-sig')))
q=rows('per_query_quality_cost.csv');t=rows('all_unprofiled_requests.csv');s=rows('static_quality_e2e.csv');checks=[]
for z in s:
 qr=[x for x in q if x['domain']==z['domain'] and x['plan']==z['plan']];tr=[x for x in t if x['domain']==z['domain'] and x['plan']==z['plan']]
 for field,col,data in [('mean_r','r',qr),('mean_nDCG10','nDCG10',qr),('mean_resident_E2E_s','resident_E2E_s',tr),('mean_CPU_s','CPU_s',tr)]:
  val=float(np.mean([float(x[col]) for x in data]));err=abs(val-float(z[field]));checks.append(dict(domain=z['domain'],plan=z['plan'],metric=field,actual=val,expected=float(z[field]),absolute_error=err,status='PASS' if err<=1e-10 else 'FAIL'))
with (O/'mean_checks.csv').open('x',newline='',encoding='utf8') as f:w=csv.DictWriter(f,list(checks[0]));w.writeheader();w.writerows(checks)
r=dict(status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',checks=len(checks),plan_domain_cells=len(s),timings=len(t),queries=len({(x['domain'],x['query_id']) for x in q}),intervals='ARCHIVED_NOT_REBOOTSTRAPPED_BY_THIS_ENTRY',GPU_jobs=0,new_training=0)
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(r['status']!='PASS')
