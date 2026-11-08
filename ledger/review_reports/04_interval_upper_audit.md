# Task 31｜4. 区间上界审计（POSTHOC）

PASS（48个工作点逐项列出）；不显著不等于收益为零。四静态与三动作目录保持分列。

| 批次 | 模型 | 最大上界 pp | 上界>5 | 上界>10 | 下界>0 |
|---|---|---:|---:|---:|---:|
| 021_POSTHOC | LightGBM_Q | 15.37734136 | 3 | 2 | 0 |
| 021_POSTHOC | LightGBM_QP | 27.39726078 | 3 | 3 | 0 |
| 021_POSTHOC | Ridge_Q | 18.16098574 | 3 | 2 | 0 |
| 021_POSTHOC | Ridge_QP | 29.66710804 | 4 | 3 | 0 |
| ORIGINAL_FROZEN | Q | 21.03482327 | 4 | 2 | 0 |
| ORIGINAL_FROZEN | QP | 25.92454823 | 4 | 3 | 0 |
| ORIGINAL_FROZEN | RR-hard | 25.33767406 | 4 | 1 | 0 |
| ORIGINAL_FROZEN | RR-soft | 21.28014639 | 2 | 2 | 0 |

各行记录历史固定seed、2000次。主列严格使用原图登记区间；另列paired-ratio敏感性。重要CONDITIONAL：Economics旧图按文档27保留ms区间除固定FullV均值的口径，而§V-C概括为每次重采FullV分母，二者不能称完全相同；四个Economics原图点需要作者注明此差异。021本轮从原始逐请求记录独立重放，70869数值、48527检查均通过。开发域按族/进程，Biomedical按来源/进程；Economics按族/进程但仅条件于一个来源组件，不能外推来源总体。多个逐点区间未联合校正；本表不进行新的显著性筛选。
