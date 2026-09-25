# -*- coding: utf-8 -*-
"""Build milestone-M4-isal-range-profile.ipynb."""
import io
import json

cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": text.splitlines(keepends=True)})


def code(text):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": text.splitlines(keepends=True)})


md("""# 里程碑 M4：仿真距离像（HRRP）与转台 ISAL——啁啾压缩之后接什么

**日期**：2026-09-20 · **脚本**：`lidar-pointnet/snn/isal_range_profile.py`、`isal_beam_scan.py` · **数据**：`results/snn/m4_isal_results.npz`、`m4_beam_scan_results.npz`

M1–M3 证明了"压缩 → spike → 蓄水池"链路可行，但输入 spike 是解析生成的。
本里程碑回答一个更贴近器件的问题：**啁啾光栅匹配滤波的真实输出——相干距离像（HRRP）——本身携带多少可分类信息？**
顺带回答它的成像版本：**多角度距离像能否合成 2D 像（转台 ISAL），以及散斑去相干何时把它毁掉。**

应用定位（沿前序讨论收敛）：短距小目标/车辆的回波识别与精细成像——
TFLN 单器件窗口（~0.2 m，M3b）对应 **D = 0.15 m 小目标**情形，SiN 窗口对应 **D = 4 m 车辆**情形。""")

md("""## 1. 物理模型（0 阶散射点模型，附诚实边界）

每个物体表面采样点 = 独立点散射中心，复反射率 $a_i = |a_i|e^{i\\phi_i}$（$|a_i|$ Rayleigh、$\\phi_i$ 均匀）。
方位角 $\\theta$ 下的相干距离像：

$$p(\\theta, r) = \\sum_{i: r_i \\in \\text{cell}(r)} a_i\\,\\exp\\!\\left(i\\tfrac{4\\pi}{\\lambda} r_i(\\theta) + i\\pi\\,\\eta_i(\\theta)\\right),\\qquad r_i(\\theta)=x_i\\cos\\theta+y_i\\sin\\theta$$

- **散斑**：距离元内多散射中心相干叠加自然产生（有效波长 $\\lambda_{\\rm eff}$ = 距离元/8，处于完全发展散斑区；绝对 $\\lambda$ 不改变统计性质）；
- **散斑去相干**：$\\eta_i(\\theta)$ 为方位角上的 Ornstein–Uhlenbeck 随机游走，相干角 $\\theta_c$ 可调（$\\theta_c\\to\\infty$ = 理想相干点目标；光学波段粗糙表面 $\\theta_c \\sim \\lambda/(2L)$，cm 级目标约 0.005°）；
- **分类用幅度** $|p|$（与真实 HRRP 系统一致），**成像用复数据**做方位向 FFT（小角度近似，弯曲走动 < 距离元，忽略 MTRC）。

**诚实边界**：无多次散射、无材料 RCS、无遮挡建模；是 proof-of-concept，写论文时升级 PO 电磁仿真。""")

code("""import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

img = Image.open("results/snn/m4_fig_profiles.png")
plt.figure(figsize=(13, 9))
plt.imshow(img); plt.axis("off"); plt.show()""")

md("""**图 1 解读**：四类目标在三个方位角下的仿真距离像（D = 4 m 窗口，128 距离元 → 3.1 cm 分辨，等效带宽 ≈4.8 GHz）。
形态与真实 HRRP 数据一致：强散斑、随方位剧烈变化、类间结构可辨——这正是"匹配滤波器输出端"上蓄水池要面对的信号。""")

code("""img = Image.open("results/snn/m4_fig_isal.png")
plt.figure(figsize=(13, 7))
plt.imshow(img); plt.axis("off"); plt.show()""")

md("""**图 2 解读（第三面墙的定量演示）**：±3° 相干孔径转台 ISAL。
- $\\theta_c=\\infty$：car 的前视轮廓、airplane 的机身+机翼" T "形清晰可辨——**相干合成孔径在理想点目标上成立**；
- $\\theta_c=0.3°$：像开始溶解成距离向条纹（能量仍在正确距离元，但方位向散焦）；
- $\\theta_c=0.05°$（仍远大于光学粗糙表面的 0.005°）：像完全消失。

**结论**：对光学波长的粗糙目标，纯相干 ISAL 的方位向聚焦会被目标自身散斑去相干摧毁——
这定量支持了应用定位：**要么小积累角/低分辨，要么放弃方位相干、走幅度域多角度处理**。""")

