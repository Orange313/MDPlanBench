# Data Availability export — local review, not published

## PASS: fixed inputs and omission policy

The README Data Availability section precedes Reproduction / Numeric Replay.
Six dataset IDs/revisions and26 distinct SHA256-pinned upstream files are read
from the experiment acquisition registry. Counts describe the manifest coverage,
not every file in the upstream repositories.

## Correction to the previous review package

The earlier ZIP contained two compressed copies of the160-row Biomedical family
map, including the original `query` column. The new release tree excludes both
compressed files (320 question rows /160 distinct questions). Original source
copies are retained outside this worktree; older release commits and ZIPs are
not overwritten or history-rewritten.

A metadata-only160-row family/source mapping replaces that input for CPU replay.
All query IDs, family IDs, source groups and numeric results are unchanged.
`config/distribution_input_overrides.json` records the original and exported
hashes. Original `input_manifest.json` and all golden numerical hashes are kept
unchanged; the I/O adapter explicitly authenticates the metadata-only export.

## PASS: no raw corpus/page assets

The structured audit inspects CSV headers, JSON/JSONL, compressed gzip contents
and NPZ arrays. No raw questions, full qrels, pages, OCR text, page embeddings or
retrieval-index payloads remain in the exported tree. Scientific-result plots
and author diagrams are retained;39 small NPZ files are numerical query-feature,
outcome or bootstrap records, not page embeddings. No pretrained visual weights
are included. Failure receipts before sanitization are kept as findings/counts,
without reproducing the original question text.

## PASS: numerical regression

The actual Windows CPU reconstruction passed in63.73s after the metadata export:
42 original numerical CSVs plus14 table outputs,48,405 independent checks over
70,747 values,zero numeric differences. Original figure-data / snapshot outcome
values, risk parameters, model settings and licenses are unchanged.

An initial Windows output path exceeded the platform path-length limit after
30+8 numeric CSVs passed; the failed output is retained privately. Retrying at a
shorter fresh path passed. No expected value or bootstrap rule was adjusted.

## Explicitly unverified

The independent all-prose-numbers audit of manuscript R83 is not completed by
this task. The README therefore claims only the audited R82 coverage of Tables
III–IV and numerical inputs to Figs.3–5, using per-query and frozen derived result
tables. It does not claim all numbers in the paper can be recomputed.
From-scratch hardware portability and upstream standalone-license limitations
remain as stated in MISSING_MATERIALS.md.

No paper/LaTeX, frozen numerical result, original provenance manifest or license
was modified. No GPU job, new training, public push or PR was performed.
