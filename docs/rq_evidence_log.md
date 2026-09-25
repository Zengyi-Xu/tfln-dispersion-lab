# RQ 证据日志（通宵调研产出）

> 配套 `RQ清单_调研草案.md` / `论文零号稿_草稿.md`。格式：`[RQx.y] 文献 | 关键数字/声明 | 支撑/威胁零号稿哪段 | 判据`。
> 起始日期 2026-09-26。维护：小白（文献会话）。所有数字引用公开来源，写论文前需按引用规范二次核实原文。

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

### 待办（下一批）

- RQ3.2：光子 SNN 突触/延迟实现方式梳理（部分已在 ising digest §三-12）；
- RQ2.2 补强：雷达数字脉压实测功耗（1–2 篇硬数字）。
