# MDPlanBench 投稿前补实验结果（posthoc_20261109）



实际汇总时间：2026-11-08T22:05:28.903511+08:00。目录日期是作者指定标签。

分析脚本 commit：`79fc71b854aeaf2fa0feb8fa3fa1eef40459bd29`；基线：`icde27-eab-v1.1 / e9d4c2d14abca6003001caf8010da4f6b7321669`。本轮不打 tag。

权威执行令：Orange31 R1；PLAN 在新筛选前单独提交：`a5f31c26203638d385a02f940a1c26c3f2388ae9`。



## 结论—决策—阻塞

- E1 DONE；E2 PARTIAL：24 个主报告格中 0 个条件区间下界>0，未触发新 GPU 实测。10 个格存在负的逐查询/进程会计估计；2 个格的 OOF 实现风险>.05。不得称为物理延迟、正式认证或已证实部署收益。

- E3 DONE：原区间逐点复现；K17 DONE：复用合法 Fit/Dev 缓存，不训练；E4 DONE：仅粗凸包。

- E5 DONE：15 个档位重复、15,240 次页面 OCR 输出指纹与冻结文本一致。新 wall 排除已准备 PNG 的转换成本，不能作为历史 407.725s 的完整替换。

- E6 NOT_RUN：作者未确认独占 GPU 预约；E7 DONE_ON_FROZEN_DEV_ONLY：40/40 HR Dev，另占完整318英文查询池12.58%；E8 PARTIAL：11个视觉资产数值核验通过，BM25未落盘，索引磁盘值/比值 MISSING。

- 不建议据此扩大路由模型。E2 数据支持“未证明条件风险下优于交叉拟合混合前沿”，并不等于证明所有潜在路由器无收益。

- 本轮 GPU=0，新训练=0；封存标签读取=0。未修改 Paper/LaTeX/联改稿、许可证或原始结果。新分支为本地审核候选，未推送、未合并。



## 闸门与复现

- 原 κ=20 H/S/O/ΔC、动作：逐位一致；新任意动作入口回归：`{"PASS": true, "entries": 96, "strict_exact_float": true}`。

- E3：72 个端点；最大误差 1.02140518265514e-13 pp < .01 pp。早期原令待补状态仅为历史记录。

- 保存分组抽样索引、配对进程索引与全部2000次 ΔC；固定拟合 κ/权重的 conditional percentile 区间，未在 bootstrap 内重拟合。

- 本报告 CSV、表图可由 `render_results.py` 再生；完整小型数值重放入口 `reproduce_posthoc.py`。干净 checkout 回执单独归档，不能等同重跑 OCR/GPU。



## E2 主报告点 b=.05

统一成本标签：**recomposed from measured components (offline screening)**。三动作 FullV/BM-100/BM25；FullV 分母按本次对应语料的同批计时。

