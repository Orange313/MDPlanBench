# Organization and preservation policy
The new reviewer entry is README + REPRODUCIBILITY_MATRIX + scripts/reproduce_submission.py.
Configuration, assets, results, plots, ledgers and validation each have a named directory.
The prior README is preserved in docs/history/README_icde27-eab-v1.1.md.
No frozen source/result tree was renamed or deleted; their relative paths are part
of prior hash contracts. Duplicate historical copies are indexed in the inventory
instead of removed blindly. Temporary Python caches, environments, downloads and
generated replay workspaces remain outside tracked content or ignored.
The separate model/data license files are unchanged. Only path metadata in newly
exported records is redacted, with explicit original/exported hashes. No scientific
number, output ranking, allocation or model parameter is changed.
Publication requires new explicit user confirmation; no remote push/PR is performed.
