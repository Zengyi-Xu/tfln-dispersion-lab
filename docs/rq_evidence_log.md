# RQ 证据日志（通宵调研产出）

> 配套 `RQ清单_调研草案.md` / `论文零号稿_草稿.md`。格式：`[RQx.y] 文献 | 关键数字/声明 | 支撑/威胁零号稿哪段 | 判据`。
> 起始日期 2026-09-26。维护：小白（文献会话）。所有数字引用公开来源，写论文前需按引用规范二次核实原文。
> 姊妹文档：`docs/ising_literature_digest.md`（伊辛机×RC×片上非线性精读综述）——RC 争议定标见其 §三（第 13/14 条反向索引回本文件），TFLN×RC 先占地图见其 §三末子节。两文档结论已对齐，发现数字漂移时以带"全文已读"标注的条目为准。

---

## 2026-09-26 第一批：RQ1（可调色散需求）+ RQ2（电子 ADC 边界）

### RQ1.1/RQ1.2 主证据：光真时延（OTTD）波束形成综述

- [RQ1.1/RQ1.2] An T. et al., "A review of research on optical true time delay technology", J. Eur. Opt. Society-Rapid Publ. 21, 2 (2025)（[全文](https://jeos.edpsciences.org/articles/jeos/full_html/2025/01/jeos20240056/jeos20240056.html)）| 宽带相控阵**结构性需要** TTD：相移器方案孔径效应限制相对带宽 Δf/f₀ ≤ 1–2%（扫到 60°、波束宽 1–2° 时），L 波段 1.3 GHz 雷达只剩 13–26 MHz 瞬时带宽，"远不足以满足高分辨成像"；TTD 使指向角与频率解耦 | **支撑**零号稿 b)（色散/延迟器件的真实应用牵引）；支撑 RQ1 主线 | 部分触发判据（给了"为什么需要"，还需"调多快"）
- [RQ1.2] 同上综述 §5 四路线对比 | 现有可调延迟方案的极限表（全部集成/半集成）：
  - 微环阵列：连续可调、范围大（Burla 2013 Ku 波段 236 ps；Xiang 2018 SiN SCISSOR 500 ps；Shan 2021 带宽 16 GHz、范围 160 ps、步进 20 ps），**但调谐是热调 → 波束切换慢（µs–ms 级）**；
  - 光栅延迟线：易集成，但离散不可连续调、或需扫波长（LCFBG 5-bit 0–168.6 ps、精度 2.46 ps；Sun 2020 SOI SWG 光栅步进 6.6 ps/范围 60 ps；Wang 2021 40 级 SWG 范围 181.9 ps@10 GHz 带宽；Srivastava 2020 RCFBG 精度 0.2 ps/范围 200 ps、Ku 波段 ±36.8° 无斜视扫描）；
  - 多路开关延迟线：**切换 ns 级**（电光开关），但离散、精度低（Pérez-López 2018 mesh 13.5 ps/步、最大 148.5 ps；Zhu 2020 Optica 1×8 波束成形器 0–496 ps）；
  - 波长选择型：范围大（Duan 2017 最大 20 µs）但依赖快速连续可调激光器 | **支撑** RQ1.2 对比表全部三槽 | ✅ 触发判据
- **RQ1 判据句（v0.1，可写进零号稿）**：宽带相控阵波束形成要求真延迟在**连续、≥100 ps 范围、ns–µs 切换**三个指标上同时达标；现有集成方案中微环（热调）慢、光开关离散、波长扫描依赖昂贵快调激光——"连续 × 大范围 × 电光 ns 级调谐"的交集在集成平台上未被占据，而 TFLN 电光调谐色散器件恰好落在这个交集。三槽出处：JEOS-RP 2025 综述（需求侧 + 微环热调慢）、Srivastava IEEE T-MTT 2020（光栅方案精度/范围）、Pérez-López JLT 2018（开关方案 ns 但离散）。
- [RQ1.1 反证，必须记录] 相干光通信的"可调色散补偿"需求已被数字 DSP 吸收：现代相干接收机在电域用均衡算法补偿 CD（如 ResearchGate 2024 widely-linear 均衡工作），ITU-T G.667 时代的可调光补偿器需求主要来自动态路由 WDM 的 40 Gbit/s 时代 | **威胁**零号稿 RQ1 主线若走电信场景——**电信不是可调色散的好需求**，需求论证必须落在雷达/波束形成/脉冲整形等"检测前处理"场景 | ✅ 反证记录完毕，RQ1 应用清单应剔除电信动态补偿

### RQ2.1 主证据：ADC 能效边界

- [RQ2.1] Murmann ADC Performance Survey 1997–2026（ISSCC+VLSI，[github.com/bmurmann/ADC-survey](https://github.com/bmurmann/ADC-survey)）| **已从原始数据集（rev20260801，N=707）提取定量边界**（脚本 `verify/adc_fom_plot.py`，图 `results/verify/adc_fom_boundary.png`）：
  - 能量前沿：~1–2 fJ/step 平台维持到 ~500 MS/s，之后每十倍频恶化 ~5×：5.0 fJ/step @ 1.8 GS/s → 10.9 @ 5.6 GS/s → 22 @ 18 GS/s → 25.8 @ 56 GS/s；
  - fs≥5 GS/s 全体（N=77）：FoM 中位 146 fJ/step，**ENOB 中位仅 5.3**，P/fs 中位 7.4 pJ/样本；
  - **fs≥5 GS/s 且 ENOB≥8：707 篇里只有 9 篇**，P/fs 中位 **92.6 pJ/样本**——这就是零号稿 a) 要填的"贵区"；
  - >5 GS/s 最优 P/fs = 958 fJ/样本（24 GS/s）——即便世界级前沿，TBP~10³ 的匹配滤波仅 ADC 就 ~1 nJ/决策 | 强支撑 a)：给出"采样率-ENOB-功耗互锁"的全数据证据 | ✅ 判据达成（a) 段的空可填：例——B=10 GHz、T_chirp=100 ns → TBP=10³ 样本/决策 → 电子链 ADC 能耗 ~1–93 nJ/决策（前沿至中位），未计 DSP）
- [RQ2.1] TI ADC12DJ5200RF（[产品页](https://www.ti.com/product/ADC12DJ5200RF)，商用 RF 直采标杆）| 10.4 GS/s 单通道、12-bit 标称、**ENOB 8.6–8.8、功耗 4 W** → 385 fJ/样本（≈1 fJ/conv-step，已是该速率下世界级水平）；输入带宽 8 GHz，可用输入 >10 GHz | 支撑 a)：一次匹配滤波需 TBP~10³ 样本 → 仅 ADC 就 ~10²–10³ pJ/决策，还没算 DSP；且这是桌面级功耗，机载/星载不可承受 | ✅ 提供锚点
- [RQ2.1 结构性上限] 孔径抖动限制：SNR_jitter = −20log₁₀(2π f_in σ_j)。σ_j=50 fs 时 f_in=20 GHz → SNR≈44 dB → **ENOB≈7**；f_in=60 GHz → ENOB≈5.7。抖动随工艺改善缓慢（十年改善 <4×），这是 a) 段"ENOB-采样率互锁"的物理根源 | 支撑 a) | ✅ 可写公式进零号稿

### 2026-09-26 第一批补：RQ2.2 / RQ2.3

- [RQ2.3] Valley G.C., "Photonic analog-to-digital converters", Opt. Express 15, 1955 (2007) | 光子 ADC 奠基综述：电子 ADC 的核心瓶颈是采样时钟抖动与比较器模糊，随载频升高 ENOB 结构性下降 | **支撑** a) 的"互锁"声明——这个论证 2007 年就已被系统写过，可直接引用 | ✅
- [RQ2.3] Khilo A. et al., "Photonic ADC: overcoming the bottleneck of electronic jitter", Opt. Express 20, 4454 (2012)（[MIT 全文](https://sclaser.mit.edu/documents/KhiloPhotonicADC.pdf)）| 用锁模激光超低定时抖动做光采样，绕开电子抖动 | 支撑 a)；**但注意差异化**：光子 ADC 路线仍是"先把整个时间轴数字化再算"——只是把采样前端换成光的，后端 ADC 量化和 DSP 功耗一分不少。我们（色散前端在检测前完成匹配滤波）与光子 ADC 是**不同层级**的方案：它优化采样器，我们消掉采样需求本身（黄超然 OSP 同款论证结构）| ✅ 差异化区间明确
- [RQ2.2] 数字脉压功耗：检索到多为实现论文（Golubicic 2013 等），实测功耗数字稀少；CORE 博士论文（低功耗相控阵气象雷达）有 FPGA 脉压实现细节但未给 pJ/样本 | **暂缺硬数字**；可先用行业常识区间锚定：28–16 nm FPGA 信号处理实测能效 ~10–50 GFLOPS/W，10 GS/s × 复数 FIR（TBP~10³ tap）≈ 10¹³ MAC/s → **百瓦级**；与 TI ADC 的 4 W 合起来，"电子方案做 10 GHz 带宽脉压 ≈ 10–100 W 级"是安全口径 | 支撑 a) 量级判断，写论文前需找 1–2 篇给实测功耗的雷达处理 FPGA 文献坐实 | 部分触发

## 2026-09-26 第二批：RQ3 占据图（色散×时间域计算）

- [RQ3.1] Goda & Jalali, "Dispersive Fourier transformation for fast continuous single-shot measurements", Nat. Photon. 7, 102 (2013)；Mahjoubfar et al., Biomed. Opt. Express 4, 1618 (2013)（time-stretch + ML 流式细胞分类）| Jalali 线占据格子：**固定色散前端 + 数字 ML 后端**。色散只做"频谱→时间"映射帮电子 ADC 降速，学习全在数字端；色散不可调、读出非时间编码 | 支撑 c) 独创性声明（该格子被占≠我们的格子被占）；**占据者缺陷明确**：固定色散、仍依赖高速数字化 | ✅ 入占据图
- [RQ3.1] Asghari & Jalali anamorphic/warped stretch 线（Appl. Opt. 52, 6735 (2013)；Mahjoubfar 2015 PMC4658532）| 按信号稀疏性设计非均匀群延迟轮廓做压缩采集——**群延迟轮廓是被"设计"的，但不是在线可调的**；后端仍是数字 | 同上 | ✅
- [RQ3.1] Sozos K. et al., recurrent optical spectrum slicing（ROSS）线：PMC10955832 (2022/2024 综述性实验)；最新 arXiv:2604.20504 (2026-04, "co-packaged photonic reservoir + receiver" 全光均衡）| **最接近"色散当计算元件"的占据者**：光谱切片经色散介质获得波长依赖延迟，构成循环 RC 的虚拟节点间耦合。但：色散固定（光纤/DCF）、面向光通信均衡（补偿 CD 而非用它做通用计算）、读出是线性读出非时间编码、无 SNN | 威胁等级：中。c) 段独创性声明需写"色散在 ROSS 里只是延迟产生器，不是被调谐的计算变量；且无 spike/时间编码读出" | ✅ 入占据图，写作时必须引用区分
- [RQ3.1] Larger L. et al., PRX 2017（被引 699）EO 相位延迟 TDRC | 延迟环 RC 经典作，延迟来自光纤环长度而非色散 | 不撞色散格子，但 RC 叙事必须引 | ✅
- [RQ3 占据图 v0.1]（前端 × 后端）：
  - 固定色散 × 数字后端 = Jalali time-stretch ML（强占据）
  - 固定色散（作延迟源） × RC 线性读出 = Sozos/ROSS 线（中占据，通信均衡场景）
  - 延迟线/微环 × RC = Larger 线及衍生物（强占据）
  - **可调色散 × 时间编码 SNN 后端 = 空（我们的格子）**
  - 可调色散 × 任何后端 = 基本空（检索未见把色散当"在线可调计算变量"的工作）| 支撑 c) | ✅ 判据达成（格子空，且能指出相邻格子占据者缺陷）

## 2026-09-26 第三批：RQ5 平台对标 + RQ1 的 SiN 反例

- [RQ5] Du Z. et al., "Silicon nitride chirped spiral Bragg grating with large group delay", APL Photonics 5, 101302 (2020)（被引 79）| SiN 啁啾螺旋布拉格光栅：**总群延迟 1440 ps、色散 −156.5 ps/nm**；同组后续报道 628 ps / −27.7 ps/nm 版本 | 固定色散标杆。定位我们的 1.22–1.30 ps/nm：绝对值小两个量级，但我们的卖点是**电光可调**不是绝对值 | ✅ 入对标表
- [RQ5] arXiv:2604.12564 (2026-04) 米级 SiN 啁啾螺旋光栅：**10 ns 群延迟** | 固定延迟摆幅天花板又抬高了一个量级；"摆幅"指标上硬拼 SiN 无意义，必须拼"可调" | 支撑目标数 3 的定位策略 | ✅
- [RQ5] 南京大学 Nature (2023) TFLN 集成飞秒脉冲源 | TFLN 上鳍形啁啾布拉格光栅（周期 406.5→414.5 nm 线性啁啾）做色散管理/脉冲压缩——**TFLN+CBG 已有先例，但角色是固定脉冲压缩器，无电光调谐** | 威胁等级：中。c) 段必须声明我们的差异在"在线电光可调谐的色散量"，不是"TFLN 上做光栅"本身 | ✅ 必引
- [RQ5/RQ1.2] TFLN 电调光栅先例簇：Prencipe et al. ACS Photonics 8, 2923 (2021)（可调超窄带光栅滤波器）；Pohl et al. IEEE PTL 33, 85 (2021)（100-GBd 波导光栅调制器）；BIT 2025 相移 WBG 电调微波光子滤波器；Glasgow 2025 电调制波导光栅 | **TFLN+光栅+电光调谐已存在，但调的都是滤波谱形/陷波位置，没人调"色散量/群延迟斜率"做时间域计算** | 既是威胁（工艺先例）又是支撑（可行性已被证明）；差异化措辞：tune *dispersion as a computational variable*，不是 tune filter | ✅ 精确划界
- [RQ1.2 反例，必须记录] SiN 平台上**连续可调色散已存在**：高纵横比 SiN 芯超低损耗平台上的 10 阶晶格滤波器（21 个 MZI 级联、2.23 cm²），**−500 到 +500 ps/nm 连续可调**（ResearchGate 2025-08 条目引用）| **威胁** RQ1 判据句 v0.1 中"交集未被占据"的表述——需修正为：可调色散本身在 SiN 热调 MZI 晶格上存在，但 ① 热调 µs–ms 慢、② 横向滤波器架构的延迟摆幅受 FSR 限制、③ 与啁啾光栅的单程映射物理不同。TFLN EO 调谐的不可替代性收窄为"**ns 级调谐速度**" + CBG 固有的大摆幅/连续映射 | ⚠️ 触发反证条款：判据句 v0.2 待修订

### RQ1 判据句 v0.2（2026-09-26，吸收 SiN 晶格滤波器反例）

> 宽带相控阵/波形捷变雷达要求色散（真延迟）**在脉冲级时间尺度（ns–µs）上重构**，且连续、摆幅 ≥100 ps。现有方案：微环热调（连续、大范围，但 µs–ms 慢）；光开关切换（ns 快，但离散、精度低）；SiN MZI 晶格滤波器（连续 ±500 ps/nm，但热调慢 + 横向架构摆幅受 FSR 限）；波长扫描型（依赖快调激光，系统成本转移）。**"电光 ns 级 × 连续 × 大摆幅"三者交集无人占据**——TFLN 电光调谐啁啾光栅恰好同时满足三条，这是 TFLN 相对 SiN 的不可替代性所在（SiN 无显著 Pockels 效应，ns 级调谐只能靠载流子注入，损耗/功耗代价大）。
> 出处：JEOS-RP 2025 OTTD 综述（四路线对比）；SiN 晶格滤波器 ±500 ps/nm（2025）；TFLN 电光调谐 ns 级为平台常识（Pockels r₃₃，调制器已达 100+ GBd）。

## 2026-09-26 第四批：RQ4（RC vs SNN 接口成本）

- [RQ4] Aadhi A. et al., "Scalable photonic reservoir computing for parallel machine learning", Nat. Commun. (2025)（被引 69）| 原文明确：时分复用虚拟节点机制"simplify the design ... **but also introduce latency and limit processing speed**" | 支撑 RQ4 论证素材：RC 的掩模/时分复用是公认的速度税 | ✅
- [RQ4] Bauwens I., VUB 博士论文 | "this preprocessing procedure is based on time-multiplexing and **limits the computing bandwidth** of the system" | 同上，独立来源 | ✅
- [RQ4] ESN vs LSM 对比工作（Virginia Tech 2026 等）| LSM = spiking 版 reservoir——**"SNN vs RC"本身是伪二分**：LSM 就是用 SNN 当蓄水池 | 提醒零号稿 b) 的"同一个本体论"表述要精确化：真正的对立面不是 RC，而是"需要高速均匀采样+数字读出的后端" | ✅ 措辞修正
- **[RQ4 判据暂判定：降级]** 证据指向：SNN 相对 RC 的不可替代性**不成立**（LSM 就是 RC）；可辩护的表述是"SNN/事件驱动读出相对**均匀采样数字后端**省掉了 Nyquist 采样与采样保持，且能耗随事件稀疏度伸缩"——这把 b) 段的论证对象从"RC vs SNN"改为"连续时间模拟接口 vs 均匀采样数字接口"。色散输出是连续时间模拟信号，事件化读出（比较器/神经元阈值）天然免采样时钟。建议按 RQ4 判据第二条执行：**SNN 降级为工程选择，论证重心移到接口本体论** | ⚠️ 触发判据（第二分支）

## 2026-09-26 第五批：RQ3.2（光子 SNN 实现方式梳理）

- [RQ3.2] 光子 SNN 主流实现盘点：神经元多为**可激发激光器**（VCSEL、DFB-SA），权重多为 **MRR weight bank 或相变材料（PCM）突触**：VCSEL-neuron × MRR weight bank 接口（arXiv:2305.00788）、VCSEL-MRR 幅度加权+速率编码（Hejda et al., Neuromorph. Comput. Eng. 2024）、光子神经突触核卷积 SNN 芯片（researching.cn 2023）、光子突触/神经元/忆阻器综述（Han et al., Opto-Electron. Technol. 2025）| **关键观察：光子 SNN 的"可训练变量"清一色是权重（幅度），延迟/时序只是信号载体而非被设计对象；没有人用色散器件做 SNN 的突触或延迟基底** | 支撑 c)：我们的格子（色散定义时序结构）在光子 SNN 内部也是空的 | ✅ RQ3.2 判据达成
- [RQ3 占据图更新]：纵轴后端加一行——"光子 SNN（权重编码）= VCSEL/MRR/PCM 线（占据，但不碰色散/延迟基底）"。我们的格子（可调色散 × 时序读出）仍然空。

## 2026-09-26 第六批：RQ2.2 补强 + 片上非线性×新方向

- [RQ2.2] Goodman 等，"Pitfalls and possibilities of radar compressive sensing"（[OU PDF](https://arrc.ou.edu/~goodman/pubs/AO_15_Pitfalls_possibilities_radar_CS.pdf)）| 实测对比：12-bit 2 GS/s ADC ≈ 3.5 W / $1500；模拟压缩感知前端 ≈ 1 W / $50 | 支撑 a) 量级判断；注意这是 2 GS/s 档，10+ GS/s 档功耗按比例恶化（对照 TI 4 W @ 10.4 GS/s）| ✅
- [RQ2.2 反例，记录] 模拟域脉压相关器芯片存在（90 nm CMOS，42 mW，eScholarship）——但带宽在百 MHz 级，不是 GHz 级；**"电子模拟相关"在 GHz 带宽同样做不好**，所以对手不是"电子模拟"而是"光学传播免费完成" | 不威胁 a)，反而划清比较对象 | ✅
- [新方向·片上非线性] TFLN 计算版图快查：北大王剑威组 TFLN 光计算电路（arXiv:2411.02734）、TFLN 光子张量核 120 GOPS（arXiv:2311.16896）——**都是 MZM 电光线性代数路线，非线性只做调制**；TFLN Kerr/EO 混合微梳（Song et al. 2025, PMC12339749）、电泵浦孤子微梳（arXiv:2510.00371）——**微梳在 TFLN 上已成立，但用途是光源/频梳，未用于计算** | 结论："TFLN 微梳 × 计算"或"EO+χ²/χ³ 协同计算"格子空着；与我们色散计算的交叉点：微梳多波长 + 色散器件天然给出大规模并行延迟抽头（comb teeth × GD slope = 抽头矩阵）| 入 digest §五机会清单候选

## 2026-09-26 第七批：微梳×色散=并行抽头矩阵（可行性 + 诚实的新颖性评估）

- 估算（一阶群延迟近似，λ=1550 nm）：抽头步进 Δτ = D·FSR_λ，时间孔径 = N_tap·Δτ。
  - 我们的 CBG（D=1.3 ps/nm）：FSR=100 GHz（0.8 nm）→ Δτ≈1.0 ps、128 抽头孔径仅 0.13 ns——**太密太短**，不适合 ns 级波形；
  - 大色散器件（SiN 螺旋 CBG 级，D=156 ps/nm）：FSR=25 GHz → Δτ≈31 ps、128 抽头孔径 4 ns、梳跨 25.6 nm——**物理上成立**；FSR=100 GHz → Δτ=125 ps、32 抽头 4 ns 孔径。
