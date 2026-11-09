"""CPU-only exact accounting from new setup and matched same-cohort warm."""
import common as C
import collections, json, math, statistics, sys

C.start('analysis_001')
p=C.load(C.ART/'protocol.json'); C.verify_sources(p)
repeats=[]; costs=[]; crossings=[]; warm=[]; guards=[]; profiles=[]
scenario_specs=[('OCR_EXCLUSIVE_NEW_INDEX',1.,1.,False),('OCR_SHARED_HALF_NEW_INDEX',.5,1.,False),
    ('OCR_PREPAID_NEW_INDEX',0.,1.,False),('EXISTING_INDEX_OCR_NEW',1.,0.,False),
    ('EXISTING_INDEX_OCR_PREPAID',0.,0.,False),('ALREADY_RESIDENT_ALL_PREPAID',0.,0.,True)]
for model in ['ColQwen2','ColPali']:
    for rep in [1,2,3]:
        stage=f'repeat/{model}_{rep:03d}'; a=C.ART/stage; r=C.REPORT/stage
        if not (a/'completed.json').exists():
            repeats.append(dict(model=model,repeat=rep,status='NOT_RUN_OR_INCOMPLETE',risk_scope='cost only; no new K1'))
            continue
        complete=C.load(a/'completed.json'); g=C.load(a/'resource_guard.json')
        assert g['valid'] and not g['foreign_pids'] and not g['errors'] and complete['pages']==1016
        guards.append(dict(stage=stage,status='PASS',GPU_samples=len(g['samples']),foreign_pids=0,guard_errors=0))
        rows=C.load(r/'setup_components.csv'); z={x['component']:x for x in rows}
        required=['CUDA_context_init','model_load','full_index_build_and_persist','index_residency','BM25_build']
        assert all(x in z for x in required)
        val=lambda name,key='wall_s':float(z[name][key])
        overlay=val('adapter_overlay') if model=='ColPali' else 0. # structural absence, not missing imputation
        startup=val('CUDA_context_init')+overlay+val('model_load')+val('index_residency')
        index=val('full_index_build_and_persist'); bm=val('BM25_build')
        q=C.load(r/'requests.csv')
        bucket=collections.defaultdict(list)
        for x in q:bucket[x['plan']].append(float(x['E2E_s']))
        assert all(len(bucket[x])==160 for x in C.PLANS) and len(q)==640
        mean={plan:statistics.mean(v) for plan,v in bucket.items()}
        for plan in C.PLANS:
            a_sorted=sorted(bucket[plan]); warm.append(dict(model=model,repeat=rep,plan=plan,queries=160,
                warm_E2E_s=mean[plan],P50_s=statistics.median(a_sorted),P95_s=a_sorted[math.ceil(.95*len(a_sorted))-1],
                scope='same017 process after3 warmups; real serial request cost; not Serving'))
        margin=mean['Full-Visual']-mean['BM25-R100']
        repeats.append(dict(model=model,repeat=rep,status='PASS',model_load_wall_s=val('model_load'),
            model_load_CPU_s=val('model_load','CPU_s'),index_wall_s=index,index_CPU_s=val('full_index_build_and_persist','CPU_s'),
            CUDA_init_wall_s=val('CUDA_context_init'),adapter_overlay_wall_s=overlay,
            index_residency_wall_s=val('index_residency'),BM25_build_wall_s=bm,base_process_startup_wall_s=startup,
            warm_FullV_s=mean['Full-Visual'],warm_R100_s=mean['BM25-R100'],warm_margin_s=margin,
            index_bytes=complete['index_bytes'],max_embedding_error=complete['max_embedding_error'],
            peak_allocated_GPU_bytes=max(int(x.get('peak_allocated_GPU_bytes') or 0) for x in rows),
            cache='OS not flushed; processcold; asset hash reads warm page cache',GPU_active_unprofiled='NOT_MEASURED'))
        for scenario,f,charge,resident in scenario_specs:
            sf=0. if resident else startup+charge*index
            sr=0. if resident else startup+charge*index+bm+f*p['lifecycle']['OCR_shared_seconds']
            extra=sr-sf
            nstar=max(0,math.ceil(extra/margin)) if margin>0 else None
            crossings.append(dict(model=model,repeat=rep,scenario=scenario,incremental_R100_setup_s=extra,
                warm_margin_s=margin,conditional_break_even_N=nstar,
                status='EXPLORATORY' if margin>0 else 'NO_FINITE_CROSSING_OBSERVED',
                interpretation='observed process sensitivity; OCR singleton407.725s; no production CI'))
            for N in p['lifecycle']['N']:
                cf=sf+N*mean['Full-Visual']; cr=sr+N*mean['BM25-R100']
                costs.append(dict(model=model,repeat=rep,scenario=scenario,N=N,
                    FullV_setup_s=sf,R100_setup_s=sr,FullV_total_wall_s=cf,R100_total_wall_s=cr,
                    R100_over_FullV_ratio=cr/cf,R100_minus_FullV_wall_s=cr-cf,
                    OCR_charge_once_s=0. if resident else f*p['lifecycle']['OCR_shared_seconds'],
                    cost_scope='conditional sequential component lifecycle; same017 warm; CPU/GPU not added to wall',
                    status='EXPLORATORY'))
    pa=C.ART/f'profile/{model}_001'
    if (pa/'completed.json').exists():
        g=C.load(pa/'resource_guard.json');assert g['valid']
        profiles.append(dict(**C.load(pa/'GPU_profile_summary.json'),status='PASS_SEPARATE_PROFILE'))
    else:profiles.append(dict(model=model,status='NOT_RUN_OR_INCOMPLETE',full_index_GPU_active_s=None))
