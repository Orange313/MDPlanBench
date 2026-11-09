"""Conditional wall/core-second crossings using paired017 model processes."""
from pathlib import Path
import argparse,csv,hashlib,json,math
import numpy as np
import accounting as C

ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--ocr-input',type=Path);ap.add_argument('--setup-input',type=Path)
a=ap.parse_args();R=a.project;O=a.out;O.mkdir(parents=True,exist_ok=False)
root=a.ocr_input or R/'posthoc_20261109/E5_ocr_001';done=C.read(root/'completed.json')
assert done['completed_settings']==15
timings=C.read(root/'timings.jsonl')
C.csvsave(O/'E5_worker_timings.csv',timings)
if done['mismatched_page_observations']:
    C.jsave(O/'NOT_RUN_crossings.json',dict(status='NOT_RUN',reason='Frozen OCR hash mismatch; no replacement cost assumption applied'))
    raise SystemExit(0)
source=a.setup_input or R/'reports/icde_eab_g2_setup_017/repeat';pairs=[];cross=[]
for model in ['ColQwen2','ColPali']:
    for repeat in [1,2,3]:
        comp=C.read(source/f'{model}_{repeat:03d}/setup_components.csv')
        requests=C.read(source/f'{model}_{repeat:03d}/requests.csv')
        bm=next(z for z in comp if z['component']=='BM25_build')
        pair=dict(model=model,setup_process=repeat,BM25_setup_wall_s=float(bm['wall_s']),BM25_setup_CPU_s=float(bm['CPU_s']))
        for plan,label in [('Full-Visual','FullV'),('BM25-R100','R100')]:
            rr=[z for z in requests if z['plan']==plan];assert len(rr)==160
            pair[label+'_warm_wall_s']=float(np.mean([float(z['E2E_s']) for z in rr]))
            pair[label+'_warm_CPU_s']=float(np.mean([float(z['CPU_s']) for z in rr]))
        pairs.append(pair)
        for t in timings:
            for scenario,fraction in [('exclusive',1.),('half_shared',.5),('prepaid',0.)]:
                for resource in ['wall','CPU']:
                    ocr=float(t['wall_s'] if resource=='wall' else t['child_CPU_s'])
                    extra=pair['BM25_setup_'+resource+'_s']+fraction*ocr
                    margin=pair['FullV_warm_'+resource+'_s']-pair['R100_warm_'+resource+'_s']
                    n=math.ceil(extra/margin) if margin>0 else None
                    cross.append(dict(model=model,setup_process=repeat,OCR_round=t['round'],workers=t['workers'],
                        scenario=scenario,resource=resource,OCR_cost_s=ocr,incremental_setup_s=extra,warm_margin_s=margin,
                        N_star=n,status='FINITE_CONDITIONAL' if n is not None else 'NO_FINITE_CROSSING',
                        scope='Prepared PNG input; OCR cost plus paired017 warm/BM25 setup; observed range, not production CI'))
ranges=[]
for model in ['ColQwen2','ColPali']:
    for workers in [1,2,4,8,16]:
        for scenario in ['exclusive','half_shared','prepaid']:
            for resource in ['wall','CPU']:
                rr=[z for z in cross if (z['model'],z['workers'],z['scenario'],z['resource'])==(model,workers,scenario,resource)]
                vals=[z['N_star'] for z in rr if z['N_star'] is not None]
                ranges.append(dict(model=model,workers=workers,scenario=scenario,resource=resource,
                    finite_observations=len(vals),observations=len(rr),min_N=min(vals) if vals else None,max_N=max(vals) if vals else None,
                    status='FINITE_CONDITIONAL' if len(vals)==len(rr) else 'PARTIAL_SOME_NO_FINITE_CROSSING' if vals else 'NO_FINITE_CROSSING'))
C.csvsave(O/'E5_same_process_components.csv',pairs);C.csvsave(O/'E5_all_crossings.csv',cross);C.csvsave(O/'E5_crossing_ranges.csv',ranges)
C.jsave(O/'input_hashes.json',C.INPUTS)
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(8,3))
for ax,metric,label in [(axes[0],'wall_s','Wall seconds'),(axes[1],'child_CPU_s','Child CPU core-seconds')]:
    for w in [1,2,4,8,16]:
        v=[float(z[metric]) for z in timings if z['workers']==w];mean=np.mean(v)
        ax.errorbar(w,mean,yerr=[[mean-min(v)],[max(v)-mean]],fmt='o',capsize=3,color='#1766a3')
    ax.set(xscale='log',xticks=[1,2,4,8,16],xticklabels=[1,2,4,8,16],xlabel='OCR workers',ylabel=label)
    ax.grid(alpha=.2)
fig.suptitle('POST-HOC: prepared PNGs; 3 repeats/setting; observed min/max');fig.tight_layout()
fig.savefig(O/'E5_parallelism.pdf');fig.savefig(O/'E5_parallelism.png',dpi=240);plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(8,6))
for row,resource in enumerate(['wall','CPU']):
    for col,model in enumerate(['ColQwen2','ColPali']):
        ax=axes[row,col]
        for scene,color in [('exclusive','#b44737'),('half_shared','#1766a3'),('prepaid','#777777')]:
            rr=[z for z in ranges if z['model']==model and z['resource']==resource and z['scenario']==scene and z['min_N'] is not None]
            if rr:
                x=np.array([z['workers'] for z in rr]);lo=np.array([z['min_N'] for z in rr]);hi=np.array([z['max_N'] for z in rr])
                ax.plot(x,(lo+hi)/2,'-o',color=color,label=scene);ax.fill_between(x,lo,hi,color=color,alpha=.12)
        ax.set(xscale='log',yscale='log',xlabel='OCR workers',ylabel='Conditional crossing queries',title=model+' / '+resource)
        ax.legend(fontsize=7);ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(O/'E5_crossings.pdf');fig.savefig(O/'E5_crossings.png',dpi=240);plt.close(fig)
C.jsave(O/'completed.json',dict(status='DONE_CONDITIONAL_PREPARED_PNG_COST_MODEL',settings=15,hash_mismatch_observations=0,
    max_output_bytes=done['bytes_retained'],crossings=len(cross),ranges=len(ranges),GPU_jobs=0,
    limitations=['Input PNG preparation is prepaid in these new OCR timings. Historical407.725s included RGB/PNG materialization.',
                'CPU resource uses child user+sys; parent CPU is separately recorded. Wall and CPU are never added.',
                'Ranges combine3 OCR repeats with3 paired model setup/warm processes; they are not9 independent workload samples.',
                'Shared CPU host, warm filesystem cache; no production-level confidence guarantee.']))
print(json.dumps(dict(status='DONE',settings=15,crossings=len(cross)),indent=2),flush=True)
