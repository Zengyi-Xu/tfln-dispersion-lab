# -*- coding: utf-8 -*-
"""Build milestone-M1-photonic-chain.ipynb (Jupyter summary document)."""
import io
import json

cells = []


def md(text):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    })


def code(text):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    })


md("""# 里程碑 M1：光子处理链综合仿真（FDTD → 匹配滤波 → spike → 蓄水池慢读出）

**日期**：2026-09-20 · **脚本**：`lumerical/comprehensive_simulation.py`（约 90 s）

## 本节要回答的问题

> 雷达/LiDAR 回波经啁啾光栅匹配滤波后天然是 ps 级脉冲串。电子电路只能读 ns 级信号。
> **能否用光子蓄水池在 ps 时标上处理这些脉冲，然后用慢光电积分读出结果？**

这个问题决定整个架构的成败：如果慢读出丢失了时序信息，就必须让光栅本身提供 ns 级色散（TFLN 损耗不允许）；如果蓄水池能把时序模式"冻结"成空间模式并保持到 ns 级，电域带宽压力就被解除。

## 仿真链

1. **FDTD 校验**：直线波导（T≈1）+ 啁啾光栅（反射平台、群延迟、色散）
2. **匹配滤波**：用实测 $\\tau_r(\\lambda)$ 重建谱相位，扫描输入啁啾找最佳压缩
3. **LiDAR→spike**：匹配啁啾 + 多目标回波 → 光栅压缩 → 阈值化 spike train
4. **蓄水池慢读出**：等能量等质心三类任务 + 漏电积分读出 + 消融/扫描""")

md("""## 1. FDTD 器件校验

FDTD GUI 已确认正常启动（`hello_fdtd.py`）。啁啾光栅来自 `chirp2d.npz`（2D TEz，有效折射率近似）。""")

code("""import numpy as np

d = np.load("lumerical/results/comprehensive_summary.npz")
print("反射平台宽度: %.1f nm" % float(d["fdtd_platform_width_nm"]))
print("色散 D (平台线性拟合): %.4f ps/nm" % float(d["fdtd_D_ps_per_nm"]))
print("平台群延迟摆幅: %.2f ps" % float(d["fdtd_delay_swing_ps"]))
print("phi2 = d tau/d omega = %.3e s^2/rad" % float(d["phi2"]))
print("匹配啁啾率 = %.3e rad/s^2" % float(d["chirp_rate_matched"]))""")

md("""**合理性核对**：D ≈ 0.051 ps/nm 与几何预言偏差 <10%；平台宽 66 nm 覆盖设计啁啾区；群延迟摆幅 3.2 ps 与 L=250 µm、n_g≈2.1 一致。

## 2. 时间透镜 / 匹配滤波

物理：TFLN 相位调制器施加 $\\phi(t)=Ct^2/2$，稳相近似下等效于给脉冲加谱啁啾 $\\gamma\\approx-1/C$。因此扫描输入啁啾 $\\gamma$ 就是在扫描调制器驱动波形——**同一个被动光栅可匹配不同啁啾参数的回波**（可调匹配滤波）。""")

code("""from PIL import Image
import matplotlib.pyplot as plt

img = Image.open("lumerical/results/report_matched_filter.png")
plt.figure(figsize=(10, 9))
plt.imshow(img)
plt.axis("off")
plt.show()

print("变换极限脉宽 0.068 ps → 纯光栅展宽 0.230 ps → 匹配压缩 0.130 ps")
print("注：本例输入脉宽已接近变换极限，压缩比受输入带宽限制；")
print("    对更长啁啾，压缩比 = 时间带宽积（见第 3 节 22x）。")""")

md("""## 3. LiDAR 回波 → spike train

四个点目标（延迟 0.5/1.5/3.0/4.5 ps，幅度 1.0/0.6/0.4/0.3）的啁啾回波在时域完全重叠，经光栅匹配滤波后分离为压缩脉冲，阈值化后即为 spike train。""")

code("""img = Image.open("lumerical/results/report_lidar_to_spike.png")
plt.figure(figsize=(10, 9))
plt.imshow(img)
plt.axis("off")
plt.show()

print("啁啾时长 %.2f ps, 压缩脉宽 %.3f ps, 压缩比 %.1f" % (
    float(d["lidar_T_chirp"])*1e12, float(d["lidar_pulse_fwhm"])*1e12,
    float(d["lidar_T_chirp"])/float(d["lidar_pulse_fwhm"])))""")

md("""**尺度声明（重要）**：当前 250 µm 光栅的匹配啁啾时长仅 ~3.4 ps，对应 mm 级目标间距。
真实 LiDAR 的啁啾为 ns–µs 级，需要延迟摆幅同样为 ns 级的色散器件——差距约 3000 倍。
这是后续 spiral/级联/长器件工作的直接动机，也是本架构最大的物理约束。

## 4. 光子蓄水池 + 慢读出（核心结果）

**任务设计（刻意为难慢读出）**：三类场景的总光能（∫功率）和质心时间完全相同：
- 类 0：1 个 spike（t=2.0 ps，幅度 1.0）
- 类 1：2 个 spike（t=1.5/2.5 ps，幅度 0.5）
- 类 2：3 个 spike（t=1.4/2.0/2.6 ps，幅度 1/3）

任何只测总能量或平均时间的慢读出都无法区分它们（理论上限 = 随机 33%）。
只有蓄水池的非线性（tanh 饱和，模拟 QD 激光器/MRR 节点）才能把时序模式转成可积分的空间特征。""")

