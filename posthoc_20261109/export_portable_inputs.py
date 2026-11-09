"""Allowlisted small numerical inputs; never exports raw questions/qrels/pages."""
from pathlib import Path
import argparse,csv,hashlib,json
import numpy as np
import accounting as C
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
ds=C.read(R/'artifacts/icde_evidence_closure_003/E2/pharma_dataset.npz');dev=ds['roles']=='development'
raw=C.read(R/'reports/icde_evidence_closure_003/E2/per_query_policy.csv')
members=C.read(R/'reports/icde_final_gate_004/S3/paired_fit_subsets.csv')
old=C.read(R/'reports/icde_final_gate_004/S3/matched_risk_learning_curves.csv')
raw=[{k:z[k] for k in ['source','method','Pharma_fit_n','seed','kappa','query_id','r','E2E_s']} for z in raw if
    z['source']=='Pharma_only' and z['method'] in ['Q_regret','QP_regret'] and float(z['kappa']) in [10,20]]
members=[{k:z[k] for k in ['seed','requested_n','query_id','family']} for z in members]
data=dict(dev_dataset={k:ds[k][dev].tolist() for k in ['qids','roles','family','Y','T']},policy_rows=raw,
    subset_membership=members,archived_learning_curves=[z for z in old if float(z['kappa']) in [10,20]],
    scope='Numerical fixed-Dev diagnostic inputs; no query text or page-relevance mappings')
C.jsave(O/'K17_inputs.json',data)
for model in ['ColQwen2','ColPali']:
    for repeat in [1,2,3]:
        src=R/f'reports/icde_eab_g2_setup_017/repeat/{model}_{repeat:03d}'
        comp=C.read(src/'setup_components.csv');requests=C.read(src/'requests.csv')
        target=O/'setup017'/f'{model}_{repeat:03d}'
        C.csvsave(target/'setup_components.csv',comp)
        C.csvsave(target/'requests.csv',[{k:z[k] for k in ['model','repeat','query_id','plan','E2E_s','CPU_s']} for z in requests])
ref=C.read(R/'artifacts/icde_eab_independent_007/T1_preparation/ocr_001/pages.json')
C.jsave(O/'reference_OCR_hashes.json',{int(z['corpus_id']):hashlib.sha256(z['markdown'].encode()).hexdigest() for z in ref})
C.jsave(O/'source_hashes.json',C.INPUTS)
C.jsave(O/'export_receipt.json',dict(status='ALLOWLISTED_NUMERICAL_EXPORT',K17_policy_rows=len(raw),raw_question_text=False,
    full_qrels=False,page_images=False,OCR_text=False,model_weights=False))
