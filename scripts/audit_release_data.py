"""Audit release bytes for raw/large page assets; do not delete source evidence.

Works on an extracted review package or a checkout. Numerical observations,
bootstrap arrays and scientific plots are distinct from original page assets.
"""
from pathlib import Path
import argparse,collections,csv,gzip,hashlib,io,json,re,zipfile
import numpy as np

BAD_EXT={'.parquet','.arrow','.pt','.pth','.safetensors','.ckpt','.bin','.npy','.h5','.hdf5','.onnx','.jpg','.jpeg','.webp','.tif','.tiff','.bmp'}
FIELD=re.compile(rb'"(?:query|question|query_text|markdown|ocr_text|image|embeddings|page_embeddings|qrels)"\s*:')
RAW_TEXT={'query','question','query_text','markdown','ocr_text'}
PLOTS=('records/manuscript_R74_assets/','records/manuscript_R82_assets/','records/diagram_source/',
       'posthoc_20261109/review_002/','posthoc_20261109/independent_001/',
       'posthoc_20261109/E5_analysis_001/','posthoc_20261109/E6_001/analysis_001/',
       'planb014_full/reference_outputs/')

def scan_json(obj,findings,prefix=''):
 if isinstance(obj,dict):
  for key,val in obj.items():
   p=prefix+'/'+key
   if key in RAW_TEXT and isinstance(val,str) and val.strip():findings.append((p,'RAW_QUERY_OR_PAGE_TEXT'))
   elif key in ['image','embeddings','page_embeddings'] and isinstance(val,(dict,list,str)) and val:findings.append((p,'POSSIBLE_PAGE_ASSET'))
   elif key=='qrels' and isinstance(val,dict) and val and all(str(k).lstrip('-').isdigit() for k in val):findings.append((p,'RAW_RELEVANCE_MAP'))
   if isinstance(val,(dict,list)):scan_json(val,findings,p)
 elif isinstance(obj,list):
  for i,val in enumerate(obj):
   if isinstance(val,(dict,list)):scan_json(val,findings,prefix+'/'+str(i))

def inspect(name,b):
 suffix=Path(name).suffix.lower();issues=[];detail='';kind='CODE_CONFIG_DOCUMENTATION_OR_RECORD'
 if suffix in BAD_EXT:return 'FORBIDDEN_RAW_OR_REBUILDABLE_ASSET',[(name,'FORBIDDEN_EXTENSION')],detail
 if suffix in ['.png','.pdf']:
  if not name.startswith(PLOTS):issues.append((name,'UNCLASSIFIED_IMAGE_OR_PDF'))
  return 'SCIENTIFIC_RESULT_PLOT_OR_AUTHOR_DIAGRAM',issues,'Not a corpus page; explicit scientific-asset locations'
 if suffix=='.npz':
  kind='NUMERICAL_FEATURE_OUTCOME_OR_BOOTSTRAP_RECORD'
  if not name.startswith(('posthoc_20261109/','records/021_snapshot/')):issues.append((name,'UNCLASSIFIED_NPZ'))
  with np.load(io.BytesIO(b),allow_pickle=False) as z:
   shapes=[]
   for key in z.files:
    a=z[key];shapes.append(dict(key=key,shape=list(a.shape),dtype=str(a.dtype)))
    if any(k in key.lower() for k in ['page_embedding','passage_embedding','pixel_values']):issues.append((key,'PAGE_ARRAY_NOT_NUMERIC_RECORD'))
    if a.dtype.kind=='O':issues.append((key,'OBJECT_ARRAY_REQUIRES_REVIEW'))
   detail=json.dumps(shapes,sort_keys=True)
  return kind,issues,detail
 if suffix=='.gz':
  b=gzip.decompress(b);name=name[:-3];suffix=Path(name).suffix.lower();kind='COMPRESSED_NUMERICAL_OR_OPERATIONAL_RECORD'
  if suffix in BAD_EXT:issues.append((name,'COMPRESSED_FORBIDDEN_ASSET'))
 if suffix=='.csv':
  header=next(csv.reader(io.StringIO(b.decode('utf-8-sig'))),[]);keys={x.lower() for x in header}
  if keys&RAW_TEXT:issues.append((name,'RAW_TEXT_COLUMN'))
  if {'query-id','corpus-id','score'}<=keys or {'query_id','corpus_id','relevance_grade'}<=keys:issues.append((name,'RAW_QRELS_TABLE'))
  detail='Columns: '+', '.join(header)
 elif suffix in ['.json','.jsonl'] and FIELD.search(b):
  if suffix=='.json':scan_json(json.loads(b.decode('utf-8-sig')),issues)
  else:
   for line in b.decode('utf-8-sig').splitlines():
    if line.strip() and FIELD.search(line.encode('utf8')):scan_json(json.loads(line),issues)
 return kind,issues,detail

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path);ap.add_argument('--zip',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if bool(a.root)==bool(a.zip):ap.error('Choose exactly one of --root or --zip')
 O=a.output.resolve();O.mkdir(parents=True,exist_ok=False);files=[];findings=[];counts=collections.Counter()
 def consume(name,b):
  try:kind,bad,detail=inspect(name,b)
  except Exception as e:kind='UNVERIFIED';bad=[(name,'PARSE_'+type(e).__name__)];detail=''
  counts[kind]+=1;files.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),classification=kind,status='PASS' if not bad else 'REVIEW_REQUIRED',detail=detail))
  for location,reason in bad:findings.append(dict(path=name,location=location,reason=reason))
 if a.zip:
  with zipfile.ZipFile(a.zip) as z:
   for m in z.infolist():
    if not m.is_dir():consume(m.filename,z.read(m))
 else:
  import subprocess
  R=a.root.resolve();names=subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0')
  for name in sorted(set(n for n in names if n)):
   p=R/name
   if p.is_file():consume(name,p.read_bytes())
 for name,rows,cols in [('data_file_inventory.csv',files,list(files[0])),('findings.csv',findings,['path','location','reason'])]:
  with (O/name).open('x',newline='',encoding='utf8') as f:w=csv.DictWriter(f,cols);w.writeheader();w.writerows(rows)
 result=dict(status='PASS_NO_RAW_OR_REBUILDABLE_PAGE_ASSETS' if not findings else 'REVIEW_REQUIRED',files=len(files),classifications=dict(counts),findings=len(findings),removed_assets=0,source_files_modified=0,
  scope='Filename and structured-payload audit, including gzip and NPZ. Source-code literals and SHA256/ID metadata are retained; raw query text, page/OCR text, full qrels, pages and embedding/index payloads are not allowed. Scientific result plots are not original page images.')
 (O/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2));return int(bool(findings))
if __name__=='__main__':raise SystemExit(main())
