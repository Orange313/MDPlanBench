"""Export already-defined fits/secondary draws and verify against the headline.

No new configurations, bootstrap or model fitting; the LP/selection calculations
are deterministic re-execution solely to persist their previously omitted trace.
"""
from pathlib import Path
import argparse,ast,hashlib,json
import numpy as np
import accounting as C

ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();O=a.out;O.mkdir(parents=True,exist_ok=False)
source=Path(__file__).with_name('run_screening.py')
nodes=[z for z in ast.parse(source.read_text()).body if isinstance(z,ast.FunctionDef) and z.name in ['mixture_fit','fit_config']]
env={'np':np,'C':C};exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen_fit_functions','exec'),env)
D=C.all_data(a.project);expected=C.read(a.project/'posthoc_20261109/screening_001/selected_kappas.csv')
main=C.read(a.project/'posthoc_20261109/screening_001/E2_all_budgets.csv');stability=C.read(a.project/'posthoc_20261109/screening_001/stability.csv')
weights=[];samples=[];verified=[]
for name,d in D.items():
    for seed in [C.SEED,1,2,3,4,5]:
        z=env['fit_config'](d,seed)
        for x in z['choices']:
            old=next(r for r in expected if r['domain']==name and int(r['seed'])==seed and r['method']==x['method'] and float(r['b'])==x['b'] and int(r['fold'])==x['fold'])
            assert str(old['kappa'])==str(x['kappa'])
        for j,(m,b) in enumerate(z['config']):
            old=next(r for r in (main if seed==C.SEED else stability) if r['domain']==name and r['method']==m and
                (str(r['b'])==str(b) if isinstance(b,str) or r['b']=='frozen20' else float(r['b'])==b) and (seed==C.SEED or int(r['seed'])==seed))
            delta=float(z['delta'][j])-float(old['DeltaC_cf_pp']);assert delta==0
            verified.append(dict(domain=name,seed=seed,method=m,b=b,delta_vs_previous=delta))
        for x in z['fitmix']:
            k=x['fold'];tr=z['fold']!=k;bi=list(C.BUDGETS).index(x['b']);w=np.array(x['weights'])
            weights.append(dict(domain=name,seed=seed,cohort='posthoc_three_action',fold=k,b=x['b'],
                FullV_weight=w[0],R100_weight=w[1],BM25_weight=w[2],
                training_r=float(d['risk'][tr][:,C.CAT].mean(0)@w),training_cost_ms=float(d['static'][tr][:,:,C.CAT].mean((0,1))@w*1000)))
        if seed==C.SEED:
            np.savez_compressed(O/(name+'_OOF_mixture_weights.npz'),query_ids=d['ids'],fold=z['fold'],weights=z['w'],budgets=C.BUDGETS)
            for i,q in enumerate(d['ids']):
                for bi,b in enumerate(C.BUDGETS):
                    u=int.from_bytes(hashlib.sha256(f'{C.SEED}:{name}:{b}:{int(q)}:cfmix'.encode()).digest()[:8],'big')/2**64
                    action=int(C.CAT[min(np.searchsorted(np.cumsum(z['w'][i,bi]),u,side='right'),2)])
                    samples.append(dict(domain=name,query_id=int(q),b=float(b),action=C.PLANS[action],scope='Single sampled offline allocation, not a new hardware request'))
    old=dict(d,risk=d['old']['Y'][:,0,:4],static=d['old']['T'][:,:,:4])
    z=env['fit_config'](old,C.SEED,cat=np.arange(4),routers=False)
    for x in z['fitmix']:
        w=x['weights'];weights.append(dict(domain=name,seed=C.SEED,cohort='original_four_static',fold=x['fold'],b=x['b'],
            FullV_weight=w[0],R50_weight=w[1],R100_weight=w[2],BM25_weight=w[3]))
C.csvsave(O/'mixture_fold_weights.csv',weights);C.csvsave(O/'secondary_sampled_allocations.csv',samples)
C.csvsave(O/'previous_result_regression.csv',verified)
C.jsave(O/'completed.json',dict(status='DONE_TRACE_EXPORT',previous_point_estimates_exactly_preserved=len(verified),new_configurations=0,model_training=0))
print(json.dumps(dict(weight_rows=len(weights),unchanged_points=len(verified)),indent=2))
