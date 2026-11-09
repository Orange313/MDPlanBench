"""Create review-only tables, plots and RESULTS_SUMMARY from completed records.

No paper source is opened or modified. Does not train, benchmark, or read qrels.
"""
from pathlib import Path
import argparse,csv,hashlib,json,subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--code-commit');a=ap.parse_args()
S=Path(__file__).resolve().parent;O=a.out.resolve();O.mkdir(parents=True,exist_ok=False)
inputs={}
def read(p):
    p=S/p;b=p.read_bytes();inputs[str(p.relative_to(S))]=hashlib.sha256(b).hexdigest()
    return json.loads(b) if p.suffix=='.json' else list(csv.DictReader(b.decode('utf-8-sig').splitlines()))
def table(headers,rows):
    return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+
                     ['|'+'|'.join(str(v).replace('|','/') for v in row)+'|' for row in rows])
def interval(z,key='DeltaC_cf_pp'):
    return f"{float(z[key]):+.4f} [{float(z['low95_pp']):+.4f}, {float(z['high95_pp']):+.4f}]"
domains=['HR','Finance','Industrial','Pharma','Biomedical','Economics']
methods=['Ridge_Q','Ridge_QP','LightGBM_Q','LightGBM_QP']
labels=['Ridge Q','Ridge QP','LGBM Q','LGBM QP'];colors=['#24659a','#76a5c6','#b4563c','#e4a27e']
main=read('screening_001/E2_main_b005.csv');grid=read('screening_001/E2_all_budgets.csv')
choices=read('screening_001/selected_kappas.csv');bias=read('screening_001/E1_bias_summary.csv')
e3=read('independent_001/E3_intervals_36.csv');counts=read('independent_001/E3_upper_bound_counts.csv')
k17=read('independent_001/K17_kappa10_vs20.csv');e4=read('independent_001/E4_coarse_hull.csv')
ocr=read('E5_analysis_001/E5_worker_timings.csv');cross=read('E5_analysis_001/E5_crossing_ranges.csv')
od=read('E5_analysis_001/completed.json');e7=read('E7_HR_001/E7_summary.csv');cov=read('E7_HR_001/coverage.json')
e8=read('E8_storage_001/E8_assets.csv');g=read('gates_001/gate_summary.json')
gate=read('screening_001/gate.json')
eligible=sum(x['conditional_measurement_eligible']=='True' for x in main)
negative=sum(int(x['negative_query_process_costs'])>0 for x in main)
violations=sum(float(x['OOF_r'])>.05 for x in main)
assert len(main)==24 and eligible==0
plt.rcParams.update({'font.size':8,'pdf.fonttype':42,'ps.fonttype':42})
def save(fig,name):
    fig.savefig(O/(name+'.pdf'),bbox_inches='tight');fig.savefig(O/(name+'.png'),dpi=240,bbox_inches='tight');plt.close(fig)
fig,axes=plt.subplots(2,3,figsize=(10,5),sharey=True)
for ax,d in zip(axes.flat,domains):
    rr=[next(z for z in main if z['domain']==d and z['method']==m) for m in methods]
    for i,z in enumerate(rr):
        ax.plot([i,i],[float(z['low95_pp']),float(z['high95_pp'])],color=colors[i],lw=1.5)
        ax.plot(i,float(z['DeltaC_cf_pp']),'o',color=colors[i],ms=4)
    ax.axhline(0,color='black',lw=.7);ax.set_title(d);ax.set_xticks(range(4),labels,rotation=30,ha='right');ax.grid(axis='y',alpha=.18)
for ax in axes[:,0]:ax.set_ylabel('DeltaC cf (pp): positive = cheaper')
fig.suptitle('POST-HOC / three-action catalog / b=0.05 / fixed-fit conditional 95% intervals')
fig.tight_layout();save(fig,'E2_main_crossfit')
fig,axes=plt.subplots(2,3,figsize=(10,5),sharex=True)
for ax,d in zip(axes.flat,domains):
    for m,c,l in zip(methods,colors,labels):
        rr=sorted([z for z in grid if z['domain']==d and z['method']==m and z['b']!='frozen20'],key=lambda z:float(z['b']))
        ax.plot([float(z['b']) for z in rr],[float(z['DeltaC_cf_pp']) for z in rr],'-o',color=c,label=l,ms=3)
    ax.axhline(0,color='black',lw=.7);ax.set_title(d);ax.grid(alpha=.18)
