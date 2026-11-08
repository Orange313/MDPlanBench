"""Build the author review report, provenance snapshot, and immutable review archive."""
import common as C
from pathlib import Path
import collections
import json
import shutil
import subprocess
import zipfile

FINAL=C.ROOT/"reports"/C.RUN/"analysis_003"
OUT=C.REPORT/"delivery_002"
OUT.mkdir(exist_ok=True)
results=C.load(FINAL/"EX1/router_capacity_results.csv")
decomp=C.load(FINAL/"EX2/information_value_decomposition.csv")
mixtures=C.load(FINAL/"EX3/static_mixture_prospective.csv")
replay=C.load(C.REPORT/"EX7/new_run_cpu_replay_002.json")
assert replay["status"]=="PASS" and len(replay["outputs"])==14
gbm=[r for r in results if r["method"].startswith("LightGBM")]
assert len(gbm)==12
supported=[r for r in gbm if float(r["DeltaC_low_pp"])>0]
domains=["HR","Finance","Industrial","Pharma","Biomedical","Economics"]
def num(row,key,digits=2):
    return f"{float(row[key]):.{digits}f}"

capacity_table="| Domain | Ridge Q ΔC | Ridge QP ΔC | LightGBM Q ΔC | LightGBM QP ΔC [95%] |\n|---|---:|---:|---:|---:|\n"
for domain in domains:
    values={r["method"]:r for r in results if r["domain"]==domain}
    point=lambda k:num(values[k],"DeltaC_pp")
    q=values["LightGBM_QP"]
    capacity_table+=f"| {domain} | {point('Ridge_Q')} | {point('Ridge_QP')} | {point('LightGBM_Q')} | {point('LightGBM_QP')} [{num(q,'DeltaC_low_pp')}, {num(q,'DeltaC_high_pp')}] |\n"
decomp_table="| Domain | Oracle headroom | Selector loss | Route minus standalone cost | Measured non-action + residual ms | Zero-signal ΔC [95%] |\n|---|---:|---:|---:|---:|---:|\n"
for domain in domains:
    r=next(x for x in decomp if x["domain"]==domain and x["method"]=="LightGBM_QP")
    decomp_table+=f"| {domain} | {num(r,'oracle_headroom_pp')} | {num(r,'selector_loss_pp')} | {num(r,'realized_minus_standalone_execution_pp')} | {num(r,'measured_extra_and_residual_ms',3)} | {num(r,'zero_signal_DeltaC_pp')} [{num(r,'zero_signal_low_pp')}, {num(r,'zero_signal_high_pp')}] |\n"
mix_table="| Domain | Fit target | Expected transferred risk | Executed frozen allocation risk |\n|---|---:|---:|---:|\n"
for domain in domains:
    r=next(x for x in mixtures if x["domain"]==domain and x["Fit_budget"]=="0.05")
    mix_table+=f"| {domain} | 0.05 | {num(r,'achieved_expected_r',5)} | {num(r,'achieved_replayed_r',5)} |\n"
