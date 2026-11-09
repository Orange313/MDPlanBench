"""Read pinned public README/license endpoints; never infer rights from HTTP success."""
from pathlib import Path
import argparse,datetime,hashlib,json,urllib.request
G=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
 reg=json.loads((G/'config/acquisition_registry.json').read_text());assets={(x['repo'],x['revision'],'datasets') for x in reg['assets']};assets|={(x['repo'],x['revision'],'models') for x in reg['models']};checks=[]
 for repo,rev,kind in sorted(assets):
  for name in ['README.md','LICENSE']:
   url='https://huggingface.co/'+('datasets/' if kind=='datasets' else '')+repo+'/resolve/'+rev+'/'+name
   z=dict(repo=repo,revision=rev,file=name,url=url,status='NOT_VERIFIED',time_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MDPlanBench-reproducibility/1.0'}),timeout=20) as r:
     b=r.read(2_000_001)
     if len(b)>2_000_000:raise ValueError('Metadata budget exceeded')
     z.update(status='PASS_ENDPOINT_BYTES_ONLY',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),http_status=r.status)
     text=b.decode('utf8',errors='replace');z['declared_license_lines']=[s.strip() for s in text.splitlines() if s.lower().startswith('license:') or s.lower().startswith('license_name:')][:5]
   except Exception as exc:z['error_type']=type(exc).__name__;z['error']=str(exc).split('?')[0][:200]
   checks.append(z)
 result=dict(checks=checks,limitation='A card declaration or HTTP200 is not an independent legal clearance; standalone404 is NOT_VERIFIED and never a rights grant. Gemma base terms and source-image exceptions remain separate.',downloaded_corpus=False,downloaded_weights=False)
 (O/'upstream_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(checked=len(checks),verified_endpoints=sum(x['status']=='PASS_ENDPOINT_BYTES_ONLY' for x in checks),not_verified=sum(x['status']=='NOT_VERIFIED' for x in checks))))
if __name__=='__main__':main()
