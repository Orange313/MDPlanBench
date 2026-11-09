# Acceptance report — local review candidate, 2026-11-09

## Tested baseline

Public base `icde27-eab-v1.1` = `e9d4c2d14abca6003001caf8010da4f6b7321669`.
Initial private test commit `4057380601bf40c648d238fbd052b08198283e4d`;
strict successful Linux CPU pipeline commit
`384b46bba2136c89b50eb2e0be1b3f049e81be36`. Current manuscript is **R82**,
revision `34d15ab3-c937-4bf7-b5e8-d61e49000131`, tree
`c2803d51b7221a5d926ae85463cda1dbda2602bf548fc96c3373e7528cc97f08`.
The R74→R82 incremental audit confirms all154 table numbers and all active figure
bytes unchanged. The current wrapper reruns those checks under the R82 lock.

## Actual tests, separately scoped

| Test | Actual outcome | Evidence |
|---|---|---|
| New Windows Python3.11.14 environment, pinned packages | PASS installation | local audit log / `validation/reproducibility_20261109/` |
| Anonymous public-base Git clone, local candidate-bundle fetch, fresh clean clone | PASS; no remote candidate publication | Linux acceptance setup records |
| New Linux Python3.11.15 venv and lock installation | PASS; pyarrow added through same pinned extension lock | archived install/freeze receipt |
| Strict complete offline pipeline | PASS,80.98s wrapper | `linux/final_stage_003.json`, `linux/replay_003/submission_replay_receipt.json` |
| Main/older numerical CSV replay | PASS30+8+4 CSVs; no expected hash changed | base/legacy receipts and independent verification |
| Independent numeric audit | PASS48,405 checks /70,747 values;0 deltas | `linux/replay_003/base/audit/audit_summary.json` |
| Later post-hoc supplement | PASS75 files /7 PNGs; bootstrap arrays checked | `linux/replay_003/posthoc/replay_receipt.json` |
| E6 schedule reanalysis | PASS5 CSV+2NPZ+2PNG and summary | `linux/replay_003/E6/receipt.json` |
| Manuscript values | PASS154 table cells +16 explicit key checks | `paper_R82/paper_numeric_checks.csv` |
| Saved Ridge/LightGBM inference | PASS42 cells,2,674 query/model pairs; Linux max error0, Windows2.22e-16; actions exact | frozen-inference receipts |
| Earlier BM200/dense/hybrid audit | PASS84 point means,21 cells/119 queries/7,497 timings; intervals preserved | `earlier_audit/` |
| Pinned Economics documents metadata acquisition | PASS9,860bytes/SHA256 | `official_metadata_fetch.json` |
| Biomedical/Economics official annotations | PASS4 pinned files acquired on Windows, rehashed on Linux; no sealed data | original module's verified lock / mechanism receipt |
| Full Economics and Plan B CPU analysis | PASS25 scientific CSV+3PNG bytes on Linux,8.65s | `linux/mechanism_replay_003/full_replay_receipt.json` |
| New GPU/preprocessing/full-dataset reruns | NOT_RUN | explicitly outside this audit's execution scope |
| From-scratch complete six-corpus portability | MISSING / NOT_VERIFIED | `MISSING_MATERIALS.md`; no archival worker promoted to PASS |

## Failures retained, not rewritten as successes

1. Initial Windows replay stopped at privileged directory symlink creation.
   New I/O-only fallback copies identical directory bytes on WinError1314;
   statistics and expected SHA values unchanged. A later Windows base run passes.
2. Windows supplement/E6 and3 mechanism PNGs differ bytewise from Linux.
   All25 mechanism numerical CSVs match; the strict PNG failure remains FAIL.
   Linux's PNG and bootstrap-array checks pass. Windows is not a byte-identical
   graphical reference.
3. Initial Linux replay exhausted disk while expanding large original GPU traces.
   The trace archives remain untouched and SHA-verified. The numerical summary
   uses cost CSVs, so the I/O adapter skips only unconsumed `_GPU.json` scratch
   materialization. The same expected numerical outputs pass afterward.
4. One wrapper had Windows backslashes in asset metadata, so Linux could not
   copy final graphics even though all scientific stages passed. Relative paths
   were normalized and the whole wrapper passed in a fresh output.
5. Direct Linux official-annotation acquisition timed out. Those failed attempts
   remain recorded. The successful Linux mechanism replay used the separately
   verified Windows official bytes, rehashed under the original official lock.

## Graphics and numerical fidelity

R82 has4 active tables and5 active figures. Statistical plots regenerate from
real frozen CSVs. Exact current author graphic bytes and editable diagram are
archived separately under `records/manuscript_R82_assets/` and root MANIFEST.
The currently rendered Fig.1/3/4 PNG canvas sizes differ from the manuscript
assets (Windows observations:999×621 vs998×620;2101×1024 vs2099×961;
2084×985 vs2083×985). Their numerical arrays are verified, but their exact
current layout reconstruction is **NOT_VERIFIED**. The diagram is an exact
frozen export, not a newly generated empirical plot. The compact diagnostic PDF
matches the archived manuscript bytes in the Windows test.

## Integrity and boundaries

No original snapshot, frozen quality/cost CSV, original Q/QP model parameter,
split, risk budget, LICENSE or manuscript source was changed. New metadata path
redactions have original/exported hashes. Source-only workers, historical logs,
failed runs, negative results and unsupported claims remain distinguishable.
All installed versions, generated claims and statuses must be read at their
actual tested commit; later documentation/manifest commits do not imply another
GPU experiment. No push, PR, visibility change or CMT submission occurred.
