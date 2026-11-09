# Review-only post-hoc supplement

This directory extends `icde27-eab-v1.1` (commit
`e9d4c2d14abca6003001caf8010da4f6b7321669`). It does not change the paper,
frozen experiment records, licenses, or existing tags. The assigned run label
`20261109` is not a claim about the execution date; timestamps are Beijing time.

The initial PLAN commit is `a5f31c26203638d385a02f940a1c26c3f2388ae9`.
The current review branch is `codex/posthoc-20261109`. There is no new tag or
public release in this round.

## CPU numerical replay

From a clean checkout containing the base artifact and this supplement:

```sh
python3.11 -m venv /path/to/new-isolated-env
/path/to/new-isolated-env/bin/pip install -r posthoc_20261109/requirements-cpu.txt
/path/to/new-isolated-env/bin/python posthoc_20261109/reproduce_posthoc.py --output /path/to/new-empty-replay
```

`--statistical-only` runs E1/E2/E3/K17/E4 without waiting for the system-record
supplement. The full replay additionally checks 15,240 archived OCR fingerprints,
recomputes conditional lifecycle crossings, checks HR quality arithmetic, and
checks the storage-inventory arithmetic, and redraws all seven supplement
figures (PNG bytes checked; PDF also regenerated). It does **not** repeat OCR, GPU work,
or original qrels evaluation. Saved draws and numerical CSVs are checked exactly;
NPZ comparisons use their arrays, not container timestamps. Receipts explicitly
distinguish archived numerical reconstruction from fresh system measurements.

To regenerate the new review plots and tables from the saved stage CSVs:

```sh
python posthoc_20261109/render_results.py --out /path/to/new-empty-review-directory
```

## Entry points and evidence

| Item | Script | Saved evidence |
|---|---|---|
| Original accounting/CI gates | `regression_gates.py` | `gates_001/` |
| Arbitrary-action accounting; grouped cross-fit | `accounting.py`, `run_screening.py` | `screening_001/`, `fit_trace_002/` |
| Original interval upper bounds; learning diagnostic; coarse hull | `independent_cpu.py` | `independent_001/` |
| OCR workers, frozen output fingerprints | `ocr_workers.py` | `portable_inputs_001/E5_metadata/` |
| Wall and child-CPU conditional crossings | `ocr_crossings.py` | `E5_analysis_001/` |
| HR text-source quality control | `hr_text_control.py` | `E7_HR_001/` |
| Visual asset/file inventory | `storage_inventory.py` | `E8_storage_001/` |
| Review-only tables and figures | `render_results.py` | `review_002/`, `RESULTS_SUMMARY.md` |

Fresh OCR/HR/inventory scripts require the legal private assets and frozen
runtime on the original experiment host. They are not steps in public CPU replay.
They use supplied project-root arguments, never download sealed data. Raw OCR
text and page images are deliberately absent from this supplement.

## Limitations that survive successful replay

- All new analyses are POSTHOC and NOT_CERTIFIED. The frozen risk contract and
  prior certificates are unchanged. Economics has one relevance-connected source
  component; family-based intervals are conditional on that corpus.
- New action-screening costs are **recomposed from measured components (offline
  screening)**. Signed archived execution-context differences are transferred;
  some query/process estimates are negative. They are retained, never clipped,
  and cannot be interpreted as physical time.
- Cross-fit intervals condition on the fitted fold kappas and LP weights. They
  do not include a refit within each bootstrap. Seed1–5 stability ranges are not
  confidence intervals and need not contain the separate main seed's estimate.
- OCR timing starts from prepared PNGs. The old 407.725-second measurement also
  included image preparation. Wall and CPU seconds are different resources.
- HR coverage is 40/40 of the frozen Dev workload and 40/318 of the English pool.
  There is no new full-ranking acquisition or independent HR evaluation.
- BM25 indexes were built in memory and not persisted. Their disk size and the
  visual-to-BM25 disk ratio are MISSING, not zero. Economics/ColPali is not built.
- No GPU reservation was confirmed; E6 and conditional new routed timings are
  NOT_RUN. A clean CPU replay does not remedy those missing measurements.

Metadata exports replace private server-root prefixes with placeholders. Source
hashes describe original inputs; the delivery MANIFEST describes exported files.
No model weights, pages, OCR prose, question text, full qrels, sealed labels, or
credentials are included. New public publication remains an author decision.
