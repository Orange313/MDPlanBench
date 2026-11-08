# Task 31｜5. Table I 原文复核

25格逐项证据见tableI_primary_evidence.csv；五篇官方原文全部下载并保留SHA256。页码为PDF页码，非网页行号。每篇短引文合计少于25词。

状态定义：PASS=有明确正面报告；CONDITIONAL=在所读实验节与附录中未报告该指定评测，不是断言作者没有做过；MISSING=文字不足以支持当前二元标注，明确待定。

## Arabzadeh

[官方原文](https://arxiv.org/pdf/2109.10739)，PDF SHA256 `790e92b46bc6db7c5d8efdf435dc4ba5d3c25ce1d4acf0e282fe982709aa5f37`。

- Random static baseline: **✓ / PASS**；§3.2, PDF pp.3–4, Fig.2。短引文：“randomly assign a retriever”。在同一dense/hybrid调用预算下比较随机分配；不是本研究同正遗憾静态凸包。
- Signal cost in latency: **– / CONDITIONAL**；§3.2, PDF p.4, Fig.4。延迟引用既有BM25/ANCE时间再按预算组合，未单列或确认计入分类器信号成本。
- Setup cost: **– / CONDITIONAL**；§3, PDF pp.3–4。未报告OCR/索引建立的生命周期摊销。
- Risk feasibility and sample size: **– / CONDITIONAL**；§2–3, PDF pp.2–4。质量/资源预算实验，未给均值正遗憾有限样本认证与样本功效审计。
- A/A-gated serving test: **– / CONDITIONAL**；§3, PDF pp.3–4。未报告相同路径A/A等效性后再比较队列Serving。
## AdaptiveRAG

[官方原文](https://aclanthology.org/2024.naacl-long.389.pdf)，PDF SHA256 `1e5abee712c5d8552416b2fd456bcf2c37a0ba518372e64302db2b7b7bdf643f`。

- Random static baseline: **– / CONDITIONAL**；§4, PDF pp.5–9, Tables1–3。静态、adaptive与oracle比较，未登记匹配成本的随机静态分配。
- Signal cost in latency: **待定 / MISSING**；PDF p.8, Table3 and classifier-efficiency analysis。短引文：“exact elapsed time per query”。报告完整策略按预测类的时间；没有足够文字证明分类器是否已计入，不能把当前–当成明确未收费；建议△或待作者/代码核验。
- Setup cost: **– / CONDITIONAL**；§4, PDF pp.5–9。未报告预处理/索引资产的建立与摊销。
- Risk feasibility and sample size: **– / CONDITIONAL**；§3–4, PDF pp.4–9。复杂度分类和QA指标，不是参考相对风险认证与校准功效。
- A/A-gated serving test: **– / CONDITIONAL**；§4 and AppendixB, PDF pp.5–9,14–15。时间/查询实验未报告A/A等效门禁。
## RetrievalRouter

[官方原文](https://arxiv.org/pdf/2608.25625)，PDF SHA256 `32e920bd4c58b7e46e7d36efef7b159bb34d9e3e07c33fabb4a36b9a6829e25c`。

- Random static baseline: **– / CONDITIONAL**；§5.2, PDF p.5。比较七静态、adapted Arabzadeh和Oracle，未登记随机静态包络控制。
- Signal cost in latency: **✓ / PASS**；§5.3 Latency, §6 Router overhead; AppendixA, PDF pp.5–6,13。短引文：“including router inference”。端到端时间明确包含router；另报告约15ms。
- Setup cost: **– / CONDITIONAL**；§5.3 Storage, PDF p.5。报告索引空间与复用，不等于测量索引建立/OCR生命周期成本。
- Risk feasibility and sample size: **– / CONDITIONAL**；§5.3 Statistical testing, PDF p.5。配对显著性检验与Holm校正，不是风险合同认证或校准样本功效。
- A/A-gated serving test: **– / CONDITIONAL**；§5–6 and AppendixA, PDF pp.4–8,13。同一H100上的延迟/P95，不是队列Serving A/A等效性实验。
## BeyondQuery

[官方原文](https://arxiv.org/pdf/2609.12437)，PDF SHA256 `3a97797d29c191ac2f85f4f7a9ae6fc189d2544e77b4b968eecaadc453478d78`。

- Random static baseline: **– / CONDITIONAL**；§3–5, PDF pp.2–6。主要比较匹配query-only/query+retrieval，未报告同风险随机静态包络。
- Signal cost in latency: **△ / PASS**；§3–5 and AppendixE, PDF pp.3–6,11。短引文：“not measured serving latency”。主要路由指标采用分配的动作成本；仅部分有效记录给warm增量时间，Audio/Video存在missing。
- Setup cost: **– / CONDITIONAL**；§4–5 and AppendixE, PDF pp.4–6,11。未测OCR/索引建立摊销。
- Risk feasibility and sample size: **– / CONDITIONAL**；§3–5, PDF pp.2–6。有分组划分/不确定性，未提供有限样本风险认证与校准功效。
- A/A-gated serving test: **– / CONDITIONAL**；AppendixE, PDF p.11。区分assigned cost与measured latency；未报告A/A门禁Serving。
## ConformalArbitrage

[官方原文](https://proceedings.neurips.cc/paper_files/paper/2025/file/65a655c5a267f678fd3e897e4137ef53-Paper-Conference.pdf)，PDF SHA256 `07f18942343527f05e5b197d5d3200d25022a90b7a3f6b8a438373c53a255a40`。

- Random static baseline: **△ / PASS**；§5.1, PDF p.8, Fig.1/Table1。短引文：“cost-matched random router”。随机路由匹配平均成本，非同风险全目录静态最优包络，保留△。
- Signal cost in latency: **– / CONDITIONAL**；§5.1 and AppendixB, PDF pp.7–9,24–27。成本主要用API token价格；不支持与本研究完整CPU/GPU路径收费同义。
- Setup cost: **– / CONDITIONAL**；§5 and AppendixB, PDF pp.7–10,24–27。API级实验未报告本地OCR/索引建立摊销。
- Risk feasibility and sample size: **✓ / PASS**；§4–5.1 and AppendixB.3, PDF pp.7–8,24–25。短引文：“calibration split sizes”。CRC保证/校准量n=300/400/500敏感性明确存在；保证是期望风险，不能写为本研究δ-PAC。
- A/A-gated serving test: **– / CONDITIONAL**；§5 and AppendicesB,E, PDF pp.7–10,24–33。未报告相同路径排队Serving A/A等效性门禁。

建议作者优先处理Adaptive-RAG的Signal cost格：目前“–”缺少明确收费口径证据，不能据此下结论其分类器免费。Conformal Arbitrage的风险列✓仅表示做了相应研究，不等同本项目δ-PAC认证。没有修改Table I或论文。
