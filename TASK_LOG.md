# 任务日志 / 会话交接

> 供新会话快速对接。最近更新：2026-09-26（防幻觉核查全部完成，含 L1–L3，见第六节）
> 主线任务：KGFP Call 2027 申请（Concept Note）+ 支撑仿真（A 组容差 + M7 分类）

## 一、申请状态（Concept Note 第二版已完成）

- 第二版位置：`D:\BaiduSyncdisk\SyncWorkplace\Individual\Text\20260703 KAUST 申请\Global Fellowship\第二版\kgfp_call2027_concept_note_第二版.docx`
- 已修正：色散规格改带宽绑定（~1 ns 摆幅/10–100 GHz/IL<3dB）、亚米窗口定位、FMCW/Ghelfi/RC 差异化、10 条参考文献、风险句、Cheng Wang 合作流片 + 预算口径。摘要 174 词，各节字数合规。
- **Stage 1 截止 2026-10-01**。待办：CV 更新学位状态（用户自改）、两封推荐信签字转 PDF、网申表单、转 PDF（Times New Roman 11，正文 ≤3 页）。

## 二、仿真任务状态

### A 组：TFLN 光栅容差分析（支撑 Objective 1 "design rules"）

**已完成：A3–A6（TMM，纯 Python）**
- 脚本：`simulations/02_tolerance_scan.py`；结果：`results/tolerance_scan.npz` / `.png`
- 关键结论：
  - ~~摆幅随 L 严格线性（Δτ=2n_gL/c，1–20 mm 偏差 ~2%）~~ **【V1 核查修正】** 摆幅随 L 线性：L≥5 mm 偏差 ≤3%（全域 R>0.5 窗口 ≤1%）；1 mm 短器件偏差 −8%~−15%（窗口效应），需切趾补偿后使用
  - D 由啁啾率决定（C=12 nm/mm → D≈1.22 ps/nm）【V1 复现一致】
  - FDTD 交叉校验：TMM D=0.046 vs FDTD 0.051 ps/nm（10%）
  - 余弦切趾：ripple 2.85→0.09 ps（进 M1 的 0.1 ps 容限），摆幅保留 1/3 → **设计规则：0.1 ps 容限 ↔ 3× 长度**（**【V1 注】** 1 mm 短器件不适用线性外推，见 C2 修正）
  - 随机相位误差（σ_λB≤0.1nm）与温漂（0.03 ps/K，梯度 1K/mm）影响可忽略；ripple 主因是端面法珀效应
  - 未覆盖：慢变相关误差（电子束剂量漂移类），后续可补

**已完成：A1/A2 均匀光栅部分（FDTD，7 个运行，稳健重提取）**
- 脚本：`lumerical/run_tolerance_fdtd.py`（复用 `run_scan_2d.py`，断点续跑）；数据 `lumerical/results/w*_raw.npz`、`dnf*_raw.npz`、`dn010/dn040_raw.npz`
- ⚠️ 带隙提取必须用"最长 T<0.5 连续段"法；脚本里的 `band_center` 交叉法在个别点误判（w1470 曾误报 κ=444，重提取为 594/cm）
  - **【V2 核查修正 2026-09-25】** 重提取脚本已入库 `verify/v2_reextract_a1a2.py`；平底带隙下谷底 argmin 有 ±1.5nm 伪差，λ_B 须用**带边中点法**：
  - w1470 κ 重提取值 **607/cm**（非 594；五条 w 谱 κ=606–608/cm，对条宽不敏感）；证据 `results/verify/v2/`