- **新颖性自查（反幻觉纪律）**：微梳+色散做横向滤波/TTD 波束形成**是已确立概念**（Xue et al. JLT 2018 微梳 TTD 波束成形，被引 581；后续微梳 RF 横向滤波器系列）。**这条路本身不是创新点**。可用的差异化只剩：① D 在线可调 → 抽头间隔跟随波形重构（配合 RQ1 判据句 v0.2）；② 训练式读出（RC/SNN）而非固定滤波——但这又回到我们主线叙事。结论：微梳×色散**不构成独立新方向**，只能作为主线的"并行化扩展"备选。

## 2026-09-26 第八批：RQ2.3 收尾 + 黄超然 OSP 原文核对

- [RQ2.3] Wang B. et al.（黄超然组）, "Beyond Terabit/s Integrated Neuromorphic Photonic Processor for DSP-Free Optical Interconnects", arXiv:2504.15044（Science 2026 版）| **摘要原文已核实**：100 Gbaud PAM4/通道、1.6 Tb/s、5 km C 波段（≈O 波段 80 km）；延迟降 4 个数量级、能耗降 3 个数量级；硅光工艺。"DSP 抽头 882→25、67.5 fJ/bit、55 ps"三个数出自站位指南转引，**摘要未见**，写论文前需对 Science 正式版全文核实（新闻稿只说 "sub-60 ps"，与 55 ps 一致）| 支撑 a) 论证结构（别人已用"检测前计算"叙事发 Science）| ⚠️ 部分数字待核
- **[定位警示，重要] OSP 本身就是深度储备池计算（deep RC）**——"RC 硬件在光通信均衡碾压 DSP"这个论点已被黄超然组占住（Science 级）。我们的差异化必须绕开电信均衡：我们做的是 ① 可调色散作为计算变量（OSP 的 RC 节点是固定延迟线）、② 雷达/LiDAR 时间模式识别（OSP 是通信均衡）、③ TFLN 电光可调（OSP 是硅光）。叙事上 OSP 应作为"RC 硬件已被顶级验证"的**盟友证据**引用，同时一句话划界 | ✅ 入占据图：固定延迟 RC × 通信均衡 = 强占据（OSP）

## 2026-09-26 第九批：RC vs 深度学习的系统对比（回应"蓄水池不好用"质疑的量化弹药）

- [RC vs DL] Shahi S. et al., "Prediction of chaotic time series using recurrent neural networks and reservoir computing techniques: A comparative study", (2022)，PMC9230140（被引 183）| 系统对比 RNN/LSTM/RC：混沌时序长期预测上 RC 与 NVAR **精度更高且训练成本远低于** LSTM 类 | 正面弹药：在 RC 的合法领地（混沌/动力系统、中小数据、实时）它有系统级优势，不是"潜力不足" | ✅
- [RC vs DL] Valle J. et al., Chaos Solitons Fractals (2025)（被引 24）：LSTM vs Transformer 混沌预测对比，仍把 RC 当基准对手 | RC 在 2025 年的 DL 论文里仍是必须打的基准——领域地位佐证 | ✅
- [RC vs DL·反面] LLM/Transformer 长程混沌预测（arXiv:2608.29579）等线正在从"短观测长预测"角度侵蚀 RC 领地 | 诚实记录：RC 的精度护城河在被压缩，**硬件能耗/延迟优势才是不可替代的部分**——这正是我们零号稿的论证方向（不比精度比能效） | ✅

## 2026-09-26 第十批：Shahi 2022 精读数字（Machine Learning with Applications 8, 100300）

全文已读（PMC9230140，五个数据集：Mackey-Glass、Lorenz-63、Morris-Lecar 爆发神经元、ENSO、心脏电压实验数据）。可引用硬数字：

- **Lorenz-63**：LSTM/GRU 训练+预测耗时比 NVAR/ESN **慢 3 个数量级以上**（"more than 3 orders of magnitude slower"）；ESN 比 NVAR 慢 2–5× 但同量级；
- **Morris-Lecar**："LSTM and GRU have little if any predictive power"——门控 RNN 在爆发式混沌上基本失效，RC 正常；
- **Mackey-Glass**：NVAR 最高效；最大 ESN（500 单元）比对应 NVAR 预测误差低 ~8%——规模上去后 RC 精度可反超 NVAR；
- **ENSO**：LSTM/GRU 比 ESN 慢近 2 个数量级，且 RMSE 与 ESN 相当（精度无补偿）。

**给"蓄水池不好用"质疑的回答骨架**：在混沌/动力系统类时序上，门控 RNN 要么失效要么慢 2–3 个数量级且精度更差；RC 的合法领地由这类系统对比论文系统性确立（Shahi 2022, 被引 183）。同事印象中"RC 不好用"若来自静态/图像类任务，那是拿 RC 打它不该打的仗——我们的零号稿恰恰只主张时序时间模式任务。

## 2026-09-26 第十一批：Kong 2026 全文精读（最大定位风险解除）

- [RQ3 威胁复核] Kong D. et al., "Delay-based photonic reservoir computing on thin-film lithium niobate with time–wavelength-coupled virtual nodes", npj Unconv. Comput. 3, 36 (2026-07-21，OA)。获取方式：桌面浏览器读 nature.com 全文（FetchURL 被反爬，**不用再等用户下载，清单 #5 销项**）。
- 架构：MZM 编码 10 GHz 脉冲列 → 5 级微环（τ=20 ps）→ PPLN χ² SHG（1550→775 nm）→ 双 PD + **160 GSa/s 电子采样** → 岭回归。Santa Fe NMSE 2.6e-3 / NARMA-10 3.9e-3，FW+SH 比单分量低约 1 个数量级。需 ~200 mW 平均光功率达 SNR 45 dB。
- **判定：不占我们的格子**。"时-波长耦合"=χ² 倍频双通道，非色散连续 GD 映射；记忆=微环离散延迟；无电光在线可调、无 spike/事件读出、纯仿真单 run。差异化假设①②③④全部存活（细节见 digest §三 Kong 精读段）。
- **反向利用**：Kong 的读出需要 160 GSa/s 高速电子采样——这是 TFLN-RC 现状"把瓶颈推给 ADC"的活例证，直接支撑零号稿 a) 与 RQ4 的事件读出论证（08 仿真正是测这个）。
- 方法学警示：Kong 每个配置只跑单次确定性仿真（无种子统计）——我们的多种子协议是审稿人可见的严谨性优势，写论文时值得点出。

## 2026-09-26 第十二批：PIC-OPO RC 全文精读（最后一个真风险销项，威胁定级：中）

- [RQ3 威胁复核] Parto M., Li G.H.Y., Sekine R., Gray R.M., Williams J., Marandi A., "High-speed reservoir computing using photonic integrated circuit optical parametric oscillators", Sci. Adv. 12(38):eaeb3077 (2026-09-18，OA)。获取方式：science.org/PubMed 均被反爬挡死，**EuropePMC REST API 拿到 PMCID=PMC13588183 开放全文**——不用再等用户下载，清单 #6 销项。
- 架构（OPONN）：EO comb（10 GHz、1045 nm、~2 ps）→ EOM 掩码（AWG 10 GSa/s）→ TFLN x-cut 跑道腔 PPLN OPO（简并，信号 ~2090 nm；腔反馈=记忆、参量放大=全光非线性）→ 12 GHz PD → 数字加权平均读出（in silico SVD）。Lorenz63 NMSE 0.07±0.017 / MGS 0.06±0.017 / PAM4 SER 19%→7%（线性对照 11%）/ 波形分类 100%（3×100 样本）。10 GHz 受限于 AWG，声称全光化可 sub-ns（SI S2）。专利 US20240061316A1 + PINC Technologies 利益关联。
- **判定：大格子被占、我们的格子仍空**。① "TFLN χ² 高速非线性 RC" 已被**实验**占据（Caltech Marandi 组，与 TFLN 伊辛机同组）——零号稿若有"首次 TFLN RC"类措辞必须降级；② 但它的记忆=腔 roundtrip（τ 由 FSR 钉死不可调）、读出=快 PD+数字训练（仍在电子采样范式内）、任务=基准老三样（无雷达、无 spike、无可调色散）；③ 可行性盟友价值：TFLN χ² 非线性做 RC 物理成立 + 300 样本小样本读出训练可行。
- **[措辞建议，入零号稿]**：把新颖性表述从"TFLN 上的 RC"收紧为"**首个基于在线可调色散器件的时间编码处理链路**"（对标 OPO 腔的固定 τ 与微环的固定延迟链）。威胁级别定为"中"是因为同组已有 >100 GHz 全光路线（arXiv:2501.05756）在追速度叙事——我们的护城河不在速度在**可调性+事件读出+负载**。
- **反向利用**：OPONN 的读出仍是 12 GHz PD + 数字 SVD，与 Kong 的 160 GSa/s 采样同属"把瓶颈推给电子"——两家 TFLN-RC 先占都成了 RQ4 事件读出论证的反面例证。
- 至此 digest §三 TFLN×RC 先占地图（Wang 2024 / Abdalla 2023 / Kong 2026 / PIC-OPO 2026 / 忆阻器 2023）**全部精读销项**。

## 2026-09-26 第十三批：色散 GD×伊辛耦合交叉核查（片上非线性×新方向）

- [新方向·先占核查] "延迟实现伊辛耦合" = CIM 标准做法（Yamamoto 白皮书：N−1 条离散延迟线拼任意 J_ij）；"波长域伊辛机"已被占：Liu et al., Adv. Photonics Nexus 4, 056005 (2025)（华科张新亮组，片上 32 自旋、两种耦合编码）+ Luo/Mi/Huang/Ruan, Sci. Adv. (2023)（WDM 伊辛模拟器，全可编程耦合+外场，耦合靠 MZI/MRR 权重而非色散）| **"用连续色散 GD 生成耦合"无人走过，但线性 GD 只给出谱距的结构化耦合（Toeplitz/距离依赖型），不是任意 J** | 不威胁主线；作为新方向时叙事必须锁定"结构化/晶格类伊辛（幂律耦合，对标 Rydberg 物理）"，不与全可编程 WDM 伊辛机竞争 | ✅ 入 digest §五 #8
- [旁证] MDPI Photonics 12, 974 (2025)（SOI 级联 CBG 可调延迟做光子 CNN 卷积移位）已于早前批次入库（digest §五 #3）——本次交叉确认其为仿真工作、热调、SOI 平台，与我们 TFLN EO 色散整形不同生态位。
- [仿真候选 09] 色散耦合伊辛链退火可行性（一维链+次近邻，CBG GD 生成耦合剖面，MZM sin² 作增益/非线性）——列入小黑任务队列，等 05–08 回执后再发。

## 2026-09-26 第十四批：Mohseni NRP 2022 全文精读（清单 #3 销项）+ 伊辛基准现实入库

- [伊辛基准·标准综述] Mohseni, McMahon & Byrnes, "Ising machines as hardware solvers of combinatorial optimization problems", Nat. Rev. Phys. 4, 363–379 (2022)（被引 881）| 原文总判决："Ising hardware based on **classical digital technologies is the best performing** for common benchmark problems"；SK/MaxCut TTS 实测最优=RBM/东芝分叉机（数字），CIM3/PRIS/MRT 曲线是理论外推；D-Wave 受 Chimera 稀疏连接+N² 嵌入拖累，只有定制问题类（deceptive cluster loops）有常数因子加速、无标度优势；所有路线 TTS 随 N 指数恶化，竞争只在指数/前置因子 | **强约束**：光子/模拟伊辛机在通用基准上未超越数字硬件——我们的论文不能把伊辛当主叙事，只能作 sin² 非线性多功能性的副演示；主叙事留在时序信号处理能效（与"不比精度比能效"判据一致）| ✅ 获取方式：作者课程主页公开 PDF（aiichironakano.github.io），清单 #3 销项
- [方法学沿用] 该综述的 TTS 定义（99% 集体成功概率折算）+ Hamerly 的 T_ann 假象警示 = 我们 06 仿真已遵循的诚实规范；写论文时实例生成方式、退火时长扫描必须主动声明。
- [引用句式，入零号稿]「即使在被引 881 次的领域标准综述中，光子/模拟伊辛机在通用基准上也未超越数字硬件（Mohseni et al. 2022）；我们因此不主张优化霸权，而主张面向实时时序信号的能效/延迟优势。」

## 2026-09-26 第十五批：小黑 rc_designspace 全量回执合并（23,520 run，10 种子）

- [RQ4/零号稿 b)·sim] `results/rc_designspace/`（commit 20af4e5，7945HX 通宵）：延迟环 RC 设计空间全网格 1176 配置 × 2 架构 × **10 种子** = 23,520 core run + 500 scene run，**0 失败** | **核心数字：sin²（MZM 真实传递函数）best MC 319.0（N=800, a=0.05, ρ=0.99, γ=2.0）vs tanh 363.2（N=400, a=0.1, ρ=0.99, γ=0.02）——真实器件非线性仅损 12%；NARMA-10 NMSE sin² 0.1328 略优于 tanh 0.1377**；scene 分类（L3 真实光栅脉冲）500/500 构型 ≥0.9、中位 1.0 | 支撑 b)：MZM sin² 作 RC 节点不劣于理想 tanh，"蓄水池不好用"在器件层面不成立；**诚实 trade-off**：MC/N 效率 sin²=0.40 < tanh=0.91，同等 MC 需更大 N——论文须报此代价；10 种子协议 = 对 Kong 2026 单 run 的可见严谨性优势 | ✅
- [验收口径记录] 任务书预估行数 ≥47000 是我口径估错（按每 arch 两行），实际每 run 一行、全网格恰好 23520，无缺失——已在中转夹 RECEIPT_designspace_20260926.md 向小黑说明，未改任何数值。
- [队列状态] `results/rc_vs_baselines/`、`results/rc_vs_deep/` 空目录已就位；小黑后续优先级建议：rc_vs_deep > rc_vs_baselines > 07-NGRC > 08 全量复核。

## 2026-09-26 第十六批：Hamerly 2019（CIM vs D-Wave）精读（OA，PMC6534389）

- [伊辛基准·原始实验对比] Hamerly R. et al., "Experimental investigation of performance differences between coherent Ising machines and a quantum annealer", Sci. Adv. 5:eaau0823 (2019)（被引 511，全文已读）| 可引用结论：① TTS 定义 T_soln = T_ann·⌈log(0.01)/log(1−P)⌉（99% 集体成功，与 Mohseni 综述同源）；② **连接度是决定性变量**——CIM（全连接）在 SK 和稠密 MAX-CUT 上碾压 DW2Q，DW2Q 仅在 d=3–4 立方图上快 10–100× 且优势随 N 缩小；③ 经验假说：物理退火机最优 TTS ~ exp(O(N_ph^½))，D-Wave 嵌入使 N_ph→N² 从而指数吃亏；④ NTT CIM 有效环程时间 2.5N ns（把 TTS 折算成墙钟时间的关键参数）；⑤ 作者自承"claims are only suggestive, not conclusive" | 对零号稿的用法：支撑"连接度/嵌入开销比量子性更重要"的方法学声明；也给我们的 CIM 对比提供折算基准（环程 2.5N ns）| ✅
- [能效数字状态] Hamerly 本文**没有系统能效对比**（原文说 wall-clock/energy 留作后续工作）；二手来源（CNRS-Thales 博士论文 2023 表格：CMOS 0.45 mJ、忆阻器 0.22 µJ、D-Wave 250 MJ/解——含 25 kW 低温制冷）可作背景但**不可作一手引用**，需找原始出处（Cai et al. Nat. Electron. 2020 忆阻器；Dutta et al. 2020 振荡器 1.3×10⁷ solutions/s/W）再引。
- [与 Mohseni 2022 的互洽性] 两篇结论一致：稠密问题上光/模拟机相对 D-Wave 有优势，但相对最优数字硬件无优势——第十四批"伊辛只作副演示"的判据不变。

## 2026-09-26 第十七批：RC 读出在线训练（审稿人预防："为什么用离线岭回归？"）

- [读出训练·先占与出路] Antonik P., Duport F., Hermans M., Smerieri A., Haelterman M., Massar S., "Online training of an opto-electronic reservoir computer applied to real-time channel equalization", IEEE TNNLS 28(11), 2686 (2017)；Antonik P., Haelterman M., Massar S., "Online training for high-performance analogue readout layers in photonic reservoir computers", Cognitive Computation 9(3), 297–306 (2017)（VUB Massar 组，光电 RC 领域最成体系的一组）| 核心事实：**模拟读出层 + 在线训练（SGD/FORCE 式逐样本更新）在光电 RC 上 2017 年就已实验实现，性能与数字离线读出同级**；离线岭回归被原文明确称为硬件 RC 的"主要瓶颈"（数据要搬回后处理机） | 我们的答辩骨架：① 离线岭回归是概念验证期的标准做法，不损失器件结论（读出训练与蓄水池动力学解耦）；② 在线模拟读出已有成熟先例（VUB 2017×2），是我们的兼容升级路径而非缺口；③ 更根本的：我们的事件化读出（LIF 首脉冲）把读出数据量压到每样本几个时间戳，离线训练的"数据搬运瓶颈"对我们不成问题——08 仿真正是在定量这条 | ✅ 引用弹药
- [方法学备选] FORCE learning（Sussillo & Abbott 2009）= RC 闭环在线训练的经典算法；若审稿人要求在线演示，仿真层面可低成本补一个 FORCE vs 岭回归对照（列入候选仿真，优先级低于 05–08）。

## 2026-09-26 第十八批：事件化/spike 延迟编码读出的实验先例（给 RQ4/08 找佐证）

- [事件读出·先例盘点] ① VCSEL-SA 可激发神经元：spike latency（刺激→首脉冲间隔）编码是公认实验能力（中国光学期刊 2021 综述 Fig.1 及一系列 VCSEL-SA 工作）；② RTD 共振隧穿二极管 resonate-and-fire 神经元（arXiv:2510.14515，2025）：C 波段 1550 nm 直接光注入、ns 速率全-or-无脉冲——**电信波段光电脉冲神经元的最新实验**；③ 人工视觉神经元 rate+TTFS 复用编码（Nat. Commun. 2024，s41467-024-48103-9）：首脉冲延迟随刺激强度指数变化（3.51→1.19 µs）——TTFS 编码在器件层面成立；④ SNN 在 neuromorphic 硬件上做 IM/DD 光通信解映射（arXiv:2302.14726）：SNN 读出已进光通信系统 | **判定：spike 延迟编码的物理载体充分存在，但没有人把它用作"色散/CBG 处理波形的读出方式"——08 仿真的命题（LIF 首脉冲读出色散压缩脉冲）在文献中仍是空格，且每个组件都有实验先例支撑** | ✅ 支撑 RQ4 与 08 的合法性
- [措辞边界] 先例④（SNN 解映射）说明"SNN 读出光链路"概念已有人做——我们 08 的差异化不在"用 SNN 读出"本身，而在**输入是被色散器件物理整形过的波形**（延迟即特征），读出的是器件产生的时序结构而非任意电信号。

## 2026-09-26 第十九批：光子 RC 商业/专利版图 2026（回应同事质疑的时效性核对 + FTO 预警）

- [商业化现况] PatSnap 创新情报《Photonic Reservoir Computing Technology Landscape 2026》（2026-04）+ Pandaily WAIC 2026 报道 | 事实层：① 商业化资金集中在前馈 matmul（Lightelligence PACE 3，256×256 光子矩阵，WAIC 2026 首个实际部署的门禁系统；Ayar Labs 光互连 $500M 轮、估值 $3.75B）——**没有一家商业公司做 RC**；② RC 的商业化兴趣集中在**电信均衡**（Nokia Bell Labs 32 GBd OOK/80 km、IFISC PAM-4、华为 2021 把 PRC 列为模拟光 AI 三大支柱之一）——恰好是 OSP/黄超然组 Science 的路线；③ **雷达/时序模式识别不在任何商业 PRC 版图中**——产业情报侧也确认我们的负载是空白 | 同事质疑的最终回答骨架：RC 缺席商业化 = 生态错位（前馈有现成负载可接、RC 要自己造负载）+ 商业化路径被电信均衡单点占据；不是潜力死刑（Shahi 2022 系统对比 + 我们 designspace 23.5K run 佐证器件层面成立）| ✅ 支撑 digest §三"生态错位"论证，时效性到 2026-08
- **[FTO 预警，重要]** 同报告：光子 RC 领域检索到的**正式有效专利仅 3 件，全部归 IMEC VZW**（2 EP + 1 JP），最新 EP 于 **2026-03 授权，覆盖"加权元件+光电探测器的片上光学读出训练"**；另一件覆盖"时间编码+无源波导传播+非线性读出节点"。含义：① 我们走"无源波导+时间编码"路线，商业化前必须做正式 FTO 分析（WIPO PATENTSCOPE 跨辖区），IMEC 是唯一但真实的 IP 风险点；② 该数据集是"检索所得"，可能不全，结论需用专业专利检索复核；③ 学术发表不受限，但论文里避免"商业化路径"式表述 | ⚠️ 入 digest §六风险清单
- [趋势印证] 该报告六大方向中两条与我们资产直接相关：#1 全光读出/片上训练（IMEC 专利方向）、#3 频域复用 RC（ULB 2022，25 态频率梳 @20 MHz）——我们的微梳×色散抽头矩阵估算（第七批）与之呼应，但 #3 已有人做频率复用 RC，差异化仍在"可调色散"。

