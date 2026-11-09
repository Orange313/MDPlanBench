"""E1/E2 conditional cross-fit screening, under the committed author plan."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix,eye,kron
import accounting as C

ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();O=a.out;O.mkdir(parents=True,exist_ok=False);D=C.all_data(a.project)
refs=C.read(a.project/'reports/icde_eab_review_strengthening_021/analysis_003/EX1/router_capacity_results.csv')
decomp=C.read(a.project/'reports/icde_eab_review_strengthening_021/analysis_003/EX2/information_value_decomposition.csv')
frontier_path=a.project/'scripts/icde_eab_validation_005/frontier_math.py'
if not frontier_path.exists():frontier_path=Path(__file__).resolve().parents[1]/'repro/frontier_math.py'
sp=importlib.util.spec_from_file_location('original_frontier',frontier_path)
F=importlib.util.module_from_spec(sp);sp.loader.exec_module(F)
reg=[];adapter=[]
for name,d in D.items():
    n=len(d['ids']);st=d['static'];r=d['risk'];full=st[:,:,0].mean()
    # Preserve the archived tensor layout and reduction order for exact replay.
    archived_y=np.empty_like(d['t'])
    for jj in range(len(C.METHODS)):
        archived_y[:,:,jj]=r[np.arange(n),d['acts'][:,jj]][:,None]
    static_r=archived_y[:,:,:4].mean((0,1));static_t=st.mean((0,1))
    for method in C.MODELS:
        acts=C.kappa_actions(d,method,20);j=C.METHODS.index(method);t=C.chosen_cost(d,method,acts)
        adapter.append(dict(domain=name,method=method,actions_equal=bool(np.array_equal(acts,d['acts'][:,j])),
            costs_equal=bool(np.array_equal(t,d['t'][:,:,j]))))
        selected=st[np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]]
        risk=archived_y[:,:,j].mean();ev=F.envelope(static_r[C.CAT],static_t[C.CAT],risk)[0][0]
        yy=archived_y[:,:,:4].mean(1)[:,C.CAT];tt=st.mean(1)[:,C.CAT]
        lp=linprog(tt.ravel()/n,A_ub=csr_matrix(yy.ravel()[None,:]/n),b_ub=[risk+1e-12],
            A_eq=kron(eye(n),np.ones((1,3)),format='csr'),b_eq=np.ones(n),bounds=(0,1),method='highs')
        assert lp.success
        values={'oracle_headroom_pp':100*(ev-lp.fun)/full,'selector_loss_pp':100*(selected.mean()-lp.fun)/full,
            'realized_minus_standalone_execution_pp':100*(t.mean()-selected.mean())/full,'DeltaC_pp':100*(ev-t.mean())/full}
        ref=next(z for z in refs if z['domain']==name and z['method']==method)
        dec=next(z for z in decomp if z['domain']==name and z['method']==method)
        for k,v in values.items():
            ex=float(ref[k] if k=='DeltaC_pp' else dec[k])
            reg.append(dict(domain=name,method=method,metric=k,expected=repr(ex),reproduced=repr(float(v)),
                exact_equal=bool(v==ex),delta_pp=float(v)-ex))
C.csvsave(O/'kappa20_adapter_gate.csv',reg);C.csvsave(O/'kappa20_array_gate.csv',adapter)
passed=all(z['exact_equal'] for z in reg) and all(z['actions_equal'] and z['costs_equal'] for z in adapter)
C.jsave(O/'gate.json',dict(PASS=passed,entries=len(reg),strict_exact_float=True))
if not passed:raise SystemExit('STOP: arbitrary-action kappa20 regression mismatch; no E1/E2 computed')

def mixture_fit(r,s,fold,cat):
    w=np.empty((len(r),len(C.BUDGETS),len(cat)));fitted=[]
    for k in range(5):
        tr=fold!=k;te=~tr
        for bi,b in enumerate(C.BUDGETS):
            z=C.mix_lp(r[tr][:,cat].mean(0),s[tr][:,:,cat].mean((0,1)),b)
            w[te,bi]=z;fitted.append(dict(fold=k,b=float(b),weights=z.tolist()))
    return w,fitted
def fit_config(d,seed,cat=C.CAT,routers=True):
    r,s=d['risk'],d['static'];fold=C.folds(d['groups'],seed);w,fitmix=mixture_fit(r,s,fold,cat)
    mixr=np.einsum('nba,na->nb',w,r[:,cat]);mixc=np.einsum('nba,npa->npb',w,s[:,:,cat])
    point_h=C.hull(np.r_[mixr.mean(0),0,r[:,3].mean()],np.r_[mixc.mean((0,1)),s[:,:,0].mean(),s[:,:,3].mean()])
    if not routers:return dict(fold=fold,w=w,mixr=mixr,mixc=mixc,hull=point_h,fitmix=fitmix)
    rc=[];rr=[];config=[];choices=[];actions_all=[]
    for method in C.MODELS:
        ka=[C.kappa_actions(d,method,k) for k in C.KAPPAS]
        kr=np.stack([r[np.arange(len(r)),z] for z in ka],axis=1)
        kc=np.stack([C.chosen_cost(d,method,z) for z in ka],axis=2)
        for bi,b in enumerate(C.BUDGETS):
            aa=np.empty(len(r),int)
            for k in range(5):
                tr=fold!=k;te=~tr
                feasible=np.flatnonzero(kr[tr].mean(0)<=b)
                best=min(feasible,key=lambda z:(kc[tr,:,z].mean(),-C.KAPPAS[z]))
                aa[te]=ka[best][te]
                choices.append(dict(domain=d['name'],seed=seed,method=method,b=float(b),fold=k,
                    kappa='inf' if np.isinf(C.KAPPAS[best]) else int(C.KAPPAS[best]),
                    training_r=float(kr[tr,best].mean()),training_cost_ms=float(kc[tr,:,best].mean()*1000)))
            rr.append(r[np.arange(len(r)),aa]);rc.append(C.chosen_cost(d,method,aa));actions_all.append(aa)
            config.append((method,float(b)))
        aa=C.kappa_actions(d,method,20);rr.append(r[np.arange(len(r)),aa]);rc.append(C.chosen_cost(d,method,aa))
        actions_all.append(aa);config.append((method,'frozen20'))
    rr=np.stack(rr,axis=1);rc=np.stack(rc,axis=2);mr=rr.mean(0);mc=rc.mean((0,1));full=s[:,:,0].mean()
    delta=100*(C.evaluate_hull(point_h,mr,r[:,3].mean(),s[:,:,3].mean())-mc)/full
    return dict(fold=fold,w=w,mixr=mixr,mixc=mixc,hull=point_h,fitmix=fitmix,rr=rr,rc=rc,
        config=config,choices=choices,actions=np.stack(actions_all,axis=1),delta=delta)

rows=[];biasrows=[];biaspoints=[];foldrows=[];fitrows=[];perquery=[];sensitivity=[];samples=[];limitations=[]
for name,d in D.items():
    n=len(d['ids']);main=fit_config(d,C.SEED);s=d['static'];r=d['risk'];ix,proc=C.boot_indices(d['groups'])
    C.save_indices(O/(name+'_conditional_indices.npz'),d,ix,proc)
    bc=np.asarray([main['rc'][i][:,p].mean((0,1)) for i,p in zip(ix,proc)])
    br=np.asarray([main['rr'][i].mean(0) for i in ix])
    bmixc=np.asarray([main['mixc'][i][:,p].mean((0,1)) for i,p in zip(ix,proc)])
    bmixr=np.asarray([main['mixr'][i].mean(0) for i in ix])
    bs=np.asarray([s[i][:,p].mean((0,1)) for i,p in zip(ix,proc)])
    by=np.asarray([r[i].mean(0) for i in ix])
    draws=np.empty_like(bc)
    for z in range(C.B):
        h=C.hull(np.r_[bmixr[z],0,by[z,3]],np.r_[bmixc[z],bs[z,0],bs[z,3]])
        draws[z]=100*(C.evaluate_hull(h,br[z],by[z,3],bs[z,3])-bc[z])/bs[z,0]
    np.savez_compressed(O/(name+'_conditional_draws.npz'),DeltaC_cf_pp=draws,
        configs=np.asarray([m+':'+str(b) for m,b in main['config']]))
    stable=[fit_config(d,seed) for seed in [1,2,3,4,5]]
    for seed,z in zip([1,2,3,4,5],stable):
        fitrows.extend(z['choices'])
        for j,(m,b) in enumerate(z['config']):sensitivity.append(dict(domain=name,seed=seed,method=m,b=b,DeltaC_cf_pp=float(z['delta'][j])))
    fitrows.extend(main['choices'])
    for i,q in enumerate(d['ids']):foldrows.append(dict(domain=name,query_id=int(q),group=str(d['groups'][i]),fold=int(main['fold'][i]),seed=C.SEED))
    for j,(method,b) in enumerate(main['config']):
        low,high=np.quantile(draws[:,j],[.025,.975]);sv=[float(z['delta'][j]) for z in stable]
        costs=main['rc'][:,:,j];risk=main['rr'][:,j]
        rows.append(dict(domain=name,method=method,b=b,n=n,OOF_r=float(risk.mean()),OOF_cost_ms=float(costs.mean()*1000),
            cost_pct_FullV=float(100*costs.mean()/s[:,:,0].mean()),DeltaC_cf_pp=float(main['delta'][j]),
            low95_pp=float(low),high95_pp=float(high),stability_min_pp=min(sv),stability_max_pp=max(sv),
            negative_query_process_costs=int((costs<0).sum()),
            interval='conditional on fitted kappa and weights; pointwise95; Economics one-source conditional',cost_scope=C.SCOPE,
            conditional_measurement_eligible=bool(b==.05 and low>0)))
        for i,q in enumerate(d['ids']):perquery.append(dict(domain=name,query_id=int(q),group=str(d['groups'][i]),method=method,b=b,
            action=C.PLANS[main['actions'][i,j]],r=float(risk[i]),cost_ms=float(costs[i].mean()*1000),cost_scope=C.SCOPE))
    # Component transfer audit, never clipped or represented as physical timings.
    for method in C.MODELS:
        j=C.METHODS.index(method);old=d['acts'][:,j]
        selected=s[np.arange(n)[:,None],np.arange(3)[None,:],old[:,None]]
        signal=d['signal'][:,:,j]+(d['bm'][:,:,j]*(old==0)[:,None] if method.endswith('_QP') else 0)
        limitations.append(dict(domain=name,method=method,archived_route_minus_static_ms=float((d['t'][:,:,j]-selected).mean()*1000),
            measured_signal_ms=float(signal.mean()*1000),execution_context_and_residual_ms=float((d['t'][:,:,j]-selected-signal).mean()*1000),
            scope='Signed archived context transferred; not pure decision overhead, not a new measured route'))
    # E1: identical fold rules, but never mix timing cohorts.
    for cohort,rd,sd,cat,z in [('posthoc_three_action',r,s,C.CAT,main),
        ('original_four_static',d['old']['Y'][:,0,:4],d['old']['T'][:,:,:4],np.arange(4),None)]:
        od=dict(d,risk=rd,static=sd)
        zz=z if z is not None else fit_config(od,C.SEED,cat=cat,routers=False)
        vals=[]
        for b in C.BUDGETS:
            if b>rd[:,3].mean():continue
            ev=C.env(rd[:,cat].mean(0),sd[:,:,cat].mean((0,1)),b)[0]
            hv=float(C.evaluate_hull(zz['hull'],b,rd[:,3].mean(),sd[:,:,3].mean()))
            v=100*(ev-hv)/sd[:,:,0].mean();vals.append(v)
            biaspoints.append(dict(domain=name,cohort=cohort,r=float(b),Bias_pp=float(v),cost_scope=C.SCOPE))
        biasrows.append(dict(domain=name,cohort=cohort,points=len(vals),median_Bias_pp=float(np.median(vals)),
            max_abs_Bias_pp=float(np.max(np.abs(vals))),cost_scope=C.SCOPE))
    # One sampled secondary allocation: offline component replay, not hardware execution.
    for bi,b in enumerate(C.BUDGETS):
        aa=[]
        for i,q in enumerate(d['ids']):
            u=int.from_bytes(hashlib.sha256(f'{C.SEED}:{name}:{b}:{int(q)}:cfmix'.encode()).digest()[:8],'big')/2**64
            aa.append(C.CAT[min(np.searchsorted(np.cumsum(main['w'][i,bi]),u,side='right'),2)])
        aa=np.asarray(aa);ct=s[np.arange(n)[:,None],np.arange(3)[None,:],aa[:,None]]
        samples.append(dict(domain=name,b=float(b),sampled_r=float(r[np.arange(n),aa].mean()),sampled_cost_ms=float(ct.mean()*1000),
            expected_r=float(main['mixr'][:,bi].mean()),expected_cost_ms=float(main['mixc'][:,:,bi].mean()*1000),
            scope='One deterministic sampled allocation; offline static-component replay; no new GPU execution'))
    print(name,'E1/E2 completed; conditional bootstrap saved',flush=True)

for filename,data in [('E2_all_budgets.csv',rows),('E1_bias_summary.csv',biasrows),('E1_bias_points.csv',biaspoints),
    ('fold_membership.csv',foldrows),('selected_kappas.csv',fitrows),('OOF_per_query.csv',perquery),
    ('stability.csv',sensitivity),('mixture_sampled_secondary.csv',samples),('context_transfer_audit.csv',limitations)]:C.csvsave(O/filename,data)
C.jsave(O/'input_hashes.json',C.INPUTS)
headline=[z for z in rows if z['b']==.05]
C.csvsave(O/'E2_main_b005.csv',headline)
text=['# E1 + E2 main screening result','','All new costs: '+C.SCOPE+'. No new certification or independent test.','',
    '|Domain|Router|OOF risk|Cost ms|DeltaC cf pp [95%]|Seed1–5 range|','|---|---|---:|---:|---|---|']
for z in headline:text.append(f"|{z['domain']}|{z['method']}|{z['OOF_r']:.6f}|{z['OOF_cost_ms']:.3f}|{z['DeltaC_cf_pp']:+.2f} [{z['low95_pp']:+.2f},{z['high95_pp']:+.2f}]|{z['stability_min_pp']:+.2f} to {z['stability_max_pp']:+.2f}|")
text+=['','Intervals are conditional on fitted kappa/weights; all results are post-hoc. Economics has one source component.',
    'The adapter retains signed archived execution-context differences. Per-query negative accounting estimates are explicitly counted, never clipped. They are not physical latency observations.',
    f"Eligible cells for conditional hardware measurement: {sum(z['conditional_measurement_eligible'] for z in headline)}. No reserved GPU has been confirmed; hardware measurements are NOT_RUN."]
(O/'E2_HEADLINE.md').write_text('\n'.join(text)+'\n',encoding='utf8')
C.jsave(O/'summary.json',dict(status='DONE_OFFLINE_SCREENING',main_cells=len(headline),
    positive_lower_cells=sum(z['conditional_measurement_eligible'] for z in headline),
    negative_accounting_cells=sum(z['negative_query_process_costs']>0 for z in headline),cost_scope=C.SCOPE,
    GPU_jobs=0,new_models_trained=0,sealed_labels_read=0))
print(json.dumps(json.loads((O/'summary.json').read_text()),indent=2),flush=True)
