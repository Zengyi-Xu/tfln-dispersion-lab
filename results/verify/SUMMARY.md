# 防幻觉核查总结（2026-09-25，verify/2026-09-25 分支）

执行主机：**双主机并行核查**。本机 = Windows + RTX 3060（torch 2.11.0+cu126，V6 全量/V7/V8 GPU 复核）；对方 = 无 GPU 核查机（V1–V4/V9 + 独立重实现）与原机（V5/V6-road 部分/V8/V10-Concept Note，CPU）。
L1–L3 跳过（无 Lumerical）；17 条结论全部有判定（C14 双机独立支持，C16 双机一致不支持）。
所有任务报告：`results/verify/v*/report.md`；可复用脚本：`verify/v1_recheck.py`、`verify/v2_reextract_a1a2.py`、`verify/v3_chirp_robust.py`（本机），
另有对方机独立实现 `verify/v1_tolerance_recheck.py`、`verify/a1a2_reextract.py`、`verify/v3_chirp_extract.py`、`verify/v4_theory_check.py`，两机 CPU 任务数值逐项一致。

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
| C12 | 支持（10 种子，~7σ；机理决定性证实） | echo+MLP 0.412 → 0.435±0.028 vs raw+MLP 0.663 → 0.680±0.020；角度加密 echo（8扇区×36bin）**0.721±0.017 超 raw 上限** → 「丢角度」机理成立；attention 读出 0.381 更差 | `results/verify/v5/report.md`、`lidar-pointnet/outputs_m7/verify/results.json` |
| C13 | 支持（且更强） | 4–8 bit 不降 → **2–8 bit 全程无损**（2bit 0.431 / 3bit 0.428 vs 未量化 0.435，10 种子） | `results/verify/v5` |
| C14 | **支持（双机独立）** | road_crossing 0.872/0.923（单种子申报）→ 本机 GPU 3 种子 **0.871±0.004 / 0.924±0.001**；uav_cap **0.754±0.003 / 0.860±0.003**；原机 CPU 3 种子 road 0.8696±0.0033 / 0.9119±0.0092（扫描链差 0.012，在容差内）；seed0 与申报逐位一致（原跑=seed 0）；键名乱码系 GBK 环境误读 UTF-8 文件 | `results/verify/v6/report.md` + `v6_kitti_full_3seeds.json`（本机）、`lidar-pointnet/.../results_v67_verify.json`（原机） |
| C15 | **支持（本机 GPU 五档完整）** | 增益随预算单调收窄：road +0.124@1.2k → +0.119@2.8k → +0.083@4.7k → +0.074@7.7k → +0.053@21.6k（严格单调）；uav +0.196 → +0.180 → +0.186 → +0.172 → +0.106（4706 档 1σ 内回弹）；扫描链均值 0.754→0.924；旧小预算 0.657/0.766 为单种子，3 种子均值 0.630/0.754；中间预算点已补齐（原机此前缺中间点，本机销号） | `results/verify/v7/report.md` + `budget_sweep_summary.json` |
| C16 | **不支持（双机一致）** | 旧「合成 0.892/0.919 ≈ 真实 0.923」系口径错位；同口径对齐后**合成近饱和**（本机 4 类 scan 1.000/0.9994，原机 0.979/1.000）vs KITTI（本机 0.924/0.860，原机 0.87/0.91），差 7.6–13.9 pp（本机）/ 8–21 pt（原机）——生成器不复现真实难度，不可背书；仅扫描链增益方向可引用 | `results/verify/v8/report.md` + `v8_synth_4class.json`（本机）、`lidar-pointnet/.../road_synth_v8/results_v8.json`（原机） |
| C17 | 支持（原始 npz 已指认） | docx §2 数字与 `comprehensive_summary.npz` 逐位一致 | `results/verify/v10/report.md` |

## 必须修改的表述

1. **C2（TASK_LOG §二.A / lab-note §17 规则 1；Concept Note 已核验不含此句，见 v10 补充）**
   - 旧：「摆幅随 L 严格线性（Δτ=2n_gL/c，1–20 mm 偏差 ~2%）」
   - 新：「延迟摆幅随 L 线性：L≥5 mm 与几何值偏差 ≤3%（全域 R>0.5 窗口 ≤1%）；1 mm 短器件偏差 −8%~−15%，需切趾补偿后使用」
2. **C7（TASK_LOG / lab-note / 后续申请书 Objective 1；Concept Note 已核验不含此数）**
   - 旧：「dλ_B/dw = 46 nm/µm（R²=1.000）」
   - 新：「dλ_B/dw ≈ 41 nm/µm（R²=0.999，带边中点提取；阈值 0.1–0.9 稳健 39.9–40.9）」；±10nm 条宽误差 → ±0.41 nm λ_B 偏移（非 ±0.46）
