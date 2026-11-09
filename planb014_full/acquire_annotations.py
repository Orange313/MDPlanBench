"""Acquire only pinned official queries/qrels into user cache, never into release tree."""
from pathlib import Path
import hashlib,json,urllib.request,argparse,collections,csv
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def acquire(root,cache,workspace):
 import pyarrow.parquet as pq
 ext=root/'planb014_full';locks=json.loads((ext/'official_annotations_lock.json').read_text());side=json.loads((ext/'candidate_and_source_metadata.json').read_text());packs=[]
 for d in side:
  name=d['domain'];data={}
  for kind in ['queries','qrels']:
   item=locks[name][kind];p=cache/name/(kind+'.parquet');p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():
    tmp=p.with_suffix('.download');req=urllib.request.Request(item['url'],headers={'User-Agent':'MDRouter-reproducibility/015'});
    with urllib.request.urlopen(req,timeout=90) as r,tmp.open('xb') as f:
     while True:
      b=r.read(2**20)
      if not b:break
      f.write(b)
    assert sha(tmp)==item['sha256'],str(tmp);tmp.rename(p)
   assert sha(p)==item['sha256'];data[kind]=pq.read_table(p,columns=['query-id','query'] if kind=='queries' else ['query-id','corpus-id','score']).to_pylist()
  queries={int(q['query-id']):q['query'] for q in data['queries']};labels=collections.defaultdict(dict)
  for q in data['qrels']:labels[int(q['query-id'])][int(q['corpus-id'])]=int(q['score'])
  pp={k:v for k,v in d.items() if k not in ['queries','unlabelled_page_doc_map']};pp['quality_path']=d['quality_path'];pp['queries']=[]
  for q in d['queries']:
   q=dict(q);i=q['query_id'];q['query']=queries[i];q['qrels']={str(p):v for p,v in labels[i].items()};q['empty_OCR_relevant']=[p for p in labels[i] if p in d['empty_OCR_pages']];q['page_doc_map']={str(p):d['unlabelled_page_doc_map'].get(str(p)) for p in labels[i]};pp['queries'].append(q)
  packs.append(pp)
 target=workspace/'reports/icde_eab_planb_014/B2_prepare_002/allowed_query_diagnostics.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(packs,ensure_ascii=False,indent=2)+'\n')
 return {'status':'OFFICIAL_HASH_VERIFIED','query_qrels_files':4,'raw_annotations_in_release':False,'cache_is_user_owned':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cache',required=True);p.add_argument('--workspace',required=True);a=p.parse_args();print(json.dumps(acquire(Path(__file__).resolve().parents[1],Path(a.cache).resolve(),Path(a.workspace).resolve())))
