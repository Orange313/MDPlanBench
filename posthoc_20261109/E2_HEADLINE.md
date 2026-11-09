# E1 + E2 main screening result

All new costs: recomposed from measured components (offline screening). No new certification or independent test.

|Domain|Router|OOF risk|Cost ms|DeltaC cf pp [95%]|Seed1–5 range|
|---|---|---:|---:|---|---|
|HR|Ridge_Q|0.047736|23.686|-5.20 [-25.17,+12.07]|-4.73 to +4.64|
|HR|Ridge_QP|0.039562|22.246|+5.55 [-12.74,+19.15]|+5.55 to +5.55|
|HR|LightGBM_Q|0.038126|26.846|-6.03 [-29.23,+8.34]|-6.82 to -0.75|
|HR|LightGBM_QP|0.043294|29.764|-18.40 [-37.31,-7.20]|-20.97 to -17.39|
|Finance|Ridge_Q|0.052397|24.794|-12.49 [-26.66,+4.79]|-14.94 to -9.91|
|Finance|Ridge_QP|0.032589|25.117|-1.47 [-15.30,+20.57]|-1.54 to -1.09|
|Finance|LightGBM_Q|0.049498|25.662|-12.58 [-27.80,+3.45]|-20.07 to -14.78|
|Finance|LightGBM_QP|0.029411|28.316|-6.23 [-21.68,+16.14]|-12.85 to -6.11|
|Industrial|Ridge_Q|0.035725|58.643|-49.60 [-60.90,+3.44]|-52.49 to -46.08|
|Industrial|Ridge_QP|0.045492|32.716|-16.05 [-30.36,+4.99]|-18.06 to -14.14|
|Industrial|LightGBM_Q|0.042204|27.536|-6.58 [-18.54,+11.98]|-14.37 to -7.79|
|Industrial|LightGBM_QP|0.040207|24.523|-1.02 [-17.57,+12.20]|-4.58 to +2.64|
|Pharma|Ridge_Q|0.033982|36.508|-29.04 [-47.53,+3.10]|-32.48 to -22.43|
|Pharma|Ridge_QP|0.038094|25.516|-8.23 [-25.57,+17.88]|-8.72 to -5.53|
|Pharma|LightGBM_Q|0.042185|26.890|-15.01 [-31.98,-0.57]|-19.36 to -8.94|
|Pharma|LightGBM_QP|0.014354|29.622|+8.60 [-7.02,+28.19]|-6.64 to +9.55|
|Biomedical|Ridge_Q|0.000000|35.761|-1.03 [-1.60,-0.49]|-1.03 to -1.03|
|Biomedical|Ridge_QP|0.000000|36.870|-4.16 [-5.17,-2.82]|-4.16 to -4.16|
|Biomedical|LightGBM_Q|0.045033|34.209|-11.70 [-19.22,-3.64]|-13.23 to -7.52|
|Biomedical|LightGBM_QP|0.051726|34.751|-15.47 [-24.34,-5.20]|-16.79 to -14.77|
|Economics|Ridge_Q|0.049288|22.311|+2.81 [-8.83,+13.91]|+2.84 to +3.18|
|Economics|Ridge_QP|0.034620|25.386|+1.01 [-9.04,+11.51]|+0.98 to +1.28|
|Economics|LightGBM_Q|0.023108|27.696|-0.08 [-11.81,+10.87]|-0.11 to +0.20|
|Economics|LightGBM_QP|0.019839|28.953|-2.24 [-8.79,+4.90]|-2.27 to -1.95|

Intervals are conditional on fitted kappa/weights; all results are post-hoc. Economics has one source component.
The adapter retains signed archived execution-context differences. Per-query negative accounting estimates are explicitly counted, never clipped. They are not physical latency observations.
Eligible cells for conditional hardware measurement: 0. No reserved GPU has been confirmed; hardware measurements are NOT_RUN.

Status: PARTIAL — the computation completed, but 10 main cells contain negative query/process accounting estimates from transferring signed archived execution-context differences. These are retained without clipping and are not physical times. 2 OOF mean risks exceed the nominal training budget .05; this diagnostic does not certify a risk contract.