|域|Router|OOF r|成本ms|%FullV|ΔC_cf pp [95%]|种子1–5范围|负成本项|
|---|---|---|---|---|---|---|---|
|HR|Ridge_Q|0.04773589|23.685532|65.754021|-5.2017 [-25.1739, +12.0706]|-4.7338…+4.6394|0|
|HR|Ridge_QP|0.03956182|22.245793|61.757125|+5.5501 [-12.7379, +19.1537]|+5.5501…+5.5501|2|
|HR|LightGBM_Q|0.03812582|26.846176|74.528368|-6.0345 [-29.2307, +8.3411]|-6.8170…-0.7543|0|
|HR|LightGBM_QP|0.04329411|29.763510|82.627256|-18.4043 [-37.3130, -7.1968]|-20.9674…-17.3870|5|
|Finance|Ridge_Q|0.05239734|24.793588|51.487255|-12.4940 [-26.6600, +4.7899]|-14.9442…-9.9068|1|
|Finance|Ridge_QP|0.03258931|25.117224|52.159329|-1.4652 [-15.3020, +20.5687]|-1.5366…-1.0948|1|
|Finance|LightGBM_Q|0.04949770|25.661836|53.290290|-12.5841 [-27.8002, +3.4548]|-20.0675…-14.7766|0|
|Finance|LightGBM_QP|0.02941145|28.316045|58.802117|-6.2308 [-21.6816, +16.1446]|-12.8514…-6.1094|1|
|Industrial|Ridge_Q|0.03572498|58.643496|87.585741|-49.6023 [-60.9008, +3.4388]|-52.4878…-46.0823|0|
|Industrial|Ridge_QP|0.04549178|32.716423|48.862915|-16.0549 [-30.3621, +4.9873]|-18.0577…-14.1414|0|
|Industrial|LightGBM_Q|0.04220367|27.536041|41.125866|-6.5754 [-18.5432, +11.9828]|-14.3667…-7.7850|0|
|Industrial|LightGBM_QP|0.04020682|24.522683|36.625329|-1.0168 [-17.5730, +12.2033]|-4.5833…+2.6355|3|
|Pharma|Ridge_Q|0.03398232|36.508296|81.527380|-29.0407 [-47.5281, +3.1048]|-32.4776…-22.4327|0|
|Pharma|Ridge_QP|0.03809390|25.516476|56.981333|-8.2271 [-25.5738, +17.8846]|-8.7183…-5.5307|4|
|Pharma|LightGBM_Q|0.04218496|26.889614|60.047716|-15.0073 [-31.9769, -0.5731]|-19.3645…-8.9446|1|
|Pharma|LightGBM_QP|0.01435373|29.621986|66.149428|+8.6032 [-7.0179, +28.1941]|-6.6361…+9.5513|0|
|Biomedical|Ridge_Q|0.00000000|35.761075|101.028808|-1.0288 [-1.6049, -0.4912]|-1.0288…-1.0288|0|
|Biomedical|Ridge_QP|0.00000000|36.870135|104.162020|-4.1620 [-5.1695, -2.8200]|-4.1620…-4.1620|0|
|Biomedical|LightGBM_Q|0.04503315|34.209044|96.644157|-11.7022 [-19.2216, -3.6430]|-13.2312…-7.5155|0|
|Biomedical|LightGBM_QP|0.05172599|34.751009|98.175264|-15.4712 [-24.3388, -5.2030]|-16.7929…-14.7681|0|
|Economics|Ridge_Q|0.04928790|22.310688|68.698817|+2.8130 [-8.8258, +13.9132]|+2.8433…+3.1830|0|
|Economics|Ridge_QP|0.03462048|25.385597|78.167042|+1.0141 [-9.0407, +11.5057]|+0.9849…+1.2779|10|
|Economics|LightGBM_Q|0.02310799|27.695839|85.280713|-0.0800 [-11.8074, +10.8662]|-0.1114…+0.2043|0|
|Economics|LightGBM_QP|0.01983890|28.953101|89.152060|-2.2403 [-8.7940, +4.8979]|-2.2740…-1.9519|5|



各折所选 κ（主种子20261109，折序0–4）：

|域|Router|κ*|
|---|---|---|
|HR|Ridge_Q|inf, 10, 10, 40, 40|
|HR|Ridge_QP|10, 10, 10, 10, 10|
|HR|LightGBM_Q|10, 20, 10, 20, 10|
|HR|LightGBM_QP|20, 10, 10, 20, 10|
|Finance|Ridge_Q|10, 20, 160, 160, 20|
|Finance|Ridge_QP|10, 10, 10, 10, 10|
|Finance|LightGBM_Q|10, 10, 10, 20, 20|
|Finance|LightGBM_QP|10, 10, 10, 10, 10|
|Industrial|Ridge_Q|5, inf, inf, inf, inf|
|Industrial|Ridge_QP|5, 10, 10, 10, 10|
|Industrial|LightGBM_Q|10, 10, 20, 10, 10|
|Industrial|LightGBM_QP|10, 10, 10, 10, 5|
|Pharma|Ridge_Q|inf, 10, inf, 20, inf|
|Pharma|Ridge_QP|10, 10, 10, 10, 10|
|Pharma|LightGBM_Q|10, 10, 20, 10, 10|
|Pharma|LightGBM_QP|10, 10, 10, 10, 10|
|Biomedical|Ridge_Q|inf, inf, inf, inf, inf|
|Biomedical|Ridge_QP|inf, inf, inf, inf, inf|
|Biomedical|LightGBM_Q|80, 80, 40, 80, 80|
|Biomedical|LightGBM_QP|160, 80, 40, 80, 80|
|Economics|Ridge_Q|20, 20, 40, 20, 40|
|Economics|Ridge_QP|10, 10, 10, 10, 10|
|Economics|LightGBM_Q|20, 20, 20, 20, 20|
|Economics|LightGBM_QP|10, 10, 10, 10, 10|



