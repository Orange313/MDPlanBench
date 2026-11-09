"""Read-only release-tree privacy/size gate, including compressed text records."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,re,subprocess
G=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 patterns={'private_path':re.compile(r'(?:C:[/\\]Users[/\\][^\s"\'<>]+|/home/[A-Za-z0-9_.-]+[^\s"\'<>]*)'),'private_ip':re.compile(r'(?<!\d)(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)(?!\d)'),'email':re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),'credential':re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9]{32,})')}
 names=[n for n in subprocess.check_output(['git','ls-files','-z'],cwd=G).decode().split('\0') if n];findings=[];sizes=[];allowed=0
 for name in names:
  f=G/name
  if not f.is_file():continue
  b=f.read_bytes();sizes.append((len(b),name))
  if len(b)>50_000_000:findings.append(dict(path=name,rule='OVER_50_MB',matches=1))
  if f.name=='.env' or f.name.startswith('.env.'):findings.append(dict(path=name,rule='ENV_FILE',matches=1))
  try:s=(gzip.decompress(b) if f.suffix=='.gz' else b).decode('utf8')
  except (UnicodeError,OSError):continue
  for rule,pat in patterns.items():
   bad=[]
   search=s
   if rule=='email':search='\n'.join(line for line in s.splitlines() if '@' in line)
   if rule=='private_path' and '/home/' not in s and 'C:' not in s:continue
   for m in pat.finditer(search):
    # Reserved invalid addresses are fixtures; @ in numerical Python is matrix multiplication.
    if rule=='email' and (m.group().endswith('.invalid') or m.group() in ('z.T@np.linalg.solve','lp.x@yt.ravel')):allowed+=1;continue
    bad.append(m)
   if bad:findings.append(dict(path=name,rule=rule,matches=len(bad)))
 with (a.output/'findings.csv').open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,['path','rule','matches']);w.writeheader();w.writerows(findings)
 result=dict(status='PASS' if not findings else 'FAIL',files=len(sizes),tree_bytes=sum(x[0] for x in sizes),largest_file_bytes=max(x[0] for x in sizes),files_over_50_MB=sum(x[0]>50_000_000 for x in sizes),findings=len(findings),reserved_fixture_or_matrix_operator_matches=allowed,license_sha256=hashlib.sha256((G/'LICENSE').read_bytes()).hexdigest(),scope='Current tracked release tree including gzip payloads; Git history is preserved, not rewritten. No sensitive matched text is written to the report.')
 (a.output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2));return int(bool(findings))
if __name__=='__main__':raise SystemExit(main())
