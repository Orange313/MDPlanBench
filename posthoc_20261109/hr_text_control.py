"""E7 only: existing HR full-page scores, new OCR text, CPU-only evaluation."""
from pathlib import Path
import argparse,ast,collections,concurrent.futures,hashlib,io,json,math,os,subprocess,sys,tempfile,time
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
wait=R/'posthoc_20261109/E5_ocr_001'
while not (wait/'completed.json').exists():
    if (wait/'failed.json').exists() or (wait/'NOT_RUN.json').exists():
        (O/'NOT_RUN.json').write_text(json.dumps(dict(status='NOT_RUN',reason='E5 OCR-engine validation failed/not run')))
        raise SystemExit(0)
    time.sleep(10)
e5=json.loads((wait/'completed.json').read_text())
if e5['mismatched_page_observations']:
    (O/'NOT_RUN.json').write_text(json.dumps(dict(status='NOT_RUN',reason='E5 frozen-text hash validation mismatched')))
    raise SystemExit(0)
inputs={}
def load(p):
    p=Path(p);b=p.read_bytes();inputs[str(p)]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    return json.loads(b)
queries=load(R/'artifacts/splits/query_generalization_002/vidore_v3_hr/dev_queries.json')
ids=sorted(int(q['query_id']) for q in queries);qtext={int(q['query_id']):q['query'] for q in queries}
rankpath=R/'artifacts/phase1/hr_pilot_004/rankings.jsonl';data=rankpath.read_bytes();inputs[str(rankpath)]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
ranks={}
for line in data.decode().splitlines():
    z=json.loads(line)
    if z['plan_id']=='V-Multi' and int(z['query_id']) in ids and len(z['page_ids'])==1110 and len(z['scores'])==1110:
        ranks[int(z['query_id'])]=[int(x) for x in z['page_ids']]
covered=sorted(set(ids)&set(ranks));coverage=dict(HR_Dev_queries=len(ids),covered_queries=len(covered),coverage_Dev=len(covered)/len(ids),
    HR_all_English_queries=318,coverage_all_English=len(covered)/318,covered_ids=covered,
    denominator='Primary: frozen HR Dev workload from common evaluation objects; full318-query pool reported separately')
