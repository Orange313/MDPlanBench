"""Archive-only regression gates; no new policy selection or fitting.

Writes exclusively below a fresh output directory. Sealed annotations, model
weights, pages, images, embeddings and query text are never opened.
"""
from pathlib import Path
import argparse,collections,csv,hashlib,importlib.util,json,sys
from datetime import datetime,timezone,timedelta
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix,eye,kron

ap=argparse.ArgumentParser()
ap.add_argument('--project',type=Path,required=True)
ap.add_argument('--public',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
A=R/'artifacts/icde_eab_review_strengthening_021'
REPORT=R/'reports/icde_eab_review_strengthening_021/analysis_003'
PLANS=['Full-Visual','BM25-R50','BM25-R100','BM25']
MODELS=['Ridge_Q','Ridge_QP','LightGBM_Q','LightGBM_QP']
METHODS=PLANS+MODELS+['FitFrozenMix_0.05'];CAT=[0,2,3];B=2000
INPUTS={}
def read(p):
    p=Path(p);data=p.read_bytes()
    INPUTS[str(p)]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if p.suffix=='.json':return json.loads(data)
    if p.suffix=='.jsonl':return [json.loads(s) for s in data.decode().splitlines()]
    if p.suffix=='.npz':return dict(np.load(p,allow_pickle=False))
    return list(csv.DictReader(data.decode('utf-8-sig').splitlines()))
def write(name,rows):
    keys=list(dict.fromkeys(k for z in rows for k in z))
    with (O/name).open('x',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def save_json(name,x):
    with (O/name).open('x',encoding='utf8') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

# Use the original envelope implementation for the exact accounting regression.
fpath=R/'scripts/icde_eab_validation_005/frontier_math.py'
read(fpath)
sp=importlib.util.spec_from_file_location('archived_frontier',fpath)
F=importlib.util.module_from_spec(sp);sp.loader.exec_module(F)
def oracle(y,t,budget):
    n,m=y.shape
    z=linprog(t.ravel()/n,A_ub=csr_matrix(y.ravel()[None,:]/n),b_ub=[budget+1e-12],
        A_eq=kron(eye(n),np.ones((1,m)),format='csr'),b_eq=np.ones(n),bounds=(0,1),method='highs')
    assert z.success,z.message
    return z.fun
def indices(groups,seed,interleaved=False,process_seed=None):
    u=np.unique(groups);rng=np.random.default_rng(seed);ix=[];process=[]
    for _ in range(B):
        ix.append(np.concatenate([np.flatnonzero(groups==h) for h in rng.choice(u,len(u),replace=True)]))
        if interleaved:process.append(rng.integers(0,3,3))
    if not interleaved:process=np.random.default_rng(seed if process_seed is None else process_seed).integers(0,3,(B,3))
    return ix,np.asarray(process)
def save_draws(name,ids,groups,ix,proc,draws,methods,seed,scope):
    offsets=np.r_[0,np.cumsum([len(z) for z in ix])]
    np.savez_compressed(O/(name+'_bootstrap.npz'),query_ids=ids,groups=groups,
        offsets=offsets,query_row_indices=np.concatenate(ix).astype(np.int32),
        process_indices=proc.astype(np.int16),deltaC_pp=np.asarray(draws),methods=np.asarray(methods))
    write(name+'_draws.csv',[dict(replicate=b,method=m,DeltaC_pp=float(draws[b,j]),
        seed=seed,scope=scope) for b in range(B) for j,m in enumerate(methods)])

metadata=read(A/'EX0/domains.json');alloc=read(A/'EX1/predictions_and_allocations.json')
expected=read(REPORT/'EX1/router_capacity_results.csv')
decomp=read(REPORT/'EX2/information_value_decomposition.csv')
oldpoints=read(a.public/'records/figure_data/plot_points_registered.csv')
raw=read(A/'GPU/process_03/partial.jsonl')
for process in [6,8,9]:
    completed=read(A/f'GPU/process_{process:02d}/completed.json')
    assert completed['status']=='PASS_MATCHED_RESIDENT_PATHS'
    raw.extend(read(A/f'GPU/process_{process:02d}/requests.csv'))
assert len(raw)==30942
lut=collections.defaultdict(list)
for z in raw:lut[z['domain'],int(z['query_id']),int(z['process']),z['method']].append(z)

regression=[];ci_checks=[];allocation_checks=[];draw_inventory=[]
for di,d in enumerate(metadata):
    name=d['domain'];ds=read(A/f'EX0/{name}.npz');ids=ds['qids'].astype(int);groups=ds['groups'];n=len(ids)
    t=np.full((n,3,len(METHODS)),np.nan);y=t.copy();actions=np.zeros((n,len(METHODS)),int)
    for i,q in enumerate(ids):
        for pi,process in enumerate([6,8,9] if name=='Economics' else [3,8,9]):
            for j,m in enumerate(METHODS):
                rr=lut[name,int(q),process,m]
                assert len(rr)==3 and sorted(int(z['repeat']) for z in rr)==[0,1,2]
                act={z['action'] for z in rr};assert len(act)==1
                action=PLANS.index(next(iter(act)));actions[i,j]=action
                t[i,pi,j]=np.mean([float(z['E2E_s']) for z in rr])
                y[i,pi,j]=ds['Y'][i,0,action]
    for m in MODELS:
        pr=np.maximum(np.asarray(alloc[name][m]['prediction']),0)
        costs=np.asarray(d['cvec'])[CAT];costs=costs/costs[0]
        acts=np.asarray(CAT)[np.argmin(costs+20*pr,axis=1)]
        allocation_checks.append(dict(domain=name,method=m,identical=bool(np.array_equal(acts,alloc[name][m]['actions']))))
    sr=y[:,:,:4].mean((0,1));st=t[:,:,:4].mean((0,1));full=t[:,:,0].mean()
    for j,m in enumerate(METHODS):
        if m not in MODELS:continue
        erow=next(z for z in expected if z['domain']==name and z['method']==m)
        dr=next(z for z in decomp if z['domain']==name and z['method']==m)
        risk=y[:,:,j].mean();env=F.envelope(sr[CAT],st[CAT],risk)[0][0]
        opt=oracle(y[:,:,:4].mean(1)[:,CAT],t[:,:,:4].mean(1)[:,CAT],risk)
        chosen=t[:,:,:4][np.arange(n)[:,None],np.arange(3)[None,:],actions[:,j,None]]
        vals={'oracle_headroom_pp':100*(env-opt)/full,'selector_loss_pp':100*(chosen.mean()-opt)/full,
              'realized_minus_standalone_execution_pp':100*(t[:,:,j].mean()-chosen.mean())/full,
              'DeltaC_pp':100*(env-t[:,:,j].mean())/full}
        for k,value in vals.items():
            target=float(erow[k] if k=='DeltaC_pp' else dr[k])
            regression.append(dict(domain=name,method=m,metric=k,archived=repr(target),reproduced=repr(float(value)),
                delta_pp=float(value)-target,exact_float_equal=bool(value==target),
                displayed_2dp_equal=format(value,'.2f')==format(target,'.2f'),
                scope='ARCHIVED_KAPPA20_REGRESSION_ONLY; not a new recomposed policy'))
    ix,proc=indices(groups,20261105+di)
    bt=np.asarray([t[ii][:,pp].mean((0,1)) for ii,pp in zip(ix,proc)])
    by=np.asarray([y[ii][:,pp].mean((0,1)) for ii,pp in zip(ix,proc)])
    draws=[]
    for m in MODELS:
        j=METHODS.index(m);env=F.envelope(by[:,CAT],bt[:,CAT],by[:,j])[0]
        delta=100*(env-bt[:,j])/bt[:,0];draws.append(delta)
        ref=next(z for z in expected if z['domain']==name and z['method']==m)
        for side,v in zip(['low','high'],np.quantile(delta,[.025,.975])):
            target=float(ref['DeltaC_'+side+'_pp'])
            ci_checks.append(dict(cohort='POSTHOC_021',domain=name,method=m,side=side,archived=target,reproduced=float(v),
                error_pp=float(v)-target,PASS=bool(abs(v-target)<=.01),seed=20261105+di,denominator='resampled FullV'))
    save_draws(name+'_021',ids,groups,ix,proc,np.stack(draws,axis=1),MODELS,20261105+di,'ARCHIVED_POINTWISE_CI_REPRODUCTION')
    # Original Q/QP policy intervals use a separate old timing cube and four-static comparator.
    oldt,oldy=ds['T'],ds['Y']
    seed=202610272130+di if di<4 else 202610281101 if name=='Biomedical' else 202610281100
    ix,proc=indices(groups,seed,interleaved=name=='Economics',process_seed=202610281143 if name=='Biomedical' else None)
    bt=np.asarray([oldt[ii][:,pp].mean((0,1)) for ii,pp in zip(ix,proc)])
    by=np.asarray([oldy[ii][:,pp].mean((0,1)) for ii,pp in zip(ix,proc)])
    olddraws=[]
    for j,m in [(4,'Q'),(5,'QP')]:
        env=F.envelope(by[:,:4],bt[:,:4],by[:,j])[0]
        denominator=oldt[:,:,0].mean() if name=='Economics' else bt[:,0]
        delta=100*(env-bt[:,j])/denominator;olddraws.append(delta)
        ref=next(z for z in oldpoints if z['domain']==name and z['model']=='ColQwen2' and z['method']==m)
        for side,v in zip(['low','high'],np.quantile(delta,[.025,.975])):
            target=float(ref['gain_'+side])
            ci_checks.append(dict(cohort='ORIGINAL_FROZEN',domain=name,method=m,side=side,archived=target,reproduced=float(v),
                error_pp=float(v)-target,PASS=bool(abs(v-target)<=.01),seed=seed,
                denominator='fixed original FullV mean' if name=='Economics' else 'resampled FullV'))
    save_draws(name+'_original',ids,groups,ix,proc,np.stack(olddraws,axis=1),['Q','QP'],seed,'ARCHIVED_POINTWISE_CI_REPRODUCTION')
    print(name,'archive regression and bootstrap exports completed',flush=True)

write('kappa20_regression.csv',regression);write('interval_endpoint_gate.csv',ci_checks)
write('allocation_gate.csv',allocation_checks);save_json('input_hashes.json',INPUTS)
summary=dict(time_beijing=datetime.now(timezone(timedelta(hours=8))).isoformat(),
    scope='Regression only; no new screening configurations or model fitting',
    kappa20_exact_float_gate=all(z['exact_float_equal'] for z in regression),
    kappa20_displayed_2dp_gate=all(z['displayed_2dp_equal'] for z in regression),
    kappa20_allocation_gate=all(z['identical'] for z in allocation_checks),
    endpoint_gate=all(z['PASS'] for z in ci_checks),endpoint_checks=len(ci_checks),
    max_endpoint_error_pp=max(abs(z['error_pp']) for z in ci_checks),
    strict_stop=not(all(z['exact_float_equal'] for z in regression) and all(z['PASS'] for z in ci_checks)),
    original_order_status='PENDING_ORIGINAL_ORDER',new_effects_computed=False,
    bootstrap_repeats=B,bootstrap_index_and_draw_exports=12,GPU_jobs=0,new_models_trained=0,sealed_label_reads=0)
save_json('gate_summary.json',summary)
print(json.dumps(summary,indent=2),flush=True)