全预算网格：`screening_001/E2_all_budgets.csv`；分组：`fold_membership.csv`；逐查询：`OOF_per_query.csv`；逐折 LP 权重：`fit_trace_002/mixture_fold_weights.csv`。

主结果用期望混合。一次固定随机分配仅以已测静态组件离线重放，不是新增 GPU 请求；已单列 sampled allocation，不能写成新完整路径实测。

κ=0/∞ 强制动作，但沿用登记的路由路径会计项；纯静态端点没有路由开销。



### 冻结 κ=20 在同一交叉拟合前沿下的参照

|域|Router|ΔC_cf pp [95%]|
|---|---|---|
|HR|Ridge_Q|+3.3160 [-14.3933, +19.5991]|
|HR|Ridge_QP|+1.8630 [-19.6654, +16.8277]|
|HR|LightGBM_Q|-0.3134 [-12.8149, +8.0914]|
|HR|LightGBM_QP|-8.4501 [-17.0556, -1.5444]|
|Finance|Ridge_Q|-10.0095 [-25.7085, +10.8289]|
|Finance|Ridge_QP|-5.3544 [-18.1962, +31.3966]|
|Finance|LightGBM_Q|-15.8833 [-23.1064, +4.8190]|
|Finance|LightGBM_QP|+7.5255 [-2.7091, +20.6725]|
|Industrial|Ridge_Q|-25.4226 [-37.0345, -7.6672]|
|Industrial|Ridge_QP|-21.2414 [-36.8386, +4.1691]|
|Industrial|LightGBM_Q|-1.6874 [-9.5232, +43.9450]|
|Industrial|LightGBM_QP|+4.6132 [-9.5654, +28.5625]|
|Pharma|Ridge_Q|-25.6235 [-42.9666, -2.4811]|
|Pharma|Ridge_QP|+12.0510 [-11.5583, +25.3748]|
|Pharma|LightGBM_Q|-1.6593 [-12.7793, +15.0533]|
|Pharma|LightGBM_QP|-3.8031 [-20.9797, +18.9067]|
|Biomedical|Ridge_Q|-11.8101 [-22.9457, +0.6881]|
|Biomedical|Ridge_QP|-12.2056 [-19.1313, -4.0061]|
|Biomedical|LightGBM_Q|-19.2651 [-27.9338, -9.3715]|
|Biomedical|LightGBM_QP|-21.7815 [-31.2995, -10.7079]|
|Economics|Ridge_Q|+2.9678 [-8.5877, +13.9463]|
|Economics|Ridge_QP|+1.8018 [-4.8438, +7.8829]|
|Economics|LightGBM_Q|-0.0800 [-11.8074, +10.8662]|
|Economics|LightGBM_QP|-3.0019 [-6.2185, +0.4516]|



### 成本适配的科学限制

会计入口保持原 Figure5(b) 的有符号“路由路径−匹配静态路径”差额。改变动作时转移此项，QP在FullV回退与快速动作切换时显式加/减可复用的已测 BM25 检索。κ20 同动作精确回归。

该差额包括 execution-context/residual，不能全称为纯特征或决策开销。转移后可能产生负逐查询估计；如实保留，不截断、不改假设追求通过。分项见 `context_transfer_audit.csv`。



## E1 前沿乐观偏差

Bias<0 代表 retrospective 更便宜；每个语料只使用预算网格与 BM25 风险范围相交的点，主批次四静态与 post-hoc 三动作分开。

