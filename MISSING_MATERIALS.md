# Remaining materials and unverified steps

The frozen-record **numerical** route passes on Linux. This is not an assertion
that the entire six-corpus hardware study has been independently rerun.

## Intentionally not distributed (not missing experimental evidence)

| Status | Omitted asset | Acquisition or regeneration |
|---|---|---|
| INTENTIONALLY_NOT_DISTRIBUTED | Original ViDoRe page images/PDFs, original questions and raw relevance annotation files | Obtain the six pinned datasets under the original terms; exact IDs, revisions and SHA256-pinned file counts are in README Data Availability and `config/acquisition_registry.json` |
| INTENTIONALLY_NOT_DISTRIBUTED | ColQwen2/ColPali page embeddings | Original index-building code in `execution_source/t2_biomedical_exact_004.py` and `execution_source/008_l1_biomedical_colpali_002.py`; fresh hardware portability remains a separate unverified step |
| INTENTIONALLY_NOT_DISTRIBUTED | Tesseract OCR page text | `prepare_ocr.py`, pinned English/psm3 runtime; numerical timing/fingerprint records remain included |
| INTENTIONALLY_NOT_DISTRIBUTED | BM25 indexes | Rebuilt in memory by the original BM25/Engine code; no persisted original BM25 index artifact existed |
| INTENTIONALLY_NOT_DISTRIBUTED | Large pretrained retriever weights | Official pinned model revisions and separate upstream/base-model terms; no weights bundled |
| INTENTIONALLY_SEALED | Project Cal/Eval, historical B-L/test/CS label partitions | Not accessed, not bundled, and not required by the offline numerical replay |

The two old compressed Biomedical query-family maps contained original question
text. They are excluded from this candidate and replaced by
`splits/biomedical_groups_metadata_only.csv`. Original and exported hashes are in
`config/distribution_input_overrides.json`; all 160 query IDs, families and source
groups are unchanged. Original experiment files and earlier review versions are
preserved outside the new distribution. This is a distribution-only metadata
export, not a change to frozen results or original provenance manifests.

## Genuine gaps and unverified steps

| Status | Material / gap | Available now | Required next |
|---|---|---|---|
| MISSING | One portable from-scratch orchestrator for all domains/retrievers | exact source workers, configs, model revisions, original records; concrete Economics workspace preparer; HR/ColPali smoke recipes | adapt original-layout manifests/Dev-only input views; validate each worker under one controlled GPU reservation before claiming end-to-end portability |
| NOT_RUN | Fresh full GPU quality/timing/setup/Serving/OCR suites | original logs, separate measured cohorts and replay | separate authorization/resource plan; do not relabel CPU replay as hardware reproduction |
| CONDITIONAL | Legal development label-view reconstruction procedure | frozen Fit/Dev IDs and numerical supervision features; original labels intentionally not distributed | supply/reconstruct only authorized Fit/Dev views for a from-scratch rerun; no mixed qrels download opening Cal/Eval/B-L/test/CS |
| NOT_VERIFIED | Three active PNGs' exact current layout regeneration | exact author assets + underlying numerical CSVs + existing plot scripts | recover final author rendering settings/crop pipeline; keep science arrays unchanged |
| NOT_VERIFIED | Nine standalone upstream LICENSE endpoints | nine pinned README bytes verified; declared terms/primary notices archived | missing404/license endpoint is not a permission grant; check source-specific restrictions and Gemma access separately |
| NOT_VERIFIED | R83 prose numbers individually formula-mapped | the R82 audit inventories543 occurrences and verifies154 table cells +16 key tests /70,747 independent values | complete the separate line-by-line R83 audit before claiming all paper numbers are reproducible; current README states only verified R82 table/figure coverage |
| CONDITIONAL | Related-work absence/partial-reporting cells | original primary URLs, sections, short quotes and hashes | manual review; removed Adaptive-RAG row remains history only |
| NOT_RUN / NOT_MEASURED (original experiment) | Economics×ColPali evaluation and persisted-BM25 disk-size comparison |11 actual visual-index cells; BM25 rebuilt in memory | keep unexecuted evaluation and disk-size/ratio measurements absent, not0; omission of index payloads itself is intentional, not a missing release file |
| NOT_CERTIFIED | New formal risk guarantee and Serving speedup | sample-power audit; failed/repeated A/A evidence | remain negative/unsupported; replay is not a new certificate |
| BLOCKED_BY_USER_REVIEW | Publishing this candidate | local independent branch, commit/diff/manifest and validation | explicit approval required before any push, PR or publication |

Raw pages, OCR prose, original query cases, full relevance maps and large pretrained
weights are deliberately not added. Official acquisition links/revisions/hashes
are provided under separate terms. They are not replaced by fabricated fixtures.
