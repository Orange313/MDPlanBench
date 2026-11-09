"""E8 physical files and mmap tensor-shape inventory; no CUDA or index build."""
from pathlib import Path
import argparse,csv,hashlib,json,statistics
import torch
torch.set_num_threads(1)
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
qwen={'HR':'hr_primary_001','Finance':'finance_primary_001','Industrial':'industrial_primary_003',
      'Pharma':'pharma_fixedcorpus_index_001','Biomedical':'icde_eab_independent_007_biomedical_colqwen_001'}
pali={'HR':'icde_eab_independent_007_colpali_vidore_v3_hr_002',
      'Finance':'icde_eab_independent_007_colpali_vidore_v3_finance_en_002',
      'Industrial':'icde_eab_independent_007_colpali_vidore_v3_industrial_002',
      'Pharma':'icde_eab_independent_007_colpali_Pharmaceuticals_002',
      'Biomedical':'icde_eab_lastmile_008_biomedical_colpali_001'}
meta=json.loads((R/'artifacts/icde_eab_review_strengthening_021/EX0/domains.json').read_text())
eco=Path(next(z['index'] for z in meta if z['domain']=='Economics'))
rows=[];files=[]
for domain in ['HR','Finance','Industrial','Pharma','Biomedical','Economics']:
    shared=(R/'cache/indexes'/qwen[domain]) if domain in qwen else eco
    text=shared/'pages.json';pages=json.loads(text.read_text());n=len(pages)
    text_payload=sum(len((z.get('markdown') or '').encode()) for z in pages)
    for model in ['ColQwen2','ColPali']:
        if model=='ColPali' and domain=='Economics':
            rows.append(dict(domain=domain,model=model,status='MISSING_NOT_BUILT'));continue
        ip=shared if model=='ColQwen2' else R/'cache/indexes'/pali[domain]
        parts=sorted((ip/'visual_parts').glob('*.pt'));assert parts
        logical=allocated=payload=count=0;tokens=[];dims=set();dtype=set();ids=set()
        for p in parts:
            st=p.stat();logical+=st.st_size;allocated+=st.st_blocks*512
            z=torch.load(p,map_location='cpu',weights_only=True,mmap=True)
            assert len(z['ids'])==len(z['embeddings'])
            for pid,v in zip(z['ids'],z['embeddings']):
                assert int(pid) not in ids;ids.add(int(pid));assert v.ndim==2
                tokens.append(v.shape[0]);dims.add(v.shape[1]);dtype.add(str(v.dtype));payload+=v.numel()*v.element_size();count+=1
            files.append(dict(domain=domain,model=model,file=str(p),logical_bytes=st.st_size,allocated_bytes=st.st_blocks*512))
            del z
        assert count==n and dtype=={'torch.float16'}
        analytic=sum(tokens)*next(iter(dims))*2 if len(dims)==1 else None
        rows.append(dict(domain=domain,model=model,status='PARTIAL_BM25_INDEX_NOT_PERSISTED',pages=n,parts=len(parts),
            visual_logical_MB=logical/1e6,visual_allocated_MB=allocated/1e6,tensor_payload_MB=payload/1e6,
            mean_stored_vectors_per_page=statistics.mean(tokens),dimension='|'.join(map(str,sorted(dims))),dtype='fp16',
            analytic_MB=analytic/1e6 if analytic is not None else None,analytic_payload_equal=analytic==payload,
            serialization_overhead_MB=(logical-payload)/1e6,text_json_MB=text.stat().st_size/1e6,
            text_utf8_payload_MB=text_payload/1e6,text_shared_with_other_model=True,
            persisted_BM25_index_MB=None,visual_over_BM25_ratio=None,
            visual_over_text_json_ratio=logical/text.stat().st_size,
            index_path=str(ip),text_path=str(text),index_manifest_sha256=hashlib.sha256((ip/'index_manifest.json').read_bytes()).hexdigest(),
            note='BM25 is rebuilt in memory; no persisted file is imputed as0. Stored vectors may include special tokens, not independently measured raw image patches.'))
        print(domain,model,'metadata inventory completed',flush=True)
def save(name,data):
    keys=list(dict.fromkeys(k for z in data for k in z))
    with (O/name).open('x',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(data)
save('E8_assets.csv',rows);save('E8_visual_files.csv',files)
assert not torch.cuda.is_initialized()
(O/'completed.json').write_text(json.dumps(dict(status='PARTIAL',existing_cells=11,missing_cells=['Economics x ColPali'],
    analytic_payload_checks=sum(z.get('analytic_payload_equal',False) for z in rows),GPU_jobs=0,
    limitations=['No persisted BM25 index file: size/ratio MISSING, not0.','Stored vector count is not a separate raw-image patch audit.'],
    torch_version=torch.__version__,CUDA_initialized=False),indent=2)+'\n')
