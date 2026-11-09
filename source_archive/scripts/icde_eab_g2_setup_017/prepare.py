"""Verify frozen assets and freeze G2 before any CUDA/model load."""
import common as C
import importlib.metadata, json, pathlib, subprocess, shutil

C.start('preflight_001')
bio = C.load('artifacts/icde_eab_independent_007/T1/biomedical_frozen_protocol.json')
checks = []
def check(path, expected, role):
    p = pathlib.Path(path); p = p if p.is_absolute() else C.ROOT / p
    actual = C.sha(p)
    checks.append(dict(path=str(p), expected=expected, actual=actual, bytes=p.stat().st_size, role=role, status='PASS' if actual == expected else 'FAIL'))
    assert actual == expected, 'ASSET_HASH_MISMATCH ' + str(p)

for rel, h in bio['code_SHA256'].items(): check(rel, h, 'FROZEN_007_CODE')
for name in ['corpus', 'queries']:
    x = bio['official_inputs'][name]; check(x['path'], x['sha256'], 'PUBLIC_BIOMEDICAL_' + name)
check('artifacts/icde_eab_independent_007/T1_preparation/ocr_001/pages.json', bio['OCR']['pages_SHA256'], 'SHARED_OLD_OCR')
models = C.load('manifests/hr_models_verified.json')
for x in models['visual']['files']: check(x['path'], x['sha256'], 'COLQWEN_CONFIG')
weights = list(pathlib.Path(models['visual']['local_path']).glob('*.safetensors'))
assert len(weights) == 1, 'EXPECTED_PINNED_SINGLE_COLQWEN_WEIGHT'
check(weights[0], models['visual']['weight_sha256'], 'COLQWEN_WEIGHT')
prep = C.load('artifacts/icde_eab_main_006/X1/preparation.json')
for x in C.load('reports/icde_eab_main_006/X1/model_asset_checks.csv'):
    check(pathlib.Path(prep['model_path'][x['repository']]) / x['file'], x['actual_SHA256'], 'COLPALI_PINNED_ASSET')
index_inputs = {}; index_bytes = 0
for model, name in [('ColQwen2','icde_eab_independent_007_biomedical_colqwen_001'), ('ColPali','icde_eab_lastmile_008_biomedical_colpali_001')]:
    p = C.ROOT / 'cache/indexes' / name
    manifest = C.load(p / 'index_manifest.json')
    for f, h in manifest['files'].items(): check(p / f, h, 'IMMUTABLE_REFERENCE_INDEX')
    nbytes = sum((p / f).stat().st_size for f in manifest['files'])
    index_bytes += nbytes
    index_inputs[model] = dict(path=str(p), manifest_SHA256=C.sha(p / 'index_manifest.json'), registered_bytes=nbytes)
primary_budget = 3 * index_bytes
need = primary_budget + 8 * 2**30
assert shutil.disk_usage(C.ROOT).free >= need, 'REVISED_DISK_GATE_FAILED'
packages = {x: importlib.metadata.version(x) for x in ['torch','transformers','colpali-engine','numpy','peft','safetensors']}
assert packages['torch'] == '2.5.1+cu121', 'FROZEN_TORCH_VERSION_CHANGED'
C.table(C.R / 'asset_hash_checks.csv', checks)
C.write(C.ART / 'asset_lock.json', dict(time_bj=C.stamp(), files=checks, inputs=index_inputs,
    packages=packages, git_commit=subprocess.check_output(['git','-C',str(C.ROOT),'rev-parse','HEAD'],text=True).strip()))
sources = [*sorted((C.ROOT / 'scripts' / C.RUN).glob('*.py')),
    C.ROOT/'src/mdrouter_v5/gpu_accounting.py', C.ROOT/'scripts/cross_domain_four_plan_001.py',
    C.ROOT/'scripts/icde_eab_independent_007/engine_exact_004.py',
    C.ROOT/'scripts/icde_eab_independent_007/colpali_loader_003.py',
    C.ROOT/'scripts/icde_eab_submission_gate_009/gpu_profile_001.py']
