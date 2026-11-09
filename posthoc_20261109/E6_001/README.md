# E6: resident FullV schedule diagnosis

This is a post-hoc system diagnostic, not new retrieval-quality evaluation,
certification, or a Serving benchmark. The original PLAN was committed before
GPU execution (`4838316b3e31f840c5124b05274c0b818b525d0d`). The author then
explicitly approved original global request shuffle and restoration of the
frozen in-memory BM25 object outside timing. The GPU/analysis implementation
was committed as `23659374ae697d11dcc78c534028f6b58c52e56e` before execution.

`measure_001/` and `measure_002/` are retained PRE-CUDA resource rejections;
`measure_003/` is the single actual GPU experiment. No measured run was retried
to improve a result. No page embeddings, OCR, router models or on-disk indexes
were rebuilt. Shared `.venv` and old scientific records were unchanged.

## Read results

- `E6_RESULTS.md`: requested results plus the postflight interpretation.
- `analysis_001/`: all numerical estimates, paired intervals and plots.
- `measure_003/requests.csv`: all16,640 measured requests,2560 FullV requests;
  legacy shuffle labels and actual chronological repeat order are separate.
- `measure_003/nvidia_smi.csv`: 1Hz clocks/temperature/power/utilization.
- `measure_003/resource_guard.json`: continuous/request-boundary checks.
- `preflight_001/`: old source/asset hashes, old timing cohorts, frozen outputs.
- `legacy_*_reference.py`: source references; do not run as standalone drivers.

## CPU reconstruction

In a new isolated Python3.11 environment with NumPy2.4.6 and Matplotlib3.10.7:

```sh
python replay_analysis.py --root /path/to/E6_001 --out /path/to/new-empty-output
```

This verifies five numerical CSVs, the paired bootstrap arrays, the analysis
summary, and two PNGs; PDFs are also regenerated. It never loads a model,
starts CUDA, or reads qrels. The original analytical fixture validation is
explicitly SYNTHETIC_ONLY and is not a measured result.

## Scientific limits

The CI resamples paired queries across eight fixed blocks, not independent
processes. Repeated requests do not increase the160 independent workload IDs.
Hardware telemetry is correspondence at1Hz, not proof of a clock mechanism.
The small new A−B difference must not replace the old70.22/36.22ms cohorts or
be described as explaining the original twofold difference. Models, precision,
batch size and seeds are fixed; no paper, LaTeX, bilingual draft or license was
edited. No GitHub push, new tag, or submission is part of this task.
