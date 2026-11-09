"""Replay old38 CSV, Economics9-method statistics, and all18 PlanB CSV/3PNG."""
from pathlib import Path
import json,os,sys,subprocess,hashlib,shutil,argparse,time
from acquire_annotations import acquire
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--official-cache',required=True);p.add_argument('--skip-parent',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1];ext=root/'planb014_full';out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False);ws=out/'workspace';shutil.copytree(ext/'inputs',ws);start=time.perf_counter();receipts={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in json.loads((ext/'input_manifest.json').read_text()).items():assert sha(ws/name)==h,name
receipts['annotations']=acquire(root,Path(a.official_cache).resolve(),ws)
if not a.skip_parent:subprocess.run([sys.executable,str(root/'reproduce_all.py'),'--output',str(out/'parent_public_replay')],cwd=root,check=True)
subprocess.run([sys.executable,str(ext/'bio_statistics.py'),str(ws),str(ext/'bio_statistics_lock.json')],check=True,cwd=root)
env={**os.environ,'MDROUTER_FULL_REPLAY_ROOT':str(ws),'MDROUTER_REPLAY_STAGE':'economics'}
subprocess.run([sys.executable,str(ext/'economics_summary.py'),'auto2_attempt_001'],env=env,check=True,cwd=root)
env['MDROUTER_REPLAY_STAGE']='mechanism';subprocess.run([sys.executable,str(ext/'b2_analysis_002.py')],env=env,check=True,cwd=root)
subprocess.run([sys.executable,str(ext/'paper_figures.py'),str(ws),str(out/'paper_figures')],check=True,cwd=root)
checks=[]
for name,h in json.loads((ext/'expected_numeric_hashes.json').read_text()).items():
 target=ws/name;actual=sha(target);checks.append({'file':name,'expected_sha256':h,'actual_sha256':actual,'identical':actual==h})
(out/'full_replay_receipt.json').write_text(json.dumps({'status':'PASS' if all(x['identical'] for x in checks) else 'FAIL','new_GPU_executions':0,'raw_annotations_in_checkout':False,'all_checks':checks,'new_science_CSV':18,'mechanism_PNG':3,'economics_methods':9,'parent_replayed':not a.skip_parent,'wall_s':time.perf_counter()-start,'scope':'Historical numeric reconstruction; not independent evaluation/Serving/K1 or public hosting'},indent=2)+'\n');assert all(x['identical'] for x in checks),[x for x in checks if not x['identical']]
print(json.dumps({'status':'PASS_FULL_ECONOMICS_AND_18_CSV_3_PNG_REPLAY','checks':len(checks),'parent':not a.skip_parent,'wall_s':time.perf_counter()-start}))
