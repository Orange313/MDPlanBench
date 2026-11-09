"""Seal only this appended E6 stage; the parent frozen manifest stays unchanged."""
from pathlib import Path
import hashlib,json,subprocess
from datetime import datetime,timezone,timedelta
S=Path(__file__).resolve().parent
for name in ['manifest.json','MANIFEST.sha256']:assert not (S/name).exists(),name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
raw=json.loads((S/'measure_003/completed.json').read_text());guard=json.loads((S/'measure_003/resource_guard.json').read_text());summary=json.loads((S/'analysis_001/analysis_summary.json').read_text());replay=json.loads((S/'replay_receipt_001/receipt.json').read_text())
assert raw['status']=='DONE' and guard['valid'] and summary['status']=='DONE' and replay['status']=='PASS_CPU_ARCHIVED_REPLAY'
meta=dict(run_id='posthoc_20261109/E6_001',time_beijing=datetime.now(timezone(timedelta(hours=8))).isoformat(),
 status='DONE',replication_verdict=summary['verdict'],physical_GPU_index=0,GPU_cards_used=1,GPU_model='RTX A6000',
 PLAN_commit='4838316b3e31f840c5124b05274c0b818b525d0d',GPU_analysis_implementation_commit='23659374ae697d11dcc78c534028f6b58c52e56e',
 assembly_parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip(),
 actual_GPU_attempt='measure_003',pre_CUDA_rejections=['measure_001','measure_002'],actual_measured_runs=1,requests=16640,FullV_requests=2560,
 GPU_window_s=raw['GPU_window_s'],paired_bootstrap_queries=160,B=2000,seed=20261109,
 A_minus_B=summary['A_minus_B'],qrels_reads=0,sealed_reads=0,new_indexes_built=0,new_training=0,paper_edited=False,
 public_push=False,new_tag=None,branch='codex/posthoc-20261109',cpu_replay_checks=len(replay['checked_files']),
 code_sha256={p.name:sha(p) for p in S.glob('*.py')})
(S/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
files=sorted(p for p in S.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='MANIFEST.sha256')
assert all(p.suffix not in ['.pt','.safetensors','.bin','.parquet','.arrow'] for p in files)
(S/'MANIFEST.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(S)).replace('\\','/')+'\n' for p in files),encoding='utf8')
print(json.dumps(dict(status='SEALED',files=len(files),manifest_sha256=sha(S/'MANIFEST.sha256')),indent=2))
