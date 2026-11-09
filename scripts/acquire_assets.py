"""Pinned official assets, explicit terms acknowledgement, no sealed label downloads."""
from pathlib import Path
import argparse,hashlib,json,shutil,urllib.request
G=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['plan','fetch','verify']);p.add_argument('--asset');p.add_argument('--destination',type=Path);p.add_argument('--accept-upstream-terms',action='store_true');p.add_argument('--max-bytes',type=int,default=100_000_000);a=p.parse_args()
 registry=json.loads((G/'config/acquisition_registry.json').read_text())
 if a.mode=='plan':print(json.dumps(registry,indent=2));return
 if not a.asset or not a.destination:p.error('--asset and --destination required')
 x=next((x for x in registry['assets'] if x['id']==a.asset),None)
 if x is None:p.error('Unknown pinned asset; mutable revisions and arbitrary URLs are not accepted')
 if x['sha256'] is None:p.error('MISSING upstream checksum; will not fetch an unverifiable asset')
 dest=a.destination.resolve()
 if dest.is_relative_to(G):p.error('Raw assets must be kept outside the Git worktree')
 if a.mode=='fetch':
  if not a.accept_upstream_terms:p.error('Read the pinned upstream and original-source terms; use --accept-upstream-terms')
  dest.mkdir(parents=True,exist_ok=False);out=dest/Path(x['path']).name;n=0
  req=urllib.request.Request(x['url'],headers={'User-Agent':'MDPlanBench-reproducibility-check/1.0'})
  with urllib.request.urlopen(req,timeout=60) as r,out.open('xb') as f:
   size=r.headers.get('Content-Length')
   if size and int(size)>a.max_bytes:raise RuntimeError('DOWNLOAD_BUDGET_EXCEEDED; no payload downloaded')
   while True:
    b=r.read(2**20)
    if not b:break
    n+=len(b)
    if n>a.max_bytes or shutil.disk_usage(dest).free<len(b)+256*2**20:raise RuntimeError('RESOURCE_BUDGET_EXCEEDED; partial preserved')
    f.write(b)
 else:out=dest/Path(x['path']).name
 h=hashlib.sha256(out.read_bytes()).hexdigest();ok=h==x['sha256']
 receipt=dict(status='PASS_PINNED_BYTES' if ok else 'FAIL_HASH',asset=x['id'],url=x['url'],bytes=out.stat().st_size,sha256=h,expected_sha256=x['sha256'],license_scope=x['license'],qrels_read=False,scope='Byte acquisition and hash verification only; no content evaluation')
 if a.mode=='fetch':(dest/'acquisition_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
 print(json.dumps(receipt,indent=2));return int(not ok)
if __name__=='__main__':raise SystemExit(main())