## 2026-09-26 第二十批：TFLN 微梳×计算占位复核（2026 时效）+ 小黑回执对齐

- [新方向·复核] TFLN 微梳 2025–2026 现状：Lv et al. 电泵浦孤子微梳（arXiv:2510.00371，杨起帆组）、Harvard Nat. Rev. Phys. 综述（s42254-025-00825-5）提到 EO-Kerr 混合梳与"梳源+调制器+PPLN 系统级组合"的方向性表述 | **判定：TFLN 微梳仍全部是光源/频梳叙事，无"微梳作为计算基底"的占位**——第六批"微梳×计算格子空"结论 2026 年仍成立；微梳×色散抽头矩阵保持为"并行化扩展备选"定位（第七批已判不构成独立新方向） | ✅
- [小黑回执对齐] HANDOFF_FROM_7945HX_rc_designspace.md 与我方验收一致：网格 = 2 arch × 6 N × 4 a × 7 ρ × 7 γ × 10 seeds = 23520 core + scene 320 + quant 80 + jitter 100 = 24020，100% 跑完 0 失败；墙钟 4.24 h；量化（2/4/8 bit）与 spike 抖动扫描行已在 results.jsonl（500 scene 行内含）；scene_acc 均值 0.996、慢读出 0.997（C13 物理版）；行数差异双方记录口径一致（任务书估算错误，非数据缺失）。小黑队列：04 rc_vs_deep → 05/06 → 07 → 08 串行。

## 2026-09-26 第二十一批：小黑 rc_vs_deep 领域特异性对打（"RC 不好用"的正面战场，已验收）

- [同事质疑·sim 判定] `results/rc_vs_deep/`（commit 74a732d，7945HX）：4 任务 × 4 臂（rc_tanh / rc_sin2 / MLP / linear）× 训练预算扫描 × 5 种子 = 480 行，**1 行 ok=false**（narma/rc_sin2/n_train=1000/seed=1 发散，ValueError inf——sin² 在 γ=1.0 边缘混沌区的已知不稳定性，已原样保留）| **核心数字（大预算/小预算）**：① NARMA NMSE：rc_tanh 0.135 胜 MLP 0.338、linear 0.354——**时序任务 RC 完胜**；② 信道均衡 acc：小预算 rc_sin2 0.640 vs MLP 0.495（**小样本效率高 15 个百分点**），大预算 rc_sin2 0.771 仍第一；③ 静态三分类：linear 0.987 > MLP 0.982 > rc_tanh 0.937 > rc_sin2 0.838——**RC 连线性臂都打不过，领域特异性实锤**；④ scene 全臂 1.0 饱和（任务太容易，下次需加难度） | **判定：假设成立——"RC 不好用"是场景选错的实证；我们的论文只主张时序时间模式负载，恰好在 RC 胜区** | ✅
- [诚实注记] sin² vs tanh 在此基准更全面：信道任务两者打平（0.640/0.771 vs 0.645/0.762），但小预算 NARMA sin² 明显差（0.744 vs 0.411）、静态也更差——与 designspace 的"sin² 略优 NARMA"对照，说明 sin² 的优势区在大数据+非线性任务，小数据正则敏感。论文里 sin² 的表述要限定条件。
- [验收] sanity 四项全过（标准见 TASK_REQUEST_20260926_rc_vs_deep.md）；行数 480/480；失败行 1 行符合"原样保留+回执说明"协议。中转夹已写 RECEIPT_rc_vs_deep_20260926.md。

## 2026-09-26 第二十二批：递归正在回流——衍射/空间光计算的 2026 新动向

- [格局更新] ① ReDON（arXiv:2602.23616，2026-02，Jiaqi Gu 组）：**递归衍射光处理器**——固定超表面 + EO 自调制非线性（GLU 启发的门控），"递归光学硬件复用"，图像识别/分割比前代 DONN 提升最高 20%；② Teğin et al.（arXiv:2602.19246，2026-02）：**多模光纤时空递归计算**——被动光纤环、光学系统零可训练参数、无电子反馈，混沌预测/动作识别/转向角/手术技能评估全打——实质是"物理递归"的 RC 变体 | **判定：连衍射社区都在 2026 年向"递归+自调制非线性"收敛——RC 的思想正在以别的名字回流主流光计算**。对同事质疑的补充弹药：商业化衍射网络里没有 RC 这个名字，但递归结构本身正在被重新发明；同时也提示**占用风险**：ReDON 的"EO 自调制非线性"与我们 EO 叙事邻近，但它的负载仍是图像、非线性是新增可训练模块而非器件物理 | ✅ 入 digest 版图
- [与我们格子的关系] 两者均不涉及：可调色散 GD、事件读出、雷达时序负载。Teğin 的 MMF 时空 RC 属于自由空间/空间 RC 集群（§四 Cluster 3）的 2026 延续，速度受限于空间光调制链，不构成威胁；可作为"物理递归"趋势引用。

## 2026-09-26 第二十三批：色散耦合物理二次审查（关键修正）+ 仿真 09 任务书已发

- [自我纠错·物理] 二次审查 digest §五 #8 发现**概念性错误并已修正**：异色脉冲互不干涉（拍频超出探测器带宽），**色散本身不产生伊辛耦合**——WDM 伊辛机被迫用 MZI/MRR 路由正是这个原因，CIM 能耦合是因为全同波长简并。修正后的两段式架构：① CBG GD = **碰撞调度器**（波长差→到达时序，决定谁与谁在非线性窗口相遇）；② 共享非线性元件（XPM/共享增益/χ²）提供实际 σ_iσ_j。GD 的角色从"耦合介质"降级为"耦合拓扑的可编程调度器"——叙事更弱但更诚实 | digest 已改 | ✅
- [仿真 09 已发小黑] `TASK_REQUEST_20260926_09_collision_scheduler.md`（中转夹）：纯 Python 先行研究——S1 理想碰撞图（3 档器件 D=1.3/25/156.5 ps/nm）、S2 GDR 对配对保真度影响（实测量级 1–10 ps）、S3 非线性 GD 剖面拟合三种目标耦合核（箱型/幂律/指数）、S4 器件现实性热图。含解析 sanity（d* = √2·σ_t/(D·Δλ) 逐行核对）。**排队在最后（05/06→07→08→09）**；完整退火仿真（10 号）等 09 结果再设计。
- [方法论记录] 这次纠错发生在任务书起草阶段（写 S1 公式时发现干涉项不成立）——"先写任务书公式、后发任务"的流程挡住了一个会浪费小黑 1 小时的错误方向。

## 2026-09-26 第二十四批：共享非线性混频机制选型（为仿真 10 储备）

- [机制盘点] 碰撞调度后提供 σ_iσ_j 相互作用的候选，按我们平台可达性排序：
  ① **测量反馈式（MF-CIM 变体，最现实）**：GD 调度碰撞 → 探测重叠脉冲的模拟邻居求和 → 电子只做符号/阈值更新 → MZM 再注入。色散的真实价值 = **把 Σ_j J_ijσ_j 的邻域求和在光域并行完成**，电子 MAC 数从 O(N²) 降到 O(N)——这是可辩护的角色，且全部用我们已有器件（CBG + MZM + FPGA，06 仿真框架可直接扩展）；
  ② **SOA 交叉增益/交叉相位（XGM/XPM）**：成熟分立器件、ns 响应、异色耦合天然（载流子共享）——**与 Wan 组相容性新接口**：他们有 QD SOA/激光器（UCSB/Intel 背景），"我们的 CBG 调度器 + 他们的 QD SOA 混频器"是比之前"光域线性层"更具体的合作切口；
  ③ **共享 OPO 增益竞争**：PIC-OPO 已实验示范（Marandi），但我们无 PPLN 工艺——远期；
  ④ **TFLN χ³ Kerr XPM**：TFLN 的 χ³ 弱（n₂ 比 SiN 低），长相互作用长度才够，边缘选项 | **判定：仿真 10 的混频机制选 ①（MF-CIM 变体），物理模型最简单且全部器件在手；②作为与 Wan 组合作的物理备选写入 digest §四** | ✅
- [合作点更新] digest §四相容性矩阵应加一行：CBG 碰撞调度器 × Wan 组 QD SOA（异色混频）——结构化伊辛的混合集成路线。

## 2026-09-26 第二十五批：仿真 10 的实例类选型（1D 幂律伊辛的物理叙事）

- [实例类调研] Rydberg 原子阵列的耦合是 1/r^6（van der Waals），一维反铁磁幂律伊辛链的基态是**周期晶体相（Z_n 序）**——物理上标准且有解析/数值基准可对（PXP 模型极限、iDMRG 相图，arXiv:2512.09040 显示 1/r^6 全模型基态相图仍在活跃争论中）| **仿真 10 的实例类定为**：① 1D 反铁磁幂律 Ising 链（α ∈ {1,2,3,6}，N=32–64，开放边界）——基态 Z_n 晶体结构有解析预期，退火对错一目了然；② 带距离权重的路径图 MAX-CUT（优化风味对照）。"物理启发的格点模型天然硬件"叙事的含义：我们不拼 Max-Cut 霸权（Mohseni 判决），而是演示**模拟物理系统本身**——量子模拟器类比（Rydberg 能做的耦合剖面，我们能用啁啾设计）| ✅ 叙事自洽性核查通过：这与"结构化伊辛"定位（digest §五 #8）和"不比精度比能效"主判据都不冲突
- [诚实的边界] 1D 幂律伊辛的基态问题**计算上不难**（多项式可解）——所以仿真 10 的卖点不能是"解难题"，只能是"演示器件物理可实现非平凡耦合剖面+退火动力学"。这个定位要在任务书里写死，避免日后叙事膨胀。

## 2026-09-26 第二十六批：编码方式三次审查（QUBO 强度编码）+ 仿真 10 骨架起草

- [自我纠错·物理②] 三次审查发现仿真 10 设计的又一个前提问题：异色自旋**不能相位编码**（0/π 相位在强度探测下不可读、异色无干涉项、符号信息丢失）。**可用方案 = QUBO 强度编码**（x∈{0,1} 脉冲有无，σ=2x−1 标准映射）+ 共享增益介质（SOA XGM / 共享 OPO 增益）：x_j=1 消耗增益 → 同窗口脉冲 i 幅度被调制 → 探测器直接读出加权"邻居点亮数" Σ_j J_ij x_j——**模拟邻居求和在强度域天然成立，无需相干接收**。动力学 = 光电混合 Hopfield 更新（电子只做逐点 sigmoid/阈值）| digest §五 #8 已补三次审查段 | ✅
- [仿真 10 骨架] `docs/sim10_taskbook_draft.md` 已起草（**DRAFT 未发布**，等 09 结果定稿）：架构 = QUBO 强度编码 + CBG 调度 + 唯象饱和增益混频 + 电子逐点更新 + β(t) 逆温 ramp；对照臂 = 理想 Hopfield / SA / 随机基线；sanity 含 α→∞ 极限应复现 Z_2 反铁磁序（≥0.99 否则模型 bug）、理想臂 ≥ 含噪臂的方向性检查、"若全面碾压 SA 先怀疑实例太易"的反作弊条款。
- [流程记录] 连续两次自查（色散≠耦合、相位编码不可行）都发生在任务书设计阶段——新方向的物理栈（色散调度→混频→编码→更新）每一层都必须过"异色不干涉"这一关；仿真 09 不受影响（它只研究碰撞几何，与编码无关）。

## 2026-09-26 第二十七批：光子 Hopfield 退火机先占核查（仿真 10 的新颖性边界）

- [先占核查] 光子 Hopfield 退火机**概念已被占**：Farhat & Psaltis 1985（光学 Hopfield 鼻祖）；Fan & Lin, Opt. Express 31, 21340 (2023)（被引 24，光子 Hopfield 解 Ising + 退火增强收敛）；Al-Kayed et al., Nature 648, 576 (2025)（Hopfield-inspired，200 GOPS，清单 #2 待全文） | **判定：仿真 10 的新颖性只能挂在"GD 调度产生可编程 Toeplitz 耦合"这一层——Hopfield 动力学本身、光电混合更新、退火日程全部是成熟件**。任务书草稿已符合此定位（卖点=啁啾可编程耦合剖面的器件物理演示），无需修改，但将来写论文时相关工作的这三篇必须引 | ✅
- [与 Al-Kayed 的划界] 他们的耦合矩阵靠通信 DSP 嵌入光回路（全可编程、通用），我们靠啁啾物理剖面（结构化、超低功耗模拟求和）——仍是"通用可编程 vs 结构化超低功耗"的互补叙事，等清单 #2 全文到手后核对 SI 细节再确认。

## 2026-09-26 第二十八批：Toeplitz×色散的进一步诚实化（仿真 10 新颖性最终边界）

- [概念核查] "色散实现 Toeplitz 算子"本质上是**光卷积的老概念**——任何横向滤波器/卷积核就是 Toeplitz 矩阵，微梳横向滤波（Xue 2018）与 CBG 光子 CNN（MDPI 2025，digest §五 #3）都是这一族；光卷积综述（IOE 2026, 10.67704/ioe.2026.260003）也明确"convolution = Toeplitz/im2col 结构化矩阵" | **判定：仿真 10 的增量被进一步压缩为一句话——"把啁啾可编程的 Toeplitz 核放进退火/反馈回路（而非前馈滤波）"**。前馈 Toeplitz 滤波是旧世界，反馈/退火动力学里的可编程结构化耦合才是新格子；这个表述精度恰好与批 25 的"器件物理演示，不拼霸权"定位一致 | ✅ 已是最诚实边界，不再需要压缩
- [流程判断] 新方向文献循环至此饱和：色散伊辛耦合线的物理栈（调度→混频→编码→更新）与新颖性边界（批 23–28）已全部固化，仿真 09 任务书已发、仿真 10 骨架已备。下一步等 09 数据，不再对该方向做无数据空转。

## 2026-09-26 第二十九批：docs 一致性通读（批 1–28 交叉核查）

- [一致性核查] 三份文档（rc_tutorial / ising_literature_digest / rq_evidence_log）关键数字互查：designspace（319.0/363.2/0.1328/0.1377）、Kong（2.6e-3/3.9e-3/160 GSa/s）、PIC-OPO（0.07±0.017）、ADC 调研（9/707、92.6 pJ）、rc_vs_deep 八格数字 vs `results/rc_vs_deep/summary.json` 逐一相符；批次引用（rq 第四至二十八批）全部存在；下载清单销项状态（#3/#5/#6）三处一致；先占地图五行状态与精读段一致。**未发现矛盾**。
- [旁路记录] 中转夹出现 PPT 会话的 HANDOFF（fig1 改收发链路）——按分工红线不处理；其架构描述（TX 拉伸光栅 + RX 压缩光栅 + 延迟环 RC + 慢 PD）与本会话教程 §5.1 的器件-RC 映射自洽，无需联动。

## 2026-09-26 第三十批：小黑 rc_vs_baselines 验收（含 sanity 偏差的诚实记录）

- [基线对打·sim] `results/rc_vs_baselines/`（commit 47d4583 区段，7945HX）：5 臂（rc_tanh / rc_sin2 / **ESN 稠密数字标准形** / **二阶 Volterra 信道经典基线** / ELM / linear）× NARMA / 信道（SNR 10/20/30 扫描）/ scene，900/900 行、0 ok=false | **核心数字（大预算）**：① NARMA NMSE：rc_tanh **0.117** 全场最优（rc_sin2 0.143、ESN 0.274、ELM 0.331、linear 0.334、Volterra 0.671）——**我们的掩码延迟环 SCR 打赢教科书 ESN**；② 信道均衡 SNR 扫描（5 种子均值±std）：SNR10 **linear 0.615 ≈ Volterra 0.613 > rc 0.571–0.579（RC 输）**；SNR20 **Volterra 0.774 > rc_sin2 0.762**（差 0.012，~1σ 内）；SNR30 rc_sin2 0.822 ≥ Volterra 0.820（打平）；③ **小预算段 RC 双臂全场最优**（0.61–0.63 vs Volterra 0.476、linear 0.540、ELM 0.548、ESN 0.407） | **判定（诚实版）：RC 在大预算信道任务上不占优——低 SNR 连线性都输、中 SNR 输 Volterra、高 SNR 打平；可辩护的护城河 = 小训练预算（校准成本）+ NARMA 类强非线性时序。论文禁用"RC 优于经典基线"的无限定表述** | ⚠️ sanity 偏差已记录（见下）
- [验收记录] 任务书 sanity「channel@SNR20 rc 两臂 ≥ linear/volterra」**未达成**（Volterra 0.7736 > rc_sin2 0.7621；rc_tanh 0.7533 ≈ linear 0.7540）。按纪律：双方 JSON 与本分析入档，不改任何数值；小黑推送时尚未写 05/06 回执（06 可能在跑），已在中转夹 RECEIPT 中说明并提醒。
- [数据质量注记] 1 行 ok=true 但 metric=NaN（narma/rc_tanh/n_train=100/seed=1，发散未被捕获），导致 summary 的 rc_tanh narma small_mean = NaN（聚合器用了 mean 而非 nanmean）——建议聚合器改 nanmean，原始行保留不动。
- [对零号稿的收紧] 信道均衡叙事从"性能优势"改为"**训练数据效率 + 免 DSP 的模拟前端**"：大预算精度 Volterra 可追平，但 Volterra 需要精确信道建模/大量校准数据，我们免校准——这才是与 OSP 叙事兼容的表述。

## 2026-09-26 第三十一批：零号稿对齐审查（只列清单不改原稿）

- [零号稿核查] `docs/zero_draft_alignment_review.md` 已写：① 可填充——§a 待补数字有 Murmann 硬数据（9/707、92.6 pJ/样本）、C13 物理版、数据效率三任务规律；② 需收紧——§b"同一本体论"段按 RQ4 判定改写（事件读出 vs 采样后端，SNN 可替换）、数据效率必须保留"小预算"限定（大预算 Volterra/linear 可反超）、禁止"首次 TFLN RC"句式；③ 可核销——威胁 #1（占据图完成，我们的格子空）、威胁 #3 部分核销（护城河收窄到 EO ns 速度，应用侧论证仍是缺口：多制式波形自适应匹配滤波）；④ 三个目标数状态盘点（缺口都不变，#3 建议加"调谐时间"指标）；⑤ 新增三条威胁（PIC-OPO 措辞纪律、Mohseni 判决、Volterra 边界）| ✅ 原稿未动，改动权在用户

## 2026-09-26 第三十二批：威胁 #3 应用侧论证（波形敏捷的认知雷达，含诚实边界）

- [需求侧文献] 认知雷达/波形敏捷是条令级需求（NATO STO-TR-SET-227、DTIC AD1183721；ML 驱动认知雷达综述 Springer 2026）：雷达需在跟踪/对抗中切换波形参数（载频、脉宽、PRI、脉压方式）。**关键诚实边界（NATO 报告原文级）**：SAR 成像过程中不能中途改波形参数，自适应主要发生在**跟踪段/驻留之间**——即 CPI 级（µs–ms）切换，这个档位热调（µs 级微加热器）就能做，EO 不是刚需 | **判定：我们的 EO ns 调谐护城河只在两个子场景成立**：① **高 PRF（≥1 MHz）逐脉冲波形敏捷**——脉冲间隔 <1 µs，热调跟不上，EO 是唯一路线；② **脉内重构**（chirp 中途的频谱整形/自适应陷波抗干扰）——ns 级刚需。论文动机段必须落在"逐脉冲敏捷 + 脉内重构"，不能笼统说"认知雷达需要可调" | ⚠️ 已写入零号稿对齐审查的威胁 #3 条目需按此细化（审查文档已含"多制式波形自适应"方向，此批给出时间尺度依据）
- [对目标数 3 的影响] "调谐时间"指标建议定为 **≤100 ns**（对应 PRF 1–10 MHz 的逐脉冲切换留 10× 余量）；若只做到 µs 级，与热调的差异化就只剩"省功耗"，叙事强度大减。

## 2026-09-26 第三十三批：对抗侧依据（DRFM 响应时间）锁定"逐脉冲敏捷"的硬度

