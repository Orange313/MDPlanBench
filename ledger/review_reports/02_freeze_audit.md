# Task 31｜2. 冻结与首次执行时间线

PASS（已有执行记录的先后顺序）；CONDITIONAL（历史审计并非外部可信时间戳，不能排除没有记录的外部执行）。完整时间/commit/hash见freeze/chronology.csv。

- Biomedical 冻结：2026-10-28 11:53:58.962370+08:00；协议SHA256 5f3db14fea91d12128d7507d07d7a3c9fe54a7c1dea3d3354207eea84357be3b；冻结代码32b7e2a29cad7ae6031e7102f8851e6fa09d0db8。首个记录的ColQwen2质量进程12:04:37.979941开始，最终主实验12:35:11完成。
- Economics 冻结：2026-10-29 17:25:52.376911+08:00；协议SHA256 c6b76cf2242afe4b8791cd5997b56336f2e6779cc3e17af172575e222950b613；冻结代码093daa67b0e9796a4857259e4ee95c258fc038c5。16:12 E2条目为BLOCKED，不是质量执行；17:27资源门禁未通过，未执行模型质量；监测记录19:35:44启动8页smoke，后完成正式评价，19:44:44主表归档，代码b10796851c10db218fcdaed41dba7db585b38e36。
- ColPali×Biomedical：2026-10-28 15:03:27.845352首进程；16:43:58汇总，代码42c8aee489bd4cdc10b670a5dcfbf1d0c1c8dd1a。晚于同日12:35 ColQwen2主结果，必须标post-hoc。007中12:03 ColPali pilot是旧Dev，不能当作Biomedical执行。

原协议和历史manifest保持原字节/哈希；公开版需去除内部路径时会独立标注导出hash，不将脱敏版冒充历史原文件。协议中的计划/模型/seed沿用冻结记录，不使用已见结果重新选择。
