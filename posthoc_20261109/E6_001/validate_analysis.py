"""Synthetic arithmetic validation only: NEVER an E6 GPU result."""
from pathlib import Path
import argparse,csv,json,subprocess,tempfile
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
S=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='E6_SYNTHETIC_ONLY_',dir=a.out));I=T/'input';P=T/'preflight';I.mkdir();P.mkdir()
def save(p,x):p.write_text(json.dumps(x)+'\n')
ids=list(range(160));save(P/'query_ids.json',ids);save(I/'resource_guard.json',dict(valid=True,foreign_pids=[],errors=[],scope='MOCK_SYNTHETIC'))
save(I/'top10_gate.json',dict(PASS=True,scope='MOCK_SYNTHETIC'));save(I/'three_idle_checks.json',[dict(PASS=True,scope='MOCK_SYNTHETIC')]*3);save(I/'completed.json',dict(scope='MOCK_SYNTHETIC'))
methods=['Full-Visual','BM25-R50','BM25-R100','BM25','Q_regret','QP_regret','RandomMix','RR_hard','RR_soft']
seq=['A','B','A1','B3','B3','A1','B','A'];base={'A':60.,'B':30.,'A1':50.,'B3':40.};rows=[];tele=[]
for bi,s in enumerate(seq,1):
 reps=3 if s in ['A','B3'] else 1;mm=methods if s in ['A','A1'] else methods[:4]
 for q in ids:
  for m in mm:
   for rep in range(1,reps+1):
    offset=rep-2 if reps==3 else 0
    rows.append(dict(block=bi,schedule=s,query_id=q,method=m,repeat=rep,legacy_repeat=4-rep if reps==3 else 1,
      E2E_s=(base[s]+q/159+bi/10+offset)/1000))
 save(I/f'block_{bi:02d}.json',dict(block=bi,schedule=s,status='COMPLETE',start_monotonic=bi*100,end_monotonic=bi*100+50,scope='MOCK_SYNTHETIC'))
 for j in range(5):tele.append(dict(monotonic=bi*100+j,SM_clock_MHz=1500,memory_clock_MHz=8000,temperature_C=40,power_W=180,GPU_util_pct=50))
for p,rr in [(I/'requests.csv',rows),(I/'nvidia_smi.csv',tele)]:
 with p.open('w',newline='') as f:w=csv.DictWriter(f,list(rr[0]));w.writeheader();w.writerows(rr)
import sys
with (a.out/'synthetic_validation.log').open('x') as f:subprocess.run([sys.executable,str(S/'analyze_e6.py'),'--input',str(I),'--preflight',str(P),'--out',str(T/'analysis')],check=True,stdout=f,stderr=subprocess.STDOUT)
z=json.loads((T/'analysis/analysis_summary.json').read_text());assert z['status']=='DONE'
assert abs(z['A_minus_B']['mean_ms']-30)<1e-10 and abs(z['A_minus_B']['low95_ms']-30)<1e-10 and abs(z['A_minus_B']['high95_ms']-30)<1e-10
expected={'method_combination':20,'timing_repetitions':10,'interaction':0}
for x in z['factorial_effects']:assert all(abs(x[k]-expected[x['contrast']])<1e-10 for k in ['mean_ms','low95_ms','high95_ms'])
with (T/'analysis/repeat_differences.csv').open() as f:
 for x in csv.DictReader(f):assert abs(float(x['mean_ms'])-{'first_minus_second':-1,'first_minus_third':-2,'first_minus_mean23':-1.5}[x['contrast']])<1e-10
save(a.out/'validation_receipt.json',dict(status='PASS_SYNTHETIC_ARITHMETIC_ONLY',actual_GPU_jobs=0,real_queries_read=0,
 AB_ms=30,method_effect_ms=20,repetition_effect_ms=10,interaction_ms=0,
 tests='Paired-query nuisance cancellation, balanced linear block drift, chronological repeats independent of shuffled legacy labels',
 synthetic_fixture=str(T),NOT_AN_EXPERIMENT_RESULT=True))
print((a.out/'validation_receipt.json').read_text(),flush=True)
