from pathlib import Path
import difflib
b=Path(__file__).resolve().parent
for name in ['economics_worker_001.py','summarize_economics_001.py','supervisor_001.py','start_monitor_001.py']:
 p=b/name;t=p.read_text(encoding='utf8').replace('setup_004/','setup_005/')
 if name in ['supervisor_001.py','start_monitor_001.py']:t=t.replace("runtime=C.ART/'runtime'","runtime=C.ART/'runtime_002'").replace("runtime=a/'runtime'","runtime=a/'runtime_002'")
 if name=='supervisor_001.py':
  t=t.replace("attempt=f'attempt_{attempts:03d}'","attempt=f'auto2_attempt_{attempts:03d}'")
  old="adir=C.ART/attempt;adir.mkdir(exist_ok=False);C.write(adir/'three_idle_checks.json',snaps)"
  new="adir=C.ART/attempt;physical=C.STORAGE/'monitor_artifacts'/attempt;physical.mkdir(parents=True,exist_ok=False);adir.symlink_to(physical,target_is_directory=True);C.write(adir/'three_idle_checks.json',snaps)"
  assert old in t;t=t.replace(old,new)
 p.write_text(t,encoding='utf8')
t=(b/'setup_monitor_004.py').read_text(encoding='utf8').replace("C.start('setup_004')","C.start('setup_005')").replace("C.finish('setup_004',","C.finish('setup_005',")
with (b/'setup_monitor_005.py').open('x',encoding='utf8') as f:f.write(t)
patch=''
for a,c in [('original_t2_biomedical_exact_004.txt','economics_worker_001.py'),('original_engine_exact_004.txt','engine_frozen_004.py')]:patch+=''.join(difflib.unified_diff((b/a).read_text(encoding='utf8').splitlines(True),(b/c).read_text(encoding='utf8').splitlines(True),fromfile=a,tofile=c))
(b/'worker_format_resource_diff.patch').write_text(patch,encoding='utf8')