- [对抗文献] DRFM 干扰机 = 捕获-存储-修改-转发雷达信号，商用件已宣称 **ns 精度操控**、环路延迟 sub-µs（Axellio/Microwave Journal 2025）；反 DRFM 的标准思路是**波形分集**（Lu et al., PIER 2010，被引 38）——雷达波形变化快于 DRFM 的捕获-重放环路，相干假目标就失效 | **论证链闭合**：在我方"模拟前端免 ADC"的叙事里，TX 逐脉冲变 chirp 率 → **RX 匹配滤波必须逐脉冲跟随**——数字路线改相关系数即可但那是 a) 段论证要替代的路线；模拟路线里只有 EO 调谐色散能 ≤1 µs 跟随 PRF ≥1 MHz 的敏捷波形。威胁 #3 场景①由此获得对抗侧硬依据：**调谐时间指标的物理对手是 DRFM 环路（~0.1–1 µs），不是热调** | ✅ 零号稿对齐审查威胁 #3 已可定稿（本次不再改文档，等用户处理清单一并改）
- [自检] 该论证依赖"RX 模拟匹配滤波"这个前提——若审稿人问"TX 敏捷为什么不用数字 RX"，回答回到 a) 段（ADC 结构性成本）+ 批 32 的时标表。逻辑闭环无新缺口。

## 2026-09-26 第三十四批：Catch-22 原文精读（清单 #4 销项，"RC 不好用"的最强反方弹药诚实入库）

- [文献判定·反方] Zhang, Y. & Cornelius, S. P., "Catch-22s of reservoir computing", **Phys. Rev. Research 5, 033213 (2023)**（用户下载全文，已精读）| 两个 catch-22 的硬数字：① **标准 RC（ESN）**：多稳态系统（磁摆、Kuramoto）basin 预测存在"可预报性相变"——warm-up 必须覆盖**几乎整个瞬态**（能量跌到势垒高度之下才行），否则 NRMSE=O(1)、甚至不收敛到任何吸引子；贝叶斯优化超参 + N_r 加倍到 600 均无解。**讽刺点：等 warm-up 够了，预测已无意义**；② **NGRC**：warm-up 只需 k−1 步、精确非线性下 98.6% basin 准确率（单条训练轨迹也有 85%），**但对读出非线性的不确定度极端敏感——磁摆模型磁铁坐标 1% 扰动（ε=0.01）准确率从 ~100% 跌到 <50%（随机猜测 33.3%），ε=10⁻⁵ 已有可见影响**；多项式特征（6188 项）发散、RBF×1000 只有 53.4%；Kuramoto n=9 多项式/三角特征 ≈ 随机、精确非线性 >99%（n=83 高维 basin 97.5%）；③ 普适警示：**训练拟合完美 ≠ 自治预测正确**（训练初值都能预测错 basin，自治误差累积），已训练 (NG)RC 的稳定性是公开问题 | **这是"RC 不好用"争议最严格的反方文献，必须诚实入库** | ✅
- [划界：为什么不动摇我们的负载] ① 两个 catch-22 都针对**多稳态系统的闭环 basin/吸引子预测**；我们的负载是**开环单吸引子信号处理**（驱动输入→特征→读出，无吸引子选择、无自治迭代）——已跑的全部对打（designspace/rc_vs_deep/rc_vs_baselines）都在开环区，不在本文打击面内；② **论文纪律新增：永不主张我们的蓄水池"学会/预测动力学"（closed-loop forecasting），所有 demo 保持开环特征提取**——若未来想做雷达波形外推类 demo，先重读本文 Fig. 8；③ 本文 §VIII 顺带佐证我们的 designspace 结论：标准 RC 对激活函数选择**鲁棒**（vs NGRC 对特征的脆弱）——sin² vs tanh 只差 12% MC 与此一致，器件非线性选型不是标准 RC 架构的生死项。
- [反转利用：catch-22 恰是我们的论据] NGRC 的 catch-22 原文表述 = "**除非已知道系统的精确非线性，否则动力学学不会**"。物理器件恰恰**就是**精确非线性本身——光子器件的 sin²/tanh/χ² 响应不是拟合近似而是地面真值，**器件实现的特征映射天然零模型失配**。这给出两个可用表述：① "physical NGRC" 叙事——器件物理做 NGRC 特征层，绕开 1% 敏感度陷阱（小黑 07 rc_vs_ngrc 仿真可引用此框架）；② **伊辛副演示的直接论据**——basin/吸引子选择正是伊辛机的本职工作，而 Catch-22 证明学习型代理在此类问题上结构性脆弱，物理退火机（物理嵌入真实能量地形）没有失配问题——副演示动机从"追赶热点"升级为"学习代理被证明不行的格子"。
- [对 digest 的回灌] 本文与 Mohseni 判决（批 14）、Shahi 对比（批 13）构成"诚实性三角"：RC 在时序信号处理胜区有系统证据（Shahi+我们对打），在多稳态 basin 区有结构弱点（本文），在通用优化硬件上不如数字（Mohseni）——三个边界都写进论文相关工作，审稿人无法用任何一篇反将我们。

## 2026-09-26 第三十五批：Al-Kayed Nature 2025 正式版+SI 精读（清单 #2 销项）

- [文献判定] Al-Kayed et al., "Programmable 200 GOPS Hopfield-inspired photonic Ising machine", **Nature 648, 576–584 (2025)**（正式版+SI 全文精读，替代预印本口径）。**SI 新增的关键事实（预印本精读时没有或需修正）**：
  ① **200 GOPS 的诚实口径（SI §S2 原文）**：该数字"仅适用于级联 TFLN 调制器执行的核心模拟光学运算（EO 非线性+逐元乘），**不适用于端到端反馈环**"——实验室实际每步迭代被 AWG 上传（满内存 ~9.76 s）+ RTO 捕获（0.81 s）主导，真实端到端迭代率 ~0.1 Hz；Table 1 的 TTS 全是剔除 AWG/RTO 后的**估计值**，星号数字（如 353.64 µs）假设了尚未实现的流水 DSP ASIC（引用 Ciena WaveLogic 6 Extreme 作为商用可行性依据）；
  ② **DSP 流水线构成**：深度 115 = 20-tap 抗混叠 + 51-tap FFE + 3 拍求和 + 51-tap RRC 成形，@200–500 MHz 时钟 → 反馈延迟估计 230–500 ns；@128 GBaud 时系统频响 64 GHz 处每迭代衰减 ~5 dB，FFE 残余误差累积使高频自旋衰减翻转——**DSP 嵌回路不是锦上添花而是高波特率的生存条件**；
  ③ **自旋数上限 = AWG 内存**（2²⁰ 样本，@2.415 SPS = 434,176 符号），且负值编码需时间交织辅助符号、可用符号再减半——**耦合矩阵的存储/寻址全部在电子域**，他们的扩规模路线本质是电子的（更大内存/ASIC/更多通道）；
  ④ 更新方程定式：σ(t+1) = (I−βJ)σ(t) − αh + ξ（SI Eq.14，H 上的随机梯度下降）；Pramanik 收敛理论：残差上界 ∝ η(c²+Nσ_v²)，递减步长调度可证以概率 1 收敛但**实验未实现**；
  ⑤ **噪声退火的定量曲线**：400 节点方格子收敛迭代数 32 GBaud=144 → 96/106 GBaud=88/89（最优）→ 128 GBaud=240（劣化）——"噪声有益"存在最优波特率；大格子实验 1000 迭代只到 97.2%，仿真显示 143×143 需 2,653 迭代、203×203 需 5,366 迭代才能到基态；
  ⑥ 功耗分解（SI §S4.2）：QD SOA 1.19 W（700 mA×1.7 V，实验值）、双 MZM 模组 ~200 mW（含驱动）、微梳 ~1 W（集成投影）；当前单通道 **48 GOPS/W**（vs H100 FP64 95.6），并行 16 通道投影 868 TOPS @2.34 TOPS/W，拉伸值 9.3 POPS @5.9 TOPS/W（>3×10⁷ 自旋）。
- [划界定稿：通用可编程 vs 结构化超低功耗，新增"内存墙"维度] CMIM 正式版强化而非削弱了批 27–28 的划界：① 我们的副演示不碰它的解质量/可编程性/波特率（全线 Nature 级）；② **但 CMIM 暴露了它路线固有的三堵墙**——耦合存储器墙（AWG 内存定自旋上限）、逐迭代 DAC/ADC 转换墙（TTS 里的 4.1 µs 前馈+DSP 延迟）、负值编码开销墙（符号减半）——**我们的色散调度路线把耦合存进器件几何（啁啾剖面），三堵墙全没有**；这是副演示"结构化耦合物理演示"定位的最终表述，与批 28 的"啁啾可编程 Toeplitz 放进退火回路"互洽；③ 对主线（RC×色散×雷达）零冲突——CMIM 无记忆维度、不做时序处理。
- [对 06 仿真的理论支援] SI §S1.4 给了我们 06 任务书缺的理论锚点：① 更新方程的 H-梯度下降诠释（α=自反馈/β=耦合的物理意义 = 步长与哈密顿量梯度的相对权重）；② Pramanik 残差界 ∝ N——解释了 06 里大 N 收敛变难；③ 递减步长+噪声调度（η_k=η_0/(k+1)^r，r∈(0.5,1]）是 06 没扫的维度，可作为 06b 增补实验的候选（低成本、有理论保证背书）。
- [与 Wan 组相容性新证据] CMIM 的 QD SOA 是 Innolume 分立件（1.19 W、NF 5.6 dB），其并行化路线（S4）明确需要**微梳源 + QD SOA 阵列**——Wan 组（QD 激光器/SOA on Si）正是这类器件的供应方；且 SI 承认 QD SOA 功耗占大头、bulk SOA 可降到 ~100 mW 但 NF 变差——**片上 QD SOA 的功耗/NF 优化是 Wan 组能直接贡献的点**。我们的合作切口（批 24：CBG 调度器×QD SOA 混频器）与此兼容且不重叠：他们供"增益/混频"，我们供"色散调度"。
- [引用更新] 论文里 Al-Kayed 条目全部改用正式版引用（Nature 648, 576 (2025)，DOI 10.1038/s41586-025-09838-7）；其 ref 15 = Li et al. ACS Photonics 2024（清单 #1，CMIM Table 1 给出其口径：6.25 GBaud、16,384 自旋方格子、TTS 800.74 s）——等 #1 到手后核对。

## 2026-09-26 第三十六批：约束回灌 rc_tutorial（批 30–35 落盘）

- [文档] `docs/rc_tutorial.md` 三处更新：① §六新增第 6 条"vs Catch-22 结构弱点"（划界+反转利用，FAQ Q1 同步）；② §七新增 7.1"应用场景的时间尺度纪律"（CPI 级热调可及 ❌ / 逐脉冲敏捷 ✅ / 脉内重构 ✅ 三档表 + DRFM 环路 0.1–1 µs 对抗依据 + 目标数 3 加 ≤100 ns 指标）；③ §七新增 7.2"开环纪律"（永不主张闭环动力学预测）+ 第 6 条补 CMIM"三墙"对照（内存墙/转换墙/负值编码墙）。教程至此与批 30–35 全部结论对齐。

## 2026-09-26 第三十七批：Li ACS Photonics 2024 自助获取（清单 #1 部分销项）+ 顺带捕获两个新条目

- [获取记录] 正文仍付费墙（$48），但经桌面浏览器过了 Cloudflare 拿到：① 官方摘要全文；② **SI 全文**（figshare 免费，`ph4c00003_si_001.pdf` 已存中转夹，转文本 `.tmp/li2024_si.txt`）；③ **Correction 内容**（DOI 10.1021/acsphotonics.4c00855，2024-05-29：仅替换 Figure 3——CSR 稀疏矩阵格式/FPGA MAC 架构图，**不涉及自旋数/延迟/能效数字**）。清单 #1 降级为中优先级残项（只剩正文 Methods/结果讨论未读），不再阻塞。
- [文献判定·先占] Li, Z. et al., "Scalable On-Chip Optoelectronic Ising Machine Utilizing Thin-Film Lithium Niobate Photonics", ACS Photonics 11(4), 1703–1714 (2024)，中山大学 Jie Liu/SCNU Changjian Guo 组 | **双方案**：Scheme I = TFLN 芯片 + FPGA 稀疏 MVM（CSR 格式 + 可配置并行累加器/气泡层），2048 自旋、**迭代延迟 1.78 µs**；Scheme II = **单个片上 FMZM 同时做线性乘法+非线性变换**（强度调制域），16,384 自旋 MAX-CUT（自称当时片上 IM 最大规模） | **器件参数（SI S1）**：X-cut NanoLN 400 nm TFLN/3 µm BOX，VπL=3.8 V·cm 推挽，56 Ω，**3-dB EO 带宽仅 ~30 GHz**（vs CMIM 的 HyperLight 110 GHz——CMIM 快 4 个数量级的器件根源） | **负值编码（SI S4）**：强度调制无法直接取负——差分双信号法（I⁺+I⁻ 消交叉项留 W⊗x），矢量构造成 [+w,−w,…] DC 平衡对（8B/10B 式），**容量减半——与 CMIM 的辅助符号墙完全同构，"负值编码墙"是 IM/DD 路线的通病，我们的三墙表述由此获得第二个独立实例** | **能效（SI S5）**：Scheme I 51.9 pJ/MAC+35 pJ/symbol（2.6 GBaud）；Scheme II 42.6 pJ/MAC（6.25 GBaud）；Scheme II 预测（100 GBaud、1 V 驱动、FPGA DSP 累加）**2.4 pJ/MAC**——注意这个 2.4 pJ/MAC 是 TFLN EO 路线能效的合理锚点，写能效对标时可用 | ✅ 对仿真 10 的意义：耦合矩阵实现细节（CSR+差分编码）已够支撑相关工作段的写作，正文残项不阻塞任何当前决策
- [对 CMIM 对照表的修正] CMIM Table 1 里 Li 2024 的口径（6.25 GBaud、16,384 自旋方格子、TTS 800.74 s）与 SI 一致；CMIM 引用它时说"only basic benchmark problems"——但 Li 的 1.78 µs 迭代延迟是 FPGA 全流水实测值，比 CMIM 的实验室实测（~0.1 Hz 端到端）**实在得多**；写综述时要给 Li 2024 公平待遇：它是片上 TFLN IM 的第一枪，器件带宽是其后所有指标的瓶颈。

## 2026-09-26 第三十八批：⚠️ 新威胁——Ding/Pei "双 MZM NGRC"（ACS Photonics 2026）占用"物理 NGRC"概念

- [文献判定·威胁，高] Ding, B., Pei, L. et al., "Architecture-Level Simplification and Nonlinearity Enhancement of Photonic Reservoir Computing with Only Two MZMs", **ACS Photonics 13(3), 705–714 (2026-01-21)**，北京交通大学裴丽组（摘要+SI 预览精读，正文付费墙）| **核心概念：用 MZM 内禀 sin² 响应替代二次函数，在输入层实现最高 7 阶非线性变换——明确自称 "MZM-based NGRC"** | 数字：NCE 信道均衡 SER 5.56×10⁻⁴（仅 16 特征维）、NARMA10 NMSE **0.155**（22 特征维，岭回归）/ 0.105（随机森林读出）；特征维 ~20 vs 传统 RC 数百-千节点；SI 含 Lorenz63 observer | **这正是批 34 我们从 Catch-22 推出的"physical NGRC"叙事的实验先占**——"器件非线性=精确高阶特征"不再是空格子 | ⚠️
- [划界与定量对照] ① **未占**：片上集成（他们是分立光纤 MZM 系统，集成只是展望）、可调色散 GD（NGRC 无真实循环动力学，时延维靠 k 个离散延迟）、事件读出、雷达负载；② **定量**：他们的 NARMA10 0.155（22 维实验）**比我们 designspace/baselines 的 rc_tanh 0.117/rc_sin2 0.143（仿真）更差**——我们掩码延迟环 SCR 在数字上反而占优，但实验 vs 仿真不能直接比，论文里只能并列引用不能宣称优势；③ 他们也是"sin² 非线性有效"的盟友证据（强化我们 designspace 的 sin² 臂合理性）；④ **对 rc_tutorial §七.4"片上 NGRC 化"的修订**：该方向表述必须从"空格子"改为"BJTU 已实验演示 MZM-NGRC（分立、固定延迟、基准任务），我们的差异化=色散 GD 提供波长复用连续延迟抽头（他们需 k 个分立延迟）+ 片上 + 可调 + 事件读出"。
- [连锁发现·待查] Crossref 同检索带出：**"Dynamic-scaling photonic reservoir computing via adaptive semiconductor-optical-amplifier nonlinearity", Chinese Optics Letters (2026)**（DOI 10.3788/col202624.081901）——"动态缩放+自适应 SOA 非线性"听起来逼近"可调"叙事，下一批核查其摘要。

## 2026-09-26 第三十九批：小黑 06 ising_nonlinearity 验收（"MZM sin² 兼做 Ising 机"成立，附失效区地图）

- [仿真验收·sim] `results/ising_nonlinearity/`（commit ad40f37，7945HX，全量 1465 s）：4 激活（tanh/sin/laser/clip）× α∈{0.3,0.5,0.8,1.0} × β∈{1,2,5,10} × noise∈{0.1,0.5,1.0} × 图（3reg 反铁磁=max-cut / dense 自旋玻璃）× N∈{100,1000} × 4 实例 = **3072/3072 行、0 ok=false** | **sanity 全过**：tanh/sin/clip 最优 E/E_BK = 1.093/1.089/1.093（config 均值口径，≥0.95 ✅）；laser 全局均值 0.555 最低且 3reg/N=1000 塌到 0.251——阈值死区预期物理 ✅ | **口径记录**：summary.json=config 均值口径；单行极值口径 1.1086/1.1072/1.0758/1.1057——两口径结论一致，双方入档不改数 | 小黑回执 HANDOFF_FROM_7945HX_06 与我方独立分析一致；中转夹已写 RECEIPT_06 | ✅
- **任务 B 答案：我们的 TFLN MZM sin² 能兼做 Ising 机**——最优点（α=0.3, β=10, 3reg）sin 1.089 ≈ tanh 1.093 ≈ clip 1.093，器件非线性零成本。但有三个超出回执的物理发现：
  ① **sin 失效区 = dense + β=5 + 大噪声 + N=1000（配对 sin−tanh −0.97）**：sin 非单调（|z|>π/2 折返），稠密图耦合和 ~√N 大信号时有效增益变号——**器件设计约束：MZM 臂必须增益定标把输入箝在单调区**；
  ② **sin 占优区 = 3reg + α=0.8 + β=1 + 小噪声（+0.68）**——稀疏弱耦合小信号区 sin 优于 tanh；
  ③ **噪声-TTS 权衡**：sin 最优点 noise=0.1 → E/E_BK≈1.07、TTS≈16 迭代；noise=1.0 同质但 TTS≈210（慢 13×）——噪声帮助的是坏工作点（CMIM"噪声有益"叙事），好工作点不需要大噪声；laser 在 dense/N=100 有 0.704 不垫底，死区问题主要在稀疏大图。
- [对文档的回灌] digest §一 06 复现段的 quick 档观察被全量扫描证实并扩展（失效区/占优区地图是新内容）；仿真 10 骨架的"唯象饱和增益混频"臂设计可参考①——混频器输入摆幅定标是必须建模的器件约束。

## 2026-09-26 第四十批：小黑 07 rc_vs_ngrc 验收（Catch-22 在我们硬件仿真上的完整复现 + hybrid 裁决）

- [仿真验收·sim] `results/rc_vs_ngrc/`（commit c3ef837，7945HX，全量 42.5 s）：7 臂（rc_tanh/rc_sin2/esn/ngrc/volterra/**hybrid**/linear）× 3 任务 = **1080/1080 行** | **sanity**：narma rc_tanh 入区间 ✅、channel rc>0.65@≥500 ✅、ngrc lorenz 73% 发散=预期 ✅ | **两处偏差双方入档不改数**：① rc_tanh lorenz 13/60 发散、esn 2/60（全在 λ≤1e-4——弱正则下读出条件数爆炸，闭环预测无人免疫）；② 5 行 ok=false（narma inf 发散，原样保留）| **第三处（小黑发现）**：聚合器 `lorenz_diverged_frac` bug（先滤后均恒为 1）——正确口径 rc_tanh 22%/esn 3%/ngrc 73%/hybrid 65%；已授权小黑单独 commit 修聚合器、不动原始行 | 中转夹已写 RECEIPT_07 | ✅
- **头条数字（λ=1e-4 切片，我方复算）**：① NARMA：**hybrid 全场最优**（3000→0.086）> rc_tanh（0.093）> rc_sin2（0.156）> esn（0.257）> linear > volterra ≈ ngrc（0.66）；② channel：小预算 rc 双臂最优（50→0.597/0.575），大预算 volterra 反超（3000→0.776 vs rc_sin2 0.770）——与 rc_vs_baselines 互洽；③ **Lorenz 闭环：ngrc 稳定时 VPT≈5.9–6.2 Lyapunov，rc_tanh 仅 0.2–0.6，但 ngrc 73% 配置发散**；④ hybrid 核心问题"RC 循环分量能否稳住 NGRC 病态"——**裁决：不能**（λ=1e-2：4/20 vs 5/20；λ=1e-4：15/20 vs 19/20，仅边际改善；λ=1e-6 皆 20/20 全发散）；hybrid 的价值在 NARMA 互补（有界池+多项式特征），不在抗发散。
- **科学意义（三重新证据）**：① **Catch-22 Model III 在我们仿真上复现**——NGRC 二次特征=Lorenz 精确非线性，稳定时碾压（VPT 6 vs 0.4），73% 发散率就是它的 catch-22；② 我们 rc 闭环 VPT 低同样是已知弱区——**开环负载定位获得自家数据支撑**（批 34/36 的红线不再是纯文献防御）；③ NARMA 上 NGRC 全面落后（0.66 vs 0.086）说明"精确非线性优势"是任务依赖的——NARMA 的 10 步延迟结构里循环记忆比多项式阶数值钱。论文表述：闭环预测基准让给 NGRC/数字，开环信号处理是我们的领土，hybrid 是两者之间的诚实地带。

