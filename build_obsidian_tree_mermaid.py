# -*- coding: utf-8 -*-
"""生成 Obsidian 原生 Mermaid 树状图（不预渲染 PNG，打开笔记即渲染）

输出：
  Heterogeneous_integration/4-plan/KGFP任务图谱/工程与学习过程树.md
  tfln-dispersion-lab/results/project_tree_mermaid.md
  tfln-dispersion-lab/results/learning_tree_mermaid.md
"""
import os
import sys

# 复用 build_tree_views.py 里的树数据
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_tree_views import (
    PROJECT_TREE, LEARNING_TREE,
    PROJECT_COLOR, LEARNING_COLOR,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

VAULT_DIR = os.path.join(HERE, "..", "Heterogeneous_integration", "4-plan", "KGFP任务图谱")


def safe_id(nid):
    return "n" + "".join(ch for ch in nid if ch.isalnum() or ch == "_").replace("__", "_")


def escape_label(s):
    return s.replace('"', "#quot;").replace("\n", " ").replace("<", "<").replace(">", ">")


def build_mermaid(rows, color_map):
    """rows: list of (id, parent, label, type, detail)"""
    id_of = {r[0]: safe_id(r[0]) for r in rows}
    lines = ["graph TD"]
    # 节点定义
    for nid, parent, label, ntype, detail in rows:
        sid = id_of[nid]
        text = f"{escape_label(label)}<br/>({escape_label(detail)})"
        lines.append(f'    {sid}["{text}"]')
    # 边
    for nid, parent, label, ntype, detail in rows:
        if parent is not None:
            lines.append(f'    {id_of[parent]} --> {id_of[nid]}')
    # 样式类
    for ntype, color in color_map.items():
        lines.append(f'    classDef {ntype} fill:{color},stroke:#555555,color:#222222;')
    for nid, parent, label, ntype, detail in rows:
        lines.append(f'    class {id_of[nid]} {ntype};')
    return "\n".join(lines)


def build_bullets(rows, title):
    """生成可折叠的 Markdown 大纲树"""
    children = {}
    root = None
    data = {}
    for nid, parent, label, ntype, detail in rows:
        data[nid] = (label, ntype, detail)
        if parent is None:
            root = nid
        else:
            children.setdefault(parent, []).append(nid)

    lines = [f"## {title}（文本大纲）", ""]
    icon_map = {
        "root": "🌳", "repo": "📁", "category": "📂", "phase": "📂",
        "doc": "📝", "notebook": "📓", "code": "💻", "data": "🗃️",
        "datafile": "📄", "results": "📊", "infra": "🔧",
        "milestone": "⭐", "knowledge": "💡", "deliverable": "📦",
        "lesson": "⚠️",
    }

    def walk(u, depth):
        label, ntype, detail = data[u]
        icon = icon_map.get(ntype, "•")
        indent = "  " * depth
        lines.append(f"{indent}- {icon} **{label}** — {detail}")
        for c in children.get(u, []):
            walk(c, depth + 1)

    walk(root, 0)
    return "\n".join(lines)


def main():
    project_mermaid = build_mermaid(PROJECT_TREE, PROJECT_COLOR)
    learning_mermaid = build_mermaid(LEARNING_TREE, LEARNING_COLOR)

    md = "---\n"
    md += "type: tree-view\ntags: [kgfp-task]\ncreated: 2026-09-25\n"
    md += "---\n\n"
    md += "# 工程结构树与学习过程树\n\n"
    md += "> 本页使用 Obsidian 原生 Mermaid 渲染，无需预生成 PNG。"
    md += "若 Mermaid 插件未启用，可查看下方的 Markdown 文本大纲。\n\n"

    md += "## 工程结构树\n\n"
    md += "```mermaid\n" + project_mermaid + "\n```\n\n"
    md += build_bullets(PROJECT_TREE, "工程结构树") + "\n\n"

    md += "---\n\n"

    md += "## 学习过程树\n\n"
    md += "```mermaid\n" + learning_mermaid + "\n```\n\n"
    md += build_bullets(LEARNING_TREE, "学习过程树") + "\n\n"

    # 写入 vault（Obsidian 直接查看）
    if os.path.isdir(VAULT_DIR):
        os.makedirs(VAULT_DIR, exist_ok=True)
        vault_path = os.path.join(VAULT_DIR, "工程与学习过程树.md")
        with open(vault_path, "w", encoding="utf-8") as f:
            f.write(md)
        print("saved", vault_path)

    # 同时写入仓库 results 目录
    for name, content in [("project_tree_mermaid.md", project_mermaid),
                          ("learning_tree_mermaid.md", learning_mermaid)]:
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("```mermaid\n" + content + "\n```\n")
        print("saved", path)


if __name__ == "__main__":
    main()
