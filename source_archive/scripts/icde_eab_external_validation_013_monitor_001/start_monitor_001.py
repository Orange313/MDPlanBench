from pathlib import Path
import subprocess,sys,os,json,datetime
root=Path('${PROJECT_ROOT}');a=root/'artifacts/icde_eab_external_validation_013/monitor_001';runtime=a/'runtime_002';runtime.mkdir(parents=True,exist_ok=True)
script=root/'scripts/icde_eab_external_validation_013_monitor_001/supervisor_001.py'
assert (a/'setup_005/launch_authorization_orange.json').exists(),'REGISTER_SETUP_TO_ORANGE_FIRST'
status=runtime/'status.json'
if status.exists():
 v=json.loads(status.read_text());pid=v['pid']
 try:
  cmd=Path(f'/proc/{pid}/cmdline').read_bytes()
  if str(script).encode() in cmd:print(json.dumps({'status':'ALREADY_RUNNING','pid':pid,'state':v['state']}));sys.exit()
 except FileNotFoundError:pass
 raise RuntimeError('STALE_MONITOR_REQUIRES_NEW_ATTEMPT_NO_OVERWRITE')
log=(runtime/'supervisor_stdout.log').open('xb')
p=subprocess.Popen([str(root/'.venv/bin/python'),str(script)],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
receipt={'status':'LAUNCHED_DETACHED_SERVER_MONITOR','pid':p.pid,'script':str(script),'time_bj':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'poll_s':60,'log':str(runtime/'supervisor_stdout.log')}
with (runtime/'launch_receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
