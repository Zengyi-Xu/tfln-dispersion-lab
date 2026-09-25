# 防幻觉核查总结（2026-09-25，verify/2026-09-25 分支）

执行主机：Windows 无 GPU 机。完成 V1/V2/V3/V4/V9/V10（部分）；V5–V8 blocked（无 GPU + lidar 仓库未就位）；L1–L3 跳过（无 Lumerical）。
所有任务报告：`results/verify/v*/report.md`；可复用脚本：`verify/v1_recheck.py`、`verify/v2_reextract_a1a2.py`、`verify/v3_chirp_robust.py`。

## 核查结果总表

| 结论# | 复核结果 | 旧值 → 新值 | 证据路径 |
|---|---|---|---|
| C1 | 支持（须带 α 口径） | 424 ps/dB（α=3.3 dB/cm 保守值）→ 同值但注明区间 414–465（n_g）/ 3500–4242（α 取 0.2–0.3 dB/cm 时） | `results/verify/v4/report.md`、`v9/report.md` |
| C2 | **不支持，须改表述** | 「1–20 mm 偏差 ~2%」→「L≥5 mm 偏差 ≤3%（全域 R>0.5 窗口 ≤1%）；1 mm 偏差 −8%~−15%」 | `results/verify/v1/report.md` + `v1_tolerance_recheck.json` |
| C3 | 支持 | D=1.22–1.30 ps/nm（复现 1.2233–1.3025） | `results/verify/v1` |
| C4 | 支持 | ripple 2.85→0.09 ps，摆幅 33.6%（复现一致） | `results/verify/v1` |
| C5 | 支持 | σ≤0.1nm → 2.924±0.018 ps；ripple 随 L 下降 | `results/verify/v1` |
| C6 | 支持 | 0.034 ps/K（dn/dT=3.95e-5/K 文献实测命中） | `results/verify/v4`、`v9` |
| C7 | **部分支持（数值须改）** | 46 nm/µm（R²=1.000）→ **40.65±0.53 nm/µm（R²=0.999，midgap 法，阈值稳健）** | `results/verify/v2/report.md` + `verify/v2_reextract_a1a2.py` |
| C8 | **部分支持（数值须改）** | w1470 κ=594/cm → **607/cm**（旧提取 444/cm 确为误判；κ 对条宽不敏感 606–608） | `results/verify/v2` |
| C9 | 支持 | κ +8%（实测 +8.4%）；λ_B 漂移 0.03nm（midgap 实测 0.022nm；argmin 法假漂移 1.8nm） | `results/verify/v2` |
| C10 | 支持（附限定） | D=0.051 不变（R>0.9: 0.0512/0.0518/0.0507）；ripple +24%（实测 +24.1%）；「必须 R>0.9」获机理实证（dn022 低阈值 D 被低估 20–40%） | `results/verify/v3/report.md` + `verify/v3_chirp_robust.py` |
| C11 | 支持 | 0.0463 vs 0.051 = −9.6% ≈ 10% | `results/verify/v3`、`v4` |
| C12 | 未执行（blocked） | — | `results/verify/v5/report.md` |
| C13 | 未执行（blocked） | — | `results/verify/v5/report.md` |
| C14 | 未执行（blocked） | —（键名乱码修复一并等待仓库就位） | `results/verify/v6/report.md` |
| C15 | 未执行（blocked） | — | `results/verify/v7/report.md` |
| C16 | 未执行（blocked） | — | `results/verify/v8/report.md` |
| C17 | 支持（原始 npz 已指认） | docx §2 数字与 `comprehensive_summary.npz` 逐位一致 | `results/verify/v10/report.md` |

## 必须修改的表述

1. **C2（Concept Note / TASK_LOG §二.A / lab-note §17 规则 1）**
   - 旧：「摆幅随 L 严格线性（Δτ=2n_gL/c，1–20 mm 偏差 ~2%）」
   - 新：「延迟摆幅随 L 线性：L≥5 mm 与几何值偏差 ≤3%（全域 R>0.5 窗口 ≤1%）；1 mm 短器件偏差 −8%~−15%，需切趾补偿后使用」
2. **C7（同上 + 申请书 Objective 1）**
   - 旧：「dλ_B/dw = 46 nm/µm（R²=1.000）」
   - 新：「dλ_B/dw ≈ 41 nm/µm（R²=0.999，带边中点提取；阈值 0.1–0.9 稳健 39.9–40.9）」；±10nm 条宽误差 → ±0.41 nm λ_B 偏移（非 ±0.46）
3. **C8**
   - 旧：「W1470 κ=594/cm」「κ ≈ 570–600/cm」
   - 新：「κ ≈ 6.1×10²/cm（600–610，对条宽 1470–1530 nm 不敏感；n_g=2.105）」；TASK_LOG §二.A 中「w1470 曾误报 444，重提取为 594」改为「重提取为 607」
4. **lab-note §17 标定行 κ 表**：340/520/569/619/1238 → 353/556/607/658/1246（n_g=2.105，midgap）
5. **TASK_LOG §二.A 余弦切趾行**：「0.1 ps 容限 ↔ 3× 长度」保留，但注明 1mm 短器件不适用线性外推（见 C2）
6. **ripple 口径（simulation_report §2.1）**：「ripple 峰峰值 ~9%」注明为反射率口径；群延迟口径 ripple = 1.2 ps（摆幅 38%）
7. **C1 口径（m3b / Concept Note）**：α=0.033 dB/mm 注明「保守深刻蚀值」；当代刻蚀 0.2–0.4 dB/cm 时 FoM 升至 3.5–5.3×10³ ps/dB；并修正 Si 行 n_g=2.1→4.2（Si FoM 140→280 ps/dB）

## 新发现的风险点（本次核查产出）

1. **tau_r / tau 字段陷阱（最高优先）**：chirp2d.npz 与 chirpdf*_raw.npz 中，物理延迟斜坡在 `tau_r` 字段；`tau`/`tau_g` 在平台上是平的（D≈0）。任何人（包括未来的自己）拿错字段会得出「D=0」并推翻 C10/C11。建议重存 npz 时改名/注释。
2. **R>0.9 平台在 TMM 无耗模型中不存在**（R_max≈0.77，V1）——「R>0.9 平台」规则仅适用于 FDTD 数据；TMM 侧用 R>0.5 去带边窗口。
3. **m3b 三平台共用 n_g=2.1**：Si 应 ~4.2，Si 行 FoM 需修正。
4. **带隙提取方法依赖**：平底带隙（强耦合）下谷底 argmin 有 ±1.5 nm 伪差，A1/A2 的 λ_B 必须用带边中点法（V2 脚本已固化）。

## 遗留（blocked）

| 任务 | 原因 | 解除条件 |
|---|---|---|
| V5（M7 10 种子+角度加密臂） | 无 GPU；仓库正文缺失 | GPU 主机 + 完整 LiDarSim 克隆 + road_objects.npz |
| V6（KITTI 3 种子+键名修复） | 同上 | 同上（全量 ~10–20 min GPU） |
| V7（预算扫描） | 同上 | 同上（2–3 h GPU） |
| V8（合成↔真实一致性） | 同上 | 同上 |
| V10-Concept Note 段 | 第二版 docx 在原机 D 盘 | 拷入工作区后可补跑（C2/C7/C8 修正措辞已备） |
| L1–L3 | 无 Lumerical | 回旧机执行（各 15min–2h） |
