"""Package the committed review branch with public small numerical prerequisites."""
from pathlib import Path
import argparse,csv,hashlib,json,re,subprocess,zipfile
from datetime import datetime,timezone,timedelta

ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--scan-only',action='store_true');a=ap.parse_args()
S=Path(__file__).resolve().parent;G=S.parent;O=a.out.resolve();O.mkdir(parents=True,exist_ok=False)
paths=subprocess.check_output(['git','ls-files','posthoc_20261109'],cwd=G,text=True).splitlines()
files=[G/p for p in paths]
source_files=[G/p for p in subprocess.check_output(['git','ls-files','records/021_snapshot','repro/frontier_math.py','LICENSE'],cwd=G,text=True).splitlines()]
assert all(p.exists() for p in files+source_files)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()
for p in files:
    assert p.stat().st_size<5*1024*1024,('Review file unexpectedly large',p)
    assert p.suffix.lower() not in ['.pt','.pth','.bin','.safetensors','.parquet','.zip','.arrow']
    assert 'worker_' not in p.name or not p.name.endswith('_texts.jsonl')
    assert p.name!='HR_ocr_pages.json'
findings=[]
for p in files:
    if p.suffix.lower() not in ['.json','.csv','.md','.py','.txt','.jsonl']:continue
    text=p.read_text(encoding='utf-8-sig')
    for label,pattern in [('private-home',r'/home/(?!\$)[A-Za-z][^/\s"\']+/'),
                          ('backup-user',r'/backup01/[A-Za-z][^/\s"\']+/'),
                          ('github-token',r'gh[pousr]_[A-Za-z0-9]{20,}'),
                          ('private-key',r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----'),
                          ('bearer-credential',r'Bearer\s+[A-Za-z0-9._-]{24,}')]:
        if re.search(pattern,text):findings.append(dict(file=str(p.relative_to(G)),kind=label))
if findings:
    (O/'privacy_scan_failed.json').write_text(json.dumps(findings,indent=2)+'\n')
    raise RuntimeError('Review export still contains disallowed literals; no package created')
if a.scan_only:
    receipt=dict(status='SCOPED_LITERAL_SCAN_PASS',commit=commit,files=len(files),findings=0,package_created=False)
    (O/'privacy_scan.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2));raise SystemExit(0)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries=[dict(path=str(p.relative_to(G)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files+source_files)]
manifest=''.join(z['sha256']+'  '+z['path']+'\n' for z in entries)
readme='''# MDPlanBench post-hoc review package

Review-only supplement; not a new public release or tag. Includes the public
v1.1 small numerical prerequisites, the new post-hoc records/scripts, and MIT
software license. No raw pages, question text, OCR prose, model weights, full
qrels, sealed labels or credentials are included.

From this extracted directory in a clean Python3.11 environment:

    pip install -r posthoc_20261109/requirements-cpu.txt
    python posthoc_20261109/reproduce_posthoc.py --output /path/to/new-empty-replay

See posthoc_20261109/RESULTS_SUMMARY.md and REPRODUCE.md for conclusions, input
boundaries, original versus recomposed cost scopes and conditional inference.
The replay reconstructs archived numbers; it does not repeat OCR or GPU timing.
'''
zip_path=O/'MDPlanBench_posthoc_20261109_review.zip'
with zipfile.ZipFile(zip_path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(files+source_files):z.write(p,str(p.relative_to(G)).replace('\\','/'))
    z.writestr('DELIVERY_MANIFEST.sha256',manifest)
    z.writestr('README_REVIEW_PACKAGE.md',readme)
(O/'DELIVERY_MANIFEST.sha256').write_text(manifest,encoding='utf8')
(O/'package_receipt.json').write_text(json.dumps(dict(status='REVIEW_PACKAGE_CREATED',time_beijing=datetime.now(timezone(timedelta(hours=8))).isoformat(),
    branch='codex/posthoc-20261109',commit=commit,tag=None,public_push=False,files=len(entries)+2,
    scientific_csv_files=sum(p.suffix=='.csv' for p in files),zip_bytes=zip_path.stat().st_size,zip_sha256=sha(zip_path),
    manifest_sha256=hashlib.sha256(manifest.encode()).hexdigest(),privacy_pattern_findings=0,
    limitations='Heuristic literal scan plus scoped content review; not a legal clearance or fresh measurement'),indent=2)+'\n',encoding='utf8')
print((O/'package_receipt.json').read_text(encoding='utf8'))