3. **C8**
   - 旧：「W1470 κ=594/cm」「κ ≈ 570–600/cm」
   - 新：「κ ≈ 6.1×10²/cm（600–610，对条宽 1470–1530 nm 不敏感；n_g=2.105）」；TASK_LOG §二.A 中「w1470 曾误报 444，重提取为 594」改为「重提取为 607」
4. **lab-note §17 标定行 κ 表**：340/520/569/619/1238 → 353/556/607/658/1246（n_g=2.105，midgap）
5. **TASK_LOG §二.A 余弦切趾行**：「0.1 ps 容限 ↔ 3× 长度」保留，但注明 1mm 短器件不适用线性外推（见 C2）
6. **ripple 口径（simulation_report §2.1）**：「ripple 峰峰值 ~9%」注明为反射率口径；群延迟口径 ripple = 1.2 ps（摆幅 38%）
7. **C1 口径（m3b / Concept Note）**：α=0.033 dB/mm 注明「保守深刻蚀值」；当代刻蚀 0.2–0.4 dB/cm 时 FoM 升至 3.5–5.3×10³ ps/dB；并修正 Si 行 n_g=2.1→4.2（Si FoM 140→280 ps/dB）
8. **Concept Note 参考文献（唯一需改处）**："Yu et al., 'Integrated chirped waveguide Bragg gratings on thin-film lithium niobate,' Nature (2022)" 标题有误 → 应为 **M. Yu et al., "Integrated femtosecond pulse generator on thin-film lithium niobate," Nature 612, 252–258 (2022)**（正文 "1.6 ps/nm in 2.5 mm" 数字属实，保留）
9. **C16（TASK_LOG §二.M7 段「90% headline」与后续 proposal）**：删去「合成与真实惊人一致→生成器被背书」类表述；绝对精度只引 KITTI（本机 0.924/0.860，原机 0.87/0.91，3 种子），合成仅用于协议对比（增益方向一致）。建议措辞：「合成数据验证链路可达饱和性能；真实数据绝对性能以 KITTI 为准，生成器当前不复现真实难度（遮挡、截断、类不平衡）」
10. **C14 表述升级**：「0.872→0.923（单次运行）」→「road_crossing 3 种子 0.871±0.004 / 0.924±0.001（本机 GPU）与 0.8696±0.0033 / 0.9119±0.0092（原机 CPU）；uav_cap 0.754±0.003 / 0.860±0.003（本机）」

## 新发现的风险点（本次核查产出）

1. **tau_r / tau 字段陷阱（最高优先）**：chirp2d.npz 与 chirpdf*_raw.npz 中，物理延迟斜坡在 `tau_r` 字段；`tau`/`tau_g` 在平台上是平的（D≈0）。任何人（包括未来的自己）拿错字段会得出「D=0」并推翻 C10/C11。建议重存 npz 时改名/注释。
2. **R>0.9 平台在 TMM 无耗模型中不存在**（R_max≈0.77，V1）——「R>0.9 平台」规则仅适用于 FDTD 数据；TMM 侧用 R>0.5 去带边窗口。
3. **m3b 三平台共用 n_g=2.1**：Si 应 ~4.2，Si 行 FoM 需修正。
4. **带隙提取方法依赖**：平底带隙（强耦合）下谷底 argmin 有 ±1.5 nm 伪差，A1/A2 的 λ_B 必须用带边中点法（V2 脚本已固化）。
5. **C14 跨机扫描链差异**：本机 GPU 0.924±0.001 vs 原机 CPU 0.912±0.0092，差 0.012（~1.3σ），在 CROSSCHECK 容差内但偏下限；引用时建议给双机区间 0.91–0.92。

## 遗留（blocked）

| 任务 | 状态 |
|---|---|
| V5（M7 10 种子+角度加密臂） | **已完成（原机 CPU 5.5 min）**，C12/C13 销号 |
| V6 road/uav（3 种子+键名修复） | **双机完成**（原机 road 部分 + 本机 GPU 全量） |
| V7（预算扫描） | **已完成（本机 GPU 五档）**，C15 销号 |
| V8（合成↔真实一致性） | **双机完成**，C16 不支持结论一致 |
| V10-Concept Note 段 | **已由原机补核**（数字全一致；唯一改动 = Yu 文献标题） |
| L1–L3 | 无 Lumerical，回旧机执行（各 15min–2h），唯一剩余 blocked |
