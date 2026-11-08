"""Fit-only grouped capacity control, with target labels opened after model freeze."""
import common as C
import collections
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(C.ART / "python_deps"))
import lightgbm as lgb
spec = importlib.util.spec_from_file_location(
    "frozen_learning", C.ROOT / "scripts/icde_evidence_closure_003/learning_base_001.py")
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)

CONFIG = dict(
    seed=C.SEED, kappa=20, CV_folds=3, Ridge_L2=[1., 8., 64.],
    LightGBM_grid=[dict(num_leaves=3, min_data_in_leaf=10, lambda_l2=1.),
                  dict(num_leaves=3, min_data_in_leaf=20, lambda_l2=8.),
                  dict(num_leaves=7, min_data_in_leaf=10, lambda_l2=8.),
                  dict(num_leaves=7, min_data_in_leaf=20, lambda_l2=8.)],
    LightGBM_fixed=dict(objective="regression", metric="l2", learning_rate=.05,
                       max_depth=3, num_threads=1, deterministic=True,
                       force_col_wise=True, feature_pre_filter=False,
                       num_leaves=3, verbosity=-1, seed=C.SEED),
    rounds=60, budgets=[.02, .05, .10], bootstrap=2000,
    feature_blocks={"Q": [], "QP": list(range(13)), "Q_distribution": [0,1,2,3,4,5,9,10,12],
                    "Q_gaps": [6,7,8], "Q_coverage": [11]},
    scope="POSTHOC_EXPLORATORY; existing frozen policies remain separate",
)


def process(X):
    cols = np.isfinite(X).any(0)
    med = np.nanmedian(X[:, cols], axis=0)
    return {"cols": cols.tolist(), "median": med.tolist()}


def transform(pre, X):
    values = X[:, np.array(pre["cols"], bool)]
    missing = ~np.isfinite(values)
    return np.c_[np.where(missing, np.array(pre["median"]), values), missing]


def fit_model(kind, X, Y, params):
    if kind == "Ridge":
        return dict(kind=kind, model=[v.tolist() for v in L.fit(X, Y, params["L2"])])
    pre = process(X)
    design = transform(pre, X)
    models = []
    for target in Y.T:
        trainer = lgb.train(CONFIG["LightGBM_fixed"] | params,
                            lgb.Dataset(design, label=target),
                            num_boost_round=CONFIG["rounds"])
        models.append(trainer.model_to_string())
    return dict(kind=kind, preprocess=pre, model=models)


def predict(model, X):
    if model["kind"] == "Ridge":
        values = [np.array(v) for v in model["model"]]
        values[0] = values[0].astype(bool)
        return L.predict(values, X)
    design = transform(model["preprocess"], X)
    boosters = [lgb.Booster(model_str=text) for text in model["model"]]
    return np.stack([b.predict(design, num_threads=1) for b in boosters], axis=1)


def design(data, block):
    features = CONFIG["feature_blocks"][block]
    return np.c_[data["Q"], data["P"][:, features]] if features else data["Q"]


def envelope(risk, cost, budget):
    answer = linprog(cost, A_ub=[risk], b_ub=[budget + 1e-12],
                     A_eq=[np.ones(len(cost))], b_eq=[1], bounds=(0,1), method="highs")
    assert answer.success, answer.message
    return answer.fun, answer.x


