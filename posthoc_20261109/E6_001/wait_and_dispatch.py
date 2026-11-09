"""Wait for a free A6000; retry only PRE-CUDA resource failures, never measurements."""
from pathlib import Path
import argparse,json,os,subprocess,time
from datetime import datetime,timezone,timedelta
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--wait-seconds',type=int,default=1800);a=ap.parse_args()
R=a.project;O=R/'posthoc_20261109/E6_001';start=time.monotonic();attempt=2
def stamp():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def log(name,**kw):
 z=dict(time_beijing=stamp(),event=name,**kw)
 with (O/'resource_dispatch_001.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(z)+'\n')
 print(json.dumps(z),flush=True)
log('MONITOR_STARTED',wait_only_budget_s=a.wait_seconds,policy='Never retry after CUDA starts; preserve all attempts')
while time.monotonic()-start<a.wait_seconds:
 raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,utilization.gpu','--format=csv,noheader'],text=True)
 apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
 occupied={z.split(',')[0].strip() for z in apps.splitlines() if z.strip()}
 available=[]
 for line in raw.splitlines():
  z=[v.strip() for v in line.split(',')]
  if 'RTX A6000' in z[2] and int(z[3].split()[0])<128 and int(z[4].split()[0])==0 and z[1] not in occupied:available.append(int(z[0]))
 log('SNAPSHOT',GPU_snapshot=raw.strip(),available=available)
 if not available:time.sleep(10);continue
 gpu=next(k for k in [3,5,0,1,2,4] if k in available);dest=O/f'measure_{attempt:03d}'
 assert not dest.exists();log('PRE_CUDA_ATTEMPT',gpu=gpu,attempt=attempt)
 with (O/f'measure_{attempt:03d}.log').open('x') as f:
  code=subprocess.run([str(R/'.venv/bin/python'),str(O/'run_e6.py'),'--project',str(R),'--out',str(dest),'--gpu',str(gpu)],
   stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')).returncode
 if code==71 and (dest/'NOT_RUN.json').exists():
  log('PRE_CUDA_RESOURCE_REJECTED',gpu=gpu,attempt=attempt);attempt+=1;time.sleep(10);continue
 log('WORKER_FINISHED',gpu=gpu,attempt=attempt,exit_code=code,complete=(dest/'completed.json').exists())
 with (O/'resource_dispatch_receipt.json').open('x') as f:json.dump(dict(time_beijing=stamp(),status='WORKER_FINISHED',attempt=attempt,gpu=gpu,exit_code=code,output=str(dest),GPU_measurement_retry=False),f,indent=2)
 raise SystemExit(code)
log('RESOURCE_WAIT_EXHAUSTED',wait_s=time.monotonic()-start)
with (O/'resource_dispatch_receipt.json').open('x') as f:json.dump(dict(time_beijing=stamp(),status='NOT_RUN_RESOURCE_BLOCKED',wait_s=time.monotonic()-start,attempts_before_CUDA=attempt-1),f,indent=2)
