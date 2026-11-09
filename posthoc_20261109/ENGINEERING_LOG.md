# Engineering log

The first local headline-annotation command used the Windows default GBK text
decoder and failed before changing the report or exported hash inventory. The
scientific computation was unaffected. This explicit UTF-8 follow-up records
the limitations. A verbose Git whitespace check also treated standard CSV CRLF
as trailing whitespace; future checks recognize CR-at-EOL instead of rewriting
scientific CSV bytes. No prior commit was amended or forced.

The first fit-trace export (`fit_trace_001`) stopped while parsing the nonnumeric
`frozen20` reference label as a budget. That failed directory remains on the
experiment server. `export_fit_trace_v001.py` preserves the failed implementation;
the corrected parser exported `fit_trace_002`. Its 1,008 saved scientific points
exactly match the already-completed screening. No model, allocation, cost or
statistical parameter changed.

Portable replay adds path arguments and a public `repro/frontier_math.py` fallback
to the analysis scripts. It does not change the scientific definitions. Local
review copies of metadata replace private server-root prefixes with placeholders;
the original server records remain immutable. Source hashes still identify the
original inputs; the delivery manifest identifies the sanitized review copies.

The first scoped privacy scan stopped before creating any archive because a
historical metadata helper contained a literal private server-root prefix. The
helper now uses a generic root pattern. No original record or scientific value
changed; the failed scan receipt is retained outside the review branch. This
branch is still local and was never pushed, so no public history was rewritten.

`review_001` rendering stopped before drawing because the archive gate files were
still in their original `reports/.../gates_001` directory on the server. The
unchanged gate files were copied into the supplement's expected location.
`review_002` is the fresh rendering directory; the failed directory is retained.
This repairs input placement and does not change any metric or statistical rule.

Windows final sealing stopped because the local Python lacked the optional
`tzdata` database. The two partial review files are retained under
`finalization_failed_001/`; no previous scientific output was overwritten.
Packaging/sealing now uses the explicitly requested UTC+08:00 offset without
an external time-zone database. Scientific replay was already complete on Linux;
this changes only packaging timestamp portability.
