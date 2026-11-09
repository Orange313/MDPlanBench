"""Hash verification independent of numerical reconstruction."""
from pathlib import Path
import argparse,hashlib,json
G=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,default=G/'MANIFEST.sha256');a=ap.parse_args();bad=[];n=0
for line in a.manifest.read_text(encoding='utf8').splitlines():
 h,s=line.split('  ',1);p=(G/s).resolve();n+=1
 if not p.is_relative_to(G) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:bad.append(s)
print(json.dumps(dict(status='PASS' if not bad else 'FAIL',files=n,failures=bad),indent=2));raise SystemExit(bool(bad))
