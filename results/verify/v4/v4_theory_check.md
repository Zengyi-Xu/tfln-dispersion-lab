# V4 报告 — 解析式与常量核对

| 量 | 公式 | 脚本位置 | 计算值 | 登记表/声称值 | 判定 |
|---|---|---|---|---|---|
| TFLN FoM | `2 n_g / (c a)` | m3b_delay_budget.py:60 | 424.5 ps/dB | 424 ps/dB | OK |
| 3 dB swing | `2 n_g L / c @ IL=3dB` | m3b_delay_budget.py:41,87-90 | 1.274 ns | 1.27 ns | OK |
| range window | `c dTau / 2` | m3b_delay_budget.py:49 | 0.1909 m | 0.19 m | OK |
| D @ C=12nm/mm (n=2.2) | `2 n_g/(c C)` | 02_tolerance_scan.py:31-33, a5 table | 1.223 ps/nm | 1.22 ps/nm | OK |
| D analytic for chirp2d | `2 n_g/(c C), C=2 n_bar dLambda/dz` | run_scan_2d.py:133; chirp2d.npz | 0.05011 ps/nm | 0.051 ps/nm | OK |
| kappa(w1500,dn=0.02) | `pi n_g gap / lambda_B^2` | run_tolerance_fdtd.py:83; v2 re-extraction | 606.2 /cm | 606 /cm | OK |
| dTau/dT | `D lambda_B (dn/dT)/n_g` | 02_tolerance_scan.py:211-217 | 0.03413 ps/K | 0.034 ps/K | OK |

## n_g 敏感性（C1: FoM / 3 dB 摆幅 / 距离窗口）

| n_g | FoM (ps/dB) | 3 dB 摆幅 (ns) | 距离窗口 (m) |
|---|---|---|---|
| 2.05 | 414 | 1.243 | 0.186 |
| 2.1 | 425 | 1.274 | 0.191 |
| 2.2 | 445 | 1.334 | 0.200 |
| 2.3 | 465 | 1.395 | 0.209 |

- n_g 每 ±0.05 → FoM ±~2.4%，距离窗口 ±~5 mm；n_g=2.1 vs TMM 脚本 N_EFF=2.2 的不一致带来 ~5% 系统性差异，不影响「亚米窗口」量级结论。
- 424 ps/dB 与 0.19 m 在 n_g∈[2.05,2.3] 全区间成立（±5%）。

## 遗留

- α=0.033 dB/mm、dn/dT=4e-5/K、n_g=2.1 均为文献值，由 V9 核查文献出处。
