"""CPU-only hardware-path plan/preflight; deliberately does not auto-start CUDA."""
from pathlib import Path
import argparse,hashlib,json
G=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plan',action='store_true');ap.add_argument('--check',action='store_true');ap.add_argument('--asset-root',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
stages=json.loads((G/'config/hardware_stage_registry.json').read_text())
if not a.check:print(json.dumps(stages,indent=2));raise SystemExit(0)
if not a.asset_root or not a.output:ap.error('--check requires --asset-root and a fresh --output')
O=a.output.resolve();O.mkdir(parents=True,exist_ok=False);R=a.asset_root.resolve();checks=[]
for z in json.loads((G/'config/acquisition_registry.json').read_text())['assets']:
 p=R/z['repo'].split('/')[-1]/z['path']
 if not p.exists():status='MISSING';h=None
 else:
  # Byte checksum only; no parsed annotation or label access.
  if '/qrels/' in p.as_posix():status='NOT_READ_IN_PREFLIGHT';h=None
  else:
   h=hashlib.sha256(p.read_bytes()).hexdigest();status='PASS' if h==z['sha256'] else 'FAIL_HASH'
 checks.append(dict(asset=z['id'],status=status,sha256=h))
r=dict(status='PARTIAL_PREFLIGHT_ONLY',checks=checks,GPU_started=False,sealed_labels_read=0,full_suite_status='MISSING_PORTABLE_END_TO_END_HARNESS',reason='Archived workers require original-layout view/manifests and a separate hardware validation. No GPU command is launched by preflight.')
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