|域|计时/目录|点数|中位Bias pp|最大绝对Bias pp|
|---|---|---|---|---|
|HR|posthoc_three_action|6|-2.01505981|3.07935780|
|HR|original_four_static|6|-0.00000000|0.00000000|
|Finance|posthoc_three_action|6|-0.07131398|0.89376480|
|Finance|original_four_static|6|-0.07900748|0.57490766|
|Industrial|posthoc_three_action|5|-0.90694258|3.38764833|
|Industrial|original_four_static|5|-4.32272397|12.04466004|
|Pharma|posthoc_three_action|5|-0.08430283|3.97322018|
|Pharma|original_four_static|5|-2.59186333|3.13722905|
|Biomedical|posthoc_three_action|6|+0.00000000|0.00000000|
|Biomedical|original_four_static|6|+0.00000000|0.00000000|
|Economics|posthoc_three_action|6|+0.02682349|0.15680223|
|Economics|original_four_static|6|-0.31489118|0.38086029|



## E3 原区间的可检测边界

|类别|格数|U<5pp|U<10pp|U<15pp|
|---|---|---|---|---|
|original12|12|4|7|9|
|posthoc24|24|11|14|16|
|all36|36|15|21|25|

|类别|域|方法|L pp|U pp|
|---|---|---|---|---|
|ORIGINAL_FROZEN|Biomedical|Q|-29.28722797256928|-9.47882783431336|
|ORIGINAL_FROZEN|Biomedical|QP|-22.142122382779394|-5.962752473178019|
|ORIGINAL_FROZEN|Economics|Q|-10.977832045040888|5.151712794539569|
|ORIGINAL_FROZEN|Economics|QP|-5.235868044551727|6.885996691842344|
|ORIGINAL_FROZEN|Finance|Q|-13.834765466465544|21.0348232736894|
|ORIGINAL_FROZEN|Finance|QP|-14.556742908245626|25.924548227256633|
|ORIGINAL_FROZEN|HR|Q|-26.05052543684145|13.254931518453771|
|ORIGINAL_FROZEN|HR|QP|-21.15001823159736|14.597800740742146|
|ORIGINAL_FROZEN|Industrial|Q|-40.189782354673476|2.270135909200937|
|ORIGINAL_FROZEN|Industrial|QP|-41.4140097346362|-0.4490649629880626|
|ORIGINAL_FROZEN|Pharma|Q|-36.94467416017522|8.55401598391318|
|ORIGINAL_FROZEN|Pharma|QP|-8.141097185155635|20.212192533080636|
|POSTHOC_021|Biomedical|LightGBM_Q|-27.933832729195682|-9.37147328500112|
|POSTHOC_021|Biomedical|LightGBM_QP|-31.29947980813765|-10.70787377003596|
|POSTHOC_021|Biomedical|Ridge_Q|-22.945717036352374|0.7489826873321864|
|POSTHOC_021|Biomedical|Ridge_QP|-19.131337007197814|-4.006127624600411|
|POSTHOC_021|Economics|LightGBM_Q|-11.315526369606985|10.804769188962066|
|POSTHOC_021|Economics|LightGBM_QP|-7.452238743442953|0.34334321640089566|
|POSTHOC_021|Economics|Ridge_Q|-7.70823143662813|14.282993507172886|
|POSTHOC_021|Economics|Ridge_QP|-5.804391789309703|7.428393934129808|
|POSTHOC_021|Finance|LightGBM_Q|-24.611936890294384|-8.940695185412624|
|POSTHOC_021|Finance|LightGBM_QP|-22.624885695051624|19.80579457090251|
|POSTHOC_021|Finance|Ridge_Q|-25.707883603209726|6.272987363689685|
|POSTHOC_021|Finance|Ridge_QP|-17.680235334815443|29.66710804388572|
|POSTHOC_021|HR|LightGBM_Q|-14.248374109674689|5.805636935079043|
|POSTHOC_021|HR|LightGBM_QP|-19.268694777581132|-2.8399683953409993|
|POSTHOC_021|HR|Ridge_Q|-16.730949297646646|18.160985744797287|
|POSTHOC_021|HR|Ridge_QP|-22.578781840372432|15.888585804764327|
|POSTHOC_021|Industrial|LightGBM_Q|-10.326927853008797|2.763329870736252|
|POSTHOC_021|Industrial|LightGBM_QP|-14.130480211582427|27.39726078401821|
|POSTHOC_021|Industrial|Ridge_Q|-37.82131186384277|-8.213164222975877|
|POSTHOC_021|Industrial|Ridge_QP|-37.245756633020605|-3.5390840207599745|
|POSTHOC_021|Pharma|LightGBM_Q|-15.751554168384127|15.37734135864692|
|POSTHOC_021|Pharma|LightGBM_QP|-21.693827436520575|19.34311232982824|
|POSTHOC_021|Pharma|Ridge_Q|-42.08008012762708|-4.87949324157019|
|POSTHOC_021|Pharma|Ridge_QP|-12.794688315330252|24.65436236627716|

