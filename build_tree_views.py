# -*- coding: utf-8 -*-
"""生成两个树状可视化 PNG（备用）：工程结构树 + 学习过程树

数据来自 tree_data.py。默认推荐使用 build_obsidian_tree_mermaid.py，
直接在 Obsidian 里渲染 Mermaid，无需等待 PNG。
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

from tree_data import (
    PROJECT_TREE, LEARNING_TREE,
    PROJECT_COLOR, LEARNING_COLOR,
)


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


def draw_tree(rows, title, filename, color_map, fontsize=10):
    G = make_graph(rows)
    root = [n for n, d in G.in_degree() if d == 0][0]
    pos, total_h = horizontal_tree_layout(G, root)

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    n_leaves = sum(1 for n in G if G.out_degree(n) == 0)
    fig_h = max(12, n_leaves * 0.62)
    fig_w = max(24, (x_max - x_min) * 2.8)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    nx.draw_networkx_edges(
        G, pos, ax=ax, arrows=False,
        edge_color="#888888", width=1.3, alpha=0.7,
        node_size=0,
    )
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
    draw_tree(
        PROJECT_TREE,
        "工程结构树：KGFP 工作空间",
        "project_tree",
        PROJECT_COLOR,
    )
    draw_tree(
        LEARNING_TREE,
        "学习过程树：从立项到 Stage 1",
        "learning_tree",
        LEARNING_COLOR,
    )
    if os.path.isdir(VAULT_DIR):
        os.makedirs(VAULT_DIR, exist_ok=True)
        for name in ("project_tree", "learning_tree"):
            src = os.path.join(OUT, name + ".png")
            dst = os.path.join(VAULT_DIR, name + ".png")
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print("copied ->", dst)


if __name__ == "__main__":
    main()
