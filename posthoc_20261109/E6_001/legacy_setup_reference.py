"""Fresh process for smoke, each full setup repeat, or separate GPU profile."""
import time
PROCESS_START = time.perf_counter()
import common as C
import io, json, os, resource, shutil, subprocess, sys, threading
from pathlib import Path

model_name, mode, repeat = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert model_name in ['ColQwen2', 'ColPali'] and mode in ['smoke', 'repeat', 'profile']
stage = f'{mode}/{model_name}_{repeat:03d}'
C.start(stage)
protocol = C.load(C.ART/'protocol.json')
C.verify_sources(protocol)
assert C.sha(C.ART/'asset_lock.json') == protocol['asset_lock_SHA256']
gpu = protocol['gpu']
os.environ.update(CUDA_VISIBLE_DEVICES=str(gpu), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
    OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
    PYTHONDONTWRITEBYTECODE='1', TOKENIZERS_PARALLELISM='false')
idle = []
for _ in range(3):
    raw = subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
    z = [s.strip() for s in raw.split(',')]
    apps = subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
    foreign = [x for x in apps.splitlines() if x.split(',')[0].strip() == z[1]]
    ok = int(z[2].split()[0]) < 128 and int(z[3].split()[0]) == 0 and not foreign
    idle.append(dict(time_bj=C.stamp(), raw=raw, idle=ok))
    if not ok:
        C.write(C.A/'three_idle_checks.json', idle)
        raise RuntimeError('RESOURCE_BLOCKED_BEFORE_CUDA_NO_RETRY')
    time.sleep(1)
C.write(C.A/'three_idle_checks.json', idle)
C.disk_check()
sys.path.insert(0, str(C.ROOT/'src'))
from mdrouter_v5.gpu_accounting import ResourceGuard
guard = ResourceGuard(gpu, C.A/'resource_guard.json', period=.1)
stop_watch = threading.Event()
def watchdog():
    next_cap = 0.
    while not stop_watch.wait(.2):
        try:
            C.disk_check()
            if guard.foreign or guard.errors:
                raise RuntimeError('GPU_EXTERNAL_PROCESS_OR_GUARD_FAILURE')
            if time.monotonic() >= next_cap:
                size = C.auxiliary_bytes()
                if size > protocol['auxiliary_budget_bytes']:
                    raise RuntimeError('AUXILIARY_OUTPUTS_EXCEED_3GiB')
                next_cap = time.monotonic() + 5
        except Exception as e:
            C.write(C.A/'guard_abort.json', dict(time_bj=C.stamp(), reason=str(e),
                foreign_pids=sorted(guard.foreign), errors=guard.errors,
                policy='abort ONLY this owned process; retain partial indexes and logs'))
            try: guard.close()
            except Exception: pass
            print(json.dumps(dict(status='ABORT_OWN_WORKER', reason=str(e))), flush=True)
            os._exit(72)