report=f"""# MDRouter reviewer experiment closure

Run {C.RUN}, completed {C.stamp()}.

The nonlinear controls do not establish positive matched-risk net savings on these
six workloads. Of 12 LightGBM domain/input points, {len(supported)} have a pointwise paired
95% lower bound above zero. All 24 Ridge/LightGBM domain/input points and negative
results are retained. The unit of saving is percentage points of the same-cohort
FullV warm complete-path cost.

{capacity_table}

## What limits realization

The LightGBM-QP accounting is shown below. All percentage-point terms use the
same three-action catalog and the same risk as the evaluated policy.

{decomp_table}

The identity is realized ΔC = oracle headroom − selector loss − execution difference.
The selector loss uses the measured standalone price of the action actually selected.
The execution difference is signed and includes differences between selected-path
and standalone measurements as well as signal acquisition, inference and residual work.
It must not be described as pure causal probe overhead. The separately recorded
non-action components use the same request and keep the required reused BM25 search
inside the action. Zero-signal is an analysis-only removal of non-action work.

At these GBM-QP points selector loss is 42.39–60.49 pp, whereas the signed execution
difference is 1.04–5.83 pp. On HR, Pharma, Biomedical and Economics the selected actions
already lose the entire catalog headroom under standalone prices. Signal cost also
matters, but is insufficient as a universal explanation of the negative outcome.
Even the zero-signal Biomedical point remains negative with its interval below zero.

The present experiments do not identify an information-theoretic limit of the features.
Only 4 of 81 Fit queries incur R100 harm, all above .05. Finite data, rare harmful cases,
feature information and learner approximation remain confounded. The tested nonlinear
control narrows the Ridge-only objection, while retaining this unresolved limitation.

## Frozen static mixture

{mix_table}

Three weight vectors for .02/.05/.10 were chosen using Fit81 risks and costs only.
The .05 vector is FullV 0, R100 .5679251830, BM25 .4320748170. Query-ID hash assignment
uses seed 20261105, with domain and query ID fixed before evaluating target allocations.
The .05 path was actually executed. Other budgets retain both expectation and replayed
static-component costs, with cost scope explicit in the table.
The expectation is over the fixed mixture, whereas its single frozen draw can differ.
None of these rows is a risk certificate. The new design and external analyses are
post-hoc, although target labels were excluded from all tuning and weight fitting.
The historical Frozen RandomMix remains a distinct archived method.

## Execution and statistical scope

Training used Pharma Fit81, 80 query families. Three grouped inner folds selected
Ridge regularization and four predeclared LightGBM configurations. The chosen LightGBM
models allow up to 60 boosting rounds, three leaves, minimum leaf size20 and L2=8,
with one CPU thread and kappa20. Q150 and QP163 retain the original observable features.
Ridge controls are refitted for the same three targets, and are identified separately
from the original four-head frozen Ridge policies in the manuscript.

There are 382 evaluation queries, 164 exposed Dev plus Biomedical160 and Economics58.
Each query/method was timed three times in each of three independent processes,
on GPU1 only, for 30,942 unprofiled requests across nine methods. Each domain has
three complete process cohorts. The initial valid five-domain batch was retained;
Economics used a separate replacement process after a path-audit exception.
CPU time, total E2E and step timing are measured. This batch has no separate
kernel GPU-active profile and does not impute that field as zero.

Risk uses frozen linear-gain nDCG@10 positive regret. For each returned ranking,
all methods selecting the same action return the same pages in the new run.
The frozen outcome map is reused. Intervals use 2,000 paired resamples of query
families and measurement processes. All 30,942 newly returned Top-10 rankings
match their frozen per-action historical outputs exactly, validating outcome reuse.
Biomedical instead resamples source lectures and processes.
Economics intervals are conditional on its one connected source component.
All intervals are pointwise and conditional on the fitted model. Repeated timings
do not increase the number of independent queries.

Three-action matched-risk ΔC is primary in these capacity controls. The four-static
manuscript envelope is reported as sensitivity, without changing the manuscript's
original results. Timing comparisons stay within this new cohort. Historical
Biomedical70.22ms and setup01736.22ms remain separate source cohorts.

## Independent reproduction and review state

A fresh public no-login clone at e971def8e2c2f0278a272105e9016fe1d473a5d5 and an independently
installed Python3.11 lock environment reproduce 38+4 public numerical CSVs.
In a second isolated workspace, all 8 new scientific CSVs and all 3 PDF+PNG figure
pairs reproduce byte-for-byte, 14 outputs total.

For the six manuscript graphics and three additional options, input hashes and
complete text lists match the private rendering replay. The original copied
plotter first failed its pre-export clipping check. A reviewed copy corrects
the check to the actual tight export extent. PNG byte equality is not achieved,
and current plot sources/results are not all public. See EX7 matrices and repair receipts.

EX0 PASS. EX1 PASS_EXECUTION with supported gain NOT_ESTABLISHED.
EX2 PASS_ACCOUNTING with information-vs-data identification INSUFFICIENT.
EX3 PASS_FIXED_WEIGHT_TRANSFER, with achieved risks explicitly reported and NOT_CERTIFIED.
EX7 PASS_NUMERIC_REPLAY and ARTIFACT_GAP.
EX4 reuses the prior source-level diagnostics. EX5 remains NOT_RUN given the failed
strict Serving gate and no new Serving claim. EX6 reuses hash-verified setup017 and
its independent cost reconciliation. No new P1 hardware experiments were started.
"""
C.prose(OUT/"round_summary.md",report)
C.prose(OUT/"EX1_report.md",report.split("## What limits realization")[0]+"""
Prediction, tuning and cost data are in EX1 training_cv.csv, overfitting_diagnostics.csv,
CPU_inference_raw.csv, and final analysis_003 EX1 tables. Block ablations are in EX2.
The model choice cannot be transferred to a new benchmark as preregistered confirmation.
""")
C.prose(OUT/"EX2_report.md","## Information and cost decomposition\n\n"+decomp_table+
    "\nThe identity is"+report.split("The identity is")[1].split("## Frozen static mixture")[0])