### 待办（下一批）

- 主线：精读 Li 2024 正文（`D:\BaiduSyncdisk\Temp_transit\ph4c00003.pdf`，清单 #1 全销项）；
- 核查 COL 2026 "Dynamic-scaling PRC via adaptive SOA nonlinearity"（批 38 连锁发现）；
- 检查中转夹（小黑 08 interface_readout 回执；小黑顺手修 07 聚合器 diverged_frac 的 commit）；
- 备选：06b 递减步长调度增补任务书起草（DRAFT 不发）；把批 39–40 回灌 rc_tutorial §六（hybrid 裁决 + sin Ising 失效区）。

## 2026-09-26 第四十一批：小黑 08 interface_readout 验收（事件接口能效代理胜出，但 LIF 饱和需加难）

- [仿真验收·sim] `results/interface_readout/results.jsonl`（commit 76c18b1，7945HX）：3 噪声 × 5 种子 ×（12 uniform + 2 lc + 1 lif）= **225/225 行**，每行 arm/acc/energy_proxy/noise/seed 齐全；quick 档基线 4 行与全量对应单种子值**逐位吻合**（lif 1.000/469、lc_b4 0.5625/663、fs0.5_b4 0.852/4096、fs1.0_b4 0.760/8192）✅；小黑尚未发 HANDOFF_08，本批为我方主动验收 | ✅
- **头条（noise=0.05，5 种子均值）**：① **LIF acc 0.999±0.001 @ E_proxy 469**——同等精度 uniform 需 fs0.25_b8（0.971 @ 4096，**8.7×**）；同精度下最优 uniform 是 fs0.25_b2（0.979 @ 1024，**2.2×**）；同位数 b4 最优（0.935 @ 2048，**4.4×**）；② **lc 全面失败**：lc_b4 0.546 @ 664（精度远低于 LIF 且能耗更高），lc_b8 随噪声恶化（0.699→0.311、E 2608→7030——噪声触发更多事件，事件接口的"活动正比能耗"特性反噬）；③ **任务书疑点 2 坐实**：fs1.0_b4 0.753 < fs0.5_b4 0.849（非单调=岭回归高维正则不足，数字后端已知陷阱，全量复现非单种子假象）；④ fs2.0 各行与 fs1.0 完全相同（采样率封顶 Nyquist，预期行为）。
- **RQ4 判据裁决（部分支持）**：任务书预测"事件接口能耗低 1 个数量级"——**对同精度 uniform 为 8.7×（接近 10×）✅，但对最优低配 uniform 仅 2.2× ❌**。如实记录：事件接口的能效优势依赖比较口径，论文表述应为"在等精度约束下事件接口能耗代理低 4–9×"，不主张无条件数量级。
- **⚠️ 新行动项（任务书疑点 1 触发）**：LIF 在三档噪声（≤0.1）下 5 种子全部 ≥0.998——**任务对时间编码太简单，判据失效**。按任务书预案"需加更难噪声档再议"：拟起草 08b（noise 0.2/0.35/0.5 + 可选 LIF 神经元数 32/16 降维），排在小黑 09 之后。在本结果出齐前，论文不得引用 LIF 的绝对精度值，只能用"事件接口在现有难度下不成为瓶颈"的弱表述。
- [口径记录] uniform_fs2.0 与 fs1.0 逐行相同（Nyquist 封顶）；E_proxy 为代理量（样本×位 / 事件×(log2L+8) / 脉冲×8），不是物理能耗，论文图注必须写明"proxy"。

### 待办（下一批）

- 主线：精读 Li 2024 正文（`.tmp/li2024_main.txt` 285 行起，清单 #1 全销项）；
- 核查 COL 2026 "Dynamic-scaling PRC via adaptive SOA nonlinearity"；
- 起草 08b（更难噪声档）任务书 DRAFT，排 09 之后；
- 检查中转夹（小黑 HANDOFF_08、07 聚合器修复 commit、09 进度）；
- 备选：06b 递减步长调度增补任务书起草；批 39–40 回灌 rc_tutorial §六。

## 2026-09-26 第四十二批：Li ACS Photonics 2024 正文精读（清单 #1 全销项）——Table 2 延迟分解 + WDM 展望里的合作切口

- [精读记录] `Temp_transit/ph4c00003.pdf`（用户下载，FUDAN UNIV 机构访问版）全文，转文本 `.tmp/li2024_main.txt` 526 行读完。清单 #1 **全部销项**（摘要+SI+Correction+正文齐）。
- [关键增量 1·Table 2 延迟/能效分解（正文独有，SI 无此表）]：**Scheme I**（FPGA KU115 + 2.6 GS/s ADC/DAC）：2.6 GBaud，N=2000/Nnz=41,980，**传输延迟 0.5 µs + 运算延迟 1.28 µs = 1.78 µs/迭代**，51.9 pJ/MAC(L)+35 pJ/symbol(NL)；**Scheme II**（PC i7-8700 + AWG/RTO）：6.25 GBaud，N=16,384/Nnz=81,408，**传输延迟 0.4 s（！）+ 运算延迟 370 µs**，42.6 pJ/MAC；**Scheme II 预测**（FPGA 实时化 + 100 GBaud 器件）：传输 0.5 µs + 运算 **2.14 µs**，2.4 pJ/MAC。→ **他们自己承认 Scheme II 的 0.4 s 传输延迟来自 AWG/RTO/PC 远程通信**——与 CMIM 端到端 0.1 Hz 同病，"电子域搬运数据"是第二条独立证据链；且 Scheme II 运算延迟随 Nnz 线性增长（TDM 串行），16,384 自旋已需 370 µs/迭代（vs Scheme I 2000 自旋 1.78 µs）——**TDM 用时间换规模，规模-速度不可兼得**。
- [关键增量 2·G22 细节] 2000 自旋/19,990 边（W 对称 41,980 非零），20 试最优 13,052 = **97.6% BK(13,359)**，全部 ≥96.6%；α=0.4/β=0.8。**自旋幅度不均匀性在 900 迭代后仍存→局域极小陷阱**，他们自己引的解法是动态参数控制（其 OFC 2021）+ Leleu 辅助误差变量（PRL 2019）——**与我们 06b 递减步长调度任务书（Pramanik/Al-Kayed SI 路线）是同一类思路的独立佐证**，06b 立项依据 +1。
- [关键增量 3·Discussion 的 WDM 展望 = 我们的切口] 他们明确写：① TDM+SDM：4 组 100 GHz MZM 并行 → 4×10¹¹ mult/s，但光子器件尺寸限制空间扩展；② **TDM+WDM：不同波长注入携带不同权重的光载波可做 WDM-IM，但"可重构片上光谱调制器实现多波长权重加载会占用片上空间资源，波长维度不完全独立于空间维度"**——他们看到了 WDM 权重加载的价值（PD 直接探测多波长=相位不敏感强度累加、零额外能耗 fan-in）却卡在权重加载器件上。**我们的啁啾布拉格光栅/CBG 恰恰是波长相关的色散延迟器件——"波长→延迟抽头"的映射是他们缺的拼图**（注意：他们要做的是波长→权重，我们是波长→延迟，用途不同但同属"无源色散元件提供波长维度"家族；合作叙事：他们缺可重构波长元件，我们有色散元件平台）。此点强化批 35 的 Wan 组相容性结论。
- [关键增量 4·公平待遇要点] ① Scheme I 的 1.78 µs 是 FPGA 全流水实测（0.5 µs 传输+1.28 µs 运算），比 CMIM 端到端 ~0.1 Hz 实在四个数量级以上——综述里 Li 2024 应列为"片上 TFLN IM 第一枪+最低实测迭代延迟"之一；② 他们明确选择 EO 调制非线性而非全光非线性（引石墨烯吸收/Marandi ReLU），理由：全光需额外元件+脉冲泵浦——**这恰是批 35 三墙之外的第四论证角度：纯 IM 圈自己认为 EO 非线性够用，全光非线性的卖点不在 IM 而在信号处理/RC**；③ checkerboard 非 NP-hard 他们自己承认（引 Cipra），只用 G22 撑 NP-hard。
- [对账] SI S5 能效数字（51.9/42.6/2.4 pJ/MAC）与正文 Table 2 一致 ✅；CMIM Table 1 转述的 Li 口径（6.25 GBaud/16,384 自旋）✅；Correction 仅换 Figure 3 不动数字 ✅（Figure 3=CSR/MACC 架构图，正文 Methods 描述与 SI S3 一致）。
- [下载清单状态] **全部销项**（#1 正文到手、#2–#6 此前已清）。DOWNLOAD_REQUESTS_20260926.md 已更新。

### 待办（下一批）

- 核查 COL 2026 "Dynamic-scaling PRC via adaptive SOA nonlinearity"（批 38 连锁发现，清单空后首个开放项）；
- 起草 08b（更难噪声档+LIF 降维）任务书 DRAFT，排 09 之后；
- 检查中转夹（小黑 HANDOFF_08、07 聚合器修复 commit、09 进度）；
- 备选：06b 递减步长调度任务书（Li 2024 G22 幅度不均+动态参数控制=新立项依据）；批 39–40 回灌 rc_tutorial §六。

## 2026-09-26 第四十三批：COL 2026 Ds-PRC 全文核查（威胁判定：低，不占格子）+ 小黑 HANDOFF_08 对账

- [文献判定·威胁低] Huang, Q. et al.（UESTC 文峰组）, "Dynamic-scaling photonic reservoir computing via adaptive semiconductor-optical-amplifier nonlinearity", **Chinese Optics Letters 24(8), 081901 (2026-08)**，开放获取（researching.cn 官方 PDF 已存 `.tmp/col2026_dsprc.pdf`）| 全文精读 | **核心：SOA 增益饱和做激活函数 + sigmoid 门控自适应输入缩放（a_t≈0.5 收敛），MNIST 97.6%@100 mA、低功耗模式 85.9%@40 mA、Mackey-Glass RMSE 0.0176** | **判"不占格子"的依据**：① 记忆核是**数字 ESN**（W_in/W_reservoir/谱半径 0.8/2000 节点全在软件里演化，SOA 只是逐节点查表的激活——Thorlabs SOA1117S 分立件实测曲线）；② "dynamic-scaling"=输入功率定标校准工作点，**不是色散/延迟/结构可调**——与我们"可调色散 GD"完全两回事，但"adaptive PRC"这个词在输入定标层面已被占；③ 缩放控制数字实现，自承 O-E-O 转换；④ 任务=MNIST/MG 基准，无雷达、无事件读出、无片上集成 | **盟友价值**："输入摆幅必须匹配非线性甜区"获得独立实验证据（其 a_t 自校准 ≈ 我们批 39 sin 失效区的"增益定标"约束——SOA 路线也需要同样的定标纪律）；其 97.6% vs 光纤色散 FF-RC 93.4%（其 ref 18, Zhang/Wen/Zou Opt. Express 2023——注意：**光纤色散前馈 RC 已存在**，固定色散+DFB-LD，MNIST 93.4%，我们的差异化=片上+可调+啁啾 GD 轮廓，引用时需列为先占）
- [连锁入档] 其 ref 19 Nie et al., Optica 11, 1690 (2024)"集成激光分级神经元无反馈环 RC"（92.3% 数字识别）——feedforward 无环 RC 第二例，rc_tutorial §5.3 先占表可补但非必须。
- [对账·小黑 HANDOFF_08 与我方批 41 的两处口径差]（双方入档，不改数）：① **RQ4 判据表述**：小黑口径"LIF 能耗代理≈均匀采样 1/9（469 vs fs0.5_b4 的 4096）→预测成立"；我方口径"fs0.5_b4 精度仅 0.85 远低于 LIF 0.999，**等精度比较**应为 fs0.25_b8（0.971@4096）→8.7×，对最优低配 uniform 仅 2.2×→部分支持"。分歧在比较基准选择，非数据冲突；论文采用等精度口径（4–9×），小黑的 1/9 作为乐观上限并列引用。② **疑点 1 处置**：小黑认为 LIF 饱和本身即"无损编码的实证，不需加难"；我方维持任务书预案——饱和状态下**噪声-精度权衡曲线不可测**，RQ4 的鲁棒性主张缺 0.2+ 噪声档数据，08b（noise 0.2/0.35/0.5 + LIF 降维）继续起草但降为低优先级。两点都不是返工项。

### 待办（下一批）

- 起草 08b（更难噪声档+LIF 降维）任务书 DRAFT（低优先级，排 09 后）；
- 检查中转夹（小黑 07 聚合器修复 commit、09 collision scheduler 进度）；
- 备选：06b 递减步长调度任务书（Li 2024 G22 幅度不均+动态参数控制=新立项依据）；批 39–43 回灌 rc_tutorial / digest（COL Ds-PRC + HANDOFF_08 口径差）。

## 2026-09-26 第四十四批：08b 加难档脚本+任务书（已发小黑，排 09 后）

- [sim·任务下发] 新脚本 `simulations/08b_interface_readout_hard.py`（不改 08，导入复用其任务生成/前端/读出；输出独立目录 `results/interface_readout_hard/`）：噪声 {0.10,0.20,0.35,0.50} × 5 种子 ×（uniform 3 臂 = 08 最强参照 + lif_N{16,32,64}）= 120 行。文献机 quick 冒烟 2 行通过（115 s）：**noise=0.35 时 lif_N64 0.950@404 vs uniform_fs0.25_b8 0.956@4096**——LIF 退出饱和（难度到位 ✅）且等精度能耗仍 ~1/10 ✅。任务书 `TASK_REQUEST_20260926_08b_interface_readout_hard.md` 已放中转夹，排 09 后，预计小黑 <10 min。
- [设计要点] ① noise=0.10 锚点行用于跨脚本一致性检验（应复现 08 的 lif ~0.999/469）；② 08b 的 lif 随机数流取同一 rng 前 n 行（N=64 时与 08 同分布但实现路径不同，若有数值差异如实记录不对齐）；③ 科学问题：LIF 精度崩溃点 + 时间编码所需神经元数下限。

### 待办（下一批）

- 检查中转夹（小黑 07 聚合器修复 commit、09 collision scheduler 进度、08b 回执）；
- 备选：06b 递减步长调度任务书 DRAFT（Li 2024 G22 幅度不均+动态参数控制+Pramanik=立项依据齐）；批 39–44 回灌 rc_tutorial / digest。

## 2026-09-26 第四十五批：06b 退火调度脚本+任务书（已发小黑，排 08b 后）

- [sim·任务下发] 新脚本 `simulations/06b_ising_schedule.py`（导入 06 复用图生成/能量/SA 基准，只换退火调度）：5 调度（linear 锚点 / pow_r{0.5,0.75,1.0} Pramanik 幂律 / beta_ramp CIM 式耦合爬升）× act{sin,tanh} × 2 区域（fail_dense: dense+β5+noise1.0+N1000+α∈{0.3,0.5,0.8}；ctrl_3reg: 3reg+β1+noise0.1+α0.8）× 4 inst = 160 行。**冒烟 4 行通过并与 06 归档逐点对账**（dense 0.083 vs 归档 0.091=n_runs 子集差；3reg 0.208 vs 0.209 吻合；bk 种子一致）。任务书 `TASK_REQUEST_20260926_06b_ising_schedule.md` 已放中转夹，排 08b 后。
- [科学问题] 调度能否把 sin 失效区救回 tanh 水平 + 对照区是否被帮倒忙——答案直接决定仿真 10 混频器臂是否必须内建增益定标/调度电路（Li 2024 动态参数控制 + Al-Kayed SI Pramanik 两条文献线索的自家验证）。

### 待办（下一批）

- 检查中转夹（小黑 07 聚合器修复 commit、09 进度、08b/06b 回执）；
- 备选：批 39–45 回灌 rc_tutorial / digest（hybrid 裁决、sin 失效区、COL Ds-PRC、HANDOFF_08 口径差、光纤色散 FF-RC 先占）。

## 2026-09-26 第四十六/四十七批：小黑进度检查（无新回执）+ 批 39–45 回灌教程与 digest

- [中转夹/git] 无新 commit、无 HANDOFF_08/08b/06b 回执——小黑应在跑 09 collision scheduler（或 PPT 线）。07 聚合器修复 commit 亦未到。下载清单保持全销项。
- [文档回灌] `docs/rc_tutorial.md` 四处：① §六第 2 条补自家 rc_vs_ngrc 数据（hybrid 最优 0.086、Lorenz 闭环裁决、hybrid 稳不住 NGRC 病态）；② §六第 4 条补 interface_readout 全量结果（LIF 8.7×/2.2× 双口径、lc 失败、"等精度 4–9×"措辞纪律）；③ §六第 6 条补 Catch-22 自家复现（73% 发散、开环定位获自家数据支撑）；④ 新增 **§5.4 非 TFLN 近邻先占表**（光纤色散 FF-RC / Nie 2024 无环激光神经元 / COL Ds-PRC——"adaptive PRC"一词已被输入定标层占用，我们的"可调"表述需区分）+ Ds-PRC 与 06 sin 失效区的"工作点定标共同纪律"互证。
- [文档回灌] `docs/ising_literature_digest.md` 两处：① §一"我不懂→自己复现"段第 4 条更新为 06 全量完成 + 新增第 5 条（失效区/占优区地图、噪声-TTS 权衡、06b 后续）；② §二 Al-Kayed 段 Li 2024 数字升级为正文 Table 2 口径（Scheme I 1.78 µs 实测公平待遇、Scheme II 0.4 s 传输自证、2.4 pJ/MAC 能效锚点、WDM 缺元件=我们切口）。

### 待办（下一批）

- 检查中转夹（小黑 09 进度、08b/06b 回执、07 聚合器修复 commit）；
- 若长时间无回执：通读 rc_tutorial 全文做一致性校对（五处改动后），或起草仿真 10 混频器臂设计草案（消化批 39/42/45 的器件约束）。

## 2026-09-26 第四十八批：rc_tutorial 一致性校对（回灌后）

- [文档] 校对修正 4 处过时表述：① §七.5「08 仿真验证中」→ 08 全量已验证（4–9× 口径）；② §七.6 仿真候选编号修正（09 已被 collision scheduler 占用，改指 digest §五 #8 + 06/06b 状态）；③ §九证据索引批次计数 二十批→四十七批；④ §九仿真数据清单补 08 全量/07/06 状态。中转夹与 git 仍无小黑新回执。

### 待办（下一批）

- 检查中转夹（小黑 09 进度、08b/06b 回执、07 聚合器修复 commit）——**当前唯一阻塞项全部在小黑侧**；
- 若仍无回执：起草仿真 10 混频器臂设计草案（消化批 39/42/45 器件约束：增益定标、调度、幅度不均）。

## 2026-09-26 第四十九批：仿真 10 设计草案（DRAFT 入 docs，未下发）+ Correction 重复下载确认

- [用户下载] 10.1021/acsphotonics.4c00855（Li 2024 Correction）——批 37 已判定（仅换 Figure 3 不动数字），中转夹两份为同一文件，无需再读。下载清单维持全销项。
- [设计固化] `docs/sim10_design_draft.md`：两段式架构（CBG 碰撞调度 × SOA XGM 共享增益混频）的完整退火机设计稿。要点：QUBO 强度编码（禁相位编码）；邻居求和在强度域天然成立（对照 CMIM 三墙）；唯象混频器模型内建"摆幅箝单调甜区"约束（批 39 sin 失效区 + Ds-PRC 自适应定标 = 跨平台共同纪律的自家验证设计）；退火调度等 06b 选型；问题集限晶格/幂律（不碰全连接 Max-Cut）；4 实验臂（理想/GDR 退化/拟合核/失箝对照）；验收锚点含"臂 D 必须失效否则模型有误"的可证伪设计。**依赖 09 + 06b 结果，齐后定稿发任务书。**

### 待办（下一批）

- 检查中转夹（小黑 09/08b/06b 回执、07 聚合器修复 commit）；
- 若仍无回执：新文献检索一轮（arXiv 2026-09 新稿：dispersion/tunable delay RC、structured Ising photonic、event-based readout 关键词），保持文献面不落后。

## 2026-09-26 第五十批：文献例行扫描（2026-07 后新稿）——零新威胁

