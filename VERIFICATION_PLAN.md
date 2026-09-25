# KGFP 结果核查与验证任务书（防幻觉）

> 目的：把目前写进 Concept Note / TASK_LOG / 推荐信的每一条关键结论，
> 都对应到「脚本 + 数据文件 + 文献」三重证据；凡是当前仓库数据**不直接支持**的说法，
> 标记为风险项并安排复算。本任务书面向一台空闲的 GPU 主机执行（纯 Python/PyTorch 任务），
> 需要 Lumerical 的新仿真单列在最后一节（只能回本机跑）。
>
> 生成日期：2026-09-25。执行后把结果写进 `results/verify/` 并回填 TASK_LOG。

---

## 1. 关键结论登记表（claim → 证据 → 风险）

| # | 结论（现写法） | 证据位置 | 仓库数据是否直接支持 | 风险 | 验证任务 |
|---|----------------|----------|----------------------|------|----------|
| C1 | TFLN 延迟/损耗 FoM = 424 ps/dB，3 dB 摆幅 1.27 ns ↔ 0.19 m 窗口 | `lumerical/m3b_delay_budget.py`（N_G=2.1, α=0.033 dB/mm） | ✅ 是（解析式） | 低：依赖 α、n_g 文献值 | V4/V9 |
| C2 | 摆幅随 L 线性，1–20 mm 偏差 ~2% | `results/tolerance_scan.npz` | ⚠️ **部分不支持**：实测偏差 1mm −14.9%、2.5mm −6.2%、5mm −2.9%、10mm −1.6%、20mm −0.9% | **高：现表述过于乐观** | V1 |
| C3 | D 由啁啾率决定，C=12 nm/mm → D≈1.22 ps/nm | 同上（a5_D≈1.22–1.30） | ✅ 是（≥2.5mm） | 低 | V1/V4 |
| C4 | 余弦切趾 ripple 2.85→0.09 ps，摆幅保留 1/3 | 同上（a6: 0.089 ps, 11.55/34.40=33.6%） | ✅ 是 | 低 | V1 |
| C5 | 随机相位误差 σ_λB≤0.1 nm 可忽略，且不随 L 增长 | 同上（a3: 2.85→2.93 ps；a3L 不增长） | ✅ 是 | 低 | V1 |
| C6 | 温漂 0.03 ps/K、1 K/mm 梯度无畸变 | 同上（a4_tau_shift=0.034 ps/K） | ✅ 是 | 低：dn/dT=4e-5/K 需文献 | V1/V9 |
| C7 | A1 条宽标定 dλ_B/dw = 46 nm/µm（R²=1.000） | `lumerical/results/tolerance_fdtd.npz` | ❌ **不支持**：该 npz 由旧 `band_center` 法产出，斜率仅 21.9 nm/µm 且 λB(w) 非单调（w1520 下掉）；46 nm/µm 来自未提交的「最长连续段」重提取 | **高：证据未入库** | V2 |
| C8 | W1470 κ=594/cm（重提取后） | 同上 | ❌ npz 里 w1470 κ=444/cm | **高：证据未入库** | V2 |
| C9 | A2 κ(dn) 线性 +8%，λ_B 对 dn ±10% 仅漂 0.03 nm | 同上 + dn010/dn040 粗点 | ⚠️ 粗点齐、细点（0.018/0.022）在库里；+8% 未系统复核 | 中 | V2 |
| C10 | A2b 啁啾 dn±10%：D=0.051 不变，ripple 最坏 +24%；须用 R>0.9 平台提取 | `lumerical/results/chirpdf018/022_raw.npz` | ⚠️ 原始数据在，提取脚本与窗口选择未入库 | 中 | V3 |
| C11 | TMM vs FDTD 交叉校验偏差 10%（0.046 vs 0.051） | `a5_fdtd_check_D=0.0463` + chirp2d FDTD 0.051 | ✅ 是 | 低 | V3/V4 |
| C12 | M7：瓶颈在 echo 编码（0.31/0.41 vs raw 0.66），非蓄水池/二值化 | `lidar-pointnet/outputs_m7/results.json` | ✅ 是（3 种子） | 低：仅 3 种子、单一数据集 | V5 |
| C13 | 池权重 4–8 bit 量化不降性能 | 同上（R1_quant*=0.41–0.42） | ✅ 是 | 低 | V5 |
| C14 | KITTI 全量 road 0.872→**0.923**（+0.05），uav 0.758→0.857 | `snn/outputs_isal/road_kitti/results.json` | ✅ 数值在（⚠️ JSON 键名乱码，需修复） | 中：单次运行、无种子方差 | V6 |
| C15 | 训练预算决定绝对性能（0.766→0.923），扫描链价值在受限场景 | 小预算 0.766 + 全量 0.923 | ⚠️ 是，但中间预算点缺失 | 中 | V7 |
| C16 | 合成 0.892/0.919 与真实 0.923 一致 → 生成器被背书 | `outputs_isal/road_*/results.json` | ⚠️ 不同任务/类集合，「惊人一致」表述偏强 | 中 | V8 |
| C17 | M1 时标分离：蓄水池+漏电积分 1.00 vs 直接积分 0.27 | `simulation_report_2026-09-20.docx` §2 | ⚠️ 数字在报告里，原始 npz 需指认 | 中 | V10 |

