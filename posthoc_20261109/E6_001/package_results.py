"""Private Orange review package; does not push GitHub or change a license."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,zipfile
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
S=Path(__file__).resolve().parent;G=S.parents[1];rel=S.relative_to(G).as_posix()
files=[G/p for p in subprocess.check_output(['git','ls-files',str(rel)],cwd=G,text=True).splitlines()]
assert files and all(p.stat().st_size<20*2**20 for p in files)
for p in files:
 assert p.suffix not in ['.pt','.safetensors','.bin','.parquet','.arrow']
 if p.suffix in ['.json','.md','.py','.txt','.log','.csv','.jsonl']:
  text=p.read_text(encoding='utf-8-sig')
  assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----',text),p.name
manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (S/'MANIFEST.sha256').read_text().splitlines()}
for p in files:
 if p.name=='MANIFEST.sha256':continue
 assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest[str(p.relative_to(S)).replace('\\','/')],p.name
zpath=a.out/'MDPlanBench_E6_001_review.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,str(p.relative_to(S)))
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()
receipt=dict(status='PRIVATE_REVIEW_PACKAGE',commit=commit,branch='codex/posthoc-20261109',files=len(files),
 zip_bytes=zpath.stat().st_size,zip_sha256=hashlib.sha256(zpath.read_bytes()).hexdigest(),
 manifest_sha256=hashlib.sha256((S/'MANIFEST.sha256').read_bytes()).hexdigest(),public_push=False,new_tag=None,
 scope='No model/page/OCR prose/query-text/qrels files; numerical outputs and source references; private provenance paths retained')
(a.out/'package_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,indent=2))