- **A1 条宽标定**（dn=0.02，w=1470–1530 nm）：~~dλ_B/dw = **46 nm/µm（R²=1.000）**~~ **【V2 核查修正】dλ_B/dw = 40.65±0.53 nm/µm（R²=0.999，midgap 法；阈值 0.1–0.9 扫描 39.9–40.9）**。±10 nm 条宽误差 → ±0.41 nm λ_B 偏移（非 ±0.46）
- **A2 dn 标定**（w=1500 nm，dn=0.01–0.04）：~~κ = 340/520/569/619/1238 /cm~~ **【V2 修正】κ = 353/556/607/658/1246 /cm**（n_g=2.105，midgap 法），κ∝dn 线性度 +8%（实测 +8.4%）；λ_B 对 dn ±10% 仅漂 0.03 nm（midgap 实测 0.022nm；argmin 法假漂移 1.8nm）
- **A2b 啁啾 dn ±10%（FDTD 长任务，已完成）**：250 µm 啁啾光栅，R>0.9 平台法提取
  - dn=0.018 / 0.020 / 0.022：D = 0.052 / 0.051 / 0.051 ps/nm（**D 对 dn ±10% 不敏感**）
  - ripple_pp = 1.26 / 1.22 / 1.51 ps（+10% dn 时 ripple 增 ~24%，-10% 几乎不变）
  - ⚠️ 提取窗口敏感：R>0.5 全域拟合会把带边慢光曲率混进来（曾误报 D=0.031），必须用 R>0.9 平台 + 最长连续段

### M7：信息量匹配分类实验（已完成 2026-09-24，本机 CPU 7.7 min）

- 脚本：`lidar-pointnet/snn/m7_matched_info.py`；结果：`lidar-pointnet/outputs_m7/results.json`；结论已回填 `lidar-pointnet/snn/README.md` M7 节
- 关键数字：E1 echo+ridge 0.313 / E2 echo+MLP 0.412 / E2b 模拟速率 0.419 / E3 coord+MLP 0.526 / E4 raw+MLP 0.663 / E5b raw+LR 0.610
- **结论：瓶颈在 echo 编码格式本身（径向直方图丢角度），不在蓄水池或二值化**；池权重 4–8 bit 量化不降性能（硬件卖点成立）
- 90% headline 不用 ModelNet40 数字，用道路目标扫描链结果（road car/person 0.892，road vehicles 0.919/0.963）
  - **【V8 核查修正 2026-09-25】** 删去「合成与真实惊人一致 → 生成器被背书」类表述：同预算同口径下合成 0.979/1.000 vs KITTI 0.87/0.91，**差 8–21 pt，一致性是口径不对齐的巧合**；绝对精度只引 KITTI（3 种子），合成仅用于协议对比（增益方向一致 +2.1 vs +5.1 pt）

### 真实道路数据

- RadarScenes.zip 截断损坏 + Zenodo 封本机 IP（403），待换网络重下（zenodo.org/records/4559821）
- **KITTI 已下载并跑通全流程**（`data/kitti/` + `data/road_objects.npz`，28,746 对象）：
  - 分类实验 `snn/road_kitti_experiment.py`（train=1200/test=27,546，4 类合并 car/truck/pedestrian/cyclist）：
  - road_crossing：单次 0.657 → 扫描链 **0.766**（+0.11）；uav_cap：0.419 → 0.631（+0.21）
  - **扫描链增益在真实数据上成立**（架构故事的核心证据）；绝对值低于合成（0.766 vs 0.89-0.96）~~主要是训练预算仅 1200 + 真实遮挡 + 类不平衡~~ **【V8 核查修正】** 同预算（1200）对拍合成仍 0.979/1.000 → 差距主因是**真实数据本身更难**（遮挡、类不平衡、噪声），非预算；预算只解释 0.766→0.912 的上升段（V7）
  - uav_cap 与 KITTI 车端采集几何不匹配，不作为主要场景