C.prose(OUT/"EX3_report.md","## Fit-only static mixture transfer\n\n"+mix_table+
    "\nWeights, expected risks, observed draw and cost scopes are fully registered in EX3.\n")
C.prose(OUT/"paper_revision_suggestions.md",
"""# Author review suggestions against R52

These paragraphs are candidates only. Preserve the original preregistered result tables.

## Abstract and Introduction

Replace the assertion that decision signals are the key barrier with the bounded claim
that both action-selection errors and decision costs limit realization. The new capacity
control addresses the Ridge-only objection, while finite supervised data and observable
information remain unresolved explanations.

Suggested paragraph

Post-hoc capacity controls compare the linear selectors with regularized gradient-boosted
trees trained on the same 81 Fit queries and observable inputs. Across six workloads,
none of the 12 nonlinear domain/input configurations attains a positive lower endpoint
of its pointwise paired 95% matched-risk saving interval. Greater prediction flexibility
therefore does not by itself establish additional routing value in these experiments.

## Experimental Setup and RQ2

Add a small capacity-control table and the three new review figures, clearly labelled
post-hoc. Keep the original frozen Ridge transfer policies and their intervals as their
own experiment. The new Ridge controls refit the same three target heads as LightGBM.
Feature and regularization choices use only grouped Fit folds. The comparison uses
the same three-action envelope, with the four-static envelope as sensitivity.

Suggested mechanism paragraph

At the tested nonlinear probe-augmented working points, standalone-price selection
loss accounts for 42.4–60.5 percentage points of FullV cost, compared with a signed
1.0–5.8 point difference between realized routes and selected standalone actions.
This decomposition localizes most unrealized headroom to action choices under the
registered prices. Its interpretation depends on counterfactual pricing, and does
not distinguish unavailable information from limited supervision or approximation.
Only four Fit queries harm the R100 plan, highlighting the scarcity of adverse examples.

## Static baseline fairness

Suggested paragraph

Static mixtures chosen from Fit risks alone are transferred with fixed weights and
query-ID randomization. The mixture fitted at mean regret .05 attains expected
regret .1890 on Biomedical and .0840 on Economics, while its executed fixed draw
attains .1955 and .0586. These observations motivate reporting achieved risk rather
than treating the training budget as a target-domain guarantee. The retrospective
envelope remains a descriptive same-risk reference.

## Lessons, Threats and artifacts

Explain that improved risk prediction need not yield beneficial actions, charge required
probe reuse correctly, and separate signal overhead from execution-context differences.
Retain source dependence, post-hoc design, rare training harms, unprofiled GPU activity
and lack of a new K1 or Serving claim. Existing setup017 findings remain separate.
The public release must include current CSVs and plot generation before full EAB artifact
closure can be asserted. Review the exported plotting-bounds repair and software license.
""")
states=[
dict(stage="EX0",status="PASS",evidence="28 raw aggregate checks; R51-R52 diff; legal Fit/Dev feature audit"),
dict(stage="EX1",status="PASS_EXECUTION_GAIN_NOT_ESTABLISHED",evidence="12 nonlinear points, 0 positive95 lower bounds"),
dict(stage="EX2",status="PASS_ACCOUNTING_INFORMATION_LIMIT_INSUFFICIENT",evidence="8 CSVs and paired intervals; selector/signal/execution identity"),
dict(stage="EX3",status="PASS_POSTHOC_FIT_ONLY_TRANSFER_NOT_CERTIFIED",evidence="three frozen mixtures; .05 actual paths; achieved risk retained"),
dict(stage="EX4",status="REUSED_PRIOR_NOT_RUN_NEW",evidence="prior Biomedical source and leave-one-out analysis"),
dict(stage="EX5",status="NOT_RUN",evidence="prior strict A/A failure; resident experiments only"),
dict(stage="EX6",status="REUSED_017_NOT_RUN_NEW",evidence="frozen same-process lifecycle data and hash check"),
dict(stage="EX7",status="PASS_NUMERIC_ARTIFACT_GAP",evidence="42 public CSVs;14 new exact outputs; current publication and raster gaps"),
]
C.table(OUT/"stage_status.csv",states)
cases=C.load(FINAL/"EX1/false_safe_cases.csv")
case_text="# Severe-harm cases selected by the fixed top3 rule\n\n"
case_text+="| Domain | Method | Query ID | Action | Regret |\n|---|---|---:|---|---:|\n"
for r in cases:
    case_text+=f"| {r['domain']} | {r['method']} | {r['query_id']} | {r['action']} | {float(r['regret']):.5f} |\n"
