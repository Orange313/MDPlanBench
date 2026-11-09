"""Check the HR official-text control against its archived legal Dev risks."""
from pathlib import Path
import argparse,csv,json
import numpy as np
import accounting as C
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True)
ap.add_argument('--E7-input',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
d=C.read(a.project/'artifacts/icde_eab_review_strengthening_021/EX0/HR.npz')
pq=C.read(a.E7_input/'E7_per_query.csv');indices={int(q):i for i,q in enumerate(d['qids'])};checks=[]
for z in pq:
    if z['text_source']!='official_markdown':continue
    j={'BM25':3,'BM25-R100':2}[z['plan']];expected=float(d['Y'][indices[int(z['query_id'])],0,j])
    delta=float(z['r'])-expected
    checks.append(dict(query_id=z['query_id'],plan=z['plan'],archived_r=expected,reproduced_r=float(z['r']),
                       delta_r=delta,PASS=abs(delta)<1e-12))
assert len(checks)==80
C.csvsave(a.out/'E7_official_reference_gate.csv',checks)
ok=all(z['PASS'] for z in checks)
C.jsave(a.out/'gate.json',dict(PASS=ok,checks=len(checks),max_absolute_error=max(abs(z['delta_r']) for z in checks),
    qrels_read=False,interpretation='Official-text scorer regression only; OCR quality remains exploratory'))
C.jsave(a.out/'input_hashes.json',C.INPUTS)
print(json.dumps(dict(PASS=ok,checks=len(checks)),indent=2))
if not ok:raise SystemExit('Official-text scorer mismatch: no new HR comparison claim')
