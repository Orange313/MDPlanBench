import common as C
import json
import collections
lookup={}
short=dict(zip(C.DOM[:3],["HR","Finance","Industrial"]))
for r in C.load("reports/icde_evidence_closure_003/E1/all_unprofiled_requests.csv"):
    if r["plan"] in C.PLANS:
        lookup[short[r["domain"]],int(r["query_id"]),r["plan"]]=json.loads(r["top10"])
for r in C.load("artifacts/icde_evidence_closure_003/E2/outcomes_001/request_rows.json"):
    lookup["Pharma",int(r["query_id"]),r["plan"]]=r["top10"]
for name,path in [("Biomedical","reports/icde_eab_independent_007/T2/process_0_001/quality.csv"),
                  ("Economics","reports/icde_eab_external_validation_013/monitor_001/auto2_attempt_001/process_00/quality.csv")]:
    for r in C.load(path):
        if r["method"] in C.PLANS:
            lookup[name,int(r["query_id"]),r["method"]]=json.loads(r["ranking"])
raw=[json.loads(x) for x in (C.ART/"GPU/process_03/partial.jsonl").read_text().splitlines()]
for proc in (6,8,9):
    raw.extend(C.load(C.ART/f"GPU/process_{proc:02d}/requests.csv"))
checks=[]
for r in raw:
    ranking=json.loads(r["ranking"]) if isinstance(r["ranking"],str) else r["ranking"]
    expected=lookup[r["domain"],int(r["query_id"]),r["action"]]
    checks.append(dict(domain=r["domain"],query_id=r["query_id"],process=r["process"],
        method=r["method"],repeat=r["repeat"],action=r["action"],
        exact_match=ranking==expected))
assert len(checks)==30942
C.table(C.REPORT/"delivery_001/ranking_parity.csv",checks)
C.write(C.REPORT/"delivery_001/ranking_parity.json",dict(
    n=len(checks),exact=sum(r["exact_match"] for r in checks),
    status="PASS" if all(r["exact_match"] for r in checks) else "FAIL",
    inputs=C.READS))
print("EXACT_RANKING_PARITY",sum(r["exact_match"] for r in checks),len(checks),flush=True)
assert all(r["exact_match"] for r in checks)
