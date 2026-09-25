# -*- coding: utf-8 -*-
"""生成 Obsidian 知识卡片库：KGFP 任务-知识图谱（43 卡 + MOC 索引）

用法（另一台机器上）：
  git clone git@github.com:Zengyi-Xu/tfln-dispersion-lab.git
  cd tfln-dispersion-lab
  python kg_obsidian_cards.py --vault <你的Obsidian vault路径>
  # 默认写入 <vault>/4-plan/KGFP任务图谱/，可用 --subdir 改

然后在 Obsidian 里打开该 vault，图谱视图（Graph View）即可看到致密网状结构；
可用搜索 path:"4-plan/KGFP任务图谱" 过滤局部图谱。
"""
import argparse
import json
import os

CREATED = "2026-09-25"

# (id, 标题, layer, status, 正文)
CARDS = [
    # ---- 申请交付 ----
    ("cn_v1", "Concept Note 第一版", "申请交付", "done",
     "初版 Concept Note（2026-09 上旬）。**已被第二版取代**：旧指标 100–1000 ps/nm 被自己的 M3b 延迟预算证伪。"
     "\n\n出处：`Global Fellowship/第一版/`"),
    ("cn_v2", "Concept Note 第二版", "申请交付", "done",
     "修订要点：① 色散规格改带宽绑定（~1 ns 摆幅 / 10–100 GHz / IL<3dB / cm 级）；② 亚米窗口定位；"
     "③ FMCW/Ghelfi/光子 RC 差异化 + 10 条参考文献；④ 风险句（SiN 异质备选）；⑤ Cheng Wang 合作流片 + 预算口径。"
     "摘要 174 词，各节字数合规。\n\n出处：`Global Fellowship/第二版/kgfp_call2027_concept_note_第二版.docx`"),
    ("rec", "推荐信素材", "申请交付", "done",
     "项目简述标准版（3 句英文）+ 一句话版 + 两位推荐人侧重 + 措辞红线 + 指南自查清单。"
     "预备数据口径：KITTI 0.923、增益谱系、压缩比 22 偏差 <10%。"
     "\n\n出处：`Global Fellowship/第二版/推荐信素材_项目简述.docx`"),
    ("sign", "推荐信签字转 PDF", "申请交付", "todo",
     "两封推荐信（Khaled Salama / Nan Chi）目前为 docx 草稿，需签字并转 PDF，Stage 1 随 Concept Note 一起上传。"),
    ("cv", "CV 学位状态更新", "申请交付", "todo",
     "CV v5 仍写 \"2021/9-now Graduate student\"，用户已 PhD 毕业，需更新为已获学位（含授予日期），否则资格审查不一致。"),
    ("form", "网申表单", "申请交付", "todo",
     "KAUST KGFP 在线申请表 + 附件上传。Stage 1 窗口 2026-09-01 ~ 10-01。"),
    ("stage1", "Stage 1 提交（截止 2026-10-01）", "申请交付", "todo",
     "提交物：Concept Note（≤3 页 PDF）+ CV（≤4 页）+ 两封签字推荐信 + 网申表单 + Host PI（已确定 Yating Wan，单 PI 合规）。"),
    ("stage3", "Stage 3 Full Proposal（2027-01-15）", "申请交付", "todo",
     "仅当 Wan 在 Stage 2 确认 host 意向后被邀请。需要：详细时间线、详细预算、C2 端到端联合仿真结果。"),
    # ---- 器件仿真 ----
    ("m1", "M1 光子链路（时标分离）", "器件仿真", "done",
     "啁啾光栅压缩 ps 啁啾（压缩比 22，D 与几何预言偏差 8%）；等能量等质心严格任务上："
     "直接慢积分 0.27（随机）vs 非线性蓄水池+漏电积分 1.00，线性消融 0.40 —— 非线性蓄水池是慢读出的必要环节。"
     "\n\n出处：`simulation_report_2026-09-20.docx` §2"),
    ("m3b", "M3b 延迟预算", "器件仿真", "done",
     "延迟/损耗品质因数：TFLN 424 ps/dB（0.033 dB/mm），SiN 46700（100×），Si 140。"
     "3 dB 预算下 TFLN 摆幅 1.27 ns → 测距窗口 ~0.19 m。**这条直接改写了 Concept Note 的指标口径**。"
     "\n\n出处：`lumerical/m3b_delay_budget.py`"),
    ("a1", "A1 条宽标定", "器件仿真", "done",
     "dλ_B/dw = 46 nm/µm（R²=1.000），κ ≈ 570–600/cm。条宽 ±10 nm 工艺误差 → ±0.46 nm λ_B 偏移，"
     "是啁啾匹配的主要工艺窗口。\n\n出处：`lumerical/results/w14*_raw.npz`"),
    ("a2", "A2 κ(dn) 标定", "器件仿真", "done",
     "κ = 340/520/569/619/1238 /cm（dn=0.01/0.018/0.02/0.022/0.04），比 κ∝dn 快 ~8%；"
     "λ_B 对 dn ±10% 仅漂 0.03 nm —— dn 容差只影响带隙不影响中心波长。"),
    ("a2b", "A2b 啁啾 dn ±10%", "器件仿真", "done",
     "250 µm 啁啾光栅 FDTD 长任务：D = 0.051–0.052 ps/nm 对 dn ±10% 不敏感；ripple 最坏 +24%。"
     "⚠️ 提取必须用 R>0.9 平台 + 最长连续段（R>0.5 全域会混入带边慢光曲率）。"),
    ("a3", "A3 相位误差", "器件仿真", "done",
     "λ_B 白噪声 σ≤0.1 nm 下 ripple 几乎不动（2.85→2.93 ps），且不随 L 增长 —— "
     "随机相位误差不是 cm 级主威胁，确定性端面效应才是（可切趾解决）。未覆盖慢变相关误差 → [[kg-corr_err]]。"),
    ("a4", "A4 温漂", "器件仿真", "done",
     "dn/dT=4e-5/K：均匀温漂仅 0.03 ps/K（占摆幅 0.1%/K），1 K/mm 梯度无畸变。"
     "热问题一阶可忽略 —— Background 里列的 thermo-optic drift challenge 实际不构成风险。"),
    ("a5", "A5 摆幅-长度线性", "器件仿真", "done",
     "Δτ=2n_gL/c，1–20 mm 偏差 ~2%；D 由啁啾率决定与 L 无关（C=12 nm/mm → D≈1.22 ps/nm）。"
     "厘米级外推物理图像成立。TMM 交叉校验 FDTD：0.046 vs 0.051 ps/nm（10%）。"),
    ("a6", "A6 切趾权衡", "器件仿真", "done",
     "余弦切趾把 ripple 2.85→**0.09 ps**（进 M1 的 0.1 ps 抖动容限），代价摆幅保留 1/3。"
     "**设计规则：满足 0.1 ps 容限 ↔ 3× 长度**。"),
    ("tmm_fdtd", "TMM vs FDTD 交叉校验", "器件仿真", "done",
     "lab-note §21 的 TMM 模型与 FDTD 在相同参数下偏差 10%（0.046 vs 0.051 ps/nm），"
     "互为方法学背书：TMM 负责长器件外推（FDTD 打不到 cm 级），FDTD 负责短器件标定。"),
    ("c1", "C1 真实信号链", "器件仿真", "todo",
     "用实测光栅 τ_r(λ) 重建反射谱 → 逆 FFT 得真实压缩脉冲，替换 M1 的高斯 spike 重跑。"
     "消除\"理想化输入\"攻击线。估计半天 CPU。Stage 3 优先级 1。"),
    ("c2", "C2 端到端联合仿真", "器件仿真", "todo",
     "光栅压缩 → QD spike → 可调蓄水池 → 慢读出，HATF 注入噪声/量化/漂移。"
     "postdoc 计划 Objective 3 的直接支撑。等 Stage 2 结果后启动。"),
    ("corr_err", "慢变相关误差模型", "器件仿真", "todo",
     "A3 的白噪声模型不覆盖电子束剂量漂移类慢变相关误差（等效啁啾率误差）。补 1–2 天。"),
    # ---- 算法实验 ----
    ("lsm", "LSM 低 SNR 检测", "算法实验", "done",
     "相参脉冲串检测（Pfa=1e-3）：-15 dB 时 LSM-iq Pd=0.39 vs MTD-CFAR 0.01 —— "
     "蓄水池把\"学到的相干积累+能量读出\"融合，低 SNR 反超经典。高 SNR 有平台期（随机池表达上限）。"
     "\n\n出处：`lidar-pointnet/snn/README.md`"),
    ("m3a", "M3a delay learning", "算法实验", "done",
     "连续编码 + 可训练延迟线端到端：固定随机延迟 0.838，+延迟学习 0.841，+输入权重学习 0.888。"
     "结论：可调延迟的价值依赖延迟敏感架构；交叉熵读出（0.84）远强于岭回归（0.40）—— M2 天花板大半在读出器。"),
    ("m7", "M7 信息量匹配对比", "算法实验", "done",
     "编码×读出分离（3 种子）：echo+ridge 0.313 / echo+MLP 0.412 / 模拟速率 0.419 / coord+MLP 0.526 / "
     "raw+MLP 0.663 / raw+LR 0.610。**瓶颈在 echo 编码格式本身（径向直方图丢角度），不在蓄水池或二值化**。"
     "池 4–8bit 量化不降性能。\n\n出处：`lidar-pointnet/outputs_m7/results.json`"),
    ("synth", "合成道路目标", "算法实验", "done",
     "road car/person 二类：扫描链 0.892/0.866；road vehicles 参数化 7 类：0.919/0.963（road/uav 预设）。"
     "合成数字与真实 KITTI 0.923 惊人一致 —— 参数化生成器的标定质量被真实数据背书。"),
    ("kitti_s", "KITTI 小预算", "算法实验", "done",
     "train=1200/test=27,546（28,746 对象，4 类合并）：road 0.657→0.766（+0.11），uav 0.419→0.631（+0.21）。"
     "扫描链增益首次在真实数据上复现。注：当次 12h 运行是笔记本睡眠挂起的墙钟假象 → [[kg-k_sleep]]。"),
    ("kitti_f", "KITTI 全量预算 0.923", "算法实验", "done",
     "train 21,558 / test 7,188（每类 75%）：road 单次 0.872 → 扫描链 **0.923**（+0.05），uav 0.758→0.857（+0.10）。"
     "**proposal 的真实数据 headline**。3060 GPU 上 ~15 分钟跑完（LiDarSim `3cc5b6f`）。"),
    ("gpu_port", "GPU 化移植", "算法实验", "done",
     "make_dataset_fast（torch einsum+scatter_add，chunk 2048）+ 读出 DEVICE 自动检测。"
     "与原 numpy 版同种子流，corr=0.999991 校验通过（`validate_profiles_fast.py`）。"),
    # ---- 数据 ----
    ("kitti_d", "KITTI 下载与提取", "数据", "done",
     "calib/label_2/velodyne(28.7GB) 经 S3 直链 + 并行分段下载（6 MB/s）完成；"
     "提取 28,746 对象（7481 帧，3 分钟）→ `data/road_objects.npz`（82MB，已临时入库 LiDarSim）。"),
    ("rs", "RadarScenes（受阻）", "数据", "blocked",
     "9-21 下载的 534MB zip 截断损坏（无中央目录）；Zenodo 封本机 IP（403）。"
     "换网络从 zenodo.org/records/4559821 重下。用途：杂波统计标定 + 雷达侧基准（优先级低于 KITTI）。"),
    ("mn40", "ModelNet40", "数据", "done",
     "M2/M3a/M7 的基准数据集（前 10 类，256 点，parquet 在 `lidar-pointnet/data/`，可用 download_data.py 重下）。"),
    # ---- 基础设施 ----
    ("git", "两仓库 Git 迁移", "基础设施", "done",
     "tfln-dispersion-lab + LiDarSim 均已 push。注意 data/checkpoints 不入 git；"
     "road_objects.npz（82MB）已临时入库 LiDarSim 供 3060 pull。"),
    ("gpu3060", "3060 平台", "基础设施", "done",
     "11800H + RTX 3060 备用机：CUDA torch 已通，LiDarSim clone 完成，KITTI 全量实验在此跑成（0.923）。"),
    ("tasklog", "TASK_LOG 交接机制", "基础设施", "done",
     "`tfln-dispersion-lab/TASK_LOG.md`：申请状态 + 仿真状态 + 待办 + 环境信息，"
     "跨会话/跨机器的单点事实源。新 session 先读它。"),
    ("runbook", "RUNBOOK 与任务书", "基础设施", "done",
     "`LiDarSim/RUNBOOK_3060.md`（仓库内）+ `任务-3060-KITTI全量实验.md`（自包含任务书）。"
     "模式验证成功：新 session 读文件即可独立执行。"),
    ("pdl", "并行分段下载", "基础设施", "done",
     "28.7GB velodyne：单连接被 S3 限速 → 6 段 Range 并行 + 卡顿自动重连（<200KB/s×20s 断线），"
     "稳定 6 MB/s；拼接前逐段字节校验 + unzip -t 完整性验证。脚本 `data/kitti/parallel_dl.sh`。"),
    # ---- 知识结论 ----
    ("k_sub", "亚米窗口定位", "知识结论", "done",
     "TFLN 424 ps/dB → 3dB 预算 1.27 ns 摆幅 ↔ 0.19 m 测距窗口。亚米不是短板而是定位："
     "机器人避障、消费电子、片上传感。长距走 SiN 延迟+TFLN 调谐异质路线（风险表）。"),
    ("k_ts", "时标分离架构", "知识结论", "done",
     "快光处理（ps）+ 慢电读出（ns）：蓄水池把时序模式展开成空间模式，漏电积分保持到电路可读，"
     "电域带宽需求降 2–3 个数量级。本计划最深的架构创新点。"),
    ("k_enc", "编码格式是瓶颈", "知识结论", "done",
     "M7：echo 径向直方图丢角度结构（0.41 vs raw 0.66），模拟速率与二值脉冲无差别 —— "
     "编码架构（而非蓄水池/读出）是 SQ1 的核心科学问题。"),
    ("k_quant", "池权重量化免疫", "知识结论", "done",
     "M7 R1：4–8 bit 量化性能不降（0.41–0.42）—— MRR crossbar 6.74 bit 权重精度足够，"
     "LUT 再校准非必需。硬件可行性卖点。"),
    ("k_gain", "扫描链增益谱系", "知识结论", "done",
     "增益随条件恶化单调放大：数据充裕 +0.05（KITTI 全量）→ 数据受限 +0.11（小预算）→ "
     "低 SNR +0.3 以上（-15dB 反超 CFAR）。**产品定位：边缘受限场景，非实验室充裕条件**。"),
    ("k_rules", "器件设计规则 ×4", "知识结论", "done",
     "① 摆幅-长度线性（~2%）；② 切趾-摆幅权衡（0.1 ps 容限 ↔ 3× 长度）；"
     "③ 条宽 46 nm/µm 主窗口、dn 只影响 κ；④ 相位/温度误差一阶可忽略。"
     "已写入 lab-note.ipynb §17。"),
    ("k_sleep", "教训：12h 是睡眠假象", "知识结论", "done",
     "KITTI 首轮\"12 小时\"实为笔记本睡眠挂起的墙钟膨胀，真实计算 3–4 分钟。"
     "教训：长任务先排监控/分段计时；性能优化前先 profile 找真瓶颈（当时误判瓶颈在仿真，实际在训练）。"),
]

