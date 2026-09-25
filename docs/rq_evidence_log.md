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

### 待办（下一批）

- 检查中转夹（小黑 05/06、07、08 回执；用户下载的清单 #1、#2、#4）；
- 若仍无回执：继续文献循环——共享非线性元件的候选物理（XPM in TFLN? χ³ 较弱；共享 OPO 增益竞争 = PIC-OPO 已示范；半导体光放大器 SOA 交叉增益）调研，为仿真 10 的可行混频机制选型。
