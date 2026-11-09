"""E3, K17 and E4 from archived legal outcomes; never trains a model."""
from pathlib import Path
import argparse,importlib.util,json
import numpy as np
import accounting as C

ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--gates',type=Path);ap.add_argument('--k17-input',type=Path)
a=ap.parse_args();R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
gates=a.gates or R/'reports/icde_eab_execution_v2_032/gates_001'
g=C.read(gates/'gate_summary.json');assert g['endpoint_gate'] and g['kappa20_exact_float_gate']
checks=C.read(gates/'interval_endpoint_gate.csv');points=[]
for cohort,domain,method in sorted({(z['cohort'],z['domain'],z['method']) for z in checks}):
    z=[x for x in checks if (x['cohort'],x['domain'],x['method'])==(cohort,domain,method)]
    points.append(dict(cohort=cohort,domain=domain,method=method,L=float(next(x['reproduced'] for x in z if x['side']=='low')),
        U=float(next(x['reproduced'] for x in z if x['side']=='high')),scope='Original pointwise interval reproduced, not new certification'))
C.csvsave(O/'E3_intervals_36.csv',points)
counts=[]
for label,group in [('original12',[z for z in points if z['cohort']=='ORIGINAL_FROZEN']),
                    ('posthoc24',[z for z in points if z['cohort']=='POSTHOC_021']),('all36',points)]:
    counts.append(dict(cohort=label,n=len(group),U_lt5=sum(z['U']<5 for z in group),U_lt10=sum(z['U']<10 for z in group),U_lt15=sum(z['U']<15 for z in group)))
C.csvsave(O/'E3_upper_bound_counts.csv',counts)

# K17: exactly the archived learning-curve comparator and paired family/seed bootstrap.
if a.k17_input:
    ki=C.read(a.k17_input);ds={k:np.asarray(v) for k,v in ki['dev_dataset'].items()}
    raw=ki['policy_rows'];members=ki['subset_membership'];old=ki['archived_learning_curves']
else:
    ds=C.read(R/'artifacts/icde_evidence_closure_003/E2/pharma_dataset.npz')
    raw=C.read(R/'reports/icde_evidence_closure_003/E2/per_query_policy.csv')
    members=C.read(R/'reports/icde_final_gate_004/S3/paired_fit_subsets.csv')
    old=C.read(R/'reports/icde_final_gate_004/S3/matched_risk_learning_curves.csv')
dev=ds['roles']=='development';ids=ds['qids'][dev].astype(int);groups=ds['family'][dev]
Y,T=ds['Y'][dev],ds['T'][dev];seed=202610271730
fpath=R/'scripts/icde_eab_validation_005/frontier_math.py'
if not fpath.exists():fpath=Path(__file__).resolve().parents[1]/'repro/frontier_math.py'
sp=importlib.util.spec_from_file_location('legacy_frontier',fpath);F=importlib.util.module_from_spec(sp);sp.loader.exec_module(F)
ix=F.boots(groups,2000,seed);brstatic=np.array([Y[i].mean(0) for i in ix]);btstatic=np.array([T[i].mean(0) for i in ix])
si=np.random.default_rng(seed).integers(0,3,(2000,3));seeds=[202610271130,202610271131,202610271132]
kr=[];verify=[]
for method in ['Q_regret','QP_regret']:
    for kap in [10,20]:
        for n in [20,40,60,81]:
            rr=[];tt=[]
            for s in seeds:
                z={int(x['query_id']):x for x in raw if x['source']=='Pharma_only' and x['method']==method and
                   int(x['Pharma_fit_n'])==n and int(x['seed'])==s and float(x['kappa'])==kap}
                assert set(z)==set(ids)
                rr.append(np.array([float(z[q]['r']) for q in ids]));tt.append(np.array([float(z[q]['E2E_s']) for q in ids]))
            rr=np.array(rr);tt=np.array(tt)
            br=np.array([[r[i].mean() for i in ix] for r in rr]);bt=np.array([[t[i].mean() for i in ix] for t in tt])
            ev=np.array([F.envelope(brstatic,btstatic,r)[0] for r in br]);inc=100*(ev-bt)/btstatic[:,0][None]
            point=np.mean([100*(F.envelope(Y.mean(0),T.mean(0),r.mean())[0][0]-t.mean())/T[:,0].mean() for r,t in zip(rr,tt)])
            low,high=np.quantile(np.mean(np.take_along_axis(inc.T,si,axis=1),axis=1),[.025,.975])
            row=dict(method=method,kappa=kap,Fit_n=n,mean_Dev_r=float(rr.mean()),mean_E2E_s=float(tt.mean()),
                matched_risk_increment_pp=float(point),paired95_low_pp=float(low),paired95_high_pp=float(high),
                catalog='Original four-action learning diagnostic: FullV/R50/R100/BM25',
                scope='Same fixed Dev45, same subsets/seeds, archived component costs; not independent generalization')
            target=next(x for x in old if x['method']==method and int(x['Fit_n'])==n and float(x['kappa'])==kap)
            for key in ['mean_Dev_r','mean_E2E_s','matched_risk_increment_pp','paired95_low_pp','paired95_high_pp']:
                error=row[key]-float(target[key]);verify.append(dict(method=method,kappa=kap,Fit_n=n,field=key,delta=error,PASS=abs(error)<1e-8))
            kr.append(row)
