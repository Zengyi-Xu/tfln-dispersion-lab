# -*- coding: utf-8 -*-
"""任务-知识图谱：KGFP 申请 + 仿真/实验/基础设施 全任务关系与进度（2026-09-25）

节点 = 任务 / 数据 / 知识结论，按层着色；前缀 ●=已完成 ◐=进行中 ○=待办 ✖=受阻
边   = 关系（实线=支撑/产出/输入，虚线=修正/证伪，点线=依赖）
输出：results/task_knowledge_graph.png + results/task_kg.json
"""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

L = {"apply": "申请交付", "dev": "器件仿真", "algo": "算法实验",
     "data": "数据", "infra": "基础设施", "know": "知识结论"}
S = {"done": "●", "doing": "◐", "todo": "○", "blocked": "×"}

# (id, label, layer, status)
NODES = [
    # 申请交付
    ("cn_v1", "Concept Note 第一版\n(100–1000 ps/nm)", "apply", "done"),
    ("cn_v2", "Concept Note 第二版\n(带宽绑定规格+文献+风险)", "apply", "done"),
    ("rec", "推荐信素材\n(项目简述+口径红线)", "apply", "done"),
    ("sign", "推荐信签字转PDF", "apply", "todo"),
    ("cv", "CV 学位状态更新", "apply", "todo"),
    ("form", "网申表单", "apply", "todo"),
    ("stage1", "Stage 1 提交\n(截止 2026-10-01)", "apply", "todo"),
    ("stage3", "Stage 3 Full Proposal\n(2027-01-15)", "apply", "todo"),
    # 器件仿真
    ("m1", "M1 光子链路\n时标分离 1.00 vs 0.27", "dev", "done"),
    ("m3b", "M3b 延迟预算\nTFLN 424 ps/dB", "dev", "done"),
    ("a1", "A1 条宽标定\ndλ_B/dw=46 nm/µm", "dev", "done"),
    ("a2", "A2 κ(dn) 标定\nλ_B 对 dn 不敏感", "dev", "done"),
    ("a2b", "A2b 啁啾 dn±10%\nD 不变 ripple+24%", "dev", "done"),
    ("a3", "A3 相位误差\n白噪声可忽略", "dev", "done"),
    ("a4", "A4 温漂\n0.03 ps/K 可忽略", "dev", "done"),
    ("a5", "A5 摆幅-长度线性\n偏差~2%", "dev", "done"),
    ("a6", "A6 切趾\n0.09 ps ↔ 3×长度", "dev", "done"),
    ("tmm_fdtd", "TMM vs FDTD 交叉校验\n偏差 10%", "dev", "done"),
    ("c1", "C1 真实信号链\n(替换高斯 spike)", "dev", "todo"),
    ("c2", "C2 端到端联合仿真\n(HATF 全链路)", "dev", "todo"),
    ("corr_err", "慢变相关误差模型\n(电子束剂量漂移)", "dev", "todo"),
    # 算法实验
    ("lsm", "LSM 低SNR检测\n-15dB 反超 CFAR", "algo", "done"),
    ("m3a", "M3a delay learning\n连续编码 0.888", "algo", "done"),
    ("m7", "M7 信息匹配对比\necho 0.41 vs raw 0.66", "algo", "done"),
    ("synth", "合成道路目标\n0.892 / 0.919", "algo", "done"),
    ("kitti_s", "KITTI 小预算\n0.657→0.766", "algo", "done"),
    ("kitti_f", "KITTI 全量 21.5k\n0.872→0.923", "algo", "done"),
    ("gpu_port", "GPU 化移植\ncorr=0.999991", "algo", "done"),
    # 数据
    ("kitti_d", "KITTI 下载+提取\n28,746 对象", "data", "done"),
    ("rs", "RadarScenes\nzip截断+IP被封", "data", "blocked"),
    ("mn40", "ModelNet40\n(M2/M7 基准)", "data", "done"),
    # 基础设施
    ("git", "两仓库 push 迁移", "infra", "done"),
    ("gpu3060", "3060 平台\n(11800H+3060)", "infra", "done"),
    ("tasklog", "TASK_LOG 交接机制", "infra", "done"),
    ("runbook", "RUNBOOK_3060\n+ 任务 md", "infra", "done"),
    ("pdl", "并行分段下载\n6 MB/s 断点续传", "infra", "done"),
    # 知识结论
    ("k_sub", "亚米窗口定位\n(1ns摆幅↔0.19m)", "know", "done"),
    ("k_ts", "时标分离架构\n(快光处理+慢电读出)", "know", "done"),
    ("k_enc", "编码格式是瓶颈\n(非蓄水池/二值化)", "know", "done"),
    ("k_quant", "池权重 4–8bit\n量化免疫", "know", "done"),
    ("k_gain", "扫描链增益随\n条件恶化放大", "know", "done"),
    ("k_rules", "器件设计规则×4\n(摆幅/切趾/容差/温漂)", "know", "done"),
    ("k_sleep", "教训: 12h=\n睡眠挂起假象", "know", "done"),
]

