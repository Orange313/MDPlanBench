"""EX0 reconciliation and CPU-only feature preparation."""
import common as C
import ast
import collections
import hashlib
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import time
import types
import numpy as np


def feature_backend():
    # Extract only the existing pure CPU encoder and lexical implementation.
    def extract(path, predicate, env):
        source = C.load(path)
        tree = ast.parse(source)
        nodes = [n for n in tree.body if predicate(n)]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), env)
        return env

    import re
    from typing import Any, Callable, Iterable
    env = dict(np=np, re=re, math=math, hashlib=hashlib, Counter=collections.Counter,
               Any=Any, Callable=Callable, Iterable=Iterable,
               EvidenceUnit=object, Query=object, __name__="frozen_feature_map")
    chosen = extract("src/aaber/router/fast_query_router.py",
        lambda n: isinstance(n, (ast.Assign, ast.AnnAssign, ast.FunctionDef, ast.ClassDef)), env)
    from aaber.common.text import tokenize
    from mdrouter_v5.graded_metrics import stable_ranking
    env = dict(np=np, math=math, Counter=collections.Counter, defaultdict=collections.defaultdict,
               tokenize=tokenize, stable_ranking=stable_ranking,
               CFG=C.load("configs/hr_pilot_sparse_004.json"))
    bm = extract("scripts/cross_domain_four_plan_001.py",
                 lambda n: isinstance(n, ast.ClassDef) and n.name == "BM25", env)["BM25"]
    ep = extract("scripts/icde_eab_independent_007/engine_exact_004.py",
                 lambda n: isinstance(n, ast.FunctionDef) and n.name == "probe_features",
                 dict(np=np))["probe_features"]
    return chosen["FastLexicalFeatureEncoder"], bm, ep


def raw_cube(rows, ids, groups, methods, timefield):
    buckets = collections.defaultdict(list)
    for row in rows:
        buckets[int(row["query_id"]), int(row["process"]), row.get("method", row.get("plan"))].append(row)
    data = {name: np.full((len(ids), 3, len(methods)), np.nan) for name in ("T", "Y", "U")}
    for i, qid in enumerate(ids):
        for p in range(3):
            for j, method in enumerate(methods):
                records = buckets[qid, p, method]
                assert len(records) == 3, (qid, p, method, len(records))
                for name, field in (("T", timefield), ("Y", "r"), ("U", "nDCG10")):
                    data[name][i, p, j] = np.mean([float(x[field]) for x in records])
    return data, buckets