C.table(C.R/'G2_setup_repeats.csv',repeats)
C.table(C.R/'G2_same_cohort_warm.csv',warm)
C.table(C.R/'G2_reuse_sensitivity.csv',costs)
C.table(C.R/'G2_break_even_ranges.csv',crossings)
C.table(C.R/'G2_GPU_profiles.csv',profiles)
C.table(C.R/'G2_guard_checks.csv',guards)
summary=[]
for model in ['ColQwen2','ColPali']:
    rr=[x for x in repeats if x['model']==model and x['status']=='PASS']
    for metric in ['model_load_wall_s','index_wall_s','model_load_CPU_s','index_CPU_s','warm_FullV_s','warm_R100_s']:
        v=[x[metric] for x in rr]
        summary.append(dict(model=model,metric=metric,independent_processes=len(v),
            mean=statistics.mean(v) if v else None,observed_min=min(v) if v else None,
            observed_max=max(v) if v else None,uncertainty='observed range, not95% or production quantile'))
C.table(C.R/'G2_observed_ranges.csv',summary)
cohorts=[]
old=C.load('reports/icde_eab_submission_gate_009/Y1/summary_001/warm_static_costs_009.csv')
for x in old:
    if x['plan'] not in ['Full-Visual','BM25-R100']:continue
    vals=[z['warm_E2E_s'] for z in warm if z['model']==x['model'] and z['plan']==x['plan']]
    cohorts.append(dict(model=x['model'],plan=x['plan'],old009_warm_s=float(x['warm_E2E_ms'])/1000,
        new017_warm_s=statistics.mean(vals) if vals else None,
        comparability='NO_CROSS_COHORT_CAUSAL_OR_SPEEDUP_CLAIM; keep old009 and new017 accounting separate'))
C.table(C.R/'G2_timing_cohorts.csv',cohorts)
full=all(x['status']=='PASS' for x in repeats) and len(repeats)==6
status='PASS_COST_MEASUREMENTS' if full else 'INSUFFICIENT_INCOMPLETE_REPEATS'
lines=['# G2 Setup重复与生命周期敏感性', '',f'执行：{C.stamp()}；状态：{status}。',
    'PASS表示测量完成，不表示R100或路由获得收益。只使用既有Biomedical1016页、冻结模型及公开160条查询进行成本测量，未读取qrels或封存数据。', '',
    '|模型|独立全量建索引次数|加载Wall范围(s)|建索引Wall范围(s)|', '|---|---:|---|---|']
for model in ['ColQwen2','ColPali']:
    vals=[x for x in repeats if x['model']==model and x['status']=='PASS']
    fmt=lambda k: f"{min(x[k] for x in vals):.3f}–{max(x[k] for x in vals):.3f}" if vals else 'missing'
    lines.append(f"|{model}|{len(vals)}|{fmt('model_load_wall_s')}|{fmt('index_wall_s')}|")
lines += ['', '## 条件成本与统计边界',
    'Total = CUDA上下文 + 模型加载/必要适配 + 索引驻留 + 被收费的视觉索引构建 + 必要BM25初始化 + OCR收费一次 + N×本017进程Warm均值。',
    'OCR独占、共享半额、预付是会计条件；共享半额不是实测免费。原OCR407.725秒是既有单次观测，未重新计时。',
    '同模型R100与FullV使用同一视觉索引。共同的视觉索引与模型启动成本在两者成本差中抵消，影响成本比值但不单独决定交叉点；交叉点取决于OCR/BM25增量与Warm时间差。',
    '新017与旧009各自保持同cohort accounting；不拼接007/008旧Warm或宣称跨批次加速。GPU Profile独立于三次非Profiling重复，不把其GPU活动秒加到Wall。',
    '三次进程不增加独立质量查询，不支持生产级P95、严格冷启动IID置信区间或通用部署保证。OS缓存未清，权重hash读取会预热文件缓存；CPU共享负载与监测开销均存在。',
    'Warm是串行实际请求成本；无新K1、无Serving加速或完整业务净收益结论。', '',
    '## 论文主张与证据',
    '支持第三贡献中Setup实测范围和OCR/索引归属的条件生命周期敏感性表图；不改变主质量表、风险预算或历史005。新图表是否并入Paper需依据独立验收，不自动覆盖Paper。']
