"""022 independent CPU audit. Reads frozen outcomes, never qrels or model weights.

Reconstructs 021 request cubes and repeats the registered paired bootstrap using
independent envelope and LP implementations. No model fitting or inference.
"""
import argparse, collections, csv, hashlib, itertools, json, math, shutil, zipfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, kron

RUN = 'icde_eab_paper_revision_022'
P = ['Full-Visual', 'BM25-R50', 'BM25-R100', 'BM25']
MODELS = ['Ridge_Q', 'Ridge_QP', 'LightGBM_Q', 'LightGBM_QP']
METHODS = P + MODELS + ['FitFrozenMix_0.05']
CAT = [0, 2, 3]
SEED, B = 20261105, 2000
ap = argparse.ArgumentParser()
ap.add_argument('--root', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args()
ROOT, OUT = args.root, args.out
OUT.mkdir(parents=True, exist_ok=False)
A = 'artifacts/icde_eab_review_strengthening_021/'
R = 'reports/icde_eab_review_strengthening_021/'
checks, deltas, provenance, inputs, ledger, points, curves = [], [], [], {}, [], [], []

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):
    p = ROOT / rel
    inputs[rel] = dict(bytes=p.stat().st_size, sha256=sha(p))
    if p.suffix == '.json': return json.loads(p.read_text())
    if p.suffix == '.npz': return dict(np.load(p, allow_pickle=True))
    if p.suffix == '.jsonl': return [json.loads(s) for s in p.read_text().splitlines()]
    return list(csv.DictReader(p.open(newline='', encoding='utf-8-sig')))
