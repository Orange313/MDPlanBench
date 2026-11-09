"""Official fixed Economics assets; default metadata plan, no implied rights grant."""
from pathlib import Path
import argparse,json,urllib.request,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('--destination');p.add_argument('--accept-official-license-terms',action='store_true');a=p.parse_args();lock=json.loads((Path(__file__).parent/'economics_execution_contract.json').read_text())
if not a.destination:print(json.dumps(lock['official_inputs'],indent=2));raise SystemExit(0)
if not a.accept_official_license_terms:p.error('Read and accept upstream dataset and original source terms before acquisition')
dest=Path(a.destination).resolve();dest.mkdir(parents=True,exist_ok=False)
for kind,item in lock['official_inputs'].items():
 if shutil.disk_usage(dest).free<30*2**30:raise RuntimeError('DISK_BLOCKED_30GiB_RESERVE;partialdownloadpreserved')
 out=dest/kind/Path(item['repo_path']).name;out.parent.mkdir();h=hashlib.sha256()
 with urllib.request.urlopen(item['url'],timeout=120) as src,out.open('xb') as target:
  while True:
   block=src.read(2**20)
   if not block:break
   if shutil.disk_usage(dest).free<len(block)+30*2**30:raise RuntimeError('DISK_BLOCKED_PARTIAL_PRESERVED')
   target.write(block);h.update(block)
 assert h.hexdigest()==item['sha256'],'HASH_MISMATCH_PARTIAL_PRESERVED';print(json.dumps({'kind':kind,'sha256':h.hexdigest()}),flush=True)
