"""Offline replay from public numerical snapshots and this branch's small inputs.

Does not repeat OCR/GPU measurements, load weights, or open original qrels.
"""
from pathlib import Path
import argparse,csv,hashlib,json,os,subprocess,sys,time
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--statistical-only',action='store_true')
a=ap.parse_args();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
S=Path(__file__).resolve().parent;G=S.parent;P=G/'records/021_snapshot';start=time.perf_counter();checks=[]
def run(label,script,*args):
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1';env['MPLCONFIGDIR']=str(O/'mpl_cache')
    cmd=[sys.executable,str(S/script),*map(str,args)]
    with (O/(label+'.log')).open('x',encoding='utf8') as f:
        code=subprocess.run(cmd,cwd=G,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
    if code:raise RuntimeError(f'{label} failed; saved log, no expected values changed')
def same(expected,actual):
    assert expected.exists(),expected
    if expected.suffix=='.npz':
        with np.load(expected,allow_pickle=False) as x,np.load(actual,allow_pickle=False) as y:
            ok=set(x.files)==set(y.files) and all(np.array_equal(x[k],y[k],equal_nan=True) if x[k].dtype.kind in 'fc' else np.array_equal(x[k],y[k]) for k in x.files)
    else:ok=expected.read_bytes()==actual.read_bytes()
    checks.append(dict(file=str(expected.relative_to(G)),PASS=bool(ok)))
    assert ok,expected.name
run('archive_gate','regression_gates.py','--project',P,'--public',G,'--out',O/'gates')
for p in (S/'gates_001').iterdir():
    if p.suffix in ['.csv','.npz']:same(p,O/'gates'/p.name)
run('cross_fit','run_screening.py','--project',P,'--out',O/'screening')
for p in (S/'screening_001').iterdir():
    if p.suffix in ['.csv','.npz']:same(p,O/'screening'/p.name)
run('independent','independent_cpu.py','--project',P,'--out',O/'independent','--gates',O/'gates','--k17-input',S/'portable_inputs_001/K17_inputs.json')
for name in ['E3_intervals_36.csv','E3_upper_bound_counts.csv','K17_kappa10_vs20.csv','K17_original_reproduction.csv',
             'K17_subset_membership.csv','E4_coarse_hull.csv']:
    same(S/'independent_001'/name,O/'independent'/name)
for p in (S/'independent_001').glob('*_E4_draws.npz'):same(p,O/'independent'/p.name)
extra=[]
try:
    checkout_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True,stderr=subprocess.DEVNULL).strip()
    checkout_clean=not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
except subprocess.CalledProcessError:
    checkout_commit=None;checkout_clean=None
if not a.statistical_only:
    meta=S/'portable_inputs_001/E5_metadata'
    ref=json.loads((S/'portable_inputs_001/reference_OCR_hashes.json').read_text())
    observations=0
    for p in meta.glob('*_page_timings.json'):
        data=json.loads(p.read_text());assert len(data)==1016
        for z in data:assert z['sha256']==ref[str(z['corpus_id'])];observations+=1
    assert observations==15*1016
    extra.append(dict(check='Archived OCR fingerprint consistency',observations=observations,PASS=True,fresh_OCR_executed=False))
    run('ocr_lifecycle','ocr_crossings.py','--project',P,'--out',O/'E5_analysis','--ocr-input',meta,'--setup-input',S/'portable_inputs_001/setup017')
    for name in ['E5_worker_timings.csv','E5_same_process_components.csv','E5_all_crossings.csv','E5_crossing_ranges.csv']:
        same(S/'E5_analysis_001'/name,O/'E5_analysis'/name)
    def rows(p):
        with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    pq=rows(S/'E7_HR_001/E7_per_query.csv');summ=rows(S/'E7_HR_001/E7_summary.csv')
    for z in pq:
        r=max(float(z['reference_nDCG10'])-float(z['nDCG10']),0)
        assert abs(r-float(z['r']))<1e-12
        assert (r>1e-10)==(z['harm']=='True')
    for z in summ:
        part=[x for x in pq if x['plan']==z['plan'] and x['text_source']==z['text_source']]
        assert len(part)==int(z['queries'])
        for key,col in [('mean_r','r'),('mean_nDCG10','nDCG10')]:assert abs(np.mean([float(x[col]) for x in part])-float(z[key]))<1e-12
        assert abs(np.mean([x['harm']=='True' for x in part])-float(z['harm_rate']))<1e-12
    extra.append(dict(check='HR reported quality aggregates and positive-regret identity',PASS=True,fresh_OCR_or_qrels_read=False))
    run('HR_reference_gate','verify_E7_reference.py','--project',P,'--E7-input',S/'E7_HR_001','--out',O/'E7_reference_gate')
    same(S/'E7_reference_gate_001/E7_official_reference_gate.csv',O/'E7_reference_gate/E7_official_reference_gate.csv')
    assets=rows(S/'E8_storage_001/E8_assets.csv');files=rows(S/'E8_storage_001/E8_visual_files.csv')
    existing=[z for z in assets if z['status']!='MISSING_NOT_BUILT'];assert len(existing)==11
    for z in existing:
        rr=[x for x in files if x['domain']==z['domain'] and x['model']==z['model']]
        assert sum(int(x['logical_bytes']) for x in rr)==round(float(z['visual_logical_MB'])*1e6)
        payload=round(int(z['pages'])*float(z['mean_stored_vectors_per_page'])*int(z['dimension'])*2)
        assert payload==round(float(z['tensor_payload_MB'])*1e6)
        assert z['persisted_BM25_index_MB']=='' and z['visual_over_BM25_ratio']==''
    extra.append(dict(check='Archived storage inventory arithmetic',cells=11,PASS=True,fresh_assets_opened=False))
    run('review_figures','render_results.py','--out',O/'review_figures','--code-commit',checkout_commit or 'NOT_A_GIT_CHECKOUT')
    for name in ['E2_main_crossfit','E2_budget_grid','E1_envelope_bias','E7_text_source']:
        same(S/'review_002'/(name+'.png'),O/'review_figures'/(name+'.png'))
    for name in ['E5_parallelism','E5_crossings']:same(S/'E5_analysis_001'/(name+'.png'),O/'E5_analysis'/(name+'.png'))
    same(S/'independent_001/K17_learning.png',O/'independent/K17_learning.png')
    extra.append(dict(check='Seven review figures reconstructed and PNG bytes matched',PASS=True,
        PDF_regenerated=True,PDF_bytes_not_compared='Creation timestamps may differ; underlying CSV and PNG checked'))
receipt=dict(status='PASS_STATISTICAL_REPLAY' if a.statistical_only else 'PASS_CPU_POSTHOC_REPLAY',
    wall_s=time.perf_counter()-start,checked_files=len(checks),checks=checks,extra_checks=extra,
    checkout_commit=checkout_commit,checkout_clean=checkout_clean,
    executed_code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in S.glob('*.py')},
    GPU_jobs=0,new_models_trained=0,sealed_labels_read=0,fresh_system_measurements=False,
    limitations=['This is offline reconstruction of numerical records, not fresh OCR/GPU benchmarking.',
      'Economics intervals are conditional on one source component.',
      'New accounting costs retain signed execution-context transfer and may be negative per query.'])
(O/'replay_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['checks']},indent=2),flush=True)