原端点使用原脚本/原种子/原分母；Economics原口径固定FullV均值，不能混成新E2分母重采样口径。区间上界计数不等于证明收益严格为零。



## K17 固定学习诊断的κ20重算

κ10与κ20来自同一轮七点网格开发，展示κ10的理由未登记；不得表述为“冻结前诊断”。原训练种子202610271130/131/132，配对bootstrap种子202610271730；不重新训练。

本节保留原四动作学习诊断与固定Dev45，不能与新三动作成本筛选混用；子集清单与时间线在 `independent_001/`。

|模型|κ|Fit规模|Dev r|原诊断ΔC pp [95%]|
|---|---|---|---|---|
|Q_regret|10|20|0.02212730999730523|+6.7627 [-8.8663,+17.7136]|
|Q_regret|10|40|0.026205209320641774|+2.0872 [-14.6677,+14.7147]|
|Q_regret|10|60|0.045652980865593135|-10.1784 [-29.7960,+6.4678]|
|Q_regret|10|81|0.056462713953342535|-21.3835 [-41.4822,-1.7514]|
|Q_regret|20|20|0.016705492719449485|-0.6310 [-14.4783,+8.0363]|
|Q_regret|20|40|0.015279250339973143|-2.0179 [-15.6115,+10.8197]|
|Q_regret|20|60|0.01815115123854109|-3.6155 [-21.8278,+8.2180]|
|Q_regret|20|81|0.04809335372280049|-26.8020 [-48.1857,-6.2279]|
|QP_regret|10|20|0.018489759227339798|+6.8463 [-9.7558,+16.6411]|
|QP_regret|10|40|0.03004319120308644|-3.5502 [-20.2314,+8.1752]|
|QP_regret|10|60|0.03974856159435437|-5.8328 [-25.0983,+11.2013]|
|QP_regret|10|81|0.05115708267660083|-19.8314 [-41.3379,+2.7230]|
|QP_regret|20|20|0.015416684744368359|-3.5244 [-19.3518,+6.8310]|
|QP_regret|20|40|0.015915098314806517|-5.6378 [-19.4341,+8.6059]|
|QP_regret|20|60|0.018989485605762593|-5.8100 [-24.4402,+7.0447]|
|QP_regret|20|81|0.02604471342753535|-8.6730 [-34.8263,+14.3084]|



## E4 同批实测三点粗凸包

仅 FullV / Fit-only .05 mixture / BM25，冻结κ20；不使用.02/.10重组成本。粗凸包较弱，胜出不能等同超过最强静态随机包络。

|域|Router|ΔC_tr pp [95%]|
|---|---|---|
|HR|Ridge_Q|+1.5602 [-23.9326, +17.2025]|
|HR|Ridge_QP|+1.0877 [-20.7522, +15.3808]|
|HR|LightGBM_Q|-0.8258 [-17.0379, +7.2618]|
|HR|LightGBM_QP|-8.9562 [-20.7362, -1.8350]|
|Finance|Ridge_Q|-3.4807 [-29.6159, +30.4154]|
|Finance|Ridge_QP|+14.2039 [-20.7822, +36.5867]|
|Finance|LightGBM_Q|+5.7359 [-11.8334, +15.4606]|
|Finance|LightGBM_QP|+10.6763 [+2.3015, +21.5004]|
|Industrial|Ridge_Q|-26.2995 [-38.9595, +14.3095]|
|Industrial|Ridge_QP|-22.5674 [-41.3517, +34.1191]|
|Industrial|LightGBM_Q|+22.7463 [-5.1937, +45.0697]|
|Industrial|LightGBM_QP|+24.4906 [+4.1163, +38.2294]|
|Pharma|Ridge_Q|-18.5351 [-40.9703, +6.4715]|
|Pharma|Ridge_QP|+16.6398 [+4.0676, +27.0165]|
|Pharma|LightGBM_Q|+6.0470 [-11.6583, +19.7836]|
|Pharma|LightGBM_QP|+4.2434 [-16.5851, +19.3427]|
|Biomedical|Ridge_Q|-11.8101 [-22.9457, +0.7490]|
|Biomedical|Ridge_QP|-12.2056 [-19.1313, -4.0061]|
|Biomedical|LightGBM_Q|-19.2651 [-27.9338, -9.3727]|
|Biomedical|LightGBM_QP|-21.7815 [-31.2995, -10.7079]|
|Economics|Ridge_Q|-9.8171 [-24.6391, +6.7434]|
|Economics|Ridge_QP|+1.5180 [-4.7946, +7.1273]|
|Economics|LightGBM_Q|-4.6310 [-21.5924, +7.5095]|
|Economics|LightGBM_QP|-3.1918 [-8.7231, +0.4669]|



