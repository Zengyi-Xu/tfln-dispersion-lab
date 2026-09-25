# -*- coding: utf-8 -*-
"""两棵树的共享数据（无 matplotlib 依赖，可被 Mermaid/绘图脚本共用）"""

# (id, parent, label, type, detail)
PROJECT_TREE = [
    ("workspace", None, "KGFP 工作空间", "root", "tfln-dispersion-lab + lidar-pointnet"),
    # tfln-dispersion-lab
    ("tfln", "workspace", "tfln-dispersion-lab", "repo", "TFLN 色散/器件/光子链路"),
    ("tfln_docs", "tfln", "申请文书", "category", "Concept Note / 报告 / 日志"),
    ("tfln_readme", "tfln_docs", "README.md", "doc", "项目总览"),
    ("tfln_tasklog", "tfln_docs", "TASK_LOG.md", "doc", "会话交接事实源"),
    ("tfln_report", "tfln_docs", "simulation_report_2026-09-20.docx", "doc", "器件仿真报告"),
    ("tfln_labnote", "tfln_docs", "lab-note.ipynb", "notebook", "实验记录主笔记"),
    ("tfln_ms", "tfln_docs", "milestone-M1~M4.ipynb", "notebook", "4 个里程碑 notebook"),

    ("tfln_dev", "tfln", "器件仿真", "category", "TMM/FDTD + 容差扫描"),
    ("tfln_sim", "tfln_dev", "simulations/02_tolerance_scan.py", "code", "TMM 容差扫描"),
    ("tfln_fdtd", "tfln_dev", "lumerical/run_tolerance_fdtd.py", "code", "FDTD 均匀/啁啾光栅"),
    ("tfln_m3b", "tfln_dev", "lumerical/m3b_delay_budget.py", "code", "延迟预算 424 ps/dB"),
    ("tfln_fdtd_res", "tfln_dev", "lumerical/results/", "results", "FDTD 原始数据"),
    ("tfln_tol_res", "tfln_dev", "results/tolerance_scan.{npz,png}", "results", "容差扫描结果"),

    ("tfln_kg", "tfln", "知识/图谱", "category", "任务-知识网络"),
    ("tfln_kg_py", "tfln_kg", "task_knowledge_graph.py", "code", "图谱生成脚本"),
    ("tfln_cards", "tfln_kg", "kg_obsidian_cards.py", "code", "Obsidian 卡片生成"),
    ("tfln_kg_json", "tfln_kg", "results/task_kg.json", "datafile", "43 节点 48 边"),

    ("tfln_infra", "tfln", "基础设施", "category", "Notebook 构建 + Git"),
    ("tfln_build", "tfln_infra", "build_m1~m4_notebook.py", "code", "自动生成 milestone notebook"),

    # lidar-pointnet
    ("lidar", "workspace", "lidar-pointnet", "repo", "光子 SNN / LiDAR 分类实验"),
    ("lidar_code", "lidar", "LiDAR/SNN 代码", "category", "训练、编码、读出"),
    ("lidar_m7", "lidar_code", "snn/m7_matched_info.py", "code", "M7 信息量匹配"),
    ("lidar_kitti", "lidar_code", "snn/road_kitti_experiment.py", "code", "KITTI 扫描链分类"),
    ("lidar_isal", "lidar_code", "snn/isal_range_profile.py", "code", "ISAL 距离像生成"),
    ("lidar_pn", "lidar_code", "models/pointnet.py", "code", "PointNet 基线"),
    ("lidar_train", "lidar_code", "train.py", "code", "端到端训练"),

    ("lidar_data", "lidar", "数据", "category", "KITTI / ModelNet40 / road_objects"),
    ("lidar_road", "lidar_data", "data/road_objects.npz", "datafile", "28,746 道路对象"),
    ("lidar_kitti_dir", "lidar_data", "data/kitti/", "data", "原始 Velodyne + label"),
    ("lidar_mn40", "lidar_data", "data/modelnet40_*.parquet", "datafile", "ModelNet40 基准"),

    ("lidar_res", "lidar", "结果", "category", "实验输出"),
    ("lidar_m7_res", "lidar_res", "outputs_m7/results.json", "datafile", "M7 echo/raw 对比"),
    ("lidar_kitti_res", "lidar_res", "snn/outputs_isal/road_kitti/", "results", "KITTI 0.923"),
    ("lidar_outputs", "lidar_res", "snn/outputs_classify/", "results", "ModelNet40 分类"),

    ("lidar_docs", "lidar", "文档/运行书", "category", "README + RUNBOOK"),
    ("lidar_runbook", "lidar_docs", "RUNBOOK_3060.md", "doc", "3060 开箱指南"),
    ("lidar_readme", "lidar_docs", "snn/README.md", "doc", "SNN 实验说明"),
]

