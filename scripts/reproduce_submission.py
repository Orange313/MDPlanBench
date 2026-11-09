"""Complete offline numerical replay; archived experiments remain unchanged."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
G=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--keep-going',action='store_true',help='Preserve and report all independent failures instead of aborting.');a=p.parse_args()
 O=a.output.resolve();O.mkdir(parents=True,exist_ok=False);start=time.perf_counter();steps=[]
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(O/'font_cache'),PYTHONHASHSEED='0',PYTHONUTF8='1')
 commands=[('base',['scripts/reproduce_paper.py','--output',str(O/'base')]),('posthoc',['posthoc_20261109/reproduce_posthoc.py','--output',str(O/'posthoc')]),('E6',['posthoc_20261109/E6_001/replay_analysis.py','--root',str(G/'posthoc_20261109/E6_001'),'--out',str(O/'E6')]),('paper_values',['scripts/verify_paper_values.py','--output',str(O/'paper_values')]),('R84_number_map',['scripts/verify_R84_number_map.py','--output',str(O/'R84_number_map')]),('frozen_inference',['scripts/verify_frozen_inference.py','--output',str(O/'frozen_inference')]),('earlier_plan_audit',['scripts/verify_earlier_plan_audit.py','--output',str(O/'earlier_plan_audit')])]
 for name,args in commands:
  ts=time.perf_counter()
  with (O/(name+'.log')).open('x',encoding='utf8') as f:r=subprocess.run([sys.executable,*args],cwd=G,env=env,stdout=f,stderr=subprocess.STDOUT)
  steps.append(dict(step=name,status='PASS' if r.returncode==0 else 'FAIL',exit_code=r.returncode,wall_s=time.perf_counter()-ts,log=name+'.log'))
  if r.returncode and not a.keep_going:break
 # Preserve author figure bytes separately from data-driven reconstructions.
 exact=O/'figures_exact_manuscript';exact.mkdir()
 current=json.loads((G/'config/paper_current.json').read_text())
 for x in json.loads((G/current['asset_manifest']).read_text()):
  src=G/x['path'].replace('\\','/');assert hashlib.sha256(src.read_bytes()).hexdigest()==x['sha256'];shutil.copyfile(src,exact/src.name)
 generated=O/'figures_generated';generated.mkdir()
 mapping={'fig1_industrial_ab_019.png':'fig1_overview.png','fig3_static_frontiers_018_019.png':'fig3_frontier.png','fig4_decision_information_019.png':'fig4_decision.png','posthoc_diagnostic.pdf':'posthoc_diagnostic.pdf','posthoc_diagnostic.png':'posthoc_diagnostic.png'}
 for old,new in mapping.items():
  src=O/'base/figures'/old
  if src.exists():shutil.copyfile(src,generated/new)
 receipt=dict(status='PASS_ALL_OFFLINE_STAGES' if len(steps)==len(commands) and all(s['status']=='PASS' for s in steps) else 'FAIL_OR_PARTIAL',steps=steps,wall_s=time.perf_counter()-start,python=sys.version,platform=sys.platform,source_manuscript_revision=current['revisionNumber'],GPU_jobs=0,new_training=0,new_benchmark_evaluation=False,network=False,limitations=['Fresh timings, OCR, model acquisition, and original-data evaluation are separate hardware paths.','Exact manuscript graphics are immutable archived assets; freshly rendered graphics may differ in layout/fonts but are checked numerically.','Public replay does not open sealed qrels.'])
 (O/'submission_replay_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,indent=2));return int(receipt['status']!='PASS_ALL_OFFLINE_STAGES')
if __name__=='__main__':raise SystemExit(main())