## E5 OCR并行与条件生命周期

原407.725s：Tesseract4.1.1、eng、psm3、4个ThreadPool派发worker，外部tesseract每进程OMP_THREAD_LIMIT=1；旧计时含RGB/PNG物化。新计时从已准备的1016张PNG开始，内容一致但输入准备范围不同。

新结果15次、每档3次；文本哈希不一致=0；回执记录保留字节=4707575（预算≤1GB）。输出不替换旧OCR。CPU为子进程user+sys；父进程CPU单列，wall与CPU不相加。

|workers|wall秒，3次|子进程CPU秒，3次|父进程CPU秒，3次|
|---|---|---|---|
|1|588.402698, 575.818511, 579.947364|586.914910, 574.374045, 578.530274|1.446848, 1.363165, 1.358153|
|2|293.087811, 289.817291, 289.745119|584.545894, 578.141101, 578.082268|1.405074, 1.332849, 1.283421|
|4|145.940735, 144.949719, 143.971573|581.562205, 577.400166, 573.840479|1.335853, 1.227866, 1.239927|
|8|73.457033, 73.551564, 77.588007|581.886202, 582.973319, 614.848574|1.202504, 1.185195, 1.121243|
|16|47.256413, 48.502082, 47.882345|725.784830, 755.315585, 743.948566|1.144589, 1.149043, 1.140153|

N*=ceil[(同进程BM25建立成本 + OCR归属比例×新OCR成本)/(同进程FullV warm − BM100 warm)]。共同视觉setup抵消。wall/core-second分别计算；范围来自3次OCR×3个已测setup/warm进程，不是9个独立生产样本置信区间。

CPU主机并非独占，部分OCR窗口与本任务的单线程数值复算并行；已记录主机loadavg。新数据是共享主机条件观测，不能声称完全隔离的worker扩展因果实验。原407.7s脚本的child CPU是累计值，不用作孤立OCR CPU差分；配置证据与源hash见 `portable_inputs_001/historical_OCR_configuration.json`。

