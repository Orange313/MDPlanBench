# Official data recipe

No raw source corpus, full qrels, original query examples, weights, or sealed
partition data are distributed here. `records/` contains numerical observations,
not a grant to redistribute original benchmark documents.

1. Read the pinned cards and terms referenced in `config/official_acquisition_lock.json`
   and `freeze/*_frozen_protocol.json`.
2. Inspect the existing recipe without downloading:
   `python acquire_public_assets.py plan --lock config/official_acquisition_lock.json`.
3. Biomedical fetch and model fetch require explicit upstream-terms acceptance;
   use the modes shown by `python acquire_public_assets.py --help`. Raw assets
   belong outside Git and are checked against official hashes before execution.
4. Economics uses the revision and four official parquet hashes in its frozen
   protocol. Resolve each `corpus/docs/queries/qrels/test-00000-of-00001.parquet`
   at the pinned Hugging Face dataset revision, verify SHA256, and keep them
   outside this repository. Do not substitute a mutable `main` dataset revision.
5. Development query IDs and family/source metadata are in `splits/`. Historical
   split builders are included as provenance; do not rerun them to change the
   frozen partition. The CPU replay reads none of the original annotation files.

Default CPU analysis is entirely offline. Any complete GPU benchmark rerun is a
separate, explicit operation under the official data/model conditions; it must
not access or repurpose this study's sealed Cal/Eval or historical test labels.