def table(name, rows):
    rows = list(rows)
    keys = list(dict.fromkeys(k for r in rows for k in r)) if rows else ['status']
    with (OUT/name).open('x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
def q(x): return np.quantile(x, [.025, .975])
def compare(key, actual, expected, tol=1e-8):
    av, ev = np.asarray(actual, float), np.asarray(expected, float)
    assert av.shape == ev.shape, (key, av.shape, ev.shape)
    err = float(np.max(np.abs(av-ev))) if av.size else 0
    ok = bool(np.all(np.isfinite(av)) and np.all(np.isfinite(ev)) and err <= tol)
    row = dict(key=key, n_values=av.size, max_abs_delta=err, tolerance=tol, status='PASS' if ok else 'FAIL')
    checks.append(row)
    if not ok: deltas.append(dict(**row, recomputed=av.tolist(), registered=ev.tolist()))
    return ok
def invariant(key, ok, detail=''):
    row = dict(key=key, n_values=1, max_abs_delta=0 if ok else 1, tolerance=0, status='PASS' if ok else 'FAIL', detail=detail)
    checks.append(row)
    if not ok: deltas.append(row)

# Independent pair-enumeration of the 1-constraint static mixture LP.
def envelope(r, c, budget):
    r, c = np.atleast_2d(r), np.atleast_2d(c)
    budget = np.broadcast_to(budget, (len(r),))
    candidates = [np.where(r[:, j] <= budget+1e-12, c[:, j], np.inf) for j in range(r.shape[1])]
    for j, k in itertools.combinations(range(r.shape[1]), 2):
        d = r[:, k]-r[:, j]
        z = np.divide(budget-r[:, j], d, out=np.zeros(len(r)), where=np.abs(d)>1e-12)
        candidates.append(np.where((abs(d)>1e-12)&(z>=0)&(z<=1), (1-z)*c[:, j]+z*c[:, k], np.inf))
    return np.min(candidates, axis=0)
def oracle(y, t, budget):
    n, m = y.shape
    z = linprog(t.flatten()/n, A_ub=csr_matrix(y.flatten()[None, :]/n), b_ub=[budget+1e-12],
        A_eq=kron(eye(n), np.ones((1, m)), format='csr'), b_eq=np.ones(n), bounds=(0, 1), method='highs')
    assert z.success, z.message
    return float(z.fun)
def sample_indices(groups, seed, interleaved=False):
    g, rng = np.unique(groups), np.random.default_rng(seed)
    ix, processes = [], []
    for _ in range(B):
        ix.append(np.concatenate([np.flatnonzero(groups == h) for h in rng.choice(g, len(g), replace=True)]))
        if interleaved: processes.append(rng.integers(0, 3, 3))
    if not interleaved: processes = np.random.default_rng(seed).integers(0, 3, (B, 3))
    return ix, processes

manifest=json.loads((Path(__file__).resolve().parents[1]/'records/021_snapshot_manifest.json').read_text())
archive_files=0
for rel,expected in manifest['files'].items():
    invariant('PUBLIC_SANITIZED_INPUT/'+rel,sha(ROOT/rel)==expected['sha256'])
    archive_files+=1
metadata = read(A+'EX0/domains.json')
allocations = read(A+'EX1/predictions_and_allocations.json')
preanalysis = read(A+'EX1/preanalysis.json')
mixtures = read(A+'EX3/frozen_mixtures.json')
fit = read(A+'EX0/fit.npz')
cpu = read(R+'EX0/fresh_CPU_feature_timings.csv')
inference = read(R+'EX1/CPU_inference_raw.csv')
registered = {}
for stage, name in [('EX1','router_capacity_results'), ('EX1','capacity_paired_contrasts'), ('EX1','actual_per_query'),
                    ('EX1','false_safe_cases'), ('EX2','information_value_decomposition'), ('EX2','feature_ablation'), ('EX3','static_mixture_prospective')]:
    registered[name] = read(R+f'analysis_003/{stage}/{name}.csv')
raw = read(A+'GPU/process_03/partial.jsonl')
for p in (6,8,9):
    complete = read(A+f'GPU/process_{p:02d}/completed.json')
    invariant(f'process{p}_complete', complete['status']=='PASS_MATCHED_RESIDENT_PATHS')
    raw.extend(read(A+f'GPU/process_{p:02d}/requests.csv'))
invariant('raw_request_count', len(raw)==30942)
index = collections.defaultdict(list)
for row in raw:
    index[row['domain'], int(row['query_id']), int(row['process']), row['method']].append(row)
new_results, new_decomp, new_mix, new_contrasts, new_ablation, new_pq, new_failures = [], [], [], [], [], [], []
bootstrap_points = []
domains = {}
for di, meta in enumerate(metadata):
    name = meta['domain']; ds = read(A+'EX0/'+name+'.npz'); domains[name] = ds
    ids, groups = ds['qids'].astype(int), ds['groups']; n = len(ids)
    cube = np.empty((n, 3, len(METHODS), 5))  # seconds, CPU seconds, risk, nDCG, intrinsic
    actions = np.empty((n, len(METHODS)), int)
    for i, qid in enumerate(ids):
        for pi, proc in enumerate((6,8,9) if name=='Economics' else (3,8,9)):
            for j, method in enumerate(METHODS):
                rr = index[name, int(qid), proc, method]
                invariant(f'block/{name}/{qid}/{proc}/{method}', len(rr)==3 and sorted(int(r['repeat']) for r in rr)==[0,1,2])
                acts = {r['action'] for r in rr}; assert len(acts)==1
                action = P.index(acts.pop()); actions[i,j] = action
                for row in rr:
                    invariant(f'ranking/{name}/{qid}/{proc}/{method}/{row["repeat"]}', row['ranking']==index[name,int(qid),proc,row['action']][0]['ranking'])
                cube[i,pi,j] = [np.mean([float(r['E2E_s']) for r in rr]), np.mean([float(r['CPU_s']) for r in rr]),
                    ds['Y'][i,0,action], ds['U'][i,0,action], np.mean([float(r['selected_path_s'])+
                    (float(r['BM_search_s']) if str(r['probe_reused']).lower()=='true' else 0) for r in rr])]
    t, cp, y, u, intrinsic = (cube[:,:,:,k] for k in range(5))
    compare(name+'/frozen_static_r', y[:,:,:4], ds['Y'][:,:,:4], 1e-12)
    invariant(name+'/risk_bounds', np.all((y>=0)&(y<=1)) and np.all(y[:,:,0]==0))
    ix, procs = sample_indices(groups, SEED+di)
    boot = np.array([cube[ii][:,pp].mean((0,1)) for ii,pp in zip(ix, procs)])
    bt, by, bi = boot[:,:,0], boot[:,:,2], boot[:,:,4]
    mr, mt = y.mean((0,1)), t.mean((0,1))
    full = mt[0]
    for model in MODELS+['Ridge_Q_distribution','Ridge_Q_gaps','Ridge_Q_coverage']:
        pr = np.clip(np.asarray(allocations[name][model]['prediction']), 0, None)
        recomputed = np.array(CAT)[np.argmin(np.array(meta['cvec'])[CAT]+20*pr, axis=1)]
        compare(name+'/'+model+'/frozen_allocation', recomputed, allocations[name][model]['actions'], 0)
    for j, method in enumerate(METHODS):
        ev = float(envelope(mr[CAT],mt[CAT],mr[j])[0]); eb = envelope(by[:,CAT],bt[:,CAT],by[:,j])
        ev4 = float(envelope(mr[:4],mt[:4],mr[j])[0]); eb4 = envelope(by[:,:4],bt[:,:4],by[:,j])
        # Independent direct LP checks the pair-enumeration point estimates.
        for label, cat, cost in [('3_ACTION',CAT,ev),('4_STATIC',list(range(4)),ev4)]:
            lp = linprog(mt[cat], A_ub=[mr[cat]], b_ub=[mr[j]+1e-12], A_eq=[np.ones(len(cat))], b_eq=[1], bounds=(0,1), method='highs')
            compare(f'{name}/{method}/LP_static_{label}', lp.fun, cost, 2e-10)
        dc = 100*(eb-bt[:,j])/bt[:,0]; dc4 = 100*(eb4-bt[:,j])/bt[:,0]
        rr = [r for r in raw if r['domain']==name and r['method']==method]
        r = y[:,0,j]; mask=(actions[:,j]!=0)&(r>.05)
        row = dict(domain=name,method=method,n=n,groups=len(np.unique(groups)),mean_r=mr[j],
            r_low=q(by[:,j])[0],r_high=q(by[:,j])[1],nDCG10=u[:,:,j].mean(),harm_rate=np.mean(r>1e-10),
            false_safe_rate=mask.mean(),false_safe_risk_mass=r[mask].sum()/max(r.sum(),1e-15),
            E2E_ms=mt[j]*1000,E2E_low_ms=q(bt[:,j]*1000)[0],E2E_high_ms=q(bt[:,j]*1000)[1],
            P50_ms=np.quantile([float(v['E2E_s'])*1000 for v in rr],.5),P95_ms=np.quantile([float(v['E2E_s'])*1000 for v in rr],.95),
            CPU_ms=cp[:,:,j].mean()*1000,DeltaC_pp=100*(ev-mt[j])/full,DeltaC_low_pp=q(dc)[0],DeltaC_high_pp=q(dc)[1],
            four_static_DeltaC_pp=100*(ev4-mt[j])/full,four_static_low_pp=q(dc4)[0],four_static_high_pp=q(dc4)[1],
            envelope_ms=ev*1000,actions=json.dumps(np.bincount(actions[:,j],minlength=4).tolist()),
            C_FullV_same_cohort_ms=full*1000,envelope4_ms=ev4*1000,source_components=27 if name=='Biomedical' else 1 if name=='Economics' else 'NOT_ASSERTED',
            evidence_tier='POSTHOC_EXPLORATORY',plan_catalog='FullV|R100|BM25',cost_scope='ACTUAL_FULL_WARM_PATH_021',
            interval_scope='paired source27/process' if name=='Biomedical' else 'paired family/process; ONE_SOURCE_COMPONENT' if name=='Economics' else 'paired family/process')
        expected = next(z for z in registered['router_capacity_results'] if z['domain']==name and z['method']==method)
        for k in expected:
            if k=='actions': compare(f'{name}/{method}/{k}',json.loads(row[k]),json.loads(expected[k]),0)
            elif k in row and k not in ('domain','method'): compare(f'{name}/{method}/{k}',row[k],expected[k])
        new_results.append(row)
        ov = oracle(y[:,:,:4].mean(1)[:,CAT],t[:,:,:4].mean(1)[:,CAT],mr[j])
        selected = t[np.arange(n)[:,None],np.arange(3)[None,:],actions[:,j,None]]
        H, S, O = 100*(ev-ov)/full,100*(selected.mean()-ov)/full,100*(mt[j]-selected.mean())/full
        de = dict(domain=name,method=method,risk=mr[j],oracle_headroom_pp=H,selector_loss_pp=S,
            realized_minus_standalone_execution_pp=O,measured_extra_and_residual_ms=(t[:,:,j]-intrinsic[:,:,j]).mean()*1000,
            zero_signal_intrinsic_ms=intrinsic[:,:,j].mean()*1000,actual_E2E_ms=mt[j]*1000,
            zero_signal_DeltaC_pp=100*(ev-intrinsic[:,:,j].mean())/full,
            zero_signal_low_pp=q(100*(eb-bi[:,j])/bt[:,0])[0],zero_signal_high_pp=q(100*(eb-bi[:,j])/bt[:,0])[1],
            C_env3_ms=ev*1000,C_oracle3_ms=ov*1000,C_selected_static_ms=selected.mean()*1000,
            C_FullV_same_cohort_ms=full*1000,DeltaC_pp=row['DeltaC_pp'],identity_residual_pp=H-S-O-row['DeltaC_pp'],
            O_definition='SIGNED_ROUTED_MINUS_QUERY_MATCHED_STANDALONE; NOT_PURE_PROBE_COST')
        compare(name+'/'+method+'/H_minus_S_minus_O',H-S-O,row['DeltaC_pp'],1e-10)
        expected = next(z for z in registered['information_value_decomposition'] if z['domain']==name and z['method']==method)
        for k in expected:
            if k in de and k not in ('domain','method'): compare(f'EX2/{name}/{method}/{k}',de[k],expected[k])
        new_decomp.append(de)
        for i,qid in enumerate(ids):
            pq=dict(domain=name,query_id=int(qid),group=str(groups[i]),method=method,action=P[actions[i,j]],r=y[i,0,j],nDCG10=u[i,0,j],
                E2E_ms=t[i,:,j].mean()*1000,intrinsic_ms=intrinsic[i,:,j].mean()*1000,other_ms=(t[i,:,j]-intrinsic[i,:,j]).mean()*1000)
            old=next(v for v in registered['actual_per_query'] if v['domain']==name and int(v['query_id'])==qid and v['method']==method)
            compare(f'perquery/{name}/{qid}/{method}',[pq[k] for k in ['r','nDCG10','E2E_ms','intrinsic_ms','other_ms']],[old[k] for k in ['r','nDCG10','E2E_ms','intrinsic_ms','other_ms']])
            new_pq.append(pq)
    for a,b in [('LightGBM_Q','Ridge_Q'),('LightGBM_QP','Ridge_QP'),('Ridge_QP','Ridge_Q'),('LightGBM_QP','LightGBM_Q')]:
        j,k=METHODS.index(a),METHODS.index(b)
        z=dict(domain=name,contrast=a+' minus '+b,delta_r=mr[j]-mr[k],r_low=q(by[:,j]-by[:,k])[0],r_high=q(by[:,j]-by[:,k])[1],
            delta_ms=(mt[j]-mt[k])*1000,ms_low=q((bt[:,j]-bt[:,k])*1000)[0],ms_high=q((bt[:,j]-bt[:,k])*1000)[1])
        old=next(v for v in registered['capacity_paired_contrasts'] if v['domain']==name and v['contrast']==z['contrast'])
        for key in z:
            if key not in ('domain','contrast'):compare(f'contrast/{name}/{a}/{b}/{key}',z[key],old[key])
        new_contrasts.append(z)
    for mix in mixtures:
        key='FitFrozenMix_'+str(mix['budget']); acts=np.asarray(allocations[name][key]['actions']); w=np.asarray(mix['weights'])
        ua=np.array([int.from_bytes(hashlib.sha256(f'{SEED}:{name}:{qid}:prospective'.encode()).digest()[:8],'big')/2**64 for qid in ids])
        aa=np.array(CAT)[np.minimum(np.searchsorted(np.cumsum(w),ua,side='right'),2)]
        compare(f'EX3/{name}/{key}/allocation_hash_rule',aa,acts,0)
        ay=y[np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]];at=t[np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]]
        compare(f'EX3/Fit81/{key}/risk',fit['Y'][:,:3].mean(0)@w if fit['Y'].shape[1]==3 else fit['Y'].mean(0)[CAT]@w,mix['training_risk'],1e-10)
        z=dict(domain=name,Fit_budget=mix['budget'],weights=json.dumps(w.tolist()),Fit_risk=mix['training_risk'],
            achieved_expected_r=mr[CAT]@w,achieved_replayed_r=ay.mean(),expected_E2E_ms=mt[CAT]@w*1000,
            replayed_component_E2E_ms=at.mean()*1000,actions=json.dumps(np.bincount(acts,minlength=4).tolist()),
            actual_full_path=(key=='FitFrozenMix_0.05'))
        if z['actual_full_path']:z['measured_mixture_path_ms']=mt[-1]*1000
        z['risk_above_fit_budget_expected']=bool(z['achieved_expected_r']>mix['budget']+1e-10)
        old=next(v for v in registered['static_mixture_prospective'] if v['domain']==name and float(v['Fit_budget'])==mix['budget'])
        for k in ['Fit_risk','achieved_expected_r','achieved_replayed_r','expected_E2E_ms','replayed_component_E2E_ms']:compare(f'EX3/{name}/{key}/{k}',z[k],old[k])
        compare(f'EX3/{name}/{key}/weights',w,json.loads(old['weights']),0)
        compare(f'EX3/{name}/{key}/actions',np.bincount(acts,minlength=4),json.loads(old['actions']),0)
        new_mix.append(z)
    for method in ['Ridge_Q_distribution','Ridge_Q_gaps','Ridge_Q_coverage']:
        acts=np.asarray(allocations[name][method]['actions']); ay=y[np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]]
        selected=t[np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]];extra=[]
        for i,qid in enumerate(ids):
            x=next(z for z in cpu if z['domain']==name and int(z['query_id'])==qid)
            it=next(z for z in inference if z['domain']==name and int(z['query_id'])==qid and z['model']==method)
            extra.append(np.mean(json.loads(x['Q_wall_s']))+np.mean(json.loads(x['Pstats_s']))+
                (np.mean(json.loads(x['BM_search_s'])) if acts[i]==0 else 0)+np.mean(json.loads(it['wall_s'])))
        composed=selected+np.array(extra)[:,None];br=np.array([ay[ii][:,pp].mean() for ii,pp in zip(ix,procs)])
        bc=np.array([composed[ii][:,pp].mean() for ii,pp in zip(ix,procs)])
        env=float(envelope(mr[CAT],mt[CAT],ay.mean())[0]);db=100*(envelope(by[:,CAT],bt[:,CAT],br)-bc)/bt[:,0]
        z=dict(domain=name,method=method,mean_r=ay.mean(),composed_E2E_ms=composed.mean()*1000,
            DeltaC_pp=100*(env-composed.mean())/full,low_pp=q(db)[0],high_pp=q(db)[1],mean_extra_ms=np.mean(extra)*1000)
        old=next(v for v in registered['feature_ablation'] if v['domain']==name and v['method']==method)
        for k in z:
            if k not in ('domain','method'):compare(f'ablation/{name}/{method}/{k}',z[k],old[k])
        new_ablation.append(z)
    for j,method in enumerate(MODELS,4):
        for i in np.argsort(-y[:,0,j],kind='stable')[:3]:
            old=next(v for v in registered['false_safe_cases'] if v['domain']==name and v['method']==method and int(v['query_id'])==ids[i])
            compare(f'case/{name}/{method}/{ids[i]}',y[i,0,j],old['regret'])
    print(name, 'raw reconstructed; 2000 paired draws; all registered controls checked', flush=True)

