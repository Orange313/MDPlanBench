# posthoc_20261109 — frozen execution plan

Authoritative order: Orange31, revision 1, resource a71e700f-dd74-4350-b621-2ea6892ab19f, revision b652d5fb-ffeb-4d4e-860e-27fc52177884, canonical SHA256 eb5d11ecdb7761bf49558d5e34442988a0ce51af58075e428e0f71b3fdb697b6.

Base: icde27-eab-v1.1 / e9d4c2d14abca6003001caf8010da4f6b7321669.
Branch: codex/posthoc-20261109. No tag this round. Real execution timestamps use Asia/Shanghai; the directory date is the author-assigned diagnostic label.

## 2. 登记参数（PLAN.md 原样写入）

### 2.1 共同对象

- 检索器：ColQwen2。
- 语料 c ∈ {HR, Finance, Industrial, Pharmaceuticals（仅 dev split，45 题）, Biomedical（160 题）, Economics（58 题）}。
- 动作集 A = {FullV, BM-100, BM25}（三动作）。
- Router ρ ∈ {ridge-Q, ridge-QP, LightGBM-Q, LightGBM-QP}，取自 post-hoc 批次。模型权重与特征预处理冻结，只重选 κ。
- 质量：nDCG@10（线性增益）；regret r_a(q) = max{nDCG(FullV, q) − nDCG(a, q), 0}。
- 成本：s_a(q, m) 为查询 q 在进程 m 中动作 a 的匹配静态路径成本（post-hoc 批次实测，按进程保留）；o_ρ(q, m) 为 router ρ 的决策开销（特征、预测，以及 QP 的探针）。QP 选择 BM-100 时复用探针候选，不得重复计费。组合规则**完全复用 Fig. 5(b) 会计分解的现有代码**。

### 2.2 回归闸门（先于一切 E2 计算）

在 κ=20 下，用适配任意动作数组后的新入口重算：Fig. 5(b) 的三项分解及四个 router 在六个语料上的 ΔC，必须与现有结果**逐位一致**。任何一项不一致即停止 E1/E2，报告差异表。

### 2.3 折划分

- K = 5，按组划分：开发域与 Economics 按问题族分组；Biomedical 按来源讲座分组（27 个）。
- 分配方法：组按 ID 排序，用种子打乱后，依次放入当前查询数最少的折（贪心平衡）。
- 主种子：20261109。稳定性检查种子：1, 2, 3, 4, 5。
- 记折 k 的留出集为 H_k，训练集为 T_k = Q_c \ H_k。

### 2.4 网格

- 风险预算 b ∈ {0.01, 0.02, 0.03, 0.05, 0.075, 0.10}。主报告点 b = 0.05。
- κ ∈ {0, 1, 2, 5, 10, 20, 40, 80, 160, 320, ∞}。
  - 一般情形：a_{ρ,κ}(q) = argmin_a { ĉ_a + κ · max(r̂_{ρ,a}(q), 0) }，ĉ_a 与 r̂ 的定义、归一化方式和平局规则沿用冻结代码（与论文 Eq.(7) 一致），并在 PLAN.md 中写明。
  - κ = 0：取 argmin ĉ_a（即 BM25）。
  - κ = ∞：**定义为全部走 FullV**，不按预测 regret 取 argmin。

### 2.5 κ 选择规则（每折、每个 b）

κ*_{k,b} = 在 T_k 上满足 mean_{q∈T_k} r(q | κ) ≤ b 的 κ 中，mean_{q∈T_k} C_{ρ,κ}(q) 最小者。
其中 C_{ρ,κ}(q) 为跨进程平均的组合成本。κ = ∞ 始终可行（regret 为 0），因此总有解。若成本并列，取较大的 κ。

### 2.6 Mixture（每折、每个 b）

在 T_k 上计算各动作的平均 regret r̄_a^T 与平均成本 C̄_a^T，求解

min_w Σ_a w_a C̄_a^T s.t. Σ_a w_a r̄_a^T ≤ b，Σ_a w_a = 1，w ≥ 0，

得到权重 w^{(k,b)}。在 H_k 上按期望计算：R_mix(k,b) = Σ_a w_a · mean_{q∈H_k} r_a(q)，C_mix(k,b) 同理。主结果用期望值；另按固定种子实际抽样执行一次，作为次要结果。

### 2.7 OOF 汇总与 ΔC_cf 定义

1. Router：R_ρ^OOF(b) = (1/|Q_c|) Σ_k Σ_{q∈H_k} r(q | κ*_{k,b})；C_ρ^OOF(b) 同理（成本取跨进程平均）。
2. Mixture：R_mix^OOF(b) 与 C_mix^OOF(b) 为各折结果按 |H_k| 加权的平均。
3. Cross-fitted 前沿 H(·)：取点集 { (R_mix^OOF(b), C_mix^OOF(b)) : b ∈ 网格 } ∪ { FullV 点 (0, C̄_FullV)，BM25 点 (r̄_BM25, C̄_BM25) }，其中 FullV、BM25 点为全语料均值（静态计划无需拟合）。取其下凸包，在 [0, r̄_BM25] 上分段线性插值；风险超过 r̄_BM25 时 H = C̄_BM25。
4. **定义**：
   ΔC_cf(ρ, b) = 100 × [ H(R_ρ^OOF(b)) − C_ρ^OOF(b) ] / C̄_FullV，单位 pp。
   C̄_FullV 为该语料在 post-hoc 批次中的 FullV 平均成本。正值表示 router 在相同实现风险下比 cross-fitted mixture 便宜。
