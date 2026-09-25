# 任务日志 / 会话交接

> 供新会话快速对接。最近更新：2026-09-24 21:25
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
  - 摆幅随 L 严格线性（Δτ=2n_gL/c，1–20 mm 偏差 ~2%），D 由啁啾率决定（C=12 nm/mm → D≈1.22 ps/nm）
  - FDTD 交叉校验：TMM D=0.046 vs FDTD 0.051 ps/nm（10%）
  - 余弦切趾：ripple 2.85→0.09 ps（进 M1 的 0.1 ps 容限），摆幅保留 1/3 → **设计规则：0.1 ps 容限 ↔ 3× 长度**
  - 随机相位误差（σ_λB≤0.1nm）与温漂（0.03 ps/K，梯度 1K/mm）影响可忽略；ripple 主因是端面法珀效应
  - 未覆盖：慢变相关误差（电子束剂量漂移类），后续可补

**已完成：A1/A2 均匀光栅部分（FDTD，7 个运行，稳健重提取）**
- 脚本：`lumerical/run_tolerance_fdtd.py`（复用 `run_scan_2d.py`，断点续跑）；数据 `lumerical/results/w*_raw.npz`、`dnf*_raw.npz`、`dn010/dn040_raw.npz`
- ⚠️ 带隙提取必须用"最长 T<0.5 连续段"法；脚本里的 `band_center` 交叉法在个别点误判（w1470 曾误报 κ=444，重提取为 594/cm）
- **A1 条宽标定**（dn=0.02，w=1470–1530 nm）：dλ_B/dw = **46 nm/µm（R²=1.000）**，κ ≈ 570–600/cm。±10 nm 条宽误差 → ±0.46 nm λ_B 偏移，对啁啾匹配是重要工艺窗口
- **A2 dn 标定**（w=1500 nm，dn=0.01–0.04）：κ = 340/520/569/619/1238 /cm，κ∝dn 线性度 +8%；λ_B 对 dn ±10% 仅漂 0.03 nm
- **A2b 啁啾 dn ±10%（FDTD 长任务，已完成）**：250 µm 啁啾光栅，R>0.9 平台法提取
  - dn=0.018 / 0.020 / 0.022：D = 0.052 / 0.051 / 0.051 ps/nm（**D 对 dn ±10% 不敏感**）
  - ripple_pp = 1.26 / 1.22 / 1.51 ps（+10% dn 时 ripple 增 ~24%，-10% 几乎不变）
  - ⚠️ 提取窗口敏感：R>0.5 全域拟合会把带边慢光曲率混进来（曾误报 D=0.031），必须用 R>0.9 平台 + 最长连续段

### M7：信息量匹配分类实验（已完成 2026-09-24，本机 CPU 7.7 min）

- 脚本：`lidar-pointnet/snn/m7_matched_info.py`；结果：`lidar-pointnet/outputs_m7/results.json`；结论已回填 `lidar-pointnet/snn/README.md` M7 节
- 关键数字：E1 echo+ridge 0.313 / E2 echo+MLP 0.412 / E2b 模拟速率 0.419 / E3 coord+MLP 0.526 / E4 raw+MLP 0.663 / E5b raw+LR 0.610
- **结论：瓶颈在 echo 编码格式本身（径向直方图丢角度），不在蓄水池或二值化**；池权重 4–8 bit 量化不降性能（硬件卖点成立）
- 90% headline 不用 ModelNet40 数字，用道路目标扫描链结果（road car/person 0.892，road vehicles 0.919/0.963）

### 真实道路数据

- RadarScenes.zip 截断损坏 + Zenodo 封本机 IP（403），待换网络重下（zenodo.org/records/4559821）
- **KITTI 已下载并跑通全流程**（`data/kitti/` + `data/road_objects.npz`，28,746 对象）：
  - 分类实验 `snn/road_kitti_experiment.py`（train=1200/test=27,546，4 类合并 car/truck/pedestrian/cyclist）：
  - road_crossing：单次 0.657 → 扫描链 **0.766**（+0.11）；uav_cap：0.419 → 0.631（+0.21）
  - **扫描链增益在真实数据上成立**（架构故事的核心证据）；绝对值低于合成（0.766 vs 0.89-0.96）主要是训练预算仅 1200 + 真实遮挡 + 类不平衡（truck 仅 736）
  - uav_cap 与 KITTI 车端采集几何不匹配，不作为主要场景
- **全量预算已完成（3060 机器，2026-09-25，LiDarSim `3cc5b6f`）**：train 21,558 / test 7,188
  - road_crossing：单次 0.872 → 扫描链 **0.923**（+0.051）；uav_cap：0.758 → 0.857（+0.099）
  - 验收：>0.85 达标（0.923）；增益收窄至 +0.05~0.10（小预算时 +0.11~0.21）
  - 解读：训练预算是绝对性能的主因（0.766→0.923）；扫描链价值集中在数据/SNR 受限场景
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