# 016 original frozen-policy metrics are a different cost cohort and model.
D16='reports/icde_eab_figure_verification_016/delivery_003/MDRouter_016_figures/figures/data/'
legacy_points=read(D16+'plan_points.csv')
legacy_contrasts=read(D16+'paired_contrasts.csv')
legacy_fixed=read(D16+'fixed_budget_oracle.csv')
for name in ['Biomedical','Economics']:
    ds=domains[name];t,y,u=ds['T'],ds['Y'],ds['U']; groups=ds['groups']
    seed=202610281101 if name=='Biomedical' else 202610281100
    ix,pr=sample_indices(groups,seed,interleaved=name=='Economics')
    if name=='Biomedical':pr=np.random.default_rng(202610281143).integers(0,3,(B,3))
    bt=np.array([t[ii][:,pp].mean((0,1)) for ii,pp in zip(ix,pr)])*1000
    by=np.array([y[ii][:,pp].mean((0,1)) for ii,pp in zip(ix,pr)])
    for control,j in [('Q',4),('R100',2),('R50',1)]:
        old=next(v for v in legacy_contrasts if v['domain']==name and v['control']==control)
        dr=by[:,5]-by[:,j];dt=bt[:,5]-bt[:,j]
        z=dict(delta_r=(y[:,:,5]-y[:,:,j]).mean(),r_low=q(dr)[0],r_high=q(dr)[1],
               delta_ms=(t[:,:,5]-t[:,:,j]).mean()*1000,ms_low=q(dt)[0],ms_high=q(dt)[1])
        for k in z:compare(f'016/{name}/QPminus{control}/{k}',z[k],old[k],1e-7)
    for j,method in enumerate(['FullV','R50','R100','BM25','Q','QP']):
        old=next(v for v in legacy_points if v['domain']==name and v['model']=='ColQwen2' and v['method']==method)
        for k,val in [('risk',y[:,:,j].mean()),('ndcg',u[:,:,j].mean()),('warm_ms',t[:,:,j].mean()*1000)]:
            compare(f'016/{name}/{method}/{k}',val,old[k],1e-7)