|检索器|workers|OCR归属|资源|N*最小|N*最大|有限/总数|
|---|---|---|---|---|---|---|
|ColQwen2|1|exclusive|wall|106046|114449|9/9|
|ColQwen2|1|exclusive|CPU|105831|120121|9/9|
|ColQwen2|1|half_shared|wall|53037|57239|9/9|
|ColQwen2|1|half_shared|CPU|52930|60074|9/9|
|ColQwen2|1|prepaid|wall|25|29|9/9|
|ColQwen2|1|prepaid|CPU|27|29|9/9|
|ColQwen2|2|exclusive|wall|53375|57022|9/9|
|ColQwen2|2|exclusive|CPU|106514|119636|9/9|
|ColQwen2|2|half_shared|wall|26702|28525|9/9|
|ColQwen2|2|half_shared|CPU|53271|59831|9/9|
|ColQwen2|2|prepaid|wall|25|29|9/9|
|ColQwen2|2|prepaid|CPU|27|29|9/9|
|ColQwen2|4|exclusive|wall|26536|28408|9/9|
|ColQwen2|4|exclusive|CPU|105732|119026|9/9|
|ColQwen2|4|half_shared|wall|13282|14218|9/9|
|ColQwen2|4|half_shared|CPU|52881|59526|9/9|
|ColQwen2|4|prepaid|wall|25|29|9/9|
|ColQwen2|4|prepaid|CPU|27|29|9/9|
|ColQwen2|8|exclusive|wall|13553|15116|9/9|
|ColQwen2|8|exclusive|CPU|107214|125837|9/9|
|ColQwen2|8|half_shared|wall|6791|7572|9/9|
|ColQwen2|8|half_shared|CPU|53622|62932|9/9|
|ColQwen2|8|prepaid|wall|25|29|9/9|
|ColQwen2|8|prepaid|CPU|27|29|9/9|
|ColQwen2|16|exclusive|wall|8729|9460|9/9|
|ColQwen2|16|exclusive|CPU|133721|154579|9/9|
|ColQwen2|16|half_shared|wall|4379|4744|9/9|
|ColQwen2|16|half_shared|CPU|66875|77303|9/9|
|ColQwen2|16|prepaid|wall|25|29|9/9|
|ColQwen2|16|prepaid|CPU|27|29|9/9|
|ColPali|1|exclusive|wall|96650|133969|9/9|
|ColPali|1|exclusive|CPU|91527|135254|9/9|
|ColPali|1|half_shared|wall|48339|67000|9/9|
|ColPali|1|half_shared|CPU|45777|67643|9/9|
|ColPali|1|prepaid|wall|27|30|9/9|
|ColPali|1|prepaid|CPU|26|31|9/9|
|ColPali|2|exclusive|wall|48647|66746|9/9|
|ColPali|2|exclusive|CPU|92118|134708|9/9|
|ColPali|2|half_shared|wall|24337|33388|9/9|
|ColPali|2|half_shared|CPU|46072|67370|9/9|
|ColPali|2|prepaid|wall|27|30|9/9|
|ColPali|2|prepaid|CPU|26|31|9/9|
|ColPali|4|exclusive|wall|24186|33251|9/9|
|ColPali|4|exclusive|CPU|91442|134021|9/9|
|ColPali|4|half_shared|wall|12106|16640|9/9|
|ColPali|4|half_shared|CPU|45734|67026|9/9|
|ColPali|4|prepaid|wall|27|30|9/9|
|ColPali|4|prepaid|CPU|26|31|9/9|
|ColPali|8|exclusive|wall|12353|17691|9/9|
|ColPali|8|exclusive|CPU|92724|141690|9/9|
|ColPali|8|half_shared|wall|6190|8861|9/9|
|ColPali|8|half_shared|CPU|46375|70861|9/9|
|ColPali|8|prepaid|wall|27|30|9/9|
|ColPali|8|prepaid|CPU|26|31|9/9|
|ColPali|16|exclusive|wall|7957|11071|9/9|
|ColPali|16|exclusive|CPU|115648|174053|9/9|
|ColPali|16|half_shared|wall|3992|5550|9/9|
|ColPali|16|half_shared|CPU|57837|87042|9/9|
|ColPali|16|prepaid|wall|27|30|9/9|
|ColPali|16|prepaid|CPU|26|31|9/9|



## E6 / E7

E6 NOT_RUN：未确认独占GPU预约，因此未测试70.22ms与36.22ms的调度因果；不拿跨批次相减补证。

E7：覆盖冻结HR Dev 40/40=100.00%；相对全部英文池 40/318=12.5786%。主覆盖分母在PLAN中已登记，不能声称覆盖全HR。

|文本来源|计划|n|mean nDCG10|mean r|harm rate|
|---|---|---|---|---|---|
|official_markdown|BM25|40|0.4489531079032611|0.1172566548622946|0.55|
|official_markdown|BM25-R100|40|0.499806365985235|0.016744178641910922|0.125|
|Tesseract411_eng_psm3|BM25|40|0.44920467068955683|0.11485620529564122|0.5|
|Tesseract411_eng_psm3|BM25-R100|40|0.4963178984818537|0.020453913816234914|0.15|

仅从已有全页视觉排序限制候选得到R100，BM25参数与分词不变。OCR为新增文本来源；质量仅Dev诊断，不是独立评估。原始OCR文本只留服务器，不进入Git或附件。



## E8 视觉与文本资产

