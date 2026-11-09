"""Frozen-data accounting helpers; no fitting, CUDA, qrels or old writes."""
from pathlib import Path
import collections,csv,hashlib,itertools,json
import numpy as np
from scipy.optimize import linprog

PLANS=['Full-Visual','BM25-R50','BM25-R100','BM25'];CAT=np.array([0,2,3])
MODELS=['Ridge_Q','Ridge_QP','LightGBM_Q','LightGBM_QP']
METHODS=PLANS+MODELS+['FitFrozenMix_0.05']
KAPPAS=np.array([0,1,2,5,10,20,40,80,160,320,np.inf])
BUDGETS=np.array([.01,.02,.03,.05,.075,.10]);B=2000;SEED=20261109
SCOPE='recomposed from measured components (offline screening)'
INPUTS={}
def read(p):
    p=Path(p);b=p.read_bytes();INPUTS[str(p)]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    if p.suffix=='.npz':return dict(np.load(p,allow_pickle=False))
    if p.suffix=='.json':return json.loads(b)
    if p.suffix=='.jsonl':return [json.loads(z) for z in b.decode().splitlines()]
    return list(csv.DictReader(b.decode('utf-8-sig').splitlines()))
def jsave(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def csvsave(p,rows):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);rows=list(rows)
    fields=list(dict.fromkeys(k for z in rows for k in z))
    with p.open('x',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def all_data(root):
    a=root/'artifacts/icde_eab_review_strengthening_021'
    meta=read(a/'EX0/domains.json');alloc=read(a/'EX1/predictions_and_allocations.json')
    raw=read(a/'GPU/process_03/partial.jsonl')
    for proc in [6,8,9]:raw.extend(read(a/f'GPU/process_{proc:02d}/requests.csv'))
    assert len(raw)==30942
    lut=collections.defaultdict(list)
    for z in raw:lut[z['domain'],int(z['query_id']),int(z['process']),z['method']].append(z)
    output={}
    for d in meta:
        name=d['domain'];ds=read(a/f'EX0/{name}.npz');ids=ds['qids'].astype(int);n=len(ids)
        time=np.empty((n,3,9));bm=np.zeros_like(time);signal=np.zeros_like(time);acts=np.empty((n,9),int)
        for i,q in enumerate(ids):
            for pi,proc in enumerate([6,8,9] if name=='Economics' else [3,8,9]):
                for j,m in enumerate(METHODS):
                    rr=lut[name,int(q),proc,m];assert len(rr)==3
                    aa={z['action'] for z in rr};assert len(aa)==1
                    acts[i,j]=PLANS.index(next(iter(aa)))
                    time[i,pi,j]=np.mean([float(z['E2E_s']) for z in rr])
                    bm[i,pi,j]=np.mean([float(z['BM_search_s']) for z in rr])
                    signal[i,pi,j]=np.mean([sum(float(z[k]) for k in ['Q_s','Pstats_s','predict_s']) for z in rr])
        y=ds['Y'][:,0,:4]
        output[name]=dict(name=name,meta=d,ids=ids,groups=ds['groups'],old=ds,t=time,bm=bm,signal=signal,
                          acts=acts,static=time[:,:,:4],risk=y,alloc=alloc[name])
    return output
def chosen_cost(d,method,actions):
    """Transfer the archived signed accounting difference; preserve same action exactly.

    The context transfer is an explicit offline assumption, not a measured
    response under a new action. A changed QP FullV fallback pays the search
    that is already included in each matched BM static path.
    """
    j=METHODS.index(method);s=d['static'];old=d['acts'][:,j]
    original=s[np.arange(len(old))[:,None],np.arange(3)[None,:],old[:,None]]
    actions=np.asarray(actions,int)
    new=s[np.arange(len(old))[:,None],np.arange(3)[None,:],actions[:,None]]
    ans=d['t'][:,:,j]+(new-original)
    if method.endswith('_QP'):
        ans=ans+d['bm'][:,:,j]*((actions==0).astype(int)-(old==0).astype(int))[:,None]
    return ans
def kappa_actions(d,method,kappa):
    if kappa==0:return np.full(len(d['ids']),3,int)
    if np.isinf(kappa):return np.zeros(len(d['ids']),int)
    c=np.array(d['meta']['cvec'])[CAT];c=c/c[0]
    pr=np.maximum(np.asarray(d['alloc'][method]['prediction']),0)
    return CAT[np.argmin(c+kappa*pr,axis=1)]
def folds(groups,seed):
    u=np.unique(groups);rng=np.random.default_rng(seed);rng.shuffle(u);counts=np.zeros(5,int);out=np.empty(len(groups),int)
    for g in u:
        j=int(np.argmin(counts));mask=groups==g;out[mask]=j;counts[j]+=mask.sum()
    assert all(not set(groups[out==k])&set(groups[out!=k]) for k in range(5))
    return out
def mix_lp(r,c,b):
    z=linprog(c,A_ub=[r],b_ub=[b+1e-12],A_eq=[np.ones(len(c))],b_eq=[1],bounds=(0,1),method='highs')
    assert z.success,z.message
    return z.x
def env(r,c,b):
    r,c=np.atleast_2d(r),np.atleast_2d(c);b=np.broadcast_to(b,(len(r),))
    out=np.where(r<=b[:,None]+1e-12,c,np.inf).min(1)
    for j,k in itertools.combinations(range(r.shape[1]),2):
        den=r[:,k]-r[:,j];w=np.divide(b-r[:,j],den,out=np.zeros(len(r)),where=abs(den)>1e-12)
        v=(1-w)*c[:,j]+w*c[:,k];ok=(abs(den)>1e-12)&(w>=0)&(w<=1)
        out=np.minimum(out,np.where(ok,v,np.inf))
    return out
def hull(r,c):
    points={}
    for x,y in zip(r,c):points[float(x)]=min(float(y),points.get(float(x),float('inf')))
    out=[]
    for p in sorted(points.items()):
        while len(out)>=2:
            x,y=out[-2:]
            cross=(y[0]-x[0])*(p[1]-y[1])-(y[1]-x[1])*(p[0]-y[0])
            if cross>0:break
            out.pop()
        out.append(p)
    return np.asarray(out)
def evaluate_hull(h,x,bm_r,bm_c):
    return np.where(np.asarray(x)>bm_r,bm_c,np.interp(np.asarray(x),h[:,0],h[:,1]))
def boot_indices(groups):
    rng=np.random.default_rng(SEED);u=np.unique(groups)
    ix=[np.concatenate([np.flatnonzero(groups==g) for g in rng.choice(u,len(u),replace=True)]) for _ in range(B)]
    return ix,np.random.default_rng(SEED).integers(0,3,(B,3))
def save_indices(path,d,ix,proc):
    np.savez_compressed(path,query_ids=d['ids'],groups=d['groups'],offsets=np.r_[0,np.cumsum([len(z) for z in ix])],
        query_row_indices=np.concatenate(ix).astype(np.int32),process_indices=proc.astype(np.int16),seed=SEED)