- [核查 1] Nature 站 s44335-026-00081-5（2026-07-21，"Delay-based photonic reservoir computing on TFLN with time–wavelength-coupled virtual nodes"，Deyang Kong et al.）——**经作者+标题比对确认 = 已销项的 Kong 2026 MP²-RC**（digest §三，批 11 精读，威胁中低，不占格子），非新论文。Nature 页有反爬未再抓全文（无必要）。
- [核查 2] arXiv:2602.10066（Devata et al., 2026-02，v2 2026-07）"Programmable and nonvolatile computing with composition tuning in TFLN"——电化学锂化非易失调折射率做 MVM 权重（MZI/微环，前馈 matmul，纯仿真，1.6% 平均相对误差）。**零威胁**（无 RC/无色散/无时域动力学），但作为 **TFLN 非易失调谐路线**存档：与我们的 EO ns 级调谐互补（非易失=一次性校准/修整，EO=实时重构），若未来 CBG 需要出厂级色散修整可引此路线；威胁面不变。
- [状态] 文献面维持"真风险清单清空"（digest §三结论未被本轮扫描动摇）。下载清单全销项。

### 待办（下一批）

- 检查中转夹（小黑 09/08b/06b 回执、07 聚合器修复 commit）——09 回执是 sim10 定稿的最后依赖；
- 若仍无回执：把 sim10 设计草案里"2D 格点→1D 波长轴折叠映射"的开放设计点做解析推导（纯纸面：行主序映射下近邻耦合在谱距域的杂散结构分析）。

## 2026-09-26 第五十一批：sim10 开放设计点解析解决（2D→1D 波长折叠否决，2D 改为弱耦合链束）

- [推导] 2D 方格近邻折进 1D 波长轴的可行性——**解析否决**：① 图带宽定理：L×L 方格任意排序必有边长 ≥L（行主序已最优），纵向近邻钉死在谱距 d=L；② 单调 Toeplitz 核（高斯，数值表 L=8/16/32 × w=1.5–12）：各向同性 J(L)/J(1)=0.4 需 w≈0.75L，代价是杂散/目标能量比 4–14×——各向同性与低杂散不可兼得；③ **诚实替代：弱耦合 1D 链束**（w≲1.5 行间自然解耦，d≥2 行内耦合=多跳短程，恰匹配 09 S3 箱型核目标①）——硬件原生模型类，非妥协；④ 翻案条件=09 S3 若能做出支撑集 {1,L} 梳状核再议（v1 不指望）。已写入 `docs/sim10_design_draft.md` §5a，问题集定稿为：1D 箱型链 + 1D 幂律链 + 弱耦合链束。
- [意义] sim10 设计草案至此无开放设计点，只剩 09/06b 两个数据依赖。

### 待办（下一批）

- 检查中转夹（小黑 09/08b/06b 回执、07 聚合器修复 commit）；
- 若仍无回执：arXiv 定向检索第二轮（structured Ising / Rydberg-inspired photonic coupling / power-law coupling analog simulator——为 sim10 问题集补文献定位句）。

## 2026-09-26 第五十二批：spQUBO 先占判定（结构化耦合叙事有正式先占，划界三条）+ 例行扫描第二轮

- [文献判定·先占，中] Yamashita, H. et al., "Spatial QUBO: Convolutional Formulation of Large-Scale Binary Optimization with Dense Interactions", arXiv:2506.24008（v1 2025-06, v2 2026-01，NTT 系，摘要级）| **核心：为 SPIM（自由空间 SLM 伊辛机）提出空间卷积结构 QUBO——平移不变耦合作为光子 IM 天然问题类；证明任意 spQUBO 可归约到 2D 卷积并免复用 SPIM 实现；应用=布局/聚类等距离问题；自承卷积结构可用 FFT 数字高效计算** | **对 sim10 的影响**：我们"Toeplitz/距离依赖耦合=结构化伊辛天然硬件"的叙事不再是空白——划界三条（自由空间 SLM Hz–kHz vs 片上波长域 GHz；2D 空间卷积+布局聚类 vs 1D 链/幂律物理模型；FFT 可算→结构化耦合不构成问题类排他，主张必须落在速率/能效与免 SLM/复用上）。已写入 `docs/sim10_design_draft.md` §1 | 威胁面：不占"波长域 GD 调度耦合"的格子（SPIM 靠空间光调制，无波长维度），引用作正式先占+划界。
- [连锁] 百万自旋综述 arXiv:2607.13446（已读）大概率已引 spQUBO——综述引用表对账时可顺带确认；本扫描其余命中（Rydberg 原子 ladder、超导量子比特耦合）与光子平台无关，不展开。

### 待办（下一批）

- 检查中转夹（小黑 09/08b/06b 回执、07 聚合器修复 commit）；
- 若仍无回执：spQUBO 全文精读（HTML 版可及，确认其 SPIM 耦合实现的细节与我们划界是否稳固——摘要级判定升级为全文级）。

## 2026-09-26 第五十三批：spQUBO 全文精读（判定升级为全文级，发现 MVP 互补定位点）

- [精读记录] arXiv:2506.24008v2 HTML 全文（已存工具输出档）。要点：① **纯理论**——理想化 SPIM，数值 demo 用动量退火在 M1 MacBook 上跑，原文"scarcely mentioned specific optical implementations"；② SPIM 光学部分算的是 **H=xᵀJx 标量**（傅里叶光学+参考图相关），自旋更新全在电子域（SLM+图像传感器 OEO 环）；③ **关键发现：他们原文承认 SPIM 算不了 MVP（J·x），把"基于卷积结构的光学 MVP"列为 future research**——我们的碰撞调度+共享增益架构在模拟域读出的恰是逐自旋局域场 h_i=Σ_j J_ij x_j，**正好补上他们缺的那块**；④ 平移不变/循环耦合在空间域早有先例（其 ref 28/29/31：2D/3D 近邻自旋玻璃、Fourier-mask SPIM），我们的新性只剩"波长域连续 GD 调度"；⑤ 相干相位编码 vs 我们强度/QUBO 免相干。
- [定位升级] sim10 §1 定位句改为："**SPIM 光学读能量、我们光学读局域场——结构化耦合的两条互补光学路线，我们是片上/GHz/免相干的那条**"。这个互补表述比"划界防御"更强：spQUBO 从威胁转为可引用的需求证明（卷积耦合 IM 的光学 MVP 是公认空白）。
- [对 digest 的回灌建议] digest §五 #8 先占核查段可补一行 spQUBO（连同其 ref 28 循环矩阵 IM），但 §五 #8 的三次自审结论（GD 不产耦合、两段式、QUBO 强度编码）不受影响——SPIM 能读 H 靠同波长干涉，与我们异色约束不冲突。

### 待办（下一批）

- 检查中转夹（小黑 09/08b/06b 回执、07 聚合器修复 commit）；
- 把 spQUBO 互补定位回灌 digest §五 #8（与 rc_tutorial §七.6 同步）；
- 若仍无回执：起草"光学 MVP vs 光学能量读出"对比段的写法建议（供零号稿相关工作段用）。

## 2026-09-26 第五十四批：百万自旋综述引用对账 + "光学 MVP vs 能量读出"写法建议

- [对账] 百万自旋展望（Aadhi/McMahon/Shastri/Yamamoto，arXiv:2607.13446）全文检索：**未引 spQUBO**（"SPIM 算不了光学 MVP"这个空白尚不为综述层面所知——我们互补定位的新鲜度确认）；其 Box 1 分类学（空间=衍射/MZI 网格；波长=微环权重库/交叉阵列；时间=延迟线+级联 EO 调制）**不含色散 GD 调度耦合**——权威综述层面我们的格子是空的，这是比逐篇先占核查更强的空白证据；另记：该综述认可 TFLN SLM/EO 调制器为"高可重构 IM 的硬件进展"（可引）。
- [文档] 新建 `docs/optical_mvp_positioning.md`：相关工作段写法建议（一句话版+展开版 4 段+诚实边界 3 条+引用清单），供零号稿用；不改零号稿本身（11 条更新清单仍待用户拍板）。

### 待办（下一批）

- 检查中转夹（小黑 09/08b/06b 回执、07 聚合器修复 commit）；
- 若仍无回执：rc_tutorial §九证据索引补 spQUBO/optical_mvp_positioning 条目（小修），或 arXiv 第三轮扫描（event-based photonic readout / level-crossing ADC photonics——为 RQ4 接口叙事补文献面）。

## 2026-09-26 第五十五批：小黑 09 collision_scheduler 验收（✅ 369/369，三个科学头条+一个混叠洞察）

- [仿真验收·sim] `results/dispersion_ising_coupling/`（commit cb745fc，7945HX）：S1 180 + S2 180 + S3 9 = **369/369 行** | sanity：① d*=√2σ_t/(DΔλ) 理论公式逐行 0 误差、146 可测行 meas vs theory 最大 2e-16 ✅；② S2 无 A>0 零偏差行 ✅；③ S3 9/9 not_worse_than_linear ✅ | 四联图渲染正常 ✅ | 中转夹已写 RECEIPT_09 | ✅
- **头条 1（核可合成性）**：**指数核 e^(−d/3) 分段 GD 拟合误差 0.001（比最优线性好 100×）；幂律 d^(−1.5) 0.059；箱型 box2 0.2915≈线性基线（优化无改善，物理不可合成——锐利截断被高斯重叠平滑禁止）**。sim10 问题集目标①从"箱型"改述"短程指数/高斯截断"；批 51 的 2D 否决进一步加固（梳状核同属锐利族）。
- **头条 2（GDR 容限量化）**：参考=我们 CBG 档（N=32/Δλ0.2/D1.3/σ_t10ps）：A=1ps→偏差 1.4–1.7%；**A=3ps（我们实测量级）→~6%（max 10%）**；A=10ps→~32%。sim10 臂 B 验收锚点定为"GDR 3ps 档 E/E_BK 降 <10%"。
- **头条 3（混叠洞察，S2 副产品）**：p_gdr=Δλ=0.2nm 档偏差恒为机器零（sin(2πi+φ)≡sinφ 共模相消）——**周期=自旋波长间隔的 GDR 无害**。器件 actionable：**实测我们 CBG 的 GDR 周期比测幅度更重要**（有害区=2.5–5×Δλ；若实测周期恰在有害区才需要担心那 6%）。
- **头条 4（耦合程可调性）**：d*∈2.7–435（D=1.3 我们 CBG，σ_t/Δλ 可调）vs 高 D 器件 ≤3.6——**低 D 反而是耦合程设计最灵活的档位**（反直觉但解析显然）；S4 feasibility N=32 全网格绿灯。
- [文档] sim10 设计草案新增 §10（09 结果回灌：核族选型、臂 B 锚点、混叠洞察）。sim10 数据依赖只剩 06b。

### 待办（下一批）

- 检查中转夹（小黑 08b/06b 回执、07 聚合器修复 commit、HANDOFF_09）；
- 06b 到后：定稿 sim10 任务书发小黑；
- 备选：把"GDR 周期混叠"写进 rc_tutorial §七（器件测量纪律）或 L 系任务备注。

## 2026-09-26 第五十六批：HANDOFF_09 对账 + GDR 测量纪律回灌 + 第三轮扫描（OET 综述入档）

- [对账] HANDOFF_FROM_7945HX_09 与我方批 55 独立验收**数值全部一致**（369 行、sanity 三项、GDR 3ps≈5–7%、S3 误差）。小黑透明披露两处实现 bug（S1 插值→解析反演；S3 参数化钉死→sigmoid 参数化），均为出数前修复、非数据问题，✅ 无返工。**一处 prose 口径差异入档**：回执"d* 从 ~1 到 ~870"与 summary.json（D=1.3 档 max 435.14）差 2×——回执散文可能混入 FWHM/半峰口径，数据文件无误；引用时一律以 summary.json 的 2.7–435 为准。
- [文档] rc_tutorial 新增 **§7.3 器件测量纪律**（GDR 混叠洞察：测周期比测幅度重要；有害区 2.5–5×Δλ；到手先傅里叶分析 τ(λ) 残差周期谱）。
- [文献入档·综述] Han, S., Shen, W., Gu, M., Zhang, Q.（USST）, "Integrated photonic synapses, neurons, memristors, and neural networks for photonic neuromorphic computing", **Opto-Electronic Technology 1(3), 250011 (2025-12)**，OA 综述 | 价值：① 2025 年底 IPNN 全景综述（突触/神经元/忆阻器×相干/并行/衍射/RC 四架构），相关工作段可引；② 其 RC 节转述前馈 RC 60 GHz/211 TOPS/41 TOPS/W（能效对标语境）；③ **其 spiking 节全部是神经元级实现（可激发激光器/PCM 微环/自脉动），没有接口级事件读出讨论**——我们"读出接口本体论"（uniform/LC/LIF，08 仿真）的框架在综述层面仍属空白，RQ4 叙事的文献面稳固 | 威胁：无（综述不占格子）。
- [扫描] 其余命中（事件视觉边缘综述、神经形态光子学能效对比）与接口级读出无关，不展开。

### 待办（下一批）

- 检查中转夹（小黑 08b/06b 回执、07 聚合器修复 commit）；
- 06b 到后：定稿 sim10 任务书发小黑；
- 备选：OET 综述 RC 节精读（确认 60 GHz FF-RC 的出处是否与已入档的 Zhang/Wen/Zou 同一篇，避免重复计数先占）。

## 2026-09-26 第五十七批：Wang 2024 片上光子 NG-RC 先占判定（"片上 NGRC 化"叙事的最强实验先占，威胁=高，划界五条）

- [文献判定·先占，高] Wang, K. et al.（CUHK，Chaoran Huang 组）, "Ultrafast silicon photonic reservoir computing engine delivering over 200 TOPS", **Nat. Commun. 15, 10841 (2024)**，DOI 10.1038/s41467-024-55172-3，被引 129，PMC11686264 全文已读 | **架构：SOI 芯片，8 条离散延迟线（16.7 ps 步进=60 GBaud 符号周期，1.18 mm Si 波导）→ 星型耦合器（9 进 45 出，0.04 mm²，含延迟线共 2 mm²）→ 非线性=探测器平方律（Eq.4：每个 PD 输出=常数+线性+二次多项式特征的混合，即光学实现的 Volterra 特征展开）→ 数字读出（实验用 256 GSa/s RTO；光学读出方案=MRR 权重库+BPD 热调，未实测）** | 数字：Santa Fe NMSE **0.029**（仅 45 特征，Fig 3d 自称最小维度+最快速度的 SOTA）、NCE、NARMA10、COVID-19 X 光分类；**211 TOPS、5.1 W、41 TOPS/W**（比 H100 的 0.15 TOPS/W 高两个数量级）；可扩 >5000 输出节点、可 WDM；输入调制器是分立 TFLN（LIOBATE 40 GHz，Vπ≈3 V）；容差论据：星型耦合器任意满秩传输矩阵都行、读出训练吸收；高阶多项式：级联输入调制器可实现 3–4 阶（Supplementary Note 9）。
- **对我们的影响（需立即修订 rc_tutorial §七.4）**：rc_tutorial "片上 NGRC 化"叙事此前记录的最强先占是 Ding/Pei 2026（分立光纤组件，Nat. Mach. Intell.）和 EPFL arXiv:2404.07857（自由空间 SLM）——**Wang 2024 是片上+实验+60 GHz+Nat. Commun. 四重占据，比两者都强，实质上压缩了"片上 NGRC"大格子的空白度**。剩余划界五条（全部可辩护）：① **延迟轴：他们 8 条固定离散延迟线（硬连线 60 GBaud 符号率锁定），我们色散 GD 连续且可调（CBG 调 D 即调延迟分布）**；② 混合域：他们空间域星型耦合器（满秩矩阵，无结构），我们波长域 GD 调度（结构化、可设计核——09 结果恰好证明结构化核的价值）；③ 平台：SOI 芯片+分立 TFLN 输入调制器 vs TFLN 原生（电光系数非线性/MZM 啁啾在片）；④ 读出：256 GSa/s RTO 数字读出 vs 事件读出（08/08b 线）；⑤ 负载：基准任务（Santa Fe/NARMA）vs 雷达时间模式（ISAL/M4 线）。
- [盟友面] 其容差论据（任意满秩混合矩阵+训练读出吸收）对 GD 混合同样成立——可直接引用为我们的宽容差论据的实验支撑；其"光学读出提案（MRR 权重库）未实测"与我们"读出接口开放问题"同病，相关工作段可同列。
- [口径纪律] Wang 2024 的 Santa Fe 0.029 是**实验实测**（60 GBaud、45 特征）；我们 rc_tanh 仿真的 0.117–0.143 与 Ding/Pei 实验 0.155 的既有对照口径不变——任何横向对比必须标"实验 vs 仿真、维度数、符号率"三要素，禁止裸比 NMSE。
- [对 OET 综述的对账] 批 56 记录的 OET 综述 RC 节"60 GHz/211 TOPS/41 TOPS/W"数字确认出自 Wang 2024（非光纤 FF-RC 的 Zhang/Wen/Zou）——两处引用同源，不重复计数先占。

### 待办（下一批）

- 检查中转夹（小黑 08b/06b 回执、07 聚合器修复 commit）；
- 把 Wang 2024 回灌 rc_tutorial §5.4（第四家非 TFLN 先占/最强片上 NG-RC）、§七.4（差异化五条）、digest §三第 9 条（光学 NGRC 段交叉引用）；
- 若仍无回执：arXiv 第四轮扫描（TFLN star-coupler / analog Volterra / photonic feature map——Wang 2024 同族普查，防再漏档）。

## 2026-09-26 第五十八批：光子 NG-RC 同族普查（5+1 家族谱）——FM-NGRC 占"梳+色散=波长复用延迟抽头"格子，§七.2 差异化再收窄

- [普查动机] 批 57 Wang 2024 同族防漏档扫描，沿 NLPO 引文 [7,8,28,29] 展开族谱。**结论：光子 NGRC 已是一个 6 家的小家族，NRL（Cox/Redding 组）独占 3 家**——"物理 NGRC"赛道正在快速拥挤化，我们的定位句必须升级为"在该家族内划界"而非"发现空白"。
- **族谱（按复用域）**：① 时间域：Cox 2024（光纤 Rayleigh 背向散射干涉混合+平方律读出，Chaos 34, 073111，arXiv:2404.07116，observer 任务）；② **频率域：Cox/Murray/Hart/Redding 2025 FM-NGRC（APL Photonics 10, 036122，arXiv:2411.09624，实验）**；③ 空间域自由空间：EPFL/Gigan 2024（Light: Sci. Appl. 2025，毛玻璃散斑）；④ 空间域片上：Wang/Huang 2024（Nat. Commun. 15, 10841，SOI 星型耦合，批 57）；⑤ 空间域片上：Cox/Redding 2026 NLPO（arXiv:2606.14052，耦合波导阵列混合，仿真，电信均衡）；⑥ 混合：Ding/Pei 2026（双 MZM sin²，分立光纤，Nat. Mach. Intell.）。
- [文献判定·先占，高] **FM-NGRC（APL Photonics 2025，实验，全文已读）——与我们最近的一家**：架构=2 激光载波 × 2 台 MZM（quadrature 偏置=线性编码、近 null 偏置=二次编码）→ EO 梳（9 齿，15.411 GHz 间隔，MZM+2 相位调制器产生）→ **100 km DCF 色散补偿光纤（每齿 GDD=200 ps）把相邻齿延迟恰好一个符号** → Waveshaper（Finisar 4000A）逐齿加权=**模拟域读出层** → 平衡探测；5 GS/s 实时信道均衡 SER ~2e-3，18 维特征向量（9 延迟×2 阶），特征向量可按任务解析设计（可解释性卖点）。| **占掉的格子**：① "梳+色散=波长复用延迟抽头"（此前 rc_tutorial §七.2 记的 Xue 2018 概念先占升级为**实验先占**）；② **训练式模拟读出也被占**（Waveshaper 逐齿权重+BPD）——§七.2 原表述"差异化只剩 D 可调+训练式读出"中的后者不再成立。| **仍空的划界（收窄后五条）**：① 色散元件=**100 km 台式 DCF**（固定 GDD、分立、不可调）vs 我们毫米级片上 CBG、**EO 可调 D + 啁啾连续 GD 轮廓**；② 延迟结构=离散等距齿（梳间隔锁定符号率）vs 连续 GD 曲线可设计核（09 结果）；③ 系统级=台式（2 激光器+4 调制器+100 km 光纤+Waveshaper）vs 单片 TFLN；④ 负载=电信均衡基准 vs 雷达时间模式；⑤ 事件读出无。| 盟友价值：其"特征向量可按任务解析定制"论据与我们的可调 D 叙事同向（他们靠换光纤/梳间隔，我们靠 EO 调 D——便利性差一个量级）。
- [文献判定·先占，中] **NLPO（arXiv:2606.14052，NRL+Sandia，仿真）**：PIC 版 NGRC 电信均衡器——螺旋延迟线组（ΔL=(T0/Ros)c/ng，离散抽头）+ 耦合波导阵列/星型耦合混合 + MRR 权重库+BPD（全光链路提案）；50 GBd PAM-4、免 LO 利用相位信息、虚拟过采样 250 GS/s、仿真把 IM/DD 链路从 1.6 km 延到 51.2 km。**占用**："PIC NGRC 做电信均衡"的应用格子（我们是雷达，不冲突）；**强化**："电信均衡单点商业化"叙事（§4.1）——电信均衡已同时被 FF-RC、FM-NGRC、NLPO 三家光子 NGRC 瞄准，恰好佐证我们避开该赛道的正确性。
- [文档动作] rc_tutorial §七.2 差异化表述更新（训练式读出已占）；§5.4 表注：FM-NGRC/NLPO 与 Wang 2024 同属"物理 NGRC 家族"，引用时三家并列、划界用"家族内差异化"框架。