十进制MB；logical与allocated分开。11格的 fp16 实际张量payload与页数×平均保存向量数×维度×2 精确对账。保存向量可能含特殊token，不另称独立测得的图像patch数量。

|域|检索器|页|视觉logical MB|allocated MB|fp16 payload MB|文本JSON MB|BM25磁盘MB|视觉/BM25|
|---|---|---|---|---|---|---|---|---|
|HR|ColQwen2|1110|213.541574|214.245376|212.785664|3.635768|MISSING|MISSING|
|HR|ColPali|1110|293.72487|295.5264|292.96896|3.635768|MISSING|MISSING|
|Finance|ColQwen2|2942|570.63425|572.399616|568.62976|11.762749|MISSING|MISSING|
|Finance|ColPali|2942|778.504202|783.532032|776.499712|11.762749|MISSING|MISSING|
|Industrial|ColQwen2|5244|1018.197908|1021.349888|1014.624768|10.784878|MISSING|MISSING|
|Industrial|ColPali|5244|1387.653524|1396.16256|1384.080384|10.784878|MISSING|MISSING|
|Pharma|ColQwen2|2313|449.354207|451.87072|447.77856|3.65885|MISSING|MISSING|
|Pharma|ColPali|2313|612.059615|615.911424|610.483968|3.65885|MISSING|MISSING|
|Biomedical|ColQwen2|1016|199.952056|200.577024|199.26016|0.782921|MISSING|MISSING|
|Biomedical|ColPali|1016|268.850872|270.630912|268.158976|0.782921|MISSING|MISSING|
|Economics|ColQwen2|452|88.054372|88.35072|87.74656|1.26616|MISSING|MISSING|
|Economics|ColPali||MISSING|MISSING|MISSING|MISSING|MISSING|MISSING|

BM25每次在内存建立，未持久化倒排索引，磁盘大小与视觉/BM25索引比值不可识别，不填0。Economics×ColPali MISSING_NOT_BUILT，不补建。



## 论文需要的事实与证据（不修改论文）

- BM200 / Dense→R50 / Hybrid→R50：HR、Finance、Industrial均有，含regret/E2E；原记录 `${PROJECT_ROOT}/reports/icde_evidence_closure_003/E1/{per_query_quality_cost.csv,static_quality_e2e.csv,all_unprofiled_requests.csv}`。

- False-Safe代码定义：选择非FullV且真实正遗憾>.05；rate分母为所有查询。不是要求预测risk≤.05，也不是逐请求认证。风险贡献按False-Safe真实遗憾质量/总真实遗憾质量。

- Biomedical协议原SHA `5f3db14fea91d12128d7507d07d7a3c9fe54a7c1dea3d3354207eea84357be3b`；协议时间2026-10-28 11:53:58.962370+08，commit `32b7e2a29cad7ae6031e7102f8851e6fa09d0db8`，commit时间11:53:59+08；首个已记录质量进程12:04:37.979941。

- Economics协议原SHA `c6b76cf2242afe4b8791cd5997b56336f2e6779cc3e17af172575e222950b613`；协议/commit时间2026-10-29 17:25:52+08，commit `093daa67b0e9796a4857259e4ee95c258fc038c5`；首个有效smoke 19:35:44.222928，完整进程19:36:09。更早BLOCKED日志不是质量结果。

- 两份协议分别在各自已记录质量运行之前；不能用Economics协议证明更早的Biomedical预注册。ColPali×Biomedical在2026-10-28 15:03:27.845352开始，晚于ColQwen结果，属于事后补充。基包 `freeze/` 保存净化后的协议与原文件hash/时间记录，原文件保留服务器。



## 工件与边界

- 全部新增输入哈希分阶段保存；逐文件SHA在交付MANIFEST中。保存失败目录和旧脚本，不用新结果覆盖失败。

- 数值小型缓存、抽样索引、CSV、PDF/PNG、脚本可以审核；不包含新原始问题、页面、模型权重、OCR正文、封存标签或完整query-page qrels。

- 本轮只提交审核分支；未自动合并、推送、打tag或提交CMT。新工件是否公开由作者决定。

- 旧正式证书、FrozenMix与事后包络不变；新增结果全部POSTHOC，NOT_CERTIFIED，无新增Serving优越性结论。
