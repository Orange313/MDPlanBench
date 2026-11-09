"""Paired query bootstrap for the preregistered resident 2x2 E6 experiment."""
from pathlib import Path
import argparse,csv,hashlib,json
from datetime import datetime,timezone,timedelta
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--preflight',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
I=a.input;O=a.out;O.mkdir(parents=True,exist_ok=False);hashes={}
def read(p):
 b=p.read_bytes();hashes[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 return json.loads(b) if p.suffix=='.json' else list(csv.DictReader(b.decode('utf-8-sig').splitlines()))
def save(name,x):(O/name).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def table(name,rr):
 with (O/name).open('x',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,list(dict.fromkeys(k for z in rr for k in z)));w.writeheader();w.writerows(rr)
def md(headers,rows):return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+['|'+'|'.join(map(str,r))+'|' for r in rows])
ids=list(map(int,read(a.preflight/'query_ids.json')));pos={q:i for i,q in enumerate(ids)};assert len(ids)==160
raw=read(I/'requests.csv') if (I/'requests.csv').exists() else []
bs=[read(p) for p in sorted(I.glob('block_*.json'))];complete=[b for b in bs if b['status']=='COMPLETE']
guard=read(I/'resource_guard.json') if (I/'resource_guard.json').exists() else None
idle=read(I/'three_idle_checks.json') if (I/'three_idle_checks.json').exists() else []
top=read(I/'top10_gate.json') if (I/'top10_gate.json').exists() else None
tele=read(I/'nvidia_smi.csv') if (I/'nvidia_smi.csv').exists() else []
done=read(I/'completed.json') if (I/'completed.json').exists() else None
abort=read(I/'abort.json') if (I/'abort.json').exists() else read(I/'failure.json') if (I/'failure.json').exists() else read(I/'NOT_RUN.json') if (I/'NOT_RUN.json').exists() else None
valid=bool(guard and guard['valid'] and top and top['PASS'] and len(idle)==3 and all(x['PASS'] for x in idle))
status='DONE' if valid and len(complete)==8 and done else 'PARTIAL' if raw else 'NOT_RUN'
expected_total=16640
if status=='DONE':assert len(raw)==expected_total and sum(z['method']=='Full-Visual' for z in raw)==2560
ix=np.random.default_rng(20261109).integers(0,160,(2000,160),dtype=np.int32)
np.savez_compressed(O/'bootstrap_indices.npz',query_ids=ids,query_indices=ix,seed=20261109)
def estimate(x):
 draws=x[ix].mean(1);lo,hi=np.quantile(draws,[.025,.975]);return dict(mean_ms=float(x.mean()),low95_ms=float(lo),high95_ms=float(hi)),draws
def show(z):return f"{z['mean_ms']:.6f} [{z['low95_ms']:.6f}, {z['high95_ms']:.6f}]"
schedule_rows=[];by_schedule={};by_first={};perblock={};diag=[];block_rows=[];label_audit=[];draws_saved={}
for b in complete:
 bi=b['block'];label=b['schedule'];reps=3 if label in ['A','B3'] else 1
 rr=[z for z in raw if int(z['block'])==bi and z['method']=='Full-Visual'];assert len(rr)==160*reps
 cube=np.full((160,reps),np.nan)
 for z in rr:
  qi=pos[int(z['query_id'])];ri=int(z['repeat'])-1;assert np.isnan(cube[qi,ri]);cube[qi,ri]=1000*float(z['E2E_s'])
 assert np.isfinite(cube).all();perblock[bi]=cube
 ss=[z for z in tele if b['start_monotonic']<=float(z['monotonic'])<=b['end_monotonic']]
 def avg(k):
  v=[float(z[k]) for z in ss if z.get(k) not in ['',None]];return float(np.mean(v)) if v else None
 block_rows.append(dict(block=bi,schedule=label,FullV_mean_ms=float(cube.mean()),FullV_first_ms=float(cube[:,0].mean()),FullV_queries=160,
  FullV_requests=len(rr),wall_s=b['end_monotonic']-b['start_monotonic'],GPU_samples=len(ss),
  SM_clock_MHz=avg('SM_clock_MHz'),memory_clock_MHz=avg('memory_clock_MHz'),temperature_C=avg('temperature_C'),
  power_W=avg('power_W'),GPU_util_pct=avg('GPU_util_pct')))
 label_audit.append(dict(block=bi,schedule=label,FullV_requests=len(rr),legacy_repeat_not_chronological=sum(z['repeat']!=z['legacy_repeat'] for z in rr)))
