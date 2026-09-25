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

### Marandi 组 TFLN 时分管 OPO 芯片精读（arXiv:2405.17355 全文）

Gray/Sekine/Ledezma/Li/…/Marandi（Caltech，[全文](https://arxiv.org/html/2405.17355v1)）
——这是**片上 TFLN 伊辛机路线最强的硬件平台**，必须作为对标对象吃透：

- **规模与指标**：单芯片 53 cm 螺旋腔（FSR 250 MHz，往返 4 ns），EO comb 泵浦
  （1045 nm，ps 脉冲，17.5 GHz 重频 = 往返时间的 N 次谐波），实现 **N=70 个
  相互独立**的时分管 OPO；阈值仅数 pJ/脉冲（色散工程 PPLN 波导）——比任何
  其它平台的非线性强几个量级。N=40 已用干涉统计严格验证独立性。
- **Ising 自旋**：简并 regime 下信号相位被锁定为二值 |0⟩/|π⟩（Eq. 2:
  ϕ_p−2ϕ_s=π/2）——天然 Ising 自旋；用非平衡 MZI + Bernoulli 统计
  （快慢两种探测器，2 s 采 19,999 次迭代）证实每次振荡相位由真空涨落随机播种。
- **关键缺口 = 我们的机会**：全文只演示了**独立**振子；可编程全互联耦合
  （Fig. 5 主腔+N+1 位存储腔+EOM 编程 MZI 方案）**尚停留在 proposal**，没有实验。
  即"片上 χ² 自旋有了，片上耦合网络还没有"。谁先做出低损耗、可编程的片上
  耦合层，谁就补上了这条路线的最后一公里。我们的色散/延迟器件恰好可以做
  固定拓扑耦合层（不需要全可编程也有价值，如稀疏图、链式图）。
- **速率上限**：受限于泵浦重频与探测电子学（25 GHz PD）；他们自承更快的
  片上泵浦源可继续放大 N。
- 前身对照：Okawachi et al., Nat. Commun. 11, 4119 (2020)（SiN 微腔耦合 DOPO
  自旋玻璃，空间复用，N 小）——Marandi 这条 TDM 路线是"一个物理腔当时分管用
  N 个"的可扩展答案。

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

### 规模动机与关键对照数字（百万自旋综述挖掘）

- **为什么需要百万自旋**：TSP 1000 城市 ≈ 10⁶ 自旋；HP 格子蛋白质折叠
  200 氨基酸/100×100 格子 ≈ 10⁶ 自旋。现有光子 IM 全在 10⁴–10⁵ 量级，
  差 1–2 个数量级。
- **数字对手盘**：多板 FPGA CMOS 退火机已到 1.3×10⁶ 自旋；25×H100 集群
  可做百万变量 MVM（功耗数十 kW）。光子 IM 要赢必须赢在能耗/延迟而非规模。
- **综述 Table 1 里 TFLN 级联 MZM 机（Al-Kayed 2025）的条目**：稀疏 4.1×10⁴
  自旋、单步延迟 1.9 ms、可重构耦合——这是 TFLN 路线当前的性能锚点。
- **四大公认瓶颈**：scalability / connectivity / time-to-solution / solution
  accuracy。光电架构的 TTS 被 ADC/DAC 转换和存储带宽卡死——**这正是我们
  C13（慢读出无损）结论可能贡献的地方：若物理上慢读出不掉解质量，
  光电 IM 的转换开销预算可以大幅放松。**

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
5. **商业化动向（重要更正）**：之前说"商业化产品里没有 RC"需要细化——
   [Quantum Computing Inc. 于 2026 年 4 月推出 NeuraWave](https://quantumcomputingreport.com/quantum-computing-inc-launches-neurawave-photonic-platform-for-edge-ai-inference/)：
   PCIe 卡形态的光子 RC 平台，**恰好基于 TFLN 集成光子**，定位边缘 AI/时序推理。
   注意：QCi 是争议性公司（市值驱动叙事浓，独立技术验证少），NeuraWave 的实测
   性能没有同行评议背书。**正确表述**：学术界主流片上色散/衍射网络确实不用 RC，
   但产业端已有人把光子 RC 做成产品形态在卖——且用的正是我们的材料平台。
   这把我们的问题从"RC 有没有前途"细化为"RC 在哪些负载上是帕累托最优"。
6. 顺带发现：[Lightelligence PACE 3 在 WAIC 2026 展示 256×256 光子矩阵
   推理卡](https://pandaily.com/lightelligence-optical-computing-commercialization-jul2026)
   ——前馈 matmul 路线的商业化代表，与 NeuraWave 的 RC 路线构成对照组。
7. **物理 RC 的权威定标**：[Tanaka et al., Neural Networks 115, 100–123 (2019)](https://ar5iv.labs.arxiv.org/html/1808.04962)
   （ar5iv 全文可读，被引 ~2900）——按物理基底分类的标准综述，写论文引言时用它
   锚定"物理蓄水池"概念谱系。
8. **RC 最强的真实应用锚点：光纤非线性均衡**（我们 04/05 的 channel 任务
   正是这个负载）——Argyris et al. 2018 实验演示；[Masaad et al. 2022（64-QAM
   + Kramers–Kronig 接收机仿真）](https://pmc.ncbi.nlm.nih.gov/articles/PMC11501668/)；
   [2026 年新作报告 PRC 对相干信号非线性补偿带来 44% BER 改善](https://arxiv.org/pdf/2608.17419)。
   这条线的商业逻辑最硬：均衡在模拟域线速完成就**不需要高速 ADC+DSP**，
   正好打在光通信功耗痛点上——是"RC 潜力"一侧最有力的证据。
9. **光学 NGRC（重要，直接回答"RC 争议"和我们平台的定位）**：
   [Wang et al., "Optical next-generation reservoir computing", arXiv:2404.07857
   （Gigan 组 EPFL + 清华刘强）](https://arxiv.org/html/2404.07857v2)，全文已读。要点：
   - 机制：SLM 把 u_t、u_{t−1}（时延输入，**不经过循环态**）编码到相位 →
     毛玻璃散射（线性随机混合）→ 相机测强度。非线性全部来自
     y=|W·exp(ix)|² 的相位编码+平方律探测，Taylor 展开后每个散斑像素天然携带
     输入的**全部阶多项式特征**，即 r ≈ M_s·Θ(U)，与数字 NGRC 严格等价
     （W'_out ≈ W_out·M_s）。
   - 数字：KS 方程（L=22, 64 格点）用 2500 个光学节点（数字 NGRC 二阶项需 8385）；
     训练仅 6000 步、warmup 仅 2 步（此前光学 RC SOTA Rafayelyan 2020 用 90500 步）；
     预测 4 个 Lyapunov 时间（前值 2.5）；observer 任务优于三次样条插值。
   - **对 Catch-22 争议的意义**：NGRC 证明很多 RC 的成功其实来自"时延输入的
     多项式特征"，**不需要真实的循环动力学**。这与我们 04 的结论互洽——掩码后
     线性 RC 退化为 Hankel（纯延迟抽头）结构，性能不降，说明延迟抽头+非线性
     特征映射才是主力。
   - **对我们平台的启示（机会）**：CBG 啁啾光栅天然是"波长复用的延迟抽头阵列"
     （τ_r(λ) 实测 424 ps 跨度），加上探测器的 |E|² 平方律——结构上就是一台
     **片上 NGRC 特征生成器**。他们用的是自由空间 SLM+相机（Hz–kHz 速率），
     我们若用 TFLN 在片上做同样的"延迟抽头+隐式多项式特征"，速率可达 GHz 量级。
     缺口：目前 CBG 链路的非线性只有探测平方律（二阶），χ²/χ³ 材料非线性可提供
     更高阶、更低功耗的特征；真循环（反馈）对需要长记忆的任务仍是我们的差异化项。
     （该文已正式发表于 Light: Sci. Appl., 2025-07-21。）
10. **对冲证据：NGRC 的"数据越多越不稳定"失败模式**（全文已读）：
    [Zhang & Lai, "How more data can hurt: Instability and regularization in
    next-generation reservoir computing", Chaos 35, 073142 (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12221348/)
    ——磁摆/Lorenz 实验证明：训练轨迹数超过阈值后 NGRC 自回归预测**整体发散到
    无穷**，且不是过拟合（流面拟合误差单调下降）。机制：延迟状态与当前状态的
    特征在时间上近似线性相关 → 设计矩阵 G 病态（κ(Gᵀ)~10¹⁰，主子角恒近零，
    与数据量无关）→ 固定 λ 的岭回归给出范数暴涨的 W → 学到的等价积分器是
    系数巨大且互相抵消的病态 Adams–Bashforth（±100 量级 vs 最优 {3/2,−1/2}）。
    缓解：λ 随数据量同步增大，或训练时主动加噪。
    **对辩论的意义**：①传统 RC 的循环态有 echo-state 性质保证有界，NGRC 没有
    内禀稳定性——这是"RC 潜力"一侧被忽视的论据；②但 NGRC 的病态出在数字
    读出层而非物理层，对我们"片上 NGRC"机会（§五-7）不构成硬件障碍，只需在
    读出训练时用数据规模自适应的 λ——将来做该方向时这是必须写进方法的坑；
    ③我们的 04/05 仿真若要加 NGRC 基线，必须扫 λ×数据量二维网格才算公平。

### 伊辛机的诚实性警示（对审稿/写论文有用）

- Hamerly（NTT）的基准方法学幻灯片指出：time-to-solution 对退火时长 T_ann
  高度敏感，T_ann 取得过大时 Tsoln 随 N 变平，会造成**量子加速假象**。
- QA 领域的教训同样适用于光子 IM：只在"硬件原生"实例上测 = best-case。
- 我们 06 用 SA 作参照 + 随机图实例（非定制结构）+ 报 E/E_BK 比值而非绝对 cut，
  符合这套诚实规范；将来写论文时要主动声明实例生成方式。

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
   **已有直接先例**（交叉检验过）：
   - [Zhang et al., "Reconfigurable Cascaded Chirped-Grating Delay Lines for Silicon
     Photonic Convolutional Computing", Photonics 12, 974 (2025)](https://www.mdpi.com/2304-6732/12/10/974)
     ——SOI 上级联 CBG 做可调真延迟（0–100 ps，GD 斜率 ~25 ps/nm，10 mm/段，
     GDR 2–3 ps），波长选择粗调 + 微加热器精调，直接喂给光子 CNN 的卷积移位。
     **与他们对比**：他们要的是大延迟粗粒度（ps 级 bit 移位），我们的 TFLN 啁啾光栅
     是色散整形细粒度（D≈0.051 ps/nm、带宽数十 nm）——同一物理（GD 工程）
     不同生态位，恰好互补而非竞争。
   - Huang et al., Opt. Express 27, 20456 (2019)：时-波长平面操控 + 色散延迟做
     可编程矩阵运算（复旦/暨南路线）；Jiang et al., JLT 39, 4592 (2021)：
     交错时-波长调制 PCNN。**结论：色散延迟做矩阵运算是已被验证的方向，
     我们的切入点应在"TFLN 平台上的高精度 GD 整形"而非做大延迟。**
4. **TFLN χ² OPO 路线**（Caltech Marandi，arXiv:2405.17355 全文已读）：物理上最
   优雅的 CIM；**其可编程耦合层仍停留在 proposal（Fig. 5 未实验）**——我们的
   色散/延迟器件可做固定拓扑片上耦合层（稀疏图/链式图不需要全可编程），这是
   EO 平台切入 χ² 生态的现实接口。我们自身无 PPLN 工艺，自旋本体列为远期。
5. **全光 ReLU 等深学激活**（Marandi, Nanophotonics 2023）：与我们 sin² 互补，
   静态任务我们已用 04-T4 证明不该硬上 RC。
6. **光电混合读出**（RC+DNN）：工程上最现实的落地方案。
7. **片上 NGRC / 隐式多项式特征生成器**（新增，源自光学 NGRC 精读）：CBG 的
   τ_r(λ) 波长复用延迟抽头 + 探测器平方律，结构上等价于 NGRC 的"时延输入
   多项式特征"。自由空间 NGRC 只有 Hz–kHz 速率，TFLN 片上版可到 GHz。
   设计问题：如何在 CBG 链里引入受控高阶项（χ²/χ³ 或级联 MZM）超越纯二阶。

## 六、待下载文献（ACS/Nature 付费墙，请用户明早帮下）

见同步文件夹 DOWNLOAD_REQUESTS_20260926.md。
