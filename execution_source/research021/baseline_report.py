import common as C
import json
import math
import numpy as np

base="reports/icde_eab_figure_verification_016/delivery_003/MDRouter_016_figures/figures/data/"
oracle=C.load(base+"fixed_budget_oracle.csv")
points=C.load(base+"plan_points.csv")
contrasts=C.load(base+"paired_contrasts.csv")
aa=C.load(base+"AA_equivalence_intervals.csv")
g2=C.load("reports/icde_eab_g2_setup_017/final_manifest_001.json")
assert C.sha(C.ROOT/"reports/icde_eab_g2_setup_017/final_manifest_001.json") == "8610cc33009937b7875614b88bd2e522b71a6abc99edd2992ce05d5a06ccfa27"
claims=[
dict(claim="offline oracle headroom",source=base+"fixed_budget_oracle.csv",
     values=[{k:r[k] for k in ["domain","budget","headroom3_pp"]}
             for r in oracle if r["model"]=="ColQwen2" and r["budget"]=="0.02"],
     status="PASS_SOURCE_RECONCILED",scope="POSTHOC fractional same-catalog offline upper bound"),
dict(claim="Dev static warm saving",source=base+"plan_points.csv",
     values=[dict(domain=r["domain"],saving=100-float(r["cost_pct_FullV"]))
             for r in points if r["model"]=="ColQwen2" and r["method"]=="R100" and
             r["domain"] in ["HR","Finance","Industrial","Pharma"]],
     status="PASS_SOURCE_RECONCILED",scope="exposed Dev; measured complete resident path"),
dict(claim="external paired QP contrasts",source=base+"paired_contrasts.csv",
     values=contrasts,status="PASS_SOURCE_RECONCILED",
     scope="27 source lectures Biomedical; Economics conditional on 1 connected source"),
dict(claim="OCR lifecycle crossings",source="reports/icde_eab_g2_setup_017/G2_break_even_ranges.csv",
     values="Qwen 75097-79315 / Pali 68444-92841 exclusive; 25-29 / 27-30 prepaid",
     status="PASS_HASH_BOUND",scope="same-process setup/warm; observed ranges; fixed OCR407.725"),
dict(claim="all-zero calibration capacity",source="exact bound 1-delta**(1/n)",
     values=dict(n_min=math.ceil(math.log(.01)/math.log(1-.05)),UCB_n81=1-.01**(1/81)),
     status="PASS_THEORETICAL_BOUND",scope="requires independent units and single atomic test; no certificate"),
dict(claim="strict Serving A/A",source=base+"AA_equivalence_intervals.csv",
     values=aa,status="PASS_FAILURE_PRESERVED",scope="existing failed equivalence gate; EX5 remains deferred"),
dict(claim="main vs lifecycle FullV latency",source="PaperR52 sections/05_setup.tex and 017",
     values=dict(main_ms=70.22157923396057,setup_cohort_ms=36.21837651977936),
     status="PASS_DIFFERENT_MEASUREMENT_COHORTS",
     scope="main nine interleaved methods/3 repeats; setup four statics/1 repeat; both synchronize; cause unresolved"),
]
C.table(C.REPORT/"EX0/claim_to_evidence.csv",claims)
C.prose(C.REPORT/"EX0/baseline_manifest.md",
"""# EX0 baseline

PASS for controlled continuation using existing authorized data and assets.

Paper R52 is pinned at tree aac5fb3b5351706d69d8ed2caf2869e25b3d6abee9d499391f4cc87c2b4221cd.
R51 to R52 changes three sections. Plot widths changed, setup explicitly explains distinct
main and lifecycle schedules, and a transfer-certification sentence was removed.
The canonical source was read and copied only.

The source repository HEAD is e53de31c5ea4272d3639e7a0a98f6c778ae7c742.
Existing work contains many untracked historical artifacts. New outputs are exclusive under run021.
Training is Pharma Fit81 from 80 query families. Dev is HR40, Finance39, Industrial40, Pharma45.
External descriptive evaluation has Biomedical160/27 lectures and Economics58/53 query families
within one connected source component. New models and analyses are post-hoc.
All original quality outcomes are retained. Raw three-process measurements reconcile 28
domain/plan risk and latency aggregates against the frozen 016 source tables.

CPU and GPU snapshots, data hashes and read ledger are in artifacts/run021/EX0 and reads.jsonl.
The model/index paths and existing cost estimators are registered in domains.json.
No new certification, sealed test data, Cal/Eval or CS data is used.
""")
C.prose(C.REPORT/"EX0/reproduce_existing.md",
"""# Existing and missing experiments

Existing raw records support four-domain static/Q/QP/Mix measurements, both external
benchmarks, candidate-harm counts, same-catalog oracle/envelopes, paired intervals,
failed strict A/A and paired setup017 lifecycle curves.

Missing P0 evidence is a nonlinear selector capacity control, cost-separated feature
ablations and a Fit-only frozen mixture evaluated prospectively. These are executed
under EX1-EX3. Reuse alone cannot label recomposed paths as newly measured E2E.

EX7 uses a fresh public clone and a new Python3.11 environment with the public lock file.
Run python reproduce_all.py --output NEW_DIRECTORY from the clone.
Its 38+4 table replay is CPU numerical reconstruction, and does not reexecute GPU measurements.
The public main omits 013/014/015/016/017/018 additions and current manuscript figure sources.
EX7 must retain that publication gap even if all available public outputs reproduce.

New code is under scripts/icde_eab_review_strengthening_021.
Training uses capacity.py, and actual hardware runs use gpu_worker_002.py or later
preserved engineering repairs, with three idle checks and ResourceGuard.
All three-process intervals are paired across query groups and measurement processes.
""")
C.write(C.REPORT/"EX0/final_manifest.json",dict(
    time=C.stamp(),status="PASS_BASELINE_RECONCILIATION",
    input_manifest=C.sha(C.REPORT/"EX0/manifest.json"),
    files={str(p.relative_to(C.ROOT)):C.sha(p) for p in (C.REPORT/"EX0").iterdir()
           if p.is_file()},reads=C.READS))
print("EX0_FINAL",C.sha(C.REPORT/"EX0/final_manifest.json"),flush=True)
