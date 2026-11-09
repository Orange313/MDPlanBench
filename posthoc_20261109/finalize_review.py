"""Seal a completed, review-only supplement; never changes old records or paper."""
from pathlib import Path
import csv,hashlib,json,subprocess
from datetime import datetime,timezone,timedelta
S=Path(__file__).resolve().parent;G=S.parent
def read(p):return json.loads((S/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read('E7_reference_gate_001/gate.json')['PASS']
assert read('screening_001/gate.json')['PASS']
assert read('gates_001/gate_summary.json')['endpoint_gate']
rr=read('replay_receipts/full_005.json');assert rr['status']=='PASS_CPU_POSTHOC_REPLAY'
for name in ['RESULTS_SUMMARY.md','manifest.json','hash_inventory.json','MANIFEST.sha256','claim_to_evidence_matrix.csv']:
    assert not (S/name).exists(),('Refusing to overwrite delivery',name)
(S/'RESULTS_SUMMARY.md').write_bytes((S/'review_002/RESULTS_SUMMARY.md').read_bytes())
claims=[
 ('CF_ROUTER_SUPERIORITY','PARTIAL_NOT_SUPPORTED','No b=.05 cell has a positive conditional lower95; signed cost-transfer limitations remain','screening_001/E2_main_b005.csv'),
 ('RETROSPECTIVE_FRONTIER_BIAS','DONE_CONDITIONAL','Cohort-specific retrospective minus grouped cross-fit frontier; effects differ by domain','screening_001/E1_bias_summary.csv'),
 ('ORIGINAL_CI_RECONSTRUCTION','PASS','All72 original endpoints within .01pp; query/process draws and indices saved','gates_001/interval_endpoint_gate.csv'),
 ('INTERVAL_UPPER_BOUND_COUNTS','DONE','All36: U<5/10/15 counts15/21/25; not a proof of no conceivable gain','independent_001/E3_upper_bound_counts.csv'),
 ('LEARNING_DIAGNOSTIC_KAPPA20','DONE_EXPLORATORY','Same fixed Dev/subsets and seeds, no retraining; original four-action diagnostic','independent_001/K17_kappa10_vs20.csv'),
 ('TRANSFERRED_MIXTURE_COMPARISON','DONE_COARSE_HULL','Only actual same-cohort FullV/Fit-only.05/BM25 points; weaker than full static frontier','independent_001/E4_coarse_hull.csv'),
 ('OCR_CONTENT_EQUIVALENCE','PASS','15 settings x1016 frozen text fingerprints; prepared-PNG scope','portable_inputs_001/E5_metadata/completed.json'),
 ('OCR_PARALLEL_LIFECYCLE','DONE_CONDITIONAL','Observed shared-host wall/childCPU scenarios, paired017 model processes; not production CI','E5_analysis_001/E5_crossing_ranges.csv'),
 ('SCHEDULER_CAUSAL_DIAGNOSIS','NOT_RUN','No confirmed exclusive-GPU reservation; old cohort difference unresolved','E6_NOT_RUN.json'),
 ('HR_TEXT_SOURCE_CONTROL','DONE_DEV_ONLY','40/40 frozen HR Dev;40/318 English pool; no new FullV ranking','E7_HR_001/E7_summary.csv'),
 ('HR_OFFICIAL_TEXT_REGRESSION','PASS','80 per-query BM25/BM100 risks checked against archived legal Dev cache','E7_reference_gate_001/E7_official_reference_gate.csv'),
 ('VISUAL_STORAGE_PAYLOAD','PARTIAL','11 payload checks pass; BM25 persisted-index size and ratio MISSING; Eco/ColPali not built','E8_storage_001/E8_assets.csv'),
 ('REVIEW_CPU_REPLAY','PASS_ARCHIVED_RECONSTRUCTION','Clean review checkout, fixed environment, no fresh OCR/GPU/qrels in replay','replay_receipts/full_005.json'),
 ('FORMAL_CERTIFICATION','NOT_CERTIFIED','No new K1, sealed labels read0, unchanged historical contract','PLAN.md')]
with (S/'claim_to_evidence_matrix.csv').open('x',encoding='utf8',newline='') as f:
    w=csv.writer(f);w.writerow(['claim_id','status','supported_scope_and_limits','evidence_path','evidence_sha256'])
    for key,status,scope,p in claims:w.writerow([key,status,scope,p,sha(S/p)])
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()
changed=subprocess.check_output(['git','diff','--name-only','icde27-eab-v1.1','HEAD'],cwd=G,text=True).splitlines()
assert all(p.startswith('posthoc_20261109/') for p in changed)
meta=dict(run_id='posthoc_20261109',time_beijing=datetime.now(timezone(timedelta(hours=8))).isoformat(),
    code_and_replay_input_commit=rr['checkout_commit'],assembly_parent_commit=commit,base_commit='e9d4c2d14abca6003001caf8010da4f6b7321669',
    branch='codex/posthoc-20261109',new_tag=None,public_push=False,
    author_order_resource='a71e700f-dd74-4350-b621-2ea6892ab19f',
    author_order_canonical_sha256='eb5d11ecdb7761bf49558d5e34442988a0ce51af58075e428e0f71b3fdb697b6',
    stage_status=dict(E1='DONE',E2='PARTIAL_ACCOUNTING_LIMITATIONS',E3='DONE',E4='DONE_COARSE_HULL',
      E5='DONE_CONDITIONAL_PREPARED_PNG_SCOPE',E6='NOT_RUN_NO_GPU_RESERVATION',E7='DONE_HR_DEV_ONLY',
      E8='PARTIAL_BM25_INDEX_NOT_PERSISTED',K17='DONE_NO_RETRAINING'),
    gates=dict(kappa20='PASS_EXACT',original_CI='PASS_72_ENDPOINTS',OCR='PASS_15240_FINGERPRINTS',HR_reference='PASS_80_RISKS'),
    CPU_replay=dict(status=rr['status'],checked_files=rr['checked_files'],receipt='replay_receipts/full_005.json'),
    GPU_jobs=0,new_training=0,sealed_labels_read=0,paper_edits=False,license_edits=False,
    modifications_outside_supplement=False,formal_new_certification='NOT_CERTIFIED')
(S/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
files=sorted(p for p in S.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name not in ['hash_inventory.json','MANIFEST.sha256'])
inv={str(p.relative_to(S)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
(S/'hash_inventory.json').write_text(json.dumps(inv,indent=2)+'\n',encoding='utf8')
files.append(S/'hash_inventory.json');files.sort()
manifest=''.join(sha(p)+'  '+str(p.relative_to(S)).replace('\\','/')+'\n' for p in files)
(S/'MANIFEST.sha256').write_text(manifest,encoding='utf8')
print(json.dumps(dict(status='SEALED_REVIEW_ONLY',files=len(files),manifest_sha256=sha(S/'MANIFEST.sha256'),
    code_commit=commit,paper_edited=False,public_push=False),indent=2))