5. **冻结参照**：κ = 20（不做选择）在同一框架下的 ΔC_cf(ρ, κ=20) = 100 × [ H(R_ρ(κ=20)) − C_ρ(κ=20) ] / C̄_FullV。

### 2.8 区间与稳定性

- 主种子下固定折划分、固定已拟合的 κ*_{k,b} 与 w^{(k,b)}，按 §0.3 的单元做 2,000 次配对 bootstrap，每次重算 OOF 汇总、H 与 ΔC_cf。区间注明"conditional on fitted κ and weights"。
- 用种子 1–5 各重做一次折划分与拟合，报告 ΔC_cf 点估计的范围和所选 κ 的分布。

### 2.9 条件实测

只有当某个格子（语料 × router，b = 0.05）的 ΔC_cf 95% 区间**完全大于零**时，才对该组合（所选 κ）在 resident harness 中按原计时协议实测一次：3 进程 × 3 次重复，单次不超过 1 小时 GPU，需要独占卡并在 ResourceGuard 下运行。其余格子不实测。未预约到 GPU 则记 NOT_RUN 并在汇总中标明。

---



## Implementation details recorded before new screening

- Plan order is FullV, BM-100, BM25; finite-kappa action ties use the first index, exactly as frozen numpy.argmin. Cost vector is the frozen domain cvec normalized by FullV; no target outcomes modify it.
- Fold group IDs are sorted, shuffled with numpy.default_rng(seed), then assigned to the lowest-count fold (first fold index breaks count ties). Main fold seed20261109; stability seeds1,2,3,4,5. New conditional bootstrap seed20261109 is shared across domain-local cells, B=2000; original E3 seeds remain unchanged.
- Mixture LP uses scipy HiGHS, bounds[0,1], the original1e-12 budget tolerance; selected finite-kappa risk constraint uses mean risk<=b. Kappa selection cost ties choose larger kappa including infinity. Models and predicted regrets remain frozen.
- Arbitrary-action accounting retains the original Figure5(b) signed route-minus-selected-static difference, including execution-context differences; it is not called pure feature or probe overhead. Equivalently C_new=T_route20+(S_new-S_old). QP adds/removes the measured BM-search component when a change to/from FullV changes whether the probe can be reused. The same-action identity returns the original archived route cost exactly. No residual is fitted to new labels or results. Report negative per-query accounting values rather than clipping them; they are a limitation of transferring execution-context differences and are never physical-time measurements.
- Every new accounting result is labelled: recomposed from measured components (offline screening). Report measured signal components and execution-context terms separately.
- Bootstrap conditions on already-fitted fold kappas and weights: resample original groups and paired process positions, recompute OOF means and the lower hull; do not refit inside bootstrap. Save ragged query-index offsets/values, process indices and every DeltaC draw. Cross-domain/source-population guarantees are not claimed.
- The secondary single sampled mixture uses a deterministic SHA256 uniform keyed by seed20261109/domain/budget/query ID; its cost is an offline selected-component sum, not fresh GPU execution.
- E5 workers1,2,4,8,16;3 rounds; one RNG20261109 permutes settings sequentially by round. Tesseract4.1.1 eng psm3, child OMP_THREAD_LIMIT=1. Reuse the existing1016 PNGs; stdout only, no duplicate image/temp export. One text file per setting, repeated runs save only hashes/timings. Disk cap1,000,000,000 bytes; verify free space before launch and during output writes. Record shared-host CPU load and do not imply exclusive CPU resources.
- E6 is NOT_RUN without explicit exclusive-GPU reservation. Current idleness is insufficient; no CUDA task starts automatically.
- E7 denominator is the frozen HR Dev query workload from the common evaluation objects; report coverage against both that workload and the318-query English pool, without reading the latter's labels. Only existing full-page score-covered Dev IDs are eligible; no new FullV rankings. Below50% workload coverage means NOT_RUN. OCR uses the historical4-worker dispatch and identical engine settings after E5 timing has finished, so it does not contaminate the OCR timing comparison.
- E8 reports logical bytes and allocated disk blocks separately. There is no persisted BM25 index where it is rebuilt from pages.json; mark disk index and visual/index ratio MISSING rather than zero. Stored multi-vector token counts include any saved special vectors; do not silently equate them with raw image patch counts.
- K17 uses the original legal Pharma Fit/Dev, subsets and seeds, saved per-query kappa20 outputs and the original four-static diagnostic comparator. No retraining. Report together with kappa10 and the undocumented reason for that display choice.
- Strict gates precede new results: arbitrary-action kappa20 must reproduce the existing unrounded H/S/O/DeltaC exactly; E3 endpoint error<=.01pp. Keep original gate attempt and all failures.
- All new files below posthoc_20261109; no sealed labels, no new training, no changes to original results, Paper, LaTeX or bilingual drafts. No public push until new-content privacy/rights review is complete; no tag or main merge.
