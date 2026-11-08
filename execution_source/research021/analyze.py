"""Paired source/family and process statistics for frozen run021 allocations."""
import common as C
import collections
import importlib.util
import json
import sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import eye, kron, csr_matrix

spec = importlib.util.spec_from_file_location("frozen_frontier",
    C.ROOT/"scripts/icde_eab_validation_005/frontier_math.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
METHODS=C.PLANS+["Ridge_Q","Ridge_QP","LightGBM_Q","LightGBM_QP","FitFrozenMix_0.05"]


def oracle(Y,T,budget):
    n,m=Y.shape
    lp=linprog(T.ravel()/n,A_ub=csr_matrix(Y.ravel()[None,:]/n),b_ub=[budget+1e-12],
        A_eq=kron(eye(n),np.ones((1,m)),format="csr"),b_eq=np.ones(n),
        bounds=(0,1),method="highs")
    assert lp.success,lp.message
    return lp.fun


def ci(value):
    return np.quantile(value,[.025,.975]).tolist()


def main():
    metadata=C.load(C.ART/"EX0/domains.json")
    allocation=C.load(C.ART/"EX1/predictions_and_allocations.json")
    input_report=C.ROOT/"reports"/C.RUN
    cpu=C.load(input_report/"EX0/fresh_CPU_feature_timings.csv")
    inference=C.load(input_report/"EX1/CPU_inference_raw.csv")
    mixspec=C.load(C.ART/"EX3/frozen_mixtures.json")
    rows=[]
    for proc in (6,8,9):
        complete=C.load(C.ART/f"GPU/process_{proc:02d}/completed.json")
        assert complete["status"]=="PASS_MATCHED_RESIDENT_PATHS"
        rows.extend(C.load(C.ART/f"GPU/process_{proc:02d}/requests.csv"))
    partial=C.ART/"GPU/process_03/partial.jsonl"
    rows.extend(json.loads(line) for line in partial.read_text().splitlines())
    # Paired timing repeats do not increase query/sample counts.
    results, contrasts, decomposed, mixtures, ablations, selectedrows, failures=[],[],[],[],[],[],[]
    plotrisk=[]
    for di,dom in enumerate(metadata):
        name=dom["domain"]
        ds=C.load(C.ART/("EX0/"+name+".npz"))
        ids=[int(q) for q in ds["qids"]]
        n=len(ids)
        data=collections.defaultdict(list)
        for row in rows:
            if row["domain"]==name:
                data[int(row["query_id"]),int(row["process"]),row["method"]].append(row)
        T=np.full((n,3,len(METHODS)),np.nan)
        CPU=T.copy()
        Y=T.copy()
        U=T.copy()
        intrinsic=T.copy()
        signal=T.copy()
        actions=np.zeros((n,len(METHODS)),int)
        for i,q in enumerate(ids):
            processes=(6,8,9) if name=="Economics" else (3,8,9)
            for p,proc in enumerate(processes):
                for j,method in enumerate(METHODS):
                    rr=data[q,proc,method]
                    assert len(rr)==3
                    acts={r["action"] for r in rr}
                    assert len(acts)==1
                    action=C.PLANS.index(next(iter(acts)))
                    actions[i,j]=action
                    T[i,p,j]=np.mean([float(r["E2E_s"]) for r in rr])
                    CPU[i,p,j]=np.mean([float(r["CPU_s"]) for r in rr])
                    Y[i,p,j]=ds["Y"][i,0,action]
                    U[i,p,j]=ds["U"][i,0,action]
                    intrinsic[i,p,j]=np.mean([float(r["selected_path_s"])+
                        (float(r["BM_search_s"]) if r["probe_reused"] in (True,"True") else 0) for r in rr])
                    signal[i,p,j]=T[i,p,j]-intrinsic[i,p,j]
                    # All methods selecting the same plan must return identical pages.
                    for record in rr:
                        static=data[q,proc,record["action"]][0]
                        assert record["ranking"]==static["ranking"]
        # Raw quality invariance is an already verified frozen label/outcome mapping.
        assert np.allclose(Y[:,:,:4],ds["Y"][:,:,:4],atol=1e-12)
        group=ds["groups"]
        ix=F.boots(group,2000,C.SEED+di)
        rng=np.random.default_rng(C.SEED+di)
        proc=rng.integers(0,3,(2000,3))
        bt=np.array([T[a][:,p].mean((0,1)) for a,p in zip(ix,proc)])
        by=np.array([Y[a][:,p].mean((0,1)) for a,p in zip(ix,proc)])
        bu=np.array([U[a][:,p].mean((0,1)) for a,p in zip(ix,proc)])
        bi=np.array([intrinsic[a][:,p].mean((0,1)) for a,p in zip(ix,proc)])
        shared="paired source/process" if name=="Biomedical" else "paired query-family/process"
        if name=="Economics":shared+="; CONDITIONAL_ONE_SOURCE_COMPONENT"
        for j,method in enumerate(METHODS):
            risk=Y[:,:,j].mean()
            static_r=Y[:,:,:4].mean((0,1))
            static_t=T[:,:,:4].mean((0,1))
            envelope=F.envelope(static_r[C.CAT],static_t[C.CAT],risk)[0][0]
            benv=F.envelope(by[:,C.CAT],bt[:,C.CAT],by[:,j])[0]
            envelope4=F.envelope(static_r,static_t,risk)[0][0]
            benv4=F.envelope(by[:,:4],bt[:,:4],by[:,j])[0]
            delta=100*(benv-bt[:,j])/bt[:,0]
            low,high=ci(delta)
            rlo,rhi=ci(by[:,j])
            tlo,thi=ci(bt[:,j]*1000)
            r=Y[:,0,j]
            rr=[x for x in rows if x["domain"]==name and x["method"]==method]
            result=dict(domain=name,method=method,n=n,groups=len(set(group)),
                mean_r=risk,r_low=rlo,r_high=rhi,nDCG10=U[:,:,j].mean(),
                harm_rate=(r>1e-10).mean(),false_safe_rate=((actions[:,j]!=0)&(r>.05)).mean(),
                false_safe_risk_mass=r[(actions[:,j]!=0)&(r>.05)].sum()/max(r.sum(),1e-15),
                E2E_ms=T[:,:,j].mean()*1000,E2E_low_ms=tlo,E2E_high_ms=thi,
                P50_ms=np.median([float(x["E2E_s"])*1000 for x in rr]),
                P95_ms=np.quantile([float(x["E2E_s"])*1000 for x in rr],.95),
                CPU_ms=CPU[:,:,j].mean()*1000,
                DeltaC_pp=100*(envelope-T[:,:,j].mean())/T[:,:,0].mean(),
                DeltaC_low_pp=low,DeltaC_high_pp=high,
                comparator="SAME_THREE_ACTION_CATALOG",
                four_static_DeltaC_pp=100*(envelope4-T[:,:,j].mean())/T[:,:,0].mean(),
                four_static_low_pp=ci(100*(benv4-bt[:,j])/bt[:,0])[0],
                four_static_high_pp=ci(100*(benv4-bt[:,j])/bt[:,0])[1],
                envelope_ms=envelope*1000,actions=np.bincount(actions[:,j],minlength=4),
                evidence="POSTHOC_EXPLORATORY_MATCHED_ACTUAL_RESIDENT_PATHS",
                interval=shared+"; pointwise95; conditional on fitted model",
                GPU_activity_s=None,GPU_activity_scope="NOT_PROFILED_THIS_MATCHED_COHORT")
            results.append(result)
            expected=oracle(Y[:,:,:4].mean(1)[:,C.CAT],T[:,:,:4].mean(1)[:,C.CAT],risk)
            static_selected=T[:,:,:4][np.arange(n)[:,None],np.arange(3)[None,:],actions[:,j,None]]
            G=100*(envelope-expected)/T[:,:,0].mean()
            error=100*(static_selected.mean()-expected)/T[:,:,0].mean()
            difference=100*(T[:,:,j].mean()-static_selected.mean())/T[:,:,0].mean()
            assert abs(G-error-difference-result["DeltaC_pp"])<1e-8
            decomposed.append(dict(domain=name,method=method,
                risk=risk,oracle_headroom_pp=G,selector_loss_pp=error,
                realized_minus_standalone_execution_pp=difference,
                measured_extra_and_residual_ms=signal[:,:,j].mean()*1000,
                zero_signal_intrinsic_ms=intrinsic[:,:,j].mean()*1000,
                actual_E2E_ms=result["E2E_ms"],
                zero_signal_DeltaC_pp=100*(envelope-intrinsic[:,:,j].mean())/T[:,:,0].mean(),
                zero_signal_low_pp=ci(100*(benv-bi[:,j])/bt[:,0])[0],
                zero_signal_high_pp=ci(100*(benv-bi[:,j])/bt[:,0])[1],
                scope="ANALYSIS_ONLY; required reused BM25 retained; standalone-context difference signed"))
            for i,q in enumerate(ids):
                selectedrows.append(dict(domain=name,query_id=q,group=group[i],method=method,
                    action=C.PLANS[actions[i,j]],r=Y[i,0,j],nDCG10=U[i,0,j],
                    E2E_ms=T[i,:,j].mean()*1000,intrinsic_ms=intrinsic[i,:,j].mean()*1000,
                    other_ms=signal[i,:,j].mean()*1000))
        for a,b in [("LightGBM_Q","Ridge_Q"),("LightGBM_QP","Ridge_QP"),
                    ("Ridge_QP","Ridge_Q"),("LightGBM_QP","LightGBM_Q")]:
            j,k=METHODS.index(a),METHODS.index(b)
            contrasts.append(dict(domain=name,contrast=a+" minus "+b,
                delta_r=(Y[:,:,j]-Y[:,:,k]).mean(),r_low=ci(by[:,j]-by[:,k])[0],r_high=ci(by[:,j]-by[:,k])[1],
                delta_ms=(T[:,:,j]-T[:,:,k]).mean()*1000,
                ms_low=ci((bt[:,j]-bt[:,k])*1000)[0],ms_high=ci((bt[:,j]-bt[:,k])*1000)[1],
                same_risk=False,interpretation="Direct quality/cost tradeoff; compare own matched-risk DeltaC separately"))
        for mix in mixspec:
            key="FitFrozenMix_"+str(mix["budget"])
            acts=np.array(allocation[name][key]["actions"])
            actualY=Y[:,:,:4][np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]]
            actualT=T[:,:,:4][np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]]
            weights=np.array(mix["weights"])
            er=Y[:,:,:4].mean((0,1))[C.CAT]@weights
            et=T[:,:,:4].mean((0,1))[C.CAT]@weights
            mixtures.append(dict(domain=name,Fit_budget=mix["budget"],weights=weights,
                Fit_risk=mix["training_risk"],achieved_expected_r=er,achieved_replayed_r=actualY.mean(),
                expected_E2E_ms=et*1000,replayed_component_E2E_ms=actualT.mean()*1000,
                actions=np.bincount(acts,minlength=4),
                actual_full_path=key=="FitFrozenMix_0.05",
                scope="NEW_POSTHOC_DESIGN; weights chosen on Fit only; expected/replayed allocation not new certification"))
        # Low-cost observable feature ablations, with complete probe computed before masking.
        for method in ["Ridge_Q_distribution","Ridge_Q_gaps","Ridge_Q_coverage"]:
            acts=np.array(allocation[name][method]["actions"])
            actualY=Y[:,:,:4][np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]]
            selected=T[:,:,:4][np.arange(n)[:,None],np.arange(3)[None,:],acts[:,None]]
            extra=[]
            for i,q in enumerate(ids):
                timing=next(z for z in cpu if z["domain"]==name and int(z["query_id"])==q)
                infer=next(z for z in inference if z["domain"]==name and int(z["query_id"])==q and z["model"]==method)
                extra.append(np.mean(json.loads(timing["Q_wall_s"]))+np.mean(json.loads(timing["Pstats_s"]))+
                    (np.mean(json.loads(timing["BM_search_s"])) if acts[i]==0 else 0)+
                    np.mean(json.loads(infer["wall_s"])))
            composed=selected+np.array(extra)[:,None]
            r=actualY.mean()
            env=F.envelope(Y[:,:,:4].mean((0,1))[C.CAT],T[:,:,:4].mean((0,1))[C.CAT],r)[0][0]
            br=np.array([actualY[a][:,p].mean() for a,p in zip(ix,proc)])
            bc=np.array([composed[a][:,p].mean() for a,p in zip(ix,proc)])
            benv=F.envelope(by[:,C.CAT],bt[:,C.CAT],br)[0]
            low,high=ci(100*(benv-bc)/bt[:,0])
            ablations.append(dict(domain=name,method=method,mean_r=r,
                composed_E2E_ms=composed.mean()*1000,
                DeltaC_pp=100*(env-composed.mean())/T[:,:,0].mean(),
                low_pp=low,high_pp=high,mean_extra_ms=np.mean(extra)*1000,
                scope="COMPONENT_COMPOSITION; full existing P13 computed then group masked; no new routed path"))
        for i,method in enumerate(METHODS[4:8],4):
            r=Y[:,0,i]
            order=np.argsort(-r,kind="stable")[:3]
            for q in order:
                failures.append(dict(domain=name,method=method,query_id=ids[q],
                    action=C.PLANS[actions[q,i]],regret=r[q],false_safe=r[q]>.05,
                    selection="predeclared top3 positive regret including zeros if necessary"))
        print(C.stamp(),"ANALYZED",name,flush=True)
    C.table(C.REPORT/"EX1/router_capacity_results.csv",results)
    C.table(C.REPORT/"EX1/capacity_paired_contrasts.csv",contrasts)
    C.table(C.REPORT/"EX1/actual_per_query.csv",selectedrows)
    C.table(C.REPORT/"EX1/false_safe_cases.csv",failures)
    C.table(C.REPORT/"EX2/information_value_decomposition.csv",decomposed)
    C.table(C.REPORT/"EX2/feature_ablation.csv",ablations)
    C.table(C.REPORT/"EX3/static_mixture_prospective.csv",mixtures)
    for stage in ("EX1","EX2","EX3"):
        C.seal(stage)


if __name__=="__main__":
    main()