**文献常量待核（V9）**：TFLN α=0.033 dB/mm、SiN α=0.3 dB/m、Si α=1 dB/cm、LN dn/dT=4e-5/K、n_g≈2.1。
这些值直接决定 C1/C6，若文献值不同，亚米窗口结论要重算。

---

## 2. 已确认的疑点（执行前必读）

1. **C2 表述错误风险**：`a5_swing/a5_swing_geo` 在 1 mm 处只有 0.851。
   两种可能：(a) 短 L 时啁啾总量 ≈ 局域带隙，`R>0.5` 平台区提取把带边曲率算进来，低估摆幅；
   (b) 物理上短器件确实达不到几何摆幅。**结论要改成「≥5 mm 偏差 ≤3%」或修正提取窗口**——由 V1 判定。
2. **C7/C8 证据未入库**：46 nm/µm 与 κ=594/cm 来自口头/日志里的重提取，
   `tolerance_fdtd.npz` 仍是旧值（21.9 nm/µm、444/cm）。**必须把「最长 T<0.5 连续段」
   重提取写成脚本并提交**，否则这两条结论在仓库层面不可复现——这是当前最大的幻觉风险点。
3. **C14 键名乱码**：`road_kitti/results.json` 的键是 GBK 解码错误（`HRRP+CNN1D`）。
   数值可信，但报告引用前需修复键名编码。
4. **n_g 不一致**：M3b 用 2.1，TMM 容差脚本用 N_EFF=2.2（无色散近似）。
   对 C1 影响 ~5%，需在报告里说明并做敏感性（V4）。

---

## 3. GPU 主机执行任务（按优先级排序）

> 约定：所有输出写到 `results/verify/<任务号>/`，附 `report.md`。
> 验收标准写在每个任务末尾；未达标则在报告里给出修正后的结论表述。

### V1 — A3/A5/A6 TMM 复核与 C2 判定（CPU，<10 min）
- 跑 `simulations/02_tolerance_scan.py`（5 种子），另加两个提取窗口变体：
  (a) 现行 `R>0.5` 平台；(b) `R>0.9` 平台 + 最长连续段；(c) 排除带边 2×局域带隙。
- 对每个 L 输出 swing/D/ripple，并和几何摆幅对比。
- **判定 C2**：若 (b)/(c) 下 1 mm 偏差仍 >5%，则改表述为「≥5 mm 线性度 ≤3%，短器件需切趾补偿」。
- 输出：`v1_tolerance_recheck.json` + 对比图。
- 验收：三种窗口结果表格齐全；给出最终建议措辞。

### V2 — A1/A2 重提取（CPU，<5 min；**最高优先级，直接决定 C7/C8**）
- 从 `lumerical/results/w{1470,1480,1500,1520,1530}_raw.npz`、`dnf{018,022}_raw.npz`、
  `dn010_raw.npz`、`dn040_raw.npz` 读 λ、T。
- 实现「最长 T<0.5 连续段」带隙提取：找所有 T<0.5 的连续区间，取最长者的两端点为带隙边，
  中心取区间内 T 最小值；与旧 `band_center` 交叉法并排输出。
- 计算 dλ_B/dw（线性拟合 + R²）、κ(w)、κ(dn)、λ_B(dn)。
- 验收：给出「若 w1520/w1470 为离群点」的判据（残差 >3σ 或非单调）；最终斜率与 κ 表；
  明确 46 nm/µm 是否成立。输出 `v2_a1a2_reextract.json` + λB(w) 图。

### V3 — A2b 啁啾提取稳健性（CPU，<10 min）
- 对 `chirpdf018/022_raw.npz`（及 `chirp2d.npz` 基准）用 R 阈值 {0.5,0.7,0.8,0.9,0.95}
  × {全域拟合, 最长连续段} 提取 D 与 ripple_pp。
- 验收：给出 D 对阈值的标准差；确认「R>0.9 平台」是唯一稳健选择；
  复核 ripple +24%（dn=0.022 vs 0.020）。输出 `v3_chirp_extract.json`。

