# 光子伊辛机 × 片上非线性 × 我们平台：文献精读与相容性评估

> 2026-09-26 晚，小白（338H）整理。输入：用户提供的 Wan 组（KAUST IPL）两篇草稿 PDF
> + 通宵文献检索 + 我们在 simulations/06 里的第一手复现检验。
> 关联文档：docs/reservoir_computing_101.md（RC 原理教程）。

---

## 一、Wan 组两篇草稿精读

### 1. QD 激光器伊辛机（"Fully Integrated Quantum Dot Laser Ising Machine"）

**一句话**：把量子点（QD）激光器的光-电流（LI）曲线当作伊辛自旋的非线性激活函数，
激光器同时兼任光源，非线性核 + 光源单片集成，核心面积仅 ~0.25 mm²。

关键数字：
- 全连接 300 spins / 稀疏 22,500 spins（150×150 方格子）
- Max-cut 质量：G22（2000 点）达 best-known 的 98.35%；G67（10000 点）96.52%
- 更新速度目前 1 kHz（受限于实验室 SMU 仪表，器件本身带宽 5.7 GHz）
- 应用演示：5 路可编程光路由（10×10 MZM mesh，5×32 Gbit/s NRZ，路损差 <0.58 dB）

动力学（其 Eq.2）：x[k+1] = f_nl(αx[k] + βJx[k] + η[k])，f_nl = LI 曲线奇延拓，
η 为"梯度启发"的注入噪声（帮助逃离局域极小）。

**他们自认的两个短板**（= 别人可以切入的缺口）：
1. 线性耦合项 ΣW_ij x_j 目前在**电域**算——想找集成 EAM 把它挪到光域；
2. 更新率被仪表卡在 1 kHz，离 GHz 差三个数量级。

### 2. MRR 光互联单元 PIU（"Scalable Microring-Based Interconnects..."）

**一句话**：4×4 微环交换 + 可编程均衡微环 + FPGA 三段式 PID 闭环锁定，
解决多核模拟光子计算之间"模拟幅度保真"的传输问题。

关键数字：均衡后通道功率差 <0.2 dB；10.3 bit 等效控制精度；22 °C 温漂下 SNR 波动
<0.5 dB；ResNet-18 硬件感知仿真精度从 54.33% 恢复到 ~94.6%。

注意：这篇**不是伊辛机**，是他们布局"多核光子计算簇"的互联/信号调理层。
它说明 Wan 组的系统观：非线性核（Ising/计算）+ 光源 + 互联，三位一体。

---

## 二、光子伊辛机版图（交叉检验后）