for ax in axes[1]:ax.set_xlabel('Training-fold risk budget b')
for ax in axes[:,0]:ax.set_ylabel('DeltaC cf (pp)')
axes[0,0].legend(fontsize=6);fig.suptitle('POST-HOC / three actions / offline recomposed costs / all fixed budgets')
fig.tight_layout();save(fig,'E2_budget_grid')
fig,ax=plt.subplots(figsize=(8,3))
for delta,cohort,color,label in [(-.15,'posthoc_three_action',colors[0],'Post-hoc three actions'),(.15,'original_four_static',colors[2],'Original four static')]:
    vals=[next(float(z['median_Bias_pp']) for z in bias if z['domain']==d and z['cohort']==cohort) for d in domains]
    ax.bar(np.arange(6)+delta,vals,width=.3,color=color,label=label)
ax.axhline(0,color='black',lw=.7);ax.set_xticks(range(6),domains);ax.set_ylabel('Median retrospective minus cross-fit cost (pp)')
ax.legend(fontsize=7);ax.set_title('POST-HOC E1 / each timing cohort stays separate');fig.tight_layout();save(fig,'E1_envelope_bias')
fig,ax=plt.subplots(figsize=(7,3))
for kind,color in [('official_markdown',colors[0]),('Tesseract411_eng_psm3',colors[2])]:
    rr=[next(z for z in e7 if z['text_source']==kind and z['plan']==p) for p in ['BM25','BM25-R100']]
    ax.plot([0,1],[float(z['mean_r']) for z in rr],'-o',color=color,label=kind)
ax.set_xticks([0,1],['BM25','BM-100']);ax.set_ylabel('HR Dev mean positive regret');ax.legend(fontsize=7)
ax.set_title('POST-HOC text-source control / frozen FullV ranking / Dev40 only');fig.tight_layout();save(fig,'E7_text_source')

now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
commit=a.code_commit or subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()
lines=['# MDPlanBench 投稿前补实验结果（posthoc_20261109）','',f'实际汇总时间：{now}。目录日期是作者指定标签。',
 f'分析脚本 commit：`{commit}`；基线：`icde27-eab-v1.1 / e9d4c2d14abca6003001caf8010da4f6b7321669`。本轮不打 tag。',
 '权威执行令：Orange31 R1；PLAN 在新筛选前单独提交：`a5f31c26203638d385a02f940a1c26c3f2388ae9`。',
 '', '## 结论—决策—阻塞',
 f'- E1 DONE；E2 PARTIAL：24 个主报告格中 {eligible} 个条件区间下界>0，未触发新 GPU 实测。{negative} 个格存在负的逐查询/进程会计估计；{violations} 个格的 OOF 实现风险>.05。不得称为物理延迟、正式认证或已证实部署收益。',
 '- E3 DONE：原区间逐点复现；K17 DONE：复用合法 Fit/Dev 缓存，不训练；E4 DONE：仅粗凸包。',
 '- E5 DONE：15 个档位重复、15,240 次页面 OCR 输出指纹与冻结文本一致。新 wall 排除已准备 PNG 的转换成本，不能作为历史 407.725s 的完整替换。',
 '- E6 NOT_RUN：作者未确认独占 GPU 预约；E7 DONE_ON_FROZEN_DEV_ONLY：40/40 HR Dev，另占完整318英文查询池12.58%；E8 PARTIAL：11个视觉资产数值核验通过，BM25未落盘，索引磁盘值/比值 MISSING。',
 '- 不建议据此扩大路由模型。E2 数据支持“未证明条件风险下优于交叉拟合混合前沿”，并不等于证明所有潜在路由器无收益。',
 '- 本轮 GPU=0，新训练=0；封存标签读取=0。未修改 Paper/LaTeX/联改稿、许可证或原始结果。新分支为本地审核候选，未推送、未合并。',
 '', '## 闸门与复现',
 f'- 原 κ=20 H/S/O/ΔC、动作：逐位一致；新任意动作入口回归：`{json.dumps(gate,ensure_ascii=False)}`。',
 f"- E3：{g['endpoint_checks']} 个端点；最大误差 {g['max_endpoint_error_pp']:.15g} pp < .01 pp。早期原令待补状态仅为历史记录。",
 '- 保存分组抽样索引、配对进程索引与全部2000次 ΔC；固定拟合 κ/权重的 conditional percentile 区间，未在 bootstrap 内重拟合。',
 '- 本报告 CSV、表图可由 `render_results.py` 再生；完整小型数值重放入口 `reproduce_posthoc.py`。干净 checkout 回执单独归档，不能等同重跑 OCR/GPU。',
 '', '## E2 主报告点 b=.05',
 '统一成本标签：**recomposed from measured components (offline screening)**。三动作 FullV/BM-100/BM25；FullV 分母按本次对应语料的同批计时。',
 table(['域','Router','OOF r','成本ms','%FullV','ΔC_cf pp [95%]','种子1–5范围','负成本项'],
 [[z['domain'],z['method'],f"{float(z['OOF_r']):.8f}",f"{float(z['OOF_cost_ms']):.6f}",f"{float(z['cost_pct_FullV']):.6f}",interval(z),
   f"{float(z['stability_min_pp']):+.4f}…{float(z['stability_max_pp']):+.4f}",z['negative_query_process_costs']] for z in main]),
 '', '各折所选 κ（主种子20261109，折序0–4）：']