C.prose(C.R/'G2_decision.md','\n'.join(lines)+'\n')
C.prose(C.R/'G2_resource_guard.md',f'# 资源守卫\n\n{len(guards)}个已完成独立测量进程守卫通过；GPU3、3次空闲检查、100ms ResourceGuard、200ms磁盘检查和仅中止自身作业的watchdog。全部原始日志/失败/索引保留。5GiB余量和3GiB辅助预算是用户批准的测量前资源修订；原30GiB规则和历史NOT_RUN保留。\n')
C.prose(C.R/'claim_to_evidence_matrix.md','|主张|证据|状态/边界|\n|---|---|---|\n|三次独立Setup范围|G2_setup_repeats.csv/G2_observed_ranges.csv|'+status+'；非生产级CI|\n|条件生命周期随N和OCR归属变化|G2_reuse_sensitivity.csv/G2_break_even_ranges.csv|EXPLORATORY，同017Warm，OCR仍单次|\n|真实GPU活动|G2_GPU_profiles.csv|独立Profiling队列，不混入Wall|\n|质量不变|每次index_equivalence.csv及冻结输入hash|逐页嵌入核对；未重算质量主表|\n|新K1/Serving优越性|无此实验|NOT_CERTIFIED/NOT_RUN|\n')
# Standard scientific plotting, using all predeclared scenarios and N points.
import os
os.environ['MPLCONFIGDIR']=str(C.A/'mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':8,'pdf.fonttype':42,'ps.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(10,3.8),sharey=True)
for ax,model in zip(axes,['ColQwen2','ColPali']):
    for scenario,_,_,_ in scenario_specs:
        yy=[];lo=[];hi=[]
        for N in p['lifecycle']['N']:
            vals=[x['R100_over_FullV_ratio'] for x in costs if x['model']==model and x['scenario']==scenario and x['N']==N]
            yy.append(statistics.mean(vals));lo.append(min(vals));hi.append(max(vals))
        ax.plot(p['lifecycle']['N'],yy,marker='o',ms=3,label=scenario.replace('_',' ').lower())
        ax.fill_between(p['lifecycle']['N'],lo,hi,alpha=.12)
    ax.axhline(1,color='black',lw=.8,ls='--');ax.set_xscale('log');ax.set_title(model)
    ax.set_xlabel('Query count N (conditional projection)');ax.grid(alpha=.2)
axes[0].set_ylabel('R100 / FullV lifecycle wall cost')
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',ncol=2,fontsize=7,bbox_to_anchor=(.5,-.07))
fig.tight_layout(rect=[0,.16,1,1])
fig.savefig(C.R/'G2_lifecycle_ranges.png',dpi=250,bbox_inches='tight')
fig.savefig(C.R/'G2_lifecycle_ranges.pdf',bbox_inches='tight');plt.close(fig)
files={str(x.relative_to(C.ROOT)):C.sha(x) for base in [C.ART,C.REPORT,C.INDEX] for x in base.rglob('*')
       if x.is_file() and not x.is_symlink() and '__pycache__' not in x.parts and 'mplconfig' not in x.parts}
C.write(C.REPORT/'hash_inventory.json',dict(run_id=C.RUN,files=files))
C.write(C.REPORT/'manifest.json',dict(run_id=C.RUN,status=status,time_bj=C.stamp(),
    protocol_SHA256=C.sha(C.ART/'protocol.json'),asset_lock_SHA256=C.sha(C.ART/'asset_lock.json'),
    inventory_SHA256=C.sha(C.REPORT/'hash_inventory.json'),
    independent_unprofiled_processes=sum(x['status']=='PASS' for x in repeats),
    pages=1016,public_timing_queries=160,new_relevance_labels=0,sealed_reads=0,
    new_K1='NOT_CERTIFIED',Serving='NOT_ESTABLISHED',code_SHA256=p['code_SHA256']))
print(json.dumps(dict(status=status,report=str(C.R),manifest_SHA256=C.sha(C.REPORT/'manifest.json'),
    repeats=6,summary=summary)),flush=True)