C.prose(OUT/"false_safe_cases.md",case_text)
import importlib.util
spec=importlib.util.spec_from_file_location("frozen_fold_definition",
    C.ROOT/"scripts/icde_evidence_closure_003/learning_base_001.py")
folds=importlib.util.module_from_spec(spec)
spec.loader.exec_module(folds)
fit=C.load(C.ART/"EX0/fit.npz")
membership=[]
for fold,mask in enumerate(folds.folds(fit["family"],3,C.SEED)):
    for i,q in enumerate(fit["qids"]):
        membership.append(dict(fold=fold,query_id=int(q),family=fit["family"][i],
                               role="validation" if mask[i] else "train"))
C.table(OUT/"training_fold_membership.csv",membership)
frozen=C.load(C.ART/"EX1/frozen_models.json")
C.write(OUT/"nonlinear_tree_counts.json",{k:[v.count("\nTree=") for v in m["model"]]
    for k,m in frozen.items() if m["kind"]=="LightGBM"})
C.table(OUT/"claim_to_evidence_matrix.csv",[
dict(claim="nonlinear capacity alone establishes matched-risk savings",status="NOT_SUPPORTED",
     evidence="analysis_003/EX1/router_capacity_results.csv",paper_change="Bound existing routing conclusions"),
dict(claim="signal overhead fully explains lost oracle headroom",status="NOT_SUPPORTED",
     evidence="analysis_003/EX2/information_value_decomposition.csv",paper_change="Replace key-barrier attribution with measured decomposition"),
dict(claim="observable information is fundamentally insufficient",status="INSUFFICIENT",
     evidence="Fit81 with four R100 harms and tested models only",paper_change="Keep information/data/learning identification open"),
dict(claim="Fit risk target guarantees transfer risk",status="NOT_SUPPORTED",
     evidence="analysis_003/EX3/static_mixture_prospective.csv",paper_change="Report achieved risk and frozen-mixture role"),
dict(claim="all public manuscript artifacts are complete",status="ARTIFACT_GAP",
     evidence="EX7/artifact_reproduction_matrix.csv",paper_change="Resolve public content/license and current figure sources"),
])
C.prose(OUT/"failure_ledger.md",
"""# Retained engineering and resource outcomes

- GPU process00 was blocked before CUDA because GPU0 was occupied.
- Process01 stopped at strict feature equality before timing. Original cached Q features
  in the three old Dev domains contain float32 roundtrip precision.
- Process02 confirmed that array dtype alone cannot recover a precision-losing JSON cache.
  The CPU audit proves exact float32 roundtrip parity, and records all differences.
- Process03 completed five domains, then stopped on audit-path registration for the backup01
  Economics index. Only that path-key handling was changed in worker004. Five complete
  prior domain blocks are retained, while Economics uses process06.
- Process07 idle check stopped on transient occupied memory. The log does not establish
  that it belonged to another user. Processes08 and09 then completed sequentially on GPU1.
- EX7 system Python lacked ensurepip. An independently installed Python3.11 environment
  completed the public lock replay. All initial logs remain.
- Private figure replay first omitted its integrity manifest and qa output directory,
  then hit the plotter's canvas/tight-export clipping mismatch. A separate renderer
  copy corrects only the guard and all source inputs/text values reconcile.
- analysis001 parsed a JSON boolean as a CSV string, undercounting required reused BM25
  in one cohort's intrinsic action diagnostic. Its raw timings and main DeltaC were unaffected.
  analysis002 fixes that accounting. analysis003 adds the required offline-oracle plot.
- Earlier independent-replay attempts used a pre-existing exclusive log filename.
  New isolated output and log names preserve all failed/intermediate versions.
- The first review-pack build stopped because the server Git lacks init -b.
  A new standalone snapshot uses git init and symbolic-ref, preserving the failed candidate.
""")