watch = threading.Thread(target=watchdog, daemon=True); watch.start()
try:
    import torch, numpy as np, pyarrow.parquet as pq
    from PIL import Image
    sys.path.insert(1, str(C.ROOT/'scripts/icde_eab_independent_007'))
    sys.path.insert(2, str(C.ROOT/'scripts/icde_eab_submission_gate_009'))
    import engine_exact_004 as E
    from mdrouter_v5.graded_metrics import stable_ranking
    from gpu_profile_001 import profile
    torch.set_num_threads(1); torch.manual_seed(C.SEED)
    torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    records=[]; blocks=[]; profiled = mode == 'profile'
    C.write(C.A/'environment_before.json', dict(cache=C.cache_state(),
        GPU_snapshot=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu,temperature.gpu,power.draw','--format=csv,noheader'],text=True),
        torch_threads=torch.get_num_threads(), cuda_runtime=torch.version.cuda,
        CPU_affinity=sorted(os.sched_getaffinity(0)), OS_cache='not flushed', index_mode=mode))
    def measure(name, fn, use_profile=False):
        guard.check(); C.disk_check(); torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        st=time.perf_counter(); ct=time.process_time()
        if use_profile:
            value, g=profile(fn, C.A/(name+'_GPU.json'), validate=name=='model_load', require_kernels=False)
        else: value=fn(); g=None
        torch.cuda.synchronize()
        row=dict(model=model_name, repeat=repeat, mode=mode, component=name,
            wall_s=time.perf_counter()-st, CPU_s=time.process_time()-ct,
            GPU_s=g['gpu_active_union_seconds'] if g else None,
            GPU_scope='separate instrumented cohort' if g else 'NOT_MEASURED_THIS_UNPROFILED_COHORT',
            peak_allocated_GPU_bytes=torch.cuda.max_memory_allocated(),
            peak_reserved_GPU_bytes=torch.cuda.max_memory_reserved(),
            peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        records.append(row); C.event('component_complete', **row)
        guard.check(); C.disk_check(); return value
    st=time.perf_counter(); ct=time.process_time()
    torch.cuda.init(); torch.cuda.synchronize()
    records.append(dict(model=model_name, repeat=repeat, mode=mode, component='CUDA_context_init',
        wall_s=time.perf_counter()-st, CPU_s=time.process_time()-ct, GPU_s=None,
        GPU_scope='NOT_MEASURED_CONTEXT_CREATION'))
    env=E.backend()
    if model_name=='ColPali':
        from colpali_engine.models import ColPali, ColPaliProcessor
        from colpali_loader_003 import prepare_overlay, validate_model
        overlay,mapping=measure('adapter_overlay', lambda:prepare_overlay(C,C.A/'adapter_overlay'))
        prep=C.load('artifacts/icde_eab_main_006/X1/preparation.json')
        adapter=prep['model_path']['vidore/colpali-v1.3']
        def load_model():
            m=ColPali.from_pretrained(str(overlay),torch_dtype=torch.bfloat16,device_map='cuda:0',local_files_only=True,attn_implementation='eager').eval()
            return m,ColPaliProcessor.from_pretrained(adapter,local_files_only=True)
    else: load_model=env['load_visual']
    model, processor=measure('model_load',load_model,profiled)
    if model_name=='ColPali': C.write(C.A/'adapter_validation.json',validate_model(model,overlay,mapping))
    bio=C.load('artifacts/icde_eab_independent_007/T1/biomedical_frozen_protocol.json')
    pages=C.load('artifacts/icde_eab_independent_007/T1_preparation/ocr_001/pages.json')
    pages.sort(key=lambda x:int(x['corpus_id']))
    all_ids=[int(x['corpus_id']) for x in pages]; assert len(all_ids)==1016 and len(set(all_ids))==1016
    selected=set(all_ids[:8] if mode=='smoke' else all_ids)
    source=Path(protocol['index_inputs'][model_name]['path'])
    old_values={}
    for part in sorted((source/'visual_parts').glob('*.pt')):
        d=torch.load(part,weights_only=True,map_location='cpu')
        old_values.update({int(i):v for i,v in zip(d['ids'],d['embeddings']) if int(i) in selected})
    assert set(old_values)==selected
    index=C.INDEX/mode/model_name/f'{repeat:03d}'
    index.mkdir(parents=True,exist_ok=False); (index/'visual_parts').mkdir()
    done=[]
    corpus=C.ROOT/protocol['corpus']['path']
    def encode_rows(rows):
        for j in range(0,len(rows),2):
            guard.check(); C.disk_check()
            batch=rows[j:j+2]
            images=[Image.open(io.BytesIO(x['image']['bytes'])).convert('RGB') for x in batch]
            inp=processor.process_images(images).to('cuda:0')
            em=model(**inp); valid=inp['attention_mask'].bool()
            vectors=[v[m].detach().to(torch.float16).cpu() for v,m in zip(em,valid)]
            ids=[int(x['corpus-id']) for x in batch]
            start=time.perf_counter()
            torch.save(dict(ids=ids,embeddings=vectors),index/'visual_parts'/f'{ids[0]:06d}.pt')
            blocks.append(dict(kind='serialization',pages=len(ids),wall_s=time.perf_counter()-start))
            done.extend(ids)
    def build():
        for bi,b in enumerate(pq.ParquetFile(corpus).iter_batches(batch_size=32,columns=['corpus-id','image'])):
            rows=[x for x in b.to_pylist() if int(x['corpus-id']) in selected]
            if not rows: continue
            if profiled:
                _,g=profile(lambda:encode_rows(rows),C.A/f'index_block_{bi:03d}_GPU.json',require_kernels=True)
                blocks.append(dict(kind='profiled_encoding_block',pages=len(rows),**g))
            else: encode_rows(rows)
            if len(done)%128==0 or len(done)==len(selected):
                print(json.dumps(dict(time_bj=C.stamp(),model=model_name,mode=mode,repeat=repeat,pages=len(done),total=len(selected))),flush=True)
        assert len(done)==len(selected) and set(done)==selected
    with torch.inference_mode(): measure('full_index_build_and_persist' if mode!='smoke' else 'smoke_8_page_build',build)
    # Deliberately outside the index-build timer: no gold labels or retrieval quality selection.
    equivalence=[]; vv={}
    for part in sorted((index/'visual_parts').glob('*.pt')):
        z=torch.load(part,weights_only=True,map_location='cpu')
        for pid,v in zip(z['ids'],z['embeddings']):
            ov=old_values[int(pid)]; assert v.shape==ov.shape
            error=float((v.float()-ov.float()).abs().max())
            equivalence.append(dict(corpus_id=int(pid),maxabs=error,bitwise_equal=torch.equal(v,ov)))
            assert error<=protocol['numerical_tolerance_maxabs'],'FROZEN_EMBEDDING_MISMATCH'
            vv[int(pid)]=v
    C.table(C.R/'index_equivalence.csv',equivalence)
    C.table(C.R/'index_blocks.csv',blocks)
    C.write(index/'index_manifest.json',dict(run_id=C.RUN,model=model_name,mode=mode,repeat=repeat,pages=len(done),
        reference_manifest_SHA256=protocol['index_inputs'][model_name]['manifest_SHA256'],
        files={str(p.relative_to(index)):C.sha(p) for p in sorted((index/'visual_parts').glob('*.pt'))},
        scientific_quality_outputs_replaced=False))
    if mode=='repeat':
        ids=all_ids
        def resident():
            lengths=torch.tensor([len(vv[i]) for i in ids],device='cuda:0')
            passage=torch.nn.utils.rnn.pad_sequence([vv[i].float() for i in ids],batch_first=True).cuda()
            return lengths,passage
        lengths,passage=measure('index_residency',resident)
        bm=measure('BM25_build',lambda:env['BM25'](pages))
        engine=type('CostEngine',(),{})()
        engine.torch=torch; engine.passage=passage; engine.lengths=lengths; engine.ids=ids; engine.env=env
        def encode(text): return model(**processor.process_queries([text]).to('cuda:0'))[0].float()
        def pali_score(q,indices):
            values=[]
            for st in range(0,len(indices),64):
                ix=indices[st:st+64]; t=torch.tensor(ix,device='cuda:0')
                block=passage.index_select(0,t)
                logits=torch.matmul(q.unsqueeze(0),block.transpose(1,2))
                mask=torch.arange(passage.shape[1],device='cuda:0')[None,:]>=lengths.index_select(0,t)[:,None]
                logits.masked_fill_(mask[:,None,:],-torch.inf)
                values+=logits.max(2).values.sum(1).cpu().tolist()
            return [indices[i] for i in stable_ranking([ids[i] for i in indices],values)]
        score=(lambda q,ix:E.Engine.score(engine,q,ix)) if model_name=='ColQwen2' else pali_score
        def execute(plan,text):
            if plan=='Full-Visual': candidate=list(range(len(ids)))
            else:
                order,_=bm.search(text)
                if plan=='BM25': return [ids[i] for i in order[:10]]
                candidate=order[:int(plan[6:])]
            return [ids[i] for i in score(encode(text),candidate)[:10]] if candidate else []
        qt=C.ROOT/protocol['public_queries']['path']
        queries={int(x['query-id']):x['query'] for x in pq.read_table(qt).to_pylist()}
        assert sorted(queries)==bio['query_ids'] and len(queries)==160
        C.write(C.A/'read_audit.json',dict(public_Biomedical_query_SHA256=C.sha(qt),qrels_reads=0,sealed_reads=0))
        requests=[]
        with torch.inference_mode():
            for plan in C.PLANS:
                for _ in range(3): execute(plan,queries[bio['query_ids'][0]])
            work=[(q,p) for q in bio['query_ids'] for p in C.PLANS]
            np.random.default_rng(C.SEED+repeat-1).shuffle(work)
            for q,plan in work:
                guard.check(); C.disk_check(); torch.cuda.synchronize()
                st=time.perf_counter(); ct=time.process_time(); top=execute(plan,queries[q]); torch.cuda.synchronize()
                requests.append(dict(model=model_name,repeat=repeat,query_id=q,plan=plan,
                    E2E_s=time.perf_counter()-st,CPU_s=time.process_time()-ct,output_top10=json.dumps(top),
                    probe_scope='one BM25 per BM25/Rerank request; FullV has none',quality_labels_read=False))
        C.table(C.R/'requests.csv',requests)
    C.table(C.R/'setup_components.csv',records)
    if profiled:
        rr=[x for x in blocks if x['kind']=='profiled_encoding_block']
        C.write(C.A/'GPU_profile_summary.json',dict(model=model_name,model_load_GPU_s=next(x['GPU_s'] for x in records if x['component']=='model_load'),
            full_index_GPU_active_s=sum(x['gpu_active_union_seconds'] for x in rr),blocks=len(rr),pages=sum(x['pages'] for x in rr),
            scope='sum of nonoverlapping per-block process-owned GPU unions in separate profiled process; not unprofiled wall'))
    guard.check(); C.disk_check()
    C.write(C.A/'completed.json',dict(status='PASS',run_id=C.RUN,time_bj=C.stamp(),model=model_name,mode=mode,repeat=repeat,
        index=str(index),index_bytes=sum(p.stat().st_size for p in index.rglob('*') if p.is_file()),
        pages=len(selected),max_embedding_error=max(x['maxabs'] for x in equivalence),
        process_wall_s=time.perf_counter()-PROCESS_START,cache_after=C.cache_state(),sealed_reads=0,qrels_reads=0,
        profile_not_counted_as_repeat=profiled))
    print(json.dumps(dict(status='PASS',model=model_name,mode=mode,repeat=repeat,pages=len(selected),time_bj=C.stamp())),flush=True)
finally:
    stop_watch.set(); watch.join()
    guard.close()