choice_rows=[]
for d in domains:
    for m in methods:
        rr=sorted([z for z in choices if z['domain']==d and z['method']==m and float(z['b'])==.05 and int(z['seed'])==20261109],key=lambda z:int(z['fold']))
        choice_rows.append([d,m,', '.join(z['kappa'] for z in rr)])
lines+=[table(['域','Router','κ*'],choice_rows),'',
 '全预算网格：`screening_001/E2_all_budgets.csv`；分组：`fold_membership.csv`；逐查询：`OOF_per_query.csv`；逐折 LP 权重：`fit_trace_002/mixture_fold_weights.csv`。',
 '主结果用期望混合。一次固定随机分配仅以已测静态组件离线重放，不是新增 GPU 请求；已单列 sampled allocation，不能写成新完整路径实测。',
 'κ=0/∞ 强制动作，但沿用登记的路由路径会计项；纯静态端点没有路由开销。',
 '', '### 冻结 κ=20 在同一交叉拟合前沿下的参照',
 table(['域','Router','ΔC_cf pp [95%]'],[[z['domain'],z['method'],interval(z)] for z in grid if z['b']=='frozen20']),
 '', '### 成本适配的科学限制',
 '会计入口保持原 Figure5(b) 的有符号“路由路径−匹配静态路径”差额。改变动作时转移此项，QP在FullV回退与快速动作切换时显式加/减可复用的已测 BM25 检索。κ20 同动作精确回归。',
 '该差额包括 execution-context/residual，不能全称为纯特征或决策开销。转移后可能产生负逐查询估计；如实保留，不截断、不改假设追求通过。分项见 `context_transfer_audit.csv`。',
 '', '## E1 前沿乐观偏差',
 'Bias<0 代表 retrospective 更便宜；每个语料只使用预算网格与 BM25 风险范围相交的点，主批次四静态与 post-hoc 三动作分开。',
 table(['域','计时/目录','点数','中位Bias pp','最大绝对Bias pp'],[[z['domain'],z['cohort'],z['points'],f"{float(z['median_Bias_pp']):+.8f}",f"{float(z['max_abs_Bias_pp']):.8f}"] for z in bias]),
 '', '## E3 原区间的可检测边界',
 table(['类别','格数','U<5pp','U<10pp','U<15pp'],[[z['cohort'],z['n'],z['U_lt5'],z['U_lt10'],z['U_lt15']] for z in counts]),
 table(['类别','域','方法','L pp','U pp'],[[z['cohort'],z['domain'],z['method'],z['L'],z['U']] for z in e3]),
 '原端点使用原脚本/原种子/原分母；Economics原口径固定FullV均值，不能混成新E2分母重采样口径。区间上界计数不等于证明收益严格为零。',
 '', '## K17 固定学习诊断的κ20重算',
 'κ10与κ20来自同一轮七点网格开发，展示κ10的理由未登记；不得表述为“冻结前诊断”。原训练种子202610271130/131/132，配对bootstrap种子202610271730；不重新训练。',
 '本节保留原四动作学习诊断与固定Dev45，不能与新三动作成本筛选混用；子集清单与时间线在 `independent_001/`。',
 table(['模型','κ','Fit规模','Dev r','原诊断ΔC pp [95%]'],[[z['method'],z['kappa'],z['Fit_n'],z['mean_Dev_r'],f"{float(z['matched_risk_increment_pp']):+.4f} [{float(z['paired95_low_pp']):+.4f},{float(z['paired95_high_pp']):+.4f}]"] for z in k17]),
 '', '## E4 同批实测三点粗凸包',
 '仅 FullV / Fit-only .05 mixture / BM25，冻结κ20；不使用.02/.10重组成本。粗凸包较弱，胜出不能等同超过最强静态随机包络。',
 table(['域','Router','ΔC_tr pp [95%]'],[[z['domain'],z['method'],interval(z,'DeltaC_tr_pp')] for z in e4]),
 '', '## E5 OCR并行与条件生命周期',
 '原407.725s：Tesseract4.1.1、eng、psm3、4个ThreadPool派发worker，外部tesseract每进程OMP_THREAD_LIMIT=1；旧计时含RGB/PNG物化。新计时从已准备的1016张PNG开始，内容一致但输入准备范围不同。',
 f"新结果15次、每档3次；文本哈希不一致={od['hash_mismatch_observations']}；回执记录保留字节={od['max_output_bytes']}（预算≤1GB）。输出不替换旧OCR。CPU为子进程user+sys；父进程CPU单列，wall与CPU不相加。",
 table(['workers','wall秒，3次','子进程CPU秒，3次','父进程CPU秒，3次'],[[w,', '.join(f"{float(z['wall_s']):.6f}" for z in ocr if int(z['workers'])==w),', '.join(f"{float(z['child_CPU_s']):.6f}" for z in ocr if int(z['workers'])==w),', '.join(f"{float(z['parent_CPU_s']):.6f}" for z in ocr if int(z['workers'])==w)] for w in [1,2,4,8,16]]),
 'N*=ceil[(同进程BM25建立成本 + OCR归属比例×新OCR成本)/(同进程FullV warm − BM100 warm)]。共同视觉setup抵消。wall/core-second分别计算；范围来自3次OCR×3个已测setup/warm进程，不是9个独立生产样本置信区间。',
 'CPU主机并非独占，部分OCR窗口与本任务的单线程数值复算并行；已记录主机loadavg。新数据是共享主机条件观测，不能声称完全隔离的worker扩展因果实验。原407.7s脚本的child CPU是累计值，不用作孤立OCR CPU差分；配置证据与源hash见 `portable_inputs_001/historical_OCR_configuration.json`。',
 table(['检索器','workers','OCR归属','资源','N*最小','N*最大','有限/总数'],[[z['model'],z['workers'],z['scenario'],z['resource'],z['min_N'] or '无有限交叉',z['max_N'] or '无有限交叉',z['finite_observations']+'/'+z['observations']] for z in cross]),
 '', '## E6 / E7',
 'E6 NOT_RUN：未确认独占GPU预约，因此未测试70.22ms与36.22ms的调度因果；不拿跨批次相减补证。',
 f"E7：覆盖冻结HR Dev {cov['covered_queries']}/{cov['HR_Dev_queries']}={100*cov['coverage_Dev']:.2f}%；相对全部英文池 {cov['covered_queries']}/{cov['HR_all_English_queries']}={100*cov['coverage_all_English']:.4f}%。主覆盖分母在PLAN中已登记，不能声称覆盖全HR。",
 table(['文本来源','计划','n','mean nDCG10','mean r','harm rate'],[[z['text_source'],z['plan'],z['queries'],z['mean_nDCG10'],z['mean_r'],z['harm_rate']] for z in e7]),
 '仅从已有全页视觉排序限制候选得到R100，BM25参数与分词不变。OCR为新增文本来源；质量仅Dev诊断，不是独立评估。原始OCR文本只留服务器，不进入Git或附件。',
 '', '## E8 视觉与文本资产',
 '十进制MB；logical与allocated分开。11格的 fp16 实际张量payload与页数×平均保存向量数×维度×2 精确对账。保存向量可能含特殊token，不另称独立测得的图像patch数量。',
 table(['域','检索器','页','视觉logical MB','allocated MB','fp16 payload MB','文本JSON MB','BM25磁盘MB','视觉/BM25'],[[z['domain'],z['model'],z['pages'],z['visual_logical_MB'] or 'MISSING',z['visual_allocated_MB'] or 'MISSING',z['tensor_payload_MB'] or 'MISSING',z['text_json_MB'] or 'MISSING','MISSING','MISSING'] for z in e8]),
 'BM25每次在内存建立，未持久化倒排索引，磁盘大小与视觉/BM25索引比值不可识别，不填0。Economics×ColPali MISSING_NOT_BUILT，不补建。',
 '', '## 论文需要的事实与证据（不修改论文）',
 '- BM200 / Dense→R50 / Hybrid→R50：HR、Finance、Industrial均有，含regret/E2E；原记录 `${PROJECT_ROOT}/reports/icde_evidence_closure_003/E1/{per_query_quality_cost.csv,static_quality_e2e.csv,all_unprofiled_requests.csv}`。',
 '- False-Safe代码定义：选择非FullV且真实正遗憾>.05；rate分母为所有查询。不是要求预测risk≤.05，也不是逐请求认证。风险贡献按False-Safe真实遗憾质量/总真实遗憾质量。',
 '- Biomedical协议原SHA `5f3db14fea91d12128d7507d07d7a3c9fe54a7c1dea3d3354207eea84357be3b`；协议时间2026-10-28 11:53:58.962370+08，commit `32b7e2a29cad7ae6031e7102f8851e6fa09d0db8`，commit时间11:53:59+08；首个已记录质量进程12:04:37.979941。',
 '- Economics协议原SHA `c6b76cf2242afe4b8791cd5997b56336f2e6779cc3e17af172575e222950b613`；协议/commit时间2026-10-29 17:25:52+08，commit `093daa67b0e9796a4857259e4ee95c258fc038c5`；首个有效smoke 19:35:44.222928，完整进程19:36:09。更早BLOCKED日志不是质量结果。',
 '- 两份协议分别在各自已记录质量运行之前；不能用Economics协议证明更早的Biomedical预注册。ColPali×Biomedical在2026-10-28 15:03:27.845352开始，晚于ColQwen结果，属于事后补充。基包 `freeze/` 保存净化后的协议与原文件hash/时间记录，原文件保留服务器。',
 '', '## 工件与边界',
 '- 全部新增输入哈希分阶段保存；逐文件SHA在交付MANIFEST中。保存失败目录和旧脚本，不用新结果覆盖失败。',
 '- 数值小型缓存、抽样索引、CSV、PDF/PNG、脚本可以审核；不包含新原始问题、页面、模型权重、OCR正文、封存标签或完整query-page qrels。',
 '- 本轮只提交审核分支；未自动合并、推送、打tag或提交CMT。新工件是否公开由作者决定。',
 '- 旧正式证书、FrozenMix与事后包络不变；新增结果全部POSTHOC，NOT_CERTIFIED，无新增Serving优越性结论。']
(O/'RESULTS_SUMMARY.md').write_text('\n\n'.join(lines)+'\n',encoding='utf8')
(O/'plot_input_hashes.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf8')
(O/'render_receipt.json').write_text(json.dumps(dict(status='DONE_REVIEW_ONLY',time_beijing=now,code_commit=commit,
    main_cells=24,eligible_GPU_measurements=eligible,negative_accounting_cells=negative,OOF_risk_exceeds_budget_cells=violations,
    figures=['E2_main_crossfit','E2_budget_grid','E1_envelope_bias','E7_text_source'],paper_modified=False),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status='DONE',out=str(O),main_cells=24),indent=2))