# Record source changes in a private, standalone repository without touching the research history.
snapshot=C.ART/"source_snapshot_002"
snapshot.mkdir()
for src in (C.ROOT/"scripts"/C.RUN).glob("*.py"):
    shutil.copy2(src,snapshot/src.name)
shutil.copy2(C.ART/"EX1/preanalysis.json",snapshot/"preanalysis.json")
subprocess.run(["git","init"],cwd=snapshot,check=True,stdout=subprocess.DEVNULL)
subprocess.run(["git","symbolic-ref","HEAD","refs/heads/codex/icde-eab-review-strengthening-021"],
               cwd=snapshot,check=True)
subprocess.run(["git","add","."],cwd=snapshot,check=True)
subprocess.run(["git","-c","user.name=Codex","-c","user.email=codex@localhost",
                "commit","-m","Freeze post-hoc capacity, information-cost and mixture review experiments"],
               cwd=snapshot,check=True,stdout=subprocess.DEVNULL)
commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=snapshot,text=True).strip()
C.write(OUT/"provenance.json",dict(run=C.RUN,private_code_commit=commit,
    base_commit="e53de31c5ea4272d3639e7a0a98f6c778ae7c742",
    paper_revision=52,paper_tree="aac5fb3b5351706d69d8ed2caf2869e25b3d6abee9d499391f4cc87c2b4221cd",
    final_numeric_directory="analysis_003",timed_requests=30942,query_n=382,train_n=81,
    primary_bootstrap="paired pointwise95, 2000 group/process",
    GPU="physical GPU1 only; three independent processes per domain",
    current_paper_modified=False,public_pushes=0,licenses_modified=False,sealed_reads=0))
