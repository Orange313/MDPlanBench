"""One frozen HR domain, official Dev-only label view, cached index, GPU5.
Execute the already public static-plan source unchanged with isolated outputs.
No training, new policy, index build, or sealed data access.
"""
import pathlib,sys,types,json,csv,hashlib,datetime,os
import numpy as np
P=pathlib.Path(__file__).resolve().parents[1]
ROOT=pathlib.Path(os.environ['MDROUTER_ROOT'])
OUT=pathlib.Path(sys.argv[1]).resolve();GPU=int(sys.argv[2]);OUT.mkdir(exist_ok=False)
C=types.ModuleType('common');C.ROOT=ROOT;C.RUN='icde_eab_independent_007';C.SEED=202610281100
C.A=OUT/'artifacts';C.R=OUT/'reports';C.A.mkdir();C.R.mkdir();reads=[]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def write(p,x):
 p=pathlib.Path(p);assert p.is_relative_to(OUT),p
 with p.open('x') as f:json.dump(x,f,indent=2,default=lambda z:z.tolist() if hasattr(z,'tolist') else str(z))
def load(p,role='EXISTING_INPUT'):
 p=pathlib.Path(p);p=p if p.is_absolute() else ROOT/p
 if 'qrels' in p.name:assert p.name=='dev_qrels.json' and 'vidore_v3_hr' in str(p),p
 assert not any(x in str(p) for x in ['B-L_pool_queries','final_test_queries','test_qrels','/vidore_v3_cs/']),p
 if p==ROOT/'scripts/cross_domain_four_plan_001.py':p=P/'execution_source/cross_domain_four_plan_001.py'
 b=p.read_bytes();reads.append(dict(path=str(p),role=role,sha256=hashlib.sha256(b).hexdigest()))
 return json.loads(b) if p.suffix=='.json' else b.decode('utf8')
def start(stage):write(OUT/'start.json',dict(stage=stage,validation='FULL_HR_FROZEN_PLAN_REPRODUCTION',time_bj=stamp(),GPU=GPU,proc=2,seed=C.SEED))
def table(p,rows):
 p=pathlib.Path(p);assert p.is_relative_to(OUT),p
 keys=list(dict.fromkeys(k for x in rows for k in x))
 with p.open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in x.items()} for x in rows)
C.sha=sha;C.stamp=stamp;C.load=load;C.write=write;C.table=table;C.start=start;sys.modules['common']=C
sys.path.insert(0,str(P/'execution_source'));sys.path.insert(0,str(P/'execution_source/src'))
# Pin imported helpers to the clean checkout before historical code adds asset root/src.
import mdrouter_v5.gpu_accounting,mdrouter_v5.graded_metrics,aaber.common.text
source=P/'execution_source/t3_colpali_expansion_004.py'
sys.argv=[str(source),str(GPU),'vidore_v3_hr','2']
try:
 exec(compile(source.read_text(),str(source),'exec'),dict(__name__='__main__',__file__=str(source)))
 write(OUT/'read_audit.json',dict(reads=reads,sealed_reads=0,Dev_qrels_only=True,source_sha256=sha(source),source_commit='e971def8e2c2f0278a272105e9016fe1d473a5d5',new_source_or_model_selection=False))
except Exception as e:
 write(OUT/'failure.json',dict(type=type(e).__name__,message=str(e),time_bj=stamp(),sealed_reads=0));raise
