from pathlib import Path
import difflib
b=Path(__file__).resolve().parent
for name in ['economics_worker_001.py','summarize_economics_001.py','supervisor_001.py','start_monitor_001.py']:
 p=b/name;t=p.read_text(encoding='utf8').replace('setup_002/','setup_003/');p.write_text(t,encoding='utf8')
t=(b/'setup_monitor_002.py').read_text(encoding='utf8').replace("C.start('setup_002')","C.start('setup_003')").replace("C.finish('setup_002',","C.finish('setup_003',")
needle="C.write(C.A/'execution_protocol.json',execproto)"
extra="""execproto['official_inputs']={k:{**v,'sha256':v['SHA256']} for k,v in frozen['official_inputs'].items()}
required={node.slice.value for node in ast.walk(tree) if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name) and node.value.id=='protocol' and isinstance(node.slice,ast.Constant) and isinstance(node.slice.value,str)}
assert required<=set(execproto),required-set(execproto)
assert all(len(x['sha256'])==64 for x in execproto['official_inputs'].values())
rr=C.load('artifacts/icde_evidence_closure_003/E2/candidate_models.json','FIXED_RR_ADAPTED_COMPATIBILITY_NO_FIT')
for target in ['hard','soft']:
 m=next(x for x in rr if x['source']=='Pharma_only' and x['seed']==202610271130 and x['method']=='Q_'+target and x['kappa']==20);a=[np.array(v) for v in m['model']];a[0]=a[0].astype(bool);pred=L.predict(tuple(a),x[None] if False else np.array([f[n] for n in enc.feature_names])[None]);assert pred.shape==(1,4) and np.isfinite(pred).all();smoke.append({'method':'RR_'+target,'synthetic_feature_inference':'PASS','refit':False})
"""
assert needle in t;t=t.replace(needle,extra+'\n'+needle)
with (b/'setup_monitor_003.py').open('x',encoding='utf8') as f:f.write(t)
patch=''
for old,new in [('original_t2_biomedical_exact_004.txt','economics_worker_001.py'),('original_engine_exact_004.txt','engine_frozen_004.py')]:patch+=''.join(difflib.unified_diff((b/old).read_text(encoding='utf8').splitlines(True),(b/new).read_text(encoding='utf8').splitlines(True),fromfile=old,tofile=new))
(b/'worker_format_resource_diff.patch').write_text(patch,encoding='utf8')
