"""Portable IO adapter. Replays archived observations; never reports a new GPU run."""
from pathlib import Path
import json,csv,hashlib,datetime,os
import numpy as np
ROOT=Path(os.environ['MDROUTER_FULL_REPLAY_ROOT']).resolve();RUN='archived_numeric_replay';SEED=202610281100
PLANS=['Full-Visual','BM25-R50','BM25-R100','BM25'];INPUT={};SOUT=[];A=R=None
eco=os.environ.get('MDROUTER_REPLAY_STAGE')=='economics'
ART=ROOT/'artifacts/icde_eab_external_validation_013/monitor_001' if eco else ROOT/'generated_audit'
REPORT=ROOT/'reports/icde_eab_external_validation_013/monitor_001' if eco else ROOT/'generated_mechanisms'
def stamp():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(x):
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [clean(v) for v in x]
 if isinstance(x,float) and not np.isfinite(x):return None
 return x
def prose(p,s):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as f:f.write(s)
def write(p,d):prose(p,json.dumps(clean(d),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p,rows,fields=None):
 rows=list(rows);fields=fields or list(dict.fromkeys(k for r in rows for k in r));p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for row in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(list,dict,tuple,np.ndarray)) else clean(v) for k,v in row.items()})
def start(stage):
 global A,R
 A=ART/stage;R=REPORT/stage;A.mkdir(parents=True,exist_ok=False);R.mkdir(parents=True,exist_ok=False)
def load(path,role='ARCHIVED_RESULT'):
 p=Path(path);p=p if p.is_absolute() else ROOT/p
 s=str(p).lower()
 if any(t in s for t in ['/sealed/','pharma_qrels','b-l_qrels','eval_qrels','cal_qrels','/computer_science/','/esg/']):raise PermissionError('OUT_OF_SCOPE')
 INPUT[str(p.relative_to(ROOT))]={'sha256':sha(p),'role':role}
 if p.suffix=='.json':return json.loads(p.read_text())
 if p.suffix=='.csv':
  with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
 return p.read_text()
def finish(stage,status,facts,decision):
 write(R/'numeric_replay_receipt.json',{'archived_stage':stage,'archived_status':status,'replay_status':'CPU_REPLAY_COMPLETED','new_GPU_runs':0,'facts':facts,'scope':'Historical numerical reconstruction, not new execution/independent evaluation/certification'})
