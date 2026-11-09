# MDPlanBench / MDRouter

MDPlanBench measures the quality, reference-relative risk, and complete-path and
lifecycle cost of physical plans and fixed routers for multimodal document retrieval.

**Paper:** *[Experiment, Analysis, and Benchmark] MDPlanBench: When Does Query-Level
Physical Plan Selection Pay Off for Multimodal Document Retrieval?*

This **local review candidate** audits manuscript **R82** (revision
`34d15ab3-c937-4bf7-b5e8-d61e49000131`). It extends public artifact v1.1
`e9d4c2d14abca6003001caf8010da4f6b7321669`. It has **not been pushed or published**.
The paper's numerical results and source are not changed by this artifact work.

## Quick start: reproduce from frozen numerical records (CPU, offline)

Linux x86-64, Python 3.11, approximately 1 GiB free for a new environment and
0.5 GiB for checkout/output are recommended. No CUDA, weights, original pages,
queries, annotation files, training, or network is required after installation.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r env/requirements-cpu-lock.txt
.venv/bin/python scripts/verify_manifest.py
.venv/bin/python scripts/reproduce_submission.py --output ../mdplanbench-replay
```

The output directory must be new. The entry point executes the original
frozen-record replay, the post-hoc supplement, the scheduling diagnosis, and
manuscript-value checks. It saves commands, errors and receipts even on failure.
Typical CPU execution is a few minutes; exact measured times and tested platforms
are recorded in [ACCEPTANCE_REPORT.md](ACCEPTANCE_REPORT.md). **Linux is the strict
PNG byte-comparison reference.** Windows renders some PNGs differently; numerical
and image-byte results are reported separately, never silently converted to PASS.

Outputs include `base/tables/`, `base/audit/`, `posthoc/`, `E6/`, `paper_values/`,
and `submission_replay_receipt.json`. `figures_generated/` contains data-driven
renders with current manuscript names. `figures_exact_manuscript/` contains the
author's hash-verified graphics; the architecture diagram is a frozen editable
draw.io/PDF asset, not a statistical plot. Render layout/font identity and
numerical identity are distinct tests.

For older commands, `scripts/reproduce_paper.py` remains available. It does not
cover all late manuscript additions; use `reproduce_submission.py` for this audit.

## Paper-to-artifact map

| R82 item | Frozen inputs and computation | Output |
|---|---|---|
| Table I, related-work settings | `ledger/tableI_primary_evidence.csv` (primary-source pointers) | Qualitative evidence; absence claims remain conditional |
| Table II, data and splits | `splits/`, pinned protocols, `records/fresh_unlabelled_page_counts.json` | `base/tables/table_II.csv` |
| Tables III鈥揑V, static plans and frozen Q/QP/RR/mix | `snapshot/`, `repro/`, `records/figure_data/` | `base/tables/table_III.csv`, `table_IV.csv`; 154 manuscript-cell checks |
| Fig. 1(a), static/envelope/oracle/router | original four-static-plan records | `figures_generated/fig1_overview.png` |
| Fig. 1(b), lifecycle | same-process setup/warm study, historical OCR singleton | overview lifecycle panel; full curves in `base/figures/` |
| Fig. 2, architecture | `records/manuscript_R82_assets/` | exact PDF + editable draw.io, no synthetic measurements |
| Fig. 3(a鈥揻), static frontiers, both retrievers | quality and actual warm request records | `figures_generated/fig3_frontier.png` |
| Fig. 3(g鈥揾), candidate containment and recovery | `containment_groups.csv`, `repair_counts.csv`, worsening audit | same figure; new harm and aggravated existing harm remain distinct |
| Fig. 4(a鈥揹), router comparison/information/cost/actions | grouped paired statistics and complete-path records | `figures_generated/fig4_decision.png` |
| Fig. 5(a鈥揵), capacity and accounting | `records/021_snapshot/`, `scripts/replay_021_017.py` | `base/audit/`, `figures_generated/posthoc_diagnostic.pdf` |
| Cross-fitted screen / envelope optimism | `posthoc_20261109/run_screening.py` | `posthoc/screening/`, saved group/process bootstrap indices and draws |
| Learning curve at fixed cost weight | `posthoc_20261109/independent_cpu.py`, fixed subsets/seeds | `posthoc/independent/K17_kappa10_vs20.csv` |
| OCR concurrency and lifecycle sensitivity | archived page fingerprints and real CPU/wall observations | `posthoc/E5_analysis/`; no fresh OCR in CPU replay |
| HR text-source sensitivity / index footprint | legal Dev-only numerical control / 11 measured cells | `posthoc/` checks; Economics脳ColPali absent |
| Calibration sample-power limits | exact zero-loss bound, split metadata | `paper_values/`; **NOT_CERTIFIED** |
| Resident/streaming A/A negative results | two cohorts, queue/service records, fixed equivalence gate | `base/figures/`, historical summaries; no Serving speedup |
| Supplemental schedule experiment | one resident process, eight balanced blocks | `E6/`; old 34 ms gap not reproduced at its original magnitude |

The exhaustive panel/experiment/configuration map, including failures and missing
hardware paths, is [REPRODUCIBILITY_MATRIX.md](REPRODUCIBILITY_MATRIX.md).
The read-only manuscript occurrence inventory is `ledger/manuscript_R82_numbers.csv`.
It is an inventory, **not a claim that every prose token was independently verified**.

## From-scratch hardware route (separate from quick replay)

Read [docs/FULL_REPRODUCTION.md](docs/FULL_REPRODUCTION.md) and
[docs/DATA_AND_LICENSES.md](docs/DATA_AND_LICENSES.md) first. They distinguish
executable acquisition/preprocessing/smoke steps from archived experiment workers
that still need original-layout inputs and hardware validation.

```bash
python scripts/acquire_assets.py plan
# Example: pinned public metadata, stored OUTSIDE the repository:
python scripts/acquire_assets.py fetch --asset economics-docs \
  --destination ../official-economics-docs --accept-upstream-terms
