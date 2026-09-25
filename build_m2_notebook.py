# -*- coding: utf-8 -*-
"""Build milestone-M2-snn-classification.ipynb (Jupyter summary document)."""
import io
import json

cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": text.splitlines(keepends=True)})


def code(text):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": text.splitlines(keepends=True)})


md("""# 里程碑 M2：SNN/蓄水池在真实分类任务上的验证（digits + ModelNet40 点云）

**日期**：2026-09-20 · **脚本**：`lidar-pointnet/snn/classification_demo.py` · **复用**：`lidar-pointnet/snn/reservoir.py` 的 LSM

## 本节要回答的问题

> M1 证明了"ps spike → 蓄水池 → 慢读出"在合成任务上成立。但这个蓄水池能不能做**真实分类任务**？
> 如果能做到什么程度？它的表达上限在哪？

用两个真实数据集：
1. **sklearn digits**（8×8，MNIST 代理，10 类）——像素强度 → 脉冲发放率编码
2. **ModelNet40 点云**（10 类子集）——两种脉冲编码：坐标速率编码 + 距离回波编码（模拟光栅压缩前端输出）""")

md("""## 1. 任务与编码

| 数据集 | 规模 | 编码 | 蓄水池 | 读出 |
|---|---|---|---|---|
| digits 8×8 | 1200 训练 / 400 测试 | 64 像素通道，发放率 ∝ 强度，T=60 步 | 256 LIF | 岭回归（对偶形式） |
| ModelNet40 | 10 类 × 150/40，256 点 | A: 6 通道坐标速率；B: 3 通道距离回波 | 512 LIF ×2 | 岭回归 + 特征拼接 |

**距离回波编码（物理动机）**：spike 到达时间 ∝ 点的径向距离——这正是光栅压缩 LiDAR 前端会产生的信号形式。
它把"点云分类"直接映射到我们这个光子链路的输出格式上。""")

md("""## 2. 结果总览""")

code("""import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

d = np.load("lidar-pointnet/snn/outputs_classify/classification_results.npz")
print("digits (10 类):")
print("  LSM 蓄水池准确率: %.3f   (raw-LR 基线 %.3f, 随机 0.10)" % (float(d["digits_acc"]), float(d["digits_raw"])))
print("  池内平均发放率: %.3f (能耗指标)" % float(d["digits_spike_rate"]))
print()
print("ModelNet40 点云 (10 类, 256 点):")
print("  LSM 坐标速率编码:   %.3f" % float(d["mn_acc_coord"]))
print("  LSM 距离回波编码:   %.3f" % float(d["mn_acc_echo"]))
print("  LSM 组合编码:       %.3f" % float(d["mn_acc_combined"]))
print("  raw-LR 基线:        %.3f   (随机 0.10)" % float(d["mn_raw"]))

img = Image.open("lidar-pointnet/snn/outputs_classify/classification_summary.png")
plt.figure(figsize=(10, 5))
plt.imshow(img)
plt.axis("off")
plt.show()""")

md("""**解读**：
- **digits 上 LSM 达 94.3%**，接近 raw-LR 的 97.8%——固定随机蓄水池对简单图像任务有效。
- **点云上组合编码 40%**（10 类，4× 随机），有意义但远低于 PointNet（40 类 ~89%）和 raw-LR 基线（68%）。
- 两种编码互补（各自 ~32%，组合 40%），说明蓄水池确实提取了不同的时序特征。""")

md("""## 3. 混淆矩阵""")

code("""fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, fname, ttl in zip(axes,
    ["confusion_digits.png", "confusion_modelnet.png"],
    ["digits (acc 0.94)", "ModelNet40 subset (acc 0.40)"]):
    ax.imshow(Image.open("lidar-pointnet/snn/outputs_classify/" + fname))
    ax.set_title(ttl)
    ax.axis("off")
plt.tight_layout()
plt.show()""")

md("""## 4. 表达上限：规模与数据量扫描（关键发现）

对组合编码做两个扫描（3 个蓄水池种子平均，误差棒为标准差）：""")

code("""img = Image.open("lidar-pointnet/snn/outputs_classify/modelnet_scaling.png")
plt.figure(figsize=(12, 4.5))
plt.imshow(img)
plt.axis("off")
plt.show()

print("蓄水池规模扫描 (n_train=150/类):")
for n, a, s in zip(d["scaling_n_res"], d["scaling_res_accs"], d["scaling_res_accs_std"]):
    print("  n_res=%5d: %.3f +/- %.3f" % (n, a, s))
print("训练集规模扫描 (n_res=512):")
for n, a, s in zip(d["scaling_train_sizes"], d["scaling_train_accs"], d["scaling_train_accs_std"]):
    print("  n_train=%3d/类: %.3f +/- %.3f" % (n, a, s))""")

md("""**两条曲线都饱和**：
- 蓄水池从 64 涨到 1024 神经元，准确率在 0.35–0.42 之间波动，**不单调增长**；
- 训练集从 20 涨到 300/类，准确率在 ~0.38 见顶。

这与 `lidar-pointnet/snn/README.md` 在低 SNR 雷达检测任务上的结论一致：
**"高 SNR 平台期不是 SNN 不行，而是随机被动蓄水池的表达上限"**。

## 5. 结论与对本项目的意义

**结论 1（支持架构）**：LSM 蓄水池确实能做真实分类任务，digits 上 94% 证明了链路末端的可行性。

**结论 2（指出方向）**：固定随机蓄水池在复杂 3D 任务上饱和在 ~40%，天花板明显。
**打破天花板需要可训练/可调的自由度**——这正是本项目"TFLN 电光可调延迟 = 可学习突触延迟"的价值主张：
- 把固定延迟抽头换成**电压可调延迟**（TFLN Pockels），
- 用 delay learning 训练这些延迟，
- 有望突破随机蓄水池的表达上限。

这把"器件层的可调色散"和"算法层的 delay learning"通过同一个物理对象（可调延迟元件）连了起来，
是博士后计划里最有原创性的一环。

## 6. 下一步（→ M3）

1. 把 LSM 的固定延迟抽头换成**可训练延迟**（先在数字模型验证 delay learning 的上限提升）；
2. 量化真实 TFLN 延迟线的损耗/带宽对蓄水池性能的影响；
3. 端到端：光栅压缩 + QD spike + 可调蓄水池的联合仿真。""")

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.14.6"}},
      "nbformat": 4, "nbformat_minor": 5}

with io.open("milestone-M2-snn-classification.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("wrote milestone-M2-snn-classification.ipynb with %d cells" % len(cells))