(O/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
if coverage['coverage_Dev']<.5:
    (O/'NOT_RUN.json').write_text(json.dumps(dict(status='NOT_RUN',reason='Below50% of frozen HR Dev workload')))
    raise SystemExit(0)

from PIL import Image
import pyarrow.parquet as pq
sys.path.insert(0,str(R/'src'))
from aaber.common.text import tokenize
from mdrouter_v5.graded_metrics import stable_ranking,ndcg
official=load(R/'cache/indexes/hr_primary_001/pages.json');official.sort(key=lambda z:int(z['corpus_id']))
cfg=load(R/'configs/hr_pilot_sparse_004.json');assert cfg['bm25']['k1']==1.5 and cfg['bm25']['b']==.75
source=R/'scripts/cross_domain_four_plan_001.py';src=source.read_bytes();inputs[str(source)]={'sha256':hashlib.sha256(src).hexdigest(),'bytes':len(src)}
node=next(x for x in ast.parse(src).body if isinstance(x,ast.ClassDef) and x.name=='BM25')
envcode={'Counter':collections.Counter,'defaultdict':collections.defaultdict,'np':np,'math':math,
    'tokenize':tokenize,'stable_ranking':stable_ranking,'CFG':cfg}
exec(compile(ast.Module(body=[node],type_ignores=[]),'frozen_BM25','exec'),envcode);BM25=envcode['BM25']
runtime=R/'artifacts/icde_eab_independent_007/T1_preparation/ocr_001/runtime';exe=runtime/'usr/bin/tesseract'
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime/'usr/lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','')
env['TESSDATA_PREFIX']=str(runtime/'usr/share/tesseract-ocr/4.00/tessdata');env['OMP_THREAD_LIMIT']='1'
manifest=load(R/'cache/indexes/hr_primary_001/index_manifest.json');corpus=R/next(iter(manifest['source_corpus']))
assert corpus.exists();tmp=O/'tmp';tmp.mkdir();start=time.perf_counter();ocr=[]
def one(z):
    q=int(z['corpus_id']);image=z['image']['bytes'];fd,p=tempfile.mkstemp(prefix='page_',suffix='.png',dir=tmp)
    os.close(fd);p=Path(p)
    try:
        Image.open(io.BytesIO(image)).convert('RGB').save(p)
        x=subprocess.run([str(exe),str(p),'stdout','-l','eng','--psm','3'],env=env,capture_output=True,text=True)
        assert x.returncode==0,(q,x.stderr)
        return dict(corpus_id=q,markdown=x.stdout,sha256=hashlib.sha256(x.stdout.encode()).hexdigest())
    finally:
        assert p.resolve().parent==tmp.resolve();p.unlink(missing_ok=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for batch in pq.ParquetFile(corpus).iter_batches(columns=['corpus_id','image'],batch_size=8):
        ocr.extend(pool.map(one,batch.to_pylist()))
        if len(ocr)%80==0:print(json.dumps(dict(event='HR_OCR',pages=len(ocr),total=1110,elapsed_s=time.perf_counter()-start)),flush=True)
ocr.sort(key=lambda z:z['corpus_id']);assert len(ocr)==1110
with (O/'HR_ocr_pages.json').open('x',encoding='utf8') as f:json.dump(ocr,f,ensure_ascii=False)
(O/'HR_ocr_hashes.json').write_text(json.dumps({z['corpus_id']:z['sha256'] for z in ocr},indent=2)+'\n')
labels=load(R/'artifacts/splits/query_generalization_002/vidore_v3_hr/dev_qrels.json')
ql=collections.defaultdict(dict)
for z in labels:
    q=int(z['query_id']);assert q in ids
    ql[q][int(z['corpus_id'])]=int(z['score'])
results=[]
for kind,pages in [('official_markdown',official),('Tesseract411_eng_psm3',ocr)]:
    bm=BM25(pages)
    for q in covered:
        order,_=bm.search(qtext[q]);bmids=[bm.ids[i] for i in order]
        ref=ranks[q][:10];reference=ndcg(ref,ql[q]);candidate=set(bmids[:100]);rerank=[p for p in ranks[q] if p in candidate][:10]
        for plan,top in [('BM25',bmids[:10]),('BM25-R100',rerank)]:
            u=ndcg(top,ql[q]);results.append(dict(query_id=q,text_source=kind,plan=plan,nDCG10=u,
                reference_nDCG10=reference,r=max(reference-u,0),harm=max(reference-u,0)>1e-10,
                output_top10=json.dumps(top),scope='POSTHOC fixed HR Dev; frozen FullV score restriction; no new full ranks'))
import csv
with (O/'E7_per_query.csv').open('x',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
summary=[]
for kind in ['official_markdown','Tesseract411_eng_psm3']:
    for plan in ['BM25','BM25-R100']:
        z=[x for x in results if x['text_source']==kind and x['plan']==plan]
        summary.append(dict(text_source=kind,plan=plan,queries=len(z),mean_r=float(np.mean([x['r'] for x in z])),
            harm_rate=float(np.mean([x['harm'] for x in z])),mean_nDCG10=float(np.mean([x['nDCG10'] for x in z]))))
with (O/'E7_summary.csv').open('x',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
(O/'input_hashes.json').write_text(json.dumps(inputs,indent=2)+'\n')
(O/'completed.json').write_text(json.dumps(dict(status='DONE_ON_FROZEN_DEV_ONLY',coverage=coverage,summary=summary,
    OCR_wall_s=time.perf_counter()-start,OCR_workers=4,GPU_jobs=0,new_full_rankings=0,sealed_labels_read=0,
    qrels_scope='Isolated HR Dev-only qrels; no mixed raw qrels opened'),indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
