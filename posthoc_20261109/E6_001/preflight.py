"""CPU-only frozen-source/asset audit. Never evaluates queries or opens qrels."""
from pathlib import Path
import argparse,ast,csv,hashlib,json,shutil,subprocess
from datetime import datetime,timezone,timedelta
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False);inputs={}
def stamp():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(rel):
 p=R/rel;inputs[rel]={'sha256':sha(p),'bytes':p.stat().st_size}
 if p.suffix=='.json':return json.loads(p.read_text())
 if p.suffix=='.csv':return list(csv.DictReader(p.open(newline='',encoding='utf-8-sig')))
 return p.read_text()
def save(name,x):(O/name).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
sources=['scripts/icde_eab_independent_007/t2_biomedical_exact_004.py','scripts/icde_eab_independent_007/engine_exact_004.py',
 'scripts/icde_eab_independent_007/common.py','scripts/icde_eab_independent_007/learning_base_001.py',
 'scripts/icde_eab_g2_setup_017/worker.py','scripts/icde_eab_g2_setup_017/common.py',
 'scripts/cross_domain_four_plan_001.py','src/mdrouter_v5/gpu_accounting.py',
 'src/aaber/router/fast_query_router.py','src/mdrouter_v5/graded_metrics.py']
for p in sources:read(p)
protocol=read('artifacts/icde_eab_independent_007/T1/biomedical_frozen_protocol.json')
assert len(protocol['query_ids'])==160 and len(set(protocol['query_ids']))==160
checks=[]
for p,h in protocol['code_SHA256'].items():
 actual=sha(R/p);checks.append(dict(path=p,expected=h,actual=actual,PASS=actual==h))
 assert actual==h,('FROZEN_CODE_CHANGED',p)
model=read('manifests/hr_models_verified.json')['visual']
for z in model['files']:
 p=Path(z['path']);actual=sha(p);assert actual==z['sha256'],('MODEL_CHANGED',p)
 inputs[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]={'sha256':actual,'bytes':p.stat().st_size}
index='cache/indexes/icde_eab_independent_007_biomedical_colqwen_001'
im=read(index+'/index_manifest.json');assert im['pages']==1016
for rel,h in im['files'].items():
 p=R/index/rel;actual=sha(p);assert actual==h,('INDEX_CHANGED',rel)
 inputs[str(p.relative_to(R))]={'sha256':actual,'bytes':p.stat().st_size}
frozen={};old=[];new=[]
for proc in range(3):
 quality=read(f'reports/icde_eab_independent_007/T2/process_{proc}_001/quality.csv')
 reference={(int(z['query_id']),z['method']):json.loads(z['ranking']) for z in quality}
 if proc==0:frozen=reference
 else:assert reference==frozen,('LEGACY_OUTPUT_PROCESS_DISAGREEMENT',proc)
 rows=read(f'reports/icde_eab_independent_007/T2/process_{proc}_001/requests.csv')
 old.append(dict(process=proc,FullV_ms=1000*sum(float(z['E2E_s']) for z in rows if z['method']=='Full-Visual')/480))
 setup=read(f'reports/icde_eab_g2_setup_017/repeat/ColQwen2_{proc+1:03d}/requests.csv')
 full=[z for z in setup if z['plan']=='Full-Visual'];assert len(full)==160
 assert all(json.loads(z['output_top10'])==frozen[int(z['query_id']),'Full-Visual'] for z in full)
 new.append(dict(process=proc+1,FullV_ms=1000*sum(float(z['E2E_s']) for z in full)/160))
model_files=['artifacts/icde_eab_independent_007/T0/locked_models.json','artifacts/icde_evidence_closure_003/E2/candidate_models.json']
for p in model_files:read(p)
qp=protocol['official_inputs']['queries'];read(qp['path']) if Path(qp['path']).suffix=='.json' else None
assert sha(R/qp['path'])==qp['sha256'];inputs[qp['path']]={'sha256':qp['sha256'],'bytes':(R/qp['path']).stat().st_size}
save('query_ids.json',protocol['query_ids'])
save('frozen_outputs.json',[dict(query_id=q,method=m,top10=v) for (q,m),v in sorted(frozen.items())])
save('input_hashes.json',inputs);save('source_checks.json',checks)
save('legacy_latency_cohorts.json',dict(main=old,setup=new,main_mean_ms=sum(x['FullV_ms'] for x in old)/3,setup_mean_ms=sum(x['FullV_ms'] for x in new)/3))
fact=dict(status='PASS_CPU_ASSET_AUDIT',time_beijing=stamp(),pages=1016,queries=160,frozen_outputs=len(frozen),
 model_repo=model['repo'],model_revision=model['revision'],index=index,free_bytes=shutil.disk_usage(R).free,
 index_or_model_rebuilt=False,qrels_reads=0,sealed_reads=0,new_GPU_jobs=0,
 main_worklist='[(q,m,k) for q in ids for m in methods for k in range(3)]; global shuffle',
 setup_worklist='[(q,p) for q in ids for p in PLANS]; global shuffle',
 BM25_persisted_index='NOT_PRESENT; author explicitly permits frozen in-memory initialization outside timing')
save('completed.json',fact);print(json.dumps(fact,indent=2),flush=True)