for label in ['A','B','A1','B3']:
 blocks=[b for b in complete if b['schedule']==label]
 if not blocks:continue
 allq=np.mean([perblock[b['block']].mean(1) for b in blocks],axis=0)
 first=np.mean([perblock[b['block']][:,0] for b in blocks],axis=0);by_schedule[label]=allq;by_first[label]=first
 for estimator,x in [('all_repeats',allq),('first_only',first)]:
  z,draw=estimate(x);schedule_rows.append(dict(schedule=label,estimator=estimator,completed_blocks=len(blocks),queries=160,**z));draws_saved[label+'_'+estimator]=draw
 if label in ['A','B3']:
  arr=np.mean([perblock[b['block']] for b in blocks],axis=0)
  for name,x in [('first_minus_second',arr[:,0]-arr[:,1]),('first_minus_third',arr[:,0]-arr[:,2]),('first_minus_mean23',arr[:,0]-arr[:,1:].mean(1))]:
   z,draw=estimate(x);diag.append(dict(schedule=label,contrast=name,**z));draws_saved[label+'_'+name]=draw
effects=[]
for estimator,d in [('all_repeats',by_schedule),('first_only',by_first)]:
 contrasts={}
 if 'A' in d and 'B' in d:contrasts['A_minus_B']=d['A']-d['B']
 if len(d)==4:
  contrasts.update(method_combination=(d['A']+d['A1']-d['B']-d['B3'])/2,
   timing_repetitions=(d['A']+d['B3']-d['A1']-d['B'])/2,interaction=(d['A']-d['A1'])-(d['B3']-d['B']))
 for name,x in contrasts.items():
  z,draw=estimate(x);effects.append(dict(estimator=estimator,contrast=name,**z));draws_saved[name+'_'+estimator]=draw
np.savez_compressed(O/'bootstrap_draws.npz',**draws_saved)
for name,rr in [('schedule_means.csv',schedule_rows),('factorial_effects.csv',effects),('repeat_differences.csv',diag),('block_gpu_metrics.csv',block_rows),('repeat_label_audit.csv',label_audit)]:
 if rr:table(name,rr)
ab=next((z for z in effects if z['estimator']=='all_repeats' and z['contrast']=='A_minus_B'),None)
if status!='DONE' or not ab:verdict='INSUFFICIENT_INCOMPLETE_OR_INVALID_GATE'
elif ab['low95_ms']>=17:verdict='REPRODUCED'
elif ab['low95_ms']<=0<=ab['high95_ms']:verdict='NOT_REPRODUCED'
elif ab['high95_ms']<0:verdict='NOT_REPRODUCED_DIRECTION_REVERSED'
else:verdict='PARTIALLY_REPRODUCED'
effect_main=[z for z in effects if z['estimator']=='all_repeats' and z['contrast']!='A_minus_B']
if verdict=='REPRODUCED':
 largest=max(effect_main,key=lambda z:abs(z['mean_ms']));conclusion=f"按预登记门槛复现；本轮最大绝对分解项为{largest['contrast']}（{largest['mean_ms']:.3f}ms），但单进程相关结果不能单独证明GPU时钟或温度因果。"
elif ab:
 conclusion=f"{verdict}：本轮A−B={ab['mean_ms']:.3f}ms，不能据此认定原34.0ms跨批次差异的来源；方法组合/重复次数/交互项分别见下表，不改旧70.22/36.22ms。"
else:conclusion='未完成合法完整对照，不能归因；保留中止前全部记录。'
save('analysis_summary.json',dict(status=status,verdict=verdict,conclusion=conclusion,queries=160,requests=len(raw),completed_blocks=len(complete),
 idle_gate=bool(len(idle)==3 and all(x['PASS'] for x in idle)),ResourceGuard_valid=bool(guard and guard['valid']),top10_gate=bool(top and top['PASS']),
 A_minus_B=ab,factorial_effects=effect_main,bootstrap_repeats=2000,bootstrap_seed=20261109,source_guard=guard and dict(valid=guard['valid'],foreign_pids=guard['foreign_pids'],errors=guard['errors']),
 limitations=['Intervals pair queries across eight fixed blocks; blocks/repeats are not independent processes or new queries.',
  'First/second/third mean actual chronological occurrence within block, not pre-shuffle legacy labels.',
  'Warm resident single-request experiment; no Serving or new risk certificate; GPU metrics are correspondence, not proof of clock causality.']))
