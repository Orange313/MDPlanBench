import common as C
import prepare
import sys
import types
import numpy as np
import time

sys.path.insert(0,str(C.ROOT/"src"))
Fast,BM,features = prepare.feature_backend()
reports, timing = [],[]
codecs = {}
for dom in C.load(C.ART/"EX0/domains.json"):
    name=dom["domain"]
    data=C.load(C.ART/("EX0/"+name+".npz"))
    texts={int(k):v for k,v in dom["query_text"].items()}
    if name in ("HR","Finance","Industrial"):
        queries=C.load(f"artifacts/splits/query_generalization_002/{dom['raw_domain']}/dev_queries.json")
        texts={int(q["query_id"]):q["query"] for q in queries}
    pages=C.load(dom["index"]+"/pages.json")
    encoder=Fast()
    encoder.fit_corpus([types.SimpleNamespace(searchable_text=p["markdown"] or "") for p in pages])
    bm=BM(pages)
    restored={"Q":[],"P":[]}
    for i,qid in enumerate(data["qids"]):
        qtime,stime,ptime=[],[],[]
        for repeat in range(5):
            start=time.perf_counter()
            q=encoder.transform(types.SimpleNamespace(question=texts[int(qid)]))
            q=np.array([q[k] for k in encoder.feature_names])
            qtime.append(time.perf_counter()-start)
            start=time.perf_counter()
            probe=bm.search(texts[int(qid)])
            stime.append(time.perf_counter()-start)
            start=time.perf_counter()
            p=features(bm,texts[int(qid)],*probe)
            ptime.append(time.perf_counter()-start)
        for field,actual in (("Q",q),("P",p)):
            expected=data[field][i]
            raw=np.array_equal(actual,expected)
            round32=np.array_equal(actual.astype(np.float32).astype(expected.dtype),expected)
            reports.append(dict(domain=name,query_id=int(qid),field=field,
                expected_dtype=str(expected.dtype),max_abs_difference=np.max(np.abs(actual-expected)),
                raw_exact=raw,float32_roundtrip_exact=round32,
                status="PASS" if raw or round32 else "FAIL"))
            restored[field].append("raw" if raw else "float32_roundtrip" if round32 else "FAIL")
        timing.append(dict(domain=name,query_id=int(qid),Q_wall_s=qtime,BM_search_s=stime,Pstats_s=ptime))
    codecs[name]={field:("raw" if all(x=="raw" for x in modes) else "float32_roundtrip"
                         if "FAIL" not in modes else "FAIL") for field,modes in restored.items()}
C.table(C.REPORT/"EX0/feature_precision_audit.csv",reports)
C.table(C.REPORT/"EX0/fresh_CPU_feature_timings.csv",timing)
C.write(C.ART/"EX0/cache_precision_codecs.json",codecs)
print(codecs,flush=True)
assert all(x["status"]=="PASS" for x in reports)