protocol = dict(run_id=C.RUN, status='FROZEN_BEFORE_NEW_G2_COSTS', time_bj=C.stamp(),
    authority='Orange26_R3_user_approved_resource_amendment',
    authority_SHA256='3240bb8f352526dbd6ebf335108e068d977fdfc4fafadc05261a8ebbd43e1ecf',
    prior_authority_SHA256='9859b58a62fb20509b7d17de9d639b5ac51b8ed09f014d6c17101db6b17b7d89',
    gpu=3, maximum_simultaneous_GPUs=1, independent_unprofiled_processes_per_model=3,
    corpus_pages=1016, corpus=bio['official_inputs']['corpus'], public_queries=bio['official_inputs']['queries'],
    queries=160, smoke_pages=8, smoke_rule='first8 numeric corpus IDs; no quality-based selection',
    code_SHA256={str(p.relative_to(C.ROOT)): C.sha(p) for p in sources}, asset_lock_SHA256=C.sha(C.ART/'asset_lock.json'),
    models=models['visual']['revision'], colpali_models=prep['model_path'], index_inputs=index_inputs,
    index_estimated_primary_bytes=primary_budget, auxiliary_budget_bytes=3*2**30, reserve_bytes=5*2**30,
    start_free_required_bytes=need, start_free_actual_bytes=shutil.disk_usage(C.ROOT).free,
    auxiliary_scope='traces, reports, adapter overlays, smoke and separate profile indexes; all retained',
    model_seed=C.SEED, order_seed=20261102, batch_size=2, parquet_batch_size=32,
    torch_CPU_threads=1, OMP_threads=1, TF32=False, numerical_tolerance_maxabs=1e-3,
    full_sequence=[['ColQwen2',1],['ColPali',1],['ColPali',2],['ColQwen2',2],['ColQwen2',3],['ColPali',3]],
    profile_sequence=['ColQwen2','ColPali'], profile_scope='separate model-load and full1016 encoding/serialization; never combine with unprofiled wall',
    timers='synchronized wall and process CPU; encoding+serialization timed; equivalence/hash validation outside build timer; no fsync/storage-cold claim',
    warm='same new process/cohort; all160 public IDs x4 static plans once/process after3 warmups; no qrels; no Serving claim',
    cache='no eviction or global changes; processcold only; hashes warm OS cache; log loadavg/meminfo/CPU external activity',
    GPU_guard='3 idle checks before each process; inherited100ms NVML ResourceGuard plus own-process abort watchdog',
    disk_guard='200ms free-space check; every5s auxiliary cap; abort OWN PROCESS only, preserve partials',
    lifecycle=dict(N=[100,1000,10000,100000], OCR_shared_seconds=407.725,
        scenarios=['OCR_EXCLUSIVE_NEW_INDEX','OCR_SHARED_HALF_NEW_INDEX','OCR_PREPAID_NEW_INDEX','EXISTING_INDEX_OCR_NEW','EXISTING_INDEX_OCR_PREPAID','ALREADY_RESIDENT_ALL_PREPAID'],
        uncertainty='three observed independent process ranges, not production quantile confidence; no cross-cohort speedup; old009 shown separately',
        setup='model_load + adapter_overlay + index residency + BM25 if needed; CUDA init separately; index build separately; OCR once only'),
    frozen005_modified=False, epsilon=.05, delta=.01, sealed_reads=0, new_K1='NOT_CERTIFIED',
    failure_policy='stop sequence on failed gate/worker; no parameter retries; preserve every partial/negative result')
C.write(C.ART/'protocol.json', protocol)
C.write(C.R/'preflight_manifest.json', dict(run_id=C.RUN, time_bj=C.stamp(), status='PASS_ASSET_AND_REVISED_DISK_PREFLIGHT',
    protocol_SHA256=C.sha(C.ART/'protocol.json'), asset_lock_SHA256=C.sha(C.ART/'asset_lock.json'),
    files_verified=len(checks), free_GiB=shutil.disk_usage(C.ROOT).free/2**30,
    required_GiB=need/2**30, CUDA_started=False, sealed_reads=0))
print(json.dumps(C.load(C.R/'preflight_manifest.json')), flush=True)