python scripts/full_reproduction.py --plan
```

The original hardware is one NVIDIA RTX A6000 48 GB per job, driver 570.133.20,
CUDA 12.1 / PyTorch 2.5.1+cu121, Linux, and Tesseract 4.1.1 (English, psm3).
Observed package versions and original worker/configuration hashes are included.
Weights and indexes are never bundled. Some full-dataset GPU paths remain
**NOT_VERIFIED / MISSING**, explicitly listed in the matrix; a historical
successful host run is not a clean-checkout rerun. This task launches no GPU job
and trains no new router.

## Repository layout

* `config/`: immutable parameters, revisions, acquisition and manuscript locks.
* `data/`, `splits/`, `freeze/`: official acquisition recipes, IDs/groups, protocols.
* `scripts/`, `repro/`: portable CPU entries and original statistical algorithms.
* `records/`, `snapshot/`, `cost009/`: measured numerical evidence and failure records.
* `posthoc_20261109/`: versioned later controls, with original input/output hashes.
* `figures/`: reviewer plotting entry; no generated files written over source records.
* `execution_source/`, `source_archive/`: original hardware workers and supporting
  code; **archive presence alone does not imply portability**.
* `ledger/`, `validation/`, `docs/`: mapping, test receipts, limitations and history.

Historical directory names are retained because frozen scripts reference them.
They are indexed instead of destructively renamed or deduplicated. No unique
experiment or failure log was deleted. Older README/review material is historical;
this README and the matrix define the current audit scope.

## Interpretation and limitations

The original policy comparison has four static plans (FullV, BM-50, BM-100,
BM25). Post-hoc capacity/accounting controls have three actions (FullV, BM-100,
BM25). Their envelopes and cost cohorts are not interchangeable. Cross-fitted
costs are **recomposed from measured components (offline screening)**, not actual
new complete-path measurements; signed context-transfer residuals can make some
per-query estimates negative. The model/cost weight is not refitted within each
conditional bootstrap.

Biomedical resamples 27 source lectures and measurement processes. Economics has
one relevance-connected component despite five PDFs; its intervals condition on
that corpus and use the original fixed FullV denominator. Development analyses
are exploratory. Labels, repeated timings, query translations and resampling do
not create new independent evaluation units. There is no new K1 risk certificate
or validated Serving acceleration. RR-adapted is not the official RetrievalRouter.
Pretraining overlap is unknown. Setup and warm costs are paired only within their
own cohort; 70.22 ms and 36.22 ms are not interchangeable baselines.

## License and citation

Original software remains under [MIT](LICENSE), copyright 2026 Harbin Institute
of Technology. **This task does not change that license.** Dataset/model/source
terms are independent; see [THIRD_PARTY_NOTICES_EAB.md](THIRD_PARTY_NOTICES_EAB.md).
No weight, raw page/PDF, original question, OCR prose, full query鈥損age label map,
credential or sealed annotation is added. Cite the official ViDoRe V2/V3 and
ColPali/ColQwen2 works and original source notices; the paper bibliography is
audited in `ledger/` rather than replaced by an invented publication DOI.

See [MISSING_MATERIALS.md](MISSING_MATERIALS.md) and
[PUSH_REVIEW.md](PUSH_REVIEW.md) before approving any future publication.

## Additional CPU reconstruction with official annotations

The restored Economics/Plan B module recomputes 25 CSVs and 3 mechanism PNGs from
pinned official queries/qrels of the **already evaluated Biomedical/Economics
benchmarks**. It performs no GPU run or model training. Raw annotations and
generated case prose stay outside Git. This separate path needs network on first
use and explicit upstream-terms acknowledgment:

```sh
python scripts/reproduce_with_official_annotations.py --output ../mechanism-replay \
  --official-cache ../official-annotation-cache --accept-upstream-terms
```

Linux rehashes the cache even when transferred from an independently verified
official download. The actual Linux upstream timeout and Windows PNG differences
remain in receipts. This path never fetches sealed project labels.
