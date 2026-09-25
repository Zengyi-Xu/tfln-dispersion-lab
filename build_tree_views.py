# -*- coding: utf-8 -*-
"""生成两个树状可视化：工程结构树 + 学习过程树

输出：
  results/project_tree.{png,json}
  results/learning_tree.{png,json}
  同时在 Heterogeneous_integration/4-plan/KGFP任务图谱/ 下生成同名 PNG + 工程与学习过程树.md
"""
import json
import os
import shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

VAULT_DIR = os.path.join(HERE, "..", "Heterogeneous_integration", "4-plan", "KGFP任务图谱")

STATUS_ICON = {"done": "✅", "doing": "🔄", "todo": "⬜", "blocked": "🚫"}

# ---------------------------------------------------------------------------
# 工程结构树（语义化，不是完整文件系统）
# ---------------------------------------------------------------------------
PROJECT_TREE = [
    # (id, parent, label, type, detail)
    ("workspace", None, "KGFP 工作空间", "root", "tfln-dispersion-lab + lidar-pointnet"),
    # ---- tfln-dispersion-lab ----
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

    # ---- lidar-pointnet ----
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

# ---------------------------------------------------------------------------
# 学习过程树（按时间/依赖组织）
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
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


def make_graph(rows):
    G = nx.DiGraph()
    for nid, parent, label, ntype, detail in rows:
        G.add_node(nid, label=label, ntype=ntype, detail=detail)
        if parent is not None:
            G.add_edge(parent, nid)
    return G


def horizontal_tree_layout(G, root, dx=3.0, dy=0.55):
    """根在左，子节点在右；每个叶子独占一行，父节点纵坐标取子树中位"""
    leaves = []

    def collect_leaves(u):
        children = list(G.successors(u))
        if not children:
            leaves.append(u)
        else:
            for c in children:
                collect_leaves(c)

    collect_leaves(root)
    leaf_y = {leaf: i * dy for i, leaf in enumerate(leaves)}
    pos = {}

    def place(u, depth):
        children = list(G.successors(u))
        if not children:
            pos[u] = (depth * dx, leaf_y[u])
        else:
            for c in children:
                place(c, depth + 1)
            ys = [pos[c][1] for c in children]
            pos[u] = (depth * dx, sum(ys) / len(ys))

    place(root, 0)
    return pos, len(leaves) * dy


def draw_tree(rows, title, filename, color_map, figsize=(30, 18), fontsize=10):
    G = make_graph(rows)
    root = [n for n, d in G.in_degree() if d == 0][0]
    pos, total_h = horizontal_tree_layout(G, root)

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    # 根据叶子数量调整高度，避免标签堆叠
    n_leaves = sum(1 for n in G if G.out_degree(n) == 0)
    fig_h = max(12, n_leaves * 0.62)
    fig_w = max(24, (x_max - x_min) * 2.8)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # 边
    nx.draw_networkx_edges(
        G, pos, ax=ax, arrows=False,
        edge_color="#888888", width=1.3, alpha=0.7,
        node_size=0,
    )
    # 节点按类型分批绘制，保证图例
    for ntype, color in color_map.items():
        ns = [n for n in G.nodes if G.nodes[n]["ntype"] == ntype]
        if not ns:
            continue
        nx.draw_networkx_nodes(
            G, pos, nodelist=ns, ax=ax,
            node_color=color, node_size=400,
            edgecolors="#555555", linewidths=1.0,
            label=ntype,
        )
    # 标签：带底色，居中对齐
    labels = {n: G.nodes[n]["label"] for n in G.nodes}
    bbox = dict(boxstyle="round,pad=0.22", facecolor="white",
                edgecolor="#cccccc", alpha=0.92)
    nx.draw_networkx_labels(
        G, pos, labels, ax=ax,
        font_size=fontsize, font_weight="normal",
        verticalalignment="center", bbox=bbox,
    )

    margin_x = (x_max - x_min) * 0.08 + 1.0
    margin_y = (total_h / max(n_leaves, 1)) * 0.5
    ax.set_xlim(x_min - margin_x, x_max + margin_x)
    ax.set_ylim(y_min - margin_y, y_max + margin_y)
    ax.set_title(title, fontsize=18, pad=16)
    ax.axis("off")
    ax.legend(loc="upper right", fontsize=10, framealpha=0.95)
    fig.tight_layout()

    png = os.path.join(OUT, filename + ".png")
    fig.savefig(png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("saved", png)

    # JSON
    js = os.path.join(OUT, filename + ".json")
    with open(js, "w", encoding="utf-8") as f:
        json.dump(
            [{"id": r[0], "parent": r[1], "label": r[2], "type": r[3], "detail": r[4]}
             for r in rows],
            f, ensure_ascii=False, indent=2,
        )
    print("saved", js)
    return png, js


def markdown_tree(rows, title):
    G = make_graph(rows)
    root = [n for n, d in G.in_degree() if d == 0][0]
    lines = [f"# {title}", ""]

    def walk(u, depth):
        icon = {"root": "🌳", "repo": "📁", "category": "📂"}.get(G.nodes[u]["ntype"], "📄")
        indent = "  " * depth
        lines.append(f"{indent}- {icon} **{G.nodes[u]['label']}** — {G.nodes[u]['detail']}")
        for c in G.successors(u):
            walk(c, depth + 1)

    walk(root, 0)
    return "\n".join(lines) + "\n"


def main():
    # 1. 工程结构树
    draw_tree(
        PROJECT_TREE,
        "工程结构树：KGFP 工作空间",
        "project_tree",
        PROJECT_COLOR,
        figsize=(26, 18),
        fontsize=9,
    )

    # 2. 学习过程树
    draw_tree(
        LEARNING_TREE,
        "学习过程树：从立项到 Stage 1",
        "learning_tree",
        LEARNING_COLOR,
        figsize=(26, 20),
        fontsize=9,
    )

    # 3. Obsidian 笔记
    if os.path.isdir(VAULT_DIR):
        os.makedirs(VAULT_DIR, exist_ok=True)
        for name in ("project_tree", "learning_tree"):
            src = os.path.join(OUT, name + ".png")
            dst = os.path.join(VAULT_DIR, name + ".png")
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print("copied ->", dst)

        md_path = os.path.join(VAULT_DIR, "工程与学习过程树.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("---\ntype: tree-view\ntags: [kgfp-task]\ncreated: 2026-09-25\n---\n\n")
            f.write("# 工程结构树与学习过程树\n\n")
            f.write("> 由 `tfln-dispersion-lab/build_tree_views.py` 生成，"
                    "用于把项目目录和知识获取过程以树形呈现。\n\n")
            f.write("## 工程结构树\n\n")
            f.write("![工程结构树](project_tree.png)\n\n")
            f.write("## 学习过程树\n\n")
            f.write("![学习过程树](learning_tree.png)\n\n")
            f.write("---\n\n")
            f.write(markdown_tree(PROJECT_TREE, "工程结构树（文本版）"))
            f.write("\n")
            f.write(markdown_tree(LEARNING_TREE, "学习过程树（文本版）"))
        print("saved", md_path)
    else:
        print("vault dir not found, skip Obsidian copy:", VAULT_DIR)


if __name__ == "__main__":
    main()
