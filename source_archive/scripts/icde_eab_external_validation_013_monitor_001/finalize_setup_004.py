from pathlib import Path
import difflib
b=Path(__file__).resolve().parent
for name in ['economics_worker_001.py','summarize_economics_001.py','supervisor_001.py','start_monitor_001.py']:
 p=b/name;t=p.read_text(encoding='utf8').replace('setup_003/','setup_004/')
 if name=='supervisor_001.py':
  old=" for x in protocol['official_inputs'].values():assert C.sha(x['path'])==x['SHA256'],'DATA_HASH_CHANGED'"
  new=old+"\n metadata=json.loads((C.ROOT/'manifests/hr_models_verified.json').read_text());weight=Path(metadata['visual']['local_path'])/'model.safetensors';assert C.sha(weight)==protocol['primary_weight_SHA256'],'WEIGHT_HASH_CHANGED'\n for model in [protocol['frozen_Q_QP'],protocol['RR_adapted']]:assert C.sha(C.ROOT/model['checkpoint'])==model['SHA256'],'POLICY_CHECKPOINT_HASH_CHANGED'"
  assert old in t;t=t.replace(old,new)
 p.write_text(t,encoding='utf8')
t=(b/'setup_monitor_003.py').read_text(encoding='utf8').replace("C.start('setup_003')","C.start('setup_004')").replace("C.finish('setup_003',","C.finish('setup_004',")
with (b/'setup_monitor_004.py').open('x',encoding='utf8') as f:f.write(t)
patch=''
for a,c in [('original_t2_biomedical_exact_004.txt','economics_worker_001.py'),('original_engine_exact_004.txt','engine_frozen_004.py')]:patch+=''.join(difflib.unified_diff((b/a).read_text(encoding='utf8').splitlines(True),(b/c).read_text(encoding='utf8').splitlines(True),fromfile=a,tofile=c))
(b/'worker_format_resource_diff.patch').write_text(patch,encoding='utf8')
