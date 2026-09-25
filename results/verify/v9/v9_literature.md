# V9 报告 — 文献常量核查

任务：核查决定 C1/C6 的 5 个文献常量（VERIFICATION_PLAN.md §1 末段）。
方法：联网文献检索（2026-09-25）。判定口径：我们的取值是否落在文献报道区间内、偏保守还是偏乐观。

## 常量对照表

| 常量 | 我们的取值 | 文献区间 | 代表文献 | 判定 |
|---|---|---|---|---|
| TFLN 传播损耗 α | 0.033 dB/mm = **0.33 dB/cm**（m3b_delay_budget.py:34） | 纪录 0.027 dB/cm（化学机械抛光/长波导）；常规刻蚀脊形 0.2–0.4 dB/cm；早期 2.7 dB/m | [Wu et al., Nanomaterials 2018 (0.027 dB/cm)](https://www.mdpi.com/2079-4991/8/11/910)；[Liang et al. 2018 (0.35 dB/cm TE)](https://www.researchgate.net/publication/323099819)；[Zhang et al. 2017 (~2.7 dB/m)](https://arxiv.org/pdf/1712.04479) | ✔ 落在常规工艺区间，吻合任务书目标 0.03–0.05 dB/mm；相对纪录值保守 12× |
| SiN 损耗 | 0.3 dB/m（m3b:35，注 "Geng 2026"） | <0.1 dB/m 已演示，纪录 0.045 dB/m；常规超低损 0.1–1 dB/m；Bauters 单模 0.7 dB/m | [Blumenthal et al. 综述, Sensors 2022 (<0.1 dB/m, 纪录 0.045 dB/m)](https://www.mdpi.com/1424-8220/22/11/4227)；[Bauters et al. (0.70 dB/m)](https://www.researchgate.net/publication/249328384)；[UCSB (<0.05 dB/m)](https://ocaqpi.ece.ucsb.edu/research/ultra-low-loss-photonic-integration) | ✔ 区间中部，合理 |
| Si 损耗 | 1 dB/cm（m3b:36，注 "rough"） | 典型 0.1–1 dB/cm | [Chin. Phys. B 综述 (0.1–1 dB/cm)](https://cpb.iphy.ac.cn/en/article/pdf/preview/10.1088/1674-1056/ad0e5b.pdf) | ✔ 取保守端 |
| LN dn/dT | 4e-5/K（02_tolerance_scan.py:34） | dn_o/dT ≈ 3.9×10⁻⁵/K，dn_e/dT ≈ 3.2×10⁻⁵/K（体材料 @1550）；TFLN 波导实测同量级 | [SAM 数据页 (3.9/3.2×10⁻⁵)](https://www.samaterials.com/content/how-lithium-niobate-is-utilized-for-refractive-index-measurement.html)；[Han et al., 中国光学 2025 (TFLN 热光表征)](https://www.researching.cn/ArticlePdf/m00005/2025/23/5/051302.pdf) | ✔ 4e-5/K 略偏保守（取上限），任务书给的 4–6e-5/K 区间上沿略高，实际文献值 3–4e-5/K |
| TFLN n_g @1550 | 2.1（m3b:32）；2.2（02_tolerance_scan.py:31 N_EFF） | LN 材料 n_o=2.211、n_e=2.138 @1550；TFLN 波导群指数实测 ~2.21 | [Sci. Rep. 2020 (n_o=2.21116, n_e=2.13755)](https://www.nature.com/articles/s41598-020-73936-x.pdf)；[UD 学位论文 (n_g=2.214 @1550)](https://udspace.udel.edu/server/api/core/bitstreams/a574369c-1d1c-4a21-a674-e74b09068f6a/content)；本仓库 FDTD 实测 n_g=2.1046（ref_raw.npz，w=1.5µm 脊形） | ✔ 2.1 与本仓库 FDTD 实测一致；2.2 接近文献值；两者差异 ~5% 已在 V4 敏感性中覆盖 |

## 对 C1/C6 的影响

- **C1（424 ps/dB、1.27 ns、0.19 m）**：α=0.33 dB/cm 有充分文献支撑且偏保守。
  若用纪录值 0.027 dB/cm，FoM 变为 424×(0.33/0.027)≈5200 ps/dB、3 dB 窗口 2.3 m ——
  即**我们的亚米窗口结论是保守下界，不会因文献值更好而失效**；风险只在于实际流片
  达不到 0.33 dB/cm（早期刻蚀工艺 0.4–1 dB/cm 时窗口缩到 0.06–0.16 m，仍是亚米量级）。
- **C6（0.034 ps/K）**：dn/dT 实际文献值 3.2–3.9e-5/K 比我们用的 4e-5 低 3–20%，
  温漂结论只会更好（0.027–0.033 ps/K），不影响「可忽略」判定。

## 结论

5 个常量全部有文献支撑，取值均居中或偏保守，**C1/C6 的文献风险解除**。
建议 Concept Note 引用：TFLN 损耗引 Wu 2018（纪录）+ Liang 2018（常规），
dn/dT 引 Han 2025 或 Sellmeier 温度项，n_g 用本仓库 FDTD 实测 2.10 并注明文献 ~2.21。
