import common as C
import json
from pathlib import Path
import subprocess

root=C.ART/"EX7"
public=root/"public_clone"
receipt=C.load(root/"replay_002/all38_receipt.json")
assert receipt["status"]=="PASS"
assert len(receipt["lifecycle010"])==4
assert all(row["identical"] for row in receipt["lifecycle010"])
sem=C.load(root/"figure_semantic_checks.json")
assert len(sem)==9
assert all(x["source_input_hashes_equal"] and x["text_values_equal"] for x in sem)
commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=public,text=True).strip()
matrix=[
dict(item="Public no-login clone",status="PASS",evidence="clean_clone_log.txt; git HEAD "+commit),
dict(item="Fresh Python3.11 environment + public lock",status="PASS",
     evidence="install_002.log; initial system ensurepip unavailable retained"),
dict(item="38 main numerical CSVs",status="PASS",evidence="replay_002/all38_receipt.json"),
dict(item="4 lifecycle CSVs",status="PASS_EXACT_HASH",evidence="replay_002/all38_receipt.json lifecycle010"),
dict(item="Current manuscript figure inputs and text",status="PASS_PRIVATE_REPLAY_ONLY",
     evidence="figure_semantic_checks.json; nine variants inputs and labels equal"),
dict(item="Current manuscript exact PNG bytes",status="NOT_IDENTICAL",
     evidence="paper_figure_hash_checks.csv; raster and trim dimensions differ"),
dict(item="Plot invocation from review source",status="REPAIR_CANDIDATE",
     evidence="export_bounds_repair_001.json; mkdir OUTPUT/qa; original clipping failure retained"),
dict(item="Current manuscript and 013-021 additions public",status="ARTIFACT_GAP",
     evidence="public git file tree has none of the current result directories"),
dict(item="New hardware experiments independently rerun",status="NOT_RUN",
     evidence="CPU replay only; public GPU acquisition paths require hardware and upstream assets"),
dict(item="Original software license",status="PENDING_RIGHTSHOLDER",
     evidence="LICENSE_PROPOSED.md only; no original-code license added"),
dict(item="Third-party terms",status="PARTIAL_ARCHIVED_VERIFICATION",
     evidence="THIRD_PARTY_NOTICES_010.md; license_pin_verification_010.json; retain NOT_VERIFIED entries"),
]
C.table(C.REPORT/"EX7/artifact_reproduction_matrix.csv",matrix)
C.prose(C.REPORT/"EX7/artifact_reproduction_matrix.md",
"""# EX7 independent reproduction

The public repository was cloned without stored Git credentials, at
"""+commit+""". A new Python 3.11 environment installed the public dependency lock.
The 38 primary CSV hashes and four lifecycle CSV hashes passed in 24.96 seconds,
excluding environment setup. This verifies archived numerical reconstruction.

The current R52 six linked graphics are not in that public revision. In the supplied
private source copy, the qa output directory must first exist. Its clipping guard
also checks the pre-export canvas although the renderer exports bbox_inches=tight.
A separate reviewed repair changes only the bounds check to the tight export extent.
All nine variants then render, and original input hashes and complete text-value lists
match. Raster dimensions differ by 0-2 pixels for most plots, and by 14 pixels in the
A/A plot height. Exact PNG byte reproduction is not registered as PASS.
The original sources, failed attempts, patch receipt and output hashes are retained.

EAB submission requires all artifacts needed for the paper through an openly accessible
URL. The current public numerical subset is reproducible, while the manuscript's
013-021 additions and current plot sources remain private. Overall public closure is
ARTIFACT_GAP until the author approves a complete licensed release.
Official reference, checked 2026-11-05
https://icde2027.github.io/cf-research-papers.html

No canonical LaTeX edit, public push or license change was performed.
""")
C.prose(C.REPORT/"EX7/figure_table_commands.md",
"""# Exact replay entry points

Public numerical tables
python -m venv NEW_ENV
NEW_ENV/bin/pip install -r public_clone/requirements-replay-lock.txt
NEW_ENV/bin/python public_clone/reproduce_all.py --output NEW_OUTPUT

Current private figures
python scripts/icde_eab_review_strengthening_021/replay_figures.py
This stages the source once, records the bounds-check repair and rerenders nine variants.
The six active R52 figure links and immutable hashes are in baseline/binding_and_revision_QA.json.
Current tables use frozen 016 CSVs and G2_setup017. EX0 claim_to_evidence.csv identifies
the separate underlying cohorts, supported claims, domain and sampling unit.

New review results
capacity.py fits and freezes with Fit81 only.
gpu_worker_004.py GPU PROCESS runs one matched resident process.
analyze.py reconstructs paired intervals from three completed processes per domain.
plot_results.py draws the three new review figures from generated CSVs.

GPU reconstruction needs local model weights and page indexes. Official revision/asset
paths are in the frozen prior manifests. These dependencies were not downloaded or
independently rebuilt by this CPU-only reproduction check.
""")
C.seal("EX7")
print("EX7",C.sha(C.REPORT/"EX7/manifest.json"),flush=True)