LAYER_ORDER = ["申请交付", "器件仿真", "算法实验", "数据", "基础设施", "知识结论"]
STATUS_ICON = {"done": "✅", "doing": "🔄", "todo": "⬜", "blocked": "🚫"}

EDGES_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "results", "task_kg.json")


def card_name(nid, title):
    return "kg-%s-%s" % (nid, title.replace(" ", "-").replace("/", "-"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, help="Obsidian vault 路径")
    ap.add_argument("--subdir", default=os.path.join("4-plan", "KGFP任务图谱"),
                    help="vault 内目标子目录")
    args = ap.parse_args()
    outdir = os.path.join(args.vault, args.subdir)
    os.makedirs(outdir, exist_ok=True)

    with open(EDGES_JSON, encoding="utf-8") as f:
        edges = json.load(f)["edges"]
    name_of = {nid: card_name(nid, t) for nid, t, _, _, _ in CARDS}

    # 出边/入边索引
    linked = {}
    for e in edges:
        linked.setdefault(e["src"], []).append((e["relation"], e["dst"]))
        linked.setdefault(e["dst"], []).append((e["relation"] + "（反向）", e["src"]))

    n_written = 0
    for nid, title, layer, status, body in CARDS:
        fn = name_of[nid]
        lines = ["---", "type: task-card", "layer: %s" % layer,
                 "status: %s" % status, "created: %s" % CREATED,
                 "tags: [kgfp-task]", "---", "",
                 "# %s %s" % (STATUS_ICON[status], title), "", body, "",
                 "## 连接"]
        for rel, other in linked.get(nid, []):
            if other in name_of:
                lines.append("- %s → [[%s]]" % (rel, name_of[other]))
        path = os.path.join(outdir, fn + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        n_written += 1

    # MOC 索引
    moc = ["---", "type: moc", "created: %s" % CREATED, "tags: [kgfp-task]",
           "---", "", "# KGFP 任务-知识图谱 MOC", "",
           "> 截至 2026-09-25。图谱视图中过滤 `path:\"%s\"` 或 tag #kgfp-task 查看本网。"
           % args.subdir.replace("\\", "/"), ""]
    for layer in LAYER_ORDER:
        moc.append("## %s" % layer)
        for nid, title, ly, status, _ in CARDS:
            if ly == layer:
                moc.append("- %s [[%s|%s]]" % (STATUS_ICON[status],
                                               name_of[nid], title))
        moc.append("")
    with open(os.path.join(outdir, "任务知识图谱-MOC.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(moc) + "\n")
    print("written %d cards + MOC -> %s" % (n_written, outdir))


if __name__ == "__main__":
    main()
