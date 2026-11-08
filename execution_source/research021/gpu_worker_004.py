"""Matched resident-path timing, with frozen decisions and no label access."""
import common as C
import importlib.util
import os
from pathlib import Path
import random
import sys
import time
import numpy as np


def main():
    gpu, proc = int(sys.argv[1]), int(sys.argv[2])
    output = C.ART / "GPU" / f"process_{proc:02d}"
    output.mkdir(parents=True, exist_ok=False)
    C.A = output
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    sys.path.insert(0, str(C.ROOT / "src"))
    # Reuse the already verified valid-token exact scorer.
    import types
    backend_path = C.ROOT / "scripts/icde_eab_independent_007/engine_exact_004.py"
    original = C.load(backend_path)
    old = "str(p.relative_to(C.ROOT))"
    assert original.count(old) == 1
    compatible = original.replace(old,
        "(str(p.relative_to(C.ROOT)) if p.is_relative_to(C.ROOT) else str(p))")
    E = types.ModuleType("backend_exact_audited_path_compatibility")
    exec(compile(compatible,str(backend_path), "exec"),E.__dict__)
    C.write(output/"path_compatibility_receipt.json",dict(source_SHA256=C.sha(backend_path),
        replacement="external backup01 index audit key only",scoring_code_changed=False))
    E.idle(gpu)
    from mdrouter_v5.gpu_accounting import ResourceGuard
    guard = ResourceGuard(gpu, output / "resource_guard.json", period=.1)
    sys.path.insert(0, str(C.ART / "python_deps"))
    from capacity import transform
    import lightgbm as lgb
    import torch
    spec = importlib.util.spec_from_file_location("frozen_learning_gpu",
        C.ROOT / "scripts/icde_evidence_closure_003/learning_base_001.py")
    L = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(L)
    models = C.load(C.ART / "EX1/frozen_models.json")
    allocated = C.load(C.ART / "EX1/predictions_and_allocations.json")
    mixes = C.load(C.ART / "EX3/frozen_mixtures.json")
    metadata = C.load(C.ART / "EX0/domains.json")
    codecs = C.load(C.ART / "EX0/cache_precision_codecs.json")
    def cached_precision(value, domain, field):
        return value.astype(np.float32).astype(np.float64) if codecs[domain][field] == "float32_roundtrip" else value
    primary = ["Ridge_Q", "Ridge_QP", "LightGBM_Q", "LightGBM_QP"]
    predictors = {}
    for key in primary:
        model = models[key]
        if model["kind"] == "LightGBM":
            predictors[key] = [lgb.Booster(model_str=text) for text in model["model"]]
        else:
            values = [np.array(x) for x in model["model"]]
            values[0] = values[0].astype(bool)
            predictors[key] = values
    rows = []
    try:
        with torch.inference_mode():
            for dom in metadata:
                name = dom["domain"]
                if len(sys.argv)>3 and name != sys.argv[3]:
                    continue
                eng = E.Engine(dom["index"], guard)
                ds = C.load(C.ART / ("EX0/" + name + ".npz"))
                ids = [int(q) for q in ds["qids"]]
                pos = {q: i for i,q in enumerate(ids)}
                texts = {int(k):v for k,v in dom["query_text"].items()}
                if name in ["HR", "Finance", "Industrial"]:
                    allowed = C.load(f"artifacts/splits/query_generalization_002/{dom['raw_domain']}/dev_queries.json")
                    texts = {int(q["query_id"]):q["query"] for q in allowed if int(q["query_id"]) in pos}
                assert set(ids) <= texts.keys()
                costs = np.array(dom["cvec"])[C.CAT]
                costs /= costs[0]
                methods = C.PLANS + primary + ["FitFrozenMix_0.05"]
                parity = []
                for qid in ids:
                    qcheck = eng.Q(texts[qid])
                    bcheck = eng.bm.search(texts[qid])
                    pcheck = E.probe_features(eng.bm,texts[qid],*bcheck)
                    qstored, pstored = ds["Q"][pos[qid]], ds["P"][pos[qid]]
                    assert np.array_equal(cached_precision(qcheck,name,"Q"), qstored)
                    assert np.array_equal(cached_precision(pcheck,name,"P"), pstored)
                    parity.append(dict(query_id=qid,Q_dtype=str(qstored.dtype),P_dtype=str(pstored.dtype),
                        max_Q_float64_difference=float(np.max(np.abs(qcheck-qstored))),
                        max_P_float64_difference=float(np.max(np.abs(pcheck-pstored))),
                        asset_dtype_exact=True))
                C.write(output/(name+"_feature_parity.json"),parity)
                def route(method, qid):
                    probe = None
                    qcost = bcost = scost = pcost = 0.
                    action = method
                    text = texts[qid]
                    if method in primary:
                        start = time.perf_counter()
                        q = cached_precision(eng.Q(text),name,"Q")
                        qcost = time.perf_counter()-start
                        if method.endswith("_QP"):
                            start = time.perf_counter()
                            probe = eng.bm.search(text)
                            bcost = time.perf_counter()-start
                            start = time.perf_counter()
                            pf = cached_precision(E.probe_features(eng.bm, text, *probe),name,"P")
                            x = np.r_[q, pf][None]
                            scost = time.perf_counter()-start
                        else:
                            x = q[None]
                        start = time.perf_counter()
                        model = models[method]
                        if method.startswith("LightGBM"):
                            design = transform(model["preprocess"], x)
                            pr = np.array([b.predict(design, num_threads=1)[0] for b in predictors[method]])
                        else:
                            pr = L.predict(predictors[method], x)[0]
                        j = int(C.CAT[np.argmin(costs + 20*np.maximum(pr, 0))])
                        action = C.PLANS[j]
                        pcost = time.perf_counter()-start
                        assert j == allocated[name][method]["actions"][pos[qid]]
                    elif method.startswith("FitFrozenMix"):
                        start = time.perf_counter()
                        mix = next(m for m in mixes if m["budget"] == .05)
                        token = __import__("hashlib").sha256(f"{C.SEED}:{name}:{qid}:prospective".encode()).digest()
                        u = int.from_bytes(token[:8],"big")/2**64
                        j = int(C.CAT[min(np.searchsorted(np.cumsum(mix["weights"]),u,side="right"),2)])
                        action = C.PLANS[j]
                        pcost = time.perf_counter()-start
                        assert j == allocated[name][method]["actions"][pos[qid]]
                    start = time.perf_counter()
                    result = eng.execute(action,text,probe)
                    path = time.perf_counter()-start
                    return result, dict(action=action, Q_s=qcost, BM_search_s=bcost,
                        Pstats_s=scost, predict_s=pcost, selected_path_s=path,
                        probe_reused=probe is not None and action!="Full-Visual")
                expected = {}
                for method in methods:
                    for _ in range(3):
                        route(method,ids[0])
                order = [(qid,method,rep) for qid in ids for method in methods for rep in range(3)]
                random.Random(C.SEED+proc).shuffle(order)
                for number,(qid,method,rep) in enumerate(order):
                    guard.check()
                    torch.cuda.synchronize()
                    start, ct = time.perf_counter(), time.process_time()
                    result, details = route(method,qid)
                    torch.cuda.synchronize()
                    elapsed, cpu = time.perf_counter()-start, time.process_time()-ct
                    action = details["action"]
                    target = (qid, action)
                    if target in expected:
                        assert expected[target] == result
                    else:
                        expected[target] = result
                    row = dict(domain=name,process=proc,query_id=qid,method=method,repeat=rep,
                        E2E_s=elapsed,CPU_s=cpu,ranking=result,**details)
                    rows.append(row)
                    with (output/"partial.jsonl").open("a") as stream:
                        stream.write(__import__("json").dumps(row)+"\n")
                    if (number+1)%300 == 0:
                        print(C.stamp(),name,proc,number+1,len(order),flush=True)
                C.write(output/(name+"_rankings.json"),
                        {str(q)+":"+p:v for (q,p),v in expected.items()})
                del eng
                torch.cuda.empty_cache()
            C.table(output/"requests.csv",rows)
            C.write(output/"completed.json",dict(status="PASS_MATCHED_RESIDENT_PATHS",
                process=proc,gpu=gpu,rows=len(rows),time=C.stamp(),
                peak_allocated_GPU_bytes=torch.cuda.max_memory_allocated()))
    finally:
        guard.close()


if __name__ == "__main__":
    main()
