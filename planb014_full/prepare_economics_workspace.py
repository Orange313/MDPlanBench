"""Prepare a fresh historical-design GPU reproduction workspace. Does not run CUDA."""
from pathlib import Path
import argparse,json,shutil,hashlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--assets',required=True);p.add_argument('--ocr-pages',required=True);p.add_argument('--colqwen2-snapshot',required=True);a=p.parse_args();pkg=Path(__file__).resolve().parents[1];ext=pkg/'planb014_full';root=Path(a.output).resolve();root.mkdir(parents=True,exist_ok=False);storage=root/'storage';(storage/'indexes').mkdir(parents=True);contract=json.loads((ext/'economics_execution_contract.json').read_text());assets=Path(a.assets).resolve()
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
def cp(src,rel):target=root/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
for kind,item in contract['official_inputs'].items():
 source=assets/kind/Path(item['repo_path']).name;assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256'];target=storage/'assets'/kind/source.name;target.parent.mkdir(parents=True);target.symlink_to(source);item['path']=str(target.relative_to(root))
pages=Path(a.ocr_pages).resolve();data=json.loads(pages.read_text());assert len(data)==452;cp(pages,'storage/ocr_001/pages.json')
shutil.copytree(pkg/'execution_source/src',root/'src');cp(pkg/'execution_source/cross_domain_four_plan_001.py','scripts/cross_domain_four_plan_001.py');cp(pkg/'config/physical_plan_config_original.json','configs/hr_pilot_sparse_004.json');write(root/'manifests/hr_models_verified.json',{'visual':{'local_path':str(Path(a.colqwen2_snapshot).resolve()),'revision':contract['primary_model_revision']}})
cp(pkg/'config/frozen_Q_QP_coefficients.json','artifacts/icde_eab_independent_007/T0/locked_models.json');cp(pkg/'config/frozen_RR_adapted_coefficients.json','artifacts/icde_evidence_closure_003/E2/candidate_models.json');cp(ext/'inputs/query_family_map.csv','query_family_map.csv')
sd=root/'scripts/icde_eab_external_validation_013_monitor_001';sd.mkdir(parents=True,exist_ok=True)
for name in ['common_execution.py','archive_code.py','engine_frozen_004.py','learning_base_001.py','economics_worker_001.py']:
 source=ext/'execution_source'/name;target=sd/('common.py' if name=='common_execution.py' else name);text=source.read_text();text=text.replace("protocol['status']=='FROZEN_BEFORE_RETRIEVAL_OUTCOMES'","protocol['status']=='ARCHIVED_DESIGN_REPRODUCTION_NOT_NEW_PRE_REGISTRATION'");target.write_text(text)
contract['status']='ARCHIVED_DESIGN_REPRODUCTION_NOT_NEW_PRE_REGISTRATION';contract['query_family_map']='query_family_map.csv';contract['code_SHA256']={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for base in [sd,root/'src'] for f in base.rglob('*.py')};write(root/'artifacts/icde_eab_external_validation_013/monitor_001/setup_005/execution_protocol.json',contract)
write(root/'reproduction_workspace_receipt.json',{'status':'PREPARED_NOT_EXECUTED','new_GPU_runs':0,'original_frozen_protocol_SHA256':contract['original_frozen_protocol_SHA256'],'boundary':'Historical unblinded reproduction; do not call this a new blind benchmark or new K1','resource_requirement':'1trulyidleA6000;3idlechecks;continuousResourceGuard;30GiBassetreserve'})
print('Prepared only. With pinned GPU dependencies and local licensed checkpoint, export:')
print('export MDROUTER_EXECUTION_ROOT='+str(root));print('export MDROUTER_ASSET_ROOT='+str(storage))
for proc in range(3):print('python '+str(sd/'economics_worker_001.py')+' GPU_ID '+str(proc)+' reproduction_001')