LEARNING_TREE = [
    ("root", None, "KGFP 申请推进", "root", "2026-07 至今"),

    ("p0", "root", "Phase 0 立项与初版", "phase", "研究方向定位"),
    ("p0_lit", "p0", "文献：TFLN 流片速度 vs SiN", "milestone", "Cheng Wang 组 TFLN 更快"),
    ("p0_v1", "p0", "Concept Note v1 (100–1000 ps/nm)", "deliverable", "2026-09 上旬"),

    ("p1", "root", "Phase 1 器件物理标定", "phase", "Objective 1 设计规则"),
    ("p1_m3b", "p1", "M3b 延迟预算 → 亚米窗口", "milestone", "TFLN 424 ps/dB; 0.19 m"),
    ("p1_a1a2", "p1", "A1/A2 条宽与 dn 标定", "milestone", "dλ/dw=46 nm/µm"),
    ("p1_a3a6", "p1", "A3–A6 容差扫描", "milestone", "相位/温度/切趾/长度"),
    ("p1_cross", "p1", "TMM/FDTD 交叉校验", "milestone", "偏差 ~10%"),
    ("p1_rules", "p1", "器件设计规则 ×4", "knowledge", "摆幅/切趾/条宽/dn/温漂"),

    ("p2", "root", "Phase 2 算法与编码", "phase", "Objective 2 光子 SNN"),
    ("p2_m3a", "p2", "M3a delay learning", "milestone", "连续编码 0.888"),
    ("p2_m7", "p2", "M7 信息量匹配", "milestone", "echo 0.41 vs raw 0.66"),
    ("p2_quant", "p2", "池权重量化免疫", "knowledge", "4–8 bit 不降性能"),
    ("p2_synth", "p2", "合成道路目标", "milestone", "0.892 / 0.919"),

    ("p3", "root", "Phase 3 真实数据验证", "phase", "从合成到 KITTI"),
    ("p3_download", "p3", "KITTI 下载/提取", "milestone", "28,746 对象"),
    ("p3_small", "p3", "小预算扫描链 0.766", "milestone", "train=1200"),
    ("p3_gpu", "p3", "GPU 移植 3060", "milestone", "corr=0.999991"),
    ("p3_full", "p3", "全量预算 0.923", "knowledge", "train=21.5k"),
    ("p3_gain", "p3", "扫描链增益谱系", "knowledge", "受限场景价值"),

    ("p4", "root", "Phase 4 申请交付", "phase", "Stage 1 截止 2026-10-01"),
    ("p4_v2", "p4", "Concept Note v2", "deliverable", "带宽绑定规格+风险句"),
    ("p4_rec", "p4", "推荐信素材", "deliverable", "口径与红线"),
    ("p4_stage1", "p4", "Stage 1 提交 (todo)", "deliverable", "CN+CV+两封推荐信"),

    ("px", "root", "支撑与教训", "phase", "跨会话/跨机器"),
    ("px_tasklog", "px", "TASK_LOG 交接机制", "infra", "事实源"),
    ("px_git", "px", "两仓库 Git 迁移", "infra", "代码+数据通道"),
    ("px_sleep", "px", "教训：12h 睡眠假象", "lesson", "先 profile 再优化"),
]

PROJECT_COLOR = {
    "root": "#f7b6d3",
    "repo": "#9ecae1",
    "category": "#c7c7f0",
    "doc": "#fdd0a2",
    "notebook": "#ffe08a",
    "code": "#a1d99b",
    "data": "#d9d9d9",
    "datafile": "#bcbddc",
    "results": "#7ec97e",
    "infra": "#e8b4d8",
}

LEARNING_COLOR = {
    "root": "#f7b6d3",
    "phase": "#9ecae1",
    "milestone": "#a1d99b",
    "knowledge": "#ffe08a",
    "deliverable": "#fdd0a2",
    "infra": "#c7c7f0",
    "lesson": "#e88a8a",
}
