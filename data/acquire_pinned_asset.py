"""Explicit official pinned downloads; plan mode is the default, no bulk labels."""
import argparse,json,pathlib,urllib.request,hashlib,shutil
ap=argparse.ArgumentParser();ap.add_argument('--lock',type=pathlib.Path,default=pathlib.Path(__file__).with_name('official_asset_checksums.json'));ap.add_argument('--fetch',type=int);ap.add_argument('--destination',type=pathlib.Path);ap.add_argument('--accept-source-license',action='store_true');a=ap.parse_args()
rows=json.loads(a.lock.read_text(encoding='utf8'))['assets']
if a.fetch is None:print(json.dumps(rows,indent=2));raise SystemExit()
assert a.accept_source_license and a.destination,'Read the official source license and provide an exclusive destination.'
x=rows[a.fetch];assert x['url'].startswith('https://huggingface.co/') and len(x['sha256'])==64
a.destination.mkdir(parents=True,exist_ok=False);p=a.destination/'asset';h=hashlib.sha256()
with urllib.request.urlopen(x['url'],timeout=120) as r,p.open('xb') as f:
 while True:
  b=r.read(2**20)
  if not b:break
  if shutil.disk_usage(a.destination).free<2**30:raise RuntimeError('DISK_BLOCKED_PARTIAL_PRESERVED')
  f.write(b);h.update(b)
assert h.hexdigest()==x['sha256'],'HASH_MISMATCH_PARTIAL_PRESERVED'
print(json.dumps(dict(status='PASS_PINNED_BYTES',asset=x['path'],sha256=h.hexdigest())))