### 待办（下一批）

- 检查中转夹（小黑 08b/06b 回执、07 聚合器修复 commit）；
- 把 FM-NGRC/NLPO 回灌 rc_tutorial §5.4 表 + §七.2、digest §三第 9 条族谱段；
- 若仍无回执：查 FM-NGRC 引文 [42-44]（频率复用 RC 三家：Butschek 2022 OL 等）确认"频率复用 RC"与"频率复用 NGRC"的先后关系，避免相关工作段写错。

## 2026-09-26 第五十九批：频率复用 RC 血统链核查（批 58 遗留项销项）+ 1 篇存档

- [血统链确认] "频率/波长复用 RC"自 2021 起有完整实验血统（非 NGRC）：Lupo/Butschek/Massar 2021（光子 ELM 频率复用，Opt. Express 29, 28257）→ **Butschek 2022（OL 47, 782，25 根梳齿同时编码神经元态，Massar 组）** → Li 2023（可扩展波长复用 RC，APL Mach. Learn. 1, 038105）→ **Cuevas/Kuse 2025（微梳 Kerr 孤子+光纤腔频率复用 RC，Nanophotonics 14, 3063，德岛大学+刘骏秋）** → FM-NGRC 2025（批 58，频率复用 NGRC）。**结论：相关工作段不得暗示"频率复用 RC 是我们的想法"——频率复用本身是成熟路线；我们的格子只剩：色散 GD 作为延迟结构本体（非齿载波复用）+ EO 连续可调 + 雷达负载 + 事件读出。** FM-NGRC 引文 [42–44] 先后关系无误（频率复用 RC 在前、频率复用 NGRC 在后），批 58 族谱成立。
- [文献存档·威胁低] Arabieh et al. 2026（arXiv:2609.12212，2026-09-10，仿真）：同步脉冲驱动腔（重复频率=腔环程）频率复用 RC 平台研究——反常色散弱非线性区 vs 正常色散双稳态；三阶色散+拉曼诱导的光谱对称破缺使信息处理容量近翻倍；双稳区分支跳变限制稳定运行。**对我们的价值**：腔 RC 的色散/拉曼物理与我们 GD 器件无关，但其"光谱对称破缺提升容量"的定量思路可借鉴到 CBG 啁啾轮廓非对称性研究（备选仿真灵感，不排期）。
- [口径固化] rc_tutorial §5.4/§七.2 与 digest 族谱段已含本链要点（批 58 已写）；本批仅补血统链时间戳，无需再改正文。

### 待办（下一批）

- 检查中转夹（小黑 08b/06b 回执、07 聚合器修复 commit）；
- 若仍无回执：第五轮扫描转向"片上非线性×新方向"主线——光子伊辛机最新进展（2026 年实验）与我们 sim10 定位的交叉核查。

## 2026-09-26 第六十批：小黑 08b interface_readout_hard 验收（✅ 120/120，噪声-精度权衡曲线补全，能耗优势边界收窄到 noise≤0.35）

- [仿真验收·sim] `results/interface_readout_hard/`（7945HX 推送，merge f57cec5）：4 噪声档 {0.1,0.2,0.35,0.5}×5 种子×6 配置（uniform: fs0.25_b2/fs0.25_b8/fs0.5_b8；lif: N16/N32/N64）= **120/120 行** | 锚点：noise=0.10 的 lif_N64 = **0.9979±0.002 @ E=390**，复现 08 的 ~0.999/469（E 略低=低噪声下伪触发更少，方向自洽）✅
- **权衡曲线（acc 均值@E_proxy）**：

  | arm | E | n=0.1 | n=0.2 | n=0.35 | n=0.5 |
  |---|---|---|---|---|---|
  | lif_N16 | 77 | 0.792 | 0.685 | 0.494 | 0.333 |
  | lif_N32 | 185 | 0.955 | 0.912 | 0.752 | 0.563 |
  | lif_N64 | 390 | **0.998** | 0.992 | 0.939 | 0.832 |
  | uniform fs0.25_b2 | 1024 | 0.980 | 0.926 | 0.890 | 0.822 |
  | uniform fs0.25_b8 | 4096 | 0.968 | 0.970 | 0.955 | **0.941** |
  | uniform fs0.5_b8 | 8192 | 0.934 | 0.926 | 0.915 | 0.888 |

- **头条 1（能耗优势量化+边界）**：noise≤0.35 区间 lif_N64 对 uniform_b8 的能耗比 = 4096/390 ≈ **10.5×**（精度 0.939 vs 0.955，LIF 略低但同量级）；**noise=0.5 极端档 LIF 最高仅 0.832，任何 N 都够不到 uniform_b8 的 0.941——等精度比较失效，能耗优势主张必须加"噪声 ≤0.35（本任务族）"边界**。措辞纪律更新：原"等精度下低 4–9×"修订为"**噪声中等（≤0.35）时等精度区间能耗代理低 4–10×；极端噪声（0.5）下 LIF 绝对精度封顶 0.83，uniform 8bit 以 0.94 反超——事件接口的能耗优势不覆盖极端噪声场景**"。
- **头条 2（LIF 精度崩溃点/神经元数下限）**：N=16 全噪声档崩溃（最高 0.79@n0.1）；N=32 可用（0.955@n0.1 但 n0.35 掉到 0.75）；**N=64 才达饱和**——下限答案：N≥32 起步、N=64 达标。
- **头条 3（uniform 过采样反噬复现）**：fs0.5_b8（8192 维）全噪声档**劣于** fs0.25_b8（4096 维）（0.934 vs 0.968 @n0.1）——与 08 的"维度越高噪声累积越多"一致；b2 在 n0.1 反而最高（0.980）——低比特量化在中低噪声下正则化效应，备注入档。
- [口径] 08b 回答了两个遗留问题（崩溃点、神经元下限），同时给出能耗优势的上边界——rc_tutorial §六.4 待回灌修订。

### 待办（下一批）

- 检查中转夹（06b 回执、07 聚合器修复 commit、HANDOFF_08b）；
- 写 RECEIPT_08b 入中转夹；rc_tutorial §六.4 口径修订（能耗优势加噪声边界+神经元下限）；
- 06b 到后：定稿 sim10 任务书。

## 2026-09-26 第六十一批：IPIM 全连接 10 万自旋预印本（06b 调度实验的实验文献锚点 ✅）

- [文献判定·盟友，中] Chen/Zhang et al.（重庆大学+NUS+中大刘洁组——Li 2024 TFLN IM 同组）, "Integrated photonic Ising machine with full connectivity for ultra-large-scale combinatorial optimization", Research Square 预印本（2026-09-09 上线，全文已读） | 架构：SOI 芯片（**热光** Si MZM+Ge-Si PD，光学部分仅 0.065 mm²）+ 电子 MVM 反馈环（时分复用单调制器逐自旋更新——与 Li 2024 Scheme I 同构）；**JA-SID 算法**（稀疏 SMA/逆稀疏 ISMA/分解 MDA：二元耦合矩阵只存稀缺元位置、乘法变加法，D=0.999 密图省 1000× 缓存/2000× FLOPs）→ 稀疏+稠密各 **102,400 自旋** MAX-CUT；Facebook 63,392 用户社区划分实测（同 cut 值比 SA 快 ~200×）；稳定性 25 小时连续运行。
- **头条（对 06b 的直接锚点）**：其 **OPCS 方案=分相调度（先 α=0.25/β=0.2 跑 100 迭代 → 切 α=0.015/β=0.31）把慢收敛问题迭代数砍 >50%**，机理=缓解 domain freezing（增益过高致早熟冻结+顽固畴）；对照组 Param3（全程低 α 高 β）证明"分相"本身必要而非仅终态参数好。**这正是 06b 在测的调度族**——06b 的五调度×sin/tanh 实验从此有实验文献锚点（10 万自旋级、实测），不再只是我们的仿真主张。相关工作/讨论段可引："分相增益-耦合调度在大规模分叉型 IM 上已被实验验证（Chen 2026 IPIM），我们的 06b 在 MZM sin² 器件物理下系统化了该调度族"。
- [对 sim10 的划界] ① 平台 Si 热光（**µs–ms 响应**，其 Discussion 自承光学瓶颈）vs 我们 TFLN EO ns 级——快 3–6 个数量级的器件层差异；② 其 MVM 全在电子域（JA-SID 优化的是数字 MVM 缓存/FLOPs）——**光学只做非线性分叉，耦合计算不在光域**；我们 sim10 的碰撞调度恰恰要把耦合结构（距离依赖核）搬进光域，方向正交互补；③ 其耦合=图邻接二元矩阵（MAX-CUT 专用，自承 TSP/SAT 连续权重矩阵是难点）vs 我们 QUBO 强度编码+物理模型核——问题类不同。| 威胁：低（不占波长域/色散格子，不做光域耦合）。| 盟友引用点三个：OPCS 调度、domain freezing 物理、"二元耦合矩阵 vs 连续权重"的问题类划分（恰支撑我们选物理模型核的理由）。
- [顺带确认] 其 Table 1 对标文献含 Li 2024（ref 17，即已入档同组前作）——该组路线=TFLN(2024)→Si(2026)，MVM 始终在电子域，进一步确认"光域耦合计算"格子在他们路线上也是空的。

### 待办（下一批）

- 检查中转夹（06b 回执、07 聚合器修复 commit、HANDOFF_08b）；
- 06b 到后：把 OPCS 分相调度作为第 6 个对照调度纳入对照分析（若 06b 已含等价调度则引用即可），定稿 sim10 任务书；
- 若仍无回执：把 IPIM/OPCS 回灌 digest §五 #8 调度段 + sim10 草案 §1 相关工作。

## 2026-09-26 第六十二批：HANDOFF_08b 对账 + 批 60 勘误（E 列分噪声值）+ 精度交叉点口径统一

- [对账] HANDOFF_FROM_7945HX_08b 数值与我方批 60 独立聚合**逐点一致**（120 行、锚点 0.9979、四噪声档 acc）。两处口径差异入档：
- **勘误（我方批 60 表格）**：批 60 表"E"列 lif_N64=390 实为 **noise=0.5 档**的值（聚合脚本按行覆盖留下的尾值），非锚点档。**分噪声正确值（lif_N64）：n0.1=453.4 / n0.2=428.3 / n0.35=404.2 / n0.5=390.0**（E 随噪声升高而**下降**——首脉冲编码下噪声诱发更早的伪触发→延迟更短→能耗代理更低，方向与 08 的 lc 反噬机制不同，注意区分）。小黑 HANDOFF 的 453 ✅ 与此一致；08 原基线 469（不同脚本随机数流）与 453 差 16 属预期（任务书已预告）。对 uniform_b8(4096) 的能耗比分档：**n0.1=9.0× / n0.2=9.6× / n0.35=10.1× / n0.5=10.5×**——"4–10×"区间在全噪声档成立（能耗侧）。
- **精度交叉点口径统一**：数据=uniform_b8 在 **n=0.35 档即反超**（0.955 vs 0.939，差 1.6pt）；n≤0.2 LIF 精度领先（0.998>0.968、0.992>0.970）。小黑主张"鲁棒区间 noise≤0.2"（任何精度落劣势即失效）；我批 60 用"同量级"容忍 1.6pt 把边界放 0.35。**合并措辞（采更严者）**：LIF 精度领先区间=noise≤0.2；0.35 档 uniform 反超 1.6pt 但 LIF 能耗仍低 10×（权衡陈述可用）；0.5 档差距扩至 11pt（能耗优势无意义）。rc_tutorial §六.4 已按此修订。
- [小黑披露] 全量 496 s（14 workers），118 新跑+2 行断点续跑——与 merge stat "118 insertions"吻合，行数口径差异销项。

### 待办（下一批）

- 检查中转夹（06b 回执、07 聚合器修复 commit）；
- 06b 到后：验收 → 定稿 sim10 任务书（OPCS 分相臂对照已备）；
- 若仍无回执：文献主线切片（片上非线性×新方向：χ²/χ³ 光子学最新综述扫描）。

## 2026-09-26 第六十三批：神经形态光子学 Roadmap 2025 格子核查（130+ 作者权威文档，三格子全空确认）+ Yildirim 2023 补档

- [权威文档入档] Brunner, Shastri et al.（130+ 作者），"Roadmap on Neuromorphic Photonics"，arXiv:2501.07917（JPhys Photonics 2025），全文转文本 `.tmp/roadmap2025.txt` 已存档 | **格子核查三结果**：① **色散在分类学里只出现为"卷积加速器"**（Fig 1(c) chromatic dispersion convolutional processor [Xu21]=微梳横向滤波线）与 MMF/液芯光纤的慢速可调（温控/应力/光折变，1520 行）——**色散 GD 作为 RC 记忆/调度本体不在路线图的任何分类里，格子在路线图层面空置**（与百万自旋综述对 IM 的核查互证）；② **事件读出**：spiking 节全是神经元级实现+事件视觉传感器（流式细胞术），**无接口级事件读出讨论**——RQ4 在路线图层面同样空置；③ RC 应用节自承"电信信号处理主导、用例太少是领域挑战"（1830/1837 行）——雷达时间模式负载恰是路线图点名的空白方向。
- [文献判定·先占，中低] Yildirim, Oguz, Kaufmann, Reig Escalé, Grange, Psaltis, Moser, "Nonlinear optical feature generator for machine learning", APL Photonics 8, 106104 (2023)，被引 23（EPFL+ETH Grange；Roadmap 引作 [Yildirim22]）| **14 mm LNOI 波导，飞秒脉冲光谱编码数据 → χ²/χ³ 非线性变换输出光谱 → 数字线性分类器，多个数据库精度 +10%、参数量省 20×** | 占用："LNOI 波导材料非线性=光学特征生成器"概念（静态 ELM 式，**无记忆/无延迟结构、不可调、基准分类任务**）| 对我们：digest §五 #7"χ²/χ³ 材料非线性提供高阶特征"获得 LNOI 实验先例——**引用作盟友**（材料非线性特征生成可行性的实证）；划界=我们有 GD 延迟记忆+EO 可调+时序负载，他们是无记忆静态变换。
- [盟友素材] Roadmap PPLN 节（Marandi 线）：PPLN 纳米波导 ReLU 激活 16 aJ/75 fs、全光开关、单片 TFLN 全光 NN 愿景（PPLN+EOM+腔+耦合器）——零号稿"TFLN 平台超越调制器"叙事的最权威背书；另有"传统 OSP 元件（DCF/HNLF/PPLN/SOA）体积大、不可重构"的自述（3080 行）=我们可调性论据的路线图级引用。

### 待办（下一批）

- 检查中转夹（06b 回执、07 聚合器修复 commit）；
- Roadmap 回灌：rc_tutorial §5.4 注一行（路线图层面三格子空置确认）、digest §五 #7 补 Yildirim 2023 盟友引用；
- 06b 到后：验收 → 定稿 sim10 任务书。

## 2026-09-26 第六十四批：小黑 06b ising_schedule 验收（✅ 158/160+2 quick 覆盖，beta_ramp 当选 sim10 默认调度）

- [仿真验收·sim] `results/ising_schedule/`（commit e08b263，7945HX）：5 调度×2 act×2 区域×4 inst = **158/160 非 quick 行 + 4 quick 行** | 缺失 2 行=(α0.5,β5,noise1,inst0) 的 (linear,sin) 与 (pow_r1.0,sin)——同一点疑似 worker 崩溃；其中 linear 点恰被 quick 行覆盖（0.0827），pow_r1.0 点真缺（对结论无影响，该档 4 点剩余 3 点 sd 仍小）| ok=false 0 行 ✅
- **头条 1（beta_ramp=耦合斜坡调度全场最优，fail_dense 救援主力）**：fail_dense 区——sin：beta_ramp **0.2492** vs linear 0.0928（**2.7×**）；tanh：beta_ramp **1.0458（succ 1.00、tts 68）** vs linear 0.9982（succ 0.85、tts 81）——beta_ramp 把 tanh 推到超 BK 且满分快速。**sim10 默认调度定为 beta_ramp**。
- **头条 2（与 IPIM OPCS 互证 ✅ 批 61 锚点兑现）**：beta_ramp=耦合强度随退火斜坡上升，与 Chen/Zhang 2026 IPIM 的 OPCS 分相（前期低耦合防早熟、后期强耦合破畴冻）**同族同向**——我们的仿真最优调度与 10 万自旋实验最优调度方向一致，调度叙事从此是"仿真×实验双边证据"。
- **头条 3（调度救不了折返区 → sim10 增益箝位不可省）**：sin fail_dense 即便 beta_ramp 也只有 0.25、**success 仍全 0**——06b 证实"调度只能缓解不能消除失效区"，sim10 草案 §3 的摆幅箝位+失箝对照臂 D（可证伪设计）维持原判。
- **头条 4（pow_r 的次要价值=加速）**：ctrl_3reg 的 sin 臂全调度 succ=1.00，但 pow_r0.75/1.0 把 tts 从 175→**102**（-42%）且 metric 不降——Pramanik 递减步长的价值在收敛速度不在精度；beta_ramp 在该区反而最慢（237）。**sim10 建议：主调度 beta_ramp，附录可报 pow_r 加速档**。
- [口径] tanh 在 ctrl_3reg 全灭（0.24–0.37）与 06 已知结论一致（3reg 是 sin 主场），非新发现。

### 待办（下一批）

- 写 RECEIPT_06b 入中转夹；sim10 草案 §4 定稿（beta_ramp 默认+OPCS 互证+箝位维持）；
- **定稿 sim10 任务书发中转夹**（所有数据依赖已齐：09 核族/臂 B 锚点 ✅、06b 调度 ✅、OPCS 文献锚 ✅）；
- 检查中转夹（07 聚合器修复 commit、HANDOFF_06b）。

## 2026-09-26 第六十五批：sim10 脚本定稿下发（三轮动力学标定的两个意外物理发现）

- [仿真下发·sim10] `simulations/10_collision_ising.py` + 任务书 `TASK_REQUEST_20260926_sim10.md`（中转夹）：14 臂配置（A 天花板/M 混频器代价/B GDR×3φ/C 拟合核×2/D 失箝扫描×3 档）×4 inst=56 行，beta_ramp 调度、双指标（self/target）、SA 同种子纪律、断点续跑内建。依赖全齐（09 拟合节点硬编码、06 SA 复用）。
- **标定发现 1（动力学选型）**：纯 sigmoid QUBO 动力学（草案 v1）比混合态差 8–13pt——混合态（光学=强度脉冲 x=Θ(v)、电子=双极模拟态 v 走 tanh）为正解，物理上更诚实（光学强度、电子双极）；均场偏置问题靠"强度和压缩−x=0.5 参考直流差分扣除"解决（草案 §2 差分读出落到实处）。
- **标定发现 2（臂 D 预期反转，草案 §7 已修订）**：失箝扫描 swing{3,10,30} 下**无灾难失效**（0.926→0.860，30× 仅 −7%，仍高于理想混频器天花板臂）——**06 sin² 的"增益定标共同纪律"不迁移到单调 XGM 混频器：纪律的对象是非单调性（折返），不是摆幅本身；单调压缩=内建软箝位**。AGC 对照（RMS 归一化）进一步显示压缩甚至单调有益（场整形）——故默认口径=固定增益接收机。M 臂（理想核+XGM）高于 A 臂（理想核+理想读出）同源于此：**混频器不是代价而是特性**。这是"两段式架构"叙事的重要正面论据。
- [文档] sim10 草案 §6/§7 更新为 v2（臂表+修订验收锚点）；脚本 docstring 记录全部标定结论。

### 待办（下一批）

- 检查中转夹（sim10 回执、07 聚合器修复 commit）；
- sim10 到后：验收（对照任务书 5 条+标定值表）→ 写批 66；
- 若仍无回执：文献切片（Wan 老师组相容性评估素材整理——用户最初的评估要求尚未单独成文）。

## 2026-09-26 第六十六批：07 聚合器修复验收（lorenz_diverged_frac 分母修正，与批 40 既有数字互洽 ✅）

