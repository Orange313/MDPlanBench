# Data, model and software terms

MIT applies only to original code. Third-party data/model terms and page-level
exceptions survive MIT. The upstream recheck saves HTTP status, URL, timestamp
and hash; an accessible README is not legal clearance, and absent standalone
LICENSE files remain NOT_VERIFIED. No new permission was invented.

| Asset | Fixed source | Terms / redistribution boundary |
|---|---|---|
| ViDoRe V3 Finance, HR, Industrial, Pharmaceuticals | exact revisions and per-file hashes in `config/acquisition_registry.json` | dataset cards declare CC-BY-4.0; source-component/third-party restrictions must also be respected; no original images or full labels bundled |
| ViDoRe V2 Biomedical | `e82eb2f3e9f701688e6f3ba41fffad68c5b3b5fa` | pinned CC-BY-NC-SA-4.0 declaration; original lecture/image limitations retained; no page redistribution |
| ViDoRe V2 Economics | `d4fba7cf3d620c42810d961435afcfaaa0678e8d` | dataset CC-BY-3.0; original World Bank CC-BY-3.0-IGO, third-party art exceptions |
| ColQwen2 | `2c9a09bb37ed19b63eb94ae6c29bb4e76eb6e3c2` | official card/backbone/adapter terms separately; weights excluded |
| ColPali adapter | `1b5c8929330df1a66de441a9b5409a878f0de5b0` | MIT adapter, does not relicense the base |
| ColPali Gemma base | `30ab955d073de4a91dc5a288e8c97226647e3e5a` | Gemma-specific official terms/access; weights excluded |
| Tesseract OCR | 4.1.1, English, psm3 | upstream software/runtime terms; raw OCR output excluded |
| Historical BGE dense audit | original archived config/source | official BAAI checkpoint terms; not a new primary plan |

Dataset/model revisions, consumed-file hashes and official acquisition scripts
are provided; a researcher must accept their applicable upstream terms. Data
acquisition tests here fetch only a small Economics documents metadata parquet,
not original query/page labels or images. Large downloads and gated weights are
NOT_RUN / NOT_VERIFIED, not PASS by inference.

Numerical records/derivatives keep applicable dataset attribution and research
restrictions; do not treat MIT as a grant for those records. This candidate does
not newly distribute query prose, OCR prose, source pages, full qrels, sealed
partitions, pretrained weights or paper PDFs. Sanitized path metadata has an
explicit before/after hash ledger. Original unredacted evidence remains private
and unchanged; nested historical manifests identify their original versions,
while the candidate root MANIFEST covers the exported bytes.

All repository URLs should resolve to official primary endpoints or the project
repository. Internal paths are replaced with placeholders in new metadata.
Negative-test address literals in historical source are test fixtures, not live
telemetry. No external analytics, tracking pixel, credentialed download URL or
callback is introduced. The candidate is local-only pending author approval.