### V4 — 解析式与常量核对（CPU，<30 min）
- 用纸笔推导 + 脚本复核：Δτ=2n_gL/c、D=2n_g/(c·C)、κ=πn_gΔλ/λ_B²、dτ/dT=D·λ_B·(dn/dT)/n_g。
- 对 n_g∈{2.05,2.1,2.2,2.3} 做 C1 敏感性：424 ps/dB 与 0.19 m 窗口的变化范围。
- 输出 `v4_theory_check.md`：每个常量 → 公式 → 脚本行号 → 数值。
- 验收：所有脚本常量都能在公式里对上号；给出 n_g 不确定度对结论的影响一句话。

### V5 — M7 复核与扩展（GPU，~1–2 h）
- `snn/m7_matched_info.py` 扩到 10 种子；新增两臂：(a) echo+浅层 attention 读出；
  (b) 角度分箱加密的 echo（验证「丢角度」假设——若角度加密后 echo 追平 coord，则 C12 机理成立）。
- 量化扫描补 2/3 bit，确认拐点。
- 输出 `outputs_m7/verify/results.json`（含每种子明细）。
- 验收：C12/C13 在 10 种子下仍成立（均值差 >3σ）；角度加密实验给出明确机理证据。

### V6 — KITTI 全量复核（GPU，~1 h）
- `snn/road_kitti_experiment.py` 全量预算跑 3 个种子（train 21,558/test 7,188 固定划分）。
- 修复 `results.json` 键名编码（统一 UTF-8 英文键）。
- 输出每类准确率 + 混淆矩阵 + 扫描链增益分布。
- 验收：road_crossing 均值 0.92±0.02 内；给出 C14 的均值±std 版本。

### V7 — 训练预算扫描（GPU，~2–3 h，可多卡并行）
- KITTI road_crossing：预算 {1200, 3000, 6000, 12000, 21558} × 3 种子，
  画「单次 vs 扫描链」两条曲线，验证 C15（增益随预算单调收窄）。
- 输出 `results/verify/v7_budget_sweep/`。
- 验收：增益曲线单调性成立或给出反例； proposal 措辞按结果调整。

### V8 — 合成↔真实一致性（GPU，~1 h）
- 重跑 `road_vehicles.py` / `road_car_person.py`（与 KITTI 相同的 4 类合并口径），
  对比合成与 KITTI 在同预算下的差距，量化「生成器标定质量」。
- 验收：给出可写进论文的一句话（差距 <X% 或不宜声称一致）。

### V9 — 文献常量核查（无计算，联网或离线文献）
- 核查并引用：TFLN 传播损耗（目标 0.03–0.05 dB/mm 区间）、SiN 超低损耗（0.1–1 dB/m）、
  Si（~1 dB/cm）、LN dn/dT（4–6×10⁻⁵/K）、TFLN n_g@1550。
- 输出 `results/verify/v9_literature.md`：常量 → 文献 → 与我们取值的一致性 → 若不一致对 C1/C6 的影响。

### V10 — 文书数字一致性（CPU，<30 min；需 Concept Note 第二版 docx）
- 用 python-docx 抽取 docx 中所有数字（ps/nm、ps/dB、m、%、accuracy），
  与第 1 节登记表逐条比对，输出 diff 表。
- 验收：文书中每个数字都能指到仓库文件；不一致处列修正建议。

---

## 4. GPU 主机 Runbook

```bash
git clone git@github.com:Zengyi-Xu/tfln-dispersion-lab.git
git clone git@github.com:Zengyi-Xu/LiDarSim.git lidar-pointnet   # 注意目录名
cd tfln-dispersion-lab && git checkout -b verify/2026-09-25
# 环境：python>=3.11, numpy, matplotlib, torch(cuda), scipy
# lidar-pointnet/data 不在 git：road_objects.npz(82MB) 需从旧机拷贝或临时 release 下载
mkdir -p results/verify
```

执行顺序建议：V2 → V1 → V3 → V4（CPU 半天内全部完成），然后 V6 → V5 → V7 → V8（GPU），最后 V9/V10 文书。
完成后：`git add results/verify && git commit && git push origin verify/2026-09-25`，并回填 TASK_LOG。

## 5. 需要本机 Lumerical 的任务（GPU 主机跳过）

- L1：w1470/w1520 用更细 mesh + 更宽波长采样重跑 FDTD，排除数值假象（各 ~15 min）。
- L2：啁啾光栅 dn=0.020 基准的网格收敛性（~2 h）。
- L3：C1 真实信号链（用实测 τ_r(λ) 重建反射谱替换高斯 spike）——Stage 3 预备。

## 6. 报告模板（每个任务一份 `report.md`）

```
# Vx 报告
- 结论原文：...
- 复核结果：支持 / 部分支持 / 不支持
- 关键数字：旧值 → 新值（脚本 + 文件路径）
- 建议措辞：...
- 遗留问题：...
```
