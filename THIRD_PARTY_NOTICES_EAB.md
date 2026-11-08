# Third-party assets and code license scope

The MIT license applies to original MDRouter software only. Upstream libraries
remain under their own licenses and are installed by the environment recipe;
model weights, raw pages, PDFs, original questions and full relevance mappings
are not redistributed.

* ColQwen2-v1.0-merged: pinned revision
  `2c9a09bb37ed19b63eb94ae6c29bb4e76eb6e3c2`; source card describes Apache-2.0
  backbone / MIT adapter terms. No weight license is replaced by our MIT file.
* ColPali-v1.3: adapter revision
  `1b5c8929330df1a66de441a9b5409a878f0de5b0`, MIT adapter. Its
  `colpaligemma-3b-pt-448-base` checkpoint at
  `30ab955d073de4a91dc5a288e8c97226647e3e5a` has separate Gemma terms.
  Acceptance/access requirements remain the reproducer's responsibility.
* ViDoRe V2 Biomedical: revision
  `e82eb2f3e9f701688e6f3ba41fffad68c5b3b5fa`, CC-BY-NC-SA-4.0 per pinned
  card/license. Cite the ViDoRe benchmark and official source notices. Released
  numerical derivatives are for research under applicable noncommercial and
  attribution/share-alike conditions; this repository does not grant image rights.
* ViDoRe V2 Economics: revision
  `d4fba7cf3d620c42810d961435afcfaaa0678e8d`, dataset CC-BY-3.0; original World
  Bank reports use CC-BY-3.0-IGO with third-party artwork exceptions. Cite ViDoRe
  and original report sources. No source PDF/page or full label mapping is bundled.
* ViDoRe V3 development metadata: only split IDs, numeric features and observed
  metrics are added here. Obtain source pages/annotations from their official
  repositories and retain original attribution/third-party restrictions. Sharing
  a fixed corpus across query partitions does not imply document independence.
* OCR recipe: Tesseract 4.1.1, English, psm3. The historical cost 407.725 s was
  measured once. OCR page text is not republished in this release.

Historical endpoint checks are retained in `license_pin_verification_010.json`.
A missing standalone LICENSE endpoint is marked NOT_VERIFIED, even when a pinned
card was fetched; we do not turn an HTTP404 into a license grant. New checks and
their timestamps/hashes are retained under `validation/task31/` when available.
No claim of pretraining-data nonoverlap is made for pretrained retrievers.

The five comparison-paper PDFs used in Table I review are private reading
sources. Only short excerpts, primary URLs, page/section pointers and PDF hashes
are included in the review ledger; their PDFs are not redistributed.
