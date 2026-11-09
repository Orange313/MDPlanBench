"""E5: fixed OCR parallelism experiment, no duplicate image files or GPU."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,resource,shutil,subprocess,time
from datetime import datetime,timezone,timedelta
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
base=R/'artifacts/icde_eab_independent_007/T1_preparation/ocr_001'
ref=json.loads((base/'pages.json').read_text());refhash={int(z['corpus_id']):hashlib.sha256(z['markdown'].encode()).hexdigest() for z in ref}
ids=sorted(refhash);assert len(ids)==1016
runtime=base/'runtime';exe=runtime/'usr/bin/tesseract';assert exe.exists()
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime/'usr/lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','')
env['TESSDATA_PREFIX']=str(runtime/'usr/share/tesseract-ocr/4.00/tessdata');env['OMP_THREAD_LIMIT']='1'
version=subprocess.check_output([str(exe),'--version'],env=env,stderr=subprocess.STDOUT,text=True)
assert version.startswith('tesseract 4.1.1')
for q in ids:assert (base/'png'/f'{q}.png').exists()
def stamp():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def size():return sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
def guard():
    assert size()<=1_000_000_000,'E5_DISK_BUDGET_EXCEEDED'
    assert shutil.disk_usage(O).free>2_000_000,'DISK_BLOCKED_BEFORE_NEXT_WRITE'
free=shutil.disk_usage(O).free
if free<1_000_000_000:
    (O/'NOT_RUN.json').write_text(json.dumps(dict(status='NOT_RUN',reason='DISK_BLOCKED: free space below maximum1GB run budget',free_bytes=free),indent=2))
    raise SystemExit('DISK_BLOCKED')
rng=np.random.default_rng(20261109);order=[rng.permutation([1,2,4,8,16]).tolist() for _ in range(3)]
protocol=dict(time_bj=stamp(),workers=[1,2,4,8,16],repeats=3,order=order,seed=20261109,
    version=version,child_env={'OMP_THREAD_LIMIT':'1'},engine_args=['-l','eng','--psm','3'],
    dispatch='ThreadPoolExecutor dispatching external Tesseract processes, same architecture as historical OCR',
    free_bytes_before=free,budget_bytes=1_000_000_000,source_pngs_reused=True,temporary_images_created=0,
    historical_runtime_lock_sha256=hashlib.sha256((base/'runtime_lock.json').read_bytes()).hexdigest(),
    historical_pages_sha256=hashlib.sha256((base/'pages.json').read_bytes()).hexdigest(),
    historical_workers=4,historical_OMP_THREAD_LIMIT='1',shared_CPU_host=True)
(O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
allstats=[];mismatch=[];done=set()
def one(q):
    st=time.perf_counter()
    p=subprocess.run([str(exe),str(base/'png'/f'{q}.png'),'stdout','-l','eng','--psm','3'],env=env,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(f'TESSERACT_FAILED page={q} returncode={p.returncode}: {p.stderr[:500]}')
    text=p.stdout;digest=hashlib.sha256(text.encode()).hexdigest()
    return q,text,digest,time.perf_counter()-st
try:
    for rnd,settings in enumerate(order,1):
        for workers in settings:
            guard();st=time.perf_counter();ru=resource.getrusage(resource.RUSAGE_CHILDREN);parent=time.process_time()
            textfile=(O/f'worker_{workers}_texts.jsonl').open('x',encoding='utf8') if workers not in done else None
            pages=[];bad=[];load_before=Path('/proc/loadavg').read_text().strip()
            print(json.dumps(dict(event='OCR_START',round=rnd,workers=workers,time_bj=stamp(),loadavg=load_before)),flush=True)
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                    for q,text,digest,wall in pool.map(one,ids):
                        ok=digest==refhash[q]
                        if not ok:bad.append(q);mismatch.append(dict(round=rnd,workers=workers,corpus_id=q,reference_sha256=refhash[q],actual_sha256=digest))
                        if textfile:textfile.write(json.dumps(dict(corpus_id=q,text=text,sha256=digest),ensure_ascii=False)+'\n')
                        pages.append(dict(corpus_id=q,wall_s=wall,sha256=digest,reference_equal=ok))
                        if len(pages)%100==0:
                            guard();print(json.dumps(dict(event='OCR_PROGRESS',round=rnd,workers=workers,pages=len(pages),total=1016,elapsed_s=time.perf_counter()-st,time_bj=stamp())),flush=True)
            finally:
                if textfile:textfile.close()
            rv=resource.getrusage(resource.RUSAGE_CHILDREN)
            row=dict(round=rnd,workers=workers,pages=len(pages),wall_s=time.perf_counter()-st,
                child_user_s=rv.ru_utime-ru.ru_utime,child_sys_s=rv.ru_stime-ru.ru_stime,
                child_CPU_s=(rv.ru_utime+rv.ru_stime)-(ru.ru_utime+ru.ru_stime),parent_CPU_s=time.process_time()-parent,
                mismatch_pages=len(bad),loadavg_before=load_before,loadavg_after=Path('/proc/loadavg').read_text().strip(),
                time_bj=stamp(),bytes_retained=size(),status='DONE' if not bad else 'PARTIAL_OCR_HASH_MISMATCH')
            with (O/f'round_{rnd}_worker_{workers}_page_timings.json').open('x') as f:json.dump(pages,f)
            with (O/'timings.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            allstats.append(row);done.add(workers);guard();print(json.dumps(dict(event='OCR_DONE',**row)),flush=True)
    with (O/'mismatch_pages.json').open('x') as f:json.dump(mismatch,f,indent=2)
    with (O/'completed.json').open('x') as f:json.dump(dict(status='DONE' if not mismatch else 'PARTIAL_OCR_HASH_MISMATCH',
        completed_settings=len(allstats),mismatched_page_observations=len(mismatch),wall_CPU_records=allstats,
        bytes_retained=size(),GPU_jobs=0,temporary_images_created=0,time_bj=stamp()),f,indent=2)
except BaseException as exc:
    with (O/'failed.json').open('x') as f:json.dump(dict(status='PARTIAL',error=repr(exc),completed_settings=len(allstats),time_bj=stamp()),f,indent=2)
    raise
