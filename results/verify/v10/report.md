# V10 报告 — 文书数字一致性

- 复核结果：**simulation_report_2026-09-20.docx 全部可核数字支持；Concept Note 第二版未执行（docx 不在本机）**
- 执行：python-docx 抽取 + 与 `comprehensive_summary.npz`、`chirp2d.npz`、`m3b_delay_budget.py` 复算比对。

## 核查表（docx 数字 → 仓库证据）

| docx 表述 | 复核 | 证据 |
|---|---|---|
| D=0.0512 ps/nm，平台 66.3 nm | ✓ 逐位一致 | `comprehensive_summary.npz` 0.05118/66.26（tau_r 字段，见 V3） |
| φ₂=-6.68e-26 s²/rad，匹配啁啾率 1.50e+25 | ✓ | 同文件 -6.681e-26 / 1.4967e+25 |
| 压缩脉宽 0.152 ps，压缩比 22 | ✓ | 3.358ps/0.152ps=22.1 |
| C17：直接积分 0.267 / 快采样 1.000 / 蓄水池+漏电 1.000 / 线性消融 0.400 | ✓ | `comprehensive_summary.npz` direct 0.2667, fast/leaky 1.0, linear 0.4（原始 npz 已指认，C17 的「需指认」项销号） |
| TFLN 424.5 / SiN 46699 / Si 140.1 ps/dB | ✓ 逐位一致 | `m3b_delay_budget.py:60` 复算 |
| 3 dB → 1.27 ns、0.19 m；R=1.5 m 需 0.71 m、23.6 dB | ✓ | L=10ns·c/(2·2.1)=0.714 m；IL=33×0.714=23.6 dB |
| 「D 与几何预言吻合到 8%」 | ✓（口径为 TMM vs FDTD：−9.6%） | 若按解析式 0.0502 vs 实测 0.0512 则偏差仅 +2.0%；建议注明口径 |
| 「平台反射率中位 0.997」 | ✓ | chirp2d R 平台 median=0.9969 |
| 「ripple 峰峰值 ~9%」 | ✓ 但口径不明 | 实为**反射率** ripple（9.1% of mean R）；群延迟 residual ripple 为 1.22 ps = 摆幅的 38%。文书应写明「反射率 ripple」，否则与 V3 的 delay ripple 混淆 |

## M2/M3 数字（digits 0.943、ModelNet40 0.318/0.329/0.400、delay learning 0.838/0.841/0.888）

来源为 lidar-pointnet 仓库 outputs（本机无该仓库正文，见遗留）。TASK_LOG 与 M2/M3 notebook 一致登记，**标：待 GPU 主机随 V5–V8 一并复核**。

## Concept Note 第二版

- 位置在原机 `D:\BaiduSyncdisk\...\kgfp_call2027_concept_note_第二版.docx`，**本机无 D 盘、文件未随仓库提交** → 按任务书规定跳过。
- 本次核查已产出 C2/C7/C8 的修正措辞（见 V1/V2 报告），**Concept Note 第二版若已写入 46 nm/µm / 594 cm⁻¹ / 「1–20 mm 偏差~2%」必须按修正稿改写**——请把该 docx 拷入本工作区后我再跑一轮完整比对。

## 建议措辞（文书级）

1. 「ripple 峰峰值 ~9%（反射率口径）」——或改报群延迟口径「平台群延迟 ripple 1.2 ps（摆幅的 38%），切趾后可压至 0.1 ps 量级（TMM A6）」。
2. 「D 与几何预言吻合到 8%」→ 建议「FDTD 实测 D=0.0512 与解析式 0.0502 偏差 +2%；与 TMM 独立模型 0.046 相差 ~10%」。