def main():
    for stage in ("EX1", "EX2", "EX3"):
        (C.ART / stage).mkdir()
        (C.REPORT / stage).mkdir()
    C.write(C.ART / "EX1/preanalysis.json", CONFIG)
    data = C.load(C.ART / "EX0/fit.npz")
    Y = data["Y"][:, C.CAT]
    costs = data["T"][:, C.CAT].mean(0) / data["T"][:, 0].mean()
    groups = data["family"]
    models, searches = {}, []
    variants = [(kind, block) for kind in ("Ridge", "LightGBM") for block in ("Q", "QP")]
    variants += [("Ridge", block) for block in ("Q_distribution", "Q_gaps", "Q_coverage")]
    for kind, block in variants:
        X = design(data, block)
        grid = [dict(L2=value) for value in CONFIG["Ridge_L2"]] if kind == "Ridge" else CONFIG["LightGBM_grid"]
        candidates = []
        for position, params in enumerate(grid):
            pred = np.empty_like(Y)
            for validation in L.folds(groups, 3, C.SEED):
                assert not set(groups[validation]) & set(groups[~validation])
                model = fit_model(kind, X[~validation], Y[~validation], params)
                pred[validation] = predict(model, X[validation])
            # Cost-estimator normalization depends only on training-fold costs.
            acts = np.empty(len(X), int)
            utility = []
            for validation in L.folds(groups, 3, C.SEED):
                fold_cost = data["T"][~validation][:, C.CAT].mean(0) / data["T"][~validation, 0].mean()
                acts[validation] = np.argmin(fold_cost + 20*np.maximum(pred[validation], 0), axis=1)
                utility.extend(fold_cost[acts[validation]] + 20*Y[validation, acts[validation]])
            score = np.mean(utility)
            mse = np.mean((pred - Y)**2)
            candidates.append((score, position, params))
            searches.append(dict(kind=kind, block=block, candidate=position, params=params,
                                 OOF_utility=score, OOF_MSE=mse, Fit_n=len(X),
                                 Fit_families=len(set(groups)), evaluated_labels="Fit81_ONLY"))
        _, _, chosen = min(candidates, key=lambda x: (x[0], x[1]))
        model = fit_model(kind, X, Y, chosen)
        fitted = predict(model, X)
        models[kind + "_" + block] = model | dict(block=block, params=chosen,
            Fit_MSE=np.mean((fitted-Y)**2),
            OOF_MSE=next(r["OOF_MSE"] for r in searches if r["kind"]==kind and
                         r["block"]==block and r["params"]==chosen))
        print(C.stamp(), "FROZEN", kind, block, chosen, flush=True)
    C.write(C.ART / "EX1/frozen_models.json", models)
    C.table(C.REPORT / "EX1/training_cv.csv", searches)
    # Frozen mixture has no target-domain label input. Use only Fit81 risks/costs.
    mixtures = []
    for eps in CONFIG["budgets"]:
        expected, weight = envelope(Y.mean(0), data["T"][:, C.CAT].mean(0), eps)
        mixtures.append(dict(budget=eps, weights=weight.tolist(), seed=C.SEED,
                             training_risk=weight @ Y.mean(0), Fit_mean_cost=expected,
                             catalog=[C.PLANS[i] for i in C.CAT], label_source="Fit81_ONLY"))
    C.write(C.ART / "EX3/frozen_mixtures.json", mixtures)
    C.write(C.ART / "EX1/freeze_receipt.json", dict(time=C.stamp(),
            model_hash=C.sha(C.ART/"EX1/frozen_models.json"),
            mixture_hash=C.sha(C.ART/"EX3/frozen_mixtures.json"),
            evaluation_outcomes_opened_in_this_process=False,
            inference_timing_scope="CPU actual measured; retrieval component composition pending matched GPU paths"))
    domains = C.load(C.ART / "EX0/domains.json")
    prediction_rows, timings, rawpreds, diagnostics = [], [], {}, []
    for dom in domains:
        name = dom["domain"]
        ds = C.load(C.ART / ("EX0/" + name + ".npz"))
        costs = np.array(dom["cvec"])[C.CAT]
        costs /= costs[0]
        outputs = {}
        for key, model in models.items():
            X = design(ds, model["block"])
            pp = predict(model, X)
            acts = C.CAT[np.argmin(costs + 20*np.maximum(pp, 0), axis=1)]
            outputs[key] = dict(prediction=pp.tolist(), actions=acts.tolist())
            # Measure single-request inference after construction/warmup.
            if model["kind"] == "LightGBM":
                boosters = [lgb.Booster(model_str=t) for t in model["model"]]
                def infer(x):
                    z = transform(model["preprocess"], x)
                    return np.stack([b.predict(z, num_threads=1) for b in boosters], axis=1)
            else:
                values = [np.array(v) for v in model["model"]]
                values[0] = values[0].astype(bool)
                def infer(x):
                    return L.predict(values, x)
            for i, qid in enumerate(ds["qids"]):
                wall, cpu = [], []
                for repeat in range(5):
                    start, ct = time.perf_counter(), time.process_time()
                    pred = infer(X[i:i+1])[0]
                    selected = C.CAT[np.argmin(costs + 20*np.maximum(pred, 0))]
                    cpu.append(time.process_time()-ct)
                    wall.append(time.perf_counter()-start)
                    assert selected == acts[i]
                timings.append(dict(domain=name, query_id=int(qid), model=key,
                                    wall_s=wall, CPU_s=cpu, scope="SINGLE_REQUEST_CPU"))
                prediction_rows.append(dict(domain=name, query_id=int(qid), group=ds["groups"][i],
                    method=key, action=C.PLANS[acts[i]], predicted_r=pp[i].tolist(),
                    actual_r=float(ds["Y"][i,:,acts[i]].mean()),
                    mean_planner_s=np.mean(wall), CPU_s=np.mean(cpu)))
            truth = ds["Y"][:,:,:4].mean(1)[:,C.CAT]
            diagnostics.append(dict(domain=name, model=key, n=len(X),
                Fit_MSE=model["Fit_MSE"], grouped_Fit_OOF_MSE=model["OOF_MSE"],
                evaluation_MSE=np.mean((pp-truth)**2),
                selected_action_MAE=np.mean(np.abs(pp[np.arange(len(X)),np.searchsorted(C.CAT,acts)]-
                                                       truth[np.arange(len(X)),np.searchsorted(C.CAT,acts)])),
                actions=np.bincount(acts,minlength=4), status="EXPLORATORY_POSTHOC"))
        for mix in mixtures:
            weights = np.array(mix["weights"])
            actions = []
            for qid in ds["qids"]:
                token = __import__("hashlib").sha256(f"{C.SEED}:{name}:{qid}:prospective".encode()).digest()
                u = int.from_bytes(token[:8], "big") / 2**64
                actions.append(int(C.CAT[min(np.searchsorted(np.cumsum(weights), u, side="right"), 2)]))
            outputs["FitFrozenMix_" + str(mix["budget"])] = dict(actions=actions)
        rawpreds[name] = outputs
    C.write(C.ART / "EX1/predictions_and_allocations.json", rawpreds)
    C.table(C.REPORT / "EX1/predictions.csv", prediction_rows)
    C.table(C.REPORT / "EX1/CPU_inference_raw.csv", timings)
    C.table(C.REPORT / "EX1/overfitting_diagnostics.csv", diagnostics)
    print(C.stamp(), "PASS_FROZEN_MODELS_AND_ALLOCATION", len(prediction_rows), flush=True)


if __name__ == "__main__":
    main()