def nfmt(x):return 'MISSING' if x is None else f'{x:.3f}'
lines=['# E6_RESULTS — FullV两倍延迟差异定位',f"实际分析时间：{datetime.now(timezone(timedelta(hours=8))).isoformat()}。POSTHOC系统诊断；不写论文正文。",f'**状态：{status}；判定：{verdict}。**',
 '## 闸门',f"三次空闲检查：{bool(len(idle)==3 and all(x['PASS'] for x in idle))}；ResourceGuard：{bool(guard and guard['valid'])}；FullV160查询Top10：{bool(top and top['PASS'])}。全部逐请求FullV也对账。",
 f'完成块数{len(complete)}/8，请求{len(raw)}/{expected_total}。重复请求不增加独立查询数。'+(f' 中止原因：{abort}' if abort else ''),
 '## 四调度FullV均值 [配对查询95%区间]（ms）',
 md(['调度','完成块','全部重复均值 [95%]','仅实际第1次 [95%]'],[[label,
  next(z['completed_blocks'] for z in schedule_rows if z['schedule']==label),
  show(next(z for z in schedule_rows if z['schedule']==label and z['estimator']=='all_repeats')),
  show(next(z for z in schedule_rows if z['schedule']==label and z['estimator']=='first_only'))] for label in ['A','B','A1','B3'] if label in by_schedule]),
 '主均值先在查询/块内平均重复，再平均同调度两块。区间条件于固定块、本进程、设备和语料；同一组查询索引同时重采各块，2000次，seed20261109，不重采块。',
 '## A−B与2×2分解（ms）',md(['估计器','对照/效应','均值 [95%]'],[[z['estimator'],z['contrast'],show(z)] for z in effects]),
 '旧对照70.22−36.22=34.0ms；预登记lower95≥17ms为复现，包含0为未复现，0<lower95<17为部分复现；完全负向另标方向相反。未通过资源/正确性或未完成8块时不作完整复现判断。',
 '## 重复序号诊断（ms）',md(['调度','差值','均值 [95%]'],[[z['schedule'],z['contrast'],show(z)] for z in diag]),
 '全局shuffle后旧k标签不代表实际先后；本节按每查询/方法在块内的实际到达顺序定义1/2/3，原legacy_repeat另存。重复之间可能插入其他请求，不能称连续微基准。',
 '## 各块GPU状态与FullV延迟',md(['块','调度','FullV ms','SM MHz','显存MHz','温度°C','功耗W','GPU利用率%','样本数'],[[z['block'],z['schedule'],nfmt(z['FullV_mean_ms']),nfmt(z['SM_clock_MHz']),nfmt(z['memory_clock_MHz']),nfmt(z['temperature_C']),nfmt(z['power_W']),nfmt(z['GPU_util_pct']),z['GPU_samples']] for z in block_rows]),
 '1秒nvidia-smi样本按其采样单调时间落入块start/end配对。均值对应不等于时钟或温度的因果证明；不计算查询能耗。',
 '## 一句话结论',conclusion,
 '## 输入、代码与复现边界','先提交PLAN，再登记作者对全局shuffle与内存BM25初始化的明确许可；方法与模型未改，不新建页面索引，未读qrels或封存标签。源A/B代码及CPU资产核验在本目录；请求计时使用同一个原Engine/route入口、GPU前后同步。',
 '原始请求/telemetry/guard在measure_001；预热20查询×9方法及160查询正确性gate不计入。请求按原循环内存append、块末或中止时保存，避免每请求写盘改变调度。',
 '所有区间为本轮post-hoc描述性诊断；不修改历史主表或风险合同，不构成新K1或Serving优势。']
(O/'E6_RESULTS.md').write_text('\n\n'.join(lines)+'\n',encoding='utf8');save('input_hashes.json',hashes)
if schedule_rows:
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(7,3))
 for estimator,offset,color in [('all_repeats',-.08,'#1766a3'),('first_only',.08,'#c16542')]:
  for i,label in enumerate(['A','B','A1','B3']):
   z=next((z for z in schedule_rows if z['schedule']==label and z['estimator']==estimator),None)
   if not z:continue
   ax.plot([i+offset]*2,[z['low95_ms'],z['high95_ms']],color=color)
   ax.plot(i+offset,z['mean_ms'],'o',color=color,label=estimator if i==0 else None)
 ax.set_xticks(range(4),['A:9x3','B:4x1','A1:9x1','B3:4x3']);ax.set_ylabel('FullV warm E2E (ms)');ax.legend();ax.set_title('POST-HOC E6 / one resident process / paired-query 95%')
 fig.tight_layout();fig.savefig(O/'E6_fullv_means.pdf');fig.savefig(O/'E6_fullv_means.png',dpi=240);plt.close(fig)
 fig,axes=plt.subplots(2,2,figsize=(8,5))
 for ax,key,title in zip(axes.flat,['FullV_mean_ms','SM_clock_MHz','temperature_C','power_W'],['FullV ms','SM MHz','Temperature C','Power W']):
  ax.plot([z['block'] for z in block_rows],[z[key] for z in block_rows],'-o');ax.set_xticks([z['block'] for z in block_rows],[str(z['block'])+':'+z['schedule'] for z in block_rows],rotation=30);ax.set_title(title);ax.grid(alpha=.2)
 fig.suptitle('POST-HOC E6 / fixed balanced sequence / block correspondence');fig.tight_layout();fig.savefig(O/'E6_block_metrics.pdf');fig.savefig(O/'E6_block_metrics.png',dpi=240);plt.close(fig)
print(json.dumps(dict(status=status,verdict=verdict,A_minus_B=ab,completed_blocks=len(complete)),indent=2),flush=True)
