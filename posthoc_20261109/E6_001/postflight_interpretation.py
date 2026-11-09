"""Read-only descriptive interpretation; leaves raw analysis and measurements intact."""
from pathlib import Path
import argparse,csv,hashlib,json
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();S=a.root;A=S/'analysis_001';I=S/'measure_003'
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
summary=json.loads((A/'analysis_summary.json').read_text());blocks=rows(A/'block_gpu_metrics.csv');tele=rows(I/'nvidia_smi.csv')
windows=[json.loads(p.read_text()) for p in sorted(I.glob('block_*.json'))]
samples=[z for z in tele if any(b['start_monotonic']<=float(z['monotonic'])<=b['end_monotonic'] for b in windows)]
metric={k:dict(min=min(float(z[k]) for z in samples),max=max(float(z[k]) for z in samples)) for k in ['SM_clock_MHz','memory_clock_MHz']}
done=json.loads((I/'completed.json').read_text());guard=json.loads((I/'resource_guard.json').read_text())
effect={z['contrast']:z for z in summary['factorial_effects']};ab=summary['A_minus_B'];ratio=ab['mean_ms']/34*100
block3=next(z for z in blocks if z['block']=='3');block6=next(z for z in blocks if z['block']=='6')
notes=f'''## 执行后解释附记（只读汇总，不改原分析）

按预先登记规则，本轮为**部分复现**：A−B={ab['mean_ms']:.6f}ms，95%区间[{ab['low95_ms']:.6f}, {ab['high95_ms']:.6f}]，下界大于0但远低于17ms。其幅度仅为原公布34.0ms的{ratio:.4f}%；这不等于复现了原来的两倍延迟。

本轮微小净差可按已登记恒等式写为方法组合效应{effect['method_combination']['mean_ms']:.6f}ms + 重复次数效应{effect['timing_repetitions']['mean_ms']:.6f}ms = A−B {ab['mean_ms']:.6f}ms。方法组合主效应区间跨0，重复次数主效应虽为正，量级也不足以解释旧34ms。交互项为{effect['interaction']['mean_ms']:.6f}ms，不能把它单独称为旧差异的原因。

需要保留时间不稳定性：同为A1的第3/6块分别为{float(block3['FullV_mean_ms']):.6f}/{float(block6['FullV_mean_ms']):.6f}ms，差{float(block3['FullV_mean_ms'])-float(block6['FullV_mean_ms']):.6f}ms。查询bootstrap条件于固定8块，不估计独立进程或未来运行之间的变动；非加性与时间变化使稳定因果归因仍不足。

在{len(samples)}个落入计时块的1Hz样本中，SM时钟范围{metric['SM_clock_MHz']['min']:.0f}–{metric['SM_clock_MHz']['max']:.0f}MHz，显存时钟范围{metric['memory_clock_MHz']['min']:.0f}–{metric['memory_clock_MHz']['max']:.0f}MHz。未观察到这些已采样时钟随调度改变；1Hz不能排除采样间隔内的短暂变化。各块温度均值约{min(float(z['temperature_C']) for z in blocks):.2f}–{max(float(z['temperature_C']) for z in blocks):.2f}°C，功耗均值{min(float(z['power_W']) for z in blocks):.2f}–{max(float(z['power_W']) for z in blocks):.2f}W，存在时间漂移，不能作为调度引发时钟/温度变化的独立证明。

GPU窗口{done['GPU_window_s']:.3f}秒（含模型加载、预热及正确性闸门），小于7200秒。ResourceGuard共{len(guard['samples'])}条采样/请求前检查，外部PID={guard['foreign_pids']}，错误={guard['errors']}；2,560条FullV计时输出与冻结Top10逐位一致，全部16,640条请求也与各自冻结方法输出一致。

本次统一使用同一原Engine/route入口、相同计时包装与同一驻留模型来隔离方法组合和重复次数；并非把两份旧独立进程驱动从加载到结束逐行重演。旧批次的其他进程、硬件状态或系统因素未被本轮识别。**原70.22/36.22ms不被替换；不修改论文或联改稿，不宣称Serving加速或新K1。**
'''
for name in ['E6_RESULTS.md','postflight_summary.json']:assert not (S/name).exists(),name
(S/'E6_RESULTS.md').write_text((A/'E6_RESULTS.md').read_text(encoding='utf8')+'\n\n'+notes,encoding='utf8')
out=dict(status=summary['status'],verdict=summary['verdict'],fraction_of_old_34ms_pct=ratio,timed_GPU_samples=len(samples),clock_ranges=metric,
 GPU_window_s=done['GPU_window_s'],ResourceGuard_checks=len(guard['samples']),foreign_pids=guard['foreign_pids'],errors=guard['errors'],
 two_A1_block_difference_ms=float(block3['FullV_mean_ms'])-float(block6['FullV_mean_ms']),
 source_raw_analysis_sha256=hashlib.sha256((A/'analysis_summary.json').read_bytes()).hexdigest(),new_experiments=0,paper_edits=False)
(S/'postflight_summary.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
