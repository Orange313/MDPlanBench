from pathlib import Path
import csv,datetime,hashlib,json,sys,traceback,subprocess
import numpy as np
ROOT=Path('${PROJECT_ROOT}')
RUN='icde_eab_external_validation_013_monitor_001';PARENT='icde_eab_external_validation_013'
ART=ROOT/'artifacts'/PARENT/'monitor_001';REPORT=ROOT/'reports'/PARENT/'monitor_001'
STORAGE=Path('${ASSET_ROOT}/icde_eab_external_validation_013_resume_001')
SEED=202610281100;A=R=None;INPUT={};SOUT=[]
def stamp():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*2**20),b''):h.update(b)
 return h.hexdigest()
def clean(x):
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,float) and not np.isfinite(x):return None
 return x
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as f:json.dump(clean(v),f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def prose(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as f:f.write(v)
def table(p,rows,fields=None):
 rows=list(rows);fields=fields or list(dict.fromkeys(k for r in rows for k in r));p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(list,dict,tuple,np.ndarray)) else clean(v) for k,v in r.items()})
def denied(p):
 s=str(p).replace('\\','/').lower()
 return any(x in s for x in ['/sealed/','b-l_qrels','b-l_pool_queries','b_l_outcomes','final_test_queries','pharma_qrels.parquet','/prereg_v2_round_005/']) or ('esg_reports_human_labeled_v2' in s and s.endswith(('.parquet','.png','.jpg','.pt'))) or (any(x in s for x in ['computer_science','/vidore_v3_cs/']) and any(x in s for x in ['queries','qrels','outcomes'])) or (any(x in s for x in ['pharma','pharmaceutical']) and any(x in s for x in ['eval_qrels','cal_qrels','eval_outcomes','cal_outcomes','eval_queries','cal_queries']))
def protect(event,args):
 if event!='open' or not args or not isinstance(args[0],str):return
 mode=args[1] if len(args)>1 else ''
 if isinstance(mode,str) and any(x in mode for x in ['w','a','x']):return
 if denied(args[0]):raise PermissionError('SEALED_OR_LICENSE_BLOCKED_READ_REFUSED')
def start(s):
 global A,R
 A=ART/s;R=REPORT/s;A.mkdir(parents=True,exist_ok=False);R.mkdir(parents=True,exist_ok=False);sys.addaudithook(protect)
 write(A/'start.json',{'time_bj':stamp(),'run':RUN,'stage':s,'scope':'Economics publicdata audit; frozenmodels/no refit; ESGblocked; sealedreads0'})
 def fail(t,v,tb):
  if not (A/'failure.json').exists():write(A/'failure.json',{'time_bj':stamp(),'error':str(v),'traceback':''.join(traceback.format_exception(t,v,tb))})
  traceback.print_exception(t,v,tb)
 sys.excepthook=fail
def load(p,role='METADATA'):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 if denied(p):raise PermissionError('SEALED_OR_LICENSE_BLOCKED_READ_REFUSED')
 b=p.read_bytes();key=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p);INPUT[key]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'role':role}
 if A:
  with (A/'reads.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps({'time_bj':stamp(),'path':key,'role':role,'sha256':INPUT[key]['sha256']})+'\n')
 if p.suffix=='.json':return json.loads(b)
 if p.suffix=='.csv':return list(csv.DictReader(b.decode('utf-8-sig').splitlines()))
 return b.decode('utf8')
def register(p,role):
 p=Path(p);key=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p);INPUT[key]={'sha256':sha(p),'bytes':p.stat().st_size,'role':role}
 return p
def snapshot(s):
 from archive_code import run
 return run(ROOT,RUN,ART/('code_'+s))
def finish(stage,status,facts,decision):
 code=snapshot(stage)
 prose(R/'orange_entry.md',f'## {RUN} / {stage} / {stamp()}（北京时间）\n\n**结论**：{status}。{facts}\n\n**决策**：{decision}\n\n**阻塞/限制**：仅Economics许可范围；ESG LICENSE_BLOCKED。新K1 NOT_CERTIFIED；GPU空闲/可保留不由显存余量推断；CPU模拟不等于GPU通过。封存Cal/Eval、旧B-L/test/CS读取0，不改005、模型/参数/候选/58查询。无新push或CMT。\n\n**证据**：{R.relative_to(ROOT)}；code {code["code_snapshot_commit"]}；阶段manifest SHA见回执。\n')
 files=[p for base in [A,R] for p in base.rglob('*') if p.is_file() and p.name not in ['manifest.json','hash_inventory.json']]+[Path(p) for p in SOUT]
 inv={'outputs':{str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):sha(p) for p in files},'inputs':INPUT,'code':code['source_file_SHA256']}
 write(R/'hash_inventory.json',inv)
 m={'run_id':RUN,'parent_run':PARENT,'stage':stage,'time_bj':stamp(),'status':status,'facts':facts,'decision':decision,'code_commit':code['code_snapshot_commit'],'code_bundle_SHA256':code['bundle_SHA256'],'inventory_SHA256':sha(R/'hash_inventory.json'),'sealed_reads':0,'new_K1':'NOT_CERTIFIED'}
 write(R/'manifest.json',m);write(A/'manifest.json',m)
 print(json.dumps({**m,'manifest_SHA256':sha(R/'manifest.json')},ensure_ascii=False),flush=True)

PLANS=['Full-Visual','BM25-R50','BM25-R100','BM25']