# (src, dst, relation, style)  style: solid/dashed/dotted
EDGES = [
    ("m3b", "cn_v1", "证伪 100–1000 ps/nm", "dashed"),
    ("cn_v1", "cn_v2", "修正为带宽绑定", "dashed"),
    ("k_sub", "cn_v2", "定位依据", "solid"),
    ("k_rules", "cn_v2", "Objective 1 支撑", "solid"),
    ("k_ts", "cn_v2", "Objective 3 支撑", "solid"),
    ("k_quant", "cn_v2", "硬件可行性", "solid"),
    ("kitti_f", "cn_v2", "预备数据 0.923", "solid"),
    ("k_gain", "rec", "口径: 增益谱系", "solid"),
    ("kitti_f", "rec", "preliminary 0.923", "solid"),
    ("m1", "rec", "压缩比22 偏差<10%", "solid"),
    ("cn_v2", "stage1", "提交物", "dotted"),
    ("sign", "stage1", "必备", "dotted"),
    ("cv", "stage1", "必备", "dotted"),
    ("form", "stage1", "必备", "dotted"),
    ("rec", "sign", "待签字", "dotted"),
    ("m1", "k_ts", "产出", "solid"),
    ("m3b", "k_sub", "产出", "solid"),
    ("a5", "k_rules", "摆幅线性", "solid"),
    ("a6", "k_rules", "切趾权衡", "solid"),
    ("a1", "k_rules", "条宽窗口", "solid"),
    ("a2", "k_rules", "dn窗口", "solid"),
    ("a3", "k_rules", "相位不敏感", "solid"),
    ("a4", "k_rules", "温漂不敏感", "solid"),
    ("a2b", "a2", "啁啾验证", "solid"),
    ("tmm_fdtd", "a5", "方法互证", "solid"),
    ("corr_err", "a3", "补白噪声盲区", "dotted"),
    ("c1", "m1", "替换理想输入", "dashed"),
    ("c2", "stage3", "全链路证据", "dotted"),
    ("m7", "k_enc", "产出", "solid"),
    ("m7", "k_quant", "产出", "solid"),
    ("m3a", "m7", "对照: 连续vs二值", "dashed"),
    ("mn40", "m7", "输入", "dotted"),
    ("mn40", "m3a", "输入", "dotted"),
    ("lsm", "k_gain", "低SNR +0.3", "solid"),
    ("kitti_s", "k_gain", "小预算 +0.11", "solid"),
    ("kitti_f", "k_gain", "全量 +0.05", "solid"),
    ("kitti_s", "kitti_f", "训练预算提升", "solid"),
    ("synth", "kitti_f", "合成预测 0.92≈真实0.923", "solid"),
    ("kitti_d", "kitti_s", "输入", "dotted"),
    ("kitti_d", "kitti_f", "输入", "dotted"),
    ("pdl", "kitti_d", "完成下载", "solid"),
    ("gpu_port", "kitti_f", "加速+校验", "solid"),
    ("gpu3060", "kitti_f", "运行平台", "solid"),
    ("runbook", "gpu3060", "开箱指南", "solid"),
    ("tasklog", "runbook", "状态来源", "solid"),
    ("git", "gpu3060", "代码+数据通道", "solid"),
    ("k_sleep", "gpu_port", "修正优先级认知", "dashed"),
    ("rs", "stage3", "杂波标定(可选)", "dotted"),
]

