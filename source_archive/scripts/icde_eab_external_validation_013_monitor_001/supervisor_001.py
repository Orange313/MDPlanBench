"""Persistent quiet GPU monitor; executes fixed smoke and full suite, never steals a GPU."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import common as C
import ctypes as ct,fcntl,json,time,subprocess,signal,shutil,sys,traceback,datetime
from pathlib import Path
C.ART.mkdir(parents=True,exist_ok=True);C.REPORT.mkdir(parents=True,exist_ok=True)
runtime=C.ART/'runtime_002';runtime.mkdir(exist_ok=True);pending=C.REPORT/'orange_pending';pending.mkdir(exist_ok=True)
lock=(runtime/'monitor.lock').open('a');fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
protocol_path=C.ART/'setup_005/execution_protocol.json';protocol=json.loads(protocol_path.read_text());protocol_hash=C.sha(protocol_path);scriptdir=C.ROOT/'scripts'/C.RUN;python=C.ROOT/'.venv/bin/python';analysis_python=Path('/dev/shm/icde_eab_release_validation_010_work_002/fresh_cpu_environment_001/bin/python')
lib=ct.CDLL('libnvidia-ml.so.1');assert lib.nvmlInit_v2()==0
class Process(ct.Structure):_fields_=[('pid',ct.c_uint),('memory',ct.c_ulonglong),('gpu_instance',ct.c_uint),('compute_instance',ct.c_uint)]
def processes(gpu):
 h=ct.c_void_p();assert lib.nvmlDeviceGetHandleByIndex_v2(ct.c_uint(gpu),ct.byref(h))==0;n=ct.c_uint(128);p=(Process*128)();assert lib.nvmlDeviceGetComputeRunningProcesses_v2(h,ct.byref(n),p)==0;return [int(p[i].pid) for i in range(n.value)]
def gpus():
 raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader'],text=True,timeout=15);rows=[]
 for line in raw.splitlines():
  z=[s.strip() for s in line.split(',')];gpu=int(z[0]);p=processes(gpu);rows.append({'gpu':gpu,'uuid':z[1],'total_MiB':int(z[2].split()[0]),'used_MiB':int(z[3].split()[0]),'free_MiB':int(z[4].split()[0]),'utilization':int(z[5].split()[0]),'pids':p,'idle':not p and int(z[3].split()[0])<128 and int(z[5].split()[0])==0})
 return rows
state={'run_id':C.RUN,'parent_run':C.PARENT,'pid':os.getpid(),'state':'INITIALIZING','created_bj':C.stamp(),'poll_interval_s':60,'checks':0,'selected_gpu':None,'attempt':None,'new_K1':'NOT_CERTIFIED','ESG':'LICENSE_BLOCKED','sealed_reads':0}
def atomic(path,obj):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(C.clean(obj),ensure_ascii=False,indent=2),encoding='utf8');os.replace(tmp,path)
def update(name,**kw):
 changed=name!=state.get('state');state.update(kw,state=name,updated_bj=C.stamp());atomic(runtime/'status.json',state)
 if changed:
  event={**state}
  with (runtime/'events.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(C.clean(event),ensure_ascii=False)+'\n')
  number=len((runtime/'events.jsonl').read_text().splitlines());(pending/f'{number:03d}_{name}.md').write_text(f'## {C.RUN} — {name} — {C.stamp()}北京时间\n\n实际状态：{json.dumps(C.clean(event),ensure_ascii=False)}\n\nNo refit/ESG/sealedreads; NOT_CERTIFIED. This is queued for Orange MCP writeback, not already published.\n',encoding='utf8')
def stop_requested():return (runtime/'STOP').exists()
def pause(seconds):
 for _ in range(int(seconds)):
  if stop_requested():raise InterruptedError('STOP_SENTINEL')
  time.sleep(1)
def idle_three(gpu):
 snaps=[]
 for k in range(3):
  snap=gpus();row=next(x for x in snap if x['gpu']==gpu);snaps.append({'time_bj':C.stamp(),'rows':snap})
  if not row['idle']:return False,snaps
  if k<2:pause(1)
 return True,snaps
def verify():
 assert C.sha(protocol_path)==protocol_hash
 for p,h in protocol['code_SHA256'].items():assert C.sha(C.ROOT/p)==h,'CODE_HASH_CHANGED '+p
 for x in protocol['official_inputs'].values():assert C.sha(x['path'])==x['SHA256'],'DATA_HASH_CHANGED'
 metadata=json.loads((C.ROOT/'manifests/hr_models_verified.json').read_text());weight=Path(metadata['visual']['local_path'])/'model.safetensors';assert C.sha(weight)==protocol['primary_weight_SHA256'],'WEIGHT_HASH_CHANGED'
 for model in [protocol['frozen_Q_QP'],protocol['RR_adapted']]:assert C.sha(C.ROOT/model['checkpoint'])==model['SHA256'],'POLICY_CHECKPOINT_HASH_CHANGED'
 if shutil.disk_usage(C.STORAGE).free<30*2**30:raise RuntimeError('DISK_BLOCKED')
def terminate_owned(child):
 if child.poll() is not None:return
 assert os.getpgid(child.pid)==child.pid
 assert Path(f'/proc/{child.pid}').stat().st_uid==os.getuid()
 os.killpg(child.pid,signal.SIGTERM)
 try:child.wait(timeout=5)
 except subprocess.TimeoutExpired:
  if child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
def launch(command,gpu,tag):
 logdir=runtime/'logs';logdir.mkdir(exist_ok=True);logpath=logdir/(tag.replace('/','_')+'.log')
 with logpath.open('x',encoding='utf8') as log:
  child=subprocess.Popen([str(x) for x in command],cwd=C.ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
  state['child_pid']=child.pid;atomic(runtime/'status.json',state)
  try:
   while child.poll() is None:
    if stop_requested():terminate_owned(child);raise InterruptedError('STOP_SENTINEL')
    if gpu is not None:
     foreign=[p for p in processes(gpu) if p!=child.pid]
     if foreign:
      terminate_owned(child);(logdir/(tag.replace('/','_')+'_contamination.json')).write_text(json.dumps({'time_bj':C.stamp(),'foreign_pids':foreign,'stopped_only_own_child':child.pid}),encoding='utf8');return 'RESOURCE_INTERRUPTED'
    if shutil.disk_usage(C.STORAGE).free<30*2**30:terminate_owned(child);return 'DISK_BLOCKED'
    time.sleep(.2)
  finally:
   if child.poll() is None:terminate_owned(child)
   state.pop('child_pid',None);atomic(runtime/'status.json',state)
  if child.returncode==0:return 'PASS_PROCESS_EXIT'
 text=logpath.read_text(encoding='utf8',errors='replace').lower()
 if 'out of memory' in text:return 'CUDA_OOM'
 if 'foreign' in text or 'not idle' in text or 'occupied' in text:return 'RESOURCE_INTERRUPTED'
 if 'disk_blocked' in text or 'no space left' in text:return 'DISK_BLOCKED'
 return 'CUDA_OR_EXECUTION_ERROR'
def finish_receipt():
 records={str(p.relative_to(C.ROOT)):C.sha(p) for p in C.REPORT.rglob('*') if p.is_file() and p.name!='runtime_completion.json'}
 atomic(C.REPORT/'runtime_completion.json',{'time_bj':C.stamp(),'state':state,'protocol_SHA256':protocol_hash,'report_file_hashes':records,'outcome_scope':'Economics frozen descriptive; no K1/Serving guarantee','Orange_pending':str(pending)})
try:
 update('WAITING_FOR_GPU',core_protocol_SHA256='c6b76cf2242afe4b8791cd5997b56336f2e6779cc3e17af172575e222950b613')
 attempts=0
 while True:
  if stop_requested():raise InterruptedError('STOP_SENTINEL')
  if shutil.disk_usage(C.STORAGE).free<30*2**30:update('DISK_BLOCKED');break
  observed=gpus();state['checks']+=1;state['last_GPU_snapshot']=observed;state['last_check_bj']=C.stamp();atomic(runtime/'status.json',state)
  idle=[x for x in observed if x['idle']]
  if not idle:pause(60);continue
  chosen=idle[0];gpu=chosen['gpu'];ok,snaps=idle_three(gpu)
  if not ok:pause(60);continue
  attempts+=1;attempt=f'auto2_attempt_{attempts:03d}';state.update(attempt=attempt,selected_gpu=gpu,selected_UUID=chosen['uuid']);adir=C.ART/attempt;physical=C.STORAGE/'monitor_artifacts'/attempt;physical.mkdir(parents=True,exist_ok=False);adir.symlink_to(physical,target_is_directory=True);C.write(adir/'three_idle_checks.json',snaps)
  verify();update('SMOKE_RUNNING');outcome=launch([python,scriptdir/'gpu_smoke_monitor_001.py',attempt+'/smoke',gpu],gpu,attempt+'/smoke')
  if outcome=='PASS_PROCESS_EXIT':
   smoke=json.loads((C.REPORT/attempt/'smoke/gpu_smoke_result.json').read_text());outcome='PASS_PROCESS_EXIT' if smoke['status']=='PASS_GUARDED_GPU_SMOKE_NO_OOM' else smoke['status']
   if outcome=='PASS_PROCESS_EXIT':
    actual_gpu=smoke['physical_GPU'];assert actual_gpu==gpu,'SMOKE_GPU_DIFFERS_FROM_CONFIRMED_GPU';update('SMOKE_PASSED',smoke_result=smoke)
    for proc in range(3):
     pause(2);ok,checks=idle_three(gpu)
     if not ok:outcome='RESOURCE_INTERRUPTED';break
     C.write(adir/f'process_{proc:02d}_idle_checks.json',checks);update('MAIN_RUNNING',process=proc)
     outcome=launch([python,scriptdir/'economics_worker_001.py',gpu,proc,attempt],gpu,attempt+f'/process_{proc:02d}')
     if outcome!='PASS_PROCESS_EXIT':break
    if outcome=='PASS_PROCESS_EXIT':
     update('ANALYSIS_RUNNING');outcome=launch([analysis_python,scriptdir/'summarize_economics_001.py',attempt],None,attempt+'/summary')
     if outcome=='PASS_PROCESS_EXIT':update('COMPLETED',results=str(C.REPORT/attempt/'summary'),final_numbers=json.loads((C.REPORT/attempt/'summary/final_numbers.json').read_text()));break
  if outcome in ['RESOURCE_INTERRUPTED','RESOURCE_BLOCKED','RESOURCE_BLOCKED_CONTAMINATION']:
   update('RESOURCE_INTERRUPTED',reason=outcome)
   if attempts>=3:update('NEEDS_USER_AFTER_3_INTERRUPTED_ATTEMPTS');break
   pause(60);update('WAITING_FOR_GPU');continue
  update(outcome if outcome in ['CUDA_OOM','DISK_BLOCKED'] else 'FAILED_NEEDS_USER',reason=outcome);break
except InterruptedError as e:update('STOPPED_BY_USER',reason=str(e))
except Exception as e:
 (runtime/'supervisor_failure.json').write_text(json.dumps({'time_bj':C.stamp(),'error':str(e),'traceback':traceback.format_exc()}),encoding='utf8');update('FAILED_NEEDS_USER',reason=str(e))
finally:finish_receipt()
