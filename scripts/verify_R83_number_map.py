"""Read-only numerical assertions for the R83 artifact (no corpus or GPU access)."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,math
import numpy as np

G=Path(__file__).resolve().parents[1]
def rows(p):
    with (G/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def calculate(s):
    rr=rows(s['source'])
    for k,v in s.get('where',{}).items():rr=[r for r in rr if r[k] in v] if isinstance(v,list) else [r for r in rr if r[k]==str(v)]
    field=s['field']; values=[float(r[field]) for r in rr]
    op=s.get('op','first')
    if op=='first':assert len(values)==1,(s['id'],len(values));v=values[0]
    elif op=='min':v=min(values)
    elif op=='max':v=max(values)
    elif op=='sum':v=sum(values)
    elif op=='mean':v=sum(values)/len(values)
    elif op=='count':v=len(values)
    elif op=='count_positive':v=sum(x>0 for x in values)
    elif op=='max_abs':v=max(map(abs,values))
    else:raise ValueError(op)
    v=v*s.get('scale',1)+s.get('offset',0)
    if s.get('ceil'):v=math.ceil(v)
    if 'round' in s:v=round(v,s['round'])
    return v
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    specs=json.loads((G/'config/paper_R83_claims.json').read_text(encoding='utf8'));checks=[]
    for s in specs:
        v=calculate(s);ok=abs(v-s['expected'])<=s.get('tolerance',0)
        checks.append(dict(item=s['id'],location=s['location'],reported=s['reported'],recomputed=v,status='PASS' if ok else 'FAIL',source=s['source'],row_selector=json.dumps(s.get('where',{}),sort_keys=True),field_formula=f"{s.get('op','first')}({s['field']}) * {s.get('scale',1)} + {s.get('offset',0)}",source_sha256=hashlib.sha256((G/s['source']).read_bytes()).hexdigest(),scope=s.get('scope','ARCHIVED_MEASUREMENTS_OR_DERIVED_RESULTS; CPU_REPLAY')))
    # Metadata and exact bound checks do not inspect calibration labels.
    audit=json.loads((G/'splits/audit.json').read_text())
    values={'Cal families':audit['roles']['new_calibration_sealed']['families'],'Cal components':audit['roles']['new_calibration_sealed']['sources'],'Fit-Cal overlapping components':len(audit['Fit_Cal_intersections']['source_component'])}
    for m in (1,2,8):values['zero-loss n, policies='+str(m)]=math.ceil(math.log(.01/m)/math.log(.95))
    for k,e in [('Cal families',81),('Cal components',20),('Fit-Cal overlapping components',19),('zero-loss n, policies=1',90),('zero-loss n, policies=2',104),('zero-loss n, policies=8',131)]:
        checks.append(dict(item=k,location='sections/06_results.tex, RQ5',reported=e,recomputed=values[k],status='PASS' if e==values[k] else 'FAIL',source='splits/audit.json' if k.startswith(('Cal','Fit')) else 'scripts/verify_R83_number_map.py',row_selector=k,field_formula=k,source_sha256=hashlib.sha256((G/('splits/audit.json' if k.startswith(('Cal','Fit')) else 'scripts/verify_R83_number_map.py')).read_bytes()).hexdigest(),scope='METADATA_OR_EXACT_FORMULA; NO_LABEL_READ'))
    # Verify the documented, author-acknowledged definition discrepancy directly.
    src='planb014_full/inputs/reports/icde_eab_main_006/X2/rebuild_002/all_per_query.csv'
    rr=rows(src)
    for method,wanted in [('Q_regret',96.63915649505253),('QP_regret',88.08924818353047)]:
        r=[x for x in rr if x.get('dataset') in ('Pharma','Pharmaceuticals','vidore_v3_pharmaceuticals') and x.get('policy')==method]
        key='mean_r'
        vv=[float(x[key]) for x in r];assert len(vv)==45
        v=100*sum(x for x in vv if x>.05)/sum(vv)
        checks.append(dict(item='False-Safe '+method,location='sections/06_results.tex:256-260',reported=round(wanted,1),recomputed=v,status='KNOWN_ERRATUM_ACKNOWLEDGED' if abs(v-wanted)<1e-9 else 'FAIL',source=src,row_selector='Pharma / '+method,field_formula='100*sum(r[r>0.05])/sum(r); r>0 would give 100%',source_sha256=hashlib.sha256((G/src).read_bytes()).hexdigest(),scope='R83_DEFINITION_ERRATUM; PUBLICATION_APPROVED; FROZEN_NUMBERS_UNCHANGED'))
    def extra(item,expected,actual,src,formula,tolerance=0,scope='ARCHIVED_NUMERIC_RECORDS; CPU_ONLY'):
        checks.append(dict(item=item,location='R83 quantitative prose (see PAPER_NUMBER_MAP.md)',reported=expected,recomputed=actual,status='PASS' if abs(expected-actual)<=tolerance else 'FAIL',source=src,row_selector=formula,field_formula=formula,source_sha256=hashlib.sha256((G/src).read_bytes()).hexdigest(),scope=scope))
    src='records/figure_data/017/G2_setup_repeats.csv';reps=rows(src)
    for model,want in [('ColQwen2',14.5),('ColPali',10.9)]:
        rs=[r for r in reps if r['model']==model]
        v=100*(1-sum(float(r['warm_R100_s']) for r in rs)/sum(float(r['warm_FullV_s']) for r in rs))
        extra(model+' same-process warm saving',want,v,src,'100*(1-sum(warm_R100_s)/sum(warm_FullV_s)); three processes',.05)
    src='records/figure_data/017/G2_reuse_sensitivity.csv';rr=rows(src)
    vv=[float(x['R100_over_FullV_ratio']) for x in rr if x['scenario']=='OCR_EXCLUSIVE_NEW_INDEX' and x['N'] in ['100','1000']]
    for f,v,want in [('min',min(vv),2.7),('max',max(vv),3.6)]:extra('Lifecycle ratio at100/1000 '+f,want,v,src,f+' exclusive R100/FullV at N={100,1000}',.05)
    src='records/figure_data/017/G2_reuse_sensitivity.csv'
    extra('Historical OCR singleton',407.7,float(rows(src)[0]['OCR_charge_once_s']),src,'OCR_charge_once_s; original407.725; NOT retimed017',.05)
    src='records/021_snapshot/artifacts/icde_eab_review_strengthening_021/EX0/fit.npz'
    with np.load(G/src,allow_pickle=False) as z:
        extra('Fit queries',81,len(z['qids']),src,'len(qids)')
        extra('Fit families',80,len(set(z['family'])),src,'len(unique(family))')
        extra('Fit harmed by BM100',4,int(np.sum(z['Y'][:,2]>1e-10)),src,'count(Y[:,BM100=2]>1e-10)')
        extra('Query features',150,z['Q'].shape[1],src,'Q.shape[1]')
        extra('Probe features',13,z['P'].shape[1],src,'P.shape[1]')
    src='snapshot/reports/icde_final_gate_004/S2/resident_analysis_002/all_unprofiled_requests.csv.gz'
    with gzip.open(G/src,'rt',encoding='utf8') as f:rr=list(csv.DictReader(f))
    for m,lo,hi in [('Q_regret',.48,.51),('QP_regret',1.89,5.97)]:
        ds={r['domain'] for r in rr};vs=[]
        for d in ds:
            rs=[r for r in rr if r['domain']==d and r['method']==m]
            if rs:vs.append(sum((float(r['resident_full_path_E2E_s'])-float(r['selected_path_wall_s']))*1000 for r in rs)/len(rs))
        extra(m+' nonaction min',lo,min(vs),src,'min_domain(mean((resident_full_path_E2E_s-selected_path_wall_s)*1000)); reused probe inside action',.005)
        extra(m+' nonaction max',hi,max(vs),src,'max_domain(mean((resident_full_path_E2E_s-selected_path_wall_s)*1000)); includes residual',.005)
    src='records/historical_summaries/icde_evidence_closure_003/E4/stream_AA_controls.csv'
    vs=[float(r['relative_mean_latency_B_minus_A'])*100 for r in rows(src)]
    extra('Streaming A/A latency difference min',-36.6,min(vs),src,'100*min(relative_mean_latency_B_minus_A)',.05)
    extra('Streaming A/A latency difference max',739.4,max(vs),src,'100*max(relative_mean_latency_B_minus_A)',.05)
    src='records/historical_summaries/icde_evidence_closure_003/E4/streaming_window_sweep.csv'
    extra('Streaming working points',864,len(rows(src)),src,'number of recorded rows; NOT independent samples')
    src='records/022_plot_data/capacity_plot.csv';rr=rows(src)
    extra('Capacity intervals',24,len(rr),src,'number of model/domain cells')
    extra('Capacity positive lower bounds',0,sum(float(r['DeltaC_low_pp'])>0 for r in rr),src,'count(DeltaC_low_pp>0)')
    for d,v in [('Finance',3.27),('Industrial',.68)]:extra('LightGBM-QP '+d,v,float(next(r for r in rr if r['domain']==d and r['method']=='LightGBM_QP')['DeltaC_pp']),src,'domain='+d+', method=LightGBM_QP; DeltaC_pp',.005)
    src='records/figure_data/fast_action_severity.csv'
    for d,n in [('Biomedical',29),('Economics',3)]:extra(d+' QP fast harmful queries',n,sum(int(r['count']) for r in rows(src) if r['domain']==d),src,'sum(count); fast actions with r>0.05')
    src='records/021_snapshot/reports/icde_eab_review_strengthening_021/analysis_003/EX3/static_mixture_prospective.csv'
    w=json.loads(next(r['weights'] for r in rows(src) if r['domain']=='HR' and r['Fit_budget']=='0.05'))
    extra('Fit-only BM100 weight',.568,w[1],src,'weights[BM100] at Fit_budget=.05',.0005)
    extra('Fit-only BM25 weight',.432,w[2],src,'weights[BM25] at Fit_budget=.05',.0005)
    with (a.output/'R83_numeric_assertions.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,list(checks[0]));w.writeheader();w.writerows(checks)
    result={'status':'PASS_WITH_DISCLOSED_R83_ERRATUM' if not any(r['status']=='FAIL' for r in checks) else 'FAIL','checks':len(checks),'numeric_failures':[r for r in checks if r['status']=='FAIL'],'acknowledged_definition_errata':2,'raw_data_read':False,'GPU_jobs':0,'new_training':0,'scope':'Specified R83 quantitative assertions, table cells in the separate paper_values stage. Not a claim of independent raw-corpus or hardware reproduction.'}
    (a.output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2));return int(result['status']=='FAIL')
if __name__=='__main__':raise SystemExit(main())
