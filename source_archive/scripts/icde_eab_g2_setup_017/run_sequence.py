"""Serial one-GPU experiment; a failure stops all following dependent jobs."""
import common as C
import json, os, subprocess, sys, time

C.start('operations_001')
p=C.load(C.ART/'protocol.json'); C.verify_sources(p)
commands=[('smoke',m,1) for m in ['ColQwen2','ColPali']]
commands += [('repeat',m,n) for m,n in p['full_sequence']]
commands += [('profile',m,1) for m in p['profile_sequence']]
receipts=[]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
for mode,model,n in commands:
    C.disk_check()
    if C.auxiliary_bytes()>p['auxiliary_budget_bytes']: raise RuntimeError('AUXILIARY_BUDGET_STOP')
    if mode!='smoke':
        assert all((C.ART/f'smoke/{m}_001/completed.json').exists() for m in ['ColQwen2','ColPali'])
    consecutive=0; wait_start=time.monotonic()
    while consecutive<3:
        raw=subprocess.check_output(['nvidia-smi','-i',str(p['gpu']),'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip().split(',')
        ready=int(raw[0].split()[0])<128 and int(raw[1].split()[0])==0
        consecutive=consecutive+1 if ready else 0
        C.event('wait_idle',mode=mode,model=model,repeat=n,raw=raw,idle=ready)
        if time.monotonic()-wait_start>120:raise RuntimeError('RESOURCE_BLOCKED_GPU_BUSY_120S_NO_CUDA_STARTED')
        time.sleep(1)
    log=C.A/f'{mode}_{model}_{n:03d}.log'
    print(json.dumps(dict(event='starting_owned_worker',time_bj=C.stamp(),mode=mode,model=model,repeat=n)),flush=True)
    with log.open('x') as out:
        worker=subprocess.run([str(C.ROOT/'.venv/bin/python'),str(C.ROOT/'scripts'/C.RUN/'worker.py'),model,mode,str(n)],
            cwd=C.ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
    receipt=dict(mode=mode,model=model,repeat=n,returncode=worker.returncode,time_bj=C.stamp(),log=str(log))
    receipts.append(receipt)
    C.write(C.A/f'receipt_{len(receipts):02d}.json',receipt)
    print(json.dumps(receipt),flush=True)
    if worker.returncode: raise RuntimeError('OWN_WORKER_FAILED_SEQUENCE_STOPPED_NO_AUTORETRY')
    guard=C.load(C.ART/f'{mode}/{model}_{n:03d}/resource_guard.json')
    assert guard['valid'] and not guard['foreign_pids'] and not guard['errors']
C.write(C.A/'completed.json',dict(time_bj=C.stamp(),status='PASS_ALL_TEN_PROCESSES',receipts=receipts))
print('G2_ALL_MEASUREMENTS_COMPLETED',flush=True)
