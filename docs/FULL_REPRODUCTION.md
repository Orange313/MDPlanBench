# Hardware reproduction: scope and gates

This is a historical-design rerun, not a new blind benchmark or certificate.
The offline route is fully separate and never imports CUDA. Do not train Q/QP,
select a new benchmark, change cost weights, risk budgets, scoring precision or
action catalogs in order to make a rerun agree.

## Environment and assets

The observed original environment is `env/historical_gpu_environment.json`;
`env/requirements-gpu-observed.txt` records exact observed packages. This GPU
environment has **not** been newly installed in this task. Base-model terms may
require an official Hugging Face login; never commit credentials.

```sh
python -m pip install torch==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
python -m pip install -r env/requirements-gpu-observed.txt
python scripts/acquire_assets.py plan
```

Use pinned model revisions from `config/acquisition_registry.json`, not mutable
`main`. Model snapshots must be outside Git. The ColPali adapter and Gemma base
are separate assets. Official revision pins identify snapshots; consumed files
must additionally match the original model/index asset ledger. No LFS pointer is
used as a substitute for an accessible, licensed download.

For each dataset asset, `scripts/acquire_assets.py fetch --asset ID --destination
OUTSIDE_GIT --accept-upstream-terms --max-bytes BUDGET` verifies the exact SHA256.
The utility offers no mixed development-qrels download. Supply only separately
authorized Fit/Dev label views matching `splits/`; do not open sealed Cal/Eval,
old B-L/test/CS, or infer permission from a public dataset filename `test`.
Biomedical/Economics official public benchmark files are distinct from sealed
project partitions.

## Preprocessing and technical smoke

```sh
# Obtain the official OCR runtime/dependencies under their upstream terms.
OMP_THREAD_LIMIT=1 python prepare_ocr.py --corpus /external/corpus.parquet \
  --output /external/new-ocr --tesseract /external/tesseract-4.1.1/bin/tesseract
# ColPali: one fixed official query, 16 pages, no label read; not a paper experiment.
python minimal_gpu_sample.py --adapter /external/colpali-adapter \
  --base /external/colpali-gemma-base --corpus /external/biomedical-corpus.parquet \
  --queries /external/biomedical-queries.parquet --ocr /external/new-ocr/pages.json \
  --gpu GPU_ID --output /external/new-smoke
```

OCR text is not distributed. The original historical OCR timing includes page
preparation; later worker-concurrency timing starts at prepared PNGs. These are
different boundaries. Runtime hash manifests are in `config/ocr_runtime_lock.json`.
Do not replace a measured cost with zero when an asset is missing.

## Full experiment workers

`python scripts/full_reproduction.py --plan` lists the actual archived workers,
their configuration/data dependencies and unverified boundaries. It does not
schedule them. `--check --asset-root PATH --output NEW_DIR` verifies local asset
presence without loading CUDA or opening labels. A generic one-command full
six-corpus rerun is currently **MISSING**: original-layout metadata, Dev-only
annotation export and some index/model manifests must first be supplied and
the adapted worker validated. No success is inferred from source-file existence.

* Static/frozen policy main batch: `execution_source/t2_biomedical_exact_004.py`,
  `t3_colpali_expansion_004.py`, `t3_colpali_expansion_006.py`,
  `008_l1_biomedical_colpali_002.py`, and archived Economics worker. Three
  independent processes; three shuffled repeats; separate profiling.
* Capacity controls: `execution_source/research021/` and frozen predictions under
  `records/021_snapshot/`. Reuse predictions for replay; no new fitting here.
* Lifecycle setup: `source_archive/scripts/icde_eab_g2_setup_017/`, observed three
  processes per retriever with same-process warm timing; profile separate.
* Serving/A/A: `source_archive/scripts/icde_final_gate_004/` and
  `icde_eab_validation_005/`. Retain failed gates; no performance-superiority claim.
* OCR parallelism / schedule diagnosis: `posthoc_20261109/ocr_workers.py`,
  `E6_001/run_e6.py`. Original host layout required; CPU replay is portable.

Before ANY GPU job, check an unused A6000 three times, then keep ResourceGuard
active. Never terminate another user's process. Check planned disk/output needs
and retain all failures. Do not silently reduce corpus/query count to fit memory.
The historical HR rerun receipt covers 40 queries/1,110 pages and all 160 plan
rankings; its new timings differ from the old cohort and are retained separately.

## Cost and statistics

CPU commands in the top-level README regenerate all available scientific tables,
bootstrap samples, risk/cost envelopes, oracle/accounting decompositions,
lifecycle crossings and paper graphics. They do not remeasure CPU/GPU time.
Recorded original main paths, setup paths, post-hoc paths and reconstructed
counterfactual paths have separate cost labels. Frozen RandomMix and retrospective
optimal mixtures are different baselines. Keep negative results and conditional
Economics intervals. No new certification follows from replay success.

Fresh full measurements are NOT_RUN in this task. Do not allocate the original
reported total timings as a promised rerun duration: reference hardware, process
cache and shared-host conditions affect actual runtime. Historical evidence gives
an approximately eight-minute single-process schedule diagnosis and minutes per
1,016-page index build, plus model download/OCR; the complete multi-process,
multi-corpus suite is an hours-scale job requiring its own resource reservation.