- **全量预算已完成（3060 机器，2026-09-25，LiDarSim `3cc5b6f`）**：train 21,558 / test 7,188
  - ~~road_crossing：单次 0.872 → 扫描链 0.923（+0.051）；uav_cap：0.758 → 0.857（+0.099）~~
  - **【V6 核查升级：3 种子固定划分】** road_crossing：**0.870±0.003 → 0.912±0.009（+0.042）**；uav_cap：**0.755±0.006 → 0.856±0.003（+0.102）**（与申报值差 ≤0.011，均支持）
  - **【V7 预算扫描新增】** 5 档预算 × 3 种子 × 2 场景：两臂精度随预算**严格单调上升**（1200→21558：road +0.21/+0.15，uav +0.30/+0.25）；增益收窄 road 严格单调（+0.103→+0.042），uav 趋势收窄（最低预算档单次臂接近随机、增益偏低为例外）
  - 验收：>0.85 达标（0.923；复核 0.912 在任务书 0.92±0.02 线内偏低沿）；增益收窄至 +0.05~0.10（小预算时 +0.11~0.21）✓ V7 实证
  - 解读：训练预算是绝对性能的主因（0.766→0.923；V7 全程单调实证）；扫描链价值集中在数据/SNR 受限场景（小预算下增益更大：uav 1200 档 +0.15~0.20 vs 全量 +0.10）
  - 对方已把 `isal_range_profile.py` 的 D:\ 硬编码改为仓库相对路径，本机 pull 后验证通过
  - 经验：上一轮 12h 运行是笔记本睡眠挂起的墙钟假象，真实计算量小得多（全量 GPU ~10–20 min）

## 三、今晚待办（新会话按此对接）

1. ~~重启啁啾长任务（A2b）~~ **已完成**，结果见第二节
2. **M7 实验**（GPU 机器或本机外接 GPU）：按计划文件执行；注意 `lidar-pointnet/data/`（1.1G）和 `checkpoints/`（413M）不在 git 里，需重下或拷贝
3. 两仓库迁移：旧电脑 `git add -A && git commit && git push`（两仓库均有未提交内容，含本日志与新脚本 `run_tolerance_fdtd.py`、`simulations/02_tolerance_scan.py`），新电脑 clone
4. 把 A1–A6 全部结论写进 lab-note.ipynb（器件设计规则一节），作为 Objective 1 的支撑

## 四、关键环境信息

- Lumerical：装在 E 盘（`E:/Program Files/ANSYS Inc/v252/Lumerical/`），本机默认 python 无 lumapi，需用自带 python 3.13.1 或脚本内 `sys.path.append`
- FDTD 并行：脚本内设 6 进程（12 进程在笔记本上不稳定）
- 均匀光栅（77.5 µm）每任务 10–20 min；250 µm 啁啾为长任务（1.5–3 h）
- 绘图约定：画布拉格光栅结构示意图时，相邻高低折射率段必须用不同颜色区分（否则看起来像一根完整直波导）
- 新会话涉及 Concept Note 内容时，先读第二版 docx 和本日志，不要重读第一版

## 五、Obsidian 知识卡片生成（2026-09-25 追加）

在另一台机器上生成任务-知识图谱卡片库（43 卡 + MOC，Obsidian 图谱视图可看致密网状结构）：
```
git clone git@github.com:Zengyi-Xu/tfln-dispersion-lab.git
cd tfln-dispersion-lab
python kg_obsidian_cards.py --vault <Obsidian vault 路径>
# 默认写入 <vault>/4-plan/KGFP任务图谱/
```
Obsidian 图谱视图过滤 `path:"4-plan/KGFP任务图谱"` 或 tag #kgfp-task。
图数据：`results/task_kg.json`（43 节点 48 边）；脚本：`kg_obsidian_cards.py`、`task_knowledge_graph.py`。

## 六、防幻觉核查任务（2026-09-25 追加）

已生成 `VERIFICATION_PLAN.md`：17 条关键结论登记表 + 10 个验证任务（V1–V10）。
**已确认疑点**：C2「1–20mm 偏差~2%」与 npz 不符（1mm −14.9%）；C7/C8（46 nm/µm、W1470 κ=594/cm）证据未入库，
仓库内 npz 仍是旧提取值（21.9 nm/µm、444/cm）——GPU 主机优先执行 V2 重提取。
分支：`verify/2026-09-25`，结果写 `results/verify/`。