def main():
    (C.ART / "EX0").mkdir()
    (C.REPORT / "EX0").mkdir()
    sys.path.insert(0, str(C.ROOT / "src"))
    Fast, BM, probe_features = feature_backend()
    baseline = C.load("artifacts/" + C.RUN + "/baseline/paper_head.json")
    refdata = "reports/icde_eab_figure_verification_016/delivery_003/MDRouter_016_figures/figures/data/"
    registered = C.load(refdata + "plan_points.csv")
    raw = C.load("reports/icde_final_gate_004/S2/resident_analysis_002/all_unprofiled_requests.csv")
    specs = C.load("artifacts/icde_eab_main_006/X0/domain_policy_config.json")
    fit = C.load("artifacts/icde_evidence_closure_003/E2/pharma_dataset.npz")
    features = C.load("artifacts/icde_evidence_closure_003/E2/outcomes_001/features.json")
    queries = C.load("artifacts/icde_evidence_closure_003/E2/allowed_fitdev_queries.json")
    assert len(fit["qids"]) == 126
    train = np.flatnonzero(fit["roles"] == "fit")
    dev = np.flatnonzero(fit["roles"] == "development")
    assert len(train) == 81 and len(dev) == 45
    assert not set(fit["family"][train]) & set(fit["family"][dev])
    np.savez(C.ART / "EX0/fit.npz", **{k: fit[k][train] for k in
             ["qids", "family", "Q", "P", "Y", "T"]})
    C.write(C.ART / "EX0/fit_queries.json", [q for q in queries if q["role"] == "fit"])
    F = {int(row["query_id"]): row for row in features}
    domains = []
    checks = []
    mappings = ["HR", "Finance", "Industrial", "Pharma"]
    for dom, short in zip(C.DOM, mappings):
        rr = [x for x in raw if x["domain"] == dom]
        ids = sorted({int(x["query_id"]) for x in rr})
        groups = np.array([next(x["family"] for x in rr if int(x["query_id"]) == q) for q in ids])
        methods = C.PLANS + ["Q_regret", "QP_regret", "RandomMix_Q_regret", "RandomMix_QP_regret"]
        arrays, bucket = raw_cube(rr, ids, groups, methods, "resident_full_path_E2E_s")
        old = fit if short == "Pharma" else C.load(
            "artifacts/icde_main_experiment_001/icde_main_experiment_001_s0_inputs_correctness_001/"
            + dom + "_dataset.npz")
        ix = [list(old["qids"]).index(q) for q in ids]
        if short == "Pharma":
            texts = {int(q["query_id"]): q["query"] for q in queries if q["role"] == "development"}
        else:
            texts = {int(q["query_id"]): q["query"] for q in C.load(
                f"manifests/roles/split002/{dom}_development.json")} if False else {}
        qwall = np.array([[np.mean([float(z["Q_wall_s"]) for z in bucket[q, p, "Q_regret"]])
                            for p in range(3)] for q in ids])
        # Reused QP paths expose incremental costs without charging lexical search twice.
        extra = np.array([[np.mean([float(z["Probe_search_extra_wall_s"]) +
                                   float(z["Pstats_extra_wall_s"])
                                   for z in bucket[q, p, "QP_regret"]])
                           for p in range(3)] for q in ids])
        actions = np.array([C.PLANS.index(bucket[q, 0, "QP_regret"][0]["action"]) for q in ids])
        index = {"HR": "hr_primary_001", "Finance": "finance_primary_001",
                 "Industrial": "industrial_primary_003", "Pharma": "pharma_fixedcorpus_index_001"}[short]
        info = dict(domain=short, raw_domain=dom, n=len(ids), grouping="query_family",
                    index=str(C.ROOT / "cache/indexes" / index),
                    cvec=next(x["label_free_cost_vector"] for x in specs if x["domain"] == dom),
                    query_text=texts, evidence="DEV_EXPLORATORY")
        np.savez(C.ART / ("EX0/" + short + ".npz"), qids=ids, groups=groups,
                 Q=old["Q"][ix], P=old["P"][ix], qwall=qwall, old_extra=extra,
                 old_actions=actions, **arrays)
        domains.append(info)
        for j, method in enumerate(C.PLANS):
            row = next(x for x in registered if (x["domain"], x["model"], x["method"]) ==
                       (short, "ColQwen2", ["FullV", "R50", "R100", "BM25"][j]))
            assert abs(float(row["warm_ms"]) - arrays["T"][:, :, j].mean() * 1000) < 1e-7
            assert abs(float(row["risk"]) - arrays["Y"][:, :, j].mean()) < 1e-10
            checks.append(dict(domain=short, method=method, status="PASS_RAW_THREE_PROCESS_RECONCILIATION"))

    bio_protocol = C.load("artifacts/icde_eab_independent_007/T1/biomedical_frozen_protocol.json")
    eco_protocol = C.load("artifacts/icde_eab_external_validation_013/monitor_001/setup_005/execution_protocol.json")
    for name, protocol in [("Biomedical", bio_protocol), ("Economics", eco_protocol)]:
        if name == "Biomedical":
            folders = [f"reports/icde_eab_independent_007/T2/process_{p}_001" for p in range(3)]
            ip = C.ROOT / "cache/indexes/icde_eab_independent_007_biomedical_colqwen_001"
            querypath = C.ROOT / "artifacts/icde_eab_main_006/X3/biomedical_audit_inputs_001/queries/test-00000-of-00001.parquet"
        else:
            folders = [f"reports/icde_eab_external_validation_013/monitor_001/auto2_attempt_001/process_{p:02d}" for p in range(3)]
            ip = Path("${ASSET_ROOT}/icde_eab_external_validation_013_resume_001/indexes/economics_auto_auto2_attempt_001")
            querypath = Path("${ASSET_ROOT}/icde_eab_external_validation_013_resume_001/assets/queries/test-00000-of-00001.parquet")
        import pyarrow.parquet as pq
        C.READS[str(querypath)] = dict(sha256=C.sha(querypath), role="AUTHORIZED_PUBLIC_QUERY_TEXT_ONLY")
        texts = {int(q["query-id"]): q["query"] for q in pq.read_table(querypath, columns=["query-id", "query"]).to_pylist()}
        quality = C.load(folders[0] + "/quality.csv")
        ids = sorted(texts)
        methods = C.PLANS + ["Q_regret", "QP_regret", "RandomMix", "RR_hard", "RR_soft"]
        qm = {(int(x["query_id"]), x["method"]): x for x in quality}
        groupkey = "source_group" if name == "Biomedical" else "family"
        groups = np.array([qm[q, C.PLANS[0]][groupkey] for q in ids])
        rr = []
        for folder in folders:
            for row in C.load(folder + "/requests.csv"):
                point = qm[int(row["query_id"]), row["method"]]
                row.update(r=point["r"], nDCG10=point["nDCG10"])
                rr.append(row)
        arrays, bucket = raw_cube(rr, ids, groups, methods, "E2E_s")
        pages = C.load(ip / "pages.json")
        encoder = Fast()
        encoder.fit_corpus([types.SimpleNamespace(searchable_text=p["markdown"] or "") for p in pages])
        bm = BM(pages)
        Q, P, timing = [], [], []
        for qid in ids:
            qcost, pcost, scost = [], [], []
            for repeat in range(5):
                start = time.perf_counter()
                q = encoder.transform(types.SimpleNamespace(question=texts[qid]))
                qcost.append(time.perf_counter() - start)
                start = time.perf_counter()
                order, scores = bm.search(texts[qid])
                scost.append(time.perf_counter() - start)
                start = time.perf_counter()
                p = probe_features(bm, texts[qid], order, scores)
                pcost.append(time.perf_counter() - start)
            Q.append([q[k] for k in encoder.feature_names])
            P.append(p)
            timing.append(dict(query_id=qid, Q_wall_s=qcost, BM_search_s=scost, Pstats_s=pcost))
        qwall = np.array([[np.mean([float(z["Q_wall_s"]) for z in bucket[q, p, "Q_regret"]])
                            for p in range(3)] for q in ids])
        extra = np.array([[np.mean([float(z["Probe_extra_wall_s"] if name == "Economics" else z["Probe_extra_wall_s"]) +
                                   float(z["Probe_statistics_wall_s"]) for z in bucket[q, p, "QP_regret"]])
                           for p in range(3)] for q in ids])
        actions = np.array([C.PLANS.index(bucket[q, 0, "QP_regret"][0]["action"]) for q in ids])
        np.savez(C.ART / ("EX0/" + name + ".npz"), qids=ids, groups=groups, Q=Q, P=P,
                 qwall=qwall, old_extra=extra, old_actions=actions, **arrays)
        C.write(C.ART / ("EX0/" + name + "_feature_timing.json"), timing)
        cvec = protocol.get("inherited_cost_vector", protocol.get("cost_vector"))
        if cvec is None:
            cvec = C.load("artifacts/icde_eab_independent_007/T0/domain_policy_config.json")[-1]["label_free_cost_vector"]
        info = dict(domain=name, n=len(ids), grouping=groupkey,
                    cvec=cvec, index=str(ip), query_text=texts,
                    evidence="POSTHOC_FROZEN_TRANSFER_NEW_ANALYSIS",
                    source_components=27 if name == "Biomedical" else 1)
        domains.append(info)
        for j, method in enumerate(C.PLANS + ["Q", "QP"]):
            row = next(x for x in registered if (x["domain"], x["model"], x["method"]) ==
                       (name, "ColQwen2", ["FullV", "R50", "R100", "BM25", "Q", "QP"][j]))
            assert abs(float(row["warm_ms"]) - arrays["T"][:, :, j].mean() * 1000) < 1e-7
            assert abs(float(row["risk"]) - arrays["Y"][:, :, j].mean()) < 1e-10
            checks.append(dict(domain=name, method=method, status="PASS_RAW_THREE_PROCESS_RECONCILIATION"))
    C.write(C.ART / "EX0/domains.json", domains)
    C.table(C.REPORT / "EX0/baseline_numeric_checks.csv", checks)
    C.write(C.ART / "EX0/input_hashes.json", C.READS)
    C.write(C.ART / "EX0/environment.json", {
        "python": sys.version, "numpy": np.__version__, "git": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=C.ROOT, text=True).strip(),
        "lscpu": subprocess.check_output(["lscpu"], text=True),
        "nvidia_smi": subprocess.check_output(["nvidia-smi"], text=True),
        "paper": baseline,
    })
    print(C.stamp(), "PASS_EX0", len(checks), [(x["domain"], x["n"]) for x in domains], flush=True)
    C.seal("EX0")


if __name__ == "__main__":
    main()