主要依据：[Aadhi et al., "Photonic Ising machines toward and beyond a million spins",
arXiv:2607.13446 (2026)](https://arxiv.org/abs/2607.13446)（McMahon/Shastri/Yamamoto
等合写的 perspective），辅以 [Mohseni et al., Nat. Rev. Phys. 4, 363 (2022)]。

| 路线 | 代表 | 自旋规模 | 非线性来源 | 集成度 |
|---|---|---|---|---|
| OPO-CIM（光纤时分管） | NTT/Stanford, Science 2016; Sci. Adv. 2021 | 10⁴–10⁵ | χ² 简并 OPO | 公里级光纤腔，难集成 |
| SLM 自由空间 | Pierangeli PRL 2019 | 10⁴+ | 空间光调制 | 自由空间 |
| OEO 光电振荡器 | Böhm Nat. Commun. 2019; Cen LSA 2022 | 10²–4×10⁴ | MZM+PD+DSP | 分立器件 |
| **级联 TFLN MZM 时分环** | [Al-Kayed et al., Nature 648, 576 (2025)](https://arxiv.org/abs/2509.09581) | 稀疏 41,000，200 GOPS | **TFLN MZM** | 半集成 |
| **TFLN 片上光电 IM** | [Li et al., ACS Photonics 11, 1703 (2024)](https://pubs.acs.org/doi/abs/10.1021/acsphotonics.4c00003)（中大刘洁/余思远组） | 片上可扩展 | TFLN 调制器混合集成 | 片上 |
| **TFLN χ² 纳米光子 OPO** | [Gray/Sekine/Ledezma/Marandi, arXiv:2405.17355 (2024)](https://arxiv.org/html/2405.17355v1) 大规模时分管 OPO | 大规模阵列演示 | **TFLN χ²** | 纳米光子片上 |
| QD 激光器 LI | Wan 组草稿 | 22,500 | QD 激光器 LI | 单片 III-V |

**交叉检验结论**：TFLN 在伊辛机里已有三条独立路线（EO 调制器时分环、片上光电 IM、
χ² OPO-CIM），我们的 MZM sin² 非线性做激活的路线并不孤独——Al-Kayed 2025 已经用
级联 TFLN MZM 做到了 OEO 类伊辛机的最大自旋数。这既是利好（路线被验证）也是警示
（先发优势在别人手里，我们需要差异化：色散元件/慢读出/和 RC 的统一）。

### 我不懂 → 自己复现检验的点（simulations/06 的第一手结果）

1. **α（自反馈）与 β（耦合）的平衡**：草稿里 W = αI − βJ 一笔带过。我用 06 复现发现
   α=2 时自反馈淹没耦合项，系统退化成随机分岔（E/E_BK ≈ 0.3）；α=0.5、β≈2 时
   tanh/sin/clip 三种激活都追到 E/E_BK ≈ 1.05（略超 SA 参照）。**工作点在 α<1、
   β 足够大**——这是任何器件实现都必须满足的动力学窗口。
2. **激活函数奇对称性的作用**：所有论文都"奇延拓"但少解释。本质：自旋 ±1 对称
   （Ising 哈密顿量在全局自旋翻转下不变），激活函数奇对称保证动力学不破缺该对称。
   sin（MZM 正交偏置）天然奇对称，LI 曲线必须人为奇延拓。
3. **QD 激光器 LI 曲线的阈值死区**：06 里 laser 臂在小 α·β 区塌缩到全零态
   （|z|<0.25 时输出恒 0）——KAUST 草稿用"线性+饱和区"回避了这点，但死区对
   弱耦合问题是真实风险。相比之下我们 MZM 的 sin 过零点光滑，无死区。**这是我们
   相对 QD-LI 路线的一个真实优点，值得写进报告。**
4. **噪声退火**：所有平台都用"梯度启发噪声"逃逸局域极小；06 确认初始噪声幅度
   是成功率的关键旋钮（全量扫描在 7945HX 上跑）。

### Böhm 2019（OEO-CIM 原始论文）方程级交叉检验

读了 [Böhm et al., Nat. Commun. 10, 3538 (2019)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6687753/)
全文（开放获取），其 Eq.2–3 为：

```
x_n[k+1] = cos²(f_n[k] − π/4 + ζ_n[k]) − 1/2      (Eq.2, MZM 强度非线性)
f_n[k]   = α·x_n[k] + β·Σ_m J_mn·x_m[k]            (Eq.3, 自反馈+耦合)
```

交叉检验要点：

1. **我的 06 脚本 sin 臂 ≡ Böhm 的 cos² OEO 非线性**：cos²(z−π/4)−1/2 = ½sin(2z)，
   即 MZM 在 −π/4 偏置下就是奇对称正弦饱和。所以 06 的"sin 臂追到 E/E_BK≈1.05"
   可直接表述为"TFLN MZM OEO-CIM 动力学在这些实例上追平/略超 SA 参照"。
2. **分岔阈值解析解吻合**：x' = ½sin(2αx) ≈ αx（小信号），pitchfork 分岔恰在 α=1，
   与 Böhm 的线性稳定性分析一致；我的 06 网格 α∈[0.3,1.0] 跨分岔点（sin 臂斜率
   1.2 → 分岔 α≈0.83），覆盖正确。
3. **KAUST 草稿的 W = αI − βJ 与 Böhm Eq.3 同构**（符号约定差一个 J 的负号，
   取决于 J 用反铁磁 +1 还是 −1 编码）。
4. **DOPO-CIM 近阈值方程**（Böhm Methods Eq.4–5）化简为 pitchfork 标准形
   dc/dt = (p−1−c²)c——所有分岔式伊辛机共享同一标准形，这就是"换激活函数
   只换系数不换物理"的理论根基，也是 06 多臂可比性的依据。
5. Böhm 用**恒定**小噪声（σ=0.04）+ 不模拟退火也能解小图；KAUST 用**退火**噪声
   解大图。06 采用退火方案，与后者一致。
6. 工程细节值得记：Böhm 明确指出偏置符号反了只需要反转 α、β 符号
   （cos² 偶对称、斜率奇对称）——这类"偏置-符号"对应关系在我们将来做实验时是
   常见坑。

---

## 三、RC「不好用」争议的文献定标

1. [Yan et al., "Emerging opportunities and challenges for the future of reservoir
   computing", Nat. Commun. 15, 2056 (2024)](https://www.nature.com/articles/s41467-024-45187-1)
   ——RC 领域最权威的展望（558 次引用）。挑战清单：超参敏感、缺乏硬件友好理论、
   大规模任务竞争力不足。
2. **Zhang & Cornelius 的 Catch-22**（2023，
   [报道](https://www.innovationnewsnetwork.com/what-are-the-limitations-to-reservoir-computing/37814/)）：
   ① RC 预测混沌系统需要 warmup 时间 ≈ 动力学本身的时间尺度；
   ② NGRC 必须把非线性形式"预先偷渡"进模型。——这解释了同事口中的"不好用"：
   RC 的超参/结构敏感是公认痛点。
3. [RC 作光子前处理器 + DNN 读出（Frontiers, 2022）](https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2022.1051941/full)
   ——混合路线：光 RC 做时序展开，数字 DNN 做精细读出。这是"RC 不是取代深度学习
   而是前置特征提取"的折中定位。
4. 我们自己的 04/05 数据（quick 档）：RC 在信道均衡小预算段领先（0.66 vs MLP 0.48），
   静态任务落后（0.71 vs 0.94）——与文献判断一致：**领域特异，不是潜力死刑**。

---

## 四、与 Wan 组研究的相容性评估

Wan 组（KAUST IPL）版图：QD 激光器 on Si（老本行，UCSB/Intel 背景）、
光子计算（QD comb 边缘计算，Adv. Photonics 2026）、Ising 机（草稿 1）、
多核互联 PIU（草稿 2）。**他们有源（激光器），我们无源+调制（TFLN 色散、EO）。**

相容性矩阵：

| 我们的资产 | 与 Wan 组的接口 | 相容性 |
|---|---|---|
| 啁啾布拉格光栅 GD/κ 引擎（C1–C17 已验证） | 他们 PIM 的线性耦合目前电域实现，想找光域方案——色散元件可做光学线性/延迟层 | **高**：补他们的短板① |
| TFLN MZM sin² 非线性模型（03/05/06） | 与 Al-Kayed 的级联 TFLN MZM OEO-Ising 同族；我们的 sin 无死区 vs 他们 QD-LI 有死区 | **高**：差异化卖点 |
| 慢读出结论 C13（低速读出无损） | 他们更新率被卡在 1 kHz 恰因读出链——C13 提供"慢读出不掉性能"的物理依据 | **中高**：理论支持他们换便宜读出 |
| SCR 延迟环 RC（04：掩码是刚需） | QD comb 多波长源 + 我们的时分环 = WDM×TDM 混合蓄水池 | **中**：需要 comb 源，我们没有 |
| SNN 脉冲链（M1–M4） | 他们不做 SNN | **低直接相容**：但 PIU 的模拟保真传输对任何模拟计算都通用 |

**给用户的建议**：与 Wan 组最自然的合作切口是"用我们的 TFLN 色散/光栅器件做他们
PIM 的光域线性耦合层"，或"我们的 EO 激活 + 他们的 QD comb 源做混合集成 OEO-Ising"。
纯 RC/SNN 方向与他们交集小，不构成冲突也不构成合作点。

---

## 五、片上非线性 × 新方向：机会清单（按我们平台可达性排序）

1. **MZM sin² 作 Ising 激活**（06 已在仿真）：差异点 = 无死区 + TFLN 高带宽。
2. **MZM sin² 作 RC 节点**（03/04/05 已在仿真）：输入掩码刚需是 04 的新发现。
3. **色散元件作光学线性层**（我们的独特资产）：把啁啾光栅的 GD 用于"模拟矩阵/
   延迟嵌入"——连接 Ising（耦合层）与 RC（掩码/记忆层）两个世界。
4. **TFLN χ² OPO 路线**（NTT/Marandi）：物理上最优雅的 CIM，但需要 PPLN 工艺，
   我们当前是 EO 平台，列为远期。
5. **全光 ReLU 等深学激活**（Marandi, Nanophotonics 2023）：与我们 sin² 互补，
   静态任务我们已用 04-T4 证明不该硬上 RC。
6. **光电混合读出**（RC+DNN）：工程上最现实的落地方案。

## 六、待下载文献（ACS/Nature 付费墙，请用户明早帮下）

见同步文件夹 DOWNLOAD_REQUESTS_20260926.md。
