# 013 Economics + 014 PlanB complete numeric extension — REVIEW CANDIDATE

This extension is NOT yet publicly hosted. Numerical reproduction is historical replay, not a new GPU evaluation, certification or Serving claim. No original pages, OCR text, query text, raw qrels, model weights or private resource traces are redistributed. Official queries/qrels are downloaded to a separate user-owned cache using pinned revisions and SHA256; use is subject to upstream licenses, including Biomedical noncommercial/share-alike and Economics attribution/third-party conditions. Do not publish generated query/source-page mappings or case text without a separate rights review.

## Linux CPU reproduction

```bash
python -m venv .venv-replay
. .venv-replay/bin/activate
pip install -r requirements-replay-lock.txt -r planb014_full/requirements-extra.txt
python planb014_full/reproduce_full.py --output /tmp/mdrouter-full-replay --official-cache /tmp/mdrouter-official-cache
```

Output paths must not exist. The command first replays the existing public parent38 CSV/five figure families and lifecycle4 CSV; then recomputes Biomedical source27/family157 paired intervals (2000 draws), Economics9 methods/all7 summaryCSV including conditional family53/process paired intervals and posthoc envelopes, and all18 PlanB scienceCSV/3 PNG. Candidate/source metadata include all pages and frozen BM25 candidate IDs, not raw graded qrels. All218 external and164 exposedDev queries remain. Economics5PDF connect into1sourcecomponent; source95CI NA. Raw timings are original measured complete paths, GPU separateprofile; no new timing. Statistics unchanged; only IO/hardware-private-trace access is adapted. Expected output hashes are compared byte-for-byte.

## Evidence boundary

FrozenRandomMix is the actual locked allocation. Outcome-fitted static envelopes and same-catalog fractional Oracle remain POSTHOC_DESCRIPTIVE, not independent deployed baselines. NewK1 NOT_CERTIFIED. No test/CS/PharmaCalEval access. 009setup must not be merged with007warm to imply causal speedup. Software copyright and downstream metadata rights still need author review; no MIT grant is made by this candidate.

## Full Economics execution recipe (NOT rerun in this CPU audit)

Read official source terms and obtain the unchanged ColQwen2 checkpoint through parent acquisition recipe; no weights ship here. Use the pinned GPU environment in parent environment.json; CPU replay environment is separate.

```bash
python planb014_full/acquire_economics_assets.py --destination /path/official_economics --accept-official-license-terms
python prepare_ocr.py --corpus /path/official_economics/corpus/test-00000-of-00001.parquet --output /path/new_ocr
python planb014_full/prepare_economics_workspace.py --output /path/new_gpu_workspace --assets /path/official_economics --ocr-pages /path/new_ocr/pages.json --colqwen2-snapshot /path/licensed_pinned_snapshot
```

The final command prepares a standalone workspace and prints three ordered process commands, with fixed58queryIDs/9methods/seed and checkpoints. It performs noCUDAcall. Original executed worker/engine source is archived unchanged; workspace relocation and original-protocol-status assertion are adapted for explicitly unblinded historical reproduction. Newcodehashlock is NOT the original frozenprotocol. ResourceGuard/3idlechecks remain and fullindexrequires30GiBreserve. Do not run on busy GPU. OCR exactness requires originalTesseract/engdata hashes; both quality and timing may depend on hardware/OCR. No new scientific result or fresh-GPU reproducibility has been claimed by this CPU task. All original counts/failures remain.