code("""print("基线 1 - 直接能量积分（无蓄水池）: %.3f  <- 约等于随机" % float(d["direct_acc"]))
print("基线 2 - 快采样读出（32 点 ADC）:   %.3f" % float(d["fast_acc"]))
print("蓄水池 + 漏电积分慢读出:           %.3f" % float(d["leaky_acc"]))
print("消融 - 线性蓄水池（无 tanh）+ 慢读出: %.3f  <- 证明非线性必需" % float(d["linear_acc"]))""")

md("""### 4.1 三类场景的蓄水池状态

下图左侧是三类等能量等质心的输入 spike train（肉眼和慢积分都无法区分），
右侧是 40 抽头延迟蓄水池的状态图——时序模式被展开成清晰可分的空间模式。""")

code("""img = Image.open("lumerical/results/report_reservoir_examples.png")
plt.figure(figsize=(10, 9))
plt.imshow(img)
plt.axis("off")
plt.show()""")

md("""### 4.2 慢读出窗口：答案能存活多久（关键图）

读出用漏电积分模型 $v_i = \\sum s_i(t') e^{-(t_{\\rm read}-t')/\\tau_{\\rm leak}} dt$ + 常数读出噪声。
这模拟真实慢光电探测器：信号随读出延迟指数衰减，噪声不变，SNR 随之下降。""")

code("""img = Image.open("lumerical/results/report_readout_delay.png")
plt.figure(figsize=(9, 5))
plt.imshow(img)
plt.axis("off")
plt.show()""")

md("""**结论**：准确率在读出延迟 ≈ τ_leak 之前保持 ~1.0，之后才退化。
τ_leak = 5 ns 时读出窗口超过 10 ns，完全覆盖常规跨阻放大器/ADC 时标。
**这正是问题想要的答案：ps 光处理 + ns 电读出的时标分离成立。**

### 4.3 蓄水池规模与鲁棒性""")

code("""fig, axes = plt.subplots(1, 3, figsize=(16, 4))
for ax, fname, ttl in zip(axes,
    ["report_tap_count.png", "report_jitter.png", "report_noise.png"],
    ["抽头数", "时序抖动", "加性噪声"]):
    ax.imshow(Image.open("lumerical/results/" + fname))
    ax.set_title(ttl)
    ax.axis("off")
plt.tight_layout()
plt.show()""")

md("""- **抽头数**：~20–40 个延迟抽头即饱和。对应几毫米光栅上 20–40 个波长通道或电极分段，器件规模现实。
- **抖动**：绝对抖动达 ~0.1 ps（与脉宽相当）时开始退化。光栅 ripple 必须压低到这个量级以下。
- **噪声**：加性噪声达信号峰值 ~30% 前性能基本不变，蓄水池对器件噪声有冗余容忍度。

## 5. 本次仿真发现并修正的问题（方法论价值）

| 问题 | 后果 | 修正 |
|---|---|---|
| v1 慢积分直接长时间平均蓄水池状态 | 积分越久准确率越低（错误结论） | 改为漏电积分读出（答案存活 τ_leak），结论反转 |
| 分类特征量纲 ~1e-13，sklearn 默认 L2 正则直接压零权重 | 一切慢读出准确率都=随机 | `StandardScaler` 标准化 |
| v1 任务三类能量/质心不同 | 慢积分本身就能区分，证明不了蓄水池必要性 | 改为等能量等质心任务，直接积分基线确实随机 |
| 群延迟摆幅用全谱 min/max | 混入带边伪影 | 只在 R>0.9 平台上线性拟合 |

## 6. 本节结论与下一步

**结论**：在理想数字模型下，"光栅压缩（ps）→ spike → 蓄水池（ps 内部延迟）→ 漏电积分慢读出（ns）"链路成立，且非线性蓄水池是必不可少的环节。

**遗留的硬问题**（→ M3 自主提问仿真）：
1. 啁啾时长尺度差 3000 倍——spiral/级联光栅的损耗-延迟-带宽三角定量？
2. 蓄水池的延迟抽头用真实 TFLN 波导（损耗+色散）实现时性能如何？
3. 真实 spike 来自 QD 激光器阈值动力学而非理想阈值——噪声和抖动会如何？
4. 这套蓄水池能否处理真实分类任务（ModelNet40 点云）？（→ M2）""")

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.14.6"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

with io.open("milestone-M1-photonic-chain.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("wrote milestone-M1-photonic-chain.ipynb with %d cells" % len(cells))
