# Known R83 erratum and distribution clarifications

Publication with this disclosed definition erratum was explicitly approved by the author. No paper, frozen outcomes, models or intervals are changed.

## False-Safe threshold (Results, RQ3)

R83 describes False-Safe as choosing a cheaper plan with **positive regret**, but the reported **96.6% (Q)** and **88.1% (QP)** regret shares were computed using **r > 0.05**, not merely r > 0. With the positive-regret-only threshold the shares are 100% for both routers. The archived definition is `bad=(action != 'Full-Visual') and r > .05` in `source_archive/scripts/icde_final_gate_004/resident_analyze_002.py`.

The independent check in `scripts/verify_R83_number_map.py` reads the 45 Pharmaceuticals development query rows per router in `planb014_full/inputs/reports/icde_eab_main_006/X2/rebuild_002/all_per_query.csv`. Unrounded r>.05 shares are 96.63915649505253% and 88.08924818353047%. This is a definition mismatch, not a new experiment or a revised risk contract.

## Public-data boundary

R83 mentions internal query text records. Original query prose and complete relevance maps are intentionally **not distributed** in this artifact. Public records retain numerical outcomes and anonymous query/family/source identifiers. Obtain original queries/labels only from the pinned official sources under their terms.

## Evidence scope

Numeric replay of archived observations is separate from rechecking nDCG against original qrels and from rerunning GPU retrieval/timing. Economics intervals remain conditional on its single source component. Post-hoc component-recomposed costs are not measurements of newly executed complete paths. The three-action post-hoc envelope is distinct from the original four-static-plan envelope. No new K1 certificate or Serving speedup is claimed.