- [修复验收] 小黑 commit 3de6186：`lorenz_diverged_frac` 分母从"仅 diverged 行"改为"全部 lorenz 行"（diff 已审，修改正确且仅限聚合器，不动原始 jsonl）。修复后数值：**ngrc 0.733 / hybrid 0.650 / rc_tanh 0.217 / esn 0.033**——与批 40 既有记录逐点对账：ngrc "73% 配置发散"✅、rc_tanh "weak-λ 下 22% 发散"✅、hybrid 对 ngrc 仅边际改善（65% vs 73%，与 λ=1e-2 档 4/20 vs 5/20 的边际结论同向）✅。**rc_tutorial §六.2 与 digest 的既有引用数字无需修订**（它们引的就是批 40 手工聚合值，恰与修复后聚合器一致——修复前 summary.json 的错误值从未进入文档）。
- [口径] 07 聚合器修复 commit 长期未到事项**销项**；小黑队列当前只剩 sim10（批 65 已下发）。

### 待办（下一批）

- 检查中转夹（sim10 回执/HANDOFF）；
- sim10 到后：验收（任务书 5 条+标定值表）→ 写批 67；
- 若仍无回执：Wan 老师组相容性评估素材整理成文（用户最初要求，素材=批 52–66 的先占/盟友判定）。

## 2026-09-26 第六十七批：批 64 勘误（06b 无真实缺行，quick 行覆盖口径）+ HANDOFF_06b/NOTE×2 对账销项

- [勘误·我方批 64] "pow_r1.0 的 (α0.5,β5,noise1,inst0) 点真缺"**判定错误**。小黑 NOTE_06b_rows_reconcile 指出并经我复核确认：该点以 **quick=True 行存在（metric=0.0878）**，linear 点同为 quick 行（0.0827）。文件 162 行=160 网格行（158 全量+2 quick 覆盖行）+2 quick 锚点行（ctrl_3reg α0.5，网格外）；脚本自检 done=160 todo=0 ✅ **网格覆盖完整，无 worker 崩溃、无丢行**。两点差异仅在 n_runs=2（quick）vs 5（全量）的统计权重。批 64 的"疑似 worker 崩溃"归因一并撤回。教训入档：断点续跑口径下 quick 行计入网格覆盖，分析端过滤 quick 前应先按 _KEY_FIELDS 核覆盖。
- [对账销项] NOTE_07_aggregator_fix 与批 66 验收一致（数值逐点同）；HANDOFF_06b/SIMLOG 与批 64 数值一致（除上述缺行口径外无分歧）。小黑队列：sim10 已受理（批 65 任务书），无其他未决项。

### 待办（下一批）

- 检查中转夹（sim10 回执/HANDOFF）；
- sim10 到后：验收（任务书 5 条+标定值表+批 65 预告的三个"非 bug"趋势）→ 写批 68；
- 若仍无回执：Wan 老师组相容性评估成文（素材=批 52–67 判定链）。

## 2026-09-26 第六十八批：Wan 组相容性评估成文（`docs/wan_compatibility.md` 新建 + digest §四刷新）

- [成文] 用户最初要求"评估我们的创意与 Wan 老师组研究的相容性"完成：新建 `docs/wan_compatibility.md`（七节：评估口径/Wan 组版图/我方资产清单/相容性矩阵批68刷新版/重叠竞争面划界4条/合作切口排序A–E/风险未决5条/一句话结论）。digest §四替换为速查版+指针。
- [核心判定] 相容性总体=**高**：Wan 组两个自认短板（耦合层在电域、读出 1 kHz）恰是我方资产主轴；双方同处"避开全连接 Max-Cut"的船。起手式=切口 A（调度互惠，零成本：06b beta_ramp/OPCS 可移植到 QD-LI 机，IPIM 实验锚点+CMIM"Pramanik 理论实验未实现"空白）；战略抓手=切口 B（混合集成 OEO-Ising：QD 核+我们色散耦合层=CMIM 三堵墙对照组）；切口 D（碰撞调度×QD SOA 异色混频）等 sim10 验收后升级。
- [划界4条入档] ①光域耦合层生态位仍空但窗口有限（IPIM 热光慢/CMIM 电子域/spQUBO 仅仿真）；②QD-LI vs sin² 不对抗做混合；③结构化叙事主打 spQUBO 后的"光学 MVP 空白"互补定位；④全连接 Max-Cut 战场两组都不碰。
- [风险入档] 草稿未发表需复核；sim10 未验收前 D 级论据不对外引用；QD-LI 死区定量证据缺实测小信号段（列入合作 A 交换清单）。

### 待办（下一批）

- 检查中转夹（sim10 回执/HANDOFF）；
- sim10 到后：验收（任务书 5 条+标定值表+批 65 预告的三个"非 bug"趋势）→ 写批 69 + RECEIPT_sim10；
- 若仍无回执：arXiv 新一轮扫描（photonic local field readout / optical MVP Ising 同族普查，spQUBO 互补定位点防漏档）。

## 2026-09-26 第六十九批：arXiv 同族普查（optical MVP/局域场读出方向）——hex mesh 入档，SPIM 校准存档

- [扫描] 围绕 spQUBO 互补定位点（卷积耦合光学 MVP 空白）与"photonic local field readout"两关键词扫描，命中 2 篇新稿。
- [入档·低威胁但重要信号] [Rausell-Campo/Al-Kayed/Pérez-López/Aadhi/Shastri/Capmany, "Ising accelerator with a reconfigurable interferometric photonic processor", arXiv:2511.13284v2 (2025-11)](https://arxiv.org/abs/2511.13284)：UPV hex mesh 通用可编程光子平台做伊辛耦合层，电子退火环+可重构 MVM，实验 3 节点铁磁+4 节点 Max-Cut、仿真 N=50 >80%。**作者含 Al-Kayed（CMIM）与 Aadhi（百万自旋综述）=Shastri 生态圈已同时押注干涉网格耦合路线**。划界：逐元热调相移器功耗随 N² 涨 vs 我们色散几何零逐元调制；实验规模极小。"耦合层竞赛升温"由推测升级为事实，已回灌 wan_compatibility.md §6 风险 1。
- [存档] [Karanikolopoulos et al., "Precision Hamiltonian Encoding in Full-Aperture SPIM", arXiv:2602.13714 (2026-02)](https://arxiv.org/abs/2602.13714)（Savvidis/Conti/Berloff/Tsintzos）：SPIM 全孔径标定（波前检索 <λ/40+相互作用归一化），方法学论文，与片上路线距离远，非威胁。
- digest §二版图表新增两行（hex mesh、全孔径 SPIM 校准）+hex mesh 划界注。

### 待办（下一批）

- 检查中转夹（sim10 回执/HANDOFF）；
- sim10 到后：验收（任务书 5 条+标定值表+批 65 预告趋势）→ 写批 70 + RECEIPT_sim10；
- 若仍无回执：继续 RC vs 其它技术对比方向的文献切片（候选：模拟/光子 Ising 的数字退火对照基准现状——为"不比精度比能效"叙事补弹药；或 Cuevas/Kuse 2025 微梳 RC 正文补读）。

## 2026-09-26 第七十批：Cuevas/Kuse 2025 微梳频率复用 ORC 全文精读（批 59 遗留销项）

- [获取] De Gruyter 主站反爬（202 空响应）；经 PMID 40970238 → PMC idconv → [PMC12442360](https://pmc.ncbi.nlm.nih.gov/articles/PMC12442360/) 拿到全文。正式引用：Cuevas/Hu/Shi/Liu/Minoshima/Kuse, "Frequency-multiplexed optical reservoir computing using a microcomb", Nanophotonics 14(18), 3063–3073 (2025)，被引 4。单位：德岛大学+IQA 深圳（刘俊秋）+UEC。
- [精读要点] 孤子微梳（Si₃N₄，Q_loaded=7×10⁶，线宽 28 MHz，FSR 100 GHz，泵浦 200 mW）梳齿=节点；输入经 DP-MZM 载波抑制单边带调到泵浦失谐；记忆=腔光子存储（瞬态振荡周期 ~6 ns，持续 >100 ns）；仿真 60 齿 Santa Fe NMSE 0.015@50 MSa/s（最优归一化调制率≈2）、NLEQ SER 降 >10×@100 MSa/s；实验 37 齿 Santa Fe 0.081±0.006（最优 0.061）、NLEQ SER 0.0635±0.004@SNR40；读出实验为电子域串行扫齿，微环权重阵列（add-drop+BPD 正负权重）仅提案；ASE 噪声限 SNR 20–25 dB。
- [关键判定·盟友切口] **模式间随机延迟是其实验最强单一杠杆（NMSE 0.8→0.21→0.081），但他们没有片上模式相关延迟器件，只能后处理 trial-and-error——我们的啁啾光栅 GD 正是确定性可设计的波长相关延迟元件，可把该技巧硬件化**。引用句式与划界五条（腔寿命记忆 vs 几何 GD 记忆/孤子稳频环 vs 无源免稳定/Si₃N₄ 外置 EOM vs TFLN 原生 EO/ASE 噪声/基准任务）已回灌 rc_tutorial §5.4 表+盟友价值③。
- [附带证据] 失谐工作点敏感性（蓝边 0.064 vs 红边 0.17）=跨平台工作点定标共识又添一条实验证据（与 Ds-PRC/06 sin 失效区同族）。
- [存档] arXiv:2602.18110（"Cavity Solitons as a Nonlinear Substrate for Photonic Neuromorphic Computing"，alphaxiv 二级来源）自承是 Cuevas 2025 的空间孤子扩展——频率复用 RC 血统链再延一代，暂不精读。

### 待办（下一批）

- 检查中转夹（sim10 回执/HANDOFF）；
- sim10 到后：验收（任务书 5 条+标定值表+批 65 预告趋势）→ 写批 71 + RECEIPT_sim10；
- 若仍无回执：数字退火对照基准现状调研（"不比精度比能效"叙事弹药）或 digest §五机会清单与新证据的对齐检查。

## 2026-09-26 第七十一批：小黑 sim10 collision_ising 验收（✅ 56/56，任务书 5 条全过）

- [验收通过] `results/collision_ising/results.jsonl` @ 6453c1a：① 56 行 ok=false=0，臂分布 A/M/B/D=12、C=8 ✅；② 臂 D sw3/10/30 self=0.934/0.916/0.881，30× 失箝仅 −5.6%、无灾难失效 ✅；③ 臂 B GDR 代价 1.5%/1.3%/0.7%（vs M gauss 0.934）<10% ✅；④ C exp3 self 0.956 ≥0.95 ✅，C pow15 target_ratio 0.804（0.758–0.827）首次测量入档 ✅；⑤ A/M/D(exp3) bk_real 4 inst 浮点精确逐位相等 ✅。三个"非 bug"预告（失箝不失效/M>A/C pow15 self>1.0）全部确认。
- [勘误·我方] 对账时我一度把 C pow15 target_ratio 算成 0.639（误用 bk_real/bk_tgt），脚本定义 target_ratio=E(J_tgt,best_s0)/bk_tgt → 0.804，与小黑 HANDOFF 一致。**我方计算口径错误，双方数据无分歧**；bk_real/bk_tgt 与 target_ratio 是两个不同量，入档防再犯。
- [schema 注记] A/M/B/C 臂无 `swing` 键（仅 D 臂有），双方如实入档，不补 null 不改脚本。
- [科学结论升级] sim10 四条设计层结论 → 验收级：**① 单调 XGM 混频器是正贡献不是代价（M 臂 exp3 +7.1%、gauss +3.9% vs A 臂，压缩场整形 4inst×3 核成立）；② 增益定标纪律对象=非单调性而非摆幅；③ GDR（A=3ps）对结构化伊辛核几乎无损；④ 09 拟合核可用且 pow15 实现核比目标核更好解（self 0.969、succ 0.55、tts 233 全场最优）**。
- [回灌] sim10_design_draft.md 新增 §11 验收结果表；wan_compatibility.md 风险 2 标记解除、切口 D 论据升级为可引用级（仿真级证据口径）；RECEIPT_sim10_20260926 已入中转夹；HANDOFF_sim10/SIMLOG 对账一致销项。小黑队列全部清空。

### 待办（下一批）

- 检查中转夹（用户新指令/新 HANDOFF；注意 HANDOFF_XIAOBAI_background_slides/transceiver_fig1 属 PPT 会话，不碰）；
- 小黑队列已空：可设计下一任务书（候选：sim11=微梳 RC 的模式间延迟硬件化验证——把批 70 Cuevas 杠杆做成我们的 GD 引擎演示；或 L1-L3 之外的重型仿真需求）；
- 文献切片：数字退火对照基准现状（"不比精度比能效"弹药）。

## 2026-09-26 第七十二批：sim11 设计定稿+本机标定+任务书下发（GD 模式间延迟硬件化）

- [设计] `simulations/11_gd_intermode_delay.py`（新，361 行）：把批 70 Cuevas 杠杆做成我方 GD 引擎演示。唯象模型三轮标定修正：① 单极点+静态多样性 → A 臂 NMSE>1（动力学多样性不足）；② 加 τ_eff 散布 → 基线自带动态多样性、延迟边际价值被稀释（模型经济学错误）；③ **定稿=欠阻尼二阶孤子弛豫振荡（τ_ring=40 ns、f_ring=150 MHz，对齐 Cuevas Fig 3 振荡 6.8 ns/持续>100 ns）+ 全齿共享动态 + 静态 (g_m,q_m) 多样性 + γ=0.1 双线性 Kerr 交叉项**——动态去相关完全由模式间延迟提供，臂间差异干净归因。教训入档：唯象模型里"谁提供多样性"决定臂间归因，内置多样性会偷走被测机制的功劳。
- [数据] Santa Fe A 集入库 `data/santafe_laser.npy`（reservoirpy GitHub 仓库镜像，10093 点 int 0–255）。De Gruyter 正文反爬教训后改走 PMC/GitHub 数据镜像的成功路径。
- [标定头条（quick，16 配置）] **santafe@50M：A=0.986（无延迟退化，复现 Cuevas 0.8 方向）→ B 随机延迟 best=0.126（复现其 0.21 杠杆）→ C 线性 GD a=100ps/mode=0.068——确定性设计 2× 胜随机试错上限**；@1G：0.128 vs 0.307 同向。NARMA 对延迟多样性不敏感（诚实负面对照）。
- [任务书] TASK_REQUEST_20260926_sim11 已入中转夹：556 配置、验收 5 条、标定对照表、物理预告 3 条（增益集中 a≥100ps/mode=D≥125ps/nm 超工程可达标注为预期；1THz 间隔梳 D 需求降 10×=报告口径）。

### 待办（下一批）

- 检查中转夹（sim11 回执/用户指令）；
- sim11 到后：验收（5 条+标定对照）→ 批 73 + RECEIPT_sim11；通过后回灌 rc_tutorial §5.4 盟友价值③（把"盟友切口"升级为"仿真验证"）；
- 文献切片：数字退火对照基准（"不比精度比能效"弹药）。

## 2026-09-26 第七十三批：数字退火对手盘基准表（Aadhi 2026 全文挖掘，能效叙事弹药）

- [获取] arXiv:2607.13446v1 HTML 全量转文本（`.tmp/aadhi2026.txt`，13.3 万字符）。
- [成表] digest §二"规模动机"节新增**数字对手盘基准表**（6 行+口径列）：25×H100=数十 kW/数百万美元（估计）、多板 FPGA CMOS 1.3M 自旋（已演示）、Hitachi 20k 单片、Toshiba SBM 多片 10⁵ 级、**耦合激光空间 PIM 估计 ~2 PFLOPS@13W vs H100 700W（估计非实测，引用必须带口径）**、光子存储 40 fJ/MAC@8bit（4bit 再降 250×）+TFLN DOPA 55 dB/cm/√W。
- [弹药句式入档]「不主张规模对抗 CMOS/GPU；耦合存进色散几何后单芯片 W 级功耗完成结构化耦合层——能效而非规模是赛道」。附带可引用点：sigmoid vs 多项式 TTS 差 10×（呼应 06 sin²）；光纤 >10⁵ 自旋不稳；Fig 1(d) 蜘蛛图框架现成。

### 待办（下一批）

- 检查中转夹（sim11 回执/用户指令）；
- sim11 到后：验收（5 条+标定对照）→ 批 74 + RECEIPT_sim11；通过后回灌 rc_tutorial §5.4 盟友价值③（"盟友切口"→"仿真验证"）+ 任务书口径（1 THz 间隔梳 D 需求降 10×）写进机会清单；
- 若仍无回执：Cuevas 后续 arXiv:2602.18110（空间孤子扩展）或 Jiang 2024 三类退火机基准（被引 22）精读。

## 2026-09-26 第七十四批：Jiang 2024 三类退火机第三方基准精读（"不碰经典基准"弹药补强）

- [获取] [Jiang/Shu/Lin, "Benchmarks and Recommendations for Quantum, Digital, and GPU Annealers in Combinatorial Optimization", IEEE Access 12, 125014 (2024)](https://ieeexplore.ieee.org/document/10665740)（inspirehep PDF 镜像，6 页正文+表，`.tmp/jiang2024.pdf/.txt`）。台湾中央大学 CS 组=无光子利益方的第三方。
- [关键数字] QA(D-Wave Advantage)/DA(Fujitsu DAU-3)/GPUA(Compal Quantix) × 8 类 COP × 经典 SOTA：**执行时间榜首计数 CA 42 / DA 13 / QA 2 / GPUA 1**；QA 长耗时主因=分解+嵌入映射税；其结论与 Mohseni 2022 总判决互洽（机会在 CA 未深耕的新问题）。
- [回灌] digest §诚实性警示新增条目+引用句式（"连最佳商用退火机执行时间榜首率仅 13/58"）；方法论（双轴排名+X/IS/N/A 协议）与我们 06-10 的 success/tts 口径兼容确认。

### 待办（下一批）

- 检查中转夹（sim11 回执/用户指令）；
- sim11 到后：验收（5 条+标定对照）→ 批 75 + RECEIPT_sim11 + rc_tutorial §5.4 回灌；
- 若仍无回执：arXiv:2602.18110 空间孤子稿或 Tatsumura SBM 多片扩展（批 73 表内 10⁵ 级条目）精读。

## 2026-09-26 第七十五批：arXiv:2602.18110 精读——血统链起点 ULB Massar 组亲自下场孤子 RC

- [判定修正] 批 70 据 alphaxiv 二级来源记为"Cuevas 的空间孤子扩展"**不准确**。摘要+作者级精读：[Arabieh/Lupo/Gorza/Massar, arXiv:2602.18110 (2026-02)](https://arxiv.org/abs/2602.18110)=**频率复用 RC 血统链起点 ULB Massar 组**（Lupo 2021/Butschek 2022 同组）的**光纤腔孤子**RC：相位调制驱动编码输入、频率分辨读出、数值仿真为主；**明示 Kelly 波（三阶色散谐振辐射）丰富动力学提升性能**。
- [格子核查] 不占我们的格子（光纤腔非片上、无 GD 工程、无事件读出、基准任务），但**"色散参与 RC 特征生成"的叙事距离在收窄**——该家族已开始用色散效应当特征丰富机制（物理给定不可设计 vs 我们工程化可设计的划界成立）。已入 rc_tutorial §5.4 血统链注+划界四条。
- [动作] 无需改族谱结论；"色散 GD 当记忆/调度"格子仍空。

### 待办（下一批）

- 检查中转夹（sim11 回执/用户指令）；
- sim11 到后：验收（5 条+标定对照）→ 批 76 + RECEIPT_sim11 + rc_tutorial §5.4 盟友价值③升级；
- 若仍无回执：Tatsumura SBM 多片扩展精读（批 73 表内 10⁵ 级条目补一手数字），或 digest §五机会清单与批 52–75 新证据对齐检查。

## 2026-09-26 第七十六批：digest §五机会清单对齐检查（批 52–75 证据回灌）

- [对齐] §五 #8 状态行过期（"列为仿真候选 09 号待排队"）→ 更新为：09 ✅ 369/369 + sim10 ✅ 56/56 两段式架构仿真链已闭环，指针到 sim10_design_draft §11；定位句保留。
- [新增] §五 #9 **微梳 RC 模式间延迟硬件化**（批 70/72 素材）：Cuevas 杠杆的需求证明 + sim11 标定头条（GD 0.068 vs 随机 0.126=2×，标注"标定值待全量验收"）+ 三元设计空间口径（GD 延迟×模式间隔×符号率；1 THz 间隔梳把 D 需求降 10× 落入工程可达域）+ 盟友切口定位。
- [核查] §五其余各项与批 52–75 无冲突：#3 GD 线性层（Zhang 2025/Huang 2019 划界有效）、#5 全光 ReLU（电子学瓶颈在 ADC/DSP 论断有效）、#7 片上 NGRC（Yildirim 盟友有效）。§六 FTO/基准诚实性/先占地图无需变动。

### 待办（下一批）

- 检查中转夹（sim11 回执/用户指令）；
- sim11 到后：验收（5 条+标定对照）→ 批 77 + RECEIPT_sim11 + rc_tutorial §5.4 盟友价值③升级 + §五 #9 标定值→验收值；
- 若仍无回执：Tatsumura SBM 多片扩展精读（批 73 表内 10⁵ 级条目一手数字）。