assert all(x['PASS'] for x in verify)
C.csvsave(O/'K17_kappa10_vs20.csv',kr);C.csvsave(O/'K17_original_reproduction.csv',verify)
C.csvsave(O/'K17_subset_membership.csv',[{k:z[k] for k in ['seed','requested_n','query_id','family']} for z in members])
C.jsave(O/'K17_timeline.json',dict(original_grid=[0,1,5,10,20,50,100],training_seeds=seeds,
    original_preanalysis='2026-10-27T15:23:04.291948+08:00',kappa20_candidate_written='2026-10-27T15:57:11.214590+08:00',
    kappa10_figure_written='2026-10-27T15:57:13.538609+08:00',
    statement='Kappa10 and20 came from the same seven-point development sweep; the reason for displaying10 was not registered. This is not a pre-freeze diagnostic.'))

# E4 last-priority coarse hull, all three comparator paths were actually timed in the021 cohort.
D=C.all_data(R);tr=[]
for name,d in D.items():
    n=len(d['ids']);s=d['static'];r=d['risk'];mixrisk=r[np.arange(n),d['acts'][:,8]]
    comparator_r=np.c_[np.zeros(n),mixrisk,r[:,3]];comparator_t=d['t'][:,:,[0,8,3]]
    h=C.hull(comparator_r.mean(0),comparator_t.mean((0,1)));ix,proc=C.boot_indices(d['groups'])
    bs=np.array([d['t'][i][:,p].mean((0,1)) for i,p in zip(ix,proc)])
    by=np.array([r[i].mean(0) for i in ix]);bmix=np.array([mixrisk[i].mean() for i in ix])
    draws=[]
    for m in C.MODELS:
        j=C.METHODS.index(m);risk=r[np.arange(n),d['acts'][:,j]];br=np.array([risk[i].mean() for i in ix])
        dr=[]
        for k in range(C.B):
            bh=C.hull([0,bmix[k],by[k,3]],bs[k,[0,8,3]])
            dr.append(100*(C.evaluate_hull(bh,br[k],by[k,3],bs[k,3])-bs[k,j])/bs[k,0])
        dr=np.array(dr);draws.append(dr);lo,hi=np.quantile(dr,[.025,.975])
        val=100*(C.evaluate_hull(h,risk.mean(),r[:,3].mean(),s[:,:,3].mean())-d['t'][:,:,j].mean())/s[:,:,0].mean()
        tr.append(dict(domain=name,method=m,DeltaC_tr_pp=float(val),low95_pp=float(lo),high95_pp=float(hi),
            comparator='coarse hull: measured FullV/Fit-only .05 mixture/BM25',
            cost_scope='Archived same-cohort frozen-kappa20 measured route; no .02/.10 cost composition'))
    np.savez_compressed(O/(name+'_E4_draws.npz'),DeltaC_tr_pp=np.stack(draws,axis=1),methods=C.MODELS)
C.csvsave(O/'E4_coarse_hull.csv',tr)

import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(8,5))
for col,m in enumerate(['Q_regret','QP_regret']):
    for kap,color in [(10,'#777777'),(20,'#1766a3')]:
        z=[x for x in kr if x['method']==m and x['kappa']==kap];xx=[x['Fit_n'] for x in z]
        axes[0,col].plot(xx,[x['mean_Dev_r'] for x in z],'-o',color=color,label=f'kappa={kap}')
        v=np.array([x['matched_risk_increment_pp'] for x in z]);lo=np.array([x['paired95_low_pp'] for x in z]);hi=np.array([x['paired95_high_pp'] for x in z])
        axes[1,col].errorbar(xx,v,yerr=[v-lo,hi-v],fmt='-o',color=color,capsize=2)
    axes[0,col].set_title(m);axes[0,col].legend();axes[1,col].axhline(0,color='black',lw=.6)
    axes[0,col].set_ylabel('Fixed Dev mean regret');axes[1,col].set_ylabel('Original four-static DeltaC (pp)');axes[1,col].set_xlabel('Fit queries')
fig.suptitle('POST-HOC / fixed Dev45 / original learning diagnostic');fig.tight_layout()
fig.savefig(O/'K17_learning.pdf');fig.savefig(O/'K17_learning.png',dpi=240);plt.close(fig)
C.jsave(O/'input_hashes.json',C.INPUTS)
C.jsave(O/'completed.json',dict(E3='DONE',E3_cells=36,E3_counts=counts,K17='DONE_NO_RETRAINING',K17_points=16,
    E4='DONE_COARSE_HULL',E4_cells=24,GPU_jobs=0,sealed_labels_read=0))
print(json.dumps(dict(E3=counts,K17_points=16,E4_cells=24),indent=2),flush=True)