**【核查任务全部完成 2026-09-25，本机 CPU；17/17 条结论已判定】**
- 总结：`results/verify/SUMMARY.md`（17 条逐条结论 + 11 条必改表述）；跨机对照：`results/verify/CROSSCHECK.md`
- 判定：14 条支持/部分支持；3 条不支持——C2（1mm 偏差 −8%~−15%）、C7 原值（→40.65 nm/µm）、C16（合成≠真实，差 8–21pt）
- V1–V4/V9/V10：修正 C2、C7、C8、lab-note κ 表、ripple 口径、C1 α 口径、Si 行 n_g；Concept Note 唯一需改 = Yu 文献标题（→ "Integrated femtosecond pulse generator on thin-film lithium niobate," Nature 612, 252–258 (2022)）
- V5–V8 原判 blocked（无 GPU），实际全部 CPU 跑通：V5 5.5 min、V8 3.5 min、V6 ~2.5 min/种子、V7 54 min
- 新风险点：chirp npz 物理斜坡在 `tau_r` 字段（tau/tau_g 是平台平坦分量，拿错即得 D≈0）
- 复现脚本：`verify/v2_reextract_a1a2.py`（必须入库，已提交）、`verify/v1_recheck.py`、`verify/v3_chirp_robust.py`
- blocked：V5–V8（无 GPU + LiDarSim 克隆网络中断仅 41M/300M+，需 U 盘拷贝或换网络 + road_objects.npz 82MB）；V10-Concept Note 段（第二版 docx 在原机 D 盘）；L1–L3（无 Lumerical）

**【V6–V8 已执行完毕 2026-09-25 下午，本机 RTX 3060】**- 环境：torch 2.11.0+cu126（anaconda3），`KMP_DUPLICATE_LIB_OK=TRUE` 绕 OpenMP 冲突；LiDarSim 仓库经 ghfast 代理克隆（`workspace/lidar-pointnet`，HEAD 3cc5b6f，data/road_objects.npz 28,746 对象完好）
- V6（C14 支持）：KITTI 全量 3 种子 road **0.871±0.004 / 0.924±0.001**、uav 0.754±0.003 / 0.860±0.003；seed0 与申报值逐位一致（原跑=seed 0）。键名乱码实因 GBK 环境误读 UTF-8 文件，`fix_kitti_keys.py` 已产出英文键版
- V7（C15 支持）：预算扫描 1200→21558 五档，road 增益 +0.124→+0.053 严格单调收窄，中间点补齐；旧小预算 0.657/0.766 是单种子，3 种子均值 0.630/0.754
- V8（C16 不支持）：4 类同口径对齐后合成 scan 1.000 / 0.9994 vs KITTI 0.924 / 0.860，差 7.6/13.9 pp——合成近饱和，生成器不复现真实难度；旧「7 类合成 vs 4 类 KITTI」对比系口径错位。措辞替换见 SUMMARY §必须修改的表述 9
- 新脚本（在 `lidar-pointnet/snn/`，未推送远端，待用户决定）：`road_kitti_verify.py`、`road_vehicles_verify.py`、`fix_kitti_keys.py`

**【双机合并 2026-09-25 晚：本机提交 6a47cff 与原机提交 9b4fd28 已合并】**
- 原机并行完成了 V5（C12 支持 10 种子 ~7σ、角度加密 echo 0.721 超 raw 0.680 →「丢角度」机理决定性成立；C13 支持且更强：2bit 无损）、V6-road（CPU 3 种子 0.8696±0.0033 / 0.9119±0.0092）、V8（CPU，C16 同判不支持）、V10-Concept Note（数字全一致，唯一改动 = Yu 文献标题）
- 跨机对照结论：C14 双机独立支持（扫描链 0.924 vs 0.912，差 0.012 在容差内）；C16 双机一致不支持；CPU 任务（V1–V4）两机数值逐项一致
- 本机不再需要 ModelNet parquet（V5 已由原机销号）
- blocked 仅剩：L1–L3（无 Lumerical，回旧机执行）