C.prose(OUT/"reproduction_commands.md",
"""# Review reconstruction

The public subset follows its own README and requirements-replay-lock.txt.
For the new review's numerical results, use the packaged run layout and a new output directory.

export MDROUTER_ROOT=/absolute/path/to/extracted-review
export MDROUTER_REPORT_ROOT=$MDROUTER_ROOT/reports/replay_review_021
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
python scripts/icde_eab_review_strengthening_021/analyze.py
python scripts/icde_eab_review_strengthening_021/plot_results.py

Use Python3.11, NumPy2.4.6, SciPy1.17.1, Matplotlib3.10.7 and Pillow12.2.0.
The portable review includes frozen feature matrices, allocations, raw timing rows,
and the source helper for the envelope. It excludes original pages, qrels and weights.
Model fitting can be reexecuted with capacity.py in a fresh copied run tree and LightGBM4.6.0,
using only the supplied Fit81 derivative data. This regenerates CPU timing observations,
so new timing samples should not be hash-compared with historical measured values.
""")

# Explicit private review payload. Large public clones, environments and model/page assets stay outside.
paths=[]
for directory in [C.REPORT/"EX0",C.REPORT/"EX7",FINAL,OUT]:
    paths.extend(p for p in directory.rglob("*") if p.is_file())
for path in (C.ROOT/"scripts"/C.RUN).glob("*.py"):
    paths.append(path)
paths.append(C.ROOT/"scripts/icde_eab_validation_005/frontier_math.py")
paths += [p for p in (C.ART/"EX0").glob("*.npz")]
for rel in ["EX0/domains.json","EX0/input_hashes.json","EX0/cache_precision_codecs.json",
            "EX1/preanalysis.json","EX1/frozen_models.json","EX1/predictions_and_allocations.json",
            "EX1/freeze_receipt.json","EX3/frozen_mixtures.json","GPU/process_03/partial.jsonl"]:
    paths.append(C.ART/rel)
for proc in (6,8,9):
    for name in ("requests.csv","completed.json","three_idle_checks.json","resource_guard.json"):
        p=C.ART/f"GPU/process_{proc:02d}"/name
        if p.exists():
            paths.append(p)
paths += list(C.ART.glob("*.log"))
paths += [C.REPORT/"EX1/CPU_inference_raw.csv",C.REPORT/"EX1/training_cv.csv",
          C.REPORT/"EX1/overfitting_diagnostics.csv",C.REPORT/"EX1/predictions.csv"]
paths += [p for p in (C.ART/"baseline").rglob("*") if p.is_file()]
paths += [p for p in (C.ART/"source_snapshot_002").iterdir() if p.is_file()]
paths += [C.REPORT/"delivery_001/ranking_parity.csv",C.REPORT/"delivery_001/ranking_parity.json"]
paths=sorted(set(paths),key=str)
inventory={str(p.relative_to(C.ROOT)):dict(bytes=p.stat().st_size,sha256=C.sha(p)) for p in paths}
C.write(OUT/"MANIFEST.json",dict(time=C.stamp(),run=C.RUN,status="AUTHOR_REVIEW_CANDIDATE",
    private_code_commit=commit,files=inventory,new_CPU_replay=replay["status"],
    final_outputs="analysis_003",risk_budget_unchanged=True,public_push=False))
manifest=OUT/"MANIFEST.json"
C.prose(OUT/"MANIFEST.sha256",C.sha(manifest)+"  MANIFEST.json\n")
archive=OUT/"MDRouter_021_author_review.zip"
with zipfile.ZipFile(archive,"x",zipfile.ZIP_DEFLATED) as z:
    for p in paths+[manifest,OUT/"MANIFEST.sha256"]:
        z.write(p,str(p.relative_to(C.ROOT)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for path,item in inventory.items():
        assert __import__("hashlib").sha256(z.read(path)).hexdigest()==item["sha256"]
print(json.dumps(dict(code_commit=commit,manifest_SHA256=C.sha(manifest),
    ZIP_SHA256=C.sha(archive),ZIP_bytes=archive.stat().st_size,files=len(paths)),indent=2),flush=True)
