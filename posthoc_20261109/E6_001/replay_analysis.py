"""CPU-only reconstruction from archived E6 records; never starts a GPU job."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
S=a.root.resolve();O=a.out.resolve();O.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(O/'font_cache'))
with (O/'command.log').open('x') as f:
 subprocess.run([sys.executable,str(S/'analyze_e6.py'),'--input',str(S/'measure_003'),'--preflight',str(S/'preflight_001'),'--out',str(O/'analysis')],check=True,env=env,stdout=f,stderr=subprocess.STDOUT)
checks=[]
for name in ['schedule_means.csv','factorial_effects.csv','repeat_differences.csv','block_gpu_metrics.csv','repeat_label_audit.csv','E6_fullv_means.png','E6_block_metrics.png']:
 p=S/'analysis_001'/name;q=O/'analysis'/name;ok=p.read_bytes()==q.read_bytes();checks.append(dict(file=name,PASS=ok,sha256=hashlib.sha256(q.read_bytes()).hexdigest()));assert ok,name
for name in ['bootstrap_indices.npz','bootstrap_draws.npz']:
 with np.load(S/'analysis_001'/name,allow_pickle=False) as x,np.load(O/'analysis'/name,allow_pickle=False) as y:
  ok=set(x.files)==set(y.files) and all(np.array_equal(x[k],y[k]) for k in x.files)
 assert ok,name;checks.append(dict(file=name,PASS=ok,comparison='NPZ arrays'))
assert json.loads((S/'analysis_001/analysis_summary.json').read_text())==json.loads((O/'analysis/analysis_summary.json').read_text())
r=dict(status='PASS_CPU_ARCHIVED_REPLAY',wall_s=time.perf_counter()-start,checked_files=checks,analysis_summary_equal=True,
 actual_GPU_jobs=0,new_model_training=0,qrels_reads=0,paper_edits=False,PDF_regenerated=True,
 limitation='Reconstruction of one archived resident process, not a new GPU replication or independent process confidence interval')
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(status=r['status'],checks=len(checks),wall_s=r['wall_s']),indent=2))