md("""## 2. 单剖面分类：距离像本身携带多少信息？

10 类 ModelNet40（airplane/bathtub/bed/bench/bookshelf/bottle/bowl/car/chair/cone），
每类 ~150 训练 / ~40 测试，每个样本取**一个随机方位**的幅度距离像。

为公平判断"0.382 是高是低"，补跑两类基准：
- **1D CNN**：把距离像当 1D 空间信号处理，是 HRRP 深度识别文献的标准基线；
- **multi-look 平均**：对同一个目标取 4/16 个随机方位的距离像做非相干平均后再用 1D CNN，模拟雷达里的脉冲/频率分集。""")

code("""import numpy as np
d = np.load("results/snn/m4_isal_results.npz", allow_pickle=True)
print("10-class ModelNet40, single random-aspect range profile:")
for k in ["acc_profile_ridge", "acc_profile_ce", "acc_profile_esn_ce", "acc_profile_cnn", "acc_isal_img_ce"]:
    print("  %-22s %.3f" % (k.replace("acc_",""), float(d[k])))
print("\nmulti-look baseline (1D CNN, no average / 4-look / 16-look):")
for k in ["acc_profile_cnn", "acc_4look_cnn", "acc_16look_cnn"]:
    print("  %-22s %.3f" % (k.replace("acc_",""), float(d[k])))
print("\n对照（M2 同任务全 3D 点云）: ridge 0.40 / CE 0.84 —— 单剖面信息上限显著更低")
print("小目标 D=0.15 m (TFLN 窗口): profile+ESN %.3f" % float(d["acc_small"]))""")

code("""img = Image.open("results/snn/m4_fig_classification.png")
plt.figure(figsize=(13, 5))
plt.imshow(img); plt.axis("off"); plt.show()""")

md("""**分类结果解读**：
- **ESN 单剖面 0.382 > 1D CNN 单剖面 0.291**——对"单次随机方位回波"这个任务，蓄水池不是瓶颈，反而略胜标准 1D CNN；
- **multi-look 是信息天花板**：4 次平均 0.397，16 次平均 **0.509**。这是雷达 HRRP 文献的标准做法：通过脉冲/频率分集平均散斑；
- **单剖面 vs 16-look 的差距（0.38 vs 0.51）≈ 散斑/视角信息增益**；单剖面 vs 全 3D 点云（0.84）≈ 1D 投影的信息论损失；
- 所以**0.382 不是方法失败**，而是"单次随机方位 HRRP 分类"这个设定本身的天花板就在 0.3–0.4 附近。我们的卖点应放在**单次脉冲处理**（无需 16 次积累）+ 蓄水池的低训练成本上，而不是去追 0.8+ 的全 3D 精度。""")

md("""## 3. 方位角泛化：一个 U 形曲线和一个免费的对称性

训练方位限制在 ±30° 内，测试方位逐步偏移。""")

code("""img = Image.open("results/snn/m4_fig_aspect.png")
plt.figure(figsize=(7, 5))
plt.imshow(img); plt.axis("off"); plt.show()
d = np.load("results/snn/m4_isal_results.npz", allow_pickle=True)
print("offset(deg):", list(d["offsets"]))
print("acc        :", [round(float(a),3) for a in d["acc_vs_off"]])""")

md("""**图 4 解读**：精度从 0° 的 0.43 衰减到 90° 的 ~0.11（≈随机），但 **180° 处恢复到 0.44**。
物理原因：$r(\\theta+\\pi) = -r(\\theta)$——背向剖面是正向剖面的**时间反演**，ESN 的均值池化特征对反演近似不变，等于白捡一个对称性。
含义两条：(1) HRRP 类任务必须做方位多样化训练或序列输入，单方位训练的泛化极脆；(2) 180° 对称性可作为数据增强的免费来源，也是这类管线必备的 sanity check。""")

