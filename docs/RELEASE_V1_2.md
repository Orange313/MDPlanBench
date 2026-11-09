# ICDE EAB v1.2 release review

Target branch: `codex/icde-eab-reproducibility-20261109`.
Annotated tag: `icde27-eab-v1.2`; paper R83. No main merge, force push, license edit or repository visibility change is authorized or performed.

Retains posthoc_20261109, preliminary BM-200/dense/hybrid diagnostics, negative results and original recorded outcomes. Raw pages, original questions/qrels, OCR text, page embeddings, BM25 indexes and pretrained weights are excluded from the release tree. Models used for saved small-router inference are numerical parameters, not restricted retriever weights. Scientific plots are included as results.

Privacy cleanup removes the two legacy compressed original-question maps (metadata-only distribution override, same 160 grouping IDs) and four non-scientific author/contact audit rows across two old inventories. Numeric records are unchanged. No new original-code or third-party license is introduced. Root LICENSE is the existing MIT grant; dataset/model terms remain independent.

Prior commits and existing public history are retained as requested. Exclusion/redaction describes this release tree; it is not a claim that old Git history or previously published artifacts have been purged. Original experiment/provenance hashes remain archived. No file larger than 50 MB is required in this tree, so no large-file Release attachment is planned.

Before publication, inspect `validation/release_v1_2/`, run the root manifest verifier and all CPU replay stages from a clean checkout. Unauthenticated clone and tag-page checks are additionally required after publication. Full GPU retrieval/Serving and independent qrels revalidation remain separate unexecuted paths, not implied by numerical replay success.
