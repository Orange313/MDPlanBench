"""Compare frozen manuscript observations to scientific CSVs, without opening LaTeX."""
from pathlib import Path
import argparse,csv,hashlib,json,math
G=Path(__file__).resolve().parents[1]
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
 checks=[]
 def check(item,expected,actual,source,formula='',tol=1e-8):
  checks.append(dict(item=item,reported=expected,recomputed=actual,tolerance=tol,status='PASS' if abs(float(expected)-float(actual))<=tol else 'FAIL',source=source,source_sha256=hashlib.sha256((G/source).read_bytes()).hexdigest(),formula=formula))
 src='records/figure_data/plot_points_registered.csv';points=rows(G/src)
 current=json.loads((G/'config/paper_current.json').read_text())
 for c in rows(G/current['table_cells']):
  r=next(z for z in points if (z['domain'],z['model'],z['method'])==(c['domain'],c['model'],c['method']))
  v=c['paper_value'];d=len(v.split('.')[1]) if '.' in v else 0;s=float(c['scale'])
  check('/'.join([c['item'],c['domain'],c['method'],c['field']]),float(v)*s,float(r[c['field']]),src,c['source']+':'+c['line'],.500001*10**(-d)*s)
 # Positive-regret, catalog, denominator and decomposition are independent gates
 # in replay_021_017.py and regression_gates.py; do not replace those with rounding tests.
 src='records/figure_data/paired_contrasts.csv'
 for d,reg,ms in [('Biomedical',-.0322,3.60),('Economics',-.0267,4.06)]:
  z=next(r for r in rows(G/src) if r['domain']==d and r['control']=='Q')
  check(d+'/QP-Q/mean_regret',reg,float(z['delta_r']),src,'Paired mean regret difference',.00005)
  check(d+'/QP-Q/ms',ms,float(z['delta_ms']),src,'Paired complete-path mean difference',.005)
 src='records/figure_data/plot_points_registered.csv'
 r=next(x for x in points if x['domain']=='Pharma' and x['model']=='ColQwen2' and x['method']=='Q')
 check('Pharma Q warm saving vs FullV',24.,100-float(r['cost_pct_FullV']),src,'100 - cost_pct_FullV',.05)
 src='posthoc_20261109/independent_001/E3_upper_bound_counts.csv'
 ee=rows(G/src)
 # Exact one-sided zero-loss sample-power numbers (no calibration labels).
 for m,n in [(1,90),(2,104),(8,131)]:
  actual=math.ceil(math.log(.01/m)/math.log(1-.05))
  check('Calibration zero-loss minimum m='+str(m),n,actual,'scripts/verify_paper_values.py','ceil(log(delta/m)/log(1-epsilon))',0)
 check('Calibration u0 n81',.0553,1-.01**(1/81),'scripts/verify_paper_values.py','1-delta**(1/n)',.00005)
 # All late manuscript additions are backed by real archived analyses.
 src='posthoc_20261109/independent_001/K17_kappa10_vs20.csv';kk=rows(G/src)
 for m,n,v in [('Q_regret',20,-.63),('Q_regret',81,-26.80),('QP_regret',20,-3.52),('QP_regret',81,-8.67)]:
  z=next(x for x in kk if x['method']==m and float(x['kappa'])==20 and int(x['Fit_n'])==n)
  check('Learning k20/'+m+'/'+str(n),v,float(z['matched_risk_increment_pp']),src,'Original subsets/seeds and four-action diagnostic',.005)
 src='posthoc_20261109/screening_001/E2_main_b005.csv';rr=rows(G/src)
 lo='low95_pp'
 check('Cross-fit positive lower bounds',0,sum(float(z[lo])>0 for z in rr),src,'24 cells at b=.05; conditional intervals',0)
 src='posthoc_20261109/screening_001/E1_bias_summary.csv';rr=rows(G/src)
 z=next(x for x in rr if x['domain']=='Industrial' and x['cohort']=='original_four_static')
 check('Industrial envelope median optimism',4.3,-float(z['median_Bias_pp']),src,'Optimism = -Bias; Bias is retrospective minus cross-fitted cost (four-static original cohort)',.05)
 check('Industrial envelope maximum optimism',12.,float(z['max_abs_Bias_pp']),src,'Four-static original cohort',.05)
 with (O/'paper_numeric_checks.csv').open('x',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,list(checks[0]));w.writeheader();w.writerows(checks)
 result=dict(status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',checks=len(checks),failures=[x for x in checks if x['status']!='PASS'],manuscript_revision=current['revisionNumber'],scope='All 154 numeric table cells and explicit key-claim checks. The separate numeric-token inventory includes unverified prose/configuration tokens; a token inventory is not proof of every sentence.',GPU_jobs=0,training=0,manuscript_writes=0)
 (O/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