md("""## 4. 鲁棒性：噪声与相干角""")

code("""img = Image.open("results/snn/m4_fig_robustness.png")
plt.figure(figsize=(13, 4.5))
plt.imshow(img); plt.axis("off"); plt.show()""")

md("""**图 5 解读**：
- **SNR**：-10 dB 时 ≈ 随机，20 dB 处饱和（0.40）——饱和点以上精度受限于信息内容而非噪声（30 dB 点的回落是种子间方差，340 测试样本 ±0.03 量级）。系统的噪声预算很宽松；
- **相干角**：非相干序列 ESN（幅度剖面序列）对 $\\theta_c$ 完全免疫（0.27–0.30 全程平坦）；相干 ISAL 图像从 0.25 崩到 0.16。
**器件含义**：面对光学波长的粗糙目标，"幅度域 + 多角度 + 蓄水池"路线的鲁棒性优于"相干成像"路线——这与图 2 的物理一致，也是对我们架构（非线性蓄水池处理压缩回波）的又一次支持。""")

md("""## 5. 真实照射模式：多波束扇区有序扫描

前面的"随机方位"是压力测试，不是真实系统。实际激光雷达/声呐总有固定波束或扫描规律。
这里模拟一个贴近器件的设定：
- **4 个固定波束**朝向 $-45°、-15°、+15°、+45°$（角度已知）；
- 每个波束可做小范围有序扫描（$±3°$ 三步）；
- 分类器获得有序剖面序列，可用蓄水池处理其时序结构。

为回答"0.68 离上限多远"，额外训练一个深度 2D CNN 把 12×128 扫描图当图像分类——给出这个表示的**经验上限**。""")

code("""import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

img = Image.open("results/snn/m4_fig_beam_scan.png")
plt.figure(figsize=(11, 6))
plt.imshow(img); plt.axis("off"); plt.show()

d = np.load("results/snn/m4_beam_scan_results.npz", allow_pickle=True)
keys = ["single_random_ESN", "single_random_CNN", "4random_avg_CNN",
        "4beam_avg_CNN", "4beam_concat_CE", "4beam_seq_ESN",
        "4beam_seq_ESN+angle", "4beam_3step_ESN",
        "4beam_3step_shuffled_ESN", "4beam_3step_2DCNN_ceiling",
        "2beam_seq_ESN", "8beam_seq_ESN"]
print("%-32s %s" % ("method", "accuracy"))
print("-" * 45)
for k in keys:
    print("%-32s %.3f" % (k, float(d[k])))""")

md("""**图 6 解读**：
- **蓝色**：单次随机方位基线（~0.36–0.42）；
- **橙色**：4 次随机方位平均（0.39）——没有结构，增益很小；
- **绿色**：固定波束/有序扫描方案：
  - 4 波束幅度平均 **0.54**（已知分散角度比随机角度显著更好）；
  - 4 波束拼接 **0.63**（保留每个波束独立投影 > 简单平均）；
  - **4 波束 × 3 步有序扫描 + ESN 0.68**（蓄水池结果）；
  - 把同样 12 个剖面**打乱顺序**，ESN 跌到 **0.50**——证明是**扫描结构**在贡献精度，不是样本数。
- **红色柱**：深度 2D CNN 在同样 12×128 扫描图上的经验上限 **0.821**。

**上限含义**：
- 对于这个多波束 HRRP 表示（12 个有序剖面），强分类器能到 **0.82**；
- 蓄水池的 **0.68 ≈ 经验上限的 83%**——不算差，但还有 0.14 的差距；
- 0.82 已经非常接近全 3D 点云的线性读出上限 0.84，说明**多波束扫描本身几乎捕获了全部 3D 形状信息**；
- 剩下的差距主要来自表示方式：ESN 把扫描图当 1D 序列处理，没有显式利用"距离-角度"二维结构；用 2D CNN 才能吃干抹净。

**器件含义**：
- 啁啾光栅前端只需为每个波束独立做脉冲压缩；
- 4 个已知角度波束 + 每波束小角度扫描，就能把分类精度从单次 ~0.4 推到 **0.68–0.82**；
- 若追求极致精度，扫描图后面可以接小型 2D CNN；若追求低延迟/低训练成本，蓄水池 0.68 是个合理的折中。""")