**【二次合并 2026-09-25 晚：原机 851bd7b（V6 uav + V7 全档补齐）已并入】**
- 原机补齐 V6 uav_cap（3 种子 0.7547±0.0063 / 0.8560±0.0026，与本机 GPU 0.754±0.003 / 0.860±0.003 逐位一致）与 V7 五档扫描（CPU 54.4 min，30 组一次跑通）
- 双机同档对照（1200/2802/4706/7706/21558 × 3 种子 × 2 场景）：两臂精度逐档差 ≤0.03（最低档为种子方差）；road 增益严格单调收窄双机确认（本机 +0.124→+0.053，原机 +0.103→+0.042）；uav 最低档非单调例外双机确认（单次臂近随机所致）
- 申报锚点 1200→0.657/0.766、21558→0.872/0.923 双机均复现（差 ≤0.004）
- **17 条结论全部销号**：14 支持/部分支持，3 不支持（C2、C7 原值、C16）；唯一剩余 blocked = L1–L3（Lumerical）
- 复现脚本：`verify/v1_recheck.py`、`verify/v2_reextract_a1a2.py`、`verify/v3_chirp_robust.py`（本机）；V5–V8 脚本在 `lidar-pointnet/snn/`（`road_kitti_verify_v67.py` 支持 `--v6-only/--v7-only/--scenario=` 断点续跑；另有本机 `road_kitti_verify.py`、`road_vehicles_verify.py`、`fix_kitti_keys.py` 未推送远端，待用户决定）
- ~~仍 blocked：L1–L3（本机无 Lumerical，需原机 E 盘 v252）~~

**【L1–L3 已执行完毕 2026-09-25/26，原机 Lumerical v252】**
- L1（w1470/w1520 细网格 dx=5nm + 宽窗 1500–1640nm/281pt 重跑，62 min）：n_g 收敛（2.10365 vs 2.10457）；dλB/dw=40.79 nm/µm（阈值扫描 40.76–40.90）落在 40.65±0.53 内 ✓；κ=607.5/607.0/cm 落在 606–608 ✓ → C7/C8 复核值排除数值假象。λB 绝对值 −0.25nm 共模偏移（dx=10nm staircasing 系统误差），不影响任何已入库结论
- L2（chirp dn=0.020 仅加密网格 dx=5nm，75 min）：D@R>0.9 = 0.0513 vs 0.0512（+0.15%，验收 ±5% 内）✓；阈值色散 ±0.0022 与基准一致；「必须 R>0.9 平台」规则二次确认（低阈值 D 低估在细网格下同样复现）
- L3（C1 真实信号链，CPU）：实测 tau_r 重建 H(ω) 得真实压缩脉冲（FWHM 0.146ps 含旁瓣）替换高斯 spike，M1 链四项指标不变（0.267/1.000/1.000/0.389 vs 0.267/1.000/1.000/0.400）；FoM 真实链口径 389（器件级）/384 ps/dB（3dB 预算应用级）= −8~−10%，主因 R>0.9 平台截断 η=0.915 → 建议措辞注明「真实信号链有效 FoM ≈385–390 ps/dB，3dB 预算摆幅 1.17ns、窗口 0.18m」
- 脚本：`verify/l1_fdtd_rerun.py`、`verify/l1_analyze.py`、`verify/l2_chirp_mesh.py`、`verify/l2_analyze.py`、`verify/l3_real_chain.py`；证据 `results/verify/l1`–`l3/`（json+png+report.md，.fsp 入库）
- 排障固化：fftshift 后的非单调时间轴喂 np.interp 会静默得全零（L3 脚本注释）
- **至此核查任务全清：17/17 结论 + L1–L3 全部完成，无剩余 blocked**
