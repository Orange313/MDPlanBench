"""One resident process, preregistered E6 2x2 schedules. No qrels or new indexes."""
from pathlib import Path
import argparse,ast,collections,csv,hashlib,json,os,shutil,subprocess,sys,threading,time,traceback
from datetime import datetime,timezone,timedelta

ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--gpu',type=int,required=True);a=ap.parse_args()
R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
os.environ.update(CUDA_VISIBLE_DEVICES=str(a.gpu),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',
 OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false',TMPDIR=str(O/'tmp'))
(O/'tmp').mkdir()
def stamp():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def save(name,x):
 with (O/name).open('x',encoding='utf8') as f:json.dump(x,f,indent=2);f.write('\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def event(label,**x):
 with (O/'events.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(time_beijing=stamp(),event=label,**x))+'\n')
event('WORKER_START',pid=os.getpid(),gpu=a.gpu)
root=Path(__file__).resolve().parent;pre=root/'preflight_001'
pf=json.loads((pre/'completed.json').read_text());assert pf['status']=='PASS_CPU_ASSET_AUDIT'
locks=json.loads((pre/'input_hashes.json').read_text())
for rel,v in locks.items():
 p=R/rel;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],('PRE_GPU_ASSET_CHANGED',rel)
sys.path.insert(0,str(R/'scripts/icde_eab_independent_007'));sys.path.insert(0,str(R/'src'))
import common as C
C.A=O;C.R=O;assert C.ROOT==R
sys.addaudithook(C.protected)
# Stricter no-qrels boundary for this cost-only run, in addition to old sealed guard.
def no_labels(name,args):
 if name=='open' and args and isinstance(args[0],str):
  mode=args[1] if len(args)>1 else ''
  if not (isinstance(mode,str) and any(x in mode for x in ['w','a','x'])) and 'qrels' in args[0].lower():
   raise PermissionError('E6_COST_ONLY_QRELS_READ_REFUSED')
sys.addaudithook(no_labels)
idle=[]
for i in range(3):
 raw=subprocess.check_output(['nvidia-smi','-i',str(a.gpu),'--query-gpu=index,uuid,name,driver_version,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
 z=[s.strip() for s in raw.split(',')];apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
 foreign=[s for s in apps.splitlines() if s.split(',')[0].strip()==z[1]]
 mem=int(z[4].split()[0]);ok='RTX A6000' in z[2] and mem<128 and int(z[5].split()[0])==0 and not foreign
 if idle:ok=ok and mem==idle[0]['memory_MiB']
 idle.append(dict(time_beijing=stamp(),monotonic=time.perf_counter(),raw=raw,memory_MiB=mem,foreign_processes=foreign,PASS=ok))
 if not ok:
  save('three_idle_checks.json',idle);save('NOT_RUN.json',dict(status='NOT_RUN',reason='RESOURCE_BLOCKED_BEFORE_CUDA',time_beijing=stamp()));raise SystemExit(71)
 if i<2:time.sleep(10)
save('three_idle_checks.json',idle)
from mdrouter_v5.gpu_accounting import ResourceGuard
guard=ResourceGuard(a.gpu,O/'resource_guard.json',period=.1);window_start=time.monotonic();stop=threading.Event();aborting=threading.Event()
state={'phase':'initialization','block':0,'schedule':None};rows=[];blocks=[];written=0;write_lock=threading.RLock();telemetry_errors=[]
FIELDS=['block','schedule','sequence','query_id','method','repeat','legacy_repeat','action','start_time_beijing','start_monotonic','end_monotonic','E2E_s','CPU_process_s','CPU_thread_s','Q_wall_s','Probe_extra_wall_s','Probe_statistics_wall_s','planner_wall_s','selected_path_wall_s','Probe_reused','Probe_paid_before_FullV','output_sha256','FullV_top10_equal']
def flush_rows():
 global written
 with write_lock:
  snapshot=rows[written:]
  if not snapshot:return
  p=O/'requests.csv';fresh=not p.exists()
  with p.open('a',encoding='utf8',newline='') as f:
   w=csv.DictWriter(f,FIELDS)
   if fresh:w.writeheader()
   w.writerows(snapshot);f.flush()
  written+=len(snapshot)
def abort(reason):
 if aborting.is_set():return
 aborting.set();stop.set();flush_rows()
 try:save('abort.json',dict(status='PARTIAL',reason=reason,time_beijing=stamp(),state=state.copy(),completed_requests=len(rows),completed_blocks=blocks))
 except Exception:pass
 try:guard.close()
 except Exception:pass
 print(json.dumps(dict(event='ABORT_OWN_PROCESS',reason=reason)),flush=True);os._exit(72)
def watchdog():
 last_size=0.
 while not stop.wait(.05):
  if guard.foreign or guard.errors:abort('EXTERNAL_PROCESS_OR_RESOURCE_GUARD_ERROR')
  if telemetry_errors:abort('GPU_TELEMETRY_ERROR')
  if time.monotonic()-window_start>=7200:abort('TWO_HOUR_GPU_BUDGET_EXHAUSTED')
  if time.monotonic()-last_size>=5:
   if shutil.disk_usage(R).free<128*2**20:abort('DISK_FREE_BELOW_128MiB')
   if sum(p.stat().st_size for p in O.rglob('*') if p.is_file())>128*2**20:abort('OUTPUT_BUDGET_EXCEEDS_128MiB')
   last_size=time.monotonic()
def telemetry():
 fields=['time_beijing','monotonic','sample_start_monotonic','sample_end_monotonic','phase','block','schedule','SM_clock_MHz','memory_clock_MHz','temperature_C','power_W','GPU_util_pct','memory_util_pct','memory_used_MiB']
 target=time.monotonic()
 with (O/'nvidia_smi.csv').open('x',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fields);w.writeheader()
  while not stop.is_set():
   try:
    snapshot=state.copy();st=time.perf_counter();ts=stamp()
    v=subprocess.check_output(['nvidia-smi','-i',str(a.gpu),'--query-gpu=clocks.current.sm,clocks.current.memory,temperature.gpu,power.draw,utilization.gpu,utilization.memory,memory.used','--format=csv,noheader,nounits'],text=True,timeout=5).strip().split(',');en=time.perf_counter()
    def number(s):
     try:return float(s.strip())
     except ValueError:return None
    w.writerow(dict(time_beijing=ts,monotonic=(st+en)/2,sample_start_monotonic=st,sample_end_monotonic=en,
      phase=snapshot['phase'],block=snapshot['block'],schedule=snapshot['schedule'],**dict(zip(fields[7:],map(number,v)))));f.flush()
   except Exception as e:telemetry_errors.append(repr(e));return
   target+=1;stop.wait(max(0,target-time.monotonic()))
watch=threading.Thread(target=watchdog,daemon=True);poll=threading.Thread(target=telemetry,daemon=True);watch.start();poll.start()
try:
 import numpy as np,torch,pyarrow.parquet as pq
 import engine_exact_004 as E
 import learning_base_001 as L
 eng=E.Engine(pf['index'].split('/')[-1],guard);torch.cuda.synchronize()
 save('initialization.json',dict(time_beijing=stamp(),setup=eng.setup,model=pf['model_repo'],revision=pf['model_revision'],
  model_dtype=str(next(eng.model.parameters()).dtype),resident_passage_dtype=str(eng.passage.dtype),page_files_dtype='float16',batch_size=64,
  torch=torch.__version__,CUDA_runtime=torch.version.cuda,CPU_threads=torch.get_num_threads(),CPU_affinity=sorted(os.sched_getaffinity(0)),
  TF32_matmul=torch.backends.cuda.matmul.allow_tf32,index_built=False,BM25='author-approved in-memory initialization, outside request timing'))
 protocol=C.load('artifacts/icde_eab_independent_007/T1/biomedical_frozen_protocol.json','FROZEN_PROTOCOL_METADATA')
 qpath=R/protocol['official_inputs']['queries']['path'];assert sha(qpath)==protocol['official_inputs']['queries']['sha256']
 queries={int(z['query-id']):z['query'] for z in pq.read_table(qpath).to_pylist()};ids=protocol['query_ids'];assert sorted(queries)==sorted(ids) and len(ids)==160
 save('read_audit.json',dict(public_query_file=str(qpath.relative_to(R)),sha256=sha(qpath),query_count=160,qrels_reads=0,sealed_reads=0))
 frozen={(int(z['query_id']),z['method']):z['top10'] for z in json.loads((pre/'frozen_outputs.json').read_text())}
 locked=C.load('artifacts/icde_eab_independent_007/T0/locked_models.json','FROZEN_FIT81_MODELS');models={x['method']:x for x in locked}
 rr=C.load('artifacts/icde_evidence_closure_003/E2/candidate_models.json','FROZEN_MODEL_PARAMETERS_ONLY')
 for target in ['hard','soft']:models['RR_'+target]=next(x for x in rr if x['source']=='Pharma_only' and x['seed']==202610271130 and x['method']=='Q_'+target and x['kappa']==20)
 def unpack(m):
  z=[np.asarray(x) for x in m['model']];z[0]=z[0].astype(bool);return tuple(z)
 models={k:unpack(v) for k,v in models.items()};cvec=np.asarray(protocol['inherited_cost_vector']);catalog=np.asarray([0,2,3])
 costnorm=cvec/float(cvec[0]) if protocol['cost_vector_normalize_by_FullV'] else cvec
 source=R/'scripts/icde_eab_independent_007/t2_biomedical_exact_004.py'
 route_node=next(n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef) and n.name=='route')
 env=dict(C=C,np=np,eng=eng,queries=queries,models=models,L=L,E=E,catalog=catalog,costnorm=costnorm,protocol=protocol,time=time,hashlib=hashlib)
 exec(compile(ast.Module(body=[route_node],type_ignores=[]),str(source), 'exec'),env);route=env['route']
 methods=C.PLANS+['Q_regret','QP_regret','RandomMix','RR_hard','RR_soft'];seq=['A','B','A1','B3','B3','A1','B','A'];configs={'A':(methods,3),'B':(C.PLANS,1),'A1':(methods,1),'B3':(C.PLANS,3)}
 schedules=[]
 for bi,label in enumerate(seq,1):
  mm,n=configs[label];work=[(int(q),m,k) for q in ids for m in mm for k in range(n)];np.random.default_rng(20261109+bi).shuffle(work)
  schedules.append(work)
 save('schedule.json',dict(seed_base=20261109,block_index_base=1,blocks=[dict(block=i,schedule=s,seed=20261109+i,work=w) for i,(s,w) in enumerate(zip(seq,schedules),1)],route_AST_sha256=hashlib.sha256(ast.dump(route_node,include_attributes=False).encode()).hexdigest()))
 with torch.inference_mode():
  state.update(phase='warmup',block=0,schedule=None)
  for q in ids[:20]:
   for m in methods:
    guard.check();got,_=route(m,q);assert got==frozen[q,m],('WARMUP_OUTPUT_MISMATCH',q,m)
  torch.cuda.synchronize();event('WARMUP_COMPLETE',queries=20,requests=180)
  state.update(phase='correctness_gate')
  correct=[]
  for q in ids:
   guard.check();got,_=route('Full-Visual',q);torch.cuda.synchronize();ok=got==frozen[q,'Full-Visual']
   correct.append(dict(query_id=q,PASS=ok))
   if not ok:save('top10_gate.json',dict(PASS=False,query_id=q,actual=got,expected=frozen[q,'Full-Visual']));raise RuntimeError('FROZEN_FULLV_TOP10_MISMATCH')
  save('top10_gate.json',dict(PASS=True,queries=160,checks=correct));event('TOP10_GATE_PASS',queries=160)
  for bi,(label,work) in enumerate(zip(seq,schedules),1):
   state.update(phase='timed',block=bi,schedule=label);event('BLOCK_START',block=bi,schedule=label,requests=len(work));print(json.dumps(dict(event='BLOCK_START',block=bi,schedule=label,requests=len(work),time_beijing=stamp())),flush=True)
   bstart=time.perf_counter();start_stamp=stamp();seen=collections.Counter();block_rows=[]
   for wi,(q,m,k) in enumerate(work,1):
    guard.check();seen[q,m]+=1;repeat=seen[q,m];state.update(query_id=q,method=m,repeat=repeat)
    tstamp=stamp();torch.cuda.synchronize();st=time.perf_counter();ct=time.process_time();tt=time.thread_time()
    got,d=route(m,q);torch.cuda.synchronize();en=time.perf_counter();wall=en-st;cpu=time.process_time()-ct;thread=time.thread_time()-tt
    match=got==frozen[q,m]
    if not match:
     save('output_mismatch.json',dict(block=bi,query_id=q,method=m,actual=got,expected=frozen[q,m]));raise RuntimeError('FROZEN_OUTPUT_MISMATCH')
    row=dict(block=bi,schedule=label,sequence=wi,query_id=q,method=m,repeat=repeat,legacy_repeat=k+1,
      start_time_beijing=tstamp,start_monotonic=st,end_monotonic=en,E2E_s=wall,CPU_process_s=cpu,CPU_thread_s=thread,
      **d,output_sha256=hashlib.sha256(json.dumps(got).encode()).hexdigest(),FullV_top10_equal=True if m=='Full-Visual' else '')
    rows.append(row);block_rows.append(row)
    if wi%500==0:print(json.dumps(dict(event='REQUEST_PROGRESS',block=bi,completed=wi,total=len(work),time_beijing=stamp())),flush=True)
   bend=time.perf_counter();full=[z for z in block_rows if z['method']=='Full-Visual'];n=configs[label][1]
   assert len(full)==160*n and len({z['query_id'] for z in full})==160
   br=dict(block=bi,schedule=label,seed=20261109+bi,start_time_beijing=start_stamp,end_time_beijing=stamp(),start_monotonic=bstart,end_monotonic=bend,
    requests=len(block_rows),FullV_requests=len(full),FullV_mean_ms=1000*sum(z['E2E_s'] for z in full)/len(full),status='COMPLETE')
   blocks.append(br);flush_rows();event('BLOCK_COMPLETE',**br)
   print(json.dumps(dict(event='BLOCK_COMPLETE',**br)),flush=True)
   save(f'block_{bi:02d}.json',br)
 guard.check();save('completed.json',dict(status='DONE',time_beijing=stamp(),blocks=blocks,requests=len(rows),FullV_requests=sum(x['FullV_requests'] for x in blocks),
  GPU_window_s=time.monotonic()-window_start,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated(),peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved(),
  qrels_reads=0,sealed_reads=0,new_indexes_built=0,models_retrained=0))
 print(json.dumps(dict(status='DONE',requests=len(rows),blocks=8,time_beijing=stamp())),flush=True)
except BaseException as e:
 flush_rows()
 if not (O/'failure.json').exists():save('failure.json',dict(status='PARTIAL',reason=repr(e),traceback=traceback.format_exc(),time_beijing=stamp(),state=state.copy(),completed_requests=len(rows),blocks=blocks))
 raise
finally:
 stop.set();watch.join(timeout=2);poll.join(timeout=6);flush_rows();guard.close()