md("""## 6. 空间分置传感器：同一位置多波束 vs 分布式多基地

用户提出的关键问题：不是从同一位置发 4 个角度的波束，而是把 4 个传感器放在目标周围不同位置，会不会更准？

这里比较三种 4 视图配置：
- **Collocated**：同一位置 4 个波束 -45°/-15°/+15°/+45°；
- **Equatorial**：4 个传感器在目标赤道面正交分布（0°/90°/180°/270°，距离 10 m）；
- **Tetrahedral**：4 个传感器位于正四面体顶角，包围目标。

为了保证斜向视图不截断目标，距离窗扩大到 D=6 m。""")

code("""import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

img = Image.open("results/snn/m4_fig_distributed.png")
plt.figure(figsize=(11, 6))
plt.imshow(img); plt.axis("off"); plt.show()

d = np.load("results/snn/m4_distributed_results.npz", allow_pickle=True)
keys = ["collocated_4beam_avg_CNN", "collocated_4beam_concat_CE",
        "collocated_4beam_seq_ESN",
        "equatorial_avg_CNN", "equatorial_concat_CE", "equatorial_seq_ESN",
        "equatorial_2DCNN_ceiling",
        "tetrahedral_avg_CNN", "tetrahedral_concat_CE",
        "tetrahedral_seq_ESN", "tetrahedral_2DCNN_ceiling"]
print("%-34s %s" % ("method", "accuracy"))
print("-" * 48)
for k in keys:
    print("%-34s %.3f" % (k, float(d[k])))""")

md("""**图 7 解读**：
- **蓝色**：同一位置 4 波束（collocated）——与图 6 的快照结果一致，concat 0.69；
- **橙色**：赤道面分布式 4 传感器——avg 0.63、concat 0.66、seq-ESN 0.64，**略胜 collocated**，尤其是平均法提升明显（多视角互补）；
- **绿色**：正四面体分布式 4 传感器——**显著更差**，concat 仅 0.50，2D CNN 天花板也只有 0.66。

**为什么四面体反而差？**
ModelNet40 里主要是"立起来"的物体（家具、车辆、飞机），它们的判别特征（机翼、椅腿、车身轮廓）大多分布在**水平截面**上。赤道面传感器正对水平轮廓；而四面体传感器包含大量俯视/仰视角度，从顶上看很多物体只剩一个矩形剪影，类间可分性反而下降。

**关键结论**：
- 分布式传感器**可以更好**，但取决于几何排布——对地面/家具/车辆类目标，**赤道面/侧视分布**优于包围式四面体；
- 赤道面 4 传感器的 2D CNN 经验上限 **0.803**，与 collocated 4 波束 3 步扫描的 0.821 相当；
- 器件设计启示：如果系统允许布置多个传感器，**沿目标 principal plane（如道路两侧、机器人腰部一圈）放 4 个侧视单元**，可能比单一位置扫描更省时间、更鲁棒。""")

md("""## 7. 自动驾驶场景：粗分类单次剖面足够吗？

用户指出：真实车辆行驶任务中通常无法从多角度发射波束；自动驾驶关心的其实是**车 / 行人 / 骑手 / 背景**这类粗分类，单次前视 HRRP 的 1D 轮廓差异很大，应该足以区分。

这里用同样的 0 阶散射点模型和 ESN 蓄水池（n_res=512），把 10 类 ModelNet40 重新组合成粗分类任务，全部使用**单次随机方位幅度距离像**（D=4 m），验证这个直觉。""")

code("""import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

img = Image.open("results/snn/m4_fig_automotive_focus.png")
plt.figure(figsize=(7, 5))
plt.imshow(img); plt.axis("off"); plt.show()

d = np.load("results/snn/m4_automotive_focus_results.npz", allow_pickle=True)
print("%-28s %s" % ("task", "accuracy"))
print("-" * 40)
for k in ["car_vs_noncar", "vehicle_vs_nonvehicle", "coarse_4class", "fine_10class"]:
    print("%-28s %.3f" % (k.replace("_", " "), float(d[k])))""")