# 017 same-process warm/setup arithmetic. OCR is a fixed historical singleton.
D17='reports/icde_eab_g2_setup_017/'
setup=read(D17+'G2_setup_repeats.csv');warm=read(D17+'G2_same_cohort_warm.csv')
costs=read(D17+'G2_reuse_sensitivity.csv');crossings=read(D17+'G2_break_even_ranges.csv')
read(D17+'final_manifest_001.json')
scenarios={'OCR_EXCLUSIVE_NEW_INDEX':(1,1,False),'OCR_SHARED_HALF_NEW_INDEX':(.5,1,False),'OCR_PREPAID_NEW_INDEX':(0,1,False),
    'EXISTING_INDEX_OCR_NEW':(1,0,False),'EXISTING_INDEX_OCR_PREPAID':(0,0,False),'ALREADY_RESIDENT_ALL_PREPAID':(0,0,True)}
for s in setup:
    for scene,(fraction,index_charge,resident) in scenarios.items():
        base=0 if resident else float(s['base_process_startup_wall_s'])+index_charge*float(s['index_wall_s'])
        extra=0 if resident else float(s['BM25_build_wall_s'])+fraction*407.725
        fw,rw=float(s['warm_FullV_s']),float(s['warm_R100_s'])
        for plan,k in [('Full-Visual','warm_FullV_s'),('BM25-R100','warm_R100_s')]:
            wr=next(v for v in warm if v['model']==s['model'] and v['repeat']==s['repeat'] and v['plan']==plan)
            compare(f'017/{s["model"]}/{s["repeat"]}/{plan}/same_cohort_warm',s[k],wr['warm_E2E_s'],1e-12)
        cr=next(v for v in crossings if v['model']==s['model'] and v['repeat']==s['repeat'] and v['scenario']==scene)
        compare(f'017/{s["model"]}/{s["repeat"]}/{scene}/crossing',math.ceil(extra/(fw-rw)),cr['conditional_break_even_N'],0)
        for c in (v for v in costs if v['model']==s['model'] and v['repeat']==s['repeat'] and v['scenario']==scene):
            n=int(c['N']);ft,rt=base+n*fw,base+extra+n*rw
            z=dict(FullV_setup_s=base,R100_setup_s=base+extra,FullV_total_wall_s=ft,R100_total_wall_s=rt,
                R100_over_FullV_ratio=rt/ft,R100_minus_FullV_wall_s=rt-ft,OCR_charge_once_s=fraction*407.725 if not resident else 0)
            for k in z:compare(f'017/{s["model"]}/{s["repeat"]}/{scene}/N{n}/{k}',z[k],c[k],1e-9)

