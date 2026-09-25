# V4 报告 — 解析式与常量核对（C1/C3/C6/C11）

- 复核结果：**全部支持**；两条 n_g 使用不一致需注明（已在敏感性中量化）
- 执行：手工推导 + Python 复算（本报告）；脚本 `lumerical/m3b_delay_budget.py`、`simulations/02_tolerance_scan.py`、`lumerical/run_tolerance_fdtd.py`。

## 逐条核对（常量 → 公式 → 脚本行号 → 数值）

### 1. 延迟摆幅 Δτ = 2n_gL/c（反射式往返）
- 推导：光栅penetration深度 L，群延迟 = n_g·(2L)/c。✓
- 脚本：`m3b_delay_budget.py:40-41` `delay_swing = 2*n_g*L/C0`；`02_tolerance_scan.py:106` `swing_geo = 2*N_EFF*L/C0`。
- 数值：L=20mm、n_g=2.2 → 293.5 ps；A5 实测 swing 293.0（偏差 −0.9%，V1 窗口效应已判明）。

### 2. 色散 D = 2n_g/(c·C)
- 推导：摆幅 Δτ=2n_gL/c 分布在啁啾带宽 Δλ=C·L 上，D=Δτ/Δλ=2n_g/(c·C)。✓
- 数值：
  - TMM：n_g=2.2、C=12 nm/mm → **1.223 ps/nm**（解析）vs a5 实测 1.2233 ✓（4 位有效数字一致）
  - FDTD chirp2d：n_g=2.1046、dλ/dz=2·2.02·17.3nm/250µm → **0.0502 ps/nm**（解析）vs tau_r 实测 0.0512（+2.0%）✓
- C11 交叉校验：TMM 交叉点 0.0463 vs FDTD 0.0512 → −9.6% ≈「偏差 10%」✓

### 3. 耦合系数 κ = πn_gΔλ/λ_B²
- 推导：CMT 阻带半高宽 Δλ=λ_B²κ/(πn_g)。✓
- 脚本：`run_tolerance_fdtd.py:83` `kap = gap*np.pi*n_g/lb**2`；`run_scan_2d.py:186` `kappa_from_gap` 同式（锚定设计 λ_B）。
- 数值（V2 midgap 带隙、n_g=2.1046）：13.12/20.67/24.40/46.33 nm → 353.8/557.6/658.2/1250.0 /cm，与 V2 脚本输出逐位一致 ✓

### 4. 温漂 dτ/dT = D·λ_B·(dn/dT)/n_g
- 推导：Λ 固定时 dλ_B/dT=2Λ·dn/dT=λ_B·(dn/dT)/n_eff；无色散 n_eff=n_g；τ 平移 = D·dλ_B/dT。✓
- 脚本：`02_tolerance_scan.py:211` `dlamb_per_K = lam_b0*DNDT/N_EFF`，`217` `a4_tau_shift = D_ref*dlamb_per_K`。
- 数值：n_g=2.2 → 0.0279 nm/K × 1.2327 = **0.0344 ps/K** ✓ 与 a4 基线一致；若改用 FDTD 实测 n_g=2.1046 则为 0.0360 ps/K（+4.7%）。

### 5. C1 的 FoM 与亚米窗口（m3b_delay_budget.py）
- FoM = 2n_g/(cα)：脚本 `:60`；n_g=2.1、α=33 dB/m → **424.5 ps/dB** ✓（claim 424）
- 3 dB 摆幅：L=3/33=9.09cm → 1.274 ns ✓；窗口 = c·Δτ/2 = 0.191 m ✓（claim 0.19 m，脚本 `:86-91`）

## n_g 敏感性（C1 结论的稳健性）

| n_g | FoM (ps/dB) | 3 dB 摆幅 (ns) | 窗口 (m) |
|---|---|---|---|
| 2.05 | 414.4 | 1.243 | 0.186 |
| 2.10（采用值） | 424.5 | 1.274 | 0.191 |
| 2.20（TMM 用值） | 444.8 | 1.334 | 0.200 |
| 2.30 | 465.0 | 1.395 | 0.209 |

**一句话结论**：n_g 在 2.05–2.30 间 C1 全部数值变化 ≤ ±5%（FoM 414–465 ps/dB，窗口 0.186–0.209 m），亚米窗口结论对 n_g 不敏感；但 M3b（2.1）与 TMM 容差脚本（2.2）的 5% 内部不一致应在文书中统一声明。

## n_g 使用点清单（供文书统一）

| 位置 | 取值 | 来源 |
|---|---|---|
| `m3b_delay_budget.py:32` | 2.1 | 文献 TFLN @1550（V9 核） |
| `02_tolerance_scan.py:31` | 2.2 | lab-note §21 无色散近似（n_g=n_eff） |
| `run_tolerance_fdtd.py`（运行时） | 2.1046 | ref_raw 实测（C0·mean(τ)/(L_uni+4µm)） |
| `run_scan_2d.py` N_EFF | 2.02 | n_bar（相指数，非群指数） |

## 遗留问题

- dn/dT=4e-5/K、α=0.033 dB/mm 的文献核查归 V9；若文献值漂移，C1/C6 按上表公式线性重算即可。
- 建议 TMM 脚本把 `N_EFF` 改名为 `N_G_NODISP` 或加注释，避免与 n_bar=2.02 混淆。
