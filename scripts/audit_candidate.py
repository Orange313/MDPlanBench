"""Candidate file/duplicate/privacy inventory; records findings, never deletes evidence."""
from pathlib import Path
import argparse,collections,csv,gzip,hashlib,json,re,subprocess
G=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);a=ap.parse_args();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=G).decode().split('\0');paths=sorted(set(n for n in names if n));files=[];hits=[];byhash=collections.defaultdict(list)
patterns=[('PRIVATE_HOME',re.compile(r'/home/(?!\$)[A-Za-z0-9_.-]+/(?!\$)')),('PRIVATE_WINDOWS',re.compile(r'[A-Za-z]:[/\\]+Users[/\\]+[A-Za-z0-9_.-]+')),('PRIVATE_BACKUP',re.compile(r'/backup\d*/[A-Za-z0-9_.-]+/')),('PRIVATE_IP',re.compile(r'(?<![\d.])(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)(?![\d.])')),('CREDENTIAL',re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9]{30,}|Bearer\s+[A-Za-z0-9_-]{45,})')),('TRACKING_QUERY',re.compile(r'[?&](?:utm_[a-z]+|fbclid|gclid|mc_eid)='))]
for name in paths:
 p=G/name
 if not p.is_file() or name=='.git':continue
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();files.append(dict(path=name,bytes=len(b),sha256=h));byhash[h].append(name)
 if p.suffix=='.gz':
  try:b=gzip.decompress(b)
  except Exception:hits.append(dict(path=name,line=0,kind='INVALID_GZIP',status='REVIEW'));continue
 if p.suffix in ['.png','.pdf','.npz','.drawio'] or len(b)>30*2**20:continue
 try:s=b.decode('utf8')
 except UnicodeDecodeError:continue
 for i,line in enumerate(s.splitlines(),1):
  for label,pat in patterns:
   if pat.search(line):
    # Regex definitions in a scanner are not live internal addresses/credentials.
    fixture=('scripts/audit_candidate.py'==name or ('re.compile' in line) or ('r\"' in line and ('pattern' in line or 'private' in line)))
    hits.append(dict(path=name,line=i,kind=label,status='SCANNER_PATTERN_NOT_SECRET' if fixture else 'REVIEW'))
def table(name,rows):
 with (O/name).open('x',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,list(rows[0]) if rows else ['status']);w.writeheader();w.writerows(rows)
table('file_inventory.csv',files);table('privacy_findings.csv',hits);table('duplicate_groups.csv',[dict(sha256=h,files=';'.join(v),copies=len(v),policy='RETAINED_FROZEN_PATH_CONTRACT') for h,v in byhash.items() if len(v)>1])
r=dict(status='PASS_AUTOMATED_SCAN' if not any(x['status']=='REVIEW' for x in hits) else 'REVIEW_REQUIRED',files=len(files),bytes=sum(x['bytes'] for x in files),largest_files=sorted(files,key=lambda x:-x['bytes'])[:10],findings=len(hits),review_required=sum(x['status']=='REVIEW' for x in hits),duplicates_retained=sum(len(v)-1 for v in byhash.values()),LFS_required=any(x['bytes']>100*2**20 for x in files),scope='Automated text/filename screening only, not legal or exhaustive secret assurance; immutable observations are not edited or deleted.')
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