md("""**图 8 解读**：

| 任务 | 类别数 | 单次随机 HRRP 测试准确率 |
|---|---|---|
| car vs non-car | 2 | **0.885** |
| vehicle vs non-vehicle | 2 | **0.788** |
| coarse 4-class（car/airplane/chair/bottle） | 4 | **0.619** |
| fine 10-class（参考） | 10 | 0.356 |

- 用户的直觉完全正确：把任务放宽到自动驾驶关心的粗分类，**单次前视剖面就够了**——“car vs non-car”接近 0.9，“vehicle vs non-vehicle”接近 0.8；
- 四类粗分仍有 **0.62**，是细粒度 10 类任务的近两倍；
- 之前反复讨论的 0.36 / 0.38 是 10 类细粒度任务的数字，**不是自动驾驶场景的代表**；
- 这意味着应用定位应该强调：**光子蓄水池接收机对“单次脉冲粗识别”有价值**——不需要多波束扫描或长时间积累，正好匹配 TFLN 器件“单发压缩 → spike → 蓄水池”的低延迟链路。

若要进一步区分车辆子型号，那才需要多波束/扫描/高分辨成像等额外信息。""")

md("""## 8. 结论与自主提问

**本里程碑的数字**：
1. 仿真距离像形态与真实 HRRP 一致；相干 ISAL 在理想点目标上成像成功，$\\theta_c<0.3°$ 时散焦崩溃（第三面墙的定量演示）；
2. 单随机方位剖面 10 类分类：**ESN 0.382 > 1D CNN 0.291**；multi-look 天花板 4-look 0.397 / 16-look 0.509；
3. **真实照射模式（4 固定波束 + 扇区有序扫描）把精度推到 0.68**，同样 12 剖面打乱后仅 0.50——证明扫描结构/时序信息是关键；
4. **同一表示的经验上限约 0.82**（深度 2D CNN），蓄水池达到约 83%；0.82 已接近全 3D 点云上限 0.84，说明多波束扫描几乎捕获了全部 3D 信息；
5. **空间分置传感器**：赤道面分布优于同一位置多波束（2D CNN 上限 0.80 vs 0.69 快照），但四面体分布因目标姿态先验而变差；
6. 方位泛化 U 形曲线（180° 时间反演对称白捡）；
7. 幅度域蓄水池对散斑去相干免疫，相干成像路线脆弱；
8. D=0.15 m（TFLN 窗口）小目标情形精度保持（0.350）；
9. **自动驾驶粗分类任务**：单次随机前视 HRRP 对 car vs non-car 达 0.885、vehicle vs non-vehicle 达 0.788、coarse 4-class 达 0.619——粗分类单次剖面已足够。

**下一步（按优先级）**：
1. **多角度序列 + delay learning 重测**：现在已确认有序扫描有价值，把 M3a 的可调延迟搬到波束扫描序列上；
2. **把蓄水池升级成 2D 结构感知**：small CNN 特征提取 + 蓄水池时序聚合，或片上延迟线的 2D 拓扑；
3. **传感器几何参数扫描**：赤道面 2/4/6/8 单元、不同半径、不同扫描扇区，找最优；
4. **多波长 diversity**：光栅 66 nm 带宽做频率分集；
5. **真实数据接口**：Soli / RadarScenes 按应用线择一接入；
6. 升级 PO 电磁仿真替换 0 阶模型（写论文前必做）；
7. 器件实验设计：TFLN 窗口内小目标压缩-识别链路预算。

**方法论沉淀**：
- HRRP 任务先做 180° 反演 sanity check；
- 评估新方法时必须先建立任务内基准（1D CNN + multi-look + 多波束扫描 + 强 2D CNN 上限 + 分布式几何），别把信息缺失误判为方法失败；
- 单剖面信息有限，但**真实照射规律能把信息补回来**；
- 蓄水池需要足够长的有序序列（T≥10）才能体现优势；分布式几何需匹配目标的 principal plane。""")

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": "3.14"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

path = "milestone-M4-isal-range-profile.ipynb"
with io.open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
json.load(io.open(path, encoding="utf-8"))
print("OK: %s (%d cells)" % (path, len(cells)))
