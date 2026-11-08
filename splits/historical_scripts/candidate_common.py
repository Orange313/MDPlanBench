"""Strict stage-specific inputs. Never load new BL/test/CS labels or queries."""
import pathlib,json,hashlib,datetime,csv,sys,traceback
import numpy as np
ROOT=pathlib.Path('${PROJECT_ROOT}');RUN='icde_main_experiment_001'
REPORT=ROOT/'reports'/RUN;ART=ROOT/'artifacts'/RUN;SEED=202610261600
DOMAINS=['vidore_v3_hr','vidore_v3_finance_en','vidore_v3_industrial'];NAMES=dict(zip(DOMAINS,['HR','Finance-EN','Industrial']))
INDEX=dict(zip(DOMAINS,['hr_primary_001','finance_primary_001','industrial_primary_003']))
FROZEN='reports/prereg_v2_round_004/preregistration_v2_freeze_candidate_005'
CAL='artifacts/prereg_v2_round_005/prereg_v2_round_005_calibration_report_003'
PRIMARY=CAL+'/primary.json';ATOMS=CAL+'/all_atoms.json'
DEV={d:f'artifacts/{"cross_domain_k1_001" if d==DOMAINS[1] else "cross_domain_k1_resume_001"}/development_analysis_001/{d}/counterfactual_complete.json' for d in DOMAINS}
STAGE=None;OUT=None;AUDIT=None;INPUTS={};EXACT=set();CORPUS=set()
def stamp():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def clean(x):
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,float) and not np.isfinite(x):return None
 return x
def emit(record):
 if AUDIT is not None:
  with AUDIT.open('a',encoding='utf8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
def guard(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 mode=args[1]
 if not (mode is None or isinstance(mode,str) and 'r' in mode):return
 p=pathlib.Path(str(args[0])).absolute()
 try:rel=p.relative_to(ROOT).as_posix()
 except ValueError:return
 if rel.endswith('.jsonl') and rel.startswith('artifacts/'+RUN+'/'):return
 bad=any(t in rel for t in ['B-L_pool_queries','final_test_queries','test_qrels','B-L_qrels','B_L_outcomes','/sealed/','/vidore_v3_cs/'])
 local=rel.startswith('scripts/'+RUN+'/') or rel.startswith('reports/'+RUN+'/') or rel.startswith('artifacts/'+RUN+'/')
 libraries=rel.startswith('.venv/') or rel.startswith('cache/report_dependencies/') or rel.startswith('scripts/') or rel.startswith('src/')
 allowed=local or libraries or rel in EXACT or rel in CORPUS
 if bad or not allowed:
  emit({'time_bj':stamp(),'event':'DENIED_READ','path':rel,'stage':STAGE});raise PermissionError('stage input fence: '+rel)
 if not libraries:emit({'time_bj':stamp(),'event':'READ','path':rel,'stage':STAGE,'role':'UNLABELED_SHARED_CORPUS' if rel in CORPUS else 'ALLOWLISTED_METADATA_OR_RESULTS'})
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def register(p):
 p=pathlib.Path(p);rel=str(p.relative_to(ROOT));INPUTS[rel]=sha(p);return p
def read(p):return json.loads(register(p).read_text())
def text(p):return register(p).read_text()
def write(p,data):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as f:json.dump(clean(data),f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def prose(p,s):
 with pathlib.Path(p).open('x',encoding='utf8') as f:f.write(s)
def table(p,rows):
 cols=list(dict.fromkeys(k for r in rows for k in r))
 with pathlib.Path(p).open('x',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(list,dict,np.ndarray)) else clean(v) for k,v in r.items()})
def mdtable(cols,rows):return '|'+ '|'.join(cols)+'|\n|'+ '|'.join(['---']*len(cols))+'|\n'+''.join('|'+ '|'.join(str(v) for v in row)+'|\n' for row in rows)+'\n'
def start(stage,suffix,extra=()):
 global STAGE,OUT,AUDIT,EXACT
 STAGE=stage;REPORT.mkdir(parents=True,exist_ok=True);ART.mkdir(parents=True,exist_ok=True)
 OUT=ART/(RUN+'_'+suffix);OUT.mkdir(exist_ok=False);AUDIT=OUT/'read_audit.jsonl';AUDIT.touch(exist_ok=False)
 EXACT=set(extra);sys.addaudithook(guard)
 def fail(kind,value,tb):
  failure={'time_bj':stamp(),'status':'FAIL','stage':STAGE,'exception':kind.__name__,'message':str(value),'traceback':''.join(traceback.format_exception(kind,value,tb))}
  write(OUT/'failure.json',failure);traceback.print_exception(kind,value,tb)
 sys.excepthook=fail
 return OUT
def finish(status,extra=None):
 files={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='read_audit.jsonl'}
 audit_hash=sha(AUDIT)
 write(OUT/'manifest.json',{'run_id':OUT.name,'stage':STAGE,'time_bj':stamp(),'status':status,'inputs':INPUTS,'outputs':files,
  'code_SHA256':sha(pathlib.Path(sys.argv[0])),'common_SHA256':sha(pathlib.Path(__file__)),
  'read_audit_creation_SHA256':audit_hash,'seed':SEED,'new_B_L_raw_reads':0,'test_query_or_label_reads':0,'CS_query_or_label_reads':0,
  '005_protocol_changed':False,'formal_new_certification':False,**(extra or {})})
 print(json.dumps({'stage':STAGE,'status':status,'run_id':OUT.name,'time_bj':stamp(),**(extra or {})}),flush=True)