STATUS_COLOR = {"done": "#7ec97e", "doing": "#f5c542", "todo": "#d9d9d9",
                "blocked": "#e88a8a"}
LAYER_COLOR = {"apply": "#e8b4d8", "dev": "#9ecae1", "algo": "#a1d99b",
               "data": "#fdd0a2", "infra": "#c7c7f0", "know": "#ffe08a"}


def main():
    G = nx.DiGraph()
    for nid, label, layer, status in NODES:
        G.add_node(nid, label="%s %s" % (S[status], label),
                   layer=layer, status=status)
    for s, d, rel, st in EDGES:
        G.add_edge(s, d, relation=rel, style=st)

    # 泳道布局：按层分列（信息流 左->右），列内按状态排序均布 + 微抖动
    col_order = ["infra", "data", "dev", "algo", "know", "apply"]
    status_rank = {"done": 0, "doing": 1, "todo": 2, "blocked": 3}
    rng_j = __import__("numpy").random.default_rng(3)
    pos = {}
    for ci, layer in enumerate(col_order):
        ns = [n for n in G.nodes if G.nodes[n]["layer"] == layer]
        ns.sort(key=lambda n: (status_rank[G.nodes[n]["status"]], n))
        for ri, n in enumerate(ns):
            y = 1.0 - 2.0 * (ri + 0.5) / max(len(ns), 1)
            pos[n] = (ci * 1.0 + rng_j.uniform(-0.06, 0.06),
                      y + rng_j.uniform(-0.02, 0.02))

    fig, ax = plt.subplots(figsize=(22, 13))

    for layer in L:
        ns = [n for n in G.nodes if G.nodes[n]["layer"] == layer]
        nx.draw_networkx_nodes(
            G, pos, nodelist=ns, ax=ax, node_size=4200,
            node_color=[LAYER_COLOR[layer]] * len(ns),
            edgecolors=[STATUS_COLOR[G.nodes[n]["status"]] for n in ns],
            linewidths=3.0, label=L[layer])

    for st, ls in [("solid", "-"), ("dashed", "--"), ("dotted", ":")]:
        es = [(s, d) for s, d, r, sty in EDGES if sty == st]
        nx.draw_networkx_edges(G, pos, edgelist=es, ax=ax, style=ls,
                               edge_color="#666666", arrows=True,
                               arrowsize=14, width=1.1,
                               connectionstyle="arc3,rad=0.06",
                               alpha=0.75)

    labels = {n: G.nodes[n]["label"] for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=8.5)

    edge_labels = {(s, d): r for s, d, r, st in EDGES if st != "solid"}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax, font_size=7,
                                 font_color="#a03030")

    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
                      markersize=12, label=L[k]) for k, c in LAYER_COLOR.items()]
    handles += [Line2D([0], [0], marker="o", color="w", markerfacecolor="w",
                       markeredgecolor=c, markersize=12, markeredgewidth=3,
                       label=t)
                for t, c in [("已完成", "#7ec97e"), ("进行中", "#f5c542"),
                             ("待办", "#d9d9d9"), ("受阻", "#e88a8a")]]
    ax.legend(handles=handles, loc="upper left", fontsize=9, ncol=2,
              framealpha=0.9)
    ax.set_title("任务-知识图谱：KGFP 申请 × TFLN 器件 × 光子 SNN 实验"
                 "（截至 2026-09-25）", fontsize=15)
    ax.axis("off")
    fig.tight_layout()
    png = os.path.join(OUT, "task_knowledge_graph.png")
    fig.savefig(png, dpi=160)
    print("saved", png)

    data = {"nodes": [{"id": n, "label": l, "layer": ly, "status": s}
                      for n, l, ly, s in NODES],
            "edges": [{"src": s, "dst": d, "relation": r, "style": st}
                      for s, d, r, st in EDGES]}
    js = os.path.join(OUT, "task_kg.json")
    with open(js, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("saved", js, " nodes=%d edges=%d" % (len(NODES), len(EDGES)))


if __name__ == "__main__":
    main()