# Every figure input is emitted by this audit, using one explicit metrics version.
metrics_version='022.metrics.v1.'+hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()[:12]
for name,rows in [('capacity_verified.csv',new_results),('decomposition_verified.csv',new_decomp),('fit_mixture_verified.csv',new_mix),
    ('paired_contrasts_verified.csv',new_contrasts),('feature_ablation_verified.csv',new_ablation),('per_query_verified.csv',new_pq)]:
    for row in rows:row['metrics_version']=metrics_version
    table(name,rows)
table('legacy016_points.csv',legacy_points);table('legacy016_paired_contrasts.csv',legacy_contrasts)
table('legacy016_catalog_control.csv',legacy_fixed)
table('setup017_verified.csv',setup);table('warm017_verified.csv',warm)
table('lifecycle017_verified.csv',costs);table('crossings017_verified.csv',crossings)
table('verification_checks.csv',checks);table('numeric_delta.csv',deltas);table('provenance_delta.csv',provenance)
(OUT/'input_inventory.json').write_text(json.dumps(inputs,indent=2)+'\n')
summary=dict(run_id=RUN,actual_time_bj=datetime.now(timezone(timedelta(hours=8))).isoformat(),metrics_version=metrics_version,
    status='PASS_NUMERIC_REPLAY' if not deltas else 'FAIL_NUMERIC_MISMATCH',numeric_failures=len(deltas),
    checks=len(checks),numeric_values=sum(r['n_values'] for r in checks),archive_files_verified=archive_files,
    loose_operational_log_drifts=len(provenance),raw_requests=len(raw),distinct_queries=382,independent_IID_queries='NOT_ESTABLISHED',
    per_domain_queries={m['domain']:m['n'] for m in metadata},new_effect_experiments=0,model_fits=0,GPU_jobs=0,
    sealed_label_reads=0,bootstrap_draws=B,bootstrap_seed=SEED,positive_lower_CI_capacity_controls=int(sum(z['DeltaC_low_pp']>0 for z in new_results if z['method'] in MODELS)),
    paper_modified=False,github_pushes=0,CMT_submissions=0,fit_label_budget=81,
    source_021_code_commit=manifest['private_code_commit'],scope='AUTHOR_REVIEW_CANDIDATE; NO_MANUSCRIPT_TEXT')
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
if deltas:raise SystemExit('Numeric differences found; block downstream candidate generation')
